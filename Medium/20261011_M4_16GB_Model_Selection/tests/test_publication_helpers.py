"""Model-free checks for the new publication helpers, using synthetic HTTP only."""
from __future__ import annotations
import ast
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import ollama_probe
import plan_measured
from checkpoint_fetch import FetchError

@contextlib.contextmanager
def service(*,content='READY',reason='stop',advertised='demo:latest',ready='READY'):
 state={'posts':[]}
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send_json(self,value):
   data=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  def do_GET(self):
   if self.path=='/api/tags':self.send_json({'models':[{'name':advertised,'model':advertised,'digest':'fixture-digest'}]})
   elif self.path=='/v1/models':self.send_json({'object':'list','data':[{'id':advertised,'object':'model'}]})
   else:self.send_error(404)
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));state['posts'].append(body)
   if self.path=='/api/chat':self.send_json({'model':advertised,'message':{'role':'assistant','content':content},'done':True,'done_reason':reason,'eval_count':5,'prompt_eval_count':12});return
   if self.path!='/v1/chat/completions':self.send_error(404);return
   prompt=body['messages'][-1]['content']
   answer=ready if prompt.startswith('Reply with READY') else json.dumps({'order_id':'ORD-27A9','owner':'Mira','amount_eur':2400}) if 'order_id' in prompt else 'harbor-mint-47'
   self.send_json({'id':'mock-'+str(len(state['posts'])),'object':'chat.completion','model':advertised,'choices':[{'index':0,'message':{'role':'assistant','content':answer},'finish_reason':'stop'}],'usage':{'prompt_tokens':12,'completion_tokens':5,'total_tokens':17}})
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:yield f'http://127.0.0.1:{server.server_port}',state
 finally:server.shutdown();server.server_close();thread.join()

class RevisionPlanning(unittest.TestCase):
 def test_recorded_revision_is_used(self):self.assertEqual(plan_measured.select_revision('x',{'x':{'revision':'a'*40}},False),'a'*40)
 def test_absent_revision_requires_permission(self):
  with self.assertRaises(FetchError):plan_measured.select_revision('missing',{},False)
 def test_new_experiment_explicit(self):self.assertEqual(plan_measured.select_revision('missing',{},True),'main')
 def test_plan_only_does_not_download(self):
  with patch.object(plan_measured,'make_plan') as plan, contextlib.redirect_stdout(io.StringIO()):
   self.assertEqual(plan_measured.main(['bonsai-ternary','--lab','/tmp/fixture']),0)
   self.assertEqual(plan.call_args.args[2],'2aec25cc51a1ddfef6e3c61e07ccb17399e1d43d')

class RawOllamaEvidence(unittest.TestCase):
 def invoke(self,root,url,model='demo:latest'):
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   return ollama_probe.main(['--base-url',url,'--model',model,'--prompt','A small test','--out-root',str(root),'--output-tokens','64'])
 def test_completed_response_is_saved(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):
   root=Path(tmp);self.assertEqual(self.invoke(root,url),0);folder=next(root.iterdir());self.assertTrue((folder/'response.json').exists());self.assertEqual((folder/'answer.txt').read_text(),'READY');self.assertEqual(len(state['posts']),1)
 def test_truncation_is_saved_and_rejected(self):
  with tempfile.TemporaryDirectory() as tmp,service(content='partial',reason='length') as (url,state):
   root=Path(tmp);self.assertEqual(self.invoke(root,url),1);folder=next(root.iterdir());self.assertEqual(json.loads((folder/'response.json').read_text())['done_reason'],'length');self.assertEqual((folder/'answer.txt').read_text(),'partial');self.assertEqual(len(state['posts']),1)
 def test_empty_completed_message_is_not_pass(self):
  with tempfile.TemporaryDirectory() as tmp,service(content='') as (url,state):self.assertEqual(self.invoke(Path(tmp),url),1)
 def test_exact_model_required_no_substitution(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):self.assertEqual(self.invoke(Path(tmp),url,'demo'),2);self.assertEqual(len(state['posts']),0)
 def test_local_only(self):
  with tempfile.TemporaryDirectory() as tmp:self.assertEqual(self.invoke(Path(tmp),'https://example.com'),2)
 def test_non_text_message_preserves_raw(self):
  with tempfile.TemporaryDirectory() as tmp,service(content={'not':'text'}) as (url,state):
   root=Path(tmp);self.assertEqual(self.invoke(root,url),2);folder=next(root.iterdir());self.assertTrue((folder/'response.json').exists());self.assertTrue((folder/'error.txt').exists())
 def test_request_is_bounded_non_thinking_and_unloads(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):
   self.assertEqual(self.invoke(Path(tmp),url),0);r=state['posts'][0];self.assertIs(r['think'],False);self.assertIs(r['stream'],False);self.assertEqual(r['keep_alive'],0);self.assertEqual(r['options']['num_ctx'],4096);self.assertEqual(r['options']['num_predict'],64)
 def test_invalid_message_cannot_pass_predicate(self):self.assertFalse(ollama_probe.completion_ok({'done':True,'done_reason':'stop','message':42}))

class SequentialReadiness(unittest.TestCase):
 def invoke(self,tmp,url,model='demo:latest',label='sample'):
  lab=Path(tmp);binpath=lab/'venv-tools/bin';binpath.mkdir(parents=True);(binpath/'python').symlink_to(sys.executable)
  env=dict(os.environ,LAB=tmp);env.pop('LOCAL_AI_API_KEY',None)
  return subprocess.run(['bash',str(ROOT/'scripts/test_model.sh'),url+'/v1',model,label],env=env,text=True,capture_output=True,timeout=20)
 def test_one_readiness_then_six_contracts(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):
   r=self.invoke(tmp,url);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(len(state['posts']),7);runs=list((Path(tmp)/'logs').iterdir());self.assertEqual(len(runs),1);rows=[json.loads(x) for x in (runs[0]/'smoke.jsonl').read_text().splitlines()];self.assertEqual(len(rows),6);self.assertTrue(all(x['passed'] for x in rows))
 def test_wrong_ready_stops_before_contracts(self):
  with tempfile.TemporaryDirectory() as tmp,service(ready='not-ready') as (url,state):
   r=self.invoke(tmp,url);self.assertNotEqual(r.returncode,0);self.assertEqual(len(state['posts']),1);self.assertFalse(list(Path(tmp).rglob('smoke.jsonl')))
 def test_model_mismatch_does_not_infer(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):r=self.invoke(tmp,url,'another');self.assertNotEqual(r.returncode,0);self.assertEqual(len(state['posts']),0)
 def test_no_path_traversal_label(self):
  with tempfile.TemporaryDirectory() as tmp,service() as (url,state):r=self.invoke(tmp,url,label='../bad');self.assertNotEqual(r.returncode,0);self.assertEqual(len(state['posts']),0)

class Manuscript(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.text=(ROOT/'article.md').read_text()
 def test_eight_images(self):
  refs=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',self.text);self.assertEqual(len(refs),8)
  for name in refs:self.assertTrue((ROOT/name).is_file())
 def test_bash_blocks_parse_and_are_plain(self):
  blocks=re.findall(r'^```bash\n(.*?)^```',self.text,re.M|re.S);self.assertGreater(len(blocks),35)
  for b in blocks:
   self.assertNotIn('\u00a0',b);self.assertNotRegex(b,r'\[https?://');p=subprocess.run(['bash','-n'],input=b,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr+'\n'+b)
 def test_no_old_revision_handoff(self):
  for name in ('setup-guide.md','quantized-model-lab.md','GUIDE-UPDATES-R3','NEXT-L7'):self.assertNotIn(name,self.text)
 def test_iq3_launch_and_preflight_ack(self):
  lines=[x for x in self.text.splitlines() if 'launch_lab.py' in x and 'qwen38-iq3xxs' in x];self.assertGreaterEqual(len(lines),2)
  for line in lines:self.assertIn('--accept-tight-memory',line)
 def test_streaming_flags_preserved(self):
  self.assertIn('--max-active-experts 0',self.text);self.assertIn('--expert-cache-gb 4',self.text)
 def test_runtime_fields_match_original(self):
  old=json.loads((ROOT/'validation/unchanged-runtime-profile-fields.json').read_text());new=json.loads((ROOT/'config/standalone-models.json').read_text());new.pop('snapshot')
  for model in new['models'].values():model.pop('status')
  self.assertEqual(old,new)
 def test_ollama_exact_alias(self):self.assertIn('qwen38-local-iq2s:latest',self.text)

if __name__=='__main__':unittest.main()
