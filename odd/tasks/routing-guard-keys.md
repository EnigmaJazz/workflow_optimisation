# Routing Guard Keys

## Objective
Make the orchestrator's routing compliance mechanically enforced with session-scoped keys, keyed on the adapter actually loaded, inherited by spawned workers, and suspicious of self-granted authority. Keep the gate warn-only until the log shows no spurious hits.

## Problem
The route gate could be satisfied by any skill load, including a hollow one. A fixed 30-minute lifetime conflated orphaned sessions with long-running work; keys were deleted on every user message, creating a per-turn reset; a valid key did not authorise gated tools on its own; workers could self-mint keys; and registered worker mutation tools were not gated.

## Scope
- `global-config/plugins/systematic-routing-guard.ts`
- `odd/tasks/routing-guard-keys.md`
- Magic Context mirror at `ODD_TASKS key=odd/workflow_optimisation/routing-guard-keys/tasks`

## Constraints
- Keep the routing gate warn-only; do not block tool calls.
- Preserve the kill switch at `~/.config/opencode/routing-guard-off` and `SYSTEMATIC_ROUTING_GUARD_MODE` semantics.
- Keep routing keys outside the project because a plugin may not derive the project path from the server cwd.
- The health plugin's digest pin covers `verify-workflow.sh` only; do not change the health plugin or verifier for this task.
- Do not change `opencode.json` or any ledger.

## Tasks
- **T1 — Warn-only gate** — **done**. Commit `2c0134f`.
- **T2 — Session-scoped key store minted for `workflow-*` skills** — **done**. Commit `3ae9c94`.
- **T3 — Inactivity expiry and removal of per-message deletion** — **done**. Commits `f652ddb` and `1993a8e`.
- **T4 — ISO-timestamped per-occurrence logging** — **done**. Commit `83311d0`.
- **T5 — Parentage, inherited authority and purge of a child's self-minted key** — **done**. Commit `21e59c0`.
- **T6 — Require an adapter key; bare router key is insufficient** — **done**. Commit `d27d2d1`.
- **T7 — Per-route stage table and worker mutation gating on required artifacts** — **in progress**. T7a (the ODD bootstrap write gate) is implemented in this change.
- **T8 — Bug-fix route with its own stages and no ODD tracker** — **planned**.

## Acceptance criteria
- A session with only a `workflow-route` key warns on gated tools.
- A session with an unexpired adapter key does not warn.
- A child's authority follows its parent's adapter-key validity.
- Every gated occurrence is logged with a timestamp.
- Nothing blocks while warn-only is in force.

## Authorized scope
The authorized implementation scope is the routing-guard plugin change and this task tracker. No commits, deployment, verifier/health-plugin edits, configuration edits, or ledger edits are authorized by this task.

## Checks
- Run `bun build global-config/plugins/systematic-routing-guard.ts --target=bun --external @opencode-ai/plugin --outdir /tmp/guard-odd-stage-check` for T7a.
- Confirm `context.directory` is absent from the plugin; verify `ODD_TRACKER_PATTERN` references and warning behavior remain warn-only.
- After each commit, assess RDD with an explicit base ref; assessments to date returned `review_due: false` with reason `under_budget`.
- Review live warning evidence in `~/.local/share/opencode/logs/routing-guard.log`; ROUTER-LOG.md records live log evidence for the initial key-backed gate at row 98.

## Progress
The assessed slice accumulates from boundary `65b1f35`. Completed commit sequence recorded for this task: `2c0134f`, `3ae9c94`, `f652ddb`, `1993a8e`, `83311d0`, `21e59c0`, and `d27d2d1`; T6 is done, T7 is in progress (T7a implemented in this change), and T8 is planned. This change implements the ODD bootstrap write warning: before the session's `odd/tasks/<feature>.md` tracker is observed, valid ODD-key sessions warn on path-known non-tracker file mutations and path-unknown file mutations. No commit has been created. The slice continues to accumulate from `65b1f35`; take native review when assessment returns `review_due` (`slice_budget_reached`), then advance the boundary.

## Route and trigger evidence
Route: delegated. Specialist: `general` sandbox writer. Triggers fired: mapping (4+ files), writer (2+ non-trivial files), preparation, and long-session backstop. The task is a global tooling change. The historical tracker is being created after the first implementation source edit, contrary to protocol; see Debt.

## Delivery strategy
`accumulate`, per the owner's decision. Take native review when the assessment returns `review_due` (`slice_budget_reached`), then advance the boundary. Keep the current assessed slice accumulating from `65b1f35`; retain the per-commit reviewability caps and checks.

## Next step
Continue T7 with the remaining route-stage coverage; T7a is implemented but not yet reviewed or committed.

## Debt
- This tracker was created after the first implementation source edit, contrary to protocol.
- Work-unit commits went to `main` rather than a feature branch.
- No delivery strategy was selected at tracker creation.
- The host commit tool rejects multi-line messages, so the `ROUTED:` trailer has to sit on the subject line rather than in the commit body.
