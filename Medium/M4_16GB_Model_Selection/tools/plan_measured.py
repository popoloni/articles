#!/usr/bin/env python3
"""Plan one checkpoint using a revision recorded in the supplied experiment.
No weights are downloaded; no checkpoint code is imported. Missing historical
revisions require explicit permission to resolve a new, unmeasured revision.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from checkpoint_fetch import make_plan, FetchError, catalog

ROOT = Path(__file__).resolve().parents[1]

def select_revision(profile: str, records: dict, allow_unrecorded: bool) -> str:
    if profile in records:
        return records[profile]['revision']
    if not allow_unrecorded:
        raise FetchError('The archive contains no recorded revision for this profile. '
                         'Use --allow-unrecorded only for a new experiment, not an exact historical reproduction.')
    return 'main'

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', choices=sorted(catalog()))
    p.add_argument('--lab', required=True)
    p.add_argument('--allow-unrecorded', action='store_true')
    a=p.parse_args(argv)
    try:
        records=json.loads((ROOT/'config/measured-checkpoints.json').read_text())
        revision=select_revision(a.profile,records,a.allow_unrecorded)
        if revision=='main':
            print('NEW EXPERIMENT: resolving current metadata; no historical checkpoint SHA is available.')
        else:
            print('Using recorded checkpoint revision:', revision)
        make_plan(a.profile,a.lab,revision)
        print('Review the plan. Download is a separate checkpoint_fetch.py download command.')
        return 0
    except (FetchError, OSError, ValueError, ImportError) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(main())
