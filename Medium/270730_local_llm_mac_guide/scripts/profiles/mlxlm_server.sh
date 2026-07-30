#!/usr/bin/env bash
# Basic MLX-LM localhost server profile.
# Required: MODEL=<Hugging Face identifier or local MLX model directory>

set -euo pipefail

usage() {
  cat <<'MSG'
Usage:
  MODEL=mlx-community/<model>-4bit ./mlxlm_server.sh

Optional environment variables:
  MLX_LM_SERVER_BIN  default: mlx_lm.server
  HOST               default: 127.0.0.1
  PORT               default: 8080
  EXTRA_ARGS         extra raw mlx_lm.server flags
  DRY_RUN            set to 1 to print only

The MLX-LM server is a convenient local development endpoint, not a hardened
production security boundary. Keep it bound to localhost unless protected by
an authenticated reverse proxy and firewall policy.
MSG
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

: "${MODEL:?Set MODEL to an MLX model identifier or local directory}"
: "${MLX_LM_SERVER_BIN:=mlx_lm.server}"
: "${HOST:=127.0.0.1}"
: "${PORT:=8080}"
: "${EXTRA_ARGS:=}"
: "${DRY_RUN:=0}"

command -v "$MLX_LM_SERVER_BIN" >/dev/null 2>&1 || {
  echo "error: $MLX_LM_SERVER_BIN was not found; install mlx-lm or set MLX_LM_SERVER_BIN" >&2
  exit 2
}

HELP="$($MLX_LM_SERVER_BIN --help 2>&1 || true)"
ARGS=()
supports() { grep -Fq -- "$1" <<<"$HELP"; }

ARGS+=(--model "$MODEL")
if supports --host; then ARGS+=(--host "$HOST"); fi
if supports --port; then ARGS+=(--port "$PORT"); fi

if [[ -n "$EXTRA_ARGS" ]]; then
  # Intentional word splitting for user-supplied CLI flags.
  # shellcheck disable=SC2206
  EXTRA=( $EXTRA_ARGS )
  ARGS+=("${EXTRA[@]}")
fi

printf 'Starting:'
printf ' %q' "$MLX_LM_SERVER_BIN" "${ARGS[@]}"
printf '\n'
[[ "$DRY_RUN" == "1" ]] && exit 0
exec "$MLX_LM_SERVER_BIN" "${ARGS[@]}"
