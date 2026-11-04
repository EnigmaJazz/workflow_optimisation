# Q100 — host_plan_archive permission coverage

## Objective and identity
Restore fail-closed V2 derivation coverage with exactly two canonical configuration insertions. Permission coverage only, not deployment or end-to-end archive activation. This is r2 of the EXISTING plan, not a new work unit.
- unit_id: q100-host-plan-archive-permission-u1
- task_id: T1
- task_class: global tooling change
- Risk: security-boundary authorization configuration despite a two-line source diff.
- route: delegated; workflow-route and workflow-odd-secure reloaded. Secure policy requires delegated implementation/execution; Planner dispatches no writer or native review lens.
- PM-supplied branch/current anchor: chore/coordinator-selection at 860f132792802c40c69b6a29b87b9e9cdc2d6a49. Original planning anchor: 3970311718482b928759c54b537e4a999a27056e. Fixed plan/gate acts commit metadata: PM must refresh actual writer HEAD/status afterward, not reuse stale anchors.
- RDD mode supplied: on, source global; never toggle automatically.
- Pending review target identity preserved: sha256:029ec5a5bfaeea1927b68da154361b24a952b3fb1823094ec223bad6c176f9ea. Not established as a Git baseRef; obtain the actual last-reviewed commit from native authority rather than reinterpret this digest.
- Owner decision 2026-11-04 preserved: hold the open high-risk slice pending, fix this blocker first, then run one native review over the combined committed tree. Preserve the pending boundary; no review waiver or delivery approval.
- Forecast: 2 source insertions plus bounded tracker, one Q100 queue entry and one ROUTER-LOG row. Actual staged receipt must remain below 400 authored changed lines and 100 KiB authored patch; generated/binary paths listed separately.
- Delivery strategy: ask-on-risk. No push, PR, merge, restart, deployment or archive execution authorized here.

## Problem and evidence
- Supplied by PM, not executed by Planner: RealConfig derivation fails with `[derive-v2] refused: tools without an explicit permission rule (V2 would allow them silently): host_plan_archive`; absent temporary output causes downstream failures.
- Supplied external evidence, not read by Planner: agent-sandbox-integration tool-specs-host-ops.ts:173-197 defines host_plan_archive, archives finished odd/tasks or odd/mini documents without an approval request, and rejects missing, occupied, escaping, protected, staged or conflicted paths. External implementation is not an edit surface.
- Observed in prior reads: scripts/derive-v2-config.py check_rules:99-117 requires each inventory tool in top-level permission and resolves explicit agent entries over the global value; build:390-393 checks before output; derive_config:355-363 copies non-plugin values.
- Observed in prior reads: global-config/opencode.json identifies gentle-orchestrator at :772, its permission map at :776, host_orca_report allow at :876 and top-level host_task_mark deny at :2849. Both anchors already have commas, enabling pure insertions.
- Observed in prior reads: tests/test_derive_v2_config.py:118 can skip RealConfig without its HOME-relative external checkout; :123 uses temporary --out; :149-153 compares permission maps. tests/test_review_pipeline_permissions.py:836-847 explicitly tests clean skips when Bun cannot execute. A skipped pass is not runtime validation.
- Observed on r2 readback: docs/TODO.md:7-13 gates STARTING on queue registration; Q96 :2288-2304 uses Status/Prerequisites/Source/Description bullets, Q97 :2306-2325 is followed by ## Done at :2327. Q100 belongs at that boundary. Owner identifies absent Q98/Q99 headings as a separate known gap, not fixed here; the readback confirms no intervening headings at this insertion boundary.
- Observed in prior reads: global-config/prompts/gentle-orchestrator/overlay.md:213 authorizes explicitly ask-gated mutations and enumerates other plan tools; :214 separately allows host_test_run. Configuration grants do not establish prompt/broker authority.
- AFT/read fallback followed the local CodeGraph check with no usable index; no index initialization attempted. Planner has not implemented code or executed tests.

## Explicit owner resolutions — 2026-11-04
- Q1 option (b) GRANTED: docs/TODO.md is the fourth allowed path. Writer adds Q100 FIRST, before the config edit, within this same unit. Queue registration is satisfied, not waived. No further owner decision on this prerequisite is needed.
- Q2 option (a) ACCEPTED: permission coverage only. global-config/prompts/gentle-orchestrator/overlay.md stays untouched; no archive invocation is made or claimed; the grant is not runtime prompt authority. Aligning overlay authorization text is a separate follow-up, not a prerequisite to this coverage patch. No inferred waiver is used.
- Required owner limitation, copied VERBATIM into the ROUTER-LOG row as well as this tracker:

> the rule makes the derive succeed and closes the silent-allow hole; it does not establish that any agent is instructed to call host_plan_archive.

This sentence records owner-approved scope/intended effect, not an observed test result. Its first clause is earned only after successful real-inventory execution. If inventory membership or derivation fails, retain pending/failed status and explicit failure evidence; do not claim success from this sentence.

## Exact requested contract and FOUR allowed edit surfaces — r2
Same two-line config diff: global host_plan_archive deny beside :2849 and gentle-orchestrator host_plan_archive allow beside host_orca_report at :876. No other agent gains the tool. No reformatting, reserialization, version bumps or other tool rules.
Owner explicitly supersedes the historical r1 three-path restriction with exactly:
- global-config/opencode.json: precisely two inserted permission entries.
- odd/tasks/q100-host-plan-archive-permission.md: same plan, task state and factual evidence.
- ROUTER-LOG.md: one unit row/factual closure fields, including exact limitation.
- docs/TODO.md: one Q100 entry with problem, fix, prerequisites none and truthful status; no unrelated queue cleanup.
No test-file, prompt, plugin, verifier entry/module/digest, pin or version edits. No live-root writes, derive --apply, restart, deployment, full verifier/self-heal or real archive call. Missing Q98/Q99 headings are a separate known gap, not fixed here; no renumbering or extra queue headings.

## T1 — bounded implementation plan
- [ ] T1: Register Q100 first, add global deny and orchestrator-only allow, execute scoped checks, obtain Gate 2 before commit.

### Readiness and sequence
Owner-controlled queue/scope and overlay prerequisites are RESOLVED explicitly above. The queue prerequisites field is none; ordinary execution preflight and verification are still required.
1. PM/writer verifies actual root, branch, refreshed HEAD/status. Cleanliness is PM-supplied, not executed by Planner; stop on unrelated changes. PM resolves the recipe's writer-tier decision before dispatch; unknown model-family decisions are not inherited.
2. Use only an approved inventory/fixture execution boundary. A registered-project child must not opportunistically inspect/fetch an external checkout. Missing required inventory/tests means BLOCKED/EXTERNAL_CONTEXT_REQUIRED with Purpose, Expected location and Required evidence, not a skipped pass.
3. Writer inserts Q100 before touching global-config/opencode.json. Capture the pre-source-edit regression baseline, then make two targeted config insertions. The queue edit must not alter/mask the source baseline.

### docs/TODO.md Q100 entry — adjacent formatting
Insert `### Q100. host_plan_archive permission coverage` immediately after Q97, before `## Done`, with adjacent-style bullets:
- **Status:** IN PROGRESS (owner-authorized, 2026-11-04); unit q100-host-plan-archive-permission-u1, T1; source and verification pending. Never DONE before Gate 2 and the actual work-unit commit.
- **Prerequisites:** none.
- **Source:** odd/tasks/q100-host-plan-archive-permission.md T1; owner decisions 2026-11-04.
- **Description:** a new host tool shipped without a permission rule, so derive-v2-config.py refuses and the V2 root cannot be derived. Add global deny and gentle-orchestrator allow. Permission coverage only; no archive invocation or deployment.
- **Deferred:** overlay authorization-text alignment is separate follow-up, not this implementation; routing-guard archive parity stays later work. Each requires its own queue entry/prerequisites before separately scheduling or starting; no extra task is created/authorized here.
Use ordinary Markdown bullets/inline code consistent with Q96/Q97. Preserve every other entry and ordering. Assert exactly one Q100 heading and required problem/fix/prerequisites/status fields; do not repair Q98/Q99. Preserve IN PROGRESS through the implementation commit; PM may close metadata afterward with actual commit evidence. No post-Gate2 installed-candidate mutation without rechecking the changed metadata. PM independently checks queue-first evidence: final file contents alone do not prove edit order.

### Configuration approach and behavioral controls
- Tests first: capture existing targeted failures/full-suite baseline before source changes; no new repository test file. Record exact IDs/errors/skips/commands/environment/output references. Expected refusal must name host_plan_archive; unrelated failures in the required fully-passing derive module are blockers, not scope expansion.
- Minimal targeted textual insertions only: top-level permission.host_plan_archive = deny immediately after host_task_mark; agent.gentle-orchestrator.permission.host_plan_archive = allow immediately after host_orca_report. No tools-map entry or serializer roundtrip.
- Validate exact patch and config-only numstat: two added lines/zero deleted lines. Duplicate-aware JSON parse; assert two exact nested values and every other semantic value unchanged from baseline.
- Execute temporary assertions on canonical AND derived output: sweep other agents for exact grants and matching tool-level wildcards, including ask/allow/effective ordering; exclude task-name/read-path submaps. Include derived aliases/access mirrors. Stop on unexplained non-orchestrator access, not extra rule edits. check_rules is not an OpenCode authorization evaluator; disclose unresolved ordering gaps.
- In-memory non-vacuity controls only: inventory contains host_plan_archive; fixed check_rules input passes; removing global rule raises naming host_plan_archive; removing orchestrator grant makes positive grant assertion fail. Assert supplied no-approval inventory semantics; unexpected ask semantics stop unit. Never invoke real archive tool as probe.

### Required verification and acceptance — retained, four-path scope
1. git diff --numstat -- global-config/opencode.json reports exactly 2 additions/0 deletions; textual patch is exactly two intended insertions. Entire changed-path inventory stays within FOUR authorized paths. Check Q100 fields/order and required sentence separately.
2. python3 scripts/derive-v2-config.py --source global-config --sandbox-repo <approved inventory checkout> --out <isolated temporary root> exits 0, no missing-permission refusal; output opencode.json exists and passes permission/agent sweep. Never --apply. Record actual argv/inventory evidence. Argv-safe temporary procedure only, no shell substitutions/pipes; clean temp outputs before export.
3. python3 -m unittest tests.test_derive_v2_config -v fully passes. Concrete RealConfig IDs/counts execute, not skip. Record HOME/approved checkout resolution, no forced host HOME/access bypass. Missing approved inventory is BLOCKED, not reduced acceptance.
4. python3 scripts/verifier_manifest.py check passes without manifest/pin update.
5. python3 -m unittest discover -s tests has no new failure IDs/errors vs documented same-runner/same-environment pre-edit baseline; compare skips too. Missing sqlite3, denied node, HOME=/nonexistent and historical counts are supplied categories, not blanket waivers. Expected derive failures disappear. Unestablished comparison is a gap, not a no-regressions claim.
6. Execute bun tests/test_review_pipeline_permissions.js or prove equivalent Python-invoked Bun controls actually executed non-skipped on same candidate. Record availability/result, no test-file edits.
7. FIRST post-code pass includes aft_inspect or applicable static diagnostics for ALL FOUR paths, required tests/independent verifier/advice on SAME initial candidate. JSON/Markdown structural checks may establish applicable coverage; disclose analyzer gaps. Never first run diagnostics after correction.
8. Tracker records observed argv/exits/counts/IDs/errors/skips/baseline comparison/raw evidence/dispositions/limits. ROUTER-LOG has one global tooling row, pending review/source-only deployment status, tracker reference and the exact owner limitation verbatim. PENDING-COMMIT is valid. Record overlay/route-parity deferrals as later work, not completed behavior. Assert exact sentence text, not paraphrase.
9. Writer returns actual root/branch/refreshed anchor/status, complete diff/path inventory, staged reviewability receipt (authored additions+deletions, raw patch bytes, generated/binary paths separately). No implementation commit before Gate 2. Four-path metadata must match the checked installed candidate.

## Advice selection and RAW evidence — T1 / pre-code
One configuration/derivation authorization surface plus compulsory specification carrier; different model families, no vote/approval claim. r2 is targeted recheck of same findings, not a new full advice cycle or an extra surface advisor.
- advisor-integration-pre selected for permission inheritance/derivation/alias-wildcard controls; configured opencode-go/mimo-v2.6-flash. Session ses_e58d91ef4ffdbrrw5rW4m7uCN7 returned initial advice and targeted r2 F2/F9/F3 recheck; both RAW outputs read.
- advisor-gemini-pre selected as compulsory specification carrier replacing advisor-spec-pre with Antigravity inactive; configured google/gemini-4-argon. Session ses_e58d91ef4ffeFrJqTTfIcwV8eH returned initial advice and targeted r2 SPEC-F1/scope recheck; both RAW outputs read. Exactly one carrier per position.
- advisor-spec-pre skipped because substitute occupies position; advisor-gemini-post reserved for compulsory post position replacing advisor-spec-post, never both.
- Separate security/design/testing/maintainability passes skipped: same narrow permission-config surface covered by configuration advisor plus spec carrier; no independent deployment implementation. Subscription Gemini advisors remain undispatched while external lane PLANNED.
- planner-evidence skipped: bounded own reads plus initial explore sufficed. Initial explore session ses_e58deedc1ffe6ygatfY02aFdot; no extra broad mapping or Gemini gatherer for this resolution recheck.

### Findings and r2 dispositions
- Integration F1 retained: Bun controls/non-skipped equivalent. F4/F6 retained: inventory membership, exact refusal red-to-green, actual RealConfig execution, stop on other derive failures. F5/F7/F8 retained: source/derived sweep, exact middle-map insertions, duplicate-aware parse, coverage-only claim.
- Integration F2/F9 and SPEC-F1: initial blockers RESOLVED by explicit owner Q1/Q2 authority and queue-first four-path plan. Both RAW targeted rechecks confirm resolution; no inferred waiver/overlay edit.
- Integration F3: route-parity later work; no archive invocation/broader activation. Deferral recorded in tracker/ROUTER row and Q100 description without inventing another unit.
- Targeted Integration R1: follow-ups require separate queue registration when separately scheduled; Q100 records deferral, not implementation. R2: exact mandatory sentence is owner-specified scope/intended effect until runtime evidence proves success; failures remain pending/failed.
- SPEC-F2/F3/F4 retained: approved environment, argv-safe probes, insertion anchors; no forced host HOME bypass.
- SPEC-R2-N1: IN PROGRESS at implementation commit, evidence-based PM metadata closure afterward; installed candidate not changed after Gate2 without recheck. Neither targeted advisor reported a new blocker.

## Post-code and Gate 2 handoff
PM dispatches authorized ODD writer after Gate 1; Planner does not. Security/global-tooling budget owes one independent gentle-ai-verify (security tier, PM/orchestrator dispatched), PM self-check and independent orchestrator readback. After writer/verifier evidence and first-pass four-path diagnostics, Planner dispatches advisor-gemini-post with exact specification, four allowed paths, actual diff/code/results; no advisor-spec-post duplicate. Advice is evidence, never approval.

Gate 2 requires installed candidate, writer/verifier/post-advisor evidence and pre-commit assessment BEFORE implementation commit and BEFORE PM ticks/completes T1. Missing required tool/evidence stops BLOCKED; native postcommit review is not a substitute. One initial writer plus ONE consolidated fresh correction maximum; targeted recheck and Gate 2 again after revision. Second Gate 2 passes unless a true blocker remains; second REFINE/ESCALATE returns human, non-blockers become later work. Planning r2 is not a code correction and does not reset correction budget.

After Gate 2 PASS, authorized PM commit/metadata closure apply. Record actual commit/native assessment. Owner-requested native review is afterward over combined committed tree with held high-risk slice, through provider-returned authority, never Gate2 input. Pending review is not delivery/deployment approval. Do not archive this tracker in verification/closure under this coverage-only unit.

## Log
- 2026-11-04 — Initial Planner read route/ODD contracts, inspected configuration/derivation/tests, dispatched configuration advisor and compulsory API spec carrier independently, read both RAW outputs. No implementation/tests/deployment/native review/writer dispatch performed.
- r1 Gate1 REFINE: queue-scope/overlay prerequisites unresolved then. Fixed plan commit 57be41c026889e546c8f5785832dd205aed5b7b5; fixed gate commit 860f132792802c40c69b6a29b87b9e9cdc2d6a49. Prior gate/revision history is broker-owned and retained, not rewritten as PASS.
- 2026-11-04 — Owner explicitly granted fourth-path Q100 entry and accepted coverage-only limitation. Planner reread same tracker/queue gate/Q96-Q97 formatting, drafted r2, obtained targeted same-advisor rechecks, read RAW results and incorporated non-blocking recording guardrails. Original plan blockers resolved. T1 remains unchecked; no runtime success claimed; technical outcome appended separately by host_gate_verdict.


## Revisions
- r1 2026-11-04T15:44:52Z planner: Finalize T1 plan and raw pre-advice dispositions; Gate 1 requires scope/queue authorization resolution before writer.
- r2 2026-11-04T15:59:37Z planner: r2: owner resolves queue/overlay scope; four paths, queue-first Q100 entry and exact limitation; targeted rechecks read. Broker preserves gate history.

## Gates
- T1 REFINE 2026-11-04T15:45:28Z planner ref=odd/tasks/q100-host-plan-archive-permission.md; raw advisors ses_e58d91ef4ffdbrrw5rW4m7uCN7 and ses_e58d91ef4ffeFrJqTTfIcwV8eH :: Before any writer, establish the exact docs/TODO.md queue entry for this unit or obtain explicit scoped owner authority/waiver; TODO is outside the three allowed paths. Resolve overlay.md:213-214 versus the allow-gated archive grant: explicitly scope this to permission coverage with archive use deferred, or authorize separate prompt alignment. Do not infer waivers or expand this patch. Retain exact two insertions, non-skipped real-inventory tests, Bun permission controls, baseline comparison and pre-commit Gate 2. Refresh the writer anchor after the fixed plan commit.
