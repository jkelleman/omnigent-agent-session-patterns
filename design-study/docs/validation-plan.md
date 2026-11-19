# Validation plan: hands-on sessions

The audit's findings come from Omnigent's source code and its visual-test screenshots. This plan checks them against real use, on desktop and phone, and produces the held-out messages for the [evals](../evals/).

## Questions

1. Do the five findings show up in real sessions, and how often?
2. Which handoffs cost the most time or attention when supervising from a phone?
3. Are there handoff messages the source read missed: runtime strings, harness-native prompts, or errors from the runner?

## Setup

| Item | Choice |
|---|---|
| Omnigent | Latest release, desktop app and web UI, phone browser for mobile |
| Harnesses | Claude Code and Codex (the two with the fullest approval support) |
| Policies | `ask_on_os_tools` at session level, `github_policy` with branch limits in the agent spec, and a server-wide `cost_budget` with a warning threshold, so a block from each of the three policy owners can occur |
| Tasks | Three small real tasks in a sample repo: a refactor with tests, a push to a restricted branch, and a long test run |

## Scenarios

Each scenario targets a finding. Record a screenshot of every handoff message, the time to understand it, and what was done next.

| # | Scenario | Finding it tests |
|---|---|---|
| 1 | Run the same refactor in Claude Code and Codex at once. Compare every approval and question card. | Harness voice |
| 2 | Approve a shell command with each scope option, then check whether the agent asks again in this session and the next. | Approval scope |
| 3 | Start a task, trigger an approval, and leave it unanswered past a short `ask_timeout`. Return on the phone. | Approval timeout |
| 4 | Trigger one block from each owner: session, agent spec, and server. For each, note whether the message says who to ask. | Policy messages |
| 5 | Close the laptop lid mid-run, then check the session from the phone at 1, 5, and 15 minutes. | Session status |
| 6 | Share a session, co-drive it from a second account, and fork it. Note how each relationship is shown. | Session relationships |

## What to capture

- Every handoff string as shown, with the surface (card, toast, badge, tooltip, transcript)
- Time from opening a message to choosing an action, using a stopwatch per message
- Any wrong action or wrong assumption, and what in the message caused it
- Harness, surface, and device for each capture

## Outputs

1. **Audit addendum:** confirmed findings with counts, plus new findings with screenshots.
2. **Held-out eval set:** 10 or more handoff messages from these sessions, added to `evals/messages.jsonl` with `"variant": "omnigent"`. These were not used to build the keyword checker or tune the judge, so they give a fair test of both.
3. **Baseline numbers** for the [metrics plan](metrics-plan.md): time to understand a message and the share of messages acted on correctly the first time.
