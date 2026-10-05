# Model assignments — review lenses and advisors

## Objective
Reassign model families across the review and advice seats so that no reviewer shares a model family with the author of what it reviews, and record the change in the workflow.

## Problem
Verified in the live `~/.config/opencode/opencode.json` (2026-10-03):
- The writer is `general` = `openai/gpt-6-luna` (line 498).
- `review-readability` = `openai/gpt-6-luna` (824), `review-resilience` = `openai/gpt-6-luna` (973), `review-risk` = `openai/gpt-6.1-sol` (1023), `jd-judge-a` = `openai/gpt-6.1-sol` (724).
- Three of the four blocking review lenses and Judge A share the writer's family, so the only blocking gate is substantially self-review.
- The planner/orchestrator is DeepSeek family. Three of five pre-code advisors are `opencode-go/deepseek-v4.1-flash`, so the plan is critiqued by its own author's family.

## Constraints (the rules these assignments enforce)
1. A reviewer never shares a model family with the author of what it reviews. No `gpt-*` on any `review-*`, `asi-review-*`, `jd-judge-*`, or post-code advisor. No `deepseek-*` on any pre-code advisor.
2. The four lenses use four distinct families; validator and refuter use families distinct from all four lenses and from each other.
3. The two judgment-day judges differ from each other, from the fix agent, and from the writer.
4. Native review is the only blocking gate; advisors are evidence only.
5. Gate fails closed: if any lens fails or times out, the gate blocks; never pass on fewer lenses. Malformed lens output counts as a lens failure — retry once, then fall back, then fail closed; never parse it leniently or skip the lens.
6. Fallbacks preserve diversity and never land on GPT for a review seat; two lenses failing to the same fallback family at once fails closed. GLM is used only on the resilience lens, its relay, its fallback, and `jd-judge-a`.
7. Keep the barred-model exclusion in every advisor fallback chain.
8. The orchestrator routes and aggregates mechanically; it never ranks, dismisses, or merges findings because it authored the plan.
9. Barred from per-commit fan-out seats: `qwen3.8-max`, `kimi-k3`, `grok-4.7`. Grok only on the refuter.

## Tasks
- **T1 Review lens seats and relays — complete.** `review-risk` → `opencode-go/qwen3.7-plus` (high); `review-resilience` → `opencode-go/glm-5.3-flash` (high); `review-reliability` → `opencode-go/kimi-k2.7-code` (high, already correct); `review-readability` → `opencode-go/deepseek-v4.1-flash` (max). The six `asi-review-*` relays map one-to-one to their corresponding plain review seats. `review-validator` → `opencode-go/minimax-m3` (high); `review-refuter` → `opencode-go/grok-4.7` (high). Evidence: commits `261c6d0` and `e6c6e64`; GPT-exclusion assertion PASS; reviewability receipt for `261c6d0`: 36 authored changed lines / 21,305 authored patch bytes.
- **T2 Judgment day — complete.** `jd-fix-agent` → `openai/gpt-6.1-sol` (medium); `jd-judge-a` → `opencode-go/kimi-k2.7-code` (high); `jd-judge-b` → `opencode-go/qwen3.7-plus` (high). `opencode-go/kimi-k3` and `opencode-go/qwen3.8-max` are documented escalation options for unresolved consequential cases only, never defaults. Evidence: commit `261c6d0` (`fix(models): move review lenses and judges off the writer's model family`); GPT-exclusion assertion PASS; reviewability receipt: 36 authored changed lines / 21,305 authored patch bytes.
- **T3 Advisor split.** Split into two units; T3b switched routing and retired the five old names.
  - **T3a Add split agents — complete in this unit.** Add `advisor-<x>-pre` and `advisor-<x>-post` as deep copies of their existing source agents, with only model changed and `variant` removed; leave all five `advisor-<x>` definitions unchanged. Pre: design/security `openai/gpt-6.1-sol`; integration `opencode-go/kimi-k2.7-code`; testing `opencode-go/minimax-m3`; maintainability `opencode-go/mimo-v2.6-flash`. Post: design/security `opencode-go/qwen3.7-plus`; integration/testing `opencode-go/kimi-k2.7-code`; maintainability `opencode-go/deepseek-v4.1-flash`. `mimo-v2.6-flash` variant support was unconfirmed, so the copied variant was removed.
  - **T3b Routing switch and retirement — complete.** Switched pre-code advice to `-pre`, post-code advisory review to `-post`, and retired the old five advisor entries. Commit: `502fa74`.
- **T4 Enforcement surfaces.**
  - **T4a Verifier and guard enforcement — complete.** Updated verifier reviewer/writer family-diversity checks and advisor name lists, and routing-guard specialist allow-lists. Commit: `aaebc3c`.
  - **T4b Documentation and test surfaces — complete.** Updated `WORKFLOW.md`, `docs/ADVISOR-HANDOFF.md`, `docs/PLAN.md`, `docs/TODO.md`, and the routing-guard test sample for the pre/post advisor split. No verifier changes in this unit.

## Acceptance criteria
- Every changed agent is re-read after editing and asserted against rule 1; the unit fails if any assertion is violated.
- `opencode models openai` shows `gpt-6.1-sol` under the OAuth provider (substitute the listed ID if different, and report); `opencode models opencode-go --verbose` shows every `opencode-go/*` ID used, and any model without a `high`/`medium` variant gets its `variant` line omitted with a report — never substitute a variant name.
- No duplicate agent definitions; edit where each agent is defined.

## Authorized scope
`global-config/opencode.json`, `global-config/tui.json` if needed, `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts`, `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` (digest pin only), `WORKFLOW.md`, `docs/PLAN.md`, this tracker.

## Known evidence gaps and follow-ups (record, do not act)

Evidence gaps (do not act): GLM-5.3's quota under per-commit fan-out; `opencode-go/mimo-v2.6-flash` as a lens fallback.
`opencode-go/minimax-m3` as validator is an unproven seat. Kimi occupies several seats (reliability lens, two post-code advisors, one judge) and may produce correlated misses. A future seeded-defect run should measure per-lens recall and pairwise miss-correlation and revise the assignments from its results.

**Resolved:** `modelFamily()` in `verify-workflow.sh` now recognizes gpt, deepseek, glm, qwen, kimi, mimo, minimax, grok, and gemini; it no longer returns `undefined` for those families.

## Checks
Per work unit: `bash -n verify-workflow.sh`; the routing-guard test suite under an isolated `HOME`; the changed-agent re-read assertions; and a readback of `global-config/opencode.json` parsing as valid JSON.

Note: the pre-existing `advisor-testing` entry carries `"variant": "medium"` on `opencode-go/kimi-k2.7-code`, which offers no variants; `advisor-maintainability` carries `medium` on `opencode-go/mimo-v2.6-flash`, unconfirmed. Both are candidates for cleanup in T4.

## Progress
- [x] T1 lens seats and relays
- [x] T2 judgment day
- [x] T3a add the ten split advisor agents (old names retained)
- [x] T3b switch routing and retire old five advisor entries (commit `502fa74`)
- [x] T4a verifier and guard enforcement surfaces (commit `aaebc3c`)
- [x] T4b documentation and test surfaces
- [x] T5 model assignment update and follow-on verifier fixes (commits `e6c6e64`, `5552a4e`, `2a40821`)

## Route and trigger evidence
Route: delegated (secure policy — the orchestrator is read-only). Intended specialist: `general` sandbox writer. Trigger: substantial change across `opencode.json`, the guard, the verifier and `WORKFLOW.md`.

## Next step
T1-T5 and the follow-on verifier fixes are complete. The owner must decide whether to replace the GPT fallback target or explicitly waive the constraint; the question remains open.

## Delivery
Strategy: `ask-on-risk`. Forecast: above the ~400-line planning heuristic because T3 adds ten agent definitions; recompute from the first work-unit receipt and ask before the next commit if the total crosses ~400. Chain strategy: `stacked-to-main` (owner, 2026-10-03).

## Review-size exception

**T3a — record before commit.** Receipt: **521 authored changed lines** (500 insertions in `global-config/opencode.json`, 21 in this tracker), **36,338 authored patch bytes**, no generated or binary paths.

The per-commit cap is 400 authored lines and 100 KiB of authored patch. The patch bytes are well inside the 100 KiB budget; only the line count is exceeded. Technical reason the change is treated as atomic: it adds ten advisor agent definitions that are **deep copies of the five existing advisors** with only `model` and `variant` changed, so the change is one mechanically repeated shape rather than ten independent behaviors; the deletion side is zero; and splitting it would require applying the same configuration twice from the same working tree. The line count is dominated by duplicated prompt text, not by reviewable logic.

Reviewability: the native review's 200 KiB serialized-input budget is not approached. The reviewer's burden is a repeated shape, verifiable by the fifteen-agent model inventory printed at apply time.

Recorded by: orchestrator, 2026-10-03. Chain strategy: `stacked-to-main`.

## Post-code advisory review

- **Fixed:** The five post-code advisors are excluded from rate-limit fallback replay via `excludeAgents`.
- **Fixed:** The verifier's `required_agents` set now asserts all ten split advisors exist in the canonical OpenCode config.
- **Current assignment:** `asi-review-resilience` and `review-resilience` both use `opencode-go/glm-5.3-flash` with variant `high`.
- **Accepted, not fixed (informational):** Relay model/variant assignments are not compared against their corresponding review lenses by a verifier assertion.
- **Accepted, not fixed (informational):** The Sol-assigned `advisor-design-pre` and `advisor-security-pre` have selectable Astra aliases.

## T5 Model assignment update

| Agent | Old model / variant | New model / variant |
|---|---|---|
| `review-resilience` | `opencode-go/mimo-v2.6-pro` / none | `opencode-go/glm-5.3-flash` / `high` |
| `asi-review-resilience` | `opencode-go/mimo-v2.6-pro` / none | `opencode-go/glm-5.3-flash` / `high` |
| `review-readability` | `openrouter/~google/gemini-flash-latest` / none | `opencode-go/deepseek-v4.1-flash` / `max` |
| `asi-review-readability` | `openrouter/~google/gemini-flash-latest` / none | `opencode-go/deepseek-v4.1-flash` / `max` |
| `jd-judge-a` | `openrouter/~google/gemini-flash-latest` / none | `opencode-go/glm-5.3-flash` / `high` |

The existing GLM-5.3 fallback-policy chain was renamed to the exact GLM-5.3-flash key and merged with the existing flash chain. The resilience policy starts with `opencode-go/glm-5.3` (non-flash, `high`). Risk and reliability policies start with `opencode-go/mimo-v2.6-flash` (`high`); readability starts with `deepseek/deepseek-flash` because its primary is `opencode-go/deepseek-v4.1-flash` and the verifier requires that first target. None of these policies contains GLM targets.

Verifier changes: retain distinct judgment-day models but no longer require distinct providers; retain at least four distinct 4R models but no longer require multiple providers. The judgment-day fallback diversity check (two distinct providers) remains and was not relaxed. The owner decided subscription capacity plus failover replaces provider spread for the two relaxed checks.

### Follow-on verifier failures and fixes

The subsequent verifier run exposed five fallback-policy failures, fixed in commit `5552a4e`: `FALLBACK_OBSOLETE_MODEL` (`glm-5.2` → `glm-5.3`); `FALLBACK_UNSUPPORTED_START_PROVIDER` (removed `openrouter` from `startProviders`); `FALLBACK_EXACT_SOURCE_INACTIVE` (removed the stale Gemini policy key); `DEEPSEEK_V4_1_MODEL_FALLBACK_FIRST_MISMATCH` (moved `deepseek/deepseek-flash` to first); and `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY` (moved `architecture-strategist` to `glm-5.3-flash` in `global-config/systematic.jsonc`). A subsequent fix, commit `2a40821`, removed the orphaned `openrouter` provider rule.

### Open item

The `opencode-go/glm-5.3-flash` fallback chain ends on `openai/gpt-6.1-sol`, which conflicts with the constraint that no GPT model appears on a review seat. This target is inert because every review and judge seat is in `excludeAgents`. The owner must decide whether to change the chain or explicitly waive the rule; it is not resolved here.

## DeepSeek V4.1 unusable lens-turn recovery

Owner decision: a lens turn is a **FAILURE**, never "no findings", if the finish reason is unknown, output tokens are 0, the message contains a reasoning part but no text part, the output is malformed or does not match the lens output contract, or a tool-call-ID error occurs. On failure, retry once, then fall back, then fail closed. Log the error text. Malformed lens output must never be parsed leniently or skipped.

### Model reassignment

| Agent | Old model / variant | New model / variant |
|---|---|---|
| `review-readability` | `opencode-go/deepseek-v4.1-flash` / `max` | `opencode-go/deepseek-v4-flash` / `high` |
| `asi-review-readability` | `opencode-go/deepseek-v4.1-flash` / `max` | `opencode-go/deepseek-v4-flash` / `high` |
| `advisor-maintainability-post` | `opencode-go/deepseek-v4.1-flash` / none | `opencode-go/deepseek-v4-flash` / `medium` |

The exact fallback policy for `opencode-go/deepseek-v4-flash` is new because the verifier requires an exact policy for every active primary. It starts with `opencode-go/mimo-v2.6-flash` as required for the readability seats. The existing `opencode-go/deepseek-v4.1-flash` exact policy was left unchanged.


### Muse Spark 1.3 readability reassignment

| Agent | Old model / variant | New model / variant |
|---|---|---|
| `review-readability` | `opencode-go/deepseek-v4-flash` / `high` | `opencode-go/muse-spark-1.3-contributor` / `high` |
| `asi-review-readability` | `opencode-go/deepseek-v4-flash` / `high` | `opencode-go/muse-spark-1.3-contributor` / `high` |

The exact fallback policy for `opencode-go/muse-spark-1.3-contributor` starts with `opencode-go/mimo-v2.6-flash` (`high`), followed by the existing non-GPT `deepseek/deepseek-flash` and `openrouter/deepseek/deepseek-v4.1-flash` targets. The existing `opencode-go/deepseek-v4-flash` policy remains because `advisor-maintainability-post` still uses that primary.
