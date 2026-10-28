# Evidence index: what is included and what is not

This directory separates **author-supplied historical records**, **newly executed reference tests**, and **unexecuted optional integrations**. These are different kinds of evidence and must not be combined into one success rate.

## Original experiment: complete supplied material

All five files from the uploaded archive are included unchanged under `original/`, alongside the original ZIP. Their hashes are listed in [source-file-sha256.json](source-file-sha256.json).

| Supplied file | Readable copy | Exact original |
|---|---|---|
| Laboratory runbook | [Runbook](reading/README.md) | [README.md](original/README.md) |
| Execution narrative and retained failures | [Runtime report](reading/runtime-lab.md) | [runtime-lab.md](original/runtime-lab.md) |
| Subsequent foundation assessment | [Foundation report](reading/foundation-report.md) | [foundation-report.md](original/foundation-report.md) |
| Complete machine-readable record | [Full JSON](original/runtime-lab-record.json) | Same file; not merely an extract |
| Original author draft | [Original draft](reading/testing-an-sdd-framework-autonomously.md) | [Original Markdown](original/testing-an-sdd-framework-autonomously.md) |

The [original upload ZIP](original-upload.zip) preserves the exact supplied archive. The [editorial evidence notes](experiment-notes.md) map article claims to these sources. The previous [record extract](experiment-record-extract.json) remains available, but no longer substitutes for the full record.

Portable reading copies remap local links where the target was supplied. References to absent private-repository files are displayed as source-only references rather than broken download links. Exact originals intentionally retain their original context and links.

## Historical record consistency audit

The [audit result](record-audit/record-audit.json) checks 16 properties: expected cell expansion and uniqueness, 44 live plus three structural cells, reported outcomes, coverage, report-hash syntax, the later regression counts, retained failures and explicit non-certification. Its [implementation](../tools/audit_original_record.py) and [six negative/regression tests](../tools/tests/test_record_audit.py) are included, with [test output](record-audit/auditor-tests.log).

**A consistent summary is not proof that absent raw executions occurred.** This audit does not rerun the original framework and does not authenticate raw payloads by inspecting their hashes alone.

## Newly executed proof

The [starter validation index](starter-validation/README.md) contains the executed unit tests, reference matrix, six deliberate-defect demonstrations, JSON/JUnit outputs and per-cell observations. These runs exercise the complete [reusable starter](../starter/README.md), not the private production implementation.

For a concrete example, the [proof walkthrough](PROOF_WALKTHROUGH.md) links a denied-write verdict to its actual observations and a corresponding defective implementation.

## Missing original artifacts, explicitly inventoried

The [machine-readable inventory](evidence-inventory.json) lists **38 source-only repository links** in the supplied Markdown and **70 distinct recorded raw-report references** whose payloads were not in the upload. Their absence is not repaired by generating look-alike files.

The upload did not contain the original private framework source, executable lab/worker/native adapters, per-cell transcripts, raw relay/JUnit logs, container image archives or model weights. Some identities and report hashes are preserved in the supplied record, but the corresponding bytes cannot be reconstructed from those hashes.

The new starter is included so readers can run and extend the method immediately. It is not a claim to reproduce all 47 original native-CLI cells, the 1,197-test production regression, or the original isolation architecture.

## Publication review

The complete archival sources contain provenance metadata, including local paths and a private-repository identifier. Review these before publishing the entire ZIP publicly. No additional private repository was accessed and no credentials, font files, raw original CLI transcripts, container images or model weights were added. Preserve evidence limitations if producing a public redacted copy; do not silently edit the exact originals while retaining their original hashes.
