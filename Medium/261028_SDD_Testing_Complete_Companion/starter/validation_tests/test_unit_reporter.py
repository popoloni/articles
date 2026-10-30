"""Fixture failures must remain inspectable without corrupting completed tests."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('companion_unit_reporter', ROOT / 'tools/run_unit_tests.py')
reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporter)


class UnitReporterTests(unittest.TestCase):
    def report_fixture(self, kind, outcome, *, preceding_success=False, teardown=False):
        module = ModuleType('reporter_fixture_subject')
        previous = ModuleType('reporter_fixture_previous')
        marker = f'{kind} fixture {outcome} retained'

        def fixture(*unused):
            if outcome == 'skip':
                raise unittest.SkipTest(marker)
            raise RuntimeError(marker)

        case_type = type('Subject', (unittest.TestCase,), {
            '__module__': module.__name__, 'test_body': lambda self: None})
        prefix = 'tearDown' if teardown else 'setUp'
        if kind == 'class':
            setattr(case_type, prefix + 'Class', classmethod(fixture))
        else:
            setattr(module, prefix + 'Module', fixture)
        tests = []
        if preceding_success:
            success_type = type('Previous', (unittest.TestCase,), {
                '__module__': previous.__name__, 'test_ok': lambda self: None})
            tests.append(success_type('test_ok'))
        tests.append(case_type('test_body'))
        suite = unittest.TestSuite(tests)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with patch.dict(sys.modules, {module.__name__: module, previous.__name__: previous}), \
                    patch.object(unittest.defaultTestLoader, 'discover', return_value=suite), \
                    patch.object(sys, 'argv', ['run_unit_tests.py', '--output', str(output)]), \
                    redirect_stdout(io.StringIO()):
                status = reporter.main()
            report = json.loads((output / 'unit-tests.json').read_text(encoding='utf-8'))
            log = (output / 'unit-tests.log').read_text(encoding='utf-8')
            xml = ET.parse(output / 'unit-tests.xml').getroot()
        self.assertEqual(status, 1)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['errors'], int(outcome == 'error'))
        self.assertEqual(report['skipped'], int(outcome == 'skip'))
        self.assertIn(marker, log)
        self.assertEqual(len(report['fixture_outcomes']), 1)
        fixture_record = report['fixture_outcomes'][0]
        self.assertEqual(fixture_record['status'], 'ERROR' if outcome == 'error' else 'SKIP')
        self.assertIn(marker, '\n'.join(fixture_record['details']))
        if outcome == 'error':
            self.assertIn('RuntimeError', '\n'.join(fixture_record['details']))
            self.assertIn('Traceback', log)
        self.assertEqual(int(xml.attrib['tests']), len(xml.findall('testcase')))
        element = xml.find('testcase/error' if outcome == 'error' else 'testcase/skipped')
        self.assertIsNotNone(element)
        self.assertIn(marker, element.text)
        return report

    def test_class_and_module_setup_errors_retain_primary_tracebacks(self):
        for kind in ('class', 'module'):
            with self.subTest(kind=kind):
                report = self.report_fixture(kind, 'error')
                self.assertEqual(report['tests_run'], 0)
                self.assertEqual(report['test_cases'], [])

    def test_class_and_module_setup_skips_fail_closed(self):
        for kind in ('class', 'module'):
            with self.subTest(kind=kind):
                report = self.report_fixture(kind, 'skip')
                self.assertEqual(report['tests_run'], 0)
                self.assertEqual(report['test_cases'], [])

    def test_fixture_error_or_skip_does_not_mutate_preceding_success(self):
        for kind in ('class', 'module'):
            for outcome in ('error', 'skip'):
                with self.subTest(kind=kind, outcome=outcome):
                    report = self.report_fixture(kind, outcome, preceding_success=True)
                    self.assertEqual(report['tests_run'], 1)
                    self.assertEqual(report['passed'], 1)
                    self.assertEqual(len(report['test_cases']), 1)
                    self.assertEqual(report['test_cases'][0]['status'], 'PASS')
                    self.assertEqual(report['test_cases'][0]['details'], [])

    def test_class_and_module_teardown_outcomes_keep_completed_tests(self):
        for kind in ('class', 'module'):
            for outcome in ('error', 'skip'):
                with self.subTest(kind=kind, outcome=outcome):
                    report = self.report_fixture(kind, outcome, teardown=True)
                    self.assertEqual(report['tests_run'], 1)
                    self.assertEqual(report['passed'], 1)
                    self.assertEqual(report['test_cases'][0]['status'], 'PASS')
                    self.assertEqual(report['test_cases'][0]['details'], [])

    def test_current_is_cleared_after_a_completed_test(self):
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=reporter.EvidenceResult).run(suite)
        self.assertIsNone(result.current)
        self.assertEqual(result.fixture_outcomes, [])
        self.assertEqual(result.records[0]['status'], 'PASS')

    def test_unexpected_runner_exception_preserves_collected_log(self):
        def interrupted_run(runner, suite):
            runner.stream.write('primary diagnostic already collected\n')
            raise RuntimeError('unexpected runner failure')

        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(unittest.defaultTestLoader, 'discover', return_value=unittest.TestSuite()), \
                    patch.object(unittest.TextTestRunner, 'run', interrupted_run), \
                    patch.object(sys, 'argv', ['run_unit_tests.py', '--output', temporary]):
                with self.assertRaisesRegex(RuntimeError, 'unexpected runner failure'):
                    reporter.main()
            self.assertIn('primary diagnostic already collected',
                          (Path(temporary) / 'unit-tests.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
