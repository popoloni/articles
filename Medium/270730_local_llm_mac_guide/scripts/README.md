# Local LLM Mac companion files

## Files

- `benchmark_mac_backends.py` — dependency-free concurrent streaming benchmark for Ollama native and OpenAI-compatible APIs.
- `mac_probe.sh` — captures hardware, memory pressure, swap, display/Metal information, processes, storage, and installed engine versions.
- `profiles/ollama_mac.sh` — applies a conservative Ollama profile with `launchctl`; `install` adds a login LaunchAgent.
- `profiles/llamacpp_server.sh` — parameterized llama.cpp Metal server profile that skips unsupported version-specific flags.
- `profiles/omlx_server.sh` — parameterized oMLX memory, cache, and concurrency profile that checks the installed CLI surface.
- `profiles/mlxlm_server.sh` — basic localhost MLX-LM server profile.
- `prompts.example.jsonl` — mixed short, long-prefix, coding, long-context, and structured-output workloads.

## Quick start

```bash
chmod +x benchmark_mac_backends.py mac_probe.sh profiles/*.sh
./mac_probe.sh > machine-state.txt
```

Ollama benchmark:

```bash
python3 benchmark_mac_backends.py \
  --provider ollama \
  --base-url http://127.0.0.1:11434 \
  --model '<ollama-model>' \
  --prompts prompts.example.jsonl \
  --concurrency 1,2,4 \
  --repetitions 3 \
  --max-tokens 256 \
  --num-ctx 16384 \
  --output results-ollama.json
```

OpenAI-compatible benchmark for llama.cpp, oMLX, MLX-LM, or Ollama:

```bash
python3 benchmark_mac_backends.py \
  --provider openai \
  --base-url http://127.0.0.1:8080/v1 \
  --model '<served-model-name>' \
  --prompts prompts.example.jsonl \
  --concurrency 1,2,4 \
  --repetitions 3 \
  --max-tokens 256 \
  --output results-openai.json
```

The server scripts print the final command before execution. Set `DRY_RUN=1` to inspect it without starting the server.
