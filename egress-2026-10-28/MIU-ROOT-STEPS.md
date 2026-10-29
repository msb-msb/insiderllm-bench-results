# Root steps for Miu (Mark runs these; paste back all output)

Already running on Miu as minotaur (started by Claude, rootless):
- llama-server, CPU only, 127.0.0.1:8080 (Qwen3.5-0.8B-Q8_0 from LLM_repo)
- tinyproxy allowlist on 127.0.0.1:8888 (allow: huggingface.co, pypi.org, files.pythonhosted.org)

```bash
E=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/2af3e31d-5e96-40f7-be1f-07b6ab2627a8/scratchpad/egress
ss -ltn | grep -E ':8080|:8888'          # both must be listening first

# --- B1. dedicated user + the rule -------------------------------------
sudo useradd --create-home --shell /bin/bash agent
sudo install -o agent -g agent -m 755 "$E/fake-agent.sh" /home/agent/fake-agent.sh
sha256sum /home/agent/fake-agent.sh "$E/agent-egress.nft"
#   expect 7276e33a…42335 and 16ce3397…281888
cat "$E/agent-egress.nft"
sudo nft -c -f "$E/agent-egress.nft" && echo "syntax OK"
sudo nft -f "$E/agent-egress.nft"
sudo nft list table inet agent_egress

# --- B2. agent user, no proxy: outside blocked, local model works ---------
sudo -u agent -i /home/agent/fake-agent.sh

# --- C. agent user through the allowlist proxy ----------------------------
P='https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888 no_proxy=127.0.0.1,localhost'
sudo -u agent -i env $P /home/agent/fake-agent.sh
sudo -u agent -i env $P curl -sS -m 10 -o /dev/null -w 'allowlisted: HTTP %{http_code}\n' https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next
sudo -u agent -i env $P curl -sS -m 10 --noproxy '*' -o /dev/null -w 'HTTP %{http_code}\n' https://huggingface.co/ ; echo "(tool ignoring the proxy, exit $?)"
tail -4 "$E/tpd/tinyproxy.log"

# --- control: your own user is untouched ----------------------------------
curl -sS -m 5 -o /dev/null -w 'minotaur -> example.com: HTTP %{http_code}\n' https://example.com/

# --- D. detection: the kernel log lines + counters ------------------------
journalctl -k --since "-10 min" --no-pager -g agent-egress | tail -6
sudo nft list table inet agent_egress | grep -E 'counter|log'

# --- E (optional). hosts-file sinkhole for the known routify hosts -------
printf '%s\n' '# agent-egress test' \
  '0.0.0.0 routify-file-proxy-sg.oss-ap-southeast-1.aliyuncs.com' \
  '0.0.0.0 routify-file-proxy-sg.ap-southeast-1.oss.aliyuncs.com' | sudo tee -a /etc/hosts
getent hosts routify-file-proxy-sg.oss-ap-southeast-1.aliyuncs.com
getent hosts example.com      # anything not on the list still resolves
```

## Cleanup (undo everything above)

```bash
sudo nft delete table inet agent_egress
sudo userdel -r agent
sudo sed -i '/^# agent-egress test$/,+2d' /etc/hosts
grep -c routify /etc/hosts                     # expect 0
sudo nft list tables | grep agent_egress       # expect nothing
id agent                                       # expect "no such user"
```

Claude stops the rootless llama-server and tinyproxy afterwards.
