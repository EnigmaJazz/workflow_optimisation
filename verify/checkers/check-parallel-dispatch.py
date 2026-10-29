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
