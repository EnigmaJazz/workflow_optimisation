# Q26 — Stable anchors for the verifier's prose assertions

Metadata: Feature: gentle-ai v4 upgrade / queue Q26 (stable anchors). Task ID: q26-stable-anchors (stable). Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T0 IN PROGRESS (tracker created; T1 docs anchors and T2 verifier checker pending). Model: cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07). Ordering: Q26 lands BEFORE Q04 (Q04 owns the verifier split and must preserve the anchor checker).

## Objective

Remove the verifier's coupling to editable prose by introducing stable machine anchors, so routine wording/heading edits stop red-lighting the verifier, while contractual literals, negative absence checks and exact deployment equality stay exactly as strong as they are today.

## Problem

`docs/TODO.md:386-399` (Q26). The verifier asserts hardcoded prose literals against `WORKFLOW.md` and the assembled routing contract in `verify-workflow.sh` section 7 (~`:4312-4629`). The brittleness is already demonstrated: Q30's heading retitles red-lit verifier pins until Q32 rewrote them (`odd/tasks/gentle-ai-v4.md:258-261`). Two recorded figures in the Q26 entry are STALE and must be corrected in T1: "About 15 hardcoded prose literals" (the region actually carries ~170 grep predicates) and "4,772 lines / 13 functions" (the script is now larger).

## Scope

### In scope

T1 (docs-only): paired anchor markers around the load-bearing blocks; correction of the stale `docs/TODO.md:392-399` figures.

T2 (verifier): an artifact-specific anchor checker; migration of the load-bearing long chains; re-targeting the AGENTS greps that are already byte-compared; the coupled `VERIFY_SCRIPT_SHA256` re-pin; fixtures with positive controls.

### Out of scope (preserved)

PRESERVE as literal checks: every negative absence assertion (`:4415-4427`, `:4433`, `:4625-4629`); the exact deployment-equality block (`:4453-4498`); the six task-class names (`:4318-4320`); the R1–R14 requirement numbering (`:4443-4445`); the external-context sentinel. Also out of scope: Q04 (the verifier split), Q36's change-set content, Q28's gate table, Q48's lint.

## Constraints

The marker syntax is `<!-- workflow:anchor workflow.<id>:begin -->` … `<!-- workflow:anchor workflow.<id>:end -->`; both delimiters are unindented WHOLE lines; each full delimiter occurs EXACTLY ONCE in its OWNING file with begin before end; validate each block in its owning file, never in the assembled concatenation; every block carries a keystone token (a machine identifier that must appear inside the block) so an empty or watered-down block fails; the assembly is AGENTS + three `workflow-*` skills + their three reference files (`verify-workflow.sh:4522-4528`) — NOT four; the AGENTS routing block has a second authority (the heredoc at `verify-workflow.sh:1305-1319`, byte-compared at `:4453-4472`), so markers placed there require a script edit + `global-config/AGENTS.md` sync + re-pin; skill-side anchors go in `global-config/skills/...` source only (recovery byte-copies them); any `verify-workflow.sh` edit — including comments — requires re-pinning `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts` in the SAME commit, LAST; the verifier is never run against the host tree (fixtures + `WORKFLOW_VERIFY_*` overrides only, and NOT `--recover-config-only`, which exits before section 1); branch `feat/gentle-ai-v4`; never switch branches; never commit; `bash -n` is NOT evidence.

## Acceptance criteria

The migrated assertions no longer depend on editable prose; missing, duplicated, reversed or emptied anchors FAIL; a wrong-artifact marker FAILS; rewording prose INSIDE an anchored block still PASSES; every preserved literal/negative/equality check still fires; the digest pin equals `sha256sum verify-workflow.sh`; each commit stays inside the 400-line / 100-KiB authored budget.

## Authorized scope

T1: `WORKFLOW.md`, `global-config/AGENTS.md` (source), `global-config/skills/workflow-{route,odd-secure,systematic}/**`, `docs/TODO.md` (the stale figures only). T2: `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` (the pin only), `tests/**`. Plus this tracker, the advice record, `ROUTER-LOG.md`. No deployment.

## Checks

`bash -n verify-workflow.sh` (smoke only, NOT evidence); a FULL fixture workspace (`cp -a` into `$(mktemp -d)` with all `WORKFLOW_VERIFY_*` overrides pointing into it) run message-level, asserting the `fail()` strings, not an exit code; positive controls (anchor begin deleted → fail; keystone deleted but markers intact → fail; anchor duplicated → uniqueness fail); negative control (reword inside a block → pass; delete the body leaving markers → keystone fail); a regression control proving a preserved negative check still trips; `HOME="$(mktemp -d)" bun test tests/routing-guard`; `python3 -m unittest discover -s tests`; `sha256sum verify-workflow.sh` == the pin extracted by `read_verify_script_pin`.

## Tasks

- [ ] T1 — docs-only anchors: add the paired markers + keystone tokens around the load-bearing blocks in `WORKFLOW.md` and the three `workflow-*` skills/references (source), sync `global-config/AGENTS.md` where its routing block is anchored, and correct the stale `docs/TODO.md:392-399` figures ("~15 literals", "4,772 lines / 13 functions"). No `verify-workflow.sh` edit, therefore NO re-pin; every existing grep still passes, so this is a green intermediate state.
- [ ] T2 — verifier: add the artifact-specific anchor checker (exactly-one begin/end, ordered, non-empty interior, keystone present, owning-file scope); migrate the load-bearing long chains (`:4339-4353`, `:4359-4409`, `:4562-4570`, `:4579-4619`); RE-TARGET the AGENTS greps already covered by `PY_COMPARE_BOUNDED` (`:4501-4505`, `:4511-4514`) at `$AGENTS_SOURCE`/`$ROUTING_CANONICAL`; PRESERVE the negative checks, the deployment-equality block, the task classes and the R1–R14 numbering; add the fixture-based positive/negative/regression controls; re-pin `VERIFY_SCRIPT_SHA256` LAST and prove coherence.

## Progress

- 2026-10-11: T0 — tracker and advice record created. Route: delegated. No source edit yet. Scope settled from two pre-code advisories (see `odd/advice/q26-stable-anchors.md`): migrate the load-bearing prose chains, re-target the redundant AGENTS greps, preserve the negative and equality checks.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; PM layer unusable — see the PM-layer note). Trigger: secure no-inline-mutation policy (any file change delegated); multiple non-trivial files → bounded sandbox writer.

## Next step

T1 (docs-only anchors, no re-pin), then T2 (the verifier checker + re-pin), each as its own commit; then the owner's deployment (mirror + restart) and a re-verify.
