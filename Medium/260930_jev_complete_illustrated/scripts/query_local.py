#!/usr/bin/env python3
"""Query the loopback decision server and validate an advisory-only response."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from decision_contract import ContractError, normalize_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=Path(__file__).resolve().parents[1] / "example_request.json")
    args = parser.parse_args()
    try:
        key = os.environ.get("OPENDECIDER_API_KEY", "")
        if not key:
            key = (Path.home() / ".config/local-decider/api.key").read_text().strip()
        if not key:
            raise ValueError("Missing local API key.")
        body = json.loads(args.request.read_text())
        req = urllib.request.Request("http://127.0.0.1:8011/v1/systemone",
            data=json.dumps(body, allow_nan=False).encode(), method="POST",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        # Never send loopback traffic through an environment-configured HTTP proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=40) as response:
            data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError("Unexpectedly large response.")
        result = json.loads(data)
        print(json.dumps(normalize_result(result, body["questions"]), indent=2,
                         ensure_ascii=False, allow_nan=False))
        return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}; no decision authorized.", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, ContractError) as exc:
        print(f"Decision request failed; no action authorized: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
