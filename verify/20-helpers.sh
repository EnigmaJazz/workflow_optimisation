fail() {
  FAIL_MESSAGES+=("$*")
  echo "   ${C_RED}!! $*${C_RESET}"
  FAIL=1
}

check_embedded_orchestrator_prompt() {
  local output status
  output=$(python3 - "$WORKSPACE" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
assembler = root / "global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py"
config_path = root / "global-config/opencode.json"
try:
    result = subprocess.run([sys.executable, str(assembler)], cwd=root, capture_output=True, timeout=30)
except subprocess.TimeoutExpired:
    print("ORCHESTRATOR_PROMPT_ASSEMBLER_TIMEOUT: assembler exceeded 30 seconds")
    raise SystemExit(4)
if result.returncode != 0:
    print("ORCHESTRATOR_PROMPT_ASSEMBLER_FAILED: " + result.stderr.decode("utf-8", errors="replace").strip())
    raise SystemExit(1)
try:
    embedded = json.loads(config_path.read_text(encoding="utf-8"))["agent"]["gentle-orchestrator"]["prompt"]
except (OSError, ValueError, KeyError, TypeError) as error:
    print("ORCHESTRATOR_PROMPT_CONFIG_INVALID: " + str(error))
    raise SystemExit(2)
assembled = result.stdout.decode("utf-8")
def matches(prompt):
    return prompt == assembled
if not matches(assembled):
    print("ORCHESTRATOR_PROMPT_EQUALITY_CONTROL_FAILED: identical prompts did not match")
    raise SystemExit(3)
mutated = assembled + "\nCONTROL: mutated embedded prompt\n"
if matches(mutated):
    print("ORCHESTRATOR_PROMPT_INEQUALITY_CONTROL_FAILED: mutated prompt matched")
    raise SystemExit(3)
if not matches(embedded):
    print("ORCHESTRATOR_PROMPT_ASSEMBLER_DRIFT: embedded prompt differs from assembler output")
    raise SystemExit(5)
PY
  2>&1)
  status=$?
  if [ "$status" -eq 0 ]; then
    echo "   ok: embedded orchestrator prompt matches assembler output; equality controls pass"
  else
    fail "$output"
  fi
}
if [ "$RECOVERY_ONLY" -eq 0 ] && [ "${WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY:-0}" != "1" ]; then
  check_embedded_orchestrator_prompt
fi

plugin_check_failure() {
  local failure_policy="$1"
  shift
  if [ "$failure_policy" = advisory ]; then
    echo "   !! advisory: $*"
  else
    fail "$@"
  fi
}

check_plugin_loads() {
  local plugin_dir="${1:-$PLUGINS_DIR}" mode="${2:-factory}" failure_policy="${3:-fatal}"
  local scratch_dir plugin output status checked=0
  plugin_dir=$(cd "$plugin_dir" 2>/dev/null && pwd) || {
    plugin_check_failure "$failure_policy" "deployed plugin directory is unavailable: $plugin_dir"
    return
  }
  if ! command_exists bun || ! command_exists timeout; then
    plugin_check_failure "$failure_policy" "cannot load-check deployed plugins: bun and timeout are required"
    return
  fi
  scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/workflow-plugin-load.XXXXXX") || {
    plugin_check_failure "$failure_policy" "cannot create scratch directory for deployed plugin load checks"
    return
  }
  # Keep the tracked-plugin hook-key allowlist aligned with the installed OpenCode plugin API version; it must track that version.
  for plugin in "$plugin_dir"/*.ts "$plugin_dir"/*.js; do
    [ -f "$plugin" ] || continue
    case "${plugin##*/}" in
      *.bak*|*.disabled) continue ;;
    esac
    checked=$((checked + 1))
    output=$(cd "$scratch_dir" && SYSTEMATIC_ROUTING_GUARD_STATE_ROOT="$scratch_dir" WORKFLOW_HEALTH_CHECK_PROBE=1 PLUGIN_LOAD_CHECK_PATH="$plugin" PLUGIN_LOAD_CHECK_MODE="$mode" timeout 8s bun --no-install -e 'const path = process.env.PLUGIN_LOAD_CHECK_PATH; const knownHooks = new Set(["event", "chat.message", "chat.params", "chat.headers", "permission.ask", "shell.env", "tool.definition", "tool", "tool.execute.before", "tool.execute.after", "auth", "provider", "command.execute.before", "config", "dispose", "experimental.chat.messages.transform", "experimental.session.compacting", "experimental.compaction.autocontinue", "experimental.chat.system.transform", "experimental.text.complete"]); const trackedNames = new Set(["astra-sol-upgrade.ts", "systematic-routing-guard.ts", "workflow-health-check.ts"]); const tracked = trackedNames.has(path.split("/").pop()); let m; try { m = await import(path) } catch (error) { console.error("plugin import failed: " + String(error)); process.exit(3) } const dual = m.default && typeof m.default === "object" ? m.default : null; const functionExports = Object.entries(m).filter(([, value]) => typeof value === "function").map(([name]) => name); const namedFactories = Object.entries(m).filter(([name, value]) => /Plugin/.test(name) && typeof value === "function"); const factoryNames = [...(typeof m.default === "function" ? ["default"] : []), ...namedFactories.map(([name]) => name)]; const unexpectedFunctionExports = functionExports.filter(name => !factoryNames.includes(name)); const dualFailure = !dual ? null : (typeof dual.id !== "string" || !dual.id) ? "dual-mode default export needs a string id" : (typeof dual.setup !== "function" || typeof dual.server !== "function") ? "dual-mode default export must have both setup and server functions" : namedFactories.length ? "dual-mode default export must not be combined with named Plugin factory exports" : null; const exportFailure = dualFailure ? dualFailure : unexpectedFunctionExports.length ? "unexpected function-valued plugin exports: " + unexpectedFunctionExports.join(", ") : namedFactories.length > 1 ? "ambiguous named Plugin factory exports: " + namedFactories.map(([name]) => name).join(", ") : null; if (exportFailure) { if (tracked) { console.error(exportFailure + ": " + path); process.exit(6) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + exportFailure + ": " + path) } if (process.env.PLUGIN_LOAD_CHECK_MODE === "import") { console.log("plugin import succeeded"); process.exit(0) } const factory = typeof m.default === "function" ? ["default", m.default] : (dual && typeof dual.server === "function") ? ["default.server", dual.server.bind(dual)] : namedFactories.length === 1 ? namedFactories[0] : null; if (!factory) { const reason = namedFactories.length > 1 ? "ambiguous named Plugin factory exports: " + namedFactories.map(([name]) => name).join(", ") : "no default or named Plugin factory export"; if (tracked) { console.error(reason + ": " + path); process.exit(4) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + reason + ": " + path); process.exit(0) } try { const result = await factory[1]({}); const hooks = result && typeof result === "object" ? [...knownHooks].filter(key => Object.prototype.hasOwnProperty.call(result, key)) : []; if (!hooks.length) { const message = "factory returned no recognized hooks: " + factory[0]; if (tracked) { console.error(message); process.exit(5) } console.log("PLUGIN_LOAD_REPORT_ONLY: " + message + ": " + path); process.exit(0) } console.log("plugin factory invoked: " + factory[0] + "; recognized hooks: " + hooks.join(", ")) } catch (error) { console.log("PLUGIN_LOAD_WARNING: factory threw (non-fatal): " + factory[0] + ": " + String(error)) }' 2>&1)
    status=$?
    if [ "$status" -eq 0 ]; then
      case "$output" in
        PLUGIN_LOAD_WARNING:*|PLUGIN_LOAD_REPORT_ONLY:*) echo "   !! ${plugin##*/}: $output" ;;
        *) echo "   OK plugin ${mode}: ${plugin##*/}${output:+ — $output}" ;;
      esac
      continue
    fi
    if [ "$status" -eq 124 ]; then
      plugin_check_failure "$failure_policy" "plugin load timed out: $plugin"
      continue
    fi
    plugin_check_failure "$failure_policy" "plugin load check failed: $plugin (exit $status): $output"
  done
  rm -rf "$scratch_dir"
  if [ "$checked" -eq 0 ]; then
    plugin_check_failure "$failure_policy" "plugin load check found no plugin files under $plugin_dir"
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
  # These pre-mirror bytes may be stale but repairable, so this import probe is advisory only.
  check_plugin_loads "${WORKFLOW_VERIFY_PLUGIN_LOAD_DIR:-$PLUGINS_DIR}" "$plugin_mode" advisory
fi
if [ "${WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY:-0}" = "1" ]; then
  [ "$FAIL" -eq 0 ] && exit 0
  exit 1
fi

