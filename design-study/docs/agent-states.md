# Agent session states: a pattern spec

This spec defines a shared vocabulary for what a live agent session is doing, what the person can do about it, and what the interface has to say in each case. It is harness-neutral by design: the same state looks and reads the same whether Claude Code, Codex, or a custom YAML agent is underneath.

Each state is mapped to what Omnigent has today (from `SessionStateBadge.tsx`, `ApprovalCard.tsx`, and `docs/POLICIES.md` at commit `ce5f47b`), so the gaps are concrete.

## Principles

1. **Say who is asking, and who made the rule.** Every pause names the agent (and its parent, if it's a sub-agent) and the owner of the policy that caused it: you, the agent's author, or your admin.
2. **Show how far a yes reaches before the tap, not after.** The button and the resulting label use the same scope words.
3. **Not answering is a decision. Say what it does.** Every pending request shows its deadline and what happens at that deadline.
4. **Never show activity you can't verify.** "Working" always has a "last heard" time. Past a threshold, it becomes *Lost contact*.
5. **Every problem names the next move, for this reader.** If the fix belongs to someone else, say who.
6. **Uncertain information is worded as uncertain.** Inferred states use "may" (Omnigent already does this with "May need input").
7. **One event, one voice.** Harness names go in metadata, never in the headline.

## States

| State | What it means | What the person can do | Omnigent today | Gap |
|---|---|---|---|---|
| **Starting** | The session is booting: runner, sandbox, harness | Wait or cancel | `starting` ("Session starting up") | Same spinner as running; no progress or ETA for slow sandbox boots |
| **Working** | The agent is acting, and we heard from it recently | Watch, steer, stop | `running` ("Session running" / "Working in the background") | No "last heard" time; can stay stuck on "working" when the runner is offline |
| **Needs you** | The agent is paused on the person: an approval, a question, a plan review | Answer, or open details | `awaiting` ("Needs response" / "May need input") | Deadline and default aren't shown while the request is pending |
| **Blocked** | A policy denied an action and the agent can't continue that path | Adjust the task, or ask the rule's owner | Surfaces as an agent error in the transcript | Not a distinct state; the reason doesn't name the rule's owner |
| **Lost contact** | No signal from the runner or host past a threshold | Reconnect, move to the cloud, or wait | `disconnected` ("Host disconnected") | Only covers the host; a runner going quiet isn't shown |
| **Failed** | The agent stopped on an error it couldn't recover from | Retry, fork from before the error, or read the log | `error` ("Latest message is an error") | Describes the message, not whether the agent stopped |
| **Recovered** | The agent hit an error and got past it on its own | Nothing required; can review | None | Recovery isn't shown, so the error badge can outlive the problem |
| **Done** | The turn finished | Review the changes, reply | `idle` / `unseen` ("New messages") | — |

### Severity order (for one badge per session)

Needs you › Lost contact › Failed › Blocked › Working › Starting › Recovered › Done

The person's attention is the scarcest resource in a fleet, so a request waiting on the person outranks everything else.

## Anatomy of a "Needs you" request

Every approval, on every surface, carries these seven parts:

| # | Part | Example |
|---|---|---|
| 1 | **Who** | "Codex · sub-agent of *Polly*, on `feature/auth-retry`" |
| 2 | **Wants to** (plain words) | "Push 3 commits to GitHub" |
| 3 | **Exact action** (collapsed on mobile) | `git push origin feature/auth-retry` |
| 4 | **Why it paused** | "Pushes need approval. *Set by your workspace admin.*" |
| 5 | **What changes** | "3 commits become visible on origin. Can be reverted." |
| 6 | **Scope of your answer** | Just this once · This session · Always for this agent |
| 7 | **If you don't answer** | "Denied automatically at 9:41 PM tomorrow. The agent will stop this step." |

On a phone, parts 1, 2, 4, and 7 are always visible, and the rest sit one tap away. Approve and deny stay within thumb reach, and deny is never the visually dominant button.

## Scope ladder

One set of words, used on the buttons before the tap and on the label after:

| Scope | Button | Label after | Maps to Omnigent verdicts |
|---|---|---|---|
| Once | **Approve** | "Approved once" | "Approved" |
| Session | **Approve for this session** | "Approved for this session" | "Approved for this session", "Session allow requested", "Approved · directory access for this session", "Approved · auto mode" |
| Always | **Always allow for this agent** | "Always allowed for *[agent]*" | "Always allowed", "Approved · won't ask again", "Approved and remembered", "Always allow requested" |

- **Pending confirmation:** while a harness hasn't confirmed delivery, add a suffix ("· confirming…") instead of changing the verb.
- **Rules the reader doesn't own:** when a server policy makes a scope unavailable, show the option disabled, with the owner: "Only your admin can change this rule."

## Policy messages: three layers

| Layer | Audience | Example |
|---|---|---|
| **Headline** | The person deciding | "Force pushes aren't allowed in this workspace." |
| **Next move** | That same person | "Ask the agent to push without force, or ask your admin." |
| **Details** (collapsed) | Policy author or admin | "Policy `github_access` · `deny_force_push=True` · server-wide" |

## Session relationships

Omnigent sessions can be watched, co-driven, and forked. Each relationship needs one persistent, glanceable cue:

| Relationship | Cue |
|---|---|
| **Watching** | "View only · *[owner]*'s session". The composer is replaced, not disabled. |
| **Co-driving** | Avatars of everyone who can send input. Each message is attributed. |
| **Forked** | "Forked from *[session]* at *[step]*", with a link back. Approvals from the original don't carry over, and the fork says so. |

## Open questions

These are for the team:

- Should **Recovered** be shown at all on mobile, or only in the session log?
- Who can lift a **Blocked** state for a co-driver: the session owner only, or any participant?
- Is 24 hours the right default deadline for a phone-first approval? Or should the deadline scale with the action's blast radius?
