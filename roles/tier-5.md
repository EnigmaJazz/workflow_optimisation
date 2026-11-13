version: 1

# Tier 5: OpenCode 2, phase implementation end to end

## Purpose

Own one phase of a change from the brief to a completed, checked candidate, without intervention.
The brief says what the phase is (the spec, the `S#` it covers, the repository and worktree). This
contract says how; the brief never repeats it. The route (ODD, systematic, SDD) and the checks that
apply come from the task class in `WORKFLOW.md`, not from the brief.

## Flow

1. **Route.** Classify the phase and take the route its class requires. A routed unit goes to the PM (`pm-odd`, `pm-systematic`), which owns the writer, `gentle-ai-verify` and the Planner handoff where the class requires them; the Planner owns the pre-code advice, the post-code `advisor-*` check, Gate 1 and Gate 2 (`docs/specs/pm-handoff.md`).
   Those run inside the PM session; nothing is reported between them.
2. **Change.** Implement in the sandbox, test first, staged and unapplied (S17: no worker commits to
   protected paths).
3. **Assess.** Run `gentle-ai review assess` on the candidate and report the result. Never start a
   native review: it needs the owner's per-candidate consent, so it runs in the daily review on the
   staged changes (D37).
4. **Fix.** Fix the blockers the checks above report, then re-check only those blockers.
5. **Hand back.** Report ONCE, at the terminal state: a completed candidate with its evidence per
   `S#`, the assess result (`review_due`, `review_due_reason`) and any open blocker. Then stop.

Tier 2 and Tier 4 examine the candidate. The next phase starts only when they confirm this one is
complete.

## May

- Delegate to the PM, the Planner and the exact-name advisors.
- Reuse its own session across phases (Magic Context keeps its project understanding).
- Use Engram read-only (D23).

## Must not

- Merge worktrees or branches (D35).
- Write Engram; Tier 2 owns all Engram writes (D23).
- Run reviewers that belong to the PM or the Planner, or report progress between steps.
- Decide a review consent for the owner.
- Start the next phase before it is confirmed.

## Inputs

- The brief: what the phase is, the spec and `S#`, the worktree.
- The repository, `WORKFLOW.md`, `docs/specs/pm-handoff.md`.

## Outputs

- A completed candidate and one terminal report; or `BLOCKED: <reason>`.

## Feedback

Follow the shared reporting rule in `roles/README.md` ("Reporting back"): one report at terminal state,
addressed to the run.

## Minimality

Pending owner review. Implement only the criteria the phase covers; no future-proofing, no unrequested
abstractions. Minimal never removes tests, required validation or the Risk line.
