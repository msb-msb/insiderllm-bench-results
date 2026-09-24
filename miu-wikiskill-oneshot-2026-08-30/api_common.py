"""Shared API plumbing: .env loading (project convention) + request shape."""
import os, json

ENV_FILE = os.path.expanduser("~/Desktop/InsiderLLM/.env")
MODEL = "claude-opus-5"

def load_env():
    """Match x-poster.py:61 -- read the project .env into os.environ."""
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not found in environment or .env")

def request_shape(bundle, ttl="1h"):
    """The exact system/messages shape sent for compilation.

    cache_control sits on the system block, i.e. the breakpoint is at the end
    of the prefix (task def + deployed prompt + traces). The instruction is the
    user message and is the only content after the breakpoint -- mirroring a
    loop where wiki+traces are the stable bulk and the instruction varies.
    """
    return {
        "system": [{"type": "text", "text": bundle["prefix"],
                    "cache_control": {"type": "ephemeral", "ttl": ttl}}],
        "messages": [{"role": "user", "content": bundle["instruction"]}],
    }
