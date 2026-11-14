"""Rule-based baseline for the message rubric.

Runs with no dependencies and no API key. It's deliberately crude: the point
is to show which checks string rules can approximate (Actor, Cause owner,
config-in-the-message) and which need a judge that reads meaning
(Consequence, whether a Next move is actually available to this reader).

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

AGENTS = r"\b(Claude Code|Codex|Cursor|Polly|Pi|Devin|Goose|Kiro|Antigravity)\b"
AGENT_CONTEXT = r"\b(sub-agent|session|on your laptop|in [a-z0-9/_-]+-[a-z0-9/_-]+|auth-retry|release/|feature/)"
PLAIN_VERBS = r"\b(push|pushes|run|runs|delete|deletes|open|opens|edit|edits|write|writes|hit|hits|create|creates|approved|denied|allowed)\b"
JARGON = r"\b(operation|gated|tool call|blast-radius|high-blast-radius|elevated|prompt)\b"
OWNER = r"\b(your (workspace )?admin|agent's author|agent file|you set|set by you)\b"
REASON = r"\b(because|need|needs|aren't allowed|can only|isn't allowed|nobody answered|lost contact|couldn't)\b"
CONSEQUENCE = r"(if you don't answer|will be denied|will stop|stopped|still on|may still|didn't go through|will continue|without asking|always allowed)"
CONFIG = r"\b[a-z_]+=(True|False|true|false|\d+)\b"
NEXT_MOVE = r"(^|[.:] )(Ask|Open|Run|Change|Deny|Approve|Retry)\b|\bAsk again\b|We'll update"


def score(text: str) -> dict:
    s = {}
    has_agent = re.search(AGENTS, text)
    s["actor"] = 2 if has_agent and re.search(AGENT_CONTEXT, text) else 1 if has_agent else 0

    verbs, jargon = re.search(PLAIN_VERBS, text, re.I), re.search(JARGON, text, re.I)
    s["action"] = 2 if verbs and not jargon else 1 if verbs or jargon else 0

    s["cause"] = 2 if re.search(OWNER, text, re.I) else 1 if re.search(REASON, text, re.I) else 0

    hits = len(re.findall(CONSEQUENCE, text, re.I))
    s["consequence"] = 2 if hits >= 2 else 1 if hits == 1 else 0

    if re.search(CONFIG, text):
        s["next_move"] = 0  # a config change the supervising reader usually can't make
    else:
        s["next_move"] = 2 if re.search(NEXT_MOVE, text) else 0
    return s


def load(path: Path = HERE / "messages.jsonl") -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def passes(sc: dict) -> bool:
    return sum(sc[c] for c in CHECKS) >= 7 and min(sc[c] for c in CHECKS) > 0


def table(rows: list[dict], scores: dict) -> str:
    out = ["| id | variant | text | A | Ac | C | Co | N | total | pass |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sc = scores[r["id"]]
        text = r["text"] if len(r["text"]) <= 70 else r["text"][:67] + "…"
        total = sum(sc[c] for c in CHECKS)
        out.append(f"| {r['id']} | {r['variant']} | {text} | "
                   + " | ".join(str(sc[c]) for c in CHECKS)
                   + f" | {total} | {'yes' if passes(sc) else 'no'} |")
    return "\n".join(out)


def summary(rows: list[dict], scores: dict) -> str:
    lines = []
    for variant in ("omnigent", "rewrite"):
        group = [r for r in rows if r["variant"] == variant]
        mean = sum(sum(scores[r["id"]][c] for c in CHECKS) for r in group) / len(group)
        passed = sum(passes(scores[r["id"]]) for r in group)
        lines.append(f"- **{variant}**: mean {mean:.1f}/10, {passed}/{len(group)} pass")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    rows = load()
    scores = {r["id"]: score(r["text"]) for r in rows}
    md = ("# Lint baseline\n\nRule-based scores (A = Actor, Ac = Action, C = Cause, "
          "Co = Consequence, N = Next move). See `lint.py` for the rules and their limits.\n\n"
          + summary(rows, scores) + "\n\n" + table(rows, scores) + "\n")
    if args.out:
        args.out.write_text(md)
        print(f"Wrote {args.out}")
    print(md)


if __name__ == "__main__":
    main()
