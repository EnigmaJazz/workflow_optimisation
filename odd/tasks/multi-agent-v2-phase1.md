# Multi-agent v2 — Phase 1: inert plan-task permissions

Feature: multi-agent v2 plan tools, gating, and the ODD tracker change. Task ID
`multi-agent-v2-phase1`. Class: global tooling change. Route: `workflow-odd-secure` (delegated).
Unit `q90-phase1-plan-u1`: PLANNING COMPLETE; PENDING-COMMIT. Implementation tasks T2 and T3 are
NOT STARTED. Delivery strategy: auto-chain with the resolved topology stacked-to-main
(owner-supplied); each unit gets its own commit; no push or PR. Q56 counted unit 5/10
(brief-authorized 2026-10-23; earlier planning units were not counted). RDD enabled (global);
input boundary `41c293de5365c861242ed78999a3fbc1d565e5fb`.

## Objective

Record an implementable, inert phase 1 for the supplied multi-agent v2 contract: add permission
entries for the future plan tools without implementing them or changing any workflow rule, and
publish the author split, tool contracts and phase boundaries that later units must obey.

## Problem

The current workflow lets the orchestrator delegate tracker creation to a sandbox writer. The
supplied contract replaces that with two broker-validated paths: a PLANNER writes plan prose and
gate verdicts, a PM ticks tasks with evidence, and the orchestrator only reads. Those tools do not
exist yet. Adding their permissions first is inert and safe, but only if the permission posture
and the later author split are recorded now, before any tool or workflow change.

## Phase 1 scope (inert permissions only)

Phase 1 adds the three permission names to `global-config/opencode.json`; it adds no tool
implementation, no tools-map key, no new activation and no reader. A permission for a tool that
does not exist grants nothing and blocks nothing, which is why it can land first.

### Exact future permission insertions (T2 acceptance; NOT implemented by this unit)

| Surface | Entries | Insert after | Insert before |
| --- | --- | --- | --- |
| Global `permission` block `:2444-2548` | `host_plan_write`, `host_gate_verdict`, `host_task_mark` = `"deny"` | `host_plan_append` (`"deny"`, `:2535`) | `host_review_start` (`:2536`) |
| `pm-odd` permission `:2124-2197` | `host_plan_write`, `host_task_mark` = `"ask"` | `host_sandbox_result_install` (`"ask"`, `:2175`) | `host_review_start` (`:2176`) |
| `pm-systematic` permission `:2260-2341` | `host_plan_write`, `host_task_mark` = `"ask"` | `host_sandbox_result_install` (`"ask"`, `:2320`) | `host_review_start` (`:2321`) |

Current-state observations at base `41c293d` (verify again in T2 before editing):

- The three target names are absent from `global-config/opencode.json`. Positive control for the
  search: the literal `host_plan_append` is found at `:2535`.
- The global block has no top-level `"*"` permission key; host-tool entries are explicit denies.
  The `"*": "deny"` entries in the `task` maps are task-dispatch defaults and are separate.
- `host_git_commit` is `"ask"` in `pm-odd` `:2173` and `pm-systematic` `:2318` while global is
  `"deny"` (`:2532`); this is the posture the new per-PM grants follow.
- There is no `host_gate_verdict` grantee and no orchestrator permission grant. There are no
  tools-map keys for any of the three names.

This unit does not edit the config. T2 is the config-only implementation unit and must preserve
the exact ordering above.

## Author split (normative)

| Record | Author and path |
| --- | --- |
| Plan document (objective, approach, reasoning, acceptance criteria) | PLANNER through `host_plan_write`; nobody else writes plan prose. |
| Gate verdicts | PLANNER through `host_gate_verdict`, append-only. |
| Task ticks and evidence | PM through `host_task_mark`. |
| Reading all of it | ORCHESTRATOR, read-only. |

The split protects fidelity and posture: the orchestrator cannot mutate project state and must not
gain a plan-writing tool to route around the worker ban.

## Tool contracts (future; not implemented here)

- **`host_plan_write`** — allowlist roots `odd/tasks/**` and `odd/mini/**` in broker code; reject
  traversal, symlinks and every path outside those roots. Require a revision number, a one-line
  change note and an expected-revision compare-and-swap; refuse a stale writer rather than
  merging. PLANNER may write both roots; PM may write `odd/mini/**` only, and only when the plan
  frontmatter route is a no-Sol route. Refuse every other agent. Agents may not write the
  broker-owned frontmatter keys `route`, `tier` and `gate`.
- **`host_gate_verdict`** — PLANNER only. Append-only `PASS`, `REFINE` or `ESCALATE` against a task
  ID; `REFINE` must carry a refinement plan. Store verdicts where `host_task_mark` can read them
  without trusting the caller. Refuse other roles, invalid verdicts, missing task IDs and a
  `REFINE` without its plan.
- **`host_task_mark`** — PM only. Tick exactly one task ID and never edit task text. Require a
  commit reference or diff digest, plus a test command and result; refuse unless the gate
  requirement is met. Never trust route or risk tier from plan frontmatter: derive the tier with
  `gentle-ai review assess --committed-only` on the evidence commit, raise only and never lower,
  and treat a failed assessment as high. Refuse other roles, malformed or incomplete evidence,
  task-text changes and more than one tick.
- **Apply-time plan-root protection** — add `odd/tasks/**` and `odd/mini/**` to the apply deny list
  in code, but keep it DISABLED behind a config flag until the tools are proven live. Phase 3
  changes the `WORKFLOW.md` tracker rule and enables this protection together, never earlier.

## Context and non-negotiable boundaries

- `docs/contracts/multi-agent-v2-workflow-prompt.md` is committed INPUT, not output. Phase 1 only.
- Phases 2-4 (tool implementation with dormant protection, the workflow/tracker change, and
  verification) belong to agent-sandbox-integration and are explicitly OUT OF SCOPE. They require
  separate authorization; no work-unit allocation for them is created here.
- This phase makes no `WORKFLOW.md`, tracker-rule, plan-root-protection, tool-implementation,
  source, test or prompt change.
- Native 4R review is unchanged. The `ce:review` revision is separate. Magic Context must not
  mirror verdicts or ticks; the record stays file-only, and the PM never reads the mirror.
- Mirror writing and verification are UNIMPLEMENTED until the deterministic host tool lands.

## Stable task IDs

- [x] **T1 — planning.** `q90-phase1-plan-u1`: author this tracker, the Q89 queue entry and the
  router row. Planning artifact complete; commit PENDING-COMMIT. No implementation claimed.
- [ ] **T2 — permission implementation.** Add the three names to the three permission surfaces
  exactly as above; no tools-map key, no orchestrator grant and no `host_gate_verdict` PM grant.
  JSON parse and config diff readback are the required checks; no tool implementation.
- [ ] **T3 — implementation evidence and closure.** Record the T2 commit, actual checks, review
  receipt and native assessment; close only after the committed candidate is assessed. Do not
  claim the tools are live: phase 1 is inert.

## Acceptance criteria and checks

Planning unit (this unit):

- Exactly `odd/tasks/multi-agent-v2-phase1.md`, `docs/TODO.md` and `ROUTER-LOG.md` change.
- The tracker accurately reflects the committed contract and the current config, including
  explicit denies rather than an imagined wildcard.
- Q89 is collision-free, appears once in the queue, and links this tracker; Q56 records 5/10.
- The router row records the actual branch/HEAD and PENDING-COMMIT; no fabricated results.
- `git diff --check` is clean; the reviewability receipt is supplied by the worker.
- Zero advice and zero verifier Tasks: the actual diff is simple docs. No runtime tests are run.

T2 future acceptance (not this unit):

- The three entries exist on exactly the three surfaces, in the stated order and posture.
- `global-config/opencode.json` still parses; no tools-map keys, no orchestrator grant, no
  `host_gate_verdict` grantee and no implementation or activation is present.
- The config diff is limited to the permission additions; a targeted readback confirms the
  explicit denies.

## Progress

- 2026-10-23: T1 planning authored. Worker checked the supplied base: sandbox branch `work` at
  baseline `603b2037d627282c8ef538d0fa7d7d19f773cc4d`, whose parent is the supplied host HEAD
  `41c293de5365c861242ed78999a3fbc1d565e5fb`; no `MERGE_HEAD` or `REBASE_HEAD`; the contract file
  is present at the boundary and was committed by `92a2a38676641473bea2f0bf0c3b868581162e4c`.
  No divergence observed. Host branch `chore/multi-agent-v2-phase1` is dispatch-supplied; the
  worker can observe only its synthetic `work`/`baseline` refs.
- 2026-10-23: T1 planning records the exact future insertions, author split and tool contracts;
  no config, source, test, prompt or workflow edit. Q56 counted unit 5/10 recorded in the queue.
  Advice/verifier: zero, on the simple-docs actual diff. Mirror write/verification UNIMPLEMENTED.
- 2026-10-23: T2/T3 NOT STARTED; no implementation, deployment, live-tool claim or native review.

## Delivery strategy and forecast

**Chosen strategy:** auto-chain with the resolved topology stacked-to-main (owner-supplied); each
unit gets its own commit; no push or PR. **Forecast:** phase 1 is approximately 200-230 authored
changed lines (planning tracker plus TODO/router text, then the small config-only T2 and its
evidence). No deletions are forecast. Each unit stays under the 400-authored-line / 100 KiB
per-commit reviewability cap; actual counts and patch bytes are returned in the worker receipt.
Phases 2-4 are external and are not estimated or allocated in this repository.

## Count

Q56 counted unit **5/10** (2026-10-23), explicitly authorized by the dispatch brief even though
earlier planning units were not counted. This is a planning unit; it does not assert Q58
enforcement, deployment or broker runtime registration.

## Route / trigger evidence

Route: delegated, `workflow-odd-secure`; specialist `odd-apply` (DeepSeek-family cloud sandbox
writer). Triggers: preparation ahead of a writer; a two-or-more non-trivial-file unit; the secure
every-write delegation rule. Actual dispatch: PM-dispatched `odd-apply`; worker session
`ses_e973e8912ffeXn7tgIZQy2wIwm`; actual root `/work`. Worker baseline `work` at `603b203`
(parent `41c293d`); host branch/HEAD `chore/multi-agent-v2-phase1` at `41c293d`
(dispatch-supplied and PM-read; not observable from the worker). RDD enabled (global); boundary
`41c293d`. No branch switch and no commit.

## Log

- 2026-10-23: `q90-phase1-plan-u1` planning prepared by delegated `odd-apply`. Checks: exact
  three-path scope, config/contract readback, Q89 collision check, `git diff --check`; no runtime
  tests, advice dispatch, verifier or native review. Commit PENDING-COMMIT; PM assessment pending.
- 2026-10-23: T2/T3 remain unchecked. Mirror write/verification UNIMPLEMENTED; PM never reads the
  mirror. No implementation or activation is claimed.

## Next step

PM commits the planning result and assesses the committed candidate against boundary `41c293d`.
If the assessment is medium/`under_budget`, retain the boundary and require an explicit owner
closure or native review before the next high-risk commit. The next unit (T2) is a high-risk
config-only change: it owes the consequential two-family pre-advice (one phase), an independent
post-advice check, an independent `gentle-ai-verify`, static diagnostics on the initial candidate,
one correction ceiling, then commit and native assessment/review. The writer choice for that
actual code change must be resolved by the parent before dispatch; this planning unit does not
choose it.
