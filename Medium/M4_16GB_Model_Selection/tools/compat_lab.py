#!/usr/bin/env python3
"""Small, non-executing OpenAI-compatible local API probe.

No external inference, automatic downloads, tool execution, redirects or retries.
A socket timeout is NOT inference cancellation. Stop and inspect the server.
"""
from __future__ import annotations
import argparse
import datetime as dt
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

class LabError(RuntimeError):
    pass

def strict_json(text: str):
    def reject(value):
        raise LabError(f'Non-finite JSON constant: {value}')
    try:
        return json.loads(text, parse_constant=reject)
    except (ValueError, TypeError) as exc:
        raise LabError(f'Invalid JSON: {exc}') from exc

def validate_base(base: str) -> tuple[str, int, str]:
    try:
        u = urlsplit(base)
        host = u.hostname
        port = u.port
        if u.scheme != 'http' or not host or not ipaddress.ip_address(host).is_loopback:
            raise ValueError('Use a literal loopback HTTP address, e.g. http://127.0.0.1:8082/v1')
        if u.username or u.password or u.query or u.fragment or u.path.rstrip('/') != '/v1':
            raise ValueError('No credentials/query/fragment; base path must be /v1')
        return host, port or 80, '/v1'
    except ValueError as exc:
        raise LabError(str(exc)) from exc

def validate_model(model: str) -> str:
    if not isinstance(model, str) or not model.strip() or len(model) > 2048:
        raise LabError('An explicit, nonempty model ID is required.')
    if any(ord(c) < 32 for c in model) or '://' in model or model.lower().endswith(':cloud'):
        raise LabError('Refusing a URL, cloud model or control characters in model ID.')
    return model

class Client:
    def __init__(self, base: str, timeout: float = 180.0, api_key: str = ''):
        self.host, self.port, self.prefix = validate_base(base)
        if not math.isfinite(timeout) or not 0 < timeout <= 3600:
            raise LabError('Timeout must be finite, positive and at most 3600 seconds.')
        if '\r' in api_key or '\n' in api_key:
            raise LabError('Invalid API key header.')
        self.timeout, self.key = timeout, api_key
        self.base = base.rstrip('/')
    def request(self, method: str, suffix: str, body=None):
        # http.client bypasses environment proxy settings; no redirect handler exists.
        if suffix not in ('/models', '/chat/completions'):
            raise LabError('Unsupported endpoint.')
        headers = {'Accept': 'application/json'}
        if self.key: headers['Authorization'] = 'Bearer ' + self.key
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        conn = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)
        t0 = time.perf_counter()
        try:
            conn.request(method, self.prefix + suffix, body=data, headers=headers)
            reply = conn.getresponse()
            raw = reply.read(4 * 1024 * 1024 + 1)
            elapsed = time.perf_counter() - t0
            if len(raw) > 4 * 1024 * 1024: raise LabError('Response exceeds 4 MiB limit.')
            if reply.status != 200:
                # Do not print potentially sensitive server response bodies in errors.
                raise LabError(f'HTTP {reply.status}; no redirect or automatic retry performed.')
            result = strict_json(raw.decode('utf-8'))
            if not isinstance(result, dict) or result.get('error'):
                raise LabError('Response is not a successful JSON object.')
            return result, elapsed
        except (OSError, http.client.HTTPException, UnicodeDecodeError) as exc:
            raise LabError(f'{type(exc).__name__}: {exc}. Inspect the server before retrying; '
                           'a client timeout does not cancel inference.') from exc
        finally:
            conn.close()
    def models(self):
        result, _ = self.request('GET', '/models')
        rows = result.get('data')
        if not isinstance(rows, list) or not all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in rows):
            raise LabError('Malformed model discovery response.')
        return result
    def require_model(self, model):
        validate_model(model)
        if model not in [r['id'] for r in self.models()['data']]:
            raise LabError('Requested ID is not advertised. Run models and choose its exact ID; no substitution made.')
    def chat(self, payload):
        return self.request('POST', '/chat/completions', payload)

def response_message(response):
    choices = response.get('choices')
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise LabError('Expected exactly one completion choice.')
    choice = choices[0]
    reason = choice.get('finish_reason')
    if reason not in ('stop', 'tool_calls'):
        raise LabError(f'Completion not verified: finish_reason={reason!r}.')
    message = choice.get('message')
    if not isinstance(message, dict) or message.get('role', 'assistant') != 'assistant':
        raise LabError('Malformed assistant message.')
    return message

def visible_text(response):
    msg = response_message(response)
    content = msg.get('content')
    if msg.get('tool_calls') or not isinstance(content, str) or not content.strip():
        raise LabError('Expected nonempty visible text and no tool calls.')
    return content

def check_contract(response):
    value = strict_json(visible_text(response))
    expected = {'order_id': 'ORD-27A9', 'owner': 'Mira', 'amount_eur': 2400}
    return isinstance(value, dict) and value == expected and type(value.get('amount_eur')) in (int, float)

def check_recall(response):
    return visible_text(response).strip() == 'harbor-mint-47'

def check_tool(response):
    msg = response_message(response)
    calls = msg.get('tool_calls')
    if not isinstance(calls, list) or len(calls) != 1: return False
    call = calls[0]
    if not isinstance(call, dict) or call.get('type') != 'function': return False
    function = call.get('function', {})
    args = function.get('arguments')
    if function.get('name') != 'lookup_order' or not isinstance(args, str): return False
    return strict_json(args) == {'order_id': 'ORD-27A9'}

def cases(with_tools=False):
    rows = [
        ('json_contract', 'Return only a JSON object with exactly order_id, owner and amount_eur. '
         'Use this record, not outside knowledge: order_id=ORD-27A9; owner=Mira; amount_eur=2400. '
         'amount_eur must be a number. No Markdown or explanation.', check_contract, None),
        ('literal_recall', 'Synthetic lab data: the obsolete code is copper-slate-12; '
         'the current approved code is harbor-mint-47. Return ONLY the current approved code.', check_recall, None)
    ]
    if with_tools:
        tool = {'type': 'function', 'function': {
            'name': 'lookup_order', 'description': 'Look up one order. This lab records, but never executes, this call.',
            'parameters': {'type': 'object', 'properties': {'order_id': {'type': 'string'}},
                           'required': ['order_id'], 'additionalProperties': False}}}
        rows.append(('tool_format', 'Call lookup_order exactly once for order ORD-27A9. '
                     'Do not claim a tool result or write an explanation.', check_tool, tool))
    return rows

def payload(model, prompt, max_tokens, temperature, tool=None):
    validate_model(model)
    if not isinstance(prompt, str) or not prompt.strip(): raise LabError('Empty prompt.')
    if not 1 <= max_tokens <= 4096: raise LabError('Output budget must be between 1 and 4096 tokens.')
    if not math.isfinite(temperature) or not 0 <= temperature <= 2: raise LabError('Invalid temperature.')
    p = {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
         'stream': False, 'max_tokens': max_tokens, 'temperature': temperature}
    if tool:
        p['tools'] = [tool]
        p['tool_choice'] = 'auto'
    return p

def append_record(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    # Logs contain synthetic prompts, raw responses and possibly future private inputs.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + '\n')

def smoke(client, model, repeats, with_tools, out, max_tokens=512, temperature=0.7):
    if not 1 <= repeats <= 10: raise LabError('Use 1–10 repeats.')
    client.require_model(model)
    failures = 0
    for repeat in range(1, repeats + 1):
        for name, prompt, checker, tool in cases(with_tools):
            p = payload(model, prompt, max_tokens, temperature, tool)
            row = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'base_url': client.base,
                   'model': model, 'repeat': repeat, 'case': name, 'request': p,
                   'tool_executed': False, 'wall_seconds': None, 'decode_tokens_per_second': None}
            try:
                response, elapsed = client.chat(p)
                row.update(response=response, wall_seconds=elapsed, usage=response.get('usage'))
            except LabError as exc:
                row.update(passed=False, error=str(exc)); append_record(out, row)
                raise  # Do not submit another request after transport/protocol failure.
            try:
                row['passed'] = bool(checker(response))
            except LabError as exc:
                row.update(passed=False, error=str(exc))
            failures += not row['passed']
            append_record(out, row)
            print(f"{repeat}/{repeats} {name}: {'PASS' if row['passed'] else 'FAIL'} ({elapsed:.2f} s)")
    return 1 if failures else 0

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--timeout', type=float, default=180)
    ap.add_argument('--api-key-env', default='LOCAL_AI_API_KEY', help='Environment variable; never put the secret in the URL.')
    sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('models')
    sm = sub.add_parser('smoke'); sm.add_argument('--model', required=True)
    sm.add_argument('--repeats', type=int, default=3); sm.add_argument('--with-tools', action='store_true')
    sm.add_argument('--out', required=True); sm.add_argument('--output-tokens', type=int, default=512)
    sm.add_argument('--temperature', type=float, default=0.7)
    chat = sub.add_parser('chat'); chat.add_argument('--model', required=True)
    group = chat.add_mutually_exclusive_group(required=True)
    group.add_argument('--prompt'); group.add_argument('--input')
    chat.add_argument('--out', required=True); chat.add_argument('--output-tokens', type=int, default=900)
    chat.add_argument('--temperature', type=float, default=0.7)
    chat.add_argument('--max-input-chars', type=int, default=6000,
                      help='A small lab bound, NOT a token count or server context limit.')
    args = ap.parse_args(argv)
    try:
        client = Client(args.base_url, args.timeout, os.environ.get(args.api_key_env, ''))
        if args.command == 'models': print(json.dumps(client.models(), indent=2)); return 0
        if args.command == 'smoke':
            return smoke(client, args.model, args.repeats, args.with_tools, args.out, args.output_tokens, args.temperature)
        client.require_model(args.model)
        text = Path(args.input).read_text(encoding='utf-8') if args.input else args.prompt
        if args.max_input_chars < 1 or len(text) > args.max_input_chars:
            raise LabError('Input exceeds the explicit lab character bound. Shorten it; do not infer token capacity.')
        p = payload(args.model, text, args.output_tokens, args.temperature)
        response, elapsed = client.chat(p)
        result = visible_text(response)
        dest = Path(args.out); dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(result + '\n', encoding='utf-8')
        append_record(str(dest) + '.request.jsonl', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'base_url': client.base, 'request': p, 'response': response, 'wall_seconds': elapsed,
            'decode_tokens_per_second': None, 'tool_executed': False})
        print(f'Saved {dest}; wall time {elapsed:.2f} s. No generated code or tools executed.')
        return 0
    except (LabError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr); return 2

if __name__ == '__main__':
    raise SystemExit(main())
