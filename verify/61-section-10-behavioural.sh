# --- 10. Optional behavioural parallel-dispatch probe ---
echo "--- 10. Behavioural parallel dispatch ---"
if [ "$RUN_BEHAVIOURAL" -ne 1 ]; then
  echo "   skipped: run with --behavioral after workflow/OpenCode permission changes"
elif [ "$FAIL" -ne 0 ]; then
  fail "behavioural fan-out probe skipped because deterministic checks already failed"
elif ! command_exists opencode; then
  fail "opencode executable not found; behavioural fan-out probe skipped"
else
  PARALLEL_PROMPT='WORKFLOW HEALTH PROBE. Do not answer inline and do not inspect the repository. In your FIRST assistant tool-use step, emit exactly TWO native Task calls in the SAME assistant message before waiting for either result. Call subagent_type="explore" with prompt "Return exactly PARALLEL_SENTINEL_A and do not call any tools." Call subagent_type="general" with prompt "Return exactly PARALLEL_SENTINEL_B and do not call any tools." These tasks are independent. Do not call any other tool. After both Task results return, reply exactly PARALLEL_FANOUT_DONE.'

  PARALLEL_STATUS=0
  if command_exists timeout; then
    (
      cd "$PROBE_CWD" || exit 1
      WORKFLOW_HEALTH_CHECK_PROBE=1 \
      timeout 180s opencode run --format json --agent gentle-orchestrator "$PARALLEL_PROMPT" \
        >"$PARALLEL_EVENTS" 2>"$PARALLEL_STDERR"
    ) || PARALLEL_STATUS=$?
  else
    (
      cd "$PROBE_CWD" || exit 1
      WORKFLOW_HEALTH_CHECK_PROBE=1 \
      opencode run --format json --agent gentle-orchestrator "$PARALLEL_PROMPT" \
        >"$PARALLEL_EVENTS" 2>"$PARALLEL_STDERR"
    ) || PARALLEL_STATUS=$?
  fi

  if [ "$PARALLEL_STATUS" -ne 0 ]; then
    fail "behavioural fan-out probe failed (exit $PARALLEL_STATUS)"
    if [ -s "$PARALLEL_STDERR" ]; then
      echo "      probe stderr (tail):"
      tail -16 "$PARALLEL_STDERR" | sed 's/^/      /'
    fi
  elif python3 "$PARALLEL_CHECKER" "$PARALLEL_EVENTS"; then
    echo "   ok: native Task behavioural probe passed"
  else
    fail "behavioural parallel-dispatch contract failed"
    echo "      retained diagnostic preview:"
    grep -E '"type":"(tool_use|text|step_finish)"|"tool":"task"' "$PARALLEL_EVENTS" 2>/dev/null | tail -20 | sed 's/^/      /'
    if [ -s "$PARALLEL_STDERR" ]; then
      echo "      probe stderr (tail):"
      tail -12 "$PARALLEL_STDERR" | sed 's/^/      /'
    fi
  fi
fi

# A second, read-only behavioural probe checks that the ODD authorization
# boundary holds in an actual orchestrator turn. It runs only under the paid,
# user-invoked --behavioral flag, in the same neutral temporary project.
echo "--- 10a. Behavioural ODD read-only authorization ---"
if [ "$RUN_BEHAVIOURAL" -ne 1 ]; then
  echo "   skipped: run with --behavioral to test the ODD route"
elif [ "$FAIL" -ne 0 ]; then
  fail "ODD behavioural probe skipped because earlier health checks failed"
else
  ODD_PROMPT='WORKFLOW HEALTH READ-ONLY PROBE. This is a planning-only question. Briefly explain how you would approach adding a single text label to a hypothetical application. Do not implement, write or modify files, register a project, start review, or create task records. No source repository is provided.'
  ODD_EVENTS="$TMP_DIR/odd-readonly-events.jsonl"
  ODD_STDERR="$TMP_DIR/odd-readonly.stderr"
  ODD_STATUS=0
  (
    cd "$PROBE_CWD" || exit 1
    WORKFLOW_HEALTH_CHECK_PROBE=1 timeout 120s opencode run --format json --agent gentle-orchestrator "$ODD_PROMPT" >"$ODD_EVENTS" 2>"$ODD_STDERR"
  ) || ODD_STATUS=$?
  if [ "$ODD_STATUS" -ne 0 ]; then
    fail "ODD_READ_ONLY_PROBE_FAILED: opencode run exited $ODD_STATUS"
    tail -10 "$ODD_STDERR" 2>/dev/null | sed 's/^/      /'
  elif python3 - "$ODD_EVENTS" "$PROBE_CWD" <<'PY_ODD_READONLY'
import json
from pathlib import Path
import sys

events = Path(sys.argv[1])
root = Path(sys.argv[2])
loaded_router = False
skill_calls = []
for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    part = event.get("part")
    if not isinstance(part, dict):
        continue
    tool = part.get("tool")
    state = part.get("state") or {}
    if not isinstance(state, dict):
        state = {}
    launch = state.get("input") or {}
    if not isinstance(launch, dict):
        launch = {}
    if tool == "skill" and isinstance(launch.get("name"), str):
        skill_calls.append(launch["name"])
        if launch["name"] == "workflow-route":
            loaded_router = True
    if tool in {"sandbox_write","sandbox_edit","sandbox_apply_patch","sandbox_bash","sandbox_apply","write","edit","bash","host_plan_append","host_review_start","host_register_project"} or (tool == "task" and launch.get("subagent_type") not in {"explore"}):
        print(f"   !! ODD_READ_ONLY_MUTATION_OR_WRITER: tool={tool} agent={launch.get('subagent_type')}")
        raise SystemExit(1)
if not loaded_router:
    print("   !! ODD_ROUTER_SKILL_NOT_LOADED: expected native skill(workflow-route) call")
    raise SystemExit(1)
route_skills = [name for name in skill_calls if name.startswith("workflow-") and name != "workflow-route"]
assigned_route = "workflow-odd-secure"
if not route_skills:
    print("   !! ODD_ROUTE_SKILL_NOT_LOADED: expected the assigned workflow-odd-secure route adapter after workflow-route")
    raise SystemExit(1)
if assigned_route not in route_skills:
    print(f"   !! ODD_ROUTE_SKILL_NOT_ASSIGNED: expected {assigned_route}, observed {route_skills!r}")
    raise SystemExit(1)
if skill_calls.index("workflow-route") > skill_calls.index(assigned_route):
    print("   !! ODD_ROUTE_SKILL_ORDER: workflow-route must load before the assigned route adapter")
    raise SystemExit(1)
if route_skills != [assigned_route]:
    print(f"   !! ODD_ROUTE_SKILL_UNEXPECTED: expected only {assigned_route}, observed {route_skills!r}")
    raise SystemExit(1)
if (root / "odd" / "tasks").exists():
    print("   !! ODD_READ_ONLY_TRACKER_CREATED: odd/tasks exists in probe")
    raise SystemExit(1)
print("   ok: planning-only request launched no writer and created no ODD tracker")
PY_ODD_READONLY
  then
    :
  else
    fail "ODD_READ_ONLY_AUTHORIZATION_FAILED"
  fi
fi

