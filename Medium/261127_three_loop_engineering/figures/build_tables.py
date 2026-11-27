"""Render the article's Markdown tables as PNGs for Medium, which has no table support.

Optional build step: requires Playwright with Chromium (`pip install playwright`
and `playwright install chromium`). Output: figures/tables/table_NN.png.
"""
from html import escape
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent
article = (root.parent / 'article.md').read_text(encoding='utf-8')


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def inline(text):
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'`(.+?)`', r'<code>\1</code>', text)


tables, block = [], []
for line in article.splitlines() + ['']:
    if line.startswith('|'):
        block.append(line)
    elif block:
        tables.append(block)
        block = []

CSS = """
body{margin:0;background:#fff;font:15px/1.45 'DejaVu Sans',system-ui,sans-serif;color:#1f2a36}
#t{display:inline-block;padding:16px;background:#fff}
table{border-collapse:collapse;min-width:420px}
th{background:#eaf3f9;color:#153653;font-weight:600;text-align:left}
th,td{padding:9px 14px;border-bottom:1px solid #d7e0e7;vertical-align:top}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
code{font:13.5px 'DejaVu Sans Mono',monospace;background:#f1f5f9;padding:1px 4px;border-radius:3px}
"""
out = root / 'tables'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=2, viewport={'width': 1100, 'height': 400})
    for n, rows in enumerate(tables, 1):
        head, align, body = cells(rows[0]), cells(rows[1]), [cells(r) for r in rows[2:]]
        cls = ['num' if a.endswith(':') else '' for a in align]
        html = '<table><thead><tr>' + ''.join(f'<th class="{c}">{inline(h)}</th>' for h, c in zip(head, cls)) + '</tr></thead><tbody>'
        html += ''.join('<tr>' + ''.join(f'<td class="{c}">{inline(v)}</td>' for v, c in zip(r, cls)) + '</tr>' for r in body)
        html += '</tbody></table>'
        page.set_content(f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><div id="t">{html}</div>')
        page.locator('#t').screenshot(path=str(out / f'table_{n:02}.png'))
    browser.close()
print(f'{len(tables)} tables rendered to {out}')
