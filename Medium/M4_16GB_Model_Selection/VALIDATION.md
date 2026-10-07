# Validation of the consolidated article and package

**Prepared 6 October 2026. No new model inference or physical-Mac benchmark was run for this publication.**

## Evidence and numerical checks

The supplied original `logs.zip` was parsed again with the R7 analysis code. Its SHA-256 is `0856bf466702f953dcc05a0fe1ed278917cd2d450a7fc12a529745de137f78ca`. The recomputed audit, request table, profile summary, case summary, suite summary and CLI observations match the included R7 numeric tables byte for byte. The eight existing matplotlib plots preserve that evidence rather than inventing new measurements.

The archive contains 66 smoke responses to two fixed questions, not 66 distinct benchmark tasks. The 53 passing and 13 failing verdicts were recomputed from saved answers. No coding, tool execution, long-context, native-Ollama performance or full-system memory result has been filled in where evidence is absent.

## Tests actually run

**185 model-free helper and regression tests passed**, including tests of the three newly added convenience helpers. Synthetic local HTTP servers verified the exact model-ID gate, one completed readiness answer before six contract requests, refusal to proceed after readiness failure, preservation of truncated native-Ollama responses, non-thinking/request-budget settings, and no model substitution. These tests do not run an MLX kernel or load a checkpoint.

**28 analysis tests passed**, covering contract re-evaluation, aliases, failures, derived statistics, missing measurements, archive safety and the eight figure links. Total: **213 model-free tests** in the two suites.

All **61 Bash blocks in the article** passed `bash -n`; the code blocks contain no nonbreaking-space indentation or rendered-link syntax. Python files parsed successfully, and supplied shell scripts passed syntax checks. Syntax validation is not a claim that every external dependency resolves on a new Mac.

## Publication checks

Both the 1,440-pixel desktop and 390-pixel mobile article layouts were rendered in Chromium from the exact HTML content. All eight embedded PNGs decoded and displayed, with no JavaScript errors or horizontal page overflow. Selected opening, cache-comparison and conclusion views were visually inspected. Local links and heading fragments were checked, and each base64 image was decoded and verified as a real PNG.

`article-standalone.html` embeds the plots for offline reading. Supporting audit/data links still refer to files in the package; the standalone article itself does not need those files to display its text or figures.

## What changed—and what did not

The working launchers, checkpoint downloader, API clients, loader checker, dependency requirement files and memory-snapshot helper are preserved from R7. `analysis/inference-code-checksums.json` checks the byte-identical original components that are shipped in this package; the full original checksum inventory is retained under `validation/`.

`config/standalone-models.json` changes only the descriptive status text and review date. Execution fields were compared against the original after excluding those two metadata fields. The exact runtime-field baseline is retained in `validation/unchanged-runtime-profile-fields.json` and checked by the test suite.

New files are `tools/plan_measured.py`, `scripts/test_model.sh`, `tools/ollama_probe.py`, their tests, the single rewritten article and its supporting publication material. Obsolete multi-revision patch installers and old duplicated guide assertions are not shipped. Independent launcher and wired-snapshot regression tests remain.

Existing environments, weights and Mac settings are not changed by extracting or reading this package. Running a selected installation command is a separate, deliberate action. The numerical recommendation remains provisional for coding: its basis is the observed short-contract behavior and limited memory evidence, not a completed repository-level benchmark.
