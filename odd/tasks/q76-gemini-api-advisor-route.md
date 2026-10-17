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
| T1 | S2 S4 S5 S7 | inline | pending | — |
| T2 | S1 S3 | inline | pending | — |
| T3 | S6 | inline | pending | — |

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
