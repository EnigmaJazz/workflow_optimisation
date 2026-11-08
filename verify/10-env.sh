
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
SKILLS_DIR="${WORKFLOW_VERIFY_SKILLS_DIR:-$OPENCODE_CONFIG_DIR/skills}"
COMMANDS_DIR="${WORKFLOW_VERIFY_COMMANDS_DIR:-$OPENCODE_CONFIG_DIR/commands}"
ROUTER_SKILLS_SOURCE="$WORKSPACE/global-config/skills"
PLUGINS_DIR="$OPENCODE_CONFIG_DIR/plugins"
OPENCODE_CACHE_DIR="${WORKFLOW_VERIFY_OPENCODE_CACHE_DIR:-/home/james/.cache/opencode}"
PACKAGES_DIR="$OPENCODE_CACHE_DIR/packages/@fro.bot"
MAGIC_PACKAGES_DIR="$OPENCODE_CACHE_DIR/packages/@cortexkit"
AGENTS_FILE="${WORKFLOW_VERIFY_AGENTS_FILE:-$OPENCODE_CONFIG_DIR/AGENTS.md}"
RUNTIME_CONFIG_FILE="${WORKFLOW_VERIFY_RUNTIME_CONFIG_FILE:-$OPENCODE_CONFIG_FILE}"
CLI_CONFIG_FILE="${WORKFLOW_VERIFY_CLI_CONFIG_FILE:-$OPENCODE_CONFIG_DIR/cli.json}"
RECOVERY_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ).$$"
SYSTEMATIC_CONFIG="$OPENCODE_CONFIG_DIR/systematic.jsonc"
FALLBACK_POLICY_DEPLOYED="$OPENCODE_CONFIG_DIR/rate-limit-fallback.json"

derive_workspace_paths() {
  ROUTER_SKILLS_SOURCE="${WORKFLOW_VERIFY_ROUTER_SKILLS_SOURCE:-$WORKSPACE/global-config/skills}"
  OPENCODE_CONFIG_SOURCE="${WORKFLOW_VERIFY_OPENCODE_CONFIG_SOURCE:-$WORKSPACE/global-config/opencode.json}"
  TUI_CONFIG_SOURCE="${WORKFLOW_VERIFY_TUI_CONFIG_SOURCE:-$WORKSPACE/global-config/tui.json}"
  CLI_CONFIG_SOURCE="${WORKFLOW_VERIFY_CLI_CONFIG_SOURCE:-$WORKSPACE/global-config/cli.json}"
  AGENTS_SOURCE="${WORKFLOW_VERIFY_AGENTS_SOURCE:-$WORKSPACE/global-config/AGENTS.md}"
  RECOVERY_BACKUP_ROOT="${WORKFLOW_VERIFY_RECOVERY_BACKUP_ROOT:-$WORKSPACE/backups/workflow-recovery}"
  SYSTEMATIC_CONFIG_SOURCE="${WORKFLOW_VERIFY_SYSTEMATIC_CONFIG_SOURCE:-$WORKSPACE/global-config/systematic.jsonc}"
  FALLBACK_POLICY_SOURCE="${WORKFLOW_VERIFY_FALLBACK_POLICY_SOURCE:-$WORKSPACE/global-config/rate-limit-fallback.json}"
  HEALTH_PLUGIN_SOURCE="${WORKFLOW_VERIFY_HEALTH_PLUGIN_SOURCE:-$WORKSPACE/global-config/plugins/workflow-health-check.ts}"
  ROUTING_GUARD_SOURCE="${WORKFLOW_VERIFY_ROUTING_GUARD_SOURCE:-$WORKSPACE/global-config/plugins/systematic-routing-guard.ts}"
  ASTRA_PLUGIN_SOURCE="${WORKFLOW_VERIFY_ASTRA_PLUGIN_SOURCE:-$WORKSPACE/global-config/plugins/astra-sol-upgrade.ts}"
  PLUGIN_CACHE_INTEGRITY_HELPER="${WORKFLOW_VERIFY_PLUGIN_CACHE_INTEGRITY_HELPER:-$WORKSPACE/scripts/plugin-cache-integrity.py}"
  PLUGIN_QUARANTINE_DIR="${WORKFLOW_VERIFY_PLUGIN_QUARANTINE_DIR:-$WORKSPACE/backups/plugin-quarantine}"
  SECURE_RUNTIME_WITNESS="${WORKFLOW_VERIFY_SECURE_RUNTIME_WITNESS:-$WORKSPACE/.atl/secure-opencode-runtime-witness.json}"
  CACHE_PRUNE_APPROVAL="${WORKFLOW_VERIFY_CACHE_PRUNE_APPROVAL:-$WORKSPACE/.atl/opencode-cache-prune-approval.json}"
  WORKFLOW="${WORKFLOW_VERIFY_WORKFLOW:-$WORKSPACE/WORKFLOW.md}"
  REQS="${WORKFLOW_VERIFY_REQS:-$WORKSPACE/docs/brainstorms/2026-08-10-workflow-routing-requirements.md}"
}
derive_workspace_paths
# V2 mode (Q44): the generated V2 config root, its npm cache and the sandbox repo derive reads.
V2_BASE_DIR="${WORKFLOW_VERIFY_V2_BASE_DIR:-/home/james/.local/share/opencode-v2}"
export V2_BASE_DIR
V2_CONFIG_ROOT="${WORKFLOW_VERIFY_V2_CONFIG_ROOT:-$V2_BASE_DIR/config/opencode}"
V2_NPM_CACHE="${WORKFLOW_VERIFY_V2_NPM_CACHE:-$V2_BASE_DIR/cache/opencode/npm}"
V2_SANDBOX_REPO="${WORKFLOW_VERIFY_SANDBOX_REPO:-/home/james/agent-sandbox-integration}"
V2_SERVER_URL="${WORKFLOW_VERIFY_V2_SERVER_URL:-http://127.0.0.1:4097}"
V2_SERVER_PASSWORD_FILE="${WORKFLOW_VERIFY_V2_SERVER_PASSWORD_FILE:-$V2_BASE_DIR/server-password}"
GENTLE_STATE_FILE="${WORKFLOW_VERIFY_GENTLE_STATE_FILE:-/home/james/.gentle-ai/state.json}"

ROUTING_MARKER_START="<!-- user:workflow-routing -->"
ROUTING_MARKER_END="<!-- /user:workflow-routing -->"

HEALTH_PLUGIN_DEPLOYED="$PLUGINS_DIR/workflow-health-check.ts"
ROUTING_GUARD_DEPLOYED="$PLUGINS_DIR/systematic-routing-guard.ts"
ASTRA_PLUGIN_DEPLOYED="$PLUGINS_DIR/astra-sol-upgrade.ts"
RELAY_PLUGIN_DEPLOYED="$PLUGINS_DIR/reviewer-relay-transport.ts"
HOST_APPROVAL_HELPER_DEPLOYED="$PLUGINS_DIR/lib/host-tool-approval.ts"
FALLBACK_EXCLUSION_SOURCE="$PLUGINS_DIR/opencode-rate-limit-fallback-mapped/src/config.ts"
SANDBOX_INTEGRATION_REPO="${WORKFLOW_VERIFY_SANDBOX_REPO:-}"
OLD_TIERING_PLUGIN_ACTIVE="$PLUGINS_DIR/systematic-model-tiering.ts"
AUTO_UPDATE_LOCK="$OPENCODE_CONFIG_DIR/.auto-update.lock"
LOCAL_AUTO_UPDATE_REF="${WORKFLOW_VERIFY_LOCAL_AUTO_UPDATE_REF:-file:///home/james/.local/share/opencode-plugin-auto-update-local/dist/index.js}"
SECURE_OPENCODE_SERVICE="${WORKFLOW_VERIFY_SECURE_OPENCODE_SERVICE:-secure-opencode.service}"

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

