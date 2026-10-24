# Multi-agent v2 workflow config — Q90 queue revision
Task `q90-multi-agent-v2-queue`; units `q90-queue-revision-u1` (initial),
`q90-decisions-correction-u1` (correction), `q90-t2-readiness-u1` (T2 closure) and T3a1 metadata
closure `q90-t3a1-orchestrator-tools-u1`. Header history: those earlier units were class
documentation; each later unit records its own class below (the T3.0 plan and this correction are
`global-tooling-change`, canonical name "global tooling change", with the simple-docs exemption
recorded separately). Route `workflow-odd-secure` delegated cloud `odd-apply`.
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
- Record decisions (b), (d), (e) and (f) and the current T3.0 -> T3b -> T3c -> T3d -> T4 -> T5
  -> T6 dependency order (the earlier T3a-d order is historical).
- Update contradictory OPEN approval and M3 seat language; label earlier evidence historical.
- No `WORKFLOW.md`, `PLAN.md`, spec, config, guard, skill, prompt, test, handoff or Q89 edit.

## Constraints
- Handover order: host tools built/tested first for actor slices that need them; owner decisions;
  then T3.0 model/role, then actor slices -> verifier/digest -> mirror/restart -> behavioral
  probes/trial metrics. The earlier blanket "host tools first, then actor slices" is
  HISTORICAL/SUPERSEDED for the T3.0 model/role work only: the 2026-10-23/24 owner direction puts
  T3.0 ahead of T3b with no `agent-sandbox-integration` dependency; host-tool gates remain for
  T3a1, T3a2, T3b and T3c slices that need a tool.
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
    SUPERSEDED 2026-10-23/24 for future planning: the owner model direction selects
    `minimax-m3.1-flash` for reliability `xhigh` and advisor `high` seats; the M3 exclusion and the
    absence of session/hang clearance remain historical facts. The T3d replacement-selection
    sentence and "no seat chosen" are retained as history only, not current direction.
(f) RESOLVED — actor slices: T3a1/T3a2 orchestrator (plan/test tools, then review dispatch); T3b
    Planner (advisor + evidence-agent + verdict permissions); T3c PM (drop relay/advisor dispatch;
    GLM seat); T3d fallbacks/remaining seats. EACH actor commit changes config task permissions,
    guard `ROUTE_STAGES`/helper lists, route skills and its own `WORKFLOW.md` lines together; no size
    exception and no intermediate guard-denies/skill-allows state — any inconsistent slice STOPS AND ASKS.
    SUPERSEDED for sequencing only by the 2026-10-23 owner direction: T3.0 model/role work now
    precedes T3b; T3c becomes permission-only and T3d residual, with the atomic rule unchanged.

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

## T3.0 model and role assignment (owner direction, 2026-10-23/24)

Planning unit `q90-t30-model-plan-u1`, class `global-tooling-change` ("global tooling change"),
route `workflow-odd-secure`, delegated cloud writer `odd-apply`; the simple-docs exemption covers
this documentation-only deliverable and is recorded separately from the task class. This section
is the complete SOURCE-table plan required before T3b; it changes no config, test, verifier,
skill, prompt, agent definition or deploy. Q90 remains IN PROGRESS.

### Basis and boundary

- **Owner ruling, verbatim:** "Planning basis: canonical `global-config/`; the deployed file is
  stale because T3a1/T3a2 are not deployed. The implementation unit must re-read the deployed
  file after the mirror and record any source-vs-live difference; it must not edit the live file
  directly." Source-to-mirror remains authority.
- **Owner direction:** T3.0 model assignments and role designation come FIRST, before T3b, with
  no `agent-sandbox-integration` dependency. Former `minimax-m3` seats become
  `opencode-go/minimax-m3.1-flash`: reliability xhigh; advisors high. This supersedes the prior
  no-seat-selected/open R3 planning text, NOT historical review evidence and NOT a runtime hang
  clearance.
- **Availability evidence:** Go IDs are owner-reported; Sol, Luna and
  `google/gemini-flash-latest` are orchestrator-confirmed. `minimax-m3.1-flash` hang, session
  resume and Go allowance are NOT independently observed; no clearance claim is made. They remain
  future acceptance gates and do not block this plan.
- **Source/boundary:** canonical `global-config/opencode.json`; current native-reviewed source
  boundary `77ef08af7c376386b24a62e26efc6809b9753bdf`. PM-observed host branch HEAD
  `36d461fdb922f23ebc2aedad6a8a7b961c5fa655` on `chore/multi-agent-v2-phase1`; the initial sandbox
  was a synthetic `work`/`baseline` at `fea922f` (earlier snapshot `caa0043`; both are baseline
  commits whose parent is `36d461f`); this correction runs at `2318ed4` (parent `36d461f`) with the
  applied initial edits in its baseline tree; `77ef08a` is an observed ancestor, not re-read from
  the host ref.
- **Historical labels:** T2 (e) "no seat chosen", the T3d "R3 replacement selection" wording and
  the "T3b is PLANNED NEXT" line are HISTORICAL/SUPERSEDED for future planning by the owner
  direction above. Historical findings, review evidence and the fail-closed M3 exclusion up to
  that decision are unchanged.
- **Prefix key:** `Go`=`opencode-go/`, `O`=`openai/`, `G`=`google/`, `K`=`kinver/`,
  `D`=`deepseek/`, `R`=`openrouter/`; `DS4.1F`=`deepseek-v4.1-flash`,
  `GLMF`=`glm-5.3-flash`. `oc:` = `global-config/opencode.json` model/variant line; `h:` =
  handover; `fb:` = `rate-limit-fallback.json`; `sys:` = `systematic.jsonc`. `absent` means no
  `variant` key; `""` is an explicit empty variant. Absent is not default.

### Current source vs target (complete)

| Seat | Current model · variant | Target model · variant/thinking | Authority |
|---|---|---|---|
| `gentle-orchestrator` | Go DS4.1F · `default` `oc:466/625` | Go DS4.1F · `high` | h:73 |
| `explore` | Go DS4.1F · `medium` `oc:32/33` | Go DS4.1F · non-thinking or lowest supported; explicit `low` if disable is unavailable | h:74 |
| `gentle-ai-explore` | Go DS4.1F · `medium` `oc:270/294` | same explorer policy | h:74 |
| `general` (Tiny) | O `gpt-6-luna` · `high` `oc:243/244` | O `gpt-6-luna` · `medium`, never above `high` | h:78 |
| `vision` | O `gpt-6-luna` · `""` `oc:1082/1125` | UNCHANGED; handover silent, no invented binding | — |
| `gentle-ai-worker` | Go DS4.1F@worker · `default` `oc:369/392` | Go DS4.1F@worker · `high`; preserve the `@worker` alias | h:77 |
| `gentle-ai-worker-local` | K `professional` · `""` `oc:418/441` | UNCHANGED owner opt-in; Qwen-family independence hazard recorded | h:77 note |
| `odd-apply` | Go DS4.1F@worker · `default` `oc:2354/2355` | Go DS4.1F@worker · `high`; preserve the alias | h:77 |
| `frontend-apply` | Go DS4.1F@worker · `default` `oc:60/107` | Go DS4.1F@worker · `high` | h:77 |
| `frontend-apply-local` | K `professional` · `""` `oc:113/160` | UNCHANGED owner opt-in | h:77 note |
| `frontend-dev` | Go GLMF · `high` `oc:166/215` | UNCHANGED design coordinator: no sandbox mutation, not reclassified as a coder | `oc:166-215` |
| `frontend-dev-premium` | O `gpt-6.1-sol` · `high` `oc:1131/1181` | UNCHANGED O `gpt-6.1-sol` · `high`; READ-ONLY DESIGN coordinator, not a coder; `edit`/`write` and sandbox mutators/lifecycle denied `oc:1140-1154` | `oc:1131-1181` |
| `gentle-ai-verify` | O `gpt-6.1-sol` · `high` `oc:320/343` | UNCHANGED independent verifier, not a review seat | `oc:320/343` |
| `pm-odd` | O `gpt-6.1-sol` · `high` `oc:2069/2070` | Go GLMF · `high`; fallback Go `qwen3.8-flash` `high` | h:76; TODO decision 3 |
| `pm-systematic` | O `gpt-6.1-sol` · `high` `oc:2207/2208` | same as `pm-odd` | h:76 |
| `jd-judge-a` | Go GLMF · `high` `oc:678/722` | Go `qwen3.8-max` · `high` | h:98 |
| `jd-judge-b` | Go `qwen3.7-plus` · `high` `oc:728/752` | Go `glm-5.3` · `max` (GLM has low/high/max, no medium) | h:99 |
| `jd-fix-agent` | O Sol · `absent` `oc:631/-` | O `gpt-6-luna` · `high`; Sol `high` only as an explicit consequential profile | h:100 |
| `review-risk` | Go `qwen3.7-plus` · `high` `oc:981/1026` | Go `qwen3.8-flash` · `high` | h:84 |
| `review-resilience` | Go GLMF · `high` `oc:930/975` | Go GLMF · `high` | h:85 |
| `review-reliability` | Go `kimi-k2.7-code` · `absent` `oc:880/-` | Go `minimax-m3.1-flash` · `xhigh`, output ≥ 32768 | h:86, :127-130 |
| `review-readability` | Go `muse-spark-1.3-contributor` · `high` `oc:778/823` | Go `kimi-k2.7-code` · forced thinking; omit numeric variant if unsupported | h:87 |
| `review-validator` | Go `minimax-m3` · `absent` `oc:1032/-` | Go `claude-haiku-5-5` · `high` | h:88 |
| `review-refuter` | Go `grok-4.7` · `high` `oc:829/853` | Go `mimo-v2.6-flash` · default thinking, output ≥ 32768 | h:89 |
| `asi-review-risk` | Go `qwen3.7-plus` · `high` `oc:1187/1188` | mirror `review-risk` exactly | h:91-92 |
| `asi-review-resilience` | Go GLMF · `high` `oc:1228/1263` | mirror `review-resilience` | h:91-92 |
| `asi-review-readability` | Go `muse-spark-1.3-contributor` · `high` `oc:1269/1304` | mirror `review-readability` | h:91-92 |
| `asi-review-reliability` | Go `kimi-k2.7-code` · `absent` `oc:1310/-` | mirror `review-reliability` | h:91-92 |
| `asi-review-validator` | Go `minimax-m3` · `absent` `oc:1391/-` | mirror `review-validator` | h:91-92 |
| `asi-review-refuter` | Go `grok-4.7` · `high` `oc:1350/1351` | mirror `review-refuter` | h:91-92 |
| `advisor-design-pre` | O Sol · `absent` `oc:1454/-` | Go `qwen3.8-flash` · `medium`; mapped to Architecture pre | h:111 |
| `advisor-design-post` | Go `qwen3.7-plus` · `absent` `oc:1704/-` | Go `qwen3.8-flash` · `medium`; mapped to UX/accessibility post | h:117 |
| `advisor-maintainability-pre` | Go `mimo-v2.6-flash` · `absent` `oc:1654/-` | Go `minimax-m3.1-flash` · `high`; Dependencies/config pre | h:116 |
| `advisor-maintainability-post` | Go DS4.1F · `medium` `oc:1904/1926` | Go `kimi-k2.7-code` · forced; Dependencies/config post; migrate off DS to clear the collision | h:116 |
| `advisor-testing-pre` | Go `minimax-m3` · `absent` `oc:1604/-` | Go GLMF · `high` (not m3.1; prior researcher row corrected) | h:107 |
| `advisor-testing-post` | Go `kimi-k2.7-code` · `absent` `oc:1804/-` | Go `qwen3.8-flash` · `medium` | h:107 |
| `advisor-security-pre` | O Sol · `absent` `oc:1504/-` | Go GLMF · `high` | h:109 |
| `advisor-security-post` | Go `qwen3.7-plus` · `absent` `oc:1854/-` | Go `mimo-v2.6-flash` · default (not m3.1) | h:109 |
| `advisor-integration-pre` | Go `kimi-k2.7-code` · `absent` `oc:1554/-` | Go `minimax-m3.1-flash` · `high` | h:110 |
| `advisor-integration-post` | Go `kimi-k2.7-code` · `absent` `oc:1754/-` | Go `qwen3.8-flash` · `medium` | h:110 |
| `advisor-gemini-pre` | G `gemini-4-argon` · `absent` `oc:1941/-` | UNCHANGED cross-cutting escalation, default | h:124-125, :151-156 |
| `advisor-gemini-post` | G `gemini-4-argon` · `absent` `oc:1983/-` | UNCHANGED cross-cutting escalation, default | h:124-125, :151-156 |
| `advisor-gemini-evidence` | G `gemini-3.8-flash` · `absent` `oc:2038/-` | G `gemini-flash-latest` · `default`; omit variant if absent | h:125, :154-155 |

`systematic.jsonc` core writer seats — CURRENT vs TARGET (authority target h:77; exact model
identity preserved):

| Seat | Current model · variant | Target model · variant | Authority |
|---|---|---|---|
| `systematic-implementer` | Go DS4.1F · `xhigh` `sys:121-122` | same model Go DS4.1F · `high` | h:77 |
| `bug-reproduction-validator` | Go DS4.1F · `absent` `sys:133` | same model Go DS4.1F · `high` | h:77 |
| `pr-comment-resolver` | Go DS4.1F · `default` `sys:142` | same model Go DS4.1F · `high` | h:77 |

These three join the core-seat slice (T3.0.2) and its exact readback checks (consumer re-read of
model and effective variant for the plain Systematic names). The h:77 profile names
`deepseek-v4.1-flash` worker `high` but does not explicitly name the `@worker` alias or any
Systematic agent ID; the three current Systematic variant fields differ as the rows show
(`xhigh`, absent and `default`). Applying the worker-high target to these explicit code-writing
plugin seats is therefore a clearly SOURCED PROPOSAL, not unchanged conformance: owner
confirmation of the plugin-profile application is required if it is retained. `design-iterator` Go GLMF
`absent` `sys:184` is a real mutator; GLM collides with target resilience and its fallback reaches
mimo, so the recommendation is Go DS4.1F `high` (OWNER DECISION REQUIRED). Research seats
`sys:150-157` remain unchanged nonwriters because the handover is silent:
`spec-flow-analyzer`/`repo-research-analyst` `default`,
`git-history-analyzer`/`best-practices-researcher`/`framework-docs-researcher`/
`issue-intelligence-analyst` `medium`, `learnings-researcher` `low`, `slack-researcher` O Luna
`low`; no research seat equals a target review/post seat. No SDD agent is added.

**Planned, not present:** `Planner` O Sol `high` (xhigh for Gate 1 on multistep/high-risk) has no
definition or permission in this unit. The eleven new advisor names have no definitions, prompts,
dispatch grants, memory grants, `noFallbackAgents` entries or verifier tests yet. Optional
algorithm/repo-level DS `v4-pro` `high` requires host resolution and an owner profile decision;
it is not an automatic switch.

### 12-lens mapping (recommendation; owner decision where marked)

| Lens | Pre | Post |
|---|---|---|
| Scope & requirements | NEW `advisor-scope-pre` · Go `qwen3.8-flash` medium | — |
| Testing | `advisor-testing-pre` · Go GLMF high | `advisor-testing-post` · Go `qwen3.8-flash` medium |
| Bug hunt | — | NEW `advisor-bug-hunt-post` · Go GLMF high; escalation Go `glm-5.3` max |
| Security | `advisor-security-pre` · Go GLMF high | `advisor-security-post` · Go `mimo-v2.6-flash` default |
| Integration | `advisor-integration-pre` · Go `minimax-m3.1-flash` high | `advisor-integration-post` · Go `qwen3.8-flash` medium |
| Architecture | `advisor-design-pre` retained · Go `qwen3.8-flash` medium | —; escalation Go `qwen3.8-max` high |
| Data & migration | NEW `advisor-data-pre` · Go `qwen3.8-flash` medium | NEW `advisor-data-post` · Go GLMF high |
| Performance | NEW `advisor-performance-pre` · Go `qwen3.8-flash` medium | NEW `advisor-performance-post` · Go `minimax-m3.1-flash` high |
| Concurrency | NEW `advisor-concurrency-pre` · Go `qwen3.8-flash` medium | NEW `advisor-concurrency-post` · Go GLMF high |
| Resilience | NEW `advisor-resilience-pre` · Go `minimax-m3.1-flash` high | NEW `advisor-resilience-post` · Go GLMF high |
| Dependencies / config | `advisor-maintainability-pre` retained · Go `minimax-m3.1-flash` high | `advisor-maintainability-post` retained · Go `ling-3.1-flash` default (variant absent) |
| UX / accessibility | NEW `advisor-ux-pre` · Go `kimi-k2.7-code` forced | `advisor-design-post` retained · Go `qwen3.8-flash` medium |

Owner correction 2026-10-24: the Dependencies/config post target is
`opencode-go/ling-3.1-flash` default with `variant` absent (not Kimi). Unit
`q90-t30-advisor-drift-u1` applies the six normal WORKFLOW rows and the validator
migration; no other mapping changes.

No `arch-post`, `scope-post` or `bug-pre` is invented; scope and architecture are pre-only and bug
hunt is post-only as the handover states. The retained design names map to Architecture pre and
UX post to preserve design integrity across both, with a new UX pre partner; this rename/scope
mapping is an OWNER DECISION REQUIRED before source implementation, not settled policy. The same
applies to expanding the retained maintainability pair to Dependencies/config while keeping its
abstraction/coupling/intent remit; no current lens is dropped. No current advisor is silently
retired: five existing normal pairs are retained and remapped, and the Gemini pair remains a
cross-cutting escalation. The per-lens pre/post model-diversity rule holds; Architecture pre and
UX post both using `qwen3.8-flash` is not a coupled pair because they are different lenses.

### Variants and thinking levels (exact mechanics)

`h:62` "no variants today" is stale. The source catalog has `variants` maps only for
`ling-3.1-flash` `oc:3023`, `muse-spark-1.3` `oc:3066`, `gemini-3.8-flash` `oc:3146` and
`deepseek-v4.1-flash@worker` `oc:3296`. `minimax-m3.1-flash` `oc:2973-3005` declares
`reasoning: true` and output 512000 but NO variants. An agent `variant` string selects a declared
variant; `@worker` is part of the model ID, not a thinking level. Add explicit per-model maps
only where the model/SDK supports them, using the V1 shape
`provider.<provider>.models.<id>.variants.<name>` with `reasoningEffort` for the existing
openai-compatible models (Anthropic thinking budgets use the provider's own option shape). V1
also permits model-local overrides under the singular `provider` map for O/G models; do not use
global root variants or V2 plural `providers` arrays. GLM has low/high/max only; Kimi is forced;
Mimo is default. Do not fabricate a numeric Kimi/Mimo effort, and do not claim `low` equals "no
thinking". The current verifier compares exact configured/runtime variants at `verify-workflow.sh:2396-2399`
(GGA), `:2216-2219` (Systematic) and requires an explicit orchestrator variant at `:3446-3448`;
implementation must accept a configured supported effective variant, distinguish absent from empty,
and fail unknown variants with positive/negative controls. Exact max-output is an SDK/runtime host
check; catalog output ≥ 32768 alone does not prove an effective request floor.

### Fixes, fallback graph and collisions (all planned in T3.0)

1. **Fix 1, writer fallback reaches review/post seats.** Actual keys are
   `fb:193` (`opencode-go/deepseek-v4.1-flash`) and `fb:225` (`...@worker`), with mimo at
   `fb:206` and `fb:238`. GLM `fb:257`, Kimi `fb:318`, qwen3.7 `fb:359` and Muse `fb:622` chains
   also include mimo. `deepseek-v4-flash` exists as a catalog model at `oc:3253` but has NO
   `fallbackModels` key in the fully read file; do not edit a nonexistent entry. The DeepSeek
   writer base and `@worker` fallback cleanup is DeepSeek-only, using the exact full IDs
   `deepseek/deepseek-flash` then `openrouter/deepseek/deepseek-v4.1-flash`; assert no mimo is
   reachable from the base, the `@worker` alias, or a legacy identity for those chains.
   Tiny/`general` and `jd-fix-agent` are the independent owner exception (fix 6) and may keep
   `opencode-go/gpt-6-luna` plus DeepSeek fallbacks; do not overwrite that exception as a blanket
   writer policy. Every other effective writer closure is inspected and must be collision-free,
   not rewritten by assumption. Full registry is the 13
   names at `tests/test_model_independence.py:106-122`; effective mutators are
   general, systematic-implementer, frontend-apply, frontend-apply-local, jd-fix-agent,
   pr-comment-resolver, bug-reproduction-validator, design-iterator, gentle-ai-worker,
   gentle-ai-worker-local and odd-apply. `frontend-dev` and `frontend-dev-premium` are design
   leads with sandbox mutation denied (`oc:166-215`, `oc:1131-1181`), so registry membership does
   not make them effective mutators. The closure must traverse agent overrides, exact model-scope,
   provider-scope and transitive fallbacks, with capability filters, stall retries and cycle
   detection. `providerFallbacks.opencode-go` `fb:729` is already D/R-safe; OpenAI, Kinver and
   Google provider chains include Gemini/Luna and must be checked for post-code collisions.
   `design-iterator`'s GLM primary/fallback collision and the legacy DS
   `advisor-maintainability-post` must migrate in the same prerequisite slice; the global guard
   must not be activated while a known interim collision exists.
2. **Fix 2, `qwen3.8-max` scope.** Only `jd-judge-a` and the named Architecture escalation;
   never an ordinary lens or default seat. Recommend an explicit isolated named escalation target
   or a resolved model-override contract; describe the separate-agent versus rename tradeoff and
   do not execute that owner decision here. No ordinary advisor runs on qwen-max.
3. **Fix 3, M3 substitution.** Owner direction replaces every former `minimax-m3` native/advisor
   seat with `minimax-m3.1-flash` (reliability xhigh, advisors high). Fix 3 is resolved by owner
   substitution but its hang is unverified; retain session/hang/Go-allowance acceptance gates.
   Fix 4 (missing IDs) is CLOSED by owner/model existence, not by a new probe claim.
4. **Fix 5, Gemini evidence.** Change `advisor-gemini-evidence` from `G gemini-3.8-flash` `oc:2038`
   to `G gemini-flash-latest` and change `verify-workflow.sh:3344` plus
   `tests/test_gemini_advisor_route.py:37` in the same commit. Argon pre/post stay the
   cross-cutting escalation and are not silently retired.
5. **Fix 6, Luna provider.** `general`/Tiny and `jd-fix-agent` use explicit O `gpt-6-luna`; keep
   their fallback independence (Go Luna and DS are acceptable only after confirming no review
   collision). Tiny never exceeds high. Do not treat a different provider as independent by
   itself.
6. **No-fallback and judge semantics.** Review 12 stay excluded; both judges and all advisors are
   in `noFallbackAgents` `fb:893`, yet `verify-workflow.sh:2755-2759` still compares the judges'
   first fallbacks. SETTLED RECOMMENDATION: KEEP both judges fixed and no-fallback, and branch the
   verifier assertions on the effective disabled fallback with positive and negative controls;
   never count an inactive chain as a runtime chain. Adding real judge fallbacks and removing the
   judges from `noFallbackAgents` is a CONTRARY POLICY that needs separate owner authorization; it
   is not an equally pending default option.
7. **PM same-provider fallback.** `verify-workflow.sh:2673` filters same-provider targets for a
   provider-failure check and `:2678` requires a non-empty result. PM is Go GLM with a Go
   qwen3.8-flash fallback, so a provider-wide Go outage leaves no target. EXPLICIT RECOMMENDATION:
   preserve qwen for same-provider model-scope failures and fail closed on provider outage; a
   cross-provider option needs separate owner approval. Tests must state model-failure versus
   provider-failure semantics. Do not silently broaden the fallback or ignore the conflict.

### Future atomic slices (plan only; each < 400 changed lines / 100 KiB)

Every line/byte figure below is an AUTHORED ESTIMATE, NOT a measured receipt; the measured receipt
is a prerequisite before each slice's commit. Dependency order is behavior-first: variants -> core
seats -> PM -> judges -> fallback writer cleanup -> fallback/legacy closure -> review pairs ->
existing advisor mappings -> new lens units -> escalations/Gemini -> integration audit. Each slice
carries its config change, the matching verifier edits, digest re-pin, and exact targeted
tests/fixtures in the SAME commit; no slice is config-only, and rollback reverts the whole
behavior. No slice may land a global checker that deliberately accepts a known unsafe intermediate
candidate, and no slice may use a silent size exception: a measured receipt over the cap splits
the behavior before commit. The final global completeness sweep is T3.0.9, only after legacy
collisions are gone. Prerequisite for the first high-risk T3.0 source unit: close the pending
medium metadata slice from `77ef08a` by native review or an explicit owner boundary; never assume
`under_budget` closes it.

| Unit | Scope | Estimate (ESTIMATES, NOT MEASURED: authored lines / patch bytes) | Prerequisites | Split/rollback |
|---|---|---|---|---|
| T3.0.1 `q90-t30-variants-u1` | Add the target model variant maps, effective-variant verifier semantics and absent-versus-empty fixtures; no seat reassignment yet | 160-220 / 22,000-30,000 | `77ef08a` metadata boundary closed | Revert whole unit; no seat depends on it |
| T3.0.2 `q90-t30-core-seats-u1` | Orchestrator high; explorer nonthinking/low; cloud workers high with alias; Tiny Luna medium; jd-fix Luna high; Systematic implementer/validator/resolver high; check: consumer re-read of exact model and variant for both families plus the plain Systematic seats | 170-250 / 20,000-32,000 | T3.0.1; set the orchestrator to `high` and activate the strict validator for all confirmed models; the validator is staged and untested against live seats until this step (`supportedVariantFailure`, staged by T3.0.1) | Revert; review seats untouched |
| T3.0.3a `q90-t30-pm-u1` | PM GLM high + qwen fallback; PM model-failure versus provider-failure tests; check: PM seat equality and stated outage semantics | 200-280 / 25,000-38,000 | T3.0.2 | Revert PM; judges untouched |
| T3.0.3b `q90-t30-judges-u1` | Judge A `qwen3.8-max` high, judge B GLM max; noFallback/judge-fallback contract and verifier branch controls; check: judge seat equality and effective no-fallback evidence | 180-260 / 22,000-35,000 | T3.0.3a | Revert judges; PM untouched |
| T3.0.4a `q90-t30-fallback-writer-u1` | Fix 1 DeepSeek writer base + `@worker` cleanup, design-iterator primary, maintainability-post migration, legacy-identity assertion; check: no DeepSeek writer closure reaches a review/post seat and no interim writer collision | 260-360 / 32,000-48,000 | T3.0.3b | Revert writer kernel; guard stays disabled |
| T3.0.4b `q90-t30-fallback-closure-u1` | Provider-scope and legacy fallback closure, scoped collision controls over every other effective writer; explicit pre-guard collision-free proof; check: remaining effective writers are collision-free without a blanket policy overwrite | 230-330 / 30,000-46,000 | T3.0.4a | Revert closure; global completeness waits for T3.0.9 |
| T3.0.5a `q90-t30-review-risk-resilience-u1` | Native + `asi` risk and resilience parity; check: two-lens model/variant parity and independence | 150-230 / 20,000-32,000 | T3.0.4b | Revert pair; other lenses untouched |
| T3.0.5b `q90-t30-review-readability-reliability-u1` | Native + `asi` readability/reliability, Kimi forced, M3.1 xhigh and output floor; check: forced/default thinking and output-floor evidence | 220-320 / 28,000-44,000 | T3.0.5a | Revert pair; if M3.1 acceptance fails, stop and ask |
| T3.0.5c `q90-t30-review-refuter-validator-u1` | Native + `asi` refuter/validator, Mimo default, Haiku high; check: remaining review-seat parity and independence | 180-260 / 24,000-36,000 | T3.0.5b | Revert pair |
| T3.0.6a `q90-t30-advisor-design-map-u1` | Retained design pair remap to Architecture pre / UX post, prompts and caller allowlists; check: design-to-architecture/UX mapping and dispatch | 250-350 / 32,000-48,000 | T3.0.5c | Revert lens pair |
| T3.0.6b `q90-t30-advisor-deps-map-u1` | Retained maintainability pair remap to Dependencies/config, M3.1 high pre / Kimi forced post; check: dependency/config coverage and collision clearance | 230-330 / 30,000-46,000 | T3.0.6a | Revert pair |
| T3.0.6c `q90-t30-advisor-testing-map-u1` | Existing testing pair; check: lens target and caller scope | 200-280 / 25,000-40,000 | T3.0.6b | Revert that pair |
| T3.0.6d `q90-t30-advisor-security-map-u1` | Existing security pair; check: lens target and caller scope | 200-280 / 25,000-40,000 | T3.0.6c | Revert that pair |
| T3.0.6e `q90-t30-advisor-integration-map-u1` | Existing integration pair; check: lens target and caller scope | 200-280 / 25,000-40,000 | T3.0.6d | Revert that pair |
| T3.0.7a `q90-t30-advisor-scope-ux-u1` | NEW scope pre + UX pre/post pair: definitions, prompts, strict caller allowlists, guard route-stage/skill dispatch, memory denies, `noFallbackAgents`, verifier tests; check: one lens pair and no Planner authority preinstalled | 280-380 / 36,000-54,000 | T3.0.6e | Revert pair; current actor owns advice until T3b |
| T3.0.7b `q90-t30-advisor-data-u1` | NEW data pair, same atomic surfaces as 7a; check: data lens pair and dispatch | 300-380 / 38,000-56,000 | T3.0.7a | Revert pair; current actor owns advice until T3b |
| T3.0.7c `q90-t30-advisor-performance-u1` | NEW performance pair, same atomic surfaces as 7a; check: performance lens pair and dispatch | 300-380 / 38,000-56,000 | T3.0.7b | Revert pair; current actor owns advice until T3b |
| T3.0.7d `q90-t30-advisor-concurrency-u1` | NEW concurrency pair, same atomic surfaces as 7a; check: concurrency lens pair and dispatch | 300-380 / 38,000-56,000 | T3.0.7c | Revert pair; current actor owns advice until T3b |
| T3.0.7e `q90-t30-advisor-resilience-u1` | NEW resilience pair, same atomic surfaces as 7a; check: resilience lens pair and dispatch | 300-380 / 38,000-56,000 | T3.0.7d | Revert pair; current actor owns advice until T3b |
| T3.0.7f `q90-t30-advisor-bug-hunt-u1` | NEW bug-hunt post pair, same atomic surfaces as 7a; check: bug-hunt lens pair and dispatch | 200-280 / 25,000-40,000 | T3.0.7e | Revert pair; current actor owns advice until T3b |
| T3.0.8 `q90-t30-escalations-u1` | Named Architecture qwen-max and bug-hunt GLM-max escalation targets; Gemini evidence change with verifier+tests; check: escalations are isolated and rare and the evidence model matches | 300-390 / 40,000-60,000 | T3.0.7f | Revert; ordinary lenses unaffected |
| T3.0.9 `q90-t30-integration-audit-u1` | Full source matrix, effective-family sweep, caller/route/skill/memory consistency, digest audit; check: T3.0 completeness before T3b | 180-260 / 22,000-36,000 | T3.0.8 | Final T3.0 gate; T4 remains the later whole-workflow audit |

T3.0.4a is the safe scoped writer/legacy behavior; T3.0.4b is the remaining closure and collision
proof. Neither enables the global guard, and completeness remains T3.0.9. A new advisor lens-pair
unit (7a-f) normally spans definitions, prompts, permissions, guard/skills, verifier, tests and pin
together; its estimate above is the real expected scope, not an arbitrary small number.

**T3.0.2 activation prerequisite (explicit):** set the orchestrator to `high` and activate the strict validator for all confirmed models; the validator is staged and untested against live seats until this step (`supportedVariantFailure`, staged by T3.0.1). T3.0.1's staged fixture verification is NOT live seat/runtime clearance. The full `opencode-go/deepseek-v4-pro` identity remains an ASSUMPTION (owner-named model plus the plan's Go convention, not a resolved full ID); resolve it before the optional v4-pro profile. No unavailability claim is made.

**Owner PM deferral (2026-10-24):** PM reassignment is deferred until Planner setup is complete; this supersedes the earlier PM-before-T3b ordering. It does not rewrite other task design and does not migrate seats.

### T3.0.1 staged variant validator (source unit)
Unit `q90-t30-variants-u1`; class `global-tooling-change`; route `workflow-odd-secure`; delegated cloud `odd-apply`. Route/trigger: multi-file source unit plus secure preparation; delegated, not inline; mirror UNIMPLEMENTED/not read. Owner boundary: `77ef08a..544a2630` closed by owner DECISION, not native review; boundary `544a2630...`; Q90 IN PROGRESS.
Scope: stage self-contained `supportedVariantFailure(model, variant)` in the verifier JS heredoc, marked for extraction. Full IDs (including `@worker`); explicit target subset, not full catalog. Absent accepted; `""`/unknown/non-string refused by name with model+variant. qwen/kimi/mimo absence only; Mini high/xhigh; Luna every listed name; GLM and `@worker` low/high/max; base DS low/high; DS v4-pro and Haiku high; Gemini absence only, no literal `default`. Not called against live/configured seats; `opencode.json` unchanged; exact GGA/Systematic checks and the explicit orchestrator requirement unchanged.
Activation prerequisite: set the orchestrator to `high` and activate the strict validator for all confirmed models; the validator is staged and untested against live seats until this step (`supportedVariantFailure`). T3.0.1 fixture verification is not live seat/runtime clearance.

### T3.0 Kimi-removal implementation (owner-directed 2026-10-24)

Unit `q90-t30-kimi-removal-u1`; class `global-tooling-change`; route `workflow-odd-secure`; delegated cloud `odd-apply`; multi-file plus secure-preparation trigger. Owner direction supersedes the earlier T3.0 target rows for these seats. Scope: five Kimi primaries and the DeepSeek maintainability-post remapped; readability untouched; replacement exact policies and the inactive Kimi key. Prerequisites: T3.0.1 staged boundary and pre-advice; source tests are not runtime clearance.

Source/owner direction: reliability and `asi-review-reliability` MiniMax `xhigh`; integration-pre MiniMax `high`; integration-post/testing-post Qwen with the `variant` property omitted; maintainability-post Ling with the `variant` property omitted. Future `advisor-ux-pre` is planned MiniMax `high` at T3.0.7a and is NOT created here. Readability stays Muse `high` byte/structurally unchanged.

Fallback (INITIAL detector HISTORICAL; corrected in round 1/1 below): the first detector covered `model`/`small_model` assignments and fallback dictionary keys but not scalar `modelID` target values, so its "no Kimi reference" result was incomplete and its source-target control could be satisfied by the exact-policy key. After the five agent remaps it found no Kimi reference except the inactive exact key, so the key was removed. Three dormant completeness policies were copied from the existing `minimax-m3` shape (non-Go targets; no self/duplicate/cycle); every evaluator seat remains in `excludeAgents`/`noFallbackAgents`, so they are not reachable evaluator fallback. No provider variant map, verifier seat pin, validator migration or general fallback cleanup.

PM-resolved preparation/advice: the source catalog lacks MiniMax variants; the owner explicitly requires `high`/`xhigh`, so actual consumer variant support, model availability and M3.1 hang/session/Go-allowance acceptance remain UNVERIFIED deployment prerequisites. `WORKFLOW.md` and `docs/ADVISOR-HANDOFF.md` retain old model rows, excluded by owner scope and recorded as deferred drift, not executable Kimi usage. No runtime provider-provenance claim.

Advice: security PRE `ses_e91572725ffeRKjqB1DbgBWnpy` (Sol) required seat independence, exact variants, detector controls, exclusion semantics and live UNVERIFIED. Integration PRE `ses_e9157271effeF5LF1fqV9uOzCg` failed with `<400> InternalError.Algo.DataInspectionFailed: Output data may contain inappropriate content.` (`data_inspection_failed`); the owner authorized substitute testing-pre `ses_e91512f4effeMgIo3zeeYjiZ41` (canonical and runtime MiniMax `minimax-m3`, independent of security). No Kimi retry; the substitute's variant/fallback/Ling/docs gates are PM-dispositioned above, not approval. The reliability lens was owner-reported provider-blocked twice on lineage `review-642f4745d7f6d6fe` for `decd167b`, with three lenses captured; this worker did not reproduce that. The owner designates that lineage SUPERSEDED by this candidate, not approved and not closed; no lifecycle mutation. Fresh native review after commit/deploy is external to this unit.

Checks/log (HISTORICAL INITIAL): test-first RED 7 failures (including DeepSeek maintainability and all Kimi refs), then GREEN 10/10 new, 8/8 independence, 23/23 variants, 23/23 review-pipeline, 20/20 Gemini; JSON loads and `git diff --check` clean. Session `ses_e914a9d25ffef4Al8EcRnhKyjx`, synthetic baseline `2acc9c2` (parent `decd167`), sandbox `/work`. Full verifier, consumer/runtime variant support, model availability, hang/session/Go allowance, deploy and native review remain UNVERIFIED. Ordering deviation: this tracker section was authored after the first config edit; recorded, not repaired. Mirror UNIMPLEMENTED/not read. Receipt measured at PM handoff.

### Correction round 1/1 (refines the installed candidate)

Scope: refine the installed uncommitted candidate against `decd167b`; no commit, native review, deploy, restart, push or PR. The six-seat configuration, readability Muse, `systematic.jsonc` (read-only), PM/orchestrator/workers, Tiny, `WORKFLOW.md`, skills, prompts, agent definitions and provider map are unchanged. Correction session/result IDs and the measured receipt belong to the PM handoff envelope.

Finding dispositions:
- V1 ACCEPTED: the initial fallback walk yielded dictionary keys rather than scalar `modelID` values, and `fallbackModel` substring matching was satisfied by a `fallbackModels` key. The detector now traverses global `fallbackModel`, exact `fallbackModels` source keys and targets, `providerFallbacks` targets and `agentFallbackModels` targets; five isolated controls assert exact path, policy identity and value. Source-key detection cannot satisfy the target check.
- V2 ACCEPTED: added read-only `systematic.jsonc` category/agent `model` scanning with a parser mirroring the verifier's string/comment state machine, plus Systematic-profile and `small_model` (tool-model) mutation controls and a catalog-ignored control. The corrected live scan finds zero Kimi executable references; no out-of-scope field was silently deleted or remapped.
- V3 ACCEPTED: isolated controls mutate every required-present high/xhigh seat (wrong value and absent) and each of the three required-absent posts with `null`, `""`, `default` and `medium`, asserting the target seat reason from `variant_shape_failures`. They validate the helper only; no production-runtime variant semantics are claimed.
- V4 ACCEPTED (PM): the live review/advisor check uses one dynamic `review-`/`asi-review-`/`advisor-` inventory, asserts it equals the tracked name set, and the same checker rejects injected `other/deepseek-v5` and an unknown family in review and advisor seats. Systematic reviewer seats are not migrated here; the Systematic read is no-Kimi inventory only. `ling` remains a test-only family marker.
- Post-security advisor `ses_e913c4500ffeqF7MkmWO5wTi0r` reported no blockers, but its A5 comprehensive-target-detector conclusion is DISAGREED by verifier V1 and the PM read; recorded as an interpretation, not approval.
- Post-verifier evidence on the same initial candidate: `ses_e913c44faffeUx5Yfi8UYWMLav` (Sol) executed 84 tests (10+8+23+23+20), 0 skips, 103 Bun controls; `git diff --check` clean; measured 390 lines / 8 paths. Consumer `opencode` execution was denied EACCES, so runtime remains UNVERIFIED and no workaround was attempted.
- PM first-pass `aft_inspect` of all eight paths was PARTIAL (six files without LSP). Pyright `tests/test_model_independence.py:72:58` optional `specialist.group` is unchanged from the anchor (only `ling` was inserted); it is recorded as an inferred pre-existing diagnostic with no clean claim and no unrelated fix.

The independent literal inventory separately saw only the Kimi catalog entry and none in fallback or Systematic; source absence is corroborated, but the regression detector above was not adequate until this correction. Initial RED 7 / GREEN 84 remains HISTORICAL INITIAL. The tracker-order deviation (this section after the first config edit) remains recorded and unrepaired. This correction observed RED before the helper fix (4 errors: missing detector/seat API) and GREEN after (14/14 q90; 88 tests across the five required modules, 0 skips; 103 Bun controls; `git diff --check` clean). Future `advisor-ux-pre` remains planned as full `opencode-go/minimax-m3.1-flash` `high` at T3.0.7a with no definition created here.

Future flow: canonical workflow places source review before deployment; the owner's plan to request fresh native review after this commit/deploy is recorded as owner plan only. No deploy, native review or restart is authorized or performed by this unit; the existing integration/testing-pre and superseded-lineage records stand without mechanism-equivalence claims.

### T3.0 normal-row drift and validator migration (owner-directed 2026-10-24)

Unit `q90-t30-advisor-drift-u1`; class `global-tooling-change`; route `workflow-odd-secure`; delegated cloud `odd-apply`; multi-file plus secure-preparation trigger. Baseline `d14e83f90a4f044e5b42b268fd47eec8c4ee96d8` on `chore/multi-agent-v2-phase1`; the sandbox uses a synthetic work branch and does not switch the host branch. No commit, deploy, restart, push, PR or native review. Route/trigger evidence: authorized single writer, targeted tests; mirror UNIMPLEMENTED/not read.

Owner cost override (explicit deviation, THIS unit only): `WORKFLOW.md`'s high-risk/global-tooling row normally owes an advisor plus an independent verifier. The owner directed ONE writer, targeted tests, NO advisor and NO independent verifier. Reason: owner cost directive; every mapping owner-decided; static config plus targeted tests; PM self-check plus orchestrator readback. This is not a simple-docs classification and not a standing waiver. Source/runtime verification distinctions are retained.

Intent: align the six normal WORKFLOW advisor rows with canonical config (`advisor-integration-pre`/`advisor-testing-pre`/`advisor-maintainability-pre`, plus the three post rows), migrate both validators to `opencode-go/claude-haiku-5-5` `high`, and teach the verifier the `ling`/`claude` families plus the Ling absent-only variant target. Design/security rows, the post-seat variant omission and all other agents, catalogs and fallback policy stay unchanged. Status PENDING-COMMIT; review assessment PENDING.

Findings/checks (INITIAL candidate): RED before source changes: 75 focused tests, 7 failures, 0 skips/errors (4 q90, 1 model-independence, 1 variants, 0 review-pipeline). GREEN after source: the same 75 tests, 0 failures/errors/skips, plus 103 extracted Bun controls. `python3 -m json.tool global-config/opencode.json` parsed (exit 0); `bash -n verify-workflow.sh` exit 0; `git diff --check` clean; verifier sha256 `41100b1b1896d808ca5b49f0db2edf5470db5f402dfe2d0314724a9a80e07b61` equals the updated health-plugin pin (also enforced by `DigestPin`). The changed verifier functions were EXECUTED, not only parsed: `modelFamily` was extracted and run for Claude/Ling/MiniMax identities (Python/verifier parity test), and the marked `supportedVariantFailure` block ran the Ling absence-only target. Static diagnostics: `aft_inspect` was not run because the host AFT workspace is not the sandbox candidate; no clean static claim. The optional `specialist.group` Pyright diagnostic in `tests/test_model_independence.py` remains pre-existing and unfixed.

Limitations: runtime/live consumer resolution, model availability, MiniMax M3.1 hang/session/Go allowance, full verifier execution, plugin load, deploy and native review remain UNVERIFIED and were not attempted. Source assignments are canonical `global-config/` only; the host branch was not switched and nothing was committed. Design/security rows and post-seat variant absence were checked by `git diff`; `docs/ADVISOR-HANDOFF.md` remains deferred drift outside the authorized scope. Mirror UNIMPLEMENTED/not read.

### Planned checks per slice (plan only; none run here)

JSON/JSONC parse and schema; consumer agent re-read exact model/variant for plain and `asi` names;
independence by effective model family including fallback closure, overrides and fixed exclusions;
focused `tests/test_model_independence.py`, `tests/test_gemini_advisor_route.py`,
`tests/test_review_pipeline_permissions.py`, `tests/test_pm_task_allowlists.py` and
`tests/test_tiny_fix_route.py` where relevant; extracted verifier self-tests with negative and
positive controls; `bash -n`; digest compute and pin equality in the same commit; AFT static
first pass with no clean claim when partial. Full verifier, live model resolution, session resume,
hang evidence and effective SDK output options are HOST-ONLY and cannot run in the sandbox; they
run only on the approved host lane after source review, mirror and owner restart. Source changes
remain runtime UNVERIFIED until executed. No source test is run in this planning unit.

### Owner decisions still pending before source

Exact design-pair mapping to Architecture/UX and the new UX pre; maintainability scope expansion;
optional DS v4-pro profile; qwen-max escalation representation; and the local Kinver owner opt-in
with its Qwen-family independence hazard — recommendations only, not settled policy.
SETTLED RECOMMENDATIONS (a contrary policy needs separate owner authorization): keep both judges
fixed/no-fallback and branch the verifier with positive/negative controls; preserve PM qwen for
same-provider model-scope failure and fail closed on provider outage. `frontend-dev-premium` is no
longer an open target: it stays the unchanged read-only Sol design coordinator.

## Work units
| Unit | Scope | Status | Prerequisites |
|---|---|---|---|
| T1 | Queue revision: Q90, Q87 overlay, Q91, router | COMPLETE source `114366b`, metadata `dfbeb29`, medium/`under_budget` | owner authorization 2026-10-23 |
| T2 | Readiness: decisions b/d/e/f, model IDs, M3/hang and seat gates | COMPLETE for decisions/evidence; metadata commit `2f196b6`; owner decision 2026-10-23 closed the retained MEDIUM SLICE (`22132ad`..`2f196b6`), not a native review of it; host-tool, session and independence checks remain future gates | T1; owner decisions 2026-10-23 |
| T3a | Orchestrator slice: T3a1 plan/test tools + ask-gated `host_plan_write`; T3a2 review dispatch | T3a1 COMPLETE source `b89f5a0`, native review `review-1ca5500bc130a1cf` approved/acknowledged, authority burned; T3a2 COMPLETE source `77ef08a`, approved lineage `review-bff8f73a89ebffa5` (target `3677691…`), four deferred WARNINGs | T2; T3.0 and T3b owe their own high-risk gates |
| T3.0 | Model and role assignment: complete source table, variant mechanics, fallback fix graph, native/`asi` review seats, 12-lens advisor mapping, escalations; atomic subunits T3.0.1-T3.0.9 | PLAN COMPLETE; T3.0.1 source STAGED and unactivated (fixture checks only, not live seat/runtime clearance); T3.0.2 next | T2; T3a1/T3a2 landed; owner direction 2026-10-23/24; no `agent-sandbox-integration` dependency; `77ef08a..544a2630` closed by owner DECISION, not native review |
| T3b | Planner slice: advisor + evidence-agent + both verdict permissions | PLANNED, high risk, after T3.0 | T2; T3a1/T3a2/T3.0 landed with consistent surfaces; the existing current actor owns advice until T3b |
| T3c | PM slice: permission-only drop of relay/advisor dispatch, after the T3.0 model migration | PLANNED, high risk | T2; T3.0/T3b landed; no model seat deferred to T3c |
| T3d | Residual fallbacks/routing audit only; no duplicated model or fallback seat work already done in T3.0 | PLANNED, high risk | T2; T3.0-T3c; M3.1 session/hang/Go-allowance acceptance before its promotion goes live |
| T4 | Verifier checks + digest re-pin | PLANNED | ALL T3a1/T3a2/T3b-T3d slices landed |
| T5 | Mirror and owner restart | PLANNED | T4 |
| T6 | Behavioral probes and trial metrics | PLANNED | T5; owner restart |

## Open choices and standing gates
- Genuine open choices: design mapping, maintainability scope, optional v4-pro profile, qwen-max
  escalation shape and local Kinver opt-in. SETTLED RECOMMENDATIONS (a contrary policy needs
  separate owner authorization): judges stay fixed/no-fallback with verifier controls; PM keeps
  qwen for same-provider model-scope failure and fails closed on provider outage.
  `frontend-dev-premium` stays the unchanged read-only Sol design coordinator. M3.1 remains subject
  to the session/hang/Go-allowance acceptance gate. The R3 replacement itself is no longer open:
  owner direction names `minimax-m3.1-flash` (planning), and no clearance is claimed.
- Resolved: (a) item 8; (b) plan-write ask-gated; (c) GLM/`qwen3.8-flash` collision gone; (d) model
  IDs; (f) actor slicing; (g) 2026-10-23/24 model and role direction, with T3.0 before T3b and no
  `agent-sandbox-integration` dependency. Standing FAIL CLOSED until that direction is implemented:
  `minimax-m3` stays excluded from every native seat (e).

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
- T3.0 planning unit `q90-t30-model-plan-u1` (2026-10-24): DOCS-ONLY; allowed paths exactly this
  tracker, `docs/TODO.md` and `ROUTER-LOG.md`; no config/test/verifier/skill/prompt/agent/deploy
  change, no branch switch and no commit. Baseline/ancestry observed in the sandbox; the commit SHA
  for this unit is recorded in the PM envelope. Owner closed `77ef08a..544a2630` by DECISION, not
  native review; the boundary is now `544a2630...`.
- Q90 T3.0.1 `q90-t30-variants-u1` (2026-10-24): source staged, not activated; six intended paths
  (this tracker, advice, ROUTER-LOG, test, verifier, pin only); `opencode.json` unchanged; staged
  `supportedVariantFailure` not called against live seats; T3.0.2 owns activation/live testing; PM
  owns commit/review; exact receipt in the PM envelope; mirror UNIMPLEMENTED/not read.

## Review-size exception
`review-size-exception` — OWNER AUTHORIZED 2026-10-24 for ONE three-path docs commit on
`q90-t30-model-plan-u1`, the paths being this tracker, `docs/TODO.md` and `ROUTER-LOG.md`. The
initial correction's 482 authored lines / 58,658 patch bytes is HISTORICAL PRE-FINAL. The FINAL
measured TOTAL is 522 authored lines / 63,094 patch bytes,
measured from ORIGINAL `36d461fdb922f23ebc2aedad6a8a7b961c5fa655` to the final state of all three
docs; it is not a delta-only figure, and generated/binary paths are `[]`.

Atomicity: this is docs-only, one repeated table shape plus its queue row and log row. The diff
carries no executable behavior, config or test. Splitting would require two path-scoped sandbox
results and two commits for the same tracker; the line count alone does not justify that overhead,
which is why the owner authorized one three-path commit under this exception.

Precedent: `odd/tasks/model-assignments.md:77-85` was PM-read as 521 lines / 36,338 bytes with ten
mechanically repeated advisor definitions. That is a comparable docs-size precedent, not a
measurement of this unit and not a claim that the changes are equivalent.

The owner assesses the native-review input as far below 200 KiB. That is an OWNER ASSESSMENT, not
a measurement here: raw Git patch bytes do not prove serialized-input admission, and native START
remains the final authority on that limit. Mirror is UNIMPLEMENTED/not performed and the body is
not read. Hard ceiling is 102,400 patch bytes: if the final receipt exceeds it, this result stops
frozen-only with no apply and no commit. There is no line-count stop because the owner explicitly
authorized this one-commit review-size exception.

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
- T3.0 planning writer `q90-t30-model-plan-u1` (2026-10-24): HISTORICAL INITIAL. Actual sandbox
  session `ses_e934abfa5ffe4MDVnRdVW444cJ` (identity also present in its sandbox baseline commit
  message); route delegated cloud `odd-apply`, docs exemption, no advisors/verifier/runtime tests.
  Sandbox root `/work`, synthetic branch `work`, baseline `fea922f` whose parent is `36d461f` (an
  earlier snapshot was `caa0043`, same role/parent); ancestry `77ef08a` → `36d461f` observed, host
  ref not re-read. Changed paths exactly this tracker, `docs/TODO.md` and `ROUTER-LOG.md`; initial
  `git diff --check` clean; initial diff 3 files, 355 insertions / 44 deletions (399 authored
  lines), initial patch below the 102,400-byte cap; exact initial receipt returned to the PM.
  Initial structural claims: 43 seat rows and 12 lens rows by reading; the initial writer reported
  `grep -o` finding all eleven new advisor names once; the `docs/TODO.md` diff hunks were confined
  to Q90; no new native-review or commit claim. Mirror UNIMPLEMENTED and not read; the PM owns the
  commit and assessment.
- F8 CORRECTION/INCIDENT (2026-10-24): in a read-only clarification the initial writer admitted
  running exact `sandbox_bash` shell `grep -o`, `grep -c` and `grep -n` content searches despite the
  search contract. The breach is recorded, NOT endorsed, and those checks are REJECTED as
  compliant evidence; no `CLAIM-RETRACTIONS.md` path was authorized, so the incident lives here
  only. Reliance is replaced by compliant dedicated `read`/`sandbox_read` factual/table readback
  (no shell searches, no Python-search bypass) in this correction. Correction `1/1`, session
  `ses_e932076c5ffe1PbmDPFOBqn2s1`, baseline `2318ed4` (parent `36d461f`) containing the applied
  initial edits; the original 399-line / 48,701-byte figure stays clearly HISTORICAL INITIAL, and
  the corrected TOTAL and baseline→corrected DELTA receipts are measured against `36d461f` and
  returned to the PM. Correction readback by dedicated `sandbox_read`: 46 seat rows (43 in the plan
  table plus the 3 Systematic rows) and 12 lens rows; no shell search used. No additional writer
  round.
- T3.0 planning FINAL owner-exception round (2026-10-24): writer session
  `ses_e930fe4d5ffebBkTISkNy8twgW`; sandbox root `/work`, synthetic branch `work` (the initial ref
  was unresolved; the worktree was materialized from the index without changing content), baseline
  commit `ae3c8af248c72ec5a551b09263ff2e5dc5da1ad2` (parent `36d461f`). Normal correction stays
  `1/1`; this separately recorded OWNER OVERRIDE authorizes exactly ONE final bounded round and one
  three-path docs commit. Reason: the installed correction left the F2 rationale and F7 estimate
  cells wrong. Scope/limit: F2 rationale, all 22 F7 estimate cells and the required
  review-size-exception bookkeeping only; F1, F3-F6 and F8 are not reopened and no new source
  decision is made. Dedicated `sandbox_read` readback confirms 46 seat rows, 12 lens rows and 22
  numeric estimate cells; `git diff --check` is clean and the final receipt against `36d461f` is
  returned to the PM. No source tests, full verifier, live model resolution or native review ran.
  The prior initial prohibited `grep -o/-c/-n` incident remains recorded and rejected, not repaired
  by this round. Mirror UNIMPLEMENTED/not read; PM owns the commit and assessment.
- T3.0.1 `q90-t30-variants-u1` (2026-10-24): SOURCE STAGED, not activated. Initial writer sandbox `ses_e92b5326affe5Y5TpcXbN3OgK3`, root `/work`, synthetic branch `work`, baseline `9479c0ab3dd7d1962afbc68290e8b8a688cc19ed` (parent `544a2630...`); route `workflow-odd-secure`, delegated cloud `odd-apply`, multi-file plus secure-preparation trigger; owner closed `77ef08a..544a2630` by DECISION, not native review; boundary `544a2630...`.
  `supportedVariantFailure` staged; not called against live seats; `opencode.json` unchanged; T3.0.2 must set orchestrator `high` and activate the strict validator; fixture checks are not live clearance.
  Initial RED: 22 tests, 20 failures + 5 errors from the absent block/controls; initial GREEN after source+pin: 22/22, Gemini 20/20, `bash -n`/`git diff --check` clean, verifier+pin `f18638...`.
  Correction `1/1` (fresh pass; baseline snapshot `b79bcd20bff56e38af8c950caac46a46df3abd7e`, parent `544a2630`, snapshot label `ses_e92a38cacffegugfXPCSsJNNj7`): the PM's first post-code `aft_inspect` was PARTIAL with 11 Pyright optional-access errors in `tests/test_model_variants.py:85,86,90-93,180,191,196,201,228`; after that correction the last VERIFIED host diagnostics were 11→1 remaining at `tests/test_model_variants.py:203:33` (`extract_block().replace` on optional `None`); AFT Bash 0, and the TS workspace marker is absent and Markdown has no producer, so no all-static-clean or zero-error claim.
  F-STATIC partially fixed with a typed `required_block` accessor (explicit None guard) and an explicit regex `match` guard; no blanket ignores, and `extract_block` still returns None so the missing-marker negative control is retained, but correction 1/1 left the one optional-`None` diagnostic at line 203. OWNER OVERRIDE (2026-10-24): exactly one fresh correction; reason the residual optional `None.replace` at line 203; scope this one-line `required_block().replace(...)` change plus factual evidence and targeted tests; one new writer; normal correction count remains 1/1; previous task IDs, dispositions, owner quote, the `77ef08a..544a2630` closure-by-DECISION and PM deferral are preserved. The exceptional accessor fix is this round; final host `aft_inspect` confirmation is pending the PM envelope.
  F-PROTOTYPE fixed with an own-key lookup, so `constructor`, `__proto__` and `toString` return named `SUPPORTED_VARIANT_MODEL_UNCLASSIFIED` rather than crashing on `.includes`; a new executable test covers those three plus the ordinary unclassified-model control; observed RED before the source fix and GREEN after.
- T3.0 normal-row/validator unit `q90-t30-advisor-drift-u1` (2026-10-24): Task/session id not
  exposed to this writer. Sandbox root `/work`, synthetic branch, baseline parent
  `d14e83f90a4f044e5b42b268fd47eec8c4ee96d8`; host branch not switched. Delegated cloud
  `odd-apply`; one writer, targeted tests, NO advisor and NO independent verifier under the
  recorded THIS-unit owner cost override. Changed paths: `global-config/opencode.json` (four
  agents), `WORKFLOW.md` (six rows), `verify-workflow.sh` (`modelFamily` + Ling target),
  `global-config/plugins/workflow-health-check.ts` (pin), three test modules and the
  tracker/TODO/ROUTER-LOG/advice metadata. Observed: RED 7/75 before source; GREEN 75/75,
  0 skips/errors, 103 Bun controls; JSON parse, `bash -n`, `git diff --check` clean; pin
  equality. Static diagnostics were not workspace-correct for AFT, so no clean claim. Commit
  `PENDING-COMMIT`; review assessment `PENDING`; runtime/full verifier/deploy/native review
  UNVERIFIED. Receipt measured at PM handoff.
  F-EVIDENCE: the advice record now carries the post-code advisor (`ses_e92aa908bffeq3Wgqt0lx7lxbL`, `opencode-go/kimi-k2.7-code`, no blockers) and independent verifier (`ses_e92aa9096ffeN3ynypfY0hWNyf`, `openai/gpt-6.1-sol`) results; the verifier's INITIAL 50-test execution and first-pass diagnostics are recorded as evidence, not approval.
  V1: the full `opencode-go/deepseek-v4-pro` identity remains an ASSUMPTION (owner names the model; `opencode-go/` follows the plan convention, not a resolved full ID); resolve it before the optional v4-pro profile. No unavailability claim.
  V2: the activation test accepts any matching line rather than independently requiring both the T3.0.2 row and its prerequisite (both are present); recorded as optional/deferred test-strength, not changed.
  Post-correction checks: 23/23 variant tests GREEN (RED observed for the new prototype test before the source fix), Gemini 20/20, model-independence 8/8 (51 total), `bash -n` and `git diff --check` clean, verifier/pin both `d2555af8325d5f2e8c854f1d08bc01522f7688a5f21c57796d919f601796a6ff`. OWNER OVERRIDE rerun: same 23/23 + 20/20 + 8/8 (51/51, 0 skips), `bash -n` and `git diff --check` clean; final host diagnostics confirmation still pending.
  No full verifier/deploy/live seat checks/native review; source checks vs live UNVERIFIED. Mirror UNIMPLEMENTED/not read; PM owns commit/assessment; exact receipt in the PM envelope.
  This correction does not change the staged/untouched seat contract or activate the validator.

## Next step
T3.0.1 (`q90-t30-variants-u1`) source is STAGED with the validator unactivated; T3.0.2
(`q90-t30-core-seats-u1`) follows after the PM/owner activation gate sets the orchestrator to
`high` and activates the strict validator for all confirmed models. T3.0.3a PM reassignment is
deferred until Planner setup is complete, superseding the earlier PM-before-T3b ordering. T3.0.3b-
T3.0.9 follow in order, then T3b, T3c (permission-only), T3d (residual), T4-T6. Q90 remains IN
PROGRESS.

Review-size exception (owner-authorized 2026-10-24): this candidate is 561 authored lines / 47,119 bytes, over the ~400-line cap. Reason: a single coherent model-remap unit; splitting would require committing a known-defective detector (V1–V3) or a second full writer cycle. Correction counter remains 1/1; the exception is not a reset.

Receipt-byte limitation (prior installed candidate, before this owner-authorized V2 follow-up): an independent count recorded 565 authored lines; its writer reported 48,110 raw patch bytes. Independent byte measurement was refused with the exact error `argv item contains shell metacharacters` and was not retried. On the writer's measurement that prior candidate was far below the 100 KiB / 102,400-byte cap, but its bytes were NOT independently byte-verified. The frozen owner exception above (561 authored lines / 47,119 bytes) and correction round 1/1 are preserved verbatim; the 565/48,110 figures are prior-candidate evidence and do not imply that 565 authored lines remains the final total. The updated current TOTAL for this follow-up candidate is reported separately in the PM handoff envelope. No byte figure here is an independent measurement.

## Kimi-removal metadata closure (2026-10-24)

Unit `q90-t30-kimi-removal-u1` — METADATA-ONLY closure; class `documentation` under the
simple-docs allowlist; route `workflow-odd-secure` metadata phase; delegated cloud `odd-apply`.
Exactly three paths change in this unit: this tracker, `docs/TODO.md` and `ROUTER-LOG.md`. No
test, config, skill, prompt, source, advice or verifier change is made. The PM commits the
applied result; this worker does not commit or update metadata. The Magic Context mirror remains
UNIMPLEMENTED/not read. This metadata writer's session ID was not exposed to the worker and is
not invented; it belongs to the PM envelope. This is the same unit's post-commit metadata, not a
new implementation or correction round.

IMPLEMENTATION RECEIPT (source, unchanged by this metadata unit): commit
`ee2dab0f2c24f3daaf34bf50ba4633557fbf1b19` on `chore/multi-agent-v2-phase1`, 8 repository paths,
independently counted 587 authored lines = 555 additions + 32 deletions. Independent evidence:
verifier session `ses_e913c44faffeUx5Yfi8UYWMLav`; verifier-reported latest snapshot
`6661e88c45c9f8f3be1b07e718a3c2bd66cc6286` (direct parent `decd167`; not present in this
checkout, so not independently readable here); the host commit confirmed
the 555/32 count. The writer's raw patch receipt is 51,008 bytes and is NOT independently
verified: a prior independent byte measurement was refused with exactly `argv item contains shell
metacharacters` and was not retried; that limitation is recorded in the advice record (line 25)
and in the frozen paragraph above. On the writer's figure the current patch is below the 100 KiB
/ 102,400-byte cap, but there is no independent byte claim. Historical sizes 561 authored lines /
47,119 bytes (owner-frozen exception) and 565 authored lines / 48,110 bytes (pre-V2 follow-up)
are unchanged and must not be read as the final size.

Verification state: V1 fallback controls, V2 actual tool-scope/vision control, V3 variant
mutations and V4 same-seat independence are CLEARED. The latest independent execution was
`python3 -B -m unittest tests.test_q90_t30_kimi_removal tests.test_model_independence -v`:
`Ran 22 tests in 0.101s`, `OK`, 14+8, with zero failures, errors or skips; this metadata unit did
not rerun it. `aft_inspect` is PARTIAL; the earlier unchanged
`tests/test_model_independence.py:72:58` optional `specialist.group` diagnostic is
recorded/inferred pre-existing. The latest scoped follow-up Python result was 0 errors, not an
overall clean claim. The earlier 88-check result is historical, not the latest 22-test result.
There is no full runtime approval.

Assessment (EXACT IMPLEMENTATION assessment; not a review, approval or closure): the
`host_review_assess` call with
`baseRef=decd167b8b01e0d4fcd41653840f817d607c7859` and `committedOnly=true` returned status 0,
`gentle-ai.review-assessment/v1`, risk `medium`, reasons
`[{code: configuration_change, path: global-config/opencode.json}]`, `changed_paths` 8,
`changed_lines` 587, candidate `{kind: base-diff, base_ref:
decd167b8b01e0d4fcd41653840f817d607c7859, consumed: false}`, `review_due: false`,
`review_due_reason: under_budget`. The last reviewed boundary is RETAINED at
`decd167b8b01e0d4fcd41653840f817d607c7859`. The assessment neither approves, advances nor closes
the candidate, and no new lineage was started. RDD is enabled/global.

Lineage: `review-642f4745d7f6d6fe` is owner-designated SUPERSEDED, NOT approved and NOT closed.
Provider blocking was owner-reported twice and was not reproduced here (an integration provider
error was observed); no new mechanism-equivalence claim is made.

Owner decision (2026-10-24): native review of `ee2dab0` runs AFTER the owner deploy, so the
reliability lens uses `opencode-go/minimax-m3.1-flash` instead of Kimi. This is an OWNER DECISION
recorded here; it is not a claim that review or deployment executed and is not a change to
`WORKFLOW.md` policy. No review start, acknowledgement, consent or state change occurred. Deploy
and restart are OWNER actions and were NOT performed; every runtime, consumer, model-availability
and M3.1 gate remains UNVERIFIED.

Model outcome — CANONICAL SOURCE ASSIGNMENTS ONLY, not a live/deployed claim. Five prior Kimi
seats were remapped: `review-reliability` and `asi-review-reliability` to
`opencode-go/minimax-m3.1-flash` `xhigh`; `advisor-integration-pre` to the same model `high`;
`advisor-integration-post` and `advisor-testing-post` to `opencode-go/qwen3.8-flash` default with
`variant` OMITTED; additionally `advisor-maintainability-post` to
`opencode-go/ling-3.1-flash` default with `variant` OMITTED. Readability
(`review-readability`/`asi-review-readability`) stays `opencode-go/muse-spark-1.3-contributor`
`high` unchanged. Future `advisor-ux-pre` is planned as `opencode-go/minimax-m3.1-flash` `high`
WHEN created at T3.0.7a and is NOT created now. The inactive Kimi exact fallback entry was
removed; evaluator exclusions are preserved. The owner called five seats "live", but because
deployment was not performed these are clearly source assignments only.

Separately recorded owner authorizations: the original size exception, the single recovery and
the bounded V2 test follow-up remain as previously recorded. Correction counters stay 1/1
(normal) and this metadata unit is not a new implementation round. Nothing is deleted: the
historical tracker-order incident, the pre-existing diagnostics and the disagreed A5 conclusion
remain intact. `q90-t30-kimi-removal-u1` source is COMPLETE; deployment and native review are
PENDING. Q90 remains IN PROGRESS and no new planned unit is added.
