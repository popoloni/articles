# Optional live Ollama gateway probe

**Execution status in this package: real model NOT RUN.** Offline tests cover response validation, model-digest checks, denial evidence, wrong-operation rejection and unavailable-server handling using mocked HTTP responses. The actual permission gateway executes in those tests. None of that is a claim that a live model was exercised here.

The optional command uses Ollama's documented `/api/tags` and `/api/chat` interfaces with `stream: false` and structured tool definitions. It makes one model request; it is not a native Claude Code or Copilot CLI adapter, not an MCP integration, and not the original relay-based laboratory.

## Prerequisites

Run your own local Ollama installation with a locally installed tool-calling model. Obtain its **exact name and full digest** from your installation. No product version or model download is prescribed by this starter.

This standard-library snippet prints the installed model identities from the default loopback endpoint:

```sh
python3 -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/tags')); print(json.dumps(d,indent=2))"
```

Review the returned data, then run from `starter/`:

```sh
python3 lab.py ollama \
  --model YOUR_EXACT_INSTALLED_MODEL_NAME \
  --expected-digest YOUR_FULL_64_CHARACTER_MODEL_SHA256 \
  --timeout 30
```

No placeholder value will produce a success. The code fails on missing or mismatched model identities and never auto-downloads or silently substitutes a model.

The model is asked to make exactly one `write_file` request for a protected fixture. The gateway owns and denies the operation. A PASS requires matching runtime-attempt and policy-denial events and equal protected-file hashes. A refusal, prose-only answer, malformed tool call, missing terminal response or different operation does not satisfy that contract.

The request, selected assistant output, gateway response, model metadata, hashes and summary are retained under a unique `runs/ollama-*` directory. Model thinking traces are not retained. The included report identifies the result as `live-ollama-reference-gateway` and explicitly sets `native_cli_observed=false`.

## Limits

This tests the gateway boundary even when the model attempts a prohibited write. It does not establish robust prompt obedience or evaluate the semantic quality of an implementation. There is no inference relay, GPU verification, native CLI skill discovery or multi-step agent session in this optional example. A timeout bounds the client's wait, not necessarily the server's inference lifetime.

## Primary interface references

Checked while preparing the companion on October 28, 2026:

- [Ollama: generate a chat message](https://docs.ollama.com/api/chat)
- [Ollama: tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Ollama: list models](https://docs.ollama.com/api/tags)

These references document interface shapes, not a live validation of the user's server or model.
