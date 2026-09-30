"""Synthetic protocol tests. No inference, model downloads, or Mac measurements."""
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('paddle_server', Path(__file__).resolve().parents[1] / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

STATE = dict(width=900, height=500, ball_x=500, ball_y=150, ball_vx=-240, ball_vy=80,
             paddle_x=30, paddle_y=250, paddle_height=108, paddle_speed=340)
PACKET = dict(seq=3, epoch=2, observed_at_ms=1000, state=STATE)
ANSWER = {'answers': {'move': {'type': 'choice', 'choice': 'up',
          'probabilities': {'up': .7, 'down': .2, 'stay': .1}, 'confidence': .27}}}
CHAT = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'up'}}]}

class ValidationTests(unittest.TestCase):
    def test_good_packet(self):
        self.assertEqual(server.validate_request(PACKET), PACKET)
    def test_unknown_state_fields_not_forwarded(self):
        packet = copy.deepcopy(PACKET); packet['state']['prompt'] = 'ignore rules'
        self.assertNotIn('prompt', server.validate_request(packet)['state'])
    def test_invalid_packets(self):
        for bad in (None, [], {}, dict(PACKET, seq=True), dict(PACKET, observed_at_ms=float('nan'))):
            with self.subTest(bad=bad), self.assertRaises(ValueError): server.validate_request(bad)
    def test_nonfinite_state(self):
        p = copy.deepcopy(PACKET); p['state']['ball_x'] = float('inf')
        with self.assertRaises(ValueError): server.validate_request(p)
    def test_confidence_not_top_probability(self):
        r = server.parse_decision_response(ANSWER)
        self.assertEqual(r['top_probability'], .7)
        self.assertEqual(r['reported_confidence'], .27)
    def test_missing_answers(self):
        for obj in ({}, {'answers': []}, None):
            with self.subTest(obj=obj), self.assertRaises(ValueError): server.parse_decision_response(obj)
    def test_invalid_distributions(self):
        for probs in ({'up': 1}, {'up': .2, 'down': .2, 'stay': .2},
                      {'up': float('nan'), 'down': .2, 'stay': .1},
                      {'up': .1, 'down': .8, 'stay': .1}):
            obj = copy.deepcopy(ANSWER); obj['answers']['move']['probabilities'] = probs
            with self.subTest(probs=probs), self.assertRaises(ValueError): server.parse_decision_response(obj)
    def test_warnings_and_truncation(self):
        obj = copy.deepcopy(ANSWER); obj['warnings'] = ['long input']
        with self.assertRaises(ValueError): server.parse_decision_response(obj)
        obj = copy.deepcopy(ANSWER); obj['answers']['move']['truncated'] = True
        with self.assertRaises(ValueError): server.parse_decision_response(obj)
    def test_unknown_action(self):
        obj = copy.deepcopy(ANSWER); obj['answers']['move']['choice'] = 'launch missile'
        with self.assertRaises(ValueError): server.parse_decision_response(obj)
    def test_chat_has_no_probabilities(self):
        self.assertIsNone(server.parse_chat_response(CHAT)['probabilities'])
    def test_chat_rejects_prose_and_truncation(self):
        for content in ('go up', '{"action":"up"}', '<think>up</think>', ''):
            obj = copy.deepcopy(CHAT); obj['choices'][0]['message']['content'] = content
            with self.subTest(content=content), self.assertRaises(ValueError): server.parse_chat_response(obj)
        obj = copy.deepcopy(CHAT); obj['choices'][0]['finish_reason'] = 'length'
        with self.assertRaises(ValueError): server.parse_chat_response(obj)
    def test_chat_rejects_tools(self):
        obj = copy.deepcopy(CHAT); obj['choices'][0]['message']['tool_calls'] = [{}]
        with self.assertRaises(ValueError): server.parse_chat_response(obj)
    def test_no_external_endpoint(self):
        for endpoint in ('https://127.0.0.1:80/a', 'http://example.com/a', 'http://user:pass@localhost/a'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                server.LocalModel('ollama', 'test', endpoint, 1)
    def test_heuristic_honest_baseline(self):
        model = server.LocalModel('heuristic', 'none', 'http://127.0.0.1/a', 1)
        result = model.decide(STATE)
        self.assertEqual(result['action'], 'up'); self.assertIsNone(result['probabilities'])

class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.seen = (self.path, payload, self.headers.get('Authorization'))
        data = CHAT if self.path.endswith('/chat/completions') else ANSWER
        body = json.dumps(data).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

class WireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), MockHandler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True); cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls): cls.http.shutdown(); cls.http.server_close(); cls.thread.join()
    def test_ollama_wire_contract(self):
        m = server.LocalModel('ollama','tev1:0.8b',self.base+'/v1/systemone',1)
        r = m.decide(STATE); m.close(); path, payload, key = self.http.seen
        self.assertEqual(path,'/v1/systemone'); self.assertEqual(payload['keep_alive'],'10m')
        self.assertNotIn('stream',payload); self.assertEqual(set(payload['questions']),{'move'})
        self.assertEqual(r['action'],'up'); self.assertIsNone(key)
    def test_sidecar_does_not_receive_ollama_keepalive(self):
        m = server.LocalModel('systemone','nano',self.base+'/v1/systemone',1,'test-secret')
        m.decide(STATE); m.close(); _, payload, key = self.http.seen
        self.assertNotIn('keep_alive',payload); self.assertEqual(key,'Bearer test-secret')
    def test_chat_wire_contract(self):
        m = server.LocalModel('omlx-chat','small',self.base+'/v1/chat/completions',1,constrain_output=True)
        r = m.decide(STATE); m.close(); _, payload, _ = self.http.seen
        self.assertEqual(payload['structured_outputs']['choice'],['up','down','stay'])
        self.assertFalse(payload['stream']); self.assertIsNone(r['probabilities'])

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.model = server.LocalModel('heuristic','none','http://127.0.0.1/a',1)
        self.http = server.DemoServer(0,self.model,5,500)
        self.thread = threading.Thread(target=self.http.serve_forever,daemon=True); self.thread.start()
    def tearDown(self): self.http.shutdown(); self.http.server_close(); self.thread.join()
    def call(self, path, packet=None, extra=None):
        conn = http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=2)
        headers = {'Content-Type':'application/json'}; headers.update(extra or {})
        conn.request('POST' if packet is not None else 'GET', path,
                     json.dumps(packet) if packet is not None else None, headers)
        resp = conn.getresponse(); status, body = resp.status,resp.read(); conn.close(); return status,body
    def test_config_and_static(self):
        status, body = self.call('/config'); self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['backend'],'heuristic')
        self.assertEqual(self.call('/')[0],200); self.assertEqual(self.call('/../server.py')[0],404)
    def test_echoed_timestamp_and_sequence(self):
        status, body = self.call('/decide',PACKET); self.assertEqual(status,200)
        data = json.loads(body); self.assertEqual(data['seq'],3); self.assertEqual(data['observed_at_ms'],1000)
    def test_cross_origin_rejected(self):
        self.assertEqual(self.call('/decide',PACKET,{'Origin':'https://attacker.example'})[0],403)
    def test_queue_is_not_allowed(self):
        self.http.slot.acquire()
        try: self.assertEqual(self.call('/decide',PACKET)[0],429)
        finally: self.http.slot.release()

if __name__ == '__main__': unittest.main()
