> **Portable reading copy.** Original experiment text; local links were remapped where supplied. Unavailable repository files are shown as source-only references, not working downloads. The [unchanged source](../original/testing-an-sdd-framework-autonomously.md) and [original ZIP](../original-upload.zip) are preserved separately.

# How to Test an SDD Framework Autonomously on Your Mac

*A practical lab with Claude Code, GitHub Copilot CLI, native Ollama on Metal, disposable containers, and evidence you can replay.*

An agent says it respected your project rules. It says it loaded the right skill, completed the review, and left protected files untouched. How do you verify those statements?

That is the central testing problem for a spec-driven development framework. The framework coordinates specifications, agents, quality gates, tools, and generated configuration. A successful conversation can conceal a missing review, a bypassed gate, or an instruction that the CLI never loaded.

The Enterprise SDD harness lab makes those behaviors observable. Its recorded local matrix passed **47 execution cells** across structural tests and live Claude Code and GitHub Copilot CLI scenarios. A subsequent framework regression passed **1,197 tests and 111 subtests**, with explicitly reported platform skips.

This article explains how that lab works, how to run it locally, and how to preserve enough evidence to repeat the experiment. The configuration and results below are a dated baseline from **October 27–28, 2026**. The commands assume a checkout containing the companion lab implementation (`../enterprise-sdd/_tests/harness_runtime/`; source-only reference, not supplied); they are repository commands, not commands supplied by either CLI vendor.

## Start with an observable contract

An SDD framework maintains relationships between requirements, acceptance criteria, tests, implementation tasks, and code. Its gates decide when work can proceed. Its adapters translate canonical agents and instructions into files that individual coding tools understand.

Each of those responsibilities needs an observable contract. For example:

| Framework promise | Evidence the test must collect |
|---|---|
| A failed gate blocks progress | Actual CLI exit status, checkpoint, and unchanged downstream artifacts |
| A review belongs to the current artifact | Separate reviewer session and the digest of the reviewed bytes |
| The CLI loaded a native skill | A fresh hidden receipt available only inside that skill, plus native discovery evidence where available |
| A prohibited write was denied | A native permission event matching the tool and arguments, plus unchanged protected-file hashes |
| Rollback preserves existing work | Restored original content and ownership records; unrelated files remain unchanged |

The test runner evaluates these conditions independently of the model's account of what happened. A missing result fails coverage. A skipped required scenario cannot become a pass.

Keep three scopes explicit: deterministic framework behavior, live CLI behavior, and release acceptance. A passing local experiment supports the first two within its declared coverage. Wider compatibility and pilot acceptance require their own evidence.

## Put the CLIs in containers and inference on Metal

The lab uses this topology:

```text
Mac: Python orchestrator
    │
    ├── offline test containers: network disabled
    │
    └── live CLI containers: Docker internal network
               │
               ▼
         allowlisted relay at http://llm:11434
               │
               ▼
         host.docker.internal:11434
               │
               ▼
         native Ollama → local model → Metal GPU
```

Claude Code and Copilot CLI run as Linux ARM64 programs in separate images. Ollama runs natively on macOS, using the Mac's Metal backend. This arrangement keeps CLI dependencies and project mutations inside disposable environments while retaining native GPU inference.

Each live attempt receives a fresh container, project, and CLI home. Workers run as a non-root user with a read-only root filesystem, dropped Linux capabilities, and limits of two CPUs, 2 GiB of memory, and 128 processes. Writable temporary filesystems hold the project and session state. Workers receive no host directory mounts, Docker socket, or published ports.

Offline structural and regression containers have larger limits: 4 GiB of memory and 2 GiB per temporary filesystem. Those filesystems permit execution because the tests create virtual environments and run the real installed SDD launcher.

The network boundary matters just as much. Docker's normal bridge provides external connectivity; an internal network removes that route for workers attached only to it. The relay connects to both networks and exposes a restricted inference interface. See Docker's [internal network documentation](https://docs.docker.com/compose/how-tos/networking/#internal-networks).

The relay accepts only the pinned model and specific inference routes. It rejects model-management requests. Every live cell probes that direct public TCP access and direct access to host Ollama fail, while the relay remains reachable. These are concrete isolation checks with bounded coverage, rather than a comprehensive security certification.

Native Ollama's GPU and unified-memory consumption remain outside Docker's memory limits. Container isolation does not make inference resource usage disappear.

## 1. Establish the recorded baseline

The tested host was an Apple M2 Max with 64 GiB of memory. That is the observed configuration, not a measured minimum requirement.

Provision these host prerequisites through their normal installation procedures:

- Docker Desktop, running Linux ARM64 containers.
- Python 3.11 or later and Git.
- Native Ollama, running locally, with the version required by the chosen profile.
- The framework checkout, including the lab files and any uncommitted implementation changes needed for replay.

The host Python orchestrator uses the standard library. CLI packages and test dependencies are installed inside the images. Host Claude/Copilot installations, provider credentials, and global npm or pip installations are unnecessary for this profile.

| Component | Recorded value |
|---|---|
| Claude Code | `2.1.311` |
| GitHub Copilot CLI | `1.0.104` |
| Ollama | `0.40.11` |
| Base model | `qwen3.5:9b-q4_K_M` |
| Lab model alias | `sdd-w30-qwen35:9b-64k` |
| Context / output defaults | 65,536 / 8,192 tokens |
| Temperature default | `0` |

Exact CLI versions, package integrity values, and the Node base-image digest live in versions.lock.json (`../enterprise-sdd/_tests/harness_runtime/versions.lock.json`; source-only reference, not supplied). Ollama versions, model digests, and resource settings live in config.ollama.json (`../enterprise-sdd/_tests/harness_runtime/config.ollama.json`; source-only reference, not supplied).

For reproduction, retain those pins. Resolving “latest” again creates a new experiment that needs a new build and validation record.

From the repository root, enter the framework directory:

```sh
cd enterprise-sdd
```

All remaining shell examples run from this directory. Substitute the path to your Python 3.11+ interpreter if `python3` selects an older version.

## 2. Prepare a dedicated local model

On a fresh installation, download the base weights once:

```sh
ollama pull qwen3.5:9b-q4_K_M
```

Then prepare the lab alias:

```sh
python3 _tests/harness_runtime/lab.py prepare-ollama \
  --config _tests/harness_runtime/config.ollama.json
```

This command checks the server version and the installed base-model digest, creates the lab alias if it is missing, and verifies the resulting alias and parameters. It does not overwrite a conflicting alias or change the Ollama service configuration. The alias shares the base weights.

A model tag can resolve to different bytes in the future. If the digest differs, restore the preserved model cache or deliberately adopt and record a new configuration. A mismatched model should stop the experiment.

The recorded setup kept Ollama bound to loopback. Docker Desktop reached it through `host.docker.internal`; no public bind was needed. Treat that as a verified property of this setup, and verify connectivity on a different host before changing service exposure.

The 64k profile supports these bounded scenarios. GitHub recommends at least 128k context for general Copilot CLI use, and requires streaming and tool calling. Larger workloads therefore need a separately validated profile. See GitHub's [model requirements](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models#model-requirements).

Temperature zero is a model default, and requests can override defaults. The lab does not promise identical sampling between clients or identical model output on repeated runs.

## 3. Install both CLIs inside the lab images

Build the two images:

```sh
python3 _tests/harness_runtime/lab.py build \
  --config _tests/harness_runtime/config.ollama.json
```

The builder reads the lock, installs the exact official npm package for each target, and checks its installed version and integrity. The relevant installation step in the Dockerfile (`../enterprise-sdd/_tests/harness_runtime/Dockerfile`; source-only reference, not supplied) is:

```dockerfile
ARG CLI_PACKAGE
ARG CLI_VERSION
RUN npm install --prefix /opt/runtime --save-exact "${CLI_PACKAGE}@${CLI_VERSION}" \
    && npm cache clean --force
```

The builder supplies `@anthropic-ai/claude-code` or `@github/copilot` and the corresponding pinned version. Automatic CLI updates are disabled in the lab.

The image also contains the selected framework source, complete test tree, support scripts, and a local wheelhouse. The wheelhouse includes the actual SDD CLI wheel. During testing, `PIP_NO_INDEX=1` forces installation from those baked wheels into disposable virtual environments. The existing production command dispatch and Sandbox lifecycle remain under test.

Image construction and the initial model download require network access. Offline regression execution requires neither a package index nor a model service.

### How each CLI reaches the local model

The worker (`../enterprise-sdd/_tests/harness_runtime/worker.py`; source-only reference, not supplied) configures child processes directly. These are the effective routing values during a live matrix cell:

| Setting | Claude Code | Copilot CLI |
|---|---|---|
| Base URL | `ANTHROPIC_BASE_URL=http://llm:11434` | `COPILOT_PROVIDER_BASE_URL=http://llm:11434/v1` |
| Local authentication | `ANTHROPIC_AUTH_TOKEN=ollama`, empty `ANTHROPIC_API_KEY` | No provider API key |
| Model | `ANTHROPIC_MODEL=sdd-w30-qwen35:9b-64k` | `COPILOT_MODEL=sdd-w30-qwen35:9b-64k` |
| Additional routing | Small/default model aliases use the same model | Provider `openai`, wire API `completions`, explicit wire/model IDs |
| Token limits | Context 65,536; output 8,192 | Prompt 57,344; output 8,192 |
| Background traffic controls | Nonessential traffic and updater disabled | `COPILOT_OFFLINE=true`, updater disabled |

The matrix replaces the profile's host-facing URL with the relay address before invoking the worker. Ollama documents the [Anthropic-compatible connection used by Claude Code](https://docs.ollama.com/integrations/claude-code); GitHub documents [custom providers and offline mode](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models).

The runner removes inherited provider credentials, alternate provider routes, and proxy settings. It uses isolated CLI configuration directories. There is no need to put these values into your shell startup files or change your everyday coding environment.

Copilot's offline mode still permits requests to its configured provider. Here, the provider is local and the container network supplies the additional boundary. Native tool permissions remain enabled: scenarios receive narrowly scoped rules so permission-denial behavior can itself be tested.

## 4. Prove the framework works offline

Start with preflight:

```sh
python3 _tests/harness_runtime/lab.py check \
  --config _tests/harness_runtime/config.ollama.json
```

The recorded preflight passed eight checks for each CLI. Then exercise the structural matrix and full regression:

```sh
python3 _tests/harness_runtime/lab.py matrix \
  --config _tests/harness_runtime/config.ollama.json \
  --scenario deterministic --target claude

python3 _tests/harness_runtime/lab.py regression \
  --config _tests/harness_runtime/config.ollama.json \
  --target claude
```

In these commands, `claude` selects the image. Neither command invokes a model.

The deterministic runner (`../enterprise-sdd/_tests/harness_runtime/deterministic.py`; source-only reference, not supplied) covers twelve stable scenario IDs through fourteen selected pytest nodes. It exercises gate success and failure/resume, missing and stale review evidence, greenfield and brownfield deployment, optional packages, profile rejection, injection, ownership, and MCP validation. The matrix runs this suite in three independent containers.

Its collection checks are deliberately strict. Missing, skipped, duplicate, or uncaptured required tests fail coverage. Stale-review checks use the existing artifact-hash verifier; they do not claim that planned future review-freshness features already exist.

Run the full regression as well: later renderer and rollback tests can live outside the stable twelve-ID selection.

## 5. Run the complete local scenario matrix

With Ollama prepared and the images built:

```sh
python3 _tests/harness_runtime/lab.py matrix \
  --config _tests/harness_runtime/config.ollama.json
```

The scenario manifest (`../enterprise-sdd/_tests/harness_runtime/scenarios.json`; source-only reference, not supplied) expands thirteen families into **47 cells**: three offline suite executions, twenty-two live Claude cells, and twenty-two live Copilot cells.

| Family | Executions | What determines success |
|---|---:|---|
| Deterministic framework suite | 3 total | Real exits, checkpoints, artifacts, and complete collection |
| Requirements and review | 1 per CLI | Actual draft edit, separate observed reviewer session, digest binding, missing-review gate rejection |
| Native agent, skill, instructions | 1 each per CLI | Hidden receipts from content loaded through native mechanisms |
| Optional skill present / absent | 1 / 3 per CLI | Discovery and activation, or verified absence without the withheld receipt |
| Denied write / denied shell | 3 each per CLI | Operation-specific native denial and unchanged protected state |
| Prompt injection | 3 per CLI | Successful read of the malicious input, legitimate result, protected files unchanged |
| MCP allowed / denied | 1 / 3 per CLI | Exactly one audited tool call, or native denial with zero server-side calls |
| Interrupted session resume | 1 per CLI | Real process interruption and recovery of earlier random context through the actual session ID |

The strongest oracles combine independent observations. A tool error alone cannot prove native permission enforcement. For MCP denial, the client must discover the server and report the relevant permission refusal, while the server audit records zero tool calls.

Likewise, an injection test must prove the agent encountered the malicious text. Otherwise, an unchanged project could simply mean the document was never read.

Critical negative cases use three fresh environments. This helps expose state contamination and some variable behavior; it is too small a sample to establish a statistical reliability guarantee.

Use `matrix` for this network boundary. The older `run` smoke command uses ordinary bridge egress and does not provide the same isolation checks.

## 6. Give autonomous repair a bounded loop

The suite automates execution, observation, reporting, and cleanup. An engineering agent can operate it and repair failures, provided the repair loop preserves the test contract:

1. Read the failed cell's command, transcript, assertions, and protected-state differences.
2. Identify whether the cause belongs to the framework, fixture, CLI integration, or lab infrastructure.
3. Apply a narrow fix in the source checkout, preserving the acceptance condition.
4. Rebuild images when source, runner, modes, or locks change.
5. Rerun the failed family, retaining its required repetitions.
6. Run the relevant regression and full matrix before making a new full-coverage claim.

For example:

```sh
python3 _tests/harness_runtime/lab.py build \
  --config _tests/harness_runtime/config.ollama.json

python3 _tests/harness_runtime/lab.py matrix \
  --config _tests/harness_runtime/config.ollama.json \
  --target copilot --scenario denied-write
```

A focused pass establishes selected coverage only. Failed attempts remain saved. Do not retry until green and discard the failures, or accept a model's proposed change to the success criteria without reviewing the underlying contract.

The existing runner executes finite, on-demand batches. It does not implement an unattended repair scheduler. For a surrounding agent or CI controller, set an explicit attempt/time budget and retain an unresolved failure when that budget expires. Keep image inputs stable during a batch.

### Three failures that improved the lab

**The temporary filesystem prevented execution.** A restrictive mount blocked the real virtual-environment launcher. The fix allowed execution on the disposable test filesystems while retaining installed-CLI dispatch.

**Claude used an additional exact API route.** Its Messages request included `?beta=true`, which the relay rejected. The fix added that observed route to the allowlist while keeping arbitrary routes and model-management operations blocked.

**All cells passed, but the aggregate failed.** Intentional session interruption produced client disconnects while the relay was delivering responses. The aggregate initially classified those as transport failures. The fix distinguished downstream disconnects and bounded their allowance by completed interruption cases. Upstream failures continued to fail the run.

These failures are documented in the [execution evidence](runtime-lab.md). They illustrate why the evidence collector and its aggregate verdict need testing too.

## 7. Preserve the experiment, including its limits

Each matrix writes a unique directory under the lab's runs folder (`../enterprise-sdd/_tests/harness_runtime/runs/`; source-only reference, not supplied), containing one report per cell, a summary, and a relay audit. Reports include commands, exit codes, timeouts, transcripts, artifact hashes, observed sessions, and model evidence. Live cells check the pinned loaded model, context, and GPU residency before and after execution.

A successful full local summary contains these distinct claims:

```json
{
  "status": "PASS",
  "selected_complete": true,
  "local_matrix_complete": true,
  "overall_complete": false,
  "certificate_issued": false
}
```

Retain the full report, including unresolved requirements and cleanup results. Relay audit logs omit prompt content, but CLI transcripts can contain fixture or project content; review them before publication.

Rebuilding the recipe and restoring the exact tested binaries are different operations. The builder records source hashes, executable modes, image IDs, recipe hashes, and resolved npm dependency trees. Nevertheless, package repositories and transitive dependencies can change. Version pins alone do not guarantee byte-identical image reconstruction.

For durable replay, preserve:

- The source revision **and all required local changes**, including untracked lab files. A commit hash alone is insufficient for this recorded working tree.
- The configuration (`../enterprise-sdd/_tests/harness_runtime/config.ollama.json`; source-only reference, not supplied), version lock (`../enterprise-sdd/_tests/harness_runtime/versions.lock.json`; source-only reference, not supplied), both Python dependency locks, build records, and resolved npm locks.
- The exact tested container images as archives.
- The Ollama binary/version and both model manifests with every referenced weight blob.
- The complete successful and failed reports, plus the [replay record](../original/runtime-lab-record.json) linking evidence to tested inputs.

For example, after a build, archive the images named by the current build records:

```sh
python3 - <<'PY'
import json
import subprocess
import tempfile
from pathlib import Path

builds = Path("_tests/harness_runtime/builds")
archive_dir = Path(tempfile.mkdtemp(prefix="image-archive-", dir=builds))
images = [
    json.loads((builds / f"{target}.json").read_text())["image_id"]
    for target in ("claude", "copilot")
]
archive = archive_dir / "cli-images.tar"
subprocess.run(["docker", "image", "save", "--output", str(archive), *images], check=True)
print(archive)
PY
```

Retain those build records alongside the archive; historical test reports may refer to earlier images. Docker can restore an archive with `docker image load --input PATH_TO_ARCHIVE`. Restoring images also requires restoring their matching source/configuration and build records for the runner's drift checks. Move the replay bundle into durable storage: build and run outputs are ignored by Git.

After execution, the runner attempts cleanup of its own containers, relay, and uniquely named network and reports any failure. Images and reports remain available. To release the lab model's GPU memory when you have finished using it:

```sh
ollama stop sdd-w30-qwen35:9b-64k
```

This leaves the model weights available for the next run.

## What the recorded results establish

The October 27 UTC / October 28 local run passed **47 of 47 cells**, validated the relay audit, and completed cleanup. It took approximately nineteen minutes on the recorded machine; that is one observation, not a performance guarantee.

The subsequent foundation increment added real managed-renderer lifecycle tests and stronger original-baseline rollback checks. Five focused cases passed. The full offline regression then passed **1,197 tests and 111 subtests**, with **20 PowerShell skips** and one existing warning. Those skips remain visible coverage limitations. The [foundation report](foundation-report.md) records the exact scope and timings.

These runs belong to their respective image and source hashes. Earlier live evidence does not automatically validate later changes.

The remaining work includes actual generated production role/workflow coverage, VS Code execution evidence, and foundation review acceptance. Native macOS and Windows CLI behavior also requires separate evidence: the CLIs in this lab ran on Linux. Synthetic native-loading fixtures and legacy adapter generation cover useful mechanisms without establishing every production workflow or application runtime.

The Wave 30 plan (`../enterprise-sdd/_plan/WAVE-30-HARNESS-EVOLUTION-IMPLEMENTATION-PLAN.md`; source-only reference, not supplied) consequently keeps foundation acceptance open. The next engineering task is concrete: turn each unresolved workflow into a fixture with an independent oracle, execute it in the required host, and attach its evidence to the same repeatable process.
