from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from .catalog import PATCHES
from .model import Verdict, Case, write_json


class Verifier:
    """Owns the acceptance suite; never consumes the worker's success claims."""
    def check(self, source: Path, cases: tuple[Case, ...], patch_id: str):
        expected = PATCHES[patch_id].encode()
        if source.read_bytes() != expected:
            raise ValueError('Source is not the trusted catalogue patch')
        sha = hashlib.sha256(expected).hexdigest()
        request = {'source_sha': sha, 'cases': [asdict(c) for c in cases]}
        result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).with_name('worker.py')), str(source.resolve())],
                                input=json.dumps(request), capture_output=True, text=True,
                                timeout=5, check=True)
        report = json.loads(result.stdout)
        rows = report['rows']
        if report['source_sha'] != sha or len(rows) != len(cases):
            raise ValueError('Verifier protocol failure')
        for case, row in zip(cases, rows):
            if any(row.get(k) != v for k, v in asdict(case).items()) or type(row.get('passed')) is not bool:
                raise ValueError('Verifier returned mismatched test metadata')
            if row['passed'] != (type(row['actual']) is type(case.expected) and row['actual'] == case.expected):
                raise ValueError('Verifier result inconsistent with evidence')
        return Verdict(tuple(rows), sha)

    @staticmethod
    def probe_applies(route, failed):
        """The only diagnostic in this lab: a float route failing a half-up tie."""
        return route == 'float_first' and any(f['tag'] == 'half_up_tie' for f in failed)

    def probe(self, out: Path):
        """A diagnostic witness fixed before experiments, not an acceptance test.

        It compares one patch of the current route with one patch of a single
        named alternative route on the same tie. The report names that
        alternative; L2 may switch to it only if the hypothesis is supported.
        """
        out.mkdir(parents=True, exist_ok=True)
        case = Case('probe_tie', '1.125', 113, 'half_up_tie')
        reports = {}
        for patch_id in ('float_round', 'decimal_half_up'):
            source = out / (patch_id + '.py')
            source.write_bytes(PATCHES[patch_id].encode())
            verdict = self.check(source, (case,), patch_id)
            reports[patch_id] = {'summary': verdict.summary(), 'rows': verdict.rows}
        supported = not reports['float_round']['summary']['accepted'] and reports['decimal_half_up']['summary']['accepted']
        report = {'hypothesis': 'HALF_UP_TIE_MISMATCH', 'route_under_test': 'float_first',
                  'alternative': 'decimal_exact', 'supported': supported, 'reports': reports}
        write_json(out / 'probe.json', report)
        return report
