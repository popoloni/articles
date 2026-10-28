# Newly executed companion validation

These results were produced while building this companion on **October 28, 2026**. They test the **included reference implementation**, not the author's original Enterprise SDD runtime. The original live-model and 1,197-test results remain historical and separately attributed.

## Results

| Scope | Observed result | Retained evidence |
|---|---|---|
| Reference regression suite | **81/81 tests PASS**, 58 successful subtests, zero failures/errors/skips | [JSON](unit-tests.json), [JUnit XML](unit-tests.xml), [full log](unit-tests.log) |
| Offline reference scenario matrix | **20/20 cells PASS**, 78 passing assertions across 12 families | [Summary](matrix-20261028T095947Z-559ba564b5/summary.json), [JUnit XML](matrix-20261028T095947Z-559ba564b5/junit.xml), [console](matrix-console.log) |
| Deliberately broken implementations | **6/6 detected by failed assertions**, not crashes | [Summary](mutations-295a33bcee/summary.json), [console](mutations-console.log) |
| Historical-summary auditor regression | **6/6 tests PASS** | [Test source](../../tools/tests/test_record_audit.py), [log](../record-audit/auditor-tests.log) |
| Original record consistency | **16/16 checks PASS** | [Audit result](../record-audit/record-audit.json) |

Execution host: **Python 3.13.5, Linux x86_64**. The full platform identifier and executed source fingerprints are in each machine-readable report. No real model was called for these newly executed results. Optional Ollama behavior is tested using mocked HTTP responses; the reference permission gateway itself executes normally. See the [execution-scope declaration](execution-scope.json).

The original matrix ran on a different, author-recorded Apple Silicon environment. Do not present these Linux results as new native macOS/Windows, Claude, Copilot, MCP or GPU evidence.

## Inspect the proof, not just the totals

For every matrix cell, the summary links to `cells/<id>/report.json`. That report retains explicit assertions and SHA-256 hashes of its evidence: `events.jsonl`, before/after workspace snapshots, final fixture files, and controller state. Tool scenarios also retain a separate synthetic service audit. These are small generated fixtures, not withheld production transcripts.

A file hash does not authenticate an unavailable original report. The original record audit can check count consistency and hash syntax, but it cannot verify the historical payloads whose bytes were never supplied.

The [proof walkthrough](../PROOF_WALKTHROUGH.md) follows one denied-write claim to its actual events, file hashes and deliberately broken counterexample.

## Why the mutation reports are red

The mutation suite patches one implementation at a time without modifying the source files. The matrix oracle must reject each defective behavior. Its reports intentionally contain `FAIL`; the mutation summary is `PASS` because those violations were detected. `ERROR` would not count as detection.

| Deliberate defect | Scenario outcome | Failed assertions |
|---|---|---|
| `allow-protected-write` | FAIL | `operation_bound_policy_denial`, `protected_bytes_unchanged` |
| `silence-policy-denial` | FAIL | `operation_bound_policy_denial` |
| `accept-stale-and-self-review` | FAIL | `stale_artifact_review_rejected`, `old_checkpoint_invalidated`, `builder_cannot_self_approve`, `stale_spec_review_rejected` |
| `rollback-does-nothing` | FAIL | `rollback_restores_complete_workspace`, `rollback_restores_ledger_bytes` |
| `omit-exposure-evidence` | FAIL | `injection_payload_was_read` |
| `bypass-tool-policy` | FAIL | `native_like_gateway_denial_bound_to_attempt`, `zero_server_side_calls`, `no_tool_result_returned` |

This six-defect demonstration does not measure the fraction of all possible defects the harness detects.

## Repeat the new validation

From the extracted package root:

```sh
cd starter
python3 tools/run_unit_tests.py --output test-results/new-run
python3 lab.py run
python3 lab.py mutations
cd ..
python3 -m unittest discover -s tools/tests -v
python3 tools/audit_original_record.py
python3 tools/verify_package.py
```

Choose a new unit-test output directory for each run: existing evidence is not overwritten. Re-running changes timestamps, random receipts and run identifiers; it should reproduce the contracts and verdicts, not identical report bytes.
