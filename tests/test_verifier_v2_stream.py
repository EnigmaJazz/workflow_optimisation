"""Verifier V2 mode (queue Q44): section 10's stream parsers accept the V2 tool-part shape and fail loudly when blind.

Observed: V2's stored tool parts are {"type": "tool", "name", "state": {"input", ...}} (GET /api/session/.../message), and
`run --format json` events carry top-level type/timestamp/sessionID. The tool-event shape of that stream itself was NOT observed
(the probe could not reach a provider), so the parsers accept both the V1 wrapper and the bare V2 part, and refuse to pass on V2
when they recognise no tool event at all."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SECTION = (REPO / "verify" / "61-section-10-behavioural.sh").read_text()
PARALLEL = REPO / "verify" / "checkers" / "check-parallel-dispatch.py"
ODD = re.search(r"<<'PY_ODD_READONLY'\n(.*?)\nPY_ODD_READONLY", SECTION, re.S).group(1)


def run_odd(events, major="2", tracker=False):
    d = Path(tempfile.mkdtemp())
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    if tracker:
        (d / "odd" / "tasks").mkdir(parents=True)
    proc = subprocess.run([sys.executable, "-c", ODD, str(d / "events.jsonl"), str(d)], capture_output=True, text=True, env={**os.environ, "OC_MAJOR": major})
    return proc.returncode, proc.stdout


def v1_tool(tool, **inp):
    return {"type": "tool_use", "part": {"tool": tool, "state": {"input": inp}}}


def v2_tool(tool, **inp):
    return {"type": "tool", "id": "call_1", "name": tool, "state": {"status": "completed", "input": inp}}


ROUTE = [("skill", {"name": "workflow-route"}), ("skill", {"name": "workflow-odd-secure"})]


class OddParser(unittest.TestCase):
    def test_the_v1_shape_is_unchanged(self):
        code, out = run_odd([v1_tool(t, **i) for t, i in ROUTE], major="1")
        self.assertEqual(code, 0, out)
        self.assertIn("launched no writer", out)

    def test_the_bare_v2_tool_part_is_recognised(self):
        code, out = run_odd([v2_tool(t, **i) for t, i in ROUTE])
        self.assertEqual(code, 0, out)

    def test_a_v2_part_wrapped_like_v1_is_recognised_too(self):
        code, out = run_odd([{"type": "tool_use", "part": v2_tool(t, **i)} for t, i in ROUTE])
        self.assertEqual(code, 0, out)

    def test_a_mutating_tool_is_caught_in_both_shapes(self):
        for event in (v1_tool("sandbox_write", path="x"), v2_tool("sandbox_write", path="x")):
            code, out = run_odd([event] + [v2_tool(t, **i) for t, i in ROUTE])
            self.assertEqual(code, 1, out)
            self.assertIn("ODD_READ_ONLY_MUTATION_OR_WRITER", out)

    def test_on_v2_a_stream_with_no_recognisable_tool_event_fails_loudly_never_passes(self):
        stream = [{"type": "text", "timestamp": 1, "sessionID": "s", "text": "hi"}, {"type": "step_finish", "sessionID": "s"}]
        code, out = run_odd(stream, major="2")
        self.assertEqual(code, 1)
        self.assertIn("ODD_V2_STREAM_UNRECOGNISED", out)
        code, out = run_odd([], major="2")
        self.assertIn("ODD_V2_STREAM_UNRECOGNISED", out)

    def test_on_v1_an_empty_stream_keeps_its_old_failure(self):
        code, out = run_odd([], major="1")
        self.assertEqual(code, 1)
        self.assertIn("ODD_ROUTER_SKILL_NOT_LOADED", out)

    def test_the_route_order_and_tracker_checks_still_apply_on_v2(self):
        code, out = run_odd([v2_tool("skill", name="workflow-odd-secure"), v2_tool("skill", name="workflow-route")])
        self.assertIn("ODD_ROUTE_SKILL_ORDER", out)
        code, out = run_odd([v2_tool(t, **i) for t, i in ROUTE], tracker=True)
        self.assertIn("ODD_READ_ONLY_TRACKER_CREATED", out)


class ParallelDispatch(unittest.TestCase):
    def run_checker(self, events):
        path = Path(tempfile.mkdtemp()) / "e.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        proc = subprocess.run([sys.executable, str(PARALLEL), str(path)], capture_output=True, text=True)
        return proc.returncode, proc.stdout

    def dispatch(self, agent, call, message="m1"):
        part = {"type": "tool", "id": call, "callID": call, "messageID": message, "name": "subagent",
                "state": {"status": "completed", "input": {"agent": agent}, "time": {"start": 10, "end": 20}}}
        return part

    def test_two_v2_subagent_parts_in_one_message_pass_in_both_wrappers(self):
        for wrap in (lambda p: p, lambda p: {"type": "tool_use", "part": p}):
            code, out = self.run_checker([wrap(self.dispatch("explore", "a")), wrap(self.dispatch("general", "b"))])
            self.assertEqual(code, 0, out)

    def test_serialised_dispatches_still_fail_on_v2(self):
        code, out = self.run_checker([self.dispatch("explore", "a", "m1"), self.dispatch("general", "b", "m2")])
        self.assertEqual(code, 1)
        self.assertIn("PARALLEL_DISPATCH_SERIALIZED", out)

    def test_a_stream_with_no_dispatch_still_fails(self):
        code, out = self.run_checker([{"type": "text", "text": "hi"}])
        self.assertEqual(code, 1)
        self.assertIn("PARALLEL_DISPATCH_MISSING", out)


if __name__ == "__main__":
    unittest.main()
