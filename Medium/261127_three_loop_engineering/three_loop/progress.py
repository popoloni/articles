"""L2: deterministic supervisor, immutable policy, explicit stop reasons."""
from dataclasses import asdict
from .audit import Audit
from .catalog import FAMILY_ROUTES
from .execution import ProposalRejected, execute_attempt
from .model import write_json, digest


def run_episode(task, policy, agent, verifier, out):
    out.mkdir(parents=True, exist_ok=False)
    audit = Audit(out / 'trace.jsonl')
    audit.append('episode_started', task=task.id, policy_sha=policy.sha, agent=agent.name,
                 task_sha=digest(asdict(task)), max_attempts=policy.max_attempts)
    route = policy.route(task.family)
    best, plateau, repeated = -1, 0, 0
    previous = None
    switched = False  # at most one evidence-backed strategy change per episode
    feedback = []
    history = []
    probes = []
    status, reason, accepted_source = 'escalated', 'attempt_budget_exhausted', None
    attempts = 0
    for n in range(1, policy.max_attempts + 1):
        attempts = n  # reserve before invoking the agent; no hidden retries
        audit.append('attempt_reserved', attempt=n, route=route)
        try:
            proposal, verdict = execute_attempt(task, route, agent, verifier, feedback[-2:], out / f'attempt_{n:02}', audit)
        except ProposalRejected:
            reason = 'invalid_proposal'
            audit.append('attempt_error', error_type='ProposalRejected', attempt=n)
            break
        except Exception as exc:
            reason = 'execution_or_verifier_error'
            audit.append('attempt_error', error_type=type(exc).__name__, attempt=n)
            break
        s = verdict.summary()
        improved = verdict.passed > best
        best = max(best, verdict.passed)
        plateau = 0 if improved else plateau + 1
        repeated = repeated + 1 if previous == verdict.fingerprint else 1
        previous = verdict.fingerprint
        history.append({'attempt': n, 'route': route, 'patch': proposal.patch_id,
                        'input_tokens': proposal.input_tokens, 'output_tokens': proposal.output_tokens,
                        'improved': improved, 'repeat_count': repeated, 'plateau': plateau, **s})
        feedback.append({'route': route, 'patch': proposal.patch_id, **s})
        audit.append('progress_measured', **history[-1])
        if verdict.accepted:
            status, reason = 'accepted', 'all_acceptance_checks_passed'
            accepted_source = f'attempt_{n:02}/implementation.py'
            break
        if repeated >= policy.repeat_limit or plateau >= policy.plateau_limit:
            if not switched and n < policy.max_attempts and verifier.probe_applies(route, s['failed']):
                try:
                    probe = verifier.probe(out / f'probe_{n:02}')
                except Exception as exc:
                    audit.append('probe_error', error_type=type(exc).__name__)
                    reason = 'diagnostic_error'
                    break
                record = {'attempt': n, 'hypothesis': probe['hypothesis'], 'supported': probe['supported'],
                          'alternative': probe['alternative'], 'probe_sha': digest(probe)}
                probes.append(record)
                audit.append('diagnostic_probe', **record)
                allowed = probe['alternative'] in FAMILY_ROUTES[task.family] and probe['alternative'] != route
                if probe['supported'] and allowed:
                    audit.append('strategy_changed', previous=route, next=probe['alternative'], hypothesis=probe['hypothesis'])
                    route, switched = probe['alternative'], True
                    best, plateau, repeated, previous = -1, 0, 0, None
                    continue
            reason = 'stagnation' if n < policy.max_attempts else 'attempt_budget_exhausted'
            break
    report = {'task': task.id, 'split': task.split, 'family': task.family, 'policy_sha': policy.sha,
              'agent': agent.name, 'status': status, 'reason': reason, 'attempts': attempts,
              'history': history, 'probes': probes, 'accepted_source': accepted_source}
    audit.append('episode_finished', status=status, reason=reason, attempts=attempts, report_sha=digest(report))
    write_json(out / 'episode.json', report)
    return report
