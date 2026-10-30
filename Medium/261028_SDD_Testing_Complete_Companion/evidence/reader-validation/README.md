# Reader workflow validation — October 29, 2026

These are fresh executions of the public reader workflow after adding the single-command runner and fixing its reporter and a macOS path assertion. They are separate from the [earlier local validation](../local-validation/README.md) and do not rerun the private native-agent matrix.

| Execution | Recorded result | Evidence |
|---|---|---|
| Complete offline reader run, Linux ARM64 / Python 3.12.15 | PASS: 81 tests, 58 subtests; 20 matrix cells, 78 assertions; six deliberate defects detected | [Unchanged aggregate](container-run/summary.json), [unit report](container-run/unit/unit-tests.json), [matrix](container-run/matrix/matrix-20261029T215343Z-0f67c31124/summary.json), [mutations](container-run/mutations/mutations-5ecff50875/summary.json) |
| Combined host reader run, macOS ARM64 / Python 3.14.6 | PASS: all four requested stages, including the live gateway probe | [Host summary projection](host-summary.json), [unchanged live summary](live-probe/summary.json) |
| Reader orchestration and reporter regressions | 24 tests passed | [Unchanged test log](reader-tooling-tests.log) |
| Package tooling regressions | 17 tests passed, reported by the controller; no raw log retained | [Tooling scope](tooling-validation.json) |
| Initial host attempt | FAIL: 80/81 unit tests passed; matrix and mutations passed | [Failure projection and correction](initial-host-failure.json) |

## What was executed

The container aggregate was recorded at **21:53:42–21:53:43 UTC**, and the final combined host aggregate at **21:54:40–21:54:43 UTC**. Both used the final reader runner and unit reporter identified by their retained SHA-256 values. The container's live step is explicitly `NOT_REQUESTED`; the separate host run explicitly requested the exact installed model name and digest.

The [container execution projection](container-execution.json) records immutable image ID `sha256:f33bad86270ff0bbeb40473c9a87bbb129f0cb6762f63fca86fc85d8dc256a77` and distinguishes image inspection from controller-supplied runtime configuration. The invocation used host UID:GID **501:20**, overriding the image's **10001:10001** default, with network disabled, a read-only root filesystem, dropped capabilities, bounded resources and one dedicated evidence bind mount. Image inspection alone does not prove those invocation flags.

The host live probe used `sdd-w30-qwen35:9b-64k`, digest `2de0531475f0ecfe815dde919b206d02eb3d343ac95fa26d9f6427ad0b27e20e`. Inspect the retained [request](live-probe/request.json), [assistant tool request](live-probe/assistant-output.json), [operation and denial events](live-probe/events.jsonl), and [protected hashes](live-probe/protected-hashes.json). All three gateway checks passed. The probe itself does not measure GPU use; the earlier [Metal observations](../local-validation/ollama-metal-evidence.json) belong to a separate execution.

## Retained failure and corrections

The first host run failed `test_contracts.PathTests.test_path_is_contained`: on macOS, `/var` aliases `/private/var`, while the assertion compared a resolved path against an unresolved expected path. The correction resolves the expected path. The runtime implementation was unchanged; the [failure projection](initial-host-failure.json) preserves the failed count, test identity and before/after test-source hashes.

The unit reporter also now retains class/module fixture failures and skips separately from executed test methods. Its JSON `fixture_outcomes` list preserves these diagnostics, and JUnit includes synthetic fixture cases. This keeps the original **81-test** baseline separate from the **24** reader-tooling regressions. Both final unit reports have no fixture outcomes, skips, errors or failures.

## How this evidence was shared

The complete [container run](container-run/summary.json), complete seven-file [live probe](live-probe/summary.json), and reader-tooling log were copied byte for byte. Their embedded evidence hashes were not rewritten. Original container commands retain their synthetic `/work` and `/evidence` paths as execution history; public report links remain relative within the copied run.

The host aggregate, initial failure and image inspection are explicitly labeled **exported derivatives**. They omit absolute user paths, private temporary identifiers and unrelated image-storage details. Original source hashes identify the unpublished input bytes; they are distinct from hashes of these rewritten summaries. The host's outer console log was excluded because it contained an absolute user path. Host offline reports are not exported; the complete independent container run supplies the raw offline evidence.

The [export manifest](export-manifest.json) separates unchanged copies from derived files and records their hashes. It does not attest authorship, reproduce omitted inputs, or establish native-agent conformance. No private source or native transcripts are required to open these public files.

For another execution, follow the [reproduction guide](../../starter/docs/REPRODUCE.md).

