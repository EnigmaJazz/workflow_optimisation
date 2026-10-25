# Q90 — Activate PM-to-Planner handoff, unit 1

## Identity and authority

Work unit and task ID: `q90-activate-pm-planner-u1`.
Project: `/home/james/ai-workspace/workflow_optimisation`.
Class: global-tooling-change; high/normative configuration, text-only.
ROUTE: global-tooling-change | intent: authorized plan-only document | route: workflow-odd-secure / Gate 1 | specialist: advisor-integration-pre | basis: WORKFLOW.md

This is the owner-authorized plan-only document, not implementation authorization or a task tick. Its creation is the explicit exception to the unit's no-tracker-write boundary; the writer may not edit it or any other tracker. Gate verdicts are append-only technical records through host_gate_verdict, never delivery, deployment, merge, release, or user acceptance. Planner dispatches no writer or review lens and never calls host_task_mark.

## Task

- [ ] q90-activate-pm-planner-u1: Apply exactly the source edits and test additions below, collect the bounded checks and post-code evidence, and return for Gate 2 before any work-unit commit or PM completion. This unchecked item states future work only; no implementation is claimed.

## Evidence and limitations

- observed directly at unit start: `.git/HEAD:1` is `ref: refs/heads/chore/multi-agent-v2-phase1`; `.git/refs/heads/chore/multi-agent-v2-phase1:1` is `636df2e622a75f145dd268c75a86e938019a60df`. Not a fresh end-of-planning Git check.
- observed by PM, supplied: RDD `receipt-driven development: on (decided by global)`; clone-local unset. Planner does not have an authorized review-mode surface and will not recheck it.
- observed: Planner AFT calls returned `ROLE_DENIED_FOR_AFT_READ`; no further AFT calls or shell fallback. PM supplied attributed byte-exact T1/T2 excerpts. Writer must independently enforce exact matching and refuse zero/multiple matches.
- observed directly: global-config/AGENTS.md:148-180 preserves query-type tools, orchestrator-only ask-gated grep, and subagent grep prohibition; CLAIM-RETRACTIONS.md:13-19,24-31,51-55 defines seven columns, provenance and append-only rules.
- observed directly: tests/test_pm_layer_prompts.py:95-141,157-205,208-304 provides per-agent assertions, exact-occurrence checks, mutation controls and <6000-character cap. tests/test_anchor_manifest.py:158-207 executes extracted verifier loops on real sources; :210-240 provides positive controls.
- observed directly: verify-workflow.sh:5219,5245,5292 locks the SKILL anchor with `Tiny-fix route:`, `openai/gpt-6-luna`, and `Temporary writer deviation (owner decision, 2026-10-17)`; preserve the complete prefix and anchor markers.
- observed directly: docs/specs/pm-handoff.md:7 supplies initial_plan rather than separate draft path/revision fields; :11 says not to duplicate route procedure in another prompt source; WORKFLOW.md:164-199 carries the full live Planner contract.
- observed by owner-relay: owner explicitly mandates the shortened SKILL replacement and procedural PM bullet verbatim despite those concerns. These are deliberate bounded owner decisions, not claims of textual equivalence to the complete canonical contract. Do not change specs/permissions/verifier to reconcile them in this unit.
- owner-supplied clarification: `the draft path, revision` slots carry the initial_plan draft content handed over in this session; no separate draft file exists. A future draft-path mechanism is out of scope. No functioning path/revision mechanism is inferred or verified.
- historical supplied baseline only: full Python suite `Ran 244 ... OK`, PM-layer `26 OK` / prompts `13 OK`; none is a fresh Planner execution. Require actual new counts and no weakened coverage.
- observed: initial gate attempts recorded no verdict: first `GATE_VERDICT_REFINEMENT_INVALID: refinementPlan must be at most 600 characters and contain no newline`, then `GATE_VERDICT_DOCUMENT_MISSING: plan document must already exist`. This document supplies the newly authorized binding; only a successful subsequent fixed-tool result establishes Gate 1.

## Objective and allowed writer surfaces

Activate PM-to-Planner teaching in source prompts/skill and strengthen absence-claim search discipline. Exactly these implementation paths are allowed:

1. global-config/skills/workflow-odd-secure/SKILL.md
2. global-config/opencode.json
3. global-config/AGENTS.md
4. CLAIM-RETRACTIONS.md
5. ROUTER-LOG.md
6. tests/test_pm_layer_prompts.py
7. tests/test_anchor_manifest.py

No runtime code, verifier edit, digest re-pin, permission edit, tracker write, deploy/mirror, push, PR, branch switch, prompt externalization or scope expansion. The owner alone handles later deployment/restart. Existing installed/live wording is the owner-directed description of the Planner layer, not evidence that these new source changes have reached live config.

## Exact edit contract

### Edit 1 — SKILL.md:16, owner-exact replacement

Replace only this entire tail substring. Preserve every preceding byte in the tiny-fix bullet, including the PENDING-COMMIT sentence, and both anchor markers.

oldString:
```text
Planner handoff (PLANNED, NOT INSTALLED OR LIVE): in the target, `planner` (`openai/gpt-6.1-sol` `high`) finalises the orchestrator draft and PM suggestions (messages, never plan writes), calls ALL pre-code advisors itself and reads their RAW outputs, issues Gate 1 after the pre advice, and issues Gate 2 pre-commit — after the post-code advice, the writer and verifier evidence, and the pre-commit assessment of the installed candidate — occurring BEFORE the work-unit commit; Gate 2 runs again after any revision; on the second Gate 2, PASS unless a true blocker remains; record non-blocking follow-ups as later work; a second REFINE or ESCALATE stops the unit for human direction. Both verdicts are technical only and never approve delivery; the Planner dispatches no writer or review lens. Current PM runtime ownership remains until deferred integration. Deferred Q90-D1 prompt reduction/externalization happens only AFTER the PM layer becomes active, not as an immediate prerequisite.
```

newString (owner-exact):
```text
Planner handoff (installed and live since 2026-10-25): the PM reads the orchestrator draft and hands it to `planner` with its own suggestions as messages; the Planner selects the pre-code advisors the task class and impact require (none for docs/metadata/tiny; one surface advisor for medium; at most three for high/normative/config/security), reads their RAW outputs, issues Gate 1, and issues Gate 2 pre-commit; Gate 2 re-runs after any revision and a second REFINE/ESCALATE returns the unit to the human.
```

Owner deliberately replaces the whole supplied tail, including its technical-only and Q90-D1 sentences. Do not reappend them. The full technical constraints remain binding on this unit under WORKFLOW.md:175-199 and the Planner role; prompt externalization is still not authorized.

### Edit 2 — both PM prompts, owner-exact bullet

PM-supplied observed source positions: pm-odd :2252, pm-systematic :2391. Scope each edit to its own agent prompt. The originally mentioned `No tracker write...` sentence belongs to an injected brief, not these config prompts. Insert after the Tiny-fix paragraph and before the search-contract block, keeping that block last. No task-map changes: PM supplied observation already shows planner allowed.

oldString (literal JSON source escapes):
```text
Record the change in the active unit tracker `## Log` and in the return envelope, including its commit and changed-line count.\n\n<!-- user:subagent-search-contract -->
```

newString (same in both prompts, literal JSON source escapes):
```text
Record the change in the active unit tracker `## Log` and in the return envelope, including its commit and changed-line count.\n\n- Hand the plan to the Planner: after the orchestrator drafts the plan, read it, add your suggestions as messages (never plan writes), and dispatch `planner` with the draft path, revision and your suggestions. The Planner finalises the plan and issues Gate 1; you do not finalise the plan yourself and you do not issue gate verdicts.\n\n<!-- user:subagent-search-contract -->
```

The `- ` is the Markdown bullet marker; bullet prose is verbatim owner text. Both prompts must receive it exactly once. Preserve existing tiny-fix text, JSON escaping, all unrelated prompts and permission maps, and the <6000-character cap.

### Edit 3 — AGENTS.md insert, accepted seven-line passage

oldString (observed directly :156-158):
```text
index, and structural matching does not replace a needed literal text search.

For the orchestrator, built-in `grep` remains `ask`-gated. Use it only when
```

newString:
```text
index, and structural matching does not replace a needed literal text search.

Search-order hardening for orchestrator absence claims: use applicable, available
tools in this order: `read` → `aft_outline`/`aft_zoom` → `codegraph_explore` →
`ast_grep_search` → built-in `grep` last, retaining query-type tool selection.
Built-in `grep` is case-sensitive by default; a zero match is evidence about the
pattern, not the file. State the exact pattern and a positive control proving it
would match the real spelling (e.g. capitalisation). `grep` remains `ask`-gated
and unavailable to subagents; shell search never bypasses these boundaries.

For the orchestrator, built-in `grep` remains `ask`-gated. Use it only when
```

Keep all surrounding rules verbatim, including do-not-bypass and subagent-specific tool order. No shell-search permission is granted.

### Edit 4 — append retraction, owner-exact provenance correction

Append below the current last entry (observed directly at CLAIM-RETRACTIONS.md:75), never rewrite an earlier row:
```text
| 2026-10-25 | workflow_optimisation | absence | "SKILL.md has no planner text" | The owner reports the claim was corrected by `aft_search` matching capitalised "Planner", locating the existing clause inside the tiny-fix bullet | Search with the real spelling (or case-insensitive) and state the exact pattern and positive control before any absence claim | owner report |
```

The owner now supplies report-and-retraction provenance. The exact original grep pattern is not known; do not invent it or assert a lowercase-token mechanism. Source remains owner report, never upgraded to agent observed.

### ROUTER-LOG.md row

observed directly at ROUTER-LOG.md:11-12: the header has EIGHT columns, not seven. Use the existing full row shape; no schema/header rewrite:
```text
| 2026-10-25 | q90-activate-pm-planner-u1 | global-tooling-change | none | Gate 1 recorded; implementation checks and Gate 2 pending | false | odd/tasks/q90-activate-pm-planner-u1.md; advisor session ses_e8b37f4eeffeWEkP2s7wDsNjSD | PENDING-COMMIT; source-only; no deployment/mirror/restart. Owner-exact SKILL and PM wording retained after advisor concerns; retraction provenance is owner report. Advisor disclosed sandbox scratch probes contrary to its read-only brief; not verification or implementation artifacts. Possible Planner routing-guard advisory warnings remain an unexecuted follow-up hypothesis. |
```

Use `Gate 1 recorded` only after the fixed gate act actually succeeds. At post-code closure replace pending check/Gate 2 descriptions only with observed evidence. Commit identity is filled at applicable closure; no fabricated current commit or reviewer approval. A commit cannot contain its own hash; final commit trace metadata follows the PM's authorized closure mechanism, not an extra implementation-writer round silently granted here.

## Test-first additions and expected execution

First add new test methods in the two allowed test files before source changes, then run both focused commands against the unchanged config to demonstrate meaningful RED. RED must arise from missing new Planner text/installed-live token, not an import/syntax/environment failure. Preserve all existing tests and mutation controls; counts must grow, not be weakened or removed to meet a historical count.

1. tests/test_pm_layer_prompts.py: assert the EXACT owner PM bullet once independently in pm-odd and pm-systematic; verify it is after the existing Tiny-fix paragraph and immediately before the search-contract block. Add missing-bullet, duplicate-bullet, cross-agent contamination and displaced-placement mutation controls. Keep JSON parsing, named-writer assertions and <6000-character cap. A needle in another prompt cannot satisfy either agent's check.
2. tests/test_anchor_manifest.py: extract only the interior of workflow.tiny-fix-odd-route from SKILL.md, assert exact owner new clause once, installed-live token present and old planned token absent within that interior. Preserve anchor/token loops. Add mutation control removing/reverting the new clause, and controls detecting damage to the preexisting tiny-fix prefix/trace tokens. Do not demand that removed tail sentences remain in this anchor. Do not make any repository-wide old-token absence assertion: historical records may legitimately retain it.
3. After meaningful RED, apply exact edits and record GREEN from both focused commands, then full suite, parse and cleanliness. Independent verifier executes checks on the installed same candidate; no parse-only claim of runtime activation.

Exact commands (one invocation per command; no shell pipelines/redirects):
```text
python3 -m unittest tests.test_pm_layer_prompts -v
python3 -m unittest tests.test_anchor_manifest -v
python3 -m unittest discover -s tests
python3 -m json.tool global-config/opencode.json
git diff --check
```

Expected GREEN means exit 0 and actual observed unittest totals/OK; JSON parse proves syntax only. git diff --check expected exit 0 with no whitespace diagnostics. Capture real failures, skipped tests, unavailable consumers and static-diagnostic gaps rather than inventing success. No build/parse proves deployment or successful real PM dispatch.

## Advice selection and disposition

Selected exactly advisor-integration-pre: the affected surface is normative prompt/skill integration plus existing test/verifier readers. No separate design, security, testing or maintainability pass: no materially independent second surface requires one for this bounded text-only unit. Gemini skipped because external lane is PLANNED, not active. planner-evidence skipped because direct reads plus attributed PM source evidence suffice.

observed: advisor-integration-pre session ses_e8b37f4eeffeWEkP2s7wDsNjSD completed in the sole invocation, and Planner read its RAW output in full. No timeout/UNAVAILABLE and no retry/additional advisor.

Disposition of raw findings:
- B1/B2/R3: PM-prompt procedure duplication, absent separate draft path/revision, and abbreviated advisor-budget drift were valid technical concerns supported by docs/specs/pm-handoff.md:7,11 and WORKFLOW.md:175-181. Owner explicitly restores exact wording; record bounded override, do not silently amend it or claim equality. Draft-path mechanism remains out of scope. These are not true blockers after explicit owner direction for this source-only unit.
- B3: double pre-advice ownership was an advisor inference from retained PM permissions. Canonical WORKFLOW.md:172-181 and Planner prompt already assign selection to Planner; permission to call is not an obligation. No permission change needed or authorized. Preserve actual single phase and Planner-selected advice in execution.
- B4: owner now confirms report/retraction provenance; owner-report source and conservative row remove unsupported exact-pattern mechanism. Resolved without upgrading provenance.
- R1/R5: accepted exact substring boundary, prefix preservation, JSON escape/placement, tiny-fix preservation, contract block last, prompt cap and parse checks.
- R2: owner deliberately restores shortened exact tail. Full Gate 2 and technical-only constraints remain in canonical policy and this execution plan; Q90-D1 is still out of scope. Not permission to weaken actual gates.
- R4: accepted scoped <=10-line absence-claim passage retaining query-type selection and subagent grep prohibition, rather than rewriting existing rules.
- R6: accept/document asymmetric carriers (ODD skill + PM prompt versus Systematic PM prompt). Both PMs still read WORKFLOW.md and get identical owner bullet. No systematic skill expansion.
- R7: possible recurring guard warnings remain an inferred/unexecuted follow-up, not proven runtime behaviour. No guard edits here; a true blocking dispatch refusal must be reported rather than bypassed.
- R8: owner exact installed/live wording retained; this is source-only work and no new mirror/restart is claimed.
- R9: preserve observed eight-column ROUTER-LOG schema and truthful pending/closure evidence.

observed disclosure in advisor RAW output: it ran scratch Python probes in a sandbox worker and wrote ten `.scratch_advisor_probe*.py` files despite its read-only/no-execution brief. This is a process finding, NOT validation, not an approved change, and not accepted verification. No advisor result may be exported/installed; the implementation writer must exclude those paths and originate from the authorized project candidate. No host execution, cleanup or worker lifecycle authority is granted to Planner.

## Post-code disposition and owner-authorized correction exception

observed: sole advisor-integration-post ses_e8af1ac96ffebRoaZ3nf8LjX3v returned and Planner read its RAW output fully. Initial writer ses_e8b082337ffemXNoeRyOaJ7RGH and independent verifier execution evidence were supplied by PM. Gate 1 PASS and first Gate 2 REFINE remain preserved in the broker-owned append-only record, not rewritten by this revision.

F1 router correction and retraction:
- observed in the original bounded tail read: no unit row followed the historical final row q90-gate2-precommit-u1-r1. That did NOT prove absence elsewhere in the file.
- RETRACTED inference: a concurrent actor clobbered/reverted the router row. PM withdraws that mechanism; Planner withdraws any acceptance of it and the advisor's file-wide absence conclusion. The differential is that no full-file search/positive control preceded the tail-only claim.
- observed by PM, supplied: the initial writer appended per the PM brief's mid-file row-55 anchor, q90-t3b-planner-reconcile-u1; the Usage Notes block predates later appends. The normal correction re-appended at the actual tail, temporarily duplicating the record. The owner-authorized micro-fix removed the stale mid-file copy and corrected the mechanism sentence to the anchor-placement history. The historical tail rows persisted throughout; line numbers shifted after deletion.
- observed directly on final readback: ROUTER-LOG.md:55 is the reconciliation row; :56 blank and :57 Usage Notes, with no unit row at the old slot. At :298 the final unit row carries the corrected anchor-placement story; preceding historical gate2-precommit-u1-r1 is now :297. Exactly-once full-file uniqueness and verbatim historical-row preservation are supplied PM/micro-fix observations, not independently proved by these two bounded reads. The old 293-298 range is a historical range, not a current-line-number assertion.
- disposition: F1 resolved on final supplied readbacks. No concurrent-clobber mechanism remains asserted. Preserve historical advice/gates as history rather than silently sanitizing them.

Correction accounting: correction_rounds_used = 1 normal + 1 owner-authorized bounded micro-fix exception. Ordinary envelope correction_rounds_used stays 1; separately record bounded exception_count=1, never reset the normal budget. Normal correction writer ses_e8ae62fbfffe0DyPWaBhYhQOqS; micro-fix writer ses_e8ad518f3ffeoJanKPPLJW9wKE. Authorization supplied by owner-relay PM. Planner dispatched neither. This is not standing authority for another writer or advice cycle.

F2: observed by PM after correction, Pyright 0 errors / 0 warnings on both tests; unsupported Python complexity/dead-code categories are not authoritative. Observed directly in tests/test_pm_layer_prompts.py:215-263 and tests/test_anchor_manifest.py:173-179: runtime assertions retained and explicit non-None assertions before Optional operations. Supplied correction evidence confirms accurate malformed-fixture typing with intentional None mutation preserved, no suppression/weakening. Original diagnostic novelty remains unproved; do not call them introduced without a baseline differential. F2 resolved.

Executed results observed by normal correction/micro-fix writers and supplied by PM: focused 21/21 OK each, full Ran 358 tests OK; correction JSON parse passed; final git diff --check clean. The initial independent verifier's reproduced checks remain part of Gate 2 input, with targeted corrected-candidate rechecks rather than another full advice/verifier round. Planner ran no tests or implementation commands. Runtime/deployment remain UNVERIFIED and out of scope.

F3 receipts: retire original unverified 43,888 bytes. Supplied measured correction interim receipt 292 lines / 51,064 bytes. Supplied final micro-fix receipt vs 636df2e622a75f145dd268c75a86e938019a60df: 291 authored changed lines (+282/-9), no generated/binary paths. Latest handoff does not state final post-micro-fix raw bytes; do not relabel interim 51,064 as final. Require exact final STAGED line/byte receipt at PM commit boundary counting every actual commit member. No final byte value invented by Planner.

Pre-commit technical assessment: supplied final tests/diagnostics and readbacks resolve source findings; no true source blocker established on deciding evidence. The concurrent-clobber theory is withdrawn. Second Gate 2 PASS is the intended technical disposition, recorded only after a successful subsequent fixed act. No implementation commit or task completion/tick is performed by this plan revision.

Final commit notes: this plan/control artifact remains outside the seven implementation paths unless separately authorized metadata disposition includes it. Count its NEW revised size if staged; the old +179-line figure is no longer current. PM discloses ROUTER-LOG diff includes other units' uncommitted rows; preserve and reconcile attribution/commit membership at commit boundary without silently broadening this unit. Native committed-candidate assessment is AFTER commit, not Gate 2 input. Pre-commit technical assessment means this bounded source/evidence evaluation, not an impossible committed-only native assessment of uncommitted work.

## Finite post-code and gate sequence

One initial implementation writer plus ONE fresh consolidated correction maximum. Do not dispatch writer from Planner. First post-code phase on the SAME initial installed candidate combines required executed tests, applicable static diagnostics for every changed path, advisor-integration-post and one independent verifier (global-tooling high/normative budget). Writer/verifier must report unavailable tools or partial diagnostics. Post-code advisor raw output must be read by Planner; if a required advisor is genuinely unavailable, stop BLOCKED per Planner authority, never invent a result.

Gate 2 follows post-code advice, writer/verifier evidence and the pre-commit assessment of installed candidate; it occurs BEFORE the work-unit commit and BEFORE PM completes/ticks. A REFINE batches finding IDs into the single correction; install first, correct once, target recheck, rerun Gate 2. Second Gate 2 PASS unless a true blocker remains; record non-blocking later work. A second REFINE/ESCALATE returns the unit to the human. No native post-commit review is Gate 2 input. After a permitted commit, RDD on/global requires assessment of committed candidate against last reviewed boundary and native review where due through authorized owner-controlled surfaces.

Require staged reviewability receipt before commit: authored additions+deletions <=400 and raw authored patch <=100 KiB, generated/binary paths listed separately. No silent size exception, shrinking correct tests or arbitrary boundary changes.

## Planning completion, not implementation completion

After successful plan creation and successful Gate 1 fixed act, the PM may use this exact contract for its separately authorized writer dispatch. No work is marked complete here, no tests have been run by Planner, no implementation source has been edited by Planner, and no deployment or delivery is approved.


## Revisions
- r1 2026-10-25T21:27:09Z planner: Create owner-authorized plan-only Gate 1 binding; preserve exact owner edit texts and record advisor dispositions; no implementation or task completion.
- r2 2026-10-25T22:33:46Z planner: Correct router-placement disposition and record correction 1/1 plus bounded owner micro-fix exception; retain owner-exact edit contract and existing broker-owned gate/revision records.

## Gates
- q90-activate-pm-planner-u1 PASS 2026-10-25T21:27:57Z planner ref=plan odd/tasks/q90-activate-pm-planner-u1.md rev1; advisor-integration-pre ses_e8b37f4eeffeWEkP2s7wDsNjSD RAW; owner-verbatim contract
- q90-activate-pm-planner-u1 REFINE 2026-10-25T22:05:27Z planner ref=post advisor ses_e8af1ac96ffebRoaZ3nf8LjX3v RAW; writer ses_e8b082337ffemXNoeRyOaJ7RGH receipt; verifier 358 OK; 8 pyright joined; router re-append planned :: Gate 2 first pass: installed-candidate technical assessment is not ready to commit. In ONE correction, fix eight Pyright sites in the two test files without weakening assertions, suppressions or losing the None mutation; re-append the planned router row LAST, preserving existing rows 293-298 verbatim; replace the retired byte claim with a fresh measured candidate receipt. Recheck diagnostics, focused tests, affected regressions, scope and tail integrity; return for second Gate 2 BEFORE commit or PM completion. Native committed-candidate assessment stays post-commit.
- q90-activate-pm-planner-u1 PASS 2026-10-25T22:33:52Z planner ref=2nd G2: plan rev2; correction+owner micro-fix readbacks; 21+21/358 OK; PM pyright 0/0; final 291 lines; router placement retraction; no true source blockers
