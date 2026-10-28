> **Portable reading copy.** Original experiment text; local links were remapped where supplied. Unavailable repository files are shown as source-only references, not working downloads. The [unchanged source](../original/README.md) and [original ZIP](../original-upload.zip) are preserved separately.

# W30 disposable CLI scenario lab

The reusable Phase F suite now contains **13 scenario families and 47 required
local execution cells**. `matrix` runs three independent copies of the 12-scenario
deterministic suite and the live Claude/Copilot cases below. `regression` runs the
complete framework test suite in an offline container. Tests, dependency locks,
configuration, native transcripts and per-attempt results are saved for reuse.

A local PASS covers this manifest. `overall_complete` and `certificate_issued`
remain false: VS Code, native macOS/Windows, complete production role/workflow
conformance and the five-PR pilot have explicit unresolved entries. Phase F stays
partial; Phase G is not implemented. See [execution evidence](runtime-lab.md).

Latest validation (October 28 Europe/Rome; October 27 UTC): **47/47 local cells
PASS**, with validated relay audit and cleanup. Full offline regression:
**1,195 passed, 111 subtests passed, 20 PowerShell skips**, one existing warning.
The [replay record](../original/runtime-lab-record.json) binds these
results to the exact tested images and source hashes; earlier failed attempts
remain saved.

October 28 F.5 follow-up: the [foundation rehearsal](foundation-report.md)
adds real managed legacy-renderer lifecycle tests and exact initial rollback/
idempotence checks. Five focused cases pass; the full regression now passes
**1,197 tests and 111 subtests**, with 20 PowerShell skips. The existing `regression`
command includes these cases; `matrix --scenario deterministic` retains its
twelve stable IDs and the frozen Sandbox bootstrap.

## Run the expanded suite

From `enterprise-sdd/`, using Python 3.11+ (substitute your interpreter path):

```sh
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py prepare-ollama --config _tests/harness_runtime/config.ollama.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py build
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py matrix --config _tests/harness_runtime/config.ollama.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py regression --target claude
```

A focused retry retains all required repetitions:

```sh
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py matrix --config _tests/harness_runtime/config.ollama.json --target copilot --scenario denied-write
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py matrix --scenario deterministic --target claude
```

Repeat `--scenario` to select multiple families. Unknown or empty selections are
errors. A focused PASS sets `selected_complete=true` but cannot claim the full
matrix passed. No skip, missing result, duplicate cell or absent terminal CLI
result counts as a successful execution.

scenarios.json (`scenarios.json`; source-only reference, not supplied) is the required-cell manifest:

| Family | Repetitions | Independent oracle |
|---|---:|---|
| `deterministic` | 3 total | 12 structural scenario IDs, 14 selected pytest nodes per copy; real CLI/gate exits, checkpoints, immutable artifacts and strict JUnit collection |
| `requirements-review` | 1 per CLI | Actual draft edits, distinct observed reviewer session, terminal review bound to artifact digest, real missing-review Gate 4 rejection |
| `native-agent`, `native-skill`, `native-instructions` | 1 each per CLI | Hidden receipt in native-loaded content; no receipt in the request; native skill inventory where applicable |
| `optional-present` | 1 per CLI | Synthetic installed optional skill discovered and activated |
| `optional-absent` | 3 per CLI | Skill absent from native inventory, unavailable response and no withheld receipt |
| `denied-write`, `denied-shell` | 3 each per CLI | Native policy denial matched to the intended tool and arguments; protected hashes unchanged |
| `injection` | 3 per CLI | Successful read includes the malicious payload; legitimate code returned without injected claims; protected hashes unchanged |
| `mcp-allowed` | 1 per CLI | Exactly one audited synthetic stdio tool call and hidden server receipt |
| `mcp-denied` | 3 per CLI | Server/tool discovery, native permission denial and zero server-side tool calls |
| `session-resume` | 1 per CLI | Interrupt after response bytes; resume the actual session ID; recover earlier random context; unchanged project |

The deterministic API is `run_suite(root: Path, selection=None)` in
deterministic.py (`deterministic.py`; source-only reference, not supplied), with `SCENARIO_IDS` and `SCENARIO_MAP` for
stable selections. Its twelve IDs cover successful Gates 1–4, failed-gate resume,
missing/stale review evidence, greenfield/brownfield upgrade and rollback,
optional packages present/absent, unverified profiles, injection, ownership and
MCP validation. It copies the framework into a writable temporary directory and
retains the real Sandbox venv/pip/installed-CLI dispatch. Only the wheelhouse
lookup is replaced with the baked local wheels. No network or model is used.
Unselected structural IDs remain in `coverage.missing`; skipped, uncollected,
duplicate or uncaptured tests fail closed. Stale review means the existing eval
hash verifier, not Phase G review-freshness enforcement.

## Matrix isolation and rebuild inputs

`matrix` accepts only the pinned Ollama profile. Every live attempt receives a
fresh container and CLI home on a Docker **internal** network. A separate relay
has access to native Ollama and permits only the pinned model on Messages,
Messages token-count and Chat Completions endpoints (including Claude's exact
`?beta=true` variant). Workers have no published ports or host/volume mounts.
Each live attempt checks that direct public TCP access and direct host-Ollama
access fail, the relay responds, and model-management requests are rejected.
This is a constrained local lab, not a general network-exfiltration certificate.

```text
CLI workers on internal network -> allowlisted relay -> native Ollama -> Metal
```

Relay logs contain route/model/settings, not prompts or response content. Missing
or invalid audit logs fail the aggregate verdict. A client disconnect during
response delivery is allowed only within the number of completed intentional
interruption tests; upstream transport failures still fail. Every container and
the exact UUID-owned relay/network are removed in `finally`. An interrupted
batch retains completed reports and leaves unfinished coverage missing.

The image includes the complete test tree, support scripts, audit allowlist,
placeholder `.env.example`, selected parent framework references, and normalized
executable modes. matrix-requirements.lock (`matrix-requirements.lock`; source-only reference, not supplied) adds pinned
MCP/async-test/build dependencies to the base Python lock. The build bakes all
wheels plus the actual SDD CLI wheel into `/opt/wheelhouse`. Runtime pip installs
use `PIP_NO_INDEX=1` and touch only disposable venvs. No host pip/npm installation
or host Claude/Copilot configuration change is required.

Live workers retain the 2 GiB/2 CPU limit. Offline deterministic/regression
containers use 4 GiB memory and 2 GiB per tmpfs; their temporary filesystems are
executable so the real installed CLI launcher can run. Native Ollama GPU memory
is outside these container limits. Build records include source bytes, normalized
file modes, recipe hashes, exact image IDs and resolved npm locks. Source, mode,
runner or lock drift requires rebuilding. A newer dependency refresh must review
both Python locks. Byte-identical rebuild limitations are documented below.

Reports are written immediately under `runs/matrix-<UTC>-<id>/`: one JSON per
cell, `summary.json`, and `relay.jsonl`. Failed attempts are retained when a later
run succeeds. Summaries distinguish selected coverage, the full local matrix and
unresolved external requirements. The run directories and images are local and
ignored by Git; preserve them and the uncommitted implementation changes for
future replay. The original `run` smoke remains available as described below.

## Native Ollama on Apple Silicon

Historical smoke checkpoint, October 27, 2026: **Claude Code and Copilot CLI each pass all 22 live
smoke checks** using this local model. Both offline preflights pass 8/8 checks;
22 runner unit tests pass. See [execution results and limitations](runtime-lab.md).

Use config.ollama.json (`config.ollama.json`; source-only reference, not supplied) for local inference. It pins **Ollama
0.40.11**, the installed **Qwen 3.5 9B Q4_K_M** base model's full manifest digest,
and a separate `sdd-w30-qwen35:9b-64k` alias. The alias reuses the weights and sets
65,536 context tokens and defaults of temperature 0 and 8,192 output tokens.
Both CLIs use this same model. The runner also sets Claude's maximum context and
output environment variables and Copilot's prompt/output limits. API request
parameters can override model defaults; temperature 0 is not an enforced request
policy. Effective sampling/output is not guaranteed identical between CLIs.

```text
Claude Code container  ── Anthropic messages API ─┐
                                                ├─ host.docker.internal:11434
Copilot CLI container  ── OpenAI completions API ─┘             │
                                                    native Ollama → Metal GPU
```

The Mac's existing Ollama service stays bound to loopback. Docker Desktop can
reach it through `host.docker.internal`; no service restart or public bind is
needed on the recorded setup. Ollama runs natively because a Linux Docker
container does not provide this Mac's Metal backend. The checked host is an
Apple M2 Max with 64 GiB RAM. Loaded-model evidence includes context, manifest
digest and GPU-resident bytes before and after each live target.

| Container CLI | Per-process routing | Authentication |
|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL=http://host.docker.internal:11434`; main/small/default models all use the lab alias | Dummy local `ANTHROPIC_AUTH_TOKEN=ollama`; empty `ANTHROPIC_API_KEY` |
| Copilot CLI | `COPILOT_PROVIDER_BASE_URL=http://host.docker.internal:11434/v1`; `openai` provider; explicit wire/model IDs | No token; `COPILOT_OFFLINE=true` |

Local runs do not read host cloud credentials. The worker removes inherited
provider credentials, alternate routes and proxy settings before starting a CLI.
No host Claude/Copilot configuration is edited. Offline Copilot mode means local
BYOK inference without GitHub services; it still needs networking to Ollama.
This is distinct from the lab's `check`, which disables all container networking.
The original `run` command uses unrestricted bridge egress. Use `matrix` for the
internal-network probes described above.

### Rebuild and run from scratch

Prerequisites on another Mac: Apple Silicon, native Ollama **0.40.11** running,
Docker Desktop with Linux ARM64 containers, Git and Python 3.11+. Preserve this
working tree's lab additions/patch as well as the source commit: the current lab
files are not yet committed to the remote branch. A checkout of that commit
alone does not contain them. No host Claude, Copilot, npm or pip installation is
needed. Start Docker/Ollama normally if they are not running.

On a fresh Ollama installation, install the base weights once:

```sh
ollama pull qwen3.5:9b-q4_K_M
```

Then, from `enterprise-sdd/` (substitute your Python 3.11+ path):

```sh
/opt/homebrew/bin/python3.13 _tests/test_harness_runtime.py -v
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py prepare-ollama --config _tests/harness_runtime/config.ollama.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py build --config _tests/harness_runtime/config.ollama.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py check --config _tests/harness_runtime/config.ollama.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py run --config _tests/harness_runtime/config.ollama.json
```

`prepare-ollama` checks the server version and installed base digest, creates only
the missing lab alias, then verifies the alias digest. It does not pull weights,
overwrite a conflicting alias or change server settings. It is safe to repeat.
A tag pulled in the future may have different bytes: that causes an explicit
failure, not a silent model upgrade. Restore the recorded model cache or review
and record a new configuration before adopting different bytes.

`run` warms the selected model for ten minutes and requires the recorded context
and fully GPU-resident weights. Ollama may reuse a runner for identical weights
and report the previously loaded alias. If the identity check stops on that
condition, inspect `ollama ps`; stop only a model you own and are finished using
before retrying. The runner does not unload someone else's model automatically.
CLI calls can refresh Ollama's normal keep-alive interval. To release this lab's
GPU memory after use, run `ollama stop sdd-w30-qwen35:9b-64k`.

The alias is the only persistent model addition and shares existing weight
blobs. To remove it deliberately, use `ollama rm sdd-w30-qwen35:9b-64k`; retain
the base model. GPU/unified-memory use belongs to the native Ollama process and
is **outside Docker's 2 GiB limit**. CLI requests run sequentially. The 64k
configuration is for this bounded smoke; GitHub recommends 128k for general
Copilot use, which would require a separately recorded configuration.

For exact restoration, retain both model manifests and all blobs they reference
from Ollama's model cache, the Ollama installer/binary version, the source patch,
config/lock and image archives. The base tag alone is not an immutable backup.
The recipe can rebuild fresh containers without cached images; byte-identical
image reconstruction has the limitations described below.

## Recorded configuration

- config.json (`config.json`; source-only reference, not supplied): ARM64 Linux, 2 CPUs, 2 GiB memory, 128 processes,
  300 seconds per model invocation, two invocations per target (builder/reviewer),
  USD 2 maximum per Claude invocation. Copilot has no monetary ceiling in this
  runner: configure account-side billing limits. Timeout is not a spending cap.
  Claude's model is `claude-sonnet-5-5`, observed in the authenticated model
  catalog on October 27. Copilot's model remains null until access is established.
- versions.lock.json (`versions.lock.json`; source-only reference, not supplied): resolved latest stable npm releases,
  package integrity values, base image digest and exact Python dependency versions.
  October 27, 2026: Claude Code **2.1.311**, Copilot CLI **1.0.104**.
- `builds/<target>.json`: immutable local image ID, git revision, actual selected
  source hashes (including local edits), runner/recipe hashes, and complete lock.
- `builds/<target>.npm-lock.json`: actual resolved npm dependency tree.
- `runs/<timestamp>-<unique-id>.json`: effective config, source/build provenance,
  exit codes, checks, transcript hashes, provider session/model observations and
  sanitized outputs. Every invocation creates a new report; failures are retained.

Builds and runs are gitignored. The config, lock, recipe, runner and this guide
are intended for version control. Keep a reviewed execution summary in
`_plan/evidence/W30` (`../../_plan/evidence/W30`; source-only reference, not supplied).

## Original smoke isolation boundary (`run`)

The host orchestrator uses Python 3.11+ **standard library only** and Docker.
It requires no host pip/npm packages, global CLI upgrades, shell startup changes
or edits to the host CLI configuration. Docker Desktop must be running.

Each attempt creates a new non-root container with a read-only root filesystem,
all Linux capabilities dropped, `no-new-privileges`, resource limits and writable
tmpfs directories for the synthetic project, home and temporary state. There are
executable permissions on the isolated home tmpfs because Copilot unpacks its
native runtime there; this grants no host filesystem access. There are
no bind mounts, volumes, Docker socket mounts or privileged containers. The local
check has networking disabled. Live runs use Docker bridge networking for provider
access; **network egress is not allowlisted**, so this first increment must use
trusted synthetic prompts. Network-exfiltration adversarial cases require an
egress-controlled follow-up before being considered covered.

Selected tracked framework inputs and narrowly selected parent instructions,
agents and the evolution reference are copied into the image; the complete parent
repository and its Git metadata are not copied. The lab explicitly includes its
uncommitted runner/tests and existing F.2 fixture files. New untracked framework implementation files are
not included automatically: review/stage those before building. Symlinks and
secret-like filenames in the selected inputs are rejected. This is not a general
content secret scanner; review the source manifest before live use.

Credentials are read from named host environment variables, sent to the worker
over stdin, and provided only to the corresponding CLI child process. They are
never Docker environment entries, command arguments, build arguments or image
layers. An agent could access a credential available inside its own environment;
use dedicated restricted credentials and synthetic projects. Do not paste tokens
into chat, commit an env file, or copy the host home/keychain into a container.

The worker gives the builder file tools and the reviewer read tools only; shell,
fetch and MCP tools are excluded. Each role uses a fresh CLI configuration
directory; no continuation/resume flags are used. Provider-returned session IDs
must be present and distinct. That supports this smoke's context separation;
it is not certification of every native reviewer route. The stock native profiles
remain unmodified and unverified.

## Repeat the recorded setup

Run these commands from the framework root (`enterprise-sdd/`) using a Python
3.11+ interpreter. On the original Mac the configured command was
`/opt/homebrew/bin/python3.13`; substitute your supported interpreter elsewhere.

```sh
/opt/homebrew/bin/python3.13 _tests/test_harness_runtime.py -v
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py build
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py check
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py run
```

`build` uses the existing version lock. `check` runs without credentials or model
calls and with container networking disabled. `run` executes both live targets
when configured; missing credentials/models produce BLOCKED records and a nonzero
overall exit. Use `--target claude` or `--target copilot` for one target. An overall
PASS requires every selected target to pass. These are on-demand invocations;
nothing is scheduled or left running in the background.

The workspace also has a `W30: Build isolated CLI lab` VS Code task. Its initial
creation timed out, but the task was subsequently created and successfully ran
both image builds. The image recipe is shared by the local and cloud profiles.

### Optional cloud profile: models and authentication

1. Set each target's `model` in config.json (`config.json`; source-only reference, not supplied) to an exact model ID
   available to that provider/account. Null intentionally blocks paid execution.
   Avoid `auto`, `sonnet`, `latest` or other moving aliases. CLI version and model
   are separate pins. Record a provider routing alias as a limitation if an exact
   underlying model revision is unavailable; observed response IDs are retained.
2. Make `ANTHROPIC_API_KEY` available to the invoking process for Claude.
3. Make `COPILOT_GITHUB_TOKEN` available for Copilot. The account needs Copilot
   access; fine-grained tokens need the account-level **Copilot Requests** permission.
   This implementation uses token authentication, not mounted existing OAuth state.
4. Run `run`. Check both the overall status and individual checks in the report.

Use a secret manager or hidden terminal input to set credentials. Never place
literal secrets in shell commands stored in history. The runner does not perform
interactive login or change existing host authentication. A rejected token,
unsupported model, missing JSON event, or unavailable CLI flag cannot become PASS.

### Refresh to a newer release deliberately

```sh
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py lock --lock _tests/harness_runtime/versions-next.lock.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py build --lock _tests/harness_runtime/versions-next.lock.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py check --lock _tests/harness_runtime/versions-next.lock.json
/opt/homebrew/bin/python3.13 _tests/harness_runtime/lab.py run --lock _tests/harness_runtime/versions-next.lock.json
```

An existing lock is never overwritten. Review the new lock and results before
adopting it. Automatic CLI updates are disabled inside the images. Runs refuse
source/runner/lock drift relative to the current build record.

### Exact replay versus rebuilding

`run`/`check` use the recorded immutable **image ID**, never an implicitly refreshed
tag. They retain the actual dependency versions. Preserve the image with Docker's
`image save` to an archive and restore it using `image load` if you need byte-exact
replay on another ARM64 Docker host. Save the matching build records, source
revision/patch, config and lock alongside the archive.

Rebuilding uses pinned base/CLI/Python versions and checks the top-level CLI npm
integrity. Apt repositories and transitive npm dependency resolution can change;
**a rebuild is not guaranteed byte-identical**. Its new image ID and resolved npm
lock make that difference visible. Exact reproducibility also does not imply
identical model output: provider behavior and sampling may vary.

## Original smoke scenario and independent oracles (`run`)

| Step | Oracle | Model involved? |
|---|---|---|
| CLI startup | Exit code and locked CLI version | No |
| New feature scaffold | Real `sdd new` exit and unique feature directory | No |
| Incomplete Gate 1 | Nonzero gate exit and no successful checkpoint | No |
| Resume after denial | Zero exit, next-gate output, unchanged specification | No |
| Greenfield/brownfield deployment | Existing F.2 publisher/recovery/frozen/rollback tests | No |
| Draft requirements | Actual spec changed; no other project file changed; US/AC assertions via existing eval utility | Builder |
| Independent draft review | Distinct observed session IDs, unchanged files, response bound to artifact digest | Reviewer |
| Missing review at ship | Real Gate 4 rejects; no successful checkpoint | No |

The smoke explicitly prepares the canonical `sdd-phase-loader --phase 1` context. It does not
silently mark profiles verified to unlock native rendering. Review text is checked
only for this draft review; actual ship denial comes from the deterministic gate.
The specification remains insufficient for shipping by design. Legacy imported
runtime eval transcripts remain BLOCKED by the existing eval framework.

## Remaining coverage

The matrix combines structural lifecycle tests with live synthetic discovery and
permission probes. It does not claim every canonical production role/workflow or
every optional package has been exercised end-to-end in a native host. Complete
production projection conformance, native macOS/Windows, VS Code Copilot and the
five-PR pilot remain explicit unresolved requirements. Capability profiles stay
unverified. Phase G/H cases cannot certify unimplemented features, and Linux CLI
results cannot close other targets. See the [execution record](runtime-lab.md).

## Reports, failures and cleanup

Exit 0 means all selected checks passed; exit 1 means a failed/blocked run; exit 2
means setup/configuration failed. Timeouts terminate the CLI process group, with
an outer Docker watchdog as backup. The orchestrator removes only its exact
UUID-named container in `finally`; tmpfs state disappears with it. Images and build
cache are retained for replay. There is no global Docker prune or host cleanup.

If the host process is forcibly killed, inspect Docker containers labeled
`sdd.lab=W30`, confirm the exact UUID, and remove that container explicitly. A
cleanup failure is included in the report with its precise name. Do not remove
unrelated containers or volumes. Sanitized transcripts may still contain provider
account details not recognized by redaction: keep run reports local and review
them before sharing. Known supplied credentials and common token formats are
redacted before host persistence; raw CLI config/home state is never exported.

## Official references checked October 27, 2026

- [Docker internal networks](https://docs.docker.com/reference/cli/docker/network/create/)
- [Copilot native skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
- [Claude container support](https://code.claude.com/docs/en/devcontainer)
- [Claude CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Claude context and output environment variables](https://code.claude.com/docs/en/env-vars)
- [Copilot installation and token authentication](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli)
- [Copilot CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)
- [Copilot configuration storage](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
- [Copilot local models, BYOK and offline mode](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models)
- [Claude Code with Ollama](https://docs.ollama.com/integrations/claude-code)
- [Ollama derived-model creation API](https://docs.ollama.com/api/create)

Installed CLI help and actual execution take precedence over assumed compatibility
with newer documentation. The first authenticated attempt may expose an adapter
gap; preserve that failed attempt and fix the adapter instead of weakening checks.
