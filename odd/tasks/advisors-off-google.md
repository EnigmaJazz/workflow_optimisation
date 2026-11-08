# Advisors off Google models

## Objective

Remove every `google/` model from the agent inventory and make every advisor pre/post pair use different models, because Google API quota is nearly exhausted. Retire the redundant `advisor-gemini-*` carriers while keeping the tool-less advisors' bounded evidence-gathering path working.

## Problem

Seven agents ran on `google/` models: `advisor-spec-pre`, `advisor-spec-post`, `advisor-design-pre`, `advisor-security-pre`, `advisor-gemini-pre`, `advisor-gemini-post`, and `advisor-gemini-evidence`. `advisor-gemini-pre`/`-post` existed only to stand in for `advisor-spec-pre`/`-post` when the Antigravity external lane is inactive; that lane is PLANNED, so the carriers only added cost. `advisor-gemini-evidence` was the only tool-bearing gatherer for four tool-less advisors, so its path had to survive the rename.

## Scope

- `global-config/opencode.json`: model map, removal of two agent definitions, evidence-agent rename, task permissions, Planner prompt.
- `global-config/rate-limit-fallback.json`: `noFallbackAgents`, inactive direct-Google wiring, exact-policy coverage.
- `verify/30-recover-config.sh`, `verify/checkers/check-runtime-agents.cjs`: advisor inventories and boundary invariants.
- Tests: a new invariant test plus updates to every test that named the removed agents or Google models.
- `WORKFLOW.md`, `docs/ADVISOR-HANDOFF.md`, `docs/gemini-api-route.md`: normative text and route doc.
- `docs/TODO.md`: Q131 (this unit) and Q132 (no-tool Gemini review-lens trial).
- `scripts/verifier_manifest.py update` re-pin, last.

## Explicit non-goals

- No change to `openrouter/~google/gemini-flash-latest` fallback targets or non-advisor seats: different provider, not advisors.
- No `derive-v2-config.py --apply`, no service restart, no native review, no live `gentle-ai-verify` (owner excluded it; Codex spec/security review follows).
- No merge, no push, no PR.
- No widening for the future Gemini review-lens trial.

## Constraints

- Tests first: RED observed before implementation, GREEN after, with positive controls.
- Slices under about 400 authored changed lines.
- The manifest/digest re-pin is the LAST step and must be re-run after rebasing on `chore/q128-pm-handoff-skill` (`b48d9a7`), which also re-pins. The rebase is not available to this read-only orchestrator worker, so the re-pin here is computed on base `2c591b0`.
- The sandbox refuses plan-root writes (`PLAN_ROOT_PROTECTED`), so this tracker is written through `host_plan_write`; writers never edit it.

## Tasks

### T1 - Tests first (RED) - DONE

Created `tests/test_advisor_models_off_google.py` with a pure `advisor_model_violations` helper, the real-config assertion, and positive controls A/B/C. Updated `tests/test_spec_advisor_seats.py`, `tests/test_q90_planner.py`, `tests/test_q90_t30_kimi_removal.py`, `tests/test_model_variants.py`. Deleted `tests/test_gemini_advisor_route.py` because its subject was removed.

RED observed before implementation: the new test reported Google-model assignments, a duplicate spec pair, and the missing renamed evidence agent.

### T2 - Config and checkers (GREEN) - DONE

Applied the model map; deleted `advisor-gemini-pre`/`-post`; renamed `advisor-gemini-evidence` to `advisor-evidence` (`opencode-go/qwen3.8-flash`); updated task permissions, the Planner prompt, `rate-limit-fallback.json`, `verify/30-recover-config.sh`, and `check-runtime-agents.cjs` (advisor block, PM maxima, planner lanes, memory classes, MODEL_POLICY rows).

### T3 - Docs - DONE

`WORKFLOW.md` advisor tables and external-lane `gemini-api-substitute` removal; `docs/ADVISOR-HANDOFF.md`; `docs/gemini-api-route.md` retirement notice; `docs/TODO.md` Q131 and Q132.

### T4 - Manifest re-pin (LAST) - DONE

`python3 scripts/verifier_manifest.py update` then `check`: `ok: manifest and pin are current`. Must be re-run after rebasing on `chore/q128-pm-handoff-skill`.

### T5 - Delivery metadata - DONE

Commit chain on `chore/advisors-off-google` (base `2c591b0`):

| Commit | What |
|---|---|
| `4a37830` | this tracker |
| `d0c4a76` | code slice: models, agent removal/rename, permissions, Planner prompt, fallback config, recover script, checker, new test. **This is the commit that removes the `advisor-gemini-*` definitions; they are recoverable at `d0c4a76^`.** |
| `941662c` | docs slice + first manifest re-pin + deletion of `tests/test_gemini_advisor_route.py` |
| `fb490c1` | correction F1/F2/F3 + manifest re-pin |

## Acceptance criteria (unit)

1. `advisor_model_violations(real_agents) == []` and positive controls fail closed. PASS
2. `python3 -m unittest tests.test_advisor_models_off_google -v` GREEN (9 tests). PASS
3. Updated advisor tests GREEN (69 tests). PASS
4. `grep -in gemini global-config/opencode.json` empty; no `advisor-gemini-` in `WORKFLOW.md`, `rate-limit-fallback.json`, the checker or the recover script. PASS
5. Every advisor pre/post pair differs. PASS
6. `advisor-evidence` on `opencode-go/qwen3.8-flash` is the only remaining gathering target. PASS
7. `verifier_manifest.py check` passes. PASS

## Checks

| Check | Command | Result |
|---|---|---|
| invariant test | `python3 -m unittest tests.test_advisor_models_off_google -v` | PASS, 9 tests |
| advisor regression set | `python3 -m unittest tests.test_spec_advisor_seats tests.test_q90_planner tests.test_q90_t30_kimi_removal tests.test_model_variants -v` | PASS, 69 tests |
| JSON validity | `python3 -m json.tool global-config/opencode.json` / `rate-limit-fallback.json` | PASS |
| shell syntax | `bash -n verify/30-recover-config.sh` | PASS |
| no Google agent model | `grep -in gemini global-config/opencode.json` | no matches |
| manifest | `python3 scripts/verifier_manifest.py check` | `ok: manifest and pin are current` |
| full suite | `python3 -m unittest discover -s tests -p 'test_*.py'` | NOT green, environmental only: `test_cli_config_mirror` (Python 3.13 dataclass loader), `test_codegraph_ensure` and `test_opencode_v2_preflight` (missing `/nonexistent`), `test_opencode_v2_db_swap` (no `sqlite3` in the sandbox), `test_verifier_split` (node execution denied; `__pycache__` enumeration). None references advisors, Gemini or Google. |
| checker syntax | `node --check verify/checkers/check-runtime-agents.cjs` | NOT EXECUTED: sandbox denies `node` (EACCES); `bun` starts but lacks `SYSTEMATIC_NODE_MODULES`. Static review only. |

## Risk

Risk: Task Size item 3 (contracts) and item 2 (permissions); high normative config change; one pre-advice phase, one post-code check; independent verifier excluded by owner (Codex spec/security review follows).

## Route and trigger evidence

- `route: delegated`; `specialist: general`; trigger: global tooling change plus a multi-file writer (WORKFLOW.md "Mandatory ODD delegation").
- PM tier unavailable: `docs/specs/pm-handoff.md` mandates BLOCKED for a HEAD under `.git/worktrees/`, and this worktree is one.
- Pre-code advice: the registered `advisor-*-pre` lanes are not materialized in this runtime, so the phase was substituted with one independent read-only `project-standards-reviewer` persona. Advisory evidence, never approval.

## Review-size exception

The per-commit reviewability cap (400 authored changed lines) was exceeded by the code slice (491) and the docs slice (638), and the correction stayed inside it (209). Technical reason: the change is one atomic removal-and-rename of two agent definitions plus the 416-line test that exclusively covered the retired route. Splitting further would commit a dangling reference or a red suite. Most changed lines are deletions of removed surface, not new code.

## Advice

### pre-code - project-standards-reviewer (substitute for advisor-*-pre)

Findings: (1) `tests/test_model_variants.py:57` named a Google model; (2) `check-runtime-agents.cjs:1859/:1888` planner lanes named the removed agents; (3) `:1957` memory classes named the evidence agent; (4) docs drift in `docs/ADVISOR-HANDOFF.md` and `docs/gemini-api-route.md`; (5) new active models need exact-policy coverage or `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY` fires; (6) `noFallbackAgents` is presence-checked only.

Resolution: items 1-4 folded into T1-T4; item 5 verified (all three models already had exact policies); item 6 cleaned in the correction.

### post-code - security-reviewer

F1 BLOCKER: the replacement advisor checker validated models only while still logging "dispatch scope and no-fallback policy". Resolved in `fb490c1`: tool-less seat isolation, evidence host/export denials, deny-all task scope, dispatch allowlists and the no-fallback policy are asserted again, with mutation controls for `sandbox_finish` exposure and stray evidence dispatch; the log line now states what is checked.

F2 BLOCKER: `rate-limit-fallback.json` still listed the direct `google` start provider, a dead `google/gemini-3.8-flash` exact policy and `providerFallbacks.google`, which the checker rejects as `FALLBACK_UNSUPPORTED_START_PROVIDER` / `FALLBACK_EXACT_SOURCE_INACTIVE` / `FALLBACK_PROVIDER_RULE_NOT_STARTER`. Resolved in `fb490c1`; OpenRouter `~google/gemini-flash-latest` targets kept.

F3 NON-BLOCKER: the WORKFLOW variant test skipped malformed rows. Resolved in `fb490c1` with bounded sections, an exact expected inventory, malformed/unknown/duplicate rejection and negative controls.

Native review: not run (owner excluded it for this unit). Independent verifier: not run (owner excluded it). Codex spec/security review follows.

## Next step

Rebase `chore/advisors-off-google` onto `chore/q128-pm-handoff-skill` and re-run `python3 scripts/verifier_manifest.py update` (the rebase needs host Git mutation, which this worker does not have). Then the Codex spec/security review over `2c591b0..fb490c1`.


## Revisions
- r1 2026-11-08T20:19:47Z gentle-orchestrator: Create tracker for the advisors-off-google global tooling unit.
- r2 2026-11-08T22:13:11Z gentle-orchestrator: Record commit chain, checks, size exception and post-code findings.
