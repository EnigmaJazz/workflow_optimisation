"""Pinned plugin set in global-config/ must be consistent and V1-safe (OpenCode V2 Phase A)."""
import json
import re
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "global-config"
SHARED = ("@fro.bot/systematic", "@cortexkit/opencode-magic-context", "@cortexkit/aft-opencode")


def split_spec(spec):
    m = re.fullmatch(r"(@[^@/]+/[^@]+|[^@/][^@]*)(?:@(.+))?", spec)
    return (m.group(1), m.group(2)) if m else (spec, None)


def registry_unpinned(entries):
    out = []
    for e in entries:
        if e.startswith(("/", ".", "~", "file:")):
            continue
        name, version = split_spec(e)
        if version is None or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            out.append(e)
    return out


def versions(entries):
    return {split_spec(e)[0]: split_spec(e)[1] for e in entries if not e.startswith(("/", ".", "~", "file:"))}


class PinTests(unittest.TestCase):
    def setUp(self):
        self.server = json.loads((CONFIG / "opencode.json").read_text())["plugin"]
        self.tui = json.loads((CONFIG / "tui.json").read_text())["plugin"]

    def test_detector_flags_unpinned_entry(self):
        # positive control: the detector can see an unversioned and a @latest entry
        self.assertEqual(registry_unpinned(["a-plugin", "@x/y@latest", "@x/z@1.2.3", "/abs/path.tsx"]),
                         ["a-plugin", "@x/y@latest"])

    def test_no_unpinned_registry_plugin_in_tui(self):
        self.assertEqual(registry_unpinned(self.tui), [])

    def test_statusline_stays_on_v1_line(self):
        self.assertEqual(versions(self.tui).get("opencode-subagent-statusline"), "1.3.1")

    def test_shared_pins_agree(self):
        s, t = versions(self.server), versions(self.tui)
        for name in SHARED:
            if name in t:
                self.assertEqual(t[name], s[name], name)

    def test_target_versions(self):
        s = versions(self.server)
        self.assertEqual(s["@fro.bot/systematic"], "3.27.0")
        self.assertEqual(s["@cortexkit/opencode-magic-context"], "0.49.28")
        self.assertEqual(s["@cortexkit/aft-opencode"], "0.62.0")

    def test_systematic_not_in_tui(self):
        self.assertNotIn("@fro.bot/systematic", versions(self.tui))

    def test_systematic_config_has_no_workflow_guard(self):
        text = (CONFIG / "systematic.jsonc").read_text()
        self.assertNotIn("workflow_guard", text)


if __name__ == "__main__":
    unittest.main()
