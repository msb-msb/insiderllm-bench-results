# DRAFT — not filed. Target: https://github.com/NVIDIA/Personal-AI-Router/issues

## Title

ollama-proxy: undocumented 120 s upstream response-header timeout turns a queued or cold-loading request into a 502

## Summary

`ollama-proxy` gives up on an upstream request after 120 s if no response headers have arrived and returns `502 {"error":"upstream error: net/http: timeout awaiting response headers"}`. Ollama serves one request at a time by default (`OLLAMA_NUM_PARALLEL=1`) and does not send headers until generation starts, so any request that sits in Ollama's queue for more than 120 s, or that waits on a model load longer than 120 s, fails through PAIR while the identical request sent straight to Ollama succeeds. Nothing in the README, `services/ollama-proxy/README.md`, the flag table, or `docs/troubleshooting.mdx` mentions the limit, and there is no flag or setting to change it.

The 120 s figure is the observed value; I did not locate the constant in the source.

## Versions

| Component | Version |
|---|---|
| PAIR | v0.1.1 release archive `service-binaries-linux-x64.zip`, product 0.91.7, `ollama-proxy` 0.26.2, `nvpair-ui-broker` 0.40.2, run via `nvpair-tui` 0.7.2 |
| OS | Ubuntu 24.04.4, kernel 6.8.0-138 (node A), Ubuntu 24.04.4 (node B) |
| Engine | Ollama 0.30.0 (node A, RTX 3090 24 GB), Ollama 0.17.5 (node B, RTX 3060 12 GB), both adopted by PAIR on port 11434, proxy on 11435 |
| Cluster | two nodes paired, one Ollama-compatible proxy each |

## Reproduction 1 — queue depth (single node, model only on this node)

1. Ollama on node A with a model that generates about 200 tokens in more than 6 s. I used `qwen3.6:27b` Q4_K_M on an RTX 3090 (about 11 s per 200-token request).
2. Fire 20 independent `POST /v1/chat/completions` requests concurrently at the PAIR proxy (`127.0.0.1:11435`), `max_tokens: 200`, `stream: false`.
3. Fire the same 20 at Ollama directly (`127.0.0.1:11434`) as the control.

Observed:

| Path | Wall clock | Succeeded | Failed |
|---|---:|---:|---:|
| Direct to Ollama | 226.5 s | 20 | 0 |
| Through PAIR | 120.3 s | 10 | 10, all `502` at 120.24 to 120.31 s |

Per-request completion times through PAIR: 12.7, 23.7, 35.2, 48.4, 58.5, 70.7, 81.5, 92.8, 104.5, 115.6 s, then ten failures at 120.2 to 120.3 s. Every request that would have started generating after the 120 s mark was dropped. Proxy log lines (debug level), one per failed request:

```
12:04:58.xxx [ollama-proxy] DEBUG proxy request complete id=... node_id=a9489f3b-... method=POST path=/v1/chat/completions target=127.0.0.1:11434 status=502 duration_ms=120002 ttfb_ms=0 err="net/http: timeout awaiting response headers"
```

GPU utilization on the node fell to zero within one second of the 502s, so Ollama cancelled the orphaned queue entries when the proxy closed the connections. No work was wasted, but the requests were lost.

## Reproduction 2 — cold load (cluster, model only on the peer)

1. Node B holds `deepseek-r1:14b` (9 GB) on a slow disk; cold load takes 2 to 3 minutes.
2. From node A, `POST /v1/chat/completions` for that model to node A's PAIR proxy. PAIR correctly routes it to node B.

Observed:

```
11:00:20  request sent
11:02:20.115 [ollama-proxy] DEBUG proxy request complete id=65 node_id=70506f7d-... method=POST path=/v1/chat/completions target=192.168.x.x:11435 status=502 duration_ms=120002 ttfb_ms=0 err="net/http: timeout awaiting response headers"
```

Node B's Ollama abandoned the load when the connection dropped (`/api/ps` was empty afterwards). A retry 30 s later succeeded in 31.6 s because the file was by then in page cache.

## Confirmation that the limit is queue depth, not the model

Same node, same `qwen3.6:27b`, same client, 8 concurrent requests instead of 20 so the deepest queue position starts before 120 s:

| Path | Wall clock | Succeeded | Failed |
|---|---:|---:|---:|
| Direct to Ollama | 86.5 s | 8 | 0 |
| Through PAIR | 85.6 s | 8 | 0 |

Per-request completions through PAIR: 11.4, 22.4, 32.6, 42.6, 52.9, 64.4, 75.1, 85.6 s. No 502s. The only variable between this run and the 10-of-20 failure above is how many requests were queued.

## Expected

Either of:

- No fixed header timeout for inference routes, or a much longer default (Ollama's own `OLLAMA_LOAD_TIMEOUT` defaults to 5 minutes, and queued generation has no bound at all), with the request-level timeout left to the client.
- A configurable limit (flag on `ollama-proxy`, entry in `settings.json`, or a per-engine setting in the desktop application), and a line in the proxy README and troubleshooting doc stating the default and the error text it produces.

## Actual

A silent 120 s limit that fails requests the engine would have served, most visibly for exactly the workload PAIR is aimed at (many concurrent independent requests against a single-slot engine) and for large models on slow storage.

## Why this matters for the scheduler

The scheduler counts pending jobs and forwards immediately rather than queueing, so a burst of N requests lands in the engines' own queues. With a 120 s header timeout, the effective maximum burst size through PAIR is `120 s / per-request time` per node. For the 27B example above that is about 10 requests per node regardless of how many the client sends.

## Workaround

None inside PAIR. Keep bursts small enough that the deepest queue position starts within 120 s, or pre-load models with a direct `keep_alive` request before routing through PAIR.

## Environment notes

Both PAIR nodes were run headless from the release archive with `nvpair-tui` inside tmux, `NVPAIR_LOG_LEVEL=debug`. Ollama was pre-existing on both nodes and adopted, not installed by PAIR. Full request logs, the load generator, and GPU samples are in the reporter's bench directory and can be attached on request.
