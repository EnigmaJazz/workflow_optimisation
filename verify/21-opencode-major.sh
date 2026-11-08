# --- OpenCode major version (queue Q44) ---
# OC_MAJOR is 1 or 2, or 0 when it cannot be determined; 0 behaves as V1, exactly as before this module
# existed. WORKFLOW_VERIFY_OPENCODE_MAJOR (1 or 2) overrides detection for fixtures. Every opencode probe
# goes through checkers/oc-probe.sh, which is the only place the two majors differ.
detect_opencode_major() {
  local override="${WORKFLOW_VERIFY_OPENCODE_MAJOR:-}" version_output major
  case "$override" in
    1|2) printf '%s\n' "$override"; return 0 ;;
  esac
  if ! command -v opencode >/dev/null 2>&1; then
    printf '0\n'
    return 0
  fi
  if command -v timeout >/dev/null 2>&1; then
    version_output=$(timeout 10 opencode --version </dev/null 2>/dev/null || true)
  else
    version_output=$(opencode --version </dev/null 2>/dev/null || true)
  fi
  major=$(printf '%s\n' "$version_output" | sed -nE 's/^[^0-9]*([0-9]+)\.[0-9]+\.[0-9]+.*/\1/p' | head -1)
  case "$major" in
    1|2) printf '%s\n' "$major" ;;
    *) printf '0\n' ;;
  esac
}
OC_MAJOR=$(detect_opencode_major)
export OC_MAJOR
if [ "$OC_MAJOR" = "2" ]; then
  if [ -z "${WORKFLOW_VERIFY_WORKSPACE:-}" ]; then
    VERIFY_SCRIPT_PATH="${VERIFY_ENTRY_PATH:-$0}"
    WORKSPACE="$(cd "$(dirname "$VERIFY_SCRIPT_PATH")" 2>/dev/null && pwd)"
    if [ -z "$WORKSPACE" ]; then
      echo "V2_WORKSPACE_DERIVATION_FAILED: cannot resolve verifier entry directory: $VERIFY_SCRIPT_PATH" >&2
      exit 2
    fi
    derive_workspace_paths
  fi
  AGENTS_FILE="${WORKFLOW_VERIFY_AGENTS_FILE:-$V2_CONFIG_ROOT/AGENTS.md}"
  RUNTIME_CONFIG_FILE="${WORKFLOW_VERIFY_RUNTIME_CONFIG_FILE:-$V2_CONFIG_ROOT/opencode.json}"
  echo "   info: V2 workspace=$WORKSPACE agents=$AGENTS_FILE runtime-config=$RUNTIME_CONFIG_FILE"
fi
# V2 loads Systematic's config from the overlay under its own HOME, not from ~/.config/opencode. Point the static validation at it
# (an explicit WORKFLOW_VERIFY override still wins).
if [ "$OC_MAJOR" = "2" ] && [ -z "${WORKFLOW_VERIFY_SYSTEMATIC_CONFIG:-}" ]; then
  SYSTEMATIC_CONFIG="$V2_BASE_DIR/config/home/.config/opencode/systematic.jsonc"
fi
OC_PROBE="$VERIFY_MODULE_DIR/checkers/oc-probe.sh"
