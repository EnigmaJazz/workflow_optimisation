# Q55 closure — pre-code advice record

## advisor-integration-pre (2026-10-14)

- **The three-item gap list is INCOMPLETE.** Beyond the tracker's `:306` trio (absent/unrecoverable
  tracker mirror, unverifiable `last_reviewed_boundary`, outstanding prerequisite checks), the
  contract leaves further procedure gaps undetermined: `:7` `last_reviewed_boundary` recovery
  (the field accepts explicit `none` but names no recovery path for a value that cannot be
  resolved), `:28` branch reconciliation ("deliberately reconcile the intended feature branch"
  names no criterion for what "intended" means), `:71` `advice_record` production (what makes an
  advice record durable or admissible is unspecified), `:72-74` guard-log reading
  (`routing_gate_observations` requires a `log_reference` with "matching evidence" but the
  contract gives no read procedure), `:87-92`/`:111` metadata-work-unit dispatch (the envelope
  describes the outcome but no dispatch trigger or hand-off is defined), and `:94-97`/`:115`
  tracker/mirror readback comparison (agreement is required for `DONE` but no comparison procedure
  is given).
- **PM tool surface (observed).** Both PMs hold `read: allow`; `glob` is inherited from
  `global-config/opencode.json:2291`; `bash` is denied and all `sandbox_*` tools are denied. This
  surface is audited at `verify-workflow.sh:2801-2812`. The consequence is that the branch check
  must use the existing `read` grant: reading `.git/HEAD` and, if needed,
  `.git/refs/heads/<branch>` is within the grant; no execution surface exists.
- **Observed `pm-odd` BLOCKED.** The live `pm-odd` run could not perform the mandated unit-start
  branch/HEAD verification and returned `BLOCKED`, recorded at `odd/advice/q32-verifier-v4.md:26`.
  The contract stated the obligation without naming a mechanism or a criterion, so the unit could
  not be executed by the PM layer.
- **Four hazards.** The branch check must fail closed, not silently pass, under: a detached HEAD
  (`.git/HEAD` holds a raw SHA), a linked worktree whose HEAD lives under `.git/worktrees/`
  (`.git/HEAD` in the worktree root is not the controlling file), an unborn branch with no
  `refs/heads/<feature_branch>`, and an in-progress rebase or merge (HEAD may transiently not be
  the branch the brief names).
- **Consumers (observed).** The contract is consumed by the PM prompts at
  `global-config/opencode.json:1921` and `:2041`, referenced by `WORKFLOW.md:53`, and described by
  `odd/tasks/pm-layer.md:159-160` and `odd/advice/gentle-ai-v4.md:41`. `verify-workflow.sh` does
  NOT assert the contract's content: it records no check over `docs/specs/pm-handoff.md`, so a
  wording change to the contract is not caught by the verifier.

## advisor-testing-pre (2026-10-14)

- **No consumer parses the file's body.** Every consumer named above points at the contract but
  none reads or validates its prose structurally; the document is human- and PM-facing only.
- **No test asserts a `docs/specs/` document.** A search of `tests/` found no assertion against any
  document under `docs/specs/`. The closest precedent is a literal-needle test that greps
  `verify-workflow.sh` for required strings; no equivalent exists for the contract.
- **The central claim is runtime-behavioural and NOT repo-testable.** Whether a PM actually performs
  the `.git/HEAD` comparison cannot be proven by any repo test; it must be recorded as `inferred`,
  with a live `pm-odd` dispatch (whose envelope records the check and its observed result) as the
  falsifier.
- **Same-commit obligation.** `odd/advice/q32-verifier-v4.md:26` records this very gap as OPEN, so
  it must change in the same commit or it becomes a contradicting advisory. It is updated to CLOSED
  here.
- **Recommended smallest verification set.** Writer-side: the existing Python suite
  (`python3 -m unittest discover -s tests`) and the Bun routing-guard suite
  (`bun test tests/routing-guard`). Orchestrator-side: a literal-needle readback of the changed
  contract lines plus cross-file wording consistency across the tracked artifacts.
