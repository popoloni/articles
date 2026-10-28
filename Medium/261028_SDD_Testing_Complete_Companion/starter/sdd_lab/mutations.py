"""Six deliberately broken implementations; a crash does not count as detection."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from .common import Recorder, write_json, now
from .core import Gate, GateResult, PermissionGateway, Publisher, ToolGateway
from .runner import run_cell, source_identity


def run_mutations(output: Path) -> tuple[dict, Path]:
    destination = output / ('mutations-' + uuid4().hex[:10])
    destination.mkdir(parents=True, exist_ok=False)
    original_write = PermissionGateway.write_file
    original_emit = Recorder.emit

    def allow_protected(self, relative, content):
        old = self.writable.copy()
        try:
            self.writable.add(relative)
            return original_write(self, relative, content)
        finally:
            self.writable = old

    def silence_denial(self, origin, kind, **data):
        if kind == 'policy.denied':
            return {'origin': origin, 'kind': kind, **data}
        return original_emit(self, origin, kind, **data)

    def accept_every_review(self, spec, artifact, review, builder_session, checkpoint):
        write_json(checkpoint, {'incorrectly_accepted': True})
        return GateResult(True, ())

    def omit_read_evidence(self, relative):
        from .common import safe_path
        return safe_path(self.root, relative).read_text(encoding='utf-8')

    cases = [
        ('allow-protected-write', 'denied-write', PermissionGateway, 'write_file', allow_protected),
        ('silence-policy-denial', 'denied-write', Recorder, 'emit', silence_denial),
        ('accept-stale-and-self-review', 'review-freshness', Gate, 'evaluate', accept_every_review),
        ('rollback-does-nothing', 'greenfield-rollback', Publisher, 'rollback', lambda self, transaction: False),
        ('omit-exposure-evidence', 'injection-exposure', PermissionGateway, 'read_file', omit_read_evidence),
        ('bypass-tool-policy', 'tool-denied', ToolGateway, 'call', lambda self, name: self.service.invoke(name)),
    ]
    results = []
    for name, scenario, cls, method, replacement in cases:
        cell = {'id': name, 'scenario': scenario, 'repetition': 1}
        with patch.object(cls, method, replacement):
            report = run_cell(cell, destination / name)
        detected = report['status'] == 'FAIL' and any(not c['passed'] for c in report.get('checks', []))
        results.append({'mutation': name, 'scenario': scenario, 'detected': detected,
                        'observed_status': report['status'], 'report': f'{name}/report.json',
                        'failed_assertions': [c['name'] for c in report.get('checks', []) if not c['passed']]})
        print(f"{'DETECTED' if detected else 'NOT DETECTED'} {name}", flush=True)
    summary = {'schema_version': 1, 'created_at': now(), 'evidence_kind': 'executed-deliberate-mutations',
               'status': 'PASS' if all(r['detected'] for r in results) else 'FAIL',
               'mutations': len(results), 'detected': sum(r['detected'] for r in results), 'results': results,
               'source_identity': source_identity(), 'certificate_issued': False,
               'interpretation': 'PASS means all six selected defects caused assertion failures, not crashes; not a general mutation coverage score.'}
    write_json(destination / 'summary.json', summary)
    return summary, destination
