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
OC_PROBE="$VERIFY_MODULE_DIR/checkers/oc-probe.sh"
