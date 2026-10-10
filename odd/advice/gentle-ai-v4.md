# Pre-code advice record — gentle-ai v4 upgrade (Q30 / T1)

**Unit:** preparation for Q30 workflow documents (tracker `odd/tasks/gentle-ai-v4.md#T1`).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Unit model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07; the author's
model family is DeepSeek).
**Status:** pre-code advice recorded (satisfies the route's advice stage); slice-1 checks
observed; post-code advisory review observed 2026-10-10 and its single required fix applied in
the refinement delta (Q30 remains open).

## Dispatch
- Registered interim advisor: `advisor-integration-pre`.
- Task session: `ses_edd654d1dffecaALlO1nkvtPuS`.
- Configured model: `opencode-go/kimi-k2.7-code` (independent of the author's family).

## Original advice (summary as supplied to this unit)
The first pass, among other points, recommended expanding Q30's scope to include Q32 and Q33,
checking out the synthetic work branch, and replacing the fixed tracker identifiers. The full
advisor response was not handed to this unit; only this summary is recorded.

## Amended advice (authoritative; supplied 2026-10-09)
1. **Intentionally nondeployed Q30.** Source-only changes; no verifier mirror, no service
   restart, no live deployment inside Q30.
2. **Preserve the excluded surfaces.** The verifier, plugins, and config (`verify-workflow.sh`,
   `global-config/plugins/**`, `opencode.json`, `tui.json`, `systematic.jsonc`, prompts) are
   Q31-Q33 work and must not be touched by Q30.
3. **Fixed tracker identifiers.** T1 = Q30; future Q31+ entries are gate references, not extra
   tasks. Do not rename.
4. **`pm-handoff` SDD debt.** `docs/specs/pm-handoff.md:25` and `:32` still mention SDD; that
   residual debt belongs to the Q55 follow-up, not to Q30.
5. **Q39 is a gate.** The six in-flight SDD changes stay pending owner dispositions; do not
   resolve them in Q30.
6. **Independent post-code advisor.** `advisor-integration-post`, and it must not be a
   DeepSeek-family model (the author is cloud DeepSeek); a post-commit RDD assessment is
   required for each work-unit commit.

## Retractions (earlier recommendations; RETRACTED — not authority)
- **Expand Q30 to Q32/Q33 — RETRACTED.** Q30's scope is fixed; Q32/Q33 are separate queue items
  with their own prerequisites.
- **Check out the synthetic work branch — RETRACTED.** The worker runs on its synthetic work
  branch by design and must never switch branches; the PM confirms the real feature branch.
- **Replace the tracker identifiers — RETRACTED.** Identifiers are stable and fixed.

## Authority resolutions (exact)
- `last_reviewed_boundary` stays `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860`; it is **NOT** host
  HEAD `b4006acc928b6bddc1ac7f98f71d5c83d3903cbb`.
- `host_git_commit` accepts a message/session id (it commits the session's applied result); it
  does **not** take a base ref/base selector. The supplied constraints are recorded here instead
  of the advisor's mistaken recommendation to pass a boundary into it.
- Q30 preserves the `SEARCH_TOOL_ROUTING_DRIFT` strings exactly and keeps the
  `two or more non-trivial files` writer rule literal.
- Consequential findings are resolved by the amended advice above; the pre-code gate for
  `workflow-odd-secure` is satisfied by this record.

## Slice 1 record (Q30/T1, 2026-10-10)
- Scope: `WORKFLOW.md` Mapping + Long-session backstop bullets (evidence budget, per
  `docs/TODO.md` Q30 and the gentle-ai v4 release line), `odd/tasks/gentle-ai-v4.md`, this file.
- Checks observed in the sandbox: doc-contract probe RED → GREEN (`PROBE_RETURNCODE=1` → `0`);
  routing-guard suite `HOME=<mktemp -d> bun test tests/routing-guard` 94 pass / 0 fail /
  224 `expect()` calls, `RETURNCODE=0` (baseline and post-edit). Raw invocations are recorded in
  the tracker.
- Post-code advisory review (observed 2026-10-10): independent `advisor-integration-post`
  (Task `ses_edb9bca70ffeiC8VwnVH6WqrHH`; not DeepSeek-family) reviewed the installed
  candidate. Findings: the WORKFLOW.md evidence-budget bullets are correct; one required fix —
  the stale `ask-on-risk` strategy text (tracker branch parenthetical, Delivery bullet, and
  delivery strategy) is replaced with the approved `feature-branch-chain`. No other findings;
  no review authority claimed; the reviewed boundary is unchanged.

## Refinement record (Q30/T1, 2026-10-10)
- Scope: `odd/tasks/gentle-ai-v4.md` and this file only; `WORKFLOW.md` untouched.
- Applied: the post-code required fix above (strategy wording), with the advisory
  identity/reference/findings/disposition recorded in the tracker's Advice record.
- Checks observed in the sandbox: WORKFLOW.md two-bullet probe GREEN (12/12,
  `PROBE_RETURNCODE=0`); routing-guard suite with the exact runner under a throwaway HOME:
  94 pass / 0 fail / 224 `expect()` calls, `GUARD_RETURNCODE=0`.
- Worker: `odd-apply` Task `ses_edbc5062bffebXomOvL1LqcGg8` (fresh worker; prior refinement
  writer `ses_edb98fc7bffevHGT1pBsTAuuAm` terminal `fallback_chain_exhausted` with no
  recoverable result).

## Post-code advisory review (observed 2026-10-10)
- Ran before the slice-1 work-unit commit: independent `advisor-integration-post` (not
  DeepSeek-family), Task `ses_edb9bca70ffeiC8VwnVH6WqrHH`.
- Findings and applied disposition: WORKFLOW.md evidence budget confirmed correct; required fix
  (stale `ask-on-risk` → approved `feature-branch-chain`, at tracker branch parenthetical,
  Delivery bullet, and delivery strategy) applied by the refinement writer in the two-path
  refinement delta; checks observed before export.
- No review authority is claimed; Q30 remains open. Native review remains separately driven and
  is never run by the worker or the PM.

## Post-commit assessment (required)
- Each T1 work-unit commit is assessed against `5387c24dfa9a96c80ef93e27e8bcc9abd58d6860`; the
  observed outcome is recorded. This preparation unit has no commit.
