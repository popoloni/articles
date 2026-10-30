#!/usr/bin/env python3
"""Standard-library test reporting: JSON, JUnit XML and full readable log."""
from __future__ import annotations
import argparse
import io
from pathlib import Path
import sys
import time
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sdd_lab.common import digest, environment, now, write_json
from sdd_lab.runner import source_identity


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self.fixture_outcomes = []
        self.subtests_passed = 0
        self.current = None

    def startTest(self, test):
        super().startTest(test)
        self.current = {'id': test.id(), 'status': 'PASS', 'details': [], '_started': time.perf_counter()}

    def record_outcome(self, test, status, detail):
        # unittest reports class/module fixture outcomes without startTest/stopTest.
        # Keep those separate from executed test methods and their testsRun count.
        if self.current is None:
            self.fixture_outcomes.append({'id': test.id(), 'status': status,
                                          'details': [detail], 'elapsed_seconds': 0.0})
            return
        priority = {'PASS': 0, 'SKIP': 1, 'FAIL': 2, 'ERROR': 3}
        if priority[status] > priority[self.current['status']]:
            self.current['status'] = status
        self.current['details'].append(detail)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record_outcome(test, 'FAIL', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record_outcome(test, 'ERROR', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record_outcome(test, 'SKIP', reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            self.subtests_passed += 1
        else:
            status = 'FAIL' if issubclass(err[0], test.failureException) else 'ERROR'
            self.record_outcome(test, status, subtest.id() + '\n' + self._exc_info_to_string(err, test))

    def stopTest(self, test):
        self.current['elapsed_seconds'] = round(time.perf_counter() - self.current.pop('_started'), 6)
        self.records.append(self.current)
        self.current = None
        super().stopTest(test)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('test-results'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ('unit-tests.log', 'unit-tests.json', 'unit-tests.xml'):
        if (args.output / name).exists():
            parser.error('Refusing to overwrite retained evidence; choose a fresh output directory')
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult)
    start = time.perf_counter()
    try:
        result = runner.run(suite)
    finally:
        text = stream.getvalue()
        (args.output / 'unit-tests.log').write_text(text, encoding='utf-8')
    good = result.wasSuccessful() and result.testsRun > 0 and not result.skipped and not result.expectedFailures
    report = {'schema_version': 1, 'created_at': now(), 'status': 'PASS' if good else 'FAIL',
              'evidence_kind': 'executed-reference-unit-tests', 'environment': environment(),
              'tests_run': result.testsRun, 'passed': sum(r['status'] == 'PASS' for r in result.records),
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'subtests_passed': result.subtests_passed, 'elapsed_seconds': round(time.perf_counter() - start, 6),
              'test_cases': result.records, 'fixture_outcomes': result.fixture_outcomes,
              'source_identity': source_identity(),
              'test_source_sha256': {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted((ROOT / 'tests').glob('*.py'))},
              'log_sha256': digest(text), 'native_cli_observed': False, 'real_model_invocations': 0}
    write_json(args.output / 'unit-tests.json', report)
    # JUnit has no separate fixture-outcome element; retain them as synthetic cases.
    junit_records = result.records + result.fixture_outcomes
    tree = ET.Element('testsuite', name='sdd-reference-unit-tests', tests=str(len(junit_records)),
                      failures=str(len(result.failures)), errors=str(len(result.errors)), skipped=str(len(result.skipped)))
    for rec in junit_records:
        case = ET.SubElement(tree, 'testcase', name=rec['id'], time=str(rec['elapsed_seconds']))
        if rec['status'] != 'PASS':
            child = ET.SubElement(case, {'FAIL': 'failure', 'ERROR': 'error', 'SKIP': 'skipped'}[rec['status']])
            child.text = '\n'.join(rec['details'])
    ET.ElementTree(tree).write(args.output / 'unit-tests.xml', encoding='utf-8', xml_declaration=True)
    print(text)
    print(f"{report['status']}: {report['passed']}/{report['tests_run']} tests; {report['subtests_passed']} successful subtests")
    return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
