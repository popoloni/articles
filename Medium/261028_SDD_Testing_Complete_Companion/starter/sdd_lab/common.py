"""Small, explicit primitives. No shell execution or third-party dependencies."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import tempfile
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def file_hash(path: Path) -> str | None:
    return digest(path.read_bytes()) if path.is_file() else None


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and existing symlinks; not a concurrent OS sandbox."""
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative or '\x00' in relative:
        raise ValueError('Expected a nonempty, slash-separated relative path')
    parts = relative.split('/')
    if any(p in ('', '.', '..') for p in parts) or PurePosixPath(relative).is_absolute():
        raise ValueError('Absolute, empty and traversal components are forbidden')
    base = root.resolve()
    candidate = base
    for component in parts:
        candidate = candidate / component
        if candidate.is_symlink():
            raise ValueError('Symlink paths are forbidden')
    if not candidate.resolve().is_relative_to(base):
        raise ValueError('Path escaped the workspace')
    return candidate


def atomic_write(path: Path, data: bytes | str) -> None:
    """Same-directory replacement; not a multi-file or power-loss transaction."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def snapshot(root: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    dirs: list[str] = []
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Snapshot does not accept symlinks')
        rel = p.relative_to(root).as_posix()
        if p.is_file():
            files[rel] = digest(p.read_bytes())
        elif p.is_dir():
            dirs.append(rel)
    return {'files': files, 'directories': dirs}


def environment() -> dict[str, str]:
    return {'python': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine()}


class Recorder:
    """Controller-owned event channel. Agent prose must never be promoted into it."""
    def __init__(self, path: Path):
        self.path = path
        self.events: list[dict[str, Any]] = []
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError('Refusing to replace an existing event log')
        path.touch()

    def emit(self, origin: str, kind: str, **data: Any) -> dict[str, Any]:
        event = {'sequence': len(self.events) + 1, 'time': now(), 'origin': origin, 'kind': kind, **data}
        self.events.append(event)
        with self.path.open('a', encoding='utf-8') as out:
            out.write(canonical(event) + '\n')
        return event
