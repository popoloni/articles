"""Finite matrix runner with retained per-cell evidence and fail-closed aggregation."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import tempfile
import time
import traceback
from uuid import uuid4
from xml.etree import ElementTree as ET
from .common import Recorder, digest, environment, now, read_json, snapshot, write_json
from .oracles import summarize
from .scenarios import Context, SCENARIOS, seed

STARTER = Path(__file__).resolve().parent.parent


def source_identity() -> dict:
    files = [STARTER / 'lab.py', STARTER / 'scenarios.json', *sorted((STARTER / 'sdd_lab').glob('*.py'))]
    hashes = {p.relative_to(STARTER).as_posix(): digest(p.read_bytes()) for p in files}
    return {'files': hashes, 'sha256': digest(json.dumps(hashes, sort_keys=True))}


def load_manifest(path: Path, selected: list[str] | None = None) -> tuple[list[dict], list[str]]:
    data = read_json(path)
    if data.get('schema_version') != 1 or data.get('target') != 'reference-fixture':
        raise ValueError('Unsupported manifest schema or target')
    definitions = data.get('scenarios')
    if not isinstance(definitions, list) or not definitions:
        raise ValueError('A nonempty scenario list is required')
    names: list[str] = []
    cells: list[dict] = []
    for item in definitions:
        name, count = item.get('id'), item.get('repetitions')
        if name not in SCENARIOS or name in names:
            raise ValueError(f'Unknown or duplicate scenario: {name}')
        if type(count) is not int or not 1 <= count <= 20:
            raise ValueError('Repetitions must be integers from 1 to 20')
        names.append(name)
        cells.extend({'id': f'{name}/reference-fixture/{i}', 'scenario': name, 'repetition': i} for i in range(1, count + 1))
    all_ids = [c['id'] for c in cells]
    if selected is not None:
        if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(names):
            raise ValueError('Unknown, duplicate, or empty scenario selection')
        cells = [c for c in cells if c['scenario'] in selected]
    return cells, all_ids


def run_cell(cell: dict, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(destination / 'events.jsonl')
    started = time.perf_counter()
    report = {'schema_version': 1, 'id': cell['id'], 'scenario': cell['scenario'], 'repetition': cell['repetition'],
              'evidence_kind': 'executed-reference-fixture', 'native_cli_observed': False, 'started_at': now()}
    with tempfile.TemporaryDirectory(prefix='sdd-cell-') as temporary:
        scratch = Path(temporary)
        workspace, controller = scratch / 'workspace', scratch / 'controller'
        workspace.mkdir()
        controller.mkdir()
        ctx = Context(workspace, controller, destination, recorder)
        seed(ctx)
        write_json(destination / 'workspace-before.json', snapshot(workspace))
        try:
            checks = SCENARIOS[cell['scenario']](ctx)
            if not checks:
                raise ValueError('A scenario without assertions cannot pass')
            report['checks'] = [c.json() for c in checks]
            report['status'] = 'PASS' if all(c.passed for c in checks) else 'FAIL'
        except Exception as exc:
            report.update(status='ERROR', checks=[], error=f'{type(exc).__name__}: {exc}')
            (destination / 'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
        finally:
            write_json(destination / 'workspace-after.json', snapshot(workspace))
            shutil.copytree(workspace, destination / 'workspace-final')
            shutil.copytree(controller, destination / 'controller-final')
    report.update(finished_at=now(), elapsed_seconds=round(time.perf_counter() - started, 6), scratch_removed=not scratch.exists())
    report['evidence_sha256'] = {p.relative_to(destination).as_posix(): digest(p.read_bytes())
                                 for p in sorted(destination.rglob('*')) if p.is_file()}
    write_json(destination / 'report.json', report)
    return report


def junit(path: Path, reports: list[dict], name: str) -> None:
    suite = ET.Element('testsuite', name=name, tests=str(len(reports)),
                       failures=str(sum(r['status'] == 'FAIL' for r in reports)),
                       errors=str(sum(r['status'] == 'ERROR' for r in reports)), skipped='0')
    for r in reports:
        case = ET.SubElement(suite, 'testcase', name=r['id'], classname=name, time=str(r.get('elapsed_seconds', 0)))
        if r['status'] in ('FAIL', 'ERROR'):
            item = ET.SubElement(case, 'failure' if r['status'] == 'FAIL' else 'error')
            item.text = r.get('error') or '\n'.join(c['name'] for c in r.get('checks', []) if not c['passed'])
    ET.ElementTree(suite).write(path, encoding='utf-8', xml_declaration=True)


def run_matrix(output: Path, manifest: Path | None = None, selected: list[str] | None = None) -> tuple[dict, Path]:
    manifest = manifest or STARTER / 'scenarios.json'
    cells, all_ids = load_manifest(manifest, selected)
    destination = output / ('matrix-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + uuid4().hex[:10])
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest, destination / 'manifest.json')
    reports: list[dict] = []
    interrupted = False
    try:
        for cell in cells:
            report = run_cell(cell, destination / 'cells' / cell['id'].replace('/', '--'))
            reports.append(report)
            print(f"{report['status']:5} {report['id']}", flush=True)
    except KeyboardInterrupt:
        interrupted = True
    summary = summarize([c['id'] for c in cells], reports, all_ids)
    summary.update(schema_version=1, evidence_kind='executed-reference-fixture', model_invocations=0,
                   native_cli_observed=False, environment=environment(), source_identity=source_identity(),
                   created_at=now(), interrupted=interrupted, planned_cells=len(cells), completed_cells=len(reports),
                   passed_cells=sum(r['status'] == 'PASS' for r in reports),
                   assertion_count=sum(len(r.get('checks', [])) for r in reports),
                   cells=[{'id': r['id'], 'status': r['status'], 'report': 'cells/' + r['id'].replace('/', '--') + '/report.json',
                           'sha256': digest((destination / 'cells' / r['id'].replace('/', '--') / 'report.json').read_bytes())} for r in reports])
    if interrupted:
        summary.update(status='FAIL', selected_complete=False, reference_matrix_complete=False)
    junit(destination / 'junit.xml', reports, 'reference-matrix')
    write_json(destination / 'summary.json', summary)
    return summary, destination
