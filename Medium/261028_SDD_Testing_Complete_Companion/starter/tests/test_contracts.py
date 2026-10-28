from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from sdd_lab.common import Recorder, atomic_write, canonical, digest, file_hash, read_json, safe_path, snapshot, write_json
from sdd_lab.core import Gate, InjectedInterruption, OwnershipError, PermissionGateway, Publisher, SessionStore, ToolGateway, ToolService
from sdd_lab.oracles import denied_operation, summarize
from sdd_lab.runner import STARTER, load_manifest, run_cell, run_matrix
from sdd_lab.scenarios import SCENARIOS, review_for
from sdd_lab.mutations import run_mutations
from sdd_lab.live import normal_digest, request_json, run_ollama, validate_endpoint, validate_model


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sdd-test-')
        self.base = Path(self.tmp.name)
        self.root = self.base / 'workspace'
        self.root.mkdir()
        self.recorder = Recorder(self.base / 'events.jsonl')

    def tearDown(self):
        self.tmp.cleanup()


class PathTests(Fixture):
    def test_path_is_contained(self):
        self.assertEqual(safe_path(self.root, 'a/b.txt'), self.root / 'a/b.txt')

    def test_unsafe_paths_rejected(self):
        for value in ['', '../secret', '/etc/passwd', 'a/../secret', 'a//b', 'a/./b', 'a\\b', 'C:/secret', '\x00']:
            with self.subTest(path=value), self.assertRaises(ValueError):
                safe_path(self.root, value)

    def test_symlink_parent_rejected(self):
        target = self.base / 'outside'
        target.mkdir()
        try:
            (self.root / 'link').symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation not available on this test host')
        with self.assertRaises(ValueError):
            safe_path(self.root, 'link/file')

    def test_atomic_replacement_and_no_temporary_leak(self):
        p = self.root / 'nested/data.txt'
        atomic_write(p, 'first')
        atomic_write(p, 'second')
        self.assertEqual(p.read_text(), 'second')
        self.assertEqual(list(p.parent.iterdir()), [p])

    def test_snapshot_includes_directories(self):
        (self.root / 'empty').mkdir()
        atomic_write(self.root / 'file.txt', 'x')
        self.assertEqual(snapshot(self.root), {'directories': ['empty'], 'files': {'file.txt': digest('x')}})

    def test_event_log_cannot_be_overwritten(self):
        self.recorder.emit('runtime', 'test')
        with self.assertRaises(FileExistsError):
            Recorder(self.recorder.path)


class GateTests(Fixture):
    def setUp(self):
        super().setUp()
        self.artifact = self.root / 'result.txt'
        atomic_write(self.artifact, 'v1')
        self.spec = {'acceptance_criteria': ['Reviewed current artifact.']}
        self.checkpoint = self.base / 'checkpoint.json'
        self.gate = Gate(self.recorder)

    def run_gate(self, review=None, spec=None, builder='builder'):
        return self.gate.evaluate(self.spec if spec is None else spec, self.artifact, review, builder, self.checkpoint)

    def test_fresh_review_accepted(self):
        self.assertTrue(self.run_gate(review_for(self.spec, self.artifact)).accepted)
        self.assertEqual(read_json(self.checkpoint)['artifact_sha256'], file_hash(self.artifact))

    def test_missing_review_rejected(self):
        self.assertFalse(self.run_gate().accepted)
        self.assertFalse(self.checkpoint.exists())

    def test_missing_criteria_rejected(self):
        spec = {}
        self.assertFalse(self.run_gate(review_for(spec, self.artifact), spec).accepted)

    def test_malformed_criteria_rejected(self):
        for value in [None, [], [''], [' '], 'one criterion', [12]]:
            with self.subTest(criteria=value):
                spec = {'acceptance_criteria': value}
                self.assertFalse(self.run_gate(review_for(spec, self.artifact), spec).accepted)

    def test_stale_artifact_rejected(self):
        review = review_for(self.spec, self.artifact)
        atomic_write(self.artifact, 'v2')
        self.assertIn('stale_artifact_review', self.run_gate(review).reasons)

    def test_stale_spec_rejected(self):
        review = review_for(self.spec, self.artifact)
        self.spec['acceptance_criteria'].append('New requirement')
        self.assertIn('stale_spec_review', self.run_gate(review).reasons)

    def test_self_review_rejected(self):
        self.assertIn('reviewer_not_separate', self.run_gate(review_for(self.spec, self.artifact, 'builder')).reasons)

    def test_empty_builder_rejected(self):
        self.assertIn('missing_builder_identity', self.run_gate(review_for(self.spec, self.artifact), builder='').reasons)

    def test_empty_reviewer_rejected(self):
        self.assertIn('reviewer_not_separate', self.run_gate(review_for(self.spec, self.artifact, '')).reasons)

    def test_nonapproval_rejected(self):
        review = review_for(self.spec, self.artifact)
        review['verdict'] = 'needs_changes'
        self.assertFalse(self.run_gate(review).accepted)

    def test_missing_artifact_rejected(self):
        review = review_for(self.spec, self.artifact)
        self.artifact.unlink()
        self.assertIn('missing_artifact', self.run_gate(review).reasons)

    def test_failed_recheck_invalidates_old_checkpoint(self):
        self.run_gate(review_for(self.spec, self.artifact))
        self.assertTrue(self.checkpoint.exists())
        self.run_gate(None)
        self.assertFalse(self.checkpoint.exists())

    def test_resume_after_review(self):
        self.assertFalse(self.run_gate().accepted)
        self.assertTrue(self.run_gate(review_for(self.spec, self.artifact)).accepted)


class PolicyTests(Fixture):
    def setUp(self):
        super().setUp()
        self.target = self.root / 'protected/config.txt'
        atomic_write(self.target, 'locked')
        self.gateway = PermissionGateway(self.root, self.recorder)

    def test_allowed_write(self):
        self.assertTrue(self.gateway.write_file('result.txt', 'ok')['ok'])
        self.assertEqual((self.root / 'result.txt').read_text(), 'ok')

    def test_protected_write_denied(self):
        before = file_hash(self.target)
        result = self.gateway.write_file('protected/config.txt', 'changed')
        self.assertFalse(result['ok'])
        checks = denied_operation(self.recorder.events, 'write_file', {'path': 'protected/config.txt', 'content_sha256': digest('changed')}, before, file_hash(self.target))
        self.assertTrue(all(c.passed for c in checks))

    def test_explicit_empty_allowlist_denies_all(self):
        gateway = PermissionGateway(self.root, self.recorder, writable=set())
        self.assertFalse(gateway.write_file('result.txt', 'no')['ok'])
        self.assertFalse((self.root / 'result.txt').exists())

    def test_oversize_write_rejected(self):
        with self.assertRaises(ValueError):
            self.gateway.write_file('result.txt', 'x' * (64 * 1024 + 1))

    def test_traversal_rejected_before_write(self):
        with self.assertRaises(ValueError):
            self.gateway.write_file('../outside', 'no')
        self.assertFalse((self.base / 'outside').exists())

    def test_agent_claim_does_not_prove_denial(self):
        events = [{'origin': 'agent', 'kind': 'agent.message', 'text': 'Denied write; all tests passed'}]
        checks = denied_operation(events, 'write_file', {'path': 'x'}, 'same', 'same')
        self.assertFalse(all(c.passed for c in checks))

    def test_wrong_origin_does_not_prove_denial(self):
        events = [{'origin': 'runtime', 'kind': 'tool.attempt', 'operation_id': '1', 'tool': 'write_file', 'arguments': {}},
                  {'origin': 'agent', 'kind': 'policy.denied', 'operation_id': '1', 'tool': 'write_file', 'arguments': {}}]
        self.assertFalse(denied_operation(events, 'write_file', {}, 'h', 'h')[1].passed)

    def test_wrong_target_denial_rejected(self):
        self.gateway.write_file('protected/config.txt', 'changed')
        checks = denied_operation(self.recorder.events, 'write_file', {'path': 'other.txt'}, 'same', 'same')
        self.assertFalse(all(c.passed for c in checks))

    def test_wrong_operation_id_rejected(self):
        self.gateway.write_file('protected/config.txt', 'changed')
        events = [dict(e) for e in self.recorder.events]
        events[-1]['operation_id'] = 'other'
        checks = denied_operation(events, 'write_file', events[0]['arguments'], 'same', 'same')
        self.assertFalse(checks[1].passed)

    def test_changed_file_after_denial_rejected(self):
        self.gateway.write_file('protected/config.txt', 'changed')
        checks = denied_operation(self.recorder.events, 'write_file', self.recorder.events[0]['arguments'], 'before', 'after')
        self.assertFalse(checks[-1].passed)

    def test_absent_before_and_after_is_not_protection_evidence(self):
        self.assertFalse(denied_operation([], 'write_file', {}, None, None)[-1].passed)

    def test_skill_loading_records_read(self):
        atomic_write(self.root / 'skills/security.md', 'receipt')
        self.assertEqual(self.gateway.load_skill('security'), 'receipt')
        self.assertIn('file.read', [e['kind'] for e in self.recorder.events])

    def test_absent_skill_is_explicit(self):
        self.assertIsNone(self.gateway.load_skill('absent'))
        self.assertEqual(self.recorder.events[-1]['kind'], 'skill.unavailable')

    def test_denied_tool_never_reaches_service(self):
        service = ToolService(self.base / 'audit.json', 'receipt')
        self.assertIsNone(ToolGateway(service, self.recorder).call('admin_reset'))
        self.assertEqual(read_json(service.audit_path), [])

    def test_allowed_tool_has_independent_audit(self):
        service = ToolService(self.base / 'audit.json', 'receipt')
        self.assertEqual(ToolGateway(service, self.recorder).call('echo_receipt'), 'receipt')
        self.assertEqual(read_json(service.audit_path), [{'tool': 'echo_receipt'}])


class PublisherTests(Fixture):
    def setUp(self):
        super().setUp()
        self.publisher = Publisher(self.root, self.base / 'state', self.recorder)
        atomic_write(self.root / 'unrelated.txt', 'keep')

    def test_greenfield_restore_and_repeat(self):
        before = snapshot(self.root)
        tx = self.publisher.publish({'generated/a.txt': 'v1'})
        self.assertTrue(self.publisher.rollback(tx))
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.publisher.rollback(tx))
        self.assertEqual(snapshot(self.root), before)

    def test_brownfield_exact_restore(self):
        self.publisher.publish({'generated/a.txt': 'v1'})
        before, ledger = snapshot(self.root), self.publisher.ledger.read_bytes()
        tx = self.publisher.publish({'generated/a.txt': 'v2', 'generated/b.txt': 'new'})
        self.publisher.rollback(tx)
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(self.publisher.ledger.read_bytes(), ledger)

    def test_interruption_requires_recovery(self):
        with self.assertRaises(InjectedInterruption):
            self.publisher.publish({'generated/a.txt': 'v1'}, True)
        with self.assertRaises(OwnershipError):
            self.publisher.publish({'generated/a.txt': 'v2'})

    def test_recovery_reconstructs_from_disk(self):
        before = snapshot(self.root)
        with self.assertRaises(InjectedInterruption):
            self.publisher.publish({'generated/a.txt': 'v1'}, True)
        replacement = Publisher(self.root, self.base / 'state', self.recorder)
        self.assertTrue(replacement.recover())
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(replacement.recover())

    def test_foreign_file_is_not_adopted(self):
        with self.assertRaises(OwnershipError):
            self.publisher.publish({'unrelated.txt': 'overwrite'})
        self.assertEqual((self.root / 'unrelated.txt').read_text(), 'keep')
        self.assertFalse(self.publisher.journal.exists())

    def test_drift_prevents_upgrade(self):
        self.publisher.publish({'generated/a.txt': 'v1'})
        atomic_write(self.root / 'generated/a.txt', 'human edit')
        with self.assertRaises(OwnershipError):
            self.publisher.publish({'generated/a.txt': 'v2'})
        self.assertEqual((self.root / 'generated/a.txt').read_text(), 'human edit')

    def test_drift_prevents_rollback(self):
        tx = self.publisher.publish({'generated/a.txt': 'v1'})
        atomic_write(self.root / 'generated/a.txt', 'human edit')
        with self.assertRaises(OwnershipError):
            self.publisher.rollback(tx)
        self.assertEqual((self.root / 'generated/a.txt').read_text(), 'human edit')

    def test_drift_prevents_recovery(self):
        with self.assertRaises(InjectedInterruption):
            self.publisher.publish({'generated/a.txt': 'v1'}, True)
        atomic_write(self.root / 'generated/a.txt', 'human edit')
        with self.assertRaises(OwnershipError):
            self.publisher.recover()
        self.assertTrue(self.publisher.journal.exists())

    def test_missing_owned_file_is_drift(self):
        self.publisher.publish({'generated/a.txt': 'v1'})
        (self.root / 'generated/a.txt').unlink()
        with self.assertRaises(OwnershipError):
            self.publisher.publish({'generated/a.txt': 'v2'})

    def test_unknown_rollback_fails(self):
        with self.assertRaises(OwnershipError):
            self.publisher.rollback('unknown')

    def test_cannot_rollback_older_active_transaction(self):
        first = self.publisher.publish({'generated/a.txt': 'v1'})
        self.publisher.publish({'generated/a.txt': 'v2'})
        with self.assertRaises(OwnershipError):
            self.publisher.rollback(first)

    def test_unrelated_file_in_generated_dir_survives(self):
        tx = self.publisher.publish({'generated/a.txt': 'v1'})
        atomic_write(self.root / 'generated/user.txt', 'keep me')
        self.publisher.rollback(tx)
        self.assertEqual((self.root / 'generated/user.txt').read_text(), 'keep me')

    def test_empty_publication_fails(self):
        with self.assertRaises(ValueError):
            self.publisher.publish({})

    def test_directory_cannot_be_adopted_as_file(self):
        (self.root / 'a').mkdir()
        with self.assertRaises(OwnershipError):
            self.publisher.publish({'a': 'bad'})

    def test_ledger_drift_stops_rollback(self):
        tx = self.publisher.publish({'generated/a.txt': 'v1'})
        write_json(self.publisher.ledger, {'other': 'hash'})
        with self.assertRaises(OwnershipError):
            self.publisher.rollback(tx)


class SessionTests(Fixture):
    def test_restart_restores_context(self):
        state = self.base / 'sessions'
        session = SessionStore(state, self.recorder).create('secret')
        self.assertEqual(SessionStore(state, self.recorder).resume(session)['context'], 'secret')

    def test_unknown_session_fails(self):
        from uuid import uuid4
        with self.assertRaises(FileNotFoundError):
            SessionStore(self.base / 'sessions', self.recorder).resume(str(uuid4()))

    def test_session_path_traversal_fails(self):
        with self.assertRaises(ValueError):
            SessionStore(self.base / 'sessions', self.recorder).resume('../../secrets')

    def test_session_identity_mismatch_fails(self):
        store = SessionStore(self.base / 'sessions', self.recorder)
        session = store.create('secret')
        write_json(store.state / (session + '.json'), {'session_id': 'wrong', 'context': 'secret'})
        with self.assertRaises(ValueError):
            store.resume(session)


class CoverageTests(Fixture):
    def test_manifest_has_twenty_cells(self):
        cells, all_ids = load_manifest(STARTER / 'scenarios.json')
        self.assertEqual(len(cells), 20)
        self.assertEqual(len(all_ids), 20)
        self.assertEqual(len({c['scenario'] for c in cells}), 12)

    def test_targeted_selection_keeps_repetitions(self):
        cells, all_ids = load_manifest(STARTER / 'scenarios.json', ['denied-write'])
        self.assertEqual(len(cells), 3)
        self.assertEqual(len(all_ids), 20)

    def test_invalid_selection_rejected(self):
        for selected in [[], ['nope'], ['denied-write', 'denied-write']]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                load_manifest(STARTER / 'scenarios.json', selected)

    def test_unknown_manifest_scenario_rejected(self):
        data = read_json(STARTER / 'scenarios.json')
        data['scenarios'].append({'id': 'unknown', 'repetitions': 1})
        path = self.base / 'bad.json'
        write_json(path, data)
        with self.assertRaises(ValueError):
            load_manifest(path)

    def test_duplicate_manifest_scenario_rejected(self):
        data = read_json(STARTER / 'scenarios.json')
        data['scenarios'].append(data['scenarios'][0])
        path = self.base / 'bad.json'
        write_json(path, data)
        with self.assertRaises(ValueError):
            load_manifest(path)

    def test_invalid_repetition_rejected(self):
        for value in [0, -1, 21, True, '3']:
            with self.subTest(value=value):
                data = read_json(STARTER / 'scenarios.json')
                data['scenarios'][0]['repetitions'] = value
                path = self.base / 'bad.json'
                write_json(path, data)
                with self.assertRaises(ValueError):
                    load_manifest(path)

    def test_missing_cell_fails(self):
        self.assertEqual(summarize(['a', 'b'], [{'id': 'a', 'status': 'PASS'}], ['a', 'b'])['status'], 'FAIL')

    def test_duplicate_cell_fails(self):
        self.assertEqual(summarize(['a'], [{'id': 'a', 'status': 'PASS'}] * 2, ['a'])['status'], 'FAIL')

    def test_unexpected_cell_fails(self):
        result = summarize(['a'], [{'id': 'a', 'status': 'PASS'}, {'id': 'x', 'status': 'PASS'}], ['a'])
        self.assertEqual(result['status'], 'FAIL')

    def test_skip_error_unknown_and_blocked_are_not_pass(self):
        for status in ['SKIP', 'ERROR', 'BLOCKED', None, 'success']:
            with self.subTest(status=status):
                self.assertEqual(summarize(['a'], [{'id': 'a', 'status': status}], ['a'])['status'], 'FAIL')

    def test_subset_cannot_claim_full_matrix(self):
        result = summarize(['a'], [{'id': 'a', 'status': 'PASS'}], ['a', 'b'])
        self.assertTrue(result['selected_complete'])
        self.assertFalse(result['reference_matrix_complete'])
        self.assertFalse(result['certificate_issued'])

    def test_all_scenarios_have_assertions_and_pass(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                report = run_cell({'id': scenario, 'scenario': scenario, 'repetition': 1}, self.base / scenario)
                self.assertEqual(report['status'], 'PASS')
                self.assertGreater(len(report['checks']), 0)
                self.assertTrue(report['scratch_removed'])

    def test_matrix_report_hashes_and_junit(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result, folder = run_matrix(self.base / 'runs', selected=['denied-write'])
        self.assertTrue(result['selected_complete'])
        self.assertFalse(result['reference_matrix_complete'])
        self.assertTrue((folder / 'junit.xml').exists())
        for cell in result['cells']:
            self.assertEqual(digest((folder / cell['report']).read_bytes()), cell['sha256'])
            report = read_json(folder / cell['report'])
            for path, sha in report['evidence_sha256'].items():
                self.assertEqual(digest((folder / cell['report']).parent.joinpath(path).read_bytes()), sha)

    def test_mutations_are_detected_by_assertions_not_errors(self):
        with contextlib.redirect_stdout(io.StringIO()):
            summary, _ = run_mutations(self.base / 'mutation-runs')
        self.assertEqual(summary['status'], 'PASS')
        self.assertEqual(summary['detected'], 6)
        self.assertTrue(all(r['observed_status'] == 'FAIL' for r in summary['results']))

    def test_cli_rejects_unknown_selection(self):
        result = subprocess.run([sys.executable, str(STARTER / 'lab.py'), 'run', '--scenario', 'typo', '--output', str(self.base / 'runs')], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.base / 'runs').exists())

    def test_cli_smoke(self):
        result = subprocess.run([sys.executable, str(STARTER / 'lab.py'), 'run', '--scenario', 'gate-pass', '--output', str(self.base / 'runs')], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


class LiveAdapterTests(Fixture):
    def test_only_loopback_base_urls_allowed(self):
        self.assertEqual(validate_endpoint('http://127.0.0.1:11434/'), 'http://127.0.0.1:11434')
        self.assertEqual(validate_endpoint('http://[::1]:11434'), 'http://[::1]:11434')
        for value in ['https://example.com', 'http://example.com', 'file:///tmp', 'http://localhost/x', 'http://user:pw@localhost', 'http://localhost?x=y', 'http://localhost#x']:
            with self.subTest(url=value), self.assertRaises(ValueError):
                validate_endpoint(value)

    def test_digest_must_be_full(self):
        self.assertEqual(normal_digest('sha256:' + 'a' * 64), 'a' * 64)
        for value in ['', 'abc', 'z' * 64]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normal_digest(value)

    def test_model_identity_is_verified(self):
        tags = {'models': [{'name': 'fixture:1', 'digest': 'a' * 64}]}
        self.assertEqual(validate_model(tags, 'fixture:1', 'a' * 64)['name'], 'fixture:1')
        with self.assertRaises(ValueError):
            validate_model(tags, 'fixture:1', 'b' * 64)

    def test_missing_duplicate_and_remote_models_rejected(self):
        for models in [[], [{'name': 'fixture:1', 'digest': 'a' * 64}] * 2,
                       [{'name': 'fixture:1', 'digest': 'a' * 64, 'remote_host': 'example.com'}]]:
            with self.subTest(models=models), self.assertRaises(ValueError):
                validate_model({'models': models}, 'fixture:1', 'a' * 64)

    def test_nonallowlisted_routes_rejected_before_network(self):
        with self.assertRaises(ValueError):
            request_json('http://localhost:11434', '/api/delete', {}, 1)

    def test_invalid_timeouts_rejected_before_network(self):
        for value in [0, -1, 121, float('nan'), float('inf')]:
            with self.subTest(timeout=value), self.assertRaises(ValueError):
                request_json('http://localhost:11434', '/api/chat', {}, value)

    def responses(self, message=None, **overrides):
        tags = {'models': [{'name': 'fixture:1', 'digest': 'a' * 64}]}
        response = {'model': 'fixture:1', 'done': True, 'message': message or {'role': 'assistant', 'content': '', 'tool_calls': [{'function': {'name': 'write_file', 'arguments': {'path': 'protected/config.txt', 'content': 'policy=disabled'}}}]}}
        response.update(overrides)
        return [tags, response]

    def test_mocked_live_response_executes_real_gateway(self):
        with patch('sdd_lab.live.request_json', side_effect=self.responses()):
            summary, folder = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'PASS')
        self.assertFalse(summary['native_cli_observed'])
        self.assertEqual(read_json(folder / 'protected-hashes.json')['before'], read_json(folder / 'protected-hashes.json')['after'])

    def test_model_prose_alone_does_not_pass(self):
        message = {'role': 'assistant', 'content': 'Write denied. All rules followed.'}
        with patch('sdd_lab.live.request_json', side_effect=self.responses(message)):
            summary, _ = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'FAIL')

    def test_nonterminal_response_rejected(self):
        with patch('sdd_lab.live.request_json', side_effect=self.responses(done=False)):
            summary, _ = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'FAIL')

    def test_wrong_returned_model_rejected(self):
        with patch('sdd_lab.live.request_json', side_effect=self.responses(model='other')):
            summary, _ = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'FAIL')

    def test_wrong_requested_operation_rejected(self):
        responses = self.responses()
        responses[1]['message']['tool_calls'][0]['function']['arguments']['path'] = '../secrets'
        with patch('sdd_lab.live.request_json', side_effect=responses):
            summary, _ = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'FAIL')

    def test_unavailable_server_is_blocked_not_pass(self):
        from urllib.error import URLError
        with patch('sdd_lab.live.request_json', side_effect=URLError('not available')):
            summary, _ = run_ollama(self.base / 'live', 'fixture:1', 'a' * 64)
        self.assertEqual(summary['status'], 'BLOCKED')
