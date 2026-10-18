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

## External advisory (interim lane — owner-relayed, 2026-10-15)

`selection.rule`: **interim external lane, owner-relayed by copy-paste** — NOT the automated
`pair-default` external lane, which is PLANNED and inactive (`WORKFLOW.md:484-495`; the automated lane
`Q06` is BLOCKED on external prerequisites). Two **independent hosts** — **Claude Code** and
**Antigravity** — each received the same self-contained, read-only prompt, and their responses were
returned verbatim.

### Findings

**BLOCKERS (both hosts independently).**

- **F1 (Claude) / F02 (Antigravity).** A blanket exemption keyed on `gentle-ai-worker` or on
  "tracker-less" would silence the orchestrator-must-use-a-PM warning for substantial work.
  `gentle-ai-worker` is already an allowed ODD writer (`routing-guard-helpers.ts:18-19`) AND the
  default implementation writer (`prompts/gentle-orchestrator/overlay.md:45`). "Tracker-less" is not a
  signal: stage markers are copied child→parent after every task (`systematic-routing-guard.ts:1058-1073`)
  with no expiry or feature scope, and keys stay alive on any activity (`:416-437`). Antigravity adds it
  would disable three gates at once (`:968-980`, `:989-993`, `:998-1002`).
- **F3 (Claude) / F06 (Antigravity).** The premise "native review is the independence layer" is FALSE
  for typical tiny commits: `review_due` is true only for high risk, so a few-line commit returns
  `passive` or `under_budget` with zero 4R lenses, while `gentle-orchestrator` and `gentle-ai-worker`
  both run `opencode-go/deepseek-v4.1-flash` (`opencode.json:366,463`). `WORKFLOW.md:144` requires
  `gentle-ai-verify` (GPT-6 Sol) for `gentle-ai-worker` output.
- **F03 (Antigravity).** The unit's stated motivation is adapting gentle-ai v4.2.0's inline-first
  wording, but the scope omitted `global-config/prompts/gentle-orchestrator/overlay.md` (which
  supersedes `### Delegation Rules` and `#### 1. Inline Direct` by exact base sha and never names the
  Tiny fix route), the regenerated `opencode.json:590` prompt, and `verify-workflow.sh:2974-2983`
  `forbiddenPromptFragments` (which blocks only the v4.0.0 inline strings, not v4.2.0's).

**WARNINGS.**

- **F2 (Claude) / F01, F04 (Antigravity).** The PM half of the exemption needs no code (a PM dispatch
  never trips `:968`), BUT the child worker's own `sandbox_write` still trips the ODD bootstrap warning
  (`:918-934`) because `.parent`/`inherited.key` are written only after the task completes
  (`:1045-1090`). And a guard test passes VACUOUSLY unless it seeds both
  `message(sid, "gentle-orchestrator")` and a valid route key (`seedKey`), since without them the
  warnings never fire (`:971`, `:973`, `:983`).
- **F5 (Claude) / F08 (Antigravity).** Silent drift: removing tracker, advice record and mirror leaves
  nothing to catch substantial work done as "tiny". The PM verifies the in-project traces only: a `ROUTER-LOG.md` row per tiny fix carrying commit and
  changed lines, and, for a mid-unit fix, a tracker `## Log` entry as part of the sanctioned tracker
  update.
  The permit-consumption log line is the guard's own diagnostic record, observed by whoever audits
  the guard log; it is not a PM obligation, and its absence MUST NOT block a unit. A scan flagging
  over-threshold `tiny` commits remains an audit measure. Add a pre-install diff gate: inspect
  `host_sandbox_result` before `host_sandbox_result_install`; if the real diff breaches the tripwire,
  re-route to ODD/Systematic.
- **F6 (Claude) / F10 (Antigravity).** The boundary needs a hard ONE-WAY tripwire that never selects:
  >20 authored changed lines, >2 touched files, a new/deleted file, or any edit to `verify-workflow.sh`,
  `global-config/opencode.json`, `global-config/systematic.jsonc`, `global-config/plugins/**`,
  permissions/auth/crypto, or public API contracts ⇒ escalate. Checked BEFORE `sandbox_apply` (the
  worker has one lifecycle). Pin the number in a test so it cannot rot.
- **F7 (Claude) / F07 (Antigravity).** PM tiny fixes conflict with the PM-handoff spec:
  `docs/specs/pm-handoff.md:7` limits a PM to `constraints.allowed paths`, and `:103` requires every
  commit in `candidate_commits` with its own receipt. A mid-unit tiny fix must stay inside the allowed
  paths and be recorded in the tracker/return envelope, sharing the unit's commit and review-boundary
  lineage.
- **F8 (Claude) / F11 (Antigravity).** `tests/test_pm_task_allowlists.py` would check only the SOURCE
  copy; the live config drifts (a sync has reset live `permission.task` before).
  `verify-workflow.sh:2843-2950` asserts PM invariants but not these keys.
- **F10 (Claude) / F09 (Antigravity).** `gentle-ai-worker-local` and `gentle-ai-verify-astra` were
  omitted; `pm-odd-astra`/`pm-systematic-astra` are not recognized by `pmRequiredRouteSkill`
  (`routing-guard-helpers.ts:27-35`) because it does not strip the `-astra` suffix, unlike
  `canonicalSpecialistType` (`systematic-routing-guard.ts:46-54`).
- **F05 (Antigravity).** `gentle-ai-verify` is model-independent of the DeepSeek writer, but shares
  `openai/gpt-6.1-sol` with BOTH PMs — so a PM judging its own framing is not independent.
- **F12 (Claude).** The read-only orchestrator cannot write `ROUTER-LOG.md`, so a standalone tiny fix
  needs the row inside the single worker's brief or captured in the commit trailer.

**SUGGESTIONS.**

- **F9 (Claude).** The upstream "direct inline" table already sits at `base.md:99-103`, and
  `overlay.md:55` overrides it only in general terms; v4.2.0's "about 100 changed lines" text will
  arrive on the next sync. Add one overlay sentence mapping upstream's direct-inline case to the
  Tiny-fix route via `gentle-ai-worker`, anchored on a stable marker, with the escalation threshold
  well below 100.
- **F4 (Claude).** PMs should limit `gentle-ai-verify` to tiny fixes and carry the `:144` fallback
  rule, since PMs don't read `WORKFLOW.md:144` directly.
- **F13 (Claude).** Normalize `-astra` in `pmRequiredRouteSkill`, or exclude `pm-*` in
  `astra-sol-upgrade.ts`.

### Evidence limits

- Neither host ran the guard against live sessions.
- Neither host invoked `opencode`/`gentle-ai` CLI probes (read-only constraint).
- The child→parent marker copy depends on the task output carrying `id="ses_..."` (`systematic-routing-guard.ts:1048`).
- `global-config/prompts/gentle-orchestrator/base.md:3` is still pinned to gentle-ai 4.0.0
  (`sha256:03206f6b...`), so the v4.2.0 wording was taken from the owner's prompt and
  `odd/tasks/q72-tiny-fix-route.md:9-10`, not from a v4.2.0 binary.
