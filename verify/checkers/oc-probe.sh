# Run opencode for a verifier probe (queue Q44): bash "$OC_PROBE" <opencode arguments...>
# V1 (and unknown): exactly `opencode "$@"`, so existing behaviour and stdin handling are unchanged.
# V2: `--standalone` keeps the probe off the shared background service (fixed port 49374, which would
# not carry the probe environment), and stdin is closed because `opencode run` waits on an open pipe.
# Safety: this file is run (bash "$OC_PROBE" ...), never sourced, and never without arguments. `exec opencode` with no
# arguments opens the TUI and would replace the calling shell (the verifier once ended that way).
if [ "${BASH_SOURCE[0]}" != "$0" ]; then
  echo "oc-probe.sh must be run, not sourced" >&2
  return 2 2>/dev/null || exit 2
fi
if [ "$#" -eq 0 ]; then
  echo "oc-probe.sh: no opencode arguments given (a bare opencode opens the TUI)" >&2
  exit 2
fi
if [ "${OC_MAJOR:-0}" = "2" ]; then
  # With V2_BASE_DIR set, probe the V2 install the way its service runs: V2's own XDG roots and the overlay HOME. Without
  # it V2 reads the default (V1) config directories, loads V1-only plugins and never finishes activating.
  if [ -n "${V2_BASE_DIR:-}" ]; then
    exec env HOME="$V2_BASE_DIR/config/home" XDG_CONFIG_HOME="$V2_BASE_DIR/config" XDG_DATA_HOME="$V2_BASE_DIR/data" \
      XDG_STATE_HOME="$V2_BASE_DIR/state" XDG_CACHE_HOME="$V2_BASE_DIR/cache" opencode --standalone "$@" </dev/null
  fi
  exec opencode --standalone "$@" </dev/null
fi
exec opencode "$@"
