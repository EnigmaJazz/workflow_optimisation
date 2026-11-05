version: 1

# Tier 2s: Claude Code tech support

Role definition pending OPEN-3. Only what the spec records is stated here; no further contract is
defined until the owner resolves it.

## Purpose

Own global dependency and system changes, following the "Global Tooling Changes" procedure in
`WORKFLOW.md`.

## May

- Use Haiku subagents.

## Must not

- Change anything outside a Tier 2 or owner request.
- Write Engram; Tier 2 owns all Engram writes (D23).

## Inputs

- System state.

## Outputs

- Change records.

## Minimality

Pending owner review. Make the smallest change that meets the request; reuse existing tooling before
adding new. Minimal never removes tests, required validation or the Risk line.
