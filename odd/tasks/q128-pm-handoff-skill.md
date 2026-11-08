# Q128 — `pm-handoff` and every prompt-named skill must resolve from any repo

**Task ID:** q128-pm-handoff-skill (stable)
**Branch:** `chore/q128-pm-handoff-skill` (from `main` 2c591b0)
**Task class:** Global tooling change (normative contract + prompts + verifier + derive)
**Route:** delegated (direct bounded `general` writer; PM layer structurally blocked — see Constraints)

## Objective

Any PM or orchestrator prompt that names a handover or a skill resolves it from ANY repository, not
only from this checkout. Today a `pm-odd` session in a worktree read
`docs/specs/pm-handoff.md`, got "file not found", and lost the contract.

## Problem (observed evidence)

- `docs/TODO.md:2500` (Q128): "`pm-odd` read `docs/specs/pm-handoff.md` in the worktree and got 'file
  not found'". `docs/TODO.md:2279(c)` records the same failure as the Q127 finding.
- `docs/TODO.md:2304` (Q102 C4/C5/C6): the `host_git_head` broker half is merged on
  `agent-sandbox-integration` master (observed: `broker/src/service.ts:4448-4482` returns
  `{ branch: string|null, detached: boolean, head: string }`; `opencode/plugins/lib/tool-specs-host-ops.ts:113`
  registers the tool). Remaining there: C4 migrate the PM anchor off `.git/HEAD`, C5 explicit grants
  with a merged-config readback, C6 ship `pm-handoff.md` as a global skill.
- C5 grants already landed in this repo (`global-config/opencode.json:2411,2489,2554,2641` `true`/`allow`;
  global `:2859` `deny`). The readback is what is missing: nothing asserts the *derived V2* merged
  config keeps them, and nothing pins the `-astra` aliases.
- `docs/TODO.md:2562-2570` (Q116): `GENTLE_AI_V4_ODD_SKILL_MISSING` fires for `work-unit-commits` and
  `chained-pr` when the skills path is the V2 root. Observed: the live V2 root
  (`~/.local/share/opencode-v2/config/opencode/skills/`) contains only `workflow-route`,
  `workflow-odd-secure`, `workflow-systematic`; `global-config/skills/` contains the same three, so
  derive copies neither ODD delivery skill. The V1 tree is not readable from a secure session
  (os error 13 on `~/.config/opencode/skills/*/SKILL.md`), so the content can only be carried at
  deploy time, never re-authored into the repo.
- The verifier never inspects the V2 skills root: `verify/10-env.sh:37` sets
  `SKILLS_DIR=$OPENCODE_CONFIG_DIR/skills` and V2 mode (`verify/21-opencode-major.sh:27-40`) redirects
  only `AGENTS_FILE` and `RUNTIME_CONFIG_FILE`. `tests/test_verifier_v2_mode.py:102` pins that
  V2 keeps the V1 skills path, so the check that matters is skipped by construction.

## Risk line

Risk: item 2 (grants on a contract others consume) and item 3 (prompts and contracts others consume)
and item 5 (verifier digest). Item 3 is the widest surface: `docs/specs/pm-handoff.md` is consumed by
`WORKFLOW.md`, `roles/tier-5.md`, the orchestrator overlay, the two PM prompts, and three test files.

## Scope

In scope:

1. C6/Q128 — ship `pm-handoff` as a global skill under `global-config/skills/pm-handoff/SKILL.md`, so
   `derive-v2-config.py` (which copies `global-config/skills`) delivers it to the V2 skills root and
   the reviewed-skill mirror delivers it to V1. Body is a byte-identical mirror of
   `docs/specs/pm-handoff.md`; the spec stays the normative in-repo source. A test pins the mirror.
2. C4 — migrate the `unit_start_anchor` mechanism in `docs/specs/pm-handoff.md` and both PM prompts
   from reading `.git/HEAD` / `.git/refs/heads/<branch>` to the read-only `host_git_head` tool.
3. C5 — merged-config readback: a test proves the *derived* V2 config keeps `host_git_head`
   (`tools: true`, `permission: allow`) for `pm-odd`, `pm-systematic`, and both `-astra` aliases,
   with the global rule `deny`.
4. Q116 — deliver `work-unit-commits` and `chained-pr` to the V2 skills root and point the verifier's
   V2 skills check at that root.
5. A verifier check that a referenced handover/skill resolves from a repository other than this one,
   with an in-verifier positive control that makes a deliberately unresolvable reference fail.

Non-goals: native review, merge, `derive --apply`, service restarts, the live `--behavioral` verifier,
and any change to `scripts/verifier_manifest.py` itself.

## Tasks

### T1 — C4 mechanism migration (normative contract + PM prompts)

Acceptance criteria:

- `docs/specs/pm-handoff.md` names the read-only `host_git_head` host tool and its result shape
  (`branch`, `detached`, `head`) as the unit-start branch/HEAD mechanism at all five sites
  (brief field ~:7, route validation ~:74, ordered step ~:78, anchor paragraph ~:87, envelope
  `method` ~:171). No `.git/HEAD` or `.git/refs/heads/<branch>` mechanism reference remains in the
  anchor contract.
- The PASS condition compares `branch` with the brief's `feature_branch` exactly and requires a
  40-hex `head`; a linked worktree is explicitly NOT a blocker (the tool supports it); `branch: null`,
  a different branch, an unresolvable HEAD (unborn branch, rebase/merge in progress), a tool error,
  truncation, or an unavailable tool each return `BLOCKED`.
- Both PM prompts in `global-config/opencode.json` name `host_git_head`; no prompt reads
  `.git/refs/heads/<feature_branch>`; each prompt stays under the 6,000-character cap
  (`tests/test_pm_layer_prompts.py:272-279`).
- `tests/test_pm_handoff_spec.py` and `tests/test_pm_layer_prompts.py` assert the new mechanism and
  keep a positive control proving a missing `host_git_head` mention fails.

### T2 — C5 merged-config readback

Acceptance criteria:

- A new test loads the real `global-config/opencode.json`, runs the real `derive_config` and
  `add_v2_astra_aliases` from `scripts/derive-v2-config.py`, and asserts for `pm-odd`,
  `pm-systematic`, `pm-odd-astra`, `pm-systematic-astra`: `tools.host_git_head is True` and
  `permission.host_git_head == "allow"`; and for the top-level `permission`: `"deny"`.
- Negative control: removing the grant from one agent makes the check report it.

### T3 — C6 `pm-handoff` global skill

Acceptance criteria:

- `global-config/skills/pm-handoff/SKILL.md` exists with valid frontmatter (`name: pm-handoff`, a
  one-line `description:`), and its bytes are exactly the frontmatter block plus
  `docs/specs/pm-handoff.md` verbatim.
- A test pins that mirror equality and proves drift fails (positive control).
- `verify/31-recover-skills-agents.sh` mirrors the fourth skill to V1 (manifest entry + wording), and
  the PM/orchestrator prompts name the `pm-handoff` skill while keeping the literal
  `docs/specs/pm-handoff.md` pointer the existing pins require.
- Editing `global-config/prompts/gentle-orchestrator/overlay.md` regenerates the embedded orchestrator
  prompt with `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py` and updates
  `CURRENT_PROMPT_SHA256` and the normative-ledger citation.

### T4 — Q116 ODD delivery skills in the V2 root

Acceptance criteria:

- `scripts/derive-v2-config.py` delivers `work-unit-commits` and `chained-pr` to the staging skills
  dir: from `global-config/skills/<name>` when present, otherwise copied from the live V1 root with a
  reported note, otherwise a reported WARNING naming the missing skill (never a silent pass).
- V2 mode points `SKILLS_DIR` at `$V2_CONFIG_ROOT/skills` (an explicit `WORKFLOW_VERIFY_SKILLS_DIR`
  still wins), and `tests/test_verifier_v2_mode.py` pins the new default.
- Tests cover: carried-from-V1, no-V1-source warning, and the V2 skills-dir default.

### T5 — Verifier check: referenced skill/handover resolves from another repo

Acceptance criteria:

- `verify/checkers/check-prompt-references.py <foreign-repo> <skills-root>` resolves every prompt-named
  skill from `<skills-root>` only, and never from `<foreign-repo>`; it fails naming the missing
  reference and the root it searched.
- The verifier module runs it from a freshly created temp directory (a repo other than this one) and
  then runs it again with a deliberately unresolvable probe reference, which MUST fail (positive
  control). A run where the control passes is itself an error.
- A test asserts the inventory matches the skill names the prompts actually reference, so the table
  cannot drift silently.

### T6 — Tracker, TODO status and manifest re-pin

Acceptance criteria: `docs/TODO.md` Q128 (and the Q102/Q116 status lines) reflect the delivered state;
`python3 scripts/verifier_manifest.py update` was run and `check` is clean; full
`python3 -m unittest discover -s tests` is green with no `__pycache__`.

## Constraints

- Process: test-first for every behaviour change; PYTHONDONTWRITEBYTECODE=1; no `__pycache__`.
- Do NOT run native review, do NOT merge, do NOT run `derive --apply`, do NOT restart services, do NOT
  run the live `--behavioral` verifier. The owner applies the derived config.
- Never edit `scripts/verifier_manifest.py`; only run it.
- Commits in slices under about 400 authored changed lines, Conventional Commits, no AI attribution.
- Binding environment facts: `host_git_head` returns `{ branch, detached, head }`; `docs/specs/**` and
  `global-config/**` are never simple docs; `odd/tasks/**` is plan-root protected, so only the
  orchestrator's `host_plan_write` touches this tracker.

## Route evidence

`ROUTE: global tooling change | intent: authorized change | route: workflow-odd-secure / delegated-slices | specialist: general (bounded direct writer) | basis: WORKFLOW.md Task Classes row "Global tooling change"`

Trigger: writer/mutation delegation (secure policy) — this orchestrator is read-only; every mutation is
a delegated sandbox writer. PM layer unavailable in this worktree (`docs/specs/pm-handoff.md:74` returns
`BLOCKED` for a HEAD under `.git/worktrees/`, confirmed: `.git` here is the pointer file
`gitdir: /home/james/ai-workspace/workflow_optimisation/.git/worktrees/q128-pm-handoff-skill`), so the
unit uses direct bounded `general` dispatches, one slice each, instead of a PM.

## Advice gap (recorded)

The pre-code advice phase could not run: the registered `advisor-*-pre` agents
(`advisor-design-pre`, `advisor-integration-pre`, `advisor-maintainability-pre`, `advisor-security-pre`,
`advisor-testing-pre`, `advisor-gemini-pre`) are not materialized in this runtime's subagent
delegation catalog — the live catalog enumerates `general`, `explore`, `correctness-reviewer`,
`project-standards-reviewer`, `planner`, … and none of the `advisor-*` names. `planner` is also
structurally blocked here for the reason above. This matches the known runtime gap recorded for the
pm-only-clone session. The pre-code advice phase is therefore recorded as **unavailable**, not passed;
no advisor opinion exists for this unit and none is claimed. Post-code: the same absence applies, so
the compensating control is test-first plus an independent verifier dispatch at the end of the unit.

## Progress

- [ ] T1 C4 mechanism migration
- [ ] T2 C5 merged-config readback
- [ ] T3 C6 `pm-handoff` global skill
- [ ] T4 Q116 V2 ODD delivery skills
- [ ] T5 referenced-skill resolution check
- [ ] T6 tracker/TODO/manifest re-pin

## Next step

Dispatch the T1 writer with the exact acceptance criteria and checks above.


## Revisions
- r1 2026-11-08T19:02:03Z gentle-orchestrator: Create the Q128 tracker before the first source edit.
