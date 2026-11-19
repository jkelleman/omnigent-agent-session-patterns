# Rubric: can a person act on this message?

This rubric scores one message, such as an approval prompt, a policy block, a status label, or a resolution label, **as the person sees it on that surface**. A sidebar tooltip isn't expected to carry everything a full approval card does, so each message comes with a `surface` and a `context` that describe what else is visible at the same time. Credit information the person can see without tapping.

Score from the point of view of **the person supervising the agent**. The policy's author is a different reader.

## Five checks

Each check is scored 0, 1, or 2.

| Check | Question | 0 | 1 | 2 |
|---|---|---|---|---|
| **Actor** | Can the reader tell which agent is acting, and on whose behalf? | No agent named, or a generic "the agent" | An agent or harness is named, but its relationship (sub-agent, session) is unclear | The agent is named, plus enough context to tell it apart from the reader's other sessions |
| **Action** | Can the reader tell what the agent did or wants to do, in plain words? | Missing, or only internal terms ("operation", "tool call") | Named, but vague or only in technical form | A specific action in plain words |
| **Cause** | Can the reader tell why this happened, and who owns the rule? | No reason, or "by policy" alone | A reason, but no owner, or an owner the reader can't act on | The reason in plain words, plus who set the rule (you, the agent's author, or your admin) |
| **Consequence** | Can the reader tell what each choice does, including doing nothing? | Unstated | Partly stated (for example, the result of yes, but not of silence) | The result of each answer, or the state of the work after the event |
| **Next move** | Does the reader know what they can do now? | No move, or a move this reader can't take (like editing a config they don't own) | A move is implied but not stated | One clear move this reader can take, or a clear "nothing needed" |

**Total:** out of 10. A message **passes** at 7 or higher with no check scored 0.

## Scoring notes

- **Score missing information.** Length alone doesn't lower a score. A three-word label can score 2 on a check when the surrounding surface supplies the rest.
- **A move the reader can't take scores 0** on Next move, even when it's correct for someone else. An instruction to set a policy parameter scores 0 when the reader isn't the admin.
- **Hedged wording is correct for inferred states.** "May need input" scores normally when the system is inferring.
- **Score the words only.** Give no credit for color or icons, because they're lost in screen readers, notifications, and other harnesses.

## Output format (for the judge)

```json
{"actor": 0, "action": 0, "cause": 0, "consequence": 0, "next_move": 0,
 "rationale": "One or two sentences on the weakest check."}
```
