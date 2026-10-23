# Q90 T3a1 — orchestrator fixed-tool grants

Unit `q90-t3a1-orchestrator-tools-u1`; class global-tooling-change; route
`workflow-odd-secure`, delegated cloud `odd-apply`; no push, PR, deployment,
native review or restart.
Baseline: sandbox `/work`, branch `work`, HEAD
`3784858f4011111b8d520f66910fc6c9462a6ed5` (synthetic, parent host
`2f196b6a88cdab53062c95c99ec3ba8fc55ae4e0`); pre-existing untracked bundle
excluded. Tracker `odd/tasks/multi-agent-v2-queue.md` exists at 150 lines.

## Owner scope
Global `host_test_run: deny`; orchestrator `host_test_run: allow` and
`host_plan_write: ask`; no tools-map keys; preserve PM `host_plan_write: ask`
and all other actor/task/model surfaces (T3a2-d excluded). Overlay: ask-gated
plan drafting (plan documents only, never code/config); allow-gated narrowly
pre-registered tests (never arbitrary caller argv, pipes, redirects or shell);
fixed exceptions grant no generic shell/edit authority; failure never widens
permission; `host_test_run` inert until the host tool ships. Reconcile blanket
"tests always delegated" wording with only that narrow exception. Regenerate the
embedded prompt from the assembler; repin prompt digest, ledger and verifier pin.

## Pre-code advice (observed; evidence only, not approval)
- `advisor-security-pre` `ses_e957e891bffeVQZBnoMD7HKtyq`
  (`openai/gpt-6.1-sol`): reject unauthorized `ask` as well as `allow` outside
  the orchestrator; qualify blanket execution claims and test assembled
  sentences; inert config proves no external enforcement; preserve PM asks.
- `advisor-integration-pre` `ses_e957e890effeymwKzrfR3yBr7m`
  (`kimi-k2.7-code`): separate the allow check from the `gatedHostMutations`
  ask loop; update prompt/hash/ledger/pin together; no tools keys. Its
  deny-PM-plan-write suggestion is rejected as contrary to scope and Q89.
- Source mapper `ses_e957e8914ffen1pBfYADVJ8XAE`: `.codegraph` unindexed, AFT
  fallback; config `:2539-2542`, orchestrator `:467-599`, Q59 `:2787-3466`,
  overlay `:16-27`/`:208-214`, test constant `:30`, predicate tests
  `tests/test_review_pipeline_permissions.py:481-645` and JS.
