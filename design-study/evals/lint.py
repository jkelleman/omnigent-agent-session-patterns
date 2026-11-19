"""Rule-based baseline for the message rubric (v2).

Runs with no dependencies and no API key. String rules can approximate some
checks (Actor, the rule owner in Cause, configuration syntax in a message).
Others need a judge that reads the message in context (whether a Next move is
available to this reader). KEYWORD-CHECKER.md explains the v1 gaps and the
v2 fixes.

v2 changes:
  1. Reads the `context` field, so controls visible on the same surface
     (Approve and Deny buttons, a visible session title) count.
  2. Scores only the checks that apply to each surface. A card title or a
     resolved label isn't expected to carry every part of a message.
  3. Broader phrase patterns: conditional consequences ("if you deny it"),
     hedged activity ("may still be working"), and imperatives mid-sentence
     ("To clean that folder, run the command yourself").
  4. Scores are normalized to 10 over the applicable checks.

Usage:
    python evals/lint.py                 # print table
    python evals/lint.py --out evals/results/lint-baseline.md
"""

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
CHECKS = ["actor", "action", "cause", "consequence", "next_move"]

# Which checks apply on each surface. Checks left out are scored "n/a".
APPLIES = {
    "approval card message": CHECKS,
    "error in transcript": CHECKS,
    "approval card title": ["actor", "action"],
    "sidebar badge tooltip": ["actor", "action", "consequence", "next_move"],
    "resolved approval card label": ["actor", "action", "consequence", "next_move"],
}

AGENTS = r"\b(Claude Code|Claude|Codex|Cursor|Polly|Pi|Devin|Goose|Kiro|Antigravity)\b"
# Context that tells this agent apart from the reader's other sessions:
# a parent agent, a session or branch name, a repo, or where it runs.
AGENT_CONTEXT = (
    r"(\bsub-agent\b|\bin session\b|\bon your laptop\b|\bin a cloud sandbox\b"
    r"|\b[a-z0-9]+(?:-[a-z0-9]+)+\b"            # kebab-case session names (auth-retry)
    r"|\b[a-z0-9._-]+/[a-z0-9._/-]+\b)"         # repos and branches (acme/web, feature/x)
)
PLAIN_VERBS = (
    r"\b(push(es|ed|ing)?|run(s|ning)?|ran|delete[sd]?|open(s|ed)?|edit(s|ed)?|write[s]?"
    r"|fetch(es|ed)?|hit[s]?|approved|denied|allowed|answer|continue[sd]?|stopped"
    r"|working|retry|skip(ped)?)\b"
)
JARGON = r"\b(operation|gated|tool call|blast-radius|high-blast-radius|elevated|prompt)\b"
OWNER = r"\b(your (workspace )?admin|agent's author|agent file|you set|set by you)\b"
REASON = (
    r"\b(because|needs? your|aren't allowed|isn't allowed|can only|nobody answered"
    r"|lost contact|couldn't|set this rule|requires)\b"
)
CONSEQUENCE = (
    r"(if you (deny|approve|don't answer|do nothing)|will be denied|will (stop|skip|continue|tell|retry|wait)"
    r"|stopped|still on|may still|didn't go through|nothing was pushed|without asking|always allowed)"
)
CONFIG = r"\b[a-z_]+=(True|False|true|false|\d+)\b"
IMPERATIVE = r"(?:^|[.:;,]\s+|\bor\s+)(Ask|ask|Open|open|Run|run|Change|change|Retry|retry|Fork|fork|Send|send|Reconnect|reconnect)\b"
NOTHING_NEEDED = r"(\bAsk again\b|\bWe'll update\b|\bnothing needed\b)"
BUTTONS_IN_CONTEXT = r"\bApprove\b.*\b(Deny|Reject)\b|\banswer options\b"


def score(row: dict) -> dict:
    """Score one message. Checks that don't apply on its surface are None."""
    text, context = row["text"], row.get("context", "")
    applies = APPLIES.get(row.get("surface", ""), CHECKS)
    s = {}

    has_agent = re.search(AGENTS, text)
    if has_agent and re.search(AGENT_CONTEXT, text.replace(has_agent.group(0), "")):
        s["actor"] = 2
    elif has_agent or "session title is visible" in context:
        s["actor"] = 1
    else:
        s["actor"] = 0

    verbs, jargon = re.search(PLAIN_VERBS, text, re.I), re.search(JARGON, text, re.I)
    s["action"] = 2 if verbs and not jargon else 1 if verbs or jargon else 0

    s["cause"] = 2 if re.search(OWNER, text, re.I) else 1 if re.search(REASON, text, re.I) else 0

    hits = {m.group(0).lower() for m in re.finditer(CONSEQUENCE, text, re.I)}
    s["consequence"] = 2 if len(hits) >= 2 else 1 if hits else 0

    if re.search(CONFIG, text):
        s["next_move"] = 0  # a configuration change the supervising reader usually can't make
    elif re.search(IMPERATIVE, text) or re.search(NOTHING_NEEDED, text):
        s["next_move"] = 2
    elif row.get("kind") == "approval" and re.search(BUTTONS_IN_CONTEXT, context):
        s["next_move"] = 2  # the answer controls sit on the same surface
    else:
        s["next_move"] = 0

    return {c: (s[c] if c in applies else None) for c in CHECKS}


def total(sc: dict) -> float:
    """Score out of 10 over the applicable checks."""
    vals = [v for v in sc.values() if v is not None]
    return round(10 * sum(vals) / (2 * len(vals)), 1) if vals else 0.0


def passes(sc: dict) -> bool:
    vals = [v for v in sc.values() if v is not None]
    return total(sc) >= 7 and min(vals) > 0


def load(path: Path = HERE / "messages.jsonl") -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def cell(v):
    return "n/a" if v is None else str(v)


def table(rows: list[dict], scores: dict) -> str:
    out = ["| id | variant | text | A | Ac | C | Co | N | score | pass |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sc = scores[r["id"]]
        text = r["text"] if len(r["text"]) <= 70 else r["text"][:67] + "…"
        out.append(f"| {r['id']} | {r['variant']} | {text} | "
                   + " | ".join(cell(sc[c]) for c in CHECKS)
                   + f" | {total(sc)} | {'yes' if passes(sc) else 'no'} |")
    return "\n".join(out)


def summary(rows: list[dict], scores: dict) -> str:
    lines = []
    for variant in ("omnigent", "rewrite"):
        group = [r for r in rows if r["variant"] == variant]
        mean = sum(total(scores[r["id"]]) for r in group) / len(group)
        passed = sum(passes(scores[r["id"]]) for r in group)
        lines.append(f"- **{variant}**: mean {mean:.1f}/10, {passed}/{len(group)} pass")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    rows = load()
    scores = {r["id"]: score(r) for r in rows}
    md = ("# Lint baseline v2\n\nRule-based scores (A = Actor, Ac = Action, C = Cause, "
          "Co = Consequence, N = Next move). Scores are out of 10 over the checks that apply "
          "on each surface; n/a marks a check that doesn't apply. See `KEYWORD-CHECKER.md`.\n\n"
          + summary(rows, scores) + "\n\n" + table(rows, scores) + "\n")
    if args.out:
        args.out.write_text(md)
        print(f"Wrote {args.out}")
    print(md)


if __name__ == "__main__":
    main()
