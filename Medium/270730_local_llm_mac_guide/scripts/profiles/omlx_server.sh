#!/usr/bin/env bash
# Parameterized oMLX serving profile for Apple Silicon.
# The script checks the installed CLI help and skips unavailable version-specific flags.

set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  ./omlx_server.sh

Optional environment variables:
  OMLX_BIN                 default: omlx
  MODEL_DIR                default: ~/models/mlx
  CACHE_DIR                default: ~/.omlx/cache
  MEMORY_GUARD             default: safe
  HOT_CACHE_MAX_SIZE       default: 20%
  MAX_CONCURRENT_REQUESTS  default: 4
  HOST                     default: 127.0.0.1
  PORT                     default: 8000
  EXTRA_ARGS               extra raw oMLX serve flags
  DRY_RUN                  set to 1 to print only

DFlash and TurboQuant KV are per-model settings. Configure them in the oMLX
admin UI or the version-matched model_settings.json after starting the server.
MSG
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

: "${OMLX_BIN:=omlx}"
command -v "$OMLX_BIN" >/dev/null 2>&1 || {
  echo "error: omlx was not found; set OMLX_BIN" >&2
  exit 2
}
: "${MODEL_DIR:=$HOME/models/mlx}"
: "${CACHE_DIR:=$HOME/.omlx/cache}"
: "${MEMORY_GUARD:=safe}"
: "${HOT_CACHE_MAX_SIZE:=20%}"
: "${MAX_CONCURRENT_REQUESTS:=4}"
: "${HOST:=127.0.0.1}"
: "${PORT:=8000}"
: "${EXTRA_ARGS:=}"
: "${DRY_RUN:=0}"

mkdir -p "$MODEL_DIR" "$CACHE_DIR"
HELP="$($OMLX_BIN serve --help 2>&1 || true)"
ARGS=(serve)

supports() { grep -Fq -- "$1" <<<"$HELP"; }
add_if_supported() {
  local flag="$1" value="$2"
  if supports "$flag"; then
    ARGS+=("$flag" "$value")
  else
    echo "warning: $flag is not exposed by this oMLX version; skipping" >&2
  fi
}

add_if_supported --model-dir "$MODEL_DIR"
add_if_supported --memory-guard "$MEMORY_GUARD"
add_if_supported --paged-ssd-cache-dir "$CACHE_DIR"
add_if_supported --hot-cache-max-size "$HOT_CACHE_MAX_SIZE"
add_if_supported --max-concurrent-requests "$MAX_CONCURRENT_REQUESTS"
add_if_supported --host "$HOST"
add_if_supported --port "$PORT"

if [[ -n "$EXTRA_ARGS" ]]; then
  # Intentional word splitting for user-supplied CLI flags.
  # shellcheck disable=SC2206
  EXTRA=( $EXTRA_ARGS )
  ARGS+=("${EXTRA[@]}")
fi

printf 'Starting:'
printf ' %q' "$OMLX_BIN" "${ARGS[@]}"
printf '\n'
printf 'Admin UI (typical): http://%s:%s/admin\n' "$HOST" "$PORT"
[[ "$DRY_RUN" == "1" ]] && exit 0
exec "$OMLX_BIN" "${ARGS[@]}"
