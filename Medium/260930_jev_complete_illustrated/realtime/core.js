// Pure simulation and freshness rules: no DOM, network, or model dependency.
export const ACTIONS = Object.freeze(["up", "down", "stay"]);
export function acceptDecision(result, epoch, lastSeq, now, maxAge) {
  return !!result && ACTIONS.includes(result.action) && result.epoch === epoch &&
    Number.isInteger(result.seq) && result.seq > lastSeq &&
    Number.isFinite(result.observed_at_ms) && now >= result.observed_at_ms &&
    now - result.observed_at_ms <= maxAge;
}
export function activeAction(result, epoch, now, maxAge) {
  return result && result.epoch === epoch && now >= result.observed_at_ms &&
    now - result.observed_at_ms <= maxAge && ACTIONS.includes(result.action) ? result.action : "stay";
}
export function percentile(values, q) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.min(sorted.length - 1, Math.ceil(q * sorted.length) - 1))];
}
export class Game {
  constructor(seed = 42) { this.epoch = 0; this.reset(seed); }
  random() { this.rng = (1664525 * this.rng + 1013904223) >>> 0; return this.rng / 4294967296; }
  reset(seed = 42) {
    this.seed = seed >>> 0; this.rng = this.seed; this.width = 900; this.height = 500;
    this.paddleX = 30; this.paddleY = 250; this.paddleHeight = 108; this.paddleSpeed = 340;
    this.radius = 8; this.hits = 0; this.misses = 0; this.simTime = 0; this.frame = 0;
    this.serve();
  }
  serve() {
    this.epoch++; this.ballX = 690; this.ballY = 70 + this.random() * 360;
    this.ballVX = -240; this.ballVY = (this.random() < .5 ? -1 : 1) * (75 + this.random() * 80);
  }
  snapshot() {
    const r = n => Math.round(n * 10) / 10;
    return {width: this.width, height: this.height, ball_x: r(this.ballX), ball_y: r(this.ballY),
      ball_vx: r(this.ballVX), ball_vy: r(this.ballVY), paddle_x: this.paddleX,
      paddle_y: r(this.paddleY), paddle_height: this.paddleHeight, paddle_speed: this.paddleSpeed};
  }
  step(dt, action) {
    if (!Number.isFinite(dt) || dt < 0 || dt > .025) throw Error("Use small fixed physics steps");
    this.frame++; this.simTime += dt;
    const sign = action === "up" ? -1 : action === "down" ? 1 : 0;
    this.paddleY = Math.max(this.paddleHeight / 2, Math.min(this.height - this.paddleHeight / 2,
      this.paddleY + sign * this.paddleSpeed * dt));
    const oldX = this.ballX;
    this.ballX += this.ballVX * dt; this.ballY += this.ballVY * dt;
    if (this.ballY < this.radius) { this.ballY = 2 * this.radius - this.ballY; this.ballVY = Math.abs(this.ballVY); }
    if (this.ballY > this.height - this.radius) { this.ballY = 2 * (this.height - this.radius) - this.ballY; this.ballVY = -Math.abs(this.ballVY); }
    if (this.ballX > this.width - this.radius) { this.ballX = 2 * (this.width - this.radius) - this.ballX; this.ballVX = -Math.abs(this.ballVX); }
    const face = this.paddleX + 12 + this.radius;
    if (this.ballVX < 0 && oldX >= face && this.ballX < face && Math.abs(this.ballY - this.paddleY) <= this.paddleHeight / 2 + this.radius) {
      this.ballX = 2 * face - this.ballX; this.ballVX = Math.abs(this.ballVX); this.hits++;
    }
    if (this.ballX < -this.radius) { this.misses++; this.serve(); }
  }
}
