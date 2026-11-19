# Scoring notes: what the numbers mean and how to raise them

## How a score is calculated

Each message is scored on five checks from the [rubric](rubric.md). Each check gets 0, 1, or 2 points, for a total out of 10.

| Check | Question | 2 points | 0 points |
|---|---|---|---|
| **Actor** | Which agent is acting? | The agent is named, with enough context to tell it apart from other sessions | No agent named, or only "the agent" |
| **Action** | What did it do, or what does it want to do? | A specific action in plain words | Missing, or only internal terms like "operation" |
| **Cause** | Why did it pause, and who owns the rule? | The reason, plus who set the rule | No reason, or "by policy" alone |
| **Consequence** | What does each answer do, including no answer? | The result of every choice, or the state of the work | Unstated |
| **Next move** | What can this reader do now? | One clear action this reader can take | None, or an action the reader can't take |

A message **passes** when it scores 7 or higher with no check at 0. The no-zero rule matters: a message that does four things well and leaves out the actor still fails, because a person supervising several agents can't act without knowing which one is asking.

## Two scorers

| Scorer | How it works | What it's good for |
|---|---|---|
| **Lint baseline** (`lint.py`) | Keyword and pattern rules. No API key needed. | Narrow checks: configuration syntax leaking into a message, a missing rule owner, a missing agent name |
| **LLM judge** (`judge.py`) | A model reads each message with its surface context and scores it against the rubric | Judging whether a person can act on the message, which takes reading in context |

The judge's scores only count once they agree with human scores. Human reviewers are the reference.

## Results from the first lint baseline (v1)

The keyword checker has since been upgraded. [KEYWORD-CHECKER.md](KEYWORD-CHECKER.md) has the v2 results: rewrites now average 8.6, with 10 of 11 passing, and Omnigent's messages average 2.0.

| Set | Mean score | Passing |
|---|---|---|
| Omnigent's current messages | 1.2 / 10 | 0 of 11 |
| Proposed rewrites | 6.6 / 10 | 3 of 11 |

## Why the rewrites scored 6.6 in v1

Most of the lost points are scorer limits. A few are real gaps in the rewrites or the rubric.

| Message | Lint score | Where points were lost | Type |
|---|---|---|---|
| `r-force` | 9, pass | Consequence 1 | Minor real gap: doesn't say what the agent does next |
| `r-risk` | 8 | Next move 0 | Scorer limit: Approve and Deny buttons are on the card |
| `r-push-ask` | 8 | Next move 0 | Scorer limit: buttons are on the card |
| `r-error-badge` | 8, pass | Cause 1, Consequence 1 | Minor real gap: no cause for the error |
| `r-expired` | 8, pass | Actor 1, Cause 1 | Minor real gap: names Polly but not the session |
| `r-gh-deny` | 7 | Consequence 0 | **Real gap:** doesn't say what Codex does after the block |
| `r-blast-deny` | 6 | Next move 0, Actor 1 | Scorer limit on Next move ("run the command yourself" is a move); real gap on Actor: no session named |
| `r-remember` | 6 | Cause 0 | **Rubric gap:** a resolved-approval label has no cause to state |
| `r-blast-ask` | 5 | Consequence 0, Next move 0 | Scorer limits ("if you deny it" states a consequence; buttons are on the card). Real gap: no timeout stated |
| `r-host` | 5 | Action 0 | Scorer limit on "may still be working"; real gap: no last known activity in the tooltip |
| `r-codex-title` | 3 | Action 0, Consequence 0, Next move 0 | **Rubric gap:** a title is scored as if it were the whole card; the question and options appear below it |

## What a good score looks like

- **Each rewrite passes:** 7 or higher with no zeros, scored by human reviewers and by a judge that agrees with them.
- **The judge agrees with human reviewers:** at least 80% exact agreement on each check, and no pass/fail disagreements on a held-out set.
- **The gap from current messages stays large.** It shows the patterns improve real strings.

The lint score is a diagnostic. It doesn't need to reach a particular number, and adding keywords to raise it would make the messages worse.

## How to raise a score

1. **Fix real content gaps.** Add the missing part the rubric asks for: the agent's name and session, what happens next, who owns the rule, or the timeout.
2. **Score each message as a unit with its surface.** A card title, a tooltip, and a full approval card carry different amounts of information. The rubric should credit what's visible on the same surface.
3. **Fit the rubric to the message type.** A resolved-approval label has no cause to state, and a title isn't expected to carry a next move. Mark those checks "not applicable" for that type and score out of the remaining points.
4. **Calibrate the judge before trusting it.** Compare its scores with human scores, find where they disagree, and tighten the rubric wording until they agree.

## Roadmap to a high score

### Now
- [ ] Score all 22 messages in `human_scores.csv` myself, using the rubric.
- [ ] Get a second reviewer to score them independently.
- [ ] Reconcile the two sets and note every disagreement as a possible rubric change.

### Next
- [x] Add applicability by surface (title, tooltip, card, resolved label) to the rubric, `lint.py`, and `judge.py`, scoring out of the applicable points. Done in lint v2.
- [ ] Fix the real gaps: add what Codex does next to `r-gh-deny`, the session name to `r-blast-deny` and `r-expired`, the timeout to `r-blast-ask`, and the last activity to `r-host`.
- [ ] Re-run the lint baseline and record the new scores.

### Then
- [ ] Run the LLM judge with an Anthropic API key, comparing against the human scores (`python evals/judge.py --human evals/human_scores.csv`).
- [ ] Tune the judge prompt or rubric until agreement reaches 80% per check with no pass/fail disagreements.
- [ ] Collect 10 or more messages from the [validation sessions](../docs/validation-plan.md) as a held-out set, and confirm the agreement holds on them.

### Later
- [ ] Publish the judge results and agreement table in `results/`.
- [ ] Add a short write-up to the README: the before and after scores, and what calibration changed in the rubric.
