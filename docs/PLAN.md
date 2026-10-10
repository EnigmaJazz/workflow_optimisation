# PLAN

## Objective
Make the global workflow scale scrutiny with complexity and impact, so that hard, risky or
wide-blast-radius changes cannot take a light route. Preference is explicit: over-applying
structure is cheaper than repeatedly repairing changes.

## Sequence
The queue with statuses and prerequisites is `docs/TODO.md`. Its Phases block is the execution order; the steps below are the plan-level narrative, and where they differ, the TODO phases govern.
1. Advisor layer: registration, then the mandatory advice policy (interim lane). Close out the
   registration (verifier mirror, restart, dispatch each advisor once), then the B0/B1/B2 policy
   unit: advice mandatory for every non-trivial change, met by the registered advisors.
2. Guard fixes in the stage-resolution path: R2-001's inverted predicate and the cross-route stage
   satisfaction (markers must be namespaced by route), with automated assertions for the stage
   table and gates. Subject to the advice mandate; they need the verifier mirror and a restart to
   take effect.
3. `docs/ADVISOR-HANDOFF.md` corrections (the sandbox project builds against it), then the
   verifier's prose coupling (stable anchors instead of prose literals).
4. Split `verify-workflow.sh`, before the external lane adds verifier checks.
5. Workflow policy: classes, ODD/advisor layers, the impact axis (how much advice), and the
   per-project impact-surface declaration.
6. External advisor lane: activate after agent-sandbox-integration plan A is installed (B3), then
   the routing-guard advice stage (B4) and the advisor handoff document (B5).
7. Tracking contract in the recipe.
8. Reconcile drift and close the gaps found by the options inventory; emergency fix route;
   worker contract; guard against gentle-ai sync overwriting the live config; remaining
   routing-guard stage work.
9. Engram as the inter-agent communication channel: evaluation first, then adoption as a
   canonical MCP with a scoped `WORKFLOW.md` policy (Magic Context stays main memory).
10. Deployment gating matrix (Q28): every workflow rule gets an enforcement point or an
    advisory-only record.
11. gentle-ai v4 upgrade (planned; owner-triggered): decisions, then docs/agents/verifier/guard
    changes on one gated branch, then the runbook (queue Q29-Q39).

12. OpenCode V2 upgrade (planned; owner-triggered; after the gentle-ai v4 upgrade): probe side by
    side, port plugins dual-mode, verifier V2 mode, change set and runbook (queue Q40-Q47).
13. Project-manager layer (owner, 2026-10-04; queue Q53-Q61): the orchestrator becomes the
    strategic front end and dispatches one route-specific project-manager subagent per work
    unit, which runs the route to completion. Q54 is done from the owner-relayed Handover A report;
    `pm-probe` is closed and removed in this unit. The required restarts
    (`sandbox-broker.service`, `secure-opencode.service`) have not been performed. The three removal
    checks—effective broker policy, installed plugin bytes, and refusal of a mutation from a
    previously bound probe session—have not been performed. Q55 remains open for the post-code
    advisory review; Q56 is gated on Q55 plus those restarts and checks, then Q57-Q61. Q62 is an
    independently planned model-retirement/seat-assignment reconciliation. Design:
    `docs/handoffs/2026-10-04-pm-layer-workflow-optimisation.md`.

## Layers
- **Execution spine** — tiny fix: direct. Everything beyond trivial follows the ODD spine and the
  Q29a route for design-heavy work.
- **Pre-code advice** — mandatory for every non-trivial change ("trivial" keeps its meaning:
  trivial document edits; clearly bounded few-line changes with no contract or security effect).
  Interim lane: the smallest sufficient set of registered `advisor-*-pre` agents, one by
  default. External lane (after plan A is installed): both external advisors (Claude Code and
  Antigravity) as an independent group for every non-trivial change, per the policy table in
  `WORKFLOW.md`.
- **Post-code review** — the interim review dispatches `advisor-*-post` agents when `ce:review`
  is not run; once active, the external advisory review of the committed unit against the agreed
  approach (both hosts), then `ce:review` where the route owes it, then the native RDD review.
  The external review is evidence, never approval.
- **Impact axis** — decides HOW MUCH advice (the number of advisors, whether a cross-family group
  is needed, whether both external hosts are consulted once the lane is active); still raises scrutiny and never lowers
  it. A heavier route always governs when the
  class and the impact disagree.

## Constraints
- The recipe is **global**; impact surfaces are **per-project data**, supplied by the host that
  knows the project root. No project's paths hardcoded into the workflow.
- The orchestrator is read-only: every mutation and every execution is delegated.
- Verification must execute what it validates; a build or parse check proves syntax only.
- Tracking is a precondition for progress, not an afterthought.
- A workflow rule is not deployed until it has an enforcement point (a routing-guard stage or
  check, a verifier check, or a native gentle-ai gate) or is explicitly recorded as advisory-only
  with the reason. Prose alone is not deployment (owner, 2026-10-01; queue Q28).
- **Forward-compatible by default (owner, 2026-10-02; queue Q48).** New and touched work must
  already hold after the gentle-ai v4 and OpenCode V2 upgrades, so no change is authored twice:
  - plugins are dual-mode (V2 `Plugin.define` plus V1 `server()`);
  - headings and checks are version-neutral;
  - verifier checks use stable anchors (Q26), not prose;
  - no new dependency on SDD, `host_sdd_*`, `strict_tdd`, or V1-only plugin hooks.
  Only what cannot be forward-compatible stays upgrade-specific: SDD removal, the V2 review
  relay, `cli.json`.
- **One source of truth, stacked upgrade branches (owner, 2026-10-02).**
  - Repo-tracked changes live only in the canonical repo.
  - The upgrades are branches stacked as `main` → v4 → V2, rebased as `main` moves.
  - Live `~/.config/opencode` is regenerated from `global-config/` by the verifier, never edited
    as a parallel copy.
  - The Q36 journal covers only what git cannot reach: `~/.claude/CLAUDE.md`, gentle-ai-managed
    blocks, and plugins owned by other projects.
  - Upgrade inventories (path:line lists) are plans: regenerate them, and build the change set,
    when the owner decides to upgrade.

## Recorded design decisions
- `ce:review` is owed for small and substantial features and for bug fixes, not for global
  tooling, whose route is source change then native review then the verifier mirror.
- The assessment runs after a commit, so it cannot trigger pre-work steps. The impact tier is
  declared up front and recorded in the route line; the assessment grades whether that
  declaration was honest.
- Enforcement of the up-front tier must come from something other than the assessment: write
  targets observed by the guard, against the project's declared surfaces.
- ODD was omitted from the first draft of the class mapping; it is the default spine beyond trivial, not a class of its own.
- The advisor layer and the impact axis share one trigger set; they are one mechanism, not two.
- 2026-10-01 (supersedes the line above): advice is mandatory for every non-trivial change, so the
  advisor layer no longer has a trigger set. The impact axis decides how much advice (number of
  advisors, cross-family group, external review lineage) and still only raises scrutiny, never
  lowers it. Source: user decision recorded in `docs/advisor/handoff-workflow-optimisation.md`
  (B0 fix 4).
- 2026-10-01: the external lane's initial state is BOTH hosts for every non-trivial pre-code
  advice request (`pair-default`), because current usage fits the subscription allowances.
  Rotation (`default-rotate`) is reserved as the first tightening step.
- 2026-10-01: native gentle-ai review always uses the in-OpenCode `asi-review-*` agents. External
  hosts give pre-code advice only, so external-lens review lineages are dropped from the plan.
- 2026-10-01 (amends the line above): external hosts ALSO give a post-code advisory review, after
  the work-unit commit and before the mandatory `ce:review` and native review. It is advisory
  evidence only and never a gentle-ai lens.
- 2026-10-01 (updated for the advisor split): interim pre-code advice dispatches registered
  `advisor-*-pre` agents, and interim post-code advisory review dispatches registered
  `advisor-*-post` agents for a non-trivial unit only when the route does not run `ce:review`
  (which already is an advisory multi-persona review). Evidence only, recorded with step
  `post-code`. `post-code-pair` takes over once the external lane is active.
- 2026-10-01: deployment gating. All workflow changes must be correctly gated when deployed; see
  the Constraints bullet and queue Q28 (gating matrix).
- 2026-10-04: review/advisor model assignments were changed so no reviewer shares a model family
  with the author of what it reviews. Review lenses, judgment seats and split advisors were
  reassigned; a later patch moved the lens seats onto the `opencode-go` subscription, removed
  `mimo-v2.6-pro`, set `glm-5.3-flash` on the resilience lens and `jd-judge-a`, and made
  `opencode-go/glm-5.3` (non-flash) the resilience fallback target. The owner relaxed the two
  verifier provider-diversity checks on the decision that subscription capacity plus failover
  replaces provider spread. Tracker: `odd/tasks/model-assignments.md`. The GPT fallback target
  question remains open.
- 2026-10-05: assign `review-readability` and `asi-review-readability` to
  `opencode-go/muse-spark-1.3-contributor` (`high`); the owner accepted the model's training-data
  terms. The local Go usage limit is unavailable and remains unknown, not a numeric assumption.
  The model-family verifier maps Muse Spark to `muse`. Tracker: `odd/tasks/model-assignments.md`.
- **Owner decision (2026-10-07) — session writing model: cloud.** This project uses
  `gentle-ai-worker` (`deepseek-v4.1-flash`); a PM unit may rely on this explicit decision without
  inferring it. The local option, `gentle-ai-worker-local` (`kinver/professional`), exists but was
  not selected.

## Memory and inter-agent communication (direction, 2026-10-01)
- **Memory pathway by runtime (owner decisions, 2026-10-01):**
  - **OpenCode:** Magic Context is the default memory pathway, holding durable project memory
    and the ODD tracker mirror.
  - **Claude Code:** it cannot reach Magic Context, so it uses Engram only, mainly in its
    advisory role.
  - **Everywhere:** blanket mandatory-Engram protocol text is removed (queue Q35), and the ODD
    tracker file is the durable task record.
- **Engram is the candidate inter-agent communication channel:** handoffs, evidence references,
  and requests and answers between agents. Adopt it only after the evaluation (queue Q14a) and
  the owner's decision.
- **On adoption:**
  - Engram is added as a canonical MCP in `global-config/opencode.json` and known to the verifier.
    Otherwise every gentle-ai sync adds it, and every verifier run strips it.
  - Engram tools are granted per agent, with first-pass independence preserved.
  - `WORKFLOW.md` states clearly what goes where, with no duplication between the two stores.
  - An Engram message is evidence, never approval.
- **Until then** the current rule stands: ODD work does not invoke `mem_*`. Even after adoption,
  Engram is never mandatory and never a memory pathway; it is only a scoped opt-in channel.
- **v4:** override or disable v4's Engram tracker mirror (Q29b decided).

## Upgrade change set: non-destructive apply and revert (design, 2026-10-01)
- Every upgrade change is a declarative operation with an expected-before value. There are no
  whole-file copies.
  - JSON: path, `expect_before`, then `set` or `delete`.
  - Markdown: anchored or marked block, expected text, then replacement.
  - Whole files: expected hash.
- **Apply** writes an operation only when the current value matches `expect_before`. It is
  idempotent when the target is already present, and it skips with a reported conflict
  otherwise. It journals before and after values per operation.
- **Revert** restores the before value only where the current value still equals what apply
  wrote. Later drift from gentle-ai sync, other sessions or hand edits is reported, never
  overwritten.
- **Process:** `scripts/changeset.py apply --dry-run`, then `apply`, with the verifier as
  `--verify-cmd`. Rollback is `scripts/changeset.py revert --dry-run`, then `revert`, newest
  journal first (spec: `docs/specs/changeset-tool.md`). Repo-tracked
  sources also ride one feature branch, so `git revert` is the repo-level rollback.
- Queue Q36. The set includes:
  - `host_sdd_*` deny, with its verifier change as one unit (Q37, merged; not applied early);
  - the strict-TDD removals (Q38);
  - an in-flight SDD preflight (Q39). Apply refuses while any open OpenSpec, Magic Context or
    Engram SDD change lacks an owner disposition: finish on 3.7.0 first, convert to ODD, or
    abandon.

## OpenCode V2 upgrade path (planned, 2026-10-02)
- **Why:** OpenChamber 2.x requires OpenCode 2.0.15 or newer.
- **Order:** gentle-ai v4 first (native review on V2 needs it), then a V2-compatible Systematic
  release (hard blocker), third-party plugin readiness (`~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md`) and the agent-sandbox plugin port,
  and only then V2.
- **Non-destructive by construction:**
  - V2 reads V1 config and normalises it in memory without rewriting files.
  - This repo's plugins go dual-mode (one file exports V2 `Plugin.define` and V1 `server()`).
  - V2 installs beside V1, and its first run is probed against a scratch copy of the config.
  - Changes ship as the Q36-style change set with a drift-preserving revert, and the V1 binary
    stays available for rollback.
- Queue Q40-Q47.

## Route for design-heavy substantial work (Q29a, v4)

Owner decision 2026-10-02 (Q29a): the full route below, chosen over a lighter variant without `ce:brainstorm`, so each stage has a durable artifact the guard can gate.
The route for design-heavy substantial work builds on the ODD spine and the `ce:*` skills.

**Substantial design-heavy feature** (material product or design ambiguity):
1. ODD spine: feature document `odd/tasks/<feature>.md` created before any source write.
2. `ce:brainstorm` produces the requirements doc (`docs/brainstorms/`).
3. `ce:plan` produces the plan (`docs/plans/`); design decisions are recorded in the feature
   document.
4. Pre-code advice: interim `advisor-*-pre` set; external `pair-default` once active. Consequential
   findings are resolved before coding.
5. `ce:work` task by task, each closing with a work-unit commit.
6. Per-commit RDD assessment.
7. Post-code advisory review: interim `advisor-*-post` set only when `ce:review` is not run;
   external `post-code-pair` once active.
8. `ce:review`.
9. Native gentle-ai review (`asi-review-*`) when due.
10. `ce:compound` captures learnings.

SDD artifact mapping:

| SDD artifact | Replacement |
|---|---|
| proposal, spec | requirements doc (`ce:brainstorm`) |
| design | plan (`ce:plan`) plus feature-document decisions |
| tasks | feature-document checklist |
| archive | ODD progress record plus `ce:compound` |

Guard stages: requirements, plan, tracker, review, namespaced by route (depends on Q03).

## Tracking contract
The orchestrator maintains `docs/TODO.md`, this plan, and an in-agent todo list, plus the
per-feature `odd/tasks/<feature>.md` and its Magic Context mirror. Updating them gates starting
a new work unit. A unit paused awaiting user input is valid recorded state and does not block.
## Emergency fix route (design — to implement)

**Purpose.** A user-declared priority lane for urgent fixes — production down, work blocked, or an
active exposure — that must not wait behind the normal queue.

**Properties.**

- **Preemption.** The emergency takes the lane. The current unit is PARKED with its state recorded
  (todo entry, feature tracker, Magic Context mirror) and resumes when the emergency closes. Queue
  order is preserved, never discarded.
- **Declaration.** Only the user invokes it, explicitly. The agent never self-declares an
  emergency, because that would make every urgent-feeling task one. One at a time.
- **Minimum ceremony, bounded diff.** No brainstorm, no plan; the smallest change that resolves it.
  Reproduce the fault, or record why reproduction is impossible in the time available.
- **Still required.** The emergency is logged — the tracker line is part of the fix, not an extra.
- **Deferred, not waived.** Native review and any `ce:review`-class check may be deferred, but only
  as recorded debt with a named follow-up, never silently skipped. Impact still governs: an
  emergency touching security, permissions, credentials or an enforcement path needs an
  independent assessment before or immediately after it lands.
- **Exit.** When resolved, schedule the debt, then resume the parked unit in order.
- **Guard interaction.** The route suspends the normal stage prerequisites by declaration. Guard
  warnings during an emergency are expected and recorded, not treated as failures.

**Open question.** Whether this is a seventh task class in the routing table or an orthogonal
session mode layered over the existing classes — the same question ODD and SDD raised, and it
should be settled when the workflow policy is defined rather than now.
## Coding standard: prefer small files — the sandbox constraint is a forcing function
Recorded 2026-09-30, correcting an earlier framing.

Prefer keeping code in smaller files wherever possible. Smaller files are more readable, and as a
direct consequence they remain editable by whole-body tools: `sandbox_edit` works on any file a
worker can emit, and fails only when a single file grows past what one call can carry.

So the order of preference is:
1. **Keep files small** — a coding standard in its own right, not a workaround.
2. **Only when a single file cannot reasonably be split**, use the patch route: host-read before
   activation, compose context-bearing hunks, apply with `sandbox_apply_patch`.

The patch route is the fallback for an unavoidable large file — never the default. Writing massive
scripts is the practice to avoid, not the condition to accommodate. This reverses the emphasis in
item 10: the contract's first rule is file size discipline, and the patch technique is its escape
hatch.

**Correction 2026-10-01.** The "whole-body" premise above is retracted (`CLAIM-RETRACTIONS.md`,
`docs/TODO-HISTORY.md` "2026-10-01 — CORRECTION: sandbox_edit is targeted"). `sandbox_edit` takes
`oldString`/`newString` and edits large files in place, up to the 512 KB cap. Small files stay the
coding standard, for readability and testability rather than as a tooling constraint. The worker
rules are queue item Q12.

## 11. Split `verify-workflow.sh` into smaller files
`verify-workflow.sh` is 4,770 lines — the file that cannot be whole-body edited, that times out on
reads, and that made every one of today's repair cycles expensive. Split it.

**Correction 2026-10-01:** the tooling no longer forces the split (targeted edits and large reads
both work). It remains worthwhile for readability and testability, and it precedes B3, which adds
verifier checks.

Options to weigh when implementing:
- A thin runner that invokes per-area check scripts: each independently runnable and testable, with
  the runner owning ordering and the aggregate FAIL status. Isolation is the gain; shared state must
  pass through files or environment.
- A thin entry point that sources modules under a `lib/`-style directory: simpler state sharing in
  one process, but harder to test a module in isolation.

Recommendation to evaluate: the runner plus per-area scripts, because each check becomes separately
executable and the verifier's own behaviour becomes testable — which is what the review's
missing-stage-tests finding asks for elsewhere. Preserve the current check ordering, the `fail`
aggregation, the TTY/`NO_COLOR` colour behaviour, the digest pinning contract, and the
`WORKFLOW_VERIFY_*` environment switches.
