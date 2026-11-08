#!/usr/bin/env bash
# verify-workflow.sh — health check + self-heal for the global workflow setup.
#
# Run after updating OpenCode, Systematic, gentle-ai, or the workflow plugins:
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh --behavioral
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh --recover-config-only
#
# Re-verifies:
#   - Gentle AI v4 ODD assets and user-selected RDD/telemetry modes are readable
#   - the active Systematic bundle contains the required workflow skills
#   - obsolete Systematic compatibility symlinks are absent
#   - the global AGENTS.md routing contract is present and canonical
#   - Gentle AI sync drift in opencode.json / AGENTS.md and accidental rollback
#     of systematic.jsonc / the mapped fallback policy are recovered from the
#     reviewed user-owned sources after a timestamped backup; unknown future
#     top-level OpenCode keys and allowlisted auto-updated plugin version pins
#     are preserved, while the fallback policy remains fixed
#   - the TUI plugin discovery surface is preserved and recovered after backup;
#     shared package refs are synchronized to the auto-updated opencode.json pins
#   - the gentle-ai skill registry refresh succeeds
#   - reviewed workflow plugins are mirrored into ~/.config/opencode/plugins
#   - the Astra alias plugin is mirrored and dynamically exposes non-writing
#     Sol roles as per-session `-astra` upgrades without freezing plugin prompts
#   - orphaned opencode-plugin-auto-update locks are safely self-repaired when
#     their recorded PID is no longer running
#   - the reviewed local auto-update build remains authoritative in both
#     opencode.json and tui.json and is never replaced by its stale npm package
#   - workflow-health-check.ts pins this exact script digest and suppresses
#     recursive health checks during OpenCode runtime probes
#   - WORKFLOW.md / requirements / AGENTS.md remain mutually consistent
#   - systematic.jsonc contains an explicit overlay for every bundled agent and
#     no stale agent/category entries
#   - the exact configured Magic Context version is materialized in the cache
#   - other Magic Context cache trees are reported as ignored diagnostics; a
#     successful unrepaired run issues a config-bound approval for the separate
#     scheduled cache-maintenance service, while this verifier never deletes them
#   - every bundled Systematic agent is registered at runtime; representative
#     resolved agents match systematic.jsonc model/variant allocations
#   - the primary orchestrator's resolved runtime model/variant exactly match
#     its current opencode.json assignment (data-driven; no model hard-code)
#   - every active OpenCode and Systematic primary model has an exact, effective
#     mapped fallback chain; the deployed policy is byte-identical to its
#     reviewed canonical source and contains no stale/unsupported entries
#   - DeepSeek V4.1 Flash replaces all Muse and older DeepSeek primaries;
#     provider/model failures use the current direct DeepSeek alias and the
#     exact OpenRouter V4.1 slug, while provider-wide OpenCode Go failures
#     correctly skip all same-provider targets
#   - Gentle/GGA and Judgment Day critical reviewers retain deliberate primary
#     and first-fallback diversity and never silently collapse onto defaults
#   - the primary orchestrator keeps Task visible with an ask fallback and
#     explicit allows for approved Gentle/Systematic subagents, mandatory
#     asi-review relay routing, and denies for the plain provider review names
#   - protected read-path denies remain intact; narrow read-only
#     Git/system-metadata/custom/sandbox tools are prompt-free, while generic
#     content-reading/search shell fallbacks remain ask-gated
#   - native host edit/write are denied for every agent; project mutation is
#     sandbox-only, and the orchestrator is read-only
#   - Systematic agents that declare Edit/Write are automatically detected from
#     the active bundle and sandbox-routed through supported systematic.jsonc
#     permission overlays (never shadowed by opencode.json agent stubs)
#   - AFT/CodeGraph/Context7/custom tools remain available to ordinary workers;
#     deliberately tool-less immutable reviewers remain exempt
#   - context-dependent fixed host-control tools are authorization-checked from
#     resolved permission rules; neutral debug-tool absence is diagnostic only
#   - native/AFT grep is allowed only for the orchestrator because it returns content without
#     inheriting protected read-path rules; glob is allowed for path discovery only
#   - an active secure-opencode.service is bound to a certified content-hash
#     generation; startup-time rewrites do not create a false restart loop
#   - optional --behavioral mode proves two independent Task calls are emitted
#     in one assistant turn and checks a planning-only request never dispatches
#     a writer or creates an ODD tracker
#
# Important deployment invariant:
#   Editing this file changes its SHA256. Update VERIFY_SCRIPT_SHA256 in the
#   reviewed workflow-health-check.ts source before expecting this verifier to
#   pass its plugin-integrity section.
#
# Structure (queue Q04): this file is only the entry. The checks live in verify/NN-*.sh and are
# sourced in order after every module's sha256 is verified against the manifest below, so the single
# VERIFY_SCRIPT_SHA256 pinned in workflow-health-check.ts still binds the whole verifier. After
# editing any module run `python3 scripts/verifier_manifest.py update`; it regenerates the manifest
# and re-pins the plugin. `python3 scripts/verifier_manifest.py check` verifies both without writing.

set -uo pipefail

# BEGIN VERIFY_MODULES
VERIFY_MODULES=(
  "10-env.sh c386f045b23c8b45f77340ea4c8066fbf181fa4374a2ea0a7be8bbfcfbfe3033"
  "20-helpers.sh fe168fd43faa3cb142ccce26ed314007912b72f91238696b8d5662d6c3775380"
  "21-opencode-major.sh 7b1a02443e8650e4f16c92f74b05fa815e4ac337592136e7db0522edc52f891c"
  "30-recover-config.sh 70b478ced6f0478c67756bb221a3dc827c6463575cea8d852ea859762a6c38af"
  "31-recover-skills-agents.sh 7c646795f905093f1582dca0ea6f4badee906264fc1051df9f3d46a6ffb1cf38"
  "32-recover-systematic.sh 6e218d4f6ff59bd3875665c9c8cc71f20e2fdb08298cdc3cb935739bd700793e"
  "40-temp-and-routing.sh 8516dec379a9c711ff398d2e6117e3d4df93d49cb02c126419999752f9db65d8"
  "41-checker-systematic.sh d2b24934715d00f7d56fc86402bc20554bd9665b18f43c613ea19c402ad3dd14"
  "42-checker-runtime-agents.sh e3ab3706ce136917b46df9bc73a338dc00e4e0aaf809bf834ef8ac6e5ba4a8be"
  "50-section-0-recover.sh 75bbc6d3f0d771822b6ad14d73b42346f6eeab102a14addff6e12ce7477e7ee6"
  "51-section-1-gentle-ai.sh 6f125ca157c9b14033749cb4f68c989551230a5d22f5f4a2d1d538704924c7f5"
  "52-section-2-systematic-install.sh 0e28347f1bf988336beb31012c6fa1816dfb43e9561d266858575a84df1e96eb"
  "53-section-2b-magic-context.sh 1f6b26b6f947977452c31f98bc75edb46f226108e918880520e9f1e0568f7070"
  "54-section-2c-package-integrity.sh 13e85a3e148e396604f0c525830fb5ae7a80291e3c349488f60f68a5647ea165"
  "55-section-3-skills.sh 9d7ff4416ae7a1c8565258a60e1b3e284217e02063daa8a3b35973f54854933f"
  "56-section-4-5-agents-registry.sh 2b66b463ddd9942fba8c065fa7e94689217add64a39a717f62547424d68951f8"
  "57-section-6-plugin-mirrors.sh 476d73263f419f0d413655d07d4c9f29ef7b531fa30e6d970effcdcd152a2622"
  "57b-section-6b-tool-decisions.sh 793aa16c003fc93d36166158ea92e6a50940042b234137b153f9639445d568b0"
  "58-section-7-recipe.sh ca63ac3b085b5205b44f6684749894a7fad5a10cc689554f892d58819e7e96c6"
  "59-section-8-9-config-runtime.sh 56028b26aa2fc51be73be255e45979f76d7510c76e6ce0911d2b2a7b49a7cbbd"
  "60-section-9a-9b-secure-service.sh 4d6526fefddb88b8a3593809f05443c9b6bdeb1c2ba0575cf783fe9296a3f76f"
  "61-section-10-behavioural.sh 24a31e750fcbfeaea7e18e6801a14547e596910103ecd1ca7d16db9b9425d134"
  "62-section-11-summary.sh 4b3a5cb0025366ebdd51135efe3cb811dfe2597b4b31427e37c995480f0c09af"
  "checkers/check-parallel-dispatch.py d970c748791710131a667b6cc1cd08ea280494c021d9b2bde520b1620208447e"
  "checkers/check-runtime-agents.cjs fa5a92a657f6778ac150bdce05a27f99087e8cc9d843e00c7548f1b31bed4ca1"
  "checkers/check-systematic-resolution.cjs ec8997e05b9b5cc390529abc62bb7608e11cf8885155ef7ea0606ac47bd16499"
  "checkers/oc-probe.sh e5b2ba64cad39b90ef5702dfb00c527bd67a275799b9f5542c5c9f25af117301"
  "checkers/recover-cli-config.py 5dc9e7af0c465f3ba237ba14c03a7b5b702f0e613445828b617189e56e05295f"
  "checkers/routing-canonical.md 2da6e80c476ee3f910611cdd57d68a22aeb1ed8c96c8eafcb8be72bd16467c97"
  "checkers/sandbox-tool-decisions.py f41c7462f36aee16235fbb9d6d3921e77f669218aacfbf91948067941d180732"
  "checkers/v2-agents-shim.cjs 93e716e96f9cc7cdcfaa73ecf7e64bed42bbbab70a04240b6433108353cf11e6"
  "checkers/v2-config-check.py d1b3df3161a7b9b18f21d42610dcabff6951886d171ebc5caccadd39aebd79ae"
  "checkers/v2-github-mcp-check.py fa24359ddfcf24c21d52f4cfc2948a5813167116fb2574cc98b82f2edce9d386"
  "checkers/v2-plugin-resolve.py 5792db1b5ddf8b3bc72f03546d2046946a6b3a6404843aafa52d2e51cd4a0bbd"
  "checkers/v2-runtime-config.py e9d3d26c388d2b4533db3c89b3dddfc9cdc89c9b3f3483abc61b178a5189ed6d"
  "checkers/v2-sandbox-plugins-check.py a26e2b97a6fcc668a2aa2f457877542ec780eb304380082c7634a1adafd6e3bd"
)
# END VERIFY_MODULES

# BEGIN VERIFY_LOADER
VERIFY_ENTRY_PATH=$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")
: "${VERIFY_MODULE_DIR:=$(dirname "$VERIFY_ENTRY_PATH")/verify}"
verify_loader_fail() { echo "verify-workflow.sh: $*" >&2; exit 2; }
verify_listed=" "
for verify_module_entry in "${VERIFY_MODULES[@]}"; do
  verify_module_name=${verify_module_entry%% *}
  verify_module_want=${verify_module_entry##* }
  verify_listed="$verify_listed$verify_module_name "
  [ -f "$VERIFY_MODULE_DIR/$verify_module_name" ] || verify_loader_fail "module missing: $verify_module_name"
  verify_module_got=$(sha256sum "$VERIFY_MODULE_DIR/$verify_module_name" 2>/dev/null | awk '{print $1}')
  [ "$verify_module_got" = "$verify_module_want" ] || verify_loader_fail "module digest mismatch: $verify_module_name"
done
for verify_module_file in "$VERIFY_MODULE_DIR"/*.sh "$VERIFY_MODULE_DIR"/checkers/*; do
  [ -f "$verify_module_file" ] || continue
  verify_module_rel=${verify_module_file#"$VERIFY_MODULE_DIR"/}
  case "$verify_listed" in
    *" $verify_module_rel "*) ;;
    *) verify_loader_fail "unlisted module file: $verify_module_rel" ;;
  esac
done
for verify_module_entry in "${VERIFY_MODULES[@]}"; do
  case "${verify_module_entry%% *}" in
    checkers/*) ;; # run by the sections (bash "$OC_PROBE" ...), never sourced: sourcing oc-probe.sh would exec a bare opencode (the TUI)
    *.sh)
      # shellcheck source=/dev/null
      source "$VERIFY_MODULE_DIR/${verify_module_entry%% *}" ;;
  esac
done
# END VERIFY_LOADER
