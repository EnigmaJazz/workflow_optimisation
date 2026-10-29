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
#   - native/AFT grep remains ask-gated because it returns content without
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
  "10-env.sh 09b537202513193205fb6fc598b4febb0b0e7020e8018321cdc7d620f8ac2194"
  "20-helpers.sh b88837e9368b62a7175ef768881f1b51595935ec62cb82f24eb5f0fecaddbaf5"
  "30-recover-config.sh 538d7715451823ce58e3227e10fa0e55811d4b7ee461fdcc3efb61c7d3d32c7a"
  "31-recover-skills-agents.sh 7c646795f905093f1582dca0ea6f4badee906264fc1051df9f3d46a6ffb1cf38"
  "32-recover-systematic.sh 6e218d4f6ff59bd3875665c9c8cc71f20e2fdb08298cdc3cb935739bd700793e"
  "40-temp-and-routing.sh 8516dec379a9c711ff398d2e6117e3d4df93d49cb02c126419999752f9db65d8"
  "41-checker-systematic.sh d2b24934715d00f7d56fc86402bc20554bd9665b18f43c613ea19c402ad3dd14"
  "42-checker-runtime-agents.sh e3ab3706ce136917b46df9bc73a338dc00e4e0aaf809bf834ef8ac6e5ba4a8be"
  "50-section-0-recover.sh 59acbf25902e61292d30175df05c073b27d13b62e9c83dd0ecf439ea9f2cc7c1"
  "51-section-1-gentle-ai.sh 6f125ca157c9b14033749cb4f68c989551230a5d22f5f4a2d1d538704924c7f5"
  "52-section-2-systematic-install.sh 2439384f1c65f5ca51f9584a75e0f887f46d8e73fac69cf9df0a9d405904e197"
  "53-section-2b-magic-context.sh a04df319dcf8a5fe740123644c57ccb2c8198fa998583662e8a18212eadd727b"
  "54-section-2c-package-integrity.sh 41f547688494c14c93b7f0a141937b7e462722196b0d74f539e15da53cdfb3a5"
  "55-section-3-skills.sh 9d7ff4416ae7a1c8565258a60e1b3e284217e02063daa8a3b35973f54854933f"
  "56-section-4-5-agents-registry.sh 2b66b463ddd9942fba8c065fa7e94689217add64a39a717f62547424d68951f8"
  "57-section-6-plugin-mirrors.sh 44937c5fb60833afe7358159c12ecd754b436cb8330882960512e56f65447af5"
  "58-section-7-recipe.sh 9f02d1b88bd2dd08ee2aacf1f8619f2c149dcc383b66a4ed6f808da74f4e8502"
  "59-section-8-9-config-runtime.sh 2a1aa57801ae868133f0bb082388f2d36950fced7a1e8dd0e54e3a7d1b09908f"
  "60-section-9a-9b-secure-service.sh fab3a32e1a08b55b3fb39fa24c8346ebf5d0c22cd55accbeeecb5af481f31d6b"
  "61-section-10-behavioural.sh 8dc2fa4080a8ad9a3385c9854bdb8fb3add707e6c74a033efb652b5c52e7b168"
  "62-section-11-summary.sh 5df415a1b7f63144822d2bb62c2300df4f2de8ea36cc0dc7ee5d4138c477ea76"
  "checkers/check-parallel-dispatch.py 7082138c1ee02dc51d73ac45e8b06911eca92c845c1e1029539042cf470b3815"
  "checkers/check-runtime-agents.cjs f23021ea00ff50efd383bb29ecb39467a1e0e499c0c6f2d249a292fbb5b7616b"
  "checkers/check-systematic-resolution.cjs 39b81b3ef5aacffa9b45ccde1bb2b3b5afc123bf928975403f8f287190360691"
  "checkers/routing-canonical.md 23c0c9ab507e96b04966a4e1e2b5419771859dfd87eef1efb2d3191e52c559e4"
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
    *.sh)
      # shellcheck source=/dev/null
      source "$VERIFY_MODULE_DIR/${verify_module_entry%% *}" ;;
  esac
done
# END VERIFY_LOADER
