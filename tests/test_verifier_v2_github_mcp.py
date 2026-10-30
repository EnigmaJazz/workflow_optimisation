"""Verifier V2 mode (queue Q44): section 9b checks github_ro scoping in the V2 config and liveness on the V2 server."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "verify" / "checkers" / "v2-github-mcp-check.py"
SECTION = REPO / "verify" / "60-section-9a-9b-secure-service.sh"

GOOD_CONFIG = {
    "tools": {"github_ro_*": False},
    "mcp": {"github_ro": {"url": "https://api.githubcopilot.com/mcp/readonly", "headers": {"X-MCP-Readonly": "true"}}},
    "agent": {
        "gentle-orchestrator": {"tools": {"github_ro_*": True}, "permission": {"github_ro_*": "allow"}},
        "explore": {"tools": {"github_ro_*": True}, "permission": {"github_ro_*": "allow"}},
        "other": {"tools": {"github_ro_*": False}},
    },
}


class Server:
    """A fake V2 server: answers GET /api/mcp with a chosen body and records the auth header it saw."""

    def __init__(self, status="connected", listed=True, code=200):
        outer = self
        self.seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.seen.append((self.path, self.headers.get("Authorization"), self.headers.get("x-opencode-directory")))
                body = {"data": [{"name": "github_ro", "status": {"status": status}}] if listed else [{"name": "other", "status": {"status": "connected"}}]}
                self.send_response(code)
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def run(config, url, password="secret"):
    d = Path(tempfile.mkdtemp())
    (d / "opencode.json").write_text(json.dumps(config))
    pw = d / "password"
    if password is not None:
        pw.write_text(password + "\n")
    env = {**os.environ, "WORKFLOW_VERIFY_RETRY_DELAY": "0"}
    return subprocess.run([sys.executable, str(CHECKER), str(d / "opencode.json"), url, str(pw), "/work"], capture_output=True, text=True, env=env).stdout.strip()


class Checker(unittest.TestCase):
    def test_a_connected_scoped_github_ro_is_clean_and_authenticates_with_the_password(self):
        server = Server()
        try:
            out = run(GOOD_CONFIG, server.url)
        finally:
            server.close()
        self.assertTrue(out.startswith("clean\t"), out)
        path, auth, directory = server.seen[0]
        self.assertEqual(path, "/api/mcp")
        self.assertEqual(auth, "Basic b3BlbmNvZGU6c2VjcmV0")  # opencode:secret
        self.assertEqual(directory, "/work")

    def test_each_scoping_defect_is_an_error_before_the_server_is_asked(self):
        cases = []
        for mutate in (
            lambda c: c["mcp"]["github_ro"].update(url="https://api.githubcopilot.com/mcp/"),
            lambda c: c["mcp"]["github_ro"]["headers"].update({"X-MCP-Readonly": "false"}),
            lambda c: c["tools"].update({"github_ro_*": True}),
            lambda c: c["agent"]["explore"]["permission"].update({"github_ro_*": "ask"}),
            lambda c: c["agent"].pop("gentle-orchestrator"),
            lambda c: c["agent"]["other"]["tools"].update({"github_ro_*": True}),
        ):
            config = copy.deepcopy(GOOD_CONFIG)
            mutate(config)
            cases.append(config)
        server = Server()
        try:
            for config in cases:
                out = run(config, server.url)
                self.assertTrue(out.startswith("error\t"), out)
                self.assertNotIn("GITHUB_RO_NOT_CONNECTED", out)
        finally:
            server.close()
        self.assertEqual(server.seen, [])

    def test_a_server_that_does_not_list_or_connect_github_ro_is_an_error(self):
        for server in (Server(status="failed"), Server(listed=False)):
            try:
                out = run(GOOD_CONFIG, server.url)
            finally:
                server.close()
            self.assertTrue(out.startswith("error\tGITHUB_RO_NOT_CONNECTED"), out)
            self.assertEqual(len(server.seen), 3)  # three bounded attempts

    def test_a_server_that_is_down_or_a_missing_password_is_an_error(self):
        self.assertTrue(run(GOOD_CONFIG, "http://127.0.0.1:9").startswith("error\tGITHUB_RO_NOT_CONNECTED"))
        self.assertTrue(run(GOOD_CONFIG, "http://127.0.0.1:9", password=None).startswith("error\tcannot read the V2 server password"))

    def test_an_unreadable_config_is_an_error(self):
        out = subprocess.run([sys.executable, str(CHECKER), "/nonexistent.json", "http://127.0.0.1:9", "/nonexistent", "/work"], capture_output=True, text=True).stdout
        self.assertTrue(out.startswith("error\tcannot read the V2 config"))

    def test_the_real_generated_config_is_scoped_correctly(self):
        config = REPO / "global-config" / "opencode.json"
        data = json.loads(config.read_text())
        sys.path.insert(0, str(CHECKER.parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location("v2_github_mcp_check", CHECKER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIsNone(module.scoping_error(data))


class Wiring(unittest.TestCase):
    def test_section_9b_calls_the_checker_on_v2_and_keeps_the_v1_probe(self):
        text = SECTION.read_text()
        self.assertEqual(subprocess.run(["bash", "-n", str(SECTION)]).returncode, 0)
        v2, _, v1 = text.partition("# --- 9b.")[2].partition('elif [ "${OC_MAJOR:-0}" = "2" ]; then')[2].partition("\nelse\n")
        self.assertIn("v2-github-mcp-check.py", v2)
        self.assertIn("GITHUB_RO_RUNTIME_INACTIVE_OR_UNSCOPED", v2)
        self.assertIn("http://127.0.0.1:4096/mcp", v1)


if __name__ == "__main__":
    unittest.main()
