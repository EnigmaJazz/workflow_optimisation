# Q90 T3.0.1 — staged supported-variant validator advice record

Unit `q90-t30-variants-u1`; class `global-tooling-change`; route `workflow-odd-secure`; delegated
cloud writer `odd-apply`. Owner boundary: `77ef08a..544a2630` was closed by explicit owner DECISION,
not native review; the current boundary is `544a2630...`. Q90 remains IN PROGRESS. Scope: stage
`supportedVariantFailure(model, variant)` in the verifier JS heredoc (full model IDs, explicit target
subset, marked for extraction); it is NOT called against live/configured seats and `opencode.json`
is unchanged. Existing exact GGA/Systematic checks and the explicit orchestrator gate are preserved.

## Pre-code advice (completed; not rerun)

| Lens | Session | Configured model |
|---|---|---|
| Security | `ses_e92ed06dfffeLxk4d0J6A3POEO` | `openai/gpt-6.1-sol` |
| Integration | `ses_e92ed06d8ffeEXX4V59w9pPNrA` | `opencode-go/kimi-k2.7-code` |
| Research | `ses_e92ed06d4ffealy4znKFuNY38t` | default/current-seat incompatibility |

- SEC01 support-vs-equality: staged target validator; active exact configured/runtime equality checks unchanged.
- SEC02 absent/empty/types: absent accepted; `""` and non-string values get distinct named refusals; no coercion.
- SEC03 evidence before map fabrication: only owner/tracker-confirmed names; Gemini absence only; no literal `default`.
- SEC04 explicit orchestrator gate: `ORCHESTRATOR_VARIANT_NOT_EXPLICIT` remains unchanged and active.
- SEC05 same-commit digest: `VERIFY_SCRIPT_SHA256` updated in this candidate.
- Integration: undeclared current selections, absent/empty and provider option differences; silent unknown
  collapse rejected because it conflicts with the owner named-refusal requirement; config-map expansion
  superseded by owner runtime evidence; the earlier "Mini has no variants" assumption was superseded.
- Research identified the default/current-seat incompatibility; owner staged activation resolves it.
- PM reassignment is deferred until Planner setup is complete; this supersedes the earlier PM-before-T3b
  ordering without rewriting other task design or migrating seats.

## Owner-supplied variant evidence (2026-10-24, owner inspection; not a runtime probe by this writer)

Verbatim:

> Owner-supplied variant evidence (2026-10-24), confirmed live by inspecting variants in OpenCode.
> Treat this as authoritative for T3.0.1 and record it as an owner-supplied evidence source, not a
> runtime probe you ran.
>
> Confirmed:
> - `mimo-v2.6-flash`: NO variants required.
> - `kimi-k2.7-code`: NO variants required.
> - `qwen3.8-flash` and `qwen3.8-max`: use DEFAULT. Record this as an owner decision overriding the
>   plan's medium/high/xhigh for these two: their seats omit `variant` entirely; `"default"` is not a
>   declared name and must be rejected as an unknown name unless it is declared.
> - `minimax-m3.1-flash`: HAS the specified variants (`xhigh`, `high` as the plan uses).
> - All other target models (`claude-haiku-5-5`, `deepseek-v4.1-flash`, `deepseek-v4-pro`,
>   `deepseek-v4.1-flash@worker`, `glm-5.3`, `glm-5.3-flash`, `google/gemini-flash-latest`,
>   `google/gemini-4-argon`, `gpt-6-luna`) have the specified variants.
> - Observed catalog blocks: `glm-5.3-flash` low/high/max (`reasoningEffort`);
>   `qwen3.8-flash` low/medium/xhigh (`effort`); `qwen3.8-max` low/medium/xhigh (`effort`);
>   `gpt-6-luna` none/low/medium/high/xhigh/max (`reasoningEffort`).
> - Owner decision: do NOT use `openai/gpt-6-luna-fast` anywhere; `openai/gpt-6-luna` only.
> - Owner decision: qwen3.8-flash/max use default, so the earlier "nearest level" mapping is retired.

## Post-code evidence (2026-10-24)

- Post-code advisor `advisor-integration-post` Task `ses_e92aa908bffeq3Wgqt0lx7lxbL`, configured `opencode-go/kimi-k2.7-code`: no blockers; confirmed staged semantics, unchanged active checks, absence-only policy and owner attribution; optional size-386 cap and v4-pro profile gate; `aft_inspect` was denied in the advisor after activation (the host PM static pass supersedes that availability limitation, not its diagnostics); advisor ran 22 variant tests, `bash -n` and `git diff --check`. Advice is evidence, NOT approval.
- Independent verifier `gentle-ai-verify` Task `ses_e92aa9096ffeN3ynypfY0hWNyf`, configured `openai/gpt-6.1-sol`: INITIAL candidate tree `f83e7e9e13e9b5a1744df384351f9103d48bcf7b`, synthetic baseline `3a8e38d` (parent `544a2630`); executed 22 variant + 20 Gemini + 8 model-independence = 50 tests, all pass, 0 skips; `bash -n`, `git diff --check` and pin equality `f18638...`; six paths / 386 authored lines; patch bytes `35,626` verified separately by the host result.
- First-pass static: PM `aft_inspect` PARTIAL with 11 Pyright optional-access errors in the new test (lines 85, 86, 90-93, 180, 191, 196, 201, 228); correction `1/1` left the last VERIFIED host diagnostics at 11→1 remaining, line 203 `extract_block().replace` on optional `None`; AFT Bash 0, but the TS workspace marker is absent and Markdown has no producer, so no all-static-clean or zero-error claim. Correction `1/1`: `required_block` explicit guard plus explicit regex-match guard (no blanket ignores; runtime missing-marker control retained), and own-key lookup so `constructor`, `__proto__` and `toString` are named `UNCLASSIFIED` instead of crashing, with an executable test and the ordinary unclassified-model control. OWNER OVERRIDE (2026-10-24): exactly one fresh correction; reason the residual optional `None.replace` at line 203; scope this one-line `required_block().replace(...)` change plus this evidence and targeted tests; one new writer; normal correction count remains 1/1; previous task IDs, dispositions, owner quote, the `77ef08a..544a2630` closure-by-DECISION and PM deferral are preserved; exceptional accessor fix done, final host `aft_inspect` confirmation pending the PM envelope.

- Disposition V1 (non-blocking before activation): the full `opencode-go/deepseek-v4-pro` identity remains an ASSUMPTION (the owner names the model and the plan's Go convention prefixes it, but that is not a resolved full ID); resolve it before selecting the optional v4-pro profile. No unavailability claim is made.
- Disposition V2 (LOW, optional): the activation test accepts any matching line rather than independently requiring both the T3.0.2 row and its prerequisite; both are present today. Deferred as optional test-strength, not changed here.
- ROUTER-LOG row `PENDING-COMMIT`; source checks and live seats remain UNVERIFIED; no full verifier, deploy or native review. Native review remains user-owned and separate; this worker does not commit or start it.
