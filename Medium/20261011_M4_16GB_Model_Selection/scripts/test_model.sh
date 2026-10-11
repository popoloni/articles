#!/bin/bash
# One explicit endpoint/model pair. Does not start a server or execute tool calls.
set -euo pipefail
if [ "$#" -ne 3 ]; then
  echo 'Usage: bash scripts/test_model.sh BASE_URL EXACT_MODEL_ID RUN_LABEL' >&2
  exit 2
fi
BASE_URL="$1"; MODEL_ID="$2"; LABEL="$3"
case "$LABEL" in ''|*[!A-Za-z0-9_-]*) echo 'Run label must contain only letters, digits, - or _.' >&2; exit 2;; esac
PACKAGE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB="${LAB:-$HOME/LocalAI/qwen-bonsai-lab}"
PYTHON="$LAB/venv-tools/bin/python"
test -x "$PYTHON" || { echo 'Prepare venv-tools first.' >&2; exit 2; }
mkdir -p "$LAB/logs"
RUN_DIR="$(mktemp -d "$LAB/logs/${LABEL}-XXXXXX")"
printf 'Records for this invocation: %s\n' "$RUN_DIR"
printf '%s\n' "$BASE_URL" > "$RUN_DIR/endpoint.txt"
printf '%s\n' "$MODEL_ID" > "$RUN_DIR/model-id.txt"
"$PYTHON" "$PACKAGE/tools/compat_lab.py" --base-url "$BASE_URL" models > "$RUN_DIR/models.json"
cat "$RUN_DIR/models.json"
"$PYTHON" "$PACKAGE/tools/compat_lab.py" --base-url "$BASE_URL" --timeout 300 chat \
  --model "$MODEL_ID" --prompt 'Reply with READY and nothing else.' \
  --output-tokens 64 --out "$RUN_DIR/ready.txt"
"$PYTHON" - "$RUN_DIR/ready.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text(encoding='utf-8').strip()
if text != 'READY':
    print('Readiness was not exactly READY. Inspect the saved response and server before proceeding.', file=sys.stderr)
    raise SystemExit(1)
PY
printf 'Readiness passed. Running the original two contracts, three repetitions. No tools will execute.\n'
"$PYTHON" "$PACKAGE/tools/compat_lab.py" --base-url "$BASE_URL" --timeout 300 smoke \
  --model "$MODEL_ID" --repeats 3 --out "$RUN_DIR/smoke.jsonl"
printf 'Completed. Inspect %s and the server log; this is not a coding benchmark.\n' "$RUN_DIR"
