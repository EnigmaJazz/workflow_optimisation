# gentle-ai v4 upgrade — workflow documents (Q30)

**Feature:** gentle-ai v4 upgrade / queue Q30 (workflow documents). **Task ID:** T1 (stable).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Unit status:** PREPARATION COMPLETE — tracker and pre-code advice written; T1 implementation not started.
**This unit:** preparation writer only. No implementation source edits, no deployment, no commit, no native review.
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
- **Branch.** Host branch `feat/gentle-ai-v4`, host HEAD
  `b4006acc928b6bddc1ac7f98f71d5c83d3903cbb` (supplied). The writer runs on the sandbox's
  synthetic work branch; never switch branches. The PM confirms the real branch at unit start.
- **Review boundary.** Last reviewed boundary is
  `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860` (supplied) — NOT host HEAD. `host_git_commit`
  accepts a message/session id (it commits the session's applied result); it does not take a
  base selector. Record the supplied constraints; do not follow the retracted advisor
  recommendation to pass host HEAD.
- **Tests.** Standard tests-first, NOT strict TDD. Exact runner:
  `HOME="$(mktemp -d)" bun test tests/routing-guard`, executed only in the isolated sandbox.
  Q30 is a docs/skills change; the guard suite is expected to remain green. The verifier is NOT
  run (it mutates host config); verifier failures are recorded as expected, never faked.
- **Delivery.** Strategy `ask-on-risk` (default). No push, PR, merge, or release authority.
- **Review.** Independent post-code advisory review (`advisor-integration-post`, not a
  DeepSeek-family model) before each T1 work-unit commit; an RDD post-commit assessment is
  required for every work-unit commit against the boundary above.
- **Metadata.** Tracker, `docs/TODO.md`, `docs/PLAN.md`, and `ROUTER-LOG.md` updates belong to
  the separate metadata work unit; this preparation unit writes only the two artifacts below.

## Tasks
- [ ] **T1 (Q30) — Workflow documents.** Deliverables:
  - [ ] Delete the SDD sections/rows and `workflow-sdd-secure/` (`SKILL.md`,
    `references/sdd-magic-adapter.md`).
  - [ ] Rewrite Task Classes and selection rules to the Q29a former-SDD route.
  - [ ] Replace file-count mapping delegation with the evidence budget; keep the 2+ writer rule
    literal.
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
### T1 implementation checks (planned)
- Re-run the exact runner in the isolated worker; record observed counts and exit status.
- Static preservation (observed by bounded literal read): `SEARCH CONTRACT: AFT=navigation` in
  `workflow-route/SKILL.md`; `all subagents have it disabled` and `EXTERNAL_CONTEXT_REQUIRED`
  in `WORKFLOW.md`; `prefer narrow read-only tools (ENFORCED)` and
  ``built-in `grep` remains `ask`-gated`` in `AGENTS.md`.
- No verifier run (host mutation). Expected verifier failures are the Q32 inventory below.

## Delivery strategy, forecast, and smallest coherent split
- **Strategy:** `ask-on-risk` (default). No PR/push authority.
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

## Progress
- 2026-10-09: preparation unit. Mapper inventory re-verified against the current tree
  (`verify-workflow.sh` predicates and guard advice pattern). Pre-code advice recorded (Task
  `ses_edd654d1dffecaALlO1nkvtPuS`). This tracker and `odd/advice/gentle-ai-v4.md` written in
  the sandbox. Preparation-artifact sizes: `odd/tasks/gentle-ai-v4.md` 255 lines and `odd/advice/gentle-ai-v4.md` 62 lines / 3743 bytes; combined 317 lines. Final digests are reported in the unit result; the tracker's line count is unchanged by this edit.
  Tracker + Magic Context mirror readback: recorded in the unit result.
- T1 implementation: not started.

## Route, triggers, and actual dispatches
- **Route:** delegated (secure ODD). No inline mutation anywhere; orchestrator/PM read-only.
- **Trigger evidence:** mapping trigger (understanding needed 4+ files) → one read-only mapper;
  writer trigger (2+ non-trivial files) → bounded sandbox writer; preparation trigger (reading
  that prepares a write) → this preparation unit; plus the secure delegation policy (every
  project mutation/execution is delegated).
- **Actual dispatches (supplied):**
  - Read-only mapper `ses_edd654cfcffehK6gRwLSKctis0` — Q32 verifier-dependency inventory.
  - Pre-code advisor `advisor-integration-pre`, Task `ses_edd654d1dffecaALlO1nkvtPuS`
    (configured `opencode-go/kimi-k2.7-code`).
  - Baseline test worker `ses_edd67c946ffeOfFSiTr2xO6697` (fresh wrapper
    `eec3384386926e28b6a071d5661a1ef0749fe936`, parent `b4006acc`, tree identical).
  - This preparation writer: `odd-apply` sandbox writer session (session id held by the PM; not
    observable from inside the worker).
- The session ROUTE line is not execution evidence; results are recorded only as observed.

## Advice record
- **Pre-code:** `odd/advice/gentle-ai-v4.md` — original and amended summaries, exact authority
  resolutions, and retractions. Satisfies the `workflow-odd-secure` advice stage
  (guard pattern `^odd/advice/[^/]+\.md$`).
- **Post-code:** PENDING — independent `advisor-integration-post` (not DeepSeek) before each T1
  work-unit commit.
- **Post-commit:** RDD assessment required per work-unit commit against
  `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860`.

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
PM installs this prepared two-file result through the fixed host result install when available
and approved (planning work-unit commit), then starts T1 slice 1 with the recorded pre-code
advice, per `docs/specs/pm-handoff.md` ordering. No commit or native review runs in this
preparation unit.
