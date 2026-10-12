# Gentle AI v4 upgrade

This document is the sole authority for Gentle AI v4 **upgrade execution, activation, recovery
and completion checks**. It replaces a procedure that was previously restated, inconsistently,
across four sources (`docs/TODO.md` Q34, `CLAUDE.md`, `docs/HANDOFF-2026-10-02.md`, `WORKFLOW.md`),
which now point here. Execution is **owner-only**: publishing or tracking this document does not
authorize the upgrade. Do not begin unless the owner has decided to upgrade.

Validated against source revision: branch `feat/gentle-ai-v4`, HEAD `f29a1fd` (2026-10-11).
Re-check that revision before executing; if the branch has moved, re-validate every command whose
source changed (see [References](#references)).

Recovery is up front. If you are already partway through the upgrade, go straight to
[Recovery](#recovery).

## Before you change anything

Work through this checklist in order. The last item is the one most easily placed too late.

- [ ] **Branch:** you are on `feat/gentle-ai-v4`.
- [ ] **Verifier pin:** the verifier source digest matches `VERIFY_SCRIPT_SHA256` in
      `global-config/plugins/workflow-health-check.ts`. A mismatch must be fixed first: the
      verifier refuses a mismatched script.
- [ ] **Installed version:** record `command -v gentle-ai` and the version it reports.
- [ ] **Rollback artifact:** record the path of the kept v3.7.0 binary. It is the only supported
      rollback for the binary upgrade.
- [ ] **Q39 in-flight SDD dispositions are RECORDED.** `gentle-ai sdd-status` exists only on
      3.7.0, so this MUST happen before the binary upgrade — a prerequisite placed after the
      upgrade cannot run. The change-set gate for Q39 is **not implemented**; the operator is the
      only enforcement.
- [ ] **The upcoming sync is DESTRUCTIVE for SDD residue.** Gentle AI v4.1.x removes
      Gentle-owned SDD agents, skills, commands, hooks and prompt blocks, so Step 3
      (`gentle-ai sync`) deletes any SDD residue. Record the rollback artifact (see above) and the
      Q39 dispositions (see above) before it runs; neither can be recovered afterwards.

**Already mid-upgrade? Go to [Recovery](#recovery).**

## Upgrade

The order is forced; do not reorder. Each step is `Action` → `Expected result` → `If it fails`.
A `ONE-WAY DOOR` step cannot be undone in place; the named artifact is the recovery.

### Step 1: Confirm the install method

- **Action:** `command -v gentle-ai`.
- **Expected result:** the `gentle-ai` path is printed.
- **If it fails:** [Binary rollback](#binary-rollback).

The sync preview moved to [Step 3](#step-3-sync-v4-managed-assets): the dry run must follow the
binary upgrade ([Step 2](#step-2-upgrade-the-binary-one-way-door)) so it previews the v4.1 assets;
run before it, the dry run would preview 3.7.0's assets.

### Step 2: Upgrade the binary (ONE-WAY DOOR)

- **Action:** `brew upgrade gentle-ai`.
- **Expected result:** Homebrew installs gentle-ai 4.x over 3.7.0.
- **Rollback artifact:** the kept v3.7.0 binary recorded above. Do not use `brew downgrade` or
  `brew uninstall`.
- **If it fails:** [Binary rollback](#binary-rollback).

### Step 3: Sync v4 managed assets

- **Action (preview):** `gentle-ai sync --dry-run`. This MUST run after
  [Step 2](#step-2-upgrade-the-binary-one-way-door): it is the first point at which the dry run
  previews the v4.1 managed-asset changes; earlier it would preview 3.7.0's.
- **Action (apply):** `gentle-ai sync`.
- **Expected result:** the dry run lists the planned v4.1 managed-asset changes and exits 0, then
  the apply overwrites managed agents and prompts with the v4 assets. A non-zero exit is possible
  when sync cannot detect the OpenCode version. The verifier re-establishes the reviewed config in
  [Step 6](#step-6-mirror-the-config), so that non-zero is tolerated, not a stop.
- **If it fails:** a hard failure other than the version-detection exit →
  [Config recovery](#config-recovery).

### Step 4: The change set — NOT APPLICABLE for this upgrade

**No change set applies for this upgrade, and one cannot usefully be authored.** `--set` names a
DIRECTORY that must contain a `changeset.json`: `load_set` joins `set_dir + "changeset.json"`
(`scripts/changeset.py:633-634`) and raises `Refuse("invalid_set")` at `:639-640` when it is
absent — exit 3 before any write (`:1036-1040`). No `upgrade/v4` directory exists in this
repository (`docs/TODO.md:985` describes `upgrade/v4/` in future tense), so the apply command
cannot run: not a no-op that silently succeeds, but a command that is unrunnable.

Even were a set directory created, the op schema (`scripts/changeset.py:624-630`) supports exactly
five kinds — `json_set`, `json_delete`, `block_replace`, `file_create`, `file_remove` — and
`file_remove` operates on a SINGLE file with a 64-hex `expect_sha256` (`:629`, `:663-664`); a
DIRECTORY removal is not expressible. The only remnants this upgrade leaves are:

- the retired skill directory `~/.config/opencode/skills/workflow-sdd-secure`, which is a
  DIRECTORY and is owned by the manual cleanup in [Step 5](#step-5-one-time-manual-cleanup); and
- the `~/.claude/CLAUDE.md` managed blocks, which `block_replace` could carry but which are out
  of scope here (Q35) and deferred post-sync (Q38).

Every live `~/.config/opencode` surface is regenerated by the verifier in
[Step 6](#step-6-mirror-the-config), so there is nothing left for a set to carry.

- **Action:** none — skip this step. Skipping is the CORRECT behaviour; do not invent a set.
- **Expected result:** no change set directory is created and `changeset.py apply` is never run.
- **If you were expecting to run a set:** the content is deliberately build-late; see `docs/TODO.md`
  Q36 for the recorded verdict. Revisit only if a future upgrade has authorable,
  non-regenerated, non-directory content.

<details>
<summary>Reference for FUTURE upgrades (not executable advice for this one)</summary>

Once a set directory containing a `changeset.json` exists, the tooling below applies:

- **Preview:** `python3 scripts/changeset.py apply --set <set-dir> --journal-root backups/changesets --dry-run`
- **Apply:** the same command without `--dry-run`.
- `--allow-root <dir>` (repeatable) extends the defaults `~/.config/opencode` and `~/.claude`
  (spec §2; `scripts/changeset.py:1010`).
- `--verify-cmd 'bash verify-workflow.sh'` is supported (spec §9; `scripts/changeset.py:1017`) and
  runs the verifier before any write; the verifier itself repairs config, so choose the pre-apply
  generation deliberately (see the open question in
  [§6](#operational-decisions-and-open-questions)).
- Exit codes: 0 = every op `applied`/`already_applied`; 2 = at least one
  `conflict`/`drift`/`unknown`; 3 = refused before any write. A dry run does NOT execute
  `--verify-cmd` (spec §8), so "dry-run passed" or "exit 0" proves nothing about runtime health.

</details>

### Step 5: One-time manual cleanup

- **Action:** `rm -rf ~/.config/opencode/skills/workflow-sdd-secure`.
- **Expected result:** the retired skill directory is gone. Until this runs the verifier stays RED
  with `RETIRED_WORKFLOW_SKILL_PRESENT` (`verify-workflow.sh:3928`) — that is the EXPECTED
  baseline, not a defect.
- **If it fails:** fix permissions and re-run; do not skip it.

### Step 6: Mirror the config

- **Action:** `bash verify-workflow.sh`.
- **Expected result:** it commonly reports `SECURE_OPENCODE_RESTART_REQUIRED` with
  `RUNTIME_RESTART_REQUIRED=1` (`verify-workflow.sh:4275-4278`): the verifier repaired config
  after the service started, so the runtime agent checks are SKIPPED. That is expected at this
  point, not the final run.
- **If it fails:** [Config recovery](#config-recovery); the expected RED codes are enumerated in
  [Expected-RED baselines](#expected-red-baselines).

### Step 7: Restart ALL THREE services (ONE-WAY DOOR)

Runtime state is lost on restart. This document resolves the source disagreement: `WORKFLOW.md:26`
names `sandbox-broker.service` + `secure-opencode.service`, while `CLAUDE.md:88` and
`docs/HANDOFF-2026-10-02.md:23` name `secure-opencode.service` + `ai-proxy.service`. The owner
decision (2026-10-11) is all three.

- **Action (Fish):** `systemctl --user restart sandbox-broker.service secure-opencode.service ai-proxy.service`
- **Expected result:** all three units restart and become active again.
- **If it fails:** [Binary rollback](#binary-rollback) or [Config recovery](#config-recovery)
  depending on the failing unit.

### Step 8: Re-verify and require a CLEAN run

- **Action:** `bash verify-workflow.sh`.
- **Expected result:** a clean run with no failures. Do not proceed on a failing run.
- **If it fails:** [Recovery](#recovery); do not treat a failing run as done.

### Step 9: Behavioral probes

- **Action:** `bash verify-workflow.sh --behavioral`.
- **Expected result:** the Task fan-out and read-only planning probes pass. It is SKIPPED when
  earlier checks failed (`verify-workflow.sh:5008-5011`), so [Step 8](#step-8-re-verify-and-require-a-clean-run)
  must be clean first.
- **If it fails:** [Recovery](#recovery).

### Step 10: Q63 post-upgrade review-store check

- **Action:** `gentle-ai review inspect-authority` then `gentle-ai review repair --preflight`.
- **Expected result:** record whether the previously malformed compact-state lineages read cleanly
  or are offered as repairable candidates. Report what the CLI says; do not assert recovery.
- **If it fails:** record the outcome for Q63. This is an observation, not a stop.
- **Authoring caveat (UNVERIFIED):** `inspect-authority` and `repair --preflight` could not be
  confirmed without executing the CLI, so both were UNVERIFIED at authoring time. Confirm each
  subcommand exists when this step is first run; if one does not exist, record that finding and
  continue.

### Step 11: Dispatch checks through the owner/TUI route

- **Action:** from the owner/TUI, dispatch `advisor-*`, the v4 generic agents
  (`gentle-ai-explore`, `gentle-ai-worker`, `gentle-ai-verify`) and the `asi-review-*` lanes on
  bounded tasks.
- Scripted `opencode run --agent advisor-*` is NOT a valid check: it silently falls back to the
  primary agent.
- **Expected result:** each dispatched agent runs and returns evidence. Naming a check is not
  evidence it ran.
- **If it fails:** record which dispatch failed (Q51).

### Step 12: Retention

- **Action:** keep the last 10 `backups/workflow-recovery/` runs and delete older ones.
- **Expected result:** at most 10 timestamped recovery directories remain. The verifier does not
  prune them.
- **If it fails:** no stop; retention is housekeeping.

## Recovery

### Failure-state table

| Symptom | Entry point |
|---|---|
| Binary missing or broken after `brew upgrade` | [Binary rollback](#binary-rollback) |
| Live config drifted, or a `verify-workflow.sh` failure | [Config recovery](#config-recovery) |
| Change set refused, or an op `conflict`/`drift` | [Change-set revert](#change-set-revert) |
| The wrong source commit is on the branch | [Repo-level rollback](#repo-level-rollback) |
| A RED code looks new | [Expected-RED baselines](#expected-red-baselines) |

### Binary rollback

Restore the kept v3.7.0 binary artifact recorded in [Before you change anything](#before-you-change-anything).
Do NOT run `brew downgrade` or `brew uninstall`: neither is a supported rollback and both can leave
a broken formula or prefix. After restoring, re-run [Step 6](#step-6-mirror-the-config) and
[Step 8](#step-8-re-verify-and-require-a-clean-run).

### Config recovery

- **Action:** `bash verify-workflow.sh --recover-config-only`.
- It restores the reviewed `opencode.json`, `AGENTS.md`, `systematic.jsonc`, the mapped
  fallback-policy overlays and the TUI plugin discovery surface, then exits without running
  package, plugin or paid-runtime probes.
- **It is NOT the acceptance run.** It skips the package, plugin and paid-runtime probes, so a
  green result here does not mean the upgrade is healthy. The full verifier
  ([Step 8](#step-8-re-verify-and-require-a-clean-run)) is the acceptance gate.

### Change-set revert

**Inert for this upgrade.** [Step 4](#step-4-the-change-set--not-applicable-for-this-upgrade)
applies nothing, so no apply journal is written under `backups/changesets/` and there is nothing
to revert. The procedure below is retained because it stays correct for any future set that does
apply.

- **Action:** `python3 scripts/changeset.py revert --journal <journal-root>/<set-id>/<run>/journal.jsonl --journal-root backups/changesets`
- Revert the **newest apply journal FIRST**. `revert` refuses an out-of-order revert with
  `refused: newer_journal_not_reverted`, naming the newer journal (spec §6 "Enforced order";
  implemented by `check_order`, `scripts/changeset.py:970-986`). There is no `check_order`
  subcommand — the refusal comes from `revert` itself.
- A revert reports `drift` instead of overwriting a file another actor changed; the drifted file
  is reported and left as it is.

### Repo-level rollback

`git revert` the branch merge commit (the commit that merged `feat/gentle-ai-v4`). This restores
the tracked source only; it does not touch the live config, which is the change set's job
([Change-set revert](#change-set-revert)) and the verifier's ([Config recovery](#config-recovery)).

### Expected-RED baselines

These RED codes are EXPECTED during the upgrade and must not be mistaken for new failures:

- `RETIRED_WORKFLOW_SKILL_PRESENT` (`verify-workflow.sh:3928`) — expected until
  [Step 5](#step-5-one-time-manual-cleanup) removes
  `~/.config/opencode/skills/workflow-sdd-secure`.
- `SECURE_OPENCODE_RESTART_REQUIRED` with `RUNTIME_RESTART_REQUIRED=1`
  (`verify-workflow.sh:4275-4278`) — expected after [Step 6](#step-6-mirror-the-config) repaired
  config post-start; cleared by [Step 7](#step-7-restart-all-three-services-one-way-door).

## Completion and evidence

The upgrade is complete only when ALL of these are true:

1. A CLEAN full verifier run ([Step 8](#step-8-re-verify-and-require-a-clean-run)).
2. `bash verify-workflow.sh --behavioral` passes ([Step 9](#step-9-behavioral-probes)).
3. The Q63 outcome is recorded ([Step 10](#step-10-q63-post-upgrade-review-store-check)).
4. The dispatch checks were actually observed to run — meaning the **manual owner/TUI checks of
   [Step 11](#step-11-dispatch-checks-through-the-ownertui-route)**, NOT the verifier's
   `--behavioral` probes of [Step 9](#step-9-behavioral-probes) and NOT the verifier's own
   `explore`/`general` fan-out checks.

Record the evidence in the Q34 tracker (`odd/tasks/q34-upgrade-runbook.md`) and in `ROUTER-LOG.md`.
**A green verifier alone does NOT mean the upgrade is complete.**

## Operational decisions and open questions

Two owner decisions are recorded once, **owner-decided for this upgrade; runtime validation
pending**:

1. **Restart all three services** — `sandbox-broker.service`, `secure-opencode.service`,
   `ai-proxy.service` ([Step 7](#step-7-restart-all-three-services-one-way-door)).
2. **Keep the last 10 `backups/workflow-recovery/` runs**
   ([Step 12](#step-12-retention)). A "recovery run" is one verifier recovery invocation's
   timestamped directory under `backups/workflow-recovery/` (`RECOVERY_BACKUP_ROOT`,
   `verify-workflow.sh:126`). It is NOT a change-set journal: those live under
   `backups/changesets/`, a different root.

Open questions this runbook had to decide:

- **Q39 gate unimplemented** → the operator enforces the in-flight SDD dispositions manually
  ([Before you change anything](#before-you-change-anything)). Revisit when the Q39 change-set
  gate is implemented.
- **The pre-apply verifier repairs config** → for v4 there is no change-set apply to precede
  ([Step 4](#step-4-the-change-set--not-applicable-for-this-upgrade)), so the verifier runs at
  [Step 6](#step-6-mirror-the-config). Revisit if the change-set tool gains a read-only preflight.
- **`openchamber-secure` restart** → no source raises one; `WORKFLOW.md:26` states it does not
  require restart for registration. Revisit if a v4 component starts depending on it.

## References

- Tool contract: [`docs/specs/changeset-tool.md`](../specs/changeset-tool.md).
- Queue entries: Q34, Q36 and Q63 in [`docs/TODO.md`](../TODO.md).
- Constraints and rationale (links only, never copied procedures): [`docs/PLAN.md`](../PLAN.md),
  section "Upgrade change set".
- Verifier: [`verify-workflow.sh`](../../verify-workflow.sh); change-set CLI:
  [`scripts/changeset.py`](../../scripts/changeset.py).
- Tracker: [`odd/tasks/q34-upgrade-runbook.md`](../../odd/tasks/q34-upgrade-runbook.md); log:
  [`ROUTER-LOG.md`](../../ROUTER-LOG.md).
- Deployment policy: [`CLAUDE.md`](../../CLAUDE.md); recipe: [`WORKFLOW.md`](../../WORKFLOW.md).
