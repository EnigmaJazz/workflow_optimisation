# PLAN

## Objective
Make the global workflow scale scrutiny with complexity and impact, so that hard, risky or
wide-blast-radius changes cannot take a light route. Preference is explicit: over-applying
structure is cheaper than repeatedly repairing changes.

## Sequence
The queue with statuses and prerequisites is `docs/TODO.md`; this sequence matches its order.
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
5. Workflow policy: classes, ODD/SDD/advisor layers, the impact axis (how much advice), and the
   per-project impact-surface declaration.
6. External advisor lane: activate after agent-sandbox-integration plan A is installed (B3), then
   the routing-guard advice stage (B4) and the advisor handoff document (B5).
7. Tracking contract in the recipe.
8. Reconcile drift and close the gaps found by the options inventory; emergency fix route;
   worker contract; guard against gentle-ai sync overwriting the live config; remaining
   routing-guard stage work.
9. Engram as the inter-agent communication channel: evaluation first, then adoption as a
   canonical MCP with a scoped `WORKFLOW.md` policy (Magic Context stays main memory).

## Layers
- **Execution spine** — tiny fix: direct. Everything beyond trivial and not SDD: **ODD** (tracker
  plus Magic Context mirror plus delegation plus the review boundary). SDD when selected.
- **Pre-code advice** — mandatory for every non-trivial change ("trivial" keeps its meaning:
  trivial document edits; clearly bounded few-line changes with no contract or security effect).
  Interim lane: the smallest sufficient set of registered advisors, one by default. External
  lane (after plan A is installed): both external advisors (Claude Code and Antigravity) as an
  independent group for every non-trivial change, per the policy table in `WORKFLOW.md`.
- **Post-code review** — an external advisory review of the committed unit against the agreed
  approach (both hosts, once the external lane is active), then `ce:review` where the route owes
  it, then the native RDD review. The external review is evidence, never approval.
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

## Recorded design decisions
- `ce:review` is owed for small and substantial features and for bug fixes, not for global
  tooling, whose route is source change then native review then the verifier mirror.
- The assessment runs after a commit, so it cannot trigger pre-work steps. The impact tier is
  declared up front and recorded in the route line; the assessment grades whether that
  declaration was honest.
- Enforcement of the up-front tier must come from something other than the assessment: write
  targets observed by the guard, against the project's declared surfaces.
- ODD was omitted from the first draft of the class mapping; it is the default spine for
  non-SDD work beyond trivial, not a class of its own.
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

## Memory and inter-agent communication (direction, 2026-10-01)
- **Magic Context is the main memory:** durable project memory and the ODD tracker mirror.
- **Engram is the candidate inter-agent communication channel:** handoffs, evidence references,
  and requests and answers between agents. Adopt it only after the evaluation (queue Q14a) and
  the owner's decision.
- **On adoption:**
  - Engram is added as a canonical MCP in `global-config/opencode.json` and known to the verifier.
    Otherwise every gentle-ai sync adds it, and every verifier run strips it.
  - Engram tools are granted per agent, with first-pass independence preserved.
  - `WORKFLOW.md` states clearly what goes where, with no duplication between the two stores.
  - An Engram message is evidence, never approval.
- **Until then** the current rule stands: ODD work does not invoke `mem_*`.

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
