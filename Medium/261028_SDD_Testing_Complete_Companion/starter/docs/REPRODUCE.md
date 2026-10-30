# Reproduce the public companion

This guide runs the included public code. It cannot reconstruct the private framework, its native agents, or the historical 47-cell experiment. The [October 29 evidence index](../../evidence/local-validation/README.md) records the exact environments actually exercised. The earlier [Linux baseline](../../evidence/starter-validation/README.md) remains available separately.

## Host run: no packages or model required

Install Python 3.11+ through your normal platform tools if it is absent. No `pip install` or credentials are needed. Open a terminal in the extracted `starter` directory.

POSIX shell (macOS/Linux):

```sh
python3 --version
python3 validate.py --output validation-runs
```

Windows PowerShell:

```powershell
py -3 --version
py -3 validate.py --output validation-runs
```

The default command executes these three stages in order, retaining separate subprocess logs and reports:

| Stage | Current expected result | Passing condition |
|---|---|---|
| Unit suite | 81 tests and 58 successful subtests | Nonempty consistent records; every test passes; no skips, failures or errors |
| Full reference matrix | 20 cells / 78 assertions across 12 families | Every manifest cell and repetition appears exactly once and passes |
| Deliberate mutations | 6/6 detected | Each of the six named defects causes failed assertions, not a crash |

The final line is `PASS (offline-reference-only); live: NOT_REQUESTED` when all three stages pass. `NOT_REQUESTED` is an explicit scope record, not a live success. No model is contacted by the default command. The runner checks records and coverage, rather than accepting a process's printed `PASS` alone. New unit tests may increase the count without modifying the reader runner.

The 81-test baseline has one portability correction: the contained-path assertion resolves its expected temporary-directory path, matching the existing runtime behavior. This handles macOS's `/var` → `/private/var` symlink without changing the path-containment contract or the test count. Historical reports retain the original source hashes; new reports fingerprint the corrected test source.

Exit codes: **0** means all requested stages passed; **1** means a stage failed, errored, was blocked or was interrupted; **2** means invalid arguments or inability to create the output directory. A requested live stage participates in the final result. Ordinary stage failures do not prevent the remaining stages from collecting evidence. Ctrl-C stops further work and retains the available summary; a force-killed process may leave `RUNNING`/`PENDING`, which is not a pass.

## Read your evidence

The command prints the exact fresh directory it created. Reusing `--output validation-runs` creates another child directory and never reuses an old run.

```text
validation-runs/validation-<UTC time>-<random ID>/
  summary.json
  unit/
    console.log
    unit-tests.json
    unit-tests.xml
    unit-tests.log
  matrix/
    console.log
    matrix-<UTC time>-<random ID>/
      summary.json
      manifest.json
      junit.xml
      cells/<family>--reference-fixture--<repetition>/
        report.json
        events.jsonl
        workspace-before.json
        workspace-after.json
        workspace-final/
        controller-final/
  mutations/
    console.log
    mutations-<random ID>/
      summary.json
      <mutation>/report.json
      ... retained events and fixture files ...
  ollama/                           # only when explicitly requested
    console.log
    ollama-<random ID>/summary.json
    ... request, model identity, events and protected hashes ...
```

Start with the outer `summary.json`: check `status`, `scope`, `offline_complete`, `live_requested`, `live_status` and each entry in `steps`. Each executed step links to its report and console log. A `runner-error.log` records failures that prevent report loading. The outer report retains interpreter/platform identity, runtime-source fingerprints, the reader-runner hash and unit-reporter hash. Reports also retain the observed source and evidence hashes; these identify bytes and do not act as a cryptographic attestation of who ran them.

For the matrix, check `reference_matrix_complete` and the `coverage` lists before reading individual `cells/*/report.json` assertions. Inspect `events.jsonl` for the actual runtime and policy observations. Mutation cell reports intentionally say `FAIL`; the mutation summary passes only when those expected assertion failures were observed. No generated result certifies native Claude, Copilot, a private framework, or an arbitrary integration.

The unit JSON retains class/module setup or teardown failures and skips in `fixture_outcomes`, separately from executed test methods. JUnit represents these as additional synthetic cases. Such outcomes make validation fail and retain their primary diagnostic; they do not disappear into a passing test count.

## Optional container run, with a pinned base and retained host evidence

The recorded container baseline uses **Linux ARM64 / Python 3.12.15** and this exact base-image digest:

```text
python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
```

You need a running Docker engine. Provision the pinned image explicitly before the offline execution; the following pull is an optional setup action requiring network access:

```sh
docker pull --platform linux/arm64 python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
```

Use the commands below from `starter`. The build produces a local image with the actual checked-out sources. Capture its immutable image ID and run that ID with pulling disabled. A different checkout creates a different image; no prebuilt companion image is distributed. The ARM64 recipe requires an ARM64 engine or configured emulation. On another architecture, choose and record an appropriate verified base digest and platform; that is a new environment to validate.

POSIX shell, run as an ordinary nonroot host user:

```sh
set -eu
if [ "$(id -u)" -eq 0 ]; then
  printf '%s\n' 'Run this recipe as an ordinary nonroot user, without sudo.' >&2
  exit 1
fi
base='python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70'
docker image inspect "$base" >/dev/null
docker build --platform linux/arm64 --pull=false --build-arg "PYTHON_IMAGE=$base" -t sdd-companion:local .
image_id=$(docker image inspect --format '{{.Id}}' sdd-companion:local)
mkdir -p validation-container
docker run --rm --pull never --platform linux/arm64 --network none --read-only \
  --user "$(id -u):$(id -g)" --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 128 --memory 512m \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --mount "type=bind,source=$(pwd)/validation-container,target=/evidence" \
  "$image_id" python validate.py --output /evidence
```

The POSIX command runs with your host UID/GID so the exported owner-readable reports belong to you on Linux. The root check preserves the nonroot execution requirement; use an ordinary account rather than `sudo`. The dedicated output directory is the only writable host mount; keep unrelated files out of it. The container's source filesystem is read-only and its network is disabled. The temporary fixture workspace is disposable; retained results are written directly to the host bind mount before the container is removed. The `Dockerfile` default command runs only a unit smoke; the explicit `python validate.py` override above runs the full offline companion. Generated container evidence is excluded by the supplied Git and Docker ignore files.

Windows PowerShell with Docker using Linux containers:

```powershell
$ErrorActionPreference = 'Stop'
$base = 'python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70'
docker image inspect $base | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Provision the exact base image first.' }
docker build --platform linux/arm64 --pull=false --build-arg "PYTHON_IMAGE=$base" -t sdd-companion:local .
if ($LASTEXITCODE -ne 0) { throw 'Container build failed.' }
$imageId = docker image inspect --format '{{.Id}}' sdd-companion:local
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the built image ID.' }
New-Item -ItemType Directory -Force validation-container | Out-Null
$evidence = (Resolve-Path validation-container).Path
docker run --rm --pull never --platform linux/arm64 --network none --read-only `
  --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges `
  --pids-limit 128 --memory 512m `
  --tmpfs /tmp:rw,nosuid,nodev,size=256m `
  --mount "type=bind,source=$evidence,target=/evidence" `
  $imageId python validate.py --output /evidence
if ($LASTEXITCODE -ne 0) { throw 'Validation failed; inspect the retained evidence.' }
```

These Windows commands are provided for readers; they do not claim that Windows was tested. Docker Desktop must allow sharing that output directory. If its permission mapping prevents writes by UID 10001, fix sharing/access for that dedicated directory and retry; an unwritable evidence directory is an error, never a pass.

Keep `docker image inspect <image ID>` output with your results if you need to record image configuration and IDs. Build output and image identity are separate from the runtime report's Python/platform/source hashes. The offline container run intentionally cannot contact host Ollama. Run an optional live probe on the host using [the Ollama guide](OLLAMA.md); it is a separate execution boundary.

## Diagnose a nonpassing run

| Symptom | Next action |
|---|---|
| `python3` or `py` not found | Install/select Python 3.11+ and rerun from `starter` |
| Output directory cannot be created | Choose a writable `--output` directory; container runs need the dedicated writable bind mount |
| Unit failure or import error | Read `unit/console.log`, `unit-tests.log` and the JSON case details |
| Matrix incomplete or nonpassing | Read the matrix `coverage` lists and the named cell's assertions, events and traceback |
| Mutation not detected | Inspect the mutation's `observed_status` and `failed_assertions`; a crash does not count |
| `ERROR` with no usable stage report | Read `console.log` and `runner-error.log`; keep the failed run when retrying |
| Live `BLOCKED` | Check the local Ollama server and timeout; requested blocked work makes the command fail |
| Live digest/name mismatch or unexpected output | Use the local `/api/tags` identity and inspect the live records; do not substitute a model silently |
| Docker daemon, architecture or permission error | Check the running engine, ARM64 execution support and output-directory sharing |

For a narrow diagnostic rerun, use `python3 lab.py run --scenario denied-write`; this retains all three repetitions but does not claim full-matrix coverage. On Windows use `py -3`. For the orchestration helper's separate regression tests:

```sh
python3 -m unittest discover -s validation_tests -v
```

The suite covers empty/skipped/duplicate unit records, incomplete matrix coverage, mutation crashes, missing reports, child-process failure, explicit live selection, preserved runs and interruption. It is intentionally outside the original unit-test directory so the published 81-test baseline remains intact.
