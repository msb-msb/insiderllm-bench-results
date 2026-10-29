#!/bin/sh
ip link add d0 type dummy && ip link set d0 up && ip -6 addr add fd00:e::2/64 dev d0 nodad && ip -6 route add default via fd00:e::1 dev d0 && echo "(IPv6 default route via a dummy interface: packets leave, nothing answers)"
echo "--- no rule, agent, bare IPv6 (route exists, nobody answers):"
su agent -s /bin/sh -c "curl -sS -m 3 -o /dev/null -w 'HTTP %{http_code}\n' 'http://[2606:4700:4700::1111]/' 2>&1"
nft -f /r/agent-egress.nft
echo "--- fixed rule, agent, bare IPv6:"
su agent -s /bin/sh -c "curl -sS -m 3 -o /dev/null -w 'HTTP %{http_code}\n' 'http://[2606:4700:4700::1111]/' 2>&1"
nft list table inet agent_egress | grep 'agent-egress-drop' | grep -o 'packets [0-9]*'
