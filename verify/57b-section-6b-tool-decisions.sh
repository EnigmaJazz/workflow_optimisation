# --- 6b. Sandbox tool decision coverage ---
echo "--- 6b. Sandbox tool decision coverage ---"
TOOL_DECISION_FIXTURE="${V2_SANDBOX_REPO:-/home/james/agent-sandbox-integration}/broker/tests/fixtures/sandbox-tools-surface.json"
if [ ! -f "$TOOL_DECISION_FIXTURE" ]; then
  echo "   info: sandbox tool surface fixture absent; decision coverage skipped"
else
  TOOL_DECISION_RESULT=$(python3 -B "$VERIFY_MODULE_DIR/checkers/sandbox-tool-decisions.py" "$OPENCODE_CONFIG_SOURCE" "$TOOL_DECISION_FIXTURE" 2>&1)
  case "$TOOL_DECISION_RESULT" in
    clean$'\t'*) echo "   ok: ${TOOL_DECISION_RESULT#*$'\t'}" ;;
    error$'\t'*) fail "SANDBOX_TOOL_DECISION_COVERAGE: ${TOOL_DECISION_RESULT#*$'\t'}" ;;
    *) fail "SANDBOX_TOOL_DECISION_COVERAGE: unexpected result ${TOOL_DECISION_RESULT:-<empty>}" ;;
  esac
fi
