# Jev and the Return of the Classifier — complete illustrated edition

## Open this first

**Open `essay-standalone.html` in your browser.** All seven illustrations are embedded directly in that file, at the corresponding sections of the essay. No internet connection, special Markdown renderer, or separately hosted images are needed to read it.

`essay.md` is the full Markdown manuscript for editing and publishing. Its seven image references use relative `figures/...png` paths. Keep the `figures/` directory beside the Markdown file. `essay.html` is an additional reading copy that uses those same local image files.

The essay’s original text, code blocks and 56 numbered source entries are retained; the new figure blocks add illustrations and explanatory captions without rewriting the body. This is a packaging/illustration update, not a new factual audit of the original evidence snapshot (30 September 2026).

## What is in the ZIP

- `essay.md`, `essay.html` and `essay-standalone.html`: the complete illustrated essay.
- `figures/`: seven high-resolution, white-background pen-and-color diagrams; `figure_manifest.json` records their locations, captions and checksums.
- `examples_ollama/`: native Python and HTTP System One examples, with triage and paddle requests.
- `realtime/`: the complete browser Paddle Lab, Python bridge, JavaScript simulation, instructions and tests.
- `scripts/`, `tests/`, `triage.py`, `laya_example.py` and `example_request.json`: the original OpenDecider/Laya examples and response-contract tools.
- `sources.json`, `VALIDATION.md` and `SHA256SUMS.txt`: reference index, actual packaging/test results and file-integrity manifest.

## Publishing the Markdown

In a Markdown preview, figures appear automatically at their image references. In a publishing editor that does not resolve local Markdown images, upload the corresponding PNG at each numbered caption. A local disk path is not a publicly hosted image URL. The standalone HTML is a visual reference for the intended placement.

## Fast local experiment

Update and restart the native Ollama app to **0.35 or later**. From this extracted directory:

```bash
ollama pull tev1:0.8b
bash examples_ollama/query.sh examples_ollama/paddle_request.json
python3 realtime/server.py --backend ollama --model tev1:0.8b
```

Open `http://127.0.0.1:8765`, warm up, then start. The Python bridge requires only the standard library (Python 3.10+); no game assets are fetched from the internet. Read **`realtime/README.md`** for model comparisons, exact timing rules, oMLX and OpenDecider backends, measurement export and security boundaries.

To inspect the game without any model:

```bash
python3 realtime/server.py --backend heuristic
```

The heuristic is visibly labeled and does not return fabricated probabilities. The ordinary oMLX chat backend is also explicitly labeled as a generative baseline, not native System One support.

## Native Ollama Python example

```bash
python3 -m venv .venv-ollama
source .venv-ollama/bin/activate
python -m pip install 'ollama==0.6.3'
python examples_ollama/systemone.py --model tev1:0.8b
```

`examples_ollama/triage_request.json` includes Choice, Noul and Score. `paddle_request.json` contains one game-action question. `query.sh` sends either JSON to the local API. Downloads and initial loading precede any steady-state timing claim.

## Original OpenDecider and Laya route

Use a separate native Apple Silicon Python environment:

```bash
python3 -m venv .venv-opendecider
source .venv-opendecider/bin/activate
python -m pip install --upgrade pip
python -m pip install 'opendecider[mlx,serve]==0.2.0'
python scripts/run_local.py
```

For the 4B MLX checkpoint:

```bash
python scripts/run_local.py --model manjunathshiva/opendecider-small-mlx-8bit
```

`--revision CHECKPOINT_COMMIT` pins the model. CPU-only experimentation can use `opendecider[serve]==0.2.0` and `--device cpu`. Package pins do not freeze all transitive dependencies or weights; record a validated environment.

The original authenticated loopback server and client remain available:

```bash
bash scripts/serve_local.sh
# In a second activated terminal:
python scripts/query_local.py
```

The secret is kept in `~/.config/local-decider/api.key`, outside the repository. `DECIDER_MODEL` and `DECIDER_REVISION` select a model/revision. `laya_example.py` is a separate example and requires its documented laya-mlx environment.

## Validation and limits

The package includes **49 passing model-free tests**: 16 original contract tests, 21 bridge/protocol tests and 12 JavaScript simulation tests. The earlier browser-game validation record used synthetic responses to inspect the UI, exports and delayed-response behavior. The model-free test suites have been rerun for this package. No real decision checkpoint was downloaded or evaluated, and no physical-Mac inference benchmark was performed.

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s realtime/tests -v
node --test realtime/tests/test_core.mjs
```

The normalizer distinguishes expected score, most-likely level and top probability; it does not transfer a provider's generic confidence field into an accuracy guarantee. These checks establish response-contract behavior, not calibration or task competence.

All local examples are advisory. The game only controls its own in-page paddle; the coding examples do not execute commands, apply patches or authorize production changes. No weights, credentials, ROMs or external game assets are included.
