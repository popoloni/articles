#!/usr/bin/env python3
"""Regenerate index.html from article.md using Pandoc.

Publication needs no build step: index.html is already included.
For later edits, install Pandoc and run: python build_preview.py
To create a portable offline preview: python build_preview.py --embed-images --output preview.html
"""
from __future__ import annotations

import argparse
import base64
import html
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

CSS = '''
:root { color-scheme: light; }
* { box-sizing: border-box; }
html { background: #fff; }
body { margin: 0; color: #242a2c; background: #fff; font-family: Georgia, "Times New Roman", serif; font-size: 20px; line-height: 1.65; -webkit-font-smoothing: antialiased; }
article { width: min(960px, calc(100% - 48px)); margin: 68px auto 90px; }
article > p, article > h2, article > h3, article > blockquote, article > hr, .references { max-width: 744px; margin-left: auto; margin-right: auto; }
header { margin: 0 auto 42px; max-width: 900px; }
h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #19292d; letter-spacing: -0.035em; }
h1 { font-size: clamp(34px, 5vw, 52px); font-weight: 750; line-height: 1.1; margin: 0 0 22px; }
header .subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #58656b; font-size: 23px; line-height: 1.42; margin: 0 0 23px; }
header .subtitle em { font-style: normal; }
header .byline { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #596266; font-size: 15px; margin: 0; padding-bottom: 24px; border-bottom: 1px solid #dce2e3; }
h2 { font-size: 30px; line-height: 1.23; margin-top: 58px; margin-bottom: 22px; }
h3 { font-size: 23px; line-height: 1.3; margin-top: 34px; margin-bottom: 16px; }
p { margin-top: 0; margin-bottom: 23px; }
a { color: #14665f; text-decoration: underline; text-underline-offset: 0.15em; text-decoration-thickness: 0.07em; overflow-wrap: anywhere; }
a:hover { color: #093c37; }
strong { font-weight: 700; }
figure { margin: 40px auto 47px; width: 100%; }
figure img { display: block; width: 100%; height: auto; max-width: 100%; background: #fff; }
figcaption { margin: 15px 10px 0; color: #525e62; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 15px; line-height: 1.55; }
blockquote { padding: 7px 0 7px 25px; border-left: 3px solid #577b77; font-size: 24px; line-height: 1.5; }
blockquote p { margin: 0; }
hr { border: 0; border-top: 1px solid #dce2e3; margin-top: 50px; margin-bottom: 36px; }
.references { font-size: 17px; line-height: 1.55; }
.references h2 { margin-top: 0; }
.references p { margin-bottom: 20px; }
@media (max-width: 600px) { body { font-size: 18px; line-height: 1.65; } article { width: calc(100% - 32px); margin-top: 32px; } header .subtitle { font-size: 20px; } h2 { font-size: 26px; } h3 { font-size: 22px; } figure { margin-top: 29px; margin-bottom: 34px; } figcaption { margin-left: 0; margin-right: 0; font-size: 14px; } blockquote { font-size: 21px; padding-left: 17px; } }
@media print { article { width: 100%; margin: 0; } body { font-size: 11pt; } h1 { font-size: 28pt; } h2 { font-size: 18pt; break-after: avoid; } h3 { break-after: avoid; } figure { break-inside: avoid; } a { color: inherit; } }
'''

def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open('rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'Expected a PNG image: {path}')
    return struct.unpack('>II', head[16:24])

def build(root: Path, output: Path, embed_images: bool) -> None:
    if not shutil.which('pandoc'):
        raise RuntimeError('Pandoc is not installed. The supplied index.html can be used without rebuilding.')
    md = (root / 'article.md').read_text(encoding='utf-8')
    converted = subprocess.run(
        ['pandoc', '--from=gfm-implicit_figures', '--to=html5', '--wrap=none'],
        input=md, text=True, capture_output=True, check=True,
    ).stdout
    header = re.match(r'(?s)(<h1\b.*?</h1>)\s*<p>(.*?)</p>\s*<p>(.*?)</p>', converted)
    if not header:
        raise ValueError('Expected article title, subtitle and byline at the beginning.')
    converted = ('<header>\n' + header.group(1) + '\n<p class="subtitle">' + header.group(2)
                 + '</p>\n<p class="byline">' + header.group(3) + '</p>\n</header>\n'
                 + converted[header.end():])

    count = 0
    def figure(match: re.Match) -> str:
        nonlocal count
        count += 1
        tag, source, caption = match.group(1), match.group(2), match.group(3)
        path = (root / source).resolve()
        if not path.is_relative_to((root / 'images').resolve()) or not path.is_file():
            raise ValueError(f'Missing or unsafe local image path: {source}')
        w, h = png_dimensions(path)
        tag = tag.replace('<img ', f'<img width="{w}" height="{h}" ')
        if embed_images:
            url = 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
            tag = tag.replace(f'src="{source}"', f'src="{url}"')
        return f'<figure id="figure-{count}">\n{tag}\n<figcaption>{caption}</figcaption>\n</figure>'

    converted = re.sub(
        r'<p>(<img\b[^>]*src="(images/[^"]+)"[^>]*>)</p>\s*<p>(<strong>Figure \d+\..*?)</p>',
        figure, converted, flags=re.S,
    )
    if count != 5:
        raise ValueError(f'Expected five figure-caption pairs, found {count}.')
    converted = converted.replace('<h2 id="sources-and-further-reading">', '<section class="references">\n<h2 id="sources-and-further-reading">', 1)
    converted += '\n</section>\n'
    title = 'The Agents Didn’t Need a Chat Room. They Had Artifactory.'
    subtitle = 'What the OpenAI–Hugging Face incident reveals about accidental blackboards, agent coordination, and the difference between capability and authority'
    document = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Enrico Papalini">
<meta name="description" content="{html.escape(subtitle, quote=True)}">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<article>
{converted}
</article>
</body>
</html>
'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding='utf-8')
    print(f'Created {output} with {count} figures.')

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Output HTML file. Default: index.html beside this script.')
    parser.add_argument('--embed-images', action='store_true', help='Embed PNG data for a standalone offline preview.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        build(root, args.output.resolve() if args.output else root / 'index.html', args.embed_images)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
