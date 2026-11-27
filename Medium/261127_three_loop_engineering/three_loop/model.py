from __future__ import annotations
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
from .catalog import FAMILY_ROUTES


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


@dataclass(frozen=True)
class Case:
    id: str
    value: str
    expected: int | str
    tag: str


@dataclass(frozen=True)
class Task:
    id: str
    family: str
    split: str
    contract: str
    cases: tuple[Case, ...]

    @classmethod
    def from_dict(cls, raw):
        return cls(raw['id'], raw['family'], raw['split'], raw['contract'],
                   tuple(Case(**c) for c in raw['cases']))


@dataclass(frozen=True)
class Policy:
    version: str
    money_start: str
    text_start: str
    max_attempts: int
    repeat_limit: int
    plateau_limit: int

    def __post_init__(self):
        if not (self.version[:1] == 'v' and self.version[1:].isdigit()):
            raise ValueError('Invalid policy version')
        if self.money_start not in FAMILY_ROUTES['money'] or self.text_start not in FAMILY_ROUTES['text']:
            raise ValueError('Unknown route')
        if not (1 <= self.max_attempts <= 10 and 2 <= self.repeat_limit <= 10 and 1 <= self.plateau_limit <= 10):
            raise ValueError('Invalid budget or stagnation threshold')

    @property
    def sha(self):
        return digest(asdict(self))

    def route(self, family):
        return {'money': self.money_start, 'text': self.text_start}[family]

    def with_route(self, family, route):
        """Next version with one family's default route changed; nothing else."""
        field = {'money': 'money_start', 'text': 'text_start'}[family]
        return replace(self, version=f'v{int(self.version[1:]) + 1}', **{field: route})


@dataclass(frozen=True)
class Proposal:
    patch_id: str
    rationale: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class Verdict:
    rows: tuple[dict, ...]
    source_sha: str

    @property
    def passed(self):
        return sum(row['passed'] for row in self.rows)

    @property
    def accepted(self):
        return bool(self.rows) and self.passed == len(self.rows)

    @property
    def fingerprint(self):
        return digest([{'id': r['id'], 'actual': r['actual']} for r in self.rows if not r['passed']])

    def summary(self):
        return {'passed': self.passed, 'total': len(self.rows), 'accepted': self.accepted,
                'fingerprint': self.fingerprint, 'source_sha': self.source_sha,
                'failed': [{'id': r['id'], 'tag': r['tag']} for r in self.rows if not r['passed']]}


def load_tasks(path):
    tasks = [Task.from_dict(x) for x in read_json(path)]
    if len({t.id for t in tasks}) != len(tasks):
        raise ValueError('Duplicate tasks')
    for task in tasks:
        if not task.id.replace('_', '').isalnum() or task.family not in ('money', 'text') or task.split not in ('train', 'holdout'):
            raise ValueError('Invalid task metadata')
        if not task.cases or len({c.id for c in task.cases}) != len(task.cases):
            raise ValueError('Empty or duplicate acceptance cases')
    return tasks
