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


def fake_jwt(payload_claims):
    def b64url(obj):
        raw = json.dumps(obj).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return f"{b64url({'alg': 'none'})}.{b64url(payload_claims)}.sig"


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


class TestCredentials(unittest.TestCase):
    def test_extracts_token_and_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = {
                "openai": {
                    "access": fake_jwt(
                        {
                            "https://api.openai.com/auth": {
                                "chatgpt_account_id": "acct-123",
                            }
                        }
                    )
                }
            }
            path = os.path.join(tmp, "auth.json")
            with open(path, "w") as fh:
                json.dump(auth, fh)
            tok, acct = bridge._openai_credentials.__wrapped__(path) \
                if hasattr(bridge._openai_credentials, "__wrapped__") \
                else (None, None)
            # simpler: monkeypatch module AUTH_FILE
            old = bridge.AUTH_FILE
            bridge.AUTH_FILE = path
            try:
                tok, acct = bridge._openai_credentials()
            finally:
                bridge.AUTH_FILE = old
            self.assertTrue(tok.startswith("ey"))
            self.assertEqual(acct, "acct-123")

    def test_missing_file_returns_none(self):
        old = bridge.AUTH_FILE
        bridge.AUTH_FILE = "/nonexistent/auth.json"
        try:
            self.assertEqual(bridge._openai_credentials(), (None, None))
        finally:
            bridge.AUTH_FILE = old

    def test_non_jwt_token_no_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "auth.json")
            with open(path, "w") as fh:
                json.dump({"openai": {"access": "plain-token"}}, fh)
            old = bridge.AUTH_FILE
            bridge.AUTH_FILE = path
            try:
                tok, acct = bridge._openai_credentials()
            finally:
                bridge.AUTH_FILE = old
            self.assertEqual(tok, "plain-token")
            self.assertIsNone(acct)


class TestMime(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(bridge._mime_for("a.png"), "image/png")
        self.assertEqual(bridge._mime_for("a.jpg"), "image/jpeg")
        self.assertEqual(bridge._mime_for("a.webp"), "image/webp")

    def test_unknown_falls_back_to_png(self):
        self.assertEqual(bridge._mime_for("a.bin"), "image/png")


class TestPayloadShapes(unittest.TestCase):
    """Each leg must use the format its backend accepts (critical regression)."""

    def _capture(self, backend_fn):
        captured = {}

        def fake_post(url, headers, payload):
            captured["url"] = url
            captured["payload"] = payload
            return None, "boom"

        old = bridge._post
        bridge._post = fake_post
        try:
            backend_fn("BASE64DATA", "image/jpeg", "Q?")
        finally:
            bridge._post = old
        return captured

    def test_luna_proxy_leg_uses_image_media_format(self):
        c = self._capture(bridge._backend_luna_proxy)
        part = c["payload"]["messages"][0]["content"][1]
        self.assertEqual(part["type"], "image")
        self.assertEqual(part["media"]["type"], "image/jpeg")
        self.assertEqual(part["media"]["data"], "BASE64DATA")
        self.assertIn("8788", c["url"])

    def test_openai_leg_uses_image_url_format(self):
        old = bridge._openai_credentials
        bridge._openai_credentials = lambda: ("tok", None)
        try:
            c = self._capture(bridge._backend_luna_openai)
        finally:
            bridge._openai_credentials = old
        part = c["payload"]["messages"][0]["content"][1]
        self.assertEqual(part["type"], "image_url")
        self.assertTrue(part["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertIn("api.openai.com", c["url"])

    def test_qwen_leg_uses_image_url_format(self):
        c = self._capture(bridge._backend_qwen_proxy)
        part = c["payload"]["messages"][0]["content"][1]
        self.assertEqual(part["type"], "image_url")
        self.assertIn("8788", c["url"])

    def test_openai_leg_skipped_without_token(self):
        old = bridge._openai_credentials
        bridge._openai_credentials = lambda: (None, None)
        try:
            body, err = bridge._backend_luna_openai("DATA", "image/png", "Q")
        finally:
            bridge._openai_credentials = old
        self.assertIsNone(body)
        self.assertIn("no openai token", err)


class TestVisionRefusal(unittest.TestCase):
    def test_recognizes_common_refusals(self):
        for text in [
            "Please upload the image so I can read it.",
            "I cannot see the image you attached.",
            "No image was provided with your message.",
            "I can't see any photo in this conversation.",
            "Sorry, I couldn't see the picture.",
        ]:
            self.assertTrue(bridge._is_vision_refusal(text), text)

    def test_legit_answers_not_marked(self):
        for text in [
            "The image shows a fish pie recipe. Ingredients: potatoes, fish.",
            "I can't see the exact quantity of salt clearly, but the list is:",
            "No image editing was applied.",
        ]:
            self.assertFalse(bridge._is_vision_refusal(text), text)

    def test_refusal_falls_through_chain(self):
        old = bridge.BACKENDS
        bridge.BACKENDS = [
            ("a", lambda i, m, q: (
                {"choices": [{"message": {"content": "Please upload the image."}}]},
                None,
            )),
            ("b", lambda i, m, q: (
                {"choices": [{"message": {"content": "Potatoes, fish"}}]},
                None,
            )),
        ]
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(b"fake")
            tmp.close()
            try:
                out = bridge._describe(tmp.name, "Q")
            finally:
                os.unlink(tmp.name)
        finally:
            bridge.BACKENDS = old
        self.assertEqual(out, "Potatoes, fish")


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
