#!/usr/bin/env python3
"""Build a verified, deterministic companion ZIP without external dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

from verify_package import audit_links, verify_hashes

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = 'SDD_Testing_Companion'
EXCLUDED_NAMES = {'.git', '.venv', '__pycache__', 'runs', 'test-results',
                  'validation-runs', 'validation-container', '.DS_Store'}
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def deliverable_files(root: Path = ROOT) -> list[Path]:
    """Keep evidence, including final fixture trees, while omitting local outputs."""
    files = []

    def visit(folder: Path) -> None:
        for path in sorted(folder.iterdir()):
            if path.name in EXCLUDED_NAMES:
                continue
            if path.is_symlink():
                raise ValueError(f'Symlink is not a release input: {path}')
            if path.is_dir():
                visit(path)
            elif path.suffix == '.pyc':
                continue
            elif path.is_file():
                relative = path.relative_to(root).as_posix()
                if '\n' in relative or '\r' in relative:
                    raise ValueError(f'Newlines are not supported in release paths: {relative!r}')
                files.append(path)
            else:
                raise ValueError(f'Not a regular release file: {path}')

    visit(root)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def write_manifest(root: Path = ROOT) -> None:
    """Refresh only the current manifest; archived historical manifests are inputs."""
    lines = []
    for path in deliverable_files(root):
        if path == root / 'SHA256SUMS':
            continue
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f'{checksum}  {path.relative_to(root).as_posix()}\n')
    (root / 'SHA256SUMS').write_text(''.join(lines), encoding='utf-8')


def snapshot_files(root: Path = ROOT) -> dict[str, tuple[bytes, int]]:
    snapshot = {}
    for path in deliverable_files(root):
        mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
        snapshot[path.relative_to(root).as_posix()] = (path.read_bytes(), mode)
    return snapshot


def verify_snapshot(snapshot: dict[str, tuple[bytes, int]]) -> dict:
    """Run existing verifiers against exactly the files being distributed."""
    # A staged copy prevents excluded caches or local runs from affecting link checks.
    with tempfile.TemporaryDirectory(prefix='sdd-release-check-') as temporary:
        staged = Path(temporary)
        for name, (content, _) in snapshot.items():
            path = staged / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        checks = {'links': audit_links(staged), 'integrity': verify_hashes(staged)}
        if any(check['status'] != 'PASS' for check in checks.values()):
            raise ValueError('Package verification failed: ' + json.dumps(checks, sort_keys=True))
        manifest = snapshot['SHA256SUMS'][0].decode('utf-8')
        covered = {line.split('  ', 1)[1] for line in manifest.splitlines()}
        expected = set(snapshot) - {'SHA256SUMS'}
        if covered != expected:
            raise ValueError('Manifest coverage differs from release inputs: ' + json.dumps({
                'unlisted': sorted(expected - covered), 'unexpected': sorted(covered - expected)}))
        return checks


def verify_archive(path: Path, snapshot: dict[str, tuple[bytes, int]]) -> None:
    expected_names = [f'{ARCHIVE_ROOT}/{name}' for name in sorted(snapshot)]
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != expected_names:
            raise ValueError('Archive member names differ from release inputs')
        for name, (content, _) in snapshot.items():
            if archive.read(f'{ARCHIVE_ROOT}/{name}') != content:
                raise ValueError(f'Archive bytes differ from release input: {name}')


def build_release(output: Path, *, root: Path = ROOT,
                  refresh_manifest: bool = False) -> dict:
    root = root.resolve()
    output = output.absolute()
    sidecar = output.with_name(output.name + '.sha256')
    if output.suffix.lower() != '.zip':
        raise ValueError('--output must name a .zip file')
    if output.resolve().is_relative_to(root):
        raise ValueError('Release output must be outside the companion directory')
    for destination in (output, sidecar):
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f'Refusing to overwrite retained release: {destination}')
    if refresh_manifest:
        write_manifest(root)
    snapshot = snapshot_files(root)
    checks = verify_snapshot(snapshot)
    output.parent.mkdir(parents=True, exist_ok=True)
    created_output = created_sidecar = False
    try:
        with tempfile.TemporaryDirectory(prefix='.sdd-release-', dir=output.parent) as temporary:
            staged_zip = Path(temporary) / 'release.zip'
            with zipfile.ZipFile(staged_zip, 'w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9) as archive:
                for name, (content, mode) in sorted(snapshot.items()):
                    info = zipfile.ZipInfo(f'{ARCHIVE_ROOT}/{name}', FIXED_TIMESTAMP)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED,
                                     compresslevel=9)
            verify_archive(staged_zip, snapshot)
            if snapshot_files(root) != snapshot:
                raise ValueError('Release inputs changed while packaging; rerun after edits finish')
            checksum = hashlib.sha256(staged_zip.read_bytes()).hexdigest()
            # Exclusive creation also protects against another writer after preflight.
            with output.open('xb') as destination:
                created_output = True
                with staged_zip.open('rb') as source:
                    shutil.copyfileobj(source, destination)
            verify_archive(output, snapshot)
            if hashlib.sha256(output.read_bytes()).hexdigest() != checksum:
                raise ValueError('Published archive checksum differs from verified archive')
            with sidecar.open('x', encoding='utf-8') as destination:
                created_sidecar = True
                destination.write(f'{checksum}  {output.name}\n')
    except BaseException:
        # Remove only outputs created by this invocation, never earlier releases.
        if created_sidecar:
            sidecar.unlink(missing_ok=True)
        if created_output:
            output.unlink(missing_ok=True)
        raise
    return {'status': 'PASS', 'archive': str(output), 'sha256': checksum,
            'sha256_sidecar': str(sidecar), 'files': len(snapshot),
            'manifest_refreshed': refresh_manifest, 'verification': checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New ZIP path outside the companion directory')
    parser.add_argument('--refresh-manifest', action='store_true',
                        help='Explicitly regenerate the current SHA256SUMS before verification')
    args = parser.parse_args(argv)
    try:
        result = build_release(args.output, refresh_manifest=args.refresh_manifest)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'FAIL', 'reason': str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
