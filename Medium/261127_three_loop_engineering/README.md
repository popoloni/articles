# Three-Loop Engineering — runnable article companion

Reference implementation for **Beyond the Loop: The Three-Loop Architecture for AI Agents** by Enrico Papalini (November 2026).

## Quick start (offline)

Requires Python 3.10+ (tested on 3.10, 3.11, 3.12, 3.13 and 3.14). No third-party packages, API keys, Docker or network access for the reference experiment. Run commands from this directory; if `python` is not on your PATH, use `python3`. Use a fresh output path on every new run.

```sh
python -m unittest discover -s tests -v
python -m three_loop demo --out runs/experiment-01
```

`demo` trains on two fixed money tasks, derives and freezes a candidate policy from those training episodes only, and runs a paired evaluation on two other money tasks and one unrelated text task. Expected: all tasks accepted under both policies; baseline 7 attempts, candidate 3. The deterministic worker intentionally repeats a poor strategy under `v1`. The report recommends `v2`; `active.json` still points to `v1`.

Open `runs/experiment-01/evaluation.json` and inspect the evidence before approving. The stdout JSON includes an `approval_digest` and a `baseline_sha`. On POSIX shells:

```sh
RUN=runs/experiment-01
APPROVAL=$(python -c 'from three_loop.model import digest,read_json; from pathlib import Path; print(digest(read_json(Path("runs/experiment-01/evaluation.json"))))')
BASELINE=$(python -c 'from three_loop.model import read_json; from pathlib import Path; print(read_json(Path("runs/experiment-01/evaluation.json"))["baseline_sha"])')
python -m three_loop promote --run "$RUN" --approve "$APPROVAL"
python -m three_loop run-active --run "$RUN" --task holdout_invoice --out runs/next-episode
python -m three_loop rollback --run "$RUN" --approve "$BASELINE"
```

On other shells, paste the digests printed by `demo` into the commands instead. Do not automatically approve real production changes.

What each governance step checks:

- `promote` binds the exact evaluation to an explicit local operator action. It requires `v1` to be active in both `active.json` and the governance log, requires the candidate to have been recorded by the learning step, verifies episode provenance, retained sources and evidence, recomputes the policy gate, and refuses an approval digest that has already been used. After a rollback, the same candidate cannot be re-promoted without a new evaluation.
- `run-active` refuses to start if `active.json` disagrees with the last promotion or rollback recorded in the governance log.
- `rollback` requires `v2` to be active (pointer and log) and the exact baseline digest. Both revisions are retained.

None of this is authenticated approval or a transactionally durable registry; a privileged local writer can rewrite everything.

## Optional live Claude adapter (paid)

The agent selects from pre-authorized patches rather than producing and executing arbitrary source. There are no agent tools, shell, file writes or hidden test fixtures supplied to the model. Contract, catalogue entries for the current route and a failure summary are sent to the provider. Set `ANTHROPIC_API_KEY` securely in your shell and specify a model available to you (do not paste a secret into the command or repo):

```sh
python -m three_loop live --model YOUR_MODEL_ID --task train_fees \
  --max-calls 3 --max-output-tokens 256 --out runs/live-01
```

The adapter calls `POST https://api.anthropic.com/v1/messages` with `Authorization: Bearer`, `anthropic-version: 2026-10-21` and, if `ANTHROPIC_WORKSPACE_ID` is set, `anthropic-workspace-id` (needed only for API keys that are not scoped to a workspace). It accepts a bare JSON object, tolerating one surrounding Markdown code fence; any other reply, or a `stop_reason` other than `end_turn`, becomes an invalid proposal and ends the episode with reason `invalid_proposal` (fail closed). Token usage is recorded either way.

The `live` command runs one bounded episode and does not modify the experimental policy or publish results. There is no automatic HTTP retry. The controller limits attempted model calls (reserved before each invocation) and output tokens requested per call. Input usage, failed requests and other expenses can vary; no hard monetary limit is claimed. The network client's timeout is not a guaranteed end-to-end deadline. Paid execution was not used for this delivery; the protocol is exercised by mocked tests, including a complete mocked episode. `--model` is required to avoid guessing provider model availability.

## Inspecting the evidence

`./reproduce_results.sh` regenerates everything below from scratch; the demo is deterministic, so the files come out byte-identical.

- `results/demo_stdout.json`: offline experiment output, including hashes.
- `results/replay/`: baseline and candidate policies, training and held-out episode artifacts, diagnostic probes, proposals, actual candidate source, independent acceptance evidence, hash-chained traces, gate report and governance trace.
- `results/test_log.txt`: unit and integration test log.
- `results/promotion_stdout.json`, `active_v2_stdout.json`, `rollback_stdout.json`: operator lifecycle replay; `results/active_v2/` contains the subsequent episode. The archived experiment ends rolled back to `v1`; a fresh demo is unpromoted.

An episode is identified by task and pinned policy digest. The verifier subprocess runs only a known catalogue source file after byte-for-byte checking in the parent and digest validation in the child. The acceptance contract is not supplied as executable code to the agent. Acceptance is relative to the finite trusted suite. The diagnostic probe is one fixed witness, not a proof of universal correctness. The `audit` module verifies internal hash continuity; it does not establish authenticity against a privileged local writer. This is a local teaching repository, not a secure sandbox.

## Design scope

The learner reads training episodes only. It proposes a route change when at least two distinct training tasks of one family were accepted after a supported diagnosis switched them to the same route and no episode of that family contradicts it; the new route is taken from that evidence. In this lab the only diagnostic, and therefore the only learnable change, is the `v1` to `v2` money route. The lab demonstrates the learning lifecycle, not a general-purpose policy optimizer. The holdout fixtures are published; the learner's input excludes them, but the developer knows the dataset. The example is synthetic and is not a benchmark of a real coding agent or evidence of real cost savings. The worker catalogue contains trusted code and must not be replaced with arbitrary model output without strong sandboxing. The policy registry, operator approval and audit log are intentionally local; production needs authentication, protected persistence, concurrency handling, recovery, budget enforcement and independent verifier authorization.

## Publication and figures

`article.md` is the English Medium draft, and `article.html` is a self-contained reading copy built with Pandoc (`./build_article.sh`). Medium does not import local images or Markdown tables: upload the PNGs from `figures/` where indicated, and use the table images in `figures/tables/`. DOT and SVG originals are included. `figures/build_figures.sh` rebuilds the diagrams with Graphviz and the chart with Python/matplotlib (optional figure-build dependencies only). See `PUBLICATION.md` for the pre-publication checklist and suggested social copy.
