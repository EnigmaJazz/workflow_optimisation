# Q74 — Tiny-fix writer model independence

**Feature:** PM-layer completion
**Task ID:** q74-writer-model-independence
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T1 implementation complete; native review and metadata record pending.
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

The orchestrator must not dispatch a writer that shares its own model family, so its review of that writer's work is genuinely independent.

## Problem

OBSERVED: `gentle-orchestrator` (`global-config/opencode.json:463`), `odd-apply` (`:2176`) and `gentle-ai-worker` (`:366`) all run `opencode-go/deepseek-v4.1-flash`. Every writer dispatch in the recent session paired a writer with the coordinator on the same model, and NOTHING caught it: `verify-workflow.sh`'s `assertCfgWriter` (`:2764-2777`) checks tool SHAPE only and never reads a `model` field; the family-pair check (`:2335`) enumerates only `[["general","gentle-orchestrator"],["gentle-ai-worker","gentle-ai-verify"]]` and never names `odd-apply`. `WORKFLOW.md:146` states a writer↔verifier family rule but is silent on the orchestrator↔writer pair.

## Owner decision (2026-10-15) — this NARROWS the fix

The intention is that ALL writers apart from tiny fixes are dispatched by a PM, not the orchestrator. So the orchestrator↔writer pairing is MOOT for normal work: a PM runs `openai/gpt-6.1-sol` and dispatches `odd-apply` (DeepSeek) — already independent. The ONLY broken pairing is the TINY-FIX route, where the orchestrator itself dispatches the writer. Therefore only the tiny-fix writer must be a non-DeepSeek family. The tiny-fix route uses `general` (`openai/gpt-6-luna`); its direct `gentle-ai-worker` task permission has been removed. Keep `gentle-ai-worker` unchanged for non-tiny-fix purposes.

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

- 2026-10-16: T0 — tracker, advice record and queue entry created; the owner decision narrowing the fix is recorded. Route: delegated.
- 2026-10-16: T1 implementation — found and changed the orchestrator task allowlist in `global-config/opencode.json`: removed direct `gentle-ai-worker` permission; retained the already-allowed `general`. The Q72 tiny-fix permit in `systematic-routing-guard.ts` is target-agnostic (it arms only for an explicit `tiny_fix` writer dispatch), and `ODD_SPECIALIST_WRITERS` in `routing-guard-helpers.ts` is a writer-eligibility inventory, not the tiny-fix route selector; both remain unchanged. The `pm-odd` task allowlist still dispatches `odd-apply` on the normal PM path. The Q72 T1a design describes the scoped permit but does not select a writer. The historical Q72 advice record still says “Tiny-fix route via `gentle-ai-worker`”; it is outside this T1's authorized edit paths and was not changed. Q74's owner-decision text now records `general` as the route target. Other generic `gentle-ai-worker` references remain for non-tiny-fix purposes.
- T1 contract — added and pinned the orchestrator/writer independence clause in `WORKFLOW.md` and `odd-and-review.md`. `odd-apply` was not added to the family-pair list: its configured route assigns no verifier, so pairing it there would assert a false verifier relationship. The repo tests previously checked config validity but did not read agent `model` fields; this is the first model-field test.
- T1 limits and waivers — runtime model resolution/fallback behavior is NOT verified by this repository test. Recorded waivers: PM↔`gentle-ai-verify` Sol-family sharing; Astra alias collapsing into the OpenAI family; and the verifier's unenforced primary-orchestrator runtime-model probe claim. The PM-dispatched path remains independent in configured models (`pm-odd` Sol → `odd-apply` DeepSeek).
- T1 checks — new model test: 5/5; review-cadence: 2/2; anchor manifest: 7/7; Python discovery: 152/152; routing-guard Bun suite: 102/102; `bash -n verify-workflow.sh`: exit 0. Same-family tiny-fix and PM pairings, stale orchestrator worker permission, omitted writer inventory, and disabled independence assertion were each temporarily planted; the corresponding test failed as expected and passed after restoration. SHA-256 and configured pin both read `53132bc1694c96d58f4e665d83522478c910a9f531ea16b98ea5f4ee9cfe43e0`; the full verifier run is not environment-valid because its hard-coded `/home/james/...` paths do not exist in the sandbox.
- T2 — `gentle-ai-worker-local` is configured as `kinver/professional`; verifier `modelFamily()` resolves it to UNKNOWN (`undefined`) because `kinver` is not in its recognized family markers. The owner decision (2026-10-15) is that a tiny fix SHOULD be dispatchable to the local model, so retain its orchestrator task permission and test both tiny-fix writers (`general` and `gentle-ai-worker-local`) against `gentle-orchestrator`. The test now fails loudly for an unrecognized model family rather than treating it as independent; the local writer therefore cannot currently be proven independent, and the T2 model test is expected to report that gap. The contract and mirror now permit CLOUD or LOCAL tiers only when the family differs and explicitly reject unknown as proof; the verifier anchor-token rows were extended without removing existing rows. Honest limit: a family the verifier cannot recognize is not evidence of independence; family recognition or a configured model change requires a separately authorized verifier-source change.
- T3 — Owner input (2026-10-15) identifies the model family behind `kinver/professional` as `qwen`. The verifier and mirrored Python test use an explicit `kinver/` provider-aware mapping to `qwen`, rather than a generic `professional` substring marker, because the provider identity avoids misclassifying unrelated models with that model name. The local writer now resolves to `qwen`, distinct from the orchestrator's `deepseek`; `tests/test_model_independence.py` passes 7/7 with the same-family control, writer-inventory coverage, and a genuinely unrecognized-model fail-closed control intact. Temporarily removing the mapping makes the local-writer independence test fail again (and the direct mapping test fails), then both mappings were restored. `python3 -m unittest discover -s tests` passes 154/154, confirming the prior deliberate failure is gone; `env HOME=/tmp/q74-fake-home bun test tests/routing-guard` passes 102/102; `bash -n verify-workflow.sh` exits 0. Honest limit: this mapping records owner input; this repository cannot independently derive or validate the provider's model-family metadata.

## Route / trigger evidence

- Route: delegated.
- Specialist: `general` (a NON-DeepSeek writer, so this unit is itself not self-reviewed by a same-model writer).
- Trigger: secure no-inline-mutation policy; multiple non-trivial files.
- RDD: on (decided by global).

## Next step

T1 implementation, then native review, then the metadata record.
