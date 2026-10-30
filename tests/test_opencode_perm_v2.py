"""Tests for the OpenCode V2 mode of ~/.local/bin/opencode-perm (the blocking-permission detector).

The script lives outside any repository, so these tests load it by path and skip when it is absent. V2 mode is opt-in
(OPENCODE_PERMISSION_API=v2): it polls V2's authenticated API per project directory instead of tailing the V1 log. A fake
V2 server stands in for the real one, and phone notifications are stubbed so a test can never send a real alert.
"""
import base64
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SCRIPT = Path.home() / ".local/bin/opencode-perm"
PASSWORD = "test-password"
DEFAULT_DIR = "/work/default"


class FakeV2(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), Handler)
        self.pending = {}  # directory -> list of permission requests
        self.sessions = {}  # id -> session
        self.replies = []  # (session id, request id, body)
        self.requests = []  # (method, path)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server_address[1]}"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self):
        expected = "Basic " + base64.b64encode(f"opencode:{PASSWORD}".encode()).decode()
        return self.headers.get("Authorization") == expected

    def do_GET(self):
        self.server.requests.append(("GET", self.path))
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            return self._send(404, {})
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        query = parse_qs(url.query)
        if url.path == "/api/permission/request":
            directory = (query.get("location[directory]") or [DEFAULT_DIR])[0]
            return self._send(200, {"location": {"directory": directory}, "data": self.server.pending.get(directory, [])})
        if url.path == "/api/session":
            return self._send(200, {"data": list(self.server.sessions.values()), "cursor": {}})
        if url.path.startswith("/api/session/"):
            session = self.server.sessions.get(url.path.rsplit("/", 1)[1])
            return self._send(200, {"data": session}) if session else self._send(404, {})
        return self._send(404, {})

    def do_POST(self):
        self.server.requests.append(("POST", self.path))
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        parts = urlparse(self.path).path.split("/")  # '', api, session, <sid>, permission, <rid>, reply
        if len(parts) == 7 and parts[4] == "permission" and parts[6] == "reply":
            self.server.replies.append((parts[3], parts[5], body))
            for items in self.server.pending.values():
                items[:] = [item for item in items if item["id"] != parts[5]]
            return self._send(200, {})
        return self._send(404, {})


def load_script(state_dir):
    os.environ["OPENCODE_PERMISSION_STATE_DIR"] = str(state_dir)
    loader = importlib.machinery.SourceFileLoader("opencode_perm_under_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def request(request_id="per_a", session="ses_1", action="edit"):
    return {"id": request_id, "sessionID": session, "action": action, "resources": ["src/a.ts"], "save": [], "metadata": {},
            "source": {"type": "tool", "messageID": "msg_1", "id": "tool_1"}, "message": "edit src/a.ts"}


def session(session_id="ses_1", directory="/work/proj", updated_ms=None):
    return {"id": session_id, "agent": "gentle-orchestrator", "model": {"id": "m", "providerID": "p"}, "title": "T",
            "time": {"created": 0, "updated": updated_ms if updated_ms is not None else int(time.time() * 1000)},
            "location": {"directory": directory}}


@unittest.skipUnless(SCRIPT.exists(), "opencode-perm is not installed")
class V2Mode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.mod = load_script(Path(cls.tmp.name) / "state")
        cls.password_file = Path(cls.tmp.name) / "server-password"
        cls.password_file.write_text(PASSWORD + "\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.server = FakeV2()
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        m = self.mod
        self.saved = {k: getattr(m, k, None) for k in ("V2_MODE", "SERVER", "PASSWORD_FILE", "OTHER_GRACE_SECONDS", "OTHER_QUIET_SECONDS", "run_phone_payload")}
        m.V2_MODE, m.SERVER, m.PASSWORD_FILE = True, self.server.url, self.password_file
        m.OTHER_GRACE_SECONDS = m.OTHER_QUIET_SECONDS = 0
        self.phone = []
        m.run_phone_payload = self.phone.append  # a test must never reach the real phone script
        m._api_cache.clear()
        m._v2_discovery.update(time=0, dirs=set())
        self.state = m.default_state()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        for key, value in self.saved.items():
            setattr(self.mod, key, value)

    def test_a_pending_request_becomes_a_tracked_permission(self):
        self.server.sessions["ses_1"] = session()
        self.server.pending[DEFAULT_DIR] = [request()]
        now = time.time()
        self.assertTrue(self.mod.sync_v2(self.state, now))
        entry = self.state["permissions"]["per_a"]
        self.assertEqual((entry["permission"], entry["patterns"], entry["session"], entry["status"]), ("edit", ["src/a.ts"], "ses_1", "pending"))
        self.assertEqual((entry["agent"], entry["title"], entry["directory"]), ("gentle-orchestrator", "T", DEFAULT_DIR))
        self.assertFalse(self.mod.sync_v2(self.state, now), "the same request must not be tracked twice")

    def test_requests_in_other_project_directories_are_found_through_the_session_list(self):
        # The API lists per location and answers the server's default location when none is given, so a request in a
        # project directory is invisible unless that directory is asked for. This was the live finding.
        self.server.sessions["ses_2"] = session("ses_2", "/work/proj")
        self.server.pending["/work/proj"] = [request("per_b", "ses_2")]
        self.assertTrue(self.mod.sync_v2(self.state, time.time()))
        self.assertEqual(self.state["permissions"]["per_b"]["directory"], "/work/proj")

    def test_the_password_is_sent_and_a_wrong_one_finds_nothing(self):
        self.server.sessions["ses_1"] = session()
        self.server.pending[DEFAULT_DIR] = [request()]
        Path(self.password_file).write_text("wrong\n")
        try:
            self.assertFalse(self.mod.sync_v2(self.state, time.time()))
            self.assertEqual(self.state["permissions"], {})
        finally:
            Path(self.password_file).write_text(PASSWORD + "\n")
        self.assertTrue(self.mod.sync_v2(self.state, time.time()))  # positive control: the right password works

    def test_session_activity_is_taken_from_the_session(self):
        long_ago = int((time.time() - 600) * 1000)
        self.server.sessions["ses_1"] = session(updated_ms=long_ago)
        self.server.pending[DEFAULT_DIR] = [request()]
        self.mod.sync_v2(self.state, time.time())
        self.assertAlmostEqual(self.state["sessions"]["ses_1"]["last_activity"], long_ago / 1000, delta=1)

    def test_an_unanswered_request_that_is_still_pending_is_reported_as_blocking(self):
        self.server.sessions["ses_1"] = session(updated_ms=int((time.time() - 600) * 1000))
        self.server.pending[DEFAULT_DIR] = [request()]
        self.mod.sync_v2(self.state, time.time() - 120)
        result = self.mod.evaluate_permission(self.state, "per_a", time.time())
        self.assertEqual(result["confidence"], "CONFIRMED PENDING")

    def test_a_request_answered_elsewhere_is_marked_resolved(self):
        self.server.sessions["ses_1"] = session()
        self.server.pending[DEFAULT_DIR] = [request()]
        self.mod.sync_v2(self.state, time.time() - 120)
        self.server.pending[DEFAULT_DIR] = []
        self.mod._api_cache.clear()
        self.assertIsNone(self.mod.evaluate_permission(self.state, "per_a", time.time()))
        self.assertEqual(self.state["permissions"]["per_a"]["status"], "resolved-elsewhere")

    def test_an_unreachable_server_is_not_an_error(self):
        self.mod.SERVER = "http://127.0.0.1:9"
        self.assertFalse(self.mod.sync_v2(self.state, time.time()))
        self.assertEqual(self.mod.fetch_pending("/work/proj"), ("unknown", None))

    def test_once_and_deny_reply_through_the_session_route(self):
        for command, decision, status in (("once", "once", "allowed-once"), ("reject", "reject", "denied")):
            self.server.sessions["ses_1"] = session()
            self.server.pending[DEFAULT_DIR] = [request("per_" + command)]
            self.mod.sync_v2(self.state, time.time())
            self.mod.save_state(self.state)
            self.mod.reply("per_" + command, command)
            self.assertEqual(self.server.replies[-1], ("ses_1", "per_" + command, {"decision": decision}))
            self.assertEqual(self.mod.load_state()["permissions"]["per_" + command]["status"], status)

    def test_a_reply_for_an_unknown_request_exits_without_calling_the_server(self):
        before = len(self.server.requests)
        with self.assertRaises(SystemExit):
            self.mod.reply("per_missing", "once")
        self.assertEqual(len(self.server.requests), before)

    def test_the_watch_loop_alerts_once_for_a_blocking_request(self):
        self.server.sessions["ses_1"] = session(updated_ms=int((time.time() - 600) * 1000))
        self.server.pending[DEFAULT_DIR] = [request()]
        self.mod.watch_v2(iterations=3, interval=0.01, state=self.state)
        self.assertTrue(self.state["permissions"]["per_a"]["alerted"])
        self.assertEqual(self.server.replies, [], "the detector must never answer a permission by itself")


@unittest.skipUnless(SCRIPT.exists(), "opencode-perm is not installed")
class V1Unchanged(unittest.TestCase):
    """V2 mode is opt-in: with it off the V1 log capture and the V1 permission route behave as before."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.mod = load_script(Path(cls.tmp.name) / "state")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_v2_mode_is_off_by_default(self):
        self.assertFalse(self.mod.V2_MODE)

    def test_the_state_directory_override_is_honoured(self):
        self.assertEqual(self.mod.STATE_DIR, Path(self.tmp.name) / "state")

    def test_a_v1_log_line_is_still_captured(self):
        state = self.mod.default_state()
        line = "timestamp=2026-10-30T05:44:43.017Z level=INFO run=4ec13045 message=asking id=per_v1abc permission=read"
        self.assertTrue(self.mod.capture_permission(state, line, time.time()))
        self.assertEqual(state["permissions"]["per_v1abc"]["permission"], "read")

    def test_v1_pending_lookup_uses_the_v1_route(self):
        server = FakeV2()
        threading.Thread(target=server.serve_forever, daemon=True).start()
        old = self.mod.SERVER
        self.mod.SERVER = server.url
        self.mod._api_cache.clear()
        try:
            self.mod.fetch_pending("/work/proj")
        finally:
            self.mod.SERVER = old
            server.shutdown()
            server.server_close()
        self.assertEqual(server.requests[0][1].split("?")[0], "/permission")


if __name__ == "__main__":
    unittest.main()
