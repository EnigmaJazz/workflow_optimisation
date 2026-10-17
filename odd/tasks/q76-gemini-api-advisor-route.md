# Q76 — Gemini API advisor route (Antigravity substitute) and Antigravity Argon/Flash split

**Branch:** `feat/gemini-api-advisor-route` (stacked on `chore/pm-layer-completion`). **Class:** global-tooling-change.
**Delivery:** ask-on-risk. **Runners:** `python3 -m unittest discover -s tests`; `HOME="$(mktemp -d)" bun test tests/routing-guard`.
**Implementer:** Claude Code, at the owner's explicit request (2026-10-17). Plan: owner-approved plan of 2026-10-17.

## Specs

- **S1** In-OpenCode Gemini advisors replace Antigravity's half of the external pair when the owner
  declares the Antigravity allowance exhausted: "a second route to the 'external' route to the gemini
  models once the antigravity usage expires (it uses a different usage pool)".
- **S2** Argon advises and does not gather evidence; Gemini 3.8 Flash gathers: "Argon 4 is the model
  to give the advice however this will be expensive if having to gather evidence so could we make a
  subagent with gemini 3.8 flash that has access to these tools and give the actual advisor only
  access to delegate this subagent".
  - `advisor-gemini-pre`, `advisor-gemini-post`: `google/gemini-4-argon`; every tool denied; the only
    task target is `advisor-gemini-evidence`.
  - `advisor-gemini-evidence`: `google/gemini-3.8-flash`; the shared advisor tool block (sandbox
    reads, sandbox test runs, every route to the host denied); `task` deny-all.
- **S3** The credential stays in the OpenCode auth store (`google`, `type: api`). `GEMINI_API_KEY`
  stays, because Antigravity needs it ("GEMINI_API_KEY is needed by antigravity").
- **S4** None of the three agents falls back to another model: all are in `noFallbackAgents`.
  `google` becomes a start provider with an emergency rule, which the verifier requires for any
  active provider.
- **S5** The orchestrator, `pm-odd` and `pm-systematic` may dispatch the two advisors, never the
  evidence agent.
- **S6** Antigravity: "argon should be used directly in antigravity, this should be giving the advice
  but gemini 3.8 flash should be gathering the information".
  - Custom agents `argon_advisor` (Argon) and `evidence_collector` (Flash) under
    `~/.gemini/config/agents/`, delivered through `scripts/changeset.py`.
  - The `argon-subagent` API skill keeps working, but its trigger becomes "use Argon API".
- **S7** The verifier and a committed test assert S2, S4 and S5, each with a positive control.
- **Out of scope:** OpenChamber usage display for Google. Google exposes no balance API for a key,
  so it is not fixable here.

## Tasks

| ID | Specs | Route | Status | Evidence |
|---|---|---|---|---|
| T1 | S2 S4 S5 S7 | inline | done | `bdeaf1f`; RED 14/14 failing, then GREEN 14/14; full suite 169/169; guard 103/103; review assess **high**, review due, pending on `asi-review-*` |
| T2 | S1 S3 | inline | done | `WORKFLOW.md` rule `gemini-api-substitute`, advisor table, `docs/gemini-api-route.md`, TODO Q76, router row (commit in this unit) |
| T3 | S6 | inline | done (one item UNVERIFIED) | change set applied; live `agy` run delegated with `Model: flash`; which model served the gatherer is not recorded anywhere |

- **T1:** the agents in `global-config/opencode.json`, the fallback policy, the verifier check plus
  digest re-pin, and `tests/test_gemini_advisor_route.py`.
- **T2:** the `WORKFLOW.md` external-lane rule and advisor table, `docs/gemini-api-route.md`, the
  `docs/TODO.md` Q76 entry, and the router-log row.
- **T3:** the Antigravity change set: two agent files and the skill trigger.

## Log

- **L1 (2026-10-17, owner, verbatim):** "I have worked out I can directly use api credits for Google
  in opencode and have managed to set it up using an environmental variable and I would like to see
  this as a second route to the "external" route to the gemini models once the antigravity usage
  expires (it uses a different usage pool) however if setting by environmental variables it is not
  set as a provider in the json (and would be overwritten by verify-workflow.sh anyway), so it can't
  be set up as a subagent, and the usage is not shown in openchamber as a side effect."
- **L2 (2026-10-17, owner corrections during planning):**
  - Advisors' sandbox write tools are intentional, for running tests; finish and apply are denied.
  - OpenRouter and DeepSeek usage does show in OpenChamber with API keys.
  - Argon is now on the Antigravity subscription.
  - Owner: "Implement yourself".
- **L3 Advice gate:** pre-code advice from the `advisor-*` lanes (mandatory per `WORKFLOW.md`) can
  only be dispatched from the OpenCode TUI, which Claude Code cannot reach. The plan was reviewed
  interactively with the owner instead. Advice is recorded as **pending owner dispatch**; it is not
  claimed as done.
- **L4 T1 evidence (2026-10-17):**
  - Both JSON sources round-trip byte-identically through `json.dumps(indent=2, ensure_ascii=False)`,
    so the edit was a load/edit/dump. The diff contains only the added members.
  - The verifier requires every active provider to be a start provider with an emergency rule
    (`FALLBACK_ACTIVE_PROVIDER_NOT_STARTER`, `FALLBACK_ACTIVE_PROVIDER_NO_EMERGENCY_RULE`). So
    `google` was added with the rule openrouter `~google/gemini-flash-latest`, then openai
    `gpt-6-luna`. That rule never applies to the three agents: `noFallbackAgents` gives them no
    chain (plugin `CLAUDE.md`, `startCycle`).
  - Five task maps would otherwise reach the gatherer and now deny it explicitly:
    `gentle-orchestrator` and `frontend-dev-premium` (`*: ask`), and `frontend-apply`,
    `frontend-apply-local`, `frontend-dev` (no `*`).
  - **Advisory (pre-existing, not changed):** `jd-fix-agent` and `vision` expose the task tool with
    no target map, so they could dispatch any subagent, the existing advisors included.
- **L5 T3 evidence (2026-10-17):**
  - Agent frontmatter `model` accepts only `flash`, `pro` and `inherit`. A full slug drops the agent
    silently; bisected with `agy plugin validate` (agents 0 vs 1).
  - `agy agents` lists main agents only, and `--agent <unknown>` names the available ones.
  - `invoke_subagent` `Model: inherit` overrode `model: flash`: the first live run resolved only
    `gemini-4-argon-medium`. The prompt now requires `Model: flash`, and the second run sent it.
  - The main agent is still offered the full default toolset. Tool narrowing for Argon is
    therefore prompt-enforced: both runs made exactly one call, `invoke_subagent`.
  - The change set was reverted and re-applied cleanly twice (4 ops each way).
- **L6 Native review (owner, 2026-10-17):**
  - The Claude Code stop hook offered a START over the whole-branch candidate
    (`base-ref 62496d51`, 25 commits).
  - Owner chose "OpenCode lanes": no START was run from Claude Code.
  - Native review runs on the `asi-review-*` lanes, one work-unit commit at a time, starting with
    `bdeaf1f` (assess: high, review due).
