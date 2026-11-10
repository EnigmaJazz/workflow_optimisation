# Claude `CLAUDE.md` trim runbook

Gentle AI owns the `gentle-ai:orchestrator` and `gentle-ai:agent-routing` blocks in
`~/.claude/CLAUDE.md` and restores their upstream text on every sync. The
`changesets/claude-md-trim` set shrinks both blocks to a short pointer and always-on rules,
while preserving the moved text verbatim in the user skill
`~/.claude/skills/gentle-ai-orchestration/SKILL.md`.

## Prerequisite

Create the skill directory first; the change-set tool's `file_create` operation never creates
parent directories:

```sh
mkdir -p ~/.claude/skills/gentle-ai-orchestration
```

## Apply and keep after sync

Preview the change set with `--dry-run` before applying:

```sh
python3 scripts/changeset.py apply --set changesets/claude-md-trim --journal-root backups/changesets --dry-run
python3 scripts/changeset.py apply --set changesets/claude-md-trim --journal-root backups/changesets
```

For routine OpenCode syncs, run `gentle-ai sync --agents opencode`, then restore the trim:

```sh
gentle-ai sync --agents opencode
python3 scripts/claude-overlay-check.py --reapply
```

The checker reports each Claude changeset as `applied` (all targets are already present),
`reapplicable` (the current bytes match the declared upstream text and are safe to apply),
`conflict` (the upstream block changed), `reverted` (the newest journal records an owner revert),
or `superseded` (a later set replaced it). A reverted set is final and is never re-applied. Only
sets named in the checker's `PERSISTENT` list are re-applied; `claude-md-trim` is the only one
today. Trial and one-shot sets must stay out of that list. State summary:

| State | Meaning |
| --- | --- |
| `applied` | All target bytes are present. |
| `reapplicable` | Safe to apply; automatic re-application is limited to persistent sets. |
| `conflict` | Before-state differs; left untouched. |
| `reverted` | Newest journal is an owner revert; settled and never re-applied. |
| `superseded` | Replaced by a later set; skipped. |

Superseded sets are skipped:
`claude-advisor-triggers` is superseded by `claude-model-routing`, which lives on the coordinator
branch and may not be present in this worktree. Remove-plus-create operations are judged by their
final state, not the intermediate removal result.

Exit code `0` means no conflict and no persistent set needs reapplication, `1` means at least one
conflict, and `2` means a persistent set is reapplicable or was just re-applied. Without
`--reapply`, the checker is report-only. It never modifies a conflicting or non-persistent set.

The expected trimmed `~/.claude/CLAUDE.md` is under 30 KB. The companion skill holds the full
orchestrator and routing text; do not remove it when applying the set.

## Revert

Use the newest applicable apply journal at
`backups/changesets/claude-md-trim/<run>/journal.jsonl`:

```sh
python3 scripts/changeset.py revert --journal backups/changesets/claude-md-trim/<run>/journal.jsonl --journal-root backups/changesets
```

The journaled revert restores the snapshot bytes and retires the created skill file. The tool
reports drift rather than overwriting any file changed after application.
