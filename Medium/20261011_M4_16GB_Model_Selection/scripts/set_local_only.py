#!/usr/bin/env python3
"""Merge Ollama's documented cloud-disable setting, preserving other settings."""
import datetime
import json
import os
from pathlib import Path
import shutil
p = Path.home() / '.ollama' / 'server.json'
p.parent.mkdir(parents=True, exist_ok=True)
settings = {}
if p.exists():
    settings = json.loads(p.read_text())
    if not isinstance(settings, dict): raise SystemExit('Expected an object; configuration not changed.')
    backup = p.with_name('server.json.backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(p, backup); os.chmod(backup, 0o600)
    print('Backup:', backup)
settings['disable_ollama_cloud'] = True
p.write_text(json.dumps(settings, indent=2) + '\n'); os.chmod(p, 0o600)
print('Saved:', p, '\nRestart Ollama and verify the cloud-disabled message in its log.')
