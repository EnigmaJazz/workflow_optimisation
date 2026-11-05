# B0 spike: native review on a staged ref (T3; S71, S79 / OPEN-1)

Run 2026-11-05 with gentle-ai 4.3.1 (stable, contract `gentle-ai.review-integration/v2`, protocol 2.6, projections `staged` and `workspace`).
`gentle-ai review mode status`: `on (decided by global)`, clone-local unset. Only `assess`, `status`, `capabilities` and `mode status` were run; no `start`, `capture` or `acknowledge`.

Scratch (not deleted), all under `S=/tmp/claude-1000/-home-james-orca-workspaces-workflow-optimisation-multi-tier-orchestration-spec/090c9d73-321e-458c-abcc-d34643f48e88/scratchpad/b0.THlDQB`:

- `$S/src`: repo with `main` at BASE `bd6f92db` and a commit STAGE `96cd6e5f` on no branch, referenced only by `refs/opencode-sandbox/chain/test/base` and `.../stage/1`.
- `$S/clone`: `git clone --shared $S/src`, detached at STAGE.
- `$S/wt`: `git worktree add --detach $S/wt STAGE` from `$S/src`.

Command form (per case and agent): `gentle-ai review assess --cwd <dir> --agent <opencode|claude-code> --base-ref BASE --committed-only --json`, and `gentle-ai review status --cwd <dir> --contract gentle-ai.review-integration/v2 --agent <same> --next-transition --base-ref BASE --committed-only`.

## Results (identical for `--agent opencode` and `--agent claude-code`)

| Case | assess | status `next_transition` | Verdict |
|---|---|---|---|
| (a) ref not checked out (`$S/src`, HEAD = `main` = BASE) | exit 1, `risk: high`, reason `unassessable` ("no pending changes"), 0 paths | `stop: empty_base_diff_bootstrap_required` (exit 0). Adding `--lenses` is rejected with `invalid_request`, exit 1 | Not feasible. Assessment is base-to-HEAD only; there is no flag to name the candidate commit. The `high` is a false signal. |
| (b) detached checkout of STAGE in a shared clone (`$S/clone`) | exit 0, `risk: medium`, `executable_change`, `review_due: false` (`under_budget`), 1 path, 1 line | `execute review.start`, reason `fresh_target_ready`; command carries `--cwd=$S/clone --base-ref=<BASE's tree> --committed-only=true --projection=workspace --agent=<agent>` | Feasible. |
| (c) linked worktree of STAGE (`$S/wt`) | same as (b) | same as (b), `--cwd=$S/wt` | Feasible at the CLI level, but see the authority-location caveat. |

- The `target_identity` (`sha256:881eb2d4...`) was the same in (b) and (c): it is content-derived, not path-derived.
- The `--base-ref=5e8b0426...` in the returned `start` command is the BASE tree, not the commit; use the returned command verbatim.
- `review_due: false / under_budget` is a size result for a 1-line stage, not a feasibility failure. A real stage over the budget should return `high_risk` or `review_due: true`.
- The two read-only commands wrote nothing into `$S/clone/.git` or `$S/src/.git`.
- Fetching the staged ref into the clone also works: `git fetch origin refs/opencode-sandbox/chain/test/stage/1:refs/opencode-sandbox/chain/test/stage/1` exited 0, and the object is already reachable through `objects/info/alternates`.

## Sandbox reachability (`nono why --profile opencode-v2-secure`, read-only)

| Path | read | write |
|---|---|---|
| `$S/clone` (under `/tmp`, granted path `/tmp`) | ALLOWED | ALLOWED (scratch location only; `/tmp` is not a candidate state directory) |
| `/home/james/.local/share/opencode-sandbox/x` (hypothetical state dir) | DENIED (`path_not_granted`; suggested `--read /home/james/.local/share/opencode-sandbox`) | not tested |
| `/home/james/.local/share/opencode` | DENIED | DENIED |
| `/home/james/agent-sandbox-integration` | ALLOWED | DENIED (`insufficient_access`) |
| this worktree (`.../multi-tier-orchestration-spec`) | DENIED | DENIED |

So a clone placed in a state directory is unreachable by the sandbox unless the profile gains a grant for it.

## Answers

- **S71 / S79: "native review is feasible on a staged ref": yes, only if the stage commit is checked out as HEAD of a repository that can resolve it and `--base-ref` is the stage's baseline.** It is not feasible on the bare ref (case a). It stays unverified past the preflight because `start` and `capture` were off limits.
- This is evidence for the OPEN-1 decision, not the decision. Review-before-apply is feasible at the preflight level, so the after-apply fallback in `plan.md` need not be chosen on feasibility grounds. The owner decides.

## Recommended materialisation

Per stage, in the broker (host side, outside the sandbox): a shared clone (`git clone --shared <project> <state-dir>/review/<chain>-<n>`), `git checkout --detach <stage-sha>`, then run `assess` / `status` with `--base-ref <baseline-sha> --committed-only`. Reasons:

- Review authority is stored in the Git common directory (the `status --help` text says "shared Git common directory"). A shared clone keeps that in the clone's own `.git`, so no authority lands in the host repo. A linked worktree shares the host's `.git`; where `start` would write was not observed.
- The clone is disposable, and the objects come from the host through alternates, with no worktree in the project directory.
- The lens reviewers run in the OpenCode sandbox and cannot read paths outside its grants. The clone's own location and the host repo (via alternates) both need read grants.

## Not verified

- `review start`, `capture` and `acknowledge` on a shared clone: where authority is written, whether lens reviewers can read the immutable trees from a clone, and whether acknowledgement burns cleanly. A second spike with owner consent is needed (an owner-run `start` on a throwaway clone).
- Whether a shared clone's authority is visible from, or conflicts with, the host repo's lineage listing.
- A real state directory path: none was chosen, so the reachability table covers hypothetical paths only. `/tmp` allows read+write here only because of this profile's `/tmp` grant.
- Behaviour on a commit that exceeds the review budget (`review_due: true`), and with `--agent opencode` inside the sandbox rather than from Claude Code's shell.
- The linked-worktree case under the known failure in memory ("a worktree in a sandbox-denied directory fails every OpenCode review lens").
