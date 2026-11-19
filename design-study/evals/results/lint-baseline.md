# Lint baseline v2

Rule-based scores (A = Actor, Ac = Action, C = Cause, Co = Consequence, N = Next move). Scores are out of 10 over the checks that apply on each surface; n/a marks a check that doesn't apply. See `KEYWORD-CHECKER.md`.

- **omnigent**: mean 2.0/10, 0/11 pass
- **rewrite**: mean 8.6/10, 10/11 pass

| id | variant | text | A | Ac | C | Co | N | score | pass |
|---|---|---|---|---|---|---|---|---|---|
| o-risk | omnigent | Elevated session risk. | 0 | 1 | 0 | 0 | 2 | 3.0 | no |
| r-risk | rewrite | Claude Code has run several risky commands in this session, so the … | 1 | 2 | 2 | 2 | 2 | 9.0 | yes |
| o-blast-ask | omnigent | High-blast-radius command needs approval | 0 | 1 | 0 | 0 | 2 | 3.0 | no |
| r-blast-ask | rewrite | Polly wants to run a command that deletes files outside the project… | 1 | 2 | 2 | 2 | 2 | 9.0 | yes |
| o-blast-deny | omnigent | Blocked by the blast-radius policy. | 0 | 1 | 0 | 0 | 0 | 1.0 | no |
| r-blast-deny | rewrite | Polly can't run `rm -rf ../build` because commands that delete outs… | 1 | 2 | 2 | 1 | 2 | 8.0 | yes |
| o-gh-deny | omnigent | GitHub operation blocked by policy. | 0 | 1 | 0 | 0 | 0 | 1.0 | no |
| r-gh-deny | rewrite | Codex can't open a pull request on acme/payments. This agent can on… | 2 | 2 | 2 | 0 | 2 | 8.0 | no |
| o-push-ask | omnigent | git push is gated; approve to proceed. | 0 | 1 | 0 | 0 | 2 | 3.0 | no |
| r-push-ask | rewrite | Codex, a sub-agent of Polly, wants to push 3 commits to feature/aut… | 2 | 2 | 2 | 2 | 2 | 10.0 | yes |
| o-force | omnigent | Force push is blocked by policy. Remove the force flag (--force / -… | 0 | 2 | 0 | 0 | 0 | 2.0 | no |
| r-force | rewrite | Force pushes aren't allowed in this workspace, so Claude Code's pus… | 2 | 2 | 2 | 1 | 2 | 9.0 | yes |
| o-error-badge | omnigent | Latest message is an error | 1 | 0 | n/a | 0 | 0 | 1.2 | no |
| r-error-badge | rewrite | Stopped: Codex hit an error it couldn't recover from. Open the sess… | 1 | 2 | n/a | 1 | 2 | 7.5 | yes |
| o-host | omnigent | Host disconnected | 1 | 0 | n/a | 0 | 0 | 1.2 | no |
| r-host | rewrite | Lost contact with your laptop 6 minutes ago. Claude Code may still … | 1 | 2 | n/a | 1 | 2 | 7.5 | yes |
| o-expired | omnigent | Prompt expired | 0 | 1 | n/a | 0 | 0 | 1.2 | no |
| r-expired | rewrite | Denied automatically: nobody answered within 24 hours. Polly stoppe… | 1 | 2 | n/a | 2 | 2 | 8.8 | yes |
| o-remember | omnigent | Approved · won't ask again | 0 | 2 | n/a | 0 | 0 | 2.5 | no |
| r-remember | rewrite | Always allowed for Codex in this workspace. Change this in Session … | 1 | 2 | n/a | 1 | 2 | 7.5 | yes |
| o-codex-title | omnigent | Codex needs input | 1 | 0 | n/a | n/a | n/a | 2.5 | no |
| r-codex-title | rewrite | Codex needs your answer to continue auth-retry | 2 | 2 | n/a | n/a | n/a | 10.0 | yes |
