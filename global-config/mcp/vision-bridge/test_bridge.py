#!/usr/bin/env python3
"""Vision bridge smoke test suite.

Usage:
  python3 test_bridge.py           # unit + protocol tests (fast, no network)
  python3 test_bridge.py --live    # + live backend chain tests (slow, network)

Unit tests monkeypatch network calls; protocol tests spawn the server over
stdio JSON-RPC with a no-network request; live tests hit the real backends
(luna via proxy up to ~120s per leg).
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server as bridge  # noqa: E402


# ---------------------------------------------------------------- unit tests

class TestContentOf(unittest.TestCase):
    def test_valid_content(self):
        self.assertEqual(
            bridge._content_of({"choices": [{"message": {"content": "Red"}}]}),
            "Red",
        )

    def test_null_content_is_fallback_trigger(self):
        self.assertIsNone(
            bridge._content_of({"choices": [{"message": {"content": None}}]})
        )

    def test_empty_string_is_fallback_trigger(self):
        self.assertIsNone(
            bridge._content_of({"choices": [{"message": {"content": "   "}}]})
        )

    def test_missing_choices_is_fallback_trigger(self):
        self.assertIsNone(bridge._content_of({"error": {"message": "boom"}}))


class TestFallbackModel(unittest.TestCase):
    def test_the_fallback_is_qwen3_8_flash(self):
        self.assertEqual(bridge.FALLBACK_MODEL, "qwen3.8-flash")
        self.assertEqual([name for name, _ in bridge.BACKENDS][1], "qwen3.8-flash via opencode-go")


class TestMime(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(bridge._mime_for("a.png"), "image/png")
        self.assertEqual(bridge._mime_for("a.jpg"), "image/jpeg")
        self.assertEqual(bridge._mime_for("a.webp"), "image/webp")

    def test_unknown_falls_back_to_png(self):
        self.assertEqual(bridge._mime_for("a.bin"), "image/png")

    def test_a_sandbox_that_denies_the_system_mime_database_does_not_break_the_lookup(self):
        # Positive control: with this patch the bare stdlib call really raises, as it does under the nono profile
        # (it cannot read /etc/mime.types). The bridge must not depend on that file for the image types it accepts.
        def denied(*_args, **_kwargs):
            raise PermissionError(13, "Permission denied", "/etc/mime.types")

        original = bridge.mimetypes.guess_type
        bridge.mimetypes.guess_type = denied
        try:
            with self.assertRaises(PermissionError):
                bridge.mimetypes.guess_type("a.png")
            self.assertEqual(bridge._mime_for("a.PNG"), "image/png")
            self.assertEqual(bridge._mime_for("a.jpeg"), "image/jpeg")
            self.assertEqual(bridge._mime_for("a.webp"), "image/webp")
            self.assertEqual(bridge._mime_for("a.gif"), "image/gif")
            self.assertEqual(bridge._mime_for("a.unknown"), "image/png")
        finally:
            bridge.mimetypes.guess_type = original


class TestPayloadShapes(unittest.TestCase):
    """Each leg must use the format its backend accepts (critical regression)."""

    def _capture(self, backend_fn):
        captured = {}

        def fake_post(url, headers, payload):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = payload
            return None, "boom"

        old = bridge._post
        bridge._post = fake_post
        try:
            backend_fn("BASE64DATA", "image/jpeg", "Q?")
        finally:
            bridge._post = old
        return captured

    def test_luna_proxy_leg_uses_image_url_format(self):
        # gpt-6-luna through the proxy accepts image_url and rejects the older image+media shape (observed 2026-10-30).
        c = self._capture(bridge._backend_luna_proxy)
        part = c["payload"]["messages"][0]["content"][1]
        self.assertEqual(part["type"], "image_url")
        self.assertEqual(part["image_url"]["url"], "data:image/jpeg;base64,BASE64DATA")
        self.assertIn("8788", c["url"])

    def test_proxy_legs_carry_a_session_header_the_proxy_routes_on(self):
        for leg in (bridge._backend_luna_proxy, bridge._backend_qwen_proxy):
            self.assertTrue(self._capture(leg)["headers"]["x-opencode-session"].startswith("vision-bridge-"))

    def test_qwen_leg_uses_image_url_format(self):
        c = self._capture(bridge._backend_qwen_proxy)
        part = c["payload"]["messages"][0]["content"][1]
        self.assertEqual(part["type"], "image_url")
        self.assertIn("8788", c["url"])

    def test_proxy_legs_send_the_pool_key_when_it_is_in_the_environment(self):
        saved = {k: os.environ.pop(k, None) for k in ("VISION_BRIDGE_PROXY_KEY", "POOL_PROXY_KEY")}
        try:
            for leg in (bridge._backend_luna_proxy, bridge._backend_qwen_proxy):
                self.assertNotIn("Authorization", self._capture(leg)["headers"])  # positive control: absent without the key
            os.environ["POOL_PROXY_KEY"] = "pool-key"
            for leg in (bridge._backend_luna_proxy, bridge._backend_qwen_proxy):
                self.assertEqual(self._capture(leg)["headers"]["Authorization"], "Bearer pool-key")
            os.environ["VISION_BRIDGE_PROXY_KEY"] = "bridge-key"  # the bridge-specific variable wins
            self.assertEqual(self._capture(bridge._backend_luna_proxy)["headers"]["Authorization"], "Bearer bridge-key")
        finally:
            for k in ("VISION_BRIDGE_PROXY_KEY", "POOL_PROXY_KEY"):
                os.environ.pop(k, None)
                if saved[k] is not None:
                    os.environ[k] = saved[k]

    def test_the_default_model_is_gpt_6_luna_and_there_is_no_direct_openai_leg(self):
        self.assertEqual(self._capture(bridge._backend_luna_proxy)["payload"]["model"], "gpt-6-luna")
        self.assertEqual([name for name, _ in bridge.BACKENDS], ["gpt-6-luna via opencode-go", "qwen3.8-flash via opencode-go"])

class TestChainSelection(unittest.TestCase):
    """First non-empty answer wins; errors/empties fall through; all-fail aggregates."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        self.tmp.write(b"fake-image-bytes")
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _run(self, backends):
        old = bridge.BACKENDS
        bridge.BACKENDS = backends
        try:
            return bridge._describe(self.tmp.name, "Q")
        finally:
            bridge.BACKENDS = old

    def test_first_answer_wins(self):
        out = self._run([
            ("a", lambda i, m, q: ({"choices": [{"message": {"content": "A"}}]}, None)),
            ("b", lambda i, m, q: ({"choices": [{"message": {"content": "B"}}]}, None)),
        ])
        self.assertEqual(out, "A")

    def test_error_falls_through(self):
        out = self._run([
            ("a", lambda i, m, q: (None, "HTTP 500: boom")),
            ("b", lambda i, m, q: ({"choices": [{"message": {"content": "B"}}]}, None)),
        ])
        self.assertEqual(out, "B")

    def test_empty_content_falls_through(self):
        out = self._run([
            ("a", lambda i, m, q: ({"choices": [{"message": {"content": None}}]}, None)),
            ("b", lambda i, m, q: ({"choices": [{"message": {"content": "B"}}]}, None)),
        ])
        self.assertEqual(out, "B")

    def test_all_fail_aggregates(self):
        out = self._run([
            ("a", lambda i, m, q: (None, "HTTP 500")),
            ("b", lambda i, m, q: ({"choices": []}, None)),
            ("c", lambda i, m, q: (None, "transport: timeout")),
        ])
        self.assertIn("All vision backends failed", out)
        self.assertIn("HTTP 500", out)
        self.assertIn("empty response", out)
        self.assertIn("transport: timeout", out)


# ------------------------------------------------------------- protocol tests

class TestJsonRpcProtocol(unittest.TestCase):
    """Server over stdio JSON-RPC: initialize, tools/list, no-network call."""

    def _rpc(self, msg, env=None):
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "server.py")],
            input=json.dumps(msg) + "\n",
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        return json.loads(lines[-1]) if lines else {}

    def test_initialize(self):
        resp = self._rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(resp["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(resp["result"]["serverInfo"]["name"], "vision-bridge")

    def test_tools_list(self):
        resp = self._rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "describe_image")
        self.assertIn("path", tools[0]["inputSchema"]["properties"])

    def test_call_missing_file_no_network(self):
        resp = self._rpc({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "describe_image",
                       "arguments": {"path": "/nonexistent/img.png"}},
        })
        text = resp["result"]["content"][0]["text"]
        self.assertIn("Image not found", text)

    def test_unknown_tool(self):
        resp = self._rpc({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "nope", "arguments": {}},
        })
        self.assertTrue(resp["result"]["isError"])


# ----------------------------------------------------------------- live tests

@unittest.skipUnless("--live" in sys.argv, "add --live for backend tests")
class TestLiveBackends(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images = {}
        cls.tmpdir = tempfile.mkdtemp(prefix="vision-bridge-test-")
        for color, name in [("red", "red"), ("green", "green")]:
            path = os.path.join(cls.tmpdir, f"{name}.jpg")
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color={color}:s=640x480",
                 "-frames:v", "1", path],
                capture_output=True,
                check=True,
            )
            cls.images[name] = path

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_qwen_leg_says_red(self):
        body, err = bridge._backend_qwen_proxy(
            base64.b64encode(open(self.images["red"], "rb").read()).decode(),
            "image/jpeg", "What color is this image? Reply with one word.",
        )
        self.assertIsNone(err, err)
        content = bridge._content_of(body)
        self.assertIsNotNone(content, "qwen leg returned empty")
        self.assertIn("red", content.lower())

    def test_full_chain_returns_nonempty(self):
        text = bridge._describe(self.images["red"],
                                "What color is this image? Reply with one word.")
        self.assertNotIn("All vision backends failed", text)
        self.assertTrue(text.strip())

    def test_forced_fallback_reaches_qwen(self):
        old = bridge.PROXY_MODEL
        bridge.PROXY_MODEL = "nonexistent-model"
        try:
            text = bridge._describe(self.images["red"],
                                    "What color is this image? Reply with one word.")
        finally:
            bridge.PROXY_MODEL = old
        self.assertIn("red", text.lower())


if __name__ == "__main__":
    unittest.main(argv=[a for a in sys.argv if a != "--live"])
