#!/bin/bash
# Foreground, loopback-only server. Stop the GUI-managed Ollama process first.
set -euo pipefail
if ! command -v ollama >/dev/null 2>&1; then
  export PATH="/Applications/Ollama.app/Contents/Resources:$PATH"
fi
command -v ollama >/dev/null 2>&1 || { echo 'Install the native Ollama app first.' >&2; exit 1; }
if lsof -nP -iTCP:11434 -sTCP:LISTEN >/dev/null 2>&1; then
  echo 'Port 11434 is occupied. Quit the existing Ollama app/server, then retry.' >&2
  exit 1
fi
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_KEEP_ALIVE=2m
# Baseline deliberately does not force a backend, KV quantization or system RAM override.
exec ollama serve
