# Multi-agent v2 — Phase 1: inert plan-task permissions

Feature: multi-agent v2 plan tools, gating, and the ODD tracker change. Task ID
`multi-agent-v2-phase1`. Class: global tooling change. Route: `workflow-odd-secure` (delegated).
Unit `q90-phase1-plan-u1`: PLANNING COMMITTED as `28d4a4368e0e3925069208ce7775b73c84c4922a`.
The planning medium slice was closed by an explicit OWNER decision (2026-10-23) that advanced the
reviewed boundary from `41c293de5365c861242ed78999a3fbc1d565e5fb` to
`b154ef3a33ce692bba5218c0547def92755dc371`; this is owner closure, NOT native review or approval.
Phase 1 source (T2) is implemented and committed as
`473c9cd85db1c70122ed5ea007241fce10be9f59` (inert permissions only; tools are NOT live). T3
records the source checks, receipt and assessment. This separate metadata unit's own commit and
post-metadata assessment remain PM-owned and are NOT claimed here.
Delivery strategy: auto-chain with the resolved topology stacked-to-main
(owner-supplied); each unit gets its own commit; no push or PR. Q56 counted unit 5/10
(brief-authorized 2026-10-23; earlier planning units were not counted; no increment for this source
or metadata unit). RDD enabled (global); the source unit's input boundary was
`b154ef3a33ce692bba5218c0547def92755dc371`; the reviewed boundary remains `b154ef3` after the
source medium assessment (not advanced to `473c9cd`).

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

### T2 insertion contract (pre-edit baseline positions; implemented)

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

The T1 planning unit did not edit the config. T2 was the config-only implementation unit and
preserved the exact ordering above.

## Author split (normative for the future supplied contract)

| Record | Author and path |
| --- | --- |
| Plan document (objective, approach, reasoning, acceptance criteria) | PLANNER through `host_plan_write`; nobody else writes plan prose. |
| Gate verdicts | PLANNER through `host_gate_verdict`, append-only. |
| Task ticks and evidence | PM through `host_task_mark`. |
| Reading all of it | ORCHESTRATOR, read-only. |

This table records the FUTURE supplied contract; it does not replace today's rule. Until the plan
tools land and phase 3 changes the tracker rule, the current workflow still delegates tracker
creation to a sandbox writer. The split protects fidelity and posture: the orchestrator cannot
mutate project state and must not gain a plan-writing tool to route around the worker ban.

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
- This planning unit makes no `WORKFLOW.md`, tracker-rule, plan-root-protection,
  tool-implementation, source, test or prompt change. (T2, the phase-1 config unit, later edits
  only the three permission surfaces in `global-config/opencode.json`.)
- Native 4R review is unchanged. The `ce:review` revision is separate. Magic Context must not
  mirror verdicts or ticks; the record stays file-only, and the PM never reads the mirror.
- Mirror writing and verification are UNIMPLEMENTED until the deterministic host tool lands.

## Stable task IDs

- [x] **T1 — planning.** `q90-phase1-plan-u1`: author this tracker, the Q89 queue entry and the
  router row. Planning artifact committed as `28d4a4368e0e3925069208ce7775b73c84c4922a` and
  assessed medium/`under_budget` against `41c293d`. Planning source complete; no implementation
  claimed.
- [x] **T2 — permission implementation.** Implemented and source-committed as `473c9cd`: exactly
  the three names on the three permission surfaces in the stated order and posture; no tools-map
  key, no orchestrator grant, no `host_gate_verdict` PM grant and no tool implementation. Actual
  diff is 7 additions / 0 removals in `global-config/opencode.json`; config blob
  `854e5c4adf495f10251e093bbe597a7cf642e2e8`. JSON parse and targeted line readback executed.
- [x] **T3 — implementation evidence and closure.** T2 commit, actual checks, reviewability
  receipt and native assessment are recorded below. Source is complete; the tools are NOT live
  (phase 1 is inert), and this unit is not DONE until the PM's metadata commit and assessment land.

## Acceptance criteria and checks

Planning unit (T1, historical):

- Exactly `odd/tasks/multi-agent-v2-phase1.md`, `docs/TODO.md` and `ROUTER-LOG.md` change.
- The tracker accurately reflects the committed contract and the current config, including
  explicit denies rather than an imagined wildcard.
- Q89 is collision-free, appears once in the queue, and links this tracker; Q56 records 5/10.
- The router row records the actual branch/commit and committed assessment; no fabricated results.
- `git diff --check` is clean; the reviewability receipt is supplied by the worker.
- Zero advice and zero verifier Tasks: the actual diff is simple docs. No runtime tests are run.

T2 acceptance (implemented; retained as the criterion):

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
- Metadata closure (2026-10-23): delegated to `odd-apply` session
  `ses_e9727236dffeHvVgHnHvAlrar0` (DeepSeek-family cloud sandbox), actual root `/work`, branch
  `work`; base `28d4a43` and parent `41c293d`. No branch switch and no commit from this worker.
- 2026-10-23: T1 planning records the exact future insertions, author split and tool contracts;
  no config, source, test, prompt or workflow edit. Q56 counted unit 5/10 recorded in the queue.
  Advice/verifier: zero, on the simple-docs actual diff. Mirror write/verification UNIMPLEMENTED.
- 2026-10-23: T2/T3 NOT STARTED; no implementation, deployment, live-tool claim or native review.
- 2026-10-23: PM installed the planning result and created commit
  `28d4a4368e0e3925069208ce7775b73c84c4922a` on `chore/multi-agent-v2-phase1`: exactly the
  three authorized paths, +212/-0, 21736-byte authored patch, no generated or binary paths. Base
  `41c293de5365c861242ed78999a3fbc1d565e5fb`; the commit's parent is the base and the committed
  input prompt blob (`555128eea526e4d54a609eaf47097732690390e2`) is unchanged. No divergence or
  hygiene issue observed; the only untracked item is the sandbox session bundle.
- 2026-10-23: PM structural readback: tracker 185 lines, the Q89 entry intact with Q56 5/10, and
  the router row present. Initial static inspection was PARTIAL: no Markdown LSP producer exists
  for the three paths, so no syntax-clean claim is made. `git diff --check` on the committed
  planning candidate is clean. No runtime tests run.
- 2026-10-23: PM committed assessment (`host_review_assess`, base
  `41c293de5365c861242ed78999a3fbc1d565e5fb`, committed-only): schema
  `gentle-ai.review-assessment/v1`, risk `medium`, reason `executable_change` on
  `odd/tasks/multi-agent-v2-phase1.md`, 3 paths / 212 changed lines, candidate
  `base-diff`/consumed=false, `review_due=false` (`under_budget`), status 0. The reviewed
  boundary remains `41c293d`, not advanced; this is not approval or native review.
- 2026-10-23: This metadata unit replaces the precommit placeholders with the committed SHA and
  assessment, marks T1 committed, and leaves T2/T3 not started. Independent orchestrator
  readback is still pending; the medium slice needs an explicit owner closure or native review
  before the next high-risk implementation (T2). Post-metadata assessment is PM-owned closure,
  with its durable evidence in the PM return envelope; this unit's own commit SHA is
  intentionally not claimed here.
- 2026-10-23: Owner decision closed the planning medium slice: the reviewed boundary advanced from
  `41c293de5365c861242ed78999a3fbc1d565e5fb` to `b154ef3a33ce692bba5218c0547def92755dc371`
  before the source commit. This is explicit OWNER closure, not native review, acknowledgement or
  approval.
- 2026-10-23: T2 source implemented by delegated cloud writer `odd-apply` session
  `ses_e97161e9bffejKEybYwkA7eTDv` (`opencode-go/deepseek-v4.1-flash@worker`; model self-reported,
  the writer did not capture its root). Frozen result `293ac0a115daf4f660212f682b147a7a39f986db`;
  host source commit `473c9cd85db1c70122ed5ea007241fce10be9f59` on branch
  `chore/multi-agent-v2-phase1`, parent `b154ef3a33ce692bba5218c0547def92755dc371`. Actual
  receipt: 7 authored changed lines, 1171 authored patch bytes, generated/binary `[]`. PM broker
  read the exact 7 additions only; positional readback `2176-2177`, `2323-2324`, `2540-2542`.
  correction_rounds_used: 0; no source change after the initial edit.
- 2026-10-23: Pre-code advice ran as one independent frozen wave before implementation.
  `advisor-security-pre` (`ses_e971b9420ffen8ZDFcKAdcp79L`, `openai/gpt-6.1-sol`): no blockers;
  recommended a duplicate-safe exact delta and in-memory controls; incorporated.
  `advisor-integration-pre` (`ses_e971b9443ffedeeCzM3YTF7ash`, `opencode-go/kimi-k2.7-code`): no
  blockers; correctly noted the named tests do not cover the new entries, but its proposed global
  anchor was WRONG (`581` is `orchestrator.permission`); PM read the true global block at
  `2535-2536` and rejected that recommendation. Independent preparation explorer
  `ses_e971b9439ffeYgjZNmnvVVvdn2` corroborated the anchors and permissions; it is not an advisor.
  PM-supplied project `.atl` fallback log `4154-4168` records the integration same-model Kimi replay
  completing; independence is preserved (OpenAI security vs Kimi integration). This is not full
  consensus approval.
- 2026-10-23: Post-code advice ran on the SAME INITIAL candidate. `advisor-security-post`
  (`ses_e9709c92affeeCr6OWGjHy6x2X`, `opencode-go/qwen3.7-plus`): no blockers. The same Task's
  clarification corrected its erroneous DeepSeek-family label and a SHA typo and exposed the
  runtime Qwen route. Its literal tools-map grep was vacuous and is NOT cited as evidence; the
  broker exact patch plus the verifier's recursive key/byte checks are used instead. No second
  review or advice cycle ran.
- 2026-10-23: Independent verifier `gentle-ai-verify` (`ses_e9709c923ffeu6JhdfDuLb41Wh`,
  `openai/gpt-6.1-sol`), actual root `/work`, candidate blob
  `854e5c4adf495f10251e093bbe597a7cf642e2e8`, SHA-256
  `4e7d356fc3a81698b4382a1e3b0358fa49951c09d98db0f8e6e0fd0b925f996d`. Observed:
  `python3 -m json.tool global-config/opencode.json` exit 0 with empty stderr;
  `python3 -m unittest tests.test_pm_task_allowlists tests.test_pm_handoff_spec -v` exit 0 with
  34 tests OK; `git diff --check` and the base diff whitespace check exit 0. It also executed an
  independent duplicate-reject parse, exact baseline+7 bytes including the newline, values/
  adjacency/recursive target locations (no tools map, no orchestrator grant, no agent verdict), and
  six in-memory negative controls that rejected three global deny->allow flips, each PM verdict
  grant and a duplicate key.
- 2026-10-23: Initial static diagnostics were PARTIAL: `aft_inspect` on
  `global-config/opencode.json` reported diagnostics unknown because Biome has no workspace root
  marker (`biome.json`/`biome.jsonc`); complexity incomplete and Python dead-code unsupported and
  unrelated. No syntax-clean, consumer or live-enforcement claim is made; the JSON source syntax
  was independently parsed, while consumer loading remains UNVERIFIED and out of scope.
- 2026-10-23: PM `host_review_mode_status` observed `on` (decided `global`), no toggles. PM
  post-source `host_review_assess` (baseRef `b154ef3a33ce692bba5218c0547def92755dc371`,
  committedOnly true) returned status 0 with empty stderr: schema
  `gentle-ai.review-assessment/v1`, risk `medium`,
  reasons `[{code: configuration_change, path: global-config/opencode.json}]`, changed_paths 1,
  changed_lines 7, candidate `{kind: base-diff, base_ref: b154ef3..., consumed: false}`,
  `review_due: false`, `review_due_reason: under_budget`. The native assessment was medium despite
  the high-risk planning budget; review was not due and the boundary stays `b154ef3`. No native
  review started; no approval or acknowledgement.
- 2026-10-23: Route: delegated global tooling change under `workflow-odd-secure`; the source writer
  was the cloud tier chosen by the brief, on the source-only policy trigger. The advice records in
  `odd/advice/multi-agent-v2-phase1.md` are written in this later authorized metadata step
  (deferred, not pre-existing). Mirror
  writing/verification remains UNIMPLEMENTED and no mirror body was read. Q56 stays 5/10 with no
  authorized increment. No phase 2-4 allocation is created.
- 2026-10-23: This metadata unit updates the tracker, creates the advice record, refreshes the Q89
  queue status and appends the router row. Metadata commit and its assessment are PM-owned and not
  claimed here; independent orchestrator readback is still pending.
- 2026-10-23: Metadata correction round 1/1 (`correction_rounds_used: 1`) on the installed initial
  metadata (prior frozen result `ba6872bb9ed25f1dc957f37ef9149b9fafc65df4`; installed sandbox
  baseline commit `2423918`, parent `473c9cd`; source commit `473c9cd` unchanged). Findings fixed:
  M1 — the advice record attributed the integration same-model Kimi replay to a rate-limit
  fallback; it now states a stall-triggered same-model replay from PM-supplied project `.atl`
  evidence `4153`/`4154`/`4156`/`4166` and asserts no rate-limit or overload cause. M2 — the T2
  insertion heading now records the implemented status instead of "NOT implemented by this unit";
  the insertion table and future contracts are unchanged. M3 — this correction accounting is
  recorded here, in the advice disposition, in the Q89 status and in the current router row. The
  source candidate itself required 0 corrections; `global-config/opencode.json` bytes are
  unchanged (blob `854e5c4adf495f10251e093bbe597a7cf642e2e8`). No new advice, verifier, review,
  deploy or runtime test ran; metadata commit and assessment remain PM-owned and independent
  orchestrator readback is pending.

## Delivery strategy and forecast

**Chosen strategy:** auto-chain with the resolved topology stacked-to-main (owner-supplied); each
unit gets its own commit; no push or PR. **Forecast:** at least 212 planning lines plus 7 config
lines in T2, plus metadata churn; roughly 260-320 authored additions/deletions across phase 1.
Actual receipts remain authoritative and are not compressed to fit the reviewability cap. Each
unit stays under the 400-authored-line / 100 KiB per-commit reviewability cap; actual counts and
patch bytes are returned in the worker receipt. Phases 2-4 are external and are not estimated or
allocated in this repository.

## Count

Q56 counted unit **5/10** (2026-10-23), explicitly authorized by the dispatch brief even though
earlier planning units were not counted. No increment is authorized for the source or metadata
units. This tracker does not assert Q58 enforcement, deployment or broker runtime registration.

## Route / trigger evidence

Route: delegated, `workflow-odd-secure`; specialist `odd-apply` (DeepSeek-family cloud sandbox
writer). Triggers: preparation ahead of a writer; a two-or-more non-trivial-file unit; the secure
every-write delegation rule. Actual dispatch: PM-dispatched `odd-apply`; worker session
`ses_e973e8912ffeXn7tgIZQy2wIwm`; actual root `/work`. Worker baseline `work` at `603b203`
(parent `41c293d`); host branch/HEAD `chore/multi-agent-v2-phase1` at `41c293d`
(planning dispatch; dispatch-supplied and PM-read; not observable from the worker). RDD enabled
(global); boundary `41c293d`. No branch switch and no commit.

Source unit dispatch (2026-10-23): PM-dispatched cloud `odd-apply` writer
`ses_e97161e9bffejKEybYwkA7eTDv` (`opencode-go/deepseek-v4.1-flash@worker`; model self-reported,
root not captured by the writer — assumed `/work`, not observed). Input boundary `b154ef3`; source
commit `473c9cd`; no branch switch and no commit from the writer. Metadata unit (this one): separate
authorized lifecycle, cloud `gentle-ai-worker`; the actual root observed in its own sandbox is
`/work`, recorded in the PM receipt.

## Log

- 2026-10-23: `q90-phase1-plan-u1` planning prepared by delegated `odd-apply`. Checks: exact
  three-path scope, config/contract readback, Q89 collision check, `git diff --check`; no runtime
  tests, advice dispatch, verifier or native review. Commit `28d4a43`; PM assessment
  medium/`under_budget` (see below).
- 2026-10-23: At planning closure T2/T3 remained unchecked (now implemented in the source unit
  above). Mirror write/verification UNIMPLEMENTED; PM never reads the mirror. No implementation or
  activation was claimed at that point.
- 2026-10-23: Metadata closure by delegated `odd-apply` session
  `ses_e9727236dffeHvVgHnHvAlrar0`, actual root `/work`. Checks executed: initial HEAD `f78b2d4`
  parent `28d4a43`; `28d4a43^ = 41c293d`; base ancestry holds; the contract blob at `41c293d`
  and HEAD is equal (`555128e...`); `git diff --numstat/--name-status` is exactly the three
  authorized paths +212/-0; committed-candidate `git diff --check` is clean. No runtime tests,
  advice, verifier or native review ran.
- 2026-10-23: Limitation: static inspection was PARTIAL for all three Markdown paths (no LSP
  producer), so no syntax-clean claim is made. PM structural check read the tracker at 185 lines,
  Q89 at `docs/TODO.md:1471-1487`, and the router row at `ROUTER-LOG.md:274`. Independent
  orchestrator readback remains pending.
- 2026-10-23: Native/medium boundary: the committed candidate assessed medium/`under_budget`;
  boundary retained at `41c293d`; no approval, acknowledgement or native review. An explicit
  owner slice closure or native review is required before the next high-risk implementation.
  Post-metadata assessment is PM-owned closure, evidenced in the PM return envelope.
- 2026-10-23: Owner closed the planning medium slice (boundary `41c293d` -> `b154ef3`) before the
  source commit; owner closure only, no native review or approval.
- 2026-10-23: T2 source committed `473c9cd` (7 additions, 0 removals; blob `854e5c4...`); T3
  records the source checks, receipt and medium/`under_budget` assessment. Tools remain inert and
  not live; no deploy, restart or full verifier ran.
- 2026-10-23: Advice/verifier on the source unit: two-family pre wave (security Sol, integration
  Kimi), post security Qwen with no blockers, independent Sol verifier; details and dispositions
  are in `odd/advice/multi-agent-v2-phase1.md`. Static diagnostics PARTIAL. Metadata commit and
  assessment remain PM-owned.
- 2026-10-23: Correction round 1/1 (`correction_rounds_used: 1`) on the installed metadata
  baseline (`2423918`, parent `473c9cd`; PM-frozen prior result `ba6872bb`). Checked: exactly the
  four authorized metadata paths changed; `global-config/opencode.json` blob unchanged
  (`854e5c4...`); targeted readback of M1–M3; `git diff --check` clean. Source candidate correction
  count remains 0; no new advice/verifier/review cycle, no runtime tests, no deploy. Metadata
  commit and assessment are PM-owned.

## Next step

Phase 1 source is committed as `473c9cd` and assessed medium/`under_budget`; the reviewed boundary
stays `b154ef3` (owner closure advanced it from `41c293d`, and the source assessment did not advance
it further). The tools are inert and not live. Next: the PM commits this metadata unit and obtains
its own post-metadata assessment, followed by an independent orchestrator readback. No phase 2-4
work is allocated here; those phases belong to agent-sandbox-integration under separate
authorization.
