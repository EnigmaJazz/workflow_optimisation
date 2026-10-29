# --- 1. Gentle AI v4 + user-selected native review/telemetry modes ---
echo "--- 1. Gentle AI v4 + native review mode ---"
if command_exists gentle-ai; then
  VERSION_RAW=$(gentle-ai --version 2>/dev/null | head -1 || true)
  echo "   ${VERSION_RAW:-version unavailable}"
  GENTLE_VERSION=$(printf '%s\n' "$VERSION_RAW" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  if [ -z "$GENTLE_VERSION" ] || [ "$(printf '%s\n' "4.0.0" "$GENTLE_VERSION" | sort -V | head -1)" != "4.0.0" ]; then
    fail "Gentle AI v4.0.0+ is required by this workflow"
  fi
  MODE=$(gentle-ai review mode status --cwd "$WORKSPACE" 2>/dev/null | head -1 || true)
  if [[ "$MODE" =~ ^receipt-driven\ development:\ (on|off)\ \(decided\ by\ (default|global|clone-local)\)$ ]]; then
    echo "   $MODE"
    if [ "${BASH_REMATCH[1]}" = off ]; then
      echo "   info: RDD is explicitly off for this project; preserving the user's choice"
    fi
  else
    fail "GENTLE_AI_V4_REVIEW_MODE_UNKNOWN: cannot read effective RDD mode and deciding source: ${MODE:-<empty>}"
  fi
  if [ -f "$GENTLE_STATE_FILE" ]; then
    SYNC_WITNESS=$(node -e 'const fs=require("fs");try{const s=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));if(typeof s.last_synced_at!=="string"||!s.last_synced_at||!Number.isFinite(Date.parse(s.last_synced_at)))process.exit(1);console.log(s.last_synced_at+"|"+(s.installed_binary_version||"unknown"))}catch{process.exit(1)}' "$GENTLE_STATE_FILE" 2>/dev/null) || SYNC_WITNESS=""
    if [ -n "$SYNC_WITNESS" ]; then
      echo "   ok: last successful Gentle AI sync: ${SYNC_WITNESS%%|*} (state binary version: ${SYNC_WITNESS#*|})"
      STATE_BINARY_VERSION=${SYNC_WITNESS#*|}
      if [ "$STATE_BINARY_VERSION" != unknown ] && [ "${STATE_BINARY_VERSION#v}" != "$GENTLE_VERSION" ]; then
        fail "GENTLE_AI_V4_SYNC_VERSION_DRIFT: managed state does not match installed binary; run gentle-ai sync"
      fi
    else
      fail "GENTLE_AI_V4_SYNC_NOT_CONFIRMED: last_synced_at is absent or invalid in $GENTLE_STATE_FILE; run gentle-ai sync"
    fi
  else
    fail "GENTLE_AI_V4_SYNC_STATE_MISSING: $GENTLE_STATE_FILE; run gentle-ai sync"
  fi
  TELEMETRY_STATUS=$(gentle-ai telemetry status 2>/dev/null | head -1 || true)
  if [ -n "$TELEMETRY_STATUS" ]; then
    echo "   telemetry: $TELEMETRY_STATUS"
  else
    fail "could not read Gentle AI v4 telemetry status"
  fi
else
  fail "gentle-ai executable not found"
fi

# Gentle AI v4 ODD delivery skills are resolved by registry name and
# must be installed before feature work can create scoped commits/PR slices.
for odd_skill in work-unit-commits chained-pr; do
  if [ ! -f "$SKILLS_DIR/$odd_skill/SKILL.md" ]; then
    fail "GENTLE_AI_V4_ODD_SKILL_MISSING: $SKILLS_DIR/$odd_skill/SKILL.md; run gentle-ai sync after upgrading"
  else
    echo "   ok: Gentle AI ODD delivery skill installed: $odd_skill"
  fi
done

