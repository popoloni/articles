#!/usr/bin/env bash
set -u

section() { printf '\n===== %s =====\n' "$1"; }
run() { printf '$ %q' "$1"; shift; printf ' %q' "$@"; printf '\n'; "$@" 2>&1 || true; }

section "Timestamp"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
date '+Local: %Y-%m-%dT%H:%M:%S%z'

section "macOS"
sw_vers 2>&1 || true
uname -a 2>&1 || true
uname -m 2>&1 || true

section "Hardware"
sysctl -n machdep.cpu.brand_string 2>&1 || true
printf 'Logical CPUs: '; sysctl -n hw.logicalcpu 2>&1 || true
printf 'Physical CPUs: '; sysctl -n hw.physicalcpu 2>&1 || true
printf 'Unified memory bytes: '; sysctl -n hw.memsize 2>&1 || true
system_profiler SPHardwareDataType SPDisplaysDataType 2>&1 || true

section "Memory pressure"
vm_stat 2>&1 || true
memory_pressure 2>&1 || true
sysctl vm.swapusage 2>&1 || true

section "Top resident processes"
ps -axo pid,ppid,%cpu,%mem,rss,etime,comm | sort -k5 -nr | head -n 20 2>&1 || true

section "Storage"
df -h / "$HOME" 2>&1 || true

section "Installed engines"
command -v ollama >/dev/null && ollama --version 2>&1 || echo 'ollama: not found'
command -v llama-server >/dev/null && llama-server --version 2>&1 || echo 'llama-server: not found in PATH'
command -v omlx >/dev/null && omlx --version 2>&1 || echo 'omlx: not found'
command -v mlx_lm.generate >/dev/null && mlx_lm.generate --help 2>&1 | head -n 3 || echo 'mlx_lm.generate: not found'
python3 - <<'PY' 2>&1 || true
mods = ["mlx", "mlx_lm"]
for name in mods:
    try:
        mod = __import__(name)
        print(f"{name}: {getattr(mod, '__version__', 'installed (no __version__)')}")
    except Exception as exc:
        print(f"{name}: unavailable ({exc})")
PY

section "Ollama state"
command -v ollama >/dev/null && ollama ps 2>&1 || true

cat <<'EOF'

Optional privileged sampling (run separately, not automatically):
  sudo powermetrics --samplers cpu_power,gpu_power,thermal -i 1000
Sampler names vary by Mac and macOS version; check: powermetrics --help
EOF
