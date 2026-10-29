# Run opencode for a verifier probe (queue Q44): bash "$OC_PROBE" <opencode arguments...>
# V1 (and unknown): exactly `opencode "$@"`, so existing behaviour and stdin handling are unchanged.
# V2: `--standalone` keeps the probe off the shared background service (fixed port 49374, which would
# not carry the probe environment), and stdin is closed because `opencode run` waits on an open pipe.
if [ "${OC_MAJOR:-0}" = "2" ]; then
  exec opencode --standalone "$@" </dev/null
fi
exec opencode "$@"
