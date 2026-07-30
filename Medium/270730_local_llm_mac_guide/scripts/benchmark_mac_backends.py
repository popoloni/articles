#!/usr/bin/env python3
"""Benchmark local Mac LLM endpoints without third-party dependencies.

Supports:
  * Ollama native /api/chat streaming (NDJSON)
  * OpenAI-compatible /v1/chat/completions streaming (SSE)

The script measures client-observed TTFT and total latency. For Ollama it also
captures the authoritative token/duration counters from the final response.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


@dataclass
class Sample:
    provider: str
    concurrency: int
    prompt_index: int
    repetition: int
    ok: bool
    error: str | None
    ttft_s: float | None
    total_s: float | None
    chunks: int
    output_chars: int
    output_tokens: int | None
    prompt_tokens: int | None
    server_prompt_eval_s: float | None
    server_eval_s: float | None
    server_load_s: float | None
    server_total_s: float | None
    client_post_first_chars_per_s: float | None
    server_output_tokens_per_s: float | None


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def load_prompts(path: Path) -> list[str]:
    prompts: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if isinstance(obj, str):
            prompt = obj
        elif isinstance(obj, dict) and isinstance(obj.get("prompt"), str):
            prompt = obj["prompt"]
        else:
            raise ValueError(f"{path}:{line_no}: expected a JSON string or {{'prompt': ...}}")
        prompts.append(prompt)
    if not prompts:
        raise ValueError(f"No prompts found in {path}")
    return prompts


def post_stream(url: str, payload: dict[str, Any], timeout: float, headers: dict[str, str]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=timeout)


def iter_ollama_chunks(resp: Any) -> Iterator[dict[str, Any]]:
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            yield json.loads(line)


def iter_sse_data(resp: Any) -> Iterator[dict[str, Any]]:
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        yield json.loads(data)


def ollama_sample(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    num_ctx: int | None,
    keep_alive: str,
    timeout: float,
    concurrency: int,
    prompt_index: int,
    repetition: int,
) -> Sample:
    url = base_url.rstrip("/") + "/api/chat"
    options: dict[str, Any] = {"num_predict": max_tokens, "temperature": 0.0}
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "keep_alive": keep_alive,
        "options": options,
    }
    start = time.perf_counter()
    first: float | None = None
    output_parts: list[str] = []
    chunks = 0
    final: dict[str, Any] = {}
    try:
        with post_stream(url, payload, timeout, {"Content-Type": "application/json"}) as resp:
            for obj in iter_ollama_chunks(resp):
                final = obj
                content = (obj.get("message") or {}).get("content") or ""
                if content:
                    chunks += 1
                    output_parts.append(content)
                    if first is None:
                        first = time.perf_counter()
        end = time.perf_counter()
    except Exception as exc:  # keep benchmark running across failed samples
        end = time.perf_counter()
        return Sample("ollama", concurrency, prompt_index, repetition, False, repr(exc), None,
                      end - start, chunks, sum(map(len, output_parts)), None, None, None, None,
                      None, None, None, None)

    out = "".join(output_parts)
    ttft = None if first is None else first - start
    post_first_rate = None
    if first is not None and end > first:
        post_first_rate = len(out) / (end - first)

    def ns_to_s(key: str) -> float | None:
        value = final.get(key)
        return value / 1e9 if isinstance(value, (int, float)) else None

    eval_count = final.get("eval_count")
    eval_s = ns_to_s("eval_duration")
    server_tps = None
    if isinstance(eval_count, int) and eval_s and eval_s > 0:
        server_tps = eval_count / eval_s

    return Sample(
        "ollama", concurrency, prompt_index, repetition, True, None, ttft, end - start,
        chunks, len(out), eval_count if isinstance(eval_count, int) else None,
        final.get("prompt_eval_count") if isinstance(final.get("prompt_eval_count"), int) else None,
        ns_to_s("prompt_eval_duration"), eval_s, ns_to_s("load_duration"),
        ns_to_s("total_duration"), post_first_rate, server_tps,
    )


def openai_sample(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
    concurrency: int,
    prompt_index: int,
    repetition: int,
) -> Sample:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stream_options": {"include_usage": True},
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    start = time.perf_counter()
    first: float | None = None
    output_parts: list[str] = []
    chunks = 0
    usage: dict[str, Any] = {}
    try:
        with post_stream(url, payload, timeout, headers) as resp:
            for obj in iter_sse_data(resp):
                if isinstance(obj.get("usage"), dict):
                    usage = obj["usage"]
                choices = obj.get("choices") or []
                for choice in choices:
                    delta = choice.get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        chunks += 1
                        output_parts.append(content)
                        if first is None:
                            first = time.perf_counter()
        end = time.perf_counter()
    except Exception as exc:
        end = time.perf_counter()
        return Sample("openai", concurrency, prompt_index, repetition, False, repr(exc), None,
                      end - start, chunks, sum(map(len, output_parts)), None, None, None, None,
                      None, None, None, None)

    out = "".join(output_parts)
    ttft = None if first is None else first - start
    rate = None
    if first is not None and end > first:
        rate = len(out) / (end - first)
    completion_tokens = usage.get("completion_tokens")
    prompt_tokens = usage.get("prompt_tokens")

    return Sample(
        "openai", concurrency, prompt_index, repetition, True, None, ttft, end - start,
        chunks, len(out), completion_tokens if isinstance(completion_tokens, int) else None,
        prompt_tokens if isinstance(prompt_tokens, int) else None,
        None, None, None, None, rate, None,
    )


def summarize(samples: list[Sample], wall_s: float) -> dict[str, Any]:
    good = [s for s in samples if s.ok]
    def vals(name: str) -> list[float]:
        return [float(v) for s in good if (v := getattr(s, name)) is not None]

    output_tokens = sum(s.output_tokens or 0 for s in good)
    return {
        "requests": len(samples),
        "successful": len(good),
        "failed": len(samples) - len(good),
        "wall_s": wall_s,
        "aggregate_output_tokens_per_s": output_tokens / wall_s if output_tokens and wall_s > 0 else None,
        "aggregate_output_chars_per_s": sum(s.output_chars for s in good) / wall_s if wall_s > 0 else None,
        "ttft_s": stats(vals("ttft_s")),
        "total_s": stats(vals("total_s")),
        "server_output_tokens_per_s": stats(vals("server_output_tokens_per_s")),
        "client_post_first_chars_per_s": stats(vals("client_post_first_chars_per_s")),
    }


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "p95": None, "p99": None, "min": None, "max": None}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "min": min(values),
        "max": max(values),
    }


def parse_concurrency(raw: str) -> list[int]:
    result: list[int] = []
    for part in raw.split(","):
        value = int(part.strip())
        if value < 1:
            raise argparse.ArgumentTypeError("concurrency must be >= 1")
        result.append(value)
    return result


def run_level(args: argparse.Namespace, prompts: list[str], concurrency: int) -> tuple[list[Sample], float]:
    jobs: list[tuple[int, int, str]] = []
    for repetition in range(args.repetitions):
        for prompt_index, prompt in enumerate(prompts):
            jobs.append((prompt_index, repetition, prompt))

    lock = threading.Lock()
    completed = 0
    start = time.perf_counter()
    samples: list[Sample] = []

    def call(job: tuple[int, int, str]) -> Sample:
        prompt_index, repetition, prompt = job
        if args.provider == "ollama":
            return ollama_sample(args.base_url, args.model, prompt, args.max_tokens, args.num_ctx,
                                  args.keep_alive, args.timeout, concurrency, prompt_index, repetition)
        return openai_sample(args.base_url, args.api_key, args.model, prompt, args.max_tokens,
                             args.timeout, concurrency, prompt_index, repetition)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(call, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            sample = future.result()
            samples.append(sample)
            with lock:
                completed += 1
                status = "ok" if sample.ok else "FAIL"
                print(f"[c={concurrency}] {completed}/{len(jobs)} {status} "
                      f"ttft={sample.ttft_s!s} total={sample.total_s!s}", file=sys.stderr)
    return samples, time.perf_counter() - start


def warmup(args: argparse.Namespace, prompt: str) -> None:
    print("Running warmup...", file=sys.stderr)
    if args.provider == "ollama":
        sample = ollama_sample(args.base_url, args.model, prompt, min(32, args.max_tokens),
                                args.num_ctx, args.keep_alive, args.timeout, 1, 0, -1)
    else:
        sample = openai_sample(args.base_url, args.api_key, args.model, prompt,
                               min(32, args.max_tokens), args.timeout, 1, 0, -1)
    if not sample.ok:
        raise RuntimeError(f"Warmup failed: {sample.error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ollama", "openai"), required=True)
    parser.add_argument("--base-url", required=True,
                        help="Ollama root (e.g. http://127.0.0.1:11434) or OpenAI /v1 root")
    parser.add_argument("--api-key", default="", help="Bearer token for OpenAI-compatible endpoint")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--concurrency", type=parse_concurrency, default=[1],
                        help="Comma-separated levels, e.g. 1,2,4")
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--num-ctx", type=int, default=None, help="Ollama native API only")
    parser.add_argument("--keep-alive", default="30m", help="Ollama native API only")
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.repetitions < 1 or args.max_tokens < 1:
        parser.error("repetitions and max-tokens must be >= 1")

    prompts = load_prompts(args.prompts)
    if not args.no_warmup:
        warmup(args, prompts[0])

    all_results: dict[str, Any] = {
        "configuration": {
            "provider": args.provider,
            "base_url": args.base_url,
            "model": args.model,
            "prompts": str(args.prompts),
            "prompt_count": len(prompts),
            "concurrency": args.concurrency,
            "repetitions": args.repetitions,
            "max_tokens": args.max_tokens,
            "num_ctx": args.num_ctx,
            "keep_alive": args.keep_alive,
            "timeout": args.timeout,
        },
        "levels": {},
    }

    for concurrency in args.concurrency:
        samples, wall = run_level(args, prompts, concurrency)
        all_results["levels"][str(concurrency)] = {
            "summary": summarize(samples, wall),
            "samples": [asdict(s) for s in sorted(samples, key=lambda x: (x.repetition, x.prompt_index))],
        }
        print(json.dumps({"concurrency": concurrency,
                          "summary": all_results["levels"][str(concurrency)]["summary"]}, indent=2))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, urllib.error.URLError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
