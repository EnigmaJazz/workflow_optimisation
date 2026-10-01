# TODO history

Append-only history of the work queue in `docs/TODO.md`; newest last. Entries below were moved verbatim from the queue on 2026-10-01 (unit `advice-mandate-and-queue`, T1). Their statuses are as written at the time and are superseded by the queue; where an item header and a later dated entry disagree, the queue states the resolved status.

<!-- Moved verbatim from docs/TODO.md starting at the "BLOCKER (active)" paragraph. -->

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
## 12. Guard review findings — fix unit
Native review `review-84383b2e59dc8844` approved and acknowledged (authority burned). Seven
advisory findings, recorded in the feature tracker. Fix priority:

- **R2-001 (real defect):** `allowsSpecialists` is inverted — the dispatch check warns for the
  specialists listed in the stage and lets unlisted ones bypass it. It names the set permitted to
  proceed, so the predicate is backwards.
- **R3-patch-stage-marker-gap:** patch path extraction recognises only `odd/tasks/*.md`, so
  `workflow-systematic` artifacts written by patch never clear their stage.
- **R3-child-marker-merge-excl:** `COPYFILE_EXCL` prevents a re-dispatched child from updating an
  existing parent marker, so parent stage state can lag behind child progress.
- **R3-marker-write-race / R4-001:** marker writes are unawaited, so an immediately following stage
  check can see them missing and warn falsely.
- **R3-specialist-warning-dedup:** specialist warnings bypass the warningKey deduplication.
- **R3-stage-logic-untested:** no automated assertions exist for the stage table or its gates — the
  recurring finding across two reviews. Assertions for the stage logic are the durable fix.

## Deploy note
The routing guard is now LIVE and enforcing (warn-only): skill markers are being minted and the gate
has fired on real sessions, including an expired-key `task` dispatch and the ODD bootstrap stage
check. Any fix unit above needs the verifier mirror and a restart to take effect.
## PRIORITY CHANGE — advisor layer moves ahead of the guard fixes
The advisor layer (formerly item 4) is now the priority, ahead of item 12.

Rationale: two review cycles in one day both found the same class of defect — logic shipped without
any pre-code examination. `R2-001` (the inverted `allowsSpecialists` predicate) would plausibly have
been caught by a design or integration advisor reading the plan before implementation, at a fraction
of the cost of a review cycle. Pre-code advice is the earlier, cheaper gate; the native review is
the last one.

Revised order: advisor layer → guard fixes (item 12, `R2-001` first) → the workflow policy → the
remaining items. The deploy note stands: any source fix needs the verifier mirror and a restart.
## Advisor registration — verifier findings and the outstanding fix
The verifier rejected the advisor registration with four findings (all five advisors each for the
first three):

1. `SUBAGENT_SEARCH_PROMPT_CONTRACT_MISSING` — each advisor's prompt lacks the required
   `SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.` line.
2. `GITHUB_RO_AGENT_TOOLS_SCOPE_MISMATCH` — `github_ro_*` was granted but is not in the reviewed
   profile for these agents. Remove it from both `tools` and `permission`; they only need the repo.
3. `MAGIC_CONTEXT_MEMORY_POLICY_UNCLASSIFIED_AGENT` — the verifier's own classification list does
   not know the five advisors. Add them to the DENIED set (no project-memory writes), matching the
   existing review lenses, then re-pin the `verify-workflow.sh` digest.
4. `FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: opencode-go/mimo-v2.6-flash` — add an exact fallback
   policy for that model in `rate-limit-fallback.json`, modelled on the sibling DeepSeek Go entry,
   with no GLM anywhere in the initial chain.

Method note: hand-written patches are rejected on this file, and the splice-script attempt failed
while isolating the long one-line prompt strings. The reliable shape is: parse the JSON, mutate the
specific values, then TEXTUALLY replace only those value strings in the file so the diff stays
minimal — never rewrite the whole file, which would reformat all 1,969 lines. Delete any scratch
script before finishing; an exported result containing only the script must never be applied.

After the fix: mirror, then restart — `SECURE_OPENCODE_RESTART_REQUIRED` is expected until then.
Then verify by dispatching each advisor on a bounded task: confirm registration, reads succeed,
mutations denied, and the assigned models are observed.
## 2026-10-01 — sandbox_read confirmed fixed
Retested after a broker fix, on a freshly activated worker:

- `docs/ADVISOR-HANDOFF.md` (47 lines) → SUCCEEDED, full content, no truncation, reached the final line.
- `verify-workflow.sh` (~4,800 lines) → the call SUCCEEDED with no broker error; the RESPONSE was
  truncated by output size, and the tool reported saving the full output elsewhere.

The earlier fault — `broker request 'readFile' timed out` at every size, including a ~100-line
control — is gone. What remains for very large files is the harness limit on one tool response,
not a broken read path.

Revised sandbox tool rules, replacing the blanket "never use sandbox_read": `sandbox_read` is now
the normal read inside an active worker for small and moderate files; for very large files prefer
a host read before activation, or the saved-output artifact, or a targeted `aft_zoom`/host read
rather than a whole-file read. `sandbox_edit` still requires the whole body to be emitted, so large
files still need patches — but that is an OUTPUT limit in the caller, not a tool fault.

Item 10 (worker sandbox rules) should be updated with this revision when it is implemented.
## 2026-10-01 — CORRECTION: sandbox_edit is targeted, not whole-body; two claims retracted
Verified against the installed plugin source (`sandbox-tools.ts`) and empirically:

- Its arguments are `oldString` / `newString` / optional `replaceAll`. The tool description reads
  "replacing only the specified text. oldString must occur exactly once unless replaceAll is true.
  Refuses an empty oldString, no match, multiple matches without replaceAll." There is no
  whole-body requirement.
- A targeted one-character edit on `verify-workflow.sh` (~235 KB, ~4,800 lines) SUCCEEDED:
  `1 file changed, 1 insertion(+), 1 deletion(-)`.

**Retracted claims:**
1. "`sandbox_edit` cannot edit this file" — wrong; targeted edits work at this size.
2. "The original silent no-op was caused by an incomplete body" — unsupported. The tool refuses on
   no-match or multi-match, so an incomplete body cannot yield a silent write. **The original
   silent no-op remains UNEXPLAINED and is an open question, not a cause.** Both belong in
   `CLAIM-RETRACTIONS.md` as mechanisms claimed without reading the tool's code.

**New real finding:** `sandbox_edit` does not preserve the file mode — `verify-workflow.sh` went
from `100755` to `100644` during the probe. `chmod` inside the sandbox returned
"Operation not permitted", and `sandbox_discard` refused with "cannot discard result from state
SANDBOX_ACTIVE". For an executable script this is material, since the verifier runs it. The host
file was untouched because nothing was applied. This belongs in the handoff for the broker project.

**Revised item 10 rule:**
- `sandbox_read` is fine to use;
- `sandbox_edit` for targeted changes at any file size up to the 512 KB cap;
- `sandbox_write` only for files the caller can produce whole;
- patches when changes span many separate places.

Item 11 (splitting `verify-workflow.sh`) remains worthwhile for readability and testability, but is
no longer forced by the tooling. The 512 KB silent-truncation cap and the ~219 KB write-back limit
were both fixed; today's successful large read confirms the reply now arrives intact.
## 2026-10-01 — mode-preservation defect fixed and verified
Re-ran the probe after a fix landed:

- `verify-workflow.sh` mode before: `-rwxr-xr-x`; after: `-rwxr-xr-x` — unchanged.
- `git diff` contains NO `old mode` / `new mode` lines (previously it showed 100755 → 100644).
- The diff hunk is exactly the intended one-character change.

So `sandbox_edit` now performs a targeted, mode-preserving edit. Combined with the earlier
`sandbox_read` fix, all three sandbox faults from this stretch are closed and verified:

1. `sandbox_read` — no longer times out at any size.
2. `sandbox_edit` — targeted (`oldString`/`newString`), works to the 512 KB cap.
3. Mode preservation — executable bits now survive an edit.

The mode defect can be dropped from the handoff's request list; it was reported and has been
resolved. Still open and unexplained: the ORIGINAL silent no-op on a whole-file write, which no
longer has a candidate cause and should be recorded as an open question in `CLAIM-RETRACTIONS.md`
rather than re-explained.
## 2026-10-01 — Advisor dispatch verification PASSED; new guard defects found
All five advisors registered and dispatched successfully on bounded tasks. Each read real files and
cited line numbers. None fabricated evidence: all five reported that `sandbox_finish` is not
registered on their surface rather than quoting a refusal that could not exist. Tool surface
confirmed — the four workspace tools present, every host-returning tool absent.

Findings from that single pass, to act on:

- **Cross-route stage satisfaction (advisor-design, observed).** `ROUTE_STAGES` is keyed by route
  name, but the key is never threaded into stage satisfaction: the resolver receives only
  `stage.id` and matches route-agnostic marker filenames, so any route sharing a stage id or skill
  marker cross-satisfies another. The legacy `artifact-odd-${stageID}` fallback is appended for
  every stage of every route, so an ODD-era marker already satisfies `workflow-systematic` stages.
  Markers should be namespaced by route and the route passed into the ancestor walk. This is a
  gating hole, alongside R2-001's inverted predicate — item 12 now covers both.
- **Advisor worker lifecycle (advisor-integration, observed).** The granted mutation tools activate
  a single-lifecycle worker that an advisor can never finish or tear down: mutable-but-unexportable
  state. Decide who owns export/teardown on the advisor's behalf.
- **`docs/ADVISOR-HANDOFF.md` corrections (advisor-integration, observed).** It frames
  `sandbox_finish`/`apply` as permission-denied when they are simply not registered; it omits that
  the read tools require an active worker; and "cannot return results" overstates it — `sandbox_bash`
  output and `sandbox_diff` return in-tool, only the persisted export needs `finish`.
- **Verifier prose coupling (advisor-maintainability, observed).** ~15 hardcoded prose literals must
  appear in `WORKFLOW.md`/`AGENTS.md` or the run fails, so routine documentation edits break the
  verifier. Also quantified item 11: 4,772 lines, only 13 functions, all ending by line 1231 —
  everything after is one top-level body; 16 numbered section markers give natural seams, and
  section numbers are cited externally so numbering and order must be preserved. Any split must
  re-pin the digest in the same change.
- **Isolation caveat (advisor-security, observed).** The granted tools do not reach the host, but
  that is a designed-in boundary, not a proven one, because the isolation guarantees remain
  unverified.
