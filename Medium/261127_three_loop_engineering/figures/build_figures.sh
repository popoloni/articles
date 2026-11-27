#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
for file in 01_architecture.dot 02_progress.dot 03_learning.dot; do
  dot -Tsvg "$file" -o "${file%.dot}.svg"
  dot -Tpng -Gdpi=160 "$file" -o "${file%.dot}.png"
done
"${PYTHON:-python3}" build_chart.py
