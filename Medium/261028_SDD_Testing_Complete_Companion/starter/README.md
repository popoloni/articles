# SDD Contract Lab: run the public companion

This is a small, standard-library Python implementation of the article's observable-contract tests. Its source, fixtures and oracles are included. It is separate from the author's private native-agent framework and its historical 47-cell matrix.

## One command

Use Python **3.11 or later**, open a terminal in this `starter` directory, and run:

```sh
python3 validate.py
```

Windows PowerShell:

```powershell
py -3 validate.py
```

The command runs the unit suite, the **complete** reference matrix, and all six deliberate mutations. It needs no Python packages, model, paid account, Docker installation or network connection. Current expected results are **81 unit tests, 58 successful subtests, 20 cells with 78 assertions, and six detected mutations**. The reader-runner's own regression tests are separate and do not change the published 81-test baseline.

Every invocation creates a fresh `validation-runs/validation-<UTC time>-<random ID>/` directory. Its `summary.json` links to per-stage JSON reports and console logs, unit JSON/JUnit/log reports, matrix JUnit and individual cell evidence, and all six mutation records. Existing results are preserved. Failed stages retain their evidence and the remaining independent stages still run. Exit code zero means every **requested** stage passed; a requested live step cannot be silently skipped.

An offline success prints `PASS (offline-reference-only); live: NOT_REQUESTED`. This explicitly makes no live-model or private-framework claim. Counts are expected results, not a substitute for checking the generated report. Missing, duplicate, skipped, errored or incomplete records cannot satisfy the validation runner.

Read [Reproduce and inspect the evidence](docs/REPRODUCE.md) for complete POSIX/Windows instructions, a pinned container recipe, output layout and troubleshooting. See the [October 29 local validation](../evidence/local-validation/README.md) for the exact tested environments and retained results; the [original companion validation](../evidence/starter-validation/README.md) preserves the earlier Linux run.

## Optional live Ollama check

Supply both the **exact installed model name** and its **full SHA-256 digest** to include one real request after the offline checks:

```sh
python3 validate.py --ollama-model YOUR_EXACT_INSTALLED_MODEL_NAME --expected-digest YOUR_FULL_64_CHARACTER_SHA256
```

On Windows replace `python3` with `py -3`. This never installs or substitutes a model. A missing server or mismatched identity is nonpassing, and a requested live failure makes the whole command exit nonzero. [The Ollama guide](docs/OLLAMA.md) shows how to read local identities, the exact observed model, and the limits of the gateway test.

## Run individual components

These commands are useful for diagnosis after the complete run:

```sh
python3 tools/run_unit_tests.py --output test-results/run-001
python3 lab.py run
python3 lab.py mutations
python3 lab.py run --scenario denied-write
python3 lab.py list
python3 -m unittest discover -s validation_tests -v
```

The unit-report command requires a fresh output directory. The other run commands generate unique subdirectories under `runs/`. A selected family retains all required repetitions but cannot claim the complete matrix passed. The six mutation cases succeed only when each deliberately broken implementation causes an assertion failure; a crash is not detection. This is a limited detection demonstration, not a comprehensive mutation score.

## What you can reuse

| File | Responsibility |
|---|---|
| [validate.py](validate.py) | One-command orchestration, complete-coverage checks and retained results |
| [scenarios.json](scenarios.json) | Versioned families and required repetitions |
| [sdd_lab/core.py](sdd_lab/core.py) | Reference gate, publisher, permission/tool gateways and session store |
| [sdd_lab/oracles.py](sdd_lab/oracles.py) | Observation-based checks and fail-closed coverage aggregation |
| [sdd_lab/scenarios.py](sdd_lab/scenarios.py) | Twelve concrete scenarios and independent assertions |
| [sdd_lab/runner.py](sdd_lab/runner.py) | Fresh workspaces, evidence retention, source fingerprints and JSON/JUnit reports |
| [sdd_lab/mutations.py](sdd_lab/mutations.py) | Six deliberately defective implementations |
| [sdd_lab/live.py](sdd_lab/live.py) | Optional real Ollama request against the companion gateway |
| [tests/test_contracts.py](tests/test_contracts.py) | Original 81 regression, negative, reporting and mocked-transport tests |
| [validation_tests/test_validate.py](validation_tests/test_validate.py) | Additional orchestration and failure-handling regression tests |

The default matrix covers gate acceptance and failed-gate resume; artifact/spec review freshness; greenfield rollback and managed-brownfield recovery; denied writes; present and absent skills; exposure to a malicious-instruction fixture; allowed and denied synthetic tools; and persisted-session recovery.

The agent is scripted. A fixture skill read is not native Claude/Copilot discovery; the synthetic tool service is not MCP; session interruption simulates a restart. Publisher tests cover bytes, directory structure and ownership-ledger content, not filesystem ownership modes, ACLs, concurrency or power-loss durability. The optional live check tests the companion gateway, not a native coding-agent CLI. No certificate is issued.

To attach your own framework, follow the [integration guide](docs/INTEGRATION.md), [scenario map](docs/SCENARIOS.md) and [security notes](docs/SECURITY.md). Keep the independent oracles and validate your adapter. The included results describe the included companion only.

New code is provided under the [MIT license](LICENSE). It does not relicense the article, artwork or archived historical reports. No font files are included.
