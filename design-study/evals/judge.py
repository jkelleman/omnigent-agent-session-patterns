"""LLM-as-judge for the message rubric.

Scores every message in messages.jsonl against rubric.md, in context, and
optionally measures agreement with human scores, which is the step that makes
a judge trustworthy.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY=...
    python evals/judge.py                       # score all messages
    python evals/judge.py --dry-run --id o-force   # print the prompt only
    python evals/judge.py --human evals/human_scores.csv   # also report agreement
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from lint import CHECKS, load, passes, summary, table

HERE = Path(__file__).parent
RUBRIC = (HERE / "rubric.md").read_text()

PROMPT = """You are grading one interface message from a tool that supervises AI coding agents.
Grade it strictly against the rubric below. Score only what the reader can see on this
surface without tapping. Reply with the JSON object described in the rubric and nothing else.

<rubric>
{rubric}
</rubric>

<message>
Kind: {kind}
Surface: {surface}
What else is visible: {context}
Text: {text}
</message>"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(rubric=RUBRIC, **{k: row[k] for k in ("kind", "surface", "context", "text")})


def judge(client, model: str, row: dict) -> dict:
    msg = client.messages.create(
        model=model, max_tokens=400, temperature=0,
        messages=[{"role": "user", "content": build_prompt(row)}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text")
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError(f"{row['id']}: judge returned no JSON:\n{raw}")
    data = json.loads(match.group(0))
    for c in CHECKS:
        data[c] = int(data[c])
        if data[c] not in (0, 1, 2):
            raise ValueError(f"{row['id']}: {c} out of range")
    return data


def agreement(scores: dict, human_csv: Path) -> str:
    """Exact agreement and mean absolute difference per check, judge vs. human."""
    with human_csv.open() as f:
        human = {r["id"]: r for r in csv.DictReader(f) if all(r.get(c, "").strip() for c in CHECKS)}
    ids = [i for i in human if i in scores]
    if not ids:
        return "No overlapping human scores yet. Fill in human_scores.csv to measure agreement."
    lines = [f"Judge vs. human on {len(ids)} messages:", "",
             "| check | exact agreement | mean abs. diff |", "|---|---|---|"]
    for c in CHECKS:
        diffs = [abs(scores[i][c] - int(human[i][c])) for i in ids]
        exact = sum(d == 0 for d in diffs) / len(diffs)
        lines.append(f"| {c} | {exact:.0%} | {sum(diffs) / len(diffs):.2f} |")
    flips = [i for i in ids if passes(scores[i]) != passes({c: int(human[i][c]) for c in CHECKS})]
    lines += ["", f"Pass/fail disagreements: {', '.join(flips) if flips else 'none'}"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--id", help="Score a single message by id")
    ap.add_argument("--dry-run", action="store_true", help="Print prompts without calling the API")
    ap.add_argument("--human", type=Path, help="CSV of human scores to compare against")
    args = ap.parse_args()

    rows = [r for r in load() if not args.id or r["id"] == args.id]
    if args.dry_run:
        for r in rows:
            print(build_prompt(r), "\n" + "-" * 60)
        return

    try:
        import anthropic
    except ImportError:
        sys.exit("pip install anthropic, then set ANTHROPIC_API_KEY.")
    client = anthropic.Anthropic()

    scores, rationales = {}, {}
    for r in rows:
        data = judge(client, args.model, r)
        scores[r["id"]] = {c: data[c] for c in CHECKS}
        rationales[r["id"]] = data.get("rationale", "")
        print(f"{r['id']:16} {sum(scores[r['id']].values()):>2}/10  {rationales[r['id']]}")

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    slug = args.model.replace("/", "_")
    with (out_dir / f"judge-{slug}.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], **scores[r["id"]], "rationale": rationales[r["id"]]}) + "\n")

    md = [f"# Judge results ({args.model})", "", summary(rows, scores), "", table(rows, scores)]
    if args.human:
        md += ["", "## Agreement with human scores", "", agreement(scores, args.human)]
    (out_dir / f"judge-{slug}.md").write_text("\n".join(md) + "\n")
    print(f"\nWrote {out_dir / f'judge-{slug}.md'}")


if __name__ == "__main__":
    main()
