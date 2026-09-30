#!/usr/bin/env bash
# Local-only OpenDecider server. Never opens a public interface.
set -euo pipefail
command -v opendecider >/dev/null || { echo 'Activate the environment with opendecider[serve]==0.2.0 installed.' >&2; exit 2; }
command -v python >/dev/null || { echo 'Python is required.' >&2; exit 2; }
umask 077
KEY_DIR="$HOME/.config/local-decider"
KEY_FILE="$KEY_DIR/api.key"
mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"
if [ -L "$KEY_FILE" ]; then echo 'Refusing a symlink as the API key file.' >&2; exit 2; fi
if [ ! -s "$KEY_FILE" ]; then
  python -c 'import secrets; print(secrets.token_hex(32))' > "$KEY_FILE"
fi
chmod 600 "$KEY_FILE"
export OPENDECIDER_API_KEY="$(cat "$KEY_FILE")"
MODEL="${DECIDER_MODEL:-manjunathshiva/opendecider-nano}"
args=(serve --model "$MODEL" --host 127.0.0.1 --port 8011 --max-in-flight 4 --request-timeout-s 30)
if [ -n "${DECIDER_REVISION:-}" ]; then args+=(--revision "$DECIDER_REVISION"); fi
exec opendecider "${args[@]}"
