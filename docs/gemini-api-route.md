# Gemini API advisor route

When the Antigravity allowance runs out, the external advisor pair keeps working: Claude Code stays
one half, and the Gemini half runs inside OpenCode on paid Google API credits, a pool separate from
the Antigravity subscription. The rule is `gemini-api-substitute` in `WORKFLOW.md` (external lane).

| Agent | Model | Does |
|---|---|---|
| `advisor-gemini-pre` | `google/gemini-4-argon` | pre-code advice |
| `advisor-gemini-post` | `google/gemini-4-argon` | post-code advisory review |
| `advisor-gemini-evidence` | `google/gemini-3.8-flash` | reads files and runs tests for the two advisors; facts only |

Argon is the expensive model, so it never gathers evidence itself. It has no file, search or shell
tools and answers from the brief. When a fact is missing, it sends at most two bounded gathering
requests to the Flash agent, which reads and runs tests in the usual sandbox-only advisor surface
and returns `path:line` evidence. Most of the reading is therefore billed at Flash rates, and
Argon's input stays close to the brief plus the gathered facts.

## Credential

The key lives in the OpenCode auth store (`~/.local/share/opencode/auth.json`, entry `google`,
type `api`), which OpenCode reads before any environment variable. `verify-workflow.sh` never
touches that file, so regenerating `opencode.json` does not affect it. To set or replace the key,
use OpenChamber **Settings → Providers → Google → API key**, or `opencode auth login` and choose
Google.

No `provider` block is needed in `global-config/opencode.json`: `google` is a Models.dev provider,
so an agent only needs `model: "google/<id>"`. The agents themselves are defined in
`global-config/opencode.json`, which is why the verifier deploys them instead of discarding them.

Keep `GEMINI_API_KEY`. Antigravity's `argon-subagent` script reads it from `~/.gemini/.env`, and the
fish universal variable of the same name is also in use. The `GOOGLE_GENERATIVE_AI_API_KEY` copies
in `~/.config/environment.d/opencode.conf` and in fish are now redundant for OpenCode. Removing them
is optional; if you do, use Fish:

```fish
set -e -U GOOGLE_GENERATIVE_AI_API_KEY
# Delete the GOOGLE_GENERATIVE_AI_API_KEY= line from ~/.config/environment.d/opencode.conf in an editor, then:
systemctl --user unset-environment GOOGLE_GENERATIVE_AI_API_KEY
systemctl --user restart secure-opencode.service
```

Then check that OpenChamber still lists Google as connected and that `opencode models google`
still lists the Gemini models.

## Spend

OpenChamber shows usage for the OpenRouter and DeepSeek keys because those providers publish a
balance endpoint for an API key. As far as we know, the Gemini API offers none: spend is recorded in
Google Cloud Billing, which needs an OAuth login or a service account rather than an API key. So
OpenChamber shows Google as connected but with no usage. Watch spend in
[AI Studio](https://aistudio.google.com/) or set a
[Cloud Billing budget alert](https://cloud.google.com/billing/docs/how-to/budgets).

The fallback plugin never moves these agents to another model (`noFallbackAgents`). An exhausted
credit or a 429 is retried on the same model and then surfaces as an error; it is never silently
answered by a different model family.

## Using it

1. Declare it when opening the session: "Antigravity is out of allowance; use the Gemini API
   substitute." The orchestrator records `selection.rule: gemini-api-substitute`.
2. The orchestrator or PM dispatches `advisor-gemini-pre` (or `advisor-gemini-post`) with the same
   frozen brief the external host would get, and never with Claude Code's answer.
3. Claude Code still supplies the other half of the pair as before.

## Deployment

The change takes effect only after the verifier mirrors it:

1. `bash verify-workflow.sh` (mirror; it asserts the agents' shape and dispatch scope).
2. Restart `secure-opencode.service`, and `ai-proxy.service` for the port-18900 server.
3. `bash verify-workflow.sh` again until it passes.

## Antigravity side

Argon is now also on the Antigravity subscription. There, the same split runs as two custom agents
under `~/.gemini/config/agents/<name>/agent.md`: `argon_advisor` (Argon) and `evidence_collector`
(Flash). Both are delivered by the change set in `changesets/q76-antigravity-agents/`. That change
set also moves the API-credit `argon-subagent` skill's trigger to "use Argon API", so a plain "use
Argon" no longer spends credits the subscription now covers.

Launch the advisor with the model named explicitly:

```fish
agy --agent argon_advisor --model gemini-4-argon-medium
```

What testing on 2026-10-17 established (`agy` CLI):

- Agent frontmatter `model` accepts only the tiers `flash`, `pro` and `inherit`. A full slug such
  as `gemini-3.8-flash-medium` makes Antigravity drop the agent silently, so it never loads
  (`agy plugin validate` counts 0 agents). This is why the advisor gets its model from `--model`.
- `invoke_subagent` passes its own `Model` value, which overrides the subagent's frontmatter. The
  advisor's prompt therefore requires `Model: flash`. With `inherit`, the gatherer ran on Argon.
- As a main agent, `argon_advisor` is still offered the full default toolset. Its `tools:` list
  and `excludeDefaultComponents` do not narrow it, so "Argon never reads or runs anything itself"
  is enforced by its prompt, not by Antigravity. A live run made exactly one call,
  `invoke_subagent`.
- `agy agents` lists main agents only, so `evidence_collector` does not appear there.

Revert with `python3 scripts/changeset.py revert --journal <journal> --journal-root
backups/changesets --allow-root ~/.gemini/config/agents --allow-root
~/.gemini/antigravity/skills/argon-subagent`. The journal path is printed by `apply`. The empty
`~/.gemini/config/agents/argon_advisor/` folder is left behind, because the change set does not
create or remove folders.
