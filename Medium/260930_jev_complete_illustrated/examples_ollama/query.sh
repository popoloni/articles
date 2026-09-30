#!/usr/bin/env bash
# Ollama must already be running. This does not start or expose a new server.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REQUEST="${1:-$HERE/triage_request.json}"
if [ ! -r "$REQUEST" ]; then printf 'Cannot read request: %s\n' "$REQUEST" >&2; exit 2; fi
curl --fail-with-body --max-time 120 -sS \
  http://127.0.0.1:11434/v1/systemone \
  -H 'Content-Type: application/json' \
  --data-binary "@$REQUEST"
printf '\n'
