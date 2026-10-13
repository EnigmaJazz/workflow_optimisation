# Q34 — Gentle AI v4 upgrade runbook

**Feature:** gentle-ai v4 upgrade / queue Q34 (upgrade runbook). **Task ID:** `q34-upgrade-runbook` (stable). **Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated). **Unit status:** DONE — the runbook was EXECUTED on 2026-10-13 against gentle-ai 4.1.1 and the upgrade completed. Steps 1-12 all resolved (see "Execution record" below). **Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07). **Prerequisites:** Q29–Q33 on the gated branch; Q36's change set (non-git surfaces only); Q63's post-upgrade repair is part of the sequence.

## Pre-install preconditions (recorded 2026-10-12)

All four runbook preconditions are satisfied and observed before Step 2:

- [x] **Verifier pin MATCHES.** `sha256sum verify-workflow.sh` = `621a7f93c2fc9dee8469793e751069b016e1121ece9d92eaaf3d342e605ad468`; `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts:93` = the same digest. The verifier will accept its own script.
- [x] **Installed version recorded.** `gentle-ai --version` → `gentle-ai 3.7.0`; `command -v gentle-ai` → `/home/linuxbrew/.linuxbrew/bin/gentle-ai` (symlink into `/home/linuxbrew/.linuxbrew/Cellar/gentle-ai/3.7.0/bin/gentle-ai`); `brew list --versions gentle-ai` → `gentle-ai 3.7.0`.
- [x] **Rollback artifact created and verified.** `ls (brew --prefix)/Cellar/gentle-ai/` showed ONLY `3.7.0` — no prior keg — so the binary was copied aside BEFORE any upgrade: `cp /home/linuxbrew/.linuxbrew/Cellar/gentle-ai/3.7.0/bin/gentle-ai ~/gentle-ai-3.7.0.bin`. Proven standalone: `~/gentle-ai-3.7.0.bin --version` → `gentle-ai 3.7.0` (resolves without the Homebrew symlink). **This path is the rollback artifact the runbook requires.**
- [x] **Q39 dispositions RECORDED** (owner, 2026-10-12) — see `docs/TODO.md` "Q39 dispositions — OWNER DECISION (2026-10-12)".

EXECUTED 2026-10-13 (gentle-ai 3.7.0 -> 4.1.1). See the Execution record below.

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

## Execution record — 2026-10-13 (gentle-ai 3.7.0 -> 4.1.1)

All preconditions were satisfied first (pin MATCH; version recorded; rollback artifact `~/gentle-ai-3.7.0.bin` created and proven standalone because `ls (brew --prefix)/Cellar/gentle-ai/` held ONLY `3.7.0`; Q39 dispositions recorded on 3.7.0 while `sdd-status` still existed).

| Step | Result |
|---|---|
| 1 Confirm install method | OK — `command -v gentle-ai` -> `/home/linuxbrew/.linuxbrew/bin/gentle-ai` |
| 2 Upgrade the binary (ONE-WAY DOOR) | OK — `brew upgrade gentle-ai` 3.7.0 -> 4.1.1; the 3.7.0 keg and its tarball were REMOVED by Homebrew, so `~/gentle-ai-3.7.0.bin` is now the only 3.7.0 copy. A Landlock warning appeared (kernel ABI 8 < required 10): benign, it only weakens build-time network denial. |
| 3 Sync v4 managed assets | OK — the preview ran from the NEW binary (4.1.1) and reported `Agents: opencode,windsurf,antigravity`, components `persona, engram, context7, gga, skills`, `Prepare steps: 4 / Apply steps: 21`. The apply reported `Sync actions executed: 123 files changed`. It DELETED the SDD assets (commands `sdd-*.md`, skills `sdd-*`, `prompts/sdd/*`, `plugins/sdd-task-result-artifacts.ts`) and OVERWROTE `opencode.json` and `AGENTS.md` (restored at Step 6). |
| 4 Change set | NOT APPLICABLE (documented skip; no `upgrade/v4` set exists and none is authorable). |
| 5 One-time manual cleanup | NO-OP — `~/.config/opencode/skills/workflow-sdd-secure` was already absent; the verifier later confirmed `no retired workflow skill directories present`. |
| 6 Mirror the config | OK — recovered `opencode.json` (also reconciling the canonical pin `@fro.bot/systematic 3.21.5 -> 3.21.8`), `AGENTS.md`, 4 reviewed workflow skill files, and re-mirrored `workflow-health-check.ts`. It reported the EXPECTED `SECURE_OPENCODE_RESTART_REQUIRED` with `RUNTIME_RESTART_REQUIRED=1`, which is why the runtime checks were skipped at that point. |
| 7 Restart all three services (ONE-WAY DOOR) | OK — `sandbox-broker.service`, `secure-opencode.service`, `ai-proxy.service` restarted. |
| 8 Re-verify, require CLEAN | OK — a CLEAN full run (`All checks passed — workflow setup intact`); the restart requirement cleared and sections 9a/9b ran for real. |
| 9 Behavioral probes | OK on the second attempt. The FIRST `--behavioral` run failed the fan-out probe with exit 1, printing only session-creation and guard-registration lines. A manual re-run of the identical probe in the same cwd shape returned exit 0 with both sentinels and `PARALLEL_FANOUT_DONE`, so the failure was TRANSIENT (exit 1, not the 180s timeout's 124). The verifier was then re-run and passed BOTH probes: 10 (fan-out emitted both Task calls in one assistant message with overlapping intervals) and 10a (planning-only request launched no writer and created no ODD tracker). |
| 10 Q63 post-upgrade review-store check | BOTH SUBCOMMANDS EXIST (this resolves the runbook's UNVERIFIED caveat). `review inspect-authority`: `complete:false, valid:false`, 12 compact entries, 6 loaded, 0 edges, and 6 entry diagnostics all `malformed_compact_state`, with `sanctioned_exits: []`. `review repair --preflight`: `status: "unsupported"`, 12 lineages (all compact, 0 legacy), 6 `unsupported_lineages`, `eligible_candidates: 0`, `supported_operations: ["review/complete-fix","review/validate-fix"]`, `required_inputs: []`. INTERPRETATION: those two supported operations finish in-flight corrections, not malformed compact state, so the 6 malformed lineages are NOT repairable by this tool and no input is owed. FINDING, not a blocker: RDD is on and demonstrably working (a dozen 4-lens reviews ran across this session, including two after the upgrade); the 6 malformed lineages are pre-v4 residue. |
| 11 Dispatch checks | OK — four lane families dispatched from an orchestrator session (the real Task path, not the disqualified `opencode run --agent advisor-*` fallback) and all returned evidence: `advisor-design-pre`, `gentle-ai-explore`, `gentle-ai-worker`, `gentle-ai-verify` (the last reported a digest MATCH). CAVEAT: the advisor could not prove its own runtime identity from inside the task. The `asi-review-*` lanes were NOT synthetically probed — they are provider-materialized and refuse without a live review context; that family is instead proven by this session's own 4-lens reviews and by verifier section 9a. |
| 12 Retention | RESOLVED and PROMOTED — the rule is now global: `WORKFLOW.md` "Recovery-backup retention" (commit `de85e7c`), with the runbook citing it as the authority. |

### Runbook corrections made during the walk-through (all committed)
- Step 4 was unrunnable and is now "NOT APPLICABLE for this upgrade"; the change-set revert section is marked inert for v4 (`d3d53bd`).
- Step 10's authoring caveat is now RESOLVED — both subcommands exist (above).
- Completion item 4 was disambiguated: it means Step 11's manual owner/TUI checks, not the verifier's `--behavioral` probes.
- Step 1's sync preview was MIS-ORDERED (it ran the 3.7.0 binary before Step 2 upgraded it) and was moved to the head of Step 3 (`14aa27e`).

### Observations worth carrying (not blockers)
- `~/.config/opencode/commands/sdd-code.md` SURVIVED the sync (it was not in the changed list); every other SDD command was deleted. Whether v4.1 omitted it or it is a user file is UNVERIFIED.
- `~/.config/opencode/skills/nono-sandbox` appears as a non-directory entry among directories — UNVERIFIED.
- Sync manages three platforms (opencode, windsurf, antigravity); the windsurf skill root is inside gentle-ai's skill-registry scan path, which is why the default all-platform sync was chosen.
- `~/.claude/CLAUDE.md`'s managed blocks remain owner-managed post-sync (Q35 out of scope, Q38 post-sync check) and were NOT touched by this upgrade.
