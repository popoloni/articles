import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from three_loop.agents import ClaudeAgent, ScriptedAgent, API_VERSION
from three_loop.audit import Audit
from three_loop.catalog import PATCHES
from three_loop.cli import baseline, tasks, demo, promote, rollback, run_active
from three_loop.learning import propose_policy, evaluate
from three_loop.model import Proposal, read_json, write_json, digest
from three_loop.progress import run_episode
from three_loop.verifier import Verifier


class BadAgent:
    name = 'bad'
    def propose(self, **kwargs):
        return Proposal('import os', 'invalid')


class BadVerifier:
    def check(self, *args):
        raise TimeoutError('verifier unavailable')


class ThreeLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = baseline()
        self.task = next(t for t in tasks() if t.id == 'train_fees')

    def episode(self, policy=None, agent=None, verifier=None):
        return run_episode(self.task, policy or self.base, agent or ScriptedAgent(), verifier or Verifier(), self.root / 'episode')

    def test_repeated_failure_changes_strategy(self):
        result = self.episode()
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual([h['patch'] for h in result['history']], ['float_round', 'float_round', 'decimal_half_up'])
        self.assertEqual(result['history'][0]['fingerprint'], result['history'][1]['fingerprint'])
        self.assertTrue(result['probes'][0]['supported'])
        self.assertTrue(result['history'][-1]['accepted'])

    def test_budget_is_reserved_before_agent_call(self):
        result = self.episode(replace(self.base, max_attempts=1))
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['reason'], 'attempt_budget_exhausted')
        self.assertIsNone(result['accepted_source'])

    def test_invalid_patch_fails_closed(self):
        r = self.episode(agent=BadAgent())
        self.assertEqual((r['status'], r['attempts'], r['reason']), ('escalated', 1, 'invalid_proposal'))
        self.assertFalse((self.root / 'episode/attempt_01/implementation.py').exists())

    def test_verifier_failure_fails_closed(self):
        r = self.episode(verifier=BadVerifier())
        self.assertEqual(r['reason'], 'execution_or_verifier_error')
        self.assertIsNone(r['accepted_source'])

    def test_modified_source_denied(self):
        file = self.root / 'implementation.py'
        file.write_text(PATCHES['float_round'] + '\n# altered')
        with self.assertRaises(ValueError):
            Verifier().check(file, self.task.cases, 'float_round')

    def test_decimal_matches_contract(self):
        file = self.root / 'implementation.py'
        file.write_bytes(PATCHES['decimal_half_up'].encode())
        self.assertTrue(Verifier().check(file, self.task.cases, 'decimal_half_up').accepted)

    def test_learning_insufficient_evidence(self):
        report = self.episode()
        policy, _ = propose_policy(self.base, [report])
        self.assertIsNone(policy)
        self.assertIsNone(propose_policy(self.base, [report, report])[0])

    def test_holdout_not_allowed_in_learning(self):
        report = self.episode()
        report['split'] = 'holdout'
        with self.assertRaises(ValueError):
            propose_policy(self.base, [report])

    def test_hash_chain_tampering(self):
        self.episode()
        path = self.root / 'episode/trace.jsonl'
        text = path.read_text().replace('episode_started', 'episode_changed', 1)
        path.write_text(text)
        with self.assertRaises(ValueError):
            Audit.verify(path)

    def test_demo_promote_rollback_and_reject_bad_approval(self):
        run = self.root / 'run'
        report = demo(run)
        self.assertEqual((report['baseline_attempts'], report['candidate_attempts']), (7, 3))
        self.assertTrue(report['recommended'])
        self.assertEqual(read_json(run / 'active.json')['version'], 'v1')
        with self.assertRaises(ValueError):
            promote(run, 'bad')
        self.assertEqual(promote(run, report['approval_digest'])['active_policy'], 'v2')
        self.assertEqual(rollback(run, report['baseline_sha'])['active_policy'], 'v1')
        Audit.verify(run / 'governance.jsonl')

    def test_promotion_rejects_modified_evidence(self):
        run = self.root / 'run'
        report = demo(run)
        path = run / 'holdout/v2/holdout_invoice/attempt_01/evidence.json'
        evidence = read_json(path)
        evidence['rows'][0]['value'] = 'tampered'
        write_json(path, evidence)
        with self.assertRaises(ValueError):
            promote(run, report['approval_digest'])

    def test_gate_rejects_failure_and_budget_relaxation(self):
        run = self.root / 'run'
        report = demo(run)
        base, cand = self.base, self.base.with_route('money', 'decimal_exact')
        before, after = [[read_json(p / 'episode.json') for p in sorted((run / 'holdout' / v).iterdir())] for v in ('v1','v2')]
        failed = copy.deepcopy(after); failed[0]['status'] = 'escalated'
        self.assertFalse(evaluate(base, cand, before, failed, report['dataset_sha'])['recommended'])
        relaxed = replace(cand, max_attempts=5)
        altered = [dict(r, policy_sha=relaxed.sha) for r in after]
        self.assertFalse(evaluate(base, relaxed, before, altered, report['dataset_sha'])['recommended'])

    def test_model_adapter_restricts_output_and_records_tokens(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'}):
            agent = ClaudeAgent('test-model')
        def response(patch_id):
            from io import BytesIO
            return BytesIO(json.dumps({'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': json.dumps({'patch_id': patch_id, 'rationale': 'test'})}], 'usage': {'input_tokens': 10, 'output_tokens': 5}}).encode())
        with patch('three_loop.agents.urlopen', return_value=response('float_round')) as mocked:
            proposal = agent.propose(contract='contract', route='float_first', feedback=[])
            self.assertEqual((proposal.patch_id, proposal.input_tokens, proposal.output_tokens), ('float_round', 10, 5))
            request = json.loads(mocked.call_args.args[0].data)
            self.assertNotIn('tools', request)
        with patch('three_loop.agents.urlopen', return_value=response('decimal_half_up')):
            proposal = agent.propose(contract='contract', route='float_first', feedback=[])
            self.assertEqual(proposal.patch_id, 'INVALID')
            self.assertEqual(proposal.output_tokens, 5)


    def test_learning_derives_route_from_training_evidence(self):
        train = [t for t in tasks() if t.split == 'train']
        reports = [run_episode(t, self.base, ScriptedAgent(), Verifier(), self.root / t.id) for t in train]
        policy, witnesses = propose_policy(self.base, reports)
        self.assertEqual((policy.version, policy.money_start), ('v2', 'decimal_exact'))
        self.assertEqual(witnesses, ['train_fees', 'train_tax'])
        self.assertEqual({k for k, v in policy.__dict__.items() if self.base.__dict__[k] != v}, {'version', 'money_start'})
        contrary = copy.deepcopy(reports)
        contrary[1]['status'] = 'escalated'
        self.assertIsNone(propose_policy(self.base, contrary)[0])

    def test_approval_is_single_use(self):
        run = self.root / 'run'
        report = demo(run)
        promote(run, report['approval_digest'])
        rollback(run, report['baseline_sha'])
        with self.assertRaises(ValueError):
            promote(run, report['approval_digest'])
        self.assertEqual(read_json(run / 'active.json')['version'], 'v1')

    def test_run_active_rejects_pointer_not_in_governance(self):
        run = self.root / 'run'
        report = demo(run)
        cand = baseline().with_route('money', 'decimal_exact')
        write_json(run / 'active.json', {'version': 'v2', 'sha': cand.sha})
        with self.assertRaises(ValueError):
            run_active(run, 'holdout_invoice', self.root / 'next')
        write_json(run / 'active.json', {'version': 'v1', 'sha': self.base.sha})
        promote(run, report['approval_digest'])
        self.assertEqual(run_active(run, 'holdout_invoice', self.root / 'next')['attempts'], 1)

    def test_model_adapter_headers_fences_and_stop_reason(self):
        from io import BytesIO
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'}):
            agent = ClaudeAgent('test-model')
        def reply(text, stop='end_turn'):
            return BytesIO(json.dumps({'stop_reason': stop, 'content': [{'type': 'text', 'text': text}],
                                       'usage': {'input_tokens': 3, 'output_tokens': 2}}).encode())
        fenced = '```json\n{"patch_id": "decimal_half_up", "rationale": "ties"}\n```'
        with patch('three_loop.agents.urlopen', return_value=reply(fenced)) as mocked:
            proposal = agent.propose(contract='c', route='decimal_exact', feedback=[])
            request = mocked.call_args.args[0]
            self.assertEqual(request.get_header('Authorization'), 'Bearer test-only')
            self.assertEqual(request.get_header('Anthropic-version'), API_VERSION)
        self.assertEqual(proposal.patch_id, 'decimal_half_up')
        with patch('three_loop.agents.urlopen', return_value=reply(fenced, stop='max_tokens')):
            self.assertEqual(agent.propose(contract='c', route='decimal_exact', feedback=[]).patch_id, 'INVALID')
        with patch('three_loop.agents.urlopen', return_value=reply('Sure! {"patch_id": "decimal_half_up"}')):
            self.assertEqual(agent.propose(contract='c', route='decimal_exact', feedback=[]).patch_id, 'INVALID')

    def test_live_episode_with_mocked_transport(self):
        from io import BytesIO
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'}):
            agent = ClaudeAgent('test-model')
        def fake_model(request, timeout):
            prompt = json.loads(json.loads(request.data)['messages'][0]['content'])
            choice = 'decimal_half_up' if 'decimal_half_up' in prompt['candidates'] else 'float_round'
            text = json.dumps({'patch_id': choice, 'rationale': 'mock'})
            return BytesIO(json.dumps({'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': text}],
                                       'usage': {'input_tokens': 7, 'output_tokens': 4}}).encode())
        with patch('three_loop.agents.urlopen', side_effect=fake_model) as mocked:
            r = run_episode(self.task, replace(self.base, max_attempts=3), agent, Verifier(), self.root / 'live')
        self.assertEqual((r['status'], r['attempts'], mocked.call_count), ('accepted', 3, 3))
        self.assertEqual([h['output_tokens'] for h in r['history']], [4, 4, 4])


if __name__ == '__main__':
    unittest.main()
