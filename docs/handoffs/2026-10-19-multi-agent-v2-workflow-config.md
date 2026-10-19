# Handover: multi-agent setup v2, workflow config half

**For:** the OpenCode agents in `workflow_optimisation`.
**From:** Claude Code (advisory review of the owner's v2 brief), 2026-10-19.
**Status:** design handover. Implementation needs the owner's go-ahead.
**Depends on:** the `agent-sandbox-integration` handover
`docs/handoffs/2026-10-19-multi-agent-v2-host-tools-agent-sandbox-integration.md`
(`host_plan_write`, `host_gate_verdict`, `host_task_mark`, the apply deny list, and the Tiny size
guard). Do not enable those tools here before they exist; the verifier would flag them.

## Read first

`WORKFLOW.md`, `docs/TODO.md` Q53-Q61 (the PM layer) and the owner's v2 brief. This is **not a
new track**. It revises the PM layer (Q55-Q61) and absorbs the unmerged planner-tier plan on
branch `docs/pm-planner-delegation` (`9938cd1`). That plan used the number Q67, which collides
with the existing Q67 ("Retired SDD command detector") on `feat/gentle-ai-v4`, so renumber it.

## Revisions to the owner's brief (from the advisory review)

1. **The PM runs the lenses, not Sol.** Each advisor result returned into Sol's context costs
   subscription turns. Gate 1, gate 2 and up to two REFINEs already make 4+ Sol sessions per
   subproject. The PM dispatches the lenses and gives Sol one synthesized findings pack, and Sol
   judges. This serves design goal 1.
2. **The gate tier comes from the native assessment, not from frontmatter.** See host tool 3 in
   the companion handover.
3. **The Tiny escape hatch is enforced by the apply tool, not by Luna's self-report.** See host
   tool 5.
4. **The Tiny route is not "covered by the normal gentle AI review".** Under gentle-ai 4.1.0,
   `review assess` sets `review_due` only for `high` risk, so Tiny and low-risk Small get no
   automatic review. State that plainly, or require one post-code lens on Tiny as well.
5. **Judgment-day is not a native review lens.** Native review is the 4R set (risk, resilience,
   readability, reliability) plus refuter and validator. Keep judgment-day as an optional skill
   for high-stakes work. **OWNER DECISION:** the brief assigns no model to native `risk` and
   `reliability`.
6. **Frontend route independence gap.** With the Kimi worker, post-code Security and
   Performance default to `kimi-k3` (Moonshot), which breaks rule 2, and the brief lists no
   alternative. **OWNER DECISION:** pick one, for example `glm-5.3-flash` or Gemini (where the
   code may be shared).
7. **Scarce pools are oversubscribed.** `grok-4.7` (~845/month) has 5 roles, and `qwen3.8-max`
   (~810) has 6. The 20%-per-5-hours rule allows roughly 165 requests per window, and a lens that
   reads files uses 5-15 requests, not 1-3. Measure from day one (trial metrics) and be ready to
   move roles onto `glm-5.3-flash`, `qwen3.7-plus` or `minimax-m3`.
8. **Policy change to make deliberately:** `PASS` from `host_gate_verdict` turns advice into
   approval, but `WORKFLOW.md` says advice is evidence, never approval. **OWNER DECISION:** rewrite
   that rule for the gated routes, or keep the gate advisory.

## Gap list for this repo

| Change | Files |
|---|---|
| New agents (PM, planner, Tiny/Luna, lens agents per the brief) with models, task permissions and per-agent tool enablement; each custom tool enabled only on its own agent | `global-config/opencode.json` |
| Orchestrator `permission.task`: route to PM and Tiny only; keep `asi-review-*` and `advisor-*` allowed | `global-config/opencode.json` (`gentle-orchestrator`, ~line 466) |
| Guard: new agents in `ROUTE_STAGES` (deny by default), new host tools in the host-tool list | `global-config/plugins/systematic-routing-guard.ts` (:219-224), `global-config/plugins/lib/routing-guard-helpers.ts` |
| Route skills: Tiny/Small/Multistep selection, escape-hatch reroute, the single tick writer | `global-config/skills/workflow-route/`, `workflow-odd-secure/` |
| Recipe: routes, gates and the advice-versus-approval rule | `WORKFLOW.md` |
| Verifier: the new agents exist, their models resolve, tools are enabled only on their agent, and the relay agents mirror their review agent's model and variant. Re-pin the digest. | `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` |
| Queue: revise Q55-Q61, renumber the planner tier | `docs/TODO.md`, `docs/PLAN.md` |

The specialist policy is stated in three places that must agree: the guard's `ROUTE_STAGES`,
the task permissions in `opencode.json`, and the route skills. Change them in one work unit.

## Risks specific to gentle-ai 4.1

- **#5403 restricts the OpenCode orchestrator to Gentle AI subagents.** `gentle-ai sync` will
  strip every new agent from the orchestrator's permissions, and the verifier must restore them
  on each sync. Add a verifier check that fails loudly when they are missing.
- OpenCode permissions now follow the "Pi safety model" (#5273). Confirm by a live run that the
  restored overlay still takes effect.

## Things to verify (from the brief, with what is already known)

1. Model IDs: run `opencode models opencode-go` (or the equivalent) and record the results.
2. Subagent session resume for gate 2: unverified. If unavailable, the plan file is the
   contract, as the brief says.
3. Calling-agent identity: **yes**, `ctx.agent` is available (see the companion handover).
4. The ODD plan lives on disk at `odd/tasks/<feature>.md` and is mirrored to Magic Context. ODD's
   own flow ticks tasks today; route that through `host_task_mark` once it exists.
5. Worker/PM/lens pairings: only the frontend route breaks rules 1-2 (item 6 above). Re-check
   after any model change.
6. Existing advisor and lens definitions: map the `advisor-*-pre` agents and the post lenses to
   the brief's lens list, and propose renames or merges. Nested dispatch of `advisor-*` from a
   subagent is unproven (`opencode run --agent advisor-*` already misbehaves, Q51), so probe it
   before relying on it.
7. Unverified claim: Haiku's price rising 5x above 100K tokens. Confirm before using it as a hard
   PM session limit.

## Trial metrics

Log these from the first run: Sol turns per subproject by route; findings and accepted findings
per lens; gate outcome counts; how often the Tiny guard refuses; Go pool use per model.

## Order

1. `agent-sandbox-integration` builds and tests the host tools.
2. Owner decisions 5, 6 and 8 above, plus the `host_plan_write` approval decision.
3. This repo: queue revision, then config, guard and skills in one work unit, then the verifier.
4. Verifier mirror, owner restart, behavioral probes (including nested advisor dispatch).
