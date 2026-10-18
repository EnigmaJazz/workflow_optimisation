# Q72 — Tiny-fix route (direct delegation, no PM, no tracker)

**Feature:** workflow routing adjustment (unit A of four)
**Task ID:** q72-tiny-fix-route (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice created; T1 pending).
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

Add a **tiny-fix route** for genuinely tiny work (a few lines, or a config value) as a direct delegation: no PM, no ODD tracker, no advice record, no review slices. Available to the orchestrator AND to both PMs as a mid-unit quick fix.

## Problem

gentle-ai v4.2.0 introduced an INLINE boundary (~100 authored lines stay inline, PR #5530 / issue #5529) that cannot map onto this setup: `gentle-orchestrator` has NO write availability, so every mutation is delegated. Adopting v4.2.0 verbatim would re-introduce an impossible instruction on the next `gentle-ai sync` re-render. Separately, the existing machinery does not support a tracker-less dispatch:
- The routing guard's stage model requires `advice → tracker` (ODD) or `advice → plan` (systematic) before a specialist writer may be dispatched (`global-config/plugins/lib/routing-guard-helpers.ts:66-103`), and `gentle-ai-worker` is already in `SPECIALIST_WRITERS`/`ODD_SPECIALIST_WRITERS` (`:18-19`).
- `systematic-routing-guard.ts:968-980` warns when the ORCHESTRATOR dispatches any writer, so every tiny fix would emit a warning (warning-only today; `:874` records that a future rollout could throw).
- Neither PM can reach the intended writer: `pm-odd` allows only `odd-apply` as a writer (`opencode.json:1995-2009`) and `pm-systematic` allows `systematic-implementer` etc. (`:2115-2138`) — neither lists `gentle-ai-worker` or `gentle-ai-verify`.
- The PM task allowlists are structurally UNTESTED: `verify-workflow.sh:2851` asserts only `pm-odd.task["odd-apply"]` and `:2942` the wildcard rules; nothing asserts writer membership.
- Already true (so the real delta is smaller): the `Tiny fix` Task Classes row exists at `WORKFLOW.md:116`; `workflow-systematic/SKILL.md:10` already permits tiny fixes via one writer; `gentle-orchestrator` already has `"gentle-ai-worker": "allow"` (`opencode.json:482`).

## Scope

### In scope

T1: (a) a tiny-fix exemption/stage in the routing guard so a tracker-less tiny dispatch does not warn, with a paired non-vacuous test; (b) add BOTH `gentle-ai-worker` AND `gentle-ai-verify` to both PM task allowlists; (c) edit the `Tiny fix` row in `WORKFLOW.md:116` to name the route, the boundary, and that no tracker/advice/slices are created; (d) an escalation backstop; (e) align `workflow-route/SKILL.md`, `workflow-odd-secure` and `workflow-systematic/SKILL.md:10`; (f) add the tiny-fix option to both PM prompts; (g) a committed `tests/test_pm_task_allowlists.py`.

Added by the 2026-10-15 external advice (three omitted surfaces):

- (h) edit `global-config/prompts/gentle-orchestrator/overlay.md` to map upstream's direct-inline case to the Tiny-fix route via `gentle-ai-worker`, anchored on a stable marker;
- (i) regenerate the assembled prompt into `global-config/opencode.json:590` (with `CURRENT_PROMPT_SHA256` and the `normative-ledger.md` pin updated in the same change);
- (j) update `verify-workflow.sh`'s `forbiddenPromptFragments` (`:2974-2983`) to also block the v4.2.0 inline strings, OR add a Python prompt test asserting them if the verifier edit is deferred to a follow-up unit (a verifier edit additionally requires `VERIFY_SCRIPT_SHA256` re-pinned last).

### Out of scope

- the v4.2.0 400-line slice alignment (unit B);
- the advisory-strategy change (unit C);
- the Q71 PM-half fix (unit D);
- any change to `docs/specs/pm-handoff.md`.

## Owner decisions (2026-10-15, do not re-litigate)

- **SUPERSEDED by Q74 (owner decision, 2026-10-17):** the tiny-fix writer is `general` (`openai/gpt-6-luna`), not `gentle-ai-worker`. The writer must be from a different model family than the DeepSeek orchestrator; the earlier DeepSeek writer choice violated that independence requirement. Q74 records the decision and rationale.
- `gentle-ai-verify` is ALSO added to both PM allowlists, so a PM can still obtain a model-independent verification when it wants one; it is optional rather than excluded.
- The guard gets an **exemption** (not "accept the warning").
- Verification for tiny = **structural readback + the native RDD checkpoint**; the native review (different models) is the independence layer. **SUPERSEDED 2026-10-15 — the external advice disproved this premise; see the post-external-advice decisions below.**

## Owner decisions (2026-10-15, post-external-advice)

External advisory (interim lane, two independent hosts) corrected the unit's scope and settled four points:

- **(a) The guard change is a SCOPED ONE-SHOT PERMIT gated on an explicit tiny-fix signal — never an agent-name bypass.** A blanket exemption keyed on `gentle-ai-worker` or on "tracker-less" would disable the writer-bypass and stage gates for substantial work (F1/F02); the permit is consumed once and scoped to the tiny unit.
- **(b) Tiny fix is PASSIVE-ONLY.** A medium/high-risk assessment or RDD-off **automatically ESCALATES out of Tiny fix** (F3/F06). `review_due` is true only for high risk, so passive/`under_budget` tiny commits get zero 4R lenses; native review is not the independence layer.
- **(c) SUPERSEDED by Q74 (owner decision, 2026-10-17):** the writer is `general` (`openai/gpt-6-luna`), not `gentle-ai-worker` or its local tier. This non-DeepSeek writer is required for model-family independence from the DeepSeek orchestrator.
- **(d) PM allows gain `general`, `gentle-ai-worker`, `gentle-ai-worker-local`, `gentle-ai-verify`, `gentle-ai-verify-astra`.**

## Constraints

- `WORKFLOW.md:125` ("Decision content, not file count… never selects a route") and `:128` ("Risk, changed-line count, file count, or perceived complexity alone never selects a route") must NOT be contradicted: the escalation backstop must be worded as **escalation-only** ("decision content selects tiny; exceeding the tiny boundary escalates out"), never as a selector.
- `WORKFLOW.md:446` defines "trivial" as "trivial document edits, and clearly bounded few-line changes with no contract or security effect" — the new boundary must reference it.
- The guard change MUST carry a paired non-vacuous test (an absence assertion needs a positive control).
- `VERIFY_SCRIPT_SHA256` re-pin is required ONLY if `verify-workflow.sh` itself is edited (it must be re-pinned LAST in that same commit); the guard is a plugin, not the verifier.
- The PM prompts are inline JSON strings and must be edited byte-preservingly (valid JSON, keep `\n` escapes and 2-space indent) and stay under the ~6,000-char cap (`docs/specs/pm-handoff.md:11`; currently ~2,106 and ~2,120).
- Branch `chore/pm-layer-completion`; never commit; never switch branches.
- **Hard ONE-WAY tripwire (an escalation boundary, never a selector).** Escalate out of Tiny fix when the authored diff is >20 changed lines, touches >2 files, adds or deletes a file, or edits a denylisted path (`verify-workflow.sh`, `global-config/opencode.json`, `global-config/systematic.jsonc`, `global-config/plugins/**`, permissions/auth/crypto, or public API contracts). Checked BEFORE `sandbox_apply` because the worker has one lifecycle; one-way only so `WORKFLOW.md:125`/`:128` stay true; the threshold is pinned in a test so it cannot rot.

## Acceptance criteria

- a tracker-less tiny dispatch does not warn;
- both PMs can reach the Q74-selected tiny-fix writer `general`, plus `gentle-ai-verify`;
- the `Tiny fix` row names the route, boundary and no-artifact rule;
- the backstop is escalation-only wording and does not contradict `:125`/`:128`;
- a committed test proves the allowlist membership non-vacuously;
- no existing check is weakened;
- the routing-guard and python suites stay green;
- **PM-verifiable traces:** a `ROUTER-LOG.md` row per tiny fix (written inside the worker's brief, since the read-only orchestrator cannot), and a tracker `## Log` entry for PM mid-unit tiny fixes. The permit-consumption log line is the guard's own diagnostic record, observed by whoever audits the guard log; it is not a PM obligation, and its absence MUST NOT block a unit. A scan flagging over-threshold `tiny` commits remains a separate host check.

## Authorized scope

T1: `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts`, `tests/routing-guard/routing-guard.test.ts`, `global-config/opencode.json` (the two PM prompts + the two task allowlists + the regenerated orchestrator prompt at `:590`, T1 (i)), `global-config/prompts/gentle-orchestrator/overlay.md` (T1 (h): maps the upstream direct-inline case to the Tiny-fix route), `global-config/prompts/gentle-orchestrator/normative-ledger.md` (T1 (i): the prompt-sha pin), `tests/test_orchestrator_prompt_source.py` (T1 (i): `CURRENT_PROMPT_SHA256`), `WORKFLOW.md`, `global-config/skills/workflow-route/SKILL.md`, `global-config/skills/workflow-odd-secure/SKILL.md` (+ its references if needed), `global-config/skills/workflow-systematic/SKILL.md`, `tests/test_pm_task_allowlists.py` (new). Plus this tracker, the advice record, `ROUTER-LOG.md`. T1 (j) `verify-workflow.sh` (`forbiddenPromptFragments`, `:2974-2983`) is in scope, with `VERIFY_SCRIPT_SHA256` re-pinned last in `global-config/plugins/workflow-health-check.ts`.

## Checks

- a fake-HOME `bun test tests/routing-guard` (green, including the new exemption control);
- `python3 -m unittest discover -s tests`;
- `python3 -m unittest tests.test_pm_task_allowlists -v`;
- `python3 -c 'import json; json.load(open("global-config/opencode.json"))'` rc 0;
- a per-PM membership probe;
- `bash -n verify-workflow.sh` only if it changed;
- the digest pin equal to `sha256sum verify-workflow.sh` only if it changed.

## Tasks

- [ ] T1 — the scoped one-shot tiny-fix permit in the guard (gated on an explicit tiny-fix signal, never an agent name) + its non-vacuous seeded test (seed both `message(sid, "gentle-orchestrator")` and a valid route key); the PM allows (`gentle-ai-worker`, `gentle-ai-worker-local`, `gentle-ai-verify`, `gentle-ai-verify-astra` for both PMs); `overlay.md` (direct-inline → Tiny-fix mapping) + the regenerated `opencode.json:590` prompt + `forbiddenPromptFragments`; the pre-install one-way tripwire (`host_sandbox_result` inspected before `host_sandbox_result_install`) + its pinning test; the required traces (permit-consumption log line, `ROUTER-LOG.md` row, over-threshold scan, PM `## Log` entry); `tests/test_pm_task_allowlists.py` with a mutation positive control (and a live-mirror assertion); the `-astra` normalization in `pmRequiredRouteSkill`; and the record.

## Delivery strategy

**Chosen strategy:** `stacked-to-main` (owner decision 2026-10-14).

**Forecast (authored additions + deletions, generated files excluded):** T0 ≈ 200; T1 ≈ 180 (guard + helper + guard test + 2 JSON regions + WORKFLOW row + 3 skill edits + 2 prompt insertions + the new test). **Forecast total ≈ 380**, under the about-400 accumulated threshold.

**Selected AT tracker creation** per `odd-and-review.md:36`.

## Progress

- 2026-10-18: Q76 signal correction — the third live `pm-odd` smoke test confirmed the Task schema exposes `description`, `prompt`, `subagent_type`, `task_id`, and `command`, but no `tiny_fix` argument. The guard now detects only `[tiny-fix]` as the first token of Task `description`; ordinary text such as “tiny fix for the routing guard” does not arm the permit. Q75 candidate-set binding and first matching-child consumption remain unchanged. The routing-guard suite baseline was 103 passing tests; the marker-control test failed before the implementation update. No commit or branch switch.
- 2026-10-16: T0 — tracker, advice record and queue entry created; delivery strategy selected at creation. No source edit yet. Route: delegated.
- 2026-10-15: External advisory (interim lane, two hosts) recorded; two BLOCKERs found (a blanket exemption would disable the writer-bypass and stage gates; the native-review independence premise is false for passive/under_budget tiny commits) plus a scope omission (overlay.md, the regenerated prompt, forbiddenPromptFragments). Owner decided: scoped one-shot permit; Tiny fix is PASSIVE-ONLY with automatic escalation. T1 scope revised accordingly; not yet dispatched.
- 2026-10-16: T1a — scoped ONE-SHOT tiny-fix permit implemented in `systematic-routing-guard.ts`: an explicit `tiny_fix` task flag (read then stripped before the host sees it) short-circuits the orchestrator-writer, advice, and tracker/plan stage gates for that dispatch; a WRITER dispatch arms a one-shot in-memory permit that the `session.created` event extends to the child session, covering the child's own `sandbox_*` writes at the ODD bootstrap gate. No key or artifact marker is minted; a permit-consumption log line is emitted. `pmRequiredRouteSkill` now strips a `-astra` suffix. Both PM task allowlists gain `gentle-ai-worker`, `gentle-ai-worker-local`, `gentle-ai-verify`, `gentle-ai-verify-astra`. New `tests/test_pm_task_allowlists.py` (with a mutation PositiveControl) and the guard suite's four permit cases + separate child-bootstrap case + Astra-alias case. Baseline 96 → 102 routing-guard tests, 139 → 145 python tests; both green; `json.tool` rc 0. T1b (prompts, route skills, WORKFLOW.md, verifier) remains open. Not committed — the PM commits.

- 2026-10-17: T1b — `WORKFLOW.md` tiny-fix table and passive boundary now name the route/writer, no-artifact property, passive risk escalation, escalation-only constants and required traces; `workflow-route/SKILL.md`, `workflow-odd-secure/SKILL.md`, and `workflow-systematic/SKILL.md` align selection and delegated writer (including the exception to generic fallback); `overlay.md` rejects upstream inline execution and maps it to the delegated Tiny-fix writer; `opencode.json` has byte-preserving additions to both PM prompts and the regenerated embedded orchestrator prompt; `systematic-routing-guard.ts` defines threshold/denylist constants and the escalation predicate; `tests/test_tiny_fix_route.py` covers constants, denylist, PM prompt cap, prompt three-way equality and positive controls; `verify-workflow.sh` checks all four PM task agents against recovered live config and adds contractual anchor manifest/token rows; `test_orchestrator_prompt_source.py` and `normative-ledger.md` carry the assembled hash; `workflow-health-check.ts` repins the verifier digest last. Assembled prompt SHA-256 `a56c4f5dd7014089226877dce2bb011bb32fc84760a3d7fb7f4c30d5f0d0dcec` (53,348 bytes; 409 lines; +352 bytes/+2 lines). Tests: tiny-fix 5, anchor manifest 7, prompt source 22, PM allowlists 6, routing guard 103 passed; full Python suite 178 tests, 10 errors from sandbox `node` denial. Positive-control mutations removed the threshold, denylisted opencode path, PM prompt option, and embedded route phrase; each affected check failed, and values were restored. Deferred v4.2.0 inline-fragment additions because `base.md` remains pinned to gentle-ai v4.0.0, making those literals dead code. Runtime pre-apply escalation is not repo-testable because the orchestrator cannot observe a diff mid-flight; falsifier: a host workflow permits an over-threshold or denylisted candidate to remain Tiny fix at pre-apply assessment. Full verifier cannot run in sandbox (host paths and `node` denied); owner deploy step remains.

- 2026-10-17: R3-02 reliability correction — replaced the Python `fnmatch.fnmatchcase` mirror in `tests/test_tiny_fix_route.py` with extraction and execution of the actual TypeScript constants and `tinyFixEscalationRequired` predicate using `bun -e`. Added executed assertions for >20 authored lines (escalates), >2 touched files (escalates), a denylisted path (escalates), and a benign one-file/one-line change (does not escalate). The PositiveControl perturbs the extracted predicate's line-threshold comparison and observes the expected-result assertion raise `AssertionError`. `node --version` is denied (`EACCES`), but Bun is available and successfully executes the extracted shipped code; this task did not stop or fall back to a Python copy. Focused tiny-fix tests: 9 passed. Full Python discovery: 182 tests, 172 passed and 10 errors from unrelated node-dependent Gemini advisor tests (`PermissionError: node`); routing-guard: 103 passed, 0 failed; `git diff --check` clean.

- 2026-10-17: Q72 T1b anchor-manifest correction — four `ANCHOR_KEYSTONE_MISSING` rows used their own anchor IDs as keystones, which cannot occur in `anchor_block_body` output because its extraction excludes marker lines; replaced each with a stable literal from its block body. The tiny-fix overlay begin marker shared a line with preceding prose, so `anchor_check_row`'s exact-line counter found begin=0/end=1; moved it onto its own line in `global-config/prompts/gentle-orchestrator/overlay.md` and kept the manifest path pointed at that file. The overlay token failure followed from failed extraction. Removed the `workflow.route-decision` token requiring executable-file wording absent from that WORKFLOW block; retained its other token rows. Added a self-referential-keystone test with a PositiveControl. The embedded prompt, prompt hash, and normative ledger were regenerated together (prompt SHA-256 `8b19b9d02a14c004007b87fa5c343ad9ff7d70a12309c9f753775f5734a1ca4e`). Extracted verifier loops passed 38/38 anchors and 96/96 tokens; anchor-manifest 10/10, tiny-fix 9/9, prompt-source 22/22, routing-guard 103/103, and `bash -n` passed. Full Python discovery ran 185 tests: 175 passed and 10 errored because the sandbox denies `node` (`PermissionError: [Errno 13]`). Verifier SHA-256 and configured health-plugin pin both `40f3d763dda357787c4e481bf0d068161616635844ebb295cbf607d7ac15fc44`. No commit; ROUTER-LOG row uses `PENDING-COMMIT`.
- 2026-10-18: Fourth live `pm-odd` smoke-test corrections: clarified per-dispatcher model-family independent tiny-fix writers (orchestrator → `general`; PM → `odd-apply`/`gentle-ai-worker`), required `ROUTER-LOG.md` in the same writer's authorized paths, and made the PM `## Log` part of its sanctioned tracker update rather than an acceptance exclusion. Added a configured-model and same-family positive-control test. Focused tiny-fix tests pass 11/11, PM allowlist tests pass 8/8, and full Python discovery ran 212 tests (201 passed, 10 errored because the sandbox denies `node`, 1 skipped). The PM same-family positive control passed; disabling its family-comparison mechanism made that test fail with `same-family PM writer was not detected: []`, then the check was restored. Anchor/token verifier control passes 39/39 anchors and 99/99 tokens. No commit or branch switch.
- 2026-10-18: Added explicit Tiny-fix commit closure semantics: PM-dispatched fixes commit the applied implementation and then applicable metadata in the separate metadata work unit before DONE; orchestrator-dispatched fixes commit after the writer's applied result. Tiny-fix briefs must permit the applicable commit, and the `ROUTER-LOG.md` commit field is completed at closure (`PENDING-COMMIT` is valid mid-unit). `python3 -m unittest tests.test_tiny_fix_route -v`: 11/11 passed. `python3 -m unittest tests.test_anchor_manifest -v`: 11/11 passed; verifier reported 39/39 anchors and 99/99 tokens. Full Python discovery ran 212 tests: 201 passed, 10 errored because execution of `node` is denied in the sandbox, and 1 skipped. `git diff --check` passed.

- 2026-10-18: Owner correction (2026-10-17): post-code advice runs before commit and its blockers must be resolved before the commit; native risk assessment runs after installation and commit against the committed candidate. Corrected `WORKFLOW.md`, the PM handoff contract, the ODD review reference/skill, and the orchestrator prompt overlay to remove the pre-apply assessment requirement. That requirement was a contract error, not a tooling gap: `host_review_assess` accepts current-change or Git-range selectors, not an uninstalled sandbox result. No PM prompt content required edits; PM prompts point to the normative closure contract. Checks: PM handoff 10/10; review cadence 2/2; anchor manifest 11/11 (39 anchors, 99 tokens); orchestrator prompt 27/27; `bash -n verify-workflow.sh` and `git diff --check` passed. Full Python discovery: 215 run, 204 passed, 10 errored because sandbox denied `node`, 1 skipped. Reverting the PM ordering clause failed the contract test; reverting the prompt overlay failed the assembler/embedded equality test. Prompt SHA-256 `bd6e207964e3738265471c3391a4c97d834c742b76101e1ec57287601772ae1c`, 55,353 bytes / 414 lines, generated delta +107 bytes / 0 lines. Verifier pin and script digest both `760350a3231e379cf82f53d7d9601206d0484e71786839660fb90a62e4d1d430`. No commit or branch switch.

- 2026-10-18: Owner contract correction: Q72 tiny-fix supports both a PM mid-unit fix using an existing tracker's full anchor and a standalone PM tiny fix with no tracker-derived anchor components but a required branch HEAD SHA. Updated the PM handoff spec, route wording, and positive-control test. PM handoff 12/12, tiny-fix route 11/11, and anchor manifest 11/11 passed; `git diff --check` passed. Full Python discovery ran 218 tests: 207 passed, 10 errored because sandbox execution of `node` is denied, and 1 skipped. The positive control removing all standalone-tiny-fix text failed the contract assertion as expected. No commit.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 revised scope (see the owner-decisions subsection), then native review, then the metadata record. The `-astra` normalization and the live-mirror allowlist assertion may be split into a follow-up if T1 exceeds the review budget.

## Native review outcome and adjudication — 2026-10-17

- **Reported lineage outcome:** `review-96fe567778db7a48` (high tier; 190 changed lines; 14 paths) ended **ESCALATED — not approved, not corrected**, with `action: stop`, `cause: unknown_causality`, and finding `R3-03`. This is recorded as escalation, never approval. A bounded exact search of the repository found no local occurrence of this lineage, so the provider outcome is not independently verifiable here by a repository `path:line` reference.
- **R3-03 (CRITICAL) — REFUTED.** The finding said ANCHOR_MANIFEST rows put a descriptive label where a repository-relative path belongs. The consumer parses each row into `anchor_id`, `anchor_file`, `anchor_label`, and `anchor_key`, then passes `anchor_label` as the label argument (`verify-workflow.sh:4468-4469`, `:4567-4569`). The manifest rows use that field for labels such as `WORKFLOW.md` and `route: delegated` (`verify-workflow.sh:4527-4564`); the manifest format has no path field. The cited consumer and manifest therefore contradict the finding's schema premise.
- **R3-01 (CRITICAL) — provider-refuter reported REFUTED; disposition remains OPEN here.** The stated refuter proof records that no runtime probe was available. The proof itself is not present at a repository `path:line` location in this workspace, so this record does not claim independent verification or close the finding.
- **R3-02 (WARNING) — VALID and FIXED** in commit `7c7cf40`. The earlier test duplicated denylist matching with Python `fnmatch`, unlike the plugin predicate; the correction extracts and executes the shipped TypeScript predicate with `bun -e` and tests its outcomes (`odd/tasks/q72-tiny-fix-route.md:113`; test implementation: `tests/test_tiny_fix_route.py`).
- The two Q72 commits on this branch are `4792ad3` (tiny-fix route contract) and `7c7cf40` (predicate-test correction). The first is confirmed by its commit summary; the second is confirmed by its commit summary and the progress record above.

## T1a design (revised 2026-10-15, post-advisory)

Two pre-code advisories returned SIX BLOCKERs against the first T1a sketch. The permit design was changed as follows.

### Blockers found
- B1: a skill-minted key PERSISTS and leaks — keys live through the 3-hop inheritance chain and refresh on any activity, so a consumed permit can silently re-activate for later substantial work.
- B2: stage markers are copied child-to-parent with no expiry or scope, so a tiny-fix marker would silently exempt later work in the parent or sibling sessions.
- B3: the orchestrator warning reads getWorkflowKeyStatus, which WALKS ANCESTORS — an inherited permit could satisfy it. The exemption must read only the current task args.
- B4: a PM dispatch DOES trip the stage-gate loop (systematic-routing-guard.ts:982-1010); the first sketch only covered the orchestrator warning and the bootstrap warning.
- B5: the child worker's own sandbox_write cannot inherit a permit — `.parent` and `inherited.key` are written only AFTER the task returns (systematic-routing-guard.ts:1045-1090).
- B6: pmRequiredRouteSkill needs the -astra strip, and astra-sol-upgrade.ts must be checked for hard-coded agent names.

### Locked design
1. The permit is signaled only by the exact `[tiny-fix]` token at the start of Task `description` — NOT by agent name, loose prose, or a minted key. No persisted state, nothing to leak, no ancestor walk. This replaces the original unsupported `tiny_fix` task-argument signal; the actual Task schema exposes no such argument.
2. It short-circuits EVERY stage gate for that dispatch: orchestrator-writer, ODD bootstrap, advice stage, tracker/plan stage.
3. Child writes are covered by an IN-MEMORY permit map keyed by child session id — not by file inheritance.
4. No artifact-* or skill-* marker is minted, so nothing the existing stage loops can match.
5. Astra: option alpha — assert the three source-canonical keys, plus a SEPARATE live-mirror check, because gentle-ai-verify-astra is a runtime alias, not a source key.
6. The escalation tripwire moves INTO CODE: the worker computes the threshold and denylist itself and returns ESCALATE rather than installing. Prose cannot enforce it, and host_sandbox_result_install is only ask-gated for PMs.
7. The verifier-side allowlist assertion is DEFERRED: it needs a re-pin, and the verifier reads the recovered config, so it would not close the live-drift gap.
8. Tests: four guard cases (exemption; paired positive control; not-global; not-over-broad), a SEPARATE bootstrap-suppression case, PositiveControl x3 for the allowlist test, and a recorded baseline pass count.

### Advisor uncertainties (recorded, not resolved)
The exact signal form; whether the advice-stage gate is lifted; and that neither advisor ran any code.

## T1b scope (revised 2026-10-15, post-advisory)

Two pre-code advisories returned 4 BLOCKERs and several warnings. Revised scope:

### Deferred (with reason)
- `forbiddenPromptFragments` v4.2.0 entries: DEFERRED. `base.md` is still pinned to gentle-ai v4.0.0 (`tests/test_orchestrator_prompt_source.py:28`, `normative-ledger.md:6`), so the v4.2.0 inline strings are NOT in the source and the fragments would be dead code. Revisit when the v4.2.0 re-render lands. Do NOT invent the literals.

### Added (closing gaps the advisories found)
- PM allowlist assertions IN `verify-workflow.sh` (the unit edits that file anyway): assert the four keys on both PMs against the RECOVERED live config. This closes the live-mirror drift gap that `tests/test_pm_task_allowlists.py` cannot (it reads only the source copy).
- `tests/test_pm_layer_prompts.py`: add per-PM needles for the tiny-fix option text, with a PositiveControl. Currently unpinned.
- Tripwire constants + a test: the thresholds (>20 authored lines, >2 files, any add/delete, denylisted paths) must exist as code constants and be asserted. Currently the "hard tripwire" is prose only.
- New overlay block, if introduced: add its id to `REQUIRED_IDS` and its heading to `SIGNATURES` in `tests/test_orchestrator_prompt_source.py`, or it can be silently removed.
- Anchor tokens for the new `Tiny fix` row wording and for each edited route skill.
- Checks must include `bash verify-workflow.sh` AND `bash -n verify-workflow.sh`: the verifier is the ONLY check that closes embedded-prompt-vs-assembled-bytes; the python suite never compares the embedded bytes.

### Corrected
- `WORKFLOW.md` must NOT repeat the tripwire numbers: stating a line count as a boundary would contradict `WORKFLOW.md:125`/`:128` ("changed-line count never selects a route"). State the boundary as ESCALATION-ONLY and reference the worker constants plus the pinning test as the source of truth.
- The host-only traces (permit-consumption log, ROUTER-LOG row, over-threshold scan, PM `## Log` entry) must be annotated as HOST-ONLY in the Checks list; they are not mechanically testable from this repo.
- The `-astra` normalization is DONE in T1a (`routing-guard-helpers.ts:41-49`), so it is not T1b scope; the T1 task line is stale.
- The 6th routing-guard case (Astra alias) WAS added in T1a at `tests/routing-guard/routing-guard.test.ts:1056-1061`; the advisor could not see it because it read only to line 500. No gap.
