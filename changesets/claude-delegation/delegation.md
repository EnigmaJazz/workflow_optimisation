# Delegating from Claude Code (Tier 2)

Source of truth: `roles/tier-2.md` "Delegating" in the multi-tier orchestration repository; re-read it before delegating.

1. **Find before you launch.** Run `orca orchestration worker-list --run <run>` and use the repository's
   retained OpenCode 2 master (one per repository, D36 worktrees under `~/ai-workspace/worktrees/<project>/`).
   Re-prompt it with `scripts/dispatch-worker.sh <its worktree> --terminal <handle> --run <run> --spec ...`.
   Launch a master with `orca agent launch --agent opencode2` only when the repository has none, then retain it.
   Never start a fresh session per work item; the master delegates to PMs, in parallel and in the background.
2. **Bind every dispatch to the Run** (`--run`), so `worker_done` and questions reach the watcher. A session
   started without a Run cannot report; read its terminal (`orca terminal read`) after launch and say so.
3. **Brief what, not how.** Outcome, repository and worktree, the spec `S#` or queue item, constraints and
   the Risk class. The role contract (`roles/tier-5.md`, `roles/tier-4.md`) carries the procedure.
4. **Review by risk.** A change that touches a security guard, a permission, a protected path or a contract
   others consume gets a Tier 4 (Codex) review against the spec, with a SECURITY section, before it is merged.
   Dispatch it Run-bound at the worktree holding the unapplied diff; Codex reviews and does not run tests.
5. **Questions come to you.** Answer a Tier 5 or Tier 4 question from the spec and the queue; take the
   advisor when it is not clear (advice is evidence, not approval); hold for the owner only for a product,
   consent or protected-path decision. Reply on the channel it used; if it is blocked in a terminal, send the
   answer there (`orca terminal send --text`, then `--enter` as a separate call).
6. **Wait with the watcher** (`scripts/orca-watch.py`, background), then run
   `scripts/release-settled-workers.py` and retain the OpenCode 2 masters.
7. **Evidence before state.** Before saying where a feature stands, read git in the owning repository;
   trackers are claims to check. Record state in Engram at each unit boundary (D23).
8. **Close the loop.** Read the terminal state of every session you started before reporting; tell the owner
   which commits only the owner may make (protected paths) with the exact commands.
