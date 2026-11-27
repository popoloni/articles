"""L1: bounded attempt. No control over acceptance, budget or policy."""
from dataclasses import asdict
from .catalog import PATCHES, ROUTES, FAMILIES
from .model import write_json, digest


class ProposalRejected(ValueError):
    """The agent proposed something outside the authorized route and family."""


def execute_attempt(task, route, agent, verifier, feedback, out, audit):
    out.mkdir(parents=True, exist_ok=False)
    proposal = agent.propose(contract=task.contract, route=route, feedback=feedback)
    write_json(out / 'proposal.json', asdict(proposal))
    audit.append('proposal', proposal_sha=digest(asdict(proposal)), **asdict(proposal))
    if proposal.patch_id not in ROUTES[route] or proposal.patch_id not in FAMILIES[task.family]:
        audit.append('proposal_denied', patch=proposal.patch_id)
        raise ProposalRejected('Patch not authorized for this task and route')
    source = out / 'implementation.py'
    source.write_bytes(PATCHES[proposal.patch_id].encode())
    verdict = verifier.check(source, task.cases, proposal.patch_id)
    evidence = {'summary': verdict.summary(), 'rows': verdict.rows}
    write_json(out / 'evidence.json', evidence)
    audit.append('verified', patch=proposal.patch_id, evidence_sha=digest(evidence), **verdict.summary())
    return proposal, verdict
