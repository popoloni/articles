# Your AI Agent Says It Followed the Rules. Make It Prove It.

Read the [illustrated article](preview.html), then run the public reference example on your own machine. This **October 29, 2026 edition** adds fresh container and Ollama results, a single-command runner, complete evidence links, and an audit finding that explains why passing tests are only as strong as their assertions.

## Start here

| Your goal | Open |
|---|---|
| Understand the method | [Article](preview.html) · [Markdown source](article.md) |
| Run the example now | [Reproduction guide](starter/docs/REPRODUCE.md) |
| Check the new reader workflow | [Host and container validation](evidence/reader-validation/README.md) |
| Inspect the latest results and their limits | [October 29 evidence](evidence/local-validation/README.md) |
| Follow a verdict back to its observations | [Proof walkthrough](evidence/PROOF_WALKTHROUGH.md) |
| Replace the fixture with your implementation | [Integration guide](starter/docs/INTEGRATION.md) |
| Verify or build the distributable | [Maintenance tools](tools/README.md) |

## A first run with no account or model

Install Python **3.11 or later**. From a clone of the repository:

```sh
git clone https://github.com/popoloni/articles.git
cd articles/Medium/261028_SDD_Testing_Complete_Companion/starter
python3 validate.py
```

From an extracted companion ZIP, open its `starter` directory and run the same command. On Windows, use `py -3` instead of `python3` and ensure it selects Python 3.11 or later. The default run needs no third-party Python packages, Docker, network access, API key, or model download.

The command runs **81 unit tests with 58 subtests**, the **20-cell reference matrix with 78 assertions**, and **six deliberate defects** that must be detected by assertion failures. It prints the path to a fresh aggregate report and preserves each stage's logs and reports. An unrequested live step is labeled explicitly; an offline pass does not claim model validation. See the [guide](starter/docs/REPRODUCE.md) for expected output, file navigation, troubleshooting, container commands, and an opt-in Ollama run.

## What the new evidence establishes

| Scope | October 29 result | Reader availability |
|---|---|---|
| Public reference tests in an ARM64 container | 81 tests / 58 subtests; 20 cells / 78 checks; six defects detected | Included code and raw evidence |
| Public live Ollama gateway probe | One real model request, three checks passed | Included code, request, events and hashes |
| Private framework's native CLI matrix | 47/47 cells passed the implemented checks | Reviewed metadata; full harness and raw private transcripts not included |
| Audit of native shell denials | Five of six cells retried despite a single-attempt instruction; every attempt was blocked | Finding and per-cell attempt counts included |
| Earlier full framework regression | Historical 1,197 tests / 111 subtests; **not rerun on October 29** | Original dated records |

The [latest evidence index](evidence/local-validation/README.md) keeps these scopes separate. The native rerun used Ollama 0.40.12, the pinned Qwen 3.5 9B alias, and verified Apple Metal inference. The original 0.40.11 configuration failed closed before live execution; both outcomes are described. The audit finding means **47/47 does not establish compliance with every instruction**.

## Verify the files you received

From the companion root:

```sh
python3 tools/verify_package.py
python3 tools/audit_original_record.py
```

The first command checks this edition's file hashes and local navigation. Historical evidence is already unpacked: no nested ZIP extraction is needed. The second checks consistency of the historical summary; it does not rerun the native matrix. Checksums detect changed bytes, not authorship.

The original five records remain unchanged. The [evidence index](evidence/README.md), [provenance](PROVENANCE.md), and [publication notes](PUBLICATION_CHECKLIST.md) identify historical material, new executions, public projections, and unavailable private inputs. The [figure captions](figure-captions.md) distinguish the historical results graphic from the latest table. The included starter and its documentation carry the [MIT license](starter/LICENSE).
