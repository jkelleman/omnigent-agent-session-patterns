# Agent session patterns: a design study

**Interaction and content patterns for supervising coding agents asynchronously.**

This is an independent design study of [Omnigent](https://github.com/omnigent-ai/omnigent), the open-source meta-harness from Databricks. Databricks has not reviewed or endorsed it.

A person running several coding agents spends most of their attention on the handoffs: human-in-the-loop approvals, policy blocks, errors, and lost connections. Each handoff is a message the person has to understand quickly, often on a phone. This study covers how Omnigent handles those messages today, and proposes a harness-neutral interaction model and message architecture for them.

<table>
<tr><th>Omnigent today</th><th>Proposed</th></tr>
<tr>
<td width="55%" valign="top"><img src="docs/images/omnigent/approval-policy.png" alt="Omnigent's approval card today: header shows the internal policy id and phase, the message refers to 'the agent', and there's no deadline"><br><br>The header shows the policy's internal ID and enforcement phase. The message refers to "the agent," and the timeout isn't shown.</td>
<td width="45%"><img src="docs/images/proposed/approve.png" alt="Proposed phone approval: names the agent and its parent, shows the deadline and default, and says who owns the rule"></td>
</tr>
</table>

## Contents

| | |
|---|---|
| **[Audit](docs/audit.md)** | Approvals, session status, policy blocks, and errors in Omnigent today. Five findings, each with screenshots, source references, and a proposed fix, plus the patterns worth keeping. |
| **[Pattern spec](docs/agent-states.md)** | <ul><li>Eight harness-neutral session states, with icons and a state diagram</li><li>A seven-part anatomy for approval requests</li><li>A scope ladder for approvals</li><li>A three-layer structure for policy messages</li></ul> |
| **[Prototype](prototype/)** | A mobile prototype for cross-session triage, approving a sub-agent's `git push`, a policy block, lost contact, and an expired request. [View it live](https://jkelleman.github.io/omnigent-agent-session-patterns/design-study/prototype/). |
| **[Evals](evals/)** | A rubric and an LLM-as-judge harness that score agent messages on whether a person can act on them. It covers 11 real Omnigent strings and 11 rewrites, with a rule-based baseline. |

## Principles

1. **Name the actor and the rule owner.** Every pause says which agent is asking and who set the policy: the user, the agent's author, or the workspace admin.
2. **Show the scope of an approval before the tap.** One scope ladder (once, this session, always for this agent) on every surface, worded the same before and after.
3. **State the timeout and its default.** An unanswered approval resolves as a deny after 24 hours, so every pending request shows that deadline.
4. **Only report activity the system can confirm.** "Working" carries a last-heard time and changes to *Lost contact* past a threshold.
5. **Keep the voice consistent across harnesses.** The same event uses the same words whether Claude Code, Codex, or Cursor is underneath.

## Why evals

Agent interface copy is templated, generated, and repeated across many harnesses, so manual review doesn't scale. The [rubric](evals/rubric.md) breaks "can a person act on this message?" into five checks that a human reviewer or an LLM judge can score consistently:

- **Actor:** which agent is acting
- **Action:** what it did or wants to do
- **Cause:** why it paused, and who owns the rule
- **Consequence:** what each answer does, including no answer
- **Next move:** what this reader can do now

## How this was made

I built this with coding agents. Claude Code handled the source reading, scaffolding, and prototype build under my direction, and the commit history shows the work.

---

*Jen Kelleman, content and product designer for AI agents. [jkelleman.com](https://jkelleman.com)*
