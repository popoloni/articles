#!/usr/bin/env python3
"""Standard-library integrity and reader-facing local-link verification."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def slug(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[`*_]', '', text).lower().strip()
    return re.sub(r'[^\w\- ]', '', text).replace(' ', '-')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if 'id' in data:
            self.ids.add(data['id'])
        for key in ('href', 'src'):
            if data.get(key):
                self.links.append(data[key])


def reader_documents(root: Path):
    for path in sorted(root.rglob('*')):
        parts = path.relative_to(root).parts
        if parts[:2] == ('evidence', 'original') or any(p in ('workspace-final', 'controller-final', '__pycache__', 'runs', 'test-results') for p in parts):
            continue
        if path.suffix in ('.md', '.html') and path.is_file():
            yield path


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.html':
        parser = Links()
        parser.feed(text)
        return parser.ids
    seen, result = {}, set()
    text = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M | re.S)
    for heading in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
        base = slug(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.add(base + (f'-{count}' if count else ''))
    return result


def audit_links(root: Path = ROOT) -> dict:
    errors, checked, external = [], 0, 0
    cache = {}
    docs = list(reader_documents(root))
    for path in docs:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            parser = Links()
            parser.feed(text)
            targets = parser.links
        else:
            text = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M | re.S)
            targets = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text)
            targets += re.findall(r'^\[[^\]]+\]:\s*(\S+)', text, re.M)
        for target in targets:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme != 'data':
                    external += 1
                continue
            destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
            checked += 1
            error = None
            if not destination.is_relative_to(root.resolve()):
                error = 'escapes_package'
            elif not destination.exists():
                error = 'missing_target'
            elif parsed.fragment and destination.suffix in ('.md', '.html'):
                if destination not in cache:
                    cache[destination] = anchors(destination)
                if unquote(parsed.fragment) not in cache[destination]:
                    error = 'missing_anchor'
            if error:
                errors.append({'source': path.relative_to(root).as_posix(), 'target': target, 'error': error})
    return {'status': 'PASS' if not errors else 'FAIL', 'documents_checked': len(docs),
            'local_links_checked': checked, 'external_links_not_fetched': external, 'errors': errors,
            'excluded_scope': 'Verbatim evidence/original sources and generated fixture content; source-only references inventoried separately.'}


def verify_hashes(root: Path = ROOT) -> dict:
    manifest = root / 'SHA256SUMS'
    if not manifest.is_file():
        return {'status': 'FAIL', 'error': 'SHA256SUMS missing', 'files_checked': 0}
    errors, seen = [], set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
        if not match:
            errors.append({'error': 'malformed_checksum_line', 'line': line})
            continue
        expected, relative = match.groups()
        path = (root / relative).resolve()
        if relative in seen or not path.is_relative_to(root.resolve()):
            errors.append({'file': relative, 'error': 'duplicate_or_escaping_path'})
            continue
        seen.add(relative)
        if not path.is_file():
            errors.append({'file': relative, 'error': 'missing_file'})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append({'file': relative, 'error': 'hash_mismatch'})
    return {'status': 'PASS' if seen and not errors else 'FAIL', 'files_checked': len(seen), 'errors': errors,
            'note': 'Checks distributed manifest entries; newly generated user runs are not part of the original manifest. Hashes are not signatures.'}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--links-only', action='store_true')
    args = parser.parse_args()
    result = {'links': audit_links()}
    if not args.links_only:
        result['integrity'] = verify_hashes()
    result['status'] = 'PASS' if all(r['status'] == 'PASS' for r in result.values()) else 'FAIL'
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
