# Multi-agent v2 workflow config — Q90 queue revision
Task `q90-multi-agent-v2-queue`; units `q90-queue-revision-u1` (initial),
`q90-decisions-correction-u1` (correction) and `q90-t2-readiness-u1` (this T2 readiness closure).
Class: documentation; route `workflow-odd-secure` delegated cloud `odd-apply`. Base boundary
`22132ad`; host branch ref read by the PM `21ff2a5` on `chore/multi-agent-v2-phase1`; prior
candidates: T1 source `114366b`, T1 metadata `dfbeb29`, decision-set correction `21ff2a5`.
No push, PR, deployment or native review.

## Problem
Earlier same-day text still carried open plan-write, model-ID, M3-seat and slicing questions plus
the superseded "PM runs the lenses" wording. This unit records the owner's final T2 readiness
decisions as FUTURE PLANNING only; it changes no executable policy and enables no host tool.

## Scope
- Update only `docs/TODO.md` (Q90), `ROUTER-LOG.md` and this tracker.
- Record decisions (b), (d), (e) and (f) and the T3a-d -> T4 -> T5 -> T6 dependency order.
- Update contradictory OPEN approval and M3 seat language; label earlier evidence historical.
- No `WORKFLOW.md`, `PLAN.md`, spec, config, guard, skill, prompt, test, handoff or Q89 edit.

## Constraints
- Handover order retained: host tools built/tested first; owner decisions; then actor slices ->
  verifier/digest -> mirror/restart -> behavioral probes/trial metrics.
- T3 slicing is RESOLVED (f): each actor commit changes config task permissions, guard
  `ROUTE_STAGES`/helper lists, route skills and its own `WORKFLOW.md` lines together.
- Deterministic Magic Context mirror is UNIMPLEMENTED; the PM never reads the mirror body.
- RDD/native review: the PM commits/assesses; the orchestrator dispatches the lanes and owns
  consent/acknowledgement; the owner approves delivery.

## Owner decisions (2026-10-23, corrected; future planning)
1. Review returns to the orchestrator: it dispatches FOUR lenses and the provider-selected
   refuter/validator, and keeps assessment, consent and acknowledgement. The PM dispatches no
   review lanes. The earlier same-day "PM runs the lenses" decision is SUPERSEDED; Q58's
   restriction is restored; Q57/Q58 historical sections are untouched.
2. The orchestrator first drafts the plan; the PM reads it and hands it to the Planner with its
   own suggestions, passing NO advice; the Planner finalises, calls ALL pre-code advisors plus
   its own read-only Luna evidence agent, runs post-code advisory, and issues BOTH gate verdicts.
   No additional advice for true docs; Q87's forward post-code actor is the Planner.
3. PM `glm-5.3-flash` high, fallback `qwen3.8-flash` high; Planner `openai/gpt-6.1-sol` high,
   xhigh for Gate 1 on multi-step/high-risk. Independence across orchestrator, PM, Planner,
   apply and review models. Planner-evidence uses `openai/gpt-6-luna`; sharing Luna with the
   Tiny writer `general` and `jd-fix-agent` is an explicit agreed exception (Tiny is
   passive/ungated).
4. The orchestrator does plan drafting + review dispatch, plus assessment/consent/acknowledgement.
   Its `host_plan_write` posture is RESOLVED by T2 decision (b): ask-gated for BOTH orchestrator
   and Planner, NO no-ask exception. The PM loses relay AND advisor dispatch.
5. Q89 phase 1 is a completed prerequisite; phases 2-4 remain external to this repository.
6. Item 8 is RESOLVED: advice is evidence; the gate verdict is the approval act. On gated routes
   the Planner issues PASS/REFINE/ESCALATE after reading the plan revision, the pre-code advice it
   called, the post-code advice it ran, the raw lens findings and the evidence commit assessment
   tier, phase-appropriate (Gate 1 does not imply post-code evidence exists). PASS technically
   approves the change and authorises the PM tick, NOT delivery/deployment/acceptance. Non-gated
   routes take advice as evidence only, no verdict.

## Pipeline (exact)
orchestrator drafts plan -> PM reads/suggests -> Planner finalises, calls pre-code advisors and
Luna evidence agent -> Gate 1 -> writer implements -> PM closes unit -> orchestrator dispatches
four post-commit lenses, Planner runs post-code advice -> Gate 2 -> PM ticks -> orchestrator
assesses/acknowledges -> owner approves delivery.

## T2 readiness (complete)
Owner decisions dated 2026-10-23; evidence is owner-supplied. These close DECISIONS only, not the
remaining host-tool built/tested, session, independence or hang checks.

(b) RESOLVED — `host_plan_write` is ask-gated for BOTH the orchestrator and the Planner; NO
    no-ask exception. PM suggestions are messages, not plan writes; the no-`ctx.ask` ask is rejected.
(d) RESOLVED — all named model IDs resolve, evidenced by THREE owner-reported host
    `opencode models` runs on 2026-10-23. Go pool present: qwen3.8-flash, qwen3.8-max,
    glm-5.3-flash, glm-5.3, kimi-k2.7-code, minimax-m3, minimax-m3.1-flash, mimo-v2.6-flash,
    claude-haiku-5-5, claude-sonnet-5-5, gpt-6-luna. OpenAI present: openai/gpt-6.1-sol
    (+ -fast, -ultrafast) and openai/gpt-6-luna (+ -fast). Google present:
    google/gemini-flash-latest, google/gemini-4-argon, google/gemini-3.8-flash. Shared-pool
    opencode-go/gpt-6-luna and opencode-go/gemini-3.8-flash exist but are NOT the handover's
    named providers.
(e) FAIL CLOSED — `minimax-m3` is excluded from EVERY native review seat until the hang is proven
    absent. The owner states the repo holds no hang record (owner-attributed absence; no
    independent search is claimed here). `minimax-m3.1-flash` exists but is NOT promoted without
    session and hang checks. R3 reliability has NO confirmed seat. T3d chooses a replacement
    from claude-sonnet-5-5, minimax-m3.1-flash (after checks), muse-spark-1.3-contributor or
    step-5-preview. No seat is chosen in this unit; model-ID resolution does NOT prove seat
    independence or hang clearance. Other seats unchanged: R1 risk `qwen3.8-flash`, R2
    readability `kimi-k2.7-code`, R4 resilience `glm-5.3-flash`; refuter `mimo-v2.6-flash`,
    validator `claude-haiku-5-5`.
(f) RESOLVED — actor slices: T3a orchestrator (plan draft + review dispatch); T3b Planner (advisor +
    evidence-agent + verdict permissions); T3c PM (drop relay/advisor dispatch; GLM seat); T3d
    fallbacks/remaining seats. EACH actor commit changes config task permissions, guard
    `ROUTE_STAGES`/helper lists, route skills and its own `WORKFLOW.md` lines together; no size
    exception and no intermediate guard-denies/skill-allows state — any inconsistent slice STOPS AND ASKS.

## Work units
| Unit | Scope | Status | Prerequisites |
|---|---|---|---|
| T1 | Queue revision: Q90, Q87 overlay, Q91, router | COMPLETE source `114366b`, metadata `dfbeb29`, medium/`under_budget` | owner authorization 2026-10-23 |
| T2 | Readiness: decisions b/d/e/f, model IDs, M3/hang and seat gates | COMPLETE for decisions/evidence; host-tool, session and independence checks remain future implementation gates | T1; owner decisions 2026-10-23 |
| T3a | Orchestrator slice: plan draft tool + review dispatch; ask-gated `host_plan_write` | PLANNED, high risk | T2; pre-advice, post-advice, one independent verifier, ONE correction round, native review after commit |
| T3b | Planner slice: advisor + evidence-agent + both verdict permissions | PLANNED, high risk | T2; T3a landed with consistent surfaces |
| T3c | PM slice: drop relay/advisor dispatch; GLM seat | PLANNED, high risk | T2; T3a/T3b landed with consistent surfaces |
| T3d | Fallbacks and remaining seats; R3 replacement selection | PLANNED, high risk | T2; T3a-T3c; M3 hang proof and session checks before any `minimax-m3.1-flash` promotion |
| T4 | Verifier checks + digest re-pin | PLANNED | ALL T3a-T3d slices landed |
| T5 | Mirror and owner restart | PLANNED | T4 |
| T6 | Behavioral probes and trial metrics | PLANNED | T5; owner restart |

## Open choices and standing gates
- Genuine open choices: (i) the R3 reliability replacement in T3d; (ii) M3 hang verification before
  any `minimax-m3.1-flash` promotion. Prerequisites (host tools built/tested, sessions, seat
  independence) remain prerequisites, not owner decisions, and are NOT completed by T2.
- Resolved: (a) item 8; (b) plan-write ask-gated; (c) GLM/`qwen3.8-flash` collision gone; (d) model
  IDs; (f) actor slicing. Standing FAIL CLOSED: `minimax-m3` excluded from every native seat (e).

## Commit and assessment evidence
- Historical record: v2 planning source
  `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md`; Q89 phase 1 source `473c9cd`,
  metadata `22132ad`, inert, tools not live.
- Historical T1: source `114366b`; metadata `dfbeb29`; final PM assessment medium/`under_budget` at
  retained boundary `22132adc686629cceaa7b32e469c5ec10d009e2a`; receipt 206 lines / 25,263 bytes /
  generated-binary []; SOURCE assessment 6 cumulative paths / 563 lines (slice, not this unit).
- Closure unit (`q90-t2-readiness-u1`): observed implementation commit `115fbdd3810ad942ec1aed0e769232f9897ad5f7`;
  targeted recheck F1-F5 ACCEPTED; observed IMPLEMENTATION assessment at retained boundary
  `22132adc686629cceaa7b32e469c5ec10d009e2a` = medium/`under_budget`, 6 cumulative paths / 671 lines,
  `consumed=false`, `review_due=false` (not the metadata/forecast assessment; metadata result not claimed).
  ROUTER-LOG row 279 closure wording and row 272 Q79 D/E metadata-commit text were corrected to
  "metadata commit not recorded; see odd/tasks/q79-mirror-write-ownership.md"; two-row evidence
  convention only (not workflow policy): no literal pending-commit label, self-referential SHA =
  "commit SHA recorded in the PM envelope". Owner authorized one additional metadata lifecycle after
  NEEDS_INPUT without resetting the original correction count 1/1 (reason: PM metadata closure;
  scope: rows 272/279 + tracker; limit: one cloud writer, no code/config/T3a; metadata self-SHA as above).
- The previous pending medium slice must close by explicit owner decision or review before the
  next high-risk (T3a) commit. Boundary `22132ad` is retained; no advance is claimed.

## Log
- Historical initial writer `ses_e96403ac5ffecd6SwEe5qMfxM2` (frozen result
  `5b035b6bf790e732fbd644f377073b65936a37c4`, installed); correction writer
  `ses_e9635ed7affeJUhfScAR23O6zs`; both previous units, not this one.
- Initial Task evidence (PM-observed): dispatch `ses_e96143036ffeG9d4jb9Xh3I9WB` completed and
  APPLIED; frozen result `c09ab9b30aac08418dc46f2423537ca23208f641`; exactly 3 allowed paths,
  321 authored lines / 39,048 bytes. Current correction round 1/1.
- Current unit: trigger owner authorization 2026-10-23; delegated `workflow-odd-secure`, cloud
  `odd-apply`, PM-dispatched. Sandbox workspace `/work`, branch `work`, synthetic baseline HEAD
  `7c08e45` (parent `21ff2a5`), not the host branch. Host branch ref read by the PM: `21ff2a5`
  on `chore/multi-agent-v2-phase1`; `.git/HEAD` itself exposes only the symbolic branch, not the
  SHA. `22132ad`, `114366b` and `dfbeb29` resolve and are ancestors; no merge/rebase in progress.
- Observed checks: exactly three allowed paths; `git diff --check` and `git diff --cached --check`
  clean. PM static check (`aft_inspect` scoped to all 3 paths): PARTIAL; no Markdown LSP producer
  for the 3 files; complexity unfinished / `dead_code` unsupported; no syntax-clean claim. No
  advisor, verifier, runtime, deployment or native-review evidence; zero runtime tests. The
  pre-existing untracked sandbox bundle is excluded and not staged.

## Next step
T3a (orchestrator slice) is next: a high-risk config + guard + route-skill + `WORKFLOW.md` change
owing pre-code advice, post-advice, one independent verifier, ONE correction round, and native
review after commit. Close the pending medium slice first. Q90 remains IN PROGRESS.
