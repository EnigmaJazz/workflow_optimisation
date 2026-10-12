# Q34 — Upgrade runbook advice record

Pre-code advice for the Gentle AI v4 upgrade runbook. Both advisories were
captured on 2026-10-11, before any artifact edit. Every `path:line` and every
correction below is preserved verbatim.

## advisor-integration-pre (2026-10-11)

### Corrected ordering (13 steps)

The correct sequence is a 13-step order. The critical correction is that the
Q39 dispositions are recorded BEFORE the binary upgrade, because
`gentle-ai sdd-status` exists only on 3.7.0 — a prerequisite placed too late
cannot run after the upgrade.

1. Preconditions — record Q39 dispositions first (needs the 3.7.0 runtime).
2. Install preview — `command -v gentle-ai`; `gentle-ai sync --dry-run`.
3. `brew upgrade gentle-ai` — a one-way door.
4. `gentle-ai sync` — overwrites managed assets; may exit non-zero.
5. The Q36 change set, for NON-GIT surfaces only:
   `python3 scripts/changeset.py apply --set upgrade/v4 --journal-root backups/changesets [--allow-root ~/.config/opencode] [--allow-root ~/.claude] [--verify-cmd 'bash verify-workflow.sh'] [--dry-run]`
6. The one-time `rm -rf ~/.config/opencode/skills/workflow-sdd-secure`.
7. `bash verify-workflow.sh` — expect `SECURE_OPENCODE_RESTART_REQUIRED` with
   `RUNTIME_RESTART_REQUIRED=1` at `verify-workflow.sh:4274-4284`, and
   `RETIRED_WORKFLOW_SKILL_PRESENT` until the `rm` runs.
8. Restart all three services.
9. `bash verify-workflow.sh` again — must be CLEAN.
10. `bash verify-workflow.sh --behavioral` — skipped if `FAIL != 0`
    (`verify-workflow.sh:5008-5011`).
11. `gentle-ai review inspect-authority` + `gentle-ai review repair --preflight`.
12. Dispatch checks (`advisor-*`, v4 generic agents, `asi-review-*`).
13. Retention.

### Idempotent vs one-way doors

- One-way doors: the binary upgrade, the service restart, and `git revert`.
- Re-runnable: `verify-workflow.sh` and change-set apply.
- `changeset.py revert` is a one-way restore that reports drift.

### Exact command shapes

Use only the command shapes above. Do not invent flags.

### Failure modes and their catching checks

Each failure mode has a check that catches it; the runbook must route the
operator to that check rather than to a silent retry.

### What the runbook must NOT say

- Do not present the change set as applying Q30–Q33.
- Do not call one verifier run done.
- `--recover-config-only` skips package/plugin/paid probes and is not
  acceptance.
- Do not omit the `rm`.
- Do not apply before Q39 dispositions are recorded — the gate is
  unimplemented so the operator is the only enforcement.
- No `brew downgrade`.
- No hand-editing `~/.config/opencode`.
- No out-of-order journal revert — `scripts/changeset.py check_order` refuses.
- Do not claim the digest pin auto-updates.

## advisor-design-pre (2026-10-11)

### Recommended structure

1. Scope / readiness.
2. Before you change anything — plus a prominent "Already mid-upgrade? Go to
   Recovery" link.
3. Numbered upgrade steps, each with action → expected result → stop/recovery
   destination.
4. A small failure-state table, then complete recovery procedures.
5. Completion and evidence.
6. Operational decisions and open questions.
7. References.

Recovery is up front, failure links are inline, and full rollback comes after
the steps.

### The four sources are NOT copies and keep their own scopes

- `docs/TODO.md:897-910` → a Deliverable line pointing at the runbook as the
  sole authority for upgrade execution, activation, recovery and completion,
  while Q34 keeps tracking document readiness.
- `CLAUDE.md:87-89` → keep the general deployment policy and point at the
  runbook for the v4 upgrade.
- `docs/HANDOFF-2026-10-02.md:20-25` → mark it as the HISTORICAL Q03 deployment
  note ("do not execute this historical handoff as a runbook") and point at the
  runbook.
- `WORKFLOW.md:26` → PRESERVE the project-registration contract and add a
  separate sentence that v4 upgrade activation is a different operation covered
  by the runbook.

### Drift prevention: authority by fact type

- Runbook = execution order, service set, recovery selection, completion
  criteria, retention.
- `docs/PLAN.md` = constraints and rationale, with executable apply/revert
  instructions replaced by links.
- The Q34 TODO = deliverable/status/prerequisites.
- The Q36 spec = CLI/journal/exit codes.
- Q36/Q63 trackers = observed results.

Plus a lightweight same-change checklist for when a referenced contract
changes.

### Owner decisions (recorded ONCE)

Record the two owner decisions once as owner-decided-for-this-upgrade with
runtime validation pending: restart ALL THREE services
(sandbox-broker/secure-opencode/ai-proxy) and keep the LAST 10
`backups/workflow-recovery/` runs. Define what constitutes a "recovery run",
and never conflate verifier recovery backups with change-set journals.

### Four risks to reject

1. An old-runtime prerequisite placed too late — the Q39 inventory needs
   3.7.0.
2. Treating "dry-run passed" / "exit 0" as completion gates — the dry run does
   not execute `--verify-cmd`, and a post-run verifier failure does not change
   operation outcomes.
3. The pre-apply verifier can refuse writes while the verifier itself repairs
   config — specify which generation/mode runs before vs after application.
4. The final dispatch names `advisor-*`, but scripted advisor dispatch is
   unreliable (`CLAUDE.md:128-130`) and Q63 needs two separate post-upgrade
   investigations — name the owner/TUI route and never claim "verifier green
   therefore upgrade complete".
