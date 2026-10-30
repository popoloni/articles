#!/usr/bin/env python3
"""Run the public companion's complete offline validation, with an opt-in live probe."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from sdd_lab.common import digest, environment, now, write_json
from sdd_lab.runner import load_manifest, source_identity
MUTATIONS = {'allow-protected-write', 'silence-policy-denial', 'accept-stale-and-self-review',
             'rollback-does-nothing', 'omit-exposure-evidence', 'bypass-tool-policy'}


def report_issues(stage: str, report: dict) -> list[str]:
    """Require complete recorded coverage; a subset or a crash cannot pass."""
    issues = []

    def require(ok: bool, message: str) -> None:
        if not ok:
            issues.append(message)

    require(report.get('status') == 'PASS', f"reported status is {report.get('status')!r}")
    if stage == 'unit':
        count = report.get('tests_run')
        require(type(count) is int and count > 0 and report.get('passed') == count, 'expected a nonempty passing unit suite')
        require(type(report.get('subtests_passed')) is int and report['subtests_passed'] >= 0,
                'missing or invalid subtest count')
        require(all(report.get(key) == 0 for key in ('failures', 'errors', 'skipped')), 'unit failures, errors or skips')
        records = report.get('test_cases', [])
        require(len(records) == count and len({r.get('id') for r in records}) == count
                and all(r.get('status') == 'PASS' for r in records), 'incomplete or nonpassing unit records')
    elif stage == 'matrix':
        manifest_cells, _ = load_manifest(ROOT / 'scenarios.json')
        cell_ids = {cell['id'] for cell in manifest_cells}
        require(report.get('reference_matrix_complete') is True and report.get('selected_complete') is True,
                'complete reference matrix was not observed')
        require(all(report.get(key) == len(cell_ids) for key in ('planned_cells', 'completed_cells', 'passed_cells')),
                f'expected {len(cell_ids)} complete passing cells')
        require(type(report.get('assertion_count')) is int and report['assertion_count'] > 0,
                'expected nonempty matrix assertions')
        cells = report.get('cells', [])
        require(len(cells) == len(cell_ids) and {c.get('id') for c in cells} == cell_ids
                and all(c.get('status') == 'PASS' for c in cells), 'wrong, missing, duplicate or nonpassing cells')
        coverage = report.get('coverage', {})
        require(all(len(coverage.get(key, [])) == len(cell_ids) and set(coverage.get(key, [])) == cell_ids
                    for key in ('required', 'passed')),
                'matrix coverage does not match the published manifest')
        require(all(coverage.get(key) == [] for key in
                    ('missing', 'duplicates', 'unexpected', 'nonpassing', 'full_matrix_not_selected')),
                'matrix coverage has gaps or unexpected results')
        require(report.get('interrupted') is False, 'matrix was interrupted')
    elif stage == 'mutations':
        require(report.get('mutations') == 6 and report.get('detected') == 6, 'expected six detected mutations')
        records = report.get('results', [])
        require(len(records) == 6 and {r.get('mutation') for r in records} == MUTATIONS,
                'wrong, missing or duplicate mutations')
        require(all(r.get('detected') is True and r.get('observed_status') == 'FAIL'
                    and bool(r.get('failed_assertions')) for r in records),
                'every mutation must fail an assertion; errors do not count')
    elif stage == 'ollama':
        require(report.get('evidence_kind') == 'live-ollama-reference-gateway', 'wrong live evidence kind')
        checks = report.get('checks', [])
        names = {'matching_attempt_observed', 'operation_bound_policy_denial', 'protected_bytes_unchanged'}
        require(len(checks) == 3 and {c.get('name') for c in checks} == names
                and all(c.get('passed') is True for c in checks), 'missing or failed gateway assertions')
        require(report.get('native_cli_observed') is False, 'unexpected native-CLI claim')
    else:
        raise ValueError(f'Unknown stage: {stage}')
    return issues


def run_stage(stage: str, arguments: list[str], destination: Path) -> dict:
    directory = destination / stage
    directory.mkdir()
    command = [sys.executable, *arguments, '--output', str(directory)]
    result = {'stage': stage, 'status': 'ERROR', 'command': command,
              'started_at': now(), 'console_log': f'{stage}/console.log'}
    started = time.perf_counter()
    try:
        with (directory / 'console.log').open('x', encoding='utf-8') as stream:
            process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, check=False)
        result['exit_code'] = process.returncode
        reports = ([directory / 'unit-tests.json'] if stage == 'unit'
                   else list(directory.glob('*/summary.json')))
        if len(reports) != 1 or not reports[0].is_file():
            raise ValueError('Expected exactly one freshly written report; see console.log')
        path = reports[0]
        result['report'] = path.relative_to(destination).as_posix()
        report = json.loads(path.read_text(encoding='utf-8'))
        result['reported_status'] = report.get('status')
        issues = report_issues(stage, report)
        if process.returncode != 0:
            issues.append(f'child command exited with {process.returncode}')
        required = ['unit-tests.log', 'unit-tests.xml'] if stage == 'unit' else ['junit.xml'] if stage == 'matrix' else []
        issues.extend(f'missing retained report: {name}' for name in required if not (path.parent / name).is_file())
        result.update(status=('BLOCKED' if report.get('status') == 'BLOCKED' else 'FAIL') if issues else 'PASS',
                      issues=issues, report_sha256=digest(path.read_bytes()))
    except KeyboardInterrupt:
        result.update(status='INTERRUPTED', issues=['Interrupted by the reader; remaining stages were not run'])
    except Exception as exc:
        result.update(status='ERROR', issues=[f'{type(exc).__name__}: {exc}'])
        (directory / 'runner-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    result.update(finished_at=now(), elapsed_seconds=round(time.perf_counter() - started, 6))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('validation-runs'), help='Parent of a fresh evidence directory')
    parser.add_argument('--ollama-model', help='Opt in to a live request using this exact installed model name')
    parser.add_argument('--expected-digest', help='Required with --ollama-model; full lowercase SHA-256')
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434', help='Ollama HTTP loopback base URL')
    parser.add_argument('--timeout', type=float, default=120.0, help='Live HTTP timeout, >0 and <=120 seconds')
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error('Python 3.11 or later is required')
    if (args.ollama_model is None) != (args.expected_digest is None):
        parser.error('--ollama-model and --expected-digest must be supplied together')
    if args.ollama_model is not None and not args.ollama_model:
        parser.error('--ollama-model must be a nonempty exact installed model name')
    if not args.ollama_model and (args.endpoint != 'http://127.0.0.1:11434' or args.timeout != 120.0):
        parser.error('--endpoint and --timeout require --ollama-model and --expected-digest')
    # Validate requested identities before starting any work. The import itself makes no network call.
    if args.ollama_model:
        import math
        from sdd_lab.live import normal_digest, validate_endpoint
        try:
            normal_digest(args.expected_digest)
            validate_endpoint(args.endpoint)
            if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
                raise ValueError('Timeout must be greater than zero and at most 120 seconds')
        except ValueError as exc:
            parser.error(str(exc))
    destination = args.output.resolve() / ('validation-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + uuid4().hex[:10])
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        print(f'Cannot create fresh evidence directory: {exc}', file=sys.stderr)
        return 2
    jobs = [('unit', [str(ROOT / 'tools/run_unit_tests.py')]),
            ('matrix', [str(ROOT / 'lab.py'), 'run']),
            ('mutations', [str(ROOT / 'lab.py'), 'mutations'])]
    if args.ollama_model:
        jobs.append(('ollama', [str(ROOT / 'lab.py'), 'ollama', '--model', args.ollama_model,
                               '--expected-digest', args.expected_digest, '--endpoint', args.endpoint,
                               '--timeout', str(args.timeout)]))
    summary = {'schema_version': 1, 'created_at': now(), 'status': 'RUNNING',
               'evidence_kind': 'public-companion-validation', 'environment': environment(),
               'scope': 'offline-reference-and-live-gateway' if args.ollama_model else 'offline-reference-only',
               'native_cli_observed': False, 'certificate_issued': False,
               'private_native_matrix_reproduced': False, 'source_identity': source_identity(),
               'runner_sha256': digest(Path(__file__).read_bytes()),
               'unit_reporter_sha256': digest((ROOT / 'tools/run_unit_tests.py').read_bytes()),
               'live_requested': bool(args.ollama_model),
               'steps': [{'stage': stage, 'status': 'PENDING'} for stage, _ in jobs]}
    if not args.ollama_model:
        summary['steps'].append({'stage': 'ollama', 'status': 'NOT_REQUESTED',
                                 'reason': 'Offline run; no live model invocation requested or performed'})
    if args.ollama_model:
        summary['live_request'] = {'model': args.ollama_model, 'expected_digest': args.expected_digest,
                                   'endpoint': args.endpoint, 'timeout_seconds': args.timeout}
    print(f'Evidence: {destination}', flush=True)
    write_json(destination / 'summary.json', summary)
    for index, (stage, arguments) in enumerate(jobs):
        print(f'Running {stage} ...', flush=True)
        result = run_stage(stage, arguments, destination)
        summary['steps'][index] = result
        print(f"{stage}: {result['status']}", flush=True)
        write_json(destination / 'summary.json', summary)
        if result['status'] == 'INTERRUPTED':
            for remaining in summary['steps'][index + 1:]:
                if remaining['status'] == 'PENDING':
                    remaining.update(status='NOT_RUN', reason='Earlier stage interrupted')
            break
    offline = summary['steps'][:3]
    summary['offline_complete'] = all(s['status'] == 'PASS' for s in offline)
    summary['live_status'] = summary['steps'][3]['status']
    summary['status'] = 'PASS' if all(s['status'] == 'PASS' for s in summary['steps'][:len(jobs)]) else 'FAIL'
    summary['finished_at'] = now()
    write_json(destination / 'summary.json', summary)
    print(f"{summary['status']} ({summary['scope']}); live: {summary['live_status']}")
    print(f"Read: {destination / 'summary.json'}")
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
