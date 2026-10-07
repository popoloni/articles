"""Model-free analysis tests; never contact a service or import inference packages."""
import unittest
import json
import tempfile
import zipfile
from pathlib import Path
import hashlib
import re
import statistics
from analyze_logs import classify,read_zip,profile_id,LABELS,clean_private

HERE=Path(__file__).resolve().parent
ROWS=json.loads((HERE/'request-metrics.json').read_text())
AUDIT=json.loads((HERE/'audit.json').read_text())
SUM=json.loads((HERE/'profile-summary.json').read_text())

def row(content,case='json_contract',finish='stop'):
 return {'case':case,'response':{'choices':[{'finish_reason':finish,'message':{'role':'assistant','content':content}}]}}

class Contracts(unittest.TestCase):
 def test_valid_json(self):self.assertEqual(classify(row('{"owner":"Mira","order_id":"ORD-27A9","amount_eur":2400}'))[0],'pass')
 def test_numeric_string_fails(self):self.assertEqual(classify(row('{"owner":"Mira","order_id":"ORD-27A9","amount_eur":"2400"}'))[0],'wrong_content')
 def test_extra_key_fails(self):self.assertEqual(classify(row('{"owner":"Mira","order_id":"ORD-27A9","amount_eur":2400,"extra":1}'))[0],'wrong_content')
 def test_fence_does_not_become_pass(self):self.assertEqual(classify(row('```json\n{"owner":"Mira","order_id":"ORD-27A9","amount_eur":2400}\n```'))[0],'format_only')
 def test_truncation_fails_even_with_good_text(self):self.assertEqual(classify(row('harbor-mint-47','literal_recall','length'))[0],'truncated')
 def test_good_recall(self):self.assertEqual(classify(row(' harbor-mint-47\n','literal_recall'))[0],'pass')
 def test_wrong_recall(self):self.assertEqual(classify(row('288','literal_recall'))[0],'wrong_content')
 def test_nonfinite_json(self):self.assertEqual(classify(row('{"amount_eur":NaN}'))[0],'invalid_json')
 def test_aliases_not_filename_define_omlx_groups(self):
  r={'model':'qwen38-mlx3','base_url':'http://127.0.0.1:8000/v1'}
  self.assertEqual(profile_id(r),'qwen38-omlx3')
  r['base_url']='http://127.0.0.1:8084/v1';self.assertEqual(profile_id(r),'qwen38-mlx3')
 def test_redaction(self):self.assertEqual(clean_private('/Users/alice/LocalAI/model'),'$HOME/LocalAI/model')

class Dataset(unittest.TestCase):
 def test_counts(self):self.assertEqual((len(ROWS),AUDIT['passed'],AUDIT['failed']),(66,53,13))
 def test_groups(self):self.assertEqual((len(SUM),AUDIT['smoke_suites']),(10,11))
 def test_outcomes_match_independent_check(self):self.assertTrue(all(r['passed']==r['reported_passed'] for r in ROWS))
 def test_no_duplicate_responses(self):self.assertEqual(len({r['response_id'] for r in ROWS}),66)
 def test_tasks_and_settings(self):
  self.assertEqual(AUDIT['unique_input_messages_per_case'],{'json_contract':1,'literal_recall':1})
  self.assertEqual({(r['temperature'],r['max_tokens'],r['stream']) for r in ROWS},{(.7,512,False)})
 def test_failed_rows_not_censored(self):
  self.assertEqual(sum(r['outcome']=='truncated' for r in ROWS),5)
  self.assertGreater(max(r['wall_seconds'] for r in ROWS if not r['passed']),55)
 def test_ternary_second_suite_not_deleted(self):self.assertEqual(len([r for r in ROWS if r['profile']=='bonsai-ternary']),12)
 def test_summaries_recalculate(self):
  for s in SUM:
   for case in ('json_contract','literal_recall'):
    rr=[r for r in ROWS if r['profile']==s['profile'] and r['case']==case]
    self.assertAlmostEqual(s[case+'_median_s'],statistics.median(r['wall_seconds'] for r in rr))
 def test_no_invented_mlx_api_decode(self):
  self.assertTrue(all(r['server_decode_tps'] is None for r in ROWS if r['timing_source']=='none'))
 def test_omlx_reasoning(self):self.assertEqual(sum(r['reasoning_characters']>0 for r in ROWS if r['profile']=='qwen38-omlx3'),6)
 def test_provenance_lines(self):self.assertTrue(all(r['source_file'].startswith('logs/') and r['source_line']>=1 for r in ROWS))
 def test_cli_dual_units_kept(self):
  r=next(r for r in json.loads((HERE/'cli-observations.json').read_text()) if r['profile']=='qwen38-tq-diagnostic')
  self.assertEqual((r['peak_memory_printed_gb'],r['second_peak_memory_printed_gb']),(12.798,11.92))
 def test_totals(self):
  self.assertAlmostEqual(sum(r['wall_seconds'] for r in ROWS),AUDIT['total_wall_seconds'])
  self.assertEqual(sum(r['completion_tokens'] for r in ROWS),4621)
 def test_no_home_name_in_public_records(self):self.assertNotIn('/Users/',(HERE/'response-records.jsonl').read_text())

class ArchiveSafety(unittest.TestCase):
 def test_safe_file(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'logs.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('logs/sample.log','hello')
   self.assertEqual(read_zip(p),{'logs/sample.log':b'hello'})
 def test_traversal(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'bad.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('../outside','hello')
   with self.assertRaises(ValueError):read_zip(p)

class Publication(unittest.TestCase):
 def test_all_eight_figures_linked(self):
  text=(HERE.parent/'article.md').read_text()
  refs=re.findall(r'!\[[^\]]*\]\((figures/[^)]+)\)',text)
  self.assertEqual(len(refs),8)
  for ref in refs:self.assertGreater((HERE.parent/ref).stat().st_size,10000)
 def test_no_inference_implementation_changes(self):
  marker=HERE/'inference-code-checksums.json'
  if not marker.exists():self.skipTest('Baseline checksum comparison written at package validation time.')
  for rel,digest in json.loads(marker.read_text()).items():
   self.assertEqual(hashlib.sha256((HERE.parent/rel).read_bytes()).hexdigest(),digest)

if __name__=='__main__':unittest.main()
