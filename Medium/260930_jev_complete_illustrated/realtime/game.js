import { Game, ACTIONS, acceptDecision, activeAction, percentile } from "./core.js";
const $ = id => document.getElementById(id);
const game = new Game(42), canvas = $("game"), ctx = canvas.getContext("2d");
const config = await fetch("/config").then(r => { if (!r.ok) throw Error("Config unavailable"); return r.json(); });
$("meta").textContent = `${config.backend} · ${config.model} · requested ≤ ${config.decision_hz} Hz · freshness ${config.max_age_ms} ms · local bridge only`;
let paused = true, busy = false, fault = false, warm = false;
let current = null, seq = 0, lastSeq = -1, due = 0, runGeneration = 0, measurementRun = 0;
let accepted = 0, discarded = 0, errors = 0, changes = 0, expiredSeconds = 0;
let records = [], latencies = [], droppedSeconds = 0, last = performance.now(), accumulator = 0;
let fpsFrames = 0, fpsStart = last, fps = 0, completedWindow = 0, decisionsPerSecond = 0;
let keys = new Set(), shownAction = "stay", lastStatus = 0, runStart = null, activeWallSeconds = 0;
const setStatus = text => { $("status").textContent = text; };
function clearAction() { current = null; game.epoch++; runGeneration++; }
function probabilities(result) {
  $("probabilities").replaceChildren();
  if (!result.probabilities) { $("probabilities").textContent = `${result.kind}: no candidate probabilities supplied.`; return; }
  for (const action of ACTIONS) {
    const p = result.probabilities[action];
    const row = document.createElement("div"); row.className = "bar-label";
    const label = document.createElement("span"), value = document.createElement("span");
    label.textContent = action.toUpperCase(); value.textContent = `${(100 * p).toFixed(1)}%`;
    row.append(label, value);
    const bar = document.createElement("div"); bar.className = "bar";
    const fill = document.createElement("i"); fill.style.width = `${p * 100}%`; bar.append(fill);
    $("probabilities").append(row, bar);
  }
}
async function requestDecision(isWarm = false) {
  if (busy) return;
  busy = true;
  const captured = performance.now(), generation = runGeneration, measuredRun = measurementRun;
  const packet = {seq: ++seq, epoch: game.epoch, observed_at_ms: captured, state: game.snapshot()};
  const timer = new AbortController();
  // The freshness deadline is shorter than this network guard; it never freezes rendering.
  const abort = setTimeout(() => timer.abort(), (isWarm ? 125 : config.timeout_s + 3) * 1000);
  try {
    const response = await fetch("/decide", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(packet), signal: timer.signal});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || `HTTP ${response.status}`);
    const now = performance.now(), elapsed = now - captured;
    if (measuredRun !== measurementRun) return; // Do not contaminate a newly reset run.
    if (isWarm) {
      warm = true; fault = false;
      setStatus(`Warm-up completed in ${elapsed.toFixed(0)} ms (not a benchmark). Start a run to measure steady state.`);
      probabilities(result);
    } else {
      completedWindow++; latencies.push(elapsed);
      const usable = !paused && $("mode").value === "model" && generation === runGeneration &&
        result.seq === packet.seq && result.observed_at_ms === captured &&
        acceptDecision(result, game.epoch, lastSeq, now, config.max_age_ms);
      if (usable) {
        accepted++; lastSeq = result.seq;
        if (current && current.action !== result.action) changes++;
        current = result; probabilities(result);
        setStatus(`Accepted decision ${result.seq}; state age ${elapsed.toFixed(0)} ms; backend ${result.inference_ms.toFixed(0)} ms. Remaining lifetime: ${Math.max(0, config.max_age_ms - elapsed).toFixed(0)} ms.`);
      } else {
        discarded++;
        setStatus(`Discarded decision ${result.seq}: stale state, superseded round, or paused run. No old action is applied.`);
      }
      records.push({packet, result, http_ms: elapsed, accepted: usable, response_at_ms: now});
      if (records.length > 10000) records.shift();
    }
  } catch (error) {
    if (measuredRun !== measurementRun) return;
    fault = true; current = null;
    if (!isWarm) { errors++; records.push({packet, error: String(error)}); }
    setStatus(`Decision service error: ${error.message}. New model requests are disabled. STAY is the fallback. Warm up again to recover.`);
  } finally {
    clearTimeout(abort); busy = false; $("warm").disabled = false;
  }
}
$("warm").addEventListener("click", () => {
  if (busy) return;
  paused = true; clearAction(); $("warm").disabled = true;
  setStatus("Warming up. A cold model may take longer than the request timeout; start it with a manual request first.");
  requestDecision(true);
});
$("start").addEventListener("click", () => {
  if ($("mode").value === "model" && (!warm || fault)) { setStatus("Warm up successfully before model-controlled play."); return; }
  paused = !paused; clearAction(); due = performance.now();
  if (runStart === null) runStart = new Date().toISOString();
  setStatus(paused ? "Paused; pending decisions will not be applied." : "Running in wall-clock time. Inference does not stop the game.");
});
$("reset").addEventListener("click", () => {
  paused = true; clearAction(); measurementRun++; game.reset(Number($("seed").value));
  accepted = discarded = errors = changes = 0; expiredSeconds = 0; droppedSeconds = 0;
  records = []; latencies = []; accumulator = 0; activeWallSeconds = 0; runStart = null;
  setStatus("New seeded run. Start when ready; a previous round's response is invalid.");
});
$("mode").addEventListener("change", () => { paused = true; clearAction(); setStatus("Control mode changed. Start to continue."); });
window.addEventListener("keydown", e => { if (["ArrowUp", "ArrowDown"].includes(e.key)) { e.preventDefault(); keys.add(e.key); } });
window.addEventListener("keyup", e => keys.delete(e.key));
window.addEventListener("blur", () => keys.clear());
document.addEventListener("visibilitychange", () => {
  if (document.hidden) { paused = true; clearAction(); setStatus("Paused because the tab is hidden; not counted as real-time play."); }
});
$("export").addEventListener("click", () => {
  const report = {format_version: 1, note: "Local run only; model scores are not win probabilities. Fill in hardware details before publishing.",
    created_at: new Date().toISOString(), run_start: runStart, backend: config, browser: navigator.userAgent,
    hardware: {machine: "FILL IN", ram_gb: null, runtime_version: "FILL IN", model_digest: "FILL IN"},
    seed: game.seed, control_mode: $("mode").value,
    metrics: {simulation_seconds: game.simTime, active_wall_seconds: activeWallSeconds, dropped_simulation_seconds: droppedSeconds,
      returns: game.hits, misses: game.misses, accepted, discarded, errors, action_changes: changes,
      neutral_fallback_seconds: expiredSeconds, http_p50_ms: percentile(latencies, .5), http_p95_ms: percentile(latencies, .95)},
    records};
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: "application/json"}));
  const a = document.createElement("a"); a.href = url; a.download = `paddle-lab-${config.backend}-${Date.now()}.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
function draw(now) {
  ctx.fillStyle = "#0a101c"; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#20334c"; ctx.lineWidth = 1; ctx.setLineDash([6, 12]);
  ctx.beginPath(); ctx.moveTo(450, 20); ctx.lineTo(450, 480); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = "#6de1c0"; ctx.fillRect(game.paddleX, game.paddleY - game.paddleHeight / 2, 12, game.paddleHeight);
  ctx.fillStyle = "#f5ba70"; ctx.beginPath(); ctx.arc(game.ballX, game.ballY, game.radius, 0, Math.PI * 2); ctx.fill();
  ctx.font = "13px ui-monospace, monospace"; ctx.fillStyle = "#9badc4";
  ctx.fillText("LEFT PADDLE · UP / DOWN / STAY", 25, 25);
  ctx.fillText(`ROUND ${game.epoch}   SIM ${game.simTime.toFixed(1)}s`, 645, 25);
  if (paused) {
    ctx.fillStyle = "rgba(10,16,28,.7)"; ctx.fillRect(0, 185, 900, 125);
    ctx.textAlign = "center"; ctx.fillStyle = "#eaf1fa"; ctx.font = "28px system-ui, sans-serif";
    ctx.fillText("PAUSED", 450, 240); ctx.font = "15px system-ui, sans-serif";
    ctx.fillStyle = "#9badc4"; ctx.fillText("Warm up the model, then start the clock.", 450, 273); ctx.textAlign = "left";
  }
  if (now - lastStatus > 200) {
    lastStatus = now;
    $("score").textContent = `${game.hits} / ${game.misses}`;
    const p50 = percentile(latencies, .5), p95 = percentile(latencies, .95);
    $("latency").textContent = p50 === null ? "—" : `${p50.toFixed(0)} / ${p95.toFixed(0)} ms`;
    $("counts").textContent = `${accepted} / ${discarded}`;
    $("action").textContent = shownAction.toUpperCase(); $("rates").textContent = `${fps.toFixed(0)} / ${decisionsPerSecond.toFixed(1)}`;
  }
}
function tick(now) {
  const realDt = Math.max(0, (now - last) / 1000); last = now;
  fpsFrames++;
  if (now - fpsStart >= 1000) {
    const elapsed = (now - fpsStart) / 1000;
    fps = fpsFrames / elapsed; decisionsPerSecond = completedWindow / elapsed;
    fpsFrames = 0; completedWindow = 0; fpsStart = now;
  }
  if (!paused) {
    activeWallSeconds += realDt;
    // Avoid a spiral after a blocked browser event loop, but disclose time lost.
    const dt = Math.min(realDt, .1); droppedSeconds += realDt - dt; accumulator += dt;
    const mode = $("mode").value;
    shownAction = mode === "manual" ? (keys.has("ArrowUp") ? "up" : keys.has("ArrowDown") ? "down" : "stay")
      : activeAction(current, game.epoch, now, config.max_age_ms);
    if (mode === "model" && (!current || current.epoch !== game.epoch || now - current.observed_at_ms > config.max_age_ms)) expiredSeconds += dt;
    while (accumulator >= 1 / 120) {
      game.step(1 / 120, shownAction); accumulator -= 1 / 120;
      if (current && current.epoch !== game.epoch) { current = null; shownAction = "stay"; }
    }
    if (mode === "model" && !busy && !fault && now >= due) {
      due = now + 1000 / config.decision_hz;
      requestDecision(false);
    }
  } else { accumulator = 0; shownAction = "stay"; }
  draw(now); requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
