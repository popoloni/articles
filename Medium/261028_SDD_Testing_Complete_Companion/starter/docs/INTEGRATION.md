# Replace the reference subject, not the acceptance criteria

## 1. Begin with one real framework promise

Choose a bounded requirement, such as “a missing security review cannot produce a successful checkpoint.” Write down its positive case, negative case, observable side effects, and failure signal before wiring in a model.

The functions in [scenarios.py](../sdd_lab/scenarios.py) receive a workspace, controller-state directory, evidence directory, and controller-owned recorder. They return explicit `Check` objects from [oracles.py](../sdd_lab/oracles.py). The default subjects live in [core.py](../sdd_lab/core.py).

## 2. Replace the subject

For a gate, call your real framework gate command or API, capture its exit code, and inspect the actual checkpoint and artifact bytes. For rollback, invoke your real publication/recovery/rollback path, not a handwritten approximation. Preserve before/after file snapshots and the original ownership ledger.

The teaching gate uses a supplied review dictionary. A production adapter must obtain review evidence from a separately observed session and bind it to artifact and specification digests. Never allow the builder to invent its own reviewer identity or evidence file.

For command-line integration, pass an argument vector with `shell=False`, a bounded timeout, a fresh environment/home, and allowlisted credentials only. Capture stdout/stderr separately. A subprocess timeout does not necessarily terminate grandchildren; use an isolated container/process group and explicit cleanup. Do not point a destructive test at a working repository or reuse the developer's authenticated home directory.

## 3. Keep the observer outside the agent's authority

An origin label in a JSON event is **not** proof of its origin. In the reference harness, trusted Python components own the event channel. In a native integration, trusted collection code must capture runtime events directly and prevent the agent from writing or replacing logs, expected values, manifests, or the oracle implementation.

A denial assertion should match a genuine attempted operation, its tool and arguments, and its operation identifier. Check the protected bytes independently. A transcript sentence such as “the tool was denied” must not be normalized into a permission event.

Use separately collected service-side audits for MCP. For a denied MCP operation, verify discovery and a native permission decision while the server audit remains at zero calls. The included `ToolService` is only a pedagogical substitute; replace it with the real server and its real transport audit.

## 4. Add a scenario without hiding missing coverage

Add a function to `SCENARIOS`, then add its identifier and required repetitions to `scenarios.json`. The manifest loader rejects unknown and duplicate identifiers. A targeted run retains all configured repetitions. Update and review the contract deliberately rather than letting the repair agent relax it after a failure.

Run the unit suite, a targeted family, the full matrix, and relevant defect-injection cases. Add tests for your event parser: prompt echoes, wrong-target denials, missing terminal events, missing cells, stale evidence, and error messages disguised as successful terminal envelopes.

## 5. Native Claude Code / Copilot CLI integrations

The original [portable runbook](../../evidence/reading/README.md) documents the author's native-runtime laboratory and its exact historical pins. Its underlying executable files were not supplied, so this companion does not pretend to contain functioning vendor adapters reconstructed from prose.

Implement adapters against the currently installed CLI's actual structured output, permission mechanisms, native instruction/skill locations, observed session identifiers, and terminal-result semantics. Pin and retain the versions and output samples used for parser tests. A generic HTTP model call does not test any of those CLI-specific mechanisms.

The optional [direct Ollama probe](OLLAMA.md) gives a working network integration against the companion gateway. It is useful for learning the observation pattern, but is not a replacement for either native CLI adapter or the restricted relay.

## 6. Evolve isolation before autonomy

A production native-agent harness should run workers in a disposable OS/container boundary, isolate credentials and tool access, limit network egress, and prevent writes to controller evidence. Test that boundary itself. Retain source, dependency, image and model identities. Then add bounded repair orchestration with a maximum attempt count, a time budget, an allowlisted change set, and escalation rather than silently weakening assertions.

No unattended repair controller is implemented here. The `mutations` command only evaluates fixed, deliberately defective implementations.
