# Q68 — Sandbox lifecycle ordering in the worker prompts — Advice record

## advisor-integration-pre (2026-10-14)

Pre-code advice (integration lens); load-bearing points only:

- **The ordering rule is CORRECT and GENERAL.** `sandbox_finish` exports the result and
  `sandbox_apply` consumes it; after apply the worker is terminal, so only one order is viable. The
  reported failure is consistent with that premise.
- **Not the same root cause as the 2026-09-30 `ensureWorker` timeout** recorded in
  `docs/TODO-HISTORY.md:54-55`: that was worker CREATION, this is worker ORDERING.
- **No earlier record establishes or contradicts the rule:** `docs/TODO-HISTORY.md:319` notes
  finish/apply are unregistered on the advisor surface; `:61` is about `sandbox_bash pwd`.
- **`global-config/opencode.json` IS the right place** because `recover_agents_file` does NOT
  recover the sandbox-tool-contract block (`verify-workflow.sh:906-914`, `:970-983`), so an
  `AGENTS.md` edit is INERT on deployment.
- **NO verifier assertion reads these three prompts** (`assertCfgWriter:2764-2777`,
  `required_agents:369-380`), so no `VERIFY_SCRIPT_SHA256` re-pin is needed.
- **The orchestrator prompt equality check is a DIFFERENT prompt** (`opencode.json:590`) and is
  untouched.
- **`astra-sol-upgrade.ts` is unaffected:** it only aliases Sol-model agents, and none of these
  three use the Sol model.
- **The recovery compares parsed Python objects, not bytes** (`verify-workflow.sh:539`) and writes
  with `json.dump(..., indent=2, ensure_ascii=False)` (`:610`), so valid JSON and 2-space
  indentation must be preserved.
- **Recommendation:** proceed with the prompt additions as the only surface that both reaches the
  agents and deploys automatically.

## advisor-testing-pre (2026-10-14)

Pre-code advice (testing lens); load-bearing points only:

- **Nothing in the verifier asserts prompt text,** so a green verifier proves only that the file
  loads. The minimum evidence is (a) the three prompt strings contain the rule, (b) the file
  parses, (c) the diff is line-additive inside the three prompt strings only.
- **No parser precedent** exists in `tests/` for reading inline agent prompts out of
  `opencode.json`, so this change sets that precedent and SHOULD add a committed test.
- **Recommended shape** mirrors `tests/test_orchestrator_prompt_source.py:355-356` and
  `tests/test_anchor_manifest.py:99-127`: assert the needle in `data['agent'][<name>]['prompt']`
  for the three names, pin the needle as a module-level constant, and add a `PositiveControl` that
  plants a tampered prompt (rule replaced with an empty string) and asserts the validator rejects
  it — without that, a green run is vacuous.
- **The behavioural claim ("apply-before-finish loses edits") is NOT testable from this repo** (it
  is a broker guarantee; the repo has no broker or worker harness), so it must be recorded as
  OBSERVED-ONCE, not verified.
- **The edit risk is JSON validity / whitespace drift / escape-style drift,** so the writer must use
  a byte-preserving text insertion and re-parse after editing.
- **What CANNOT be verified without a restart** is whether the RUNNING OpenCode process picked up
  the new prompt (state it as a gap).
- **Recommended split:** writer does the edit, the JSON parse, the scoped diff, the presence probe
  and the new test; the orchestrator runs the verifier and records the router row; the owner
  restarts.
