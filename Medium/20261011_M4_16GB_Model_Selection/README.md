# One article: choosing a local LLM for a 16 GB M4 Mac mini

Open **article-standalone.html** in Safari, Chrome or Firefox. The eight performance plots are embedded in that file. It is the complete article, including the model explanations, installation and run instructions, measured comparisons and the final selection. No earlier guide or revision patch is required.

For Medium or other publication workflows, use **article.md** and insert the PNG files from **figures/** at the eight marked positions. A Markdown file alone does not upload its companion images. **article.html** uses relative image links and works when the package stays together.

## Installation workspace

Extract this folder to `~/LocalAI/M4_16GB_Model_Selection`, then follow the article. Existing users should preserve their completed `~/LocalAI/qwen-bonsai-lab` model downloads and working virtual environments. The package does not run an installer, change memory limits, execute a model's tools or download weights automatically.

The original launcher, checkpoint downloader, API clients and loader checker remain byte-identical to the working R7 versions. Three new convenience helpers are included: `tools/plan_measured.py` selects recorded checkpoint revisions; `scripts/test_model.sh` runs a separate readiness check before the original six contracts; `tools/ollama_probe.py` saves native Ollama responses before evaluating completion, retaining truncated output for diagnosis. Status descriptions in the model catalogue now reflect the measured results; execution settings are unchanged.

## Contents

- `article.md`, `article.html`, `article-standalone.html`: one manuscript, three reading formats.
- `figures/`: eight performance figures in PNG and SVG.
- `tools/`, `scripts/`, `config/`, `fixtures/`: runnable helper code, settings and controlled test inputs.
- `analysis/`: audited request-level data, source ledger, Python parser/plotter and tests.
- `sources/`: original supplied standalone guide, preserved as source material rather than a second operating manual.
- `VALIDATION.md`, `validation/`: actual publication checks and their scope.

## Reproduce the local checks

The helper tests require Python and Bash, but no downloaded model or Apple GPU:

```bash
python3 -m unittest discover -s tests -v
```

The data-analysis suite uses its separately listed dependencies:

```bash
python3 -m venv .venvs/analysis
.venvs/analysis/bin/python -m pip install -r analysis/requirements.txt
.venvs/analysis/bin/python -m unittest discover -s analysis -p 'test_*.py' -v
```

Keep the original `logs.zip` when regenerating the analysis. It is not republished in this package; normalized response records retain the measurements but replace local home-directory names with `$HOME`. Review any newly added logs for private content before publishing them.

The experimental conclusions come from 66 recorded responses to two short tasks. They are not a general coding leaderboard. Model-free tests do not validate fresh Mac installations or prove inference quality.
