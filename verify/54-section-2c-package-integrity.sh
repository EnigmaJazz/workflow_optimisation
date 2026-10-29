# --- 2c. Incomplete plugin package directories (interrupted installs) ---
echo "--- 2c. Plugin package integrity ---"
if [ ! -f "$PLUGIN_CACHE_INTEGRITY_HELPER" ]; then
  fail "PLUGIN_PACKAGE_INTEGRITY_HELPER_MISSING: $PLUGIN_CACHE_INTEGRITY_HELPER"
else
  PLUGIN_INTEGRITY_RESULT="$(
    python3 - "$PLUGIN_CACHE_INTEGRITY_HELPER" "$OPENCODE_CACHE_DIR/packages" "$AUTO_UPDATE_LOCK" "$PLUGIN_QUARANTINE_DIR" "$OPENCODE_CONFIG_FILE" "$TUI_CONFIG_FILE" <<'PY_PLUGIN_INTEGRITY' 2>&1
import json
import re
import subprocess
import sys

helper, cache_root, lock, quarantine, *configs = sys.argv[1:]
exact = re.compile(r"^(?:@[^/@]+/)?[^/@]+@\d+\.\d+\.\d+(?:[+-][0-9A-Za-z.+-]+)?$")
specs = []
for path in configs:
    try:
        with open(path, encoding="utf-8") as handle:
            plugins = json.load(handle).get("plugin", [])
    except Exception:
        continue
    for ref in plugins if isinstance(plugins, list) else []:
        if isinstance(ref, str) and exact.match(ref) and ref not in specs:
            specs.append(ref)
if not specs:
    print("ok\tno exact-version plugin specs configured")
    raise SystemExit(0)
cmd = [sys.executable, helper, "scan", "--cache-root", cache_root, "--lock", lock,
       "--quarantine-dir", quarantine, "--apply"]
for spec in specs:
    cmd += ["--spec", spec]
proc = subprocess.run(cmd, capture_output=True, text=True)
try:
    results = json.loads(proc.stdout)["results"]
except Exception:
    print(f"error\thelper failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    raise SystemExit(0)
problems = 0
for item in results:
    if item.get("action") == "quarantined":
        print(f"quarantined\t{item['spec']}\t{item['quarantined_to']}")
        problems += 1
    elif item.get("action") == "deferred":
        print(f"deferred\t{item['spec']}\t{item['reason']}; {item['detail']}")
        problems += 1
if not problems:
    print(f"ok\t{len(results)} configured plugin package(s) complete or not yet installed")
PY_PLUGIN_INTEGRITY
  )"
  while IFS=$'\t' read -r state spec detail; do
    case "$state" in
      ok)          echo "   ok: $spec" ;;
      quarantined) fail "PLUGIN_PACKAGE_INCOMPLETE_QUARANTINED: $spec -> $detail; restart OpenCode to reinstall" ;;
      deferred)    fail "PLUGIN_PACKAGE_INCOMPLETE: $spec ($detail)" ;;
      error)       fail "PLUGIN_PACKAGE_INTEGRITY_CHECK_FAILED: $spec" ;;
      *)           [ -n "$state" ] && fail "PLUGIN_PACKAGE_INTEGRITY_CHECK_FAILED: unexpected output $state" ;;
    esac
  done <<< "$PLUGIN_INTEGRITY_RESULT"
fi

