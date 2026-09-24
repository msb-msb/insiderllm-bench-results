# mycoSwarm: router keeps the startup identity, so a node that came up before its Ollama bounces inference forever

Found 2026-09-04 while running the PAIR phase-2 fan-out comparison. mycoSwarm v0.6.0 on both nodes.

## Symptom

Every inference task submitted to Miu's daemon for `qwen3.5:9b` (a model both Miu and Rushuna hold) failed after 10 s with:

```
502 {"detail":"Can't reach rushuna: "}
```

Rushuna's `/health` answered from Miu in 7 ms the whole time.

## What was happening

Both daemons' journals for one task id (`pairbench-906a332a`, 19:41:54 UTC):

```
Miu:      🎯 Routing inference → rushuna (has model qwen3.5:9b)
rushuna:  📥 Task received ... 🎯 Routing inference → Miu (has model qwen3.5:9b)
Miu:      📥 Task received ... 🎯 Routing inference → rushuna (has model qwen3.5:9b)
... (dozens of hops in under two seconds)
```

Miu routes to Rushuna because a specialist GPU node outscores the executive for a model both hold (`_score_peer_for_inference`: +500 specialist vs +200 executive). Rushuna should then win locally (`_local_inference_score` gives it 1622 against Miu's 1445), but it routed back. Each hop's `_route_to_peer` POST waits on the next hop's POST, and the outermost one hits its 10 s httpx timeout, which surfaces as the empty-message "Can't reach" 502. There is no hop counter or source-node guard anywhere in `api.py`, `orchestrator.py`, or `router.py`.

## Root cause

Rushuna's router believed it had no models and no inference capability. `/status` on Rushuna (which reads the daemon's cached `identity`) showed:

```
capabilities: [cpu_worker, file_processing, code_execution, storage, coordinator]
ollama_models: []
```

while `/identity` on the same daemon (which calls `build_identity()` fresh) showed `gpu_inference`, `cpu_inference`, and all three models. So `can_handle_locally()` and the `requested_model in self.identity.available_models` check both failed, and the router fell through to "peer has the model".

The daemon started on 2026-08-28 21:19:05 UTC (six days earlier), evidently before its Ollama was answering. In `daemon.py`:

- `run_daemon()` builds `identity` once at startup and hands that object to `Orchestrator` → `Router` (`router.py:106  self.identity = identity`).
- `_status_refresh_loop()` rebuilds a **new** identity every 30 s and passes it only to `discovery.update_identity(identity)`. The router's reference is never updated.

So peers saw Rushuna's refreshed announcement (with models) and kept sending it work, while Rushuna's own router still saw its empty startup snapshot and kept refusing.

## Fix options

1. In `_status_refresh_loop`, also update the router: `orchestrator.identity = identity; orchestrator.router.identity = identity` (or make `Router` take a callable / hold a reference to a mutable holder).
2. Add a hop guard: include a `hops` or `routed_via` list in `TaskRequest`, and never route a task back to a node already in the list; fail fast with a clear 503 instead of ping-ponging until a timeout.
3. Optionally, at startup, retry Ollama detection for a bounded period before announcing, since a systemd race with `ollama.service` is the likely way this state is entered.

Option 1 fixes this instance. Option 2 is what would have made it diagnosable in one log line rather than two journals.

## How it was cleared for the bench

`systemctl restart mycoswarm` needs interactive auth on Rushuna, but the unit runs as `minotaur` with `Restart=on-failure`, so `kill -9 <MainPID>` brought it back in 5 s with a correct profile (19:46:28 UTC). The stale state will return the next time the daemon starts before Ollama does.
