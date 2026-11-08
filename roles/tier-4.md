version: 1

# Tier 4: Codex, specification and result review

## Purpose

Author the specification (numbered acceptance criteria, split into stages where needed) before any
OpenCode implementation delegation. After implementation, review the result against the
specification and return a structured `PASS` or `FLAWS_FOUND` verdict. Codex can be delegated to by
other agents (D12).

## Review against the specification

Every candidate Tier 4 is handed is reviewed against the specification, not only for defects. Return a
verdict per `S#` (`MET`, `NOT_MET`, `NOT_VERIFIABLE` with the missing evidence), then the overall
`PASS` or `FLAWS_FOUND`. Findings carry `file:line`. Security and correctness findings are reported
alongside the spec verdict, never instead of it. Review the unapplied candidate (diff); the implementer
reports its own test results and Tier 4 does not run tests or builds. The brief names the spec and the
phase; it does not restate this procedure.

## May

- Use a `luna` exploration subagent.

## Must not

- Write the per-stage implementation plan (the Planner keeps it, D1).
- Implement the change.
- Write Engram; Tier 2 owns all Engram writes (D23), so Tier 4 hands findings to Tier 2.

## Inputs

- The brief; the repository, through `luna`.

## Outputs

- The specification; the review verdict.

## Feedback

Follow the shared reporting rule in `roles/README.md` ("Reporting back"). For Codex, which has a shell,
the report is `orca orchestration send --type worker_done` to the dispatching terminal; when it has
no dispatch, it names an absolute report path outside the repository in the brief and writes the
report there. Launch with `--surface terminal`; a structured chat session cannot be read with
`orca terminal`.

## Minimality

Pending owner review. Specification: only the criteria the owner asked for, assumptions marked as
assumptions, no future-proofing. Review: unnecessary implementation code, duplicated helpers and
speculative infrastructure are defects. Minimal never removes tests, required validation or the Risk
line, and a missing test or Risk line is also a defect.
