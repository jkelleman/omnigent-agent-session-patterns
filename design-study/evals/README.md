# Evals: can a person act on this message?

Messages in a meta-harness are templated, generated, and multiplied across a dozen harnesses, so nobody can review them all by hand. This folder turns "is this message clear?" into something a reviewer can score consistently, whether that reviewer is a person or a model.

## What's here

| File | What it is |
|---|---|
| [`rubric.md`](rubric.md) | Five checks (Actor, Action, Cause, Consequence, Next move), each scored 0–2, judged on the surface where the message appears |
| [`messages.jsonl`](messages.jsonl) | 11 real Omnigent strings, each with its source file, paired with 11 rewrites that follow the [pattern spec](../docs/agent-states.md) |
| [`lint.py`](lint.py) | A rule-based baseline. It has no dependencies and needs no API key. |
| [`judge.py`](judge.py) | An LLM judge that scores each message against the rubric in context, and reports agreement with human scores |
| [`human_scores.csv`](human_scores.csv) | A template for human reviewers' scores |
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

The [lint baseline](results/lint-baseline.md) is useful mostly for what it gets wrong:

- **It can't see the surface.** It gives the push approval rewrite a 0 on Next move, even though Approve and Deny buttons are right there.
- **It can't tell who the reader is.** It can't tell whether "Ask your admin" is a real option for this reader or a dead end.
- **It can't read meaning.** It matches words, not consequences.

Rules can flag config syntax leaking into a message, or a missing rule owner. Judging whether a person can act needs a reader, which is why there's a judge.

## A judge is only as good as its agreement with people

The judge's scores mean nothing until they're checked against human scores. Here's the process:

1. Two reviewers score every message in `human_scores.csv`, independently.
2. They reconcile their differences, and where they disagree, the rubric gets sharpened. Most rubric changes come from this step.
3. The judge runs with `--human`. It reports exact agreement and mean difference per check, plus every message where the judge and the humans disagree on pass or fail.
4. The judge prompt or rubric is tuned until agreement holds on new messages, not only on the ones it was tuned against.

This is the same calibration loop I've used for training human reviewers and LLM judges to grade AI output consistently.
