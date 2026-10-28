# SDD Contract Lab: a reusable starting implementation

A small, inspectable Python implementation of the testing ideas in the article. It is **new companion code**, not an export of the author's private Enterprise SDD implementation. The default run uses scripted fixtures: no model, paid account, network access, Docker installation, or third-party Python package is required.

## Run it

Use Python **3.11 or later**. From the extracted companion directory:

```sh
cd starter
python3 -m unittest discover -s tests -v
python3 lab.py run
python3 lab.py mutations
```

On Windows, use `py -3` or your Python 3.11+ interpreter in place of `python3`. Only the Linux/Python version stated in the bundled validation report was executed while preparing this package; cross-platform certification is not claimed.

The default matrix has **12 scenario families and 20 execution cells**. The mutation command deliberately breaks six implementations. It succeeds only when each defect causes an **assertion failure**, not an exception. This is a limited detection demonstration, not a comprehensive mutation score.

Every run gets a unique subdirectory under `runs/`. Read its `summary.json`, `junit.xml`, and `cells/`. Cells retain before/after hashes, operation events, assertions, final fixture files, and controller state. Temporary workspaces are removed, but evidence is kept. Earlier runs are not overwritten.

```sh
# Re-run one family; all three required repetitions are retained.
python3 lab.py run --scenario denied-write

# Produce machine-readable unit-test results and a complete log.
python3 tools/run_unit_tests.py --output test-results/run-001

# List the actual expanded cell manifest.
python3 lab.py list
```

An unknown selection fails. A selected-family pass cannot claim the full reference matrix passed. Missing, duplicate, unexpected, skipped, errored, and blocked results are not silently accepted. `certificate_issued` remains false.

## What you can reuse

| File | Responsibility |
|---|---|
| [scenarios.json](scenarios.json) | Versioned families and required repetitions |
| [sdd_lab/core.py](sdd_lab/core.py) | Reference gate, publisher, permission/tool gateways, session store |
| [sdd_lab/oracles.py](sdd_lab/oracles.py) | Observation-based checks and fail-closed coverage aggregation |
| [sdd_lab/scenarios.py](sdd_lab/scenarios.py) | Twelve concrete test scenarios and independent assertions |
| [sdd_lab/runner.py](sdd_lab/runner.py) | Fresh workspaces, evidence retention, source fingerprints, JSON/JUnit reports |
| [sdd_lab/mutations.py](sdd_lab/mutations.py) | Six temporary, deliberately defective implementations |
| [sdd_lab/live.py](sdd_lab/live.py) | Optional real Ollama request against the companion's own gateway |
| [tests/test_contracts.py](tests/test_contracts.py) | Regression, negative, reporting, and mocked-transport tests |

The default matrix exercises gate acceptance and failed-gate resume; artifact/spec review freshness; greenfield rollback and managed-brownfield recovery; denied writes; present and absent skills; exposure to a malicious instruction fixture; allowed and denied synthetic tools; and persisted-session recovery.

**Scope is deliberately honest.** These are real executions of the included reference code, but the agent is scripted. A fixture skill read is not native Claude/Copilot discovery. The synthetic tool service is not an MCP implementation. Session interruption is a simulated restart, not termination of a real coding-agent process. The publisher tests bytes, directory structure, and ownership-ledger content, not ownership modes, ACLs, concurrency, or power-loss durability.

## Add your framework

Follow the [integration guide](docs/INTEGRATION.md). Replace the reference subject with an adapter to your own framework, retain independent oracles, and test that adapter with positive and negative fixtures. Do not relabel the supplied results as results for your implementation.

The [scenario map](docs/SCENARIOS.md) explains which article concepts are implemented and where native-runtime coverage is still needed. The [security and trust-boundary notes](docs/SECURITY.md) explain why a temporary directory is not a sandbox.

## Optional real-model probe

The optional [Ollama guide](docs/OLLAMA.md) explains a single, bounded real model request. It tests this companion gateway, **not** Claude Code or Copilot CLI. The network response handling has offline regression tests, but a real Ollama/model execution was **not** performed while building this package.

```sh
python3 lab.py ollama \
  --model YOUR_EXACT_INSTALLED_MODEL_NAME \
  --expected-digest YOUR_FULL_64_CHARACTER_MODEL_SHA256
```

Those two values must come from your own installation. This command never installs a model or forwards cloud credentials. A missing prerequisite produces a nonpassing result, not a fabricated success.

## Optional container smoke

The [Dockerfile](Dockerfile) is an optional recipe, not a tested or supplied binary image. A build needs a base image; specify a verified digest to pin its bytes. The following smoke runs only the offline unit suite and writes its log to the host's redirected output:

```sh
docker build -t sdd-contract-lab .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 512m \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m sdd-contract-lab \
  > docker-unit-tests.log 2>&1
```

No Docker execution is included in the new validation claim. This optional smoke is not the original multi-container inference-relay architecture.

## Evidence and reuse

Read the [executed validation results](../evidence/starter-validation/README.md) and the [original evidence inventory](../evidence/README.md). They distinguish historical results from new reference tests and unexecuted options.

New code under this directory is provided under the [MIT license](LICENSE). That license does not relicense the article, book artwork, or archived original reports. No font files are included.
