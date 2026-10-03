#!/usr/bin/env bash
# verify-workflow.sh — health check + self-heal for the global workflow setup.
#
# Run after updating OpenCode, Systematic, gentle-ai, or the workflow plugins:
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh --behavioral
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh --recover-config-only
#
# Re-verifies:
#   - Gentle AI v3.5.0+ ODD/SDD assets and user-selected RDD/telemetry modes are readable
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
#     sandbox-only, the orchestrator is read-only, and all SDD stages retain
#     sandbox artifact-write capability
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

set -uo pipefail

RUN_BEHAVIOURAL=0
RECOVERY_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --behavioral)
      RUN_BEHAVIOURAL=1
      ;;
    --recover-config-only)
      RECOVERY_ONLY=1
      ;;
    -h|--help)
      cat <<'EOF_HELP'
Usage: verify-workflow.sh [--behavioral] [--recover-config-only]

Normal mode performs deterministic configuration/runtime resolution checks.
--behavioral additionally probes OpenCode Task fan-out and a read-only
planning request; the latter must not dispatch a writer or create ODD tasks.
--recover-config-only repairs the reviewed opencode.json, AGENTS.md,
systematic.jsonc, mapped fallback-policy overlays, and the TUI plugin discovery
surface in tui.json,
then exits without running package, plugin, or paid runtime probes.
EOF_HELP
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

WORKSPACE="${WORKFLOW_VERIFY_WORKSPACE:-/home/james/ai-workspace/workflow_optimisation}"
OPENCODE_CONFIG_DIR="${WORKFLOW_VERIFY_OPENCODE_CONFIG_DIR:-/home/james/.config/opencode}"
OPENCODE_CONFIG_FILE="$OPENCODE_CONFIG_DIR/opencode.json"
TUI_CONFIG_FILE="${WORKFLOW_VERIFY_TUI_CONFIG_FILE:-$OPENCODE_CONFIG_DIR/tui.json}"
SKILLS_DIR="$OPENCODE_CONFIG_DIR/skills"
ROUTER_SKILLS_SOURCE="$WORKSPACE/global-config/skills"
PLUGINS_DIR="$OPENCODE_CONFIG_DIR/plugins"
OPENCODE_CACHE_DIR="${WORKFLOW_VERIFY_OPENCODE_CACHE_DIR:-/home/james/.cache/opencode}"
PACKAGES_DIR="$OPENCODE_CACHE_DIR/packages/@fro.bot"
MAGIC_PACKAGES_DIR="$OPENCODE_CACHE_DIR/packages/@cortexkit"
AGENTS_FILE="$OPENCODE_CONFIG_DIR/AGENTS.md"
OPENCODE_CONFIG_SOURCE="$WORKSPACE/global-config/opencode.json"
TUI_CONFIG_SOURCE="$WORKSPACE/global-config/tui.json"
AGENTS_SOURCE="$WORKSPACE/global-config/AGENTS.md"
RECOVERY_BACKUP_ROOT="$WORKSPACE/backups/workflow-recovery"
RECOVERY_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ).$$"
SYSTEMATIC_CONFIG="$OPENCODE_CONFIG_DIR/systematic.jsonc"
SYSTEMATIC_CONFIG_SOURCE="$WORKSPACE/global-config/systematic.jsonc"
FALLBACK_POLICY_SOURCE="$WORKSPACE/global-config/rate-limit-fallback.json"
FALLBACK_POLICY_DEPLOYED="$OPENCODE_CONFIG_DIR/rate-limit-fallback.json"
GENTLE_STATE_FILE="${WORKFLOW_VERIFY_GENTLE_STATE_FILE:-/home/james/.gentle-ai/state.json}"

ROUTING_MARKER_START="<!-- user:workflow-routing -->"
ROUTING_MARKER_END="<!-- /user:workflow-routing -->"

HEALTH_PLUGIN_SOURCE="$WORKSPACE/global-config/plugins/workflow-health-check.ts"
HEALTH_PLUGIN_DEPLOYED="$PLUGINS_DIR/workflow-health-check.ts"
ROUTING_GUARD_SOURCE="$WORKSPACE/global-config/plugins/systematic-routing-guard.ts"
ROUTING_GUARD_DEPLOYED="$PLUGINS_DIR/systematic-routing-guard.ts"
ASTRA_PLUGIN_SOURCE="$WORKSPACE/global-config/plugins/astra-sol-upgrade.ts"
ASTRA_PLUGIN_DEPLOYED="$PLUGINS_DIR/astra-sol-upgrade.ts"
RELAY_PLUGIN_DEPLOYED="$PLUGINS_DIR/reviewer-relay-transport.ts"
HOST_APPROVAL_HELPER_DEPLOYED="$PLUGINS_DIR/lib/host-tool-approval.ts"
FALLBACK_EXCLUSION_SOURCE="$PLUGINS_DIR/opencode-rate-limit-fallback-mapped/src/config.ts"
SANDBOX_INTEGRATION_REPO="${WORKFLOW_VERIFY_SANDBOX_REPO:-}"
OLD_TIERING_PLUGIN_ACTIVE="$PLUGINS_DIR/systematic-model-tiering.ts"
AUTO_UPDATE_LOCK="$OPENCODE_CONFIG_DIR/.auto-update.lock"
PLUGIN_CACHE_INTEGRITY_HELPER="$WORKSPACE/scripts/plugin-cache-integrity.py"
PLUGIN_QUARANTINE_DIR="$WORKSPACE/backups/plugin-quarantine"
LOCAL_AUTO_UPDATE_REF="${WORKFLOW_VERIFY_LOCAL_AUTO_UPDATE_REF:-file:///home/james/.local/share/opencode-plugin-auto-update-local/dist/index.js}"
SECURE_OPENCODE_SERVICE="${WORKFLOW_VERIFY_SECURE_OPENCODE_SERVICE:-secure-opencode.service}"
SECURE_RUNTIME_WITNESS="${WORKFLOW_VERIFY_SECURE_RUNTIME_WITNESS:-$WORKSPACE/.atl/secure-opencode-runtime-witness.json}"
CACHE_PRUNE_APPROVAL="${WORKFLOW_VERIFY_CACHE_PRUNE_APPROVAL:-$WORKSPACE/.atl/opencode-cache-prune-approval.json}"

WORKFLOW="$WORKSPACE/WORKFLOW.md"
REQS="$WORKSPACE/docs/brainstorms/2026-08-10-workflow-routing-requirements.md"

REQUIRED_SKILLS=(
  "test-driven-development"
  "frontend-design"
  "reproduce-bug"
  "ce-brainstorm"
  "ce-plan"
  "ce-work"
  "ce-review"
  "ce-review-cleanup"
  "ce-compound"
)

FAIL=0
# Colour is emitted only on an interactive terminal so captured runs (the
# health-check plugin, CI, log files) stay plain text; NO_COLOR opts out.
# Fixed 256-colour red; the 16-colour palette slot can be re-themed by a terminal.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != "dumb" ]; then
  C_RED=$'\033[38;5;196m'
  C_BOLD_RED=$'\033[1;38;5;196m'
  C_RESET=$'\033[0m'
else
  C_RED=""
  C_BOLD_RED=""
  C_RESET=""
fi
# fail() messages, printed as a summary before exit 1.
FAIL_MESSAGES=()
AUTO_REPAIRED=0
CAN_RUNTIME_PROBE=1
STATIC_SYSTEMATIC_OK=1
RUNTIME_RESTART_REQUIRED=0
ACTIVE_ROOT=""
ACTIVE_SKILLS=""
ACTIVE_AGENTS=""
SYSTEMATIC_NODE_MODULES=""

fail() {
  FAIL_MESSAGES+=("$*")
  echo "   ${C_RED}!! $*${C_RESET}"
  FAIL=1
}

check_plugin_loads() {
  local plugin_dir="${1:-$PLUGINS_DIR}" mode="${2:-factory}"
  local scratch_dir plugin output status checked=0
  plugin_dir=$(cd "$plugin_dir" 2>/dev/null && pwd) || {
    fail "deployed plugin directory is unavailable: $plugin_dir"
    return
  }
  if ! command_exists bun || ! command_exists timeout; then
    fail "cannot load-check deployed plugins: bun and timeout are required"
    return
  fi
  scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/workflow-plugin-load.XXXXXX") || {
    fail "cannot create scratch directory for deployed plugin load checks"
    return
  }
  # Keep the tracked-plugin hook-key allowlist aligned with the installed OpenCode plugin API version; it must track that version.
  for plugin in "$plugin_dir"/*.ts "$plugin_dir"/*.js; do
    [ -f "$plugin" ] || continue
    case "${plugin##*/}" in
      *.bak*|*.disabled) continue ;;
    esac
    checked=$((checked + 1))
    output=$(cd "$scratch_dir" && SYSTEMATIC_ROUTING_GUARD_STATE_ROOT="$scratch_dir" WORKFLOW_HEALTH_CHECK_PROBE=1 PLUGIN_LOAD_CHECK_PATH="$plugin" PLUGIN_LOAD_CHECK_MODE="$mode" timeout 8s bun --no-install -e 'const path = process.env.PLUGIN_LOAD_CHECK_PATH; const knownHooks = new Set(["event", "chat.message", "chat.params", "chat.headers", "permission.ask", "shell.env", "tool.definition", "tool", "tool.execute.before", "tool.execute.after", "auth", "provider", "command.execute.before", "config", "dispose", "experimental.chat.messages.transform", "experimental.session.compacting", "experimental.compaction.autocontinue", "experimental.chat.system.transform", "experimental.text.complete"]); const trackedNames = new Set(["astra-sol-upgrade.ts", "systematic-routing-guard.ts", "workflow-health-check.ts"]); const tracked = trackedNames.has(path.split("/").pop()); let m; try { m = await import(path) } catch (error) { console.error("plugin import failed: " + String(error)); process.exit(3) } const functionExports = Object.entries(m).filter(([, value]) => typeof value === "function").map(([name]) => name); const namedFactories = Object.entries(m).filter(([name, value]) => /Plugin/.test(name) && typeof value === "function"); const factoryNames = [...(typeof m.default === "function" ? ["default"] : []), ...namedFactories.map(([name]) => name)]; const unexpectedFunctionExports = functionExports.filter(name => !factoryNames.includes(name)); const exportFailure = unexpectedFunctionExports.length ? "unexpected function-valued plugin exports: " + unexpectedFunctionExports.join(", ") : namedFactories.length > 1 ? "ambiguous named Plugin factory exports: " + namedFactories.map(([name]) => name).join(", ") : null; if (exportFailure) { if (tracked) { console.error(exportFailure + ": " + path); process.exit(6) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + exportFailure + ": " + path) } if (process.env.PLUGIN_LOAD_CHECK_MODE === "import") { console.log("plugin import succeeded"); process.exit(0) } const factory = typeof m.default === "function" ? ["default", m.default] : namedFactories.length === 1 ? namedFactories[0] : null; if (!factory) { const reason = namedFactories.length > 1 ? "ambiguous named Plugin factory exports: " + namedFactories.map(([name]) => name).join(", ") : "no default or named Plugin factory export"; if (tracked) { console.error(reason + ": " + path); process.exit(4) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + reason + ": " + path); process.exit(0) } try { const result = await factory[1]({}); const hooks = result && typeof result === "object" ? [...knownHooks].filter(key => Object.prototype.hasOwnProperty.call(result, key)) : []; if (!hooks.length) { const message = "factory returned no recognized hooks: " + factory[0]; if (tracked) { console.error(message); process.exit(5) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + message + ": " + path); process.exit(0) } console.log("plugin factory invoked: " + factory[0] + "; recognized hooks: " + hooks.join(", ")) } catch (error) { console.log("PLUGIN_LOAD_WARNING: factory threw (non-fatal): " + factory[0] + ": " + String(error)) }' 2>&1)
    status=$?
    if [ "$status" -eq 0 ]; then
      case "$output" in
        PLUGIN_LOAD_WARNING:*|PLUGIN_LOAD_REPORT_ONLY:*) echo "   !! ${plugin##*/}: $output" ;;
        *) echo "   OK plugin ${mode}: ${plugin##*/}${output:+ — $output}" ;;
      esac
      continue
    fi
    if [ "$status" -eq 124 ]; then
      fail "plugin load timed out: $plugin"
      continue
    fi
    fail "plugin load check failed: $plugin (exit $status): $output"
  done
  rm -rf "$scratch_dir"
  if [ "$checked" -eq 0 ]; then
    fail "plugin load check found no plugin files under $plugin_dir"
  fi
}

repair_note() {
  echo "   !! $*"
  AUTO_REPAIRED=1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

sha256_file() {
  sha256sum "$1" 2>/dev/null | awk '{print $1}'
}

if [ "$RECOVERY_ONLY" -eq 0 ]; then
  plugin_mode=import
  if [ "${WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY:-0}" = "1" ]; then
    plugin_mode="${WORKFLOW_VERIFY_PLUGIN_LOAD_MODE:-import}"
  fi
  check_plugin_loads "${WORKFLOW_VERIFY_PLUGIN_LOAD_DIR:-$PLUGINS_DIR}" "$plugin_mode"
fi
if [ "${WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY:-0}" = "1" ]; then
  [ "$FAIL" -eq 0 ] && exit 0
  exit 1
fi

write_cache_prune_approval() {
  python3 - "$CACHE_PRUNE_APPROVAL" "$OPENCODE_CONFIG_FILE" "$TUI_CONFIG_FILE" "$0" <<'PY_CACHE_APPROVAL'
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

target = Path(sys.argv[1])
config_paths = [Path(sys.argv[2]), Path(sys.argv[3])]
verifier = Path(sys.argv[4]).resolve(strict=True)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

references = set()
digests = {}
for path in config_paths:
    value = json.loads(path.read_text(encoding="utf-8"))
    plugins = value.get("plugin", [])
    if not isinstance(plugins, list) or not all(isinstance(ref, str) for ref in plugins):
        raise RuntimeError(f"invalid plugin list in {path}")
    references.update(plugins)
    digests[path.name] = sha256(path)

approval = {
    "schema": "workflow.cache-prune-approval/v1",
    "approved_at_epoch": int(time.time()),
    "config_sha256": digests,
    "plugin_references": sorted(references),
    "verifier_path": str(verifier),
    "verifier_sha256": sha256(verifier),
}

target.parent.mkdir(parents=True, exist_ok=True)
fd, temp_name = tempfile.mkstemp(prefix=".cache-prune-approval.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(approval, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, 0o600)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY_CACHE_APPROVAL
}

recover_opencode_config() {
  python3 - "$OPENCODE_CONFIG_FILE" "$OPENCODE_CONFIG_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" "$LOCAL_AUTO_UPDATE_REF" "$PLUGIN_CACHE_INTEGRITY_HELPER" "$OPENCODE_CACHE_DIR/packages" <<'PY_RECOVER_OPENCODE'
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]
local_auto_update_ref = sys.argv[5]
integrity_helper = sys.argv[6]
packages_cache_root = sys.argv[7]
auto_update_identity = "opencode-plugin-auto-update"

parsed_local_ref = urlparse(local_auto_update_ref)
if parsed_local_ref.scheme != "file" or parsed_local_ref.netloc not in ("", "localhost"):
    print("error\treviewed local auto-update reference must be a local file URI")
    raise SystemExit(0)
local_auto_update_path = Path(unquote(parsed_local_ref.path))
if not local_auto_update_path.is_file():
    print(f"error\treviewed local auto-update build is missing: {local_auto_update_path}")
    raise SystemExit(0)

required_agents = {
    "gentle-orchestrator", "general", "explore", "sdd-research",
    "frontend-dev", "frontend-dev-premium", "sdd-apply-local",
    "asi-review-risk", "asi-review-resilience", "asi-review-readability",
    "asi-review-reliability", "asi-review-refuter", "asi-review-validator",
}

# These package identities are intentionally version-managed by the reviewed
# local auto-update plugin. The auto-update plugin itself is deliberately not
# in this set: its exact file URI is owned by this workflow and is immutable
# during recovery.
auto_updated_plugin_packages = {
    "@fro.bot/systematic",
    "@cortexkit/opencode-magic-context",
    "@cortexkit/aft-opencode",
    "opencode-usage-total",
}

def package_identity(ref):
    if not isinstance(ref, str) or ref.startswith(("file:", "/", ".")):
        return None
    if ref.startswith("@"):
        slash = ref.find("/")
        if slash < 2:
            return None
        version_at = ref.find("@", slash)
        return ref if version_at < 0 else ref[:version_at]
    version_at = ref.find("@")
    return ref if version_at < 0 else ref[:version_at]

def managed_identity(ref):
    if ref == local_auto_update_ref:
        return auto_update_identity
    return package_identity(ref)

def safe_versioned_ref(ref, identity):
    if not isinstance(ref, str) or package_identity(ref) != identity:
        return False
    suffix = ref[len(identity):]
    if not suffix.startswith("@") or len(suffix) < 2:
        return False
    tag = suffix[1:]
    return all(ch.isalnum() or ch in ".+_-" for ch in tag)

def semver_core(ref, identity):
    if not safe_versioned_ref(ref, identity):
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", ref[len(identity) + 1:])
    return tuple(map(int, match.groups())) if match else None

def pin_is_complete(ref):
    # A newer deployed pin is only trustworthy when its package is fully
    # installed in the OpenCode cache (an interrupted install leaves no package.json).
    try:
        proc = subprocess.run(
            [sys.executable, integrity_helper, "check-pin",
             "--cache-root", packages_cache_root, "--spec", ref],
            capture_output=True, text=True, timeout=30)
        return proc.returncode == 0
    except Exception:
        return False

def safe_same_or_newer(current_ref, canonical_ref, identity):
    current_version = semver_core(current_ref, identity)
    canonical_version = semver_core(canonical_ref, identity)
    if current_version is None or canonical_version is None:
        return current_ref == canonical_ref
    return current_version >= canonical_version

try:
    canonical = json.loads(source.read_text(encoding="utf-8"))
except FileNotFoundError:
    print(f"error\tcanonical OpenCode source missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical OpenCode source is invalid: {exc}")
    raise SystemExit(0)

if not isinstance(canonical, dict):
    print("error\tcanonical OpenCode source must be a JSON object")
    raise SystemExit(0)

# Normalize an older reviewed source in memory so even a staggered deployment
# cannot replace the fixed local build with the abandoned npm release. The
# distributed canonical config also contains the local URI directly.
canonical_plugins_raw = canonical.get("plugin")
if not isinstance(canonical_plugins_raw, list) or not all(isinstance(ref, str) for ref in canonical_plugins_raw):
    print("error\tcanonical OpenCode source must contain a string plugin list")
    raise SystemExit(0)
canonical_plugins_normalized = []
auto_update_seen = False
for ref in canonical_plugins_raw:
    identity = managed_identity(ref)
    if identity == auto_update_identity:
        if not auto_update_seen:
            canonical_plugins_normalized.append(local_auto_update_ref)
            auto_update_seen = True
    else:
        canonical_plugins_normalized.append(ref)
if not auto_update_seen:
    print("error\tcanonical OpenCode source has no reviewed auto-update plugin entry")
    raise SystemExit(0)
canonical["plugin"] = canonical_plugins_normalized

agents = canonical.get("agent")
missing = sorted(required_agents - set(agents if isinstance(agents, dict) else {}))
if missing:
    print(f"error\tcanonical OpenCode source is missing reviewed agents: {','.join(missing)}")
    raise SystemExit(0)
if canonical.get("default_agent") != "gentle-orchestrator":
    print("error\tcanonical OpenCode source has the wrong default_agent")
    raise SystemExit(0)

target_valid = False
current = {}
if target.is_file():
    try:
        current = json.loads(target.read_text(encoding="utf-8"))
        target_valid = isinstance(current, dict)
    except Exception:
        target_valid = False

# The reviewed source owns every key it declares. Unknown future top-level keys
# from OpenCode/Gentle AI survive, but nested security/agent maps are replaced
# atomically so a sync cannot retain unsafe local aliases or prompt drift.
merged = deepcopy(current) if target_valid else {}
for key, value in canonical.items():
    merged[key] = deepcopy(value)

preserved_pins = []
unpreserved_pins = []
canonical_plugins = canonical.get("plugin")
current_plugins = current.get("plugin") if target_valid else None
if isinstance(canonical_plugins, list) and isinstance(current_plugins, list):
    current_by_identity = {}
    for ref in current_plugins:
        identity = managed_identity(ref)
        if identity == auto_update_identity and ref == local_auto_update_ref:
            current_by_identity.setdefault(identity, []).append(ref)
        elif identity in auto_updated_plugin_packages and safe_versioned_ref(ref, identity):
            current_by_identity.setdefault(identity, []).append(ref)

    effective_plugins = []
    for canonical_ref in canonical_plugins:
        identity = managed_identity(canonical_ref)
        candidates = current_by_identity.get(identity, [])
        if identity == auto_update_identity:
            effective_plugins.append(local_auto_update_ref)
        elif (identity in auto_updated_plugin_packages and len(candidates) == 1 and
                safe_same_or_newer(candidates[0], canonical_ref, identity)):
            if candidates[0] == canonical_ref:
                effective_plugins.append(candidates[0])
            elif pin_is_complete(candidates[0]):
                effective_plugins.append(candidates[0])
                preserved_pins.append(candidates[0])
            else:
                # Incomplete install: keep the canonical pin; the overlay
                # rewrite below restores it to the live config.
                effective_plugins.append(deepcopy(canonical_ref))
                unpreserved_pins.append(candidates[0])
        else:
            effective_plugins.append(deepcopy(canonical_ref))
    merged["plugin"] = effective_plugins

owned_clean = target_valid and all(current.get(key) == merged.get(key) for key in canonical)
pin_detail = ""
for ref in unpreserved_pins:
    print(f"!! AUTO_UPDATED_PIN_INCOMPLETE_NOT_PRESERVED: {ref}", file=sys.stderr)
if unpreserved_pins:
    pin_detail += "; AUTO_UPDATED_PIN_INCOMPLETE_NOT_PRESERVED: " + ", ".join(unpreserved_pins)
if preserved_pins:
    pin_detail += "; preserved auto-update pins: " + ", ".join(preserved_pins)
# Reconcile the canonical source with pins the auto-updater advanced: the
# deployed pin is the reviewed floor, so write the newer version back into the
# canonical file. Textual and format-preserving; idempotent when already equal.
canonical_synced = []
canonical_skipped = []
if preserved_pins and isinstance(canonical_plugins, list):
    canonical_ref_by_identity = {}
    for ref in canonical_plugins:
        if isinstance(ref, str):
            canonical_ref_by_identity[managed_identity(ref)] = ref
    source_path = Path(source)
    source_text = None
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        canonical_skipped.append(f"unreadable canonical source ({exc.__class__.__name__})")
    if source_text is not None:
        updated_text = source_text
        for ref in preserved_pins:
            identity = managed_identity(ref)
            canonical_ref = canonical_ref_by_identity.get(identity)
            if not canonical_ref:
                canonical_skipped.append(f"{identity} (no canonical counterpart)")
                continue
            if updated_text.count(canonical_ref) != 1:
                canonical_skipped.append(f"{identity} (ambiguous canonical match)")
                continue
            updated_text = updated_text.replace(canonical_ref, ref, 1)
            canonical_synced.append(f"{canonical_ref} -> {ref}")
        if canonical_synced and updated_text != source_text:
            try:
                sync_backup_dir = backup_root / run_id
                sync_backup_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(sync_backup_dir, 0o700)
                shutil.copy2(source_path, sync_backup_dir / "opencode.json.source.before")
                sync_temp = source_path.with_name(source_path.name + ".tmp-sync")
                sync_temp.write_text(updated_text, encoding="utf-8")
                os.replace(sync_temp, source_path)
            except Exception as exc:
                canonical_skipped.append(f"write failed ({exc.__class__.__name__})")
                canonical_synced = []
if canonical_synced:
    pin_detail += "; synced canonical pins: " + ", ".join(canonical_synced)
if canonical_skipped:
    pin_detail += "; canonical pin sync skipped: " + ", ".join(canonical_skipped)
if owned_clean:
    print("clean\treviewed OpenCode overlay is current" + pin_detail)
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "opencode.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".opencode.json.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print(f"repaired\t{backup}{pin_detail}")
PY_RECOVER_OPENCODE
}

recover_tui_config() {
  python3 - "$TUI_CONFIG_FILE" "$TUI_CONFIG_SOURCE" "$OPENCODE_CONFIG_FILE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" "$LOCAL_AUTO_UPDATE_REF" <<'PY_RECOVER_TUI'
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from urllib.parse import unquote, urlparse

target = Path(sys.argv[1])
source = Path(sys.argv[2])
runtime_config = Path(sys.argv[3])
backup_root = Path(sys.argv[4])
run_id = sys.argv[5]
local_auto_update_ref = sys.argv[6]
auto_update_identity = "opencode-plugin-auto-update"

parsed_local_ref = urlparse(local_auto_update_ref)
if parsed_local_ref.scheme != "file" or parsed_local_ref.netloc not in ("", "localhost"):
    print("error\treviewed local auto-update reference must be a local file URI")
    raise SystemExit(0)
local_auto_update_path = Path(unquote(parsed_local_ref.path))
if not local_auto_update_path.is_file():
    print(f"error\treviewed local auto-update build is missing: {local_auto_update_path}")
    raise SystemExit(0)

def load_object(path, label):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error\t{label} missing: {path}")
        raise SystemExit(0)
    except Exception as exc:
        print(f"error\t{label} is invalid JSON: {exc}")
        raise SystemExit(0)
    if not isinstance(value, dict):
        print(f"error\t{label} must be a JSON object")
        raise SystemExit(0)
    return value

def package_identity(ref):
    if not isinstance(ref, str) or ref.startswith(("file:", "/", ".")):
        return None
    if ref.startswith("@"):
        slash = ref.find("/")
        if slash < 2:
            return None
        version_at = ref.find("@", slash)
        return ref if version_at < 0 else ref[:version_at]
    version_at = ref.find("@")
    return ref if version_at < 0 else ref[:version_at]

def managed_identity(ref):
    if ref == local_auto_update_ref:
        return auto_update_identity
    return package_identity(ref)

canonical = load_object(source, "canonical TUI source")
runtime = load_object(runtime_config, "active OpenCode config")
required_plugins = canonical.get("plugin")
if not isinstance(required_plugins, list) or not required_plugins or not all(isinstance(ref, str) and ref for ref in required_plugins):
    print("error\tcanonical TUI source must contain a non-empty string plugin list")
    raise SystemExit(0)

# The local updater participates in the TUI discovery surface. Replace any old
# npm reference and add the reviewed file URI when upgrading an older source.
normalized_required_plugins = []
auto_update_seen = False
for ref in required_plugins:
    if managed_identity(ref) == auto_update_identity:
        if not auto_update_seen:
            normalized_required_plugins.append(local_auto_update_ref)
            auto_update_seen = True
    else:
        normalized_required_plugins.append(ref)
if not auto_update_seen:
    normalized_required_plugins.append(local_auto_update_ref)
required_plugins = normalized_required_plugins

runtime_by_identity = {}
for ref in runtime.get("plugin", []):
    identity = managed_identity(ref)
    if identity:
        runtime_by_identity.setdefault(identity, []).append(ref)
ambiguous = sorted(identity for identity, refs in runtime_by_identity.items() if len(refs) != 1)
if ambiguous:
    print(f"error\tactive OpenCode config has ambiguous plugin identities: {','.join(ambiguous)}")
    raise SystemExit(0)

target_valid = False
current = {}
if target.exists() and not target.is_file():
    print(f"error\tTUI config path is not a regular file: {target}")
    raise SystemExit(0)
if target.is_file():
    try:
        current = json.loads(target.read_text(encoding="utf-8"))
        target_valid = isinstance(current, dict)
    except Exception as exc:
        print(f"error\tTUI config is invalid JSON; refusing automatic repair: {exc}")
        raise SystemExit(0)
    if not target_valid:
        print("error\tTUI config must be a JSON object")
        raise SystemExit(0)

# The installed OpenCode/CortexKit TUI uses this list as a UI-extension
# discovery surface. Preserve every existing TUI-only plugin, restore reviewed
# required entries, and replace only overlapping npm package refs with the exact
# version currently selected by the auto-updated opencode.json.
merged = deepcopy(current) if target_valid else {}
if "$schema" not in merged and isinstance(canonical.get("$schema"), str):
    merged["$schema"] = canonical["$schema"]

current_plugins = current.get("plugin") if target_valid else None
if current_plugins is not None and not isinstance(current_plugins, list):
    print("error\tTUI config plugin must be an array")
    raise SystemExit(0)
combined = list(current_plugins or []) + list(required_plugins)
if not all(isinstance(ref, str) and ref for ref in combined):
    print("error\tTUI config plugin entries must be non-empty strings")
    raise SystemExit(0)

effective_plugins = []
seen = set()
syncs = []
for ref in combined:
    identity = managed_identity(ref)
    key = ("package", identity) if identity else ("literal", ref)
    if key in seen:
        continue
    seen.add(key)
    runtime_refs = runtime_by_identity.get(identity, []) if identity else []
    effective = runtime_refs[0] if len(runtime_refs) == 1 else ref
    effective_plugins.append(effective)
    if effective != ref:
        syncs.append(f"{ref}->{effective}")
merged["plugin"] = effective_plugins

if target_valid and current == merged:
    print(f"clean\tTUI plugin surface is current ({len(effective_plugins)} entries)")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "tui.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".tui.json.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

detail = f"; synchronized: {', '.join(syncs)}" if syncs else ""
print(f"repaired\t{backup}; TUI plugin surface restored ({len(effective_plugins)} entries){detail}")
PY_RECOVER_TUI
}

recover_reviewed_router_skills() {
  python3 - "$ROUTER_SKILLS_SOURCE" "$SKILLS_DIR" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_ROUTER_SKILLS'
from pathlib import Path
import os
import shutil
import sys
import tempfile

source = Path(sys.argv[1])
target = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]
manifest = {
    "workflow-route": ("SKILL.md", "references/session-decisions.md"),
    "workflow-odd-secure": ("SKILL.md", "references/odd-and-review.md"),
    "workflow-sdd-secure": ("SKILL.md", "references/sdd-magic-adapter.md"),
    "workflow-systematic": ("SKILL.md", "references/specialists.md"),
}
errors = []
changed = []
for name, files in manifest.items():
    for directory in (source / name, source / name / "references", target / name, target / name / "references"):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            errors.append(f"unsafe skill directory: {directory}")
    entry = source / name / "SKILL.md"
    if not entry.is_file() or entry.is_symlink():
        errors.append(f"missing reviewed skill: {entry}")
        continue
    text = entry.read_text(encoding="utf-8")
    if not text.startswith(f"---\nname: {name}\n") or "\ndescription: " not in text:
        errors.append(f"invalid skill frontmatter: {entry}")
    for relative in files:
        src = source / name / relative
        dest = target / name / relative
        if not src.is_file() or src.is_symlink():
            errors.append(f"missing reviewed skill file: {src}")
        elif dest.is_symlink() or (dest.exists() and not dest.is_file()):
            errors.append(f"unsafe skill destination: {dest}")
        elif not dest.is_file() or dest.read_bytes() != src.read_bytes():
            changed.append((src,dest))
if errors:
    print("error\t" + "; ".join(errors))
    raise SystemExit(0)
if not changed:
    print("clean\tfour reviewed workflow skills and references are current")
    raise SystemExit(0)
backup = backup_root / run_id / "workflow-skills"
backup.mkdir(parents=True, exist_ok=True)
os.chmod(backup_root / run_id, 0o700)
for src,dest in changed:
    if dest.exists():
        saved = backup / dest.relative_to(target)
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest,saved)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".reviewed-skill.",dir=dest.parent)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(src.read_bytes())
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp_path,0o644)
        os.replace(temp_path,dest)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
print(f"repaired\t{backup}: {len(changed)} reviewed skill file(s)")
PY_RECOVER_ROUTER_SKILLS
}

recover_agents_file() {
  python3 - "$AGENTS_FILE" "$AGENTS_SOURCE" "$ROUTING_CANONICAL" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_AGENTS'
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
routing_path = Path(sys.argv[3])
backup_root = Path(sys.argv[4])
run_id = sys.argv[5]
route_start = "<!-- user:workflow-routing -->"
route_end = "<!-- /user:workflow-routing -->"
legacy_start = "<!-- gentle-ai:engram-protocol -->"
legacy_end = "<!-- /gentle-ai:engram-protocol -->"

try:
    canonical_full = source.read_text(encoding="utf-8")
    canonical_route = routing_path.read_text(encoding="utf-8").rstrip("\n")
except FileNotFoundError as exc:
    print(f"error\tcanonical AGENTS source missing: {exc.filename}")
    raise SystemExit(0)

if canonical_full.count(route_start) != 1 or canonical_full.count(route_end) != 1:
    print("error\tcanonical AGENTS source has malformed workflow-routing markers")
    raise SystemExit(0)

def canonical_block(start, end):
    if canonical_full.count(start) != 1 or canonical_full.count(end) != 1:
        print(f"error\tcanonical AGENTS source has malformed {start} markers")
        raise SystemExit(0)
    a = canonical_full.index(start)
    b = canonical_full.index(end, a) + len(end)
    return canonical_full[a:b]

codegraph_start = "<!-- gentle-ai:codegraph-guidance -->"
codegraph_end = "<!-- /gentle-ai:codegraph-guidance -->"
host_start = "<!-- user:host-sdd-runtime-boundaries -->"
host_end = "<!-- /user:host-sdd-runtime-boundaries -->"
cancel_start = "<!-- gentle-ai:subagent-cancellation -->"
cancel_end = "<!-- /gentle-ai:subagent-cancellation -->"
search_start = "<!-- user:grep-tool-enforcement -->"
search_end = "<!-- /user:grep-tool-enforcement -->"
canonical_codegraph = canonical_block(codegraph_start, codegraph_end)
canonical_host = canonical_block(host_start, host_end)
canonical_cancel = canonical_block(cancel_start, cancel_end)
canonical_search = canonical_block(search_start, search_end)

if target.is_file():
    try:
        current = target.read_text(encoding="utf-8")
    except Exception:
        current = ""
else:
    current = ""

new_text = current
fallback_reason = ""
if not current:
    new_text = canonical_full
    fallback_reason = "missing or unreadable active AGENTS.md"
else:
    # Remove only the precisely marked Gentle AI legacy protocol. Unmarked user
    # prose is preserved. Ambiguous marker state falls back to the reviewed full
    # source rather than guessing deletion boundaries.
    ls = new_text.count(legacy_start)
    le = new_text.count(legacy_end)
    if ls == 1 and le == 1 and new_text.index(legacy_start) < new_text.index(legacy_end):
        pattern = re.escape(legacy_start) + r".*?" + re.escape(legacy_end) + r"\n*"
        new_text = re.sub(pattern, "", new_text, count=1, flags=re.DOTALL)
    elif ls or le:
        new_text = canonical_full
        fallback_reason = "ambiguous legacy Engram markers"

    if not fallback_reason:
        starts = new_text.count(route_start)
        ends = new_text.count(route_end)
        if starts == 0 and ends == 0:
            pass
        elif starts == 1 and ends == 1 and new_text.index(route_start) < new_text.index(route_end):
            a = new_text.index(route_start)
            b = new_text.index(route_end, a) + len(route_end)
            new_text = new_text[:a] + new_text[b:]
        else:
            new_text = canonical_full
            fallback_reason = "ambiguous workflow-routing markers"

# Recover only reviewed bounded sections; keep other Gentle AI managed prose,
# generated instructions and unrelated user blocks intact. Unknown or
# partially marked sections fail closed instead of replacing all AGENTS.md.
def replace_marked(text, start, end, canonical, insert_before=None):
    starts, ends = text.count(start), text.count(end)
    if starts == ends == 1 and text.index(start) < text.index(end):
        a = text.index(start)
        b = text.index(end, a) + len(end)
        return text[:a] + canonical + text[b:]
    if starts == ends == 0 and insert_before and text.count(insert_before) == 1:
        a = text.index(insert_before)
        return text[:a] + canonical + "\n\n" + text[a:]
    raise ValueError(f"ambiguous AGENTS section: {start} ({starts} starts, {ends} ends)")

try:
    new_text = replace_marked(new_text, codegraph_start, codegraph_end,
                              canonical_codegraph, "<!-- gentle-ai:persona -->")
    # Repair the previously shipped duplicate closing marker only when its
    # first close precedes the known review extension and the last follows it.
    if new_text.count(cancel_start) == 1 and new_text.count(cancel_end) == 2:
        first = new_text.index(cancel_end)
        second = new_text.index(cancel_end, first + len(cancel_end))
        review = new_text.find("### Review process (extends the rule above)")
        if new_text.index(cancel_start) < first < review < second:
            new_text = new_text[:first] + new_text[first + len(cancel_end):]
    new_text = replace_marked(new_text, cancel_start, cancel_end,
                              canonical_cancel, "<!-- user:grep-tool-enforcement -->")
    new_text = replace_marked(new_text, search_start, search_end,
                              canonical_search, "<!-- user:workflow-routing -->")
    if new_text.count(host_start) == new_text.count(host_end) == 0:
        legacy_heading = "### Host-side SDD runtime and review boundaries\n"
        if new_text.count(legacy_heading) == 1:
            a = new_text.index(legacy_heading)
            b = new_text.find("\n## Personality", a)
            if b < 0:
                raise ValueError("host SDD runtime section has no Personality boundary")
            new_text = new_text[:a] + canonical_host + new_text[b:]
        elif new_text.count(legacy_heading) == 0:
            new_text = replace_marked(new_text, host_start, host_end,
                                      canonical_host, "## Personality")
        else:
            raise ValueError("multiple unmarked host SDD runtime sections")
    else:
        new_text = replace_marked(new_text, host_start, host_end, canonical_host)
except ValueError as exc:
    print(f"error\tAGENTS bounded-section recovery refused: {exc}")
    raise SystemExit(0)

# Put reviewed user-owned routing after the generator's managed guidance. This
# keeps secure delegation and the Magic Context ODD mirror authoritative after
# a Gentle AI v3 sync, which otherwise reintroduces host-inline/Engram prose.
if new_text.count(route_start) == 1 and new_text.count(route_end) == 1:
    a = new_text.index(route_start)
    b = new_text.index(route_end, a) + len(route_end)
    new_text = new_text[:a] + new_text[b:]
new_text = new_text.rstrip() + "\n\n" + canonical_route + "\n"

if new_text == current:
    print("clean\treviewed AGENTS routing and memory policy are current")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "AGENTS.md.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".AGENTS.md.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(new_text.rstrip("\n") + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

detail = f"{backup}"
if fallback_reason:
    detail += f" (full-source fallback: {fallback_reason})"
print(f"repaired\t{detail}")
PY_RECOVER_AGENTS
}

recover_systematic_config() {
  python3 - "$SYSTEMATIC_CONFIG" "$SYSTEMATIC_CONFIG_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_SYSTEMATIC'
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]

def parse_jsonc(path):
    text = path.read_text(encoding="utf-8")
    out = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            i = end + 2
            continue
        out.append(ch)
        i += 1
    stripped = "".join(out)
    stripped = re.sub(r",\s*([}\]])", r"\1", stripped)
    return json.loads(stripped)

try:
    canonical = parse_jsonc(source)
except FileNotFoundError:
    print(f"error\tcanonical Systematic source missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical Systematic source is invalid: {exc}")
    raise SystemExit(0)

if not isinstance(canonical, dict) or not isinstance(canonical.get("categories"), dict) or not isinstance(canonical.get("agents"), dict):
    print("error\tcanonical Systematic source lacks categories/agents overlays")
    raise SystemExit(0)

# Systematic rejects `tools` in its agents overlays and disables all bundled
# agents when configuration validation fails. Refuse a bad reviewed source
# before recovery can deploy it to a working OpenCode installation.
for name, overlay in canonical["agents"].items():
    if isinstance(overlay, dict) and "tools" in overlay:
        print(f"error\tSYSTEMATIC_UNSUPPORTED_AGENT_TOOLS: {name}; remove tools from reviewed Systematic source")
        raise SystemExit(0)

current = {}
target_valid = False
if target.is_file():
    try:
        current = parse_jsonc(target)
        target_valid = isinstance(current, dict)
    except Exception:
        target_valid = False

# Preserve unknown future top-level settings, but the reviewed schema,
# categories, agents, profiles, and policy controls remain authoritative.
merged = deepcopy(current) if target_valid else {}
for key, value in canonical.items():
    merged[key] = deepcopy(value)

# Profiles are reviewed routing policy, not an unknown forward-compatible key.
# If the canonical source intentionally has no profiles map, remove any older
# map (including the retired global astra-critical profile) during recovery.
if "profiles" not in canonical:
    merged.pop("profiles", None)

# Systematic 3.16 permits an active named profile. Preserve only a selection
# that names a reviewed canonical profile; discard stale or unknown selections.
selected = current.get("profile") if target_valid else None
profiles = canonical.get("profiles")
if isinstance(selected, str) and isinstance(profiles, dict) and selected in profiles:
    merged["profile"] = selected
else:
    merged.pop("profile", None)

if target_valid and current == merged:
    detail = "reviewed Systematic overlays are current"
    if isinstance(selected, str):
        detail += f"; active profile={selected}"
    print(f"clean\t{detail}")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "systematic.jsonc.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".systematic.jsonc.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print(f"repaired\t{backup}")
PY_RECOVER_SYSTEMATIC
}

recover_fallback_policy() {
  python3 - "$FALLBACK_POLICY_DEPLOYED" "$FALLBACK_POLICY_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_FALLBACK'
from pathlib import Path
import json
import os
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]

try:
    canonical_bytes = source.read_bytes()
    parsed = json.loads(canonical_bytes)
except FileNotFoundError:
    print(f"error\tcanonical fallback policy missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical fallback policy is invalid: {exc}")
    raise SystemExit(0)
if not isinstance(parsed, dict):
    print("error\tcanonical fallback policy must be a JSON object")
    raise SystemExit(0)

if target.is_file() and target.read_bytes() == canonical_bytes:
    print("clean\treviewed fallback policy is current")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "rate-limit-fallback.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".rate-limit-fallback.json.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(canonical_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print(f"repaired\t{backup}")
PY_RECOVER_FALLBACK
}


read_verify_script_pin() {
  local path="$1"
  python3 - "$path" <<'PY_VERIFY_PIN'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
try:
    text = path.read_text(encoding="utf-8")
except Exception:
    raise SystemExit(1)

# Accept normal TypeScript formatting, including line breaks around '=' and the
# quoted digest. Require a real const assignment ending in ';' so comments or
# documentation examples cannot satisfy the verifier accidentally.
match = re.search(
    r'''\bconst\s+VERIFY_SCRIPT_SHA256\s*=\s*(["'])(([0-9a-fA-F]{64}))\1\s*;''',
    text,
    flags=re.MULTILINE,
)
if not match:
    raise SystemExit(1)
print(match.group(2).lower())
PY_VERIFY_PIN
}

# Put temporary probe files under the user's cache when possible. This avoids
# project-local OpenCode config discovery while remaining writable in the
# normal and Nono-secured OpenCode environments.
TMP_BASE="${XDG_CACHE_HOME:-/home/james/.cache}/workflow-health-check"
if ! mkdir -p "$TMP_BASE" 2>/dev/null; then
  TMP_BASE="/tmp/workflow-health-check"
  mkdir -p "$TMP_BASE" 2>/dev/null || true
fi
TMP_DIR=$(mktemp -d "$TMP_BASE/run.XXXXXX" 2>/dev/null || mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ROUTING_CANONICAL="$TMP_DIR/routing-section.md"
ROUTING_CONTRACT="$TMP_DIR/secure-routing-contract.md"
SYSTEMATIC_CHECKER="$TMP_DIR/check-systematic-resolution.cjs"
RUNTIME_AGENT_CHECKER="$TMP_DIR/check-runtime-agents.cjs"
AGENT_LIST_OUT="$TMP_DIR/opencode-agent-list.txt"
AGENT_LIST_STDERR="$TMP_DIR/opencode-agent-list.stderr"
DEBUG_AGENT_DIR="$TMP_DIR/debug-agents"
PROBE_CWD="$TMP_DIR/neutral-cwd"
# Systematic registers agents for the active project. Use the reviewed repo
# for registration probes; keep the neutral directory for behavioural probes.
AGENT_PROBE_CWD="$WORKSPACE"
PARALLEL_EVENTS="$TMP_DIR/parallel-dispatch.ndjson"
PARALLEL_STDERR="$TMP_DIR/parallel-dispatch.stderr"
PARALLEL_CHECKER="$TMP_DIR/check-parallel-dispatch.py"
mkdir -p "$PROBE_CWD" "$DEBUG_AGENT_DIR"

cat > "$ROUTING_CANONICAL" <<'EOF_ROUTING'
<!-- user:workflow-routing -->
## Secure workflow router (MANDATORY)

This global user-owned block is a lightweight entrypoint. Keep `/home/james/ai-workspace/workflow_optimisation/WORKFLOW.md` as the single task-class and route policy. On every new user task, before choosing a phase or specialist, call the native `skill({name:"workflow-route"})` tool and follow its classification; after a long-chat compaction/resume or meaningful scope change, load it again and reconcile the route. Read the current recipe with an authorized read-only tool when the skill requests it. The absence of `skill` or a required named Task tool blocks dependent mutation; do not substitute inline execution. A read-only response may explain the limitation.

Before any writer, establish explicit change intent, and check project registration using only the reviewed `host_register_project` path when required. The `gentle-orchestrator` is a read-only technical lead: no host Bash or project edit/write, no sandbox mutation/lifecycle authority. Every project mutation/execution goes to an authorized sandbox worker, including an upstream inline one-file fix. Do not weaken `grep: ask` or the host/sandbox permission overlays. Read-only requests have no writer or ODD tracker.

Use the router's selected adapters: `workflow-odd-secure` for authorized default ODD, `workflow-sdd-secure` only when SDD is explicitly requested or accepted, and `workflow-systematic` when the route invokes its installed skills. The selected Systematic, SDD, frontend and review skills keep their named agent precedence. No file-count or risk threshold automatically selects SDD. For substantial ODD record route/trigger evidence and actual Task dispatch in the task file and complete Magic Context mirror before claiming progress; on long-chat resume read both. Any commit intended for native RDD must carry the staged reviewability receipt and obey the local per-commit line/byte cap defined by `workflow-odd-secure`; native Gentle AI START remains the final 200 KiB serialized-input authority. Gentle AI 3.5 RDD defaults on when unset: read effective mode and deciding source per project; never toggle it automatically, and honor explicit off. Native review remains user-owned and separate from SDD. Fail closed when the requested specialist or safe tool surface is unavailable.

Before coding, honor the per-project/session local-vs-cloud writing-model choice already specified in the canonical recipe; never silently reuse an unknown decision. Astra is a user-selectable upgrade only for Sol-assigned non-implementation phases on extremely critical changes; recommend it with a concrete reason and never assign it to an implementation worker or edit global config to select it. The active model and plugin permissions remain in `opencode.json`.

Emit `ROUTE: <class> | intent: <read-only/authorized change> | route: <skill/phase> | specialist: <name> | basis: WORKFLOW.md`. A route line alone does not prove execution: verify loaded skill, named Task result and relevant checks. Keep user-facing terminal commands Fish-compatible.
<!-- /user:workflow-routing -->
EOF_ROUTING

cat > "$PARALLEL_CHECKER" <<'PY_PARALLEL'
import json
import sys

path = sys.argv[1]
by_call = {}

with open(path, "r", encoding="utf-8", errors="replace") as fh:
    for raw in fh:
        raw = raw.strip()
        if not raw or not raw.startswith("{"):
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        part = event.get("part")
        if not isinstance(part, dict):
            continue
        if part.get("tool") != "task":
            continue

        state = part.get("state")
        if not isinstance(state, dict):
            continue

        inp = state.get("input")
        if not isinstance(inp, dict):
            inp = {}
        agent = inp.get("subagent_type")
        call_id = part.get("callID") or part.get("id") or f"anon:{len(by_call)}"
        rec = by_call.setdefault(call_id, {
            "agent": agent,
            "message": part.get("messageID"),
            "child": None,
            "start": None,
            "end": None,
            "statuses": set(),
        })
        if agent:
            rec["agent"] = agent
        if part.get("messageID"):
            rec["message"] = part.get("messageID")

        metadata = state.get("metadata")
        if isinstance(metadata, dict):
            rec["child"] = metadata.get("sessionId") or metadata.get("sessionID") or rec["child"]

        timing = state.get("time")
        if isinstance(timing, dict):
            start = timing.get("start")
            end = timing.get("end")
            if isinstance(start, (int, float)):
                rec["start"] = start if rec["start"] is None else min(rec["start"], start)
            if isinstance(end, (int, float)):
                rec["end"] = end if rec["end"] is None else max(rec["end"], end)

        status = state.get("status")
        if isinstance(status, str):
            rec["statuses"].add(status)
            stamp = event.get("timestamp")
            if isinstance(stamp, (int, float)):
                if status == "running":
                    rec["start"] = stamp if rec["start"] is None else min(rec["start"], stamp)
                elif status in {"completed", "error"}:
                    rec["end"] = stamp if rec["end"] is None else max(rec["end"], stamp)

wanted = {}
for rec in by_call.values():
    if rec["agent"] in {"explore", "general"}:
        wanted[rec["agent"]] = rec

missing = [name for name in ("explore", "general") if name not in wanted]
if missing:
    print("   !! PARALLEL_DISPATCH_MISSING: no Task call observed for " + ", ".join(missing))
    sys.exit(1)

a = wanted["explore"]
b = wanted["general"]

if not a["message"] or not b["message"] or a["message"] != b["message"]:
    print("   !! PARALLEL_DISPATCH_SERIALIZED: the two Task calls were not emitted from the same parent assistant message")
    print(f"      explore message={a['message']!r}; general message={b['message']!r}")
    sys.exit(1)

if a["child"] and b["child"] and a["child"] == b["child"]:
    print("   !! PARALLEL_DISPATCH_INVALID: both Task calls report the same child session")
    sys.exit(1)

timed = all(isinstance(x, (int, float)) for x in (a["start"], a["end"], b["start"], b["end"]))
if timed:
    overlaps = a["start"] < b["end"] and b["start"] < a["end"]
    if not overlaps:
        print("   !! PARALLEL_DISPATCH_SERIALIZED: Task execution intervals do not overlap")
        print(f"      explore={a['start']}..{a['end']}; general={b['start']}..{b['end']}")
        sys.exit(1)
    print("   ok: behavioural fan-out emitted both Task calls in one assistant message and execution intervals overlap")
else:
    print("   ok: behavioural fan-out emitted both independent Task calls in one assistant message")
    print("      note: this OpenCode JSON stream did not expose complete child timing metadata; same-message fan-out is the concurrency contract")

if a["child"] or b["child"]:
    print(f"      child sessions: explore={a['child'] or '<not surfaced>'}, general={b['child'] or '<not surfaced>'}")
PY_PARALLEL

cat > "$SYSTEMATIC_CHECKER" <<'EOF_NODE'
const fs = require("fs")
const path = require("path")

const nodeModules = process.env.SYSTEMATIC_NODE_MODULES
if (!nodeModules) {
  console.error("missing SYSTEMATIC_NODE_MODULES")
  process.exit(2)
}

let jsonc
try {
  jsonc = require(path.join(nodeModules, "jsonc-parser"))
} catch (error) {
  console.error(`cannot load jsonc-parser from ${nodeModules}: ${error.message}`)
  process.exit(2)
}

const [configPath, agentsRoot, resolvedConfigPath, openCodeConfigPath] = process.argv.slice(2)
const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj ?? {}, key)

function parseJsonc(file) {
  const text = fs.readFileSync(file, "utf8")
  const errors = []
  const value = jsonc.parse(text, errors, {
    allowTrailingComma: true,
    disallowComments: false,
  })
  if (errors.length > 0) {
    const detail = errors
      .map((e) => `${jsonc.printParseErrorCode(e.error)}@${e.offset}`)
      .join(", ")
    throw new Error(`${file}: JSONC parse errors: ${detail}`)
  }
  return value
}

function isDiscoverableMarkdown(fileName) {
  // Mirror Systematic's own discovery contract: README.md is directory
  // documentation, never a dispatchable bundled agent.
  return fileName.endsWith(".md") && fileName.toLowerCase() !== "readme.md"
}

function declaredToolsFromAgentMarkdown(file) {
  let text
  try {
    text = fs.readFileSync(file, "utf8")
  } catch {
    return []
  }
  const fm = text.match(/^---\s*\n([\s\S]*?)\n---/)
  if (!fm) return []
  const match = fm[1].match(/^tools:\s*(.+)$/mi)
  if (!match) return []
  return match[1]
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean)
}

function walkMarkdown(root, current = root, out = [], depth = 0, maxDepth = 2) {
  if (!fs.existsSync(current) || depth > maxDepth) return out
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name)
    if (entry.isDirectory()) {
      walkMarkdown(root, full, out, depth + 1, maxDepth)
    } else if (entry.isFile() && isDiscoverableMarkdown(entry.name)) {
      const rel = path.relative(root, full)
      const parts = rel.split(path.sep)
      const name = path.basename(entry.name, ".md")
      const category = parts.length > 1 ? parts[0] : ""
      const declaredTools = declaredToolsFromAgentMarkdown(full)
      const declaresMutation = declaredTools.includes("edit") || declaredTools.includes("write")
      out.push({ name, category, rel, declaredTools, declaresMutation })
    }
  }
  return out
}

function exactOverlayFor(config, agent) {
  const overlays = config.agents && typeof config.agents === "object" ? config.agents : {}
  const candidates = []
  if (hasOwn(overlays, agent.name)) candidates.push([agent.name, overlays[agent.name]])
  const qualified = agent.category ? `${agent.category}/${agent.name}` : agent.name
  if (qualified !== agent.name && hasOwn(overlays, qualified)) {
    candidates.push([qualified, overlays[qualified]])
  }
  return candidates
}

function applyOverlay(state, overlay) {
  if (!overlay || typeof overlay !== "object" || Array.isArray(overlay)) return

  // Mirrors current Systematic overlay semantics: setting a model without a
  // variant clears any lower-precedence variant. model:null restores inheritance.
  if (hasOwn(overlay, "model")) {
    if (!hasOwn(overlay, "variant")) state.variant = undefined
    state.model = overlay.model === null ? undefined : overlay.model
  }
  if (hasOwn(overlay, "variant")) {
    state.variant = overlay.variant == null ? undefined : overlay.variant
  }
  if (hasOwn(overlay, "disable")) state.disable = overlay.disable === true
}

function applyOpenCodeOverlay(state, overlay) {
  // v3.16 precedence within one layer: harness-specific values override flat.
  applyOverlay(state, overlay)
  applyOverlay(state, overlay?.opencode)
}

function expectedFor(config, agent, exactOverlay) {
  const state = { model: undefined, variant: undefined, disable: false }
  const categories = config.categories && typeof config.categories === "object" ? config.categories : {}
  if (agent.category && hasOwn(categories, agent.category)) {
    applyOpenCodeOverlay(state, categories[agent.category])
  }
  applyOpenCodeOverlay(state, exactOverlay)

  // Systematic 3.16 named profiles are sparse overlays on the base config.
  // Apply a reviewed active profile after the base category/agent layers.
  const activeProfile = typeof config.profile === "string" ? config.profiles?.[config.profile] : undefined
  if (activeProfile && typeof activeProfile === "object" && !Array.isArray(activeProfile)) {
    if (agent.category && hasOwn(activeProfile.categories, agent.category)) {
      applyOpenCodeOverlay(state, activeProfile.categories[agent.category])
    }
    const profileMatches = exactOverlayFor(activeProfile, agent)
    if (profileMatches.length === 1) applyOpenCodeOverlay(state, profileMatches[0][1])
  }

  const disabled = Array.isArray(config.disabled_agents) ? config.disabled_agents : []
  if (disabled.includes(agent.name) || (agent.category && disabled.includes(`${agent.category}/${agent.name}`))) {
    state.disable = true
  }
  return state
}

function normalizeResolvedModel(value) {
  if (typeof value === "string") return value
  if (value && typeof value === "object") {
    const providerID = value.providerID ?? value.providerId
    const modelID = value.modelID ?? value.modelId
    if (typeof providerID === "string" && typeof modelID === "string") {
      return `${providerID}/${modelID}`
    }
  }
  return undefined
}

function show(value) {
  return value === undefined ? "<inherit/none>" : JSON.stringify(value)
}

let config
try {
  config = parseJsonc(configPath)
} catch (error) {
  console.error(`   !! ${error.message}`)
  process.exit(1)
}

const inventory = walkMarkdown(agentsRoot).sort((a, b) => a.name.localeCompare(b.name))
if (inventory.length === 0) {
  console.error(`   !! no bundled Systematic agents found under ${agentsRoot}`)
  process.exit(1)
}

const inventoryByName = new Map()
for (const agent of inventory) {
  if (inventoryByName.has(agent.name)) {
    console.error(`   !! duplicate bundled agent stem: ${agent.name}`)
    process.exit(1)
  }
  inventoryByName.set(agent.name, agent)
}

const categoriesInBundle = new Set(inventory.map((a) => a.category).filter(Boolean))
const configuredCategories = config.categories && typeof config.categories === "object"
  ? Object.keys(config.categories)
  : []
const configuredAgents = config.agents && typeof config.agents === "object"
  ? Object.keys(config.agents)
  : []

let failed = false

for (const [name,overlay] of Object.entries(config.agents??{})) {
  if (overlay && typeof overlay==="object" && Object.hasOwn(overlay,"tools")) {
    console.error(`   !! SYSTEMATIC_UNSUPPORTED_AGENT_TOOLS: ${name}; Systematic rejects tools under agents`)
    failed=true
  }
}

for (const category of configuredCategories) {
  if (!categoriesInBundle.has(category)) {
    console.error(`   !! stale/unknown Systematic category in config: ${category}`)
    failed = true
  }
}

const consumedAgentKeys = new Set()
const expectations = []

for (const agent of inventory) {
  const matches = exactOverlayFor(config, agent)
  if (matches.length === 0) {
    console.error(`   !! bundled Systematic agent has no explicit agents.* overlay: ${agent.name} (${agent.category || "uncategorized"})`)
    failed = true
    continue
  }
  if (matches.length > 1) {
    console.error(`   !! duplicate overlays target ${agent.name}: ${matches.map(([key]) => key).join(", ")}`)
    failed = true
    continue
  }

  const [key, exact] = matches[0]
  consumedAgentKeys.add(key)
  expectations.push({ agent, expected: expectedFor(config, agent, exact) })
}

for (const key of configuredAgents) {
  if (!consumedAgentKeys.has(key)) {
    console.error(`   !! stale/unknown Systematic agent overlay in config: ${key}`)
    failed = true
  }
}

const profiles = config.profiles && typeof config.profiles === "object" && !Array.isArray(config.profiles)
  ? config.profiles
  : {}
if (hasOwn(profiles, "astra-critical")) {
  console.error("   !! retired global Systematic profile remains: astra-critical; use per-session Sol-role Astra aliases")
  failed = true
}
if (hasOwn(config, "profile") && (typeof config.profile !== "string" || !hasOwn(profiles, config.profile))) {
  console.error(`   !! active Systematic profile is missing or unknown: ${show(config.profile)}`)
  failed = true
}
for (const [profileName, profile] of Object.entries(profiles)) {
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
    console.error(`   !! Systematic profile ${profileName} must be an object`)
    failed = true
    continue
  }
  const profileAgents = profile.agents && typeof profile.agents === "object" && !Array.isArray(profile.agents)
    ? profile.agents
    : {}
  for (const key of Object.keys(profileAgents)) {
    const plain = key.includes("/") ? key.slice(key.lastIndexOf("/") + 1) : key
    if (!inventoryByName.has(plain)) {
      console.error(`   !! stale/unknown Systematic agent in profile ${profileName}: ${key}`)
      failed = true
    }
    if (profileAgents[key]?.permission !== undefined) {
      console.error(`   !! Systematic profile ${profileName}.${key} must not override security permissions`)
      failed = true
    }
  }
  if (profile.categories && Object.values(profile.categories).some((value) => value?.permission !== undefined)) {
    console.error(`   !! Systematic profile ${profileName} must not override category security permissions`)
    failed = true
  }
}

const systematicText = JSON.stringify(config)
for (const retiredModel of [
  "muse-spark-1.2-contributor",
  "muse-spark-1.3-contributor",
  "deepseek-v4-pro",
  "deepseek-v4-flash-vision-exp",
  "deepseek-v4-flash",
]) {
  if (systematicText.includes(retiredModel)) {
    console.error(`   !! retired Muse/DeepSeek model remains in systematic.jsonc: ${retiredModel}`)
    failed = true
  }
}

// User-owned Systematic security policy belongs in systematic.jsonc, not in
// same-name opencode.json agent stubs (which suppress bundled agent emission).
// Every category fails closed for mutation; exact mutator overlays may then
// opt into worker-local sandbox capabilities.
const categoryMutationDenies = [
  "edit", "write", "sandbox_bash", "sandbox_edit", "sandbox_write",
  "sandbox_apply_patch", "sandbox_apply", "sandbox_copy_in",
  "sandbox_copy_out", "sandbox_discard", "sandbox_finish",
]
for (const category of categoriesInBundle) {
  const overlay = config.categories?.[category]
  const permission = overlay && typeof overlay === "object" ? overlay.permission : undefined
  if (!permission || typeof permission !== "object" || Array.isArray(permission)) {
    console.error(`   !! Systematic category ${category} lacks a permission overlay`)
    failed = true
    continue
  }
  for (const tool of categoryMutationDenies) {
    if (permission[tool] !== "deny") {
      console.error(`   !! Systematic category ${category}.permission.${tool} must be deny`)
      failed = true
    }
  }
}

const systematicMemoryPolicy = {
  workflow: "allow",
  research: "allow",
  design: "allow",
  review: "deny",
  "document-review": "deny",
}
for (const category of categoriesInBundle) {
  const expected = systematicMemoryPolicy[category]
  if (!expected) {
    console.error(`   !! Systematic memory policy has no classification for category ${category}`)
    failed = true
    continue
  }
  const permission = config.categories?.[category]?.permission
  if (!permission || permission.ctx_memory !== expected) {
    console.error(`   !! Systematic category ${category}.permission.ctx_memory must be ${expected}`)
    failed = true
  }
}

const systematicMutators = inventory.filter((agent) => agent.declaresMutation)
const writerAllows = [
  "sandbox_read", "sandbox_list", "sandbox_grep", "sandbox_diff",
  "sandbox_bash", "sandbox_edit", "sandbox_write", "sandbox_apply_patch",
]
const writerBoundaryAsk = [
  "sandbox_apply", "sandbox_copy_in", "sandbox_copy_out",
  "sandbox_discard", "sandbox_finish",
]
for (const agent of systematicMutators) {
  const matches = exactOverlayFor(config, agent)
  if (matches.length !== 1) continue
  const permission = matches[0][1]?.permission
  if (!permission || typeof permission !== "object" || Array.isArray(permission)) {
    console.error(`   !! Systematic mutator ${agent.name} lacks an exact permission overlay`)
    failed = true
    continue
  }
  for (const tool of ["edit", "write", "bash"]) {
    if (permission[tool] !== "deny") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be deny`)
      failed = true
    }
  }
  for (const tool of writerAllows) {
    if (permission[tool] !== "allow") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be allow`)
      failed = true
    }
  }
  for (const tool of writerBoundaryAsk) {
    if (permission[tool] !== "ask") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be ask`)
      failed = true
    }
  }
}

for (const item of expectations) {
  if (!item.expected.disable && typeof item.expected.model !== "string") {
    console.error(`   !! Systematic agent ${item.agent.name} has no effective explicit model assignment`)
    failed = true
  }
}

if (failed) process.exit(1)

console.log(`   ok: ${inventory.length}/${inventory.length} bundled agents have explicit model overlays; no stale agent/category entries`)
console.log(`   ok: ${systematicMutators.length} bundled Edit/Write personas are sandbox-routed by systematic.jsonc permission overlays`)
process.exit(0)


EOF_NODE

cat > "$RUNTIME_AGENT_CHECKER" <<'EOF_RUNTIME_AGENT'
const fs = require("fs")
const path = require("path")

const nodeModules = process.env.SYSTEMATIC_NODE_MODULES
if (!nodeModules) {
  console.error("   !! missing SYSTEMATIC_NODE_MODULES")
  process.exit(2)
}
let jsonc
try {
  jsonc = require(path.join(nodeModules, "jsonc-parser"))
} catch (error) {
  console.error(`   !! cannot load jsonc-parser from ${nodeModules}: ${error.message}`)
  process.exit(2)
}

const [systematicConfigPath, agentsRoot, agentListPath, debugDir, openCodeConfigPath, fallbackPolicySourcePath] = process.argv.slice(2)
const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj ?? {}, key)
let failures = 0
function fail(msg) { console.error(`   !! ${msg}`); failures++ }
function show(value) { return value === undefined ? "<inherit/none>" : JSON.stringify(value) }

function parseJsonc(file) {
  const text = fs.readFileSync(file, "utf8")
  const errors = []
  const value = jsonc.parse(text, errors, { allowTrailingComma: true, disallowComments: false })
  if (errors.length) throw new Error(`${file}: JSONC parse error`)
  return value
}
function isDiscoverableMarkdown(name) { return name.endsWith(".md") && name.toLowerCase() !== "readme.md" }
function declaredTools(file) {
  const text = fs.readFileSync(file, "utf8")
  const fm = text.match(/^---\s*\n([\s\S]*?)\n---/)
  if (!fm) return []
  const m = fm[1].match(/^tools:\s*(.+)$/mi)
  return m ? m[1].split(",").map((x) => x.trim().toLowerCase()).filter(Boolean) : []
}
function walkAgents(root, current=root, out=[], depth=0) {
  if (!fs.existsSync(current) || depth > 2) return out
  for (const entry of fs.readdirSync(current, {withFileTypes:true})) {
    const full=path.join(current,entry.name)
    if (entry.isDirectory()) walkAgents(root,full,out,depth+1)
    else if (entry.isFile() && isDiscoverableMarkdown(entry.name)) {
      const rel=path.relative(root,full); const parts=rel.split(path.sep)
      const tools=declaredTools(full)
      out.push({name:path.basename(entry.name,".md"), category:parts.length>1?parts[0]:"", declaresMutation:tools.includes("edit")||tools.includes("write")})
    }
  }
  return out
}
function exactOverlay(config, agent) {
  const overlays=config.agents && typeof config.agents==="object" ? config.agents : {}
  const qualified=agent.category ? `${agent.category}/${agent.name}` : agent.name
  if (hasOwn(overlays,qualified)) return overlays[qualified]
  if (hasOwn(overlays,agent.name)) return overlays[agent.name]
  return undefined
}
function applyModelOverlay(state, overlay) {
  if (!overlay || typeof overlay!=="object" || Array.isArray(overlay)) return
  if (hasOwn(overlay,"model")) {
    if (!hasOwn(overlay,"variant")) state.variant=undefined
    state.model=overlay.model===null?undefined:overlay.model
  }
  if (hasOwn(overlay,"variant")) state.variant=overlay.variant==null?undefined:overlay.variant
  if (hasOwn(overlay,"disable")) state.disable=overlay.disable===true
}
function applyOpenCodeModelOverlay(state, overlay) {
  applyModelOverlay(state, overlay)
  applyModelOverlay(state, overlay?.opencode)
}
function expectedFor(config, agent) {
  const state={model:undefined,variant:undefined,disable:false}
  if (agent.category) applyOpenCodeModelOverlay(state, config.categories?.[agent.category])
  applyOpenCodeModelOverlay(state, exactOverlay(config,agent))
  const activeProfile=typeof config.profile==="string" ? config.profiles?.[config.profile] : undefined
  if (activeProfile && typeof activeProfile==="object" && !Array.isArray(activeProfile)) {
    if (agent.category) applyOpenCodeModelOverlay(state, activeProfile.categories?.[agent.category])
    applyOpenCodeModelOverlay(state, exactOverlay(activeProfile,agent))
  }
  const disabled=Array.isArray(config.disabled_agents)?config.disabled_agents:[]
  if (disabled.includes(agent.name) || (agent.category && disabled.includes(`${agent.category}/${agent.name}`))) state.disable=true
  return state
}
function normalizeModel(value) {
  if (typeof value==="string") return value
  if (value && typeof value==="object") {
    const provider=value.providerID ?? value.providerId
    const model=value.modelID ?? value.modelId
    if (typeof provider==="string" && typeof model==="string") return `${provider}/${model}`
  }
  return undefined
}
// Provider aliases do not establish review independence: OpenAI and Go Luna
// are the same family, as are direct and Go DeepSeek Flash.
function modelFamily(value) {
  const model=normalizeModel(value)?.split("/").slice(1).join("/").toLowerCase()
  if (!model) return undefined
  if (/(^|\/)gpt-[0-9]/.test(model)) return "gpt"
  if (model.includes("deepseek")) return "deepseek"
  if (model.includes("glm-")) return "glm"
  if (model.includes("qwen")) return "qwen"
  if (model.includes("kimi")) return "kimi"
  return undefined
}
const debugCache = new Map()

function stripAnsi(text) {
  return text.replace(/\x1B\[[0-?]*[ -\/]*[@-~]/g, "")
}

// `opencode debug agent` writes the agent JSON to stdout, but plugins loaded
// during startup may also write informational lines to stdout before it. Treat
// stdout as a mixed diagnostic stream rather than assuming the whole file is
// JSON. Extract a balanced top-level JSON object whose shape is the debug-agent
// payload. This deliberately does not suppress or reinterpret plugin chatter.
function parseDebugAgentStream(text) {
  const clean = stripAnsi(text)

  // Fast path for runtimes with clean stdout.
  try {
    const value = JSON.parse(clean.trim())
    if (value && typeof value === "object" && !Array.isArray(value) && value.tools && typeof value.tools === "object") return value
  } catch {}

  const starts = []
  const lineStart = /(?:^|\n)[\t ]*\{/g
  let match
  while ((match = lineStart.exec(clean)) !== null) {
    const brace = clean.indexOf("{", match.index)
    if (brace >= 0) starts.push(brace)
  }

  // Fallback for a runtime/plugin that writes a prefix and JSON on one line.
  if (starts.length === 0) {
    for (let i = 0; i < clean.length; i++) if (clean[i] === "{") starts.push(i)
  }

  for (const start of starts) {
    let depth = 0
    let inString = false
    let escaped = false
    for (let i = start; i < clean.length; i++) {
      const ch = clean[i]
      if (inString) {
        if (escaped) escaped = false
        else if (ch === "\\") escaped = true
        else if (ch === '"') inString = false
        continue
      }
      if (ch === '"') { inString = true; continue }
      if (ch === "{") depth++
      else if (ch === "}") {
        depth--
        if (depth === 0) {
          try {
            const value = JSON.parse(clean.slice(start, i + 1))
            if (value && typeof value === "object" && !Array.isArray(value) && value.tools && typeof value.tools === "object") return value
          } catch {}
          break
        }
      }
    }
  }
  return undefined
}

function readDebug(name) {
  if (debugCache.has(name)) return debugCache.get(name)
  const file=path.join(debugDir,`${name}.json`)
  if (!fs.existsSync(file)) {
    fail(`RUNTIME_AGENT_PROBE_MISSING: no debug-agent stdout for ${name}`)
    debugCache.set(name, undefined)
    return undefined
  }
  const raw=fs.readFileSync(file,"utf8")
  const value=parseDebugAgentStream(raw)
  if (!value) {
    const preview=stripAnsi(raw).replace(/\s+/g," ").trim().slice(0,180)
    fail(`RUNTIME_AGENT_PROBE_INVALID: ${name}: no debug-agent JSON object found in mixed stdout${preview ? `; prefix=${JSON.stringify(preview)}` : ""}`)
    debugCache.set(name, undefined)
    return undefined
  }
  debugCache.set(name, value)
  return value
}
function tool(debug, name) { return debug?.tools && typeof debug.tools==="object" ? debug.tools[name] : undefined }

// `opencode debug agent` exposes both the agent permission ruleset and a
// convenience tools map. The ruleset is authoritative for built-ins whose tool
// id differs from the permission they request. In particular current OpenCode
// maps edit/write/apply_patch to permission "edit"; apply_patch itself asks for
// permission "edit". Do not infer host-write authority from tools.apply_patch.
function wildcardMatch(value, pattern) {
  if (pattern === "*") return true
  if (typeof value !== "string" || typeof pattern !== "string") return false
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*")
  return new RegExp(`^${escaped}$`).test(value)
}
function permissionRules(debug) {
  return Array.isArray(debug?.permission) ? debug.permission : []
}
function matchingPermissionRules(debug, permission) {
  return permissionRules(debug).filter((rule) =>
    rule && typeof rule === "object" &&
    typeof rule.permission === "string" &&
    wildcardMatch(permission, rule.permission)
  )
}
function assertPermissionFullyDenied(debug, permission, label) {
  const rules = matchingPermissionRules(debug, permission)
  let lastWildcardDeny = -1
  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i]
    if (rule.pattern === "*" && rule.action === "deny") lastWildcardDeny = i
  }
  if (lastWildcardDeny < 0) {
    fail(`${label}: resolved permission.${permission} has no unconditional deny`)
    return false
  }
  const laterEscape = rules.slice(lastWildcardDeny + 1).find((rule) => rule.action !== "deny")
  if (laterEscape) {
    fail(`${label}: resolved permission.${permission} is re-opened after its wildcard deny by ${JSON.stringify(laterEscape)}`)
    return false
  }
  return true
}
function permissionActionForWildcard(debug, permission) {
  const rules = matchingPermissionRules(debug, permission)
  for (let i = rules.length - 1; i >= 0; i--) {
    const rule = rules[i]
    if (rule.pattern === "*") return rule.action
  }
  return undefined
}
function permissionActionForValue(debug, permission, value) {
  let action
  for (const rule of permissionRules(debug)) {
    if (!rule || typeof rule!=="object") continue
    if (!wildcardMatch(permission, rule.permission)) continue
    if (!wildcardMatch(value, rule.pattern)) continue
    action=rule.action
  }
  return action
}

let systematic, deployed
try { systematic=parseJsonc(systematicConfigPath); deployed=JSON.parse(fs.readFileSync(openCodeConfigPath,"utf8")) }
catch (error) { console.error(`   !! ${error.message}`); process.exit(1) }
const inventory=walkAgents(agentsRoot).sort((a,b)=>a.name.localeCompare(b.name))
const byName=new Map(inventory.map((a)=>[a.name,a]))

const listText=fs.readFileSync(agentListPath,"utf8")
const runtimeNames=new Set()
for (const line of listText.split(/\r?\n/)) {
  const m=line.match(/^(\S+) \((?:primary|subagent|all)\)$/)
  if (m) runtimeNames.add(m[1])
}
for (const agent of inventory) {
  const expected=expectedFor(systematic,agent)
  if (expected.disable) {
    if (runtimeNames.has(agent.name)) fail(`SYSTEMATIC_DISABLED_AGENT_PRESENT: ${agent.name}`)
  } else if (!runtimeNames.has(agent.name)) {
    fail(`SYSTEMATIC_RUNTIME_MISSING: ${agent.name} is absent from opencode agent list`)
  }
}

const deployedAgents=deployed.agent && typeof deployed.agent==="object" ? deployed.agent : {}
const gp=deployed.permission && typeof deployed.permission==="object" ? deployed.permission : {}
if (gp.grep!=="ask") fail(`GLOBAL_GREP_POLICY_CHANGED: expected ask, got ${show(gp.grep)}`)
for (const [name,agent] of Object.entries(deployedAgents)) {
  if (!agent || typeof agent!=="object" || agent.mode!=="subagent") continue
  if (agent.tools?.grep!==false) fail(`SUBAGENT_NATIVE_GREP_TOOL_EXPOSED: ${name}`)
  if (agent.permission?.grep!=="deny") fail(`SUBAGENT_NATIVE_GREP_NOT_DENIED: ${name}`)
  const repoCapable=agent.tools?.["*"]!==false && name!=="sdd-research" &&
    (agent.tools?.read===true || agent.tools?.sandbox_read===true)
  if (repoCapable && (typeof agent.prompt!=="string" || !agent.prompt.includes("<!-- user:subagent-search-contract -->"))) {
    fail(`SUBAGENT_SEARCH_PROMPT_CONTRACT_MISSING: ${name}`)
  }
}
for (const category of ["workflow","research","review","document-review","design"]) {
  if (systematic.categories?.[category]?.permission?.grep!=="deny") {
    fail(`SYSTEMATIC_CATEGORY_NATIVE_GREP_NOT_DENIED: ${category}`)
  }
}
for (const name of ["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) {
  if (!runtimeNames.has(name)) fail(`RELAY_RUNTIME_AGENT_MISSING: ${name}`)
}
for (const name of Object.keys(deployedAgents)) {
  if (name.endsWith("-astra")) fail(`ASTRA_ALIAS_MUST_NOT_BE_PINNED_IN_OPENCODE_CONFIG: ${name}`)
}
for (const agent of inventory) {
  if (hasOwn(deployedAgents,agent.name)) fail(`SYSTEMATIC_AGENT_SHADOWED: opencode.json defines ${agent.name}; remove it and use systematic.jsonc overlay instead`)
}

const mutators=inventory.filter((a)=>a.declaresMutation)
const controlNames=[...new Set([
  ...mutators.map((a)=>a.name),
  "correctness-reviewer", "testing-reviewer", "repo-research-analyst",
  "adversarial-document-reviewer",
  // Model-sensitive specialist assignments: runtime must match systematic.jsonc.
  "api-contract-reviewer", "architecture-strategist", "reliability-reviewer",
  "data-migrations-reviewer", "deployment-verification-agent",
  "feasibility-reviewer", "design-iterator", "adversarial-reviewer",
  "security-reviewer", "security-lens-reviewer",
])].filter((name)=>byName.has(name))
const reviewedProfileNames=systematic.profiles && typeof systematic.profiles==="object" && !Array.isArray(systematic.profiles)
  ? Object.keys(systematic.profiles)
  : []
let compatibleRuntimeProfiles=new Set(["base",...reviewedProfileNames])
function expectedForProfile(profileName, agent) {
  const candidate={...systematic}
  if (profileName==="base") delete candidate.profile
  else candidate.profile=profileName
  return expectedFor(candidate,agent)
}
for (const name of controlNames) {
  const agent=byName.get(name); const actual=readDebug(name)
  if (!actual) continue
  const model=normalizeModel(actual.model)
  const variant=typeof actual.variant==="string" ? actual.variant : undefined
  const matchingProfiles=[...compatibleRuntimeProfiles].filter((profileName)=>{
    const expected=expectedForProfile(profileName,agent)
    return model===expected.model && variant===expected.variant
  })
  if (matchingProfiles.length===0) {
    const allowed=["base",...reviewedProfileNames].map((profileName)=>{
      const expected=expectedForProfile(profileName,agent)
      return `${profileName}:${show(expected.model)}@${show(expected.variant)}`
    })
    fail(`SYSTEMATIC_RUNTIME_ROUTING_MISMATCH: ${name}: runtime=${show(model)}@${show(variant)} allowed=${allowed.join(",")}`)
  } else {
    compatibleRuntimeProfiles=new Set(matchingProfiles)
  }
  // Built-in edit/write/apply_patch all execute under permission "edit".
  // Validate the resolved permission ruleset, not individual debug-tool booleans.
  assertPermissionFullyDenied(actual, "edit", `SYSTEMATIC_HOST_EDIT_NOT_DENIED: ${name}`)
  if (permissionActionForWildcard(actual,"grep")!=="deny" || tool(actual,"grep")===true) {
    fail(`SYSTEMATIC_NATIVE_GREP_EXPOSED: ${name}`)
  }
  if (agent.declaresMutation) {
    if (tool(actual,"bash")!==false && permissionActionForWildcard(actual,"bash")!=="deny") {
      fail(`SYSTEMATIC_HOST_BASH_EXPOSED: ${name}.bash is not denied`)
    }
    for (const t of ["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
      if (tool(actual,t)!==true) fail(`SYSTEMATIC_SANDBOX_TOOL_MISSING: ${name}.${t} is not enabled at runtime`)
    }
  }
  const memoryExpected = {
    workflow: true,
    research: true,
    design: true,
    review: false,
    "document-review": false,
  }[agent.category]
  if (memoryExpected === undefined) {
    fail(`SYSTEMATIC_MEMORY_RUNTIME_UNCLASSIFIED_CATEGORY: ${agent.category || "<uncategorized>"} for ${name}`)
  } else if (tool(actual,"ctx_memory") !== memoryExpected) {
    fail(`SYSTEMATIC_MEMORY_RUNTIME_MISMATCH: ${name} (${agent.category}) ctx_memory expected ${memoryExpected}, got ${show(tool(actual,"ctx_memory"))}`)
  }
}
if (compatibleRuntimeProfiles.size===0) {
  fail("SYSTEMATIC_RUNTIME_PROFILE_MIXED: runtime agents do not resolve from one reviewed base/profile routing")
} else {
  console.log(`   ok: runtime Systematic routing matches reviewed profile candidate(s): ${[...compatibleRuntimeProfiles].join(",")}`)
}

const SOL_MODEL="openai/gpt-6.1-sol"
const ASTRA_MODEL="openai/gpt-6-astra"
const ASTRA_SUFFIX="-astra"
function isImplementationRoute(name) {
  return name==="general" ||
    name==="jd-fix-agent" ||
    name==="design-iterator" ||
    name==="bug-reproduction-validator" ||
    name==="pr-comment-resolver" ||
    name==="systematic-implementer" ||
    /(^|-)apply($|-)/.test(name) ||
    /(^|-)implement(er|ation)?($|-)/.test(name)
}
function sameResolvedSurface(base, alias, baseName, aliasName, field) {
  if (JSON.stringify(base?.[field])!==JSON.stringify(alias?.[field])) {
    fail(`ASTRA_ALIAS_SURFACE_MISMATCH: ${aliasName}.${field} differs from ${baseName}`)
  }
}
function ruleWitness(pattern, fallback) {
  if (typeof pattern!=="string" || !pattern) return fallback
  return pattern.includes("*") ? pattern.replace(/\*/g,"__astra_probe__") : pattern
}
function assertEquivalentPermissions(base, alias, baseName, aliasName) {
  const baseRules=permissionRules(base)
  const aliasRules=permissionRules(alias)
  const knownPermissions=[
    "bash","read","edit","write","glob","grep","list","webfetch","websearch",
    "task","todowrite","question","plan_enter","plan_exit","doom_loop",
    "external_directory","lsp","skill","ctx_search","ctx_expand","ctx_memory",
    "host_register_project","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff",
    "sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply",
    "sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish",
  ]
  const permissions=new Set([
    ...knownPermissions,
    ...Object.keys(base?.tools??{}),
    ...Object.keys(alias?.tools??{}),
  ])
  for (const rule of [...baseRules,...aliasRules]) {
    if (typeof rule?.permission==="string") permissions.add(ruleWitness(rule.permission,"__astra_permission_probe__"))
  }

  const differences=[]
  for (const permission of permissions) {
    const targets=new Set(["__astra_target_probe__"])
    for (const rule of [...baseRules,...aliasRules]) {
      if (!rule || typeof rule!=="object" || typeof rule.pattern!=="string") continue
      if (!wildcardMatch(permission,rule.permission)) continue
      targets.add(ruleWitness(rule.pattern,"__astra_target_probe__"))
      if (!rule.pattern.includes("*")) targets.add(rule.pattern)
    }
    for (const target of targets) {
      const baseAction=permissionActionForValue(base,permission,target)
      const aliasAction=permissionActionForValue(alias,permission,target)
      if (baseAction!==aliasAction) {
        differences.push({permission,target,base:baseAction??"<none>",alias:aliasAction??"<none>"})
        if (differences.length>=12) break
      }
    }
    if (differences.length>=12) break
  }
  if (differences.length) {
    fail(`ASTRA_ALIAS_EFFECTIVE_PERMISSION_MISMATCH: ${aliasName} differs from ${baseName}; samples=${JSON.stringify(differences)}`)
  }
}

const eligibleSolBases=new Set()
for (const [name,agent] of Object.entries(deployedAgents)) {
  if (agent && typeof agent==="object" && agent.disable!==true && agent.mode!=="primary" &&
      normalizeModel(agent.model)===SOL_MODEL && !isImplementationRoute(name)) eligibleSolBases.add(name)
}
for (const agent of inventory) {
  const expected=expectedFor(systematic,agent)
  if (!expected.disable && expected.model===SOL_MODEL && !isImplementationRoute(agent.name)) eligibleSolBases.add(agent.name)
}

const runtimeAstraAliases=[...runtimeNames].filter((name)=>name.endsWith(ASTRA_SUFFIX)).sort()
const expectedAstraAliases=[...eligibleSolBases].sort().map((name)=>`${name}${ASTRA_SUFFIX}`)
for (const alias of runtimeAstraAliases) {
  const baseName=alias.slice(0,-ASTRA_SUFFIX.length)
  if (isImplementationRoute(baseName)) fail(`ASTRA_IMPLEMENTATION_ALIAS_FORBIDDEN: ${alias}`)
  if (!eligibleSolBases.has(baseName)) fail(`ASTRA_ALIAS_WITHOUT_ELIGIBLE_SOL_BASE: ${alias}`)
}
for (const alias of expectedAstraAliases) {
  if (!runtimeNames.has(alias)) fail(`ASTRA_RUNTIME_ALIAS_MISSING: ${alias}`)
}

const runtimeOrchestrator=readDebug("gentle-orchestrator")
for (const baseName of [...eligibleSolBases].sort()) {
  const aliasName=`${baseName}${ASTRA_SUFFIX}`
  const base=readDebug(baseName)
  const alias=readDebug(aliasName)
  if (!base || !alias) continue
  if (normalizeModel(base.model)!==SOL_MODEL) {
    fail(`ASTRA_BASE_NOT_SOL_AT_RUNTIME: ${baseName}=${show(normalizeModel(base.model))}`)
  }
  if (normalizeModel(alias.model)!==ASTRA_MODEL || alias.variant!=="xhigh") {
    fail(`ASTRA_ALIAS_MODEL_INVALID: ${aliasName}=${show(normalizeModel(alias.model))}@${show(alias.variant)}`)
  }
  if (alias.hidden!==true) fail(`ASTRA_ALIAS_NOT_HIDDEN: ${aliasName}`)
  for (const field of ["prompt","tools","mode"]) sameResolvedSurface(base,alias,baseName,aliasName,field)
  assertEquivalentPermissions(base,alias,baseName,aliasName)
  assertPermissionFullyDenied(alias,"edit",`ASTRA_ALIAS_HOST_EDIT_NOT_DENIED: ${aliasName}`)
  if (permissionActionForValue(runtimeOrchestrator,"task",aliasName)!=="allow") {
    fail(`ASTRA_ALIAS_NOT_ALLOWED_BY_ORCHESTRATOR: ${aliasName}`)
  }
}
if (eligibleSolBases.size===0) fail("ASTRA_NO_ELIGIBLE_SOL_BASES: selectable upgrade surface would be empty")
else console.log(`   ok: ${eligibleSolBases.size} eligible Sol agents expose equivalent, non-implementation Astra aliases`)

const gga=["review-risk","review-readability","review-reliability","review-resilience","review-refuter","review-validator"]
const generic=new Set()
let genericRuntimeReady=true
for (const name of ["gentle-orchestrator","general"]) {
  const dbg=readDebug(name)
  if (!dbg) { genericRuntimeReady=false; continue }
  const m=normalizeModel(dbg.model)
  if (m) generic.add(m)
  else genericRuntimeReady=false
}
let distinct=false
let ggaRuntimeReady=true
for (const name of gga) {
  const configured=deployedAgents[name]
  if (!configured || typeof configured!=="object" || !hasOwn(configured,"model")) { fail(`GGA_REVIEW_MODEL_UNASSIGNED: ${name}`); ggaRuntimeReady=false; continue }
  const assigned=normalizeModel(configured.model); const actual=readDebug(name)
  if (!actual) { ggaRuntimeReady=false; continue }
  const runtime=normalizeModel(actual.model)
  if (assigned && !generic.has(assigned)) distinct=true
  if (runtime!==assigned) {
    if (runtime && genericRuntimeReady && generic.has(runtime)) fail(`GGA_REVIEW_MODEL_INHERITED: ${name} assigned ${assigned} but runtime primary is generic ${runtime}`)
    else fail(`GGA_REVIEW_PRIMARY_MISMATCH: ${name} assigned ${assigned} but runtime primary is ${show(runtime)}`)
  }
  if (hasOwn(configured,"variant")) {
    const expectedVariant=configured.variant==null?undefined:configured.variant
    const runtimeVariant=typeof actual.variant==="string"?actual.variant:undefined
    if (runtimeVariant!==expectedVariant) fail(`GGA_REVIEW_VARIANT_MISMATCH: ${name}: assigned=${show(expectedVariant)} runtime=${show(runtimeVariant)}`)
  }
}
if (genericRuntimeReady && ggaRuntimeReady && !distinct) {
  fail("GGA_REVIEW_NO_DISTINCT_MODEL_CONTROL: review primaries do not provide a control distinct from general/orchestrator")
}

// Compare underlying families, not provider prefixes or exact model IDs.
// A Go Luna fallback for OpenAI Luna does not create an independent reviewer.
for (const [writer,reviewer] of [["general","gentle-orchestrator"],["sdd-apply","sdd-verify"]]) {
  for (const [surface,writerModel,reviewerModel] of [
    ["configured",deployedAgents[writer]?.model,deployedAgents[reviewer]?.model],
    ["runtime",readDebug(writer)?.model,readDebug(reviewer)?.model],
  ]) {
    if (!writerModel || !reviewerModel) continue // Missing agents have their own probe errors.
    const writerFamily=modelFamily(writerModel), reviewerFamily=modelFamily(reviewerModel)
    if (!writerFamily || !reviewerFamily) {
      fail(`PRIMARY_REVIEW_FAMILY_UNKNOWN: ${surface} ${writer}=${show(normalizeModel(writerModel))}, ${reviewer}=${show(normalizeModel(reviewerModel))}`)
    } else if (writerFamily===reviewerFamily) {
      fail(`PRIMARY_REVIEW_SAME_FAMILY: ${surface} ${writer} and ${reviewer} both use ${writerFamily}`)
    } else {
      console.log(`   ok: ${surface} ${writer} (${writerFamily}) is reviewed by ${reviewer} (${reviewerFamily})`)
    }
  }
}

for (const [lane,names,configuredModel] of [
  ["Gentle AI 4R",gga,(name)=>deployedAgents[name]?.model],
  ["Systematic baseline",["correctness-reviewer","testing-reviewer","project-standards-reviewer"],(name)=>{
    const agent=byName.get(name)
    return agent ? expectedFor(systematic,agent).model : undefined
  }],
]) {
  for (const [surface,models] of [
    ["configured",names.map(configuredModel)],
    ["runtime",names.map((name)=>readDebug(name)?.model)],
  ]) {
    const families=models.map(modelFamily)
    if (families.some((family)=>!family)) {
      fail(`REVIEW_FAMILY_UNKNOWN: ${lane} ${surface} models=${JSON.stringify(models.map(normalizeModel))}`)
    } else if (new Set(families).size<3) {
      fail(`REVIEW_FAMILY_SPREAD_INSUFFICIENT: ${lane} ${surface} families=${JSON.stringify([...new Set(families)])}`)
    } else {
      console.log(`   ok: ${lane} ${surface} review spans ${[...new Set(families)].join(", ")}`)
    }
  }
}

function pluginPath(ref) {
  if (typeof ref!=="string") return undefined
  if (ref.startsWith("file://")) { try { return new URL(ref).pathname } catch { return undefined } }
  return path.isAbsolute(ref)?ref:undefined
}
function modelString(value) {
  if (typeof value==="string" && value.trim()) return value.trim()
  if (value && typeof value==="object") {
    const provider=value.providerID ?? value.providerId ?? value.provider
    const model=value.modelID ?? value.modelId ?? value.model ?? value.name
    if (typeof provider==="string" && provider.trim() && typeof model==="string" && model.trim()) return `${provider.trim()}/${model.trim()}`
    for (const k of ["id"]) if (typeof value[k]==="string" && value[k].trim()) return value[k].trim()
    if (typeof value.provider==="string" && typeof value.name==="string") return `${value.provider}/${value.name}`
  }
  return undefined
}
function parseModelRef(value, label) {
  const key=modelString(value)
  const slash=typeof key==="string"?key.indexOf("/"):-1
  if (slash<=0 || slash===key.length-1) { fail(`${label}: malformed model reference ${show(value)}`); return undefined }
  const ref={key,provider:key.slice(0,slash),model:key.slice(slash+1)}
  if (!ref.provider || !ref.model || ref.provider===ref.model) { fail(`${label}: malformed model reference ${show(value)}`); return undefined }
  return ref
}
function providerOf(model) { return parseModelRef(model,"MODEL_REFERENCE")?.provider }
function normalizedRule(value, label, sourceModel) {
  const entries=Array.isArray(value)?value:[value]
  if (value===undefined || entries.length===0) { fail(`${label}: empty fallback rule`); return [] }
  const seen=new Set(); const out=[]
  for (const entry of entries) {
    const ref=parseModelRef(entry,label); if (!ref) continue
    if (sourceModel && ref.key===sourceModel) fail(`${label}: chain contains its primary ${sourceModel}`)
    if (seen.has(ref.key)) fail(`${label}: duplicate chain member ${ref.key}`)
    else { seen.add(ref.key); out.push(ref.key) }
  }
  return out
}
function normalizedTargets(value, label, sourceModel) {
  const entries=Array.isArray(value)?value:[value]
  const keys=normalizedRule(value,label,sourceModel)
  return keys.map((key,index)=>{
    const entry=entries[index]
    const ref=parseModelRef(entry,label)
    const capabilities=entry && typeof entry==="object" && Array.isArray(entry.capabilities)?entry.capabilities:[]
    const variant=entry && typeof entry==="object" && typeof entry.variant==="string"?entry.variant:undefined
    if (entry && typeof entry==="object") {
      const supported=new Set(["providerID","modelID","variant","capabilities"])
      for (const field of Object.keys(entry)) if (!supported.has(field)) fail(`${label}: unsupported target field ${field}`)
      if (hasOwn(entry,"variant") && (!variant || !variant.trim())) fail(`${label}: empty target variant for ${key}`)
      if (hasOwn(entry,"capabilities")) {
        if (!Array.isArray(entry.capabilities)) fail(`${label}: capabilities must be an array for ${key}`)
        else {
          if (new Set(entry.capabilities).size!==entry.capabilities.length) fail(`${label}: duplicate capabilities for ${key}`)
          for (const capability of entry.capabilities) if (!["files","tools","vision"].includes(capability)) fail(`${label}: unsupported capability ${show(capability)} for ${key}`)
        }
      }
    }
    return {key,provider:ref?.provider,capabilities,variant}
  })
}
function configuredFallbacks(config, sourceModel, agent) {
  if (!config || typeof config!=="object" || config.enabled===false) return []
  const provider=providerOf(sourceModel); if (!provider) return []
  if (agent && config.agentFallbackModels && typeof config.agentFallbackModels==="object" && hasOwn(config.agentFallbackModels,agent)) {
    return normalizedRule(config.agentFallbackModels[agent],`FALLBACK_AGENT_${agent}`,sourceModel)
  }
  if (config.fallbackModels && typeof config.fallbackModels==="object" && hasOwn(config.fallbackModels,sourceModel)) {
    return normalizedRule(config.fallbackModels[sourceModel],`FALLBACK_EXACT_${sourceModel}`,sourceModel)
  }
  if (config.providerFallbacks && typeof config.providerFallbacks==="object" && hasOwn(config.providerFallbacks,provider)) {
    return normalizedRule(config.providerFallbacks[provider],`FALLBACK_PROVIDER_${provider}`)
  }
  return normalizedRule(config.fallbackModel,"FALLBACK_GLOBAL")
}
function effectiveFallbacks(config, sourceModel, agent, failureScope="provider") {
  const provider=providerOf(sourceModel)
  if (!provider || !Array.isArray(config.startProviders) || !config.startProviders.includes(provider)) return []
  const chain=configuredFallbacks(config,sourceModel,agent).slice()
  const keepSameProvider=config.sameProviderFallbackMode==="always" || (config.sameProviderFallbackMode==="model-specific" && failureScope==="model")
  return keepSameProvider ? chain : chain.filter((target)=>providerOf(target)!==provider)
}
function addRole(map, model, role) {
  const key=normalizeModel(model)
  if (!key) return
  if (!map.has(key)) map.set(key,[])
  map.get(key).push(role)
}
const refs=(Array.isArray(deployed.plugin)?deployed.plugin:[]).filter((x)=>typeof x==="string" && x.includes("opencode-rate-limit-fallback-mapped"))
if (refs.length!==1) fail(`GGA_FALLBACK_PLUGIN_UNRESOLVED: expected one mapped fallback plugin, found ${refs.length}`)
else {
  const p=pluginPath(refs[0])
  if (!p || !fs.existsSync(p)) fail(`GGA_FALLBACK_PLUGIN_SOURCE_MISSING: ${refs[0]}`)
  else {
    const dir=path.dirname(p)
    const sources=[p,path.join(dir,"src","config.ts"),path.join(dir,"src","plugin.ts"),path.join(dir,"src","log.ts")].filter(fs.existsSync).map((x)=>fs.readFileSync(x,"utf8")).join("\n")
    const fallbackDefaultsPath=path.join(dir,"src","config.ts")
    if (!fs.existsSync(fallbackDefaultsPath)) fail(`FALLBACK_DEFAULTS_SOURCE_MISSING: ${fallbackDefaultsPath}`)
    else {
      const defaults=fs.readFileSync(fallbackDefaultsPath,"utf8")
      const excludedBlock=defaults.match(/DEFAULT_EXCLUDE_AGENTS\s*=\s*\[([\s\S]*?)\]/)?.[1] || ""
      for (const name of ["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator","asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) if (!excludedBlock.includes(`"${name}"`)) fail(`FALLBACK_SOURCE_BOUND_REVIEW_EXCLUSION_MISSING: ${name}`)
    }
    const requiredPluginFeatures=[
      ["agentFallbackModels","agent-specific fallback precedence"],
      ["agentRequiredCapabilities","capability-aware replay filtering"],
      ["sourceGraceProviders","non-blocking source-provider grace"],
      ["replayWatchdogMs","replay creation watchdog"],
      ["fallback_dispatch_failed","dispatch-failure chain advancement"],
      ["recorded_fallback_provenance","provenance-scoped home restoration"],
      [".atl","approved project-local fallback log root"],
      ["project_log_skipped","missing-session-directory diagnostic"],
      ["session_directory_unavailable","session-directory lookup fail-closed behavior"],
      ["project_log_write_failed","project-log write-failure diagnostic"],
    ]
    for (const [marker,label] of requiredPluginFeatures) if (!sources.includes(marker)) fail(`FALLBACK_PLUGIN_FEATURE_MISSING: ${label} (${marker})`)
    if (/join\(\s*["']\.git["']\s*,\s*["']gentle-ai["']\s*,\s*["']rate-limit-fallback\.log["']\s*\)/.test(sources)) fail("FALLBACK_PROJECT_LOG_LEGACY_GIT_PATH_PRESENT")
    if (/return\s+context\.directory\b/.test(sources)) fail("FALLBACK_PROJECT_DIRECTORY_UNSAFE_SERVER_CWD_FALLBACK")
    if (!sources.includes("classifyFailureScope") || !sources.includes("sameProviderFallbackMode")) fail("FALLBACK_PLUGIN_FAILURE_SCOPE_ROUTING_MISSING")
    const names=[...sources.matchAll(/["'`]([^"'`\n]*rate-limit-fallback[^"'`\n]*\.json)["'`]/g)].map((m)=>m[1])
    const unique=[...new Set(names)]; const declared=unique.find((x)=>path.basename(x)===x) ?? unique[0]
    if (!declared) fail("GGA_FALLBACK_CONFIG_DISCOVERY_FAILED")
    else {
      const candidates=path.isAbsolute(declared)?[declared]:[path.join(process.env.HOME||"", ".config","opencode",declared),path.resolve(dir,declared)]
      const cfgPath=candidates.find(fs.existsSync)
      if (!cfgPath) fail(`GGA_FALLBACK_CONFIG_MISSING: ${declared}`)
      else {
        try {
          const cfg=parseJsonc(cfgPath)
          const supportedFields=new Set(["enabled","startProviders","agentFallbackModels","agentRequiredCapabilities","fallbackModels","providerFallbacks","fallbackModel","sameProviderFallbackMode","modelFailurePatterns","providerFailurePatterns","sourceGraceProviders","sourceGraceMs","replayWatchdogMs","cooldownMs","eventDebounceMs","advanceGraceMs","revertToOriginalModel","patterns","excludePatterns","excludeAgents","logging","peakPolicy"])
          for (const key of Object.keys(cfg)) if (!supportedFields.has(key)) fail(`FALLBACK_CONFIG_UNSUPPORTED_FIELD: ${key}`)
          if (cfg.enabled!==true) fail("FALLBACK_CONFIG_DISABLED")
          if (cfg.logging!==true) fail("FALLBACK_LOGGING_NOT_ENABLED")
          if (cfg.advanceGraceMs!==30000) fail(`FALLBACK_ADVANCE_GRACE_MISMATCH: expected 30000, got ${show(cfg.advanceGraceMs)}`)
          if (cfg.sourceGraceMs!==30000) fail(`FALLBACK_SOURCE_GRACE_MISMATCH: expected 30000, got ${show(cfg.sourceGraceMs)}`)
          if (!Array.isArray(cfg.sourceGraceProviders) || !cfg.sourceGraceProviders.includes("opencode-go")) fail(`FALLBACK_GO_SOURCE_GRACE_MISSING: ${show(cfg.sourceGraceProviders)}`)
          if (!(Number.isFinite(cfg.replayWatchdogMs) && cfg.replayWatchdogMs>0)) fail(`FALLBACK_REPLAY_WATCHDOG_INVALID: ${show(cfg.replayWatchdogMs)}`)
          if (cfg.sameProviderFallbackMode!=="model-specific") fail(`FALLBACK_SAME_PROVIDER_MODE_MISMATCH: ${show(cfg.sameProviderFallbackMode)}`)
          if (!Array.isArray(cfg.modelFailurePatterns) || cfg.modelFailurePatterns.length===0) fail("FALLBACK_MODEL_FAILURE_PATTERNS_EMPTY")
          if (!Array.isArray(cfg.providerFailurePatterns) || cfg.providerFailurePatterns.length===0) fail("FALLBACK_PROVIDER_FAILURE_PATTERNS_EMPTY")
          if (cfg.revertToOriginalModel!==true) fail(`FALLBACK_HOME_RESTORE_NOT_EXPLICIT_TRUE: ${show(cfg.revertToOriginalModel)}`)
          const exclusions=Array.isArray(cfg.excludePatterns)?cfg.excludePatterns.map((x)=>String(x).toLowerCase()):[]
          for (const required of ["context length","invalid request","authentication failed","unauthorized","invalid api key"]) if (!exclusions.includes(required)) fail(`FALLBACK_REQUIRED_EXCLUSION_MISSING: ${required}`)
          if (hasOwn(cfg,"peakPolicy")) console.log("   ok: peakPolicy is present but deliberately ignored by the rate-limit plugin")
          if (/glm-5\.2/i.test(JSON.stringify(cfg))) fail("FALLBACK_OBSOLETE_MODEL: GLM-5.2 remains in fallback policy")

          const requiredExcluded=["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator","asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]
          const excluded=new Set(Array.isArray(cfg.excludeAgents)?cfg.excludeAgents:[])
          for (const name of requiredExcluded) if (!excluded.has(name)) fail(`FALLBACK_BOUND_REVIEW_EXCLUSION_MISSING: ${name}`)

          if (!fallbackPolicySourcePath || !fs.existsSync(fallbackPolicySourcePath)) {
            fail(`FALLBACK_CANONICAL_POLICY_MISSING: ${fallbackPolicySourcePath || "<unset>"}`)
          } else {
            parseJsonc(fallbackPolicySourcePath)
            if (fs.readFileSync(cfgPath).compare(fs.readFileSync(fallbackPolicySourcePath))!==0) {
              fail(`FALLBACK_DEPLOYED_POLICY_DRIFT: ${cfgPath} differs from ${fallbackPolicySourcePath}`)
            }
          }

          const activeRoles=new Map()
          const activeAgentModels=new Map()
          for (const [name,agent] of Object.entries(deployedAgents)) {
            if (agent && typeof agent==="object" && agent.disable!==true) {
              addRole(activeRoles,agent.model,`opencode:${name}`)
              const model=normalizeModel(agent.model); if (model) activeAgentModels.set(name,model)
            }
          }
          for (const agent of inventory) {
            const expected=expectedFor(systematic,agent)
            if (!expected.disable) {
              addRole(activeRoles,expected.model,`systematic:${agent.name}`)
              if (expected.model) activeAgentModels.set(agent.name,expected.model)
            }
          }
          if (eligibleSolBases.size>0) {
            addRole(activeRoles,ASTRA_MODEL,`derived-astra-aliases:${[...eligibleSolBases].sort().join(",")}`)
            for (const name of eligibleSolBases) activeAgentModels.set(`${name}${ASTRA_SUFFIX}`,ASTRA_MODEL)
          }
          const optionalProfileRoles=new Map()
          const definedProfiles=systematic.profiles && typeof systematic.profiles==="object" && !Array.isArray(systematic.profiles)
            ? Object.keys(systematic.profiles)
            : []
          for (const profileName of definedProfiles) {
            const profiled={...systematic,profile:profileName}
            for (const agent of inventory) {
              const expected=expectedFor(profiled,agent)
              if (!expected.disable) addRole(optionalProfileRoles,expected.model,`systematic-profile:${profileName}:${agent.name}`)
            }
          }
          const activeModels=[...activeRoles.keys()].sort()
          const optionalProfileModels=[...optionalProfileRoles.keys()].filter((model)=>!activeRoles.has(model)).sort()
          const supportedModels=new Set([...activeModels,...optionalProfileModels])
          for (const obsolete of ["openai/gpt-5.6-sol","openai/gpt-5.6-luna"]) {
            if (supportedModels.has(obsolete)) fail(`OPENAI_V6_PRIMARY_MIGRATION_INCOMPLETE: ${obsolete}`)
          }
          const activeProviders=new Set([...supportedModels].map((m)=>providerOf(m)).filter(Boolean))
          const starters=Array.isArray(cfg.startProviders)?cfg.startProviders:[]
          if (!Array.isArray(cfg.startProviders) || starters.length===0) fail("FALLBACK_START_PROVIDERS_INVALID")
          if (new Set(starters).size!==starters.length) fail("FALLBACK_START_PROVIDERS_DUPLICATE")
          for (const provider of activeProviders) if (!starters.includes(provider)) fail(`FALLBACK_ACTIVE_PROVIDER_NOT_STARTER: ${provider}`)
          for (const provider of starters) if (!activeProviders.has(provider)) fail(`FALLBACK_UNSUPPORTED_START_PROVIDER: ${provider}`)
          for (const provider of cfg.sourceGraceProviders??[]) if (!starters.includes(provider)) fail(`FALLBACK_SOURCE_GRACE_PROVIDER_NOT_STARTER: ${provider}`)

          const exact=cfg.fallbackModels && typeof cfg.fallbackModels==="object" && !Array.isArray(cfg.fallbackModels)?cfg.fallbackModels:{}
          const providerRules=cfg.providerFallbacks && typeof cfg.providerFallbacks==="object" && !Array.isArray(cfg.providerFallbacks)?cfg.providerFallbacks:{}
          const agentRules=cfg.agentFallbackModels && typeof cfg.agentFallbackModels==="object" && !Array.isArray(cfg.agentFallbackModels)?cfg.agentFallbackModels:{}
          const agentRequirements=cfg.agentRequiredCapabilities && typeof cfg.agentRequiredCapabilities==="object" && !Array.isArray(cfg.agentRequiredCapabilities)?cfg.agentRequiredCapabilities:{}
          const activeFallbackText=JSON.stringify({agentRules,exact,providerRules,global:cfg.fallbackModel})
          if (/gpt-5\.6-(sol|luna)/.test(activeFallbackText)) fail("OPENAI_V6_FALLBACK_MIGRATION_INCOMPLETE: retired Sol/Luna active chain")
          for (const migrated of ["openai/gpt-6.1-sol","openai/gpt-6-luna"]) {
            if (supportedModels.has(migrated) && !hasOwn(exact,migrated)) fail(`OPENAI_V6_EXACT_FALLBACK_MISSING: ${migrated}`)
          }
          const astraChain=Array.isArray(exact[ASTRA_MODEL])?normalizedRule(exact[ASTRA_MODEL],"FALLBACK_ASTRA",ASTRA_MODEL):[]
          if (supportedModels.has(ASTRA_MODEL) && astraChain[0]!==SOL_MODEL) fail(`ASTRA_SOL_DOWNGRADE_MISSING: expected ${SOL_MODEL}, got ${show(astraChain[0])}`)
          for (const [agent,rule] of Object.entries(agentRules)) {
            const source=activeAgentModels.get(agent)
            if (!source) { fail(`FALLBACK_AGENT_RULE_INACTIVE: ${agent}`); continue }
            let targets=normalizedTargets(rule,`FALLBACK_AGENT_${agent}`,source)
            const provider=providerOf(source)
            targets=targets.filter((target)=>target.provider!==provider)
            const required=Array.isArray(agentRequirements[agent])?agentRequirements[agent]:[]
            if (new Set(required).size!==required.length) fail(`FALLBACK_AGENT_CAPABILITY_DUPLICATE: ${agent}`)
            for (const capability of required) if (!["files","tools","vision"].includes(capability)) fail(`FALLBACK_AGENT_CAPABILITY_UNSUPPORTED: ${agent}.${capability}`)
            targets=targets.filter((target)=>required.every((capability)=>target.capabilities.includes(capability)))
            if (targets.length===0) fail(`FALLBACK_AGENT_NO_COMPATIBLE_PROVIDER_FAILURE_CHAIN: ${agent}`)
            else console.log(`   ok: capability-sensitive agent ${agent}; first fallback=${targets[0].key}; required=${JSON.stringify(required)}`)
          }
          for (const agent of Object.keys(agentRequirements)) if (!hasOwn(agentRules,agent)) fail(`FALLBACK_AGENT_REQUIREMENT_WITHOUT_RULE: ${agent}`)
          for (const source of Object.keys(exact)) {
            parseModelRef(source,`FALLBACK_EXACT_SOURCE_${source}`)
            normalizedTargets(exact[source],`FALLBACK_EXACT_${source}`,source)
            if (!supportedModels.has(source)) fail(`FALLBACK_EXACT_SOURCE_INACTIVE: ${source}`)
          }
          for (const [provider,rule] of Object.entries(providerRules)) {
            if (!starters.includes(provider)) fail(`FALLBACK_PROVIDER_RULE_NOT_STARTER: ${provider}`)
            const chain=normalizedTargets(rule,`FALLBACK_PROVIDER_${provider}`).map((target)=>target.key)
            const effective=chain.filter((target)=>providerOf(target)!==provider)
            if (effective.length===0) fail(`FALLBACK_PROVIDER_RULE_EMPTY_EFFECTIVE_CHAIN: ${provider}`)
          }
          for (const provider of activeProviders) if (!hasOwn(providerRules,provider)) fail(`FALLBACK_ACTIVE_PROVIDER_NO_EMERGENCY_RULE: ${provider}`)
          normalizedTargets(cfg.fallbackModel,"FALLBACK_GLOBAL")

          const openCodeDeepSeek41="opencode-go/deepseek-v4.1-flash"
          const directDeepSeek41="deepseek/deepseek-flash"
          const openRouterDeepSeek41="openrouter/deepseek/deepseek-v4.1-flash"
          const fallbackText=JSON.stringify(cfg)
          for (const retiredModel of [
            "muse-spark-1.2-contributor",
            "muse-spark-1.3-contributor",
            "deepseek-v4-pro",
            "deepseek-v4-flash-vision-exp",
            "deepseek-v4-flash-0731",
            "deepseek-v4-flash",
          ]) {
            if (fallbackText.includes(retiredModel)) fail(`FALLBACK_RETIRED_MUSE_OR_DEEPSEEK_MODEL: ${retiredModel}`)
          }
          if (!hasOwn(exact,openCodeDeepSeek41)) {
            fail(`DEEPSEEK_V4_1_EXACT_FALLBACK_POLICY_MISSING: ${openCodeDeepSeek41}`)
          } else {
            const modelChain=effectiveFallbacks(cfg,openCodeDeepSeek41,undefined,"model")
            const providerChain=effectiveFallbacks(cfg,openCodeDeepSeek41,undefined,"provider")
            for (const [scope,chain] of [["model",modelChain],["provider",providerChain]]) {
              if (chain[0]!==directDeepSeek41) fail(`DEEPSEEK_V4_1_${scope.toUpperCase()}_FALLBACK_FIRST_MISMATCH: expected ${directDeepSeek41}, got ${show(chain[0])}`)
              if (!chain.includes(openRouterDeepSeek41)) fail(`DEEPSEEK_V4_1_${scope.toUpperCase()}_OPENROUTER_FALLBACK_MISSING: ${openRouterDeepSeek41}`)
              if (scope==="provider" && chain.some((target)=>providerOf(target)==="opencode-go")) {
                fail(`DEEPSEEK_V4_1_PROVIDER_FAILURE_FALLBACK_UNSAFE: same-provider target remains in ${JSON.stringify(chain)}`)
              }
            }
          }

          for (const model of activeModels) {
            if (!hasOwn(exact,model)) fail(`FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: ${model}; roles=${activeRoles.get(model).join(",")}`)
            const providerChain=effectiveFallbacks(cfg,model,undefined,"provider")
            const modelChain=effectiveFallbacks(cfg,model,undefined,"model")
            if (providerChain.length===0) fail(`FALLBACK_ACTIVE_MODEL_EMPTY_PROVIDER_FAILURE_CHAIN: ${model}`)
            if (modelChain.length===0) fail(`FALLBACK_ACTIVE_MODEL_EMPTY_MODEL_FAILURE_CHAIN: ${model}`)
            if (providerChain.length && modelChain.length) console.log(`   ok: active primary ${model}; provider-failure=${JSON.stringify(providerChain)}; model-failure=${JSON.stringify(modelChain)}`)
          }
          for (const model of optionalProfileModels) {
            if (!hasOwn(exact,model)) fail(`FALLBACK_PROFILE_MODEL_NO_EXACT_POLICY: ${model}; roles=${optionalProfileRoles.get(model).join(",")}`)
            const providerChain=effectiveFallbacks(cfg,model,undefined,"provider")
            const modelChain=effectiveFallbacks(cfg,model,undefined,"model")
            if (providerChain.length===0 || modelChain.length===0) fail(`FALLBACK_PROFILE_MODEL_EMPTY_EFFECTIVE_CHAIN: ${model}`)
            else console.log(`   ok: optional-profile primary ${model}; provider-failure=${JSON.stringify(providerChain)}; model-failure=${JSON.stringify(modelChain)}`)
          }

          const exactKeys=new Set(Object.keys(exact))
          const graph=new Map([...exactKeys].map((source)=>[source,normalizedRule(exact[source],`FALLBACK_GRAPH_${source}`,source).filter((target)=>exactKeys.has(target))]))
          const visiting=new Set(), visited=new Set(), stack=[]
          function visit(node) {
            if (visiting.has(node)) { const start=stack.indexOf(node); fail(`FALLBACK_EXPLICIT_POLICY_CYCLE: ${[...stack.slice(start),node].join(" -> ")}`); return }
            if (visited.has(node)) return
            visiting.add(node); stack.push(node)
            for (const next of graph.get(node)??[]) visit(next)
            stack.pop(); visiting.delete(node); visited.add(node)
          }
          for (const node of graph.keys()) visit(node)

          const ggaModels=new Set(gga.map((name)=>normalizeModel(deployedAgents[name]?.model)).filter(Boolean))
          const ggaProviders=new Set([...ggaModels].map(providerOf).filter(Boolean))
          if (ggaModels.size<4 || ggaProviders.size<2) fail(`GGA_REVIEW_DIVERSITY_LOST: models=${ggaModels.size}, providers=${ggaProviders.size}`)
          // Bound review sessions recover through native STATUS-based relaunch;
          // rate-limit replay would bypass transport-injected Task context.

          const judges=["jd-judge-a","jd-judge-b"].map((name)=>({name,model:normalizeModel(deployedAgents[name]?.model)})).map((x)=>({...x,first:x.model?effectiveFallbacks(cfg,x.model)[0]:undefined}))
          if (judges.some((x)=>!x.model || !x.first)) fail(`JUDGMENT_DAY_FALLBACK_MISSING: ${JSON.stringify(judges)}`)
          else {
            if (new Set(judges.map((x)=>x.model)).size!==2 || new Set(judges.map((x)=>providerOf(x.model))).size!==2) fail(`JUDGMENT_DAY_PRIMARY_DIVERSITY_LOST: ${JSON.stringify(judges)}`)
            if (new Set(judges.map((x)=>x.first)).size!==2 || new Set(judges.map((x)=>providerOf(x.first))).size!==2) fail(`JUDGMENT_DAY_FALLBACK_DIVERSITY_LOST: ${JSON.stringify(judges)}`)
          }
          console.log(`   ok: ${activeModels.length} active and ${optionalProfileModels.length} optional-profile primary models have exact effective fallback policies from ${cfgPath}`)
        } catch (error) { fail(`GGA_FALLBACK_CONFIG_INVALID: ${error.message}`) }
      }
    }
  }
}

if (gp.edit!=="deny") fail(`HOST_EDIT_NOT_DENIED: global permission.edit=${show(gp.edit)}`)
if (gp.write!=="deny") fail(`HOST_WRITE_NOT_DENIED: global permission.write=${show(gp.write)}`)
if (gp.ctx_search!=="allow") fail(`MAGIC_CONTEXT_SEARCH_NOT_ALLOW: ${show(gp.ctx_search)}`)
if (gp.ctx_expand!=="allow") fail(`MAGIC_CONTEXT_EXPAND_NOT_ALLOW: ${show(gp.ctx_expand)}`)
if (gp.ctx_memory!=="deny") fail(`MAGIC_CONTEXT_MEMORY_DEFAULT_NOT_DENY: ${show(gp.ctx_memory)}`)
if (gp.host_register_project!=="deny") fail(`HOST_REGISTER_PROJECT_DEFAULT_NOT_DENY: ${show(gp.host_register_project)}`)
if (gp.bash!=="deny" || gp.apply_patch!=="deny") fail("ORDINARY_HOST_EXECUTION_NOT_DENIED")
if (gp.grep!=="ask") fail(`GREP_PERMISSION_NOT_ASK: ${show(gp.grep)}`)
if (gp.glob!=="allow") fail(`GLOB_PERMISSION_NOT_ALLOW: ${show(gp.glob)}`)
if (gp.sandbox_bash!=="ask") fail(`SANDBOX_BASH_DEFAULT_NOT_ASK: ${show(gp.sandbox_bash)}`)
for (const t of ["sandbox_apply","sandbox_apply_patch","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_edit","sandbox_finish","sandbox_write"]) if (gp[t]!=="deny") fail(`SANDBOX_MUTATION_DEFAULT_NOT_DENY: ${t}=${show(gp[t])}`)


const registeredHostReads=["host_sdd_status","host_sdd_continue","host_sdd_task_result","host_review_assess","host_review_mode_status","host_review_status","host_review_lens_context","host_sandbox_result"]
const gatedHostMutations=["host_sdd_attempt_grant","host_sdd_archive_compose","host_git_commit","host_git_push","host_gh_issue_create","host_plan_append","host_register_project","host_review_start","host_review_capture_result","host_review_capture_unachievable","host_review_acknowledge_approved","host_review_capture_correction_plan","host_review_capture_refuter","host_review_capture_validation","host_review_validate","host_review_recover","host_sandbox_result_install"]
const retiredHostOperations=["host_sdd_verify_validate","host_sdd_attempt_status","host_sdd_attempt_acquire","host_sdd_attempt_begin","host_sdd_attempt_rescope","host_sdd_attempt_finish","host_sdd_attempt_reset","host_sdd_attempt_settle"]
for (const name of registeredHostReads) if (gp[name]!=="allow") fail(`HOST_READ_PERMISSION_MISMATCH: ${name}`)
for (const name of [...gatedHostMutations,...retiredHostOperations]) if (gp[name]!=="deny") fail(`HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY: ${name}`)
for (const name of ["host_system","host_service_status","host_service_logs","host_tailscale_status","host_memory","host_disk_usage","host_network_listeners","host_process_list","host_docker_list","host_docker_logs"]) if (gp[name]==="allow") fail(`UNREGISTERED_HOST_INSPECTION_ADVERTISED: ${name}`)

function cfgTool(agent,t) { return agent?.tools && typeof agent.tools==="object" ? agent.tools[t] : undefined }
function cfgPerm(agent,t) { return agent?.permission && typeof agent.permission==="object" ? agent.permission[t] : undefined }
function assertCfgWriter(name) {
  const a=deployedAgents[name]; if (!a) { fail(`SANDBOX_WRITER_MISSING: ${name}`); return }
  if (cfgPerm(a,"edit")!=="deny" || cfgPerm(a,"write")!=="deny") fail(`HOST_WRITE_EXPOSED: ${name}`)
  if (cfgPerm(a,"bash")!=="deny") fail(`HOST_BASH_WRITER_NOT_DISABLED: ${name}`)
  if (cfgTool(a,"edit")===true || cfgTool(a,"write")===true || cfgTool(a,"bash")===true) fail(`LEGACY_HOST_TOOL_EXPOSED: ${name}`)
  for (const t of ["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
    if (cfgPerm(a,t)!=="allow" || cfgTool(a,t)===false) fail(`SANDBOX_WRITER_TOOL_MISSING: ${name}.${t}`)
  }
  for (const t of ["sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(a,t)!=="ask" || cfgTool(a,t)===false) fail(`SANDBOX_BOUNDARY_NOT_GATED: ${name}.${t}`)
  }
  if (cfgTool(a,"*")===false) fail(`CUSTOM_TOOL_SURFACE_DISABLED: ${name}`)
}
for (const name of ["frontend-apply","frontend-apply-local","general","jd-fix-agent"]) assertCfgWriter(name)
for (const name of Object.keys(deployedAgents).filter((n)=>n.startsWith("sdd-") && n!=="sdd-research")) assertCfgWriter(name)

const sddResearch=deployedAgents["sdd-research"]
if (!sddResearch) fail("SDD_RESEARCH_AGENT_MISSING")
else {
  if (sddResearch.mode!=="subagent" || sddResearch.hidden!==true) fail("SDD_RESEARCH_AGENT_SHAPE_INVALID")
  if (!normalizeModel(sddResearch.model)) fail("SDD_RESEARCH_MODEL_NOT_EXPLICIT")
  for (const t of ["edit","write","bash","task","webfetch","websearch","sandbox_bash"]) {
    if (cfgPerm(sddResearch,t)!=="deny") fail(`SDD_RESEARCH_PERMISSION_NOT_DENY: ${t}=${show(cfgPerm(sddResearch,t))}`)
  }
  for (const t of ["read","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish","ctx_search","ctx_expand","ctx_memory"]) {
    if (cfgPerm(sddResearch,t)!=="deny" || cfgTool(sddResearch,t)!==false) fail(`SDD_RESEARCH_OUTPUT_ONLY_BOUNDARY: ${t}`)
  }
  const rp=typeof sddResearch.prompt==="string"?sddResearch.prompt:""
  for (const f of ["Gentle AI 3.5.0","output-only","actually available and authorized external tools","Partial research does not certify proposal readiness"]) if (!rp.includes(f)) fail(`GENTLE_AI_V3_RESEARCH_PROMPT_MISSING: ${JSON.stringify(f)}`)
  if (rp.includes("gentle-ai.sdd-research-capability/v1")) fail("GENTLE_AI_V3_RESEARCH_RETIRED_GATE_PRESENT")
}

const ordinaryMemoryAgents=new Set([
  "explore","frontend-apply","frontend-apply-local","frontend-dev","frontend-dev-premium","general",
  "gentle-orchestrator","jd-fix-agent","vision",
])
const isolatedMemoryAgents=new Set([
  "jd-judge-a","jd-judge-b",
  "review-risk","review-readability","review-reliability",
  "review-resilience","review-refuter","review-validator","sdd-research",
  "advisor-design","advisor-integration","advisor-testing",
  "advisor-security","advisor-maintainability",
  "asi-review-risk","asi-review-resilience","asi-review-readability",
  "asi-review-reliability","asi-review-refuter","asi-review-validator",
])

for (const [name,a] of Object.entries(deployedAgents)) {
  let expected
  if (isolatedMemoryAgents.has(name)) expected="deny"
  else if (ordinaryMemoryAgents.has(name) || name.startsWith("sdd-")) expected="allow"
  else {
    fail(`MAGIC_CONTEXT_MEMORY_POLICY_UNCLASSIFIED_AGENT: ${name}`)
    continue
  }
  if (cfgPerm(a,"ctx_memory")!==expected) {
    fail(`MAGIC_CONTEXT_MEMORY_POLICY_MISMATCH: ${name}.permission.ctx_memory expected ${expected}, got ${show(cfgPerm(a,"ctx_memory"))}`)
  }
  if (name!=="gentle-orchestrator" && cfgPerm(a,"host_register_project")!==undefined) {
    fail(`HOST_REGISTER_PROJECT_AGENT_OVERRIDE_FORBIDDEN: ${name}=${show(cfgPerm(a,"host_register_project"))}`)
  }
}

for (const name of ["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) {
  const relay=deployedAgents[name]
  if (!relay || relay.mode!=="subagent" || relay.hidden!==true || cfgTool(relay,"*")!==false || cfgPerm(relay,"ctx_memory")!=="deny" || cfgPerm(relay,"task")?.["*"]!=="deny") fail(`RELAY_AGENT_ISOLATION_MISMATCH: ${name}`)
  for (const t of [...registeredHostReads,...gatedHostMutations,"read","bash","edit","write","sandbox_read","sandbox_bash"]) if (cfgTool(relay,t)===true || cfgPerm(relay,t)==="allow" || cfgPerm(relay,t)==="ask") fail(`RELAY_TOOL_EXPOSED: ${name}.${t}`)
}
for (const name of ["review-risk","review-resilience","review-readability","review-reliability"]) {
  const lens=deployedAgents[name]
  if (!lens || lens.mode!=="subagent" || lens.hidden!==true || cfgTool(lens,"*")!==false || cfgPerm(lens,"ctx_memory")!=="deny") fail(`GENTLE_AI_V3_4_PROVIDER_TASK_AGENT_ISOLATION_MISMATCH: ${name}`)
  for (const t of [...registeredHostReads,...gatedHostMutations,"read","bash","edit","write","task","sandbox_read","sandbox_bash"]) if (cfgTool(lens,t)===true || cfgPerm(lens,t)==="allow" || cfgPerm(lens,t)==="ask") fail(`GENTLE_AI_V3_4_PROVIDER_TASK_TOOL_EXPOSED: ${name}.${t}`)
}

const researcher=deployedAgents["explore"]
if (!researcher) fail("RESEARCHER_FALLBACK_MISSING: explore")
else {
  if (cfgPerm(researcher,"bash")!=="deny") fail("RESEARCHER_HOST_BASH_EXPOSED")
  if (cfgPerm(researcher,"edit")!=="deny" || cfgPerm(researcher,"write")!=="deny") fail("RESEARCHER_HOST_WRITE_EXPOSED")
  if (cfgTool(researcher,"bash")===true || cfgTool(researcher,"edit")===true || cfgTool(researcher,"write")===true) fail("RESEARCHER_LEGACY_HOST_TOOL_EXPOSED")
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(researcher,t)!=="deny" || cfgTool(researcher,t)===true) fail(`RESEARCHER_MUTATION_EXPOSED: ${t}`)
  }
}

const orch=deployedAgents["gentle-orchestrator"]
if (!orch) fail("ORCHESTRATOR_MISSING")
else {
  const configuredOrchestratorModel=normalizeModel(orch.model)
  const configuredOrchestratorVariant=typeof orch.variant==="string" ? orch.variant : undefined
  if (!configuredOrchestratorModel) fail(`ORCHESTRATOR_MODEL_NOT_EXPLICIT: ${show(orch.model)}`)
  if (!configuredOrchestratorVariant) fail(`ORCHESTRATOR_VARIANT_NOT_EXPLICIT: ${show(orch.variant)}`)
  if (cfgPerm(orch,"edit")!=="deny" || cfgPerm(orch,"write")!=="deny") fail("ORCHESTRATOR_HOST_WRITE_NOT_DENIED")
  if (cfgPerm(orch,"bash")!=="deny") fail("ORCHESTRATOR_HOST_BASH_NOT_DENIED")
  for (const name of gatedHostMutations) if (cfgPerm(orch,name)!=="ask") fail(`ORCHESTRATOR_HOST_TOOL_NOT_ASK: ${name}`)
  for (const name of retiredHostOperations) if (cfgPerm(orch,name)!=="deny") fail(`ORCHESTRATOR_RETIRED_HOST_TOOL_EXPOSED: ${name}`)
  if (cfgPerm(orch,"host_register_project")!=="ask") fail(`ORCHESTRATOR_HOST_REGISTER_PROJECT_NOT_ASK: ${show(cfgPerm(orch,"host_register_project"))}`)
  if (cfgTool(orch,"bash")===true || cfgTool(orch,"edit")===true || cfgTool(orch,"write")===true) fail("ORCHESTRATOR_LEGACY_HOST_TOOL_EXPOSED")
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(orch,t)!=="deny" || cfgTool(orch,t)===true) fail(`ORCHESTRATOR_MUTATION_EXPOSED: ${t}`)
  }
  const task=cfgPerm(orch,"task")
  if (!task || typeof task!=="object" || task["*"]!=="ask") fail("TASK_FALLBACK_NOT_ASK")
  for (const agent of inventory) if (task?.[agent.name]!=="allow") fail(`TASK_AGENT_NOT_ALLOWED: ${agent.name}`)
  for (const name of ["frontend-dev","frontend-dev-premium"]) {
    if (task?.[name]!=="allow") fail(`FRONTEND_LANE_NOT_ALLOWED: ${name}`)
  }
  const relayReviewAgents=["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]
  const plainProviderReviewAgents=["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator"]
  for (const name of relayReviewAgents) if (task?.[name]!=="allow") fail(`RELAY_TASK_NOT_ALLOWED: ${name}`)
  for (const name of plainProviderReviewAgents) if (task?.[name]!=="deny") fail(`PLAIN_PROVIDER_REVIEW_TASK_NOT_DENIED: ${name}`)
  for (const [agentName,agentConfig] of Object.entries(deployedAgents)) {
    if (agentName==="gentle-orchestrator") continue
    const delegated=cfgPerm(agentConfig,"task")
    if (!delegated || typeof delegated!=="object") continue
    if (delegated["*"]==="allow") fail(`RELAY_TASK_WILDCARD_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}`)
    for (const relayName of relayReviewAgents) if (delegated[relayName]==="allow") fail(`RELAY_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.${relayName}`)
  }
  if (task?.["sdd-research"]!=="allow") fail("SDD_RESEARCH_TASK_NOT_ALLOWED")

  const orchPrompt=typeof orch.prompt==="string" ? orch.prompt : ""
  const forbiddenPromptFragments=[
    "Implementation runs as **direct inline**",
    "Write one mechanical, already-understood file | ✅",
    "Bash for state (`git`, `gh`) | ✅",
    "Keep one mechanical, already-understood file change inline",
    "Direct inline:"
  ]
  for (const fragment of forbiddenPromptFragments) {
    if (orchPrompt.includes(fragment)) fail(`ORCHESTRATOR_PROMPT_INLINE_DRIFT: forbidden managed prompt fragment reappeared: ${JSON.stringify(fragment)}`)
  }
  if (!orchPrompt.includes("strictly read-only coordinator") ||
      !orchPrompt.includes("never use native host Bash") ||
      !orchPrompt.includes("Every source edit or project execution is delegated to a sandbox worker")) {
    fail("ORCHESTRATOR_PROMPT_BOUNDARY_MISSING: dedicated prompt no longer encodes strict read-only/delegated execution")
  }
  const technicalLeadContractRequired=[
    "### Read-only technical-lead responsibility (MANDATORY)",
    "Read-only is an authority boundary, not a reasoning-depth boundary.",
    "For **non-SDD implementation work**",
    "**implementation contract**",
    "do not merely forward the user's wording",
    "Do not independently reimplement or duplicate a specialist's completed implementation",
    "Spend orchestrator intelligence on project understanding, architecture, decomposition, dependency analysis, precise task framing, conflict resolution, escalation decisions, and synthesis.",
    "respect the SDD artifact graph and phase ownership"
  ]
  const missingTechnicalLeadContract=technicalLeadContractRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingTechnicalLeadContract.length) {
    fail(`ORCHESTRATOR_TECHNICAL_LEAD_CONTRACT_MISSING: missing=${JSON.stringify(missingTechnicalLeadContract)}`)
  }
  const frontendEscalationRequired=[
    "### Frontend lane model escalation",
    "`frontend-dev` as the normal design/verify lane",
    "`frontend-dev-premium`",
    "major redesign",
    "ambiguous UX/product decisions",
    "failed to converge after two substantive visual iteration rounds",
    "same read-only frontend contract"
  ]
  const missingFrontendEscalation=frontendEscalationRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingFrontendEscalation.length) {
    fail(`ORCHESTRATOR_FRONTEND_ESCALATION_CONTRACT_MISSING: missing=${JSON.stringify(missingFrontendEscalation)}`)
  }
  const v3Required=[
    "### Gentle AI 3.5.0 secure ODD route (first on every request)",
    "### Gentle AI 3.5.0 substantial ODD work-unit and review boundary (MANDATORY)",
    "### Gentle AI 3.5.0 mandatory ODD delegation (SECURE)",
    "### Skill-based route entrypoint (MANDATORY)",
    'skill({name:"workflow-route"})',
    "load it again after compaction",
    "For the orchestrator, prefer available authorized `aft_outline`/`aft_zoom`",
    "SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.",
    "EXTERNAL_CONTEXT_REQUIRED",
    "four or more files",
    "two or more non-trivial files",
    "about 20 tool calls or five exploratory reads",
    "Before implementing every substantial ODD task",
    "actual named Task dispatch and result",
    "tell the user in one line which feature document was created and how many tasks it holds",
    "gentle-ai review mode enable|disable|status",
    "defaults to on when unset",
    "deciding source",
    "reason unassessable",
    "targeted_validation_inconclusive",
    "validator_result_not_admissible",
    "role_capture_failed",
    "--base-ref <last reviewed boundary> --committed-only --json",
    "--agent opencode",
    "candidate.consumed",
    "review_due",
    "review_due_reason",
    "next_transition.command",
    "gentle-ai.review-integration.status/v8",
    "provider_task.agent",
    "provider_task.prompt",
    "reviewer's raw JSON object",
    "grouped wave without waiting between launches",
    "correction_context_budget_exceeded",
    "OpenCode V2 native review remains unavailable and fails closed",
    "## 4R review lane routing (mandatory)",
    "`review-<lens>` → `asi-review-<lens>`",
    "Forward the provider-issued task line verbatim",
    "TRANSPORT-LANE FAILURE",
    "re-dispatch through the mapped `asi-review-*` lane",
    "two transports cannot own one Task",
    "Never grant review lanes to implementation workers or isolated reviewers",
    "feature delivery strategy",
    "Do not leave the evidence update uncommitted",
    "PR creation, push and merge require separate user intent",
    "Authorize → Explore → Resolve uncertainty → Classify → Track → Implement → Close",
    "ODD_TASKS key=odd/{project}/{feature-name}/tasks",
    "before the first source edit",
    "Confirm actual Task dispatch and returned result",
    "### Canonical WORKFLOW.md route decision (MANDATORY on every request)",
    "ROUTE: <class> | intent: <read-only/authorized change>",
    "basis: WORKFLOW.md",
    "Read the active selected skill",
    "### Dependency Graph — Gentle AI 3.5.0",
    "optional research → propose",
    "optional verify → archive",
    "Partial research pauses only unsafe dependent choices",
    "Inside SDD, do not start review",
    "### Review Workload Advisory",
    "## Gentle AI 3.5.0 and Systematic 3.18.4 secure integration",
    "screen`, `prepare`, `merge`, and `finalize`",
    "asi-review-*",
  ]
  for (const fragment of v3Required) if (!orchPrompt.includes(fragment)) fail(`GENTLE_AI_V3_ORCHESTRATOR_CONTRACT_MISSING: ${JSON.stringify(fragment)}`)
  for (const retired of ["### Gentle AI v2.7 workflow compatibility", "### Research and Pre-Proposal Gate — Gentle AI v2.7", "### Native Runtime Attempt Authority", "confirmed preproposal + explore", "400-line budget risk: High"]) if (orchPrompt.includes(retired)) fail(`GENTLE_AI_V3_RETIRED_ORCHESTRATOR_GATE: ${JSON.stringify(retired)}`)
  for (const retired of ["generated negotiated v2.1 lifecycle", "Native RAR owns verification applicability", "creates or discovers the terminal receipt", "staged_delivery_candidate_required", "must never substitute for a v8 `provider_task.agent`", "copy `provider_task.agent` unchanged as `subagent_type`"]) {
    if (orchPrompt.includes(retired)) fail(`GENTLE_AI_RETIRED_REVIEW_CONTRACT_PRESENT: ${JSON.stringify(retired)}`)
  }
  const magicContextContractRequired=[
    "### Mandatory Magic Context memory/context",
    "Do NOT probe Engram first",
    "ctx_search",
    "ctx_expand",
    "ctx_memory",
    "Ordinary working agents may save memories",
    "Isolated evaluation actors remain memory-write denied",
    "SDD_ARTIFACT key=<stable-key>",
    "`magic-context`",
    "`engram` is NOT a canonical store value",
    "### Secure project registration control plane",
    "`host_register_project`",
    "only `gentle-orchestrator` receives `host_register_project: ask`",
    "Remote creation is separate and explicit",
    "pending activation"
  ]
  const missingMagicContextContract=magicContextContractRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingMagicContextContract.length) {
    fail(`MAGIC_CONTEXT_ORCHESTRATOR_CONTRACT_MISSING: missing=${JSON.stringify(missingMagicContextContract)}`)
  }
  const legacyMemoryPatterns=[
    /Search Engram:/,
    /Artifacts:\s*OpenSpec,\s*Engram,\s*Both/,
    /Engram Topic Key Format/,
    /mem_search\s*\(/,
    /mem_get_observation\s*\(/,
    /mem_save\s*\(/,
    /mem_update\s*\(/
  ]
  for (const rx of legacyMemoryPatterns) {
    const scrubbed=orchPrompt.replace(/### Mandatory Magic Context memory\/context[\s\S]*?### Commands/, "### Commands")
    if (rx.test(scrubbed)) fail(`LEGACY_ENGRAM_ORCHESTRATOR_DRIFT: ${rx}`)
  }
  for (const [name,a] of Object.entries(deployedAgents)) {
    if (!name.startsWith("sdd-") || name==="sdd-research") continue
    const prompt=typeof a?.prompt==="string" ? a.prompt : ""
    if (!prompt.includes("USER-OWNED MAGIC CONTEXT SDD ADAPTER")) {
      fail(`MAGIC_CONTEXT_SDD_OVERRIDE_MISSING: ${name}`)
    }
  }
}

function assertDirectAgentModelMatchesConfig(name) {
  const configured=deployedAgents[name]
  if (!configured || typeof configured!=="object") {
    fail(`DIRECT_MODEL_AGENT_MISSING: ${name}`)
    return
  }
  const actual=readDebug(name)
  if (!actual) return
  const expectedModel=normalizeModel(configured.model)
  const runtimeModel=normalizeModel(actual.model)
  if (!expectedModel) fail(`DIRECT_MODEL_NOT_EXPLICIT: ${name}=${show(configured.model)}`)
  else if (runtimeModel!==expectedModel) {
    fail(`DIRECT_RUNTIME_MODEL_MISMATCH: ${name}: opencode.json=${show(expectedModel)} runtime=${show(runtimeModel)}`)
  } else {
    console.log(`   ok: ${name} runtime model matches opencode.json (${expectedModel})`)
  }
  if (hasOwn(configured,"variant")) {
    const expectedVariant=configured.variant==null?undefined:configured.variant
    const runtimeVariant=typeof actual.variant==="string"?actual.variant:undefined
    if (runtimeVariant!==expectedVariant) {
      fail(`DIRECT_RUNTIME_VARIANT_MISMATCH: ${name}: opencode.json=${show(expectedVariant)} runtime=${show(runtimeVariant)}`)
    } else {
      console.log(`   ok: ${name} runtime variant matches opencode.json (${show(expectedVariant)})`)
    }
  }
}
for (const name of ["frontend-dev","frontend-dev-premium","jd-judge-b","sdd-research","general","sdd-apply","sdd-verify"]) {
  assertDirectAgentModelMatchesConfig(name)
}

const sddResearchRuntime=readDebug("sdd-research")
if (sddResearchRuntime) {
  for (const name of ["read","edit","bash","grep","ctx_search","ctx_expand","ctx_memory","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out"]) {
    const resolved=permissionActionForWildcard(sddResearchRuntime,name)
    if (resolved!=="deny" || tool(sddResearchRuntime,name)===true) fail(`SDD_RESEARCH_RUNTIME_LOCAL_TOOL_EXPOSED: ${name}=${show(resolved)}`)
  }
}

const orchRuntime=readDebug("gentle-orchestrator")
if (orchRuntime) {
  const configuredOrchestratorModel=normalizeModel(deployedAgents["gentle-orchestrator"]?.model)
  const configuredOrchestratorVariant=typeof deployedAgents["gentle-orchestrator"]?.variant==="string"
    ? deployedAgents["gentle-orchestrator"].variant
    : undefined
  const runtimeOrchestratorModel=normalizeModel(orchRuntime.model)
  const runtimeOrchestratorVariant=typeof orchRuntime.variant==="string" ? orchRuntime.variant : undefined

  if (runtimeOrchestratorModel!==configuredOrchestratorModel) {
    fail(`ORCHESTRATOR_RUNTIME_MODEL_MISMATCH: opencode.json=${show(configuredOrchestratorModel)} runtime=${show(runtimeOrchestratorModel)}`)
  } else {
    console.log(`   ok: orchestrator runtime model matches opencode.json (${configuredOrchestratorModel})`)
  }
  if (runtimeOrchestratorVariant!==configuredOrchestratorVariant) {
    fail(`ORCHESTRATOR_RUNTIME_VARIANT_MISMATCH: opencode.json=${show(configuredOrchestratorVariant)} runtime=${show(runtimeOrchestratorVariant)}`)
  } else {
    console.log(`   ok: orchestrator runtime variant matches opencode.json (${configuredOrchestratorVariant})`)
  }

  assertPermissionFullyDenied(orchRuntime, "edit", "ORCHESTRATOR_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(orchRuntime,"grep")!=="ask") {
    fail(`ORCHESTRATOR_NATIVE_GREP_NOT_ASK: ${show(permissionActionForWildcard(orchRuntime,"grep"))}`)
  }
  if (tool(orchRuntime,"bash")!==false && permissionActionForWildcard(orchRuntime,"bash")!=="deny") {
    fail("ORCHESTRATOR_HOST_BASH_NOT_DENIED_RUNTIME")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (tool(orchRuntime,t)!==false) fail(`ORCHESTRATOR_RUNTIME_TOOL_EXPOSED: ${t}`)
  }
  if (tool(orchRuntime,"task")!==true) fail("ORCHESTRATOR_TASK_RUNTIME_DISABLED")

  // host_register_project is a context-dependent custom host-control tool. A
  // neutral `opencode debug agent` invocation may not register the tool at all,
  // in which case debug.tools.host_register_project is undefined. The resolved
  // permission ruleset is authoritative for who may invoke it when present.
  const hostRegisterOrchPermission=permissionActionForWildcard(orchRuntime,"host_register_project")
  if (hostRegisterOrchPermission!=="ask") {
    fail(`ORCHESTRATOR_HOST_REGISTER_PROJECT_RUNTIME_NOT_ASK: ${show(hostRegisterOrchPermission)}`)
  }
  const hostRegisterOrchTool=tool(orchRuntime,"host_register_project")
  if (hostRegisterOrchTool===false) {
    fail("ORCHESTRATOR_HOST_REGISTER_PROJECT_REGISTERED_BUT_DISABLED")
  } else if (hostRegisterOrchTool===undefined) {
    console.log("   info: host_register_project not registered in neutral orchestrator debug context; resolved permission=ask")
  } else {
    console.log("   ok: host_register_project registered for orchestrator with resolved permission=ask")
  }

  // Keep deterministic runtime checks to local/in-process intelligence tools.
  // Context7 is remote and CodeGraph is project-scoped, so those are validated
  // at configuration/permission level below rather than making startup health
  // depend on network/service availability from the neutral probe cwd.
  for (const t of [
    "aft_inspect","aft_outline","aft_zoom","ast_grep_search",
    "ctx_expand","ctx_search","ctx_memory",
    "systematic_skill","systematic_workflow_status",
    "sandbox_read","sandbox_list","sandbox_grep","sandbox_diff"
  ]) {
    if (tool(orchRuntime,t)!==true) fail(`ORCHESTRATOR_READ_TOOL_MISSING: ${t}`)
  }
}
const generalRuntime=readDebug("general")
if (generalRuntime) {
  assertPermissionFullyDenied(generalRuntime, "edit", "GENERAL_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(generalRuntime,"grep")!=="deny" || tool(generalRuntime,"grep")===true) {
    fail("GENERAL_NATIVE_GREP_EXPOSED")
  }
  if (tool(generalRuntime,"bash")!==false && permissionActionForWildcard(generalRuntime,"bash")!=="deny") {
    fail("GENERAL_HOST_BASH_EXPOSED")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
    if (tool(generalRuntime,t)!==true) fail(`GENERAL_SANDBOX_TOOL_MISSING: ${t}`)
  }
  for (const t of ["ctx_search","ctx_expand","ctx_memory"]) {
    if (tool(generalRuntime,t)!==true) fail(`GENERAL_MAGIC_CONTEXT_TOOL_MISSING: ${t}`)
  }
  const hostRegisterGeneralPermission=permissionActionForWildcard(generalRuntime,"host_register_project")
  if (hostRegisterGeneralPermission!=="deny") {
    fail(`GENERAL_HOST_REGISTER_PROJECT_RUNTIME_NOT_DENY: ${show(hostRegisterGeneralPermission)}`)
  }
  const hostRegisterGeneralTool=tool(generalRuntime,"host_register_project")
  if (hostRegisterGeneralTool===true) {
    fail("GENERAL_HOST_REGISTER_PROJECT_REGISTERED_AND_EXPOSED")
  } else if (hostRegisterGeneralTool===undefined) {
    console.log("   info: host_register_project not registered in neutral general debug context; resolved permission=deny")
  }
}

const researcherRuntime=readDebug("explore")
if (researcherRuntime) {
  assertPermissionFullyDenied(researcherRuntime, "edit", "RESEARCHER_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(researcherRuntime,"grep")!=="deny" || tool(researcherRuntime,"grep")===true) {
    fail("RESEARCHER_NATIVE_GREP_EXPOSED")
  }
  if (tool(researcherRuntime,"bash")!==false && permissionActionForWildcard(researcherRuntime,"bash")!=="deny") {
    fail("RESEARCHER_HOST_BASH_EXPOSED_RUNTIME")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (tool(researcherRuntime,t)!==false) fail(`RESEARCHER_RUNTIME_MUTATION_EXPOSED: ${t}`)
  }
  for (const t of ["aft_inspect","aft_outline","aft_zoom","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","ctx_search","ctx_expand","ctx_memory"]) {
    if (tool(researcherRuntime,t)!==true) fail(`RESEARCHER_READ_OR_MEMORY_TOOL_MISSING: ${t}`)
  }
  const hostRegisterResearchPermission=permissionActionForWildcard(researcherRuntime,"host_register_project")
  if (hostRegisterResearchPermission!=="deny") {
    fail(`RESEARCHER_HOST_REGISTER_PROJECT_RUNTIME_NOT_DENY: ${show(hostRegisterResearchPermission)}`)
  }
  const hostRegisterResearchTool=tool(researcherRuntime,"host_register_project")
  if (hostRegisterResearchTool===true) {
    fail("RESEARCHER_HOST_REGISTER_PROJECT_REGISTERED_AND_EXPOSED")
  } else if (hostRegisterResearchTool===undefined) {
    console.log("   info: host_register_project not registered in neutral researcher debug context; resolved permission=deny")
  }
}

// MCP registration/egress is environment-sensitive. Deterministically verify
// the desired MCP configuration and permission surface here; secure startup
// validation separately proves real Context7 network reachability.
const plugins=Array.isArray(deployed.plugin)?deployed.plugin:[]
const magicPlugins=plugins.filter((ref)=>typeof ref==="string" && ref.includes("opencode-magic-context"))
if (magicPlugins.length!==1) fail(`MAGIC_CONTEXT_PLUGIN_INVALID: expected exactly one opencode-magic-context plugin, found ${magicPlugins.length}`)

const mcp=deployed.mcp && typeof deployed.mcp==="object" ? deployed.mcp : {}
if (mcp.engram?.enabled===true) fail("ENGRAM_UNEXPECTEDLY_ENABLED: normal workflow must not probe Engram")
if (!mcp.context7 || mcp.context7.enabled!==true || mcp.context7.type!=="remote" ||
    typeof mcp.context7.url!=="string" || !mcp.context7.url.startsWith("https://mcp.context7.com/")) {
  fail("CONTEXT7_CONFIG_INVALID: expected enabled remote https://mcp.context7.com/ endpoint")
}
if (!mcp.codegraph || mcp.codegraph.enabled!==true || mcp.codegraph.type!=="local") {
  fail("CODEGRAPH_CONFIG_INVALID: expected enabled local CodeGraph MCP")
}
const github=mcp.github_ro
const reviewedGitHubToolsets="repos,pull_requests,issues"
if (!github || github.enabled!==true || github.type!=="remote" ||
    github.url!=="https://api.githubcopilot.com/mcp/readonly" || github.oauth!==false ||
    github.headers?.Authorization!=="Bearer {env:GITHUB_REVIEW_TOKEN}" ||
    github.headers?.["X-MCP-Readonly"]!=="true" ||
    github.headers?.["X-MCP-Toolsets"]!==reviewedGitHubToolsets ||
    Object.keys(github.headers??{}).some((key)=>!["Authorization","X-MCP-Readonly","X-MCP-Toolsets"].includes(key))) {
  fail("GITHUB_RO_CONFIG_INVALID: expected public-repo PAT placeholder and GitHub server-enforced read-only toolsets")
}
if (Object.keys(mcp).some((name)=>name!=="github_ro" && /^github([_-]|$)/i.test(name))) {
  fail("GITHUB_RO_DUPLICATE_MCP: unreviewed GitHub connection could bypass read-only mode")
}
if (deployed.tools?.["github_ro_*"]!==false) fail("GITHUB_RO_GLOBAL_TOOLS_NOT_DISABLED")
const githubReaders=new Set(["gentle-orchestrator","explore","sdd-research"])
for (const [name,agent] of Object.entries(deployedAgents)) {
  const enabled=agent?.tools?.["github_ro_*"]===true
  if (enabled!==githubReaders.has(name)) fail(`GITHUB_RO_AGENT_TOOLS_SCOPE_MISMATCH: ${name}`)
  if (enabled && agent.permission?.["github_ro_*"]!=="allow") fail(`GITHUB_RO_AGENT_PERMISSION_MISSING: ${name}`)
  if (!enabled && agent.permission?.["github_ro_*"]==="allow") fail(`GITHUB_RO_AGENT_PERMISSION_BYPASS: ${name}`)
}
for (const [name,overlay] of Object.entries(systematic.agents??{})) {
  if (overlay?.tools!==undefined || overlay?.permission?.["github_ro_*"]==="allow") {
    fail(`GITHUB_RO_SYSTEMATIC_AGENT_SCOPE_BYPASS: ${name}`)
  }
}
for (const [name,overlay] of Object.entries(systematic.categories??{})) {
  if (overlay?.tools?.["github_ro_*"]===true || overlay?.permission?.["github_ro_*"]==="allow") {
    fail(`GITHUB_RO_SYSTEMATIC_CATEGORY_SCOPE_BYPASS: ${name}`)
  }
}
const githubReaderNames=["gentle-orchestrator","explore","sdd-research"]
const githubBlockedNames=["general","repo-research-analyst","sdd-explore","sdd-apply","review-risk","correctness-reviewer"]
const githubCredentialInProbe=Boolean(process.env.GITHUB_REVIEW_TOKEN)
for (const name of [...githubReaderNames,...githubBlockedNames]) {
  const dbg=readDebug(name)
  if (!dbg) continue
  const githubTools=Object.entries(dbg.tools??{}).filter(([id])=>id.startsWith("github_ro_"))
  if (githubReaderNames.includes(name)) {
    // A one-shot opencode debug agent child does not establish the remote MCP
    // connection, so the GitHub tool is normally absent in this neutral probe;
    // absence is not a failure, but present-and-disabled is. The secure-service
    // /mcp probe below owns the authoritative active-connection evidence.
    const readerGithubTool=githubTools.find(([id])=>id==="github_ro_get_file_contents")
    if (readerGithubTool && readerGithubTool[1]===false) {
      fail(`GITHUB_RO_RESEARCH_TOOL_DISABLED: ${name}.github_ro_get_file_contents`)
    }
    for (const [id,enabled] of githubTools) {
      if (enabled===true && /^github_ro_(?:create|add|update|delete|remove|merge|push|fork|set|mark|lock|unlock|request|submit|dismiss|assign|unassign|cancel|rerun|trigger|enable|disable|replace|upsert|edit|close|reopen)(?:_|$)/.test(id)) {
        fail(`GITHUB_RO_MUTATION_TOOL_EXPOSED: ${name}.${id}`)
      }
    }
    if (permissionActionForWildcard(dbg,"github_ro_get_file_contents")!=="allow") {
      fail(`GITHUB_RO_RESEARCH_PERMISSION_MISSING: ${name}`)
    }
  } else if (githubTools.some(([,enabled])=>enabled===true)) {
    fail(`GITHUB_RO_UNAUTHORIZED_AGENT_TOOL_EXPOSED: ${name}`)
  }
}
if (!githubCredentialInProbe) {
  console.log("   info: isolated CLI probe has no GitHub credential; secure-service /mcp and /config probes own active GitHub verification")
} else {
  console.log("   info: neutral CLI debug probe does not materialize remote MCP tools; secure-service /mcp and /config probes own active GitHub verification")
}
for (const t of ["context7_query-docs","context7_resolve-library-id","codegraph_codegraph_explore"]) {
  if (gp[t]!=="allow") fail(`CUSTOM_MCP_PERMISSION_NOT_ALLOW: permission.${t}=${show(gp[t])}`)
}

if (failures) process.exit(1)
console.log(`   ok: all ${inventory.filter((a)=>!expectedFor(systematic,a).disable).length} enabled Systematic agents are registered by the plugin`)
console.log(`   ok: ${controlNames.length} Systematic runtime model/tool controls passed`)
console.log("   ok: GGA primaries, live plugin fallback policy, and sandbox capability boundaries passed")
EOF_RUNTIME_AGENT

echo "== Workflow setup health check =="

# --- 0. Recover reviewed user-owned configuration after generator/sync drift ---
echo "--- 0. User-owned configuration recovery ---"
mkdir -p "$OPENCODE_CONFIG_DIR"

OPENCODE_RECOVERY=$(recover_opencode_config)
case "$OPENCODE_RECOVERY" in
  clean$'\t'*)
    echo "   ok: ${OPENCODE_RECOVERY#*$'\t'}"
    ;;
  repaired$'\t'*)
    repair_note "OpenCode config drift recovered; backup: ${OPENCODE_RECOVERY#*$'\t'}"
    echo "   ok: reviewed OpenCode overlay restored; restart OpenCode before use"
    ;;
  error$'\t'*)
    fail "OPENCODE_CONFIG_RECOVERY_FAILED: ${OPENCODE_RECOVERY#*$'\t'}"
    ;;
  *)
    fail "OPENCODE_CONFIG_RECOVERY_FAILED: unexpected result ${OPENCODE_RECOVERY:-<empty>}"
    ;;
esac

TUI_RECOVERY=$(recover_tui_config)
case "$TUI_RECOVERY" in
  clean$'\t'*)
    echo "   ok: ${TUI_RECOVERY#*$'\t'}"
    ;;
  repaired$'\t'*)
    repair_note "TUI plugin discovery surface recovered: ${TUI_RECOVERY#*$'\t'}"
    echo "   ok: TUI-only plugins preserved; shared package versions now match opencode.json"
    ;;
  error$'\t'*)
    fail "TUI_CONFIG_RECOVERY_FAILED: ${TUI_RECOVERY#*$'\t'}"
    ;;
  *)
    fail "TUI_CONFIG_RECOVERY_FAILED: unexpected result ${TUI_RECOVERY:-<empty>}"
    ;;
esac

LOCAL_AUTO_UPDATE_PATH="${LOCAL_AUTO_UPDATE_REF#file://}"
if [[ "$LOCAL_AUTO_UPDATE_REF" != file://* ]] || [ ! -f "$LOCAL_AUTO_UPDATE_PATH" ]; then
  fail "LOCAL_AUTO_UPDATE_BUILD_MISSING: $LOCAL_AUTO_UPDATE_PATH"
else
  LOCAL_AUTO_UPDATE_CHECK="$({
    node - "$OPENCODE_CONFIG_FILE" "$TUI_CONFIG_FILE" "$LOCAL_AUTO_UPDATE_REF" <<'EOF_LOCAL_AUTO_UPDATE'
const fs = require("fs")
const [opencodeFile, tuiFile, localRef] = process.argv.slice(2)
let failed = false
for (const file of [opencodeFile, tuiFile]) {
  let config
  try {
    config = JSON.parse(fs.readFileSync(file, "utf8"))
  } catch (error) {
    console.log(`cannot read ${file}: ${error.message}`)
    failed = true
    continue
  }
  const plugins = Array.isArray(config.plugin) ? config.plugin : []
  const localCount = plugins.filter((ref) => ref === localRef).length
  const npmRefs = plugins.filter((ref) =>
    typeof ref === "string" && /^opencode-plugin-auto-update(?:@|$)/.test(ref)
  )
  if (localCount !== 1) {
    console.log(`${file}: expected one reviewed local auto-update URI, found ${localCount}`)
    failed = true
  }
  if (npmRefs.length) {
    console.log(`${file}: stale npm auto-update reference(s): ${npmRefs.join(",")}`)
    failed = true
  }
}
if (failed) process.exit(1)
EOF_LOCAL_AUTO_UPDATE
  } 2>&1)"
  if [ "$?" -eq 0 ]; then
    echo "   ok: reviewed local auto-update build is authoritative in OpenCode and TUI configs"
  else
    fail "LOCAL_AUTO_UPDATE_SURFACE_INVALID: ${LOCAL_AUTO_UPDATE_CHECK:-validation failed}"
  fi
fi

AGENTS_RECOVERY=$(recover_agents_file)
case "$AGENTS_RECOVERY" in
  clean$'\t'*)
    echo "   ok: ${AGENTS_RECOVERY#*$'\t'}"
    ;;
  repaired$'\t'*)
    repair_note "AGENTS.md drift recovered; backup: ${AGENTS_RECOVERY#*$'\t'}"
    echo "   ok: reviewed AGENTS routing/memory policy restored; restart OpenCode before use"
    ;;
  error$'\t'*)
    fail "AGENTS_CONFIG_RECOVERY_FAILED: ${AGENTS_RECOVERY#*$'\t'}"
    ;;
  *)
    fail "AGENTS_CONFIG_RECOVERY_FAILED: unexpected result ${AGENTS_RECOVERY:-<empty>}"
    ;;
esac

ROUTER_SKILLS_RECOVERY=$(recover_reviewed_router_skills)
case "$ROUTER_SKILLS_RECOVERY" in
  clean$'	'*)
    echo "   ok: ${ROUTER_SKILLS_RECOVERY#*$'	'}"
    ;;
  repaired$'	'*)
    repair_note "workflow skill drift recovered: ${ROUTER_SKILLS_RECOVERY#*$'	'}"
    echo "   ok: reviewed workflow skills restored; restart OpenCode before use"
    ;;
  error$'	'*)
    fail "WORKFLOW_SKILL_RECOVERY_FAILED: ${ROUTER_SKILLS_RECOVERY#*$'	'}"
    ;;
  *)
    fail "WORKFLOW_SKILL_RECOVERY_FAILED: unexpected result ${ROUTER_SKILLS_RECOVERY:-<empty>}"
    ;;
esac

SYSTEMATIC_RECOVERY=$(recover_systematic_config)
case "$SYSTEMATIC_RECOVERY" in
  clean$'\t'*)
    echo "   ok: ${SYSTEMATIC_RECOVERY#*$'\t'}"
    ;;
  repaired$'\t'*)
    repair_note "Systematic config drift recovered; backup: ${SYSTEMATIC_RECOVERY#*$'\t'}"
    echo "   ok: reviewed Systematic model/security/memory overlays restored; restart OpenCode before use"
    ;;
  error$'\t'*)
    fail "SYSTEMATIC_CONFIG_RECOVERY_FAILED: ${SYSTEMATIC_RECOVERY#*$'\t'}"
    ;;
  *)
    fail "SYSTEMATIC_CONFIG_RECOVERY_FAILED: unexpected result ${SYSTEMATIC_RECOVERY:-<empty>}"
    ;;
esac

FALLBACK_RECOVERY=$(recover_fallback_policy)
case "$FALLBACK_RECOVERY" in
  clean$'\t'*)
    echo "   ok: ${FALLBACK_RECOVERY#*$'\t'}"
    ;;
  repaired$'\t'*)
    repair_note "fallback policy drift recovered; backup: ${FALLBACK_RECOVERY#*$'\t'}"
    echo "   ok: reviewed mapped fallback policy restored; restart OpenCode before use"
    ;;
  error$'\t'*)
    fail "FALLBACK_POLICY_RECOVERY_FAILED: ${FALLBACK_RECOVERY#*$'\t'}"
    ;;
  *)
    fail "FALLBACK_POLICY_RECOVERY_FAILED: unexpected result ${FALLBACK_RECOVERY:-<empty>}"
    ;;
esac

# Muse and pre-V4.1 DeepSeek models are retired from primary assignments.
for MODEL_CONFIG in \
  "$OPENCODE_CONFIG_FILE" "$OPENCODE_CONFIG_SOURCE" \
  "$SYSTEMATIC_CONFIG" "$SYSTEMATIC_CONFIG_SOURCE"; do
  if [ -f "$MODEL_CONFIG" ] && grep -Eq -- 'muse-spark|deepseek-v4-(pro|flash)' "$MODEL_CONFIG" 2>/dev/null; then
    fail "RETIRED_MUSE_OR_DEEPSEEK_MODEL_REFERENCE: $MODEL_CONFIG"
  fi
done

if [ "$RECOVERY_ONLY" -eq 1 ]; then
  if [ "$FAIL" -ne 0 ]; then
    echo
    echo "== Config recovery failed — see messages above =="
    exit 1
  fi
  echo
  if [ "$AUTO_REPAIRED" -ne 0 ]; then
    echo "== Config recovery complete — restart OpenCode before use =="
  else
    echo "== Config recovery not needed — reviewed overlays are current =="
  fi
  exit 0
fi

# --- 1. Gentle AI v3.5.0+ + user-selected native review/telemetry modes ---
echo "--- 1. Gentle AI v3.5.0+ + native review mode ---"
if command_exists gentle-ai; then
  VERSION_RAW=$(gentle-ai --version 2>/dev/null | head -1 || true)
  echo "   ${VERSION_RAW:-version unavailable}"
  GENTLE_VERSION=$(printf '%s\n' "$VERSION_RAW" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  if [ -z "$GENTLE_VERSION" ] || [ "$(printf '%s\n' "3.5.0" "$GENTLE_VERSION" | sort -V | head -1)" != "3.5.0" ]; then
    fail "Gentle AI v3.5.0+ is required by this workflow"
  fi
  MODE=$(gentle-ai review mode status --cwd "$WORKSPACE" 2>/dev/null | head -1 || true)
  if [[ "$MODE" =~ ^receipt-driven\ development:\ (on|off)\ \(decided\ by\ (default|global|clone-local)\)$ ]]; then
    echo "   $MODE"
    if [ "${BASH_REMATCH[1]}" = off ]; then
      echo "   info: RDD is explicitly off for this project; preserving the user's choice"
    fi
  else
    fail "GENTLE_AI_V3_5_REVIEW_MODE_UNKNOWN: cannot read effective RDD mode and deciding source: ${MODE:-<empty>}"
  fi
  if [ -f "$GENTLE_STATE_FILE" ]; then
    SYNC_WITNESS=$(node -e 'const fs=require("fs");try{const s=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));if(typeof s.last_synced_at!=="string"||!s.last_synced_at||!Number.isFinite(Date.parse(s.last_synced_at)))process.exit(1);console.log(s.last_synced_at+"|"+(s.installed_binary_version||"unknown"))}catch{process.exit(1)}' "$GENTLE_STATE_FILE" 2>/dev/null) || SYNC_WITNESS=""
    if [ -n "$SYNC_WITNESS" ]; then
      echo "   ok: last successful Gentle AI sync: ${SYNC_WITNESS%%|*} (state binary version: ${SYNC_WITNESS#*|})"
      STATE_BINARY_VERSION=${SYNC_WITNESS#*|}
      if [ "$STATE_BINARY_VERSION" != unknown ] && [ "${STATE_BINARY_VERSION#v}" != "$GENTLE_VERSION" ]; then
        fail "GENTLE_AI_V3_5_SYNC_VERSION_DRIFT: managed state does not match installed binary; run gentle-ai sync"
      fi
    else
      fail "GENTLE_AI_V3_5_SYNC_NOT_CONFIRMED: last_synced_at is absent or invalid in $GENTLE_STATE_FILE; run gentle-ai sync"
    fi
  else
    fail "GENTLE_AI_V3_5_SYNC_STATE_MISSING: $GENTLE_STATE_FILE; run gentle-ai sync"
  fi
  TELEMETRY_STATUS=$(gentle-ai telemetry status 2>/dev/null | head -1 || true)
  if [ -n "$TELEMETRY_STATUS" ]; then
    echo "   telemetry: $TELEMETRY_STATUS"
  else
    fail "could not read Gentle AI v3 telemetry status"
  fi
  if gentle-ai sdd-archive-compose --help >/dev/null 2>&1; then
    echo "   ok: native sdd-archive-compose command available"
  else
    fail "Gentle AI v3 native sdd-archive-compose command missing"
  fi
else
  fail "gentle-ai executable not found"
fi

# Gentle AI 3.5.0 ODD delivery skills are resolved by registry name and
# must be installed before feature work can create scoped commits/PR slices.
for odd_skill in work-unit-commits chained-pr; do
  if [ ! -f "$SKILLS_DIR/$odd_skill/SKILL.md" ]; then
    fail "GENTLE_AI_V3_ODD_SKILL_MISSING: $SKILLS_DIR/$odd_skill/SKILL.md; run gentle-ai sync after upgrading"
  else
    echo "   ok: Gentle AI ODD delivery skill installed: $odd_skill"
  fi
done

RESEARCH_SKILL="$SKILLS_DIR/sdd-research/SKILL.md"
RESEARCH_COMMAND="$OPENCODE_CONFIG_DIR/commands/sdd-research.md"
if [ ! -f "$RESEARCH_SKILL" ]; then
  fail "Gentle AI v3 sdd-research skill missing: $RESEARCH_SKILL"
elif ! grep -Fq -- 'Research remains optional, including after selection.' "$RESEARCH_SKILL" 2>/dev/null || \
     ! grep -Fq -- 'Use only actually available and authorized external tools.' "$RESEARCH_SKILL" 2>/dev/null || \
     grep -Fq -- 'Admit only `gentle-ai.sdd-research-capability/v1`' "$RESEARCH_SKILL" 2>/dev/null; then
  fail "GENTLE_AI_V3_RESEARCH_SKILL_DRIFT: run gentle-ai sync; installed sdd-research must use optional output-only research without the retired admission gate"
else
  echo "   ok: sdd-research skill installed"
fi
VERIFY_SKILL="$SKILLS_DIR/sdd-verify/SKILL.md"
ARCHIVE_SKILL="$SKILLS_DIR/sdd-archive/SKILL.md"
if [ ! -f "$VERIFY_SKILL" ] || ! grep -Fq -- 'Verification is optional, not a prerequisite for archive.' "$VERIFY_SKILL" 2>/dev/null; then
  fail "GENTLE_AI_V3_VERIFY_SKILL_DRIFT: run gentle-ai sync; verification must not gate archive"
fi
if [ ! -f "$ARCHIVE_SKILL" ] || ! grep -Fq -- 'unfinished tasks do not block archive' "$ARCHIVE_SKILL" 2>/dev/null; then
  fail "GENTLE_AI_V3_ARCHIVE_SKILL_DRIFT: run gentle-ai sync; archive must record actual unfinished work"
fi
if [ ! -f "$RESEARCH_COMMAND" ]; then
  fail "Gentle AI v3 OpenCode sdd-research command missing: $RESEARCH_COMMAND"
elif ! grep -Fq -- 'Research remains optional, including after selection.' "$RESEARCH_COMMAND" 2>/dev/null; then
  fail "GENTLE_AI_V3_RESEARCH_COMMAND_DRIFT: run gentle-ai sync; OpenCode command still has the old admission gate"
else
  echo "   ok: sdd-research command installed"
fi

# --- 2. Resolve active Systematic install ---
echo "--- 2. Active Systematic install ---"

# Resolve the Systematic source tree from the plugin spec that is actually
# deployed in opencode.json. Never prefer an unrelated @latest/bare cache over
# an exact configured pin: later inventory/model/permission checks must inspect
# the same package version OpenCode is configured to load.
SYSTEMATIC_PLUGIN_SPEC="$(
  node - "$OPENCODE_CONFIG_FILE" <<'EOF_SYSTEMATIC_SPEC' 2>/dev/null || true
const fs = require("fs")
const path = process.argv[2]
try {
  const config = JSON.parse(fs.readFileSync(path, "utf8"))
  const plugins = Array.isArray(config.plugin) ? config.plugin : []
  const specs = plugins.filter((value) =>
    typeof value === "string" &&
    (value === "@fro.bot/systematic" || value.startsWith("@fro.bot/systematic@"))
  )
  if (specs.length === 1) process.stdout.write(specs[0])
  else if (specs.length > 1) process.stdout.write(`__MULTIPLE__\n${specs.join("\n")}`)
} catch {}
EOF_SYSTEMATIC_SPEC
)"

if [ -z "$SYSTEMATIC_PLUGIN_SPEC" ]; then
  fail "SYSTEMATIC_PLUGIN_SPEC_MISSING: no @fro.bot/systematic plugin entry in $OPENCODE_CONFIG_FILE"
elif printf '%s\n' "$SYSTEMATIC_PLUGIN_SPEC" | grep -q '^__MULTIPLE__$'; then
  fail "SYSTEMATIC_PLUGIN_SPEC_AMBIGUOUS: multiple @fro.bot/systematic plugin entries are configured"
else
  echo "   configured: $SYSTEMATIC_PLUGIN_SPEC"

  SYSTEMATIC_REQUESTED="${SYSTEMATIC_PLUGIN_SPEC#@fro.bot/systematic}"
  SYSTEMATIC_REQUESTED="${SYSTEMATIC_REQUESTED#@}"
  [ "$SYSTEMATIC_PLUGIN_SPEC" = "@fro.bot/systematic" ] && SYSTEMATIC_REQUESTED=""

  is_exact_version=0
  if printf '%s' "$SYSTEMATIC_REQUESTED" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$'; then
    is_exact_version=1
  fi

  candidate_root=""
  if [ "$is_exact_version" -eq 1 ]; then
    exact_cache="$PACKAGES_DIR/systematic@$SYSTEMATIC_REQUESTED/node_modules/@fro.bot/systematic"
    if [ -d "$exact_cache/skills" ] && [ -d "$exact_cache/agents" ] && [ -f "$exact_cache/package.json" ]; then
      candidate_root="$exact_cache"
    else
      # Current upstream OpenCode documents a shared node_modules cache, while
      # the auto-update plugin may materialize spec-addressed package trees.
      # Accept either layout, but only when package.json proves the exact pin.
      standard_cache="$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic"
      standard_version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$standard_cache/package.json" 2>/dev/null || true)"
      if [ "$standard_version" = "$SYSTEMATIC_REQUESTED" ] && [ -d "$standard_cache/skills" ] && [ -d "$standard_cache/agents" ]; then
        candidate_root="$standard_cache"
      fi

      # Cache naming is an implementation detail. If it changes, locate a
      # candidate by the nested package's authoritative package.json version.
      if [ -z "$candidate_root" ]; then
        while IFS= read -r pkg; do
          [ -n "$pkg" ] || continue
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          root="$(dirname "$pkg")"
          if [ "$version" = "$SYSTEMATIC_REQUESTED" ] && [ -d "$root/skills" ] && [ -d "$root/agents" ]; then
            candidate_root="$root"
            break
          fi
        done < <(find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null | sort)
      fi
    fi

    if [ -z "$candidate_root" ]; then
      discovered="$(
        { find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json"
        } |
        while IFS= read -r pkg; do
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          [ -n "$version" ] && printf '%s=%s\n' "$(dirname "$pkg")" "$version"
        done | sort | paste -sd ';' -
      )"
      fail "SYSTEMATIC_CONFIGURED_VERSION_NOT_INSTALLED: configured=$SYSTEMATIC_REQUESTED discovered=${discovered:-<none>}"
    fi
  else
    # Non-exact specs remain supported, but are intentionally reported as such.
    # They cannot prove reproducibility as strongly as an exact semver pin.
    suffix="${SYSTEMATIC_REQUESTED:-bare}"
    if [ -n "$SYSTEMATIC_REQUESTED" ]; then
      tagged="$PACKAGES_DIR/systematic@$SYSTEMATIC_REQUESTED/node_modules/@fro.bot/systematic"
    else
      tagged="$PACKAGES_DIR/systematic/node_modules/@fro.bot/systematic"
    fi
    if [ -d "$tagged/skills" ] && [ -d "$tagged/agents" ] && [ -f "$tagged/package.json" ]; then
      candidate_root="$tagged"
    else
      fail "SYSTEMATIC_CONFIGURED_CACHE_NOT_FOUND: configured=$SYSTEMATIC_PLUGIN_SPEC expected=$tagged"
    fi
  fi

  if [ -n "$candidate_root" ]; then
    ACTIVE_ROOT="$candidate_root"
    ACTIVE_SKILLS="$ACTIVE_ROOT/skills"
    ACTIVE_AGENTS="$ACTIVE_ROOT/agents"
    SYSTEMATIC_NODE_MODULES="$(dirname "$(dirname "$ACTIVE_ROOT")")"

    VERSION="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$ACTIVE_ROOT/package.json" 2>/dev/null || true)"
    echo "   resolved cache: $ACTIVE_ROOT"
    echo "   version: ${VERSION:-<unknown>}"

    if [ -z "$VERSION" ] || [ "$(printf '%s\n' "3.18.4" "$VERSION" | sort -V | head -n 1)" != "3.18.4" ]; then
      fail "Systematic v3.18.4+ is required for workflow-guard terminal replay fidelity; got ${VERSION:-<unknown>}"
    fi

    if [ "$is_exact_version" -eq 1 ] && [ "$VERSION" != "$SYSTEMATIC_REQUESTED" ]; then
      fail "SYSTEMATIC_PIN_MISMATCH: configured=$SYSTEMATIC_REQUESTED resolved=${VERSION:-<unknown>} path=$ACTIVE_ROOT"
      ACTIVE_ROOT=""
      ACTIVE_SKILLS=""
      ACTIVE_AGENTS=""
      SYSTEMATIC_NODE_MODULES=""
    elif [ "$is_exact_version" -eq 1 ]; then
      echo "   ok: exact Systematic pin is materialized and source checks will use it"
    else
      echo "   !! Systematic is not configured with an exact semver pin; source checks use the configured cache tag"
    fi

    # Stale caches are diagnostic only. They are harmless once source resolution
    # is anchored to the configured plugin spec, but listing them makes cleanup
    # straightforward.
    stale=()
    while IFS= read -r pkg; do
      [ -n "$pkg" ] || continue
      root="$(dirname "$pkg")"
      [ "$root" = "$ACTIVE_ROOT" ] && continue
      version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
      stale+=("$root=${version:-unknown}")
    done < <(
      { find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null
        [ -f "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json"
      } | sort -u
    )
    if [ "${#stale[@]}" -gt 0 ]; then
      echo "   info: ignored other cached Systematic trees:"
      for item in "${stale[@]}"; do
        echo "      $item"
      done
    fi
  fi
fi

# --- 2b. Resolve the exact Magic Context package OpenCode is configured to load ---
echo "--- 2b. Active Magic Context install ---"
MAGIC_PLUGIN_SPEC="$(
  node - "$OPENCODE_CONFIG_FILE" <<'EOF_MAGIC_SPEC' 2>/dev/null || true
const fs = require("fs")
const file = process.argv[2]
try {
  const config = JSON.parse(fs.readFileSync(file, "utf8"))
  const plugins = Array.isArray(config.plugin) ? config.plugin : []
  const specs = plugins.filter((value) =>
    typeof value === "string" &&
    (value === "@cortexkit/opencode-magic-context" ||
      value.startsWith("@cortexkit/opencode-magic-context@"))
  )
  if (specs.length === 1) process.stdout.write(specs[0])
  else if (specs.length > 1) process.stdout.write(`__MULTIPLE__\n${specs.join("\n")}`)
} catch {}
EOF_MAGIC_SPEC
)"

if [ -z "$MAGIC_PLUGIN_SPEC" ]; then
  fail "MAGIC_CONTEXT_PLUGIN_SPEC_MISSING: no @cortexkit/opencode-magic-context entry in $OPENCODE_CONFIG_FILE"
elif printf '%s\n' "$MAGIC_PLUGIN_SPEC" | grep -q '^__MULTIPLE__$'; then
  fail "MAGIC_CONTEXT_PLUGIN_SPEC_AMBIGUOUS: multiple @cortexkit/opencode-magic-context entries are configured"
else
  echo "   configured: $MAGIC_PLUGIN_SPEC"
  MAGIC_REQUESTED="${MAGIC_PLUGIN_SPEC#@cortexkit/opencode-magic-context@}"
  if [ "$MAGIC_PLUGIN_SPEC" = "@cortexkit/opencode-magic-context" ] || \
     ! printf '%s' "$MAGIC_REQUESTED" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$'; then
    fail "MAGIC_CONTEXT_VERSION_NOT_EXACT: configured=$MAGIC_PLUGIN_SPEC"
  else
    MAGIC_ROOT="$MAGIC_PACKAGES_DIR/opencode-magic-context@$MAGIC_REQUESTED/node_modules/@cortexkit/opencode-magic-context"
    if [ ! -f "$MAGIC_ROOT/package.json" ]; then
      MAGIC_ROOT=""
      standard_magic="$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context"
      standard_magic_version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$standard_magic/package.json" 2>/dev/null || true)"
      if [ "$standard_magic_version" = "$MAGIC_REQUESTED" ]; then
        MAGIC_ROOT="$standard_magic"
      else
        while IFS= read -r pkg; do
          [ -n "$pkg" ] || continue
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          if [ "$version" = "$MAGIC_REQUESTED" ]; then
            MAGIC_ROOT="$(dirname "$pkg")"
            break
          fi
        done < <(find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null | sort)
      fi
    fi

    if [ -z "$MAGIC_ROOT" ]; then
      discovered="$(
        { find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json"
        } |
        while IFS= read -r pkg; do
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          [ -n "$version" ] && printf '%s=%s\n' "$(dirname "$pkg")" "$version"
        done | sort | paste -sd ';' -
      )"
      fail "MAGIC_CONTEXT_CONFIGURED_VERSION_NOT_INSTALLED: configured=$MAGIC_REQUESTED discovered=${discovered:-<none>}"
    else
      MAGIC_RESOLVED_VERSION="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$MAGIC_ROOT/package.json" 2>/dev/null || true)"
      echo "   resolved cache: $MAGIC_ROOT"
      echo "   version: ${MAGIC_RESOLVED_VERSION:-<unknown>}"
      if [ "$MAGIC_RESOLVED_VERSION" != "$MAGIC_REQUESTED" ]; then
        fail "MAGIC_CONTEXT_PIN_MISMATCH: configured=$MAGIC_REQUESTED resolved=${MAGIC_RESOLVED_VERSION:-<unknown>} path=$MAGIC_ROOT"
      else
        echo "   ok: exact Magic Context pin is materialized and matches opencode.json"
      fi

      stale_magic=()
      while IFS= read -r pkg; do
        [ -n "$pkg" ] || continue
        root="$(dirname "$pkg")"
        [ "$root" = "$MAGIC_ROOT" ] && continue
        version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
        stale_magic+=("$root=${version:-unknown}")
      done < <(
        { find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json"
        } | sort -u
      )
      if [ "${#stale_magic[@]}" -gt 0 ]; then
        echo "   info: ignored other cached Magic Context trees (not auto-deleted):"
        for item in "${stale_magic[@]}"; do
          echo "      $item"
        done
      fi
    fi
  fi
fi

# --- 2c. Incomplete plugin package directories (interrupted installs) ---
echo "--- 2c. Plugin package integrity ---"
if [ ! -f "$PLUGIN_CACHE_INTEGRITY_HELPER" ]; then
  fail "PLUGIN_PACKAGE_INTEGRITY_HELPER_MISSING: $PLUGIN_CACHE_INTEGRITY_HELPER"
else
  PLUGIN_INTEGRITY_RESULT="$(
    python3 - "$PLUGIN_CACHE_INTEGRITY_HELPER" "$OPENCODE_CACHE_DIR/packages" "$AUTO_UPDATE_LOCK" "$PLUGIN_QUARANTINE_DIR" "$OPENCODE_CONFIG_FILE" "$TUI_CONFIG_FILE" <<'PY_PLUGIN_INTEGRITY' 2>&1
import json
import re
import subprocess
import sys

helper, cache_root, lock, quarantine, *configs = sys.argv[1:]
exact = re.compile(r"^(?:@[^/@]+/)?[^/@]+@\d+\.\d+\.\d+(?:[+-][0-9A-Za-z.+-]+)?$")
specs = []
for path in configs:
    try:
        with open(path, encoding="utf-8") as handle:
            plugins = json.load(handle).get("plugin", [])
    except Exception:
        continue
    for ref in plugins if isinstance(plugins, list) else []:
        if isinstance(ref, str) and exact.match(ref) and ref not in specs:
            specs.append(ref)
if not specs:
    print("ok\tno exact-version plugin specs configured")
    raise SystemExit(0)
cmd = [sys.executable, helper, "scan", "--cache-root", cache_root, "--lock", lock,
       "--quarantine-dir", quarantine, "--apply"]
for spec in specs:
    cmd += ["--spec", spec]
proc = subprocess.run(cmd, capture_output=True, text=True)
try:
    results = json.loads(proc.stdout)["results"]
except Exception:
    print(f"error\thelper failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    raise SystemExit(0)
problems = 0
for item in results:
    if item.get("action") == "quarantined":
        print(f"quarantined\t{item['spec']}\t{item['quarantined_to']}")
        problems += 1
    elif item.get("action") == "deferred":
        print(f"deferred\t{item['spec']}\t{item['reason']}; {item['detail']}")
        problems += 1
if not problems:
    print(f"ok\t{len(results)} configured plugin package(s) complete or not yet installed")
PY_PLUGIN_INTEGRITY
  )"
  while IFS=$'\t' read -r state spec detail; do
    case "$state" in
      ok)          echo "   ok: $spec" ;;
      quarantined) fail "PLUGIN_PACKAGE_INCOMPLETE_QUARANTINED: $spec -> $detail; restart OpenCode to reinstall" ;;
      deferred)    fail "PLUGIN_PACKAGE_INCOMPLETE: $spec ($detail)" ;;
      error)       fail "PLUGIN_PACKAGE_INTEGRITY_CHECK_FAILED: $spec" ;;
      *)           [ -n "$state" ] && fail "PLUGIN_PACKAGE_INTEGRITY_CHECK_FAILED: unexpected output $state" ;;
    esac
  done <<< "$PLUGIN_INTEGRITY_RESULT"
fi

# --- 3. Systematic bundled skills / obsolete symlinks ---
echo "--- 3. Systematic bundled skills ---"
if [ -n "$ACTIVE_SKILLS" ]; then
  for skill in "${REQUIRED_SKILLS[@]}"; do
    bundled="$ACTIVE_SKILLS/$skill/SKILL.md"
    if [ -f "$bundled" ]; then
      echo "   ok: $skill bundled by active Systematic install"
    else
      fail "required Systematic skill missing: $skill (expected $bundled)"
    fi
  done

  for required_pipeline in "$ACTIVE_SKILLS/ce-review/scripts/validate-review.mjs" "$ACTIVE_SKILLS/ce-review/references/pipeline-invocation.md" "$ACTIVE_SKILLS/ce-review-cleanup/scripts/cleanup.mjs"; do
    if [ ! -f "$required_pipeline" ]; then fail "SYSTEMATIC_REVIEW_PIPELINE_MISSING: $required_pipeline"; fi
  done

  # Systematic now registers its bundled skills directly. Old symlinks under
  # ~/.config/opencode/skills only make OpenCode discover the same skill twice.
  REMOVED_LINKS=0
  if [ -d "$SKILLS_DIR" ]; then
    while IFS= read -r -d '' link; do
      raw_target=$(readlink "$link" 2>/dev/null || true)
      resolved_target=$(readlink -f "$link" 2>/dev/null || true)
      if [[ "$raw_target" == *"/@fro.bot/systematic/"* ]] || \
         [[ "$resolved_target" == *"/@fro.bot/systematic/"* ]]; then
        repair_note "removing obsolete Systematic skill symlink: $link -> $raw_target"
        if rm -- "$link"; then
          REMOVED_LINKS=$((REMOVED_LINKS + 1))
        else
          fail "could not remove obsolete Systematic skill symlink: $link"
        fi
      fi
    done < <(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type l -print0 2>/dev/null)
  fi

  if [ "$REMOVED_LINKS" -eq 0 ]; then
    echo "   ok: no redundant Systematic skill symlinks"
  else
    echo "   ok: removed $REMOVED_LINKS redundant Systematic skill symlink(s)"
  fi
fi

# --- 4. Global AGENTS.md routing section ---
echo "--- 4. Global AGENTS.md routing section ---"
echo "   ok: routing section present and canonical (validated during recovery)"

# --- 5. Skill registry ---
echo "--- 5. Skill registry ---"
if command_exists gentle-ai; then
  if REGISTRY_OUTPUT=$(gentle-ai skill-registry refresh --cwd "$WORKSPACE" 2>&1); then
    echo "$REGISTRY_OUTPUT" | head -1
  else
    echo "$REGISTRY_OUTPUT" | head -12
    fail "gentle-ai skill-registry refresh failed"
  fi
else
  fail "gentle-ai executable not found; registry refresh skipped"
fi

# --- 6. Reviewed plugin mirrors + script digest binding ---
echo "--- 6. Reviewed plugin mirrors ---"
for required_plugin in "$PLUGINS_DIR/sandbox-tools.ts" "$PLUGINS_DIR/routing-guard.ts" "$RELAY_PLUGIN_DEPLOYED" "$PLUGINS_DIR/lib/broker-client.ts" "$HOST_APPROVAL_HELPER_DEPLOYED"; do
  if [ ! -f "$required_plugin" ]; then
    fail "HOST_TOOL_PLUGIN_MISSING: $required_plugin (install from agent-sandbox-integration; keep installer and rollback in sync)"
  fi
done
if [ -n "$SANDBOX_INTEGRATION_REPO" ]; then
  for relative_plugin in sandbox-tools.ts routing-guard.ts reviewer-relay-transport.ts lib/broker-client.ts lib/host-tool-approval.ts; do
    source_plugin="$SANDBOX_INTEGRATION_REPO/opencode/plugins/$relative_plugin"
    deployed_plugin="$PLUGINS_DIR/$relative_plugin"
    if [ ! -f "$source_plugin" ] || ! cmp -s "$source_plugin" "$deployed_plugin"; then
      fail "HOST_TOOL_PLUGIN_SOURCE_DRIFT: $relative_plugin; review installer and rollback before deployment"
    fi
  done
  for installer in "$SANDBOX_INTEGRATION_REPO/scripts/install-user-files" "$SANDBOX_INTEGRATION_REPO/scripts/rollback"; do
    if [ ! -f "$installer" ] || ! grep -Fq 'reviewer-relay-transport.ts' "$installer" || ! grep -Fq 'host-tool-approval.ts' "$installer"; then
      fail "HOST_TOOL_INSTALL_ROLLBACK_GAP: $installer must include both new plugin files"
    fi
  done
else
  echo "   info: set WORKFLOW_VERIFY_SANDBOX_REPO to inspect agent-sandbox-integration source, installer and rollback parity"
fi
SELF_PATH=$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")
SELF_SHA=$(sha256_file "$SELF_PATH")
if [ -z "$SELF_SHA" ]; then
  fail "could not compute SHA256 for $SELF_PATH"
  CAN_RUNTIME_PROBE=0
else
  echo "   verify-workflow.sh sha256: $SELF_SHA"
fi

# workflow-health-check.ts is special: its reviewed source must pin this exact
# script before we deploy it, otherwise the next OpenCode startup will (correctly)
# refuse to execute the verifier.
if [ ! -f "$HEALTH_PLUGIN_SOURCE" ]; then
  fail "health plugin source missing: $HEALTH_PLUGIN_SOURCE"
  CAN_RUNTIME_PROBE=0
else
  SOURCE_PIN=$(read_verify_script_pin "$HEALTH_PLUGIN_SOURCE" 2>/dev/null || true)
  if [ -z "$SOURCE_PIN" ]; then
    fail "could not read VERIFY_SCRIPT_SHA256 from health plugin source"
    CAN_RUNTIME_PROBE=0
  elif [ "$SOURCE_PIN" != "$SELF_SHA" ]; then
    fail "health plugin source pins $SOURCE_PIN but this script is $SELF_SHA"
    echo "      update VERIFY_SCRIPT_SHA256 in $HEALTH_PLUGIN_SOURCE after reviewing this script"
    CAN_RUNTIME_PROBE=0
  else
    echo "   ok: health plugin source pins this exact verifier"
  fi

  if grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_SOURCE"; then
    echo "   ok: health plugin source contains runtime-probe recursion guard"
  else
    fail "health plugin source lacks WORKFLOW_HEALTH_CHECK_PROBE recursion guard"
    CAN_RUNTIME_PROBE=0
  fi

  if [ "$SOURCE_PIN" = "$SELF_SHA" ] && grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_SOURCE"; then
    if [ -f "$HEALTH_PLUGIN_DEPLOYED" ] && cmp -s "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED"; then
      echo "   ok: workflow-health-check.ts mirror is current"
    else
      repair_note "re-mirroring workflow-health-check.ts from reviewed source"
      if cp "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED" && cmp -s "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED"; then
        echo "   ok: workflow-health-check.ts mirror restored (restart OpenCode to load it)"
      else
        fail "could not re-mirror workflow-health-check.ts"
        CAN_RUNTIME_PROBE=0
      fi
    fi
  fi
fi

# New runtime routing guard: reviewed workspace copy is authoritative.
if [ ! -f "$ROUTING_GUARD_SOURCE" ]; then
  fail "routing guard source missing: $ROUTING_GUARD_SOURCE"
else
  if [ -f "$ROUTING_GUARD_DEPLOYED" ] && cmp -s "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED"; then
    echo "   ok: systematic-routing-guard.ts mirror is current"
  else
    repair_note "re-mirroring systematic-routing-guard.ts from reviewed source"
    if cp "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED" && cmp -s "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED"; then
      echo "   ok: systematic-routing-guard.ts mirror restored (restart OpenCode to load it)"
    else
      fail "could not re-mirror systematic-routing-guard.ts"
    fi
  fi
fi

# Validate the deployed plugin bytes through the same factory/hook load check.
# Factory probes run below, after all three reviewed plugin mirrors.

routing_guard_test_home=$(mktemp -d) || {
  fail "could not create isolated HOME for routing-guard tests"
  routing_guard_test_home=""
}
if [ -n "$routing_guard_test_home" ]; then
  if (cd "$WORKSPACE" && env HOME="$routing_guard_test_home" bun test tests/routing-guard); then
    echo "   OK routing guard tests"
  else
    fail "routing guard test suite failed"
  fi
  rm -rf "$routing_guard_test_home"
fi

# Astra is exposed through derived aliases rather than a Systematic profile or
# copied agent definitions. The reviewed local plugin must remain byte-identical
# to its deployed mirror so Systematic/Gentle AI prompts can continue to update.
if [ ! -f "$ASTRA_PLUGIN_SOURCE" ]; then
  fail "Astra Sol-upgrade plugin source missing: $ASTRA_PLUGIN_SOURCE"
else
  ASTRA_SOURCE_OK=1
  for marker in 'SOL_MODEL = "openai/gpt-6.1-sol"' 'ASTRA_MODEL = "openai/gpt-6-astra"' 'ASTRA_SUFFIX = "-astra"' 'isImplementationRoute' 'systematic-implementer' 'bug-reproduction-validator'; do
    if ! grep -Fq -- "$marker" "$ASTRA_PLUGIN_SOURCE"; then
      fail "Astra Sol-upgrade plugin source is missing required marker: $marker"
      ASTRA_SOURCE_OK=0
    fi
  done
  if [ "$ASTRA_SOURCE_OK" -eq 1 ]; then
    if [ -f "$ASTRA_PLUGIN_DEPLOYED" ] && cmp -s "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED"; then
      echo "   ok: astra-sol-upgrade.ts mirror is current"
    else
      repair_note "re-mirroring astra-sol-upgrade.ts from reviewed source"
      if cp "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED" && cmp -s "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED"; then
        echo "   ok: astra-sol-upgrade.ts mirror restored (restart OpenCode once to load the repaired plugin)"
      else
        fail "could not re-mirror astra-sol-upgrade.ts"
      fi
    fi
    # Factory probes run only after all three reviewed plugin mirrors, including Astra, are current.
    check_plugin_loads "$PLUGINS_DIR" factory
  fi
fi

# The superseded model-tiering plugin must remain disabled. Having both active
# would create overlapping mutations/diagnostics at the task hook boundary.
if [ -e "$OLD_TIERING_PLUGIN_ACTIVE" ]; then
  fail "obsolete systematic-model-tiering.ts is active; keep it .disabled or remove it"
else
  echo "   ok: obsolete systematic-model-tiering.ts is not active"
fi

# Auto-update lock health. opencode-plugin-auto-update can leave a lock behind
# if an update process dies after acquiring it. Its normal lock acquisition does
# not force-recover stale locks, so an orphan can block every future update.
# Only self-repair when the lock contains a numeric PID and that PID is definitely
# not running. Never delete a live or ambiguous lock.
echo "   auto-update lock health:"
if [ ! -e "$AUTO_UPDATE_LOCK" ]; then
  echo "   ok: no auto-update lock present"
elif [ ! -f "$AUTO_UPDATE_LOCK" ]; then
  fail "auto-update lock path exists but is not a regular file: $AUTO_UPDATE_LOCK"
else
  AUTO_UPDATE_PID=$(sed -nE 's/.*"pid"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$AUTO_UPDATE_LOCK" | head -1)
  AUTO_UPDATE_TS=$(sed -nE 's/.*"timestamp"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$AUTO_UPDATE_LOCK" | head -1)

  if [[ ! "$AUTO_UPDATE_PID" =~ ^[0-9]+$ ]] || [ "$AUTO_UPDATE_PID" -le 0 ]; then
    fail "auto-update lock is malformed or has no valid PID; refusing automatic deletion"
    sed -n '1,8p' "$AUTO_UPDATE_LOCK" | sed 's/^/      /'
  elif kill -0 "$AUTO_UPDATE_PID" 2>/dev/null; then
    if [[ "$AUTO_UPDATE_TS" =~ ^[0-9]+$ ]]; then
      AUTO_UPDATE_LOCK_SEC=$((AUTO_UPDATE_TS / 1000))
      AUTO_UPDATE_LOCK_UTC=$(date -u -d "@$AUTO_UPDATE_LOCK_SEC" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || true)
      echo "   ok: auto-update lock is held by live pid $AUTO_UPDATE_PID${AUTO_UPDATE_LOCK_UTC:+ (since $AUTO_UPDATE_LOCK_UTC)}"
    else
      echo "   ok: auto-update lock is held by live pid $AUTO_UPDATE_PID"
    fi
  else
    LOCK_DETAIL="pid $AUTO_UPDATE_PID is not running"
    if [[ "$AUTO_UPDATE_TS" =~ ^[0-9]+$ ]]; then
      AUTO_UPDATE_LOCK_SEC=$((AUTO_UPDATE_TS / 1000))
      AUTO_UPDATE_LOCK_UTC=$(date -u -d "@$AUTO_UPDATE_LOCK_SEC" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || true)
      if [ -n "$AUTO_UPDATE_LOCK_UTC" ]; then
        LOCK_DETAIL="$LOCK_DETAIL; lock timestamp $AUTO_UPDATE_LOCK_UTC"
      fi
    fi

    repair_note "removing orphaned auto-update lock ($LOCK_DETAIL)"
    if rm -- "$AUTO_UPDATE_LOCK"; then
      echo "   ok: orphaned auto-update lock removed; future update passes are unblocked"
    else
      fail "could not remove orphaned auto-update lock: $AUTO_UPDATE_LOCK"
    fi
  fi
fi

# Disk configuration is only the desired state. OpenCode and updater plugins
# may atomically rewrite or merely touch unchanged files during startup, making
# mtime > service-start permanently true. Bind file content hashes to a systemd
# invocation instead: a changed generation fails until a later invocation sees
# the same hashes, while same-content startup rewrites remain certified.
# Never restart automatically: that would disrupt active sessions.
echo "   secure OpenCode runtime generation:"
if ! command_exists systemctl; then
  echo "   info: systemctl unavailable; secure runtime generation not checked"
else
  SERVICE_LOAD_STATE="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p LoadState --value 2>/dev/null || true)"
  SERVICE_ACTIVE_STATE="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p ActiveState --value 2>/dev/null || true)"
  if [ "$SERVICE_LOAD_STATE" != "loaded" ]; then
    echo "   info: $SECURE_OPENCODE_SERVICE is not installed in this environment; freshness check skipped"
  elif [ "$SERVICE_ACTIVE_STATE" != "active" ]; then
    echo "   info: $SECURE_OPENCODE_SERVICE is ${SERVICE_ACTIVE_STATE:-inactive}; no loaded runtime is being certified"
  else
    SERVICE_STARTED_RAW="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p ExecMainStartTimestamp --value 2>/dev/null || true)"
    SERVICE_STARTED_EPOCH="$(date -d "$SERVICE_STARTED_RAW" +%s 2>/dev/null || true)"
    SERVICE_INVOCATION_ID="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p InvocationID --value 2>/dev/null || true)"
    if [[ ! "$SERVICE_STARTED_EPOCH" =~ ^[0-9]+$ ]]; then
      fail "SECURE_OPENCODE_START_TIME_UNAVAILABLE: could not parse ${SERVICE_STARTED_RAW:-<empty>}"
    else
      if [ -z "$SERVICE_INVOCATION_ID" ]; then
        SERVICE_INVOCATION_ID="start-$SERVICE_STARTED_EPOCH"
      fi
      RUNTIME_GENERATION_RESULT="$(
        python3 - "$SECURE_RUNTIME_WITNESS" "$SECURE_OPENCODE_SERVICE" \
          "$SERVICE_INVOCATION_ID" "$SERVICE_STARTED_EPOCH" \
        "$OPENCODE_CONFIG_FILE" "$AGENTS_FILE" "$SYSTEMATIC_CONFIG" \
        "$FALLBACK_POLICY_DEPLOYED" "$HEALTH_PLUGIN_DEPLOYED" \
          "$ROUTING_GUARD_DEPLOYED" "$ASTRA_PLUGIN_DEPLOYED" \
          "$RELAY_PLUGIN_DEPLOYED" "$HOST_APPROVAL_HELPER_DEPLOYED" \
          "$FALLBACK_EXCLUSION_SOURCE" <<'PY_RUNTIME_WITNESS'
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

witness_path = Path(sys.argv[1])
service = sys.argv[2]
invocation = sys.argv[3]
start_epoch = int(sys.argv[4])
paths = [Path(value) for value in sys.argv[5:] if Path(value).is_file()]

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

current_hashes = {str(path): digest(path) for path in paths}
newer = [str(path) for path in paths if path.stat().st_mtime_ns > start_epoch * 1_000_000_000]

previous = None
try:
    candidate = json.loads(witness_path.read_text(encoding="utf-8"))
    if (candidate.get("schema") == "workflow.secure-runtime-witness/v1" and
            candidate.get("service") == service and isinstance(candidate.get("files"), dict)):
        previous = candidate
except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
    pass

same_hashes = previous is not None and previous.get("files") == current_hashes
same_invocation = previous is not None and previous.get("invocation_id") == invocation
previous_certified = previous is not None and previous.get("certified") is True
content_changed_during_invocation = previous is not None and same_invocation and not same_hashes

if content_changed_during_invocation:
    certified = False
    reason = "runtime content changed during the active service invocation"
elif newer:
    # A prior certified hash set proves unchanged content. A pending witness is
    # promoted only after systemd supplies a different invocation ID.
    certified = same_hashes and (previous_certified or not same_invocation)
    reason = "unchanged startup rewrite" if certified else "runtime content has not been loaded by a later service invocation"
else:
    certified = True
    reason = "all runtime content predates the active service invocation"

payload = {
    "schema": "workflow.secure-runtime-witness/v1",
    "service": service,
    "invocation_id": invocation,
    "service_start_epoch": start_epoch,
    "certified": certified,
    "files": current_hashes,
}

try:
    if previous != payload:
        witness_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".secure-runtime-witness.", dir=witness_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, witness_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
except OSError as exc:
    print(f"error\tcould not update runtime witness: {exc}")
    raise SystemExit(0)

if certified:
    print(f"clean\t{reason}; {len(current_hashes)} file hashes certified for invocation {invocation}")
else:
    affected = newer if newer else sorted(current_hashes)
    print(f"restart\t{reason}\t" + "\t".join(affected))
PY_RUNTIME_WITNESS
      )"

      case "$RUNTIME_GENERATION_RESULT" in
        clean$'\t'*)
          echo "   ok: ${RUNTIME_GENERATION_RESULT#*$'\t'}"
          ;;
        restart$'\t'*)
          RUNTIME_RESTART_REQUIRED=1
          generation_detail="${RUNTIME_GENERATION_RESULT#*$'\t'}"
          generation_reason="${generation_detail%%$'\t'*}"
          fail "SECURE_OPENCODE_RESTART_REQUIRED: $generation_reason"
          if [[ "$generation_detail" == *$'\t'* ]]; then
            while IFS= read -r runtime_file; do
              [ -n "$runtime_file" ] && echo "      changed/newer runtime content: $runtime_file"
            done < <(printf '%s' "${generation_detail#*$'\t'}" | tr '\t' '\n')
          fi
          echo "      Fish: systemctl --user restart $SECURE_OPENCODE_SERVICE"
          ;;
        error$'\t'*)
          fail "SECURE_OPENCODE_RUNTIME_WITNESS_FAILED: ${RUNTIME_GENERATION_RESULT#*$'\t'}"
          ;;
        *)
          fail "SECURE_OPENCODE_RUNTIME_WITNESS_FAILED: unexpected result ${RUNTIME_GENERATION_RESULT:-<empty>}"
          ;;
      esac
    fi
  fi
fi

# Re-check the deployed health plugin before permitting a nested OpenCode probe.
if [ "$CAN_RUNTIME_PROBE" -eq 1 ]; then
  if [ ! -f "$HEALTH_PLUGIN_DEPLOYED" ]; then
    fail "deployed workflow-health-check.ts missing"
    CAN_RUNTIME_PROBE=0
  elif ! grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_DEPLOYED"; then
    fail "deployed workflow-health-check.ts lacks recursion guard; runtime probe skipped safely"
    CAN_RUNTIME_PROBE=0
  else
    DEPLOYED_PIN=$(read_verify_script_pin "$HEALTH_PLUGIN_DEPLOYED" 2>/dev/null || true)
    if [ "$DEPLOYED_PIN" != "$SELF_SHA" ]; then
      fail "deployed workflow-health-check.ts pins a different verifier digest; runtime probe skipped safely"
      CAN_RUNTIME_PROBE=0
    fi
  fi
fi

# --- 7. Recipe consistency ---
echo "--- 7. Recipe consistency ---"
if [ ! -f "$WORKFLOW" ]; then
  fail "WORKFLOW.md missing: $WORKFLOW"
else
  MISSING_CLASS=""
  for cls in "Tiny fix" "Small feature" "Substantial feature" "Bug investigation" "Documentation" "Global tooling change"; do
    if ! grep -qi -- "$cls" "$WORKFLOW"; then MISSING_CLASS="$MISSING_CLASS $cls"; fi
  done
  if [ -z "$MISSING_CLASS" ]; then
    echo "   ok: all six task classes present"
  else
    fail "missing task classes:$MISSING_CLASS"
  fi

  MISSING_KW=""
  for kw in "ce:brainstorm" "ce:plan" "ce:work" "ce:review" "ce:compound" "RDD" "ROUTED:" "Required Thinking Layers" "## Substantial ODD work units and review — Gentle AI 3.5.0" "## Route decision checkpoint" "basis: WORKFLOW.md"; do
    if ! grep -q -- "$kw" "$WORKFLOW"; then MISSING_KW="$MISSING_KW $kw"; fi
  done
  if [ -z "$MISSING_KW" ]; then
    echo "   ok: required-layer keywords present"
  else
    fail "missing keywords:$MISSING_KW"
  fi

  REVIEW_BUDGET_REF="$SKILLS_DIR/workflow-odd-secure/references/odd-and-review.md"
  REVIEW_DECISIONS_REF="$SKILLS_DIR/workflow-route/references/session-decisions.md"
  if grep -Fq -- '`authored_changed_lines`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`authored_patch_bytes`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`generated_or_binary_paths`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '400 authored changed lines and 100 KiB' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '200 KiB serialized per-runtime review-input budget' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`review-size-exception`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`lens_context_budget_exceeded`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`correction_context_budget_exceeded`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`review capture-result --input`, `review recover`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'separate PR/slice planning threshold' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '400 authored changed lines and 100 KiB' "$REVIEW_BUDGET_REF" 2>/dev/null && \
     grep -Fq -- '200 KiB serialized per-runtime review-input budget' "$REVIEW_BUDGET_REF" 2>/dev/null && \
     grep -Fq -- 'Gentle AI 3.4 reviewability budget' "$REVIEW_DECISIONS_REF" 2>/dev/null && \
     grep -Fq -- 'staged reviewability receipt' "$AGENTS_FILE" 2>/dev/null && \
     grep -Fq -- 'final 200 KiB serialized-input authority' "$AGENTS_FILE" 2>/dev/null; then
    echo "   ok: Gentle AI 3.4 review-input budget limits work-unit commit size"
  else
    fail "GENTLE_AI_V3_4_REVIEWABILITY_BUDGET_MISSING: staged commit receipt, local cap, native 200 KiB authority, or split/abandon route absent"
  fi

  if grep -q -- "## Orchestrator Execution Boundary" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "no direct-inline implementation route" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "explore.*researcher fallback" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "general.*sandbox worker fallback" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "## Context and SDD Artifact Backend" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "defaulting to Magic Context" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Ordinary working agents may persist durable knowledge" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "review.*document-review.*may not" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Secure Project Registration — Pre-Routing Gate" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "host_register_project" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Orchestrator Technical-Lead Contract" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "implementation contract" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "frontend-dev-premium" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Model assignments are authoritative" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Optional SDD Research and Diagnostics — Gentle AI 3.5.0" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "gentle-ai review assess --json" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "Do not leave the evidence update uncommitted" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "## Gentle AI 3.5.0 mandatory ODD delegation" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "## Skill-based route loading and long-chat resume" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "controlled pilot" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "four or more files" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "two or more non-trivial files" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "20 tool calls or five exploratory reads" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "route/trigger evidence" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "gentle-ai review mode enable|disable|status" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "tell the user in one line which" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "ODD_TASKS key=odd/{project}/{feature-name}/tasks" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "optional verify → archive" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "gentle-ai sdd-archive-compose" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Systematic v3.18.4.*workflow-guard" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Risk, Resilience, Readability, Reliability" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "status/v8" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'candidate.consumed' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'review_due_reason' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'next_transition.command' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'provider_task.agent' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'provider_task.prompt' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- "reviewer's raw JSON object" "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'grouped wave without waiting between launches' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'correction_context_budget_exceeded' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '## 4R review lane routing (mandatory)' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- '`review-<lens>` → `asi-review-<lens>`' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'Forward the provider-issued task line verbatim' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'TRANSPORT-LANE FAILURE' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 're-dispatch through the mapped `asi-review-*` lane' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'two transports cannot own one Task' "$WORKFLOW" 2>/dev/null && \
     grep -Fq -- 'Never grant review lanes to implementation workers or isolated reviewers' "$WORKFLOW" 2>/dev/null && \
     grep -q -- "eligible_untracked_inventory" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "## Per-session Sol-to-Astra escalation" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "astra-sol-upgrade.ts" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "It never writes implementation code" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "selection never edits global config or requires an OpenCode restart" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "review.acknowledge-approved" "$WORKFLOW" 2>/dev/null && \
     ! grep -q -- "frontend-dev.*=.*openai/gpt-6.1-sol" "$WORKFLOW" 2>/dev/null && \
     grep -q -- "Fish shell" "$WORKFLOW" 2>/dev/null; then
    echo "   ok: workflow encodes read-only technical leadership, Magic Context, secure project registration, and Fish-shell UX"
  else
    fail "workflow missing read-only orchestrator / delegated researcher-worker execution contract"
  fi

  if grep -q -- "Direct inline edit" "$WORKFLOW" 2>/dev/null || \
     grep -q -- "Inline implementation is" "$WORKFLOW" 2>/dev/null; then
    fail "workflow still contains obsolete inline-mutation guidance"
  else
    echo "   ok: workflow contains no obsolete direct-inline mutation route"
  fi

  if grep -R -Fq -- 'copy `provider_task.agent` unchanged as `subagent_type`' "$WORKFLOW" "$ROUTER_SKILLS_SOURCE" 2>/dev/null || \
     grep -R -Fq -- 'must never substitute for a v8 `provider_task.agent`' "$WORKFLOW" "$ROUTER_SKILLS_SOURCE" 2>/dev/null; then
    fail "GENTLE_AI_V3_4_DIRECT_PROVIDER_REVIEW_ROUTE_REAPPEARED: v8 tasks must map to asi-review-*"
  else
    echo "   ok: v8 provider review names map only to isolated asi-review relay lanes"
  fi
fi

# Gentle AI 3.4 retired RTK from its active product surface. User-owned RTK
# binaries/configuration may remain on disk, but this reviewed workflow must not
# restore an RTK integration, preset selection, or routing instruction.
if grep -R -Iiwq -- 'RTK' "$WORKFLOW" "$AGENTS_SOURCE" "$OPENCODE_CONFIG_SOURCE" "$SKILLS_DIR" 2>/dev/null; then
  fail "GENTLE_AI_V3_4_RETIRED_RTK_INTEGRATION_PRESENT: remove RTK from reviewed workflow/config sources; do not delete user-owned binaries"
else
  echo "   ok: no retired Gentle AI RTK integration in reviewed workflow sources"
fi

if [ ! -f "$REQS" ]; then
  fail "requirements document missing: $REQS"
else
  MISSING_R=""
  for r in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
    if ! grep -q -- "- R$r\." "$REQS"; then MISSING_R="$MISSING_R R$r"; fi
  done
  if [ -z "$MISSING_R" ]; then
    echo "   ok: requirements R1-R14 present"
  else
    fail "missing requirements:$MISSING_R"
  fi
fi

# Canonical AGENTS section must exactly equal the verifier-owned repair block.
if python3 - "$AGENTS_FILE" "$ROUTING_CANONICAL" <<'PY_COMPARE'
from pathlib import Path
import sys

agents = Path(sys.argv[1]).read_text(encoding="utf-8") if Path(sys.argv[1]).exists() else ""
canonical = Path(sys.argv[2]).read_text(encoding="utf-8").rstrip("\n")
start = "<!-- user:workflow-routing -->"
end = "<!-- /user:workflow-routing -->"

if agents.count(start) != 1 or agents.count(end) != 1:
    raise SystemExit(1)
a = agents.index(start)
b = agents.index(end, a) + len(end)
raise SystemExit(0 if agents[a:b] == canonical else 1)
PY_COMPARE
then
  echo "   ok: AGENTS.md routing section matches canonical verifier copy"
else
  fail "AGENTS.md routing section differs from canonical verifier copy"
fi

# The reviewed non-routing sections must also be exact and marker-safe.
if python3 - "$AGENTS_FILE" "$AGENTS_SOURCE" <<'PY_COMPARE_BOUNDED'
from pathlib import Path
import sys
active = Path(sys.argv[1]).read_text(encoding="utf-8")
source = Path(sys.argv[2]).read_text(encoding="utf-8")
for start,end in (
    ("<!-- gentle-ai:codegraph-guidance -->", "<!-- /gentle-ai:codegraph-guidance -->"),
    ("<!-- user:host-sdd-runtime-boundaries -->", "<!-- /user:host-sdd-runtime-boundaries -->"),
    ("<!-- gentle-ai:subagent-cancellation -->", "<!-- /gentle-ai:subagent-cancellation -->"),
    ("<!-- user:grep-tool-enforcement -->", "<!-- /user:grep-tool-enforcement -->"),
):
    if any(blob.count(start) != 1 or blob.count(end) != 1 for blob in (active, source)):
        raise SystemExit(1)
    def body(blob):
        a = blob.index(start)
        b = blob.index(end, a) + len(end)
        return blob[a:b]
    if body(active) != body(source):
        raise SystemExit(1)
PY_COMPARE_BOUNDED
then
  echo "   ok: CodeGraph, host SDD, cancellation and search-tool blocks match reviewed source"
else
  fail "AGENTS_BOUNDED_BLOCK_DRIFT: reviewed CodeGraph, host SDD, cancellation or search-tool block differs from active AGENTS.md"
fi

if grep -Fq -- 'prefer narrow read-only tools (ENFORCED)' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- 'built-in `grep` remains `ask`-gated' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- 'SEARCH CONTRACT: AFT=navigation' "$SKILLS_DIR/workflow-route/SKILL.md" 2>/dev/null && \
   grep -Fq -- 'all subagents have it disabled' "$WORKFLOW" 2>/dev/null && \
   grep -Fq -- 'EXTERNAL_CONTEXT_REQUIRED' "$WORKFLOW" 2>/dev/null; then
  echo "   ok: narrow search tools prioritized and grep approval preserved"
else
  fail "SEARCH_TOOL_ROUTING_DRIFT: reviewed search-tool order or grep ask boundary missing"
fi

if grep -Fq -- '.atl/rate-limit-fallback.log' "$AGENTS_FILE" 2>/dev/null && \
   ! grep -Fq -- '.git/gentle-ai/rate-limit-fallback.log' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- 'never substitute the shared OpenCode server cwd' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- 'separate from the workflow decision ledger `ROUTER-LOG.md`' "$AGENTS_FILE" 2>/dev/null; then
  echo "   ok: fallback reconciliation uses the exact session repo .atl mirror"
else
  fail "FALLBACK_REPO_LOG_ROUTING_DRIFT: canonical .atl mirror or fail-closed session routing missing"
fi

# The compact AGENTS entrypoint is checked against the canonical block
# above. The procedure it loads is checked in the reviewed skill files below.
if cat "$AGENTS_FILE" \
    "$SKILLS_DIR/workflow-route/SKILL.md" \
    "$SKILLS_DIR/workflow-route/references/session-decisions.md" \
    "$SKILLS_DIR/workflow-odd-secure/SKILL.md" \
    "$SKILLS_DIR/workflow-odd-secure/references/odd-and-review.md" \
    "$SKILLS_DIR/workflow-sdd-secure/SKILL.md" \
    "$SKILLS_DIR/workflow-sdd-secure/references/sdd-magic-adapter.md" \
    "$SKILLS_DIR/workflow-systematic/SKILL.md" \
    "$SKILLS_DIR/workflow-systematic/references/specialists.md" > "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: secure routing contract assembled from recovered skills"
else
  fail "ROUTER_SKILL_CONTRACT_UNAVAILABLE: recovered skill files cannot be read"
  : > "$ROUTING_CONTRACT"
fi

if grep -q -- "Systematic specialist routing precedence" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- 'systematic-implementer' "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: Systematic specialist routing precedence present"
else
  fail "Systematic specialist routing precedence missing"
fi

if grep -q -- "Independent sub-agent fan-out" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "same assistant message" "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: independent sub-agent fan-out contract present"
else
  fail "independent sub-agent fan-out contract missing"
fi

if grep -q -- "Prompt-free read-only inspection" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "sandbox_bash.*ask-gated" "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: prompt-free read-only inspection routing contract present"
else
  fail "prompt-free read-only inspection routing contract missing"
fi

# Gentle AI v3 renders its native ODD guidance with a specific heading, but
# sync does not guarantee that that prose appears in this global AGENTS.md.
# Our reviewed user-owned block is the effective secure adapter: it delegates
# project writes and mirrors ODD to Magic Context instead of Engram. The
# canonical marker/body is checked separately above; require the actual ODD
# protocol and route decision here, independent of vendor heading placement.
if grep -Fq -- '## Secure workflow router (MANDATORY)' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- 'skill({name:"workflow-route"})' "$AGENTS_FILE" 2>/dev/null && \
   grep -Fq -- '### Gentle AI 3.5.0 mandatory ODD delegation (SECURE)' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'four or more files' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'two or more non-trivial files' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- '20 tool calls or five exploratory reads' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'route/trigger evidence' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- '### Secure ODD protocol — Gentle AI 3.5.0 (MANDATORY)' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'Every request follows **Authorize → Explore → Resolve uncertainty → Classify → Track → Implement → Close**' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'basis: WORKFLOW.md' "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: authoritative secure ODD route and WORKFLOW.md decision are present"
  if ! grep -Fq -- 'ODD protocol (MANDATORY, in this order, on every request)' "$ROUTING_CONTRACT" 2>/dev/null; then
    echo "   info: upstream managed ODD prose absent from global AGENTS.md; secure user-owned v3 route is effective"
  fi
else
  fail "GENTLE_AI_V3_SECURE_ODD_ROUTING_MISSING: reviewed user-owned ODD block or WORKFLOW.md route decision missing from active AGENTS.md; run --recover-config-only"
fi

if grep -q -- "Sandbox-only project mutation" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "SDD artifact writers use sandbox tools" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "gentle-orchestrator.*strictly read-only coordinator" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "no direct-inline implementation path" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "explore.*read-only researcher fallback" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "general.*sandbox worker fallback" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Mandatory Magic Context memory/context" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "SDD_ARTIFACT key=<stable-key>" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Ordinary working agents may save memories" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Isolated evaluation actors remain memory-write denied" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Secure project registration (pre-routing gate)" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "host_register_project.*single approved model-facing registration route" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Orchestrator technical-lead responsibility" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "implementation contract" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -qi -- "read-only.*authority.*reasoning" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "frontend-dev-premium" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "two substantive visual iteration rounds" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Gentle AI 3.5.0 optional SDD research" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "gentle-ai review assess --json" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "ODD_TASKS key=odd/{project}/{feature-name}/tasks" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- "basis: WORKFLOW.md" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- "gentle-ai review mode enable|disable|status" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- "tell the user in one line which" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- "--base-ref <last reviewed boundary> --committed-only --json" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "optional verify → archive" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "gentle-ai sdd-archive-compose" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Systematic v3.18.4.*workflow-guard" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Risk, Resilience, Readability, Reliability" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "status/v8" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'candidate.consumed' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'review_due_reason' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'next_transition.command' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'provider_task.agent' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'provider_task.prompt' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- "reviewer's raw JSON object" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'grouped wave without waiting between launches' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'correction_context_budget_exceeded' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- '4R review lane routing (mandatory)' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'Forward the provider-issued task line verbatim' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'TRANSPORT-LANE FAILURE' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 're-dispatch through the mapped `asi-review-*` lane' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'two transports cannot own one Task' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -Fq -- 'never grant review lanes to implementation workers or isolated reviewers' "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "eligible_untracked_inventory" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Coding Model Decision (MANDATORY)" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Sol-to-Astra upgrade decision (MANDATORY)" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Use Astra upgrade (Recommended)" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Astra is never an implementation agent" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Selection must not edit .*systematic.jsonc" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "review.acknowledge-approved" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "Fish shell" "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: sandbox/read-only/Magic-Context + technical-lead + secure-project-registration + Fish-shell contract present"
else
  fail "sandbox-only mutation/read-only orchestrator/researcher-worker/Magic Context contract missing"
fi

if grep -q -- "<!-- gentle-ai:engram-protocol -->" "$AGENTS_FILE" 2>/dev/null; then
  fail "LEGACY_ENGRAM_PROTOCOL_REAPPEARED: user workflow uses mandatory Magic Context instead"
else
  echo "   ok: no legacy mandatory Engram protocol block"
fi

# --- 8. systematic.jsonc inventory / overlay integrity ---
echo "--- 8. Systematic config inventory ---"
if [ -z "$ACTIVE_ROOT" ] || [ ! -d "$ACTIVE_AGENTS" ]; then
  fail "active Systematic agents directory unavailable; config inventory check skipped"
  STATIC_SYSTEMATIC_OK=0
elif [ ! -f "$SYSTEMATIC_CONFIG" ]; then
  fail "Systematic config missing: $SYSTEMATIC_CONFIG"
  STATIC_SYSTEMATIC_OK=0
else
  JS_RUNTIME=""
  if command_exists node; then
    JS_RUNTIME="node"
  elif command_exists bun; then
    JS_RUNTIME="bun"
  else
    fail "neither node nor bun is available for JSONC validation"
    STATIC_SYSTEMATIC_OK=0
  fi

  if [ -n "$JS_RUNTIME" ]; then
    if SYSTEMATIC_NODE_MODULES="$SYSTEMATIC_NODE_MODULES" "$JS_RUNTIME" "$SYSTEMATIC_CHECKER" "$SYSTEMATIC_CONFIG" "$ACTIVE_AGENTS"; then
      :
    else
      fail "systematic.jsonc inventory/overlay validation failed"
      STATIC_SYSTEMATIC_OK=0
    fi
  fi
fi

# --- 9. Runtime agent registration/models/tools + GGA fallback policy ---
echo "--- 9. OpenCode runtime agents + GGA fallback policy ---"
if [ "$STATIC_SYSTEMATIC_OK" -ne 1 ]; then
  fail "runtime agent checks skipped because static Systematic config validation failed"
elif [ "$CAN_RUNTIME_PROBE" -ne 1 ]; then
  fail "runtime agent checks skipped because the health-plugin recursion guard/digest binding is not ready"
elif ! command_exists opencode; then
  fail "opencode executable not found; runtime agent checks skipped"
else
  LIST_STATUS=0
  (
    cd "$AGENT_PROBE_CWD" || exit 1
    WORKFLOW_HEALTH_CHECK_PROBE=1 \
    SYSTEMATIC_ROUTING_GUARD_MODE=off \
    timeout 45s opencode agent list >"$AGENT_LIST_OUT" 2>"$AGENT_LIST_STDERR"
  ) || LIST_STATUS=$?

  if [ "$LIST_STATUS" -ne 0 ]; then
    fail "opencode agent list probe failed (exit $LIST_STATUS)"
    if [ "$LIST_STATUS" -eq 124 ]; then
      echo "   info: agent registration exceeded the 45-second cold-start budget; inspect plugin-load errors and retry from a warm cache"
    fi
    tail -12 "$AGENT_LIST_STDERR" 2>/dev/null | sed 's/^/      /'
  else
    # Every agent the embedded runtime checker reads via readDebug must be probed
    # here: SDD writers (sdd-apply, sdd-explore), github-scoped agents, and the
    # Systematic baseline reviewers. A missing probe fails section 9.
    PROBE_NAMES=(
      gentle-orchestrator general explore
      frontend-dev frontend-dev-premium frontend-dev-premium-astra
      jd-judge-a jd-judge-a-astra jd-judge-b sdd-research
      sdd-design sdd-design-astra sdd-spec sdd-spec-astra sdd-verify sdd-verify-astra sdd-apply sdd-explore
      review-risk review-readability review-reliability review-resilience review-refuter review-validator
      asi-review-risk asi-review-resilience asi-review-readability asi-review-reliability asi-review-refuter asi-review-validator
      review-risk-astra
      correctness-reviewer testing-reviewer project-standards-reviewer repo-research-analyst adversarial-document-reviewer
      adversarial-document-reviewer-astra adversarial-reviewer adversarial-reviewer-astra
      security-reviewer security-reviewer-astra security-lens-reviewer security-lens-reviewer-astra
      api-contract-reviewer architecture-strategist reliability-reviewer
      data-migrations-reviewer deployment-verification-agent feasibility-reviewer design-iterator
    )
    while IFS= read -r listed; do
      # Probe every agent the runtime registers, so the probe set cannot drift
      # from the agents the runtime checker reads via readDebug.
      if [[ "$listed" =~ ^([^[:space:]]+)[[:space:]]+\((primary|subagent|all)\)$ ]]; then
        PROBE_NAMES+=("${BASH_REMATCH[1]}")
      fi
    done < "$AGENT_LIST_OUT"
    while IFS= read -r md; do
      [ -f "$md" ] || continue
      base=$(basename "$md" .md)
      [ "${base,,}" = "readme" ] && continue
      tools_line=$(sed -nE 's/^tools:[[:space:]]*(.*)$/\1/ip' "$md" | head -1)
      if printf '%s' "$tools_line" | grep -qiE '(^|,)[[:space:]]*(Edit|Write)([[:space:]]*,|$)'; then
        PROBE_NAMES+=("$base")
      fi
    done < <(find "$ACTIVE_AGENTS" -mindepth 1 -maxdepth 2 -type f -name '*.md' -print 2>/dev/null)

    UNIQUE_PROBES=()
    declare -A SEEN_PROBE=()
    for name in "${PROBE_NAMES[@]}"; do
      if [ -z "${SEEN_PROBE[$name]+x}" ]; then
        UNIQUE_PROBES+=("$name")
        SEEN_PROBE[$name]=1
      fi
    done

    MAX_PARALLEL=4
    RUNNING=0
    # The embedded runtime checker reads agents by name. Literal readDebug(...)
    # targets plus its agent-name arrays are extracted here and must all be in
    # the probe set. Runtime-derived targets (astra aliases, Systematic
    # inventory mutators) are covered because every registered agent is probed
    # above. The guard fails closed if the extraction itself goes stale.
    CHECKER_AGENT_REFS="$(
      {
        grep -oE 'readDebug\("[^"]+"\)' "$RUNTIME_AGENT_CHECKER" 2>/dev/null
        grep -oE '(githubReaderNames|githubBlockedNames|gga)=\[[^]]*\]' "$RUNTIME_AGENT_CHECKER" 2>/dev/null
      } | grep -oE '"[a-z][a-z0-9-]*"' | tr -d '"' | sort -u
    )"
    if [ -z "$CHECKER_AGENT_REFS" ]; then
      fail "PROBE_LIST_AGENT_EXTRACTION_EMPTY: no checker agent references found in $RUNTIME_AGENT_CHECKER"
    fi
    while IFS= read -r checker_agent; do
      [ -n "$checker_agent" ] || continue
      if [ -z "${SEEN_PROBE[$checker_agent]+x}" ]; then
        fail "PROBE_LIST_MISSING_CHECKER_AGENT: ${checker_agent} is read by the runtime checker but never probed"
      fi
    done <<< "$CHECKER_AGENT_REFS"
    for name in "${UNIQUE_PROBES[@]}"; do
      (
        cd "$AGENT_PROBE_CWD" || exit 1
        status=0
        WORKFLOW_HEALTH_CHECK_PROBE=1 \
        SYSTEMATIC_ROUTING_GUARD_MODE=off \
        timeout 15s opencode debug agent "$name" \
          >"$DEBUG_AGENT_DIR/$name.json" 2>"$DEBUG_AGENT_DIR/$name.stderr" || status=$?
        printf '%s\n' "$status" >"$DEBUG_AGENT_DIR/$name.status"
      ) &
      RUNNING=$((RUNNING + 1))
      if [ "$RUNNING" -ge "$MAX_PARALLEL" ]; then
        wait -n || true
        RUNNING=$((RUNNING - 1))
      fi
    done
    wait || true

    PROBE_FAILURE=0
    for name in "${UNIQUE_PROBES[@]}"; do
      status=$(cat "$DEBUG_AGENT_DIR/$name.status" 2>/dev/null || printf 'missing')
      if [ "$status" != "0" ]; then
        echo "   !! opencode debug agent $name failed (status $status)"
        tail -8 "$DEBUG_AGENT_DIR/$name.stderr" 2>/dev/null | sed 's/^/      /'
        PROBE_FAILURE=1
      elif grep -qiE 'level=ERROR|failed to load plugin' "$DEBUG_AGENT_DIR/$name.stderr" 2>/dev/null; then
        echo "   !! opencode debug agent $name reported plugin-load error(s)"
        grep -iE 'level=ERROR|failed to load plugin' "$DEBUG_AGENT_DIR/$name.stderr" | tail -6 | sed 's/^/      /'
        PROBE_FAILURE=1
      fi
    done

    if [ "$PROBE_FAILURE" -ne 0 ]; then
      fail "one or more per-agent runtime probes failed"
    elif SYSTEMATIC_NODE_MODULES="$SYSTEMATIC_NODE_MODULES" "$JS_RUNTIME" "$RUNTIME_AGENT_CHECKER" \
      "$SYSTEMATIC_CONFIG" "$ACTIVE_AGENTS" "$AGENT_LIST_OUT" "$DEBUG_AGENT_DIR" "$OPENCODE_CONFIG_FILE" \
      "$FALLBACK_POLICY_SOURCE"; then
      echo "   ok: runtime agent registration/model/tool and GGA fallback checks passed"
    else
      fail "OpenCode runtime agent registration/model/tool or GGA fallback policy check failed"
    fi
  fi
fi

# --- 9a. Active secure-service Systematic agents ---
echo "--- 9a. Secure OpenCode Systematic agent registration ---"
if [ "$RUNTIME_RESTART_REQUIRED" -eq 1 ]; then
  echo "   skipped: configuration was repaired after service start; restart and rerun to inspect live agents"
elif ! command_exists curl; then
  fail "SYSTEMATIC_SERVICE_PROBE_UNAVAILABLE: curl missing"
elif ! curl --fail --silent --show-error --max-time 12 \
    --header "x-opencode-directory: $WORKSPACE" \
    http://127.0.0.1:4096/agent >"$TMP_DIR/secure-service-agents.json" 2>"$TMP_DIR/service-agents-curl.stderr"; then
  fail "SYSTEMATIC_SERVICE_AGENTS_UNAVAILABLE: could not read the secure service /agent catalog"
elif ! "${JS_RUNTIME:-node}" - "$TMP_DIR/secure-service-agents.json" <<'EOF_SYSTEMATIC_SERVICE'
const fs=require("fs")
try {
  const agents=JSON.parse(fs.readFileSync(process.argv[2],"utf8"))
  if (!Array.isArray(agents)) process.exit(1)
  const names=new Set(agents.map((agent)=>agent?.name))
  const missing=["repo-research-analyst","correctness-reviewer","testing-reviewer"].filter((name)=>!names.has(name))
  if (missing.length) { console.error(`   !! SYSTEMATIC_SERVICE_AGENTS_MISSING: ${missing.join(", ")}`); process.exit(1) }
} catch { process.exit(1) }
EOF_SYSTEMATIC_SERVICE
then
  fail "secure service does not expose the expected Systematic agents; inspect plugin-load logs"
else
  echo "   ok: secure service exposes the expected Systematic research and review agents"
fi

# --- 9b. Active secure-service GitHub MCP connection ---
echo "--- 9b. Secure OpenCode public GitHub MCP ---"
if [ "$RUNTIME_RESTART_REQUIRED" -eq 1 ]; then
  echo "   skipped: configuration was repaired after service start; restart and rerun to inspect live GitHub MCP"
else
GITHUB_MCP_STATUS="$TMP_DIR/github-ro-mcp-status.json"
GITHUB_MCP_CONFIG="$TMP_DIR/github-ro-effective-config.json"
GITHUB_MCP_CONNECTED=0
if command_exists curl; then
  for attempt in 1 2 3; do
    if curl --fail --silent --show-error --max-time 12 \
        --header "x-opencode-directory: $WORKSPACE" \
        http://127.0.0.1:4096/mcp >"$GITHUB_MCP_STATUS" 2>"$TMP_DIR/github-ro-mcp-curl.stderr" && \
        "${JS_RUNTIME:-node}" -e 'try {const s=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")); process.exit(s.github_ro?.status==="connected"?0:1)} catch {process.exit(1)}' "$GITHUB_MCP_STATUS"; then
      GITHUB_MCP_CONNECTED=1
      break
    fi
    [ "$attempt" -eq 3 ] || sleep 2
  done
fi
if ! command_exists curl; then
  fail "GITHUB_RO_STATUS_PROBE_UNAVAILABLE: curl missing"
elif [ "$GITHUB_MCP_CONNECTED" -ne 1 ]; then
  fail "GITHUB_RO_NOT_CONNECTED: secure OpenCode /mcp did not connect after three bounded attempts; check token and Nono egress"
elif ! curl --fail --silent --show-error --max-time 12 \
    --header "x-opencode-directory: $WORKSPACE" \
    http://127.0.0.1:4096/config >"$GITHUB_MCP_CONFIG" 2>"$TMP_DIR/github-ro-config-curl.stderr"; then
  fail "GITHUB_RO_SERVICE_CONFIG_UNAVAILABLE: could not inspect secure OpenCode effective configuration"
elif ! "${JS_RUNTIME:-node}" - "$GITHUB_MCP_STATUS" "$GITHUB_MCP_CONFIG" <<'EOF_GITHUB_MCP_STATUS'
const fs=require("fs")
try {
  const response=JSON.parse(fs.readFileSync(process.argv[2],"utf8"))
  if (response?.github_ro?.status!=="connected") process.exit(1)
  const config=JSON.parse(fs.readFileSync(process.argv[3],"utf8"))
  if (config.tools?.["github_ro_*"]!==false || config.mcp?.github_ro?.url!=="https://api.githubcopilot.com/mcp/readonly" || config.mcp?.github_ro?.headers?.["X-MCP-Readonly"]!=="true") process.exit(1)
  const readers=new Set(["gentle-orchestrator","explore","sdd-research"])
  for (const name of readers) {
    if (config.agent?.[name]?.tools?.["github_ro_*"]!==true ||
        config.agent[name].permission?.["github_ro_*"]!=="allow") process.exit(1)
  }
  for (const [name,agent] of Object.entries(config.agent??{})) {
    if (!readers.has(name) && agent?.tools?.["github_ro_*"]===true) process.exit(1)
  }
} catch { process.exit(1) }
EOF_GITHUB_MCP_STATUS
then
  fail "GITHUB_RO_RUNTIME_INACTIVE_OR_UNSCOPED: secure service must connect github_ro and grant only three read-only researchers"
else
  echo "   ok: secure OpenCode github_ro MCP connected with three scoped read-only research agents"
fi
fi

# --- 10. Optional behavioural parallel-dispatch probe ---
echo "--- 10. Behavioural parallel dispatch ---"
if [ "$RUN_BEHAVIOURAL" -ne 1 ]; then
  echo "   skipped: run with --behavioral after workflow/OpenCode permission changes"
elif [ "$FAIL" -ne 0 ]; then
  fail "behavioural fan-out probe skipped because deterministic checks already failed"
elif ! command_exists opencode; then
  fail "opencode executable not found; behavioural fan-out probe skipped"
else
  PARALLEL_PROMPT='WORKFLOW HEALTH PROBE. Do not answer inline and do not inspect the repository. In your FIRST assistant tool-use step, emit exactly TWO native Task calls in the SAME assistant message before waiting for either result. Call subagent_type="explore" with prompt "Return exactly PARALLEL_SENTINEL_A and do not call any tools." Call subagent_type="general" with prompt "Return exactly PARALLEL_SENTINEL_B and do not call any tools." These tasks are independent. Do not call any other tool. After both Task results return, reply exactly PARALLEL_FANOUT_DONE.'

  PARALLEL_STATUS=0
  if command_exists timeout; then
    (
      cd "$PROBE_CWD" || exit 1
      WORKFLOW_HEALTH_CHECK_PROBE=1 \
      timeout 180s opencode run --format json --agent gentle-orchestrator "$PARALLEL_PROMPT" \
        >"$PARALLEL_EVENTS" 2>"$PARALLEL_STDERR"
    ) || PARALLEL_STATUS=$?
  else
    (
      cd "$PROBE_CWD" || exit 1
      WORKFLOW_HEALTH_CHECK_PROBE=1 \
      opencode run --format json --agent gentle-orchestrator "$PARALLEL_PROMPT" \
        >"$PARALLEL_EVENTS" 2>"$PARALLEL_STDERR"
    ) || PARALLEL_STATUS=$?
  fi

  if [ "$PARALLEL_STATUS" -ne 0 ]; then
    fail "behavioural fan-out probe failed (exit $PARALLEL_STATUS)"
    if [ -s "$PARALLEL_STDERR" ]; then
      echo "      probe stderr (tail):"
      tail -16 "$PARALLEL_STDERR" | sed 's/^/      /'
    fi
  elif python3 "$PARALLEL_CHECKER" "$PARALLEL_EVENTS"; then
    echo "   ok: native Task behavioural probe passed"
  else
    fail "behavioural parallel-dispatch contract failed"
    echo "      retained diagnostic preview:"
    grep -E '"type":"(tool_use|text|step_finish)"|"tool":"task"' "$PARALLEL_EVENTS" 2>/dev/null | tail -20 | sed 's/^/      /'
    if [ -s "$PARALLEL_STDERR" ]; then
      echo "      probe stderr (tail):"
      tail -12 "$PARALLEL_STDERR" | sed 's/^/      /'
    fi
  fi
fi

# A second, read-only behavioural probe checks that the ODD authorization
# boundary holds in an actual orchestrator turn. It runs only under the paid,
# user-invoked --behavioral flag, in the same neutral temporary project.
echo "--- 10a. Behavioural ODD read-only authorization ---"
if [ "$RUN_BEHAVIOURAL" -ne 1 ]; then
  echo "   skipped: run with --behavioral to test the ODD route"
elif [ "$FAIL" -ne 0 ]; then
  fail "ODD behavioural probe skipped because earlier health checks failed"
else
  ODD_PROMPT='WORKFLOW HEALTH READ-ONLY PROBE. This is a planning-only question. Briefly explain how you would approach adding a single text label to a hypothetical application. Do not implement, write or modify files, register a project, start review, or create task records. No source repository is provided.'
  ODD_EVENTS="$TMP_DIR/odd-readonly-events.jsonl"
  ODD_STDERR="$TMP_DIR/odd-readonly.stderr"
  ODD_STATUS=0
  (
    cd "$PROBE_CWD" || exit 1
    WORKFLOW_HEALTH_CHECK_PROBE=1 timeout 120s opencode run --format json --agent gentle-orchestrator "$ODD_PROMPT" >"$ODD_EVENTS" 2>"$ODD_STDERR"
  ) || ODD_STATUS=$?
  if [ "$ODD_STATUS" -ne 0 ]; then
    fail "ODD_READ_ONLY_PROBE_FAILED: opencode run exited $ODD_STATUS"
    tail -10 "$ODD_STDERR" 2>/dev/null | sed 's/^/      /'
  elif python3 - "$ODD_EVENTS" "$PROBE_CWD" <<'PY_ODD_READONLY'
import json
from pathlib import Path
import sys

events = Path(sys.argv[1])
root = Path(sys.argv[2])
loaded_router = False
for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    part = event.get("part")
    if not isinstance(part, dict):
        continue
    tool = part.get("tool")
    state = part.get("state") or {}
    if not isinstance(state, dict):
        state = {}
    launch = state.get("input") or {}
    if not isinstance(launch, dict):
        launch = {}
    if tool == "skill" and launch.get("name") == "workflow-route":
        loaded_router = True
    if tool in {"sandbox_write","sandbox_edit","sandbox_apply_patch","sandbox_bash","sandbox_apply","write","edit","bash","host_plan_append","host_review_start","host_register_project"} or (tool == "task" and launch.get("subagent_type") not in {"explore"}):
        print(f"   !! ODD_READ_ONLY_MUTATION_OR_WRITER: tool={tool} agent={launch.get('subagent_type')}")
        raise SystemExit(1)
if not loaded_router:
    print("   !! ODD_ROUTER_SKILL_NOT_LOADED: expected native skill(workflow-route) call")
    raise SystemExit(1)
if (root / "odd" / "tasks").exists():
    print("   !! ODD_READ_ONLY_TRACKER_CREATED: odd/tasks exists in probe")
    raise SystemExit(1)
print("   ok: planning-only request launched no writer and created no ODD tracker")
PY_ODD_READONLY
  then
    :
  else
    fail "ODD_READ_ONLY_AUTHORIZATION_FAILED"
  fi
fi

echo "--- 11. Cache-prune safety approval ---"
if [ "$FAIL" -ne 0 ]; then
  echo "   skipped: workflow health has failures; no cleanup approval issued"
elif [ "$AUTO_REPAIRED" -ne 0 ]; then
  echo "   skipped: configuration was repaired; rerun after restart before cleanup is approved"
elif write_cache_prune_approval; then
  echo "   ok: issued a config-bound cache-prune approval for scheduled maintenance"
else
  fail "CACHE_PRUNE_APPROVAL_WRITE_FAILED: $CACHE_PRUNE_APPROVAL"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  if [ "$AUTO_REPAIRED" -eq 1 ]; then
    echo "== All checks passed — workflow setup intact (self-repairs applied) =="
  else
    echo "== All checks passed — workflow setup intact =="
  fi
else
  echo "${C_BOLD_RED}== Some checks failed — see the summary below ==${C_RESET}"
  echo ""
  echo "${C_BOLD_RED}Failed checks (${#FAIL_MESSAGES[@]}):${C_RESET}"
  idx=0
  for message in "${FAIL_MESSAGES[@]}"; do
    idx=$((idx + 1))
    printf '   %s. %s\n' "$idx" "$message"
  done
  exit 1
fi
