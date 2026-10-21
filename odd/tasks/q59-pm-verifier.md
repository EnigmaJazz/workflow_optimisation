# Q59 — PM layer: verifier

**Status:** **SOURCE COMPLETE, SOURCE-COMMITTED AND SOURCE-ACKNOWLEDGED; METADATA EVIDENCE
COMPLETE in this final metadata record.** This is unit `q59-pm-verifier-impl-u1`; tasks A–D are
source-complete and task E is this document set. Activation/deploy is **UNVERIFIED**: no verifier
mirror, service restart, full verifier, deploy, or live probe ran; those are HOST-ONLY and NOT RUN.
Q59 earns **no Q56 pilot credit** and is not a deployment claim. Prior `FAIL`/`PENDING-COMMIT`
records and old pins are **HISTORICAL**, not current.
**Tracker task:** `q59-pm-verifier`.
**Parent:** `odd/tasks/pm-layer.md` T7 (Q59).

## Objective

Make the verifier assert the project-manager layer as a set of route coordinators rather than a
single hard-coded `gentle-orchestrator` name: a coordinator-generic inventory, the PM identity
surface, permissions/depth/family independence, prompt budgets, behavioural probes, and the
digest re-pin.

## Problem

The existing verifier already contains substantial orchestration and PM checks, but they grew as
single-name assumptions and as partial per-tool grants. There is no line-numbered classification
that separates genuinely coordinator-generic assertions from orchestrator-only ones, and the
historical "23 single-name checks" figure has not been verified. Q54 also records that broker
identity on permitted calls is inferred, not echoed, so the identity surface must be asserted
explicitly rather than assumed.

## Authorized scope

### Current metadata unit (2026-10-21)

- Authorized writes are exactly `odd/tasks/q59-pm-verifier.md`, `odd/tasks/pm-layer.md`,
  `docs/TODO.md`, and `ROUTER-LOG.md`. This is a metadata/final-closure unit only.
- The installed source is frozen: the ten source paths below, `WORKFLOW.md`, and `docs/PLAN.md`
  must stay byte-identical to the worker baseline. No prompt, config, test, verifier, plugin, or
  pin edit; no deploy, branch switch, push/PR, native review/evidence, or worker commit.
- The PM owns the fixed-host commit after fresh independent verification and post-advice. Native
  review remains externally driven. This worker returns a staged reviewability receipt only.
- Existing unrelated files are preserved; an untracked broker bundle is not part of the candidate.

### Frozen source paths

- Commit1: `global-config/opencode.json`, `tests/test_pm_layer_prompts.py`,
  `tests/test_pm_task_allowlists.py`, `tests/test_tiny_fix_route.py`.
- Commit2: `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts`,
  `tests/test_review_pipeline_permissions.js`, `tests/test_review_pipeline_permissions.py`,
  `tests/test_gemini_advisor_route.py`, `tests/test_orchestrator_prompt_source.py`.

### Planning-scope correction (R3-002; historical)

- The original planning unit (2026-10-19) authorized **documentation only**: this tracker first,
  `pm-layer.md`, `docs/TODO.md`, and `ROUTER-LOG.md`; it did **not** authorize source edits.
- The owner later authorized the A–E source implementation, a minimal
  `global-config/opencode.json` correction (remove `general` from the two PM task maps), and
  exactly the two PM Tiny-fix prompt sentences. Every other prompt byte and the orchestrator
  prompt/grant stayed unchanged. The current phase is metadata-only again.
- The historical planning prohibition is therefore correct for its date and is not a statement
  about the later authorized implementation. Q04 was never a blocker.

### This planning unit (HISTORICAL; retained verbatim)

The checkboxes and pending status below are the original planning record, not current state.
Tasks A–D are now source-complete and acknowledged; see the current evidence below. The
`gentle-orchestrator`/`general` tiny-fix pair in B is the superseded pre-2026-10-19 wording; the
current B section governs.

- Authorized writes are exactly: `odd/tasks/q59-pm-verifier.md` (created first),
  `odd/tasks/pm-layer.md`, `docs/TODO.md`, and `ROUTER-LOG.md`.
- Documentation and tracker text only. No implementation source, test, config, prompt, plugin, or
  verifier edits; no deploy; no branch switch, push, PR, or worker commit/native-review
  operation/evidence.
- The PM owns the fixed-host work-unit commit and every post-commit risk assessment. The PM does
  not run native review; native review remains externally driven. This worker returns a staged
  reviewability receipt only.
- Preserve unrelated existing files. Stop on a conflicting tracked modification.

### Future implementation units (A–E) — authorized later, not this unit (HISTORICAL)

- **Scope guard for A–E as well as this unit:** no agent-prompt or `global-config/opencode.json`
  edits, and no `WORKFLOW.md` edits. Audit only. An exact missing clause or grant returns PM
  `NEEDS_INPUT` for a separate unit; it is not edited here. Q04 is not a prerequisite or blocker.
- [ ] **A — coordinator inventory.** Produce a line-numbered inventory that classifies each existing
  check as coordinator-generic or orchestrator-only. Do not repeat the unverified "23" as an exact
  count. The coordinator set is `gentle-orchestrator`, `pm-odd`, `pm-systematic`, plus
  `gentle-orchestrator-legacy` ONLY while it is actually selectable. Never restore a retired agent.
- [ ] **B — PM identity surface (exactly one unit).** Assert the one-unit identity boundary: one PM
  session executes exactly one work unit, never a whole feature or a multi-unit session. Assert
  the assigned route skill is loaded first, route validation against `WORKFLOW.md`, the
  `pm-unit-brief/v1` schema pointer, stop/resume, and report-not-proof. Keep canonical/deployed
  consistency without duplicating the prompt parity suite. Audit permissions and depth; do not
  edit prompts or `global-config/opencode.json`: the orchestrator admits PMs; the only
  general-dispatch exception is the explicit tiny-fix rule; PMs admit only their named
  writers/verifiers; no deeper or coordinator self-dispatch. Reuse the family helper; an unknown
  family fails closed, and the tiny-fix exception is preserved: DeepSeek `gentle-orchestrator`,
  OpenAI `general`, Sol PMs, and DeepSeek `odd-apply` / `gentle-ai-worker`. Preserve the
  orchestrator-only tiny-fix, fixed-host, and project-registration rules and the existing
  independent pairs. No blanket PM fixed-host grants. If a required grant is missing, return
  `NEEDS_INPUT` for a separate unit.
- [ ] **C — prompt budgets and behavioural probes.** Keep the existing PM `<6000` cap, measure and
  report every prompt size, and find the authoritative orchestrator budget. The existing
  prompt-source test prints bytes/lines but does NOT establish a numeric cap; if the authority stays
  unresolved, return `NEEDS_INPUT` and do not invent a threshold. Extend existing behavioural probes
  ONLY through the orchestrator (Q51 at `docs/TODO.md:463-475`; verifier `:5354-5462`), falling back
  to static/fixture checks when unusable. Live probes are HOST-ONLY and are NOT RUN in the sandbox.
- [ ] **D — tests and digest pin.** Every new condition needs a mutation-positive control: a
  reverted, removed, or wrong clause must fail the assertion. Assertions and their positive
  controls travel with the behavior in the same commit; do not create standalone test commits.
  Extend the existing `tests/test_review_pipeline_permissions.py`, `tests/test_pm_layer_prompts.py`,
  `tests/test_orchestrator_prompt_source.py`, and `tests/test_anchor_manifest.py`; do not create a
  parallel suite. Pin `VERIFY_SCRIPT_SHA256` in `workflow-health-check.ts` LAST, after all verifier
  edits, in the same verifier-edit commit that carries the behavior and tests; do not create a
  standalone pin commit. Verify with `sha256sum` equality and the `read_verify_script_pin` regex.
- [ ] **E — metadata and records.** After implementation, update the tracker, `docs/TODO.md`, and
  `ROUTER-LOG.md` with observed results. Update `docs/PLAN.md` only as a separately authorized
  unit.

## Historical planning evidence (retained verbatim; superseded)

Evidence below is from the read-only explore session recorded by the PM
(`ses_eaa066b63ffeI5HcVR3jdxT8jL`); this planning unit did not redo the audit. Its line numbers
predate the correction and are superseded by the current inventory below.

- **Observed — PM host reads/grants and positive controls:** `verify-workflow.sh:2771-2919`.
- **Observed — PM execution/tool denies:** `verify-workflow.sh:3016-3031` (`pmAgents`).
- **Observed — SDD retirement:** `verify-workflow.sh:3033-3053`.
- **Observed — PM task and `odd-apply` rules:** `verify-workflow.sh:3063-3076`.
- **Observed — existing reuse surfaces:** relay lockdown and writer model-family checks already
  exist (family helper `:2395-2410`). Audit and reuse them; do not duplicate.
- **Observed — legacy key:** a bounded full agent-object read of `global-config/opencode.json`
  found no `gentle-orchestrator-legacy` key. The conditional deployed inventory remains unresolved
  because no deployed/external inspection is available here.
- **Observed — PM cap:** `tests/test_pm_layer_prompts.py:141-147` asserts `<6000` characters.
- **Observed — prompt-size reporting:** `tests/test_orchestrator_prompt_source.py:625-647` prints
  bytes/lines; it does not define a numeric orchestrator cap.
- **Observed — Q26 boundary:** stable-anchor machinery is present at `verify-workflow.sh:4637-4917`,
  but broader review/deployment closure is still pending per its tracker. Do not claim all of Q26.
- **Observed — prerequisites:** Q59 names Q55 as its prerequisite. Q26 and Q04 are "easier after",
  not hard prerequisites; the user explicitly stated Q04 is NOT a blocker. Verify Q55 handoff
  acceptance at implementation start instead of inferring its state from aggregate TODO status.
- **Observed — model config:** PMs use `openai/gpt-6.1-sol` (`global-config/opencode.json:2067,:2204`),
  `odd-apply` uses `opencode-go/deepseek-v4.1-flash` (`:2350`), `gentle-ai-worker` uses the same
  (`:369`), the orchestrator uses `opencode-go/deepseek-v4.1-flash` (`:466`), and `general` uses
  `openai/gpt-6-luna` (`:243`). Configured identity is observed; live runtime/fallback is not attested.
- **Constraint — no route rewrites here:** any future verifier split must preserve existing checks.
  The later authorized implementation scope has no `WORKFLOW.md` edits.
- **Constraint — fail closed on gaps:** no agent-prompt or `global-config/opencode.json` edits in
  this planning unit or in future A–E; no `WORKFLOW.md` edits. An exact missing clause or grant
  returns PM `NEEDS_INPUT` for a separate unit rather than being edited here. Q04 stays
  non-blocking.

## Source implementation evidence (current)

Five actual source commits on `chore/q72-t1b-tiny-fix-contract`; the chain was read from the Git
objects, not reconstructed from prose. HEAD at this unit's start was metadata commit
`70d5befe1d649c923f17cfbc29ce181be9a706bb` (M1), whose parent is the boundary
`41fbe77a7ba3214c340e610df935ff7fb73b62c0`.

| Step | Source commit | Subject | Authored lines / raw patch bytes | Source native review (owner-relayed) |
|---|---|---|---|---|
| S1 | `58b1c8c7366ab01086fec54b30437d582c6d09d0` | `fix(pm): align tiny-fix dispatch with independent writers` | 253 / 32,732 | `review-87858bd36a02d266` (S1 + S2a), APPROVED + ACKNOWLEDGED |
| S2a | `44f22bdc1d63c3f9a5e77e86bace1f274861fdbe` | `fix(verifier): share coordinator permission checks and isolate harness dependencies` | 189 / 22,277 | `review-87858bd36a02d266` (S1 + S2a), APPROVED + ACKNOWLEDGED |
| S2b | `4677915f2aa911b5dd7542f0f0b95d49728d0945` | `feat(verifier): enforce PM identity and handoff contracts` | 162 / 13,680 | `review-028c45784dd7c5b9`, APPROVED + ACKNOWLEDGED |
| S2c | `db85a6b2543effba24e2b68a3dc5dc534d5a7bc0` | `feat(verifier): enforce coordinator task allowlists and dispatch depth` | 185 / 13,674 | `review-5bea3eacbe067a77`, APPROVED + ACKNOWLEDGED |
| S2d/e | `41fbe77a7ba3214c340e610df935ff7fb73b62c0` | `feat(verifier): check PM model independence and prompt routing budgets` | 213 / 19,607 | `review-8bf653955b7f58f5`, APPROVED + ACKNOWLEDGED |

- The four approvals are explicit **owner-relayed** facts, not worker-produced tokens; this unit
  did not read acknowledgement tokens and does not re-review acknowledged source candidates.
- Assessments immediately after each commit were observed: S1 `medium`, `review_due=false`,
  `review_due_reason=under_budget`, `consumed=false`; S2a, S2b, S2c and S2d/e `high` with
  `review_due=true`, each closed by the owner-supplied review above. These are source commit
  identities, not a metadata SHA. The metadata commit identity belongs to the PM envelope.
  Owner requirement: any final metadata assessment is taken at base
  `41fbe77a7ba3214c340e610df935ff7fb73b62c0` with `committedOnly=true`, not at M1 HEAD
  `70d5befe...`; the PM performs and records it.
- **Final source verification (independent, PM-supplied):** verifier
  `ses_ea4ab17f0ffeU4b2IVR6BgPiap` returned **PASS** and post-code advisor
  `ses_ea4ab17c3ffeRb02HFxdetDKAt` returned **READY**. Earlier post-code advisors
  `ses_ea4eb1771ffeoIegz67GBAKUno` (after S2b) and `ses_ea4d23e17ffe20TrkqlZ7bsVR0` (after S2c)
  also returned READY. This metadata unit did not rerun those source checks.
- **Source-time observed checks** (prior writer/verifier sessions; NOT re-run here): direct
  `bun tests/test_review_pipeline_permissions.js` PASS; focused seven Python modules 102 PASS;
  full `python3 -m unittest discover -s tests` 228 PASS with no skips; routing-guard 104 pass /
  0 fail / 254 expectations on a fresh throwaway `HOME`; `bash -n` and `git diff --check` pass;
  actual `sha256sum` and the `read_verify_script_pin` regex match the current pin.
- **Predicate controls:** 103 executed controls = 91 rejections + 12 accepted, in groups
  27/8/40/18/10; the Python module asserts every marker so an independent verifier can rerun the
  same groups. Five budget-boundary fixtures include astral 5999/6000; five actual
  `PY_ODD_READONLY` consumer mutants pass. Group 4 configured/runtime fixtures are NOT live
  model/fallback attestation.
- **Prompt metrics:** all 43 prompt sizes are measured and asserted by the existing source tests
  (no new threshold, no duplicate suite). The durable reference is
  `tests/test_review_pipeline_permissions.py`, which asserts every `prompt-size: <name>=<size>`
  line from the verifier run. The named values are
  `gentle-orchestrator=57167`, `pm-odd=2968`, `pm-systematic=2982`; the PM `<6000` cap is
  enforced. The numeric orchestrator cap is **DEFERRED to Q57** (owner 2026-10-19: "about 8,000"
  is the planning target, not an enforced cap).
- **Modules:** seven changed test modules (6 Python + 1 JS); `tests/test_anchor_manifest.py` was
  executed unchanged, not extended. No standalone test or pin commit exists.
- **Current verifier pin:** `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`,
  equal to `verify-workflow.sh` and its `VERIFY_SCRIPT_SHA256` literal. Historical
  `57fdc56c...`, `22aa96f9...` and `bdce2e68...` are not current.
- **Activation/deploy is UNVERIFIED.** No verifier mirror, service restart, full verifier, deploy,
  or live probe ran; no live model/fallback/config-consumption attestation is claimed.

## A — coordinator inventory (current installed source)

Read from the installed `verify-workflow.sh`; line numbers are the current post-S2d/e source.

| Lines | Symbols / checks | Class |
|---|---|---|
| 2791-2803 | `cfgTool`, `cfgPerm`, `hostReviewAssessFailures`, `hostReviewDiffReadFailures` shared helpers | coordinator-generic |
| 2805-2955 | `pmAgents`, `coordinatorAgents`, host-review permission/tool maps, global-default and negative-sweep controls | coordinator-generic |
| 2956-2985 | `pmIdentityFailures`: seven identity needles per PM, handoff schemas/unreadable text, orchestrator pointer | PM-generic |
| 2986-3020 | `coordinatorTaskGraphFailures`: PM admissions, self/deep dispatch, strict maximum task keys, required lanes | coordinator-generic |
| 3043-3121 | `reviewAgentLockdownFailures` and review-lane lockdown | generic review lanes |
| 3122-3136 | `pmAndAgents`; PM no-execution / no-sandbox-read surface | coordinator-generic (PM subset) |
| 3138-3160 | SDD retirement / `host_sdd_*` deny scopes / `pm-sdd` absence | coordinator-generic |
| 3161-3195 | `odd-apply` and PM writer lanes; `pmGeneralDispatchFailures`; orchestrator `general` negative | PM-generic + orchestrator-only |
| 3196-3256 | `geminiAdvisorRouteFailures`; coordinator dispatch and isolation | coordinator-generic |
| 3257-3360 | memory policy, `relayReviewAgents`, `RELAY_TASK_GRANTED_OUTSIDE_ORCHESTRATOR` | orchestrator-only + generic review lanes |
| 3361-3520 | orchestrator fixed-host/review exceptions, registration, prompt checks | orchestrator-only |
| 3521-3690 | runtime model/tool/permission checks | orchestrator-only |
| 5282-5340 | runtime probe-set derivation via `readDebug` | generic |
| 5535-5587 | `PY_ODD_READONLY` ODD read-only probe | orchestrator-only |

Coordinator set = `gentle-orchestrator`, `pm-odd`, `pm-systematic`. `gentle-orchestrator-legacy`
is absent from the current config and was not restored; a legacy coordinator is considered only
while actually selectable, and never by restoring a retired agent.

## B–E — current task closures

- **A — inventory:** done above from the installed source; the unverified "23" count is not used.
- **B — PM identity/depth/contract:** both prompts carry exactly-one-unit, route-first,
  `WORKFLOW.md` validation, `pm-unit-brief/v1`, stop/resume, and report-not-proof. The
  orchestrator alone keeps `general`; both PMs dispatch a mid-unit tiny fix only to `odd-apply` or
  `gentle-ai-worker` (DeepSeek lanes), never `general`. Neither PM grants `general`; an undeclared
  task key is rejected whether `allow` or `deny`; unknown families fail closed. PMs run on OpenAI
  Sol; the local writer `gentle-ai-worker-local` is `kinver/professional` and `gentle-ai-verify`
  is OpenAI Sol. This is not "all writers/verifiers on DeepSeek". Config/prompt runtime is not
  attested.
- **C — budgets/probes:** all 43 prompt sizes measured; `pm-odd=2968`, `pm-systematic=2982`,
  `gentle-orchestrator=57167`; PM `<6000` enforced; the numeric orchestrator cap remains DEFERRED
  to Q57 (no invented threshold). Behavioural probes use the existing harness; live probes are
  HOST-ONLY and NOT RUN.
- **D — tests/pin:** seven existing modules carry the behaviour (6 Python + 1 JS); the anchor
  manifest ran unchanged; assertions and mutation-positive controls travel together; the pin was
  set LAST to `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`. The earlier
  single-candidate and two-commit split records are historical.
- **E — metadata:** this tracker, `pm-layer.md`, `docs/TODO.md`, and `ROUTER-LOG.md`; the PM owns
  the commit and immediate post-commit assessment.

## Advisory dispositions (Q59 source-review namespace; IDs are not globally unique)

| ID | Disposition |
|---|---|
| R3-001 | **REFUTED.** Future PM systematic `odd-apply` prompt consideration only; no edit now. |
| R3-002 | **CORRECTED above.** Historical planning scope authorized docs only; the later owner authorization covered source implementation plus the minimal config and two PM Tiny-fix sentence corrections; current phase is metadata-only. |
| R3-003 | **CORRECTED.** TODO/M1 status was updated for the source phase; this final record now carries the complete metadata status. |
| R3-004 | **DEFERRED.** Prompt allowlist alignment check is a future consideration; no claim of full restoration. |
| R3-005 | **DEFERRED.** Declaration-extractor fragility. |
| R4-001 | **DEFERRED.** Bun/Node `PermissionError` fallback. |
| R4-002 | **DONE in M1.** Verifier/pin ROUTER-LOG row added with the actual commits, reviews, checks, and pin. |
| R3-needle-parse-fragility | **WARNING; DEFERRED.** Literal needle split hardening is future work. |
| R4-failfast-agg-dropped | **SUGGESTION; DEFERRED.** Identity caller aggregation is future work. |
| R3-stale-line-ref | **SUGGESTION; DEFERRED.** A later test-only slice may refresh the stale `3130-3131` comments; no source/test edit now. |
| R4-brace-balancing-fragility | **SUGGESTION; DEFERRED.** String/comment-aware extraction is future work. |
| R4-family-gate-widening | **WARNING; INFORMATIONAL, INTENDED.** Unknown families fail closed. |
| R4-pin-binding-unverified | **SUGGESTION; MITIGATED.** Native review could not recompute the pin; the independent verifier ran the actual sha256 plus the regex mechanism. This is not a fake native attestation and no source bug is claimed. |

No advisory becomes a blocker or a source fix in this unit.

## Historical provenance and recovery record (clearly HISTORICAL)

- **Frozen preclosure tracker:** the 644-line pre-M2 body is preserved in the worker baseline
  commit/ref and the broker full source. It is provenance, not current state:
  - Full preserved source commit: `d41ae29be36caac485efa09c64ebaa60b47b57fe`.
  - Partition baseline commit: `5f5fd506b4ffe8b6bd0bb895ad17bd7812f6b864`.
  - Full candidate tree: `84ae779815e63320160d4fcbc96d40eccc13d154`.
  - Historical tracker blob: `78cba29bd73ab4bba4fb04b0ae1284e84cd79fb9`.
- **M1 metadata:** `70d5befe1d649c923f17cfbc29ce181be9a706bb` changed three paths
  (`pm-layer.md`, `docs/TODO.md`, `ROUTER-LOG.md`), 130 changed lines / 26,223 raw bytes; the M1
  assessment against base `41fbe77` with `committedOnly=true` was **PASSIVE** (non-executable
  only), `review_due=false`, `consumed=false`. The exact final M1 result
  `75982faf2b2ef5852d08e75f2616913f62a8bf6e` was bound to verifier snapshot
  `610cb365c77b5a2c9eb03a64775740ef29fb52ee` via `4370926d8568913c0e2c88d32749f0c3` with a
  zero-path diff over the three paths; the raw M1 receipt (HOST, 26,223 bytes) is
  `de07e7a54070084fbd5c6a72c3af37c3`. M1 author/refiners were
  `ses_ea47c643fffecz5APMsWeS67FP`, `ses_ea46a474bffeCi1BcqFMvO8Evq`, and
  `ses_ea4576e59ffexHPNu4YKpgdwuE`; final M1 post-advice `ses_ea45e99a3ffeIAwsLPY8bB1mAs`
  was READY and M1 independent verifier `ses_ea4548d58ffeics4rXA6gY3zPi` passed 28 tests, the
  pin, source history, and the MD facts. This unit does not redo that work.
- **Prior failures/crash records are HISTORICAL, not current.** The earlier verifier FAILs, post
  advisor NOT READY results, the owner-reported 2026-10-20 crash recovery, and the coverage-control
  pass are superseded by the five committed source commits, their owner-relayed approvals, and the
  final independent PASS/READY above. The full narratives remain in the frozen snapshot; this
  record keeps only what is needed for provenance.
- **Writing provenance:** source writers were S1 `ses_ea83cc04fffeUNW3Gm2v0q3IsU`,
  S2a `ses_ea5200a7fffe9PVHXUIydyLrNB`, S2b `ses_ea4f78e21ffe1fwndM1PRIzfv6`,
  S2c `ses_ea4d6f3f5ffeev5j73dICaLj9B`, S2d/e `ses_ea4b3a38cffeEL3VxmAvi4IHA2`; all were
  `odd-apply` DeepSeek writers, separate from the Sol PM. Pre-code advisor
  `ses_eaa0c1a94ffeaxyFcbfo5hlcON` was reused; planning post advisor
  `ses_ea9f1a0ecffe8aPpAJIGyw2L11` is historical.
- **Magic Context mirror:** the deterministic mirror-write tool is unimplemented. No mirror write
  or body read was performed. The earlier one-time observations (262-line anchor, last
  `PENDING` line, `604a...` SHA) are retained as an observation only; they are not hash/committed
  tracker proof and were not rechecked against modified text.

## Constraints

- Metadata-only ODD work unit; mutation is limited to the four authorized metadata paths.
- Q59 is NOT one of Q56's ten implementation pilot units. It earns no pilot credit.
- The implementation is complete; a fresh PM takes one bounded metadata unit, not an A–E redo.
- No implementation source/test/config/prompt edits, deploy, branch switch, push, PR, worker
  commit, or worker native-review operation/evidence in this unit. The PM performs the fixed-host
  work-unit commit and post-commit assessment; native review is not run by the PM and remains
  externally driven.
- All execution and mutation use only the authorized sandbox surfaces.
- A report is a claim, not proof. Every completed task needs an observed result.

## Historical planning acceptance (retained verbatim; superseded)

- The tracker exists, is the first edit, and contains objective, problem, scope, constraints,
  tasks A–E, acceptance, checks, route/advice evidence, and status.
- `pm-layer.md` T7 remains unchecked and links this tracker without claiming pilot credit.
- `docs/TODO.md` Q59 is `READY` with the tracker link, preserved prerequisite wording, and the
  unverified-count clarification.
- `ROUTER-LOG.md` has one planning row before `## Usage Notes`, with the tracker, pre-code Task,
  and independent post Task evidence and no fabricated commit or review outcome.
- Exactly four repository paths are changed; `git diff --check` is clean.
- No implementation/test source is modified, and no implementation suite is run.

## Acceptance criteria (current)

- The changed paths are exactly the four metadata paths; the ten source paths, `WORKFLOW.md`, and
  `docs/PLAN.md` are byte-identical to the baseline; `git diff --check` is clean.
- The tracker records the five actual source commits, their line/byte receipts, the four
  owner-relayed approvals, the current pin `28ff3937...`, and labels the old pins, two-commit
  split, `FAIL`, and `PENDING-COMMIT` records as HISTORICAL.
- The current A inventory uses actual `verify-workflow.sh` line ranges and symbols, and separates
  coordinator-generic from orchestrator-only checks.
- The corrected PM contract is recorded: orchestrator alone keeps `general`; PMs dispatch a
  mid-unit tiny fix only to `odd-apply`/`gentle-ai-worker`, never `general`; strict maximum task
  keys; unknown families fail closed.
- All thirteen advisory IDs have explicit dispositions; none becomes a blocker or source fix.
- Activation/deploy is UNVERIFIED, full verifier/live probes are HOST-ONLY and NOT RUN, and no
  Q56 pilot credit is claimed.

## Historical planning delivery (retained verbatim; superseded)

- Strategy: `ask-on-risk`. Forecast: **300–500 implementation authored lines** (forecast, not
  measured), excluding generated files.
- Split into coherent future slices, each under 400 authored lines and 100 KiB, each keeping behavior
  and tests together. Before the running delivery budget crosses about 400 authored lines, resolve
  `stacked-to-main` versus `feature-branch-chain`; there is no pre-authorized exception.

## Delivery (current)

- Strategy: `ask-on-risk`. This final metadata candidate is measured against `70d5bef`; if the
  natural candidate exceeds 400 authored lines / 100 KiB, the PM must obtain a coherent
  split/authorization rather than a size exception.
- Behavior, tests, and the digest pin remain one coherent implementation history, already split
  across five reviewed source commits. This metadata unit adds no standalone test or pin commit.
- The metadata commit is the PM's, after fresh independent verification and post-advice. The
  source is not re-implemented or redeployed here.

## Historical planning checks (retained verbatim; superseded)

### This planning unit (run before finish)

- Documentation consistency assertions for the required sections/tasks/links, Q59 `READY`, T7
  pending, pilot distinction, and no implementation changes.
- `git diff --check`.
- Exactly four changed paths, excluding a pre-existing unrelated untracked bundle.
- Workspace facts: root, branch/HEAD, boundary object type and ancestry.

**Observed results (this refinement, run in the sandbox):**

- Workspace: `git rev-parse --show-toplevel` → `/work` (exit 0); branch `work`; current `HEAD`
  `509e383aa3472e34faff3d9de3b99dfc63f1d30b` (exit 0), whose parent is the briefed input
  `c9c6f02aa50488fae8857d9cace61abbcba3d3d9` (exit 0). The earlier writer's `4951d56` observation
  is superseded for this session. `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422` resolves as a
  `commit` (exit 0) and `git merge-base --is-ancestor deab3b5b... HEAD` exits 0. The host feature
  branch is not a ref in this worker clone; that remains an inferred limitation, not a host-state
  claim.
- Scope: `git diff --name-status c9c6f02aa50488fae8857d9cace61abbcba3d3d9 --` → exactly
  `M ROUTER-LOG.md`, `M docs/TODO.md`, `M odd/tasks/pm-layer.md`, and
  `A odd/tasks/q59-pm-verifier.md` (exit 0). `git diff --name-only -- verify-workflow.sh
  global-config tests scripts WORKFLOW.md` → no output (exit 0), so no implementation source,
  config, test, or workflow file changed. At check time, `git status --short` also showed the
  untracked `.broker-tmp/` check harness and the pre-existing synthetic
  `ses_ea9ed4f02ffe832R6TN3OzuDWs.bundle`; neither was staged and neither is part of the
  candidate. The bundle is not deleted.
- Documentation consistency assertions → `CONSISTENCY_OK`: 15 assertions passed and 20
  mutation-positive controls each failed the same predicate after an actual required clause was
  removed from an in-memory copy (required sections, tasks A–E, one-unit identity, worker/PM
  ownership, future prompt/config/`WORKFLOW.md` guard, `NEEDS_INPUT`, Q04 non-blocking, pre/post
  Task/model evidence, the three cross-links, host-only future checks, pin-last-same-commit, and
  planning-not-pilot).
- `git diff --check` → exit 0, no output (clean).
- The final full-candidate staged receipt (bytes, numstat, and the full new-file patch header) and
  the incremental B→C metrics are measured after this recorded content is final and returned in
  the PM envelope; recording those numbers here would change the measured artifact.

### Future implementation (NOT RUN in this planning unit)

- `bash -n verify-workflow.sh`.
- Focused four existing Python modules listed in task D.
- Full `python3 -m unittest discover -s tests`, comparing observed results with the BRIEF-SUPPLIED
  baseline of 10 node-denied errors and 1 skip. That baseline is supplied, not verified here.
- `bun` routing-guard tests with a genuinely throwaway `HOME`; never the real `HOME`.
- Positive controls must execute assertions; syntax alone is not behavioural proof.
- `sha256sum` pin equality plus the `read_verify_script_pin` regex.
- Full verifier/deploy remains HOST-ONLY and is not run. A source commit is not deployment activation.

## Checks (this metadata unit)

- Real metadata fact assertions over the four paths: five commit SHAs and ancestry, four review
  IDs, group counts 27/8/40/18/10 = 103, the current pin and verifier hash, the thirteen advisory
  IDs/dispositions, the corrected planning scope, and the current status vocabulary, with
  mutation-positive controls (an in-memory removal of a SHA, pin, advisory row, or status clause
  must fail the same predicate).
- `python3 -m unittest tests.test_orchestrator_prompt_source -v` (28 tests; includes the pin
  regex and prompt-source checks).
- `python3 -m unittest tests.test_pm_layer_prompts -v` (13 tests; prints `pm-odd=2968` and
  `pm-systematic=2982` and exercises the PM cap and Tiny-fix needles).
- `sha256sum verify-workflow.sh` equals the recorded pin; `git diff --check`;
  `git diff --name-only 70d5bef -- <ten source paths> WORKFLOW.md docs/PLAN.md` is empty.
- Workspace facts: sandbox root, branch/HEAD, baseline commit and ancestry, and the untracked
  bundle exclusion.

**Observed results (this unit):** 28/28 orchestrator-source tests passed; 13/13 PM-layer prompt
tests passed; the metadata fact checker returned `METADATA_FACTS_OK` with four mutation controls
failing closed; `sha256sum verify-workflow.sh` equals the pin; `git diff --check` is clean; the
source-path diff is empty; `git status --short` shows exactly the four metadata paths plus the
untracked broker bundle. The full 228-test Python suite and the 104 routing-guard suite were NOT
rerun by this metadata unit; their source-time PASS results remain labelled as such. The full
verifier/deploy/live probes are HOST-ONLY and NOT RUN. Config/prompt runtime is not attested.

## Log

- Initial writer: PM-supplied session `ses_ea9fcd77bffepTGGvpGp0Zk4lC` installed the four
  documentation paths; this refinement did not reconstruct that result.
- Refinement writer: delegated sandbox writer for `q59-pm-verifier-plan-u1`. Its session id is
  exposed only in the PM envelope and is not invented here.
- Refinement changes: tracker ownership/scope/post-advice/receipt wording; `pm-layer.md` T7
  post-advice reference; `docs/TODO.md` Q59 post-advice reference; `ROUTER-LOG.md` row wording and
  post Task evidence. The PM owns the commit and post-commit assessment.
- **Source implementation (`q59-pm-verifier-impl-u1`):** A–E source applied and installed; the
  earlier verifier FAILs and advisor NOT READY records were corrected by successive source
  writers. The final source is the five-commit chain above, each source commit owner-reviewed
  APPROVED + ACKNOWLEDGED. Source unchanged by metadata units.
- **M1 metadata:** recorded the five source commits, the four owner-relayed reviews, the current
  pin, the corrected PM contract, and the source-time checks in `pm-layer.md`/TODO/ROUTER-LOG;
  this unit's SHA is `70d5bef...`.
- **M2/final metadata (this unit):** replaced the stale `FAIL`/`PENDING`/two-commit status and old
  pin references with the current source+metadata facts, refreshed the A inventory from the
  installed source, corrected the planning-scope wording (R3-002), recorded all thirteen advisory
  dispositions, and preserved the historical/recovery record by frozen-snapshot reference. Source
  unchanged; no commit, native review, assessment, deploy, or live probe.

## Historical route and review evidence (retained verbatim; superseded)

- Dispatch-supplied route evidence: `workflow-odd-secure` was loaded FIRST, then
  `workflow-route`; this worker did not re-observe the skill calls.
- Class: global tooling change. Route: delegated. Triggers: preparation and multi-file secure
  delegation.
- RDD: PM-supplied observed `enabled`, decided `global`. Last reviewed boundary:
  `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`. Planning input: `c9c6f02`.
- Planning anchor is explicitly `none` and the comparison is skipped; the branch identity was
  previously observed exactly.
- After EVERY PM commit, assess with `host_review_assess` bound to the last boundary and
  `committedOnly=true`. If review is due, stop and return `NEEDS_INPUT`; native review stays with
  the orchestrator only.
- The deterministic Magic Context mirror tool is unimplemented: no mirror write or verification was
  performed, and no mirror body is fetched.

## Route and review evidence (current)

- Dispatch-supplied route evidence: `workflow-odd-secure` was loaded FIRST, then
  `workflow-route`; this worker did not re-observe the skill calls. Class: global tooling change.
- RDD: PM-supplied observed `enabled`, decided `global`; last reviewed source boundary
  `41fbe77a7ba3214c340e610df935ff7fb73b62c0`. The four source reviews above are owner-relayed
  and authority-burned. The M1 metadata assessment was PASSIVE at base `41fbe77` with
  `committedOnly=true`; no metadata review is due.
- Native review remains externally driven. The PM owns every metadata commit and immediate
  post-commit assessment; this worker does not start or relay native review.
- The deterministic Magic Context mirror tool is unimplemented: no mirror write or verification
  was performed, and no mirror body is fetched.

## Advice record (pre-code, advisory only; not approval)

- `advisor-integration-pre` Task `ses_eaa0c1a94ffeaxyFcbfo5hlcON`, configured
  `opencode-go/kimi-k2.7-code` (`global-config/opencode.json:1552`); the same-session report was
  corrected. Model configuration is observed; actual runtime/fallback is not attested.
- Summaries adopted: preserve orchestrator-only exceptions; treat the legacy inventory as
  conditional; require mutation-positive controls and no duplicate checks; prompt-cap authority is
  unresolved; live probes are host-only; split the forecast and pin last.
- Rejected: the advisor's suggested hard Q26/Q04 prerequisites, new `WORKFLOW.md`-anchor scope, and a
  full verifier run inside the sandbox.
- The explorer Task's configured model was unavailable; no result or model is fabricated.
- Writer configured model: `opencode-go/deepseek-v4.1-flash` (`:2350`). Its actual session identity
  and receipt belong to the PM envelope if not exposed here.

## Historical post-code advice (retained verbatim; superseded)

- `advisor-integration-post` Task `ses_ea9f1a0ecffe8aPpAJIGyw2L11`, configured
  `opencode-go/kimi-k2.7-code` (`global-config/opencode.json:1752`; PM-read exact). Actual
  runtime/fallback is not attested.
- **PM-supplied initial verdict and blockers (not independently re-derived here): NOT READY.**
  The blockers were: (1) the planning-unit ownership text banned commit and native review for the
  whole unit although the PM owns the fixed-host commit and post-commit assessment; (2) the future
  A–E scope did not explicitly prohibit prompt and `global-config/opencode.json` edits or name the
  `NEEDS_INPUT` route for an exact missing clause or grant; (3) the independent post-advice record
  was still a pending placeholder; (4) the staged reviewability receipt measured only the new
  tracker file, not the full four-path candidate.
- **Resolutions in this refinement:** the ownership text now bans only worker commit/native review
  and assigns the fixed-host commit plus post-commit assessment to the PM, with no PM-run native
  review; this unit and A–E prohibit prompt/config edits, require `NEEDS_INPUT` for an exact
  missing clause or grant, forbid `WORKFLOW.md` edits, and keep Q04 non-blocking; this Task/model
  record replaces the placeholder; and the final staged receipt covers all four paths against the
  host input `c9c6f02aa50488fae8857d9cace61abbcba3d3d9`, including the full new-file patch header.
  The initial 19,904-byte partial new-file measurement and the broker's 20,292-byte / 224-line
  initial patch are superseded by that full receipt; incremental B→C metrics are reported
  separately.
- **Final confirmation:** the PM envelope records the final post-advice confirmation after the
  PM's own verification. This tracker does not claim that final verdict or any native-review
  result.

## Post-code advice records (current)

- Source post advisors: `ses_ea4eb1771ffeoIegz67GBAKUno` (after S2b) READY;
  `ses_ea4d23e17ffe20TrkqlZ7bsVR0` (after S2c) READY; final
  `ses_ea4ab17c3ffeRb02HFxdetDKAt` READY. Earlier NOT READY records are HISTORICAL and were
  superseded by the correction/source commits.
- The PM envelope records the final post-advice confirmation after its own independent
  verification. This tracker does not fabricate a verdict or a native-review result.

## Status and next step

Source implementation is **COMPLETE, SOURCE-COMMITTED, and SOURCE-ACKNOWLEDGED** in the five
commits above; metadata evidence is **COMPLETE in this record**. Activation/deploy remains
**UNVERIFIED**: no verifier mirror, restart, full verifier, deploy, or live probe ran, and
config/prompt runtime is not attested. Q59 remains outside the Q56 pilot and earns no pilot
credit. The PM may commit this metadata candidate after fresh independent verification and
post-advice and record the actual metadata SHA in its envelope; no metadata SHA is invented here.
