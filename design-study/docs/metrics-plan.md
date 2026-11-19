# Metrics plan

How to measure whether the proposed patterns work, using events Omnigent already emits. Omnigent has an OpenTelemetry layer built on MLflow Tracing (`omnigent/runtime/telemetry.py`), a proposal to extend tracing across every component (`designs/OBSERVABILITY.md`), and release feature flags (`designs/FEATURE_FLAGS.md`). The plan builds on all three.

## Events

Most of these exist today as server events. The plan adds attributes, so each event can be counted by surface, harness, and policy owner.

| Event | Exists today | Attributes to add |
|---|---|---|
| `response.elicitation_request` (approval or question shown) | Yes | `surface` (desktop, web, phone), `harness`, `policy_owner` (session, spec, server), `ask_timeout` |
| `elicitation_resolved` (answered, expired, or resolved elsewhere) | Yes | `resolution` (accept, decline, timeout, elsewhere), `scope` (once, session, always), `time_to_resolve_ms` |
| Approval detail opened | No | `surface`, `section` (exact action, policy details) |
| Policy DENY shown to the person | Partly (policy-denied indicator) | `policy_owner`, `has_next_move` |
| Session state change | Partly (badge state) | `from_state`, `to_state`, `last_heartbeat_age_ms` |
| Scope reversal (an "always" rule removed within 7 days) | No | `rule`, `age_days` |

## Metrics

Each metric maps to a finding. The targets are hypotheses to test, set before launch.

| Metric | Definition | Finding | Target direction |
|---|---|---|---|
| **Time to resolve** | Median time from `elicitation_request` to `elicitation_resolved`, by surface | Harness voice, timeout | Down, especially on phone |
| **Expiry rate** | Share of approvals resolved by timeout | Timeout | Down |
| **Blocked-work time** | Total time sessions spend waiting on an approval, per active user per day | Timeout | Down |
| **Scope reversal rate** | Share of "always" approvals reversed within 7 days | Approval scope | Down: people grant the scope they meant |
| **Detail-open rate** | Share of approvals where the person opens the exact action before answering | Harness voice, policy messages | Stable or down: the summary is enough more often |
| **Policy block follow-through** | Share of policy DENYs followed by a redirect message within 10 minutes | Policy messages | Up |
| **Policy support load** | Support tickets and issues mentioning a policy block, per 1,000 blocks | Policy messages | Down |
| **False working time** | Time a session shows Working with no heartbeat in the last 60 seconds | Session status | Near zero |
| **Lost-contact recovery** | Share of Lost contact sessions the person resumes, versus abandons | Session status | Up |

### Guardrails

These should not get worse:

- **Decline rate on high-risk actions.** Clearer approvals shouldn't make people approve everything.
- **Time to first approval for new users.** The added deadline and owner lines shouldn't slow first-time comprehension.
- **Approval card height on phone.** The four always-visible parts need to fit above the fold.

## Rollout

1. **Baseline.** Ship the new event attributes alone for two weeks to get baselines for every metric. The [validation sessions](validation-plan.md) give early qualitative baselines in the meantime.
2. **Staged rollout behind a feature flag.** Release each pattern behind its own flag (scope ladder, timeout display, policy owner, status states), so its effect can be measured separately.
3. **Compare.** For each flag, compare flagged and unflagged sessions on its primary metric and the guardrails. Usage across Databricks' own engineering team is likely large enough to show changes in the approval metrics within a few weeks; confirm with a power calculation from the baseline data.
4. **Decide.** Keep, revise, or roll back each pattern based on its primary metric and guardrails.

## Message quality as a leading indicator

The [evals](../evals/) score new approval and policy strings before they ship. Two checks can run in CI:

- The keyword checker flags configuration syntax in a person-facing message and policy messages that name no owner.
- The LLM judge scores new strings against the rubric once it's calibrated against human scores.

Message quality scores are an early signal before release. The production metrics show whether comprehension actually improved.
