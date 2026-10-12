# Q34 — Gentle AI v4 upgrade runbook

**Feature:** gentle-ai v4 upgrade / queue Q34 (upgrade runbook). **Task ID:** `q34-upgrade-runbook` (stable). **Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated). **Unit status:** T0–T1 DONE-AT-SOURCE (Q34 source complete; committed). The runbook is authored and the four sources point at it; runtime validation of its steps is PENDING — it has never been executed. **Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07). **Prerequisites:** Q29–Q33 on the gated branch; Q36's change set (non-git surfaces only); Q63's post-upgrade repair is part of the sequence.

## Pre-install preconditions (recorded 2026-10-12)

All four runbook preconditions are satisfied and observed before Step 2:

- [x] **Verifier pin MATCHES.** `sha256sum verify-workflow.sh` = `621a7f93c2fc9dee8469793e751069b016e1121ece9d92eaaf3d342e605ad468`; `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts:93` = the same digest. The verifier will accept its own script.
- [x] **Installed version recorded.** `gentle-ai --version` → `gentle-ai 3.7.0`; `command -v gentle-ai` → `/home/linuxbrew/.linuxbrew/bin/gentle-ai` (symlink into `/home/linuxbrew/.linuxbrew/Cellar/gentle-ai/3.7.0/bin/gentle-ai`); `brew list --versions gentle-ai` → `gentle-ai 3.7.0`.
- [x] **Rollback artifact created and verified.** `ls (brew --prefix)/Cellar/gentle-ai/` showed ONLY `3.7.0` — no prior keg — so the binary was copied aside BEFORE any upgrade: `cp /home/linuxbrew/.linuxbrew/Cellar/gentle-ai/3.7.0/bin/gentle-ai ~/gentle-ai-3.7.0.bin`. Proven standalone: `~/gentle-ai-3.7.0.bin --version` → `gentle-ai 3.7.0` (resolves without the Homebrew symlink). **This path is the rollback artifact the runbook requires.**
- [x] **Q39 dispositions RECORDED** (owner, 2026-10-12) — see `docs/TODO.md` "Q39 dispositions — OWNER DECISION (2026-10-12)".

Not yet done: Steps 1–12 themselves (never executed). The runbook's first execution is its validation.

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

- [x] T1 — author `docs/upgrades/gentle-ai-v4.md` (structure: scope/preconditions → recovery link up front → numbered upgrade steps with action/expected/stop-link → recovery section → completion and evidence → operational decisions and open questions → references) and make the scoped pointer edits in the four sources.

## Progress

- 2026-10-11: T0 — tracker and advice record created from two pre-code advisories and an owner decision round; no artifact edit yet. Route: delegated.
- 2026-10-11: T1 committed `3789cc1` (5 files, +272/−16; authored 288 lines). Authored `docs/upgrades/gentle-ai-v4.md` (257 lines): scope/preconditions with "Already mid-upgrade? Go to Recovery" up front → 12 numbered steps each as Action → Expected result → If it fails → a Recovery section (failure-state table first, then binary rollback, config recovery, change-set revert, repo-level rollback, expected-RED baselines) → completion/evidence → owner decisions/open questions → references. The sequence records the corrected order: Q39 dispositions BEFORE the binary upgrade (`gentle-ai sdd-status` exists only on 3.7.0); the change set applies NON-GIT SURFACES ONLY (Q30–Q33 are committed); the one-time `rm -rf ~/.config/opencode/skills/workflow-sdd-secure`; mirror → restart ALL THREE services → CLEAN re-verify → `--behavioral` → Q63 `inspect-authority`/`repair --preflight` → dispatch checks via the owner/TUI route → retention. Pointer edits: `docs/TODO.md` Q34 entry now names the runbook as sole authority (inline 10-step procedure removed); `CLAUDE.md` keeps the general deployment policy and points at the runbook; `docs/HANDOFF-2026-10-02.md` marked HISTORICAL with a "do not execute as a runbook" callout; `WORKFLOW.md:26`'s project-registration contract PRESERVED byte-for-byte with ONE added sentence naming the runbook for v4 activation.
- 2026-10-11: T1 evidence — every cited flag/command re-verified against source (`--behavioral` `:85-86`; `--recover-config-only` `:88-89`; `SECURE_OPENCODE_RESTART_REQUIRED`/`RUNTIME_RESTART_REQUIRED` `:4275-4278`; behavioural skipped when earlier checks fail `:5008-5011`; `RETIRED_WORKFLOW_SKILL_PRESENT` `:3928`; `RECOVERY_BACKUP_ROOT` `:126`; `changeset.py` subcommands/options `:1008-1018`; out-of-order revert refused `:970-986`; dry-run does not execute `--verify-cmd`; the service names confirmed real). Link check: every internal link target verified present (including `odd/tasks/guard-q03.md`). Planted-duplicate control: a copy of Step 7 planted in a gitignored worker-local path made the content search return 2 hits (duplication detected), removing it returned 1 — reported with the honest limitation that sandbox tools cannot write outside the project root, and that a LINK checker alone cannot detect semantic duplication. `python3 -m unittest discover -s tests` 102 OK. No `verify-workflow.sh` edit, so NO digest re-pin.
- 2026-10-11: T1 assessment: risk medium (`executable_change` on CLAUDE.md), 5 files / 288 changed lines, `review_due: false` (`under_budget`) — the slice accumulates rather than triggering a review.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; the PM layer is unusable). Trigger: secure no-inline-mutation policy; multiple files → bounded sandbox writer.

## Next step

OWNER ACTION: READ the runbook before executing it — it has never been run. Then the deployment it describes: `bash verify-workflow.sh` to mirror, restart all three services, a CLEAN re-verify, `--behavioral`, the Q63 review-store check, and the dispatch checks. Carry-forward: the runbook's steps are unvalidated against a live upgrade; the first real execution is the validation.
