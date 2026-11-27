"""L3: train-only hypothesis, paired holdout evaluation, gated promotion."""
from dataclasses import asdict
from .model import digest

ROUTE_FIELDS = {'money_start': 'money', 'text_start': 'text'}


def propose_policy(baseline, training, min_witnesses=2):
    """Derive at most one route change from baseline training episodes only.

    A witness is a training task that was accepted after a supported diagnostic
    probe switched it to another route. A change is proposed only when at least
    `min_witnesses` distinct tasks of one family agree on the same new route,
    no episode of that family switched elsewhere, and exactly one family
    qualifies. The candidate is frozen here, before any holdout task is run.
    """
    if any(r['split'] != 'train' or r['policy_sha'] != baseline.sha for r in training):
        raise ValueError('Learning may only inspect baseline training episodes')
    switches = {}  # family -> {route: set(task ids)}
    for r in training:
        if not r['history']:
            continue
        start, final = r['history'][0]['route'], r['history'][-1]['route']
        if final == start:
            continue
        supported = any(p['supported'] and p['alternative'] == final for p in r['probes'])
        if r['status'] == 'accepted' and supported:
            switches.setdefault(r['family'], {}).setdefault(final, set()).add(r['task'])
        else:  # a switch that did not end in a supported, accepted outcome is contrary evidence
            switches.setdefault(r['family'], {}).setdefault(None, set()).add(r['task'])
    changes = []
    for family, routes in switches.items():
        if len(routes) == 1 and None not in routes:
            (route, tasks), = routes.items()
            if len(tasks) >= min_witnesses and route != baseline.route(family):
                changes.append((family, route, sorted(tasks)))
    if len(changes) != 1:
        return None, sorted(t for c in changes for t in c[2])
    family, route, witnesses = changes[0]
    return baseline.with_route(family, route), witnesses


def evaluate(baseline, candidate, before, after, dataset_sha):
    a, b = ({x['task']: x for x in rows} for rows in (before, after))
    if not a or len(a) != len(before) or len(b) != len(after) or a.keys() != b.keys():
        raise ValueError('Holdout pairing invalid')
    for x, y in zip((a[k] for k in sorted(a)), (b[k] for k in sorted(a))):
        if x['split'] != 'holdout' or y['split'] != 'holdout' or x['family'] != y['family'] or x['agent'] != y['agent']:
            raise ValueError('Holdout provenance invalid')
        if x['policy_sha'] != baseline.sha or y['policy_sha'] != candidate.sha:
            raise ValueError('Unexpected policy')
    old, new = asdict(baseline), asdict(candidate)
    changed = sorted(k for k in old if old[k] != new[k])
    route_fields = [k for k in changed if k in ROUTE_FIELDS]
    target = ROUTE_FIELDS[route_fields[0]] if len(route_fields) == 1 else None
    pairs = [{'task': k, 'family': a[k]['family'], 'baseline_status': a[k]['status'], 'candidate_status': b[k]['status'],
              'baseline_attempts': a[k]['attempts'], 'candidate_attempts': b[k]['attempts']} for k in sorted(a)]
    baseline_total = sum(r['baseline_attempts'] for r in pairs)
    candidate_total = sum(r['candidate_attempts'] for r in pairs)
    checks = {
        'only_authorized_policy_change': target is not None and changed == sorted(['version'] + route_fields)
                                         and candidate.version == f'v{int(baseline.version[1:]) + 1}',
        'target_and_control_present': sum(r['family'] == target for r in pairs) >= 2 and any(r['family'] != target for r in pairs),
        'all_baseline_and_candidate_accepted': all(r['baseline_status'] == r['candidate_status'] == 'accepted' for r in pairs),
        'no_per_task_attempt_regression': all(r['candidate_attempts'] <= r['baseline_attempts'] for r in pairs),
        'control_unchanged': all(r['candidate_attempts'] == r['baseline_attempts'] for r in pairs if r['family'] != target),
        'strict_total_attempt_improvement': candidate_total < baseline_total,
    }
    return {'baseline_sha': baseline.sha, 'candidate_sha': candidate.sha, 'dataset_sha': dataset_sha,
            'policy_change': {k: [old[k], new[k]] for k in changed},
            'pairs': pairs, 'baseline_attempts': baseline_total, 'candidate_attempts': candidate_total,
            'checks': checks, 'recommended': all(checks.values()),
            'baseline_reports_sha': digest(sorted(before, key=lambda x: x['task'])),
            'candidate_reports_sha': digest(sorted(after, key=lambda x: x['task']))}
