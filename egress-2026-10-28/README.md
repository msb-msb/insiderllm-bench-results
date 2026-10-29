# Agent egress tests: namespaces, Docker, nftables, allowlist proxy, 2026-10-28

Evidence record for the draft "Stop Your Local Agent Calling Out: Default-Deny Egress" (`drafts/stop-your-local-agent-calling-out/`). A stand-in agent (`fake-agent.sh`) tries the internet by name, by bare IPv4 (and in the second version, by bare IPv6), then asks a local llama-server for four tokens. Every method was judged on those lines: outside blocked, model still answering. File hashes are in `SHA256SUMS`.

## Common

| item | value |
|---|---|
| date | 2026-10-28 (all times PDT) |
| engine | llama.cpp `llama-server` v0.4.0, `version: 0.4.0-dev (build 1, commit 5266f24)` on both rigs |
| model | `LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf`, sha256 `0ad885ffd4bb022fc4f0d33a3308fa108ef8613159d3b3a67e23abca056b7a6c` (matches the repo's `SHA256SUMS`; Rushuna's working copy at `~/bench-models/` hashes the same) |
| prompt | `"The capital of France is"`, `n_predict` 4, temperature 0; answer `' Paris.\nThe'` everywhere it was reachable |
| test script | `fake-agent.v1.sh` (sha256 `7276e33a...42335`, 3 lines out) for every run up to the Miu first root run; `fake-agent.sh` (sha256 `69cba599...da1f41`, adds `http://[2606:4700:4700::1111]/`) for the Miu re-run and nothing else |
| tinyproxy | Ubuntu `tinyproxy-bin_1.11.1-3ubuntu0.1_amd64.deb`, run unprivileged from the extracted package; `FilterDefaultDeny Yes`, allowlist `huggingface.co`, `pypi.org`, `files.pythonhosted.org` |

## What ran where

| box | OS / kernel | what ran | as | evidence here |
|---|---|---|---|---|
| Rushuna (RTX 3060) | Ubuntu 24.04.5, 6.8.0-136, systemd 255.4-1ubuntu8.18 | baseline; `unshare -rn` (fails, AppArmor userns restriction); `unshare -Un` over TCP (model unreachable) and over a unix socket (target state); nested `unshare -Urm` (blocked); `systemd-run --user` with `IPAddressDeny=` and `PrivateNetwork=` (both let everything out); tinyproxy allowlist, uppercase-vs-lowercase proxy variables, `--noproxy '*'` bypass. 00:03 to 00:12 | minotaur, no root | `rushuna/srv-*.log`, `tinyproxy-rushuna/` (conf, allowlist, log). The fake-agent outputs for these runs are in the article as printed in the session; no separate terminal capture was saved. |
| Miu (GTX 1650, llama-server on CPU via `CUDA_VISIBLE_DEVICES=`) | Ubuntu 24.04.5, 6.8.0-147 | Docker `--network none` with the llama-server socket bind-mounted; socat TCP-to-socket bridge inside the container; nested `unshare -Urm` inside the container (blocked) | minotaur via the docker group (root-equivalent) | `container/Dockerfile.egress-test-agent`; outputs in the article |
| Miu | same | **First root run** (Mark), 10:56 to 11:04: `agent` user, nftables rule **v1** (`agent-egress.v1.nft`), tests without and with the proxy, control as minotaur, kernel log, hosts-file sinkhole | root (sudo) for setup, `agent` for tests | `miu-root-run.log` (raw `script` capture), `miu-root-run.clean.txt`, `MIU-ROOT-STEPS.md` (the commands), `miu-v1-ownerless-drops.journal.txt`, `tinyproxy-miu/` |
| Miu | same | v1 vs fixed rule, and IPv6 coverage, in a throwaway container with its own network namespace (`--cap-add NET_ADMIN`) | root inside the container | `container/check.sh`, `container/check6.sh`, `container/Dockerfile`, outputs `*.session.txt` (the run quoted in the article) and `*.recapture.txt` (re-run at 17:24, same result) |
| Miu | same | **Re-run** (Mark), 17:12 to 17:20: fixed rule (`agent-egress.nft`) loaded 17:17:24, same tests plus the IPv6 line, 30 s wait, count of drop lines without a UID, then cleanup | root (sudo) / `agent` | `miu-rerun.log` (raw), `miu-rerun.clean.txt`, `MIU-RERUN.md`, `miu-llama-server-rerun.log`, `tinyproxy-miu/tinyproxy.log` |
| Tamanna | Ubuntu 26.04.1 | `bwrap --unshare-net ... true` starts (bwrap-userns-restrict profile present). Full test not run. | minotaur | none |

## Findings recorded here

- **v1 rule bug.** `meta skuid != "agent" accept` does not match packets whose socket has no owning file (the kernel's own ACKs after a program closes a TCP socket); `nft_meta_get_eval_skugid` returns false and the rule breaks (`NFT_BREAK`, `net/netfilter/nft_meta.c`, v6.8). Those packets fell through to the drop rule. Between loading v1 (about 11:02) and the end of the first session (11:04:39) the drop rule logged 95 lines: 1 from the agent (`UID=1002`), 94 with no UID, to 11 other destinations (`miu-v1-ownerless-drops.journal.txt`). The two lines Mark asked about, to 104.20.23.154:443 (example.com: the minotaur control curl) and 108.138.246.85:443 (huggingface.co: tinyproxy's upstream connection, running as minotaur), are among them. v1 stayed loaded on Miu from about 11:02 until Mark deleted it at about 17:05.
- **Fix.** `meta skuid "agent" jump agent`, with the deny rules in the `agent` chain; ownerless packets never jump and leave by the `accept` policy. Re-run: rule loaded 17:17:24 until cleanup (before 17:20:32); 9 kernel log lines, all the agent's (8 DNS refusals, 1 SYN to 1.1.1.1 with `UID=1002`); drop lines without a UID after the 30 s wait: **0**.
- **IPv6.** Neither Miu nor Rushuna has an IPv6 route; a bare-IPv6 connect fails with `ENETUNREACH` before netfilter sees a packet, so the re-run's IPv6 line proves nothing about the rule there. With a dummy-interface IPv6 default route in the container, the agent's IPv6 SYN went out with no rule (timed out) and was refused with the fixed rule (drop counter 2).
- **Hosts sinkhole** (first root run): the two routify hostnames resolve to `0.0.0.0`; `example.com` still resolves.
- **Cleanup**: the re-run session ends with the cleanup block (table deleted, `agent` removed, hosts lines removed); afterwards `id agent` reports no such user and `/etc/hosts` has no routify lines.

## Notes

- The raw `script` logs contain terminal control codes and NUL bytes; the `.clean.txt` copies have those stripped and nothing else changed. Commands appear more than once in them because the terminal echoed pasted blocks.
- Private LAN addresses are redacted to `192.168.x.x` in the public mirror by `sync-bench-results-mirror.sh`.
