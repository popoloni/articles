#!/usr/bin/env python3
"""One local Ollama request. Preserve raw output BEFORE evaluating completion.
No automatic model download, retry, tool execution, or environment modification.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
import time
from local_ai import Client, LocalAIError

def completion_ok(response: dict) -> bool:
    message=response.get('message') or {}
    if not isinstance(message,dict): return False
    return (response.get('done') is True and response.get('done_reason')=='stop'
            and isinstance(message.get('content'),str) and bool(message['content'].strip()))

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url', default='http://127.0.0.1:11434')
    p.add_argument('--model', default='qwen38-local-iq2s:latest')
    p.add_argument('--timeout', type=float, default=300)
    p.add_argument('--ctx', type=int, default=4096)
    p.add_argument('--output-tokens', type=int, default=1024)
    inp=p.add_mutually_exclusive_group(required=True)
    inp.add_argument('--prompt'); inp.add_argument('--input', type=Path)
    p.add_argument('--out-root', type=Path, default=Path('outputs/ollama'))
    a=p.parse_args(argv)
    if not 1<=a.output_tokens<a.ctx<=8192:
        p.error('For this small lab require 1 <= output-tokens < ctx <= 8192.')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=a.out_root/stamp
    folder.mkdir(parents=True, exist_ok=False)
    print('Records:', folder, flush=True)
    try:
        client=Client(a.base_url,timeout=a.timeout)
        digest=client.model_digest(a.model)
        prompt=a.input.read_text(encoding='utf-8') if a.input else a.prompt
        if not prompt or len(prompt)>12000:
            raise LocalAIError('Use a nonempty, bounded prompt (at most 12,000 characters here; not an exact token bound).')
        request={'model':a.model,'messages':[{'role':'user','content':prompt}],
                 'stream':False,'think':False,'keep_alive':0,
                 'options':{'num_ctx':a.ctx,'num_predict':a.output_tokens,'temperature':0}}
        (folder/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (folder/'model-digest.txt').write_text(digest+'\n',encoding='utf-8')
        start=time.perf_counter()
        response=client.request('/api/chat',request)
        wall=time.perf_counter()-start
        (folder/'response.json').write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        message=response.get('message') or {}
        if not isinstance(message,dict):
            raise LocalAIError('Malformed message field; raw response retained.')
        text=message.get('content') or ''
        if not isinstance(text,str):
            raise LocalAIError('Non-text content field; raw response retained.')
        thinking=message.get('thinking') or ''
        if not isinstance(thinking,str):
            raise LocalAIError('Non-text thinking field; raw response retained.')
        (folder/'answer.txt').write_text(text,encoding='utf-8')
        summary={k:response.get(k) for k in ('done','done_reason','prompt_eval_count','eval_count','load_duration','prompt_eval_duration','eval_duration')}
        summary.update(wall_seconds=wall,thinking_characters=len(thinking),complete=completion_ok(response))
        (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2)); print(text)
        if not summary['complete']:
            print('INCOMPLETE: raw response preserved. Inspect it before retrying; do not increase limits blindly.',file=sys.stderr)
            return 1
        print('Complete response; task correctness still requires review.')
        return 0
    except (LocalAIError,OSError,ValueError) as e:
        (folder/'error.txt').write_text(str(e)+'\n',encoding='utf-8')
        print(f'ERROR: {e}. Inspect the server before another request.',file=sys.stderr)
        return 2
if __name__=='__main__': raise SystemExit(main())
