TMP_BASE="${XDG_CACHE_HOME:-/home/james/.cache}/workflow-health-check"
if ! mkdir -p "$TMP_BASE" 2>/dev/null; then
  TMP_BASE="/tmp/workflow-health-check"
  mkdir -p "$TMP_BASE" 2>/dev/null || true
fi
TMP_DIR=$(mktemp -d "$TMP_BASE/run.XXXXXX" 2>/dev/null || mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ROUTING_CANONICAL="$TMP_DIR/routing-section.md"
ROUTING_CONTRACT="$TMP_DIR/secure-routing-contract.md"
SYSTEMATIC_CHECKER="$TMP_DIR/check-systematic-resolution.cjs"
RUNTIME_AGENT_CHECKER="$TMP_DIR/check-runtime-agents.cjs"
AGENT_LIST_OUT="$TMP_DIR/opencode-agent-list.txt"
AGENT_LIST_STDERR="$TMP_DIR/opencode-agent-list.stderr"
DEBUG_AGENT_DIR="$TMP_DIR/debug-agents"
PROBE_CWD="$TMP_DIR/neutral-cwd"
# Systematic registers agents for the active project. Use the reviewed repo
# for registration probes; keep the neutral directory for behavioural probes.
AGENT_PROBE_CWD="$WORKSPACE"
PARALLEL_EVENTS="$TMP_DIR/parallel-dispatch.ndjson"
PARALLEL_STDERR="$TMP_DIR/parallel-dispatch.stderr"
PARALLEL_CHECKER="$TMP_DIR/check-parallel-dispatch.py"
mkdir -p "$PROBE_CWD" "$DEBUG_AGENT_DIR"

cat > "$ROUTING_CANONICAL" <<'EOF_ROUTING'
<!-- user:workflow-routing -->
<!-- workflow:anchor workflow.agents.secure-router:begin -->
## Secure workflow router (MANDATORY)

This global user-owned block is a lightweight entrypoint. Keep `/home/james/ai-workspace/workflow_optimisation/WORKFLOW.md` as the single task-class and route policy. On every new user task, before choosing a phase or specialist, call the native `skill({name:"workflow-route"})` tool and follow its classification; after a long-chat compaction/resume or meaningful scope change, load it again and reconcile the route. Read the current recipe with an authorized read-only tool when the skill requests it. The absence of `skill` or a required named Task tool blocks dependent mutation; do not substitute inline execution. A read-only response may explain the limitation.

Before any writer, establish explicit change intent, and check project registration using only the reviewed `host_register_project` path when required. The `gentle-orchestrator` is a read-only technical lead: no host Bash or project edit/write, no sandbox mutation/lifecycle authority. Every project mutation/execution goes to an authorized sandbox worker, including an upstream inline one-file fix. Do not weaken `grep: ask` or the host/sandbox permission overlays. Read-only requests have no writer or ODD tracker.

Use the router's selected adapters: `workflow-odd-secure` for authorized default ODD, and `workflow-systematic` when the route invokes its installed skills. The selected Systematic, frontend and review skills keep their named agent precedence. No file-count or risk threshold automatically selects SDD. For substantial ODD record route/trigger evidence and actual Task dispatch in the task file and complete Magic Context mirror before claiming progress; on long-chat resume read both. Any commit intended for native RDD must carry the staged reviewability receipt and obey the local per-commit line/byte cap defined by `workflow-odd-secure`; native Gentle AI START remains the final 200 KiB serialized-input authority. RDD defaults on when unset: read effective mode and deciding source per project; never toggle it automatically, and honor explicit off. Native review remains user-owned and separate. Fail closed when the requested specialist or safe tool surface is unavailable.

Before coding, honor the per-project/session local-vs-cloud writing-model choice already specified in the canonical recipe; never silently reuse an unknown decision. Astra is a user-selectable upgrade only for Sol-assigned non-implementation phases on extremely critical changes; recommend it with a concrete reason and never assign it to an implementation worker or edit global config to select it. The active model and plugin permissions remain in `opencode.json`.

Emit `ROUTE: <class> | intent: <read-only/authorized change> | route: <skill/phase> | specialist: <name> | basis: WORKFLOW.md`. A route line alone does not prove execution: verify loaded skill, named Task result and relevant checks. Keep user-facing terminal commands Fish-compatible.
<!-- workflow:anchor workflow.agents.secure-router:end -->
<!-- /user:workflow-routing -->
EOF_ROUTING

cat > "$PARALLEL_CHECKER" <<'PY_PARALLEL'
import json
import sys

path = sys.argv[1]
by_call = {}

with open(path, "r", encoding="utf-8", errors="replace") as fh:
    for raw in fh:
        raw = raw.strip()
        if not raw or not raw.startswith("{"):
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        part = event.get("part")
        if not isinstance(part, dict):
            continue
        if part.get("tool") != "task":
            continue

        state = part.get("state")
        if not isinstance(state, dict):
            continue

        inp = state.get("input")
        if not isinstance(inp, dict):
            inp = {}
        agent = inp.get("subagent_type")
        call_id = part.get("callID") or part.get("id") or f"anon:{len(by_call)}"
        rec = by_call.setdefault(call_id, {
            "agent": agent,
            "message": part.get("messageID"),
            "child": None,
            "start": None,
            "end": None,
            "statuses": set(),
        })
        if agent:
            rec["agent"] = agent
        if part.get("messageID"):
            rec["message"] = part.get("messageID")

        metadata = state.get("metadata")
        if isinstance(metadata, dict):
            rec["child"] = metadata.get("sessionId") or metadata.get("sessionID") or rec["child"]

        timing = state.get("time")
        if isinstance(timing, dict):
            start = timing.get("start")
            end = timing.get("end")
            if isinstance(start, (int, float)):
                rec["start"] = start if rec["start"] is None else min(rec["start"], start)
            if isinstance(end, (int, float)):
                rec["end"] = end if rec["end"] is None else max(rec["end"], end)

        status = state.get("status")
        if isinstance(status, str):
            rec["statuses"].add(status)
            stamp = event.get("timestamp")
            if isinstance(stamp, (int, float)):
                if status == "running":
                    rec["start"] = stamp if rec["start"] is None else min(rec["start"], stamp)
                elif status in {"completed", "error"}:
                    rec["end"] = stamp if rec["end"] is None else max(rec["end"], stamp)

wanted = {}
for rec in by_call.values():
    if rec["agent"] in {"explore", "general"}:
        wanted[rec["agent"]] = rec

missing = [name for name in ("explore", "general") if name not in wanted]
if missing:
    print("   !! PARALLEL_DISPATCH_MISSING: no Task call observed for " + ", ".join(missing))
    sys.exit(1)

a = wanted["explore"]
b = wanted["general"]

if not a["message"] or not b["message"] or a["message"] != b["message"]:
    print("   !! PARALLEL_DISPATCH_SERIALIZED: the two Task calls were not emitted from the same parent assistant message")
    print(f"      explore message={a['message']!r}; general message={b['message']!r}")
    sys.exit(1)

if a["child"] and b["child"] and a["child"] == b["child"]:
    print("   !! PARALLEL_DISPATCH_INVALID: both Task calls report the same child session")
    sys.exit(1)

timed = all(isinstance(x, (int, float)) for x in (a["start"], a["end"], b["start"], b["end"]))
if timed:
    overlaps = a["start"] < b["end"] and b["start"] < a["end"]
    if not overlaps:
        print("   !! PARALLEL_DISPATCH_SERIALIZED: Task execution intervals do not overlap")
        print(f"      explore={a['start']}..{a['end']}; general={b['start']}..{b['end']}")
        sys.exit(1)
    print("   ok: behavioural fan-out emitted both Task calls in one assistant message and execution intervals overlap")
else:
    print("   ok: behavioural fan-out emitted both independent Task calls in one assistant message")
    print("      note: this OpenCode JSON stream did not expose complete child timing metadata; same-message fan-out is the concurrency contract")

if a["child"] or b["child"]:
    print(f"      child sessions: explore={a['child'] or '<not surfaced>'}, general={b['child'] or '<not surfaced>'}")
PY_PARALLEL

