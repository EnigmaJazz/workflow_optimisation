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
  const readers=new Set(["gentle-orchestrator","explore"])
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

