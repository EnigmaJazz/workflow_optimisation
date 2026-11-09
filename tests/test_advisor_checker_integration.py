"""Whole-checker integration coverage for the advisor dispatch boundary block.

tests/test_advisor_checker_policy.py exercises the extracted `advisor-model-policy`
function in isolation. That cannot catch a positive control asserting on a message
the surrounding rules can no longer emit, because those controls live outside the
marked block. These tests run the WHOLE runtime checker against the real
checked-in config and assert on its observable output instead.

The checker also expects a live OpenCode probe: an `agent list` dump plus one
`debug agent` JSON per agent. This harness supplies the structural inputs only (a
synthetic agent list and an empty probe directory), so the runtime-probe
assertions fail closed as RUNTIME_AGENT_PROBE_MISSING. That is irrelevant here:
the ADVISOR_* block reads configuration only, and its own success line proves the
block ran and found nothing.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "verify/checkers/check-runtime-agents.cjs"
OPENCODE = ROOT / "global-config/opencode.json"
SYSTEMATIC = ROOT / "global-config/systematic.jsonc"
FALLBACK = ROOT / "global-config/rate-limit-fallback.json"

ADVISOR_OK = "ok: advisor model, seat isolation, dispatch boundaries and no-fallback policy"
RELAY_AGENTS = (
    "asi-review-risk",
    "asi-review-resilience",
    "asi-review-readability",
    "asi-review-reliability",
    "asi-review-refuter",
    "asi-review-validator",
)


def jsonc_node_modules():
    """A node_modules directory that resolves the checker's jsonc-parser import."""
    candidates = []
    configured = os.environ.get("SYSTEMATIC_NODE_MODULES")
    if configured:
        candidates.append(Path(configured))
    home = Path.home()
    for root in (home / ".cache/opencode", home / ".local/share/opencode-v2/cache/opencode/npm"):
        if not root.is_dir():
            continue
        candidates.append(root / "node_modules")
        for pattern in (
            "packages/*/node_modules",
            "*/node_modules",
            "*/*/node_modules",
            "*/*/*/node_modules",
        ):
            candidates.extend(sorted(root.glob(pattern)))
    for candidate in candidates:
        if (candidate / "jsonc-parser" / "package.json").is_file():
            return candidate
    return None


class AdvisorCheckerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = shutil.which("node") or shutil.which("bun")
        if cls.runtime is None:
            raise unittest.SkipTest("no JavaScript runtime found (node or bun)")
        cls.node_modules = jsonc_node_modules()
        if cls.node_modules is None:
            raise unittest.SkipTest(
                "no node_modules directory resolves jsonc-parser; set SYSTEMATIC_NODE_MODULES"
            )
        cls.deployed = json.loads(OPENCODE.read_text(encoding="utf-8"))

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="advisor-checker-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "agents-root").mkdir()
        (self.tmp / "debug").mkdir()
        names = list(self.deployed["agent"]) + list(RELAY_AGENTS)
        (self.tmp / "agents.txt").write_text(
            "".join(f"{name} (subagent)\n" for name in names), encoding="utf-8"
        )

    def run_checker(self, opencode_config):
        env = dict(os.environ)
        env["SYSTEMATIC_NODE_MODULES"] = str(self.node_modules)
        return subprocess.run(
            [
                self.runtime,
                str(CHECKER),
                str(SYSTEMATIC),
                str(self.tmp / "agents-root"),
                str(self.tmp / "agents.txt"),
                str(self.tmp / "debug"),
                str(opencode_config),
                str(FALLBACK),
                str(ROOT),
            ],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def advisor_failures(self, result):
        return [line for line in result.stderr.splitlines() if "!! ADVISOR_" in line]

    def test_whole_checker_reports_no_advisor_failure(self):
        result = self.run_checker(OPENCODE)
        self.assertEqual(self.advisor_failures(result), [], result.stderr)
        # The success line proves the block ran; a crash before it cannot pass.
        self.assertIn(ADVISOR_OK, result.stdout, result.stderr)

    def test_whole_checker_rejects_a_real_unlisted_evidence_dispatcher(self):
        deployed = json.loads(json.dumps(self.deployed))
        general = deployed["agent"]["general"]
        general.setdefault("permission", {})["task"] = {
            "*": "deny",
            "advisor-evidence": "allow",
        }
        mutated = self.tmp / "opencode-unlisted-dispatcher.json"
        mutated.write_text(json.dumps(deployed), encoding="utf-8")
        result = self.run_checker(mutated)
        self.assertIn('ADVISOR_EVIDENCE_DISPATCH_NOT_DENIED: general="allow"', result.stderr)
        self.assertNotIn(ADVISOR_OK, result.stdout, result.stderr)
        self.assertNotIn("ADVISOR_EVIDENCE_DISPATCH_POSITIVE_CONTROL_FAILED", result.stderr)


if __name__ == "__main__":
    unittest.main()
