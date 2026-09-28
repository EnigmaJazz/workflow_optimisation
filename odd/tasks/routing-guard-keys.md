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
- **T6 — Require an adapter key; bare router key is insufficient** — **in progress**.
- **T7 — Per-route stage table and worker mutation gating on required artifacts** — **planned**.
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
- Run `bun build global-config/plugins/systematic-routing-guard.ts --target=bun --external @opencode-ai/plugin --outdir /tmp/guard-adapter-key-check` for each plugin change.
- Confirm `context.directory` is absent from the plugin.
- After each commit, assess RDD with an explicit base ref; assessments to date returned `review_due: false` with reason `under_budget`.
- Review live warning evidence in `~/.local/share/opencode/logs/routing-guard.log`; ROUTER-LOG.md records live log evidence for the initial key-backed gate at row 98.

## Progress
The assessed slice accumulates from boundary `65b1f35`. Completed commit sequence recorded for this task: `2c0134f`, `3ae9c94`, `f652ddb`, `1993a8e`, `83311d0`, and `21e59c0`; T6 is in progress and T7–T8 are planned. The current accumulated slice was 263 authored changed lines at the last assessment, below the 400-line threshold. Post-commit RDD assessments to date were `review_due: false` / `under_budget`.

## Route and trigger evidence
Route: delegated. Specialist: `general` sandbox writer. Triggers fired: mapping (4+ files), writer (2+ non-trivial files), preparation, and long-session backstop. The task is a global tooling change. The historical tracker is being created after the first implementation source edit, contrary to protocol; see Debt.

## Delivery strategy
`ask-on-risk` (default). Running accumulated slice: 263 authored changed lines at the last assessment, below the 400-line threshold. Ask the owner before crossing the threshold.

## Next step
Verify T6, then proceed to T7.

## Debt
- This tracker was created after the first implementation source edit, contrary to protocol.
- Work-unit commits went to `main` rather than a feature branch.
- No delivery strategy was selected at tracker creation.
