# Q98 — Coordinator selection: the orchestrator must use the PM layer

## Identity and authority

Unit: `q98-coordinator-selection-u1`; stable task: `T1`; branch: `chore/coordinator-selection`.
Class: global tooling change; risk: high normative policy/config and enforcement-test readers.
Route: `workflow-odd-secure`; RDD enabled/global (PM-supplied evidence).
Input HEAD: `0e906e91ec0d626dc8eb3fc1dba407c87043e62b` (PM-supplied).
Last reviewed boundary: `1adba52b1c6bdfaaa7b96fd69f15c1489a86615` (PM-supplied).
Owner decision: 2026-11-01, automatic coordinator selection for substantial units.

Planner-finalised contract: the PM supplies suggestions as messages; the Planner finalises the draft, selects advice and owns both technical gates. This corrects the draft's assignment of Planner duties to the PM. Implementation is held for the explicit scope decisions below. No task is ticked and no delivery/deployment is approved.

## Problem and requirements

Observed by Planner: the overlay's PM brief at `global-config/prompts/gentle-orchestrator/overlay.md:117-123` is conditional on delegation. `WORKFLOW.md:75,139-140` defines substantial work as at least two meaningful implementation steps or progress worth recovering. The owner requires an automatic selection rule, not PM-on-request. The draft's prior-execution/deployment-age claims are inherited session reports, not independently established here.

- **S1:** substantial ODD units select `pm-odd`; substantial Systematic units select `pm-systematic`; tiny fixes stay direct delegated-writer dispatches; read-only requests start no coordinator. Selection follows task class and the existing substantial-work test, never a user request for a PM.
- **S2:** put the same canonical rule once in the overlay and WORKFLOW, then regenerate the embedded orchestrator prompt with the existing assembler.
- **S3:** retain embedded-prompt SHA/equality checks; assert the rule exactly once on all four surfaces and prove missing/duplicate rejection. The draft's conditional anchor-token-row requirement needs the explicit disposition below.
- **S4:** no changes to PM/Planner contracts, `pm-unit-brief/v1`, permissions, verifier semantics, tiny-fix writer mapping, route skills, base prompt or assembler code. No prompt externalisation or unrelated cleanup.

## Blocking decisions before implementation

1. **LEDGER-PATH:** observed `tests/test_orchestrator_prompt_source.py:833-835` requires `CURRENT_PROMPT_SHA256` in `global-config/prompts/gentle-orchestrator/normative-ledger.md`. The ledger at lines 3-8 describes the current prompt, citing the old SHA, 419 lines and 76 candidate sentences. This path is not allowlisted. Inferred: changing the prompt and its SHA introduces a new ledger-test failure unless the ledger changes. Request explicit owner permission to add this one path, bounded to actual regenerated SHA/line count, accurate candidate/classification counts, new-rule classification/provenance and necessary explanatory references. The new rule contains 'never' and falls within ledger scope. Verify actual counts; do not hardcode advisor estimates. Do not weaken/skip/dynamically compute away/decouple the existing ledger pin to evade scope.
2. **ANCHOR-DISPOSITION:** observed `tests/test_anchor_manifest.py` reads token tables through `verifier_text()`; adding an actual `ANCHOR_TOKENS` row requires out-of-scope verifier source. Request explicit acceptance that S3 here is satisfied by exact-once rule assertions plus the existing prompt SHA/equality chain, with no token-table addition and no change to `tests/test_anchor_manifest.py`. If a token row remains required, stop for a bounded scope/pin decision; never silently expand verifier scope.
3. **ADVICE-ARTIFACT:** observed `WORKFLOW.md:629-637` requires `odd/advice/<change>.md` as well as tracker advice evidence. `odd/advice/q98-coordinator-selection.md` is not allowlisted. Request bounded permission for that record, or explicit owner disposition. This tracker records RAW response references but does not claim the separate advice file exists. Planner dispatches no writer.

These are requests, not authority grants. PM relays explicit decisions and returns to this Planner for Gate 1 reconsideration before implementation.

## Allowed edit surfaces — unchanged pending approval

1. `WORKFLOW.md`
2. `global-config/prompts/gentle-orchestrator/overlay.md`
3. `global-config/opencode.json`
4. `tests/test_orchestrator_prompt_source.py`
5. `tests/test_anchor_manifest.py` (conditional; do not edit merely because allowlisted)
6. `ROUTER-LOG.md`
7. `odd/tasks/q98-coordinator-selection.md`

## Intended design

Use this byte-identical, single-physical-line paragraph once in WORKFLOW's existing Classification and Route Selection Rules and once in the overlay's existing `user:workflow-routing` block:

> Coordinator selection is automatic: dispatch substantial ODD units to `pm-odd` and substantial Systematic units to `pm-systematic`; tiny fixes stay direct delegated-writer dispatches with no PM, and read-only requests start no coordinator; select by task class and the existing substantial-work test, never by whether the user asks for a PM.

Preserve headings, anchor markers, SECURE IDs and replace/remove hashes. Add no redundant substantial-definition sentence; existing definitions remain authoritative.

Interpretation: this selects the top-level coordinator at orchestrator route entry AFTER route classification, not a replacement for the selected route's skills/specialists. The chosen ODD/Systematic adapter determines the PM counterpart. Existing PM-dispatched tiny-fix shapes remain supported when a PM is already the dispatcher; the new rule starts no PM for a top-level tiny fix and changes no writer or closure procedure. Read-only starts no new work-unit coordinator; the running orchestrator can still answer. If the owner rejects this interpretation, stop rather than modify those contracts.

Observed: assembler `main` emits stdout with a trailing newline; no config-write mode exists. Generate bytes only with the assembler. The worker uses sandbox file edits to replace just the existing JSON prompt value with the JSON-encoded assembler stdout string. Encoding that one string is permitted; whole-config reserialization is not. Require byte prefix/suffix identity outside that value span plus parsed nonprompt-tree equality. Preserve the test constant's double-quoted lowercase 64-hex assignment format.

## Tasks — one coherent implementation unit

Original IDs remain pending. T2/T3 are T1 acceptance/test/log substeps, not separate implementation deliveries or deployments. Necessary post-commit metadata closure remains the existing PM procedure.

- [ ] **T1 (S1-S3):** after scope decisions and Gate 1 PASS, implement policy, overlay, generated embedded prompt and required companion pins within explicitly approved paths.
- [ ] **T2 (S3; T1 acceptance):** extend `tests/test_orchestrator_prompt_source.py` test-first with exact-once and missing/duplicate controls, preserve existing pin checks and report bounded prompt delta.
- [ ] **T3 (T1 evidence):** record ROUTER-LOG row and closure evidence at the correct phase; commit fields stay pending until known; no completion before Gate 2/commit/required review evidence.

## Execution and verification

1. **Baseline before edits:** authorized worker runs starting assembler/embedded/SHA/ledger pin tests and records digest/bytes/lines. Stop for pre-existing pin drift. Capture full-suite failure/error identities and reasons on the unmodified candidate in the same environment. The supplied baseline of 22 failures/28 errors attributed to missing sqlite3/denied node is PM-reported, not independently reproduced. Record actual totals, IDs, runtime/environment and attribution; never assume all failures share those causes.
2. **Observed RED:** add the new checker/test before policy/prompt edits and execute it. Record actual missing-rule failure text and failing surfaces. Syntax/import/environment errors do not prove the required RED.
3. **Coverage:** assert complete rule count equals one in WORKFLOW, overlay, real assembled stdout and decoded embedded prompt. Pristine control passes; removal gives count 0 and named missing-surface diagnostic; duplication gives count 2 and duplicate diagnostic. Assert every mutation changes its input. Full-sentence checking also rejects clause corruption. Count decoded prompt text, not escaped JSON lines.
4. **Generation/locality:** add only the approved paragraph to each source, execute existing assembler, splice the embedded string, update current SHA and explicitly approved companion ledger data. No formatter, `json.tool` write mode, handwritten generated prompt or full-config reserialization. Assemble twice and require byte identity; require embedded==stdout and digest==pin. Compare against captured unit-start bytes: only approved rule insertion plus separating whitespace; report SHA/UTF-8 bytes/physical lines and deltas. Config `git diff --numstat` must show exactly 1 added/1 removed physical prompt line. Verify outside-value byte prefix/suffix and decoded nonprompt-tree identity.
5. **Tests:** focused `python3 -m unittest tests.test_orchestrator_prompt_source tests.test_anchor_manifest -v`, then `python3 -m unittest discover -s tests`. Compare failure-ID-and-reason sets, not totals alone, against observed pre-edit baseline. New/unexplained failures block acceptance. Individually attribute environment failures; never call this all-green or repair environment/dependencies outside scope.
6. **First post-code pass:** tests, applicable static diagnostics for every changed path and the one high-risk independent verifier run on the SAME INITIAL installed candidate. If AFT is denied, use applicable worker-owned static checks and report limitations; syntax checks alone do not prove behavior. Batch all findings into the one correction cycle.
7. **Gate 2:** PM provides writer result, installed diff, verifier RAW evidence, checks and pre-commit assessment of installed candidate. After writer AND verifier evidence, Planner dispatches exactly `advisor-gemini-post`, carrying exact specs, approved paths, actual diff and relevant source, reads RAW output, then issues Gate 2 BEFORE commit and task ticking/completion. No native post-commit review is Gate 2 input.
8. **Correction ceiling:** one initial writer plus ONE fresh correction writer across all pre-commit gates. Install first, consolidate finding IDs, correct installed base, targeted recheck, then Gate 2 again. Second Gate 2 fails only on true blockers; nonblockers become follow-ups. Second REFINE/ESCALATE returns to human, never starts another cycle silently.
9. **Commit/review:** worker supplies staged reviewability receipt; PM commits only after Gate 2 PASS. Enforce 400 authored changed lines/100 KiB authored patch; list generated paths separately and measure before committing. Do not shrink correct work to meet caps. RDD assessment/review after commit is separate, scoped to supplied boundary/effective mode. Required acknowledgement and metadata closure precede DONE. Planner dispatches no writer/lens and marks no task.

Source-only: no `derive --apply`, restart, deployment or live verification claim. No push/PR/branch-switch/revert/permission changes/Co-Authored-By or AI attribution. Proper PM-owned work-unit commit remains permitted. Mirror write/hash duties remain suspended until deterministic host tool lands; no mirror action claimed.

## Advisor selection and RAW evidence — one pre-code phase

High normative/config: three advisors total, different configured families and distinct questions, never all by default. All received frozen plan, exact specs, allowed paths, relevant excerpts, scope collisions and search restrictions; no first-pass advisor received another's answers.

- **Compulsory specification carrier:** `advisor-gemini-pre` (Gemini Argon), session `ses_e671cbdf1ffefKK5z9TY2bPfy9`; completed RAW output read. Antigravity inactive/external lane PLANNED: replaces `advisor-spec-pre`, never additional. Reserve exactly `advisor-gemini-post` instead of spec-post for the compulsory post position.
- **Integration surface:** `advisor-integration-pre` (configured MiMo family), session `ses_e671cbd4affeV7G8rHbP9EfRaY`; completed RAW output read. Selected for assembly/config/pin coupling and coordinator-route compatibility.
- **Testing surface:** `advisor-testing-pre` (configured GLM family), session `ses_e671cbd49ffeTkyS114hBFUHHC`; completed RAW output read. Selected for nonvacuous RED/count controls and baseline attribution. Advisor reported failed execution attempts and no executed tests/assembler; those attempts prove no check result, and host execution suggestions are not adopted.
- **Skipped:** design/UX (no UI); security (no permission/security-boundary change); maintainability (no separate refactor surface). Subscription Gemini/external subscription pair skipped: lane inactive; API-credit carrier is the explicit compulsory exception. `planner-evidence` skipped: blocking facts established through own exact-path reads. No extra advice pass or consensus claim.

### Finding dispositions

- Spec F1/integration F1/testing F2-F3: LEDGER-PATH unresolved; preserve ledger pin; explicit owner authority required.
- Spec F2/integration F8/testing F8: ANCHOR-DISPOSITION unresolved; prefer current exact-once/SHA chain without verifier expansion; redundant anchor-file test is not required merely to add a check.
- Spec F3-F4/integration F2-F4/testing F4-F6,F9: incorporated single-line rule, no redundant definition, exact splice/constant format, starting pin check, mutation diagnostics, byte locality and baseline-ID comparisons.
- Integration F5-F6/testing F7: incorporated top-level coordinator interpretation; existing route phases and PM tiny shapes unchanged.
- Integration F9/testing F1,F10: historical SHA citations and handoff-spec asymmetry stay outside scope; not claimed updated or live; not independent blockers justifying expansion.
- Integration F14: Q99 checkbox is not evidence for this phase. Q98's actual carrier Task returned completed RAW output; no Q99 closure claim.
- Testing F11-F12: verifier/pin/regression checks remain execution obligations. Integration's broader absence claims are not needed for the ledger finding and are not adopted as exhaustive proof.

## Progress and next step

Observed: Planner read initial 95-line r1 and relevant policy/source/tests; AFT outline was denied by broker role admission, so known-file reads supplied navigation. Loaded workflow-route, workflow-odd-secure, orchestration and planning skills. The specific one-unit Planner protocol governs; no extra research/review pipeline added.

Observed: three pre-code Tasks completed and RAW outputs were read. No implementation, writer dispatch, tests, deployment, Gate 2 or task tick performed by Planner.

Next: Gate 1 REFINE for the named scope decisions; PM obtains explicit owner disposition and resumes this Planner before coding. Both gates are TECHNICAL only, never approval of delivery/deployment/merge/release/user acceptance.


## Revisions
- r1 2026-11-01T17:37:19Z gentle-orchestrator: Create the Q98 tracker: coordinator selection rule for substantial units, with the observed evidence and acceptance criteria
- r2 2026-11-01T21:12:39Z planner: Planner finalisation and raw pre-advice; Gate 1 held for explicit ledger/anchor/advice-artifact scope decisions

## Gates
- T1 REFINE 2026-11-01T21:12:50Z planner ref=odd/tasks/q98-coordinator-selection.md r2; plan commit 5128feec9e628e02bf29db93a56f7c3660674084; RAW advisor sessions recorded in plan :: Gate 1 technical REFINE after reading all three RAW advisors. Before coding obtain explicit owner authority for normative-ledger.md companion SHA/count/classification updates; resolve S3 anchor-token requirement without silently editing verifier source; authorize required odd/advice/q98-coordinator-selection.md or explicitly dispose of that requirement. Do not weaken the ledger pin. Resume Planner with decisions and refreshed branch/tracker anchor; no writer or task completion yet.
