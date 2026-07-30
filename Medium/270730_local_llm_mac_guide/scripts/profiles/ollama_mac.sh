#!/usr/bin/env bash
# Conservative Ollama profile for macOS / Apple Silicon.
#
# Commands:
#   ./ollama_mac.sh apply      Apply values to the current user launchd domain.
#   ./ollama_mac.sh install    Apply now and install a LaunchAgent for future logins.
#   ./ollama_mac.sh show       Show the active launchctl values.
#   ./ollama_mac.sh uninstall  Remove the LaunchAgent and clear the values.
#
# Override any setting before running, for example:
#   OLLAMA_CONTEXT_LENGTH=32768 OLLAMA_NUM_PARALLEL=2 ./ollama_mac.sh install

set -euo pipefail

PROFILE_LABEL="${PROFILE_LABEL:-com.local-llm.ollama-profile}"
PLIST_PATH="$HOME/Library/LaunchAgents/${PROFILE_LABEL}.plist"
SCRIPT_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/$(basename -- "${BASH_SOURCE[0]}")"

: "${OLLAMA_FLASH_ATTENTION:=1}"
: "${OLLAMA_KV_CACHE_TYPE:=q8_0}"
: "${OLLAMA_CONTEXT_LENGTH:=16384}"
: "${OLLAMA_NUM_PARALLEL:=1}"
: "${OLLAMA_MAX_LOADED_MODELS:=1}"
: "${OLLAMA_KEEP_ALIVE:=-1}"

KEYS=(
  OLLAMA_FLASH_ATTENTION
  OLLAMA_KV_CACHE_TYPE
  OLLAMA_CONTEXT_LENGTH
  OLLAMA_NUM_PARALLEL
  OLLAMA_MAX_LOADED_MODELS
  OLLAMA_KEEP_ALIVE
)

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "error: this profile is intended for macOS" >&2
    exit 2
  fi
  command -v launchctl >/dev/null 2>&1 || {
    echo "error: launchctl was not found" >&2
    exit 2
  }
}

apply_profile() {
  require_macos
  local key value
  for key in "${KEYS[@]}"; do
    value="${!key}"
    launchctl setenv "$key" "$value"
    printf 'set %-27s %s\n' "$key" "$value"
  done
  cat <<'MSG'

Profile applied to the current user launchd domain.
Quit Ollama completely and start it again so the GUI service inherits the values.
MSG
}

show_profile() {
  require_macos
  local key value
  for key in "${KEYS[@]}"; do
    value="$(launchctl getenv "$key" 2>/dev/null || true)"
    printf '%-27s %s\n' "$key" "${value:-<unset>}"
  done
}

clear_profile() {
  require_macos
  local key
  for key in "${KEYS[@]}"; do
    launchctl unsetenv "$key" 2>/dev/null || true
  done
}

xml_escape() {
  local value="$1"
  value=${value//&/&amp;}
  value=${value//</&lt;}
  value=${value//>/&gt;}
  value=${value//\"/&quot;}
  value=${value//\'/&apos;}
  printf '%s' "$value"
}

install_agent() {
  require_macos
  apply_profile
  mkdir -p "$HOME/Library/LaunchAgents"

  {
    cat <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$(xml_escape "$PROFILE_LABEL")</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
PLIST
    local key value
    for key in "${KEYS[@]}"; do
      value="${!key}"
      printf '    <string>%s</string>\n' "$(xml_escape "$key=$value")"
    done
    printf '    <string>%s</string>\n' "$(xml_escape "$SCRIPT_PATH")"
    cat <<PLIST
    <string>apply</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$(xml_escape "$HOME/Library/Logs/${PROFILE_LABEL}.out.log")</string>
  <key>StandardErrorPath</key>
  <string>$(xml_escape "$HOME/Library/Logs/${PROFILE_LABEL}.err.log")</string>
</dict>
</plist>
PLIST
  } > "$PLIST_PATH"

  plutil -lint "$PLIST_PATH"
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
  echo "installed LaunchAgent: $PLIST_PATH"
}

uninstall_agent() {
  require_macos
  if [[ -f "$PLIST_PATH" ]]; then
    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
    rm -f "$PLIST_PATH"
  fi
  clear_profile
  echo "removed the profile and cleared Ollama launchctl variables"
}

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
}

case "${1:-show}" in
  apply) apply_profile ;;
  install) install_agent ;;
  show) show_profile ;;
  uninstall|reset) uninstall_agent ;;
  -h|--help|help) usage ;;
  *) echo "error: unknown command: $1" >&2; usage >&2; exit 2 ;;
esac
