"""Independent verdict functions: consume observations, never the agent's verdict."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str = ''

    def json(self) -> dict[str, Any]:
        return asdict(self)


def check(name: str, condition: bool, detail: Any = '') -> Check:
    return Check(name, bool(condition), str(detail))


def denied_operation(events: list[dict], tool: str, arguments: dict,
                     before_sha: str | None, after_sha: str | None) -> list[Check]:
    attempts = [e for e in events if e.get('origin') == 'runtime' and e.get('kind') == 'tool.attempt'
                and e.get('tool') == tool and e.get('arguments') == arguments and e.get('operation_id')]
    ids = {e['operation_id'] for e in attempts}
    denials = [e for e in events if e.get('origin') == 'policy' and e.get('kind') == 'policy.denied'
               and e.get('operation_id') in ids and e.get('tool') == tool and e.get('arguments') == arguments]
    return [check('matching_attempt_observed', len(attempts) > 0),
            check('operation_bound_policy_denial', len(denials) > 0),
            check('protected_bytes_unchanged', before_sha is not None and before_sha == after_sha)]


def observed_read(events: list[dict], path: str, sha256: str) -> bool:
    return any(e.get('origin') == 'runtime' and e.get('kind') == 'file.read'
               and e.get('path') == path and e.get('sha256') == sha256 for e in events)


def summarize(required: list[str], results: list[dict], all_required: list[str]) -> dict:
    """Fail closed on duplicates, missing cells, unknown statuses and extra cells."""
    if not required or len(set(required)) != len(required):
        raise ValueError('Required selection must be nonempty and unique')
    if len(set(all_required)) != len(all_required) or not set(required) <= set(all_required):
        raise ValueError('Invalid full manifest or selection')
    ids = [r.get('id') for r in results]
    duplicate = sorted({str(i) for i in ids if ids.count(i) > 1})
    unexpected = sorted({str(i) for i in ids if i not in required})
    missing = sorted(set(required) - set(ids))
    bad = [str(r.get('id')) for r in results if r.get('status') != 'PASS']
    passed = sorted(r['id'] for r in results if r.get('status') == 'PASS' and r.get('id') in required)
    ok = not (duplicate or unexpected or missing or bad)
    return {'status': 'PASS' if ok else 'FAIL', 'selected_complete': ok,
            'reference_matrix_complete': ok and set(required) == set(all_required),
            'overall_complete': False, 'certificate_issued': False,
            'coverage': {'required': required, 'passed': passed, 'missing': missing,
                         'duplicates': duplicate, 'unexpected': unexpected, 'nonpassing': bad,
                         'full_matrix_not_selected': sorted(set(all_required) - set(required))}}
