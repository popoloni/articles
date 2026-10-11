"""Model-free tests: algorithmic helpers and synthetic local HTTP responses only."""
from __future__ import annotations
import contextlib
import hashlib
import http.server
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from local_ai import Client, LocalAIError, chunks, percentile, read_text, write_text, write_json, validate_model, translation_prompt, summarize, STARTER, EMBED
from rag import cosine, documents, build_index, retrieve, answer
from extract_text import VisibleHTML, clean_captions

class PureHelpers(unittest.TestCase):
    def test_accept_local(self): self.assertEqual(validate_model(STARTER), STARTER)
    def test_reject_cloud(self):
        with self.assertRaises(LocalAIError): validate_model('model:cloud')
    def test_reject_url_model(self):
        with self.assertRaises(LocalAIError): validate_model('https://remote/model')
    def test_reject_empty_model(self):
        with self.assertRaises(LocalAIError): validate_model('')
    def test_loopback(self): self.assertEqual(Client().host, '127.0.0.1')
    def test_ipv6_loopback(self): self.assertEqual(Client('http://[::1]:11434').host, '::1')
    def test_reject_nonlocal(self):
        with self.assertRaises(LocalAIError): Client('http://example.com:11434')
    def test_reject_lan(self):
        with self.assertRaises(LocalAIError): Client('http://192.168.1.3:11434')
    def test_reject_credentials(self):
        with self.assertRaises(LocalAIError): Client('http://u:p@127.0.0.1:11434')
    def test_reject_path(self):
        with self.assertRaises(LocalAIError): Client('http://127.0.0.1:11434/api')
    def test_reject_query(self):
        with self.assertRaises(LocalAIError): Client('http://127.0.0.1:11434?x=y')
    def test_reject_timeout(self):
        with self.assertRaises(LocalAIError): Client(timeout=0)
    def test_empty_chunks(self): self.assertEqual(chunks('  '), [])
    def test_short_chunk(self): self.assertEqual(chunks('hello'), ['hello'])
    def test_chunk_bound(self): self.assertTrue(all(len(c)<=300 for c in chunks('a'*1000,300,20)))
    def test_chunk_overlap(self): self.assertEqual(chunks('x'*550,300,50), ['x'*300,'x'*300])
    def test_bad_chunk_size(self):
        with self.assertRaises(LocalAIError): chunks('a',20,0)
    def test_bad_overlap(self):
        with self.assertRaises(LocalAIError): chunks('a',200,200)
    def test_percentile_empty(self): self.assertIsNone(percentile([], .95))
    def test_percentile_median(self): self.assertEqual(percentile([1,2,3,4],.5),2.5)
    def test_percentile_single(self): self.assertEqual(percentile([9],.95),9)
    def test_cosine_same(self): self.assertAlmostEqual(cosine([1,2],[1,2]),1)
    def test_cosine_orthogonal(self): self.assertEqual(cosine([1,0],[0,1]),0)
    def test_cosine_dimension(self):
        with self.assertRaises(LocalAIError): cosine([1],[1,2])
    def test_cosine_zero(self):
        with self.assertRaises(LocalAIError): cosine([0,0],[1,0])
    def test_cosine_nan(self):
        with self.assertRaises(LocalAIError): cosine([math.nan],[1])
    def test_translation_template(self):
        p = translation_prompt('Hello','English','en','Italian','it')
        self.assertIn('English (en) to Italian (it)',p)
        self.assertTrue(p.endswith(':\n\n\nHello'))
    def test_html_hidden(self):
        p=VisibleHTML();p.feed('<p>Keep</p><script>bad</script><style>bad2</style><p>Also</p>')
        self.assertIn('Keep',''.join(p.result));self.assertNotIn('bad',''.join(p.result))
    def test_captions(self):
        text='WEBVTT\n\n1\n00:00.000 --> 00:01.000\nHello\nHello\nWorld\n'
        self.assertEqual(clean_captions(text),'Hello\nWorld')
    def test_write_read(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new'/'a.txt';write_text(p,'café');self.assertEqual(read_text(p),'café')
    def test_empty_text_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_text(' ')
            with self.assertRaises(LocalAIError):read_text(p)
    def test_write_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';write_json(p,{'x':1});self.assertEqual(json.loads(p.read_text()),{'x':1})

class StubHandler(http.server.BaseHTTPRequestHandler):
    scenario='normal';last_body=None
    def log_message(self,*args): pass
    def do_GET(self):
        self.reply({'version':'STUB-NOT-OLLAMA'} if self.path=='/api/version' else
                   {'models':[{'name':STARTER,'digest':'sha-fixture'}]})
    def reply(self, value, status=200):
        raw=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))));type(self).last_body=body
        mode=type(self).scenario
        if mode=='http_error':self.reply({'error':'fixture rejection'},503);return
        if mode=='redirect':self.send_response(302);self.send_header('Location','https://example.invalid');self.end_headers();return
        if mode=='api_error':self.reply({'error':'fixture error'});return
        if mode=='malformed':self.send_response(200);self.end_headers();self.wfile.write(b'not json');return
        if self.path=='/api/embed':
            vectors=[[1.0,0.0] for _ in body['input']]
            if mode=='bad_count':vectors=[]
            if mode=='nan':vectors=[[float('nan')]]
            self.reply({'embeddings':vectors});return
        if body.get('stream'):
            self.send_response(200);self.end_headers()
            rows=[{'message':{},'done':False},
                  {'message':{'content':'Synthetic answer'},'done':False}]
            if mode!='incomplete':rows.append({'message':{},'done':True,'done_reason':'stop',
                'eval_count':4,'eval_duration':2_000_000_000,'prompt_eval_count':10})
            for row in rows:self.wfile.write((json.dumps(row)+'\n').encode())
            return
        self.reply({'message':{'content':'' if mode=='empty' else 'Synthetic answer'},
                    'done':True,'done_reason':'length' if mode=='length' else 'stop'})

class HTTPHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),StubHandler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.client=Client(f'http://127.0.0.1:{cls.server.server_port}')
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):StubHandler.scenario='normal'
    def test_inventory(self):self.assertEqual(self.client.inventory()['version']['version'],'STUB-NOT-OLLAMA')
    def test_digest(self):self.assertEqual(self.client.model_digest(STARTER),'sha-fixture')
    def test_missing_digest(self):
        with self.assertRaises(LocalAIError):self.client.model_digest('missing:1b')
    def test_chat(self):self.assertEqual(self.client.chat('hello')['message']['content'],'Synthetic answer')
    def test_payload(self):
        self.client.chat('hello');self.assertEqual(StubHandler.last_body['keep_alive'],0);self.assertFalse(StubHandler.last_body['think'])
    def test_translation_omit_think(self):
        self.client.chat('hello',think=None);self.assertNotIn('think',StubHandler.last_body)
    def test_bad_context(self):
        with self.assertRaises(LocalAIError):self.client.chat('x',ctx=200)
    def test_bad_output_budget(self):
        with self.assertRaises(LocalAIError):self.client.chat('x',ctx=1024,output=1024)
    def test_empty_response(self):
        StubHandler.scenario='empty'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_truncation(self):
        StubHandler.scenario='length'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_http_error(self):
        StubHandler.scenario='http_error'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_api_error(self):
        StubHandler.scenario='api_error'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_no_redirect(self):
        StubHandler.scenario='redirect'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_invalid_json(self):
        StubHandler.scenario='malformed'
        with self.assertRaises(LocalAIError):self.client.chat('x')
    def test_embed(self):self.assertEqual(self.client.embed(['x','y']),[[1,0],[1,0]])
    def test_embed_no_truncate(self):
        self.client.embed(['x']);self.assertFalse(StubHandler.last_body['truncate'])
    def test_embed_bad_count(self):
        StubHandler.scenario='bad_count'
        with self.assertRaises(LocalAIError):self.client.embed(['x'])
    def test_embed_nonfinite(self):
        StubHandler.scenario='nan'
        with self.assertRaises(LocalAIError):self.client.embed(['x'])
    def test_unload(self):
        self.client.unload(STARTER);self.assertEqual(StubHandler.last_body,{'model':STARTER,'keep_alive':0})
    def test_stream_metrics(self):
        r=self.client.benchmark_once(STARTER,'x',4096,512)
        self.assertEqual(r['server_generation_tokens_per_second'],2)
        self.assertTrue(r['answer_complete']);self.assertIsNotNone(r['first_visible_text_seconds'])
    def test_incomplete_stream(self):
        StubHandler.scenario='incomplete'
        with self.assertRaises(LocalAIError):self.client.benchmark_once(STARTER,'x',4096,512)
    def test_reject_route(self):
        with self.assertRaises(LocalAIError):self.client.request('/remote')

class FakeRAGClient:
    def __init__(self):self.events=[];self.digest='digest-one'
    def model_digest(self,model):return self.digest
    def embed(self,text,model=EMBED,keep_alive=0):self.events.append('embed');return [[1.,0.] for _ in text]
    def unload(self,model):self.events.append('unload')
    def chat(self,prompt,model=STARTER,**kw):self.events.append('chat');return {'message':{'content':'[S1] Synthetic RAG answer'}}

class WorkflowHelpers(unittest.TestCase):
    def test_index_and_sequential_answer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);library=root/'library';library.mkdir();(library/'note.md').write_text('Approved budget EUR 2,400; owner Leena.')
            c=FakeRAGClient();idx=root/'idx.json'
            with contextlib.redirect_stderr(io.StringIO()):build_index(c,library,idx,EMBED)
            c.events=[];_,selected=retrieve(c,idx,'Budget?');text,evidence=answer(c,selected,'Budget?',STARTER,4096)
            self.assertEqual(c.events,['embed','unload','chat']);self.assertEqual(evidence[0]['label'],'S1')
    def test_reject_changed_embedding(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lib=root/'lib';lib.mkdir();(lib/'a.md').write_text('Text')
            c=FakeRAGClient();idx=root/'idx.json'
            with contextlib.redirect_stderr(io.StringIO()):build_index(c,lib,idx,EMBED)
            c.digest='new'
            with self.assertRaises(LocalAIError):retrieve(c,idx,'x')
    def test_reject_changed_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lib=root/'lib';lib.mkdir();p=lib/'a.md';p.write_text('Text')
            c=FakeRAGClient();idx=root/'idx.json'
            with contextlib.redirect_stderr(io.StringIO()):build_index(c,lib,idx,EMBED)
            p.write_text('Changed')
            with self.assertRaises(LocalAIError):retrieve(c,idx,'x')
    def test_reject_empty_library(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(LocalAIError):documents(Path(d))
    def test_skip_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.md').write_text('Text');(root/'alias.md').symlink_to(root/'a.md')
            self.assertEqual(len(documents(root)),1)
    def test_summary_preserves_source_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            c=FakeRAGClient()
            with contextlib.redirect_stderr(io.StringIO()):summarize(c,'Budget is 2400.',STARTER,Path(d))
            self.assertIn('Budget is 2400.',(Path(d)/'chunk-001.md').read_text())
            self.assertTrue((Path(d)/'summary.md').is_file());self.assertEqual(c.events[-1],'unload')
    def test_empty_summary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(LocalAIError):summarize(FakeRAGClient(),' ',STARTER,Path(d))

if __name__=='__main__':unittest.main()
