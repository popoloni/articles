#!/usr/bin/env python3
"""Download a chosen Hugging Face revision, recording the resolved commit.
This step is explicitly online and downloads weights; it does not run model code.
Use in the ASR or audio venv where huggingface_hub is installed.
"""
import argparse
import datetime
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('repo'); p.add_argument('--revision', default='main')
p.add_argument('--record', required=True)
a = p.parse_args()
info = HfApi().model_info(a.repo, revision=a.revision)
folder = snapshot_download(repo_id=a.repo, revision=info.sha)
record = {'repo': a.repo, 'revision': info.sha, 'snapshot_path': folder,
          'downloaded_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
out = Path(a.record); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(record, indent=2) + '\n')
print(folder)
