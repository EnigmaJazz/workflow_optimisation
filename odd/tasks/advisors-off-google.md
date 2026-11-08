# Advisors off Google models

## Objective

Remove every `google/` model from the agent inventory and make every advisor pre/post pair use different models, because Google API quota is nearly exhausted. Retire the redundant `advisor-gemini-*` carriers while keeping the tool-less advisors' bounded evidence-gathering path working.

## Problem

Seven agents run on `google/` models: `advisor-spec-pre`, `advisor-spec-post`, `advisor-design-pre`, `advisor-security-pre`, `advisor-gemini-pre`, `advisor-gemini-post`, and `advisor-gemini-evidence` (`global-config/opencode.json:692,734,1754,1796,2250,2292,2347`). `advisor-gemini-pre`/`-post` exist only to stand in for `advisor-spec-pre`/`-post` when the Antigravity external lane is inactive; that lane is PLANNED, so the carriers now only add cost. `advisor-gemini-evidence` is the only tool-bearing gatherer for four tool-less advisors, so its path must survive the rename.

## Scope

- `global-config/opencode.json`: model map, removal of two agent definitions, evidence-agent rename, task permissions, Planner prompt.
- `global-config/rate-limit-fallback.json`: `noFallbackAgents`, dead Google chains, exact-policy coverage for the new active models.
- `verify/30-recover-config.sh`, `verify/checkers/check-runtime-agents.cjs`: advisor inventories and invariants.
- Tests: a new invariant test plus updates to every test that names the removed agents or Google models.
- `WORKFLOW.md`, `docs/ADVISOR-HANDOFF.md`, `docs/gemini-api-route.md`: normative text and route doc.
- `docs/TODO.md`: Q131 (this unit) and Q132 (no-tool Gemini review-lens trial).
- `scripts/verifier_manifest.py update` re-pin, last.

## Explicit non-goals

- No change to `openrouter/~google/gemini-flash-latest` seats (`review-readability`, `asi-review-readability`, `jd-judge-a`): not advisors, different provider.
- No `derive-v2-config.py --apply`, no service restart, no native review, no live `gentle-ai-verify` (owner excluded it; Codex spec/security review follows).
- No merge, no push, no PR.
- No widening for the future Gemini review-lens trial.

## Constraints

- Tests first: RED observed before implementation, GREEN after, with positive controls.
- Slices under about 400 authored changed lines.
- The manifest/digest re-pin is the LAST step and must be re-run after rebasing on `chore/q128-pm-handoff-skill` (`b48d9a7`), which also re-pins. The rebase is not available to this read-only orchestrator worker, so the re-pin here is computed on base `2c591b0`.
- The sandbox refuses plan-root writes (`PLAN_ROOT_PROTECTED`), so this tracker is written through `host_plan_write`; writers never edit it.

## Tasks

### T1 - Tests first (RED)

Owner: delegated writer (`general`). Create `tests/test_advisor_models_off_google.py` with a pure `advisor_model_violations` helper, the real-config assertion, and positive controls A/B/C. Update `tests/test_spec_advisor_seats.py`, `tests/test_q90_planner.py`, `tests/test_q90_t30_kimi_removal.py`, `tests/test_model_variants.py`. Delete `tests/test_gemini_advisor_route.py` because its subject is removed.

Acceptance: RED observed before implementation, naming a `google/` model and an `advisor-gemini-` reference.

### T2 - Config and checkers (GREEN)

Owner: delegated writer (`general`). Apply the model map; delete `advisor-gemini-pre`/`-post`; rename `advisor-gemini-evidence` to `advisor-evidence` (`opencode-go/qwen3.8-flash`); update task permissions, the Planner prompt, `rate-limit-fallback.json`, `verify/30-recover-config.sh`, and `check-runtime-agents.cjs` (GEMINI block, PM maxima around 1526/1534, planner lanes around 1859/1888, memory classes around 1957, MODEL_POLICY rows).

Acceptance: no `google/` agent model; all six pairs differ; `grep -in gemini global-config/opencode.json` empty; JSON valid; `node --check` passes; target tests GREEN.

### T3 - Docs

Owner: delegated writer (`general`). `WORKFLOW.md` advisor tables and external-lane `gemini-api-substitute` removal; `docs/ADVISOR-HANDOFF.md`; `docs/gemini-api-route.md` retirement note; `docs/TODO.md` Q131 and Q132.

Acceptance: no normative doc names `advisor-gemini-*` or a `google/` advisor model; Q132 prerequisites state quota restoration and a verified, not assumed, way to feed the frozen candidate to a no-tool lens.

### T4 - Manifest re-pin (LAST)

Owner: delegated writer (`general`). `python3 scripts/verifier_manifest.py update`, then `python3 scripts/verifier_manifest.py check`.

Acceptance: `check` passes; `VERIFY_SCRIPT_SHA256` updated; re-run after rebasing on `chore/q128-pm-handoff-skill`.

### T5 - Delivery metadata

Owner: orchestrator. Record commit SHAs, including the commit that removes `advisor-gemini-*` so the definitions stay recoverable from git, plus checks and the native-review-excluded status.

## Acceptance criteria (unit)

1. `advisor_model_violations(real_agents) == []` and both positive controls fail closed.
2. `python3 -m unittest tests.test_advisor_models_off_google -v` is GREEN.
3. The updated advisor tests are GREEN.
4. `grep -in gemini global-config/opencode.json` is empty; no `advisor-gemini-` remains in `WORKFLOW.md`, `rate-limit-fallback.json`, the checker or the recover script.
5. Every advisor pre/post pair differs (spec, design, security, integration, testing, maintainability).
6. `advisor-evidence` on `opencode-go/qwen3.8-flash` is the only remaining gathering target.
7. `verifier_manifest.py check` passes after the re-pin.

## Checks

| Check | Command | Result |
|---|---|---|
| pending | filled by T1-T4 | pending |

## Risk

Risk: Task Size item 3 (contracts) and item 2 (permissions); high normative config change; one pre-advice phase, one post-code check; independent verifier excluded by owner (Codex spec/security review follows).

## Route and trigger evidence

- `route: delegated`; `specialist: general`; trigger: global tooling change plus a multi-file writer (WORKFLOW.md "Mandatory ODD delegation").
- PM tier unavailable: `docs/specs/pm-handoff.md` mandates BLOCKED for a HEAD under `.git/worktrees/`, and this worktree is one.
- Pre-code advice: the registered `advisor-*-pre` lanes are not materialized in this runtime, so the phase was substituted with one independent read-only `project-standards-reviewer` persona. Advisory evidence, never approval.

## Advice

### pre-code - project-standards-reviewer (substitute for advisor-*-pre)

Findings:

1. `tests/test_model_variants.py:57` names `google/gemini-4-argon`.
2. `check-runtime-agents.cjs:1859`/`:1888` planner-lane inventory names the removed agents, so `PLANNER_ADVISOR_LANE_MISSING` would fire.
3. `check-runtime-agents.cjs:1957` memory classes name the evidence agent, so `MAGIC_CONTEXT_MEMORY_POLICY_UNCLASSIFIED_AGENT` would fire.
4. Docs drift: `docs/ADVISOR-HANDOFF.md:15-16`, `docs/gemini-api-route.md:9-11,55,63`.
5. New active models need exact-policy coverage or `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY` fires.
6. `noFallbackAgents` is presence-checked only, so stale names never fail.

Resolution: items 1-4 are folded into T1-T4 as required updates, item 5 is verified in T2, item 6 is cleaned in T2.

## Next step

T1 and T2 by a delegated writer.


## Revisions
- r1 2026-11-08T20:19:47Z gentle-orchestrator: Create tracker for the advisors-off-google global tooling unit.
