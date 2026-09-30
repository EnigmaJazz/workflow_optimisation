# TODO

Ordered open work, one row per work unit. Maintained by the orchestrator alongside the in-agent
todo list and the per-feature tracker (`odd/tasks/<feature>.md`). The feature tracker holds the
detail for one body of work; this file holds the cross-cutting queue and the order.

**Contract:** updating this file gates STARTING a new work unit. A unit paused awaiting user
input is a valid recorded state and does not block. Unfinished work must be finished or
explicitly parked before another unit starts.

**BLOCKER (active):** the sandbox worker lifecycle is failing repeatedly — lost microVMs,
exported results with zero changed paths, `no worker recorded` on finish. Source changes and
the queued fixes are blocked until it recovers or an explicit fallback path is agreed.

## 1. IN PROGRESS — review follow-up on the plugin load check
Apply the three review fixes to `check_plugin_loads()` in `verify-workflow.sh`:
- fail when zero plugin files were checked (the vacuous-pass case);
- also fail on a module-resolution error (bun reports `Cannot find package`) and on a timeout
  (exit 124), keeping other import-time errors informational;
- require a usable exported factory without invoking it.
Record all eleven advisory findings from `review-10d26170c9d40efc` in the feature tracker, and
re-pin `verify-workflow.sh`'s sha256 in the health plugin.

## 2. Commit, assess, review the follow-up
Commit the fixes, assess RDD, and run the native review when the slice is due.

## 3. Deploy what is already committed (host action)
Verifier mirror, then service restart. Nothing from the guard work is live: the routing gate has
never run, so no keys have minted and no warnings have fired. Order matters — mirror first, then
restart.

## 4. Advisor layer
Register five read-only advisor agents (`advisor-design`, `advisor-integration`,
`advisor-testing`, `advisor-security`, `advisor-maintainability`) in
`global-config/opencode.json`, add them to the orchestrator's `permission.task`, and add the
pre-code advice policy to `WORKFLOW.md`.

## 5. Workflow policy
Define the policy across task classes and the ODD/SDD/advisor layers, including the
complexity-and-impact axis, the per-project impact-surface declaration delivered by the host,
and the rule that a heavier route always governs.

## 6. Tracking contract in the recipe
Add to `WORKFLOW.md`: the orchestrator maintains this file, the plan, and an in-agent list;
updating them gates starting a NEW unit; a unit paused awaiting user input does not block.

## 7. Recipe drift and gaps
- `WORKFLOW.md` names Systematic v3.18.4 while v3.21.0 is installed.
- The documentation class has no mandated review option — `document-review` is the candidate.
- Global tooling has no adapter skill and no stage coverage, so the guard cannot see it.
- `ce:review`'s helper pipeline needs a sandbox worker, so mandating it enforces nothing while
  the sandbox is failing.

## 8. Cross-project items
Confirm the agent-sandbox-integration work is delivered: the allowlisted append operation, the
ledger move out of git, the project-scoped signal channel, and the install-vs-commit gap.
## 2026-09-30 — sandbox blocker confirmed after reboot; fallback taken
The sandbox worker lifecycle fails at worker creation (`ensureWorker` timeout, then
`no worker recorded — fail closed`) even after a full reboot, so it is the broker/worker
lifecycle rather than a transient. Item 1 (the review follow-up) is therefore handed over for
host-side application: the exact replacement for `check_plugin_loads()`, the digest re-pin
procedure, and the tracker section. Item 1 stays IN PROGRESS and unverified until that lands
and is checked. No other unit starts while it is open.
## 2026-09-30 — activation workaround did not fix mutation; blocker narrowed
Retry with the instructed sequencing (`sandbox_bash pwd` to activate before any edit) behaved
differently but still failed:

- `sandbox_bash pwd` SUCCEEDED — the worker activated and file reads worked.
- The mutation itself failed: the patch/edit did not apply, and subsequent read and edit calls
  timed out.
- Recovery check: `git diff --stat` and `git diff --name-only` both empty; the repository is
  untouched and no sandbox result was produced.
- The verifier digest in the repo is still `ff38b6ba…`, which matches the healthy script, so the
  pin is consistent — it simply was never changed.

Failure is therefore narrowed to the sandbox WRITE path (worker mutation and post-write
operations), not worker activation. The activation workaround is necessary but not sufficient.
Item 1 remains IN PROGRESS and unverified; the prepared hand-application (replacement
`check_plugin_loads()`, digest re-pin, tracker section) stands as the fallback.
## 9. Emergency fix route (logged now; implement after the open items)
Design recorded in the plan. A user-declared priority lane: it preempts the session, parks the
current unit with its state recorded, and resumes it after. Minimum ceremony, bounded diff, the
fix is logged as part of the work, and its review/cleanup debts become named follow-ups rather
than silent omissions. Higher priority than items 4-8, but it does not start while item 1 is open.
## 2026-09-30 — root cause located: sandbox_edit silently no-ops
A worker instructed to make its first mutation with `sandbox_edit` and stop on failure reported:

- `sandbox_edit` **returned success**, but the readback showed the target unchanged (digest identical).
- Follow-up `sandbox_apply_patch` attempts were rejected.
- `git --no-pager diff` empty; no changed files; `sandbox_finish` not run.

This is a silent no-op, not an error: the tool fails OPEN, reporting success and discarding the
write. It retro-explains the two earlier "finished result with zero changed paths although edits
existed mid-run" cases — those edits never reached disk, so the workers' belief that they had
edited was the only thing that existed.

Implication for checks: because the success signal is false, "continue only if the edit succeeded"
cannot protect a worker. A readback after every mutation is the only reliable verification, and it
is what caught this. Worth making an explicit worker rule.

Item 1 remains IN PROGRESS and unverified. The prepared hand-application stays the fallback.
## 2026-09-30 — item 1 fixed and verified; commit needs the host
The review follow-up landed and is verified by execution:

- `verify-workflow.sh`: `checked` counter with the zero-files failure; module-resolution patterns
  (`Cannot find package` etc.) and timeout exit 124 now FAIL; dynamic import inspects exports and
  fails when none are usable. Digest re-pinned to `1653d28d…`.
- `odd/tasks/routing-guard-keys.md`: the review section, all eleven findings, and the closing
  status paragraph.

Checks, all passing in the sandbox: `bash -n` clean; empty directory fails with the no-plugin-files
message; a clean plugin copy reports `OK plugin load`; a broken-import copy fails with
`Cannot find package` rather than INFO.

Method that worked, and should become the worker contract: read targets with HOST tools before
activating, hand-compose context-bearing patches, apply with `sandbox_apply_patch` only, never use
`sandbox_edit` or `sandbox_read` (both read the whole file body and fail on large files). The
failure is the whole-body read path, NOT the file's size — the large script patched cleanly.

**Blocked on host:** `host_git_commit` refuses the install — `no applied B->C result` — the known
install-vs-commit gap. Commit commands handed over. Item 1 moves to COMMITTED-pending, still
uncommitted and therefore still open.
## 2026-09-30 — post-broker-fix probes: read path still broken, general not size-bound
`sandbox_read` was probed after the broker fix, on a freshly activated worker:

- `verify-workflow.sh` (4,770 lines) → `broker request 'readFile' timed out`, no content.
- `global-config/plugins/workflow-health-check.ts` (~100 lines, control) → the SAME timeout.

Conclusion: the whole-file read path is broken generally, NOT by file size — a small file fails
identically. The broker fix did not restore it.

Two distinct faults, now separated:
- `sandbox_read`: the `readFile` RPC times out regardless of size.
- `sandbox_edit`: needs the entire file body emitted in one call, which a worker cannot do for
  large files; that is an output limit, not a read limit.

Unaffected: the working method is host reads BEFORE activation, then hand-composed context-bearing
patches via `sandbox_apply_patch`. It uses neither broken tool and is what landed and verified
item 1. Unprobed: whether `sandbox_edit` works on a small file after the fix — that would separate
a pure emit limit from an additional fault.
## 2026-09-30 — sandbox tooling fault fully characterised
Retests after the broker fix, both on freshly activated workers:

- `sandbox_edit` on a SMALL file (`workflow-health-check.ts`, ~100 lines): **SUCCEEDED and the change
  LANDED** — `git diff` showed the probe line. The silent no-op did NOT reproduce.
- `sandbox_read` on the same small file and on `verify-workflow.sh`: **still times out**
  (`broker request 'readFile' timed out`) regardless of size.

Settled conclusion — two independent faults, now separated with evidence:

| Tool | Status | Rule |
|---|---|---|
| `sandbox_read` | broken at any size | never use; host-read before activation |
| `sandbox_edit` | works; needs the whole body emitted | only for files a worker can emit whole; not `verify-workflow.sh` (4,770 lines) |
| `sandbox_apply_patch` | works, proven on the 4,770-line script | the method for large files, from pre-activation host reads |
| `sandbox_bash` | works | activation, and `git diff` for verification |

The earlier silent no-op on `verify-workflow.sh` is explained by the emit limit, not a broker fault.

## 10. Worker contract — sandbox tool rules (to add to the recipe)
Record for workers: read with HOST tools BEFORE activation; use `sandbox_apply_patch` with
context-bearing hunks for any large file; verify with `sandbox_bash git diff`, never `sandbox_read`;
treat a tool's success return as unverified until a readback confirms it.
## 11. Split `verify-workflow.sh` into smaller files
`verify-workflow.sh` is 4,770 lines: too large to whole-body edit, timing out on reads, and the
reason every repair cycle today was expensive. Split it per the design recorded in `docs/PLAN.md`
— prefer a thin runner invoking per-area check scripts so each check is independently runnable and
testable, preserving check ordering, the `fail` aggregation, TTY/`NO_COLOR` colour behaviour, the
digest pinning contract, and the `WORKFLOW_VERIFY_*` switches. Related principle: keep files small
as a coding standard in its own right; the patch route is only for the unsplittable.

## Review state
Commit `71a2eb3` carries the review follow-up and item 1 is closed. The native review is now DUE
(`high`) for the accumulated slice, but `review assess` refuses until the untracked-file inventory
is declared explicitly — the digest moved from `0fc9c89f…` to `334c3048…`. Resolve by reading the
canonical inventory and re-running the assessment with the matching declaration. Note also that
`CLAIM-RETRACTIONS.md` and `ROUTER-LOG.md` hold uncommitted cross-project writes; the ledgers are
still shared git-tracked files, which is the divergence surface already logged for the
agent-sandbox-integration project.
