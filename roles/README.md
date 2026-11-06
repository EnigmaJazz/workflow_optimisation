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

