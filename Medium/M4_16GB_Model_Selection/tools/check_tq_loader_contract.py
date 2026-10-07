#!/usr/bin/env python3
"""Read the installed text-server loader contract without importing MLX or TQ.

No model execution, native imports, network access, pip operations or trust changes.
This is a targeted static check, not an end-to-end inference certification.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.machinery
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path
import sys


class ContractError(RuntimeError):
    """The known loader contract is missing, ambiguous or incompatible."""


def unique_child(parent: ast.AST, kind: type, name: str) -> ast.AST:
    matches = [n for n in getattr(parent, 'body', [])
               if isinstance(n, kind) and n.name == name]
    if len(matches) != 1:
        raise ContractError(f'Expected one {kind.__name__} named {name}; found {len(matches)}.')
    return matches[0]


def signature(node: ast.FunctionDef) -> inspect.Signature:
    """Represent defaults with sentinels; never evaluate annotations or code."""
    a = node.args
    ordinary = list(a.posonlyargs) + list(a.args)
    first_default = len(ordinary) - len(a.defaults)
    out = []
    for i, arg in enumerate(ordinary):
        kind = (inspect.Parameter.POSITIONAL_ONLY if i < len(a.posonlyargs)
                else inspect.Parameter.POSITIONAL_OR_KEYWORD)
        default = inspect.Parameter.empty if i < first_default else None
        out.append(inspect.Parameter(arg.arg, kind, default=default))
    if a.vararg:
        out.append(inspect.Parameter(a.vararg.arg, inspect.Parameter.VAR_POSITIONAL))
    for arg, default_node in zip(a.kwonlyargs, a.kw_defaults):
        default = inspect.Parameter.empty if default_node is None else None
        out.append(inspect.Parameter(arg.arg, inspect.Parameter.KEYWORD_ONLY, default=default))
    if a.kwarg:
        out.append(inspect.Parameter(a.kwarg.arg, inspect.Parameter.VAR_KEYWORD))
    return inspect.Signature(out)


def check_sources(server_source: str, wrapper_source: str) -> dict:
    try:
        server_tree = ast.parse(server_source)
        tq_tree = ast.parse(wrapper_source)
        provider = unique_child(server_tree, ast.ClassDef, 'ModelProvider')
        method = unique_child(provider, ast.FunctionDef, '_load')
        patch = unique_child(tq_tree, ast.FunctionDef, '_patch_loader')
        loader = unique_child(patch, ast.FunctionDef, '_tq_aware_load')
        sig = signature(loader)
    except (SyntaxError, TypeError, ValueError) as exc:
        raise ContractError(f'Cannot inspect known source layout: {exc}') from exc
    calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == 'load']
    if not calls:
        raise ContractError('No bare load(...) call in ModelProvider._load; inspect this source manually.')
    checked = []
    for call in calls:
        if any(isinstance(n, ast.Starred) for n in call.args) or any(k.arg is None for k in call.keywords):
            raise ContractError('Dynamic *args/**kwargs at the load call cannot be verified statically.')
        keys = [k.arg for k in call.keywords]
        try:
            sig.bind(*[None] * len(call.args), **dict.fromkeys(keys))
        except TypeError as exc:
            raise ContractError(
                f'Loader mismatch at server line {call.lineno}: {exc}. '
                f'Server keywords={keys}; TurboQuant parameters={list(sig.parameters)}. '
                'Do not start inference or silence this with trust_remote_code=True. '
                'For the guide\'s TurboQuant 0.28.0 text environment, restore the '
                'released MLX-LM 0.31.3 wheel and rerun this check.'
            ) from exc
        checked.append({'line': call.lineno, 'positional_arguments': len(call.args), 'keywords': keys})
    return {'passed': True, 'scope': 'static text-server loader call binding only',
            'loader_parameters': list(sig.parameters), 'checked_calls': checked,
            'models_loaded': False, 'native_modules_imported': False}


def installed_source(distribution: str, package: str, filename: str) -> tuple[str, dict]:
    dist = metadata.distribution(distribution)
    # PathFinder does not execute package/__init__.py. Refuse shadows / editable
    # layouts rather than reporting a metadata path that Python would not use.
    spec = importlib.machinery.PathFinder.find_spec(package, sys.path)
    locations = list(spec.submodule_search_locations or []) if spec else []
    if len(locations) != 1:
        raise ContractError(f'Cannot locate one unambiguous {package} package directory.')
    actual = (Path(locations[0]) / filename).resolve()
    advertised = Path(dist.locate_file(f'{package}/{filename}')).resolve()
    if actual != advertised:
        raise ContractError(f'{package} source shadows its distribution: {actual} != {advertised}. '
                            'Inspect this editable/custom installation before replacing packages.')
    raw = actual.read_bytes()
    if len(raw) > 4_000_000:
        raise ContractError('Unexpected source size; inspect manually.')
    info = {'distribution': distribution, 'version': dist.version,
            'source_path': str(actual), 'source_sha256': hashlib.sha256(raw).hexdigest()}
    # Merely reads package metadata; this does not fetch a URL.
    direct = dist.read_text('direct_url.json')
    if direct:
        try:
            info['direct_url'] = json.loads(direct)
        except ValueError:
            info['direct_url'] = 'unparseable metadata'
    return raw.decode('utf-8'), info


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', help='Optional NEW JSON report path; existing files are not overwritten.')
    args = parser.parse_args(argv)
    report = {'python': sys.executable, 'passed': False}
    try:
        wrapper, tq = installed_source('turboquant-mlx-full', 'turboquant_mlx', 'serve.py')
        server, mlx = installed_source('mlx-lm', 'mlx_lm', 'server.py')
        report.update(turboquant=tq, mlx_lm=mlx)
        report.update(check_sources(server, wrapper))
    except (ContractError, metadata.PackageNotFoundError, OSError, UnicodeError) as exc:
        report['error'] = str(exc)
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        try:
            path = Path(args.out).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8') as handle:
                handle.write(text + '\n')
        except OSError as exc:
            print(f'ERROR saving report: {exc}', file=sys.stderr)
            return 2
    if report['passed']:
        print('Loader call contract: PASS. This did not load or test the model.')
        return 0
    print('Loader call contract: FAIL. Do not start the inference test.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
