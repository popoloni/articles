#!/usr/bin/env python3
"""Paddle Lab: a loopback-only, dependency-free bridge to local decision models.

Run from any directory. The browser performs physics independently of inference.
The HTTP service has one inference slot, no retry queue, explicit endpoint selection,
strict output validation, and no access to an emulator or operating-system controls.
This is a development demo, not a hardened public web service.
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ACTIONS = ("up", "down", "stay")
MAX_BODY = 32 * 1024
MAX_RESPONSE = 256 * 1024
ROOT = Path(__file__).resolve().parent


def valid_number(value: object, lo: float, hi: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and lo <= value <= hi


def validate_request(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    for name in ("epoch", "seq"):
        if not isinstance(data.get(name), int) or isinstance(data[name], bool) or not 0 <= data[name] < 10**12:
            raise ValueError(f"Invalid {name}")
    if not valid_number(data.get("observed_at_ms"), 0, 10**15):
        raise ValueError("Invalid observation timestamp")
    state = data.get("state")
    if not isinstance(state, dict):
        raise ValueError("Missing state")
    fields = ("width", "height", "ball_x", "ball_y", "ball_vx", "ball_vy",
              "paddle_x", "paddle_y", "paddle_height", "paddle_speed")
    for field in fields:
        if not valid_number(state.get(field), -10000, 10000):
            raise ValueError(f"Invalid state field: {field}")
    if state["width"] <= 0 or state["height"] <= 0 or state["paddle_height"] <= 0:
        raise ValueError("Invalid geometry")
    # Forward only known fields. Never accept client-provided prompts or URLs.
    return {"epoch": data["epoch"], "seq": data["seq"], "observed_at_ms": data["observed_at_ms"],
            "state": {key: state[key] for key in fields}}


def question() -> dict:
    return {
        "type": "choice",
        "instructions": (
            "Control the left paddle in a ball-and-paddle game. Select the immediate "
            "vertical movement most likely to intercept the ball when it reaches the "
            "paddle. Coordinates are pixels; x increases right and y increases down. "
            "ball_vx and ball_vy are pixels per second. The ball reflects from the top, "
            "bottom and right walls. paddle_y is its centre. Do not assume future observations."
        ),
        "criteria": {
            "up": "Move the paddle upward, decreasing its y coordinate",
            "down": "Move the paddle downward, increasing its y coordinate",
            "stay": "Keep the paddle at its present vertical position",
        },
    }


def parse_decision_response(data: object) -> dict:
    if not isinstance(data, dict) or data.get("error") or data.get("warnings"):
        raise ValueError("Invalid response or server warning")
    answers = data.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("Expected answers object")
    answer = answers.get("move")
    if not isinstance(answer, dict) or answer.get("type") != "choice" or answer.get("truncated"):
        raise ValueError("Missing choice answer or truncated input")
    action = answer.get("choice")
    if action not in ACTIONS:
        raise ValueError("Unknown action")
    probs = answer.get("probabilities")
    if not isinstance(probs, dict) or set(probs) != set(ACTIONS):
        raise ValueError("Expected probabilities for exactly up/down/stay")
    if not all(valid_number(v, 0, 1) for v in probs.values()):
        raise ValueError("Non-finite or out-of-range probability")
    if abs(sum(probs.values()) - 1.0) > 0.015:
        raise ValueError("Probabilities do not sum approximately to one")
    if probs[action] + 0.002 < max(probs.values()):
        raise ValueError("Choice disagrees with probability argmax")
    return {"action": action, "probabilities": probs, "top_probability": probs[action],
            "reported_confidence": answer.get("confidence"), "kind": "typed-decision"}


def parse_chat_response(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Expected chat response object")
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing chat choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("Invalid chat choice")
    if first.get("finish_reason") != "stop":
        raise ValueError("Chat did not terminate normally")
    message = first.get("message", {})
    if not isinstance(message, dict):
        raise ValueError("Invalid chat message")
    if message.get("tool_calls"):
        raise ValueError("Tool calls are not allowed in this demo")
    content = message.get("content")
    action = content.strip().lower() if isinstance(content, str) else ""
    if action not in ACTIONS:
        raise ValueError("Chat must return exactly up, down, or stay; no prose")
    # A generated action is NOT a measured candidate probability distribution.
    return {"action": action, "probabilities": None, "top_probability": None,
            "reported_confidence": None, "kind": "generative-baseline"}


class LocalModel:
    def __init__(self, backend: str, model: str, endpoint: str, timeout: float,
                 api_key: str = "", constrain_output: bool = False):
        self.backend, self.model = backend, model
        self.timeout, self.api_key = timeout, api_key
        self.constrain_output = constrain_output
        url = urlsplit(endpoint)
        if url.scheme != "http" or url.username or url.password or url.query or url.fragment:
            raise ValueError("Use an http loopback endpoint without credentials/query/fragment")
        try:
            local = url.hostname == "localhost" or ipaddress.ip_address(url.hostname or "").is_loopback
        except ValueError:
            local = False
        if not local:
            raise ValueError("Only loopback model endpoints are allowed by this local demo")
        self.host, self.port, self.path = url.hostname, url.port or 80, url.path or "/"
        self.conn: http.client.HTTPConnection | None = None

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def decide(self, state: dict) -> dict:
        if self.backend == "heuristic":
            # Transparent tracking baseline; no intercept prediction, no model call.
            delta = state["ball_y"] - state["paddle_y"]
            action = "stay" if abs(delta) < state["paddle_height"] * .22 else ("down" if delta > 0 else "up")
            return {"action": action, "probabilities": None, "top_probability": None,
                    "reported_confidence": None, "kind": "heuristic-baseline"}
        if self.backend == "omlx-chat":
            q = question()
            payload = {"model": self.model, "temperature": 0, "max_tokens": 8,
                       "stream": False, "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [
                           {"role": "system", "content": q["instructions"] + " Reply only with up, down, or stay. No explanation."},
                           {"role": "user", "content": json.dumps(state, separators=(",", ":"))}]}
            if self.constrain_output:
                payload["structured_outputs"] = {"choice": list(ACTIONS)}
        else:
            payload = {"model": self.model, "state": state, "questions": {"move": question()}}
            if self.backend == "ollama":
                payload["keep_alive"] = "10m"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        try:
            if self.conn is None:
                self.conn = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)
            self.conn.request("POST", self.path, body=json.dumps(payload).encode(), headers=headers)
            response = self.conn.getresponse()
            body = response.read(MAX_RESPONSE + 1)
            if len(body) > MAX_RESPONSE:
                raise ValueError("Model response too large")
            if response.status != 200:
                raise ValueError(f"Model HTTP {response.status}: {body[:350].decode(errors='replace')}")
            data = json.loads(body)
            return parse_chat_response(data) if self.backend == "omlx-chat" else parse_decision_response(data)
        except Exception:
            # No automatic retry of an observation that may already be stale.
            self.close()
            raise


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, port: int, model: LocalModel, hz: float, max_age_ms: float):
        super().__init__(("127.0.0.1", port), Handler)
        self.model = model
        self.slot = threading.Lock()
        self.hz, self.max_age_ms = hz, max_age_ms
        self.request_count = 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: DemoServer

    def log_message(self, format: str, *args: object) -> None:
        # Do not log raw game state, model response text, or API keys.
        pass

    def same_origin(self) -> bool:
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origin = self.headers.get("Origin")
        return (self.headers.get("Host") in hosts and
                (origin is None or origin in {"http://" + host for host in hosts}) and
                self.headers.get("Sec-Fetch-Site", "same-origin") != "cross-site")

    def reply(self, status: int, body: bytes, mime: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json_reply(self, status: int, body: dict) -> None:
        self.reply(status, json.dumps(body, allow_nan=False).encode())

    def do_GET(self) -> None:
        if not self.same_origin():
            self.json_reply(403, {"error": "Loopback same-origin access required"}); return
        path = urlsplit(self.path).path
        if path == "/config":
            self.json_reply(200, {"backend": self.server.model.backend, "model": self.server.model.model,
                                  "decision_hz": self.server.hz, "max_age_ms": self.server.max_age_ms,
                                  "timeout_s": self.server.model.timeout,
                                  "constrain_output": self.server.model.constrain_output})
            return
        files = {"/": "index.html", "/game.js": "game.js", "/core.js": "core.js"}
        if path not in files:
            self.json_reply(404, {"error": "Not found"}); return
        name = files[path]
        self.reply(200, (ROOT / name).read_bytes(), "text/html; charset=utf-8" if name.endswith("html") else "text/javascript; charset=utf-8")

    def do_POST(self) -> None:
        if not self.same_origin():
            self.close_connection = True
            self.json_reply(403, {"error": "Cross-origin request rejected"}); return
        if self.path != "/decide":
            self.close_connection = True
            self.json_reply(404, {"error": "Not found"}); return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY or self.headers.get("Transfer-Encoding"):
                self.close_connection = True
                self.json_reply(413, {"error": "Invalid request length"}); return
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                self.close_connection = True
                self.json_reply(415, {"error": "Expected application/json"}); return
            self.connection.settimeout(5)
            request = validate_request(json.loads(self.rfile.read(size)))
        except (ValueError, TypeError, TimeoutError, json.JSONDecodeError) as error:
            self.close_connection = True
            self.json_reply(400, {"error": str(error)}); return
        if not self.server.slot.acquire(blocking=False):
            self.json_reply(429, {"error": "Inference already in flight; no request queue"}); return
        try:
            started = time.perf_counter()
            answer = self.server.model.decide(request["state"])
            answer.update({key: request[key] for key in ("seq", "epoch", "observed_at_ms")})
            answer["inference_ms"] = (time.perf_counter() - started) * 1000
            self.server.request_count += 1
            self.json_reply(200, answer)
        except Exception as error:
            self.json_reply(502, {"error": str(error)[:500]})
        finally:
            self.server.slot.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("ollama", "systemone", "omlx-chat", "heuristic"), default="ollama")
    parser.add_argument("--model", default="tev1:0.8b")
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--hz", type=float, default=5)
    parser.add_argument("--max-age-ms", type=float, default=500)
    parser.add_argument("--timeout", type=float, default=2)
    parser.add_argument("--key-env", default="LOCAL_DECIDER_API_KEY")
    parser.add_argument("--constrain-output", action="store_true", help="oMLX only: request grammar-constrained action output")
    args = parser.parse_args()
    if not 0 < args.hz <= 30 or not 10 <= args.max_age_ms <= 10000 or not .1 <= args.timeout <= 120:
        parser.error("Invalid rate, freshness deadline, or timeout")
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged TCP port")
    endpoint = args.endpoint or ("http://127.0.0.1:8000/v1/chat/completions" if args.backend == "omlx-chat"
                                 else "http://127.0.0.1:11434/v1/systemone")
    model = LocalModel(args.backend, args.model, endpoint, args.timeout,
                       os.environ.get(args.key_env, ""), args.constrain_output)
    server = DemoServer(args.port, model, args.hz, args.max_age_ms)
    print(f"Paddle Lab: http://127.0.0.1:{args.port}", flush=True)
    print(f"Backend={args.backend}; model={args.model}; max={args.hz:g} decisions/s; freshness={args.max_age_ms:g} ms", flush=True)
    print("Warm up before play. Model errors disable decision requests; physics continues with STAY. Ctrl-C exits.", flush=True)
    try:
        server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        model.close()


if __name__ == "__main__":
    main()
