# Waiting for Orca workers

When you have dispatched Orca workers (`orca orchestration worker-start`, `scripts/dispatch-worker.sh`) and
have no other independent work, never ask the user to tell you to check messages, and never poll.
Start the watcher in the background and end your turn; its exit re-invokes you:

    Bash(run_in_background=true): python3 <repo>/scripts/orca-watch.py --run <run_id>

(`<repo>` is `~/orca/workspaces/workflow_optimisation/multi-tier-orchestration-spec`.) It prints the
first new substantive message (heartbeats such as "alive" are ignored) and exits 0, or exits 2 after
~55 minutes with nothing new. On exit: read the output, act on it, then start the watcher again while
workers are still outstanding.

Do not use `orca orchestration check --wait` or `--unread` for this: they replay messages you have
already handled. A harness notice that "you have N new orchestration messages" is a prompt to read the
newest message by `sequence` in `orca orchestration inbox --full --json`, not to re-run `check`.
