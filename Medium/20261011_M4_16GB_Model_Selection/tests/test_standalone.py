"""Model-free checks for the new lab: no Hub downloads and no native runtime."""
from __future__ import annotations
import contextlib
import http.server
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import compat_lab as c
import checkpoint_fetch as f
import launch_lab as l

def response(text='hello',finish='stop',**message):
    return {'choices':[{'finish_reason':finish,'message':{'role':'assistant','content':text,**message}}],
            'usage':{'prompt_tokens':20,'completion_tokens':4}}

class PureProbe(unittest.TestCase):
    def test_ipv4(self):self.assertEqual(c.validate_base('http://127.0.0.1:8080/v1'),('127.0.0.1',8080,'/v1'))
    def test_ipv6(self):self.assertEqual(c.validate_base('http://[::1]:8000/v1/'),('::1',8000,'/v1'))
    def test_lan_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('http://192.168.1.2:8000/v1')
    def test_dns_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('http://localhost:8000/v1')
    def test_https_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('https://127.0.0.1/v1')
    def test_credentials_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('http://a:b@127.0.0.1/v1')
    def test_extra_path_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('http://127.0.0.1/v1/models')
    def test_query_rejected(self):
        with self.assertRaises(c.LabError):c.validate_base('http://127.0.0.1/v1?a=1')
    def test_cloud_rejected(self):
        with self.assertRaises(c.LabError):c.validate_model('foo:cloud')
    def test_local_model_path_allowed(self):self.assertEqual(c.validate_model('/Users/a/model'),'/Users/a/model')
    def test_nonfinite_timeout_rejected(self):
        with self.assertRaises(c.LabError):c.Client('http://127.0.0.1/v1',float('nan'))
    def test_key_newline_rejected(self):
        with self.assertRaises(c.LabError):c.Client('http://127.0.0.1/v1',api_key='x\ny')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(c.LabError):c.strict_json('{"p":NaN}')
    def test_invalid_json_rejected(self):
        with self.assertRaises(c.LabError):c.strict_json('no')
    def test_empty_text_rejected(self):
        with self.assertRaises(c.LabError):c.visible_text(response(''))
    def test_length_finish_rejected(self):
        with self.assertRaises(c.LabError):c.visible_text(response('partial','length'))
    def test_unknown_finish_rejected(self):
        with self.assertRaises(c.LabError):c.visible_text(response('hello',None))
    def test_json_contract(self):self.assertTrue(c.check_contract(response('{"order_id":"ORD-27A9","owner":"Mira","amount_eur":2400}')))
    def test_json_extra_field(self):self.assertFalse(c.check_contract(response('{"order_id":"ORD-27A9","owner":"Mira","amount_eur":2400,"x":1}')))
    def test_fenced_json_not_plain_json(self):
        with self.assertRaises(c.LabError):c.check_contract(response('```json\n{}\n```'))
    def test_literal_recall(self):self.assertTrue(c.check_recall(response('harbor-mint-47\n')))
    def test_old_value_rejected(self):self.assertFalse(c.check_recall(response('copper-slate-12')))
    def test_tool_contract(self):
        call={'type':'function','function':{'name':'lookup_order','arguments':'{"order_id":"ORD-27A9"}'}}
        self.assertTrue(c.check_tool(response(None,'tool_calls',tool_calls=[call])))
    def test_tool_prose_rejected(self):self.assertFalse(c.check_tool(response('I would call lookup_order')))
    def test_tool_extra_argument_rejected(self):
        call={'type':'function','function':{'name':'lookup_order','arguments':'{"order_id":"ORD-27A9","execute":true}'}}
        self.assertFalse(c.check_tool(response(None,'tool_calls',tool_calls=[call])))
    def test_payload_does_not_force_json_backend(self):self.assertNotIn('response_format',c.payload('m','hi',512,.7))
    def test_output_budget_rejected(self):
        with self.assertRaises(c.LabError):c.payload('m','hi',50000,.7)
    def test_log_permissions(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.jsonl';c.append_record(p,{'ok':True})
            self.assertEqual(p.stat().st_mode&0o777,0o600)

class ThinkingControl(unittest.TestCase):
    def test_explicit_off_for_import(self):
        from local_ai import thinking_policy
        self.assertIs(thinking_policy('qwen38-local-iq2s','off'),False)
    def test_auto_original_unchanged(self):
        from local_ai import thinking_policy
        self.assertIs(thinking_policy('qwen3.5:4b-q4_K_M'),False)
    def test_unknown_alias_not_guessed(self):
        from local_ai import thinking_policy
        self.assertIsNone(thinking_policy('my-custom-model'))
    def test_runtime_omits(self):
        from local_ai import thinking_policy
        self.assertIsNone(thinking_policy('qwen38-local-iq2s','runtime'))
    def test_on_explicit(self):
        from local_ai import thinking_policy
        self.assertIs(thinking_policy('qwen38-local-iq2s','on'),True)

class DownloadPlans(unittest.TestCase):
    def test_gguf_selected_not_full_repo(self):
        spec=f.catalog()['qwen38-iq2s']
        names=[spec['file'],'Qwen3.8-27B-BF16.gguf','mmproj-F16.gguf','MTP/model.gguf','README.md']
        self.assertEqual(f.select_names(spec,names),[spec['file'],'README.md'])
    def test_missing_exact_file_no_substitution(self):
        with self.assertRaises(f.FetchError):f.select_names(f.catalog()['qwen38-iq2s'],['other.gguf'])
    def test_custom_code_selected_for_review(self):
        names=['config.json','model.safetensors','ternel_packed_model.py','ternel_manifest.json','MTP/model.safetensors']
        result=f.select_names(f.catalog()['bonsai-ternary'],names)
        self.assertIn('ternel_packed_model.py',result);self.assertNotIn('MTP/model.safetensors',result)
    def test_traversal_rejected(self):
        with self.assertRaises(f.FetchError):f.select_names(f.catalog()['qwen38-iq2s'],['../bad'])
    def test_model_layout_required(self):
        with self.assertRaises(f.FetchError):f.select_names(f.catalog()['qwen38-mlx2'],['README.md'])
    def test_plan_valid(self):
        spec=f.catalog()['qwen38-iq2s'];p={'schema':1,'profile':'qwen38-iq2s','repo':spec['repo'],
           'revision':'a'*40,'total_bytes':10,'files':[{'name':spec['file'],'size':10}]}
        self.assertEqual(f.validate_plan(p),spec)
    def test_short_sha_rejected(self):
        p={'schema':1,'profile':'qwen38-iq2s','repo':f.catalog()['qwen38-iq2s']['repo'],'revision':'abc'}
        with self.assertRaises(f.FetchError):f.validate_plan(p)
    def test_index_missing_shard(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'model.safetensors.index.json').write_text('{"weight_map":{"w":"missing.safetensors"}}')
            with self.assertRaises(f.FetchError):f.validate_index(Path(td),['model.safetensors.index.json'])

class LaunchProfiles(unittest.TestCase):
    def test_binary_exact_file(self):self.assertIn('/tmp/lab/models/bonsai-binary/Bonsai-27B-Q1_0.gguf',l.command('bonsai-binary','/tmp/lab'))
    def test_mlx_no_unsupported_kv_flag(self):self.assertNotIn('--kv-bits',l.command('bonsai-ternary','/tmp/lab'))
    def test_mlx_correct_template_flag(self):self.assertIn('--chat-template-args',l.command('qwen38-mlx2','/tmp/lab'))
    def test_native_expert_routing(self):
        cmd=l.command('qwen36-stream','/tmp/lab');self.assertEqual(cmd[cmd.index('--max-active-experts')+1],'0')
    def test_no_implicit_disk_cache(self):self.assertNotIn('--disk-cache',l.command('qwen36-asym','/tmp/lab'))
    def test_explicit_disk_cache(self):self.assertIn('--disk-cache',l.command('qwen36-asym','/tmp/lab',True))
    def test_no_disk_cache_on_vanilla_mlx(self):
        with self.assertRaises(l.LaunchError):l.command('qwen38-mlx2','/tmp/lab',True)
    def test_diagnostic_not_auto_launched(self):
        with self.assertRaises(l.LaunchError):l.command('qwen38-tq-diagnostic','/tmp/lab')
    def test_no_sysctl_in_commands(self):
        for name in l.specs():
            if name=='qwen38-tq-diagnostic':continue
            cmd=l.command(name,'/tmp/lab');self.assertNotIn('sudo',cmd);self.assertNotIn('sysctl',cmd)
    def test_qwen38_no_expert_options(self):self.assertNotIn('--cache-budget-gb',l.command('qwen38-iq2s','/tmp/lab'))
    def test_qwen38_prefill128(self):
        cmd=l.command('qwen38-iq2s','/tmp/lab');self.assertEqual(cmd[cmd.index('-ub')+1],'128')

class HTTPProbe(unittest.TestCase):
    def setUp(self):
        self.requests=[];owner=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_GET(self):
                owner.requests.append(('GET',self.path,None))
                self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"fixture"}]}')
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.requests.append(('POST',self.path,body));prompt=body['messages'][0]['content']
                if 'obsolete code' in prompt:r=response('harbor-mint-47')
                elif body.get('tools'):
                    r=response(None,'tool_calls',tool_calls=[{'type':'function','function':{
                        'name':'lookup_order','arguments':'{"order_id":"ORD-27A9"}'}}])
                else:r=response('{"order_id":"ORD-27A9","owner":"Mira","amount_eur":2400}')
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps(r).encode())
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.client=c.Client(f'http://127.0.0.1:{self.server.server_port}/v1')
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def test_three_repeated_contracts_over_http(self):
        with tempfile.TemporaryDirectory() as td,contextlib.redirect_stdout(io.StringIO()):
            out=Path(td)/'smoke.jsonl';self.assertEqual(c.smoke(self.client,'fixture',3,True,out),0)
            rows=[json.loads(line) for line in out.read_text().splitlines()]
            self.assertEqual(len(rows),9);self.assertTrue(all(r['passed'] for r in rows))
            self.assertTrue(all(r['decode_tokens_per_second'] is None for r in rows))
            self.assertTrue(all(r['tool_executed'] is False for r in rows))
            self.assertEqual(len([r for r in self.requests if r[0]=='POST']),9)
    def test_wrong_id_never_loads(self):
        with self.assertRaises(c.LabError):self.client.require_model('not-installed')
        self.assertEqual(len(self.requests),1);self.assertEqual(self.requests[0][0],'GET')
    def test_proxies_not_used(self):
        old=os.environ.get('HTTP_PROXY');os.environ['HTTP_PROXY']='http://192.0.2.1:1'
        try:self.assertEqual(self.client.models()['data'][0]['id'],'fixture')
        finally:
            if old is None:os.environ.pop('HTTP_PROXY',None)
            else:os.environ['HTTP_PROXY']=old

if __name__=='__main__':unittest.main()
