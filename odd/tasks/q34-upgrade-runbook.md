# Q34 — Gentle AI v4 upgrade runbook

**Feature:** gentle-ai v4 upgrade / queue Q34 (upgrade runbook). **Task ID:** `q34-upgrade-runbook` (stable). **Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated). **Unit status:** T0 IN PROGRESS (tracker + advice created; T1 the runbook and its pointer edits pending). **Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07). **Prerequisites:** Q29–Q33 on the gated branch; Q36's change set (non-git surfaces only); Q63's post-upgrade repair is part of the sequence.

## Objective

Publish ONE authoritative upgrade runbook that an operator can execute alone, mid-upgrade, on a live machine, replacing a procedure currently stated four times and inconsistently.

## Problem

`docs/TODO.md:893-910` holds the 10-step procedure inline; the same sequence is restated differently at `CLAUDE.md:88`, `docs/HANDOFF-2026-10-02.md:20-25` and `WORKFLOW.md:26`. No upgrade document exists (`docs/upgrades/` and `upgrade/` are both absent). The four sources DISAGREE: the restart set differs (WORKFLOW.md = sandbox-broker + secure-opencode; CLAUDE/HANDOFF = secure-opencode + ai-proxy), the order varies, step 5 ("apply Q30–Q33") is wrong because those are already committed leaving Q36 carrying only NON-GIT surfaces (`docs/TODO.md:975`), `verify-workflow.sh --recover-config-only` is absent, and Q63's post-upgrade `inspect-authority`/`repair --preflight` steps are absent although Q63 is deferred TO the v4 upgrade (`docs/TODO.md:693-697`).

## Scope

In scope: T1 authors `docs/upgrades/gentle-ai-v4.md` and makes scoped POINTER edits in the four sources. Out of scope (preserved): `WORKFLOW.md:26`'s project-registration contract (it is a DIFFERENT scope — the pointer must not replace it); Q36's change-set CLI/journal contract; Q63's investigation outcomes; Q66; any execution of the upgrade.

## Constraints

The runbook must cite only flags that exist (verified: `--recover-config-only` and `--behavioral` in `verify-workflow.sh:88-100`; `changeset.py apply|revert --set|--journal-root|--allow-root|--verify-cmd|--dry-run`); the four sources keep their own scopes and receive scoped pointers, not blanket replacements; recovery is discoverable UP FRONT and linked inline; the two owner decisions (restart ALL THREE services sandbox-broker/secure-opencode/ai-proxy; keep the LAST 10 `backups/workflow-recovery/` runs) are recorded as owner-decided with runtime validation pending; do NOT instruct `brew downgrade`/`brew uninstall`, hand-editing `~/.config/opencode`, out-of-order journal revert, or presenting `--recover-config-only` as acceptance; any `verify-workflow.sh` edit would require the digest re-pin (T1 must not need one); branch `feat/gentle-ai-v4`; never switch branches; never commit.

## Acceptance criteria

One authoritative runbook exists ordered so that a partial failure is recoverable; every command cited is a real flag verified in the source; the change-set step says NON-GIT SURFACES ONLY; the sequence includes mirror → restart → CLEAN re-verify → `--behavioral`; Q63's two commands appear after re-verify; rollback names the v3.7.0 binary + change-set revert newest-journal-first + `git revert`; the expected pre-deploy RED baselines (`RETIRED_WORKFLOW_SKILL_PRESENT`, `SECURE_OPENCODE_RESTART_REQUIRED`) are named as expected, not as failures; the four sources point at the runbook without losing their own contracts; no fact lives authoritatively in two places.

## Authorized scope

T1: `docs/upgrades/gentle-ai-v4.md` (new), plus scoped pointer edits in `docs/TODO.md`, `CLAUDE.md`, `docs/HANDOFF-2026-10-02.md`, `WORKFLOW.md`. Plus this tracker, the advice record, `ROUTER-LOG.md`. No deployment, no execution.

## Checks

Every cited command/flag re-verified against its source (`path:line`); a link check that each pointer target exists; a planted-duplicate control proving the drift check can detect the same procedure being restated again; `python3 -m unittest discover -s tests` unaffected (no code change expected); `git diff --stat` reviewed for scope.

## Tasks

- [ ] T1 — author `docs/upgrades/gentle-ai-v4.md` (structure: scope/preconditions → recovery link up front → numbered upgrade steps with action/expected/stop-link → recovery section → completion and evidence → operational decisions and open questions → references) and make the scoped pointer edits in the four sources.

## Progress

- 2026-10-11: T0 — tracker and advice record created from two pre-code advisories and an owner decision round; no artifact edit yet. Route: delegated.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; the PM layer is unusable). Trigger: secure no-inline-mutation policy; multiple files → bounded sandbox writer.

## Next step

T1 (the runbook + the pointer edits), then the owner's review of the runbook before it is ever executed.
