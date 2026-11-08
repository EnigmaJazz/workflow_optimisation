# Orca worker session lifecycle

Do not let worker sessions accumulate. After every wake from the orchestration watcher, and before
ending a turn, run `python3 <repo>/scripts/release-settled-workers.py --run <run_id>`. It releases only
settled, run-owned workers (Codex, probes, failed dispatches) and skips retained, user-owned and
still-active ones.

- Codex is one-shot: read its verdict, then release. It reviews unapplied diffs and never runs tests.
- OpenCode 2 is reused, never released: `scripts/dispatch-worker.sh` retains it. Send follow-up work to
  the same session with `orca orchestration worker-start --terminal <handle> --spec ...` so Magic Context
  keeps its project understanding.

(`<repo>` is `~/orca/workspaces/workflow_optimisation/multi-tier-orchestration-spec`.)
