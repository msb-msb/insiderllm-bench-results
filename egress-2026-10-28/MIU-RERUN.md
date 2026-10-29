# Re-run on Miu with the fixed rule (paste back all output)

Seven steps, run in order. Each step is one fenced block. Every block opens
with the same variable lines, so a block works even in a fresh shell. The two
values made during the run (llama-server's PID, the time the rule went in) are
kept in files under $E.

What changed since the first run:
- the rule: `meta skuid "agent" jump agent` in place of `meta skuid != "agent" accept`
  (agent-egress.nft, sha256 ae02f755...a13871; the first version is kept as agent-egress.v1.nft)
- fake-agent.sh: a bare-IPv6 line (sha256 69cba599...da1f41). Miu has no IPv6
  route, so expect "Couldn't connect" on that line with no log entry for it: the
  connect fails at routing, before the firewall sees a packet. The rule's IPv6
  coverage was checked separately in a container with a dummy IPv6 route.

The `agent` user and the /etc/hosts lines from the first run are still in place.
The old table is gone (you deleted it at ~17:05).

## Step 1. Preconditions: no table, agent user and hosts lines present

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

sudo nft list tables | grep agent_egress || echo "no agent_egress table (expected)"
id agent
grep -A2 '^# agent-egress test$' /etc/hosts
ss -ltn | grep -E ':8080|:8888' || echo "nothing on 8080/8888 (expected)"
```

## Step 2. Load the fixed rule

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

sha256sum "$E/agent-egress.nft"          # expect ae02f7555ae36dc4499ca8d91c4778439c5634e80687708902763ad214a13871
cat "$E/agent-egress.nft"
sudo nft -c -f "$E/agent-egress.nft" && echo "syntax OK"
sudo nft -f "$E/agent-egress.nft"
date '+%Y-%m-%d %H:%M:%S' > "$E/rerun.since"
sudo nft list table inet agent_egress
echo "rule loaded at $(cat "$E/rerun.since")"
```

## Step 3. Install the new test script for the agent user

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

sudo install -o agent -g agent -m 755 "$E/fake-agent.sh" /home/agent/fake-agent.sh
sudo sha256sum /home/agent/fake-agent.sh   # expect 69cba599e636ec0ea5878ab4caa6e87ae3dc57c40579313944ba98aa56da1f41
```

## Step 4. Start llama-server and tinyproxy (as you, no root)

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

CUDA_VISIBLE_DEVICES= "$LLAMA" -m "$MODEL" -ngl 0 -c 2048 --host 127.0.0.1 --port 8080 > "$E/srv-rerun.log" 2>&1 &
echo $! > "$E/llama-rerun.pid"
"$E/tp/usr/bin/tinyproxy" -c "$E/tpd/tinyproxy.conf"
until curl -s -o /dev/null http://127.0.0.1:8080/health; do sleep 1; done
ss -ltn | grep -E ':8080|:8888'          # both must be listening
```

## Step 5. The tests (same as the first run, plus the IPv6 line)

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

echo "=== agent, no proxy"
sudo -u agent -i /home/agent/fake-agent.sh
echo "=== agent, through the proxy"
sudo -u agent -i env $P /home/agent/fake-agent.sh
sudo -u agent -i env $P curl -sS -m 10 -o /dev/null -w 'allowlisted: HTTP %{http_code}\n' https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next
sudo -u agent -i env $P curl -sS -m 10 --noproxy '*' -o /dev/null -w 'HTTP %{http_code}\n' https://huggingface.co/ ; echo "(tool ignoring the proxy, exit $?)"
tail -4 "$E/tpd/tinyproxy.log"
echo "=== control: you"
curl -sS -m 5 -o /dev/null -w 'minotaur -> example.com: HTTP %{http_code}\n' https://example.com/
```

## Step 6. The check the first version failed: wait, then count ownerless drops

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

sleep 30
T=$(cat "$E/rerun.since")
journalctl -k --since "$T" --no-pager -g agent-egress
echo "drop lines without a UID (expect 0): $(journalctl -k --since "$T" --no-pager -g agent-egress-drop | grep -vc 'UID=')"
sudo nft list table inet agent_egress | grep counter
```

## Step 7. Stop llama-server and tinyproxy

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
LLAMA=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.5-0.8b-gguf/Qwen3.5-0.8B-Q8_0.gguf
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'

kill "$(cat "$E/llama-rerun.pid")" "$(cat "$E/tpd/tinyproxy.pid")"
sleep 1
ss -ltn | grep -E ':8080|:8888' || echo "both stopped"
```

The rule, the agent user and the hosts lines stay in place after step 7, for
your review. Cleanup is below.

## Cleanup (after you've reviewed the draft)

```bash
sudo nft delete table inet agent_egress
sudo userdel -r agent
sudo sed -i '/^# agent-egress test$/,+2d' /etc/hosts
grep -c routify /etc/hosts                     # expect 0
sudo nft list tables | grep agent_egress       # expect nothing
id agent                                       # expect "no such user"
```
