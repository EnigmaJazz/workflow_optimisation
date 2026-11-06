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

cat "$VERIFY_MODULE_DIR/checkers/routing-canonical.md" > "$ROUTING_CANONICAL"

cat "$VERIFY_MODULE_DIR/checkers/check-parallel-dispatch.py" > "$PARALLEL_CHECKER"

