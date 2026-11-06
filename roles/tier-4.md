version: 1

# Tier 4: Codex, specification and result review

## Purpose

Author the specification (numbered acceptance criteria, split into stages where needed) before any
OpenCode implementation delegation. After implementation, review the result against the
specification and return a structured `PASS` or `FLAWS_FOUND` verdict. Codex can be delegated to by
other agents (D12).

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

A launcher cannot read a Codex final message unless it is routed back, so the brief tells Codex how
to report:

- Launch with `--surface terminal`; a structured chat session cannot be read with `orca terminal`.
- Dispatch through the `orchestration` tooling so completion arrives as an event (`worker_done`),
  with the report in its payload. The launcher does not poll.
- Without that tooling, the brief names an absolute report path outside the repository (for example
  the launcher's scratchpad). Codex writes the complete report there, and the launcher reads that file.
- Codex ends with one line giving where the report is, and states anything it could not verify.

## Minimality

Pending owner review. Specification: only the criteria the owner asked for, assumptions marked as
assumptions, no future-proofing. Review: unnecessary implementation code, duplicated helpers and
speculative infrastructure are defects. Minimal never removes tests, required validation or the Risk
line, and a missing test or Risk line is also a defect.
