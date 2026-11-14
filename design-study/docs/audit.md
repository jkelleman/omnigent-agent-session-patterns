# Audit: approvals, status, and errors in Omnigent

**Scope:** the moments when a person has to understand, or act on, an agent they aren't watching. That covers approval prompts, session status, policy blocks, timeouts, and errors.

**Method:** Part 1 is a source read of [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) at commit `f1bb65b` (Nov 13, 2026). Part 2 is hands-on use on desktop and phone.

**Note:** Omnigent is alpha, and a lot is already done well. I've called those out too, because good patterns should be kept on purpose, not by accident.

---

## Part 1: What the source shows

### 1. The same event speaks in a different voice for each harness

When an agent stops to ask the person something, the card title depends on which harness is underneath:

| Harness | Title |
|---|---|
| Claude | "Claude has questions" |
| Codex | "Codex needs input" |
| Cursor | "Cursor has questions" |
| Pi, Devin, Antigravity | "… needs your input" |

`web/src/components/blocks/ApprovalCard.tsx`

**Why it matters:** Omnigent's promise is one layer over many harnesses. When the wording changes with the harness, the seams show, and a person scanning five sessions on a phone has to re-read each title to learn it means the same thing.

**Pattern:** one title for one event, whatever the harness: **"[Agent name] needs your answer."** The harness goes in the metadata line, not the headline.

### 2. After you approve, the scope of your answer is hard to read

The resolved approval card can show at least 10 different verdict labels, including:

- "Approved"
- "Approved for this session"
- "Approved · won't ask again"
- "Approved and remembered"
- "Always allowed"
- "Always allow requested"
- "Session allow requested"
- "Approved · auto mode"
- "Approved · auto-accepting edits"
- "Approved · directory access for this session"

`ApprovalCard.tsx`, around lines 789–851

Each label is accurate. Together, they leave the question that matters for trust unanswered: **how far does my yes reach?** For example:

- "Won't ask again" and "Always allowed" read as the same thing, but may differ in scope.
- "Requested" vs. "approved" depends on whether the harness has confirmed yet.

**Pattern:** a three-step scope ladder (**Just this once · This session · Always for this agent**), named the same way on the button before you tap and on the label after. See [agent-states.md › Scope ladder](agent-states.md#scope-ladder).

### 3. Saying nothing is a decision, and the UI doesn't say so

- **The timeout:** the default `ask_timeout` is **86,400 seconds (24 hours)** (`omnigent/spec/types.py`). On timeout, the request resolves as a deny, and any state the policy would have written is dropped: "a denied ASK must leave no trace" (`omnigent/runtime/policies/approval.py`).
- **What the person sees:** the card later reads "Prompt expired."
- **What's missing:** a person who comes back on their phone the next morning learns that the prompt expired, but not:
  - what the agent did instead
  - whether the work is stuck
  - how to pick it back up

**Pattern:**
- While pending, every approval states its deadline and default: "If you don't answer by 9:41 PM tomorrow, this will be denied."
- An expired card states what happened and offers one next step.

### 4. Policy reasons are written for the policy author, not the person approving

Policy reasons become the `message` on the elicitation that reaches the approval surface (`approval.py`: `ElicitationRequest(message=result.reason …)`). Some of the built-in reasons:

- "Elevated session risk."
- "Blocked by the blast-radius policy."
- "GitHub operation blocked by policy."
- "Force push is blocked by policy. Remove the force flag (--force / -f / --force-with-lease / --force-if-includes / +refspec) or set deny_force_push=False."

The last one is the clearest case. It tells the reader to change a setting, but:

- Policies come from three owners: session (the person), agent spec (the agent developer), and server (the admin).
- Spec policies are **immutable** from a session (`designs/CUJ-ANALYSIS.md` §2.D).
- So the person reading the message often *can't* do what it suggests.

**Pattern:** every policy message names:

1. the rule in plain words
2. **who owns it** ("Set by your workspace admin")
3. the move available to *this* reader

The config fix belongs in a "Details for admins" disclosure.

### 5. Status describes the transcript, not the agent

- **The error badge:** its tooltip reads "Latest message is an error" (`SessionStateBadge.tsx`). That's true, but it doesn't say whether the agent has stopped, is retrying, or has already recovered.
- **The "working" state:** the team's own reliability analysis notes that when a runner goes offline, the client can stay **stuck on "working" until timeout** (`CUJ-ANALYSIS.md` §2.A).

A spinner that keeps going when nothing is happening costs more trust than any error message.

**Pattern:**
- Status answers "what is the agent doing, and can it continue?"
- "Working" is only shown with a "last heard" time. Past a threshold, it changes to **Lost contact**.

### Already done well (keep these)

- **Uncertain states are worded as uncertain.** When the runner *infers* that a terminal is waiting for input, the badge says **"May need input"** instead of "Needs response," and a code comment explains why ("The runner infers this reason from the terminal's screen, so stay tentative"). That's exactly the right instinct, and it should be a written principle.
- **"Resolved elsewhere" explains itself.** Its tooltip says the request was answered in the terminal, another tab, or the approve page.
- **Requests from sub-agents are attributed** ("Requested by sub-agent …").
- **Policy composition is principled:** session → spec → admin, the first deny wins, and several ASKs merge into one approval. That gives the UI a solid model to explain.

---

## Part 2: Hands-on

*In progress: I'm running real sessions with Claude Code and Codex on the desktop app and the phone, focused on approvals made from the phone and on reconnecting after a host drops.*
