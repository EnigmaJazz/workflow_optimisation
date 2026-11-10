# Q134 brief: trim ~/.claude/CLAUDE.md and keep the trim across gentle-ai sync

Queue item Q134 (docs/TODO.md on the coordinator branch). Class: global-tooling-change.
Risk: item 3 (gentle-ai-managed blocks others consume) and item 5 (delivery tooling).
Codex review before merge. You work in this worktree only; you cannot and must not write ~/.claude.
The coordinator applies the result on the host with scripts/changeset.py after review.

## Specs
- S1. A change set `changesets/claude-md-trim/changeset.json` (schema workflow-changeset/v1) with
  `block_replace` ops on `~/.claude/CLAUDE.md` for the `gentle-ai:orchestrator` and
  `gentle-ai:agent-routing` blocks. `expect_before` must equal, byte for byte,
  `upstream/orchestrator.md` and `upstream/agent-routing.md` (snapshots taken 2026-11-10 from the live
  file; `tests/test_claude_overlay.py` builds the fixture from those two files, so no whole-file copy is kept).
  Note: `gentle-ai:remote-authorization` is nested inside agent-routing; keep its markers and its
  text in the replacement verbatim.
- S2. The replacement keeps in each block only a short pointer (a few lines) plus any rule that
  must stay always-on; the moved text goes to a user skill created by `file_create`
  (`~/.claude/skills/gentle-ai-orchestration/SKILL.md`, with valid frontmatter whose description
  triggers on implementation, delegation, ODD, native review / RDD, and task sizing). Moved text is
  copied verbatim, not reworded. Target: always-loaded CLAUDE.md under about 30 KB.
- S3. A drift check `scripts/claude-overlay-check.py`: for every `changesets/claude-*` set, run
  `changeset.py status`; report per set `applied`, `reapplicable` (current bytes equal the
  set's expect_before, i.e. gentle-ai sync restored upstream) or `conflict` (upstream text changed).
  With `--reapply` it applies only `reapplicable` sets through `changeset.py apply`
  (compare-and-swap, journaled) and never touches a conflict. Exit 0 all applied, 1 conflict, 2 re-applied.
- S4. Wire S3 into the verifier as a report-only check (a new `verify/NN-*.sh` module or an existing
  one), then run `python3 scripts/verifier_manifest.py update`. Document the post-sync command and
  `gentle-ai sync --agents opencode` for routine syncs in WORKFLOW.md or docs/upgrades.
- S5. Tests (python unittest, throwaway HOME via tempfile, never the real HOME): apply on the
  synthetic fixture; re-sync simulation (restore upstream bytes) -> reapplicable -> --reapply restores the
  trim; changed upstream -> conflict and file bytes unchanged (positive control that conflict is
  detectable); revert restores the snapshot byte for byte.

## Verification
- python3 -m unittest discover -s tests
- python3 scripts/verifier_manifest.py check
- python3 scripts/changeset.py apply --set changesets/claude-md-trim --journal-root "$(mktemp -d)" --allow-root <tmp HOME> --dry-run against a temp HOME holding the upstream blocks

Commit in work units under about 400 authored lines (the verbatim moved skill text is a copy and
may exceed it; say so), Conventional Commits with suffix
`— ROUTED: global-tooling-change@tier2-queue (2026-11-10)`. Do not push. Report worker_done with
commits, checks and the S# covered.

## Amendment A1 (Tier 2, 2026-11-10) to S3
- A set whose newest journal entry is a revert is never re-applied: an owner revert is deliberate
  and must not be undone by --reapply (for example `claude-fable-advisor-trial`, reverted on
  2026-11-17, would otherwise put Fable back as advisor). Only sets marked persistent re-apply;
  add an explicit field or list for that, and exclude trial sets.
- Judge remove-plus-create pairs by the final state: on the host today
  `changeset.py status --set changesets/claude-model-routing` reports op 0 `file_remove` as
  `conflict` although the set is fully applied (ops 1-6 `already_applied`). A set whose final
  state is in place counts as applied.
- Superseded sets (`claude-advisor-triggers`, superseded by `claude-model-routing`) are retired
  or skipped, so the check does not exit 1 on every run.
- Tests cover all three cases, each with a positive control.
