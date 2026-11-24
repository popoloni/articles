#!/usr/bin/env python3
"""Preview the generated Pages site under both / and /articles/."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import sys

ROOT = Path(__file__).resolve().parent.parent
PREFIX = '/articles'

class PreviewHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parts = urlsplit(path)
        clean = parts.path
        if clean == PREFIX:
            clean = '/'
        elif clean.startswith(PREFIX + '/'):
            clean = clean[len(PREFIX):]
        return super().translate_path(clean)

    def send_head(self):
        parts = urlsplit(self.path)
        if parts.path == PREFIX:
            self.send_response(301)
            self.send_header('Location', urlunsplit(('', '', PREFIX + '/', parts.query, '')))
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--directory', type=Path, default=ROOT / 'docs', help='Generated docs directory (absolute or relative path)')
    args = parser.parse_args()
    docs = args.directory.expanduser().resolve()
    if not (docs / 'index.html').is_file():
        parser.exit(2, f'\nERROR: {docs / "index.html"} does not exist.\nBuild the site first: python3 scripts/build_article_site.py\nOr use setup_article_site.command. The preview server was not started.\n')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(PreviewHandler, directory=str(docs)))
    except OSError as exc:
        parser.exit(2, f'Cannot start preview on port {args.port}: {exc}.\nStop the previous server (Ctrl+C) or retry with --port 8001.\n')
    with server:
        port = server.server_address[1]
        print(f'Serving: {docs}', flush=True)
        print(f'Preview: http://localhost:{port}/articles/\nAlso:    http://localhost:{port}/\nStop with Ctrl+C.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nPreview stopped.', flush=True)

if __name__ == '__main__':
    main()
