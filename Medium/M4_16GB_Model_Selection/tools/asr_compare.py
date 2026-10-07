#!/usr/bin/env python3
"""Run one MLX Audio recognizer in a separate process using a pinned local snapshot."""
from __future__ import annotations
import argparse
import inspect
import json
from pathlib import Path
import time
from mlx_audio.stt import load
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--snapshot-record', required=True); p.add_argument('--audio', required=True)
p.add_argument('--language', default='English'); p.add_argument('--out', required=True)
a = p.parse_args()
record = json.loads(Path(a.snapshot_record).read_text())
model_path = Path(record['snapshot_path'])
if not model_path.is_dir(): raise SystemExit('Local snapshot missing. Download it online before this test.')
if not Path(a.audio).is_file(): raise SystemExit('Audio input does not exist.')
start = time.perf_counter()
model = load(str(model_path))
loaded = time.perf_counter()
kwargs = {}
sig = inspect.signature(model.generate)
if 'language' in sig.parameters or any(v.kind == inspect.Parameter.VAR_KEYWORD for v in sig.parameters.values()):
    kwargs['language'] = a.language
result = model.generate(a.audio, **kwargs)
finished = time.perf_counter()
text = getattr(result, 'text', None)
if text is None and isinstance(result, dict): text = result.get('text')
if not isinstance(text, str) or not text.strip(): raise SystemExit('Recognizer returned no usable transcript; inspect model/version.')
out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text + '\n')
metrics = {'checkpoint': record, 'language_requested': a.language, 'language_option_applied': bool(kwargs),
           'load_seconds': loaded-start, 'recognition_seconds': finished-loaded,
           'total_seconds': finished-start, 'input': str(Path(a.audio).resolve())}
Path(str(out)+'.metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
print(text)
print(json.dumps(metrics, indent=2))
