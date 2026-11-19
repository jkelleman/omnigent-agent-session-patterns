# Evals: can a person act on this message?

Agent messages in a meta-harness are templated, generated, and repeated across many harnesses, so manual review doesn't scale. These evals make message quality measurable: a rubric that a human reviewer or an LLM judge can score consistently, and a harness that runs it.

## Files

| File | Contents |
|---|---|
| [`rubric.md`](rubric.md) | Five checks (Actor, Action, Cause, Consequence, Next move), each scored 0–2 in the context of the surface where the message appears |
| [`messages.jsonl`](messages.jsonl) | 11 real Omnigent strings with their source files, paired with 11 rewrites that follow the [pattern spec](../docs/agent-states.md) |
| [`lint.py`](lint.py) | A rule-based baseline (v2) with no dependencies and no API key |
| [`judge.py`](judge.py) | An LLM judge that scores each message against the rubric and reports agreement with human scores |
| [`human_scores.csv`](human_scores.csv) | A template for human reviewers |
| [`KEYWORD-CHECKER.md`](KEYWORD-CHECKER.md) | Gaps found in the keyword checker, the fixes in v2, before-and-after results, and the scoring workflow diagram |
| [`SCORING.md`](SCORING.md) | How scores are calculated, what the current results mean, and the roadmap to higher scores |
| [`results/`](results/) | Output from each run |

## Run it

```bash
cd design-study
python evals/lint.py --out evals/results/lint-baseline.md

pip install anthropic
export ANTHROPIC_API_KEY=...
python evals/judge.py --human evals/human_scores.csv
```

## Why there are two scorers

The [lint baseline](results/lint-baseline.md) shows the limits of string rules:

- **It has no surface context.** It scores the push approval rewrite 0 on Next move, though the Approve and Deny buttons sit right below the message.
- **It doesn't model the reader.** It can't tell whether "ask your admin" is an option this reader has.
- **It matches keywords.** It can't judge whether a message states a consequence.

Rules work for narrow checks, such as configuration syntax leaking into a message or a missing rule owner. Judging whether a person can act on a message needs a model that reads it in context, so the harness includes an LLM judge.

## Calibrating the judge

Judge scores are only meaningful once they agree with human scores. The calibration loop:

1. Two reviewers score every message in `human_scores.csv` independently.
2. They reconcile disagreements and tighten the rubric wherever they disagreed. Most rubric changes come from this step.
3. The judge runs with `--human` and reports exact agreement and mean absolute difference per check, plus every message where the judge and the reviewers disagree on pass or fail.
4. The judge prompt or rubric is tuned until agreement holds on a held-out set of messages.

I've run this loop before, training both human reviewers and LLM judges to grade AI output consistently.
