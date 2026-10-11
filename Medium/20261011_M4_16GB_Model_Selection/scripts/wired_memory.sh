#!/bin/bash
# Read/save only. This script NEVER changes a sysctl or invokes sudo.
set -eu
umask 077
if [ "$#" -ne 2 ]; then
  printf '%s\n' 'Usage: bash wired_memory.sh status|save|saved-value LAB_DIRECTORY' >&2
  exit 2
fi
ACTION="$1"
LAB_DIR="$2"
case "$ACTION" in status|save|saved-value) ;; *) printf '%s\n' 'Unknown action.' >&2; exit 2 ;; esac
if [ -z "$LAB_DIR" ] || [ ! -d "$LAB_DIR" ]; then
  printf '%s\n' 'The lab directory must already exist. Source scripts/lab_env.sh first.' >&2
  exit 2
fi
SAVED="$LAB_DIR/logs/wired_limit_before.txt"
valid_number() {
  case "$1" in ''|*[!0-9]*) return 1 ;; *) return 0 ;; esac
}
read_saved() {
  if [ -L "$SAVED" ] || [ ! -f "$SAVED" ]; then
    printf '%s\n' 'No regular saved-value file. Do not guess the original wired limit.' >&2
    return 2
  fi
  VALUE="$(cat "$SAVED")" || return 2
  if ! valid_number "$VALUE"; then
    printf '%s\n' 'Saved wired limit is empty or not a non-negative integer. Stop and inspect; it was not overwritten.' >&2
    return 2
  fi
  printf '%s\n' "$VALUE"
}
if [ "$ACTION" = saved-value ]; then
  read_saved
  exit $?
fi
CURRENT="$(sysctl -n iogpu.wired_limit_mb)" || {
  printf '%s\n' 'Cannot read iogpu.wired_limit_mb. No snapshot written and no limits changed.' >&2
  exit 2
}
if ! valid_number "$CURRENT"; then
  printf '%s\n' 'Unexpected sysctl value. No snapshot written and no limits changed.' >&2
  exit 2
fi
printf 'Current wired limit: %s\n' "$CURRENT"
if [ -e "$SAVED" ] || [ -L "$SAVED" ]; then
  ORIGINAL="$(read_saved)" || exit 2
  printf 'Existing saved value: %s (not overwritten)\n' "$ORIGINAL"
  if [ "$CURRENT" != "$ORIGINAL" ]; then
    printf '%s\n' 'Current and saved values differ. Check the session record before changing or restoring anything.' >&2
  fi
elif [ "$ACTION" = save ]; then
  mkdir -p "$LAB_DIR/logs"
  ( set -C; printf '%s\n' "$CURRENT" > "$SAVED" ) || {
    printf '%s\n' 'Could not create the snapshot exclusively. Nothing was overwritten.' >&2
    exit 2
  }
  printf 'Saved current value to: %s\n' "$SAVED"
else
  printf '%s\n' 'No saved value. Use save BEFORE any manual change.'
fi
printf '%s\n' 'Read/save only: no system limit changed. A snapshot records what is set now, not a factory default.'
