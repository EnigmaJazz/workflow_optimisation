# Q87 — Advice record

Planning unit `q87-verification-budget-plan-u1`, 2026-10-21. Planning-only artifacts; the
`advice_record` status for this unit is `not-applicable` under the owner directive that simple
planning/docs work gets ZERO advisor and verifier Tasks. The reports below are external manual
evidence, never approval.

## Sources

- `Claude Code (Anthropic)`, manual, 2026-10-21.
- `Antigravity/Gemini (Google)`, manual, 2026-10-21.
- `selection.rule: external-manual`; the automated external lane is PLANNED and inactive. Reports are
  evidence for the plan, never approval.

## Grouped findings (current references)

- **Observed — unbounded loop wording.** `WORKFLOW.md:65` ("Repeat this loop as needed") and
  `docs/specs/pm-handoff.md:30` ("Repeat as needed") carry no ceiling; both reports read these as
  unlimited. Current file text confirmed by direct read.
- **Observed — SIX route classes, not four.** `WORKFLOW.md:118-123` lists six classes; the reports'
  "four" is STALE. The planned matrix is over those six.
- **Partially observed — docs verification.** `WORKFLOW.md:158` maps the code-review pair; a
  universal docs-verify mandate is an INFERENCE, not explicit. `WORKFLOW.md:461` states the
  trivial-docs exception; `:475` records the interim post-advice rule; `:524` the nontrivial
  pre-commit rule.
- **Disputed — overlay conditionality.** `overlay.md:199` is CONDITIONAL ("only where the external
  lane applies as written in `WORKFLOW.md`"), NOT unconditional as both reports claim; it still needs
  docs alignment.
- **Observed — unconditional ODD route-skill line.** `workflow-odd-secure/SKILL.md:10` states
  post-code advice before the work-unit commit unconditionally.
- **Observed — the systematic skill is silent on the cap.** `workflow-systematic/SKILL.md` states no
  advice/verification cap.
- **Observed locally — vendored upstream ceiling wording.**
  `global-config/prompts/gentle-orchestrator/upstream/odd-orchestrator-sections.md:42` ("One verified
  change permits at most one scoped correction; there is no loop-until-clean behavior");
  `base.md:151` gives the provenance line to `Gentleman-Programming/gentle-ai` v4.0.0. This is a
  LOCALLY VENDORED observation; the public URL was not independently verified. It does NOT justify a
  second unlimited refinement budget; the owner cap covers all.
- **Observed — Gemini post-prompt drift.** `global-config/opencode.json:2008` committed-vs-precommit
  drift vs `WORKFLOW.md:524`; Q84 already records this. `tests/test_pm_handoff_spec.py:93-111` pins
  the exact step-5 strings with mutation controls; `tests/test_anchor_manifest.py:170-215` holds the
  anchor/token/control loops (`verify-workflow.sh` ANCHOR_MANIFEST, 39 rows).
- **Observed — Q59 replay classification.** In `odd/tasks/q59-pm-verifier.md`, the JS `ReferenceError`
  and the stale PM prompt are source/high defects; stale status/pin is metadata needing PM
  facts/readback (`:417-421` metadata-fact controls; `:455-459` stale statuses/pins). The reports'
  "4+ needless docs cycles" origin/runtime is UNAVAILABLE and is NOT asserted.
- **Observed — Q84 sequencing.** `WORKFLOW.md:471/520`, `docs/specs/pm-handoff.md:23` and
  `overlay.md:199` disagree on post-code advice timing; Q84 owns the reconciliation and folds into
  Q87.

## Limitations (do not overstate)

- "99 tokens" (cited from `tests/test_anchor_manifest.py`) was not independently recounted → an
  unverified numerical detail; not claimed.
- Source pin `28ff3937…` is reported from the health-check plugin source; a LIVE deploy is not
  independently established here.
- No CodeGraph index was available to the researcher (read/AFT/AST fallback); no `init` was
  authorized.
- No routing-guard post-code stage is independently established here; not asserted.
- The reader-search negative covers only path-literal AST checks; there is no proof against dynamic
  readers, so the future reader audit fails closed.
- Q59's tracker is 545 lines; earlier cycles' needlessness is not proven.
