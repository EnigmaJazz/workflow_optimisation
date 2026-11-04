# Q100 — host_plan_archive permission coverage

## Objective and identity
Restore fail-closed V2 derivation coverage with exactly two canonical configuration insertions and the required non-prompt-config test-pin update in the SAME implementation commit. This is r3 of the existing T1 plan, a scope-recording revision, not a new unit or advice cycle. Permission coverage only, not deployment or archive activation.
- unit_id: q100-host-plan-archive-permission-u1
- task_id: T1
- task_class: global tooling change
- Risk: security-boundary authorization configuration despite the small source diff.
- route: delegated; workflow-route/workflow-odd-secure reloaded, current WORKFLOW.md Planner and finite-budget sections reread. Planner changes only this plan through the fixed act; no writer or review lens dispatch.
- Latest PM-supplied branch/HEAD: chore/coordinator-selection at a8522e4034b8b4df26e1539656bcbeda9d45d3e3. Original anchor 3970311718482b928759c54b537e4a999a27056e. Fixed plan/gate acts commit metadata; PM must refresh actual HEAD/status after r3, not reuse a stale writer anchor.
- RDD mode supplied: on/global, unchanged. Pending review target identity preserved: sha256:029ec5a5bfaeea1927b68da154361b24a952b3fb1823094ec223bad6c176f9ea. This target digest is not a Git baseRef; recover the actual reviewed commit through native authority.
- Owner decision 2026-11-04 preserved: hold open high-risk slice pending, fix blocker first, then one native review over the combined committed tree. Never substitute native review for Gate 2 or imply delivery approval.
- Budget: one original writer plus ONE fresh correction only; r3 does not reset it. Staged receipt must remain below 400 authored changed lines and 100 KiB authored patch, with generated/binary paths separate.

## Observed evidence and supplied state
- Observed in prior reads: derive check_rules:99-117 requires top-level coverage for every scanned tool; build:390-393 checks before writing output; derive_config carries non-plugin configuration. Canonical insertion anchors :876 host_orca_report allow and :2849 host_task_mark deny already have commas.
- Observed in prior reads: RealConfig uses HOME-relative agent-sandbox-integration and may skip without it. Python permission controls may also skip without executable Bun; a skipped pass is not behavioral proof.
- Observed r2 readback: docs/TODO.md:7-13 gates starting on queue registration; Q96 Status/Prerequisites/Source/Description format and Q97-before-## Done insertion boundary established. Absent Q98/Q99 headings remain a separate owner-identified known gap, not fixed here.
- Observed r3 read: tests/test_orchestrator_prompt_source.py:37-38 says deliberate non-prompt config changes must update the pin in the same commit; :39 currently contains the old digest below. This contract is working as designed, not a test to weaken.
- Observed r3 AFT zoom: CoordinatorSelectionRuleTests.test_nonprompt_config_tree_matches_the_pinned_digest:970-987 removes agent.gentle-orchestrator.prompt, serializes JSON with sort_keys=True, separators=(",", ":"), ensure_ascii=False, hashes UTF-8 bytes, compares NONPROMPT_CONFIG_SHA256, then mutates nested explore.permission.edit to prove the digest changes. Keep that test/positive control intact.
- PM-supplied first writer result, exported but NOT installed: session ses_e58b35163ffeJtzLhC1MAIioEz; ref refs/opencode-sandbox/result/ses_e58b35163ffeJtzLhC1MAIioEz; candidate f81e25953d270608949547fa943f839b21cf09df; 3 files/10 insertions (config/TODO/ROUTER). PM reports config and TODO correct; sandbox_apply not called. This is supplied state, not an independently verified installed diff.
- PM-supplied verifier state: gentle-ai-verify BLOCKED on F1 test pin and F2 inaccessible real inventory; 9 worker RealConfig skips. Raw writer/verifier evidence still must accompany Gate 2; this plan records no invented check outcome.
- Observed limitation: Planner attempted host_sandbox_result for that exact session; broker refused ROLE_DENIED_FOR_AFT_READ. Result identity/counts above remain PM-supplied. No sandbox/host execution workaround attempted; an authorized coordinator must supply actual result/install evidence for Gate 2. This optional read limitation does not prevent scope recording, but it is not evidence that a candidate is installed.

## Owner authority and required literal records — 2026-11-04
### Retained Q1/Q2 decisions
Q1 option (b) grants docs/TODO.md for the Q100 entry in this unit; queue-first registration satisfies rather than waives the gate. Q2 option (a) accepts permission coverage only, with overlay unchanged, no archive invocation made/claimed, and no assertion that a config grant establishes runtime prompt authority. Overlay authorization alignment is separate follow-up work, not this patch's prerequisite.
Required verbatim limitation retained in tracker AND ROUTER-LOG row:

> the rule makes the derive succeed and closes the silent-allow hole; it does not establish that any agent is instructed to call host_plan_archive.

This records owner-approved scope/intended effect, not an observed runtime result. Do not claim its first clause is achieved until required real-inventory host proof exists.

### F1 AUTHORIZED — fifth path, one line only
Add tests/test_orchestrator_prompt_source.py to allowed surfaces, changing ONLY line 39 NONPROMPT_CONFIG_SHA256:
- Old: c8f82943a32d7b6665681e61d9d51751a6abf063934a09b7f7af0b8889b3a8e9
- New: 1935dc8da3226b579c49a6de594cac8509130e93ed8a16ec38327a1c7fdc9996
- Exact replacement: `NONPROMPT_CONFIG_SHA256 = "1935dc8da3226b579c49a6de594cac8509130e93ed8a16ec38327a1c7fdc9996"`
No other byte in that file may change. Test-only digest maintenance for the deliberately changed config; no altered assertions, test logic, CURRENT_PROMPT_SHA256 or positive-control behavior. Recompute with the existing test algorithm and execute the test; the new value is the owner-authorized target, not a digest independently measured by Planner. Mismatch stops the unit rather than silently choosing another value. Commit this pin with the two configuration insertions, not a separate implementation commit.

### F2(a) ACCEPTED WITH CONDITION — host proof deferred, not waived
The isolated worker cannot see ~/agent-sandbox-integration. Its 9 RealConfig skips are an environment limitation, NOT a pass. Owner substitution, VERBATIM in this tracker AND the amended ROUTER-LOG row:

> the derive dry run against the real sandbox repo is owner-executed on the host after the commit, and the unit is not DONE until that command's observed output is recorded.

Owner command, Fish-compatible, executed by the OWNER on the host only after the implementation commit:

```fish
cd ~/ai-workspace/workflow_optimisation; python3 scripts/derive-v2-config.py --source global-config --sandbox-repo ~/agent-sandbox-integration --out /tmp/derive-q100
```

Success requires all three: exit 0; no `tools without an explicit permission rule` refusal line; opencode.json written into /tmp/derive-q100. Record actual command/output/exit and generated-file evidence tied to the committed candidate; a stale pre-existing file is not proof of this execution. No command has been executed by Planner. Do not delete/overwrite host files as an agent workaround. If it refuses, the unit reopens and the rule is wrong per owner decision; no automatic extra correction budget is granted.

The explicit F2 substitution supersedes r2's precommit real-inventory dry-run and non-skipped-RealConfig requirement ONLY where that external inventory is unavailable in the isolated worker. Report skips and pending host proof separately; never claim synthetic/worker checks exercise the real inventory. Do not bypass isolation or set host HOME to fetch it. Other verification remains required.

## Exact FIVE allowed surfaces and unchanged non-goals
1. global-config/opencode.json: original exactly two textual insertions, global permission.host_plan_archive deny after host_task_mark and agent.gentle-orchestrator.permission.host_plan_archive allow after host_orca_report; config-only numstat 2 additions/0 deletions. No reserialization/reformatting/other rules.
2. odd/tasks/q100-host-plan-archive-permission.md: same tracker, evidence and truthful state through authorized plan/metadata acts; correction writer must not edit protected plan roots.
3. ROUTER-LOG.md: same one Q100 unit row, retaining old exact limitation and appending F2 verbatim substitution, truthful skips/pending host proof and factual closure fields.
4. docs/TODO.md: original single Q100 entry, adjacent-style Status/Prerequisites none/Source/Description. No extra Q98/Q99 repairs, headings, renumbering or unrelated cleanup. Already correct in first writer result per PM; correction must not edit it.
5. tests/test_orchestrator_prompt_source.py: ONLY the exact old-to-new NONPROMPT_CONFIG_SHA256 line above (1 insertion/1 deletion).

No other test edits, verifier/pin-module edits, prompt/overlay changes, plugin changes, version bumps or live-root writes. The ONLY newly authorized pin is this test constant; verify-workflow.sh, verifier manifest and health-plugin digest remain untouched. No derive --apply, restart, deployment or archive invocation. No push/PR/merge authorized by this technical plan.

## T1 — continuation and ONE correction plan
- [ ] T1: Install original result, apply the single scoped correction, obtain precommit Gate 2 and commit; remain NOT DONE pending recorded owner host proof.

1. Refresh branch/HEAD/status and actual result preview through authorized coordinator tools. Preserve first writer's exact frozen ref/commit above; no new first writer, no rebase/recreation of implementation as a workaround. Resolve divergence/unknown changes before installation.
2. INSTALL FIRST the existing first writer result f81e25953d270608949547fa943f839b21cf09df, 3 files/10 insertions, through the authorized lifecycle with required approval. Planner performs no install. Verify installed diff and actual base before correction; exported bytes are not an installed candidate. Do not mistake the sandbox result commit for the final host implementation commit.
3. Consolidate first-pass findings/evidence on that same original candidate, including owed initial diagnostics/post-code advice if not already present, into ONE correction brief. Scope recording is not a replacement for existing required checks or a new advice cycle. No unnecessary complete rerun of the initial advisor set.
4. PM dispatches ONE FRESH correction writer on that installed base. Its ONLY edit paths/actions: tests/test_orchestrator_prompt_source.py single-line pin replacement, plus amendment of the existing ROUTER-LOG Q100 row to include F2 verbatim and truthful pending proof. Retain the prior scope-limitation sentence. No edits to config/TODO (already correct), no tracker edits, no reformatting/new unit/new plan. Writer returns actual diff and check evidence, not a commit.
5. Record correction_rounds_used=1 when this writer is used; no second correction is silently authorized. Install its result and verify the aggregate installed candidate across the five overall allowed paths. Refresh anchors after every fixed plan/install act.
6. Targeted verifier/post-advisor rechecks cover F1/F2 and affected regressions on installed+corrected bytes. Same committed source must include config and test pin together. Any true remaining/new blocker after the single correction goes to human; non-blockers become later work.

## Verification and Gate 2 — still precommit
- Gate 1 PASS r2 stands and its technical coverage EXTENDS to the exact fifth-path pin line, per owner authority and observed test contract. No new pre-code advisor cycle or new Gate 1 transaction is needed. This is NOT Gate 2, acceptance of runtime behavior, or a passed test.
- Required affected check: python3 -m unittest tests.test_orchestrator_prompt_source -v, including CoordinatorSelectionRuleTests.test_nonprompt_config_tree_matches_the_pinned_digest and its existing mutation positive control. Must execute on installed+corrected candidate; parse/build alone is insufficient. Compare old/new digests against exact authorized target; test-file diff must be precisely one line.
- Retain config exact textual/duplicate-aware JSON checks and all-other-values unchanged; sweep canonical permission maps for exact/wildcard/alias access, no non-orchestrator grant. Real-derived output/inventory-dependent assertions stay pending under F2, not silently counted as passed or replaced by guessed inventory.
- python3 -m unittest tests.test_derive_v2_config -v still runs; report every concrete test ID/count/skip. Worker 9 RealConfig skips are explicitly accepted environment limitation, not success. No required unskipped non-environment failures may be concealed.
- python3 scripts/verifier_manifest.py check passes without updates. Execute bun tests/test_review_pipeline_permissions.js or prove equivalent Python-invoked controls ran non-skipped. Non-vacuity controls on in-memory clones remain applicable where authorized evidence exists; disclose missing real-inventory coverage.
- python3 -m unittest discover -s tests retains documented same-runner/environment failure-ID/error/skip comparison. Missing sqlite3/denied node/HOME=/nonexistent are not blanket waivers. F1 digest mismatch must disappear; F2 skips and deferred host evidence are explicit exceptions, not no-regressions proof.
- Retain first-pass applicable static diagnostics, now including the fifth path; collect F1 changes/targeted Python diagnostics before final decision. Existing first-candidate diagnostics/advice belong to the one consolidated correction batch; report any prior coverage gap honestly, not as retrospectively executed.
- PM obtains actual writer and security-tier gentle-ai-verify evidence, PM check, independent orchestrator readback and precommit assessment on the installed+corrected candidate. Planner requires compulsory advisor-gemini-post evidence (replacing advisor-spec-post, exactly one carrier) with actual diff/code, all owner specification strings including F1/F2, five allowed paths and verification limits. If initial post advice already exists, use its raw result and targeted recheck instead of a full new cycle. Mandatory post advice is not waived by 'no new advice cycle'.
- Gate 2 is issued only AFTER required writer/verifier/post-advisor evidence and precommit assessment, BEFORE final implementation commit and BEFORE PM completion/tick. Explicitly state F2 owner-approved deferred proof and that any technical PASS authorizes no DONE claim. No Gate 2 verdict issued by this scope-recording step. Missing required tool/permission/evidence means BLOCKED, never invented checks or native-review substitution.
- Reviewability receipt on aggregate candidate: below 400 authored changed lines/100 KiB patch, allowed-path inventory, exact config 2/0 and pin 1/1 verified, both literal sentences in the single ROUTER-LOG row. No post-Gate2 byte change without appropriate recheck.

## After commit — conditional completion, not deployment
After Gate 2 PASS, authorized PM commits corrected config and test pin together. Record actual commit, preserve Q100 IN PROGRESS/awaiting owner proof, keep T1 unchecked and do NOT mark unit DONE merely because commit or native review exists. Owner then executes the exact host dry run above. Only after its observed output/exit/generated file evidence is recorded may the PM proceed to truthful completion, subject also to normal review/closure requirements. If it refuses, reopen/escalate; do not weaken F2 or spend another correction automatically.
Native review remains after commit over combined committed tree with held high-risk slice, through provider authority, not Gate2 input or deployment authority. No deployment/restart/archive call. Overlay authorization alignment and route-parity remain separate follow-ups requiring their own queue registration when scheduled; missing Q98/Q99 headings remain out of scope.

## Advice selection and preserved findings
- Existing config-surface advisor advisor-integration-pre (configured opencode-go/mimo-v2.6-flash), session ses_e58d91ef4ffdbrrw5rW4m7uCN7: initial and targeted r2 RAW outputs read. Existing compulsory spec carrier advisor-gemini-pre (configured google/gemini-4-argon), session ses_e58d91ef4ffeFrJqTTfIcwV8eH: initial/r2 RAW outputs read. Original F2/F9/SPEC-F1 resolved explicitly by Q1/Q2; Bun/non-vacuity/argv/format/baseline controls retained.
- r3 dispatches NO new advisors: exact test-pin scope is mechanically established by owner authority and existing test contract, no independent new permission/implementation surface. Gate 1 r2 remains standing. Existing mandatory post-code carrier/checks still owed before Gate2; no new pre/post full cycle is added.
- advisor-spec-pre/post are not dispatched alongside substitute carriers. Subscription Gemini advisors stay undispatched with external lane PLANNED. Extra design/security/testing/maintainability passes remain skipped for the same single permission-config surface; planner-evidence/new explore skipped because exact allowed reads establish this scope change. No missing required advisor is replaced.
- r2 requirements for non-skipped real-inventory tests were superseded ONLY by explicit F2 acceptance with condition. Preserve their historical advice, but do not apply stale r2 precommit acceptance to block the authorized substitution or label a skip a pass.

## Log
- 2026-11-04 — Initial plan/advice and r1 REFINE preserved by broker. r1 fixed plan commit 57be41c026889e546c8f5785832dd205aed5b7b5; gate commit 860f132792802c40c69b6a29b87b9e9cdc2d6a49.
- 2026-11-04 — Explicit Q1/Q2 resolved original blockers; same-advisor targeted rechecks read RAW. r2 fixed plan commit ae11ef17b231c91ee1a810353b19d3547dcf3a4b; Gate1 PASS commit a8522e4034b8b4df26e1539656bcbeda9d45d3e3. This PASS remains standing; prior gates are broker-owned history.
- 2026-11-04 — PM reports exported uninstalled first result and verifier BLOCKED F1/F2. Owner authorizes exact fifth-path pin and postcommit owner proof substitution. Planner reread tracker/current policy/test pin contract and executable digest/positive-control method, records r3 only; no writer/lens, correction, installation, tests or host dry run performed. Result-ref inspection was broker-denied; supplied result details are not independently verified. Gate2 remains pending.


## Revisions
- r1 2026-11-04T15:44:52Z planner: Finalize T1 plan and raw pre-advice dispositions; Gate 1 requires scope/queue authorization resolution before writer.
- r2 2026-11-04T15:59:37Z planner: r2: owner resolves queue/overlay scope; four paths, queue-first Q100 entry and exact limitation; targeted rechecks read. Broker preserves gate history.
- r3 2026-11-04T17:03:02Z planner: r3 scope recording: exact fifth-path test-pin update; owner-only postcommit real-inventory proof; install first then one fresh correction. Gate 1 r2 stands.

## Gates
- T1 REFINE 2026-11-04T15:45:28Z planner ref=odd/tasks/q100-host-plan-archive-permission.md; raw advisors ses_e58d91ef4ffdbrrw5rW4m7uCN7 and ses_e58d91ef4ffeFrJqTTfIcwV8eH :: Before any writer, establish the exact docs/TODO.md queue entry for this unit or obtain explicit scoped owner authority/waiver; TODO is outside the three allowed paths. Resolve overlay.md:213-214 versus the allow-gated archive grant: explicitly scope this to permission coverage with archive use deferred, or authorize separate prompt alignment. Do not infer waivers or expand this patch. Retain exact two insertions, non-skipped real-inventory tests, Bun permission controls, baseline comparison and pre-commit Gate 2. Refresh the writer anchor after the fixed plan commit.
- T1 PASS 2026-11-04T16:01:25Z planner ref=odd/tasks/q100-host-plan-archive-permission.md r2: explicit Q1/Q2 resolve blockers; RAW advisor rechecks read; four-path queue-first scope, exact limitation and unchanged checks confirmed.
