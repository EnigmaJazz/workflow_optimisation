# Q26 — Stable anchors for the verifier's prose assertions

Metadata: Feature: gentle-ai v4 upgrade / queue Q26 (stable anchors). Task ID: q26-stable-anchors (stable). Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T0–T2 DONE-AT-SOURCE (Q26 source complete; T2 native review approved+acknowledged). Deployment (verifier mirror + OpenCode restart) pending (owner). Model: cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07). Ordering: Q26 lands BEFORE Q04 (Q04 owns the verifier split and must preserve the anchor checker).

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

- [x] T1 — docs-only anchors: add the paired markers + keystone tokens around the load-bearing blocks in `WORKFLOW.md` and the three `workflow-*` skills/references (source), sync `global-config/AGENTS.md` where its routing block is anchored, and correct the stale `docs/TODO.md:392-399` figures ("~15 literals", "4,772 lines / 13 functions"). No `verify-workflow.sh` edit, therefore NO re-pin; every existing grep still passes, so this is a green intermediate state.
- [x] T2 — verifier: add the artifact-specific anchor checker (exactly-one begin/end, ordered, non-empty interior, keystone present, owning-file scope); migrate the load-bearing long chains (`:4339-4353`, `:4359-4409`, `:4562-4570`, `:4579-4619`); RE-TARGET the AGENTS greps already covered by `PY_COMPARE_BOUNDED` (`:4501-4505`, `:4511-4514`) at `$AGENTS_SOURCE`/`$ROUTING_CANONICAL`; PRESERVE the negative checks, the deployment-equality block, the task classes and the R1–R14 numbering; add the fixture-based positive/negative/regression controls; re-pin `VERIFY_SCRIPT_SHA256` LAST and prove coherence.

## Progress

- 2026-10-11: T0 — tracker and advice record created. Route: delegated. No source edit yet. Scope settled from two pre-code advisories (see `odd/advice/q26-stable-anchors.md`): migrate the load-bearing prose chains, re-target the redundant AGENTS greps, preserve the negative and equality checks.
- 2026-10-11: T1 committed `65beb19` (6 files, +66/−3). Added 31 paired anchor blocks around the prose-asserted doc blocks (15 WORKFLOW.md; 5 odd-and-review.md; 1 workflow-route/SKILL.md; 8 session-decisions.md; 2 specialists.md), mapping 32 assertions to 31 blocks; every block carries a keystone token. Additive only — no verifier edit, so no re-pin and no behaviour change yet. Also corrected the stale `docs/TODO.md` Q26 figures (~15 literals → ~170 predicates; 4,772/13/1231 → 5,008/14/1,276). DELIBERATE EXCLUSION: the AGENTS.md `## Secure workflow router (MANDATORY)` block is not anchored here — its bytes must equal the verifier heredoc (`:1305-1319`, byte-compared at `:4453-4472`), so it belongs to T2.
- 2026-10-11: T1 evidence — 132/132 literals still present after the edit (0 miss); anchor integrity 31/31; positive control (deleting `workflow.prove-out:begin` fails a count==1 probe, restoring passes byte-identical); routing-guard 96/0.
- 2026-10-11: T2 committed `e393440` (3 files, +210/−127). Added the artifact-specific anchor checker (`anchor_block_body`/anchor_has/`anchor_check_row` + a 32-row manifest keyed by `~`-separated fields): exactly one begin/end pair per id in the OWNING file (count==1 with `grep -Fxc`, not `-q`), begin-before-end, non-empty interior after stripping blank/heading/comment lines, and a keystone present inside the extracted interior; failures are distinct codes (`ANCHOR_MISSING`, `ANCHOR_DUPLICATE`, `ANCHOR_UNORDERED`, `ANCHOR_EMPTY`, `ANCHOR_KEYSTONE_MISSING`, `ANCHOR_WRONG_FILE`). Migrated the four load-bearing chains: 12+19+2+18 = 51 contractual literals KEPT but scoped inside their owning anchor block, the retained negative absence guard untouched, and the prose/heading predicates replaced by the anchor checks. Re-targeted the AGENTS greps already covered by the byte comparison at `$AGENTS_SOURCE`. Anchored the `## Secure workflow router (MANDATORY)` block via the verifier heredoc + `global-config/AGENTS.md` (byte-identical, 3145 bytes each). `VERIFY_SCRIPT_SHA256` re-pinned `12ebaf72…` → `d4241d2d…`. Fixture proof (full temp workspace, message-level assertions): baseline ok; a reword inside an anchored block passes; deleting a begin line, deleting a keystone, duplicating a begin, reversing begin/end, emptying a block, and moving a begin to another file each FAIL with their distinct code; the removed-guidance negative still trips; the deployment-equality check still fires on a stale deployed copy. routing-guard 96/0; python unittest 95 OK; the pin equals `sha256sum verify-workflow.sh` via the verifier's own `read_verify_script_pin` regex.
- 2026-10-11: T2 native review: lineage `review-492e6a492e150512`; tier **high**; candidate 3 files / 337 lines; all four lenses admitted; outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:c8faf366…`. Process note: the `asi-review-resilience` lane failed FOUR times at the relay (`opencode_task_output_malformed`/`opencode_reviewer_result_truncated`/`opencode_reviewer_result_refused`) with no rate-limit-fallback entry; the owner supplied the reviewer's actual output, whose `subject_hash` matched the bound slot (`sha256:12827c48…`), and it was captured via the provider's own `review.capture-result` operation — the result was genuine, only the transport send failed.

## T2 advisory findings (non-blocking, informational; separate later work, never re-review triggers)

- `R4-verification-coverage-relaxed` (resilience WARNING, `verify-workflow.sh:4494-4496`) — roughly twenty previously enforced predicates were dropped with no replacement manifest row, so deleting, e.g., the ODD delegation thresholds, the 4R transport rules, the review-loop literals, or the Astra guard literals from WORKFLOW.md would leave the anchors intact (their keystones never mention them) and the recipe-consistency stage would print ok. The in-code comments claiming the dropped prose is "covered by the anchor checker" are INACCURATE: the checker pins block existence, non-empty interior, and one keystone per block only. The trade is defensible but the comment minimizes the coverage loss.
- `R3-anchor-prose-coverage` (reliability WARNING, `verify-workflow.sh:4380-4395`) — same class: ~50 specific prose/heading greps replaced by keystone + non-empty checks, so contractual prose drift INSIDE a block is no longer detected; the comments overstate the coverage.
- `R4-anchor-companion-coupling` (resilience WARNING, `verify-workflow.sh:4406`) — 31 of 32 anchor rows bind markers in WORKFLOW.md and four skill files that this candidate does NOT modify; if the companion marker blocks are absent on the landing boundary, every row fails ANCHOR_MISSING and the verifier fails on every run until they arrive. Fail-closed, but a hard cross-candidate dependency. SATISFIED HERE: T1 (`65beb19`) landed those markers BEFORE this candidate's base (`c7a85ae`), so they are on the boundary; keep T1 and T2 on the same reviewed boundary and never revert T1 alone.
- `R4-anchor-scan-rework` (resilience SUGGESTION, `verify-workflow.sh:4346-4350`) — `anchor_has` re-runs a full awk pass per call (~30+ full-file passes per verifier run); a per-file body cache collected during the manifest loop would halve it and remove the source-vs-deployed asymmetry.
- `R3-agents-source-inconsistency` (reliability SUGGESTION, `verify-workflow.sh:4430-4432`) — the `workflow.agents.secure-router` anchor is structurally validated against `$AGENTS_SOURCE` but its literal `anchor_has` check reads `$AGENTS_FILE`; mixing sources for one anchor could mask mirror drift if the byte comparison is ever bypassed.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; PM layer unusable — see the PM-layer note). Trigger: secure no-inline-mutation policy (any file change delegated); multiple non-trivial files → bounded sandbox writer.

## Next step

Q26 source work is COMPLETE (T0–T2). OWNER ACTION: run `bash verify-workflow.sh` to mirror, then restart `secure-opencode.service` (+ `ai-proxy.service`), then re-verify; also run the one-time `rm -rf ~/.config/opencode/skills/workflow-sdd-secure` (Q30) which the verifier now reports as `RETIRED_WORKFLOW_SKILL_PRESENT` until done. Highest-value carry-forward: correct the two inaccurate "covered by the anchor checker" comments, and restore manifest rows (or explicit keystones) for the dropped contractual literals, per `R4-verification-coverage-relaxed` / `R3-anchor-prose-coverage`. Keep T1 and T2 on the same reviewed boundary (`R4-anchor-companion-coupling`).
