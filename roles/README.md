# Role definitions

One versioned file per tier (D26). Each starts with `version: <n>`; any change to a role's wording
increments it. Wording marked `pending owner review` is not in force until the owner has reviewed it
(spec section 14).

| File | Tier | Agent |
|---|---|---|
| `tier-1.md` | 1 | Claude Code, one session, cross-project |
| `tier-2.md` | 2 | Claude Code, one session per repository |
| `tier-2s.md` | 2s | Claude Code tech support |
| `tier-4.md` | 4 | Codex, specification and result review |
| `tier-5.md` | 5 | OpenCode 2, phase implementation end to end |

## Reporting back

A session launched with a plain `orca agent launch` has no channel back to its launcher. To get a
result without polling:

- Start the worker with `orca orchestration worker-start` inside a Run (`orca orchestration
  run-create` first; without a bound Run it fails with `consumer_fenced`), so the dispatch has a task
  id and a dispatch id.
- A sandboxed OpenCode agent has no shell. It finishes with `host_orca_report` (`type: worker_done`,
  with `subject`, `body` and `outcome`), passing its task and dispatch ids and its OWN terminal handle
  (the dispatch assignee, not the coordinator's; the broker refuses any other handle). The broker
  checks the dispatch is live first, and the report goes to the coordinator the dispatch names. Only
  `gentle-orchestrator` has this tool allowed; it is denied globally.
- A session with a shell (Codex) uses `orca orchestration send --type worker_done` instead.
- The read-only OpenCode orchestrator and its workers can write only inside the project root, so a
  report file outside the repository fails. Use `host_orca_report`, or the final message.


### Persistent sessions: one dispatch per phase, and blocked is not failed

A dispatch is one unit of work. `worker_done` (either outcome) or a failed report spends it; a
spent dispatch cannot carry another report, and typing into the terminal (`orca terminal send`)
or `orca orchestration send` creates none. The PM-only review showed it: the session reported
"blocked" as `worker_done` / `failed`, the dispatch closed, and the owner's unblock had no channel back.

- Hand a retained OpenCode 2 session each new phase as a new dispatch:
  `orca orchestration worker-start --worktree path:<its worktree> --terminal <handle> --run <run> --task-title ... --spec ...`
  (the `--worktree` must be the terminal's own; otherwise `terminal_worktree_mismatch`).
- A worker blocked on something the coordinator or owner can clear: `host_orca_report` type `ask` was
  observed to time out on the broker (the verb blocks for a reply the terminal cannot receive), after which
  the session sent `worker_done` and the dispatch was spent. Until Q104a settles a working blocked channel,
  treat every blocked report as ending its dispatch and answer with a NEW dispatch to the same terminal.
- `orca terminal send --enter` is a last resort to wake a session; it gives the session no dispatch.

## Waiting for workers

A manager that has dispatched workers waits with `scripts/orca-watch.py` run in the background (it
exits on the first new substantive message, ignoring heartbeats), never by asking the owner to say
"check". The same instruction is installed globally as `~/.claude/rules/orchestration-watch.md`
(change-sets `changesets/claude-orchestration-watch` and `claude-orchestration-sessions`). Codex dispatches made through
`scripts/dispatch-worker.sh` get `roles/codex-commands.md` prepended to the spec.

## Session lifecycle

Sessions must not accumulate. Codex (specification and review) is one-shot: once its verdict is
read, release it. OpenCode 2 is reused: `scripts/dispatch-worker.sh` retains each OpenCode 2
dispatch, and later work goes to the same session with `orca orchestration worker-start --terminal
<handle> --spec ...`, so Magic Context keeps its project understanding. After each wake from
`scripts/orca-watch.py`, run `python3 scripts/release-settled-workers.py --run <run>`; it releases
only settled workers the run owns and skips retained, user-owned and still-active ones. Codex does
not run tests: it reviews the unapplied diff, and the implementer reports its own results.

Giving work to an existing session: `orca orchestration send` only writes to the inbox and does not
start a turn in an idle interactive session. Use `worker-start --terminal <handle> --spec ...` (via
`scripts/dispatch-worker.sh <worktree> --terminal <handle> ...`). Before reporting "waiting", confirm a
session is actually working: `orca terminal read --terminal <handle>` shows a Thinking/working state, or
`worker-list` shows an active dispatch.
