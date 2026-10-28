# Your AI Agent Says It Followed the Rules. Make It Prove It.

## Complete article, evidence and reusable implementation

Start with the [illustrated HTML article](preview.html) or [Markdown article](article.md). The article embeds seven separate figures in the navy, orange, white and cyan book-cover style and links to the supporting records and runnable code included here.

| What you need | Open |
|---|---|
| Medium-ready article | [article.md](article.md) or [preview.html](preview.html) |
| Seven individual figures and captions | [Figure guide](figure-captions.md) |
| Complete supplied historical records | [Evidence index](evidence/README.md) |
| Reusable, standard-library Python implementation | [Starter quickstart](starter/README.md) |
| Newly executed tests and proof | [Validation index](evidence/starter-validation/README.md) |
| Original-record consistency audit | [Audit result](evidence/record-audit/record-audit.json) |
| Publication and provenance notes | [Publication checklist](PUBLICATION_CHECKLIST.md) and [provenance](PROVENANCE.md) |

## Execute the starter

Python 3.11+ is sufficient for the default offline tests; no paid account or model is required.

```sh
cd starter
python3 -m unittest discover -s tests -v
python3 lab.py run
python3 lab.py mutations
```

The prepared package records **81/81 regression tests**, **58 successful subtests**, **20/20 reference cells**, and **six detected deliberate defects**. Reports, logs, individual cell evidence, and executable sources are included. These are new reference results on Linux/Python, not reruns of the original author's native-agent experiment.

From the package root, check original-summary consistency and distribution integrity:

```sh
python3 tools/audit_original_record.py
python3 tools/verify_package.py
```

## Three boundaries that matter

The original **47/47 local cells** and **1,197-test/111-subtest follow-up** are historical author-supplied results. All five supplied records and the original archive are included. The original private executable framework, raw per-cell payloads, image archives and weights were not supplied; their absence is listed explicitly rather than filled with invented proof.

The new **reference starter** is fully included and was executed here. Its default agent is scripted; it teaches observable contracts, not native Claude/Copilot conformance. A direct Ollama probe and an optional Docker recipe are provided, but real-model and Docker executions were not performed during this validation.

The entire ZIP is self-contained for reading the article and running the offline starter. Re-executing the original native-agent laboratory still requires the missing original inputs. New starter code is MIT-licensed; the archive does not relicense artwork or historical documents.
