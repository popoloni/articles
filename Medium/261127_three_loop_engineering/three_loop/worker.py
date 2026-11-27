"""Trusted verifier worker. Runs only catalogue code supplied by the controller.
Process separation is NOT an OS sandbox. Never use this for arbitrary code.
"""
import hashlib
import json
from pathlib import Path
import sys


def main():
    request = json.load(sys.stdin)
    source = Path(sys.argv[1]).read_bytes()
    source_sha = hashlib.sha256(source).hexdigest()
    if source_sha != request['source_sha']:
        raise ValueError('Source hash mismatch')
    namespace = {}
    exec(compile(source, 'trusted_catalogue_patch.py', 'exec'), namespace)
    transform = namespace['transform']
    rows = []
    for case in request['cases']:
        try:
            actual = transform(case['value'])
            passed = type(actual) is type(case['expected']) and actual == case['expected']
        except Exception as exc:
            actual, passed = {'error': type(exc).__name__}, False
        rows.append({**case, 'actual': actual, 'passed': passed})
    print(json.dumps({'source_sha': source_sha, 'rows': rows}))


if __name__ == '__main__':
    main()
