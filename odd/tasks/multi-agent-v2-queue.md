# Multi-agent v2 workflow config — Q90 queue revision
Task `q90-multi-agent-v2-queue`; units `q90-queue-revision-u1` (initial) and
`q90-decisions-correction-u1` (this correction). Class: documentation; route `workflow-odd-secure`
delegated cloud `odd-apply`. Base boundary `22132ad`; start HEAD `dfbeb29` (dispatch-supplied) on
`chore/multi-agent-v2-phase1`; source candidate `114366b`. No push, PR, deployment or native review.

## Problem
`docs/TODO.md` and this tracker still carried the earlier same-day "PM runs the lenses / PM owns the
review lifecycle" wording, plus the item-8 and GLM-seat questions, contradicting the owner's later
2026-10-23 correction. This unit records FUTURE PLANNING only; it changes no executable policy and
enables no host tool. Goal: six decisions, exact pipeline, four-lens terminology, Q90 six-unit
queue and the Q91 placeholder.

## Scope
- Update only `docs/TODO.md` (Q90 section), `ROUTER-LOG.md` (one appended row) and this tracker.
- Six decisions, pipeline order, four-lens terminology, same-day supersession, item 8.
- Q57-Q60 forward wording untouched; the same-day contradictory statements are superseded only
  inside Q90/tracker. Q58's historical body remains intact.
- No `WORKFLOW.md`, `PLAN.md`, spec, config, guard, skill, prompt, test or Q89 edit.

## Constraints
- Handover order retained: host tools built/tested first; owner PASS/plan-write decisions; queue
  -> config/guard/skills in one unit -> verifier -> mirror/restart/probes.
- T3/T4 slicing is PROVISIONAL: config/guard/skills atomic consistency requires an explicit
  slicing/size decision before coding.
- Deterministic Magic Context mirror is UNIMPLEMENTED; the PM never reads the mirror body.
- Q89 phase 1 is DONE and inert; phases 2-4 belong to agent-sandbox-integration, unchanged.
- RDD/native review: the PM commits/assesses this docs unit; the orchestrator dispatches review lanes
  and owns consent/acknowledgement; the owner approves delivery. Future planning stays distinct from
  the PM's current risk-assessment permission.

## Owner decisions (2026-10-23, corrected; future planning)
1. Review returns to the orchestrator: it dispatches FOUR lenses and the provider-selected
   refuter/validator, and keeps assessment, consent and acknowledgement. The PM dispatches no
   review lanes. The earlier 2026-10-23 "PM runs the lenses" decision is SUPERSEDED the same day;
   Q58's restriction is restored. The same-day Q57/Q58 forward statements that the PM runs the
   lanes are superseded; their historical sections are untouched.
2. The orchestrator first drafts the plan; the PM reads it and hands it to the Planner with its own
   suggestions, passing NO advice; the Planner finalises, calls ALL pre-code advisors itself plus
   its own read-only Luna evidence agent, runs post-code advisory, and issues BOTH gate verdicts.
   No additional advice for true docs; Q87's forward post-code actor is the Planner.
3. PM `glm-5.3-flash` high, fallback `qwen3.8-flash` high; Planner `openai/gpt-6.1-sol` high,
   xhigh for Gate 1 on multi-step/high-risk. Independence across orchestrator, PM, Planner, apply
   and review models. New planner-evidence uses `openai/gpt-6-luna`; sharing Luna with the Tiny
   writer `general` and `jd-fix-agent` is an explicit agreed exception (Tiny is passive/ungated).
4. The orchestrator does plan drafting + review dispatch, including a deliberate narrow
   `host_plan_write` exception limited to plan documents (grant approval posture still OPEN, not
   live), plus assessment/consent/acknowledgement. The PM loses relay AND advisor dispatch.
5. Q89 phase 1 is a completed prerequisite; phases 2-4 remain external to this repository.
6. Item 8 is RESOLVED: advice is evidence; the gate verdict is the approval act. On gated routes
   the Planner issues PASS/REFINE/ESCALATE after reading the plan revision, the pre-code advice it
   called, the post-code advice it ran, the raw lens findings, and the evidence commit assessment
   tier, phase-appropriate (Gate 1 does not imply post-code evidence exists). PASS technically
   approves the change and authorises the PM tick, NOT delivery/deployment/acceptance. Non-gated
   routes take advice as evidence only, with no verdict.

## Pipeline (exact)
orchestrator drafts plan -> PM reads/suggests -> Planner finalises, calls pre-code advisors and
Luna evidence agent -> Gate 1 -> writer implements -> PM closes unit -> orchestrator dispatches
four post-commit lenses, Planner runs post-code advice -> Gate 2 -> PM ticks -> orchestrator
assesses/acknowledges -> owner approves delivery.

## Review terminology
FOUR lenses — R1 risk `qwen3.8-flash`, R2 readability `kimi-k2.7-code`, R3 reliability `minimax-m3`
(pending the M3 hang check), R4 resilience `glm-5.3-flash` — PLUS the provider-selected refuter
`mimo-v2.6-flash` and validator `claude-haiku-5-5`.

## Superseded decisions
Earlier 2026-10-23: PM ran the review lanes and owned the lifecycle and advisor dispatch; item 8
and the GLM-seat collision were open. Later 2026-10-23 (authoritative): review returns to the
orchestrator (four lenses plus provider refuter/validator); PM dispatches no review lane or
advisor; Planner calls all advisors and its evidence agent; item 8 resolved, GLM collision gone;
Q58's restriction restored; Q57/Q58 sections unchanged.

## Planning record
- v2 planning source: `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md`.
- Q89 phase 1: `odd/tasks/multi-agent-v2-phase1.md`; source `473c9cd`, metadata `22132ad`; inert,
  tools not live; boundary advanced to `22132ad` by owner closure, not native review.
- Queue: Q90 T1 COMPLETE — source `114366b`, metadata `dfbeb29`, final PM assessment
  medium/`under_budget` at retained boundary `22132ad`. Q90 IN PROGRESS; T2-T6 PLANNED; Q91 PLANNED.

## Work units
| Unit | Scope | Status | Prerequisites |
|---|---|---|---|
| T1 | Queue revision: Q90, Q87 overlay, Q91, router | COMPLETE source `114366b`, metadata `dfbeb29`, medium/`under_budget` | owner authorization 2026-10-23 |
| T2 | Readiness: decisions b/d/e/f, host tools built/tested, model IDs, seat independence, M3 hang | PLANNED | T1; agent-sandbox-integration host tools |
| T3 | Config/agents/fallbacks: orchestrator plan tool + review dispatch, Planner advisor/evidence permissions, PM loses relay/advisor dispatch, new planner-evidence agent | PLANNED | T2; explicit T3/T4 slicing decision |
| T4 | Recipe/guard/skills contract for the same actors/permissions | PLANNED | T2; T3 slice decision; atomic consistency |
| T5 | Verifier checks + digest re-pin | PLANNED | T3, T4 |
| T6 | Mirror, owner restart, behavioral probes, trial metrics | PLANNED | T5; owner restart |

## Open owner/readiness decisions
a. RESOLVED (item 8): advice is evidence; the gate verdict is the approval act.
b. OPEN: `host_plan_write` approval posture, including the orchestrator's narrow plan-document
   exception; not live.
c. RESOLVED: the PM dispatches no review lanes, so the `review-resilience` GLM / `review-risk`
   `qwen3.8-flash` seat collision is gone.
d. OPEN: model IDs — `claude-haiku-5-5`, `qwen3.8-flash`, `qwen3.8-max`, `glm-5.3-flash`,
   `mimo-v2.6-flash`, `minimax-m3`, `kimi-k2.7-code`, `google/gemini-flash-latest`.
e. OPEN: M3 hang verification before any native seat uses `minimax-m3`.
f. OPEN: one-work-unit config/guard/skills versus Q87's ~400 lines / 100 KiB: choose a slice or
   record an explicit owner size exception.

## Commit and assessment evidence
- Source `114366b`; metadata `dfbeb29`; final PM assessment medium/`under_budget` at retained
  boundary `22132adc686629cceaa7b32e469c5ec10d009e2a`.
- Historical initial-unit receipt: 206 authored lines, 25,263 authored patch bytes, generated/
  binary []; correction 1/1. Its SOURCE assessment was 6 cumulative paths / 563 lines
  (`consumed=false`, `review_due=false`): a cumulative slice, NOT the unit's 206 lines and NOT
  final metadata statistics. This correction unit does not consume another correction round.
- The PM envelope supplies this correction unit's commit SHA and assessment; no hash or assessment
  success is claimed here.

## Log
- Route: delegated `workflow-odd-secure`, cloud `odd-apply`; PM-dispatched; initial writer
  `ses_e96403ac5ffecd6SwEe5qMfxM2` (frozen result `5b035b6bf790e732fbd644f377073b65936a37c4`,
  installed); this correction round 1/1 `ses_e9635ed7affeJUhfScAR23O6zs`; PM owns commit/assessment; mirror UNIMPLEMENTED.
- Initial unit: three allowed paths, +202/-4 = 206 authored lines / 25,263 bytes; committed
  `114366b`; metadata `dfbeb29`; PM factual readback F1-F5 accepted; correction 1/1.
- This unit: sandbox root `/work`; baseline HEAD `0aa908b` (synthetic baseline; parent `dfbeb29`;
  tree includes the installed initial result); branch `work`; `22132ad`, `114366b`, `dfbeb29` are
  ancestors; no merge/rebase. PM first-pass readback F1-F3 accepted; initial `aft_inspect` PARTIAL
  (no Markdown LSP producer for all three paths), not syntax clean. Acceptance/forecast: exactly 3
  paths; tracker <=130 lines; future planning only; <=400 authored lines / 102,400 bytes; ask-on-risk
  feature-delivery strategy retained, no PR. Checks: `git diff --check` and `git diff --cached --check`
  clean; structural readback of six decisions/pipeline/terminology/open decisions and one router row; no advisor/verifier/runtime suite.

## Next step
T2 readiness only — open decisions (b), (d), (e), (f), external host tools built/tested, model IDs,
seat independence and M3 hang — not config coding. Q90 remains IN PROGRESS.
