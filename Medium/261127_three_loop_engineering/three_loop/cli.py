from argparse import ArgumentParser
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from .agents import ClaudeAgent, ScriptedAgent
from .audit import Audit
from .learning import propose_policy, evaluate
from .model import Policy, Verdict, digest, load_tasks, read_json, write_json
from .progress import run_episode
from .verifier import Verifier

ROOT = Path(__file__).resolve().parent.parent
POINTER_EVENTS = ('baseline_registered', 'policy_promoted', 'policy_rolled_back')


def baseline():
    return Policy(**read_json(ROOT / 'policies/baseline.json'))


def tasks():
    return load_tasks(ROOT / 'specs/tasks.json')


def demo(out):
    out.mkdir(parents=True, exist_ok=False)
    audit = Audit(out / 'governance.jsonl')
    base = baseline()
    all_tasks = tasks()
    train, holdout = ([t for t in all_tasks if t.split == split] for split in ('train', 'holdout'))
    dataset_sha = digest([asdict(t) for t in holdout])
    write_json(out / 'policies/v1.json', asdict(base))
    write_json(out / 'active.json', {'version': base.version, 'sha': base.sha})
    write_json(out / 'dataset.json', {'train_sha': digest([asdict(t) for t in train]), 'holdout_sha': dataset_sha})
    audit.append('baseline_registered', policy_sha=base.sha, holdout_sha=dataset_sha)
    agent, verifier = ScriptedAgent(), Verifier()
    training = [run_episode(t, base, agent, verifier, out / 'train' / t.id) for t in train]
    candidate, witnesses = propose_policy(base, training)
    if candidate is None:
        audit.append('no_candidate', witnesses=witnesses)
        return {'recommended': False, 'reason': 'insufficient_training_evidence'}
    write_json(out / 'policies/v2.json', asdict(candidate))
    audit.append('candidate_proposed', candidate_sha=candidate.sha, witnesses=witnesses, training_sha=digest(training))
    # The candidate is frozen before any holdout task runs.
    before = [run_episode(t, base, agent, verifier, out / 'holdout/v1' / t.id) for t in holdout]
    after = [run_episode(t, candidate, agent, verifier, out / 'holdout/v2' / t.id) for t in holdout]
    report = evaluate(base, candidate, before, after, dataset_sha)
    write_json(out / 'evaluation.json', report)
    audit.append('evaluation_finished', evaluation_sha=digest(report), recommended=report['recommended'])
    return {**report, 'approval_digest': digest(report), 'active_policy': 'v1'}


def validate_episode(path, task, policy):
    """Verify retained source, evidence and report against the local trace."""
    Audit.verify(path / 'trace.jsonl')
    events = [json.loads(x) for x in (path / 'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    report = read_json(path / 'episode.json')
    first = events[0]
    if first['event'] != 'episode_started' or first['data']['task_sha'] != digest(asdict(task)) or first['data']['policy_sha'] != policy.sha or report['task'] != task.id or report['policy_sha'] != policy.sha:
        raise ValueError('Episode provenance mismatch')
    if events[-1]['event'] != 'episode_finished' or events[-1]['data']['report_sha'] != digest(report):
        raise ValueError('Episode report mismatch')
    reservations = [e for e in events if e['event'] == 'attempt_reserved']
    verified = [e for e in events if e['event'] == 'verified']
    proposals = [e for e in events if e['event'] == 'proposal']
    if len(reservations) != report['attempts'] or len(verified) != len(report['history']) or len(proposals) != len(verified):
        raise ValueError('Attempt or verification count mismatch')
    for index, row in enumerate(report['history']):
        attempt = path / f"attempt_{row['attempt']:02}"
        evidence = read_json(attempt / 'evidence.json')
        if hashlib.sha256((attempt / 'implementation.py').read_bytes()).hexdigest() != row['source_sha']:
            raise ValueError('Retained source changed')
        verdict = Verdict(tuple(evidence['rows']), row['source_sha'])
        if verdict.summary() != evidence['summary'] or any(row[k] != v for k, v in verdict.summary().items()):
            raise ValueError('Evidence summary changed')
        if verified[index]['data']['evidence_sha'] != digest(evidence) or proposals[index]['data']['proposal_sha'] != digest(read_json(attempt / 'proposal.json')):
            raise ValueError('Retained evidence or proposal changed')
    for record in report['probes']:
        if digest(read_json(path / f"probe_{record['attempt']:02}" / 'probe.json')) != record['probe_sha']:
            raise ValueError('Diagnostic evidence changed')
    return report


def governance(out):
    """Verified governance events and the policy digest they say is active."""
    path = out / 'governance.jsonl'
    Audit.verify(path)
    events = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
    pointer = [e['data']['policy_sha'] for e in events if e['event'] in POINTER_EVENTS]
    if not pointer:
        raise ValueError('No registered policy in governance log')
    return events, pointer[-1]


def check_active(out, version, policy):
    """The active pointer must match both the expected version and the governance log."""
    events, governed = governance(out)
    if read_json(out / 'active.json') != {'version': version, 'sha': policy.sha} or governed != policy.sha:
        raise ValueError(f'Expected {version} active and recorded in the governance log')
    return events


def promote(out, approval):
    base, cand = (Policy(**read_json(out / f'policies/{v}.json')) for v in ('v1', 'v2'))
    events = check_active(out, 'v1', base)
    if not any(e['event'] == 'candidate_proposed' and e['data']['candidate_sha'] == cand.sha for e in events):
        raise ValueError('Candidate was not proposed by the recorded learning step')
    if any(e['event'] == 'promotion_authorized' and e['data']['approval_digest'] == approval for e in events):
        raise ValueError('Approval already used; a new promotion needs a new evaluation')
    holdout = [t for t in tasks() if t.split == 'holdout']
    before, after = ([validate_episode(out / 'holdout' / p.version / t.id, t, p) for t in holdout] for p in (base, cand))
    fresh = evaluate(base, cand, before, after, digest([asdict(t) for t in holdout]))
    stored = read_json(out / 'evaluation.json')
    if not any(e['event'] == 'evaluation_finished' and e['data']['evaluation_sha'] == digest(stored) for e in events):
        raise ValueError('Missing evaluation audit record')
    if fresh != stored or not fresh['recommended'] or digest(fresh) != approval:
        raise ValueError('Gate failed or approval does not match exact evaluation')
    # Explicit local operator action, not an authenticated approval service.
    audit = Audit(out / 'governance.jsonl')
    audit.append('promotion_authorized', approval_digest=approval, previous=base.sha, next=cand.sha)
    write_json(out / 'active.json', {'version': 'v2', 'sha': cand.sha})
    audit.append('policy_promoted', policy_sha=cand.sha)
    return {'active_policy': 'v2', 'sha': cand.sha}


def rollback(out, approval):
    base, cand = (Policy(**read_json(out / f'policies/{v}.json')) for v in ('v1', 'v2'))
    check_active(out, 'v2', cand)
    if approval != base.sha:
        raise ValueError('Rollback requires active v2 and exact baseline digest')
    audit = Audit(out / 'governance.jsonl')
    audit.append('rollback_authorized', previous=cand.sha, next=base.sha)
    write_json(out / 'active.json', {'version': 'v1', 'sha': base.sha})
    audit.append('policy_rolled_back', policy_sha=base.sha)
    return {'active_policy': 'v1', 'sha': base.sha}


def run_active(run, task_id, out):
    pointer = read_json(run / 'active.json')
    if pointer.get('version') not in ('v1', 'v2'):
        raise ValueError('Invalid active version')
    policy = Policy(**read_json(run / 'policies' / (pointer['version'] + '.json')))
    check_active(run, pointer['version'], policy)
    task = next(t for t in tasks() if t.id == task_id)
    return run_episode(task, policy, ScriptedAgent(), Verifier(), out)


def main():
    parser = ArgumentParser(description='Three-loop engineering reference')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('demo'); p.add_argument('--out', type=Path, required=True)
    for command in ('promote', 'rollback'):
        p = sub.add_parser(command); p.add_argument('--run', type=Path, required=True); p.add_argument('--approve', required=True)
    p = sub.add_parser('live'); p.add_argument('--out', type=Path, required=True); p.add_argument('--model', required=True)
    p.add_argument('--task', default='train_fees', choices=[t.id for t in tasks() if t.split == 'train'])
    p.add_argument('--max-calls', type=int, default=3, choices=range(1, 5)); p.add_argument('--max-output-tokens', type=int, default=256)
    p = sub.add_parser('run-active'); p.add_argument('--run', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--task', required=True, choices=[t.id for t in tasks()])
    args = parser.parse_args()
    if args.command == 'demo': result = demo(args.out)
    elif args.command == 'promote': result = promote(args.run, args.approve)
    elif args.command == 'rollback': result = rollback(args.run, args.approve)
    elif args.command == 'live':
        task = next(t for t in tasks() if t.id == args.task)
        result = run_episode(task, replace(baseline(), max_attempts=args.max_calls), ClaudeAgent(args.model, args.max_output_tokens), Verifier(), args.out)
    else:
        result = run_active(args.run, args.task, args.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
