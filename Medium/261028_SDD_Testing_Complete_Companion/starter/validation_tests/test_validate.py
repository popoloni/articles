"""Reader-runner failure/coverage tests, separate from the published 81-test suite."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate


def unit_report(count=2):
    return {'status': 'PASS', 'tests_run': count, 'passed': count, 'subtests_passed': 0,
            'failures': 0, 'errors': 0, 'skipped': 0,
            'test_cases': [{'id': f'test_{i}', 'status': 'PASS'} for i in range(count)]}


def matrix_report():
    cells, _ = validate.load_manifest(validate.ROOT / 'scenarios.json')
    ids = [cell['id'] for cell in cells]
    return {'status': 'PASS', 'reference_matrix_complete': True, 'selected_complete': True,
            'planned_cells': len(ids), 'completed_cells': len(ids), 'passed_cells': len(ids),
            'assertion_count': 78, 'interrupted': False,
            'cells': [{'id': cell_id, 'status': 'PASS'} for cell_id in ids],
            'coverage': {'required': ids, 'passed': ids, 'missing': [], 'duplicates': [],
                         'unexpected': [], 'nonpassing': [], 'full_matrix_not_selected': []}}


class ReportTests(unittest.TestCase):
    def test_nonempty_units_can_grow_without_fixed_count(self):
        self.assertEqual(validate.report_issues('unit', unit_report(82)), [])

    def test_empty_suite_is_not_success(self):
        self.assertTrue(validate.report_issues('unit', unit_report(0)))

    def test_duplicate_unit_record_is_rejected(self):
        report = unit_report()
        report['test_cases'][1] = report['test_cases'][0]
        self.assertTrue(validate.report_issues('unit', report))

    def test_skip_is_rejected_even_if_summary_claims_pass(self):
        report = unit_report()
        report['skipped'] = 1
        self.assertTrue(validate.report_issues('unit', report))

    def test_complete_matrix_is_accepted(self):
        self.assertEqual(validate.report_issues('matrix', matrix_report()), [])

    def test_subset_cannot_claim_full_matrix(self):
        report = matrix_report()
        report['reference_matrix_complete'] = False
        self.assertTrue(validate.report_issues('matrix', report))

    def test_duplicate_cell_cannot_replace_a_required_repetition(self):
        report = matrix_report()
        report['cells'][-1] = report['cells'][0]
        self.assertTrue(validate.report_issues('matrix', report))

    def test_crashing_mutation_is_not_detection(self):
        report = {'status': 'PASS', 'mutations': 6, 'detected': 6,
                  'results': [{'mutation': name, 'detected': True, 'observed_status': 'FAIL',
                               'failed_assertions': ['contract']} for name in validate.MUTATIONS]}
        self.assertEqual(validate.report_issues('mutations', report), [])
        report['results'][0]['observed_status'] = 'ERROR'
        self.assertTrue(validate.report_issues('mutations', report))

    def test_prose_only_live_pass_is_rejected(self):
        report = {'status': 'PASS', 'evidence_kind': 'live-ollama-reference-gateway',
                  'native_cli_observed': False, 'checks': []}
        self.assertTrue(validate.report_issues('ollama', report))


class OrchestrationTests(unittest.TestCase):
    def run_main(self, directory, extra=(), outcomes=None):
        def stage_result(stage, arguments, destination):
            return {'stage': stage, 'status': (outcomes or {}).get(stage, 'PASS')}
        with patch.object(validate, 'run_stage', side_effect=stage_result) as stage, redirect_stdout(io.StringIO()):
            status = validate.main(['--output', str(directory), *extra])
        return status, stage

    def test_default_never_invokes_live_step_and_reports_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, stage = self.run_main(temporary)
            report = json.loads(next(Path(temporary).glob('*/summary.json')).read_text())
            self.assertEqual(status, 0)
            self.assertEqual(stage.call_count, 3)
            self.assertEqual(report['live_status'], 'NOT_REQUESTED')
            self.assertEqual(report['scope'], 'offline-reference-only')
            self.assertFalse(report['private_native_matrix_reproduced'])

    def test_requested_blocked_live_step_makes_command_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, stage = self.run_main(temporary, ['--ollama-model', 'exact:tag', '--expected-digest', 'a' * 64],
                                          {'ollama': 'BLOCKED'})
            report = json.loads(next(Path(temporary).glob('*/summary.json')).read_text())
            self.assertEqual(status, 1)
            self.assertEqual(stage.call_count, 4)
            self.assertTrue(report['offline_complete'])
            self.assertEqual(report['live_status'], 'BLOCKED')
            self.assertEqual(report['status'], 'FAIL')

    def test_failed_unit_stage_does_not_discard_later_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, stage = self.run_main(temporary, outcomes={'unit': 'FAIL'})
            self.assertEqual(status, 1)
            self.assertEqual(stage.call_count, 3)

    def test_repeated_runs_keep_fresh_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.run_main(temporary)
            first = next(Path(temporary).glob('*/summary.json'))
            before = first.read_bytes()
            self.run_main(temporary)
            self.assertEqual(len(list(Path(temporary).glob('*/summary.json'))), 2)
            self.assertEqual(first.read_bytes(), before)

    def test_interruption_keeps_summary_and_marks_remaining_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, stage = self.run_main(temporary, outcomes={'unit': 'INTERRUPTED'})
            report = json.loads(next(Path(temporary).glob('*/summary.json')).read_text())
            self.assertEqual(status, 1)
            self.assertEqual(stage.call_count, 1)
            self.assertEqual(report['steps'][1]['status'], 'NOT_RUN')

    def test_model_requires_full_identity_before_running(self):
        with patch.object(validate, 'run_stage') as stage, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                validate.main(['--ollama-model', 'exact:tag'])
        self.assertEqual(raised.exception.code, 2)
        stage.assert_not_called()

    def test_empty_live_identity_is_not_silently_offline(self):
        with patch.object(validate, 'run_stage') as stage, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                validate.main(['--ollama-model', '', '--expected-digest', ''])
        self.assertEqual(raised.exception.code, 2)
        stage.assert_not_called()

    def test_missing_child_report_preserves_error_and_log(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(validate.subprocess, 'run') as process:
            process.return_value.returncode = 0
            result = validate.run_stage('unit', ['not-executed.py'], Path(temporary))
            self.assertEqual(result['status'], 'ERROR')
            self.assertTrue((Path(temporary) / 'unit/console.log').is_file())
            self.assertTrue((Path(temporary) / 'unit/runner-error.log').is_file())

    def test_nonzero_child_exit_cannot_be_overridden_by_pass_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            def child(command, **kwargs):
                output = Path(command[-1])
                (output / 'unit-tests.json').write_text(json.dumps(unit_report()))
                (output / 'unit-tests.xml').write_text('<testsuite/>')
                (output / 'unit-tests.log').write_text('unit log')
                return validate.subprocess.CompletedProcess(command, 7)
            with patch.object(validate.subprocess, 'run', side_effect=child):
                result = validate.run_stage('unit', ['not-executed.py'], Path(temporary))
            self.assertEqual(result['status'], 'FAIL')
            self.assertIn('child command exited with 7', result['issues'])


if __name__ == '__main__':
    unittest.main()
