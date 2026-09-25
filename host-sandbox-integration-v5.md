# Host sandbox integration deployment notes — Gentle AI 3.1.0

The reviewed workflow sources target Gentle AI **3.1.0+** and Systematic **3.18.4+**, with Systematic **3.18.6** reviewed as the current maintenance release. They preserve `grep: ask`, the local `file://` auto-update plugin, sandbox-only project changes, per-session optional Astra for Sol review roles, and the decision to ignore peak policy. Gentle AI v3 makes ODD the default. For substantial authorized work, our secure adapter delegates creation of `odd/tasks/<feature>.md` and mirrors its complete body to Magic Context before the first implementation source edit. It does not install or require Engram.

## Files to place in the workflow manager

| Reviewed file | Manager destination |
|---|---|
| `opencode-final-v20.json` | `global-config/opencode.json` |
| `AGENTS-final-v15.md` | `global-config/AGENTS.md` |
| `systematic-final-v9.jsonc` | `global-config/systematic.jsonc` |
| `rate-limit-fallback-final-v8.json` | `global-config/rate-limit-fallback.json` |
| `WORKFLOW-final-v16.md` | `WORKFLOW.md` |
| `verify-workflow-v5.43.sh` | `verify-workflow.sh` |
| `workflow-health-check-v23.ts` | `global-config/plugins/workflow-health-check.ts` |
| `mapped-fallback-config-v2.ts` | Merge its `DEFAULT_EXCLUDE_AGENTS` block into the mapped fallback plugin `src/config.ts` |

Inspect the manager's current files and keep any unrelated locally owned edits before replacing them. The verifier and health plugin must be installed as a pair because the latter pins the former's SHA256. Allow the existing version manager to retain newer safe Systematic and Magic Context plugin versions; preserve the local updater URI exactly.

## Required changes in the host sandbox integration repository

The sandbox integration plugin and installer sources were unavailable in this workspace, so their edits and byte parity are **unverified** here. An earlier copy of the mapped fallback plugin source was available; the updated copy supplies the exact exclusion block, but must be compared with the current host version before merging:

1. Add `opencode/plugins/reviewer-relay-transport.ts` and `opencode/plugins/lib/host-tool-approval.ts` to both `scripts/install-user-files` and `scripts/rollback`, preserving the `lib/` subpath. Keep the existing installs for `sandbox-tools.ts`, `routing-guard.ts`, and `lib/broker-client.ts`. Verify all five installed files against that repository before the OpenCode restart. A top-level `.ts` plugin auto-loads from the plugin directory; no package-array reference is needed.
2. In the mapped fallback plugin's `src/config.ts`, extend `DEFAULT_EXCLUDE_AGENTS` to include all twelve names: `review-risk`, `review-resilience`, `review-readability`, `review-reliability`, `review-refuter`, `review-validator`, and the corresponding six `asi-review-*` names. Its compiled output must reflect the source change. The reviewed `rate-limit-fallback.json` includes the same twelve. Native review status and relaunch handle transient failures of these bound actors.
3. Confirm the broker's trusted-agent allowlist remains limited to `gentle-orchestrator` for the sixteen allowed fixed host mutations, and each mutation still passes through `ctx.ask`. Seven allowed host workflow reads may be made available to ordinary agents; the remaining eight v2 host operations must remain denied. Do not expose the ten `host_system`, service, process, network, and Docker read names: the supplied manifest found no plugin registering them.
4. The verifier checks the canonical route decision text in the orchestrator prompt, AGENTS.md and WORKFLOW.md; this is static enforcement, not proof that a live session read the file or ran the named Systematic specialist. It also checks file presence, declared permissions, relay agent registration and isolation, fallback source defaults, and review bundle files. Set `WORKFLOW_VERIFY_SANDBOX_REPO` to the actual integration checkout to enable source parity and installer/rollback checks. Missing files or incomplete exclusions are failures; the verifier does not install unknown plugin bytes or rewrite the external fallback plugin source.
5. Verify that retired v2 SDD `host_sdd_attempt_*` operations (except the explicit edit grant), `host_sdd_attempt_status`, and `host_sdd_verify_validate` remain denied even if the old host plugin still registers them. The broker/plugin repository may require a separate reviewed update to remove dead registrations. SDD research is output-only and has no filesystem, sandbox, or Magic Context access; the orchestrator handles authorized memory persistence after the researcher returns.

## Gentle AI 3.1.0 integration requirement

The secure host integration must be reviewed for scoped native assessment and STATUS (`--base-ref` and `--committed-only`). Do not assume old `host_review_assess` or `host_review_status` preserves these arguments. Until the host plugin and broker prove an exact scoped route, the orchestrator must report substantial ODD native review as blocked rather than run an unscoped whole-branch review. Work-unit commits are task-local sandbox work after checks; push, PR, and merge still need explicit intent. Systematic 3.18.6 is maintenance-only and needs no model or role remap.

## Startup sequence

After the source changes have been reviewed and the active upstream packages are installed, run `gentle-ai sync` and review its managed-file diffs. Place the reviewed files in the manager, install the host sandbox plugin files from the integration repository, run `verify-workflow.sh --recover-config-only`, then install the reviewed health plugin from `global-config/plugins/` to `~/.config/opencode/plugins/`. Run the full verifier manually, restart the secure OpenCode service once after all remaining plugin checks pass, and run the verifier again for runtime checks. The verifier requires the canonical secure v3 ODD routing block in live `AGENTS.md`. The separate upstream generated ODD prose is diagnostic when present, since sync does not guarantee its appearance in this global file. The recovery step places the secure user-owned override last. Its optional `--behavioral` mode checks independent Task dispatch and that a planning-only request creates no writer or ODD tracker. The Systematic `ce:review` helper pipeline must execute in a sandbox worker; do not synthesize reports after helper failure. Run `ce-review-cleanup` only with its own preview and deletion approval; it is independent from the OpenCode package-cache pruner.

**Boundaries and unresolved integration:** The v3 ODD generator describes an Engram mirror and an inline one-file writer. This user's setup uses a reviewed Magic Context full-body mirror and delegates every project write to a sandbox worker. Live behavior for a substantial feature, ODD resume after interruption, SDD optional diagnostics/archive, and consent presentation cannot be certified here because the secure host, current sandbox plugins, and OpenChamber session are unavailable. A safe first feature trial should prove tracker/readback occurs before the first source edit and that a missing Task tool blocks rather than causing inline implementation. No cache-prune or plugin auto-update changes are made by this migration.

The verifier cannot certify the running secure service, the installer/rollback source, or the mapped fallback plugin in this scratch environment. Its local syntax and configuration checks do not replace the post-install runtime probe.
