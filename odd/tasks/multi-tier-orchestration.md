# Multi-tier orchestration: implementation tracker

**Objective:** implement the approved five-tier orchestration (Q101-Q103). **Branch:** `Enigmajazz/multi-tier-orchestration-spec`.
**Delivery:** ask-on-risk; no push or PR without the owner. **Test runner:** `python3 -m unittest discover -s tests` (repo CLAUDE.md).
**Implementer:** Claude Code, by owner authorization on 2026-11-05, until the owner asks to return implementation to OpenCode.

## Specs

The approved specification is `docs/specs/multi-tier-orchestration-criteria.md` (128 criteria, `S1`..`S128`, stages A1-A4 and B0-B4).
Design and decisions: `docs/specs/multi-tier-orchestration.md` (D1-D27, sections 3-14). Workers read both for their stage and report which `S#` they covered.
Criteria marked "blocked by OPEN-n" are not implemented until the owner resolves that item. Hard owner strings:
- Tier 2 "writes no code" and "makes no change" without an explicit owner override (D5).
- Orca is the only launcher; Paperclip never starts a CLI (D21).
- Tier 5 uses Engram read-only; Tier 2 owns all Engram writes (D23).

## Tasks

| ID | Stage / specs | Route | Status | Evidence |
|---|---|---|---|---|
| T1 | A1 usage ledger, S1-S11 | delegated writer (parallel unit) | built; S9 needs a measured day, thresholds are placeholders | commit 4f1b338; tests.test_usage_ledger 18 OK, full suite 414 OK twice |
| T2 | A2 roles/ and CLAUDE.md, S12-S35 except S16, S23 | delegated writer (parallel unit) | built; S30-S35 wording pending owner review | commit 62ba6ed; tests.test_roles 15 OK, full suite OK |
| T3 | B0 native-review spike on staged refs, S71, S79 (OPEN-1) | delegated writer (parallel unit) | done; S71/S79 stay blocked on the OPEN-1 owner decision | `odd/advice/b0-native-review-on-staged-refs.md`; parent re-ran assess on the scratch clone: exit 0, risk medium |
| T4 | A3 Paperclip and Orca setup | inline | pending: needs Paperclip download, README review (S36) and the terms check (S44) | |
| T5 | A4 Jev plan comparison and advisor step | inline | pending: needs the owner's `TYPESAFE_API_KEY` and consent to send plans | |
| T6 | B1-B2 sandbox staging and gate routing (`agent-sandbox-integration`), S72-S110 | delegated writers, sequential (shared broker files) | in progress | Worktree `~/orca/workspaces/agent-sandbox-integration/staging-chains-t6`, branch `EnigmaJazz/staging-chains-t6` off `d61f322` (owner chose the refactor tip). U0 P0 docs and U1 P1 chain code run in parallel (disjoint surfaces); then U2 P2 host_stage_* tools, U3 reduced P4, U4 gate routing (D22, own commit, independent verifier), U5 P6 acceptance tests. S17 paths: the owner reviews and installs. |
| T7 | B3 workflow contracts (`workflow_optimisation`) | inline | pending: lands after T6 | |
| T8 | B4 model assignment review (Q103) | inline | pending: final numbers need T1's baseline | |

Route evidence: T1-T3 are three independent units with disjoint edit surfaces, each needing several minutes of work (Writer trigger a, parallelism). The parent owns git.

## Log

- L1 (2026-11-05, owner, verbatim): "Spec is approved. On this occasion I am authorising Implementation via claude code until I ask to return to opencode for Implementation. This is due to needing to i
Use the weekly usage before reset at 11:59 on 6/11/26" (the message was cut off after "needing to i"; read as using the weekly usage before the reset).
- L2: created from the approved spec at commit 41e8381. Reset deadline 2026-11-06 11:59; started 2026-11-05 23:41 GMT.
- L3 (2026-11-06): T2 and T3 reported; parent spot checks passed. Spec section 8 aligned with D23 (Tier 2 owns all Engram writes). Open flag for the owner: Tier 1 now hands strategic memory to Tier 2 to record.
- L4 (2026-11-06): T1 reported; parent re-ran the full suite twice (414 OK) and scanned for leaks. Note: `gentle-ai review assess` returns `high`/`unassessable` in a worktree with untracked files; from a clean shared clone the same commits assess correctly (T2 commit medium, under_budget; T3 commit passive). No review is due.
- L5 (2026-11-06): review of the T1 commit range (base b25670a): assessed high (`process_boundary`, signal `shell_process` on scripts/usage_ledger.py, which has no subprocess, shell or os.system use). Owner declined review for this candidate (`declined_this_candidate`). T2 and T3 commits: no review due. Delivery stays under ordinary repository policy.
- L6 (2026-11-06): owner chose to build T6 on the refactor branch's committed tip. U0 and U1 launched.
- L7 (2026-11-06): U0 committed in the sandbox worktree (88bc5dc). Owner placed S93 (no Tier 5 Engram write) in U4, the B2 gate-routing unit.
