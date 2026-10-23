# Multi-agent v2 workflow config — Q90 queue revision
Task `q90-multi-agent-v2-queue`, unit `q90-queue-revision-u1`. Class: documentation (Q90 queue
revision only). Route: `workflow-odd-secure`, delegated cloud `odd-apply`. Base boundary
`22132adc686629cceaa7b32e469c5ec10d009e2a`; start HEAD
`cd6b7108df52c6e423d431197679ae2809cf72fc` (dispatch-supplied); committed candidate
`114366b35651316e00c972f71f723b7804fcae4c` on `chore/multi-agent-v2-phase1`. No push, PR,
deployment or native review.

## Objective
Record the owner's 2026-10-23 v2 planning direction in the durable queue: Q90 with six units,
a Q91 placeholder, and supersession lines that keep historical evidence intact.

## Problem
`docs/TODO.md` still describes the pre-v2 PM layer: Q57's deny-default orchestrator, Q58's
historical PM-external review restriction, and Q60's Sol PM seat conflict with the new direction.
Without a queue record, later config/guard/skill work has no ordered contract; this revision enables no host tool.

## Scope
- Update only `docs/TODO.md`, `ROUTER-LOG.md` and this tracker; Q90 records five decisions and T1-T6.
- Q57-Q60 forward wording; Q58 historical text untouched; Q87 planning-only actor overlay.
- Q91 placeholder; no planner-tier body from `9938cd1` (not locally available).
- No `WORKFLOW.md`, `PLAN.md`, spec, config, guard, skill, Q89 tracker or handover edit.

## Constraints
- Handover order retained: host tools built/tested first; owner PASS/plan-write decisions;
  queue -> config/guard/skills in one work unit -> verifier -> mirror/restart/probes.
- T3/T4 slicing is provisional: the handover requires config/guard/skills atomic consistency;
  an explicit slicing/size decision is required before coding.
- Deterministic Magic Context mirror tool is UNIMPLEMENTED; the PM does not read the Magic Context mirror body.
- Q89 phase 1 is DONE and inert; phases 2-4 belong to agent-sandbox-integration.
- RDD/native review and deployment are PM/owner actions, never this writer's.

## Owner decisions (2026-10-23)
1. The PM runs the six native `asi-review-*` lanes and keeps the review lifecycle; lenses are
   independently driven outside the implementing writer, NOT outside the PM. This supersedes
   Q58 enforced independence and resolves its open `host_review_start` question.
2. The Planner runs post-code advisory on planned/gated routes, replacing the PM
   `advisor-*-post` closure; the Q87 budget matrix's forward actor is the Planner on planned
   routes; no added advice for true docs.
3. PM `glm-5.3-flash` high, fallback `qwen3.8-flash` high; Planner `openai/gpt-6.1-sol` high,
   xhigh for gate 1 on multi-step/high-risk. Independence across PM/Planner/apply/review.
4. The orchestrator does assessment/consent/acknowledgement only; it is not a lens.
5. Q89 phase 1 is a completed prerequisite; phases 2-4 remain external.

## Planning record
- v2 planning source: `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md`.
- Q89 phase 1: `odd/tasks/multi-agent-v2-phase1.md`; source `473c9cd`, metadata `22132ad`;
  inert, tools not live; boundary advanced to `22132ad` by owner closure, not native review.
- Queue status: Q90 T1 COMPLETE/SOURCE-COMMITTED `114366b`; metadata commit and final PM
  assessment pending only. Q90 overall IN PROGRESS; T2-T6 PLANNED. Q91 PLANNED, prerequisite Q90.

## Handover order (exact, :213-218)
1. `agent-sandbox-integration` builds and tests the host tools.
2. Owner decisions: item 8 and the `host_plan_write` approval decision.
3. This repo: queue revision, then config, guard and skills in one work unit, then the verifier.
4. Verifier mirror, owner restart, behavioral probes (including nested advisor dispatch).

## Done / conflict / gap summary
| Area | Finding | Evidence |
|---|---|---|
| Q53-Q56 | Q53 DONE 7/8 (item 4 deferred); Q54 DONE report, broker deny/identity unverifiable; Q55 contract done, pilot open; Q56 5/10 | `docs/TODO.md@cd6b710:500-618` |
| Q57-Q60 | Q57 planned, numeric cap deferred; Q58 historical PM-external review restriction (superseded forward); Q59 source+metadata DONE, deploy unverified; Q60 old PM-on-Sol (superseded forward) | `docs/TODO.md@cd6b710:620-706` |
| Q61-Q64 | Q61 independent-proof language stale; Q62 planned; Q63 blocked upstream; Q64 done | `docs/TODO.md@cd6b710:707-778` |
| Q85-Q89 | Q85 runtime unverified; Q86 custody/delivery unresolved; Q87 source complete, deployment not performed (Q84 fold recorded while Q84 remains BLOCKED); Q89 phase1 DONE, inert/not live | `docs/TODO.md@cd6b710:1407-1499` |
| Planner | Unmerged Q67 planner-tier plan, renumbered as the Q91 placeholder per the handover; branch `docs/pm-planner-delegation` at `9938cd1`; locally unresolved by this worker (no local object), not a general absence claim | `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md:13-16` |

## Work units
| Unit | Scope | Status | Prerequisites |
|---|---|---|---|
| T1 | Queue revision: Q90, Q57-Q60 forward text, Q87 overlay, Q91, router | COMPLETE source `114366b`; metadata/PM assessment pending | owner authorization 2026-10-23 |
| T2 | Readiness: owner decisions a-f, host tools built/tested, model IDs, seat independence, M3 hang | PLANNED | T1; agent-sandbox-integration host tools |
| T3 | Config/agents/fallbacks: `opencode.json`, `rate-limit-fallback.json` | PLANNED | T2; explicit T3/T4 slicing/size decision |
| T4 | Recipe/guard/skills routing contract | PLANNED | T2; T3 slice decision; atomic consistency |
| T5 | Verifier checks + digest re-pin | PLANNED | T3, T4 |
| T6 | Mirror, owner restart, behavioral probes, trial metrics | PLANNED | T5; owner restart |

## Open owner/readiness decisions (do not resolve here)
a. Handover item 8: `host_gate_verdict` PASS versus "advice is evidence, never approval".
b. `host_plan_write` approval posture.
c. `review-resilience` GLM and `review-risk` qwen3.8-flash seats now the PM dispatches.
d. Model-ID existence: `claude-haiku-5-5`, `qwen3.8-flash`, `qwen3.8-max`, `glm-5.3-flash`,
   `mimo-v2.6-flash`, `minimax-m3`, `kimi-k2.7-code`, `google/gemini-flash-latest`.
e. M3 hang verification before any native seat uses `minimax-m3`.
f. The handover's one-work-unit config/guard/skills versus Q87's ~400 authored lines / 100 KiB:
   choose a slice or record an explicit owner size exception.

## Acceptance and checks
- Exactly three paths change; Q90/Q91 unique; Q67 and Q53-Q56/Q61-Q64 bodies unchanged;
  Q58 historical text retained; Q89 unchanged; tracker <=120 lines.
- Staged receipt: 206 authored lines, 25,263 authored patch bytes, generated/binary []; cap
  <=400 lines / 102400 bytes. `git diff --check` working and `--cached` clean (writer raw).
- PM factual first pass F1-F5 recheck accepted; `aft_inspect` PARTIAL (no Markdown LSP
  producer), so no syntax-clean claim; zero advisor/verifier/runtime tests (true docs).
- Correction 1/1: initial writer `ses_e96a0a14dffenleKoF0PjV2V2K`; correction
  `ses_e9699569affeammLeLt1qv21RZ`; no reset or additional refinement authorized.

## Commit and assessment evidence
- Implementation commit `114366b35651316e00c972f71f723b7804fcae4c` on
  `chore/multi-agent-v2-phase1`; 202 insertions / 4 deletions = 206 authored lines.
- PM assessment at boundary `22132adc686629cceaa7b32e469c5ec10d009e2a`: medium
  (`executable_change`, handover path), `under_budget`, `review_due=false`, `consumed=false`,
  `changed_paths=6`, `changed_lines=563` — cumulative slice, not this unit's 206 lines.
  Boundary retained; the pending slice is neither native review nor approval. Start HEAD
  `cd6b710` is distinct from the committed candidate; metadata commit identity comes from the
  PM envelope after commit.

## Route and dispatch
Delegated `workflow-odd-secure`, cloud `odd-apply`. Triggers: preparation ahead of a writer; a
three-path documentation unit; the secure every-write delegation rule. Explorer
`ses_e96a412fdffe5iDPc9Djax9D6o` reported grouped statuses; the PM owns commit and assessment;
deterministic Magic Context mirror remains UNIMPLEMENTED.

## Next step
T2 prerequisites/readiness only — owner decisions a-f, external host tools built/tested, model
IDs, seat independence and M3 hang — not config coding. Q90 remains IN PROGRESS.

## Forecast
This unit: 206 authored lines / 25,263 bytes, within <=400 lines and <=100 KiB. Feature total is
unknown and likely more than 400 lines; use an ask-on-risk strategy and split by T2-T6. No PR
authorization.
