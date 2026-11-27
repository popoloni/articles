"""Local hash-chained trace: detects edits, not authenticated or tamper-proof."""
from pathlib import Path
import json
from .model import canonical, digest


class Audit:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.seq, self.head = self.verify(path) if path.exists() else (0, '0' * 64)

    def append(self, event, **data):
        body = {'seq': self.seq + 1, 'previous': self.head, 'event': event, 'data': data}
        row = {**body, 'hash': digest(body)}
        with self.path.open('ab') as file:
            file.write(canonical(row) + b'\n')
        self.seq += 1
        self.head = row['hash']
        return self.head

    @staticmethod
    def verify(path):
        seq, head = 0, '0' * 64
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            expected = row.pop('hash')
            if row['seq'] != seq + 1 or row['previous'] != head or digest(row) != expected:
                raise ValueError('Broken audit chain')
            seq, head = row['seq'], expected
        return seq, head
