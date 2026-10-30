# Provenance and scope

Package edition: **October 29, 2026 reader rerun edition**.

The article and seven figures describe a testing method and dated experiments. The [figure manifest](figures/figure-manifest.json) records artwork provenance; Figure 7 remains historical. Latest results appear in text and tables, not in a relabeled historical image.

## Historical material

All five original records and the original ZIP remain unchanged in [evidence/original](evidence/original/README.md) and [original-upload.zip](evidence/original-upload.zip). The [source inventory](evidence/source-file-sha256.json) records their hashes. Portable copies adapt links while retaining historical scope.

The October 28 public starter evidence remains in [starter-validation](evidence/starter-validation/README.md). This edition restores 194 archived evidence files byte for byte from the supplied matrix and mutation ZIPs; every payload was checked against the original manifest. The old distribution manifest and validation record remain in [distribution history](evidence/distribution-history/README.md). The two previously absent ignore files are new replacements, not recovered historical bytes. Revised article and generated HTML files have a new edition manifest.

## Fresh October 29 executions

The public reference code ran in a Linux ARM64 container with Python 3.12.15: 81 tests and 58 subtests, 20 cells and 78 assertions, and six detected defects. Its live gateway probe ran on macOS/Python 3.14.6 against a locally installed Ollama model and passed three checks for one real request. Raw public evidence is linked from the [new evidence index](evidence/local-validation/README.md).

The matching private framework was also available on the author's machine. Its native matrix was reexecuted using Claude Code 2.1.311, Copilot CLI 1.0.104, Ollama 0.40.12, and the pinned Qwen 3.5 9B alias. All 47 cells passed the implemented assertions. A subsequent audit found single-attempt instruction violations in five denied-shell cells; all attempts were blocked. This is an oracle coverage gap, not full instruction conformance. The earlier 1,197-test framework regression was not reexecuted.

Shared native metadata is a labeled projection of private reports. It does not include the private framework, full CLI transcripts, exact container image archives, or model weights. Native file-preservation verdicts lack retained before/after hash maps, so those comparisons cannot be reconstructed from shared evidence. No production or cross-platform certificate is issued.

## Reader tooling and edition checks

The new [single-command runner](starter/validate.py) orchestrates unchanged reference contracts, retains stage failures, and makes live invocation opt-in. Its tests are separate from the original 81-test suite. One baseline assertion now resolves the expected macOS temporary path; the unit reporter also retains class/module fixture errors and skips. The [reader workflow evidence](evidence/reader-validation/README.md) preserves the initial portability failure and subsequent host/container results.

The [release builder](tools/package_release.py) creates a versioned checksum manifest and self-contained ZIP; the old manifest remains historical. Fresh tooling and reader-run checks are recorded in [package-validation.json](package-validation.json). The builder verifies the assembled archive before writing it. Final extraction verification is retained alongside the delivered ZIP, so its report can identify the exact archive digest without a self-referential manifest.

## Interface references

Official interface documentation was checked again on October 29, 2026:

- [Ollama local setup](https://docs.ollama.com/quickstart)
- [Ollama chat API](https://docs.ollama.com/api/chat), [tool calling](https://docs.ollama.com/capabilities/tool-calling), and [installed model metadata](https://docs.ollama.com/api/tags)
- [Running-model metadata](https://docs.ollama.com/api/ps) and [hardware support](https://docs.ollama.com/gpu)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Docker container execution](https://docs.docker.com/engine/containers/run/)

Documentation supports setup instructions; dated execution records support results. SHA-256 inventories are integrity metadata, not signatures.
