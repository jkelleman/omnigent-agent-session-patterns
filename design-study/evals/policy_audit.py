"""Extract every ASK/DENY reason string from Omnigent's built-in policies and classify it.

Usage (from the repo root):
    python design-study/evals/policy_audit.py . > design-study/evals/results/policy-reasons.txt

Reads omnigent/policies/builtins/*.py with the ast module. It collects reason
strings from verdict dicts, the _deny/_ask helpers, reason keyword arguments,
and default reason parameters, then checks each for a named rule owner, a
named agent, a next move, and configuration syntax. Reasons built entirely at
runtime are counted but can't be read statically.
"""
import ast, json, re, sys
from pathlib import Path
root = Path(sys.argv[1]) / "omnigent/policies/builtins"

def render(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "{…}" for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        l, r = render(node.left), render(node.right)
        return None if l is None or r is None else l + r
    return None

rows = []
for f in sorted(root.glob("*.py")):
    tree = ast.parse(f.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict): continue
        keys = {k.value: v for k, v in zip(node.keys, node.values) if isinstance(k, ast.Constant)}
        res = keys.get("result")
        if not (isinstance(res, ast.Constant) and res.value in ("ASK", "DENY")) or "reason" not in keys: continue
        text = render(keys["reason"])
        rows.append({"file": f.name, "line": node.lineno, "verdict": res.value, "text": text, "kind": "dict"})
    for node in ast.walk(tree):
        # _deny("...") / _ask("...") helpers and PolicyResponse(reason="...")
        if isinstance(node, ast.Call):
            fn = getattr(node.func, "id", getattr(node.func, "attr", ""))
            if fn in ("_deny", "_ask") and node.args:
                rows.append({"file": f.name, "line": node.lineno, "verdict": "DENY" if fn == "_deny" else "ASK",
                             "text": render(node.args[0]), "kind": "helper"})
            for kw in node.keywords:
                if kw.arg in ("reason", "deny_reason", "ask_reason") and fn not in ("_deny", "_ask"):
                    t = render(kw.value)
                    if t: rows.append({"file": f.name, "line": node.lineno, "verdict": "?", "text": t, "kind": "kwarg"})
        # default reason strings on factory parameters
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.args + node.args.kwonlyargs
            defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults) + list(node.args.kw_defaults)
            for a, d in zip(args, defaults):
                if d is not None and "reason" in a.arg:
                    t = render(d)
                    if t: rows.append({"file": f.name, "line": d.lineno, "verdict": "DENY" if "deny" in a.arg else "?", "text": t, "kind": "default"})

OWNER = re.compile(r"\b(admin|administrator|agent'?s? author|agent developer|your (workspace|organization|org)|you set|server-wide|organization)\b", re.I)
NAMED_AGENT = re.compile(r"\{…\}\s+(wants|is|has)|\b(Claude|Codex|Cursor|Polly|sub-agent)\b")
GENERIC_AGENT = re.compile(r"\b(the agent|agent wants|Agent wants)\b", re.I)
NEXT = re.compile(r"(^|[.:;]\s+|\bor\s+)(Ask|Remove|Set|Use|Run|Try|Retry|Wait|Change|Approve|Inspect|List|Switch|Add|Open)\b|\bApprove\?")
CONFIG = re.compile(r"\b[a-z_]+=(true|false|\d+)\b|\bargs\.[a-z_]+", re.I)
POLICY_WORD = re.compile(r"\bpolicy\b", re.I)

seen=set(); dedup=[]
for r in rows:
    k=(r["file"], r["text"])
    if r["text"] is not None and k in seen: continue
    seen.add(k); dedup.append(r)
rows=dedup
static = [r for r in rows if r["text"] is not None]
for r in static:
    t = r["text"]
    r.update(owner=bool(OWNER.search(t)), generic_agent=bool(GENERIC_AGENT.search(t)),
             next_move=bool(NEXT.search(t)), config=bool(CONFIG.search(t)),
             says_policy_no_owner=bool(POLICY_WORD.search(t)) and not OWNER.search(t))
n = len(static)
summary = {
  "reason_sites": len(rows), "static_text": n, "dynamic_unreadable": len(rows) - n,
  "ask": sum(r["verdict"] == "ASK" for r in static), "deny": sum(r["verdict"] == "DENY" for r in static),
  "names_owner": sum(r["owner"] for r in static),
  "generic_agent": sum(r["generic_agent"] for r in static),
  "has_next_move": sum(r["next_move"] for r in static),
  "config_syntax": sum(r["config"] for r in static),
  "says_policy_without_owner": sum(r["says_policy_no_owner"] for r in static),
  "files": len({r["file"] for r in rows}),
}
print(json.dumps(summary, indent=1))
(Path(__file__).parent / "results" / "policy-reasons.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
for r in static: print(f'{r["verdict"]:4} {r["file"]}:{r["line"]} owner={int(r["owner"])} next={int(r["next_move"])} | {r["text"][:110]!r}')
