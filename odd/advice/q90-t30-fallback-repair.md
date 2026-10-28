# Q90 T3.0 fallback exact-policy repair — evidence record

Unit `q90-t30-fallback-repair-u1` (2026-10-24), class global tooling change, route
`workflow-odd-secure` delegated cloud `odd-apply`. The owner's explicit THIS-UNIT ceremony
override authorizes one writer with no pre-code advisor, no post-code advisor and no independent
verifier: this is a mechanical verifier-failure repair under a cost directive. The deviation is
recorded here and in the tracker; it is not a simple-docs waiver and not a standing exception.
The Magic Context mirror is UNIMPLEMENTED/not read. This record supplies evidence, not approval,
and the PM owns the commit and assessment. The writer Task/session identity is not exposed to the
worker and is not invented; it belongs to the PM envelope.

## Owner-supplied failure (not independently executed as a full verifier)

```
FALLBACK_EXACT_SOURCE_INACTIVE: opencode-go/mimo-v2.6-flash
FALLBACK_EXACT_SOURCE_INACTIVE: opencode-go/minimax-m3
FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: opencode-go/claude-haiku-5-5; roles=opencode:review-validator,opencode:asi-review-validator
```

## Verified cause in canonical source

- `global-config/opencode.json:1033` (`review-validator`) and `:1394`
  (`asi-review-validator`) assign `opencode-go/claude-haiku-5-5`; those are its only two agent
  assignments. `fallbackModels` had no `opencode-go/claude-haiku-5-5` key.
- `opencode-go/mimo-v2.6-flash` and `opencode-go/minimax-m3` had zero agent assignments. They
  appeared only as provider-catalog model keys (`global-config/opencode.json:2886`, `:2920`)
  and, for `mimo-v2.6-flash`, as five fallback target refs. They remained as `fallbackModels`
  source keys.
- The verifier checks exact policies against active primary assignments
  (`verify-workflow.sh:2731-2735`, `:2771-2777`), never catalog keys or target refs.
  `opencode-go/minimax-m3.1-flash` is a distinct identity with four agent assignments and was
  left untouched.

## Repair

- Deleted the exact source keys `opencode-go/mimo-v2.6-flash` and `opencode-go/minimax-m3`.
- Added `opencode-go/claude-haiku-5-5` with the exact chain and schema of
  `opencode-go/minimax-m3.1-flash`: `deepseek/deepseek-flash` (`max`) then
  `openrouter/deepseek/deepseek-v4.1-flash` (`default`), each with `files`, `tools`, `vision`.
- Preserved all target refs, catalog keys, exclusions and `noFallbackAgents` entries. The config
  diff contains only the two key deletions and the new policy.

## Executed checks on this candidate

- Test-first RED, old policy: `python3 -m unittest tests.test_q90_t30_fallback_repair -v`
  -> 8 tests, 4 failures (the three owner diagnostics plus the accepted-control failure).
- GREEN after repair: same command -> `Ran 8 tests`, `OK`.
- Related modules: `python3 -m unittest tests.test_q90_t30_kimi_removal
  tests.test_model_independence tests.test_model_variants -v` -> 52 tests, `OK`.
- `python3 -m json.tool global-config/rate-limit-fallback.json` -> exit 0.
- `git diff --check` -> clean; `python3 -m py_compile tests/test_q90_t30_fallback_repair.py`
  -> exit 0.
- The focused test also executes the verifier's extracted `effectiveFallbacks` helper through Bun
  for the new Haiku policy (`OK`), and its controls prove the detector accepts a policy-covered
  injected model and rejects both the reintroduced inactive sources and an injected active model
  without an exact policy.

## Limitations

- The full verifier was NOT run; no deploy, restart, consumer, model-availability or runtime
  clearance is claimed.
- AFT/`aft_inspect` could not inspect the candidate after sandbox activation because the broker
  denies unbound host tools; the PM runs host `aft_inspect`.
- The verifier's exact active-model inventory includes derived Astra aliases and profile models;
  the focused test mirrors the canonical agent/inventory assignments including the derived Astra
  alias, but it is not a substitute for the full verifier.
- No native review, approval or review evidence is claimed.
