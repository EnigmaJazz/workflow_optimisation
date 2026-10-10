# gentle-ai v4 upgrade — workflow documents (Q30)

**Feature:** gentle-ai v4 upgrade / queue Q30 (workflow documents). **Task ID:** T1 (stable).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Unit status:** SLICE 1 INSTALLED (PM-supplied host commit `2db43a2`; sandbox baseline `ade9919` observed carrying the same three-path slice change) — WORKFLOW.md evidence budget applied (Mapping + Long-session backstop bullets); post-code advice observed (`advisor-integration-post`) and its single required fix applied in this refinement delta; PM commit and native review pending (Q30 retained).
**This unit:** slice-1 refinement writer (sandbox `odd-apply`, fresh worker, Task `ses_edbc5062bffebXomOvL1LqcGg8`; prior refinement writer `ses_edb98fc7bffevHGT1pBsTAuuAm` ended terminal `fallback_chain_exhausted` with no recoverable result). Only this tracker and `odd/advice/gentle-ai-v4.md` change; `WORKFLOW.md` is untouched; no deployment, commit, native review, push, PR, merge, or change set.
**Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07; observed as this worker's model, matching the selected cloud decision).

## Objective
Upgrade this repository's workflow documents to the gentle-ai v4 route: remove SDD from the
canonical recipe, the AGENTS entrypoint, and the route skills; rewrite Task Classes and the
selection rules to the Q29a former-SDD route; replace file-count mapping delegation with the v4
evidence budget; delete the retired `workflow-sdd-secure/` skill — while preserving the surfaces
owned by later queue items and staying intentionally nondeployed.

## Problem
gentle-ai 4.0.0 removes SDD and OpenSpec (queue Q29-Q39). The canonical documents still define
SDD phases, `host_sdd_*` boundaries, `workflow-sdd-secure`, and file-count delegation. The static
verifier pins many of those strings, so removing them without Q32 makes the verifier fail by
design; that future failure set is inventoried below. The change is too large for one
review-budget commit and must be split into coherent work-unit commits.

## Scope
### In scope (Q30 exactly)
- Delete the SDD sections/rows and the `workflow-sdd-secure/` skill (`SKILL.md`,
  `references/sdd-magic-adapter.md`).
- Rewrite Task Classes and the selection rules to the Q29a former-SDD route.
- Replace file-count mapping delegation with the evidence budget. Keep the
  `two or more non-trivial files` writer rule literal so the verifier checks at
  `verify-workflow.sh:4354` and `:4547` do not break for a wording reason.
- Retitle the "Gentle AI 3.5.0" headings to version-neutral or 4.x.
- Remove TDD-mode-selection assumptions (test-first remains the default; still forward the
  exact runner).
- Remove the `user:host-sdd-runtime-boundaries` block and the `workflow-sdd-secure` routing line
  in `global-config/AGENTS.md`.
- Update the Astra table.
- Update route skills: `workflow-route` (SKILL + `references/session-decisions.md`),
  `workflow-odd-secure` (SKILL + `references/odd-and-review.md`), `workflow-systematic`
  (SKILL + `references/specialists.md`).
- Update the session-decisions write path to the Q29d agents.
- Update `docs/PLAN.md` at the cited lines; regenerate the full SDD mention list at
  implementation time with a bounded literal read (line numbers drift).
### Out of scope (other queue items; preserved)
- Q31 agent allocation (`global-config/opencode.json`, `tui.json`, `systematic.jsonc`, prompts).
- Q32 verifier (`verify-workflow.sh`); Q33 guard/plugins (`global-config/plugins/**`).
- Q34 runbook; Q36/Q37/Q38 change set (`upgrade/v4/**`, `scripts/changeset.py`).
- Q39 in-flight SDD preflight; deployment of any kind.

## Constraints
- **Intentionally nondeployed.** Q30 is source-only: no verifier mirror, no service restart, no
  live `~/.config/opencode` edit. The excluded verifier/plugins/config surfaces are preserved
  for Q31-Q33.
- **Branch.** Host branch `feat/gentle-ai-v4`; the owner approved **feature-branch-chain**
  integration (strategy `feature-branch-chain`, already approved — no repeats). Host preparation commit
  `a12779e09af562dc5340b4a589c116a11f2542f1` carries this tracker and
  `odd/advice/gentle-ai-v4.md`. The writer runs on the sandbox's synthetic work branch
  (observed: `work`); never switch branches and never commit; the PM owns installation and the
  fixed host commit.
- **Review boundary.** Last reviewed boundary is
  `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860` (supplied) — NOT host HEAD, retained for slice 1.
  `host_git_commit` accepts a message/session id (it commits the session's applied result); it
  does not take a base selector. Record the supplied constraints; do not follow the retracted
  advisor recommendation to pass host HEAD.
- **Tests.** Standard tests-first, NOT strict TDD. Exact runner:
  `HOME="$(mktemp -d)" bun test tests/routing-guard`, executed only in the isolated sandbox.
  Q30 is a docs/skills change; the guard suite is expected to remain green. The verifier is NOT
  run (it mutates host config); verifier failures are recorded as expected, never faked.
- **Delivery.** Strategy `feature-branch-chain` (owner-approved). No push, PR, merge, or release authority.
- **Review.** Independent post-code advisory review (`advisor-integration-post`, not a
  DeepSeek-family model) before each T1 work-unit commit; an RDD post-commit assessment is
  required for every work-unit commit against the boundary above.
- **Metadata.** Tracker, `docs/TODO.md`, `docs/PLAN.md`, and `ROUTER-LOG.md` updates belong to
  the separate metadata work unit; this preparation unit writes only the two artifacts below.

## Native review state (owner-supplied 2026-10-10; not independently verified here)
A native review relay attempt (lineage `review-be12d8a092fe7eda`) failed with the exact
owner-supplied error:
`opencode_reviewer_relay_refused: reviewer_relay_child_exited: transport exited before completion (1): Error: opencode_review_transport_binding_invalid: Task repository context does not match the repository and binding it commits to`.
The owner reports this as the third occurrence and attributes it to a systemic, outdated
installation compounded by the deferred v4 upgrade, alongside the 600 s `RELAY_DEADLINE_MS`;
that attribution is the **owner's diagnosis**, not an independently established cause.
PM-observed `host_review_status` snapshot: status `0`, schema v9, `authority.state=reviewing`,
action `collect`, reason `reviewer_results_required`; full target
`sha256:6a3efa3ef82a8974000f2dfd589ad51a62f3071dccfa71a8e451b401f18b1a32`, revision
`sha256:66d2b6637aeefba3ce150fc7caa3a709ceb3fc2b032817e5eac3025723982ff2`. The state is
non-terminal: no acknowledged authority. Consent handling is owner-reported; RDD remains enabled
(global mode not toggled). The owner authorizes this source-only implementation slice despite the
relay refusal: **no review authority is claimed and the reviewed boundary is unchanged**; the
PM's fixed commit operation may gate — never bypass — the owed review.

A second native review outcome (supplied, 2026-10-10): lineage `review-415a851fd6a96364` is
terminal with state `escalated` (cause `unknown_causality`); no review authority or approval is
claimed from it. Its finding `R3-PM-IDENTITY-CHAT-MESSAGE-BLIND-SPOT` is the PM-layer
identity-binding known limitation already documented at `odd/tasks/pm-layer.md:372` (the binding
is the latest observed message agent, not authenticated identity, and a task-dispatched child PM
may never receive `chat.message`). Disposition: accepted as a known limitation (owner,
2026-10-10). The reviewed boundary is unchanged: `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860`.

## Tasks
- [ ] **T1 (Q30) — Workflow documents.** Deliverables:
  - [ ] Delete the SDD sections/rows and `workflow-sdd-secure/` (`SKILL.md`,
    `references/sdd-magic-adapter.md`).
  - [ ] Rewrite Task Classes and selection rules to the Q29a former-SDD route.
  - [ ] Replace file-count mapping delegation with the evidence budget; keep the 2+ writer rule
    literal. (Slice 1: WORKFLOW.md Mapping + Long-session backstop bullets done; route-skill
    file-count triggers pending in a later slice.)
  - [ ] Retitle "Gentle AI 3.5.0" headings to version-neutral/4.x.
  - [ ] Remove TDD-mode-selection assumptions; forward the exact runner.
  - [ ] Remove the `user:host-sdd-runtime-boundaries` block and the `workflow-sdd-secure`
    routing line from `global-config/AGENTS.md`.
  - [ ] Update the Astra table and the session-decisions write path (Q29d agents).
  - [ ] Update route skills and their references (`workflow-route`, `workflow-odd-secure`,
    `workflow-systematic`).
  - [ ] Update `docs/PLAN.md`; regenerate the SDD mention list first.
  - [ ] Checks, reviewability receipts, independent post-code advice, post-commit assessment,
    and tracker/mirror readback per slice.

**Future gate references (not tasks):** Q31 agent allocation, Q32 verifier, Q33 guard/plugins,
Q34 runbook, Q36-Q38 change set, Q39 in-flight SDD preflight. They gate the eventual deployment
and are referenced here only to bound T1.

## Acceptance criteria
1. The authorized files contain no SDD-route references; the Q30 source list (regenerated at
   implementation time) is the checklist.
2. Task Classes and selection rules express the Q29a route; version-neutral/4.x headings replace
   the "Gentle AI 3.5.0" pins.
3. Mapping delegation uses the evidence budget; the literal `two or more non-trivial files`
   writer rule remains.
4. `global-config/AGENTS.md` host-sdd block and `workflow-sdd-secure` routing line are removed;
   the search-contract strings checked by `SEARCH_TOOL_ROUTING_DRIFT` are preserved exactly.
5. `workflow-sdd-secure/` is deleted and unreferenced.
6. `docs/PLAN.md` is updated at the cited lines.
7. Routing-guard tests run with the exact runner and results are observed and recorded; the
   verifier is not run and expected failures are documented, never faked.
8. Per-commit receipts, slice boundaries, post-code advice, and post-commit assessment outcomes
   are recorded; tracker and Magic Context mirror agree on readback.

## Authorized paths (exact) and exclusions
**Authorized edit paths for T1:**
- `WORKFLOW.md`
- `global-config/AGENTS.md`
- `global-config/skills/workflow-route/SKILL.md`,
  `global-config/skills/workflow-route/references/session-decisions.md`
- `global-config/skills/workflow-odd-secure/SKILL.md`,
  `global-config/skills/workflow-odd-secure/references/odd-and-review.md`
- `global-config/skills/workflow-systematic/SKILL.md`,
  `global-config/skills/workflow-systematic/references/specialists.md`
- `docs/PLAN.md`
**Authorized deletion paths for T1:**
- `global-config/skills/workflow-sdd-secure/SKILL.md` (13 lines)
- `global-config/skills/workflow-sdd-secure/references/sdd-magic-adapter.md` (97 lines)
**Preparation artifacts (this unit only):**
- `odd/tasks/gentle-ai-v4.md`, `odd/advice/gentle-ai-v4.md`
**Excluded/preserved:** `verify-workflow.sh`, `global-config/plugins/**`,
`global-config/opencode.json`, `global-config/tui.json`, `global-config/systematic.jsonc`,
`global-config/prompts/**`, `upgrade/v4/**`, `scripts/changeset.py`, `tests/**` (no test edits
planned), and any host/live deployment path.

## Checks
### Baseline (reported; not independently observed in this unit)
- `HOME="$(mktemp -d)" bun test tests/routing-guard`: **94 pass / 0 fail / 224 `expect()` calls**,
  reported by worker session `ses_edd67c946ffeOfFSiTr2xO6697` (fresh wrapper
  `eec3384386926e28b6a071d5661a1ef0749fe936`, parent `b4006acc`, tree identical). Narrative:
  94/0/224. **Exit code unobserved.**
### T1 slice 1 checks (observed 2026-10-10)
- Doc-contract probe (worker-local, ignored `.atl/odd-q30-t1/probe_doc_contract.py`, run via
  `python3 .atl/odd-q30-t1/run_probe.py`): pre-edit `PROBE_RETURNCODE=1` (positive control: old
  Mapping/Long-session bullets present; new wording absent); post-edit `PROBE_RETURNCODE=0`
  (16/16 checks: new budget wording present, old file-count phrases absent, 9 anchors preserved
  — rootheading, writer x2, search x2, magic x2, readonly x2).
- `HOME=<mktemp -d> bun test tests/routing-guard` (recorded argv-only wrapper
  `.atl/odd-q30-t1/run_guard_tests.py`): baseline 94 pass / 0 fail / 224 `expect()` calls,
  `RETURNCODE=0`; post-edit 94 / 0 / 224, `RETURNCODE=0`.
- Static preservation: covered by the probe anchors (`SEARCH_TOOL_ROUTING_DRIFT` strings in
  `WORKFLOW.md` intact; the other two live in AGENTS/skills, untouched this slice).
- No verifier run (host mutation). Predicted WORKFLOW.md-side verifier breaks until Q32:
  `:4353` (`four or more files`) and `:4355` (`20 tool calls or five exploratory reads`). The
  routing-contract checks `:4546`/`:4548` read AGENTS/skills and stay unchanged until the later
  slices; the rest of the Q32 inventory applies to later slices.
- Runtime skill behavioral probe not applicable to this slice (WORKFLOW.md prose only); the
  guard suite exercises the consumer plugin.

## Delivery strategy, forecast, and smallest coherent split
- **Strategy:** `feature-branch-chain` (owner-approved). No PR/push authority.
- **Forecast (honest):** well above 400 authored changed lines in total, so a single atomic
  commit is not feasible under the local cap. Estimate per slice (recompute from measured
  receipts at implementation):
  1. Policy and entrypoint (WORKFLOW.md + AGENTS.md + PLAN.md): ~180-330 changed lines.
  2. Route skills (workflow-route, workflow-odd-secure, workflow-systematic): ~110-200.
  3. Retire `workflow-sdd-secure`: 110 deletions (13 + 97) plus headers.
  Total roughly 400-650 changed lines, excluding these preparation artifacts.
- **Smallest coherent split: 3 work-unit commits** — (1) policy and entrypoint, (2) route
  skills, (3) retire the SDD skill. Atomic reason: the full Q30 exceeds the 400-line/100 KiB
  per-commit cap and is not indivisible; the three file groups are independently coherent and
  revertible, and intermediate unreferenced state is harmless because Q30 is nondeployed. If a
  measured slice exceeds the cap, split further at file boundaries; never shrink correct content
  to fit (no code golf). No `review-size-exception` is claimed or needed.
- **Slice 1 boundary and rollback (2026-10-10).** Paths changed: `WORKFLOW.md` (Mapping +
  Long-session backstop bullets), `odd/tasks/gentle-ai-v4.md`, `odd/advice/gentle-ai-v4.md`.
  Rollback is all-or-nothing: revert those three paths to `a12779e0`; nothing else changed.
  The staged receipt vs `a12779e0` is produced at staging time and reported in the unit result.
- **Refinement delta (2026-10-10).** This unit changes only `odd/tasks/gentle-ai-v4.md` and
  `odd/advice/gentle-ai-v4.md` on the installed slice baseline; `WORKFLOW.md` is untouched. The
  refined FULL candidate vs `a12779e0` (three paths) and the two-path refinement delta receipts
  are staged at staging time and reported in the unit result; both stay within the 400-line/100
  KiB per-commit review cap.

## Progress
- 2026-10-09: preparation unit. Mapper inventory re-verified against the current tree
  (`verify-workflow.sh` predicates and guard advice pattern). Pre-code advice recorded (Task
  `ses_edd654d1dffecaALlO1nkvtPuS`). This tracker and `odd/advice/gentle-ai-v4.md` written in
  the sandbox. Preparation-artifact sizes: `odd/tasks/gentle-ai-v4.md` 255 lines and `odd/advice/gentle-ai-v4.md` 62 lines / 3743 bytes; combined 317 lines. Final digests are reported in the unit result; the tracker's line count is unchanged by this edit.
  Tracker + Magic Context mirror readback: recorded in the unit result.
- 2026-10-10: T1 slice 1 started. Owner-approved feature-branch-chain integration on
  `feat/gentle-ai-v4`; planning artifacts committed as `a12779e0`. Slice 1 is bounded to three
  paths — `WORKFLOW.md` (Mapping + Long-session backstop bullets; evidence budget), this
  tracker, `odd/advice/gentle-ai-v4.md` — and is source-only. Future slices identified:
  WORKFLOW.md remainder (Task Classes, SDD sections/rows, retitles, TDD-mode forwarding, Astra
  table, context/artifact backend), `global-config/AGENTS.md`, route skills, retire
  `workflow-sdd-secure/`, `docs/PLAN.md`.
- 2026-10-10 checks (observed): doc-contract probe RED pre-edit (`PROBE_RETURNCODE=1`; old
  bullets present, new wording absent) → GREEN post-edit (`PROBE_RETURNCODE=0`; 16/16 checks).
  Routing-guard suite `HOME=<mktemp -d> bun test tests/routing-guard`: baseline and post-edit
  both 94 pass / 0 fail / 224 `expect()` calls, `RETURNCODE=0`. The worker workspace was
  recycled twice across long turns; scaffolding and edits were re-applied each time and the
  intermediate digest re-verified identical (`body_sha256=f3a916c5...`). Raw invocations in
  Checks below.
- 2026-10-10 refinement (Task `ses_edbc5062bffebXomOvL1LqcGg8`): post-code advice observed
  (`advisor-integration-post`, Task `ses_edb9bca70ffeiC8VwnVH6WqrHH`) and its single required fix
  applied to this tracker and `odd/advice/gentle-ai-v4.md`; `WORKFLOW.md` untouched. Prior
  refinement writer `ses_edb98fc7bffevHGT1pBsTAuuAm` ended terminal `fallback_chain_exhausted`
  (`.atl/rate-limit-fallback.log:1682`) with no recoverable result; this fresh writer started
  from the installed slice baseline (`ade9919`). Checks observed: WORKFLOW.md two-bullet probe
  GREEN (12/12, `PROBE_RETURNCODE=0`); routing-guard suite with the exact runner under a
  throwaway HOME: 94 pass / 0 fail / 224 `expect()` calls, `GUARD_RETURNCODE=0`. Staged receipts
  (FULL candidate vs `a12779e0`; refinement delta vs the installed baseline) are within the
  400-line/100 KiB caps and reported in the unit result.

- 2026-10-10 mirror consolidation (owner-directed; before commit): this tracker's Magic Context mirror had accumulated **nine** overlapping base64-chunk records across three body generations; it was rewritten as **one** plain-Markdown record (Magic Context id `1120`, marker `ODD_TASKS key=odd/workflow_optimisation/gentle-ai-v4/tasks`) whose body matches this tracker, and all nine stale records were archived (1107, 1109, 1110, 1111, 1112, 1114, 1115, 1116, 1117). Acceptance criterion 8 (tracker <-> mirror readback agreement) is restored. No other file changed; `WORKFLOW.md` untouched.

- 2026-10-10 slice 2 (WORKFLOW.md remainder + `docs/PLAN.md`; docs-only, source-only): deleted the
  retired SDD surfaces (the Optional SDD Research section, the SDD-archive bullets, the SDD
  preflight/OpenSpec store bullets, and `host_sdd_*` from the host-tool counts), retitled the five
  `Gentle AI 3.5.0` headings, rewrote Task Classes and the classification/route-selection rules to
  the Q29a route, replaced TDD-mode selection with test-first plus exact-runner forwarding, and
  updated `docs/PLAN.md` (ODD/advisor layers, ODD-only execution spine, Q29a heading and lead).
  Slice-1 refinement is committed as `70a6524`. Checks observed: doc-contract probe RED pre-edit
  (`PROBE_RETURNCODE=1`, 6/6 retired strings detected with the 6/6 positive control) → GREEN
  post-edit (`PROBE_RETURNCODE=0`, 6 retired strings absent, 29 preserved pins present, six classes
  present); 81/81 fragment check `VERIFY_OK`; routing-guard suite under a throwaway HOME 94 pass /
  0 fail / 224 `expect()` calls, `GUARD_RETURNCODE=0`; `bash -n verify-workflow.sh` clean (file
  unchanged). Sandbox note: batched same-file `sandbox_edit` calls silently lost five edits to a
  parallel-apply race; all were re-applied and the fragment check now passes. AGENTS.md edits are
  deferred because they force `verify-workflow.sh` edits (tuple `:4461`, recovery engine
  `:908-917`/`:987-998`, byte-exact routing block `:1315`) which Q30's scope excludes; they move to
  the verifier/Q32 slice. Q30's WORKFLOW.md heading retitles will red the verifier pins (`:4302`,
  `:4337`, `:4350`, `:4347`, `:4360`, `:4361`) until Q32 — expected, non-deployed. The instructed
  `docs/PLAN.md:154` `/SDD` drop was not applicable by content: line 154 carries the Engram
  adoption text, and the only slash-form token in the file is `ODD/SDD` at `:20` (already edited).

- 2026-10-10 slice 2 evidence: commit `411f689c43e9c5ef550625dafcd5125ca7087ce6` (`docs(workflow): Q30 slice 2…`), 4 files (`ROUTER-LOG.md`, `WORKFLOW.md`, `docs/PLAN.md`, `odd/tasks/gentle-ai-v4.md`), +87/−72; `WORKFLOW.md` 509→491 lines, `docs/PLAN.md` 301→300. Checks observed: doc-contract probe RED→GREEN (retired SDD strings = 0), preserved pins 29/29, routing-guard suite 94 pass / 0 fail, and `bash -n verify-workflow.sh` rc 0.
- Native review outcome for this candidate: lineage `review-86b0f157bc915344`; lens `review-reliability`; state `approved`. Acknowledged; authority `burned`; `consumed_revision sha256:fa268df2…`. Post-ack assessment: `review_due:false` (`already_reviewed`, `consumed:true`). Reviewed candidate tree `b0c91df2…` (base `827749e7…`). The first lens attempt returned `Task cancelled` and was redelegated once; review lanes are skipped, not replayed, by the rate-limit fallback (`fallback_skipped_review_agent`).
- Three advisory findings, all `WARNING`/`informational` and non-blocking, recorded as separate later work (not fixed here):
  1. `R3-FALLBACK-HOLD-SUBAGENT-UNVERIFIED` — `global-config/rate-limit-fallback.json:787`.
  2. `R3-PM-BINDING-PERSISTENCE-SILENT-FAILURE` — `global-config/plugins/systematic-routing-guard.ts:328-365`.
  3. `R3-PM-IDENTITY-CHAT-MESSAGE-BLIND-SPOT` — same location; already recorded at `odd/tasks/pm-layer.md:372`.
  Findings 2 and 3 belong to the pm-layer feature and are pointers only; this unit does not edit that tracker.

- 2026-10-10 owner scope decision: the two remaining Q30 items — the `global-config/AGENTS.md` host-SDD block removal + routing-line rewrite, and retiring `global-config/skills/workflow-sdd-secure/**` — are **PARKED and deferred to Q32**, which requires coordinated `verify-workflow.sh` edits (routing-block heredoc `:1307-1321`/`:1315`; recovery engine `:908-915`/`:987-1001`/`:4461`; manifest `:812`; assembly `:4506-4507`; `VERIFY_SCRIPT_SHA256` re-pin). Q30's docs surface is COMPLETE (`70a6524`, `411f689`, `3b630b5`; evidence `601395a`/`4fa3bc2`).
- 2026-10-10 slice 3 evidence: commit `3b630b522f351e9e3ac76f1b67832284137b6d93`, 7 files (WORKFLOW.md residue + the six route-skill files), +40/−44 (84 authored lines); removed SDD from the route skills + WORKFLOW.md residue; `git diff --check` clean; probe with positive control: 0 `sdd` tokens in the six skill files, 1 permitted leftover (`WORKFLOW.md:94` `sdd-explore`, Q31 scope); preserved literals intact (`two or more non-trivial files`, `400 authored changed lines and 100 KiB`, `200 KiB serialized per-runtime review-input budget`, `### Gentle AI 3.4 reviewability budget`, `SEARCH CONTRACT: AFT=navigation`, the exact `Authorize → Explore → … → Close` sentence); routing-guard suite 94 pass / 0 fail.
- Post-commit assessment for this slice (base `601395a`): `review_due:false`, reason `under_budget` (7 paths / 84 lines) — slice accumulates pending, no review run.
- Expected verifier reds until Q32: routing-contract pins `verify-workflow.sh:4545/:4546/:4548/:4550` (3.5.0 headings, `four or more files`, `20 tool calls or five exploratory reads`).
- Q30 conclusion: the DOCS surface is now complete (`WORKFLOW.md`, `docs/PLAN.md`, the route skills, residue). The two remaining Q30 items — the `global-config/AGENTS.md` host-SDD block removal + routing-line rewrite, and retiring `global-config/skills/workflow-sdd-secure/**` — are NOT docs-only: the AGENTS.md route block deploys from the verifier heredoc (`:1307-1321`/`:1315`) so a doc-only edit is inert and drifts, its host block is read by the recovery engine (`:908-915`,`:987-1001`,`:4461`), and the verifier manifest (`:812`) + assembly (`:4506-4507`) require `workflow-sdd-secure/**` to keep existing. Both therefore belong with Q32 (or a widened co-ship). Owner chose docs-only (a); this remainder cannot land under it.
- Next step: decide the Q30 remainder disposition (defer to Q32 vs widen) and the next queue item.

## Route, triggers, and actual dispatches
- **Route:** delegated (secure ODD). No inline mutation anywhere; orchestrator/PM read-only.
- **Trigger evidence:** mapping trigger (the evidence budget: beyond one parallel batch or about
  five sequential lookups) → one read-only mapper; writer trigger (2+ non-trivial files) → bounded
  sandbox writer; preparation trigger (reading that prepares a write) → this preparation unit;
  plus the secure delegation policy (every project mutation/execution is delegated).
- **Actual dispatches (supplied):**
  - Read-only mapper `ses_edd654cfcffehK6gRwLSKctis0` — Q32 verifier-dependency inventory.
  - Pre-code advisor `advisor-integration-pre`, Task `ses_edd654d1dffecaALlO1nkvtPuS`
    (configured `opencode-go/kimi-k2.7-code`).
  - Baseline test worker `ses_edd67c946ffeOfFSiTr2xO6697` (fresh wrapper
    `eec3384386926e28b6a071d5661a1ef0749fe936`, parent `b4006acc`, tree identical).
  - This preparation writer: `odd-apply` sandbox writer session (session id held by the PM; not
    observable from inside the worker).
  - Post-code advisor `advisor-integration-post`, Task `ses_edb9bca70ffeiC8VwnVH6WqrHH`
    (observed model family Kimi; independent of the DeepSeek-family author) — succeeded.
  - Failed refinement writer `ses_edb98fc7bffevHGT1pBsTAuuAm` — terminal
    `fallback_chain_exhausted` (`.atl/rate-limit-fallback.log:1682`); no result to recover.
  - This refinement writer: `odd-apply` sandbox writer, Task `ses_edbc5062bffebXomOvL1LqcGg8`
    (fresh worker on the installed slice; sandbox baseline commit `ade9919`).
- The session ROUTE line is not execution evidence; results are recorded only as observed.

## Advice record
- **Pre-code:** `odd/advice/gentle-ai-v4.md` — original and amended summaries, exact authority
  resolutions, and retractions. Satisfies the `workflow-odd-secure` advice stage
  (guard pattern `^odd/advice/[^/]+\.md$`).
- **Post-code (observed 2026-10-10):** independent `advisor-integration-post`, Task
  `ses_edb9bca70ffeiC8VwnVH6WqrHH` (Kimi; not DeepSeek-family): WORKFLOW.md evidence-budget
  bullets confirmed correct; its single required fix applied — stale `ask-on-risk` replaced
  with the approved `feature-branch-chain` (branch parenthetical, Delivery bullet, delivery
  strategy). No other findings; no review authority claimed. Full record in
  `odd/advice/gentle-ai-v4.md`.
- **Post-commit:** RDD assessment required per work-unit commit against
  `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860` (boundary unchanged).
- **Post-code findings 2/3 (2026-10-10, supplied and applied):** finding 2 — the trigger-evidence
  line was stale after the slice-1 evidence-budget change (still `understanding needed 4+ files`)
  and now describes the evidence budget; finding 3 — `calls` in the evidence budget is defined as
  tool/read calls in `WORKFLOW.md` (:55, :59). Both applied. Advisory evidence only, never
  approval; no review authority claimed.

## Q30 -> Q32 verifier dependency inventory (verified against the current tree, 2026-10-09; line numbers drift — regenerate at implementation time)
**Q30-caused failures expected until Q32 lands:**
- Skill manifest `verify-workflow.sh:812` requires `workflow-sdd-secure` =
  (`SKILL.md`, `references/sdd-magic-adapter.md`). After deletion, `:823` (missing reviewed
  skill) / `:831` (missing reviewed skill file) errors surface as
  `WORKFLOW_SKILL_RECOVERY_FAILED` at `:3416`.
- Routing-contract assembly `:4506-4513` `cat`s `workflow-sdd-secure/SKILL.md` and its adapter
  reference; failure yields `ROUTER_SKILL_CONTRACT_UNAVAILABLE`.
- AGENTS canonical block `:900` and `:908-915`: `canonical_block(host_start, host_end)` errors
  when the `<!-- user:host-sdd-runtime-boundaries -->` block is absent →
  `AGENTS_CONFIG_RECOVERY_FAILED` at `:3399`.
- Bounded-block compare `:4459-4461` includes the host-sdd marker pair; drift →
  `AGENTS_BOUNDED_BLOCK_DRIFT` at `:4477`.
- Embedded routing copy `:1307-1321` (contains the `workflow-sdd-secure` adapter line at
  `:1315`) is byte-compared against the active AGENTS routing section at `:4432-4450`; changing
  the AGENTS block fails "AGENTS.md routing section differs from canonical verifier copy".
  Recovery `:1013` re-appends the embedded obsolete routing block, so recovery would restore
  the old route after v4 edits — Q32 must update the embedded copy.
- WORKFLOW keyword check `:4302` pins the heading
  `## Substantial ODD work units and review — Gentle AI 3.5.0`; retitling breaks it →
  `missing keywords` fail at `:4308`.
- Generic AND-list `:4337-4387`: `:4337` `## Context and SDD Artifact Backend`, `:4347`
  `Optional SDD Research and Diagnostics — Gentle AI 3.5.0`, `:4350`
  `## Gentle AI 3.5.0 mandatory ODD delegation`, `:4353` `four or more files`, `:4360`
  `optional verify → archive`, `:4361` `gentle-ai sdd-archive-compose` → any missing fails
  `:4390`.
- Routing-contract ODD checks: `:4545` `### Gentle AI 3.5.0 mandatory ODD delegation (SECURE)`,
  `:4546` `four or more files` (mapping), `:4548` `20 tool calls or five exploratory reads`,
  `:4550` `### Secure ODD protocol — Gentle AI 3.5.0 (MANDATORY)` → missing →
  `GENTLE_AI_V3_SECURE_ODD_ROUTING_MISSING` at `:4558`.
- `:4578` `Gentle AI 3.5.0 optional SDD research`, `:4585` `optional verify → archive`, `:4586`
  `gentle-ai sdd-archive-compose` → missing fails `:4614`.

**Must remain passing (Q30 preserves these exact strings):**
- `SEARCH_TOOL_ROUTING_DRIFT` `:4480-4488`: `prefer narrow read-only tools (ENFORCED)` and
  ``built-in `grep` remains `ask`-gated`` in AGENTS; `SEARCH CONTRACT: AFT=navigation` in
  `workflow-route/SKILL.md`; `all subagents have it disabled` and `EXTERNAL_CONTEXT_REQUIRED`
  in `WORKFLOW.md`. All subagents keep native `grep` disabled.
- `two or more non-trivial files` at `:4354` and `:4547` (writer rule stays literal).

**Separate, NOT Q30-caused (do not attribute to Q30):**
- Q31: `sdd-*` agent registrations, `permission.task` entries, and `host_sdd_*` permission
  assertions.
- Q32/upgrade-only: the gentle-ai 3.5.0 version floor and `GENTLE_AI_V3_5_SYNC_*` codes, digest
  re-pin, embedded-version updates, and runtime probe lists.

## Q39 — in-flight SDD changes (pending owner dispositions; do not resolve here)
Six unarchived `openspec/changes/*` entries are recorded in `docs/TODO.md` Q39:
- agent-sandbox-integration: `role-based-subagents`, `agent-host-tools`,
  `reviewer-relay-transport`
- opencode-workspace/vision: `mock-ui-test`
- peak-redir: `peak-hour-routing`
- sdd-quality/mini-sdd: `local-apply-test`

Dispositions remain pending owner choice (finish on 3.7.0, convert to ODD, or abandon) and are
enforced by the Q36 apply preflight, not by Q30.

## Next step

Per the owner decision (2026-10-10), the two remaining Q30 items — removing the `global-config/AGENTS.md` host-SDD block and rewriting its routing line, and retiring `global-config/skills/workflow-sdd-secure/**` — are PARKED and deferred to Q32. They require coordinated `verify-workflow.sh` edits to the routing-block heredoc (`:1307-1321`/`:1315`), recovery engine (`:908-915`/`:987-1001`/`:4461`), manifest (`:812`), assembly (`:4506-4507`), and `VERIFY_SCRIPT_SHA256` re-pin. Q30's docs surface is COMPLETE (`70a6524`, `411f689`, `3b630b5`; evidence `601395a`/`4fa3bc2`). The next action is the next queue item; this does not authorize a commit or host apply.
