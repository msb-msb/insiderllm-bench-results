"""Pull the deployed intent prompt + validators straight from solo.py by AST.

Importing mycoswarm.solo drags in psutil/httpx; we only need literals. Parsing
the source guarantees we use the exact deployed string, and records its hash so
a later drift is detectable.
"""
import ast, hashlib

SOLO = "/home/minotaur/Desktop/mycoSwarm/src/mycoswarm/solo.py"
_WANT = {"_INTENT_SYSTEM_PROMPT", "_INTENT_DEFAULT",
         "_VALID_TOOLS", "_VALID_MODES", "_VALID_SCOPES"}
_WANT_RE = {"_PAST_REFERENCE_RE"}

def _load():
    src = open(SOLO).read()
    tree = ast.parse(src)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id in _WANT:
                out[t.id] = ast.literal_eval(node.value)
            if isinstance(t, ast.Name) and t.id in _WANT_RE:
                # re.compile("..."): grab the literal pattern, not the object
                out[t.id] = ast.literal_eval(node.value.args[0])
    missing = (_WANT | _WANT_RE) - set(out)
    if missing:
        raise RuntimeError(f"not found in solo.py: {missing}")
    out["_SOLO_SHA256"] = hashlib.sha256(src.encode()).hexdigest()
    return out

_g = _load()
INTENT_SYSTEM_PROMPT = _g["_INTENT_SYSTEM_PROMPT"]
INTENT_DEFAULT = _g["_INTENT_DEFAULT"]
VALID_TOOLS = _g["_VALID_TOOLS"]
VALID_MODES = _g["_VALID_MODES"]
VALID_SCOPES = _g["_VALID_SCOPES"]
PAST_REFERENCE_RE = __import__("re").compile(_g["_PAST_REFERENCE_RE"])
SOLO_SHA256 = _g["_SOLO_SHA256"]

def detect_past_reference(q: str) -> bool:
    return bool(PAST_REFERENCE_RE.search(q))

if __name__ == "__main__":
    print("prompt chars:", len(INTENT_SYSTEM_PROMPT))
    print("tools:", sorted(VALID_TOOLS)); print("modes:", sorted(VALID_MODES))
    print("scopes:", sorted(VALID_SCOPES)); print("default:", INTENT_DEFAULT)
    print("past-ref regex chars:", len(_g["_PAST_REFERENCE_RE"]))
    print("solo.py sha256:", SOLO_SHA256[:16])
