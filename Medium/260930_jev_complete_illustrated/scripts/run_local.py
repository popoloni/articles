#!/usr/bin/env python3
"""Run one local OpenDecider example. No tools are executed by this script."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from decision_contract import ContractError, normalize_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=Path(__file__).resolve().parents[1] / "example_request.json")
    parser.add_argument("--model", default="manjunathshiva/opendecider-nano")
    parser.add_argument("--revision", help="Pin a checkpoint commit/tag; omission uses its current revision.")
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], help="For PyTorch models; omit for MLX.")
    args = parser.parse_args()
    try:
        from opendecider import load
    except ImportError:
        print("Install opendecider==0.2.0 (or its mlx extra) in this environment first.", file=sys.stderr)
        return 2
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        if not isinstance(request, dict) or not isinstance(request.get("questions"), dict):
            raise ValueError("Request must contain state and a questions object.")
        if "state" not in request:
            raise ValueError("Missing state.")
        t0 = time.perf_counter()
        model = load(args.model, device=args.device, revision=args.revision)
        loaded = time.perf_counter()
        result = model.system_one(request["state"], request["questions"])
        finished = time.perf_counter()
        output = normalize_result(result, request["questions"])
        output["timing"] = {"load_seconds": loaded - t0,
                            "single_call_seconds": finished - loaded,
                            "note": "One call, not a benchmark or warmed latency estimate."}
        output["requested_revision"] = args.revision
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, ContractError) as exc:
        print(f"Local decision failed; no action authorized: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
