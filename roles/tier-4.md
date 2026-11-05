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

## Minimality

Pending owner review. Specification: only the criteria the owner asked for, assumptions marked as
assumptions, no future-proofing. Review: unnecessary implementation code, duplicated helpers and
speculative infrastructure are defects. Minimal never removes tests, required validation or the Risk
line, and a missing test or Risk line is also a defect.
