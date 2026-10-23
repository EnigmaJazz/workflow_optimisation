# Q71 — PM-handoff prompt gaps — Advice record

## advisor-integration-pre (2026-10-15)

Pre-code advice (integration lens); load-bearing points only:

- **The natural surface** is the orchestrator overlay region `overlay.md:104-116`, which governs the
  ODD protocol, the tracker and the mirror readback. A new `add` block needs `after=<heading>` and
  no sha; a `replace`/`remove` block needs a `supersedes` sha computed over the exact base section,
  per `tests/test_orchestrator_prompt_source.py:175-187`.
- **The current PM prompt texts** already say "require observed checks, Git and tracker readback, and
  complete Magic Context mirror readback before `DONE`" — but they never say HOW to perform the
  complete readback.
- **The regeneration chain is mandatory:** assembler → `global-config/opencode.json:590` →
  `CURRENT_PROMPT_SHA256` at `tests/test_orchestrator_prompt_source.py:28` →
  `global-config/prompts/gentle-orchestrator/normative-ledger.md` line 5. `VERIFY_SCRIPT_SHA256` is
  NOT affected (nothing here edits `verify-workflow.sh`).
- **Verifier consumers:** `verify-workflow.sh:2957-2968` (assembler drift) and `:2973-2999`
  (required fragments). The Q26 anchor/token table does NOT reference these prompts.
- **PM prompt budget:** `pm-odd` 1,817 and `pm-systematic` 1,831 characters against the ~6,000 cap
  (`docs/specs/pm-handoff.md:11`) — ample headroom.
- **Blast radius is small:** `astra-sol-upgrade.ts:64-73` aliases model/variant only, never prompt
  text; the routing guard reads `task()` args and skill content, not prompts; no consumer compares
  PM prompt bytes.
- **`AGENTS.md` is the WRONG surface (inert):** `recover_agents_file` byte-compares only four bounded
  blocks (codegraph, subagent-cancellation, grep-enforcement, workflow-routing), so any other
  `AGENTS.md` edit does not deploy (`verify-workflow.sh:4665-4710`).

## advisor-testing-pre (2026-10-15)

Pre-code advice (testing lens); load-bearing points only:

- **The repo-testable surface is TEXT ONLY.** The behavioural claims (an orchestrator CAN build a
  valid brief; a PM CAN complete the readback) are NOT repo-testable and must be recorded `inferred`
  with explicit falsifiers: (a) a live `pm-odd` dispatch whose envelope accepts the brief; (b) a live
  dispatch whose `readback.magic_context_reference` carries the verbatim memory body.
- **Precedent to mirror:** `tests/test_sandbox_lifecycle_prompts.py:21-26,47,62,79,85-109` — a
  module-level `NEEDLE`, `AGENT_NAMES`, a `subTest` per agent, and a `PositiveControl` class; and
  `tests/test_orchestrator_prompt_source.py:28,60,267-275,305-328`.
- **Recommended new file:** `tests/test_pm_layer_prompts.py`, reading the EMBEDDED JSON prompt
  strings at `global-config/opencode.json:590`, `:1921` and `:2041` — never the assembled Markdown.
- **SIX vacuous-pass traps to avoid:** (1) asserting the wrong artefact (assembled Markdown vs
  embedded JSON); (2) cross-agent contamination via a joined string; (3) a needle chosen from the
  wrong file; (4) a needle generic enough to pre-exist, such as the bare words "Magic Context";
  (5) duplicating or conflicting with `CURRENT_PROMPT_SHA256`; (6) asserting the overlay source
  instead of the prompt bytes.
- **What must NOT be weakened:** `test_sandbox_lifecycle_prompts.py:24`'s four worker agents,
  `CURRENT_PROMPT_SHA256`, `FORBIDDEN_RESIDUE` at `:60`, `REQUIRED_IDS` at `:30-43`, and the
  routing-guard suites. `AGENT_NAMES` must contain only `pm-odd` and `pm-systematic`, since `pm-sdd`
  and `pm-probe` are retired.
- **A committed test IS the right bar here** because the verifier asserts neither text
  (`pm-handoff`/`pm-unit-brief` counts = 0 in `verify-workflow.sh`).

**Orchestrator correction (2026-10-15):** the testing advisor stated that `CURRENT_PROMPT_SHA256`
re-pins only when a `supersedes` sha changes. That is WRONG — the pin is the ASSEMBLED prompt's sha,
so any overlay edit moves it.
