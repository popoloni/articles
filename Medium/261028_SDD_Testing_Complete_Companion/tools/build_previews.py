#!/usr/bin/env python3
"""Rebuild HTML reading copies. Optional dependency; never needed by the starter."""
from __future__ import annotations
import base64
import html
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


def slug(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[`*_]', '', text).lower().strip()
    return re.sub(r'[^\w\- ]', '', text).replace(' ', '-')


def documents() -> list[Path]:
    result = []
    for p in sorted(ROOT.rglob('*.md')):
        relative = p.relative_to(ROOT).parts
        if relative[:2] == ('evidence', 'original') or any(part in ('workspace-final', 'controller-final', '__pycache__', 'runs', 'test-results', 'validation-runs', 'validation-container', '.venv') for part in relative):
            continue
        result.append(p)
    return result


CSS = '''
:root{--navy:#041923;--orange:#ed8306;--cyan:#176b84;--ink:#1a2932;--muted:#596d79}
*{box-sizing:border-box}body{margin:0;background:#eef2f5;color:var(--ink);font:18px/1.7 Georgia,serif}
header{background:var(--navy);color:white;border-bottom:5px solid var(--orange);padding:28px max(22px,calc((100vw - 1080px)/2))}
header .brand{font:700 13px/1.4 Arial,sans-serif;letter-spacing:2px;text-transform:uppercase;color:#ffab43}
nav{display:flex;gap:22px;flex-wrap:wrap;margin-top:13px;font:14px/1.4 Arial,sans-serif}nav a{color:#c9ebf5;text-decoration:none}
main{max-width:1080px;margin:24px auto 60px;padding:42px 62px;background:#fff;box-shadow:0 4px 25px #08223410;border-radius:10px}
h1,h2,h3{font-family:Arial,sans-serif;line-height:1.2;letter-spacing:-.02em;color:var(--navy)}h1{font-size:42px;margin:0 0 26px}h2{font-size:29px;margin-top:52px;border-top:1px solid #e2e9ed;padding-top:25px}h3{font-size:22px;margin-top:30px}
p{margin:1em 0}a{color:#126d87;text-decoration-thickness:1px;text-underline-offset:3px}strong{font-weight:700}img{display:block;max-width:100%;height:auto;margin:28px auto 12px;border-radius:5px}
p:has(>em:only-child){font-size:16px;line-height:1.55;color:var(--muted)}pre{background:var(--navy);color:#d7edf2;padding:20px;border-radius:7px;overflow:auto;font:13px/1.6 Consolas,monospace}code{font:14px/1.5 Consolas,monospace;overflow-wrap:anywhere}p code,li code,td code{background:#edf4f6;padding:2px 4px;border-radius:3px}
blockquote{border-left:4px solid var(--orange);background:#fff8ee;padding:3px 20px;margin:24px 0}table{width:100%;border-collapse:collapse;font:14px/1.5 Arial,sans-serif;margin:26px 0}th{background:var(--navy);color:white;text-align:left;padding:12px}td{padding:12px;border-bottom:1px solid #dce5ea;vertical-align:top;overflow-wrap:anywhere}tr:nth-child(even){background:#f6f9fa}footer{font:13px/1.5 Arial,sans-serif;color:var(--muted);border-top:1px solid #dce5ea;padding-top:24px;margin-top:45px}hr{border:0;border-top:1px solid #dce5ea;margin:34px 0}
@media(max-width:720px){main{margin:0;padding:26px 19px;border-radius:0}h1{font-size:31px}h2{font-size:25px}body{font-size:17px}table{font-size:12px}td,th{padding:8px}nav{gap:15px}}
.contents{display:block;background:#f1f7f9;padding:18px 24px;border-radius:7px;margin:24px 0;font:15px/1.6 Arial,sans-serif}.contents a{color:#126d87;text-decoration:underline}.contents ol{padding-left:22px;margin:8px 0}.contents li{margin:4px 0}a:focus-visible{outline:3px solid var(--orange);outline-offset:3px}
@media print{body{background:white}main{box-shadow:none;margin:0;max-width:none;padding:0}header,.contents{display:none}pre{white-space:pre-wrap}a{color:inherit}}
'''


def main() -> int:
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        raise SystemExit('Install optional preview dependency: python -m pip install -r tools/requirements-preview.txt')
    files = documents()
    known = {p.resolve() for p in files}
    md = MarkdownIt('commonmark', {'html': False}).enable('table')
    def render(source: Path, embedded: bool = False) -> str:
        content = source.read_text(encoding='utf-8')
        tokens = md.parse(content)
        seen = {}
        for idx, token in enumerate(tokens):
            if token.type == 'heading_open':
                text = tokens[idx + 1].content
                base = slug(text)
                count = seen.get(base, 0)
                seen[base] = count + 1
                token.attrSet('id', base + (f'-{count}' if count else ''))
            for child in token.children or []:
                attr = 'href' if child.type == 'link_open' else 'src' if child.type == 'image' else None
                if not attr:
                    continue
                target = child.attrGet(attr)
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                resolved = (source.parent / unquote(parsed.path)).resolve()
                if attr == 'href' and resolved in known and resolved.suffix == '.md':
                    updated = str(Path(parsed.path).with_suffix('.html')).replace(os.sep, '/')
                    if parsed.fragment:
                        updated += '#' + parsed.fragment
                    child.attrSet(attr, updated)
                if attr == 'src' and embedded and resolved.is_file() and resolved.suffix == '.png':
                    child.attrSet(attr, 'data:image/png;base64,' + base64.b64encode(resolved.read_bytes()).decode())
        rendered = md.renderer.render(tokens, md.options, {})
        if source.name == 'article.md':
            entries = [(token.attrGet('id'), tokens[idx + 1].content) for idx, token in enumerate(tokens)
                       if token.type == 'heading_open' and token.tag == 'h2']
            contents = '<nav class="contents" aria-label="Article contents"><strong>In this article</strong><ol>' + ''.join(
                f'<li><a href="#{html.escape(anchor)}">{html.escape(label)}</a></li>' for anchor, label in entries) + '</ol></nav>'
            # Keep the title and opening visible before navigation, then introduce the first section.
            rendered = rendered.replace('<h2 ', contents + '<h2 ', 1)
        title = next((t.content for t in tokens if t.type == 'inline'), source.stem)
        nav = [(ROOT / 'index.html', 'Companion home'), (ROOT / 'preview.html', 'Article'),
               (ROOT / 'starter/docs/REPRODUCE.html', 'Run it yourself'), (ROOT / 'evidence/local-validation/README.html', 'Latest evidence')]
        navigation = ''.join(f'<a href="{html.escape(os.path.relpath(p, source.parent).replace(os.sep,"/"))}">{label}</a>' for p, label in nav)
        return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{html.escape(title)}</title><style>{CSS}</style></head><body><header><div class="brand">Non-deterministic software engineering · Reader companion</div><nav>{navigation}</nav></header>'
                f'<main>{rendered}<footer>Reader rerun edition · October 29, 2026. Public executions, native metadata and historical records have separate scopes. '
                f'<a href="{html.escape(source.name)}">Markdown source</a></footer></main></body></html>\n')
    for source in files:
        source.with_suffix('.html').write_text(render(source), encoding='utf-8')
    (ROOT / 'preview.html').write_text(render(ROOT / 'article.md', embedded=True), encoding='utf-8')
    (ROOT / 'index.html').write_text(render(ROOT / 'README.md'), encoding='utf-8')
    print(f'Built {len(files)} document previews, the embedded-figure article, and index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
