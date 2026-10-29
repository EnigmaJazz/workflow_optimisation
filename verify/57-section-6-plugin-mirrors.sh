# --- 6. Reviewed plugin mirrors + script digest binding ---
echo "--- 6. Reviewed plugin mirrors ---"
for required_plugin in "$PLUGINS_DIR/sandbox-tools.ts" "$PLUGINS_DIR/routing-guard.ts" "$RELAY_PLUGIN_DEPLOYED" "$PLUGINS_DIR/lib/broker-client.ts" "$HOST_APPROVAL_HELPER_DEPLOYED"; do
  if [ ! -f "$required_plugin" ]; then
    fail "HOST_TOOL_PLUGIN_MISSING: $required_plugin (install from agent-sandbox-integration; keep installer and rollback in sync)"
  fi
done
if [ -n "$SANDBOX_INTEGRATION_REPO" ]; then
  for relative_plugin in sandbox-tools.ts routing-guard.ts reviewer-relay-transport.ts lib/broker-client.ts lib/host-tool-approval.ts; do
    source_plugin="$SANDBOX_INTEGRATION_REPO/opencode/plugins/$relative_plugin"
    deployed_plugin="$PLUGINS_DIR/$relative_plugin"
    if [ ! -f "$source_plugin" ] || ! cmp -s "$source_plugin" "$deployed_plugin"; then
      fail "HOST_TOOL_PLUGIN_SOURCE_DRIFT: $relative_plugin; review installer and rollback before deployment"
    fi
  done
  for installer in "$SANDBOX_INTEGRATION_REPO/scripts/install-user-files" "$SANDBOX_INTEGRATION_REPO/scripts/rollback"; do
    if [ ! -f "$installer" ] || ! grep -Fq 'reviewer-relay-transport.ts' "$installer" || ! grep -Fq 'host-tool-approval.ts' "$installer"; then
      fail "HOST_TOOL_INSTALL_ROLLBACK_GAP: $installer must include both new plugin files"
    fi
  done
else
  echo "   info: set WORKFLOW_VERIFY_SANDBOX_REPO to inspect agent-sandbox-integration source, installer and rollback parity"
fi
SELF_PATH=$(readlink -f "$0" 2>/dev/null || printf '%s' "$0")
SELF_SHA=$(sha256_file "$SELF_PATH")
if [ -z "$SELF_SHA" ]; then
  fail "could not compute SHA256 for $SELF_PATH"
  CAN_RUNTIME_PROBE=0
else
  echo "   verify-workflow.sh sha256: $SELF_SHA"
fi

# workflow-health-check.ts is special: its reviewed source must pin this exact
# script before we deploy it, otherwise the next OpenCode startup will (correctly)
# refuse to execute the verifier.
if [ ! -f "$HEALTH_PLUGIN_SOURCE" ]; then
  fail "health plugin source missing: $HEALTH_PLUGIN_SOURCE"
  CAN_RUNTIME_PROBE=0
else
  SOURCE_PIN=$(read_verify_script_pin "$HEALTH_PLUGIN_SOURCE" 2>/dev/null || true)
  if [ -z "$SOURCE_PIN" ]; then
    fail "could not read VERIFY_SCRIPT_SHA256 from health plugin source"
    CAN_RUNTIME_PROBE=0
  elif [ "$SOURCE_PIN" != "$SELF_SHA" ]; then
    fail "health plugin source pins $SOURCE_PIN but this script is $SELF_SHA"
    echo "      update VERIFY_SCRIPT_SHA256 in $HEALTH_PLUGIN_SOURCE after reviewing this script"
    CAN_RUNTIME_PROBE=0
  else
    echo "   ok: health plugin source pins this exact verifier"
  fi

  if grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_SOURCE"; then
    echo "   ok: health plugin source contains runtime-probe recursion guard"
  else
    fail "health plugin source lacks WORKFLOW_HEALTH_CHECK_PROBE recursion guard"
    CAN_RUNTIME_PROBE=0
  fi

  if [ "$SOURCE_PIN" = "$SELF_SHA" ] && grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_SOURCE"; then
    if [ -f "$HEALTH_PLUGIN_DEPLOYED" ] && cmp -s "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED"; then
      echo "   ok: workflow-health-check.ts mirror is current"
    else
      repair_note "re-mirroring workflow-health-check.ts from reviewed source"
      if cp "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED" && cmp -s "$HEALTH_PLUGIN_SOURCE" "$HEALTH_PLUGIN_DEPLOYED"; then
        echo "   ok: workflow-health-check.ts mirror restored (restart OpenCode to load it)"
      else
        fail "could not re-mirror workflow-health-check.ts"
        CAN_RUNTIME_PROBE=0
      fi
    fi
  fi
fi

# New runtime routing guard: reviewed workspace copy is authoritative.
if [ ! -f "$ROUTING_GUARD_SOURCE" ]; then
  fail "routing guard source missing: $ROUTING_GUARD_SOURCE"
else
  if [ -f "$ROUTING_GUARD_DEPLOYED" ] && cmp -s "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED"; then
    echo "   ok: systematic-routing-guard.ts mirror is current"
  else
    repair_note "re-mirroring systematic-routing-guard.ts from reviewed source"
    if cp "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED" && cmp -s "$ROUTING_GUARD_SOURCE" "$ROUTING_GUARD_DEPLOYED"; then
      echo "   ok: systematic-routing-guard.ts mirror restored (restart OpenCode to load it)"
    else
      fail "could not re-mirror systematic-routing-guard.ts"
    fi
  fi
fi

# Validate the deployed plugin bytes through the same factory/hook load check.
# Factory probes run below, after all three reviewed plugin mirrors.

routing_guard_test_home=$(mktemp -d) || {
  fail "could not create isolated HOME for routing-guard tests"
  routing_guard_test_home=""
}
if [ -n "$routing_guard_test_home" ]; then
  if (cd "$WORKSPACE" && env HOME="$routing_guard_test_home" bun test tests/routing-guard); then
    echo "   OK routing guard tests"
  else
    fail "routing guard test suite failed"
  fi
  rm -rf "$routing_guard_test_home"
fi

# Astra is exposed through derived aliases rather than a Systematic profile or
# copied agent definitions. The reviewed local plugin must remain byte-identical
# to its deployed mirror so Systematic/Gentle AI prompts can continue to update.
# Plugin loading intentionally stays non-recursive (see check_plugin_loads); mirror
# the plugin library tree recursively so imported helpers are deployed but never
# treated as standalone plugins. A missing source lib directory is valid.
PLUGIN_LIBRARY_SOURCE="$WORKSPACE/global-config/plugins/lib"
if [ -d "$PLUGIN_LIBRARY_SOURCE" ]; then
  if mkdir -p "$PLUGINS_DIR/lib" && cp -R "$PLUGIN_LIBRARY_SOURCE/." "$PLUGINS_DIR/lib/"; then
    echo "   ok: plugin library tree mirrored recursively"
  else
    fail "could not mirror plugin library tree from $PLUGIN_LIBRARY_SOURCE"
  fi
fi

if [ ! -f "$ASTRA_PLUGIN_SOURCE" ]; then
  fail "Astra Sol-upgrade plugin source missing: $ASTRA_PLUGIN_SOURCE"
else
  ASTRA_SOURCE_OK=1
  for marker in 'SOL_MODEL = "openai/gpt-6.1-sol"' 'ASTRA_MODEL = "openai/gpt-6-astra"' 'ASTRA_SUFFIX = "-astra"' 'isImplementationRoute' 'systematic-implementer' 'bug-reproduction-validator'; do
    if ! grep -Fq -- "$marker" "$ASTRA_PLUGIN_SOURCE"; then
      fail "Astra Sol-upgrade plugin source is missing required marker: $marker"
      ASTRA_SOURCE_OK=0
    fi
  done
  if [ "$ASTRA_SOURCE_OK" -eq 1 ]; then
    if [ -f "$ASTRA_PLUGIN_DEPLOYED" ] && cmp -s "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED"; then
      echo "   ok: astra-sol-upgrade.ts mirror is current"
    else
      repair_note "re-mirroring astra-sol-upgrade.ts from reviewed source"
      if cp "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED" && cmp -s "$ASTRA_PLUGIN_SOURCE" "$ASTRA_PLUGIN_DEPLOYED"; then
        echo "   ok: astra-sol-upgrade.ts mirror restored (restart OpenCode once to load the repaired plugin)"
      else
        fail "could not re-mirror astra-sol-upgrade.ts"
      fi
    fi
    # Factory probes run only after all three reviewed plugin mirrors, including Astra, are current.
    check_plugin_loads "$PLUGINS_DIR" factory
  fi
fi

# The superseded model-tiering plugin must remain disabled. Having both active
# would create overlapping mutations/diagnostics at the task hook boundary.
if [ -e "$OLD_TIERING_PLUGIN_ACTIVE" ]; then
  fail "obsolete systematic-model-tiering.ts is active; keep it .disabled or remove it"
else
  echo "   ok: obsolete systematic-model-tiering.ts is not active"
fi

# Auto-update lock health. opencode-plugin-auto-update can leave a lock behind
# if an update process dies after acquiring it. Its normal lock acquisition does
# not force-recover stale locks, so an orphan can block every future update.
# Only self-repair when the lock contains a numeric PID and that PID is definitely
# not running. Never delete a live or ambiguous lock.
echo "   auto-update lock health:"
if [ ! -e "$AUTO_UPDATE_LOCK" ]; then
  echo "   ok: no auto-update lock present"
elif [ ! -f "$AUTO_UPDATE_LOCK" ]; then
  fail "auto-update lock path exists but is not a regular file: $AUTO_UPDATE_LOCK"
else
  AUTO_UPDATE_PID=$(sed -nE 's/.*"pid"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$AUTO_UPDATE_LOCK" | head -1)
  AUTO_UPDATE_TS=$(sed -nE 's/.*"timestamp"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$AUTO_UPDATE_LOCK" | head -1)

  if [[ ! "$AUTO_UPDATE_PID" =~ ^[0-9]+$ ]] || [ "$AUTO_UPDATE_PID" -le 0 ]; then
    fail "auto-update lock is malformed or has no valid PID; refusing automatic deletion"
    sed -n '1,8p' "$AUTO_UPDATE_LOCK" | sed 's/^/      /'
  elif kill -0 "$AUTO_UPDATE_PID" 2>/dev/null; then
    if [[ "$AUTO_UPDATE_TS" =~ ^[0-9]+$ ]]; then
      AUTO_UPDATE_LOCK_SEC=$((AUTO_UPDATE_TS / 1000))
      AUTO_UPDATE_LOCK_UTC=$(date -u -d "@$AUTO_UPDATE_LOCK_SEC" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || true)
      echo "   ok: auto-update lock is held by live pid $AUTO_UPDATE_PID${AUTO_UPDATE_LOCK_UTC:+ (since $AUTO_UPDATE_LOCK_UTC)}"
    else
      echo "   ok: auto-update lock is held by live pid $AUTO_UPDATE_PID"
    fi
  else
    LOCK_DETAIL="pid $AUTO_UPDATE_PID is not running"
    if [[ "$AUTO_UPDATE_TS" =~ ^[0-9]+$ ]]; then
      AUTO_UPDATE_LOCK_SEC=$((AUTO_UPDATE_TS / 1000))
      AUTO_UPDATE_LOCK_UTC=$(date -u -d "@$AUTO_UPDATE_LOCK_SEC" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || true)
      if [ -n "$AUTO_UPDATE_LOCK_UTC" ]; then
        LOCK_DETAIL="$LOCK_DETAIL; lock timestamp $AUTO_UPDATE_LOCK_UTC"
      fi
    fi

    repair_note "removing orphaned auto-update lock ($LOCK_DETAIL)"
    if rm -- "$AUTO_UPDATE_LOCK"; then
      echo "   ok: orphaned auto-update lock removed; future update passes are unblocked"
    else
      fail "could not remove orphaned auto-update lock: $AUTO_UPDATE_LOCK"
    fi
  fi
fi

# Disk configuration is only the desired state. OpenCode and updater plugins
# may atomically rewrite or merely touch unchanged files during startup, making
# mtime > service-start permanently true. Bind file content hashes to a systemd
# invocation instead: a changed generation fails until a later invocation sees
# the same hashes, while same-content startup rewrites remain certified.
# Never restart automatically: that would disrupt active sessions.
echo "   secure OpenCode runtime generation:"
if ! command_exists systemctl; then
  echo "   info: systemctl unavailable; secure runtime generation not checked"
else
  SERVICE_LOAD_STATE="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p LoadState --value 2>/dev/null || true)"
  SERVICE_ACTIVE_STATE="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p ActiveState --value 2>/dev/null || true)"
  if [ "$SERVICE_LOAD_STATE" != "loaded" ]; then
    echo "   info: $SECURE_OPENCODE_SERVICE is not installed in this environment; freshness check skipped"
  elif [ "$SERVICE_ACTIVE_STATE" != "active" ]; then
    echo "   info: $SECURE_OPENCODE_SERVICE is ${SERVICE_ACTIVE_STATE:-inactive}; no loaded runtime is being certified"
  else
    SERVICE_STARTED_RAW="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p ExecMainStartTimestamp --value 2>/dev/null || true)"
    SERVICE_STARTED_EPOCH="$(date -d "$SERVICE_STARTED_RAW" +%s 2>/dev/null || true)"
    SERVICE_INVOCATION_ID="$(systemctl --user show "$SECURE_OPENCODE_SERVICE" -p InvocationID --value 2>/dev/null || true)"
    if [[ ! "$SERVICE_STARTED_EPOCH" =~ ^[0-9]+$ ]]; then
      fail "SECURE_OPENCODE_START_TIME_UNAVAILABLE: could not parse ${SERVICE_STARTED_RAW:-<empty>}"
    else
      if [ -z "$SERVICE_INVOCATION_ID" ]; then
        SERVICE_INVOCATION_ID="start-$SERVICE_STARTED_EPOCH"
      fi
      RUNTIME_GENERATION_RESULT="$(
        python3 - "$SECURE_RUNTIME_WITNESS" "$SECURE_OPENCODE_SERVICE" \
          "$SERVICE_INVOCATION_ID" "$SERVICE_STARTED_EPOCH" \
        "$OPENCODE_CONFIG_FILE" "$AGENTS_FILE" "$SYSTEMATIC_CONFIG" \
        "$FALLBACK_POLICY_DEPLOYED" "$HEALTH_PLUGIN_DEPLOYED" \
          "$ROUTING_GUARD_DEPLOYED" "$ASTRA_PLUGIN_DEPLOYED" \
          "$RELAY_PLUGIN_DEPLOYED" "$HOST_APPROVAL_HELPER_DEPLOYED" \
          "$FALLBACK_EXCLUSION_SOURCE" <<'PY_RUNTIME_WITNESS'
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

witness_path = Path(sys.argv[1])
service = sys.argv[2]
invocation = sys.argv[3]
start_epoch = int(sys.argv[4])
paths = [Path(value) for value in sys.argv[5:] if Path(value).is_file()]

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

current_hashes = {str(path): digest(path) for path in paths}
newer = [str(path) for path in paths if path.stat().st_mtime_ns > start_epoch * 1_000_000_000]

previous = None
try:
    candidate = json.loads(witness_path.read_text(encoding="utf-8"))
    if (candidate.get("schema") == "workflow.secure-runtime-witness/v1" and
            candidate.get("service") == service and isinstance(candidate.get("files"), dict)):
        previous = candidate
except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
    pass

same_hashes = previous is not None and previous.get("files") == current_hashes
same_invocation = previous is not None and previous.get("invocation_id") == invocation
previous_certified = previous is not None and previous.get("certified") is True
content_changed_during_invocation = previous is not None and same_invocation and not same_hashes

if content_changed_during_invocation:
    certified = False
    reason = "runtime content changed during the active service invocation"
elif newer:
    # A prior certified hash set proves unchanged content. A pending witness is
    # promoted only after systemd supplies a different invocation ID.
    certified = same_hashes and (previous_certified or not same_invocation)
    reason = "unchanged startup rewrite" if certified else "runtime content has not been loaded by a later service invocation"
else:
    certified = True
    reason = "all runtime content predates the active service invocation"

payload = {
    "schema": "workflow.secure-runtime-witness/v1",
    "service": service,
    "invocation_id": invocation,
    "service_start_epoch": start_epoch,
    "certified": certified,
    "files": current_hashes,
}

try:
    if previous != payload:
        witness_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".secure-runtime-witness.", dir=witness_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, witness_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
except OSError as exc:
    print(f"error\tcould not update runtime witness: {exc}")
    raise SystemExit(0)

if certified:
    print(f"clean\t{reason}; {len(current_hashes)} file hashes certified for invocation {invocation}")
else:
    affected = newer if newer else sorted(current_hashes)
    print(f"restart\t{reason}\t" + "\t".join(affected))
PY_RUNTIME_WITNESS
      )"

      case "$RUNTIME_GENERATION_RESULT" in
        clean$'\t'*)
          echo "   ok: ${RUNTIME_GENERATION_RESULT#*$'\t'}"
          ;;
        restart$'\t'*)
          RUNTIME_RESTART_REQUIRED=1
          generation_detail="${RUNTIME_GENERATION_RESULT#*$'\t'}"
          generation_reason="${generation_detail%%$'\t'*}"
          fail "SECURE_OPENCODE_RESTART_REQUIRED: $generation_reason"
          if [[ "$generation_detail" == *$'\t'* ]]; then
            while IFS= read -r runtime_file; do
              [ -n "$runtime_file" ] && echo "      changed/newer runtime content: $runtime_file"
            done < <(printf '%s' "${generation_detail#*$'\t'}" | tr '\t' '\n')
          fi
          echo "      Fish: systemctl --user restart $SECURE_OPENCODE_SERVICE"
          ;;
        error$'\t'*)
          fail "SECURE_OPENCODE_RUNTIME_WITNESS_FAILED: ${RUNTIME_GENERATION_RESULT#*$'\t'}"
          ;;
        *)
          fail "SECURE_OPENCODE_RUNTIME_WITNESS_FAILED: unexpected result ${RUNTIME_GENERATION_RESULT:-<empty>}"
          ;;
      esac
    fi
  fi
fi

# Re-check the deployed health plugin before permitting a nested OpenCode probe.
if [ "$CAN_RUNTIME_PROBE" -eq 1 ]; then
  if [ ! -f "$HEALTH_PLUGIN_DEPLOYED" ]; then
    fail "deployed workflow-health-check.ts missing"
    CAN_RUNTIME_PROBE=0
  elif ! grep -q 'WORKFLOW_HEALTH_CHECK_PROBE' "$HEALTH_PLUGIN_DEPLOYED"; then
    fail "deployed workflow-health-check.ts lacks recursion guard; runtime probe skipped safely"
    CAN_RUNTIME_PROBE=0
  else
    DEPLOYED_PIN=$(read_verify_script_pin "$HEALTH_PLUGIN_DEPLOYED" 2>/dev/null || true)
    if [ "$DEPLOYED_PIN" != "$SELF_SHA" ]; then
      fail "deployed workflow-health-check.ts pins a different verifier digest; runtime probe skipped safely"
      CAN_RUNTIME_PROBE=0
    fi
  fi
fi

