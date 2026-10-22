# Q87 — Finite verification budget by task type

Feature: replace open-ended pre/post advice and verifier loops with a finite budget mapped to the
six existing route classes. Task ID `q87-verification-budget`. Class: global-tooling-change. Route:
delegated (`workflow-odd-secure`). Units: `q87-verification-budget-plan-u1` (complete),
`q87-verification-budget-src-u1` (U2a, source committed), `q87-verification-budget-src-u2` (U2b,
source committed `5a8a8ab`; deployment/live activation not performed). Delivery strategy:
`ask-on-risk`.

## Objective

Define a finite ceiling of pre-code advice, post-code checks and independent verification by task
type, and stop treating "repeat as needed" as an unlimited refinement budget. The planning unit
recorded the plan only. U2a implemented the finite policy in source and is committed; U2b is now
source-committed at `5a8a8ab`, so the source scope is complete. Deployment and live activation were
not performed and remain separate work.

## Problem and evidence

- Observed (owner directive, 2026-10-21): work, verification and advice are finite by task type,
  never unlimited. Simple documentation gets ZERO advisor and `gentle-ai-verify` Tasks; the PM
  checks and an orchestrator independently reads back.
- Observed (`odd/tasks/q59-pm-verifier.md:288-295,415-459`): several correction/test cycles preceded
  the five committed source commits; two were real source defects (a JS `ReferenceError`, a stale PM
  prompt), recorded as replay evidence.
- Observed (`WORKFLOW.md:65`; `docs/specs/pm-handoff.md:30`): the current "Repeat as needed"
  refinement wording carries no ceiling.
- Inferred: the loops caught real defects, so the fix is a bounded budget, not zero checks. This
  unit does NOT assert that every cycle was needless (not proven).

## Final plan (authoritative for the future source unit; no edits here)

1. **Docs boundary by the actual unit diff, not the feature class.** Allowlist for the simple-docs
   exception: `odd/tasks/**` and `odd/advice/**` (state/planning/evidence only), `ROUTER-LOG.md`,
   `CLAIM-RETRACTIONS.md`, `docs/TODO.md`, `docs/TODO-HISTORY.md`, and the non-Constraints/
   non-decisions portions of `docs/PLAN.md`. A planning tracker may state FUTURE acceptance criteria
   without changing an existing executable acceptance contract; changing existing normative
   specs/constraints/acceptance is NOT docs. Any test/verifier reader disqualifies; uncertainty
   fails closed. `WORKFLOW.md`, `AGENTS.md`, `docs/specs/**`, `global-config/**`, ANCHOR_MANIFEST
   files and command-changing docs are never simple docs. No automatic source-comment exemption. A
   native medium/high raise moves a unit up, never down.
2. **Finite matrix over the six existing route classes** (no new classes): docs/planning/closure
   metadata and genuinely passive tiny = 0 pre-advice, 0 post-advice, 0 `gentle-ai-verify` (PM
   factual/structural checks plus an orchestrator independent readback). Medium ordinary behaviour/
   test-only/command docs = one pre-advice phase and one post-code check (`ce:review` substitutes the
   advisor); the verifier runs only on an explicit exception (security boundary, uncertainty, live
   fallback/independence, or an explicitly reduced small-model profile). High normative contract/
   config/security/enforcement tests/dependency or plugin pins = one pre phase, one post phase, one
   independent verifier. Generated inherits source. A conservative high reading of dependency/pin
   work resolves the reports' medium-vs-high conflict. The named `ce:review` baseline reviewers stay
   intact; counts are check phases, not numbers of baseline reviewers.
3. **Explicit PROPOSED policy decision:** the configured `opencode-go/deepseek-v4.1-flash` default
   writer is NOT treated as a small/reduced profile merely because of the "flash" name; no
   authoritative small-model label was found in research. The medium verifier exception must name a
   reduced profile/reason, not fire on all DeepSeek work. This is a policy decision to adopt, not a
   discovered upstream fact. The PM Sol self-check is independent of a DeepSeek docs writer;
   independent orchestrator readback remains required and no extra verifier is added.
4. **Per unit maximum: one initial writer plus ONE fresh correction writer across all pre-commit
   post-code gates** (including `ce:review` and external advice). Batch all applicable checks on the
   SAME candidate before correction; use finding IDs; issue one consolidated fix brief; install
   first, then refine on the installed base; run one targeted recheck of the IDs plus affected
   regression controls. The same unresolved blocker, or a new blocker during recheck, cannot buy
   another round: advisory/follow-up for non-blockers, `NEEDS_INPUT` for explicit human
   authorization, `BLOCKED` for missing authority/environment/evidence. A human may explicitly
   authorize a bounded exception with reason, scope and a new limit recorded; metadata or a new task
   ID never silently resets the counter. Record `correction_rounds_used` `0|1` in
   `pm-unit-result/v1`; record any override separately.
5. **`ce:review` is a post-code check, not an extra cycle;** its findings join the batch and it is
   not fully rerun after a fix. When the external post-code-pair lane is active it is one
   consolidated check whose internal and external same-candidate findings merge; both pair rules
   exclude docs. Manual advisor reports are not that lane. Native review stays a separate
   one-scoped-fix/targeted-validator step that closes it; no PM advisor/verifier loops run on a
   native correction. A tiny fix escalated after commit gets the applicable post-code check on the
   committed candidate; any one correction is a new commit, never rewritten history.
6. **Docs evidence:** exact changed-path list and allowlist rationale, stats, `git diff --check`,
   branch/SHA and any asserted references/ancestry, the PM check, the orchestrator independent
   readback, and `advice_record` status `not-applicable` with a reason; no runtime tests for true
   docs. Any test reader makes the unit normative with its applicable deterministic execution checks.
7. **Same future delivery must align:** `WORKFLOW.md:65,158,461/475,524` and the external-pair
   clauses; `docs/specs/pm-handoff.md:20,23,30,36,123` and its envelope; both route SKILLs;
   `overlay.md:196-200`; and the `advisor-gemini-post` committed-vs-precommit drift at
   `global-config/opencode.json:2008` (fold the relevant Q84 sequencing fix into Q87, keeping
   unrelated Q84 scope intact); plus the relevant Q59 ACTIVE metadata instruction, without rewriting
   historical failure reports. Add a dated owner decision. No policy edits in this unit.
8. **Overlay is included; Q88 folds into Q87, not deferred.** Exact future sequence: update the
   policy/tests and the overlay; run
   `python3 global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py --base global-config/prompts/gentle-orchestrator/base.md --overlay global-config/prompts/gentle-orchestrator/overlay.md`;
   capture stdout through authorized worker process/file APIs (no shell redirection/heredoc) and
   update the embedded `gentle-orchestrator` prompt in `global-config/opencode.json`; hash the
   assembled prompt into `CURRENT_PROMPT_SHA256` in `tests/test_orchestrator_prompt_source.py` and
   `global-config/prompts/gentle-orchestrator/normative-ledger.md`; run the assembler
   equality/mutation controls and `python3 -m unittest discover -s tests -p test_pm_handoff_spec.py`,
   then the same runner for `test_orchestrator_prompt_source.py`, `test_anchor_manifest.py`,
   `test_review_cadence.py`, `test_tiny_fix_route.py`. Verify the actual assembler location before
   documenting if it differs. No new `verify-workflow.sh` check or digest change. Future source/
   config consumer verification and deploy are HOST-ONLY through the orchestrator; the owner restart
   is separate to this unit.
9. **Forecast and delivery:** source is forecast at 250-450 authored lines (estimate; recompute the
   staged receipt). The embedded prompt is one very long line and may exceed authored bytes if not
   objectively generated: give it a separate generated receipt and never hide authored advisor-prompt
   changes as generated. Split into coherent units or record an approved size exception before
   commit, preserving source-plus-generated integrity. Default strategy `ask-on-risk`; no push/PR
   authority. Keep this tracker compact with stable finding IDs and no append-only superseded prose.
10. **Writer-tier dispatch rule.** Owner rule 2026-10-21: when the writer is
    `gentle-ai-worker-local`, dispatch exactly ONE file change per writer Task; do not batch
    multiple files. Cloud writers may batch a coherent multi-file unit. The future source unit
    records this rule in `WORKFLOW.md` and `docs/specs/pm-handoff.md`.

## Scope

- **In:** the plan above, recorded in this tracker; the advice record
  `odd/advice/verification-budget.md`; the `docs/TODO.md` queue entry; one `ROUTER-LOG.md` row.
- **Out (future source unit):** all `WORKFLOW.md`, `docs/specs/**`, `global-config/**`, test,
  verifier and prompt edits; the owner restart and deploy.
- **Future delivery (U2 policy, not enacted here):** record the owner's writer-tier rule — local
  writers take exactly ONE file change per Task; cloud writers may batch a coherent multi-file
  unit — in `WORKFLOW.md` and `docs/specs/pm-handoff.md`.

## Constraints and non-goals

- Planning-only: no source, test, verifier, config, prompt or pin edit; no commit, deploy, branch
  switch, push or PR. These constraints applied to the planning unit; U2a and U2b source are
  committed, and this metadata unit edits only the three allowlisted paths.
- Artifacts are English, compact and factual. Observations, inferences and proposed decisions are
  labelled.
- Never claim a check, deploy or live behaviour not observed.

## Acceptance criteria (future source implementation)

- **Scope note:** these are full-feature acceptance criteria. U2a and U2b source are complete and
  committed; deployment and live activation were not performed, so full delivery is not claimed.
- `WORKFLOW.md`, `docs/specs/pm-handoff.md`, both route SKILLs and `overlay.md` state the finite
  matrix and the one-correction ceiling consistently; the six route classes are unchanged.
- The docs allowlist is explicit and fails closed; a test/verifier reader reclassifies a unit as
  normative with its execution checks.
- The regeneration chain (items 7-8) is atomic and its tests pass; `correction_rounds_used` is
  recorded with no silent reset.
- No new `verify-workflow.sh` check or digest change.
- Future U2 records the local-writer one-file dispatch rule (cloud writers may batch a coherent
  multi-file unit) in `WORKFLOW.md` and `docs/specs/pm-handoff.md`; this planning unit does not
  enact it.

## Tasks

- `T0` (this unit, `q87-verification-budget-plan-u1`): create the tracker and advice record; add the
  TODO and ROUTER-LOG entries. Planning only.
- `T1` (`q87-verification-budget-src-u1`, U2a — COMPLETE, source committed `30f7665`): finite
  matrix and docs boundary across `WORKFLOW.md`, `docs/specs/pm-handoff.md`, both route SKILLs, and
  the tests. Owner advanced the source reviewed boundary to `30f7665` without native review.
- `T2` (`q87-verification-budget-src-u2`, U2b — SOURCE COMPLETE, committed `5a8a8ab`): aligned
  `overlay.md`, regenerated the embedded prompt, and updated the digest/ledger atomically (folds
  Q88); added the post-code static-diagnostic-order rule to the
  `WORKFLOW.md`/`docs/specs/pm-handoff.md` clause and overlay wording; kept the existing scope with
  no new queue ID.
- `T3` (folds into U2b — SOURCE COMPLETE in `5a8a8ab`): the Q84 `advisor-gemini-post` sequencing
  drift was folded into the aligned surfaces; unrelated Q84 scope was left unchanged.

## U2b source unit evidence (source committed)

- Unit: `q87-verification-budget-src-u2` (U2b), 2026-10-22. Class:
  `global-tooling-change`. Route: delegated. Triggers: preparation, coherent multi-file cloud
  unit, secure no-inline mutation, assembler/prompt-hash regeneration. Specialist: cloud
  `odd-apply`.
- Pre-code advice: Task `ses_e9f3f0e5fffe6yN5JTeVG8UUmc`, configured
  `opencode-go/kimi-k2.7-code`; runtime fallback was not independently attested. Findings treated
  as evidence, not approval: H01 put static diagnostics first in every required surface; H02 fix
  Gemini pre-commit sequencing narrowly (not only the question while leaving the committed-candidate
  phrase); H03 keep assembly/hash/ledger atomic; H04 add mutation-positive static-order tests; H05
  separate authored and generated accounting.
- Read-only research: Task `ses_e9f3f0e58ffeKujFP1tOiRnbeS` observed the assembler newline is
  intentional, the overlay heading after Native Checking Contract must be preserved, and the
  existing tiny-fix/pm-readback anchor interiors stay untouched; no `.codegraph` index was present,
  so AFT was the fallback. Its "no SKILL edit needed" conclusion is rejected because this U2b scope
  explicitly requires the static first-pass rule in both route SKILLs.

### U2b source closure (observed)

- Source commit `5a8a8ab191bb5fcfcccdf810f1d46e003fc52ac5` on the host branch
  `chore/q72-t1b-tiny-fix-contract`: 11 paths, +149/-7 = 156 total changed lines. The generated
  embedded-prompt hunk accounts for 2 of those lines and about 118315 patch bytes; the authored
  receipt is 154 authored changed lines and 37667 authored patch bytes (total raw patch 155982
  bytes; source-worker/PM-attributed, not re-measured here). The `advisor-gemini-post` prompt text
  in the same file is authored, not generated. `verify-workflow.sh` and its pin are unchanged.
- Paths: `WORKFLOW.md`, `docs/specs/pm-handoff.md`, `global-config/opencode.json`,
  `global-config/prompts/gentle-orchestrator/normative-ledger.md`,
  `global-config/prompts/gentle-orchestrator/overlay.md`,
  `global-config/skills/workflow-odd-secure/SKILL.md`,
  `global-config/skills/workflow-systematic/SKILL.md`, `odd/tasks/verification-budget.md`,
  `tests/test_gemini_advisor_route.py`, `tests/test_orchestrator_prompt_source.py`,
  `tests/test_pm_handoff_spec.py`. This metadata unit edits only the tracker, `docs/TODO.md` and
  `ROUTER-LOG.md`.
- Source Git readback (observed in the sandbox): commit parent `415009c...`; commit tree
  `187bdb830aed34ef2d10f9d78f18cfc89e5e0fd8` equals the verified corrected candidate tree; the
  sandbox baseline `ec58ccd` has that same tree and parent `5a8a8ab`; no branch switch. Exactly one
  commit exists in `415009c..5a8a8ab`, so there is no duplicate correction commit. The committed
  diffs contain F01's explicit `ModuleSpec`/loader guards and F02's explicit regex-null guards. The
  PM-reported `host_review_materialize` plus `diff_read` materialization confirmed the same 11-path
  inventory and both guards.
- Initial installed source writer `ses_e9f3b15cbffeNlUniEM1N4kuPG`, result
  `de14c726725c275d6aaff096f88b14c402e35c1b`. Its earlier stalled/empty response was later
  recovered; this is not a terminal failure. The duplicate alternate `gentle-ai-worker`
  `ses_e9f32dba6ffe0eTGBkqWZLXKZZ` (result `ca25127f...`) returned S16 and was EXCLUDED, not
  installed; physical deletion was not performed (do not read that as a tool discard). No repeat
  pre-advice phase: the H01-H05 pre-advice Task `ses_e9f3f0e5fffe6yN5JTeVG8UUmc` was configured
  `opencode-go/kimi-k2.7-code`, runtime not independently attested.
- First post-code phase ran on the SAME initial installed source before correction: advisor
  `advisor-integration-post` Task `ses_e9f2817ffffeyoOBPtbPOZs0wb` (configured Kimi; runtime not
  attested) and `gentle-ai-verify` Task `ses_e9f2817eaffejK2wrqH9yITtYw` (reported Sol). PM
  `aft_inspect` reported 3/3 changed test files, 6 errors, 0 warnings. Independent executed
  results: focused 7 modules 115 OK; full Python discovery 244 OK; routing-guard 104 pass / 0 fail
  (254 assertions, throwaway HOME); `bash -n`, JSON, assembler equality/digest and ledger, 39
  anchors / 99 tokens, `git diff --check` and `py_compile` passed. No full host verifier and no live
  activation. Generated prompt 59950 bytes / 417 lines, SHA-256
  `521796dfbfc71a125e49b8bbd8127de7197a491b12a0ea8bd942c29de64a046b`;
  `tests/test_pm_layer_prompts.py` was unchanged and its existing module executed.
- `correction_rounds_used: 1`. The one consolidated correction Task
  `ses_e9f1cfc0effeLmcawSpnoEZUyG` applied result
  `65270291bf1b7704a378db199ecce87b0c4e57fb`: F01 explicit `ModuleSpec`/loader guards in
  `tests/test_gemini_advisor_route.py`; F02 explicit regex-null guards in
  `tests/test_orchestrator_prompt_source.py`; exactly 2 files, +8/-2 = 10 lines, 2061 bytes. The
  owner authorized only these two files, and the corrected tree replaced the frozen initial
  candidate for equality purposes. After apply, the same independent verifier session ran
  `python3 -m unittest tests.test_gemini_advisor_route tests.test_orchestrator_prompt_source -v`
  -> 49 tests OK; PM `aft_inspect` authoritative 2/2 files, 0 errors, 0 warnings (overall PARTIAL
  for unsupported Python dead-code/incomplete complexity, not a diagnostic gap). No full suite,
  advisor or verifier rerun after correction.
- Source assessment (observed, exact): `host_review_assess(baseRef
  415009c65be9a0fb47072ae654dda835c68a3719, committedOnly true)` returned
  `gentle-ai.review-assessment/v1`, risk `medium`, reason `executable_change` on `WORKFLOW.md`,
  `changed_paths: 11`, `changed_lines: 156`, candidate `base-diff`, `consumed: false`,
  `review_due: false`, `review_due_reason: under_budget`. Record this as medium / under budget,
  NOT as the expected high, and NOT as native approval. RDD is on globally; no native review or
  acknowledgement occurred, and the reviewed boundary remains `415009c...`. The metadata
  assessment belongs to the PM envelope; the metadata commit SHA is a PENDING-COMMIT placeholder
  here and is not invented.
- Source clears for closure because no review is due. The future `ce:review` retrospective remains
  the earlier owner disposition; no execution is claimed here. Source-delivered is distinct from
  deploy/live activation, which were not performed.
- Route evidence (attributed): `workflow-odd-secure` was loaded first and the route validated
  `global-tooling-change`. The unit-start anchor was historical at 265 lines with an exact last-line
  match at branch head `415009c`; after the authorized edits there was no re-anchor or reset, and
  this record does not claim the working text equals the committed blob through the anchor. The
  Magic Context mirror tool is unimplemented; no mirror body was accessed and no readback is
  fabricated.
- Metadata checks for this docs-only unit: exact changed paths/stat, `git diff --check`, compact
  authored-line/byte stats within the 400-line and 100 KiB caps, and asserted revision/tree/
  ancestry references; no runtime tests, advisor or verifier. A bounded literal search of `tests/`
  and `verify-workflow.sh` for the three paths and `verification-budget` found only
  allowlist/contract string references (the probe matched those), not a reader of the metadata
  contents; the simple-docs classification therefore holds with no observed test-reader risk.

## U2a source unit evidence (source committed)

- Unit: `q87-verification-budget-src-u1` (U2a), 2026-10-21. Class:
  `global-tooling-change`. Route: delegated. `workflow-odd-secure` was loaded first, then
  `workflow-route`, by the PM; this worker did not re-observe those skill calls. Triggers:
  preparation, multiple non-trivial files, secure delegated mutation.
- Scope split (owner override of the full-feature delivery): U2a changes only the finite policy,
  docs allowlist, one-correction cap, local-writer rule, envelope, route SKILLs and tests. U2b was
  EXCLUDED from this unit and was pending then: `overlay.md`, assembled `global-config/opencode.json`,
  prompt regeneration, `CURRENT_PROMPT_SHA256`, normative ledger, and `advisor-gemini-post` prompt.
  U2a therefore does NOT establish full source/prompt equality.
- Pre-code advice: `advisor-integration-pre` Task `ses_e9f8386eaffeAOIdz1LMHjLupw`, configured
  `opencode-go/kimi-k2.7-code`; runtime fallback was not independently attested. Findings treated
  as evidence, not approval: B1 split the tracker feature acceptance from the U2a scope; B2 replace
  the open-ended refinement loop; B3 add the finite matrix; B4 add the correction counter to the
  result envelope; B5 add mutation-positive controls; B6 preserve the existing anchor and tiny-fix
  contracts. The advisor's suggestion of a separate verifier-anchor commit is not adopted because
  it could break anchor/token integrity; anchors, source and tests stay together if a verifier edit
  proves necessary.
- PM readback (historical): `docs/TODO.md` Q87 separates policy/tests from
  overlay/regeneration; the acceptance criteria in this tracker are FULL-FEATURE acceptance. U2a was
  PARTIAL at that readback; its source is now committed and U2b was pending then (now source-
  complete at `5a8a8ab`); no claim of full alignment.
- Verification plan: tests first, then policy text, same final candidate. No new anchors or verifier
  checks; verifier/pin edits only if an existing row requires textual change.
- Owner override (2026-10-21, English, factual): a new Pyright diagnostic
  `tests/test_pm_handoff_spec.py:359:84` (`"group" is not a known attribute of "None"`) after the one
  correction round authorized one null-check in one file; new limit: one cloud `odd-apply` writer
  plus targeted module test/scoped diagnostics only, no full advice/verifier cycle, no U2b;
  `correction_rounds_used` stays `1`, recorded separately with no silent reset; used exactly one
  writer `ses_e9f597b78ffe3ckTuejCTsijRt`. Observed (writer/PM-attributed, not re-run here):
  `python3 -m unittest tests.test_pm_handoff_spec -v` → 25 tests OK; result one test path `+3/-1`,
  patch 857 bytes; PM `aft_inspect` after apply FRESH authoritative `1/1`, 0 errors, 0 warnings.
  The earlier consolidated correction targeted recheck closed `F01`/`Q87-V01`/`Q87-V02`; this
  null-check exception closed only the new Pyright `359:84` error, not those policy findings.

### U2a source closure (observed)

- Source commit `30f76652d6fcdfe97999ffd87bff643cb8e964df` on the host feature branch
  `chore/q72-t1b-tiny-fix-contract`: 7 paths, +370/−19 = 389 authored lines, 67564 raw patch
  bytes. Paths: `WORKFLOW.md`, `docs/specs/pm-handoff.md`,
  `global-config/skills/workflow-odd-secure/SKILL.md`,
  `global-config/skills/workflow-systematic/SKILL.md`, `odd/tasks/q59-pm-verifier.md`,
  `odd/tasks/verification-budget.md`, `tests/test_pm_handoff_spec.py`.
- Owner decision (2026-10-21): ADVANCE the source reviewed boundary to `30f7665`. This is an owner
  disposition, not native review or acknowledgement; no native review occurred.
- Assessment returned medium / `under_budget` / `consumed=false` / `review_due=false`. It was NOT
  passive, approved or high, and is not native approval.
- End-of-ODD `ce:review` is pending: future retrospective coverage of Q87 slices by owner
  disposition.
- Dispatch/evidence record (compact): pre advisor `ses_e9f8386eaffeAOIdz1LMHjLupw` (configured
  `kimi-k2.7-code`; runtime not independently attested); post advisor
  `ses_e9f757002ffeBenXB1H54KGUNZ` (reported configured/runtime `opencode-go/kimi-k2.7-code`);
  independent verifier `ses_e9f75700cffewgIuFL1ZkIOqYN` (configured/runtime
  `openai/gpt-6.1-sol`); initial writer `ses_e9f7f682bffeg7tiHufkH4L384`; one-correction writer
  `ses_e9f6e808dffe13j4plhKMTDyHj`; exception writer `ses_e9f597b78ffe3ckTuejCTsijRt`.
- Execution evidence (writer/PM-attributed; no new executions in this metadata unit): correction
  writer full Python 240 OK and routing 104 pass; independent verifier initial full Python 239 and
  routing 104, corrected targeted 52; exception exact
  `python3 -m unittest tests.test_pm_handoff_spec -v` → 25 OK; PM `aft_inspect` after the exception
  FRESH authoritative `1/1`, 0 errors, 0 warnings. Do not claim all full suites reran independently
  after the exception.
- Process lesson (owner, 2026-10-21): `aft_inspect` and applicable static diagnostics MUST join the
  FIRST post-code verification pass on the INITIAL candidate, BEFORE the single correction.
  Deferring them until after correction was a PROCESS DEFECT and necessitated the exception. This is
  recorded as a lesson for U2b; it was later implemented in source at `5a8a8ab`. No normative
  `WORKFLOW.md`, `docs/specs/pm-handoff.md` or overlay edit was made in the U2a unit.
- Scope state at U2a closure: U2a was complete only and U2b was then pending with the
  post-code static-diagnostic-order clause in `WORKFLOW.md` and `docs/specs/pm-handoff.md` and
  matching overlay wording, alongside `overlay.md`, assembled `global-config/opencode.json`,
  `advisor-gemini-post` sequencing drift, prompt assembly, `CURRENT_PROMPT_SHA256`, hashes and the
  normative ledger. No separate queue ID was created. U2b is now source-complete at `5a8a8ab` (see
  the U2b closure); no live activation is claimed.

## Checks (this planning unit)

- `git status`/branch/baseline and changed-path inventory (sandbox).
- `git diff --check`; exact changed paths and stat; boundary resolution equals the expected base.
- Staged reviewability receipt: authored additions plus deletions, raw patch bytes, generated/binary
  paths.
- No runtime tests, advisor Tasks or verifier Tasks are required for planning-only artifacts.

## Advice reference

- `odd/advice/verification-budget.md`: two external manual reports (Claude Code/Anthropic;
  Antigravity/Gemini/Google), 2026-10-21, `selection.rule: external-manual`; the automated external
  lane is PLANNED. Reports are evidence, not approval.

## Route and trigger evidence

- Route: delegated. Specialist for this correction: cloud `odd-apply` (session
  `ses_e9faeabf6ffePAqD0AFjm2mT6k`). Triggers fired: preparation, two-file/four-path planning,
  secure no-inline-mutation.
- The host-retained U1 plan/advice/TODO text is preserved; this correction does not claim that
  `odd-apply` authored the original plan.
- The first cloud dispatch was malformed. The later cloud `odd-apply` session
  `ses_ea056c221ffeWZbhO5QyOZN5J6` failed with `fallback_chain_exhausted` (fallback log 3967–3968).
- The local `gentle-ai-worker-local` session `ses_ea04ab2d1ffeApUt5iTA2xDgqv` completed retained
  211-authored-line/27,772-byte text after stalls (log 3999–4000); it was not installed because the
  host already held the retained text.
- This cloud `odd-apply` Task applies only the authorized correction. Researcher
  `ses_ea061f549ffeaFsPWPWjWp7Pua` completed before dispatch. No plan commit hash is claimed. The
  present metadata Task edits only this tracker, `docs/TODO.md` and `ROUTER-LOG.md`.

## Next step

- PM metadata closure: staged receipt, host commit of the three authorized metadata paths (this
  tracker, `docs/TODO.md`, `ROUTER-LOG.md`), and result-envelope assessment; the metadata commit SHA
  belongs to the PM envelope, not this worker. U2b source is complete; deployment and live
  activation remain separate and were not performed. The Magic Context mirror tool is unimplemented;
  no mirror body was accessed and no readback is fabricated.
