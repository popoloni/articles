#!/usr/bin/env python3
"""Rebuild the self-contained HTML from the bundled v6 display data. No dependencies."""
from pathlib import Path
import argparse
import hashlib
import json
import tempfile
import os

def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=here.parent/'AI_SWE_Knowledge_Atlas_v6.html')
    args = parser.parse_args()
    template = (here/'template.html').read_text(encoding='utf-8')
    app = (here/'app.js').read_text(encoding='utf-8')
    raw_data = (here/'graph_data.json').read_text(encoding='utf-8')
    data = json.loads(raw_data)
    if len(data['nodes']) != data['meta']['nodeCount'] or len(data['edges']) != data['meta']['edgeCount']:
        raise ValueError('Payload counts disagree with metadata.')
    for marker in ('__GRAPH_DATA__', '__APP_JS__'):
        if template.count(marker) != 1:
            raise ValueError(f'Expected exactly one {marker} placeholder.')
    if '</script' in app.lower():
        raise ValueError('JavaScript must not contain a literal closing script element.')
    safe_data = raw_data.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    result = template.replace('__GRAPH_DATA__', safe_data).replace('__APP_JS__', app)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                      dir=output.parent, delete=False) as stream:
        stream.write(result)
        tmp = Path(stream.name)
    try:
        os.replace(tmp, output)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(output)
    print('SHA-256:', hashlib.sha256(output.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
