#!/usr/bin/env python3
"""Native Ollama Python 0.6.3 example; requires a local Ollama 0.35+ server.

Install: python -m pip install 'ollama==0.6.3'
Run: python examples_ollama/systemone.py --model tev1:0.8b
No cloud provider or API key is required by the loopback Ollama service.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='tev1:0.8b')
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if not 0 < args.timeout <= 300:
        parser.error('Use a positive timeout of at most 300 seconds')
    try:
        from ollama import Client
    except ImportError:
        print("Install the native SDK: python -m pip install 'ollama==0.6.3'", file=sys.stderr)
        return 2
    request = json.loads((Path(__file__).parent / 'triage_request.json').read_text())
    client = Client(host='http://127.0.0.1:11434', timeout=args.timeout)
    if not hasattr(client, 'systemone'):
        print('This SDK does not expose System One. Use ollama-python 0.6.3 or newer.', file=sys.stderr)
        return 2
    try:
        response = client.systemone(model=args.model, state=request['state'],
                                    questions=request['questions'], keep_alive='10m')
        data = response.model_dump()
        # Preserve typed semantics; never rename confidence to probability-correct.
        if not isinstance(data.get('answers'), dict):
            raise ValueError('Missing answers object')
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f'Local decision request failed: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
