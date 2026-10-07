#!/usr/bin/env python3
"""Plan a selected checkpoint at an exact Hub SHA, then explicitly download it.

Planning downloads metadata only. Download never imports checkpoint code.
No full-repository GGUF download, model inference or automatic model substitution.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'config/standalone-models.json'
class FetchError(RuntimeError): pass

def catalog():
    return json.loads(MANIFEST.read_text())['models']

def safe_filename(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '\\' not in name and '..' not in p.parts and '.' not in p.parts and not name.startswith('/')

def select_names(spec, names):
    if not all(safe_filename(n) for n in names): raise FetchError('Unsafe repository filename.')
    if spec.get('file'):
        target = spec['file']
        if target not in names: raise FetchError(f'Exact file is absent: {target}. No substitute selected.')
        selected = [n for n in names if n == target or ('/' not in n and
                    (n.lower().startswith(('license','notice','readme'))))]
    else:
        patterns = ['*.safetensors','*.json','*.txt','*.model','*.jinja','*.tiktoken','*.py','*.md','LICENSE*','NOTICE*']
        selected = [n for n in names if '/' not in n and any(fnmatch.fnmatch(n, p) for p in patterns)]
        if 'config.json' not in selected or not any(n.endswith('.safetensors') for n in selected):
            raise FetchError('Expected root config and safetensors shards are absent; inspect the new layout manually.')
    return sorted(selected)

def validate_plan(plan):
    if plan.get('schema') != 1: raise FetchError('Unknown plan schema.')
    profile = plan.get('profile')
    specs = catalog()
    if profile not in specs or plan.get('repo') != specs[profile]['repo']:
        raise FetchError('Plan does not match this catalog.')
    if not re.fullmatch(r'[a-fA-F0-9]{40}', str(plan.get('revision',''))):
        raise FetchError('Expected a full 40-character Hub commit SHA.')
    files = plan.get('files')
    if not isinstance(files, list) or not files: raise FetchError('No planned files.')
    names = [f.get('name', '') for f in files]
    if len(set(names)) != len(names) or select_names(specs[profile], names) != sorted(names):
        raise FetchError('Plan contains duplicate, unselected or unsafe files.')
    if any(type(f.get('size')) is not int or f['size'] < 0 for f in files):
        raise FetchError('All file sizes must be known nonnegative integers.')
    if plan.get('total_bytes') != sum(f['size'] for f in files): raise FetchError('Plan size sum mismatch.')
    return specs[profile]

def make_plan(profile, lab, revision='main'):
    specs = catalog()
    if profile not in specs: raise FetchError('Unknown profile.')
    from huggingface_hub import HfApi  # Lazy: model-free tests need no Hub package.
    spec = specs[profile]
    info = HfApi().model_info(spec['repo'], revision=revision, files_metadata=True)
    siblings = {f.rfilename:f for f in info.siblings}
    names = select_names(spec, list(siblings))
    files=[]
    for name in names:
        item=siblings[name]
        if item.size is None: raise FetchError(f'No reliable byte size for {name}; inspect before download.')
        lfs = getattr(item, 'lfs', None)
        digest = (lfs.get('sha256') if isinstance(lfs, dict) else getattr(lfs, 'sha256', None)) if lfs else None
        files.append({'name':name,'size':item.size,'lfs_sha256':digest})
    lab=Path(lab).expanduser().resolve()
    result={'schema':1,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'profile':profile,'repo':spec['repo'],'revision':info.sha,
            'destination':str(lab/'models'/profile),'files':files,
            'total_bytes':sum(f['size'] for f in files),
            'note':'File storage estimate only. Does not certify runtime memory or checkpoint-code safety.'}
    validate_plan(result)
    path=lab/'plans'/f'{profile}.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{profile}: {result['repo']} @ {result['revision']}")
    print(f"Selected {len(files)} files: {result['total_bytes']/1e9:.3f} GB / {result['total_bytes']/2**30:.3f} GiB")
    print(f'Plan: {path}\nDestination: {result["destination"]}')
    code=[f['name'] for f in files if f['name'].endswith('.py')]
    if code: print('Checkpoint code will be downloaded, not executed: '+', '.join(code))
    return path

def validate_index(folder, names):
    for name in names:
        if name.endswith('.safetensors.index.json'):
            index=json.loads((folder/name).read_text())
            required=set(index.get('weight_map',{}).values())
            if not required.issubset(set(names)):
                raise FetchError('Shard index refers to unselected files. Stop and inspect repository layout.')

def download(plan_path, verify=False):
    plan=json.loads(Path(plan_path).read_text());validate_plan(plan)
    dest=Path(plan['destination']).expanduser()
    # An existing snapshot may be resumed only at the same repository revision.
    marker=dest/'_SNAPSHOT.json'
    if marker.exists():
        previous=json.loads(marker.read_text())
        if (previous.get('repo'),previous.get('revision')) != (plan['repo'],plan['revision']):
            raise FetchError('Destination belongs to another revision. Use a separate lab path; nothing overwritten.')
    elif dest.exists() and any(dest.iterdir()):
        raise FetchError('Nonempty untracked destination. Move it aside or use a separate lab directory.')
    dest.mkdir(parents=True,exist_ok=True)
    missing=sum(f['size'] for f in plan['files'] if not (dest/f['name']).exists())
    # Reserve estimate; additional cache/temp allocation may still be required by the downloader.
    reserve=int(missing*1.15)+2*2**30
    if shutil.disk_usage(dest).free < reserve:
        raise FetchError(f'Insufficient planned free space; reserve about {reserve/1e9:.1f} GB. No weights downloaded.')
    marker.write_text(json.dumps({**plan,'download_complete':False},indent=2)+'\n')
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=plan['repo'],revision=plan['revision'],
                      local_dir=str(dest),allow_patterns=[f['name'] for f in plan['files']])
    for f in plan['files']:
        p=dest/f['name']
        if not p.is_file() or p.stat().st_size != f['size']: raise FetchError(f'File size mismatch: {f["name"]}')
        if verify and f.get('lfs_sha256'):
            h=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(8*1024*1024),b''): h.update(block)
            if h.hexdigest()!=f['lfs_sha256']: raise FetchError(f'LFS SHA256 mismatch: {f["name"]}')
    validate_index(dest,[f['name'] for f in plan['files']])
    marker.write_text(json.dumps({**plan,'download_complete':True,'lfs_hashes_checked':verify},indent=2)+'\n')
    print(f'Complete: {dest}. No model loaded and no checkpoint code executed.')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    a=sub.add_parser('plan');a.add_argument('profile',choices=sorted(catalog()))
    a.add_argument('--lab',required=True);a.add_argument('--revision',default='main')
    a=sub.add_parser('download');a.add_argument('--plan',required=True);a.add_argument('--verify-sha256',action='store_true')
    args=p.parse_args(argv)
    try:
        if args.command=='list':
            for key,spec in catalog().items(): print(f"{key:24} {spec['approx_download_gb']:6.2f} GB  {spec['repo']}")
        elif args.command=='plan':make_plan(args.profile,args.lab,args.revision)
        else:download(args.plan,args.verify_sha256)
        return 0
    except (FetchError,OSError,ValueError,ImportError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
