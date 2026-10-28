"""Reference systems under test. Deliberately small, not the Enterprise SDD source."""
from __future__ import annotations
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4
from .common import Recorder, atomic_write, canonical, digest, file_hash, read_json, safe_path, snapshot, write_json


@dataclass(frozen=True)
class GateResult:
    accepted: bool
    reasons: tuple[str, ...]


class Gate:
    def __init__(self, recorder: Recorder):
        self.recorder = recorder

    def evaluate(self, spec: dict, artifact: Path, review: dict | None,
                 builder_session: str, checkpoint: Path) -> GateResult:
        errors: list[str] = []
        if not isinstance(builder_session, str) or not builder_session.strip():
            errors.append('missing_builder_identity')
        criteria = spec.get('acceptance_criteria')
        if not isinstance(criteria, list) or not criteria or any(not isinstance(x, str) or not x.strip() for x in criteria):
            errors.append('missing_acceptance_criteria')
        artifact_sha = file_hash(artifact)
        if artifact_sha is None:
            errors.append('missing_artifact')
        spec_sha = digest(canonical(spec))
        if not isinstance(review, dict):
            errors.append('missing_review')
        else:
            if review.get('verdict') != 'approve':
                errors.append('review_not_approved')
            if not isinstance(review.get('session_id'), str) or not review['session_id'].strip() or review['session_id'] == builder_session:
                errors.append('reviewer_not_separate')
            if review.get('artifact_sha256') != artifact_sha or artifact_sha is None:
                errors.append('stale_artifact_review')
            if review.get('spec_sha256') != spec_sha:
                errors.append('stale_spec_review')
        if errors:
            checkpoint.unlink(missing_ok=True)
            self.recorder.emit('gate', 'gate.rejected', reasons=errors, artifact_sha256=artifact_sha)
            return GateResult(False, tuple(errors))
        write_json(checkpoint, {'artifact_sha256': artifact_sha, 'spec_sha256': spec_sha,
                                'builder_session': builder_session, 'reviewer_session': review['session_id']})
        self.recorder.emit('gate', 'gate.accepted', artifact_sha256=artifact_sha, spec_sha256=spec_sha)
        return GateResult(True, ())


class PermissionGateway:
    """Allowlisted in-process test gateway, NOT an OS/native-CLI sandbox."""
    def __init__(self, root: Path, recorder: Recorder, writable: set[str] | None = None):
        self.root = root
        self.recorder = recorder
        self.writable = set({'result.txt'} if writable is None else writable)

    def write_file(self, relative: str, content: str) -> dict[str, Any]:
        path = safe_path(self.root, relative)
        if not isinstance(content, str) or len(content.encode('utf-8')) > 64 * 1024:
            raise ValueError('Content must be a string of at most 64 KiB')
        operation = str(uuid4())
        arguments = {'path': relative, 'content_sha256': digest(content)}
        self.recorder.emit('runtime', 'tool.attempt', operation_id=operation, tool='write_file', arguments=arguments)
        if relative not in self.writable:
            self.recorder.emit('policy', 'policy.denied', operation_id=operation, tool='write_file', arguments=arguments)
            return {'ok': False, 'error': 'permission_denied', 'operation_id': operation}
        atomic_write(path, content)
        self.recorder.emit('runtime', 'file.written', operation_id=operation, path=relative, sha256=digest(content))
        return {'ok': True, 'operation_id': operation}

    def read_file(self, relative: str) -> str:
        path = safe_path(self.root, relative)
        data = path.read_text(encoding='utf-8')
        self.recorder.emit('runtime', 'file.read', path=relative, sha256=digest(data))
        return data

    def load_skill(self, name: str) -> str | None:
        path = safe_path(self.root, f'skills/{name}.md')
        if not path.exists():
            self.recorder.emit('runtime', 'skill.unavailable', name=name)
            return None
        data = self.read_file(f'skills/{name}.md')
        self.recorder.emit('runtime', 'skill.loaded', name=name, sha256=digest(data))
        return data


class ToolService:
    """Synthetic server-side audit, not an MCP transport implementation."""
    def __init__(self, audit_path: Path, receipt: str):
        self.audit_path, self.receipt = audit_path, receipt
        self.calls: list[dict] = []
        write_json(audit_path, self.calls)

    def invoke(self, name: str) -> str:
        self.calls.append({'tool': name})
        write_json(self.audit_path, self.calls)
        return self.receipt


class ToolGateway:
    def __init__(self, service: ToolService, recorder: Recorder):
        self.service, self.recorder = service, recorder

    def discover(self) -> list[str]:
        tools = ['echo_receipt', 'admin_reset']
        self.recorder.emit('runtime', 'tools.discovered', tools=tools)
        return tools

    def call(self, name: str) -> str | None:
        op = str(uuid4())
        self.recorder.emit('runtime', 'tool.attempt', operation_id=op, tool=name, arguments={})
        if name != 'echo_receipt':
            self.recorder.emit('policy', 'policy.denied', operation_id=op, tool=name, arguments={})
            return None
        return self.service.invoke(name)


class SessionStore:
    def __init__(self, state: Path, recorder: Recorder):
        self.state, self.recorder = state, recorder
        self.state.mkdir(parents=True, exist_ok=True)

    def create(self, context: str) -> str:
        session = str(uuid4())
        write_json(self.state / (session + '.json'), {'session_id': session, 'context': context})
        self.recorder.emit('runtime', 'session.started', session_id=session)
        return session

    def resume(self, session: str) -> dict:
        from uuid import UUID
        if str(UUID(session)) != session:
            raise ValueError('Noncanonical session UUID')
        data = read_json(self.state / (session + '.json'))
        if data.get('session_id') != session:
            raise ValueError('Session identity mismatch')
        self.recorder.emit('runtime', 'session.resumed', session_id=session)
        return data


class OwnershipError(RuntimeError):
    pass


class InjectedInterruption(RuntimeError):
    pass


class Publisher:
    """Single-writer example with explicit recovery; no process/concurrency certification."""
    def __init__(self, root: Path, state: Path, recorder: Recorder):
        self.root, self.state, self.recorder = root, state, recorder
        state.mkdir(parents=True, exist_ok=True)
        self.ledger = state / 'ownership.json'
        self.journal = state / 'pending.json'
        self.history = state / 'history.json'
        if not self.ledger.exists():
            write_json(self.ledger, {})
        if not self.history.exists():
            write_json(self.history, [])

    def publish(self, payload: dict[str, str], interrupt_after_first: bool = False) -> str:
        if self.journal.exists():
            raise OwnershipError('Pending transaction: recover explicitly before publishing')
        if not payload:
            raise ValueError('Empty publication')
        owned = read_json(self.ledger)
        before: dict[str, str | None] = {}
        after: dict[str, str] = {}
        for name, content in payload.items():
            if not isinstance(content, str):
                raise ValueError('Payload values must be strings')
            path = safe_path(self.root, name)
            current = file_hash(path)
            if (path.exists() and (not path.is_file() or name not in owned)) or (name in owned and current != owned[name]):
                raise OwnershipError(f'Refusing foreign or drifted artifact: {name}')
            before[name] = base64.b64encode(path.read_bytes()).decode() if path.exists() else None
            after[name] = digest(content)
        tx = str(uuid4())
        entry = {'id': tx, 'before': before, 'after': after,
                 'before_dirs': snapshot(self.root)['directories'],
                 'ledger_before': owned, 'ledger_after': {**owned, **after}, 'rolled_back': False}
        write_json(self.journal, entry)
        for index, (name, content) in enumerate(payload.items()):
            atomic_write(safe_path(self.root, name), content)
            if interrupt_after_first and index == 0:
                self.recorder.emit('publisher', 'publication.interrupted', transaction_id=tx)
                raise InjectedInterruption('Injected interruption after first file replacement')
        write_json(self.ledger, entry['ledger_after'])
        history = read_json(self.history)
        history.append(entry)
        write_json(self.history, history)
        self.journal.unlink()
        self.recorder.emit('publisher', 'publication.committed', transaction_id=tx)
        return tx

    def _restore(self, entry: dict, recovery: bool) -> None:
        ledger_now = read_json(self.ledger)
        acceptable_ledgers = [entry['ledger_before'], entry['ledger_after']] if recovery else [entry['ledger_after']]
        if ledger_now not in acceptable_ledgers:
            raise OwnershipError('Ownership ledger changed outside this transaction')
        for name, encoded in entry['before'].items():
            before_sha = digest(base64.b64decode(encoded)) if encoded is not None else None
            acceptable = {before_sha, entry['after'][name]} if recovery else {entry['after'][name]}
            if file_hash(safe_path(self.root, name)) not in acceptable:
                raise OwnershipError(f'Refusing to overwrite post-transaction drift: {name}')
        for name, encoded in entry['before'].items():
            path = safe_path(self.root, name)
            if encoded is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, base64.b64decode(encoded))
        original_dirs = set(entry['before_dirs'])
        for path in sorted(self.root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir() and path.relative_to(self.root).as_posix() not in original_dirs:
                try:
                    path.rmdir()  # Never recursively delete unrelated content.
                except OSError:
                    pass
        write_json(self.ledger, entry['ledger_before'])

    def recover(self) -> bool:
        if not self.journal.exists():
            return False
        entry = read_json(self.journal)
        history = read_json(self.history)
        if any(x['id'] == entry['id'] for x in history):
            # A commit reached history before the journal was removed.
            if read_json(self.ledger) != entry['ledger_after'] or any(file_hash(safe_path(self.root, n)) != h for n, h in entry['after'].items()):
                raise OwnershipError('Committed transaction drifted before journal cleanup')
            self.journal.unlink()
            return True
        self._restore(entry, recovery=True)
        self.journal.unlink()
        self.recorder.emit('publisher', 'publication.recovered', transaction_id=entry['id'])
        return True

    def rollback(self, transaction: str) -> bool:
        if self.journal.exists():
            raise OwnershipError('Recover pending publication before rollback')
        history = read_json(self.history)
        entries = [x for x in history if x['id'] == transaction]
        if len(entries) != 1:
            raise OwnershipError('Unknown or duplicate transaction')
        entry = entries[0]
        if entry['rolled_back']:
            return False
        active = [x for x in history if not x['rolled_back']]
        if not active or active[-1]['id'] != transaction:
            raise OwnershipError('Only the latest active publication can be rolled back')
        self._restore(entry, recovery=False)
        entry['rolled_back'] = True
        write_json(self.history, history)
        self.recorder.emit('publisher', 'publication.rolled_back', transaction_id=transaction)
        return True
