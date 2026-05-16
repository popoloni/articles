#!/usr/bin/env zsh
# Regenerate Medium-friendly Markdown + JPEG assets from the LaTeX article.
#
# Usage:
#   ./medium_export/run_export.sh                       # default: main.tex
#   ./medium_export/run_export.sh path/to/other.tex     # custom input
#   KEEP_BUILD=1 ./medium_export/run_export.sh          # keep per-float .tex/.pdf

set -euo pipefail

# Resolve script location and project root regardless of cwd.
SCRIPT_DIR="${0:A:h}"
ARTICLE_DIR="${SCRIPT_DIR:h}"
PROJECT_ROOT="${ARTICLE_DIR:h}"

INPUT_TEX="${1:-main.tex}"
OUTPUT_DIR="${SCRIPT_DIR}/output"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
CONVERTER="${SCRIPT_DIR}/latex_to_medium.py"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python venv not found at $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -f "$CONVERTER" ]]; then
  echo "ERROR: Converter script not found at $CONVERTER" >&2
  exit 1
fi

cd "$ARTICLE_DIR"

if [[ ! -f "$INPUT_TEX" ]]; then
  echo "ERROR: Input .tex not found: $ARTICLE_DIR/$INPUT_TEX" >&2
  exit 1
fi

EXTRA_ARGS=()
if [[ "${KEEP_BUILD:-0}" == "1" ]]; then
  EXTRA_ARGS+=("--keep-build")
fi

echo "==> Article dir : $ARTICLE_DIR"
echo "==> Input       : $INPUT_TEX"
echo "==> Output dir  : $OUTPUT_DIR"
echo "==> Python      : $PYTHON_BIN"
echo

"$PYTHON_BIN" "$CONVERTER" \
  --input "$INPUT_TEX" \
  --output-dir "$OUTPUT_DIR" \
  "${EXTRA_ARGS[@]}"

SLUG="${INPUT_TEX:t:r}"
echo
echo "Done. Open: $OUTPUT_DIR/$SLUG/medium.md"
