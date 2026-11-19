# Audit: approvals, status, and errors in Omnigent

**Scope:** the handoffs where a person has to understand or act on an agent running unattended: approval prompts, session status, policy blocks, timeouts, and errors.

**Method:** Part 1 is a source read of [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) at commit `ce5f47b` (Nov 15, 2026). The screenshots of Omnigent today are its own visual-test reference images and docs images (see [the notice](images/omnigent/NOTICE.md)). Part 2 is hands-on use on desktop and phone.

**Note:** Omnigent is in alpha, and much of it already works well. The audit also lists the patterns worth keeping, so they survive as the product changes.

---

## The surfaces today

<table>
<tr>
<td width="68%"><img src="images/omnigent/desktop.png" alt="Omnigent desktop app: session sidebar grouped by project, with a new-session composer in the center"></td>
<td width="32%"><img src="images/omnigent/mobile-session.png" alt="Omnigent on a phone: one session's chat, with the agent's status shown as 'Tinkering…' and a queued follow-up message"></td>
</tr>
<tr>
<td><b>Desktop.</b> Sessions are listed by project and recency. Each session's state is a small badge at the right edge of the sidebar.</td>
<td><b>Phone.</b> Today the phone shows one session at a time, as a chat. There's no cross-session view of what needs you.</td>
</tr>
</table>

---

## Part 1: What the source shows

### 1. The same event reads differently in each harness

When an agent stops to ask the person something, both the card's header and its wording depend on which harness is underneath:

<table>
<tr>
<td><img src="images/omnigent/approval-codex-command.png" alt="Approval card titled 'Command approval · Codex', reading 'Codex wants to run this command.'"></td>
<td><img src="images/omnigent/approval-policy.png" alt="Approval card titled 'Approval required · approve_shell_commands (tool_call)', reading 'Allow the agent to remove the generated cache directory?'"></td>
<td><img src="images/omnigent/approval-remember-domain.png" alt="Approval card titled 'Approval required · Claude Code', reading 'Claude wants to fetch the Storybook documentation.'"></td>
</tr>
<tr>
<td>Title: "Command approval"<br>Body: "Codex wants to run this command."</td>
<td>Title: "Approval required"<br>Body: "Allow <b>the agent</b> to remove…"</td>
<td>Title: "Approval required"<br>Body: "Claude wants to fetch…"</td>
</tr>
</table>

Question cards vary the same way:

| Harness | Card title |
|---|---|
| Claude | "Claude has questions" |
| Codex | "Codex needs input" |
| Cursor | "Cursor has questions" |
| Pi, Devin, Antigravity | "… needs your input" |

`web/src/components/blocks/ApprovalCard.tsx`

**Why it matters:** Omnigent's value is a single layer over many harnesses, and inconsistent wording exposes the harness underneath. A person scanning five sessions on a phone has to read each card closely to see that they describe the same event. When a card says only "the agent," a person running several agents can't tell which one is asking.

**Pattern:** use one title per event across all harnesses: **"[Agent name] needs your answer."** The harness name moves to the metadata line.

### 2. Approval scope uses different words before and after the tap

Before the tap, the "remember" button changes from card to card:

<table>
<tr>
<td><img src="images/omnigent/approval-codex-command.png" alt="Buttons: Approve, Approve and remember, Reject"></td>
<td><img src="images/omnigent/approval-remember-domain.png" alt="Buttons: Approve, Approve & don't ask again for storybook.js.org, Reject"></td>
</tr>
<tr>
<td>"Approve and remember"</td>
<td>"Approve & don't ask again for storybook.js.org"</td>
</tr>
</table>

After the tap, the resolved card can show at least 10 different labels (`ApprovalCard.tsx`, around lines 793–855):

| Labels that mean "this session" | Labels that mean "from now on" | Others |
|---|---|---|
| "Approved for this session" | "Approved · won't ask again" | "Approved" |
| "Session allow requested" | "Approved and remembered" | "Approved · auto mode" |
| "Approved · directory access for this session" | "Always allowed" | "Approved · auto-accepting edits" |
| | "Always allow requested" | |

Each label is accurate on its own. Together, they leave the person unsure **how far an approval reaches.** "Remember," "don't ask again," and "always allowed" may or may not grant the same scope, and the wording doesn't say.

**Pattern:** a three-step scope ladder (**Just this once**, **This session**, **Always for this agent**), worded the same on the button and on the resolved label.

<table>
<tr><th>Proposed: choose the scope before you tap</th><th>Proposed: the same words afterward</th></tr>
<tr>
<td width="50%"><img src="images/proposed/approve-anatomy.png" alt="Proposed approval screen with the seven parts of the request numbered"></td>
<td width="50%"><img src="images/proposed/approved-session.png" alt="Proposed resolved state reading 'Approved for this session'"></td>
</tr>
</table>

The numbers mark the seven parts of a request. See [agent-states.md › Anatomy](agent-states.md#anatomy-of-a-needs-you-request).

### 3. The approval timeout is hidden until it expires

- **The timeout:** the default `ask_timeout` is **86,400 seconds (24 hours)** (`omnigent/spec/types.py`). On timeout, the request resolves as a deny, and any state the policy would have written is dropped: "a denied ASK must leave no trace" (`omnigent/runtime/policies/approval.py`).
- **While the request is pending,** the card shows Approve and Reject, but no deadline and no default.
- **After the deadline,** the card is clear about the next step:

<img src="images/omnigent/approval-prompt-expired.png" alt="Expired card: 'Prompt expired · Claude Code. Claude wants to run the project tests. Nobody answered before the agent stopped waiting. Send a message to continue.'" width="540">

"Send a message to continue" gives a clear next move. The card leaves out the **outcome**: "the agent stopped waiting" describes the agent's state, and doesn't say that the action was denied or what state the work is in. The person also learns about the deadline only after it passes.

**Pattern:**

- While pending, every approval states its deadline and default.
- An expired card leads with the outcome ("Nobody answered, so the push was denied"), then the state of the work, then one way back.

<table>
<tr><th>Proposed: the deadline while it's pending</th><th>Proposed: the outcome after it passes</th></tr>
<tr>
<td width="50%"><img src="images/proposed/approve.png" alt="Proposed approval with an amber deadline bar: 'If you don't answer by 9:41 PM tomorrow, the push will be denied and Polly will stop this step.'"></td>
<td width="50%"><img src="images/proposed/expired.png" alt="Proposed expired state: 'Nobody answered, so the push was denied', with what happened next and an Ask again button"></td>
</tr>
</table>

### 4. Policy messages are written for policy authors

Omnigent's own docs describe three policy owners:

<img src="images/omnigent/policy-trust-model.png" alt="Omnigent's policy trust model: user policy, developer policy, and IT policy all apply to an agent session" width="640">

The interface doesn't say which owner set a rule. It shows the policy's internal name and enforcement phase:

<table>
<tr>
<td><img src="images/omnigent/approval-policy.png" alt="Approval card header showing the internal policy id 'approve_shell_commands (tool_call)'"></td>
<td><img src="images/omnigent/policy-denied.png" alt="'Blocked by policy · before tool call. Writing outside the selected workspace is not allowed.'"></td>
</tr>
<tr>
<td>Header: <code>approve_shell_commands (tool_call)</code></td>
<td>"Blocked by policy · before tool call." The reason is clear, but the message names no owner and no next move.</td>
</tr>
</table>

The built-in policy reasons follow the same pattern. Each reason becomes the `message` on the elicitation request that reaches the approval surface (`approval.py`: `ElicitationRequest(message=result.reason …)`):

- "Elevated session risk."
- "Blocked by the blast-radius policy."
- "GitHub operation blocked by policy."
- "Force push is blocked by policy. Remove the force flag (--force / -f / --force-with-lease / --force-if-includes / +refspec) or set deny_force_push=False."

The last reason tells the reader to change a setting. Rules set in an agent's spec can't be changed from a session (`designs/CUJ-ANALYSIS.md` §2.D), and server rules belong to the admin, so the person reading the message often has no way to act on it.

**Pattern:** every policy message states the rule in plain words, **who owns it**, and the move available to this reader. Configuration details go in a collapsed "Details for admins" section.

<table>
<tr><th>Proposed: a policy block in three layers</th></tr>
<tr><td width="50%"><img src="images/proposed/blocked.png" alt="Proposed blocked screen: 'Force pushes aren't allowed in this workspace', what you can do, who owns the rule, a message box, and collapsed admin details" width="390"></td></tr>
</table>

### 5. Status labels describe the transcript

<table>
<tr>
<td width="62%"><img src="images/omnigent/turn-error.png" alt="'Claude Code ran into an error during this turn.' with a raw API Error 502 message"></td>
<td width="38%"><img src="images/omnigent/sidebar-badges.png" alt="Omnigent sidebar badges, enlarged: Needs response, Running, Starting, New messages. Running and Starting use the same spinner."></td>
</tr>
<tr>
<td>The card reports a failure and shows the raw API error. It doesn't say whether the agent stopped, will retry, or needs the person.</td>
<td>Running and Starting render the same spinner. The error badge's tooltip reads "Latest message is an error."</td>
</tr>
</table>

The team's own reliability analysis notes that when a runner goes offline, the client can stay **stuck on "working" until timeout** (`CUJ-ANALYSIS.md` §2.A). A spinner that runs while nothing is happening makes every other status label harder to trust.

**Pattern:** status answers two questions: what the agent is doing, and whether it can continue. "Working" always carries a last-heard time and changes to **Lost contact** past a threshold. Each state also has a distinct shape, so color isn't the only signal:

<img src="images/state-icons.svg" alt="Eight session state icons in color and monochrome: Starting, Working, Needs you, Blocked, Lost contact, Failed, Recovered, Done">

<table>
<tr><th>Proposed: triage across sessions</th><th>Proposed: honest about lost contact</th></tr>
<tr>
<td width="50%"><img src="images/proposed/list.png" alt="Proposed session list sorted by what needs you, each with a state icon and, for working sessions, a last-heard time"></td>
<td width="50%"><img src="images/proposed/lost.png" alt="Proposed lost-contact screen: 'Can't reach your laptop', last heard 6 minutes ago, and the last thing seen"></td>
</tr>
</table>

### Already done well (keep these)

<table>
<tr>
<td><img src="images/omnigent/classified-error.png" alt="'Claude Code can't run as root'"></td>
<td><img src="images/omnigent/host-offline.png" alt="'Host is offline — click to reconnect'"></td>
<td><img src="images/omnigent/approval-resolved-elsewhere.png" alt="'Resolved elsewhere · Claude Code'"></td>
</tr>
<tr>
<td>Names the agent and states a known error in plain words.</td>
<td>States the problem and the next move in one line.</td>
<td>Explains why a card closed without the person's input.</td>
</tr>
</table>

- **Inferred states are hedged.** When the runner infers from the terminal screen that it's waiting for input, the badge reads **"May need input."** A code comment explains the choice: "The runner infers this reason from the terminal's screen, so stay tentative." This belongs in the written content guidelines.
- **Requests from sub-agents are attributed** ("Requested by sub-agent …").
- **The expired card gives a next step** ("Send a message to continue").
- **Policy composition is well defined:** session, then spec, then admin; the first DENY wins, and multiple ASK verdicts merge into one approval. The interface can explain this model directly.

---

## Part 2: Hands-on

*In progress: I'm running real sessions with Claude Code and Codex on the desktop app and the phone, focused on approvals made from the phone and on reconnecting after a host drops.*
