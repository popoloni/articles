#!/usr/bin/env python3
"""Extract local HTML, text-PDF or caption files. This program never downloads URLs."""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from local_ai import LocalAIError, read_text, write_text

class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.hidden = 0; self.result = []
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}: self.hidden += 1
        if not self.hidden and tag in {"p", "div", "br", "h1", "h2", "h3", "li", "tr"}: self.result.append("\n")
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}: self.hidden = max(0, self.hidden-1)
    def handle_data(self, data):
        if not self.hidden: self.result.append(data)

def clean_captions(text: str) -> str:
    # Consecutive exact duplicates removed only; auto-caption overlaps still require review.
    output = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.isdigit() or '-->' in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if not output or line != output[-1]: output.append(line)
    return "\n".join(output)

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("input", type=Path); p.add_argument("output", type=Path)
    args = p.parse_args(); suffix = args.input.suffix.lower()
    if suffix == '.pdf':
        try: from pypdf import PdfReader
        except ImportError as exc: raise LocalAIError("Install requirements-core.txt first.") from exc
        reader = PdfReader(args.input)
        if reader.is_encrypted: raise LocalAIError("Use an authorized, decrypted local copy.")
        output = []
        for i,page in enumerate(reader.pages, 1):
            text = page.extract_text() or ''
            if not text.strip(): raise LocalAIError(f"Page {i} has no extractable text. Inspect/OCR first; no pages silently skipped.")
            output.append(f"[PAGE {i}]\n{text}")
        text = '\n\n'.join(output)
    elif suffix in {'.html', '.htm'}:
        parser = VisibleHTML(); parser.feed(read_text(args.input)); text = ''.join(parser.result)
    elif suffix in {'.vtt', '.srt'}:
        text = clean_captions(read_text(args.input))
    else: text = read_text(args.input)
    if not text.strip(): raise LocalAIError('No text extracted.')
    write_text(args.output, text.strip() + '\n'); print(f"Saved {len(text)} characters to {args.output}")

if __name__ == '__main__':
    try: main()
    except (LocalAIError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise SystemExit(2)
