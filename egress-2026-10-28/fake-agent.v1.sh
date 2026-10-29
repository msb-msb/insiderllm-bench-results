#!/bin/sh
# fake-agent.sh: stands in for an agent's bash tool.
# Tries one outside host by name, one by bare IP, then the local model.
# LLAMA_URL = llama-server over TCP; LLAMA_SOCK = llama-server over a unix socket.
out() { printf '%-30s ' "$1"; }
ask_model() {
  r=$(curl -sS -m 30 "$@" -d '{"prompt":"The capital of France is","n_predict":4,"temperature":0}' 2>&1) \
    && printf '%s\n' "$r" | python3 -c 'import json,sys; print("model says:", repr(json.load(sys.stdin)["content"]))' \
    || printf '%s\n' "$r"
}

out "outside, by name:"
curl -sS -m 5 -o /dev/null -w 'HTTP %{http_code}\n' https://example.com/ 2>&1 | grep -v '^HTTP 000$'
out "outside, by IP:"
curl -sS -m 5 -o /dev/null -w 'HTTP %{http_code}\n' http://1.1.1.1/ 2>&1 | grep -v '^HTTP 000$'

if [ -n "$LLAMA_SOCK" ]; then
  out "llama-server (unix socket):"
  ask_model --unix-socket "$LLAMA_SOCK" http://localhost/completion
else
  u=${LLAMA_URL:-http://127.0.0.1:8080}
  out "llama-server ($u):"
  ask_model "$u/completion"
fi
