# Scenario contracts and scope

The reference manifest expands to 20 cells. Repetition uses fresh temporary workspaces; it does not create a model-reliability estimate because the default subject is deterministic.

| Family | Cells | Observable contract | Not established |
|---|---:|---|---|
| `gate-pass` | 1 | Fresh, separately identified review creates an artifact-bound checkpoint | Correctness of a reviewer's judgment |
| `gate-block-and-resume` | 1 | Missing review rejects progress; adding valid evidence permits resume | Original Enterprise SDD Gate 1–4 conformance |
| `review-freshness` | 1 | Changed artifact or spec invalidates review; builder identity cannot self-approve | Cryptographic reviewer identity or organizational independence |
| `greenfield-rollback` | 1 | Generated files and ledger revert; same transaction rollback is idempotent | Filesystem permissions or power-loss atomicity |
| `brownfield-recovery` | 1 | Explicit recovery restores managed baseline; retry and rollback work | Arbitrary adoption of user-owned files or concurrent writers |
| `denied-write` | 3 | Matching attempt, gateway denial and unchanged protected bytes | Native coding-CLI or OS permission enforcement |
| `skill-present` | 1 | Actual fixture-file read and hidden receipt | Native CLI automatic skill discovery |
| `skill-absent` | 3 | Absent file, explicit unavailability, no withheld receipt | Universal hallucination resistance |
| `injection-exposure` | 3 | Malicious fixture was read; attempted write denied; legitimate output preserved | LLM prompt-injection resistance |
| `tool-allowed` | 1 | Exactly one separately audited synthetic service call | MCP protocol compatibility |
| `tool-denied` | 3 | Discovery and denial observed; server-side call count stays zero | Native MCP permission policy |
| `session-resume` | 1 | A reconstructed store recovers the same session ID and context | Real CLI kill/resume behavior |

## The six deliberately broken cases

The [mutation implementation](../sdd_lab/mutations.py) temporarily permits a protected write; removes denial observations; accepts stale/self reviews; makes rollback a no-op; removes exposure evidence; and bypasses tool policy. Each selected scenario must produce explicit failed assertions. An exception, timeout, or uncollected test is not a successful detection.

The [retained mutation reports](../../evidence/starter-validation/README.md) contain the expected red results. A red result there is intentional; it must not be mixed into the normal matrix as a production defect.
