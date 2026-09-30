# Paddle Lab: real-time local decision experiment

An original single-paddle browser game, a dependency-free Python bridge, and explicit freshness rules. No ROMs, game downloads, emulator hooks, global key injection, or shell tools. It is a development experiment, not a benchmark certification or hardened network service.

## 1. Prepare Ollama

Use the native macOS Ollama app, version 0.35 or later. Restart it after updating; confirm the server version, not only the executable.

```bash
ollama --version
curl --fail -sS http://127.0.0.1:11434/api/version
ollama pull tev1:0.8b
```

From the top-level extracted package directory, warm the model before starting the game:

```bash
bash examples_ollama/query.sh examples_ollama/paddle_request.json
python3 realtime/server.py --backend ollama --model tev1:0.8b
```

Open `http://127.0.0.1:8765`, click **Warm up model**, then **Start / pause**. A Python 3.10+ installation and a current browser are sufficient for the bridge; no pip dependencies are needed. Internet access is needed for model downloads, not for the game assets.

The default is at most 5 decisions/s with a 500 ms maximum observation age. The network timeout is 2 seconds; the shorter freshness timer already makes an expired action neutral while that request is pending. Cold model loading may exceed 2 seconds, hence the manual warm-up. A failed service call disables new requests; click Warm up to recover after fixing the service. The game never silently invokes a cloud fallback.

## 2. Compare models and tighter timing

After downloading a model, restart the bridge with the matching name:

```bash
ollama pull tev1:4b
python3 realtime/server.py --backend ollama --model tev1:4b
```

Other choices are `nimble` and `nimble:9b-q4_K_M`. Unload unused models with `ollama stop MODEL` when memory is tight. The supplied warm-up JSON defaults to Tev1 0.8B; change its `model` field for another model, or warm the selected model with an equivalent API call first.

```bash
python3 realtime/server.py --backend ollama --model tev1:0.8b \
  --hz 10 --max-age-ms 250
```

These are test settings, not promised throughput. Shorter deadlines can cause every answer to be discarded. That is a valid latency result; it should not be concealed by slowing the physics clock. The model sees positions and velocities; no hidden program predicts the interception point for it.

## 3. No-model baseline

```bash
python3 realtime/server.py --backend heuristic
```

This controller tracks the current ball height with a dead zone, not a future-trajectory solver. It uses no model and reports no probabilities. The UI also supports manual up/down arrow control. Apply the same seeds, run lengths, and requested decision rates for comparisons.

## 4. oMLX chat baseline — not native System One

Start a supported ordinary instruction model in oMLX, with a short context and no thinking for this experiment. Use its exact model ID. With authentication enabled, set the local secret outside the repository:

```bash
export LOCAL_DECIDER_API_KEY="YOUR_LOCAL_OMLX_KEY"
python3 realtime/server.py --backend omlx-chat --model local-small \
  --endpoint http://127.0.0.1:8000/v1/chat/completions
```

Add `--constrain-output` to request `structured_outputs.choice` when the installed oMLX backend supports it. The bridge requires a completed answer containing only `up`, `down`, or `stay`; it rejects prose, truncation and tool calls. It intentionally provides **no probability distribution** for chat results. This does not demonstrate Nimble/Tev1's specialized scoring in oMLX.

The API key remains in the Python process. It is never embedded into game JavaScript or exported measurements. Stop and restart the bridge after changing a backend.

## 5. Existing OpenDecider HTTP service

Using the service from the original essay:

```bash
export LOCAL_DECIDER_API_KEY="$(cat "$HOME/.config/local-decider/api.key")"
python3 realtime/server.py --backend systemone \
  --model manjunathshiva/opendecider-nano \
  --endpoint http://127.0.0.1:8011/v1/systemone
```

The generic System One path omits Ollama's `keep_alive` option. Other servers must support the same Choice response contract. A Laya/MLX endpoint with a different schema needs a deliberate adapter; it is not interchangeable merely because it returns decisions.

## Timing and failure semantics

The browser updates physics at fixed 1/120-second steps inside its animation loop, independently of asynchronous inference. Rendering follows the display's animation cadence. The model loop is separately rate-limited. There is at most one request in flight, and no FIFO backlog of old observations. A fresh snapshot is taken when the worker becomes available.

The maximum action age is measured from **observation capture**, not response arrival. Sequence number, round identifier, capture timestamp, candidate validity and expiry are checked. Resetting, pausing, switching controls or starting a new ball invalidates old replies. Resetting a run also prevents pending responses from contaminating the new measurement series.

A missing, expired or failed action becomes `stay`. No heuristic silently replaces an AI decision. Model errors disable additional inference until explicitly warmed again; physics continues. Backgrounding the browser tab explicitly pauses the run. A severe browser stall can drop simulation catch-up time to avoid an unbounded catch-up loop, and that lost time is disclosed in exported metrics.

The live confidence bars display candidate probabilities, not a win forecast. The bridge retains the backend's reported confidence separately; it does not equate confidence, winning probability or empirical correctness.

## Measurements

Click **Export measurements** to save a JSON record. It contains backend identity, parameters, seed, snapshots and decisions, HTTP p50/p95, accepted/discarded responses, errors, returns/misses, fallback time, simulation time, active wall-clock time and dropped simulation time. Warm-up is excluded. UI logs are kept in memory; only an explicit export writes the report.

Fill in the machine, RAM, model digest and actual runtime version before publication. The history retains at most 10,000 successful-response records; long sessions should be split into explicit runs. Compare repeated seeded runs. Do not substitute a screenshot of 60 rendering FPS for model decision throughput.

## Validation

```bash
# From the package root; these require no models.
python3 -m unittest discover -s realtime/tests -v
node --test realtime/tests/test_core.mjs
```

The package was checked using 21 Python bridge/protocol tests, 12 JavaScript simulation/freshness tests, and the original 16 decision-contract tests. A headless browser exercise used synthetic fetch responses, including deliberately late replies; it verified continued simulation and stale-response rejection. **No actual model was run in the game and no Mac performance numbers were measured.**

For security, the bridge binds to loopback, validates Host/Origin, rejects cross-site browser requests, caps body size, accepts only predefined state fields, and permits only explicit loopback model URLs. These checks do not make it a public-facing hardened server. Do not expose it through a tunnel or reverse proxy without a separate security design.
