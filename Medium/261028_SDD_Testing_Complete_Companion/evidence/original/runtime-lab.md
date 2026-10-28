# W30 isolated CLI lab — smoke and expanded scenario matrix

Recorded October 27, 2026. **F.3/F.4 remain partial/blocked; 32/59 wave tasks
complete. No compatibility certificate or F.5 closure.**

**Ollama continuation:** the lab now supports native Apple Silicon/Metal inference
through [config.ollama.json](../../../_tests/harness_runtime/config.ollama.json),
using the existing Qwen 3.5 9B Q4_K_M weights without cloud credentials. See the
Ollama section below for observed runs; the original cloud attempts remain
historical evidence and are not overwritten.

**Final local-model smoke:** `20261027T205558Z-29cdd631.json` reports **PASS for
both CLIs, 22/22 checks each**, with distinct observed builder/reviewer sessions.
No native compatibility certificate is implied.

## Expanded scenario suite — October 27

**Final result, October 28 Europe/Rome (October 27 UTC): PASS, 47/47 local
cells.** The complete run `matrix-20261027T224601Z-b0dc9db0` started at
22:46:01 UTC and finished at 23:05:12 UTC. Its relay audit validated 148 entries,
including exactly two expected client disconnects from deliberate interruption.
All 47 worker containers, the relay and its internal network were removed.
The lab model was then unloaded from GPU memory; its alias/weights and the
existing Ollama service remain available for replay.

| Validation | Final result |
|---|---|
| Structural matrix | 3 independent runs × all 12 scenario IDs PASS; real Sandbox venv/pip/installed CLI retained |
| Claude Code 2.1.311 | 22/22 live cells PASS |
| Copilot CLI 1.0.104 | 22/22 live cells PASS |
| Critical negatives | 3 independent repetitions per CLI for absent skill, write/shell denial, injection and MCP denial |
| Ollama runtime | Pinned digest, 65,536 context and fully GPU-resident weights checked before/after all 44 live cells |
| Full offline regression | 1,195 passed, 111 subtests passed, 20 PowerShell skips, zero failures, one existing fixture deprecation warning; 257.11 seconds |

The regression report is `regression-09068f8979eb452faea6a1d9492efa6b.json`.
The [replay record](runtime-lab-record.json) stores report hashes, tested image
IDs, recipe/source hashes, coverage and retained failed attempts. Final evidence
documentation was written after execution, so a subsequent documentation-only
image rebuild has a new source/image identity. The recorded live verdict belongs
to the original tested images, not an unexecuted replacement image.

The [saved manifest](../../../_tests/harness_runtime/scenarios.json) defines 47
local cells. Three complete structural runs cover all twelve deterministic IDs;
live CLI cases cover native agents/skills/instructions, optional presence/absence,
write/shell denial, injection, allowed/denied MCP, requirements/review and actual
interrupted-session recovery. Critical negatives use three fresh containers per
CLI. The full test tree and CLI wheels are baked into a network-disabled
regression image; no host Python packages or CLI settings are changed.

The first complete matrix execution, `matrix-20261027T220906Z-aaaa0c51`, passed
all 47 individual cells but correctly retained an aggregate FAIL: the initial
audit validator classified deliberate client disconnections during session
interruption as transport faults. The fix distinguishes client response-write
disconnections from upstream errors and limits exceptions to completed intentional
interruption tests. The first repaired full regression passed **1,192 tests and
111 subtests**, with **20 PowerShell skips**, zero failures and one existing
warning (`regression-4a9f7ab2bb5d47f5ac0949257046683a.json`). Final reruns are
recorded in the machine-readable replay record; historical reports remain intact.

| Finding | Correction and evidence |
|---|---|
| Real sandbox launcher failed on noexec tmpfs | Offline test tmpfs is executable; real installed CLI lifecycle retained; all twelve structural scenarios passed three times |
| Image omitted support files/executable modes | Include scripts, audit allowlist, placeholder env and normalized modes; full regression green |
| Claude Messages request adds beta query | Allow only the observed exact `?beta=true` variant; arbitrary queries remain rejected |
| Copilot skill hidden from model-facing tool | Use documented native skill metadata/invocation; hidden-receipt probes pass |
| Local model retried denied operations until timeout | Request exactly one attempt and stop on denial; rerun all three repetitions; keep timeout evidence |
| Missing Claude skill was correctly reported with an unrecognized synonym | Use the same slash-invocation prompt for installed/absent skills with an explicit UNAVAILABLE fallback; retain inventory and withheld-receipt checks; focused 5/5 and fresh full 47/47 pass |
| Loose response/denial checks could accept incomplete evidence | Require terminal CLI results, final answers, and native policy denial bound to intended tool/arguments |
| Interrupted response marker could split across reads | Detect markers across accumulated stdout; regression test added |
| Injection read/answer evidence needed stronger binding | Require successful read of the expected file including the payload and only a legitimate project-code answer |
| Audit collection/postflight failure could preserve PASS | Aggregate audit validation and explicit postflight failure; expected interruption disconnects narrowly classified |

Workers have no host mounts or published ports. Live cells check blocked direct
public/host-Ollama TCP paths and rejected model-management access; the relay routes
only the pinned local model. Native CLI events, session IDs, source/image/config
hashes, protected file digests and MCP audits are retained per attempt. Reports
remain scoped to local structural/synthetic scenarios, with no compatibility
certificate. Full production role/workflow conformance, VS Code, native OS
execution and pilot acceptance remain unresolved. No Phase G implementation.

## Delivered

The [runbook](../../../_tests/harness_runtime/README.md) documents the host runner,
container recipe, effective [configuration](../../../_tests/harness_runtime/config.json),
[version lock](../../../_tests/harness_runtime/versions.lock.json), credentials,
resource/time/cost boundaries, replay, cleanup and remaining scenario coverage.
The runner reuses canonical workflow preparation, existing eval assertions,
deterministic gate/resume commands and the F.2 deployment fixtures. No production
capability profile was promoted, no existing assertion was changed, and no
Phase G implementation began.

Both latest-stable package releases were resolved from their official npm
registry entries at 19:30 UTC and their integrity hashes recorded:

| Component | Recorded value |
|---|---|
| Host Python | 3.13.14; standard library only, no new host dependencies |
| Docker client/server | 27.3.1, desktop-linux |
| Container platform | linux/arm64 |
| Claude Code | 2.1.311 |
| Copilot CLI | 1.0.104 |
| Container Python | 3.11.2 |
| Container pytest | 9.1.1 |
| Claude model | claude-sonnet-5-5, listed by authenticated model API |
| Copilot model | Unselected; token unavailable |
| Per-container resources | 2 CPUs, 2 GiB memory, 128 processes |
| Time/budget | 300 seconds per CLI invocation; Claude USD 2 per invocation; Copilot account-side spending policy required |

The standalone host Claude installation remains separate from these images.
Docker Desktop was started; no global CLI or Python packages were installed.
The initial VS Code task creation timed out; the task was subsequently created
and successfully used for both image builds. Expanded-suite orchestration used
host Python 3.14.6; the build task uses Python 3.13.14. Both use only the standard
library. The frozen deterministic bootstrap and its 21 unit tests were retained.

## Final offline verification

Host runner tests: **14 passed** using `python3.13 _tests/test_harness_runtime.py -v`.
VS Code had no discovered tests for the new file, so its direct standard-library
unittest entrypoint was used. Editor diagnostics were clean for all three new
Python files. No full 1,123-test framework rerun is claimed by this increment.

Both final containers passed **8/8 checks**: exact CLI startup version, scaffold,
incomplete Gate 1 rejection, absent successful checkpoint, resume after rejection,
spec preservation, existing F.2 greenfield/brownfield deployment regression
(**2 pytest cases per target**) and canonical Phase 1 context preparation.
Networking was disabled for this check. It is deterministic local evidence,
not live model or native discovery evidence.

Final local report: `20261027T194000Z-21af9245.json` under the runbook's ignored
`runs/` directory. See [machine-readable replay record](runtime-lab-record.json)
for the image/source identifiers and report hashes.

## Live attempt and blockers

The Claude request used the pinned model and reached Anthropic, which returned
HTTP 400, `is_error: true`, and **Credit balance is too low**. It reported
**USD 0 cost**, zero input/output tokens and no model-generated artifact. The
provider also returned `subtype: success`; the runner correctly rejected the
explicit error instead of treating this field as success. No reviewer request
followed the failed builder request. No retry was made after observing the credit
blocker. The final runner additionally classifies that known provider error as
BLOCKED; a regression test covers the observed event shape.

The preserved first live report is `20261027T193830Z-86e9e2b4.json` (overall FAIL,
Claude FAIL at the then-current adapter, Copilot BLOCKED). Historical records are
not rewritten to match later classification improvements. Claude's operational
blocker is insufficient API credit. Copilot has no `COPILOT_GITHUB_TOKEN` in this
session and no selected model; its final explicit prerequisite report is
`20261027T193957Z-99f6feff.json`, target status BLOCKED and overall nonzero exit.

At that cloud checkpoint the successful builder/reviewer path was unobserved.
The subsequent Ollama runs below exercise it locally. Distinct observed session IDs and observed model
pins are mandatory checks; imported runtime transcripts still cannot certify a
host. Container access and version checks alone do not complete F.3 or F.4.

## Failures retained and corrections

1. First Claude offline run (`20261027T193534Z-ead28176.json`): fixture copy
   preserved immutable image permissions and Git initialization failed. The
   disposable copy now becomes writable; source permissions stay unchanged.
   Added a focused regression test.
2. Copilot help initially failed to load a native addon from a non-executable
   tmpfs cache. Its isolated home now permits executable cache files. Host
   mounts remain absent; the system image remains read-only.
3. Copilot offline run (`20261027T193829Z-d834df16.json`): all scenario checks
   passed except exact-version parsing, which rejected the CLI's trailing full
   stop in `1.0.104.`. The parser now permits punctuation while rejecting
   different versions/prereleases; added a regression test.
4. Claude provider credit rejection described above. Preserved as an external
   prerequisite failure; no gate, permission or artifact check was relaxed.

## Replay and next action

The selected framework source is commit `b84792036f58eaf30c3f515c9b08d74eda59b186`
with actual selected bytes hashed as
`d965f366c973d1b1b389e4adc4a69e14e981c3a87ebe9091a6bda9853b434a30`.
The runner includes its own new uncommitted files explicitly, hashed in each
build record. Subsequent runs reject source, runner or lock drift until rebuilt.
Use the exact local image IDs for replay; apt/npm rebuilds are not guaranteed
byte-identical. Images/cache are retained, and every lab scenario container was
removed. No unrelated Docker container or volume was removed.

For the optional cloud profile: fund the Anthropic API account associated with the selected key,
provide a Copilot token with Copilot Requests permission to the invoking process,
and select an available exact Copilot model ID in the config. Never put credentials
in tracked files or chat. Then invoke `lab.py run` as documented. Successful live
smokes are the next checkpoint, followed by the remaining native/lifecycle/MCP/
adversarial/repetition matrix. F.5, VS Code and native operating-system checks
remain separate obligations.

## Native Ollama / Metal continuation

The user requested local inference on the Mac while preserving disposable CLI
environments. The existing native Ollama **0.40.11** service and installed
`qwen3.5:9b-q4_K_M` weights were reused. No model download, host CLI installation,
global Python/npm package installation or host CLI authentication/configuration
change was needed. Only `sdd-w30-qwen35:9b-64k` was added to Ollama; it shares the
base weight blobs. Its creation parameters and both manifest digests are pinned
in the local configuration. The runbook documents setup, repeat execution,
unloading/removing only this alias, and restoration prerequisites.

The native server log showed `ggml_metal_init: found device: Apple M2 Max` and
selection of that device. API `/api/ps` and `ollama ps` reported **100% GPU**,
**65,536 context tokens**, with approximately **7.5 GB** resident for this model.
The Mac has **64 GiB** unified memory. Docker's 2 GiB limit bounds each CLI, not
the separate native GPU process. Calls run sequentially. The initial base-model
probe was unloaded after use; no unrelated model or service was stopped.

Both official CLI packages route to `host.docker.internal:11434`: Claude uses
the Anthropic API and Copilot uses OpenAI chat completions with BYOK/offline
mode. No paid credentials are forwarded. CLI versions remain **2.1.311** and
**1.0.104**. Model defaults are temperature 0 and 8,192 output tokens; the final
runner also configures each CLI's context/output limits. API requests can
override sampling defaults; this is not a deterministic-output guarantee.

Preserved attempts and corrections:

1. `20261027T204227Z-ad503fbc.json`: both targets BLOCKED before model work because
   Ollama reused the shared-weight runner from the initial base-model probe and
   reported its base identity. Stopping that probe-owned runner allowed the lab
   alias to load with its pinned identity. No identity check was bypassed.
2. `20261027T204948Z-39f05c39.json`: Claude **22/22 PASS**; Copilot **21/22**.
   Copilot's artifact correctly said “Security review is still required before
   ship”, but the original lowercase-only word check rejected it. The corrected
   oracle is case-insensitive and requires the complete missing-review statement;
   a bare heading or a waived review does not satisfy it.
3. The same Copilot transcript exposed that echoed user prompts/reasoning/tool
   output were included in parsed reply text. The parser now accepts only
   `assistant.message` content for reviewer assertions, with an explicit
   prompt-echo false-positive regression test. Provider session/model IDs still
   come from observed events. Failed tool attempts are retained separately;
   that run attempted unavailable `bash` and creation of an existing file,
   recovered, and changed only the specification. A smoke PASS does not certify
   prompt obedience or every permission-denial route.
4. An independent code review found that existing alias parameters needed
   comparison with the recorded configuration, and Claude needed explicit
   context/output settings. Both are implemented, with focused regression cases.

The original full-suite container attempt had **1,114 passed, 9 failed, 20
skipped**: eight failures were missing parent-repository instruction/agent inputs
in the temporary test export, and one was missing `jq` in the regression image.
The corrected regression container includes those inputs plus `jq`, with
`pytest-asyncio 1.4.1` and `mcp 1.30.0`; its dependency snapshot is retained.
The standalone runner suite now has **22 passing tests**. No host packages were
installed. Final execution and regression identifiers are recorded in the
[machine-readable record](runtime-lab-record.json).

Final live run on the corrected adapters:

| Target | Checks | Builder | Independent reviewer | Observed tool failures |
|---|---:|---:|---:|---:|
| Claude Code 2.1.311 | 22/22 PASS | 64.039 s | 42.864 s | 0 |
| Copilot CLI 1.0.104 | 22/22 PASS | 122.134 s | 28.790 s | 0 |

Both runs observed the pinned model, changed only the intended specification,
preserved a read-only reviewer workspace, bound the review reply to the artifact
digest and received a deterministic Gate 4 rejection. The final offline report
`20261027T205139Z-053ec7b3.json` also passes **8/8 checks per CLI**. Timing values
are single observations, not performance guarantees. All scenario containers
were removed. The lab-owned model was stopped after testing; `ollama ps` was
empty. The native service, base weights, lab alias and replay images remain.

The corrected full Linux regression run passed **1,126 tests and 4 subtests**
in **269.04 seconds**, with **20 PowerShell cases skipped** because PowerShell
is unavailable in this container, and one existing pytest fixture deprecation
warning. No failures remain. The regression container was also removed. Its
image ID, complete extra dependency lock, log hash and outcome are retained in
the machine-readable record. This Linux result does not replace the earlier
macOS/PowerShell checkpoint or certify Windows parity.

Rebuildability means retaining the source revision **and these uncommitted lab
additions**, config, lock, Ollama version and the pinned model cache. A future
registry tag with changed bytes is rejected. Byte-exact container replay needs
saved images; apt/transitive dependency resolution remains a rebuild variable.
This continuation is within F.3/F.4: native discovery, successful full Gate 1–4
lifecycle, controlled MCP/adversarial cases, repeated negative scenarios, VS Code
and native operating-system certification still remain. F.5 is not closed.
