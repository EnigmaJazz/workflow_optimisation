# Q74 — Tiny-fix writer model independence

**Feature:** PM-layer completion
**Task ID:** q74-writer-model-independence
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice; T1 pending).
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

The orchestrator must not dispatch a writer that shares its own model family, so its review of that writer's work is genuinely independent.

## Problem

OBSERVED: `gentle-orchestrator` (`global-config/opencode.json:463`), `odd-apply` (`:2176`) and `gentle-ai-worker` (`:366`) all run `opencode-go/deepseek-v4.1-flash`. Every writer dispatch in the recent session paired a writer with the coordinator on the same model, and NOTHING caught it: `verify-workflow.sh`'s `assertCfgWriter` (`:2764-2777`) checks tool SHAPE only and never reads a `model` field; the family-pair check (`:2335`) enumerates only `[["general","gentle-orchestrator"],["gentle-ai-worker","gentle-ai-verify"]]` and never names `odd-apply`. `WORKFLOW.md:146` states a writer↔verifier family rule but is silent on the orchestrator↔writer pair.

## Owner decision (2026-10-15) — this NARROWS the fix

The intention is that ALL writers apart from tiny fixes are dispatched by a PM, not the orchestrator. So the orchestrator↔writer pairing is MOOT for normal work: a PM runs `openai/gpt-6.1-sol` and dispatches `odd-apply` (DeepSeek) — already independent. The ONLY broken pairing is the TINY-FIX route, where the orchestrator itself dispatches the writer. Therefore only the tiny-fix writer must be a non-DeepSeek family. The tiny-fix route currently names `gentle-ai-worker` (DeepSeek) — WRONG — and must name `general` (`openai/gpt-6-luna`).

## Scope

In scope: T1 re-points the tiny-fix writer to `general` across every surface that names it; adds the orchestrator↔tiny-fix-writer independence clause; adds `tests/test_model_independence.py` (the first model-field test in the repo).

Out of scope: re-pointing `odd-apply`, `gentle-ai-worker` or the orchestrator (the PM-dispatched path is already independent); the PM↔`gentle-ai-verify` Sol sharing and the Astra-alias collapse (record as waivers).

## Constraints

- The writer list drifts across THREE places that must stay consistent: `global-config/plugins/lib/routing-guard-helpers.ts:18-19` (`ODD_SPECIALIST_WRITERS`), `verify-workflow.sh:2777` (`assertCfgWriter` args), and the family-pair list at `verify-workflow.sh:2335`.
- `modelFamily()` at `verify-workflow.sh:1913-1927` is a pure substring function over the configured model string, so a Python test mirroring it is feasible and non-vacuous.
- Any model change must be PAIRED with an exact-policy entry in `global-config/rate-limit-fallback.json` or `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY` (`verify-workflow.sh:2648`) fires.
- `VERIFY_SCRIPT_SHA256` re-pins LAST if `verify-workflow.sh` is edited.
- Never commit; never switch branches.

## Acceptance criteria

- The tiny-fix route dispatches `general`, not `gentle-ai-worker`.
- The orchestrator↔tiny-fix-writer independence clause is in the contract and pinned.
- `tests/test_model_independence.py` asserts the tiny-fix writer's family differs from the orchestrator's, WITH a positive control proving a same-family pairing fails.
- The PM-dispatched path is documented as already independent with its reason; the waivers are recorded.
- The routing-guard and Python suites stay green.

## Authorized scope

T1: `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts`, `global-config/opencode.json` (the tiny-fix writer reference only), `WORKFLOW.md`, the ODD route-skill reference, `verify-workflow.sh` (the family-pair list + anchor tokens only), the `VERIFY_SCRIPT_SHA256` pin, `tests/test_model_independence.py` (new). Plus this tracker, the advice record, `ROUTER-LOG.md`.

## Checks

- `bash -n verify-workflow.sh`
- `python3 -m unittest tests.test_model_independence -v`
- `python3 -m unittest discover -s tests`
- A fake-HOME `bun test tests/routing-guard`
- The sha256 == the pin.

## Tasks

- [ ] T1 — re-point the tiny-fix writer to general across every surface that names it; add the orchestrator↔tiny-fix-writer independence clause and pin it; add tests/test_model_independence.py with a same-family positive control; record the PM-path rationale and the waivers; re-pin LAST.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14).

**Forecast:** T0 ~200; T1 ~140. Total ~340, under the about-400 accumulated threshold.

**Selected AT tracker creation** per `odd-and-review.md:36`.

## Progress

- 2026-10-16: T0 — tracker, advice record and queue entry created; the owner decision narrowing the fix is recorded. No source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `general` (a NON-DeepSeek writer, so this unit is itself not self-reviewed by a same-model writer).
- Trigger: secure no-inline-mutation policy; multiple non-trivial files.
- RDD: on (decided by global).

## Next step

T1 implementation, then native review, then the metadata record.
