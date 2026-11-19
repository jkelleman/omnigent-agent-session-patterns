# Agent session patterns: a design study

**Interaction and content patterns for supervising coding agents asynchronously.**

An independent design study of [Omnigent](https://github.com/omnigent-ai/omnigent), the open-source meta-harness from Databricks. Databricks has not reviewed or endorsed it.

> **Summary:** Five findings in how Omnigent handles human-in-the-loop approvals, policy blocks, and session status. Approval scope goes from 10+ labels to 3. None of the 58 readable built-in policy messages name the rule's owner, and the proposed three-layer pattern adds one to every message. Rewritten messages score 8.6 out of 10 against Omnigent's 2.0 on a keyword baseline I built; human and LLM-judge scoring are next. Live [mobile](https://jkelleman.github.io/omnigent-agent-session-patterns/design-study/prototype/) and [desktop](https://jkelleman.github.io/omnigent-agent-session-patterns/design-study/prototype/desktop.html) prototypes.

**Contribution to Omnigent:** [pull request #14464](https://github.com/omnigent-ai/omnigent/pull/14464) makes question card titles consistent across harnesses, from [issue #14463](https://github.com/omnigent-ai/omnigent/issues/14463).

<table>
<tr><th>Omnigent today</th><th>Proposed</th></tr>
<tr>
<td width="55%" valign="top"><img src="docs/images/omnigent/approval-policy.png" alt="Omnigent's approval card today: header shows the internal policy id and phase, the message refers to 'the agent', and there's no deadline"><br><br>The header shows the policy's internal ID and enforcement phase. The message refers to "the agent," and the default 24-hour timeout isn't shown.</td>
<td width="45%"><img src="docs/images/proposed/approve.png" alt="Proposed phone approval: names the agent and its parent, shows the deadline and default, and says who owns the rule"></td>
</tr>
</table>

## Why this matters

A person running several coding agents spends most of their attention on the handoffs: approvals, blocks, errors, and lost connections. Each one is a message they have to understand quickly, often on a phone. When a message is unclear, an agent sits blocked, a sandbox sits idle, or a person approves more than they meant to.

## Findings

The [audit](docs/audit.md) reads Omnigent's source (commit `c3b5dee`, Nov 18, 2026) and its own visual-test screenshots, which are reused under Omnigent's Apache 2.0 license ([notice](docs/images/omnigent/NOTICE.md)).

| Area | Finding | Fix | Implementation | Why it matters |
|---|---|---|---|---|
| **Harness voice** | Question cards use 3 different title wordings across 6 harnesses; some approval cards say only "the agent" | One title per event: "[Agent] needs your answer" | One shared string set in `ApprovalCard.tsx`; always pass the agent and parent name | Inconsistent copy exposes the harness and slows triage |
| **Approval scope** | 10+ verdict labels; "remember" and "always" don't map to a clear scope | [Scope ladder](docs/agent-states.md#scope-ladder): once, this session, always for this agent | Collapse verdicts into 3 scope values; disable scopes the reader doesn't own | People need to know how far a yes reaches before they give it |
| **Approval timeout** | Unanswered approvals become a deny after 24 hours by default (policies can override it); the pending card doesn't say so | Show the deadline and default on every pending request; expired cards lead with the outcome | Read the effective `ask_timeout` when the request is created and render it | Async approvals often sit unanswered for hours, so the default outcome has to be visible up front |
| **Policy messages** | 0 of 58 built-in reasons name the rule's owner; 8 give no specific cause; 4 show configuration syntax | [Three layers](docs/agent-states.md#policy-messages-in-three-layers): plain headline, next move, admin details | Add a person-facing summary and an owner level to each reason, separate from the agent-facing text | The reader can only act if they know who set the rule |
| **Session status** | Labels describe the transcript; Running and Starting use the same spinner; Omnigent's own reliability notes say "working" can outlast an offline runner | [Eight session states](docs/agent-states.md#states) with distinct icons and a last-heard time | Derive state from runner heartbeats; one badge per session by severity | When the spinner keeps running on a dead session, people stop trusting the status labels |

The audit also lists patterns worth keeping, such as hedging inferred states ("May need input").

## Impact

### Measured in the audit

| Measure | Today | Proposed target |
|---|---|---|
| Approval scope labels | 10+ verdict labels, 2+ button wordings | 3 scope values, worded the same before and after |
| Title wordings for question cards | 3 across 6 harnesses | 1 |
| Approval cards that show the timeout | None | All |
| Built-in policy reasons that name the rule's owner | 0 of 58 | All, through the owner field |
| Built-in policy reasons with a next move | 14 of 58 (24%) | All |
| Message quality, keyword baseline | 2.0 / 10, 0 of 11 pass | 8.6 / 10, 10 of 11 pass |

The policy counts come from a [reproducible script](evals/policy_audit.py) over `omnigent/policies/builtins/`. The message scores come from a rule-based checker I built and tuned on these same messages, so treat them as a baseline. Human scores and a calibrated LLM judge are next ([status](evals/README.md#status)). The targets in the right-hand column are design goals, to be confirmed with the [metrics plan](docs/metrics-plan.md).

### Value to Databricks

- **Engineering throughput.** Databricks says it adopted coding agents across its 5,000+ person engineering team ([Databricks blog](https://www.databricks.com/blog/introducing-omnigent-meta-harness-combine-control-and-share-your-agents)). Every unanswered or misread approval is blocked work, and in cloud sandboxes, idle compute.
- **Governance that admins can use.** Policies are a core Omnigent feature, and the managed version runs on the governed Databricks platform ([Data + AI Summit session](https://www.databricks.com/dataaisummit/session/secure-portable-collaborative-multi-harness-agent-teams-omnigent)). When a block names its owner and a next move, it reaches the right person, which should mean fewer support requests and workarounds. The metrics plan tracks this.
- **The neutral-layer strategy.** Omnigent's README lists 16 harnesses plus custom agents. Consistent session language keeps the experience the same whichever harness a team picks.
- **Phone-first supervision.** Databricks describes rejoining a running session from another device, including a phone ([Data + AI Summit session](https://www.databricks.com/dataaisummit/session/secure-portable-collaborative-multi-harness-agent-teams-omnigent)). These patterns put what's needed to decide on the first screen.

### How to measure it in production

The [metrics plan](docs/metrics-plan.md) adds attributes to events Omnigent already emits and rolls out each pattern behind its own feature flag. Primary metrics: time to resolve an approval, expiry rate, blocked-work time, scope reversal rate, policy block follow-through, and false working time.

## Prototypes

| Mobile | Desktop |
|---|---|
| [<img src="docs/images/proposed/list.png" alt="Mobile session list sorted by what needs you" width="260">](https://jkelleman.github.io/omnigent-agent-session-patterns/design-study/prototype/) | [<img src="docs/images/proposed/desktop-approve.png" alt="Desktop orchestration view with a severity-sorted session list and an inline approval card">](https://jkelleman.github.io/omnigent-agent-session-patterns/design-study/prototype/desktop.html) |
| Cross-session triage, approvals, policy blocks, lost contact, and expired requests | Dense orchestration, including watch, co-drive, and fork |

Both prototypes use Omnigent's light-theme tokens and component conventions from its source: the color palette, status colors, type scale, 8px radii, and the Approve and Reject button pattern. The state icons are new.

## Contents

| | |
|---|---|
| **[Audit](docs/audit.md)** | Five findings with screenshots, source references, and today-versus-proposed comparisons |
| **[Pattern spec](docs/agent-states.md)** | Session states, icons, state diagram, approval anatomy, scope ladder, policy message layers, session relationships |
| **[Metrics plan](docs/metrics-plan.md)** | Events, metrics, guardrails, and a feature-flagged rollout |
| **[Validation plan](docs/validation-plan.md)** | Six hands-on scenarios that test each finding and produce a held-out eval set |
| **[Evals](evals/)** | Rubric, 22 messages with baseline scores, keyword checker, LLM judge, scoring page, and policy-reason audit |

## How this was made

I set the scope, chose the five areas to audit, wrote the findings and patterns, designed the screens, and defined the rubric and its calibration process. I used Claude Code as a build partner: it read the Omnigent source to locate the components and strings I was looking for, extracted the policy reasons, and implemented the prototypes, scripts, and diagrams under my direction. The commit history shows the work step by step.

---

*Jen Kelleman, content and product designer for AI agents. [jkelleman.com](https://jkelleman.com)*
