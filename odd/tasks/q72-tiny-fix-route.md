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

- The tiny-fix writer is **`gentle-ai-worker`** (a named specialist; `general` is the guard-blocked generic fallback and is NOT used).
- **`gentle-ai-verify` is ALSO added** to both PM allowlists, so a PM can still obtain a model-independent verification when it wants one; it is optional rather than excluded.
- The guard gets an **exemption** (not "accept the warning").
- Verification for tiny = **structural readback + the native RDD checkpoint**; the native review (different models) is the independence layer. **SUPERSEDED 2026-10-15 — the external advice disproved this premise; see the post-external-advice decisions below.**

## Owner decisions (2026-10-15, post-external-advice)

External advisory (interim lane, two independent hosts) corrected the unit's scope and settled four points:

- **(a) The guard change is a SCOPED ONE-SHOT PERMIT gated on an explicit tiny-fix signal — never an agent-name bypass.** A blanket exemption keyed on `gentle-ai-worker` or on "tracker-less" would disable the writer-bypass and stage gates for substantial work (F1/F02); the permit is consumed once and scoped to the tiny unit.
- **(b) Tiny fix is PASSIVE-ONLY.** A medium/high-risk assessment or RDD-off **automatically ESCALATES out of Tiny fix** (F3/F06). `review_due` is true only for high risk, so passive/`under_budget` tiny commits get zero 4R lenses and the writer (`opencode-go/deepseek-v4.1-flash`) is not model-independent of the orchestrator. This supersedes the "native review is the independence layer" premise, which the external advice disproved.
- **(c) The writer is `gentle-ai-worker`** (and `gentle-ai-worker-local` when the local tier is selected).
- **(d) PM allows gain `gentle-ai-worker`, `gentle-ai-worker-local`, `gentle-ai-verify`, `gentle-ai-verify-astra`.**

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
- both PMs can reach `gentle-ai-worker` and `gentle-ai-verify`;
- the `Tiny fix` row names the route, boundary and no-artifact rule;
- the backstop is escalation-only wording and does not contradict `:125`/`:128`;
- a committed test proves the allowlist membership non-vacuously;
- no existing check is weakened;
- the routing-guard and python suites stay green;
- **required traces:** the permit-consumption log line; a `ROUTER-LOG.md` row per tiny fix (written inside the worker's brief, since the read-only orchestrator cannot); a scan flagging over-threshold `tiny` commits; and a tracker `## Log` entry for PM tiny fixes.

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

- 2026-10-16: T0 — tracker, advice record and queue entry created; delivery strategy selected at creation. No source edit yet. Route: delegated.
- 2026-10-15: External advisory (interim lane, two hosts) recorded; two BLOCKERs found (a blanket exemption would disable the writer-bypass and stage gates; the native-review independence premise is false for passive/under_budget tiny commits) plus a scope omission (overlay.md, the regenerated prompt, forbiddenPromptFragments). Owner decided: scoped one-shot permit; Tiny fix is PASSIVE-ONLY with automatic escalation. T1 scope revised accordingly; not yet dispatched.
- 2026-10-16: T1a — scoped ONE-SHOT tiny-fix permit implemented in `systematic-routing-guard.ts`: an explicit `tiny_fix` task flag (read then stripped before the host sees it) short-circuits the orchestrator-writer, advice, and tracker/plan stage gates for that dispatch; a WRITER dispatch arms a one-shot in-memory permit that the `session.created` event extends to the child session, covering the child's own `sandbox_*` writes at the ODD bootstrap gate. No key or artifact marker is minted; a permit-consumption log line is emitted. `pmRequiredRouteSkill` now strips a `-astra` suffix. Both PM task allowlists gain `gentle-ai-worker`, `gentle-ai-worker-local`, `gentle-ai-verify`, `gentle-ai-verify-astra`. New `tests/test_pm_task_allowlists.py` (with a mutation PositiveControl) and the guard suite's four permit cases + separate child-bootstrap case + Astra-alias case. Baseline 96 → 102 routing-guard tests, 139 → 145 python tests; both green; `json.tool` rc 0. T1b (prompts, route skills, WORKFLOW.md, verifier) remains open. Not committed — the PM commits.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 revised scope (see the owner-decisions subsection), then native review, then the metadata record. The `-astra` normalization and the live-mirror allowlist assertion may be split into a follow-up if T1 exceeds the review budget.

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
1. The permit is an EXPLICIT `tiny_fix` flag in the task args — NOT a minted key. No persisted state, nothing to leak, no ancestor walk.
2. It short-circuits EVERY stage gate for that dispatch: orchestrator-writer, ODD bootstrap, advice stage, tracker/plan stage.
3. Child writes are covered by an IN-MEMORY permit map keyed by child session id — not by file inheritance.
4. No artifact-* or skill-* marker is minted, so nothing the existing stage loops can match.
5. Astra: option alpha — assert the three source-canonical keys, plus a SEPARATE live-mirror check, because gentle-ai-verify-astra is a runtime alias, not a source key.
6. The escalation tripwire moves INTO CODE: the worker computes the threshold and denylist itself and returns ESCALATE rather than installing. Prose cannot enforce it, and host_sandbox_result_install is only ask-gated for PMs.
7. The verifier-side allowlist assertion is DEFERRED: it needs a re-pin, and the verifier reads the recovered config, so it would not close the live-drift gap.
8. Tests: four guard cases (exemption; paired positive control; not-global; not-over-broad), a SEPARATE bootstrap-suppression case, PositiveControl x3 for the allowlist test, and a recorded baseline pass count.

### Advisor uncertainties (recorded, not resolved)
The exact signal form; whether the advice-stage gate is lifted; and that neither advisor ran any code.
