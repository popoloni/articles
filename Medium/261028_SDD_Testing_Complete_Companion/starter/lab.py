#!/usr/bin/env python3
"""Run from this directory: python lab.py run; python lab.py mutations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print('Python 3.11 or later is required.', file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description='SDD companion: observable contracts, retained evidence, no implicit model calls.')
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run', help='Run the offline reference matrix')
    run.add_argument('--scenario', action='append', help='Select a family; all repetitions are retained')
    run.add_argument('--manifest', type=Path)
    run.add_argument('--output', type=Path, default=Path('runs'))
    mut = sub.add_parser('mutations', help='Prove six deliberate defects cause failed assertions')
    mut.add_argument('--output', type=Path, default=Path('runs'))
    sub.add_parser('list', help='List reference scenarios and repetitions')
    live = sub.add_parser('ollama', help='Opt-in live call: tests our gateway, not native coding-agent CLIs')
    live.add_argument('--model', required=True)
    live.add_argument('--expected-digest', required=True)
    live.add_argument('--endpoint', default='http://127.0.0.1:11434')
    live.add_argument('--timeout', type=float, default=30.0)
    live.add_argument('--output', type=Path, default=Path('runs'))
    args = parser.parse_args(argv)
    try:
        if args.command == 'run':
            from sdd_lab.runner import run_matrix
            summary, destination = run_matrix(args.output, args.manifest, args.scenario)
        elif args.command == 'mutations':
            from sdd_lab.mutations import run_mutations
            summary, destination = run_mutations(args.output)
        elif args.command == 'list':
            from sdd_lab.runner import STARTER, load_manifest
            cells, _ = load_manifest(STARTER / 'scenarios.json')
            print(json.dumps(cells, indent=2))
            return 0
        else:
            from sdd_lab.live import run_ollama
            summary, destination = run_ollama(args.output, args.model, args.expected_digest, args.endpoint, args.timeout)
        print(json.dumps({'status': summary['status'], 'report': str(destination / 'summary.json')}, indent=2))
        return 0 if summary['status'] == 'PASS' else 1
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
