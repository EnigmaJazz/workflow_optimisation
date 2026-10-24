# Multi-agent v2 workflow config — Q90 queue revision
Task `q90-multi-agent-v2-queue`; units `q90-queue-revision-u1` (initial),
`q90-decisions-correction-u1` (correction), `q90-t2-readiness-u1` (T2 closure) and T3a1 metadata
closure `q90-t3a1-orchestrator-tools-u1`. Class: documentation; route `workflow-odd-secure` delegated cloud `odd-apply`.
Prior base boundary `22132ad`; current native-reviewed source boundary `77ef08a` on
`chore/multi-agent-v2-phase1`; earlier candidates: T1 source `114366b`, T1 metadata `dfbeb29`,
decision-set correction `21ff2a5`, T2 readiness `115fbdd`, T2 metadata `2f196b6`. No push, PR or
deployment.

## Problem
Earlier same-day text still carried open plan-write, model-ID, M3-seat and slicing questions plus
the superseded "PM runs the lenses" wording. The T1/T2 units recorded the owner's readiness
decisions as FUTURE PLANNING only; they changed no executable policy and enabled no host tool.

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
    `opencode models` runs on 2026-10-23. Go pool: qwen3.8-flash, qwen3.8-max, glm-5.3-flash,
    glm-5.3, kimi-k2.7-code, minimax-m3, minimax-m3.1-flash, mimo-v2.6-flash, claude-haiku-5-5,
    claude-sonnet-5-5, gpt-6-luna. OpenAI present: openai/gpt-6.1-sol (+ -fast, -ultrafast) and
    openai/gpt-6-luna (+ -fast). Google present: google/gemini-flash-latest, google/gemini-4-argon,
    google/gemini-3.8-flash. Shared-pool opencode-go/gpt-6-luna and opencode-go/gemini-3.8-flash
    exist but are NOT the handover's named providers.
(e) FAIL CLOSED — `minimax-m3` is excluded from EVERY native review seat until the hang is proven
    absent. The owner states the repo holds no hang record (owner-attributed absence; no independent
    search is claimed here). `minimax-m3.1-flash` exists but is NOT promoted without session and
    hang checks. R3 reliability has NO confirmed seat. T3d chooses a replacement from
    claude-sonnet-5-5, minimax-m3.1-flash (after checks), muse-spark-1.3-contributor or
    step-5-preview. No seat is chosen in this unit; model-ID resolution does NOT prove seat
    independence or hang clearance. Other seats unchanged: R1 risk `qwen3.8-flash`, R2
    readability `kimi-k2.7-code`, R4 resilience `glm-5.3-flash`; refuter `mimo-v2.6-flash`,
    validator `claude-haiku-5-5`.
(f) RESOLVED — actor slices: T3a1/T3a2 orchestrator (plan/test tools, then review dispatch); T3b
    Planner (advisor + evidence-agent + verdict permissions); T3c PM (drop relay/advisor dispatch;
    GLM seat); T3d fallbacks/remaining seats. EACH actor commit changes config task permissions,
    guard `ROUTE_STAGES`/helper lists, route skills and its own `WORKFLOW.md` lines together; no size
    exception and no intermediate guard-denies/skill-allows state — any inconsistent slice STOPS AND ASKS.

## T3a1 closure (complete)
Source `b89f5a00d0bc1412f672954aaa7c1810c7a34092` on `chore/multi-agent-v2-phase1`; 11 paths,
400 authored changed lines / 48,326 bytes; 77 focused tests plus Bun controls; assembled
orchestrator prompt 419 lines / 61,050 bytes SHA-256 `0cf8da259010ca402320756ef19aaa148b9706d8c93f31a535cd97684b767838`; verifier SHA-256
`9b10a8bee1873fd7adc2e23ecd68fb9f0bd2edf5a41eb2cffdbe6dd9cc865c29`.
Review lineage `review-1ca5500bc130a1cf`, target sha256:
`3bb686d938a115b6330bb81f9da519f06bab7c2562e74642e79ab4c5a6e6f271`, four lenses APPROVED and acknowledged, authority burned. R1 risk and R3
reliability NO FINDINGS; R4 resilience R4-1 WARNING/R4-2 SUGGESTION and R2 readability
R2-001 SUGGESTION admitted. All reviewer claims are informational/non-blocking, deferred
follow-up; not endorsed or implemented here, and no correction was opened:
- R4-1 resilience WARNING, `verify-workflow.sh:2809-2817` (proof `:2836`): `host_test_run` has a grant sweep excluding only orchestrator, but `host_plan_write` has no equivalent verifier/Python/Bun sweep, so future non-orchestrator not-deny plan grants would pass gates.
  Existing PM plan-write asks are intentionally preserved by source scope; no blanket denial or fix.
  Proof refs: `global-config/opencode.json:581-582, :2545`; `tests/test_review_pipeline_permissions.py:718-731`; `tests/test_review_pipeline_permissions.js`.
- R4-2 resilience SUGGESTION, `tests/test_review_pipeline_permissions.py:709-715`: `run_controls`
  skips only `PermissionError`; missing Bun falls back to `'bun'` and raises unhandled
  `FileNotFoundError` instead of skipping.
- R2-001 readability SUGGESTION, `global-config/prompts/gentle-orchestrator/overlay.md:57`:
  "narrowly defined, pre-registered" `host_test_run` qualifier names no registry, authority or
  allowed-test list, so maintainers cannot determine the permitted set from the contract alone.
Readability attempt 1 was an incomplete-JSON transport refusal, attempt 2 admitted; rejected artifact `.git/gentle-ai/rejected-results/review-1ca5500bc130a1cf/review-readability-1-42837fe6b897.json` is transport evidence, not a finding.

## T3a2 enforcement unit (complete)
Unit `q90-t3a2-review-dispatch-u1`; class global-tooling-change; route
`workflow-odd-secure`, delegated cloud specialist `odd-apply`; baseline `2173738` on
`chore/multi-agent-v2-phase1`; ENFORCEMENT, not migration: `opencode.json` already granted
all six `asi-review-*` lanes, denied the six plain lanes, and gave both PMs `"*": "deny"`
with no review keys; config/guard/skills/`WORKFLOW.md` unchanged.

Four commits in order from `2173738`: `3b96708128dadca83ab59bfa9adfafe2792118c7` enforcement source
(347/21,247); `3069e3338001f78b1280e1b66165e51fa954959d` owner advice; `cdf9056f7a0e1912e1930847ff31205b2b132861`
two omitted-control expected-string corrections plus digest (6/2,502);
`77ef08af7c376386b24a62e26efc6809b9753bdf` post-escalation R4-1/R4-2 fix (coordinator
`host_plan_write` sweep and `run_controls` Bun-absence handling) plus digest (73/9,052). Range four
paths / 484 lines: `verify-workflow.sh`, `tests/test_review_pipeline_permissions.py`,
`global-config/plugins/workflow-health-check.ts`, `odd/advice/q90-t3a2-review-dispatch.md`; no live
deployment.

Approved lineage `review-bff8f73a89ebffa5`, target `36776914a529bd3645a44d7532f8518cb3a9c7ec50fff49f8570d0cd10b259c2`,
approved/acknowledged, authority burned per owner; terminal consumption `855454c2…8f3960` binds
target/lineage; no severity or approval field, so state/severities rest on owner-confirmed admitted
results plus ack readback. Prior lineage `review-83d13326ee0004a8` escalated on `unknown_causality`
with historical R4-1/R4-2: terminal, SUPERSEDED, NOT approved; different findings. Metadata slice
`b89f5a0..2173738` closed by owner decision, not native review.

Deferred WARNINGs, informational/non-blocking, no correction opened: `R3-MISSING_BUN_SKIP`
reliability `tests/test_review_pipeline_permissions.py:908`
(`run_script` lacks the Bun-absence skip now in `run_controls`); `R4-1`
resilience same file `:920-930` (same Bun-absence class); `R4-2` resilience
`verify-workflow.sh:2819-2828` (`hostPlanWriteGrantSweepFailures` treats boolean false as a
grant while `reviewDispatchFailures` accepts false as deny; no behaviour change); `R4-3`
resilience `verify-workflow.sh:3460` (control/producer alignment for
`<inherit/none>` inferential).

Checks (prior writer/verifier execution reports, not owner-admitted review results):
permission 20 and PM-prompt 45 passed; Bun 103 controls; V1/I1 jointly 48 PM
combinations + 50 grant/11 nongrant; post-escalation 23 focused, 0 skips with Bun
present; `HostFixedToolPermissionTests` 6 OK/4 skips; `bash -n`, pin equality,
`git diff --check`; verifier digest `e76baeda08b6504602710aec87e321ba77ba8d765a877652d0f46bbf652c2616`.
Static pass PARTIAL (Bash/Python 0, TS workspace marker absent), no clean claim; full verifier/live
hooks/deploy UNVERIFIED, not rerun. Source normal `correction_rounds_used=1`; owner exceptions
retained separately: sentinel+pin correction (2026-10-23) after V1/I1, and scoped
post-escalation R4-1/R4-2 fix (2026-10-23) with NO new advisor/verifier. Metadata correction
round 1/1; owner overrides do not reset the normal source counter. Mirror UNIMPLEMENTED; body never read/written.

## Work units
| Unit | Scope | Status | Prerequisites |
|---|---|---|---|
| T1 | Queue revision: Q90, Q87 overlay, Q91, router | COMPLETE source `114366b`, metadata `dfbeb29`, medium/`under_budget` | owner authorization 2026-10-23 |
| T2 | Readiness: decisions b/d/e/f, model IDs, M3/hang and seat gates | COMPLETE for decisions/evidence; metadata commit `2f196b6`; owner decision 2026-10-23 closed the retained MEDIUM SLICE (`22132ad`..`2f196b6`), not a native review of it; host-tool, session and independence checks remain future gates | T1; owner decisions 2026-10-23 |
| T3a | Orchestrator slice: T3a1 plan/test tools + ask-gated `host_plan_write`; T3a2 review dispatch | T3a1 COMPLETE source `b89f5a0`, native review `review-1ca5500bc130a1cf` approved/acknowledged, authority burned; T3a2 COMPLETE source `77ef08a`, approved lineage `review-bff8f73a89ebffa5` (target `3677691…`), four deferred WARNINGs | T2; T3b owes its own high-risk gate |
| T3b | Planner slice: advisor + evidence-agent + both verdict permissions | PLANNED NEXT, high risk | T2; T3a1/T3a2 landed with consistent surfaces |
| T3c | PM slice: drop relay/advisor dispatch; GLM seat | PLANNED, high risk | T2; T3a1/T3a2/T3b landed with consistent surfaces |
| T3d | Fallbacks and remaining seats; R3 replacement selection | PLANNED, high risk | T2; T3a1/T3a2-T3c; M3 hang proof and session checks before any `minimax-m3.1-flash` promotion |
| T4 | Verifier checks + digest re-pin | PLANNED | ALL T3a1/T3a2/T3b-T3d slices landed |
| T5 | Mirror and owner restart | PLANNED | T4 |
| T6 | Behavioral probes and trial metrics | PLANNED | T5; owner restart |

## Open choices and standing gates
- Genuine open choices: (i) the R3 reliability replacement in T3d; (ii) M3 hang verification before
  any `minimax-m3.1-flash` promotion. Prerequisites (host tools built/tested, sessions, seat
  independence) remain prerequisites, not owner decisions, and are NOT completed by T2.
- Resolved: (a) item 8; (b) plan-write ask-gated; (c) GLM/`qwen3.8-flash` collision gone; (d) model
  IDs; (f) actor slicing. Standing FAIL CLOSED: `minimax-m3` excluded from every native seat (e).

## Commit and assessment evidence
- Historical: v2 planning source `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md`;
  Q89 phase 1 source `473c9cd`, metadata `22132ad`, inert, tools not live.
- Historical T1: source `114366b`; metadata `dfbeb29`; receipt 206 lines / 25,263 bytes /
  generated-binary []; final assessment medium/`under_budget`; SOURCE 6 cumulative paths / 563
  lines (slice, not this unit).
- Historical T2 (`q90-t2-readiness-u1`): implementation `115fbdd`; targeted recheck F1-F5 ACCEPTED;
  IMPLEMENTATION assessment medium/`under_budget`, 6 cumulative paths / 671 lines, `consumed=false`,
  `review_due=false`; metadata result not claimed.
- Prior pending medium slice (`22132ad`..`2f196b6`) CLOSED by explicit owner decision 2026-10-23;
  boundary advanced to `2f196b6` BEFORE T3a1 source. That closure is not native review of the prior
  slice. Current native-reviewed source boundary is `77ef08af7c376386b24a62e26efc6809b9753bdf`
  (T3a2 lineage `review-bff8f73a89ebffa5` approved); the metadata slice `b89f5a0..2173738` remains
  an owner decision closure, not native review.
- Metadata evidence convention (not workflow policy): self-referential SHA = "commit SHA recorded
  in the PM envelope".

## Log
- Historical writers: initial `ses_e96403ac5ffecd6SwEe5qMfxM2` (frozen result
  `5b035b6bf790e732fbd644f377073b65936a37c4`, installed); correction
  `ses_e9635ed7affeJUhfScAR23O6zs`; T2 initial dispatch `ses_e96143036ffeG9d4jb9Xh3I9WB`
  APPLIED, frozen result `c09ab9b30aac08418dc46f2423537ca23208f641`, 321 authored lines / 39,048
  bytes. Previous units, not this one.
- T3a1 evidence (PM-observed): source writer `ses_e9572b051ffexBxZRVrDekeEtA`; pre advisors
  security `ses_e957e891bffeVQZBnoMD7HKtyq` (Sol) and integration
  `ses_e957e890effeymwKzrfR3yBr7m` (Kimi); independent verifier `ses_e9562bcafffeOQNeIGCxxCnel4`
  (Sol) executed 77 tests plus Bun controls and prompt/digest checks; post advisors security
  `ses_e9562bccdffeexMrjlOz20JrPa` and integration `ses_e9562bcc4ffeZ3GFFnyZBf71BD` before source
  commit. Source correction rounds 0. First-pass static `aft_inspect` PARTIAL, seven diagnostics at
  unchanged Python sites (pre-existing, inferred); no static-clean claim. Full verifier, runtime
  load, live consumer and tool enforcement are host-only NOT run; no deploy. Pre/post advice record
  remains pre-only; this tracker records the post-code outcome.
- Independent verifier F1 tools-map sweep blocker classification was retracted; optional hardening
  only. Separate F2 inaccurate verifier comment remained low/non-blocking, not fixed here.
- T3a1 metadata unit `q90-t3a1-orchestrator-tools-u1`: actual dispatch `ses_e951edc16ffegYNPz4Zr0cZWBz`;
  metadata correction rounds 1 (source rounds 0); sandbox `/work`, synthetic branch `work`, baseline HEAD `b5a81a6` (parent `b89f5a0`), not the host branch.
- T3a2 metadata `q90-t3a2-review-dispatch-u1`: initial writer Task `ses_e93984803ffeKLXteQ7e5axmqj`,
  result `d50cd7b2e17f1114a0f3e5e7904981c537df5d35`; metadata correction round 1/1 (this Task's
  session recorded in the PM envelope); source normal `correction_rounds_used=1`, owner overrides
  retained separately. See the T3a2 section.

## Next step
T3b is PLANNED NEXT, high risk; T3c/T3d and T4-T6 gates unchanged. Q90 remains IN PROGRESS.
