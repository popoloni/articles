#!/usr/bin/env python3
"""Audit the supplied historical SUMMARY; does not authenticate unavailable raw runs."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def audit(path: Path) -> dict:
    raw = path.read_bytes()
    record = json.loads(raw)
    matrix = record['scenario_matrix']
    cells = matrix['cells']
    expected = {f'deterministic/claude/{i}' for i in (1, 2, 3)}
    families = {'requirements-review': 1, 'native-agent': 1, 'native-skill': 1, 'native-instructions': 1,
                'optional-present': 1, 'optional-absent': 3, 'denied-write': 3, 'denied-shell': 3,
                'injection': 3, 'mcp-allowed': 1, 'mcp-denied': 3, 'session-resume': 1}
    expected |= {f'{name}/{target}/{i}' for name, count in families.items() for target in ('claude', 'copilot') for i in range(1, count + 1)}
    ids = [entry['cell']['id'] for entry in cells]
    counts = Counter('structural' if entry['cell']['offline'] else entry['cell']['target'] for entry in cells)
    checks = []
    def check(name, condition, detail=''):
        checks.append({'name': name, 'passed': bool(condition), 'detail': detail})
    check('47_required_execution_cells', matrix['required_local_cells'] == 47 and len(cells) == 47)
    check('unique_cell_ids', len(set(ids)) == len(ids))
    check('exact_declared_scenario_expansion', set(ids) == expected)
    check('all_reported_cell_statuses_pass', all(c['status'] == 'PASS' for c in cells))
    check('44_live_plus_3_structural', dict(counts) == {'structural': 3, 'claude': 22, 'copilot': 22})
    check('per_cell_hash_metadata_well_formed', all(re.fullmatch('[0-9a-f]{64}', c['sha256']) for c in cells))
    check('coverage_required_matches_cells', set(matrix['coverage']['required']) == expected)
    check('coverage_passed_matches_cells', set(matrix['coverage']['passed']) == expected)
    check('no_missing_or_unexpected_cells_reported', not matrix['coverage']['missing'] and not matrix['coverage']['unexpected'])
    check('local_pass_does_not_issue_certificate', matrix['status'] == 'PASS' and matrix['local_matrix_complete'] is True and matrix['overall_complete'] is False and matrix['certificate_issued'] is False)
    foundation = record['foundation_pilot']
    regression = foundation['final_regression']
    check('later_regression_counts', regression['passed'] == 1197 and regression['subtests_passed'] == 111)
    check('skips_and_failures_visible', regression['skipped_powershell'] == 20 and regression['failures'] == 0 and regression['warnings'] == 1)
    check('five_focused_foundation_cases', len(foundation['focused_cases']) == 5 and all(c['status'] == 'PASS' for c in foundation['focused_cases']))
    check('foundation_acceptance_not_claimed', foundation['overall_complete'] is False and foundation['certificate_issued'] is False and foundation['phase_g_ready'] is False)
    check('failed_matrix_attempts_preserved_in_summary', any(r['status'] == 'FAIL' for r in matrix['reports']))
    check('aggregate_failure_despite_green_cells_preserved', any(r['status'] == 'FAIL' and r.get('passed_cells') == 47 for r in matrix['reports']))
    start = datetime.fromisoformat(matrix['started_at'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(matrix['finished_at'].replace('Z', '+00:00'))
    return {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
            'evidence_kind': 'historical-summary-consistency-audit',
            'source': 'evidence/original/runtime-lab-record.json', 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'checks': checks, 'matrix_cell_counts': dict(counts), 'recorded_matrix_duration_seconds': (end - start).total_seconds(),
            'original_runtime_reexecuted': False, 'raw_per_cell_payloads_verified': False, 'certificate_issued': False,
            'limitation': 'Checks internal consistency and preserved metadata only. Missing raw transcripts, per-cell reports, container archives, weights and private source cannot be authenticated or reconstructed from hashes.'}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', type=Path, default=ROOT / 'evidence/original/runtime-lab-record.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.record)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}', 'original_runtime_reexecuted': False}
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            parser.error('Choose a fresh output path; historical audit output is never overwritten')
        args.output.write_text(text, encoding='utf-8')
    print(text)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
