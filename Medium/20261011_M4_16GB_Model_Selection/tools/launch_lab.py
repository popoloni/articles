#!/usr/bin/env python3
"""Start ONE standalone local model after its download and trust review.

Never installs dependencies, downloads models, changes wired memory, executes
model-proposed tools, or configures Kowalski. --dry-run only prints the command.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import re
import fcntl
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import socket
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
class LaunchError(RuntimeError):pass

def specs():return json.loads((ROOT/'config/standalone-models.json').read_text())['models']

def command(profile,lab,disk_cache=False,expert_cache_gb=4):
    all_specs=specs()
    if profile not in all_specs:raise LaunchError('Unknown model profile.')
    s=all_specs[profile];lab=Path(lab).expanduser();model=lab/'models'/profile
    runtime=s['runtime'];port=str(s['port'])
    if runtime=='turboquant-vlm-diagnostic':
        raise LaunchError('Qwen3.8 TQ diagnostic is deliberately manual. Read section L10; it is not a 16GB coding profile.')
    if disk_cache and runtime not in ('turboquant','turboquant-stream'):
        raise LaunchError('Disk-cache switch here applies only to the verified text TurboQuant server path.')
    sampling=['--temp','0.7','--top-p','0.95' if profile.startswith('bonsai') else '0.8','--top-k','20']
    template=json.dumps({'enable_thinking':False},separators=(',',':'))
    if runtime in ('prism-llama','llama'):
        binary=str(lab/'Bonsai-demo/bin/mac/llama-server') if runtime=='prism-llama' else (shutil.which('llama-server') or 'llama-server')
        cmd=[binary,'-m',str(model/s['file']),'--host','127.0.0.1','--port',port,'--alias',profile,
             '-ngl','99' if runtime=='prism-llama' else 'auto','-fa','on','-c','4096','-np','1',
             '--jinja',*sampling,'--min-p','0','--chat-template-kwargs',template]
        if runtime=='prism-llama':cmd+=['--reasoning-budget','0']
        else:
            cmd+=['-b','128','-ub','128','--presence-penalty','1.5','--repeat-penalty','1.0','--offline']
            cmd[cmd.index('--chat-template-kwargs')+1]=json.dumps({'enable_thinking':False,'preserve_thinking':False},separators=(',',':'))
        return cmd
    if runtime in ('mlx','mlx-custom'):
        venv='venv-ternary' if runtime=='mlx-custom' else 'venv-mlx'
        if runtime=='mlx':template=json.dumps({'enable_thinking':False,'preserve_thinking':False},separators=(',',':'))
        return [str(lab/venv/'bin/mlx_lm.server'),'--model',str(model),'--host','127.0.0.1','--port',port,
                *sampling,'--max-tokens','512','--chat-template-args',template,'--prompt-concurrency','1',
                '--decode-concurrency','1','--prefill-step-size','128','--prompt-cache-size','1']
    if runtime in ('turboquant','turboquant-stream'):
        if not 1<=expert_cache_gb<=8:raise LaunchError('Lab expert cache must be between 1 and 8 GB.')
        cmd=[str(lab/'venv-tq/bin/turboquant-serve'),'--model',str(model),'--host','127.0.0.1','--port',port,
             '--kv-bits','8','--tool-syntax-greedy','--prefill-step-size','128',*sampling,
             '--chat-template-args',template,'--prompt-concurrency','1']
        if runtime=='turboquant-stream':cmd+=['--cache-budget-gb',str(expert_cache_gb),'--max-active-experts','0']
        if disk_cache:cmd+=['--disk-cache']
        return cmd
    raise LaunchError('Runtime is not implemented.')

def check_snapshot(profile,lab):
    s=specs()[profile];folder=Path(lab)/'models'/profile
    marker=folder/'_SNAPSHOT.json'
    if not marker.exists():raise LaunchError('No tracked snapshot. Use checkpoint_fetch plan/download first.')
    record=json.loads(marker.read_text())
    if record.get('repo')!=s['repo'] or record.get('profile')!=profile or record.get('download_complete') is not True:
        raise LaunchError('Snapshot does not match the profile or is incomplete.')
    for item in record.get('files',[]):
        p=folder/item['name']
        if not p.is_file() or p.stat().st_size!=item['size']:
            raise LaunchError(f'File missing or changed size: {item["name"]}')
    return folder,record

# TurboQuant consumes these options before delegating to mlx_lm.server.
# They can be missing from the latter's --help. Do not infer support from a
# version string or silently remove any option: inspect the installed parser.
TQ_WRAPPER_PARSERS = {
    '--kv-bits': '_extract_kv_args',
    '--tool-syntax-greedy': '_extract_tool_syntax_greedy_args',
    '--cache-budget-gb': '_extract_stream_args',
    '--max-active-experts': '_extract_stream_args',
    '--disk-cache': '_extract_disk_cache_args',
}

TQ_SOURCE_PROBE = r"""
import importlib.metadata as md
import hashlib
import json
from pathlib import Path

dist = md.distribution('turboquant-mlx-full')
eps = [e for e in dist.entry_points
       if e.group == 'console_scripts' and e.name == 'turboquant-serve']
if len(eps) != 1 or eps[0].value.strip() != 'turboquant_mlx.serve:main':
    raise SystemExit('Unrecognized turboquant-serve entry point; inspect this installation.')
path = Path(dist.locate_file('turboquant_mlx/serve.py'))
raw = path.read_bytes()
if len(raw) > 2000000:
    raise SystemExit('Unexpectedly large installed server source; inspect manually.')
print(json.dumps({'distribution': dist.metadata['Name'], 'version': dist.version,
                  'entry_point': eps[0].value, 'source_path': str(path.resolve()),
                  'source_sha256': hashlib.sha256(raw).hexdigest(),
                  'source': raw.decode('utf-8')}))
"""

def wrapper_flags_from_source(source):
    """Inspect declarations in known, called pre-parsers; execute no source.

    A declaration is supporting evidence for CLI acceptance, not validation of
    the parser's semantics or of the model. Unknown source layouts fail closed.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, TypeError) as exc:
        raise LaunchError(f'Cannot parse installed TurboQuant source: {exc}') from exc
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    main = functions.get('main')
    if main is None:
        raise LaunchError('Installed TurboQuant source has no recognized main function.')
    # The reviewed wrapper invokes its pre-parsers directly at function scope.
    called = set()
    for statement in main.body:
        value = getattr(statement, 'value', None)
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            called.add(value.func.id)
    evidence = {}
    for flag, name in TQ_WRAPPER_PARSERS.items():
        function = functions.get(name)
        if function is None or name not in called:
            continue
        parser_names = set()
        for statement in function.body:
            if not isinstance(statement, ast.Assign):
                continue
            value = statement.value
            if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == 'argparse' and value.func.attr == 'ArgumentParser'):
                parser_names.update(t.id for t in statement.targets if isinstance(t, ast.Name))
        parsed = set()
        declarations = {}
        for node in ast.walk(function):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in parser_names):
                continue
            if node.func.attr == 'parse_known_args':
                parsed.add(node.func.value.id)
            if node.func.attr == 'add_argument':
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        declarations[arg.value] = node.func.value.id
        if flag in declarations and declarations[flag] in parsed:
            evidence[flag] = name
    return evidence


def inspect_turboquant(cmd):
    """Read the installed wheel using its OWN venv, without importing MLX/TQ."""
    executable = Path(cmd[0]).expanduser()
    python = executable.parent / 'python'
    if executable.name != 'turboquant-serve' or not python.is_file():
        raise LaunchError('Cannot locate the TurboQuant venv Python for source inspection.')
    try:
        shim = executable.read_text(encoding='utf-8')
        if not re.search(r'from\s+turboquant_mlx\.serve\s+import\s+main\b', shim):
            raise LaunchError('Unrecognized turboquant-serve launcher; inspect it before proceeding.')
        result = subprocess.run([str(python), '-I', '-c', TQ_SOURCE_PROBE],
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise LaunchError('Cannot inspect installed TurboQuant entry-point source: '
                              + (result.stderr.strip() or result.stdout.strip()))
        record = json.loads(result.stdout)
        source = record.pop('source')
        if hashlib.sha256(source.encode('utf-8')).hexdigest() != record['source_sha256']:
            raise LaunchError('Installed source-inspection hash mismatch.')
        record['registered_wrapper_flags'] = wrapper_flags_from_source(source)
        return record
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
        raise LaunchError(f'Cannot inspect installed TurboQuant source: {exc}') from exc


def flags_in_command(cmd):
    return {x.split('=', 1)[0] for x in cmd[1:]
            if x.startswith('--') or x in ('-m', '-ngl', '-fa', '-c', '-np', '-b', '-ub')}


def validate_flags(cmd, help_text, wrapper_evidence=None):
    evidence = wrapper_evidence or {}
    is_tq = Path(cmd[0]).name == 'turboquant-serve'
    missing = []
    for flag in sorted(flags_in_command(cmd)):
        if is_tq and flag in TQ_WRAPPER_PARSERS:
            if evidence.get(flag) != TQ_WRAPPER_PARSERS[flag]:
                missing.append(flag)
        elif not re.search(r'(?<![\w-])' + re.escape(flag) + r'(?![\w-])', help_text):
            missing.append(flag)
    if missing:
        raise LaunchError('Installed runtime support could not be verified for: '
                          + ', '.join(missing)
                          + '. No flags were removed; inspect the saved help/source report.')


def check_flags(cmd, report=None):
    try:
        run = subprocess.run([cmd[0], '--help'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LaunchError(f'Cannot inspect runtime help: {exc}') from exc
    text = run.stdout + '\n' + run.stderr
    if report is None:
        report = {}
    report['help_returncode'] = run.returncode
    report['help_text'] = text
    if run.returncode != 0:
        raise LaunchError('Runtime --help failed. Fix its installation before loading weights.')
    wrapper = {}
    if Path(cmd[0]).name == 'turboquant-serve':
        record = inspect_turboquant(cmd)
        report['turboquant'] = record
        wrapper = record['registered_wrapper_flags']
    validate_flags(cmd, text, wrapper)
    report['verified_flags'] = sorted(flags_in_command(cmd))
    report['no_flags_removed'] = True
    return text

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('profile',choices=sorted(specs()));ap.add_argument('--lab',required=True)
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--dry-run',action='store_true')
    mode.add_argument('--preflight-only',action='store_true',help='Check local snapshot, runtime help and installed wrapper source; do not load weights or start a server.')
    ap.add_argument('--disk-cache',action='store_true')
    ap.add_argument('--expert-cache-gb',type=int,default=4)
    ap.add_argument('--accept-checkpoint-code',action='store_true',help='Only after reviewing the recorded ternary checkpoint revision.')
    ap.add_argument('--accept-tight-memory',action='store_true',help='Acknowledgment for tight resident profiles; changes no system limits.')
    a=ap.parse_args(argv)
    try:
        lab=Path(a.lab).expanduser().resolve();s=specs()[a.profile]
        cmd=command(a.profile,lab,a.disk_cache,a.expert_cache_gb)
        print(shlex.join(cmd),flush=True)
        if a.dry_run:return 0
        if platform.system()!='Darwin' or platform.machine()!='arm64':raise LaunchError('Native Apple Silicon macOS is required.')
        folder,record=check_snapshot(a.profile,lab)
        if s.get('custom_code') and not a.accept_checkpoint_code:
            raise LaunchError('This checkpoint executes custom Python/Metal. Review it, then explicitly acknowledge trust.')
        if a.profile in ('qwen36-asym','qwen38-iq3xxs','qwen38-mlx3') and not a.accept_tight_memory:
            raise LaunchError('Tight memory profile: read the guide, then explicitly acknowledge this experiment.')
        if s['runtime']=='mlx':
            cfg=json.loads((folder/'config.json').read_text())
            if cfg.get('model_file') or cfg.get('auto_map'):
                raise LaunchError('Unexpected custom-code loader in a standard-MLX profile. Inspect before proceeding.')
        logs=lab/'logs';logs.mkdir(parents=True,exist_ok=True)
        report={'profile':a.profile,'command':cmd,'checkpoint_revision':record['revision']}
        try:
            help_text=check_flags(cmd,report)
        except LaunchError as exc:
            report['error']=str(exc)
            (logs/f'{a.profile}-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
            raise
        (logs/f'{a.profile}-runtime-help.txt').write_text(help_text)
        (logs/f'{a.profile}-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
        if 'turboquant' in report:
            tq=report['turboquant']
            print(f"Verified installed {tq['distribution']} {tq['version']} wrapper parser: "
                  + ', '.join(sorted(tq['registered_wrapper_flags'])),flush=True)
        if a.preflight_only:
            print('Preflight passed. No model loaded, server started, or system memory limit changed.',flush=True)
            return 0
        with socket.socket() as probe:
            probe.settimeout(0.5)
            if probe.connect_ex(('127.0.0.1',s['port']))==0:
                raise LaunchError('Port already occupied; stop the existing server normally.')
        # Keep lock inherited by the runtime after exec, across different lab profiles.
        lock=open(lab/'standalone.lock','a+')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise LaunchError('Another launcher-managed lab model is running. Stop it first.')
        os.set_inheritable(lock.fileno(),True)
        (logs/f'{a.profile}-launch.json').write_text(json.dumps({'command':cmd,'repo':record['repo'],
            'revision':record['revision'],'os':platform.platform(),
            'preflight_report':str(logs/f'{a.profile}-preflight.json'),
            'note':'No wired cap changed; not an inference validation.'},indent=2)+'\n')
        # These settings prohibit Hub fetches but do not sandbox arbitrary third-party code.
        env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['TRANSFORMERS_OFFLINE']='1'
        env['HF_HUB_DISABLE_TELEMETRY']='1'
        print('One local model only. Other applications are not controlled by this lock. Ctrl+C stops this server.',flush=True)
        os.execvpe(cmd[0],cmd,env)
    except (LaunchError,OSError,ValueError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
