#!/usr/bin/env bash
# Parameterized llama.cpp Metal server profile.
# Required: MODEL=/absolute/path/model.gguf
# Optional environment variables are listed in usage().

set -euo pipefail

find_binary() {
  if [[ -n "${LLAMA_SERVER_BIN:-}" ]]; then
    printf '%s' "$LLAMA_SERVER_BIN"
    return
  fi
  if command -v llama-server >/dev/null 2>&1; then
    command -v llama-server
    return
  fi
  for candidate in ./build/bin/llama-server ./llama-server; do
    if [[ -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return
    fi
  done
  echo "error: llama-server not found; set LLAMA_SERVER_BIN" >&2
  exit 2
}

usage() {
  cat <<'MSG'
Usage:
  MODEL=/path/model.gguf ./llamacpp_server.sh

Optional environment variables:
  LLAMA_SERVER_BIN     llama-server binary path
  HOST                 default 127.0.0.1
  PORT                 default 8080
  CONTEXT              default 16384
  PARALLEL             default 1
  BATCH                default 512
  UBATCH               default 128
  KV_TYPE              default q8_0, used for both K and V
  GPU_LAYERS           default all
  FLASH_ATTENTION      default auto
  CACHE_DIR            default ~/.cache/llama-slots
  CACHE_RAM_MIB        default 8192
  API_KEY              optional server API key
  EXTRA_ARGS           extra raw llama-server flags
  DRY_RUN              set to 1 to print only
MSG
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

: "${MODEL:?Set MODEL to an existing GGUF file}"
[[ -f "$MODEL" ]] || { echo "error: MODEL does not exist: $MODEL" >&2; exit 2; }

BIN="$(find_binary)"
: "${HOST:=127.0.0.1}"
: "${PORT:=8080}"
: "${CONTEXT:=16384}"
: "${PARALLEL:=1}"
: "${BATCH:=512}"
: "${UBATCH:=128}"
: "${KV_TYPE:=q8_0}"
: "${GPU_LAYERS:=all}"
: "${FLASH_ATTENTION:=auto}"
: "${CACHE_DIR:=$HOME/.cache/llama-slots}"
: "${CACHE_RAM_MIB:=8192}"
: "${API_KEY:=}"
: "${EXTRA_ARGS:=}"
: "${DRY_RUN:=0}"

mkdir -p "$CACHE_DIR"
HELP="$($BIN --help 2>&1 || true)"
ARGS=(-m "$MODEL")

supports() { grep -Fq -- "$1" <<<"$HELP"; }
add() { ARGS+=("$@"); }
add_if_supported() {
  local flag="$1"; shift
  if supports "$flag"; then
    add "$flag" "$@"
  else
    echo "warning: $flag is not exposed by this llama-server build; skipping" >&2
  fi
}

add_if_supported -ngl "$GPU_LAYERS"
add_if_supported -fa "$FLASH_ATTENTION"
add_if_supported -c "$CONTEXT"
add_if_supported -np "$PARALLEL"
if supports -cb; then add -cb; fi
add_if_supported -b "$BATCH"
add_if_supported -ub "$UBATCH"
add_if_supported -ctk "$KV_TYPE"
add_if_supported -ctv "$KV_TYPE"
add_if_supported -cram "$CACHE_RAM_MIB"
if supports --cache-idle-slots; then add --cache-idle-slots; fi
add_if_supported --slot-save-path "$CACHE_DIR"
if supports --metrics; then add --metrics; fi
add_if_supported --host "$HOST"
add_if_supported --port "$PORT"
if [[ -n "$API_KEY" ]]; then add_if_supported --api-key "$API_KEY"; fi

if [[ -n "$EXTRA_ARGS" ]]; then
  # Intentional word splitting for user-supplied CLI flags.
  # shellcheck disable=SC2206
  EXTRA=( $EXTRA_ARGS )
  ARGS+=("${EXTRA[@]}")
fi

printf 'Starting:'
printf ' %q' "$BIN" "${ARGS[@]}"
printf '\n'
[[ "$DRY_RUN" == "1" ]] && exit 0
exec "$BIN" "${ARGS[@]}"
