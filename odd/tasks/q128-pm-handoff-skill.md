# Q128 — `pm-handoff` and every prompt-named skill must resolve from any repo

**Task ID:** q128-pm-handoff-skill (stable)
**Branch:** `chore/q128-pm-handoff-skill`
**Task class:** Global tooling change (normative contract + prompts + verifier + derive)
**Route:** delegated (direct bounded `general` writer per slice)

## Objective

Any PM or orchestrator prompt that names a handover or a skill resolves it from ANY repository, not
only from this checkout.

## Result

| Task | Status | Evidence |
|---|---|---|
| T1 C4 anchor mechanism | DONE (commit `5f618c0`) | `docs/specs/pm-handoff.md` five sites + both PM prompts use `host_git_head` (`branch`, `detached`, `head`); linked worktree supported; detached/mismatch/unresolvable/error/unavailable BLOCKED. `tests.test_pm_handoff_spec`, `tests.test_pm_layer_prompts` 52 OK. Re-pin of `NONPROMPT_CONFIG_SHA256` in `b48d9a7`. |
| T2 C5 merged-config readback | DONE (`cf17e4f`, file `tests/test_pm_git_head_grants.py`) | Real `derive_config` + `add_v2_astra_aliases` over `global-config/opencode.json`: both PMs keep `tools.host_git_head: true` and `permission: "allow"`, global `deny`; no PM `-astra` alias exists today because the alias rule is Sol-only; a synthetic Sol PM does get an alias that keeps the grant. 5 tests, negative controls for removed permission, false tool, global allow, dropped alias grant. |
| T3 C6 `pm-handoff` skill | DONE (`cf17e4f`, wording `f764b16`) | `global-config/skills/pm-handoff/SKILL.md` = frontmatter + `docs/specs/pm-handoff.md` byte for byte, pinned by `tests/test_pm_handoff_skill.py` with a drift control; PM prompts and the orchestrator PM-brief section name the skill and keep the in-repo path literal; `verify/31` mirrors the fourth skill; manifest + plugin pin regenerated. |
| T3b orchestrator prompt precision | DONE (`cf17e4f` content, `fb0c055` test literal) | The PM-brief section no longer claims `read`-only observation and names the skill; embedded prompt = assembler output (sha256 `ef3e750a…`, 62,734 bytes). |
| T4 Q116 V2 delivery | DONE in the working tree, NOT committed | `derive-v2-config.py` carries `work-unit-commits` and `chained-pr` from the live V1 root into the V2 skills root (materialising symlinks) and REFUSES derivation when a required skill is absent from both; `verify/21-opencode-major.sh` points `SKILLS_DIR` at `$V2_CONFIG_ROOT/skills` in V2 mode (explicit override wins). `tests.test_derive_v2_config` 76 OK, `tests.test_verifier_v2_mode` OK. |
| T5 referenced-skill verifier check | DONE in the working tree, NOT committed | `verify/checkers/check-prompt-references.py` resolves six prompt-named skills from the installed skills root while `os.chdir`-ed into a foreign temp repository, refuses when that repository is this one, and reports cwd; `verify/55b-section-3b-prompt-references.sh` fails when the skills root is absent and runs a required-failure probe. `tests.test_prompt_references` 9 OK. |
| T6 record | DONE (`0a2f439`) | `docs/TODO.md` Q128, Q102 C4-C6 and Q116 carry the delivered state and the owner action. |

## Commits

`c6327fa` (r1 tracker) · `5f618c0` C4 mechanism · `b48d9a7` non-prompt digest re-pin ·
`cf17e4f` skill + prompts + mirror + manifest · `fb0c055` orchestrator prompt literal ·
`0a2f439` TODO · `f764b16` mirror wording.

Commit note: `cf17e4f` also carries the four T3b corrections, because `host_git_commit` stages from
the working tree at commit time; `fb0c055` then carries only the one-file test literal. Content is
correct and the tree is green; the message split is slightly imprecise.

## Owner commit required (environment constraint)

`scripts/**` is an apply-protected security path (`broker/src/config.ts` `DEFAULT_PROTECTED_SECURITY_FILES`),
so `sandbox_apply` refuses any result that touches `scripts/derive-v2-config.py`, and
`host_git_commit` cannot commit a result that was never applied. These nine paths are therefore
installed in the working tree and uncommitted, and must be committed together (their digests are
mutually bound):

```
scripts/derive-v2-config.py
verify/21-opencode-major.sh
verify/checkers/check-prompt-references.py
verify/55b-section-3b-prompt-references.sh
tests/test_derive_v2_config.py
tests/test_verifier_v2_mode.py
tests/test_prompt_references.py
verify-workflow.sh
global-config/plugins/workflow-health-check.ts
```

Suggested message: `feat(verify): deliver the ODD skills to the V2 root and check prompt references`.

## Checks observed

- `tests.test_pm_handoff_skill` 3 OK; `tests.test_pm_handoff_spec` + `tests.test_pm_layer_prompts` 52 OK;
  `tests.test_orchestrator_prompt_source` 44 OK; `tests.test_pm_git_head_grants` 5 OK;
  `tests.test_prompt_references` 9 OK; `tests.test_derive_v2_config` 76 OK (9 skipped);
  `tests.test_verifier_v2_mode` + `_v2_config` + `_v2_sections` 97 OK (19 skipped).
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are current` (working tree).
- `bash -n verify-workflow.sh` and `bash -n verify/55b-section-3b-prompt-references.sh` clean.
- Probe: `check-prompt-references.py /tmp <v2 skills> --probe q128-deliberately-unresolvable` prints
  `error` naming the probe (the in-verifier positive control).
- Full discovery: `Ran 913 tests`, `FAILED (failures=18, errors=18, skipped=56)`. All 36 are in
  modules untouched by this unit (`test_opencode_v2_db_swap` and `test_opencode_v2_preflight`:
  `sqlite3` CLI absent / `/nonexistent`; `test_codegraph_ensure`: `/nonexistent`;
  `test_verifier_split.Manifest.test_checkers_are_valid_scripts`: `node` execution denied;
  `test_cli_config_mirror.Prune` ×3: fixture `AttributeError`, not re-run against the base).
  The run before this unit had 37 failures; the fixed one is
  `test_orchestrator_prompt_source…test_nonprompt_config_tree_matches_the_pinned_digest`.

## Reviewability receipts

| Unit | authored_changed_lines | authored_patch_bytes |
|---|---|---|
| T1 (`5f618c0`) | 36 | 36,561 |
| T1 re-pin (`b48d9a7`) | 2 | ~small |
| T3 (`cf17e4f`, 11 files) | ~297 (282 ins / 15 del) | ~36 KiB, dominated by the 29,537-byte mirror |
| T3b (`fb0c055`) | 10 | 6,684 |
| T6 (`0a2f439`) | 8 | small |
| T4/T5 working tree | 99 + 23 + 85 + 86 + 83 + 2 | not captured by the workers |

## Advice gap (recorded, unchanged)

The registered `advisor-*-pre`/`-post` agents are not materialized in this runtime's subagent
catalog, so no pre-code or post-code advisory phase ran. No advisor opinion exists for this unit and
none is claimed. Compensating control: test-first slices plus one independent
`gentle-ai-verify` pass on the final candidate.

## Independent verifier (post-code) and dispositions

Verdict `REFINE`; one correction round used (`correction_rounds_used: 1`).

- **V1 skill not byte-identical** — rejected as a misreading (a skill needs frontmatter) but the
  wording was tightened in both files (`f764b16`).
- **V2 the check did not prove cross-repository resolution** — ACCEPTED: the checker now
  `os.chdir`s into the foreign repository, resolves the skills root to an absolute path first, and
  reports the process cwd; tests assert both.
- **V3 derive failed open on a missing required skill** — ACCEPTED: it now raises `DeriveError` naming
  the skill, both paths and the remedy.
- **V4 an absent skills root skipped the check** — ACCEPTED: it now fails with
  `PROMPT_REFERENCE_SKILLS_ROOT_MISSING`.

## Residual gaps

1. Live deployment unverified: the V2 root does not yet contain `pm-handoff`, `work-unit-commits` or
   `chained-pr`. The owner must run `python3 scripts/derive-v2-config.py --source global-config
   --sandbox-repo /home/james/agent-sandbox-integration --target ~/.local/share/opencode-v2/config/opencode`
   (dry run, then `--apply`). Until then the V2 verifier reports `V2_CONFIG_ROOT_DRIFT` and
   `GENTLE_AI_V4_ODD_SKILL_MISSING`, which is the intended signal, not a regression.
2. No live cross-repository skill load was executed: no second registered repository and no shell were
   available to this session.
3. Native review was deliberately not run (owner instruction). RDD is on (`global`, via
   `host_review_mode_status`), so every commit above is an unassessed RDD candidate awaiting the
   orchestrator's assessment.
4. Untracked `ses_*.bundle` transport artifacts remain at the repo root (one per applied sandbox
   session). They block an untracked-inventory declaration for native review and should be removed by
   the owner (`rm ses_*.bundle`).

## Next step

Owner: commit the nine uncommitted paths as one unit, then run the derive dry run and `--apply`, then
the verifier. Orchestrator: assess the committed candidates for native review per RDD.


## Revisions
- r1 2026-11-08T19:02:03Z gentle-orchestrator: Create the Q128 tracker before the first source edit.
- r2 2026-11-08T23:20:48Z gentle-orchestrator: Record delivered slices, the accepted verifier findings, and the owner commit/deploy actions.
