# Q98 — Coordinator selection: the orchestrator must use the PM layer

## Identity and authority

Unit: `q98-coordinator-selection-u1`; stable task: `T1`; branch: `chore/coordinator-selection`.
Class: global tooling change; risk: high normative policy/config and enforcement-test readers.
Route: `workflow-odd-secure`; RDD enabled/global (PM-supplied evidence, not independently reverified here).
Original input HEAD: `0e906e91ec0d626dc8eb3fc1dba407c87043e62b` (PM-supplied).
Recovery input: r3 at commit `e62a21dcff67a33ededba68b5429e9e3abba4e67` (PM-supplied); refresh branch/tracker anchor before writer dispatch.
Last reviewed boundary: `1adba52b1c6bdfaaa7b96fd69f15c1489a86615` (PM-supplied).
Owner decision: 2026-11-01, automatic coordinator selection for substantial units.

Planner-finalised contract: the PM supplies suggestions as messages; the Planner finalises the draft, selects advice and owns both technical gates. Final owner decisions below are retained without re-litigation. Implementation remains held until the fixed tool records Gate 1 PASS. No task is ticked and no delivery/deployment is approved.

## Problem and requirements

Observed source: the overlay's PM brief at `global-config/prompts/gentle-orchestrator/overlay.md:117-123` is conditional on delegation. `WORKFLOW.md:75,139-140` defines substantial work as at least two meaningful implementation steps or progress worth recovering. The owner requires automatic selection, not PM-on-request. Prior-execution/deployment-age claims are inherited session reports, not independently established here.

- **S1:** substantial ODD units select `pm-odd`; substantial Systematic units select `pm-systematic`; tiny fixes stay direct delegated-writer dispatches; read-only requests start no coordinator. Selection follows task class and the existing substantial-work test, never a user request for a PM.
- **S2:** put the same canonical rule once in the overlay and WORKFLOW, then regenerate the embedded orchestrator prompt with the existing assembler.
- **S3:** retain embedded-prompt SHA/equality checks; assert the complete canonical rule exactly once in WORKFLOW, overlay, real assembled stdout and decoded embedded prompt, and prove missing/duplicate rejection. These exact-once assertions plus the existing prompt SHA/equality chain satisfy S3. No token-table addition, no change to `tests/test_anchor_manifest.py`, and no verifier/pin change for `verify/58-section-7-recipe.sh`.
- **S4:** no changes to PM/Planner contracts, `pm-unit-brief/v1`, permissions, verifier semantics, tiny-fix writer mapping, route skills, base prompt or assembler code. No prompt externalisation or unrelated cleanup.

## Final owner scope decisions — 2026-11-01

Observed authority: PM continuation messages relay these decisions as FINAL; accepted without re-litigation.

1. **LEDGER-PATH — APPROVED:** add `global-config/prompts/gentle-orchestrator/normative-ledger.md`, bounded strictly to regenerated prompt SHA and line count, accurate candidate and classification counts, the new rule's classification and provenance, and necessary explanatory references. Preserve the ledger pin at `tests/test_orchestrator_prompt_source.py:833-835`; do not weaken, skip, dynamically compute away or decouple it. Verify actual counts; do not hardcode advisor estimates.
2. **ANCHOR-DISPOSITION — ACCEPTED AS AMENDED:** S3 is satisfied by exact-once rule assertions on all four surfaces plus the existing prompt SHA/equality chain. No token-table addition, no change to `tests/test_anchor_manifest.py`, and no verifier/pin change for `verify/58-section-7-recipe.sh`.
3. **ADVICE-ARTIFACT — APPROVED:** add `odd/advice/q98-coordinator-selection.md` solely as the advice record required by `WORKFLOW.md:629-637`. Record advisor evidence and dispositions accurately; do not fabricate RAW content or claim unexecuted checks.

The three r2 scope blockers are resolved. These decisions do not themselves constitute Gate 1 PASS or authorize delivery/deployment.

## Allowed edit surfaces — final scope

1. `WORKFLOW.md`
2. `global-config/prompts/gentle-orchestrator/overlay.md`
3. `global-config/opencode.json`
4. `tests/test_orchestrator_prompt_source.py`
5. `tests/test_anchor_manifest.py` (conditional/no-edit: retained for traceability; owner disposition requires no change in this unit)
6. `ROUTER-LOG.md`
7. `odd/tasks/q98-coordinator-selection.md`
8. `global-config/prompts/gentle-orchestrator/normative-ledger.md` (bounded strictly to regenerated prompt SHA and line count, accurate candidate and classification counts, new-rule classification/provenance, and necessary explanatory references; preserve existing ledger pin)
9. `odd/advice/q98-coordinator-selection.md` (required advice record only)

No other edit surfaces are authorized. Token tables, verifier source and the pin for `verify/58-section-7-recipe.sh` remain unchanged.

## Intended design

Use this byte-identical, single-physical-line paragraph once in WORKFLOW's existing Classification and Route Selection Rules and once in the overlay's existing `user:workflow-routing` block:

> Coordinator selection is automatic: dispatch substantial ODD units to `pm-odd` and substantial Systematic units to `pm-systematic`; tiny fixes stay direct delegated-writer dispatches with no PM, and read-only requests start no coordinator; select by task class and the existing substantial-work test, never by whether the user asks for a PM.

Insert it as a standalone, unbulleted physical line in both files, separated as a paragraph. The blockquote above is plan presentation, not source syntax. Count exact full-sentence substring occurrences with a single shared checker using `text.count(CANONICAL_RULE)`, never symbol/token counts or a differently wrapped sentence. Preserve headings, anchor markers, SECURE IDs and replace/remove hashes. Add no redundant substantial-definition sentence; existing definitions remain authoritative.

Interpretation: this selects the top-level coordinator at orchestrator route entry AFTER route classification, not a replacement for the selected route's skills/specialists. The chosen ODD/Systematic adapter determines the PM counterpart. Existing PM-dispatched tiny-fix shapes remain supported when a PM is already the dispatcher; the new rule starts no PM for a top-level tiny fix and changes no writer or closure procedure. Read-only starts no new work-unit coordinator; the running orchestrator can still answer. The advice record must carry this interpretation. If the owner rejects it, stop rather than modify those contracts.

Observed source and explorer excerpts: assembler `main` emits stdout with a trailing newline; no config-write mode exists. Generate bytes only with the assembler. Worker file tools replace just the existing JSON prompt value with JSON-encoded assembler stdout. Encoding that one string is permitted; whole-config reserialization is not. Inspect and preserve the existing string's Unicode-escaping convention. Require byte prefix/suffix identity outside that value span plus parsed nonprompt-tree equality. Preserve the test constant's double-quoted lowercase 64-hex assignment format. Observed independent read: `verify/checkers/check-runtime-agents.cjs:1852-1859` extracts that constant by regex and compares it to the measured assembled digest; updating the constant in the same unit as prompt and ledger is mandatory, not a verifier edit.

## Tasks — one coherent implementation unit

Original IDs remain pending. T2/T3 are T1 acceptance/test/log substeps, not separate implementation deliveries or deployments. Necessary post-commit metadata closure remains the existing PM procedure.

- [ ] **T1 (S1-S3):** after Gate 1 PASS, implement policy, overlay, generated embedded prompt and approved companion ledger data within the final allowed paths; write the required advice record from truthful evidence.
- [ ] **T2 (S3; T1 acceptance):** extend `tests/test_orchestrator_prompt_source.py` test-first with exact-once and missing/duplicate controls, preserve existing pin checks and report bounded prompt delta. Leave `tests/test_anchor_manifest.py` and verifier/pin surfaces unchanged.
- [ ] **T3 (T1 evidence):** record ROUTER-LOG row and closure evidence at the correct phase; commit fields stay pending until known; no completion before Gate 2/commit/required review evidence.

## Execution and verification

1. **Baseline before edits:** authorized worker runs starting assembler/embedded/SHA/ledger pin tests and records digest/bytes/lines. Stop for pre-existing pin drift. Capture full-suite failure/error identities and reasons on the unmodified candidate in the same environment. The supplied baseline of 22 failures/28 errors attributed to missing sqlite3/denied node is PM-reported, not independently reproduced. Record actual totals, IDs, runtime/environment and attribution; never assume all failures share those causes. PM refreshes the unit-start branch/tracker anchor before writer dispatch.
2. **Observed RED:** add the new checker/test before policy/prompt edits and execute it. Enumerate the four surfaces in independent tests or `subTest` contexts so every missing surface is reported rather than stopping at the first assertion. Record actual count-0 missing-rule failure text and all failing surfaces. Syntax/import/environment errors do not prove the required RED. Follow the existing non-noop/subTest precedents at `tests/test_orchestrator_prompt_source.py:697-709`.
3. **Coverage:** shared checker asserts exact full rule count equals one in WORKFLOW, overlay, real assembled stdout and decoded embedded prompt. Pristine control passes; for EACH named surface removal gives count 0 and a missing-surface diagnostic; duplication gives count 2 and a duplicate diagnostic. Assert every mutation changes its input. Full-sentence checking rejects clause corruption. Mutated copies exercise the same checker independently, including decoded embedded text; equality tests do not make divergence impossible. Also prove source-to-output propagation by feeding a temporary mutated overlay through the real assembler's existing `--overlay` interface and checking its missing/duplicate diagnostics. Never replace the pristine real assembler invocation with a fixture or mocked stdout. S3 uses this coverage and existing SHA/equality checks, not a token-table row or anchor-manifest edit.
4. **Generation/locality:** add only the approved paragraph to each source, execute existing assembler, splice the embedded string, update current SHA and approved ledger data together. Verify actual ledger candidate/classification counts and rule provenance; record the counting/sentence-boundary method so the recount is reproducible while retaining historical-row provenance. The new rule contains `never` and therefore needs classification; advisor predictions such as 77 candidates/51 kept are estimates, not acceptance values. Restrict explanatory edits to necessary references. No formatter, `json.tool` write mode, handwritten generated prompt or full-config reserialization. Assemble twice and require byte identity; require embedded==stdout and digest==pin. Compare against captured unit-start bytes: only approved rule insertion plus separating whitespace; report SHA/UTF-8 bytes/physical lines and deltas. Config `git diff --numstat` must show exactly 1 added/1 removed physical prompt line. Verify outside-value byte prefix/suffix and decoded nonprompt-tree identity. Retain existing ledger-pin assertion at `tests/test_orchestrator_prompt_source.py:833-835`.
5. **Tests:** focused `python3 -m unittest tests.test_orchestrator_prompt_source tests.test_anchor_manifest -v`, then `python3 -m unittest discover -s tests`. Compare failure-ID-and-reason sets, not totals alone, against observed pre-edit baseline. New/unexplained failures block acceptance. Individually attribute environment failures; never call this all-green or repair environment/dependencies outside scope.
6. **First post-code pass:** tests, applicable static diagnostics for every changed path and the one high-risk independent verifier run on the SAME INITIAL installed candidate. If AFT is denied, use applicable worker-owned static checks and report limitations; syntax checks alone do not prove behavior. Batch all findings into the one correction cycle.
7. **Gate 2:** PM provides writer result, installed diff, verifier RAW evidence, checks and pre-commit assessment of installed candidate. After writer AND verifier evidence, Planner dispatches exactly `advisor-gemini-post`, carrying exact specs, approved paths, actual diff and relevant source, reads RAW output, then issues Gate 2 BEFORE commit and task ticking/completion. No native post-commit review is Gate 2 input.
8. **Correction ceiling:** one initial writer plus ONE fresh correction writer across all pre-commit gates. Install first, consolidate finding IDs, correct installed base, targeted recheck, then Gate 2 again. Second Gate 2 fails only on true blockers; nonblockers become follow-ups. Second REFINE/ESCALATE returns to human, never starts another cycle silently.
9. **Commit/review:** worker supplies staged reviewability receipt; PM commits only after Gate 2 PASS. Enforce 400 authored changed lines/100 KiB authored patch; list generated paths separately and measure before committing. Do not shrink correct work to meet caps. RDD assessment/review after commit is separate, scoped to supplied boundary/effective mode. Required acknowledgement and metadata closure precede DONE. Planner dispatches no writer/lens and marks no task.

Source-only: no `derive --apply`, restart, deployment or live verification claim. No push/PR/branch-switch/revert/permission changes/Co-Authored-By or AI attribution. Proper PM-owned work-unit commit remains permitted. Mirror write/hash duties remain suspended until deterministic host tool lands; no mirror action claimed.

## Advisor selection and RAW evidence — authorized one-time recovery

Observed authority: the current PM message explicitly authorizes ONE recovery re-dispatch of exactly `advisor-gemini-pre`, `advisor-integration-pre`, `advisor-testing-pre`, superseding r3's no-rerun note for this transport incident only. No fourth advisor and no second round. Prior Planner `ses_e671f84c9ffeiIa4CvlX78qil5` was unreachable from the PM; PM supplied the error `Session ses_e671f84c9ffeiIa4CvlX78qil5 is not a child of the current session`. Current Planner does not claim to have recovered the historical RAW responses.

High normative/config: three advisors total with distinct configured families and independent questions; all received the same frozen r3 scope, exact S1-S4/canonical string, owner-final decisions, allowed paths, operative plan, relevant source excerpts, scope collisions and search restrictions. All three were launched in one independent wave, without another advisor's response, and returned `state="completed"`; current Planner read each RAW tool result in full.

- **Compulsory specification carrier:** `advisor-gemini-pre`, session `ses_e66e3f906ffeJyqCrDnCQyJkBP`. Selected as the API-credit specification carrier replacing spec-pre while Antigravity is inactive/external lane PLANNED, never additional. RAW disposition: S1-S4 and owner decisions covered; no blocker; F1 ledger/schema/count care, F2 exact single-line placement/count convention, F3 Unicode-encoding locality are execution guardrails. Reserve exactly `advisor-gemini-post` instead of spec-post at the compulsory post position.
- **Integration surface:** `advisor-integration-pre`, session `ses_e66e3f899ffemfVS7wk42lzCbA`. Selected for assembly/config/pin coupling and route compatibility. RAW disposition: no blocking design defect; B1/B2 ledger/constant/config same-unit updates already required; N1 mutation/source-propagation clarified below; N2 reproducible ledger recount, N3 advice-record top-level interpretation, N4 measured deltas, N5 first-pass verifier are incorporated or already required.
- **Testing surface:** `advisor-testing-pre`, session `ses_e66e3f865ffehDLDCamPUIpGgd`. Selected for nonvacuous RED/count controls and failure-baseline attribution. RAW disposition: no hard test-design blocker, but B1 sentence-count/placement convention, B2 all-surface RED enumeration and B3 mandatory same-unit digest constant update required precision before dispatch. r4 explicitly resolves all three without new scope.
- **Skipped:** design/UX (no UI); security (no permission/security-boundary change); maintainability (no separate refactor). Subscription Gemini/external subscription pair skipped because lane inactive; API-credit carrier is the compulsory exception. `planner-evidence` skipped: available source reads and one bounded `explore` established required facts. No extra advice pass or consensus/approval claim.

### Current RAW finding dispositions

- Spec F1/integration B1,N2: classify the new trigger-bearing rule with correct row schema/provenance and document reproducible recount; preserve pin. Do NOT adopt the spec advisor's predicted numeric counts as observed values. Explanatory ledger prose is not itself current-prompt input to the candidate extractor.
- Spec F2/testing B1: exact full-sentence substring count via shared checker; standalone unbulleted one-line placement in both source files. Token-only counting and wrapped/modified canonical strings are excluded.
- Testing B2: enumerate each surface independently (`subTest` or separate tests), report all real RED failures, require non-noop checks for each mutation.
- Testing B3/integration B2: mandatory measured digest update in test constant with config+ledger, retaining regex-compatible spelling and existing pin shape. Current Planner independently read the runtime checker at `verify/checkers/check-runtime-agents.cjs:1838-1859`; no verifier-source change is needed.
- Spec F3: inspect and preserve existing JSON Unicode-escaping convention; source/decoded prompt delta remains only rule plus separating whitespace; raw outside-value identity retained.
- Integration N1: accept source-fed mutated-overlay integration control and named diagnostics; reject the premise that an equality assertion makes embedded/stdout divergence impossible and reject excluding independent decoded-output checker mutations. The existing equality test DETECTS divergence; the four-surface negative controls must still exercise each checker input.
- Integration N3: top-level interpretation belongs in required advice record; existing PM tiny-fix contracts remain untouched.
- Integration N4,N5/testing F2: measured prompt deltas and initial-candidate verifier are already required. Do not convert estimated line growth into a fixed expected count.
- Testing F1: historical SHA citations outside allowed paths remain point-in-time records, not current pins; no unrelated edits or live-value claim. Broader advisor absence/size assertions are not adopted as exhaustive proof and do not replace measured reviewability receipts.

### Historical evidence retained, not substituted for current RAW

r2 sessions: spec `ses_e671cbdf1ffefKK5z9TY2bPfy9`, integration `ses_e671cbd4affeV7G8rHbP9EfRaY`, testing `ses_e671cbd49ffeTkyS114hBFUHHC`. r2 records prior RAW reads; current Planner has only historical summaries, not those responses. r3 final owner decisions resolved the historical ledger/anchor/advice scope blockers. Historical test execution attempts/suggestions prove no executed check here. Advice artifact must distinguish historical reports from this directly read recovery evidence and must not invent unavailable RAW quotations.

## Progress and next step

Observed current recovery: loaded workflow-route, workflow-odd-secure, orchestration and planning skills; specific one-unit Planner protocol overrides generic extra planning pipelines. Read complete r3 and relevant WORKFLOW/overlay/tests/ledger/runtime-checker excerpts. Bounded `explore` session `ses_e66e9b5f6ffeS4DPtX5klAHTQo` returned source excerpts, reported CodeGraph index unavailable and known-path/AFT fallback, no initialization or tests. Selected exactly the three authorized advisor recovery Tasks above and read all RAW outputs. No writer, task tick, tests, assembler execution, deployment or Gate 2 performed by Planner; this read-only role has neither Bash nor sandbox execution authority.

Observed limitation: attempted `host_review_mode_status` returned `Tool "host_review_mode_status" is denied by broker admission (ROLE_DENIED_FOR_AFT_READ). Legitimate tools are classified in TOOL_CLASSIFICATION_INVENTORY (broker/src/role-policy.ts); sandbox tools are not affected.` RDD enabled/global remains PM-supplied, not a current tool-verified claim. This Gate 1 recovery does not start or complete review; required later PM review operations must remain fail-closed if their authorized surface is unavailable.

Next: issue Gate 1 reconsideration through the fixed verdict tool using this final plan and the three directly read RAW recovery outputs. After an observed Gate 1 PASS, PM refreshes the branch/tracker anchor and may dispatch the authorized initial writer with these guardrails and accurate advice evidence. No task completion before Gate 2, commit and applicable native review. Both gates are TECHNICAL only, never approval of delivery/deployment/merge/release/user acceptance.


## Revisions
- r1 2026-11-01T17:37:19Z gentle-orchestrator: Create the Q98 tracker: coordinator selection rule for substantial units, with the observed evidence and acceptance criteria
- r2 2026-11-01T21:12:39Z planner: Planner finalisation and raw pre-advice; Gate 1 held for explicit ledger/anchor/advice-artifact scope decisions
- r3 2026-11-01T21:36:06Z planner: r3: final owner ledger/anchor/advice scope decisions; one-time Planner transport exception; RAW evidence recovery pending
- r4 2026-11-01T22:12:12Z planner: r4: authorized one-time RAW advice recovery; resolve precision gaps and finalise Gate 1 candidate

## Gates
- T1 REFINE 2026-11-01T21:12:50Z planner ref=odd/tasks/q98-coordinator-selection.md r2; plan commit 5128feec9e628e02bf29db93a56f7c3660674084; RAW advisor sessions recorded in plan :: Gate 1 technical REFINE after reading all three RAW advisors. Before coding obtain explicit owner authority for normative-ledger.md companion SHA/count/classification updates; resolve S3 anchor-token requirement without silently editing verifier source; authorize required odd/advice/q98-coordinator-selection.md or explicitly dispose of that requirement. Do not weaken the ledger pin. Resume Planner with decisions and refreshed branch/tracker anchor; no writer or task completion yet.
