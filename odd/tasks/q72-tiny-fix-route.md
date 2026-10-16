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

### Out of scope

- the v4.2.0 400-line slice alignment (unit B);
- the advisory-strategy change (unit C);
- the Q71 PM-half fix (unit D);
- any change to `docs/specs/pm-handoff.md`.

## Owner decisions (2026-10-15, do not re-litigate)

- The tiny-fix writer is **`gentle-ai-worker`** (a named specialist; `general` is the guard-blocked generic fallback and is NOT used).
- **`gentle-ai-verify` is ALSO added** to both PM allowlists, so a PM can still obtain a model-independent verification when it wants one; it is optional rather than excluded.
- The guard gets an **exemption** (not "accept the warning").
- Verification for tiny = **structural readback + the native RDD checkpoint**; the native review (different models) is the independence layer.

## Constraints

- `WORKFLOW.md:125` ("Decision content, not file count… never selects a route") and `:128` ("Risk, changed-line count, file count, or perceived complexity alone never selects a route") must NOT be contradicted: the escalation backstop must be worded as **escalation-only** ("decision content selects tiny; exceeding the tiny boundary escalates out"), never as a selector.
- `WORKFLOW.md:446` defines "trivial" as "trivial document edits, and clearly bounded few-line changes with no contract or security effect" — the new boundary must reference it.
- The guard change MUST carry a paired non-vacuous test (an absence assertion needs a positive control).
- `VERIFY_SCRIPT_SHA256` re-pin is required ONLY if `verify-workflow.sh` itself is edited (it must be re-pinned LAST in that same commit); the guard is a plugin, not the verifier.
- The PM prompts are inline JSON strings and must be edited byte-preservingly (valid JSON, keep `\n` escapes and 2-space indent) and stay under the ~6,000-char cap (`docs/specs/pm-handoff.md:11`; currently ~2,106 and ~2,120).
- Branch `chore/pm-layer-completion`; never commit; never switch branches.

## Acceptance criteria

- a tracker-less tiny dispatch does not warn;
- both PMs can reach `gentle-ai-worker` and `gentle-ai-verify`;
- the `Tiny fix` row names the route, boundary and no-artifact rule;
- the backstop is escalation-only wording and does not contradict `:125`/`:128`;
- a committed test proves the allowlist membership non-vacuously;
- no existing check is weakened;
- the routing-guard and python suites stay green.

## Authorized scope

T1: `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts`, `tests/routing-guard/routing-guard.test.ts`, `global-config/opencode.json` (the two PM prompts + the two task allowlists), `WORKFLOW.md`, `global-config/skills/workflow-route/SKILL.md`, `global-config/skills/workflow-odd-secure/SKILL.md` (+ its references if needed), `global-config/skills/workflow-systematic/SKILL.md`, `tests/test_pm_task_allowlists.py` (new). Plus this tracker, the advice record, `ROUTER-LOG.md`. If `verify-workflow.sh` must change, add it and the pin; otherwise leave both alone.

## Checks

- a fake-HOME `bun test tests/routing-guard` (green, including the new exemption control);
- `python3 -m unittest discover -s tests`;
- `python3 -m unittest tests.test_pm_task_allowlists -v`;
- `python3 -c 'import json; json.load(open("global-config/opencode.json"))'` rc 0;
- a per-PM membership probe;
- `bash -n verify-workflow.sh` only if it changed;
- the digest pin equal to `sha256sum verify-workflow.sh` only if it changed.

## Tasks

- [ ] T1 — add the tiny-fix guard exemption + paired test; add gentle-ai-worker and gentle-ai-verify to both PM task allowlists; edit the WORKFLOW.md Tiny fix row and its escalation backstop; align the three route skills; add the tiny-fix option to both PM prompts; add tests/test_pm_task_allowlists.py with a positive control.

## Delivery strategy

**Chosen strategy:** `stacked-to-main` (owner decision 2026-10-14).

**Forecast (authored additions + deletions, generated files excluded):** T0 ≈ 200; T1 ≈ 180 (guard + helper + guard test + 2 JSON regions + WORKFLOW row + 3 skill edits + 2 prompt insertions + the new test). **Forecast total ≈ 380**, under the about-400 accumulated threshold.

**Selected AT tracker creation** per `odd-and-review.md:36`.

## Progress

- 2026-10-16: T0 — tracker, advice record and queue entry created; delivery strategy selected at creation. No source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 implementation, then native review (assess the tier), then the metadata record. Units B, C and D follow.
