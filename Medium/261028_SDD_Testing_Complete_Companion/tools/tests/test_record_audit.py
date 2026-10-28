"""Negative tests for the historical-summary auditor; no original runtime calls."""
from pathlib import Path
import sys
import tempfile
import unittest
import json
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_original_record import audit


class RecordAuditTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'evidence/original/runtime-lab-record.json').read_text())
        self.tmp = tempfile.TemporaryDirectory(prefix='sdd-audit-')
        self.path = Path(self.tmp.name) / 'record.json'

    def tearDown(self):
        self.tmp.cleanup()

    def run_audit(self):
        self.path.write_text(json.dumps(self.record))
        return audit(self.path)

    def test_original_summary_is_consistent(self):
        result = self.run_audit()
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['original_runtime_reexecuted'])
        self.assertFalse(result['raw_per_cell_payloads_verified'])

    def test_duplicate_cell_detected(self):
        cells = self.record['scenario_matrix']['cells']
        cells[-1] = cells[0]
        self.assertEqual(self.run_audit()['status'], 'FAIL')

    def test_nonpassing_cell_detected(self):
        self.record['scenario_matrix']['cells'][0]['status'] = 'BLOCKED'
        self.assertEqual(self.run_audit()['status'], 'FAIL')

    def test_missing_cell_detected(self):
        self.record['scenario_matrix']['cells'].pop()
        self.assertEqual(self.run_audit()['status'], 'FAIL')

    def test_changed_regression_count_detected(self):
        self.record['foundation_pilot']['final_regression']['passed'] = 9999
        self.assertEqual(self.run_audit()['status'], 'FAIL')

    def test_unjustified_certificate_detected(self):
        self.record['scenario_matrix']['certificate_issued'] = True
        self.assertEqual(self.run_audit()['status'], 'FAIL')
