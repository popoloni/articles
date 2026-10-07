# Measured log audit: M4 local-model laboratory

*Revision 7 · 6 October 2026 · Primary basis: the supplied `logs.zip`, not web benchmarks.*

## E1. Scope

The archive contains 64 files (693,454 expanded bytes), nine smoke JSONL files with 66 rows, one separate readiness JSONL row, three nonempty CLI generation logs and supporting launch, preflight, version and error records. It has no supplied native-Ollama response files, no successful resident-Qwen3.6 smoke records, no tool-format cases and no system memory-pressure/swap time series. The author's stated machine is an M4 Mac mini with 16 GB. Recorded platform strings identify macOS 26.5.1 on arm64; they do not independently measure installed RAM.

The archive SHA-256 is:

```text
0856bf466702f953dcc05a0fe1ed278917cd2d450a7fc12a529745de137f78ca
```

[Source-file sizes, line counts and hashes](source-index.csv) · [Checkpoint/runtime launch provenance](checkpoint-provenance.csv) · [Machine-readable audit](audit.json)

Neither ZIP-member modification times nor filesystem extraction times are used to infer request speed. The client's `wall_seconds` is the measurement; request timestamps identify observations. The separate readiness timestamp is recorded after its call, so it is not treated as another smoke request start.

## E2. Requests

The same two user messages are used throughout. Temperature is 0.7 and max_tokens is 512 in every smoke request; stream is false. The system-level serialization, template additions, reasoning, server-default sampling parameters, prompt caches and background conditions are not matched. There are eleven identified suites: one per model/runtime except packed ternary Bonsai, whose file appends two suites. Those suites are not deduplicated because response IDs/timestamps are distinct; a reset to repeat 1 identifies the second suite.

Each source location below is a 1-based physical JSONL line. The complete sanitized records are in [response-records.jsonl](response-records.jsonl). Local home-directory paths have been replaced, not measurement fields.

|Source:line|Profile|Repeat|Case|Outcome|Wall s|Completion tokens|Cached tokens|
|---|---|---|---|---|---|---|---|
|`binary-smoke.jsonl:1`|bonsai-binary|1|json_contract|pass|3.602|39|0|
|`binary-smoke.jsonl:2`|bonsai-binary|1|literal_recall|pass|1.238|8|0|
|`binary-smoke.jsonl:3`|bonsai-binary|2|json_contract|format_only|3.109|44|68|
|`binary-smoke.jsonl:4`|bonsai-binary|2|literal_recall|pass|0.699|8|43|
|`binary-smoke.jsonl:5`|bonsai-binary|3|json_contract|pass|2.739|39|68|
|`binary-smoke.jsonl:6`|bonsai-binary|3|literal_recall|pass|0.677|8|43|
|`qwen36-stream-smoke-r4.jsonl:1`|qwen36-stream|1|json_contract|pass|7.254|39|0|
|`qwen36-stream-smoke-r4.jsonl:2`|qwen36-stream|1|literal_recall|pass|2.973|8|0|
|`qwen36-stream-smoke-r4.jsonl:3`|qwen36-stream|2|json_contract|pass|5.822|39|0|
|`qwen36-stream-smoke-r4.jsonl:4`|qwen36-stream|2|literal_recall|pass|2.511|8|0|
|`qwen36-stream-smoke-r4.jsonl:5`|qwen36-stream|3|json_contract|pass|4.517|26|0|
|`qwen36-stream-smoke-r4.jsonl:6`|qwen36-stream|3|literal_recall|pass|2.493|8|0|
|`qwen38-iq2s-smoke.jsonl:1`|qwen38-iq2s|1|json_contract|pass|5.003|26|0|
|`qwen38-iq2s-smoke.jsonl:2`|qwen38-iq2s|1|literal_recall|pass|2.080|8|0|
|`qwen38-iq2s-smoke.jsonl:3`|qwen38-iq2s|2|json_contract|pass|3.525|26|68|
|`qwen38-iq2s-smoke.jsonl:4`|qwen38-iq2s|2|literal_recall|pass|1.203|8|43|
|`qwen38-iq2s-smoke.jsonl:5`|qwen38-iq2s|3|json_contract|pass|3.671|26|68|
|`qwen38-iq2s-smoke.jsonl:6`|qwen38-iq2s|3|literal_recall|pass|1.160|8|43|
|`qwen38-iq3xxs-smoke.jsonl:1`|qwen38-iq3xxs|1|json_contract|pass|5.258|31|0|
|`qwen38-iq3xxs-smoke.jsonl:2`|qwen38-iq3xxs|1|literal_recall|pass|2.023|8|0|
|`qwen38-iq3xxs-smoke.jsonl:3`|qwen38-iq3xxs|2|json_contract|pass|4.218|31|68|
|`qwen38-iq3xxs-smoke.jsonl:4`|qwen38-iq3xxs|2|literal_recall|pass|1.267|8|43|
|`qwen38-iq3xxs-smoke.jsonl:5`|qwen38-iq3xxs|3|json_contract|pass|4.263|31|68|
|`qwen38-iq3xxs-smoke.jsonl:6`|qwen38-iq3xxs|3|literal_recall|pass|1.244|8|43|
|`qwen38-mlx2-smoke.jsonl:1`|qwen38-mlx2|1|json_contract|truncated|54.179|512|0|
|`qwen38-mlx2-smoke.jsonl:2`|qwen38-mlx2|1|literal_recall|wrong_content|1.745|4|0|
|`qwen38-mlx2-smoke.jsonl:3`|qwen38-mlx2|2|json_contract|truncated|54.190|512|0|
|`qwen38-mlx2-smoke.jsonl:4`|qwen38-mlx2|2|literal_recall|wrong_content|1.803|4|0|
|`qwen38-mlx2-smoke.jsonl:5`|qwen38-mlx2|3|json_contract|truncated|56.025|512|0|
|`qwen38-mlx2-smoke.jsonl:6`|qwen38-mlx2|3|literal_recall|wrong_content|1.886|4|0|
|`qwen38-mlx3-smoke.jsonl:1`|qwen38-mlx3|1|json_contract|pass|7.173|39|0|
|`qwen38-mlx3-smoke.jsonl:2`|qwen38-mlx3|1|literal_recall|pass|2.414|8|0|
|`qwen38-mlx3-smoke.jsonl:3`|qwen38-mlx3|2|json_contract|pass|6.692|39|0|
|`qwen38-mlx3-smoke.jsonl:4`|qwen38-mlx3|2|literal_recall|pass|2.525|8|0|
|`qwen38-mlx3-smoke.jsonl:5`|qwen38-mlx3|3|json_contract|pass|6.703|39|0|
|`qwen38-mlx3-smoke.jsonl:6`|qwen38-mlx3|3|literal_recall|pass|2.514|8|0|
|`qwen38-omlx-smoke.jsonl:1`|qwen38-omlx2|1|json_contract|invalid_json|13.485|72|0|
|`qwen38-omlx-smoke.jsonl:2`|qwen38-omlx2|1|literal_recall|truncated|50.752|512|0|
|`qwen38-omlx-smoke.jsonl:3`|qwen38-omlx2|2|json_contract|invalid_json|16.146|153|107|
|`qwen38-omlx-smoke.jsonl:4`|qwen38-omlx2|2|literal_recall|wrong_content|8.775|79|82|
|`qwen38-omlx-smoke.jsonl:5`|qwen38-omlx2|3|json_contract|truncated|50.877|512|107|
|`qwen38-omlx-smoke.jsonl:6`|qwen38-omlx2|3|literal_recall|wrong_content|6.213|53|82|
|`qwen38-omlx-smoke.jsonl:7`|qwen38-omlx3|1|json_contract|pass|24.753|158|0|
|`qwen38-omlx-smoke.jsonl:8`|qwen38-omlx3|1|literal_recall|pass|14.026|97|0|
|`qwen38-omlx-smoke.jsonl:9`|qwen38-omlx3|2|json_contract|pass|21.281|168|107|
|`qwen38-omlx-smoke.jsonl:10`|qwen38-omlx3|2|literal_recall|pass|9.304|74|82|
|`qwen38-omlx-smoke.jsonl:11`|qwen38-omlx3|3|json_contract|pass|20.361|169|107|
|`qwen38-omlx-smoke.jsonl:12`|qwen38-omlx3|3|literal_recall|pass|8.995|71|82|
|`qwen38-q2xl-smoke.jsonl:1`|qwen38-q2xl|1|json_contract|pass|5.230|31|0|
|`qwen38-q2xl-smoke.jsonl:2`|qwen38-q2xl|1|literal_recall|pass|1.996|8|0|
|`qwen38-q2xl-smoke.jsonl:3`|qwen38-q2xl|2|json_contract|pass|4.323|31|68|
|`qwen38-q2xl-smoke.jsonl:4`|qwen38-q2xl|2|literal_recall|pass|1.349|8|43|
|`qwen38-q2xl-smoke.jsonl:5`|qwen38-q2xl|3|json_contract|pass|4.344|31|68|
|`qwen38-q2xl-smoke.jsonl:6`|qwen38-q2xl|3|literal_recall|pass|1.213|8|43|
|`ternary-smoke.jsonl:1`|bonsai-ternary|1|json_contract|pass|4.111|26|0|
|`ternary-smoke.jsonl:2`|bonsai-ternary|1|literal_recall|pass|1.876|8|0|
|`ternary-smoke.jsonl:3`|bonsai-ternary|2|json_contract|pass|3.469|26|0|
|`ternary-smoke.jsonl:4`|bonsai-ternary|2|literal_recall|pass|1.675|8|0|
|`ternary-smoke.jsonl:5`|bonsai-ternary|3|json_contract|pass|3.595|26|0|
|`ternary-smoke.jsonl:6`|bonsai-ternary|3|literal_recall|pass|1.671|8|0|
|`ternary-smoke.jsonl:7`|bonsai-ternary|1|json_contract|pass|3.493|26|0|
|`ternary-smoke.jsonl:8`|bonsai-ternary|1|literal_recall|pass|1.685|8|0|
|`ternary-smoke.jsonl:9`|bonsai-ternary|2|json_contract|pass|3.385|26|0|
|`ternary-smoke.jsonl:10`|bonsai-ternary|2|literal_recall|pass|1.655|8|0|
|`ternary-smoke.jsonl:11`|bonsai-ternary|3|json_contract|pass|3.381|26|0|
|`ternary-smoke.jsonl:12`|bonsai-ternary|3|literal_recall|pass|1.597|8|0|


## E3. Method

JSON passes only if a completed response is parseable as JSON with exactly `order_id=ORD-27A9`, `owner=Mira` and numeric `amount_eur=2400`. Code fences are not stripped to change the original test. Recall passes only for the supplied current code after surrounding whitespace is stripped. Completion with `finish_reason=length` fails even when a useful substring appears. No tool is executed. All 66 independently recomputed outcomes agree with the stored booleans; no duplicate response IDs or inconsistent total-token sums were found.

All latency summaries include failure records. Medians and full observed ranges are descriptive: N=3 per case per configuration, except ternary N=6. Repeated fixed questions are not independently sampled tasks. No significance claim, population success estimate, confidence interval or meaningful p95 is inferred from this sample.

`wall_seconds` includes whatever the client experienced during that request; it is not time to first token. `response.timings.predicted_per_second` and `prompt_ms` are retained for llama.cpp; `response.usage.generation_tokens_per_second` and the duration fields are retained for oMLX. They remain separately labelled, not silently standardized to an invented timer. In the llama.cpp samples, the reported rate corresponds numerically to `(predicted_n - 1) / predicted_seconds`, not `predicted_n / predicted_seconds`. The supplied native rate is used, not recalculated with another convention. Rates from tiny replies do not establish sustained generation speed.

The top-level client field `decode_tokens_per_second` is null in every smoke row. It is not overwritten. The analysis adds separate **server** timing columns where the nested response supplies them. For MLX-LM and streamed Qwen API results those columns remain empty. No decode estimate is obtained by dividing output count by whole-request duration.

Server and client clocks are not perfectly additive: one supplied GGUF response has prompt+decode durations about 6.4 ms above its client wall time. That residual is retained, not clipped into an overhead chart. oMLX separately records cold model-load durations in its first rows; the total_time/TTFT fields do not cover exactly the same boundary as the client timer.

## E4. Failures

Thirteen failed checks consist of one format-only failure, five truncations and seven other completed contract failures. The failure rows account for 319.185 of 565.416 summed smoke-request seconds (56.45%) and 2,973 of 4,621 completion tokens (64.34%). This is an accounting of this recorded workload, not a projection of production waste.


**`logs/binary-smoke.jsonl:3` — json_contract; passed=False; finish_reason=stop**

````text
```json
{
  "order_id": "ORD-27A9",
  "owner": "Mira",
  "amount_eur": 2400
}
```
````


**`logs/qwen38-mlx2-smoke.jsonl:1` — json_contract; passed=False; finish_reason=length**

````text
**B-27A9**
- owner=Mira
- amount_eur must be exactly **2400** EUR

**B-27A9** owner=Mira amount_eur exactly **2400** EUR

**B-27A9** owner=Mira amount_eur exactly **2400** EUR returning only exactly these fields?User's instruction is clear: return only a JSON object with exactly these fields?User's instruction is clear: return only a JSON object with exactly these fields?User's instruction is clear: return only a JSON object with exactly these fields?User's instruction is clear: return only a JSON object with exactly these fieldsUser's instruction is clear: return only a JSON object with exactly these fieldsUser's instruction is clear: return only a JSON object with exactly these fieldsUser' [excerpt ends]
````


**`logs/qwen38-mlx2-smoke.jsonl:2` — literal_recall; passed=False; finish_reason=stop**

````text
288
````


**`logs/qwen38-omlx-smoke.jsonl:1` — json_contract; passed=False; finish_reason=stop**

````text
The problem asks me to provide reasoning and then create a JSON object containing exactly the fields `order_id`, `owner`, and `amount_eur`. The specified values are order_id=`ORD-27A9`, owner=`Mira`, and amount_eur=`2400`. The instruction states that amount_eur must be a number type."
````


**`logs/qwen38-omlx-smoke.jsonl:3` — json_contract; passed=False; finish_reason=stop**

````text
{
"Return": a JSON object
"Structure": {
"returning": "a" "valid" JSON"}
"Fields": {
"order_id": "ORD-27A9",
"owner": "Mira",
"amount_eur": "2400"
}
}
````


Two-bit ordinary MLX is identified by the launcher as `lukaskremla/Qwen3.8-27B-2bit-MLX-TextOnly`, revision `49217e7be1f217014b94bf391486b3b71de09d7c`. The oMLX two-bit/three-bit runs expose `qwen38-mlx2` and `qwen38-mlx3`, but no oMLX model-settings export or revision/digest appears in the archive. Labels in the figures reflect these aliases and the documented branches; exact weight identity across the two engines is not independently proven.

Failure under both logged two-bit paths is a reproducible warning within this sample, not a diagnosis of the causal bug. No tokenizer/config/weight-content audit, higher-precision reference logits, controlled template ablation or different quantizer comparison is present. Returning a code in 1.8 seconds is not successful recall when the answer is wrong.

## E5. Timings

GGUF values below use the JSON case only (N=3), preserving the original counters. Qwen uses fingerprint `b11429-d81235049`; binary Bonsai uses `b10743-adfffbe41`. Output length differs between formats, so total latency is not a pure kernel benchmark.


|Profile|Median decode tok/s|Min|Max|Completion token counts|
|---|---|---|---|---|
|bonsai-binary|14.946|14.758|15.188|39,44,39|
|qwen38-iq2s|8.064|7.924|8.278|26,26,26|
|qwen38-q2xl|7.740|7.684|8.234|31,31,31|
|qwen38-iq3xxs|7.953|7.909|8.012|31,31,31|

**Source: `logs/llama-server-version.txt`**

```text
L1: version: 0.6.0 (build 11429, commit d81235049)
L2: built with AppleClang 21.0.0.21000334 for Darwin arm64
```


## E6. Cache

Only reported prefix reuse is labelled as such. GGUF later JSON repeats reuse 68/72 tokens; later recall repeats reuse 43/47. oMLX later repeats reuse 107/112 and 82/87 respectively. No persistence-through-restart experiment is identifiable. In particular, all first occurrences are not treated as cold weight loads: the streaming run has a prior readiness request, and other CLI warm-ups may precede API tests.

Standalone MLX-LM sets `--prompt-cache-size 1` in the recorded launch commands. It alternates two different task prefixes and reports zero cached tokens for all observed smoke responses. The streaming server also reports zero response prefix hits while its console retains several conversation-cache entries. Stored state, reused prefix tokens, cached experts and OS file pages are four different concepts.


|Profile|First JSON prefill s|Repeats 2–3 median s|Cached tokens by repeat|
|---|---|---|---|
|bonsai-binary|1.097|0.155|0,68,68|
|qwen38-iq2s|1.980|0.444|0,68,68|
|qwen38-q2xl|1.593|0.414|0,68,68|
|qwen38-iq3xxs|1.509|0.427|0,68,68|
|qwen38-omlx2|2.090|0.450|0,107,107|
|qwen38-omlx3|1.830|0.520|0,107,107|

**Source: `logs/qwen36-stream-server-r4.log`**

```text
L5: [turboquant-serve] Expert streaming: cache_budget=4.0 GB, max_active_experts=0, page_cache=auto (single-user; use --prompt-concurrency 1)
L7: [turboquant-serve] TurboQuant KV cache: K=V=8-bit, group=64, sink=0 (forces single-stream serving)
L9: [turboquant-serve] Streaming TurboQuant model from $HOME/LocalAI/qwen-bonsai-lab/models/qwen36-stream (cache_budget=4.0 GB)
L13: [turboquant-serve] Metal buffer-cache limit: off — ample headroom (working set 14.0 GiB, resident 0.0 GiB)
L66: 2026-10-06 01:23:45,123 - INFO - Prompt Cache: 4 sequences, 0.27 GB
```


## E7. oMLX

`qwen38-omlx-smoke.jsonl` lines 1–6 are the failing `qwen38-mlx2` configuration; lines 7–12 are the passing `qwen38-mlx3` configuration. Combining them into one score or averaging them as one model is incorrect. The model names, not the filename alone, define the groups.

All six three-bit responses include a nonempty `reasoning_content` field, absent in the standalone three-bit responses. Two task input counts rise from 72/47 to 112/87. The request body itself contains neither a thinking switch nor a template export; effective server settings cannot be reconstructed from the user message alone. Reasoning changes the generated workload and limits any causal backend conclusion. The final content passes; including hidden material in the latency does not change its strict output score.

Median completion tokens rise from 39/8 under standalone MLX-LM to 168/74 under oMLX. Native oMLX generation medians across all six requests are 9.950 tokens/s for the failing 2-bit run and 8.465 for the passing 3-bit run. These numbers demonstrate why rate alone is not success. They include the model's generated completion material; there is no independent reasoning-token split.

The first oMLX JSON rows report model_load_duration 4.02 s (2-bit) and 3.91 s (3-bit). The later three-bit JSON records report time_to_first_token 0.53 and 0.51 s, total_time 21.27 and 20.35 s, and client wall 21.281 and 20.361 s. These are different measurement boundaries. Because requests are non-streaming, the client does not observe the first final-content chunk. Internal TTFT is therefore not a user-visible-answer latency claim.

## E8. Gaps

**Resident Qwen3.6 (L5):** the author previously reported it working, but the uploaded `qwen36-resident-server.log` contains only the old wrapper-flag preflight refusal. No corresponding successful smoke JSONL or performance counter is present. Keep the earlier functional report and this missing quantitative evidence separate.

**Ollama-native:** no Ollama `/api/chat` response, diagnostic `response.json`, saved answer/metrics or inventory JSON appears in this archive. Earlier troubleshooting in the conversation establishes import/residency and an output-limit problem, not an archive-backed token-rate or latency sample. Those files were saved under the package's `outputs/` directory, which was not uploaded here.

**Memory:** no sysctl/vm_stat time series, Activity Monitor capture, wired-cap snapshot, or full system-memory profile is supplied. CLI peaks and prompt-cache allocations cannot be extrapolated to total RAM pressure. The streaming startup's 14.0 GiB working-set report does not independently document how that setting was chosen or whether a previous manual cap was restored. A launch JSON saying 'No wired cap changed' describes launcher behavior, not a complete history of the machine's sysctl state.

**Coding and modality coverage:** no tool_format cases, external acceptance-test results, repository diffs, long-context tasks, RAG evaluations, translations, images or audio results are present. Passing these short contracts is a necessary early gate, not general agent readiness.

**Versions:** archived `tq.freeze.txt` and the pre-fix freeze list MLX-LM 0.32.0; the later contract report and successful response fingerprints identify 0.31.3 with MLX 0.32.3. Treat the freeze as an earlier record, not the successful inference environment. The separate VLM diagnostic freeze retains MLX-LM 0.32.0, MLX-VLM 0.7.6 and MLX 0.32.3; it is a different path, not a contradiction or permission to upgrade the fixed text server.

**Readiness/failures:** missing-wrapper-flag checks and the IQ3 acknowledgment gate stop before inference. The earlier streaming process did bind HTTP after its generation thread failed. Record these as setup/readiness incidents, not timed task failures or memory-limit measurements. The recovered successful runs remain in the latency dataset.


**Source: `logs/qwen36-resident-server.log`**

```text
L1: $HOME/LocalAI/qwen-bonsai-lab/venv-tq/bin/turboquant-serve --model $HOME/LocalAI/qwen-bonsai-lab/models/qwen36-asym --host 127.0.0.1 --port 8080 --kv-bits 8 --tool-syntax-greedy --prefill-step-size 128 --temp 0.7 --top-p 0.8 --top-k 20 --chat-template-args '{"enable_thinking":false}' --prompt-concurrency 1
L2: ERROR: Installed runtime does not advertise: --tool-syntax-greedy
```


**Source: `logs/qwen36-stream-server.log`**

```text
L9: 2026-10-06 01:04:14,923 - ERROR - mlx_lm.server generation thread died: _patch_loader.<locals>._tq_aware_load() got an unexpected keyword argument 'trust_remote_code'
L22: TypeError: _patch_loader.<locals>._tq_aware_load() got an unexpected keyword argument 'trust_remote_code'
L25: 2026-10-06 01:04:14,928 - INFO - Starting httpd at 127.0.0.1 on port 8080...
```


**Source: `logs/qwen38-q2x1-server.log`**

```text
L1: /opt/homebrew/bin/llama-server -m $HOME/LocalAI/qwen-bonsai-lab/models/qwen38-iq3xxs/Qwen3.8-27B-UD-IQ3_XXS.gguf --host 127.0.0.1 --port 8083 --alias qwen38-iq3xxs -ngl auto -fa on -c 4096 -np 1 --jinja --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0 --chat-template-kwargs '{"enable_thinking":false,"preserve_thinking":false}' -b 128 -ub 128 --presence-penalty 1.5 --repeat-penalty 1.0 --offline
L2: ERROR: Tight memory profile: read the guide, then explicitly acknowledge this experiment.
```


### Next measurement run

Keep a known-good checkpoint/runtime unchanged; export exact revision, template, thinking settings, context, cache policy and resolved environment. Use new synthetic records and distractors rather than only the two memorized prompts. Separate one initial load from warm requests, and collect enough runs before reporting tail latency. Record first visible final-content arrival in a streaming client, full response latency, actual native prefill/decode counters, and task acceptance separately. Include memory pressure and swap before/during/after the workload. Preserve failed outputs. A tokenizer-verified long-context case and an externally verified, bounded edit–test–repair task should be distinct additional experiments.

For the failing ordinary two-bit paths, validate checkpoint identity, configuration/tokenizer compatibility and non-thinking behavior against a known-good higher-precision reference. For oMLX 3-bit, make the template/reasoning policy match before comparing runtime speed. Do not raise output ceilings repeatedly for the logged degenerate 512-token loops.

## E9. CLI

The following excerpts preserve original labels and line numbers. 'Coherent' is a manual review of the saved text against the requested five-sentence explanation, not a automated semantic benchmark. CLI inference settings are not assumed identical to HTTP settings.


**Source: `logs/ternary-generate.log`**

```text
L1: ==========
L2: Retry involves re-executing an entire operation from the beginning to overcome a transient failure, while rollback reverses all changes made during a failed transaction to restore the system to its previous state. Retries aim to achieve successful completion, whereas rollbacks focus on maintaining data consistency and integrity by discarding partial work. A retry consumes resources again, potentially increasing load, whereas a rollback typically cleans up resources without reprocessing the original workload. Systems often use retries for temporary errors like network timeouts, but rollbacks are essential for permanent failures or violations of business rules. Together, they form complementary strategies: retries handle transient issues, while rollbacks ensure safety when operations cannot succeed.
L3: ==========
L4: Prompt: 24 tokens, 6.726 tokens-per-sec
L5: Generation: 133 tokens, 16.208 tokens-per-sec
L6: Peak memory: 6.232 GB
```


**Source: `logs/qwen38-mlx2-generate.log`**

```text
L1: ==========
L2: The user is asking about retry and rollback mechanisms in databases or systems, perhaps within the context of the MV-2-RC isolation level. I need to think about what these mechanisms might mean in the context of database transaction isolation levels. Based on the context, retry likely refers to retrying a failed transaction after it detects a failed lock or isolation level mismatch. Rollback refers to a failed transaction's rollback response, possibly as a recovery or compensation mechanism. These are common patterns in databases and transaction isolation contexts. I'll frame the answer around discussing how retry might involve re-execution or retry logic and how rollback might involve a failed transaction's rollback response.","
L3:   "
L4: ==========
L5: Prompt: 24 tokens, 9.508 tokens-per-sec
L6: Generation: 135 tokens, 11.001 tokens-per-sec
L7: Peak memory: 8.737 GB
```


**Source: `logs/qwen38-tq-diagnostic.log`**

```text
L1: [transformers] PyTorch was not found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
L2: [INFO] Replaced 496 layers with PolarQuantized versions
L3: [INFO] Loaded in 1.5s
L4: ==========
L5: Files: [] 
L6: 
L7: Prompt: <|im_start|>user
L8: Explain the difference between retry and rollback in five sentences.<|im_end|>
L9: <|im_start|>assistant
L10: <think>
L11: 
L12: </think>
L13: 
L14: 
L15: 
L16: Prefill:   0%|          | 0/24 [00:00<?, ?tok/s]
L17: Prefill:  96%|█████████▌| 23/24 [00:01<00:00, 15.94tok/s]
L18: Prefill:  96%|█████████▌| 23/24 [00:01<00:00, 15.94tok/s]
L19: Retry is a mechanism that attempts to re-execute a failed operation, whereas rollback is a process that reverts a transaction to its previous state. Retry is typically used for transient errors like network timeouts, while rollback is essential for maintaining data consistency after a partial failure. A retry does not undo any changes made by the initial attempt, but a rollback explicitly cancels all modifications to ensure the system remains in a valid state. Consequently, retry is often paired with idempotent operations to avoid duplicate side effects, while rollback is a fundamental feature of database transaction management. In summary, retry focuses on persistence and eventual success, while rollback focuses on safety and state integrity.
L20: ==========
L21: Prompt: 24 tokens, 11.585 tokens-per-sec
L22: Generation: 133 tokens, 2.670 tokens-per-sec
L23: Peak memory: 12.798 GB
L24: peak memory: 11.92 GB
```


**Source: `logs/qwen38-tq-diagnostic.exit-code.txt`**

```text
L1: 0
```


The diagnostic has two printed peaks: `12.798 GB` and `11.92 GB`. The numerical conversion 12.798 × 10^9 / 2^30 = 11.9190663 is consistent with decimal/binary units, but both printed labels say GB. We do not assume without implementation evidence that they are exactly the same counter; both values are retained. The chart uses the capitalized `Peak memory` field consistently across the three CLI logs and labels it as printed, not as system memory.

`binary-generate.log` is empty and supplies no CLI throughput result. The nonempty two-bit MLX CLI answer is malformed/meta-commentary, despite its displayed token rate. The TQ diagnostic's status file contains 0; its coherent answer and rate establish one ordinary-generation observation, not a result on the previously mentioned four agentic tasks.

## E10. Reproduction and privacy

Run `analyze_logs.py` on the original archive, then `plot_results.py` on the extracted numeric tables. No model is loaded by either script. The parser does not execute archive files or contact a network. The figures use matplotlib defaults and individual axes. The eight images are also included as PNG and SVG, and article-standalone.html embeds all eight for offline reading.

The original raw logs are not included in this publication package. The normalized response records preserve their prompts, responses, reasoning and metrics but replace home-directory names with `$HOME`. Source file hashes refer to the unmodified original bytes. This is a narrow local-path redaction, not a claim that an arbitrary future archive contains no personal data. Review new logs before publishing them.

