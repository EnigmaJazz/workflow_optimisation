# Q32 — verify-workflow.sh v4 overhaul: pre-code advice

**Change:** Q32 verifier v4 overhaul (class: global-tooling-change). **Branch:** feat/gentle-ai-v4. **Date:** 2026-10-11.
**Advisors:** `advisor-integration-pre` (ses_ed58741ecffeLw40QkPiTs0RY3), `advisor-testing-pre` (ses_ed58738c3ffe6B87i7HTQ6b2GT). Read-only; no mutation.

## Integration advice
- `verify-workflow.sh` and `global-config/plugins/workflow-health-check.ts` (`VERIFY_SCRIPT_SHA256`, :93) MUST change in the same commit — the health-check plugin is fail-closed on a digest mismatch (:60-70, :112-118).
- Removing the `user:host-sdd-runtime-boundaries` block from `global-config/AGENTS.md:49-59` MUST be paired, in the SAME commit, with deleting the verifier recovery logic for that block: constants `verify-workflow.sh:909-910`, legacy insertion `:988-1002`, routing heredoc `:1316`, compare tuple `:4434-4439`, success message `:4450-4453`. `recover_agents_file`'s `canonical_block` raises `ValueError` on a missing marker pair (:900-905), so removing the source block alone makes AGENTS self-heal fail closed.
- The recovery manifest still lists `workflow-sdd-secure` (:813) and reports "four reviewed workflow skills" (:842).
- The routing-contract `cat` still includes `workflow-sdd-secure/SKILL.md` + its reference (:4481-4482); if the skill is gone, `ROUTING_CONTRACT` is partial and the :4520-4561 greps fail.
- Stale routing-contract grep targets ("SDD artifact writers use sandbox tools", "no direct-inline implementation path", "four or more files", "20 tool calls or five exploratory reads", "frontend-dev-premium", "two substantive visual iteration rounds") appear only in the retired `workflow-sdd-secure/references/sdd-magic-adapter.md`; absent from WORKFLOW.md, the ODD/Systematic skills, and the deployed AGENTS.md → remove/replace and re-verify each.
- SDD residue in guard/plugins is owned by Q33, not Q32: `systematic-routing-guard.ts:280-284`, `routing-guard-helpers.ts:35` (`pm-sdd` → `workflow-sdd-secure`).
- v4 version strings: `:10`; version floor `3.5.0` at `:3462`; `GENTLE_AI_V3_5_*` (:3472/:3480/:3486); `gentle-ai sdd-archive-compose` (:3494-3498); `sdd-research|sdd-verify|sdd-archive` SKILL.md requirements (:3513-3538).
- `global-config/AGENTS.md:247` still references `workflow-sdd-secure` (observed 2026-10-11) — slice 4 drops it.
- Negative checks to add: no `sdd-*` agent in the deployed config; every `host_sdd_*` permission `deny` (global + orchestrator + PMs), moving `host_sdd_status`/`host_sdd_continue`/`host_sdd_task_result` out of `registeredHostReads` (:2702); v4 generic agents registered with the expected tools.
- Deploy after commit: verifier mirror, then OpenCode restart (owner's action).

## Testing advice
- Reuse the Q30 probe pattern (`odd/tasks/gentle-ai-v4.md:241-261`) and `tests/routing-guard/routing-guard.test.ts:72-77`: assert (a) every stale string is absent, (b) every preserved anchor is present, and (c) a re-introduced stale string still trips the check. Without (c), an `! grep -q` check passes vacuously on an empty fixture.
- Anchors that MUST stay: `:4329` "two or more non-trivial files", `:4481-4489` `SEARCH_TOOL_ROUTING_DRIFT`, `:3417` "400 authored changed lines and 100 KiB"; the preserved `sdd-explore` literal at `WORKFLOW.md:94` must NOT be treated as a stale token.
- The three new absence checks need fixture+invocation proof, not bare greps: inject a bad value under `$(mktemp -d)` and observe the specific `fail()` code (`SDD_AGENT_REAPPEARED`, `HOST_SDD_PERMISSION_NOT_DENY` / `HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY`, `V4_GENERIC_AGENT_TOOL_MISSING`). Never run the verifier against the host tree.
- `bash -n` is syntax-only and is NOT evidence. Fixtures live under `$(mktemp -d)`, never host `~/.config/opencode`.
- Test-first ordering: refresh the drifted line refs first; then manifest/recovery; then heredoc + section 7 + routing-contract; then section 9 checks; re-pin the digest LAST within each commit and assert pin == `sha256sum` before any runtime probe.

## PM-layer note (2026-10-11)
Two `pm-odd` dispatches for this unit returned `BLOCKED`: the coordinator has no Git-state read surface, so it cannot perform the mandated unit-start branch/HEAD verification (`docs/specs/pm-handoff.md:15-19`). The PM-layer design is therefore not operational for this unit (pm-layer tracker T4 pilot incomplete). This unit proceeds via a direct `odd-apply` dispatch (the Q31 operational path); routing-guard warnings for direct dispatch and the not-yet-present advice record are expected and warning-only. **Status: CLOSED by Q55 (2026-10-14).** `docs/specs/pm-handoff.md` now names the criterion (the brief's `feature_branch`) and the mechanism (read `.git/HEAD` with the existing `read` grant and compare it against `ref: refs/heads/<feature_branch>`); detached HEAD, a worktree HEAD under `.git/worktrees/`, an unborn branch, and an in-progress rebase or merge each return `BLOCKED`.
