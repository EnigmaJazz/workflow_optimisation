# Q90 PM reassignment — owner decision and evidence

Date: 2026-10-24. Unit `q90-pm-reassign-u1`; class `global-tooling-change`; route
`workflow-odd-secure`; delegated cloud writer `odd-apply`. Baseline
`040149e203d7f0c0b7d1de52c880343bf971be43`.

## Decision

- `pm-odd` and `pm-systematic` both move to `opencode-go/glm-5.3-flash` with
  `variant: high`; the Planner remains a later separate, not-installed unit using the planned
  `openai/gpt-6.1-sol`.
- Independence is by model family: GLM PM against DeepSeek `odd-apply`/`gentle-ai-worker`
  writers. The existing no-`general` PM writer policy remains; the false same-OpenAI rationale
  was removed, not replaced with a provider-only independence claim.
- `agentFallbackModels` gains identical PM chains: `opencode-go/qwen3.8-flash` `high`, then the
  existing cross-provider `openrouter/~google/gemini-flash-latest` target with no variant. Both
  targets carry files/tools/vision. The shared
  `fallbackModels["opencode-go/glm-5.3-flash"]` policy and all other policies are unchanged; no
  DeepSeek target is in the PM chain.

## Enforcement and evidence

- `verify-workflow.sh` carries a marked `pm-seat-policy` block with a live call. Tests extract
  and execute it, rejecting both PMs on `openai/gpt-6.1-sol` and `openai/gpt-6-luna`, rejecting
  a wrong or missing variant, and accepting configured GLM high.
- The same focused test module executes the production fallback resolver: model failure keeps
  Qwen first; provider failure leaves the nonempty cross-provider Gemini survivor. A negative
  control removes Gemini and observes an empty provider-failure chain.
- Observed checks: the initial test module RED 15 failures / 3 errors before the production
  changes; the final compacted module and required ten-module suite GREEN with 0 skips; both
  JSON files parse; `bash -n verify-workflow.sh` passes; verifier and health-plugin pin match;
  `git diff --check` clean. AFT post-activation was denied by the broker; the PM will run
  `aft_inspect` on the applied candidate. The full verifier, deploy, live model/runtime
  resolution and native review were NOT run.

## Authority and limits

Owner authorizes one initial writer, ONE independent `gentle-ai-verify`, NO pre/post advisors
(this-unit cost deviation, not a docs exemption), and one correction ceiling. The PM owns the
fixed commit and assessment. The PM/explorer/verifier session IDs and the measured reviewability
receipt belong to the PM envelope if not exposed here and are not invented. Magic Context mirror
is UNIMPLEMENTED and was not read or written.
