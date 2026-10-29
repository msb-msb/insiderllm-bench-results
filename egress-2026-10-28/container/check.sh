#!/bin/sh
for f in /r/agent-egress.v1.nft /r/agent-egress.nft; do
  echo "=== $(basename $f)"
  nft delete table inet agent_egress 2>/dev/null
  nft -f $f || exit 1
  curl -sS -m 5 -o /dev/null -w 'root -> example.com: HTTP %{http_code}\n' https://example.com/
  sleep 3
  echo "drop counter after root's request: $(nft list table inet agent_egress | grep -o 'agent-egress-drop' -B0 | wc -l) rule, $(nft list table inet agent_egress | grep 'agent-egress-drop' | grep -o 'packets [0-9]*')"
  su agent -s /bin/sh -c "curl -sS -m 5 -o /dev/null -w 'HTTP %{http_code}\n' http://1.1.1.1/ 2>&1; curl -sS -m 5 -o /dev/null https://example.com/ 2>&1" | sed 's/^/agent: /'
  echo "drop counter after agent's requests: $(nft list table inet agent_egress | grep 'agent-egress-drop' | grep -o 'packets [0-9]*'); dns: $(nft list table inet agent_egress | grep 'agent-egress-dns' | grep -o 'packets [0-9]*')"
done
