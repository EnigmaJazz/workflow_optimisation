# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The source of truth for the owner's **global** OpenCode workflow setup (Gentle AI + Systematic +
the sandbox stack). Nothing here is an application: it holds the routing recipe, the canonical
copy of the global OpenCode config, the plugins that enforce the recipe, and the verifier that
deploys and self-heals all of it. Changes here take effect in every project on the machine.

## Claude Code's role here

- **Advisory by default (owner, 2026-10-02).** The OpenCode agents implement; Claude Code gives
  pre-code advice and post-code advisory review. Implement only when the owner asks for it
  explicitly.
- `WORKFLOW.md` is written for the OpenCode `gentle-orchestrator` (read-only, delegates every
  mutation to sandbox workers). Its tool names (`sandbox_*`, `host_*`, `ctx_*`, `asi-review-*`)
  do not exist in Claude Code. Read it to understand the rules being enforced, not as
  instructions for this runtime.
- Memory: OpenCode uses Magic Context; Claude Code cannot reach it and uses Engram only.
- Advice is evidence, never approval. Native gentle-ai review always runs on the in-OpenCode
  `asi-review-*` lanes; never offer Claude Code as a review lens.

## Commands

```bash
# Routing guard tests (bun). The throwaway HOME is required: the suite refuses a real HOME.
HOME="$(mktemp -d)" bun test tests/routing-guard
HOME="$(mktemp -d)" bun test tests/routing-guard -t "<test name pattern>"

# Python tests (change-set tool, plugin cache integrity)
python3 -m unittest discover -s tests
python3 -m unittest tests/test_changeset.py -v
python3 -m unittest tests.test_changeset.<Class>.<test_name>

# Verifier: health check + self-heal + deploy mirror. MUTATES ~/.config/opencode.
bash verify-workflow.sh                        # full run (includes paid runtime probes)
bash verify-workflow.sh --recover-config-only  # restore config overlays only, no probes
bash verify-workflow.sh --behavioral           # adds Task fan-out and read-only probes
WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY=1 bash verify-workflow.sh   # only load-check the plugins
```

The owner's interactive shell is Fish: commands suggested to the owner must be Fish-compatible
(no heredocs, no `$(...)`-style Bash-only syntax outside `bash -c`).

## Architecture

**Source → review → mirror.** `global-config/` is the canonical copy of what lives in
`~/.config/opencode` (`opencode.json`, `tui.json`, `AGENTS.md`, `systematic.jsonc`,
`rate-limit-fallback.json`, `plugins/`, `skills/`). The live directory is never edited in place:
`verify-workflow.sh` regenerates it from `global-config/`, after a timestamped backup under
`backups/`. `gentle-ai sync` and plugin auto-updates overwrite the live files; the verifier
restores the user-owned overlays while preserving safe newer plugin version pins.

**`verify-workflow.sh`** (~4,900 lines, one file; its header comment is the index of every
check). Path overrides are `WORKFLOW_VERIFY_*` environment variables, which is how to point it at
fixtures. It spawns short-lived `opencode run` probes with `WORKFLOW_HEALTH_CHECK_PROBE=1`;
plugins must stay inert under that flag.

**Digest pin (do not skip).** `global-config/plugins/workflow-health-check.ts` pins the sha256
of `verify-workflow.sh` in `VERIFY_SCRIPT_SHA256` and refuses to run a mismatched script. Any
edit to the verifier, including comment or heredoc text, requires updating the pin in the same
change, then a verifier run to re-mirror the plugin. See `WORKFLOW.md` "Health-check plugin
lifecycle".

**Routing guard** (`global-config/plugins/systematic-routing-guard.ts`, design in
`docs/specs/routing-guard-q03.md`). Warning-only apart from one generic-task block. It records
per-session state under `~/.local/share/opencode/routing-keys/<session>/`: workflow keys minted
by loading a `workflow-*` skill (30 min inactivity TTL, inherited across up to three ancestor
sessions), and route-namespaced stage markers (`artifact-<route>-<stage>`, `skill-<name>`).
`ROUTE_STAGES` declares each route's stages and which writing specialists a stage unlocks
(deny by default). `SYSTEMATIC_ROUTING_GUARD_STATE_ROOT` relocates all of that state and exists
for tests only. Where the spec and the tests disagree, the tests win.

**Route skills** (`global-config/skills/workflow-*`): `workflow-route` is loaded for every task
and selects `workflow-odd-secure`, `workflow-systematic` or `workflow-sdd-secure`. The specialist
policy is therefore stated in three places that must agree: the guard's `ROUTE_STAGES`, the task
permissions in `opencode.json`, and these skills.

**Change-set tool** (`scripts/changeset.py`, spec `docs/specs/changeset-tool.md`). Applies and
reverts declarative edits to files git cannot reach (`~/.claude/CLAUDE.md`, gentle-ai-managed
blocks, other projects' plugins) with compare-and-swap writes, a journal, and a revert that
reports drift instead of overwriting it. It is the mechanism for the gentle-ai v4 and OpenCode V2
upgrades.

**Deployment is not complete at commit.** A source change takes effect only after: verifier run
(mirror) → owner restarts OpenCode (`secure-opencode.service`, and `ai-proxy.service` for the
port-18900 server) → verifier passes. Restarts are the owner's action.

## Tracking documents

| File | Holds |
|---|---|
| `WORKFLOW.md` | The routing recipe: task classes, ODD/SDD, advice mandate, review rules |
| `docs/TODO.md` | The ordered queue. Q-numbers are stable IDs; the Phases block is the order |
| `docs/PLAN.md` | Objective, sequence, constraints and recorded design decisions |
| `docs/TODO-HISTORY.md` | Dated reasoning and retired item bodies |
| `odd/tasks/<feature>.md` | One tracker per substantial feature, with task evidence and advice records |
| `ROUTER-LOG.md` | One row per routed task and review outcome |
| `CLAIM-RETRACTIONS.md` | One row per claim an agent had to retract |
| `docs/advisor/` | Contract shared with agent-sandbox-integration. Do not sync over it |

Every planned work unit must appear in `docs/TODO.md` once, with its prerequisites; work that
exists only in a plan or tracker is a defect in that file.

## Rules specific to this repository

- **Contract drift is worse than a missed rule.** The gates are derived from `WORKFLOW.md` and
  the specs. Re-read the current file before advising or acting; never work from a remembered
  version of a contract.
- **Verification must execute.** A build, parse or lint pass proves syntax only (the guard once
  built cleanly and failed to load for hours). A plugin change must load, a shell change must
  run, a config change must be read by its consumer. Otherwise report it as UNVERIFIED.
- **Tests first for behaviour changes, with no vacuous passes.** An absence assertion needs a
  positive control proving the probe can detect the thing.
- **Forward-compatible by default** (`docs/PLAN.md` Constraints): no new dependency on SDD,
  `host_sdd_*`, `strict_tdd` or V1-only plugin hooks; plugins dual-mode; version-neutral
  headings; verifier checks anchored on stable markers, not prose.
- **Upgrades are non-destructive**: delivered through the change-set tool, revertible without
  overwriting drift, on branches stacked `main` → gentle-ai v4 → OpenCode V2.
- **Commits**: Conventional Commits; routed work carries the suffix
  `— ROUTED: <class>@<checkpoint> (<date>)`, and most work here is class
  `global-tooling-change`. Work units stay under about 400 authored changed lines.
- **Native review** takes one work-unit commit as its candidate, assessed with
  `--base-ref <last reviewed boundary> --committed-only`. A whole-branch candidate is refused
  with `lens_context_budget_exceeded`.
- **Advice is mandatory for every non-trivial change**, from the `advisor-*` subagents,
  dispatched from the OpenCode TUI. `opencode run --agent advisor-*` silently falls back to the
  primary agent (queue Q51).
- `backups/`, `.atl/` and `.sandbox-state/` are generated and ignored.
