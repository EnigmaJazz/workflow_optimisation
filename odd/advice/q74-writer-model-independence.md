# Q74 — Tiny-fix writer model independence — Advice record

## advisor-integration-pre (2026-10-16)

Pre-code advice (integration lens); load-bearing points only:

- **Both pairings matter, at different gates.** Writer↔verifier is the EXECUTION-CHECK gate; orchestrator↔writer is the PLANNING/APPROVAL gate. `WORKFLOW.md:146` currently states the writer↔verifier family rule but is silent on the orchestrator↔writer pair.
- **The owner decision narrows the repair to tiny-fix.** The orchestrator directly dispatches the tiny-fix writer, currently `gentle-ai-worker`; all other writers are dispatched by a PM. The PM runs `openai/gpt-6.1-sol` and dispatches `odd-apply` (DeepSeek), already independent. Do not re-point `odd-apply`, `gentle-ai-worker` or the orchestrator; document this PM-path rationale.
- **Observed model assignments:** `gentle-orchestrator` is at `global-config/opencode.json:463`; `odd-apply` at `:2176`; `gentle-ai-worker` at `:366`. They all use `opencode-go/deepseek-v4.1-flash`. The target tiny-fix writer is `general` (`openai/gpt-6-luna`).
- **`odd-apply` has NO assigned verifier.** `verify-workflow.sh:2335-2349` covers only `[general,gentle-orchestrator]` and `[gentle-ai-worker,gentle-ai-verify]`; it does not pair `odd-apply` with a verifier.
- **PM/verifier overlap is a waiver, not part of this repair.** The PMs and `gentle-ai-verify` are ALL `openai/gpt-6.1-sol` (`global-config/opencode.json:317`, `:1919`, `:2043`), already flagged in `odd/advice/q72-tiny-fix-route.md:139`.
- **The Astra collapse is another waiver.** `global-config/plugins/astra-sol-upgrade.ts:74-80` and `verify-workflow.sh:1916` show the Astra alias resolves within the same `openai` family.
- **Three writer-list surfaces drift independently and must stay aligned:** `global-config/plugins/lib/routing-guard-helpers.ts:18-19` (`ODD_SPECIALIST_WRITERS`), `verify-workflow.sh:2777` (`assertCfgWriter` arguments), and the pair list at `verify-workflow.sh:2335`.
- **Fallback policy is mandatory for model changes.** The exact-policy check at `verify-workflow.sh:2648` raises `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY` when a model lacks a paired entry in `global-config/rate-limit-fallback.json`; the capability check at `:2599-2606` catches a missing capability but not a same-family pair.
- **`isImplementationRoute` is duplicated.** `verify-workflow.sh:2193-2202` and `global-config/plugins/astra-sol-upgrade.ts:39-50` must remain in sync if the route is affected.
- **F6 verifier gap:** `verify-workflow.sh:40-41` claims a primary-orchestrator runtime model match, but no code path enforces that claim.

## advisor-testing-pre (2026-10-16)

Pre-code advice (testing lens); load-bearing points only:

- **The current verifier misses the required model comparison.** `modelFamily()` at `verify-workflow.sh:1913-1927` is a pure substring function over the configured model string, so a Python mirror is feasible. The verifier's `assertCfgWriter` at `:2764-2777` checks tool shape only and never reads a `model` field. This will be the FIRST model-field test in the repo.
- **Use a non-vacuous test shape:** a passing different-family case, a failing same-family positive control, and a coverage case for every ODD writer. Follow the keystone pattern in `tests/test_review_cadence.py`.
- **Keep the three writer-list surfaces synchronized:** `global-config/plugins/lib/routing-guard-helpers.ts:18-19`, `verify-workflow.sh:2777`, and `verify-workflow.sh:2335`.
- **The exact-policy and capability checks are distinct from independence.** `verify-workflow.sh:2648` catches a different-family re-point without a paired fallback policy; `:2599-2606` catches a missing capability. Neither catches same-family pairing.
- **Pin the contract clause.** Add the orchestrator↔tiny-fix-writer independence clause to the contract and its existing verifier anchor-token surface; do not imply that this applies to PM-dispatched writer work.
- **Preserve the relevant waivers and duplication hazards:** PM↔`gentle-ai-verify` Sol sharing (`global-config/opencode.json:317`, `:1919`, `:2043`; prior record `odd/advice/q72-tiny-fix-route.md:139`); Astra alias collapse (`global-config/plugins/astra-sol-upgrade.ts:74-80`; `verify-workflow.sh:1916`); duplicate `isImplementationRoute` (`verify-workflow.sh:2193-2202`; `global-config/plugins/astra-sol-upgrade.ts:39-50`); and the unenforced runtime-model claim (`verify-workflow.sh:40-41`).
- **Re-pin last.** Any `verify-workflow.sh` edit requires updating `VERIFY_SCRIPT_SHA256` only after all verifier changes are complete.

## Owner decision (2026-10-15)

The orchestrator↔writer independence rule is narrowed to the tiny-fix route because PMs dispatch all other writers. The tiny-fix writer changes from `gentle-ai-worker` (DeepSeek) to `general` (`openai/gpt-6-luna`). Keep `odd-apply` and `gentle-ai-worker` unchanged. Record PM↔`gentle-ai-verify` Sol sharing and Astra-alias collapse as waivers.
