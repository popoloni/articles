# Experimental evidence notes

These notes accompany **Your AI Agent Says It Followed the Rules. Make It Prove It.** They reconcile the supplied October 27–28, 2026 records for editorial use. They are not a fresh execution, an independent certification, or a replacement for the original reports.

The structured [record extract](experiment-record-extract.json) retains the relevant results, per-cell report hashes, unresolved requirements, and provenance hashes of the five source files. The [complete supplied records](README.md) and [original upload ZIP](original-upload.zip) are now included, not just the extract. The original executable framework, container images, model weights, per-cell transcripts, and raw per-cell reports were not supplied and remain unavailable. A separate [runnable reference implementation](../starter/README.md) and its [new execution evidence](starter-validation/README.md) are included; they must not be confused with the historical framework.

## Recorded matrix

Article reference **[1]**.

Primary sources: `runtime-lab-record.json`, field `scenario_matrix`, and the opening and scenario-manifest sections of the supplied `README.md`.

The final matrix began at 2026-10-27 22:46:01 UTC and ended at 23:05:12 UTC, corresponding to October 28 in Europe/Rome. Its 47 required cells comprise three offline structural-suite executions, 22 Claude Code live cells, and 22 Copilot CLI live cells. All 47 have PASS outcomes. The relay audit was validated; its record contains 148 entries and two expected client disconnects. The recorded scope has `local_matrix_complete=true`, `overall_complete=false`, and `certificate_issued=false`.

The article's approximately nineteen-minute duration is calculated from those recorded timestamps. It is one observed run, not a hardware recommendation or a performance guarantee. The article's sample JSON combines the documented summary fields; it is an excerpt illustrating their meaning, not a new raw result file.

The matrix's accompanying historical regression had **1,195 tests and 111 subtests passed**, 20 PowerShell skips, zero failures, and one warning. Do not replace that historical value with 1,197: the latter belongs to the subsequent foundation increment.

The source record lists unresolved VS Code Copilot execution, native macOS CLI behavior, native Windows CLI behavior, complete production projection conformance, and foundation/pilot acceptance. The native OS coverage is a separate certification obligation, not a newly invented prerequisite for foundation work.

## Foundation follow-up

Article reference **[2]**.

Primary sources: `foundation-report.md`, the October 28 increment, and `runtime-lab-record.json`, field `foundation_pilot`.

Five focused cases passed: real managed-renderer greenfield and brownfield lifecycles, initial-migration/upgrade rollback in each setting, and failed-gate resume. The stable structural suite passed in three independent executions. The subsequent full offline regression records **1,197 tests and 111 subtests passed**, **20 PowerShell skips**, **zero failures**, and **one warning**.

The managed-renderer cases use the supported legacy Cursor generation path and shared publication/recovery/rollback logic. They do not demonstrate the Cursor application runtime. Brownfield begins with a managed baseline; it does not establish arbitrary adoption of user-owned files.

Foundation acceptance remains partial/blocked in the supplied record. No native capability profile was promoted. Earlier live evidence is attached to earlier source/image hashes and is not automatically recertified by this offline increment.

The prose foundation report reports 183.96 seconds for the regression; the machine-readable outer report records 184.239 seconds. The article deliberately does not publish either as a benchmark or conflate their timing scopes.

## Runbook and configuration

Article reference **[3]**.

Primary sources: the supplied `README.md`, original article draft, and the configuration and manifest fields in `runtime-lab-record.json`.

The recorded host is an Apple M2 Max with 64 GiB unified memory. CLI versions are Claude Code 2.1.311 and GitHub Copilot CLI 1.0.104. Ollama 0.40.11 serves `qwen3.5:9b-q4_K_M` through `sdd-w30-qwen35:9b-64k`, with defaults of 65,536 context tokens, 8,192 output tokens, and temperature zero. These are dated experiment pins, not statements about the latest vendor releases. No external product-version verification was substituted for the supplied baseline.

The full matrix uses isolated Linux ARM64 workers on an internal network and an allowlisted relay to host Ollama. It probes direct public TCP and host-Ollama access. The older `run` smoke has ordinary bridge egress; it is not interchangeable with `matrix`. Offline suites use network-disabled containers. Native inference remains outside Docker worker memory limits.

The deterministic selection has twelve scenario identifiers and fourteen selected pytest nodes per execution. The thirteen matrix families expand to 47 execution cells, not 47 individual assertions. Live native-loading tests use synthetic fixtures and hidden receipts. MCP permission checks combine native denial with server-side audit. Session-resume tests use observed session IDs and earlier random context. Requirements/review scenarios bind separate observed sessions to the artifact digest and verify missing-review gate rejection.

The runner automates finite batches, reporting, and cleanup. The repair loop described in the article is an agent-operated workflow around those batches, not an implemented unattended repair scheduler. Separate reviewer sessions are an observed mechanism; statistical independence or universal correctness of reviewers is not established.

Every command in the article was checked against the supplied runbook or original article. Running them requires the matching framework checkout, locks, and configuration. Those original-framework commands were not executed during companion preparation. The new reference implementation has its own executable commands and separately retained results.

## Retained failures

Article reference **[4]**.

Primary sources: the supplied original article's “Three failures that improved the lab” section, runbook isolation/aggregation notes, and retained attempts under `scenario_matrix.reports` in the machine-readable record. The supplied `runtime-lab.md` also retains earlier smoke-stage integration failures; those earlier 22-check outcomes must not be mistaken for the later 22-cell matrix outcomes.

The documented corrections include permitting execution on dedicated temporary filesystems needed by the real launcher; admitting the exact Messages `?beta=true` route without widening the allowlist generally; and distinguishing expected downstream disconnects from upstream transport failures.

The record explicitly retains an earlier full-matrix attempt with **47 passed cells but overall FAIL** because of an unexpected relay rejection or transport error. The later final matrix passed its aggregate checks. Raw transcripts were not supplied in the source archive, so these details are attributed to the author's documentation and replay summary rather than to newly inspected raw network logs.

## Provenance and publication

The source archive contains five files: `README.md`, `foundation-report.md`, `runtime-lab.md`, `runtime-lab-record.json`, and `testing-an-sdd-framework-autonomously.md`. Their SHA-256 hashes are preserved in the extract. Public-looking relative paths in the original documents were not assumed to be accessible repositories.

The seven figures were separated from the illustration supplied in the conversation. Corrections are documented in `../figures/figure-manifest.json`. They are explanatory illustrations, not evidence screenshots. No font files, credentials, container images, model weights or original raw CLI transcripts are added. Unlike the earlier editorial-only pack, this complete companion preserves the full author-supplied records, which contain local/private repository provenance identifiers. Review that metadata before public redistribution.

The article's numbered references resolve inside the extracted package. For publication on Medium, keep the source descriptions and publish the experiment notes at an accessible location if clickable references are desired. Relative package paths are not public web URLs.

## New reader companion

Article reference **[5]**.

The [new validation index](starter-validation/README.md) reports 81 passing reference tests and 58 successful subtests; 20 passing reference cells with 78 assertions; six detected deliberate defects; and six passing auditor tests. These were executed on Linux x86_64 / Python 3.13.5. The original 47-cell matrix and 1,197-test result were not re-executed. Real Ollama, native CLI and Docker options were not executed. All new reports contain explicit scope and source-identity fields.
