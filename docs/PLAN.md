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
2. Guard fixes (R2-001 first, with automated assertions for the stage table and gates). Subject to
   the advice mandate; they need the verifier mirror and a restart to take effect.
3. Split `verify-workflow.sh`, before the external lane adds verifier checks.
4. Workflow policy: classes, ODD/SDD/advisor layers, the impact axis (how much advice), and the
   per-project impact-surface declaration.
5. External advisor lane: activate after agent-sandbox-integration plan A is installed (B3), then
   the routing-guard advice stage (B4) and the advisor handoff document (B5).
6. Tracking contract in the recipe.
7. Reconcile drift and close the gaps found by the options inventory; emergency fix route;
   worker contract; Engram evaluation (report only); remaining routing-guard stage work.

## Layers
- **Execution spine** — tiny fix: direct. Everything beyond trivial and not SDD: **ODD** (tracker
  plus Magic Context mirror plus delegation plus the review boundary). SDD when selected.
- **Pre-code advice** — mandatory for every non-trivial change ("trivial" keeps its meaning:
  trivial document edits; clearly bounded few-line changes with no contract or security effect).
  Interim lane: the smallest sufficient set of registered advisors, one by default. External
  lane (after plan A is installed): an external advisor chosen by the policy table in
  `WORKFLOW.md`.
- **Post-code review** — focused review of the agreed approach, then the native RDD review.
- **Impact axis** — decides HOW MUCH advice (the number of advisors, whether a cross-family group
  is needed, whether an external review lineage is used); still raises scrutiny and never lowers
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

## 11. Split `verify-workflow.sh` into smaller files
`verify-workflow.sh` is 4,770 lines — the file that cannot be whole-body edited, that times out on
reads, and that made every one of today's repair cycles expensive. Split it.

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
