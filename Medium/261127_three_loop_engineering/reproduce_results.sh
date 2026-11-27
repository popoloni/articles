#!/usr/bin/env sh
# Regenerates everything under results/ from scratch (offline, deterministic).
set -eu
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
rm -rf results
mkdir -p results
"$PY" -m unittest discover -s tests -v > results/test_log.txt 2>&1
"$PY" -m three_loop demo --out results/replay > results/demo_stdout.json
APPROVAL=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["approval_digest"])' results/demo_stdout.json)
BASELINE=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["baseline_sha"])' results/demo_stdout.json)
"$PY" -m three_loop promote --run results/replay --approve "$APPROVAL" > results/promotion_stdout.json
"$PY" -m three_loop run-active --run results/replay --task holdout_invoice --out results/active_v2 > results/active_v2_stdout.json
"$PY" -m three_loop rollback --run results/replay --approve "$BASELINE" > results/rollback_stdout.json
find . -name __pycache__ -type d -exec rm -rf {} +
echo "results/ regenerated"
