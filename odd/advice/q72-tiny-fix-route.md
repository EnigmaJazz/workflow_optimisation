# Q72 — Tiny-fix route — Advice record

## advisor-integration-pre (2026-10-15)

Pre-code advice (integration lens); load-bearing points only:

- **The guard stage model.** A route's stages are declared in `ROUTE_STAGES`
  (`global-config/plugins/lib/routing-guard-helpers.ts:66-103`): `workflow-odd-secure` requires
  `advice → tracker`, and `workflow-systematic` requires `requirements → advice → plan` before a
  specialist writer is unlocked. The writer sets are `SPECIALIST_WRITERS` and
  `ODD_SPECIALIST_WRITERS` (`:18-19`); `gentle-ai-worker` is already in both, so no writer-set edit
  is needed for it.
- **The orchestrator-writer warning.** `systematic-routing-guard.ts:968-980` warns when the
  ORCHESTRATOR dispatches a non-coordinator, non-read-only specialist while holding a valid workflow
  key. Today it is warning-only: `:874` records "Future block behavior could throw here; this rollout
  is warning-only." A tracker-less tiny fix dispatched by the orchestrator would therefore emit this
  warning on every tiny fix.
- **Line-count contradiction and the remedy.** `WORKFLOW.md:125` ("Decision content, not file
  count… never selects a route") and `:128` ("Risk, changed-line count, file count, or perceived
  complexity alone never selects a route") forbid making line count a selector. The tiny boundary
  must therefore be worded as escalation-only: decision content selects tiny, and exceeding the tiny
  boundary escalates out — the number is a boundary, not a selector.
- **The "trivial" definition.** `WORKFLOW.md:446` already defines "trivial" as "trivial document
  edits, and clearly bounded few-line changes with no contract or security effect". The new boundary
  must reference it rather than invent a second definition.
- **What is already true (smaller delta).** The `Tiny fix` Task Classes row exists at
  `WORKFLOW.md:116`; `workflow-systematic/SKILL.md:10` already permits tiny fixes via one delegated
  sandbox writer; `gentle-orchestrator` already has `"gentle-ai-worker": "allow"`
  (`opencode.json:482`). Both `gentle-ai-worker` and `gentle-ai-verify` are already in the guard's
  writer/read-only sets (`routing-guard-helpers.ts:18-19`, `:44-51`).
- **The real delta.** The two PM task allowlists: `pm-odd` allows only `odd-apply` as a writer and a
  fixed advisor/`explore` set (`opencode.json:1995-2009`), and `pm-systematic` allows
  `systematic-implementer` etc. (`:2115-2138`); neither lists `gentle-ai-worker` or
  `gentle-ai-verify`. Plus the guard exemption and the prose/skill alignment.
- **PM prompt budget.** `pm-odd` ~2,106 and `pm-systematic` ~2,120 characters against the ~6,000 cap
  (`docs/specs/pm-handoff.md:11`) — enough headroom for a short tiny-fix option.
- **A verifier edit would require the digest re-pin.** `VERIFY_SCRIPT_SHA256` is pinned in
  `global-config/plugins/workflow-health-check.ts:93` and re-pinned LAST in the same commit that
  edits `verify-workflow.sh`. The guard is a plugin, not the verifier, so a guard-only change needs
  NO re-pin.

## advisor-testing-pre (2026-10-15)

Pre-code advice (testing lens); load-bearing points only:

- **The repo-testable surface is the JSON allowlist change.** The guard exemption is testable in
  `tests/routing-guard/routing-guard.test.ts`; the PM allowlist membership is testable by parsing
  `global-config/opencode.json`. The PROSE changes are NOT mechanically verifiable beyond the
  verifier's keyword checks at `verify-workflow.sh:4597-4604` (the six task-class names) and the
  anchor tokens.
- **Precedent to mirror.** `tests/test_pm_layer_prompts.py:32` (module-level `AGENT_NAMES` = the two
  live PMs), `tests/test_sandbox_lifecycle_prompts.py:26` and `:74-79` (stable module-level NEEDLE
  constants + `AGENT_NAMES` + a `PositiveControl` class proving the check can fail).
- **Warranted new test — `tests/test_pm_task_allowlists.py`.** Two `PM_NAMES` (`pm-odd`,
  `pm-systematic`); a stable NEEDLE asserting `"gentle-ai-worker": "allow"` inside each PM's
  `permission.task`; a `PositiveControl` that proves removal is detected; and an absent-key control
  (a PM with no `task` block is reported, not silently passed).
- **What must NOT be weakened.** The verifier's task-class names (`verify-workflow.sh:4597-4604`),
  the required keywords (`:4606-4614`), the inline-regression negatives (`:4627-4632`), the
  route-statement keystone token (`:4572`), the writer/tool shape assertions (`:2777`,
  `:2783-2796`), the `pm-odd` `odd-apply` assertion (`:2851`), and the wildcard rules (`:2942-2943`);
  the guard tests `tests/routing-guard/routing-guard.test.ts:285-297` (every declared writer allowed)
  and `:327-339` (orchestrator writer warning); `tests/test_sandbox_lifecycle_prompts.py:74-79`;
  `tests/test_pm_layer_prompts.py:114-123`; `tests/test_anchor_manifest.py`;
  `tests/test_retired_commands.py`; `tests/test_orchestrator_prompt_source.py:330-333`.
- **INFERRED claims with explicit falsifiers.**
  - "A tiny fix needs no tracker or advice." Falsifier: dispatch `gentle-ai-worker` from an
    orchestrator session holding a valid workflow key, then check the routing-guard log for the
    ABSENCE of the orchestrator-writer warning; if it fires, the claim is false.
  - "The backstop escalates above N lines." No mechanical observer exists; the only observer is
    `gentle-ai review assess --json` post-commit, which is too late. Either anchor-pin the number as
    a contractual token or mark it JUDGEMENT.
  - "`gentle-ai-worker` + `gentle-ai-verify` is an independent pair." Falsifier: confirm both are in
    BOTH PM allowlists and their models differ.
- **Recommended verification set.** Repo-testable: the guard tests, `tests/test_pm_task_allowlists.py`,
  the JSON parse. INFERRED: the tiny-dispatch-no-warning behaviour and the escalation boundary. The
  owner's host run: the verifier mirror + an OpenCode restart to load the changed prompts/guard.
