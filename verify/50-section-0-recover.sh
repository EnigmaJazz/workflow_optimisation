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
  if [ -f "$MODEL_CONFIG" ] && grep -Eq -- 'muse-spark-1\.2-contributor|deepseek-v4-pro' "$MODEL_CONFIG" 2>/dev/null; then
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

