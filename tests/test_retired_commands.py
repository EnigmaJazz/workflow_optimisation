"""Durable checks for the Q67 retired-SDD-command detector.

Parses verify-workflow.sh and validates the ``retiredSddCommands`` denylist:
the array exists, is non-empty, contains no glob metacharacter, and every
expected retired command basename is present and non-empty. Also asserts the
``WORKFLOW_VERIFY_COMMANDS_DIR`` seam defaults to ``$OPENCODE_CONFIG_DIR/commands``
and the failure/success message shapes.

The four fixtures EXECUTE the block's real logic (extracted from the script,
including the seam line) against temporary override directories, proving the
override is honoured and there is no fallback to the real config root. A
PositiveControl class proves the validator AND the fixture harness themselves
can fail, so a green run is not vacuous.

Run: python3 -m unittest tests.test_retired_commands -v
"""

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "verify-workflow.sh"

EXPECTED = [
    "sdd-apply",
    "sdd-archive",
    "sdd-code",
    "sdd-continue",
    "sdd-explore",
    "sdd-ff",
    "sdd-init",
    "sdd-new",
    "sdd-onboard",
    "sdd-research",
    "sdd-status",
    "sdd-verify",
]

GLOB_METACHARS = ("*", "?", "[")

ARRAY_NAME = "retiredSddCommands"


def array_body(text, name):
    """Return the raw text inside NAME=( ... ) or None when the array is absent."""
    match = re.search(
        r"^" + re.escape(name) + r"=\((.*?)\)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def array_names(body):
    """Return each quoted element of an array body (glob rows included)."""
    return re.findall(r'"([^"]*)"', body)


def validate_commands(names, expected):
    """Shared structural validator; returns a list of error strings."""
    if names is None:
        return [f"{ARRAY_NAME} array not found"]
    errors = []
    if not names:
        errors.append(f"{ARRAY_NAME} array is empty")
    for name in names:
        if not name.strip():
            errors.append(f"empty command name in row {name!r}")
        if any(ch in name for ch in GLOB_METACHARS):
            errors.append(f"glob metacharacter in command row {name!r}")
    missing = [n for n in expected if n not in names]
    if missing:
        errors.append(f"missing expected retired command(s): {missing}")
    return errors


def extract_commands_block(text):
    """Return the top-level retiredSddCommands block (array through its closing fi)."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith(f"{ARRAY_NAME}=(")),
        None,
    )
    if start is None:
        return None
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j] == "fi"),
        None,
    )
    if end is None:
        return None
    return "\n".join(lines[start:end + 1])


def extract_seam(text):
    """Return the COMMANDS_DIR assignment line, which carries the override seam."""
    match = re.search(r"^COMMANDS_DIR=.*$", text, re.MULTILINE)
    return match.group(0) if match else None


def run_predicate(commands_dir, opencode_config_dir):
    """Execute the extracted seam + block under a stub fail(), return stdout.

    The snippet is assembled from the REAL script text, so the test cannot pass
    against a stale copy of the logic. ``WORKFLOW_VERIFY_COMMANDS_DIR`` and
    ``OPENCODE_CONFIG_DIR`` are injected as environment overrides.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    seam = extract_seam(text)
    block = extract_commands_block(text)
    if not seam or not block:
        raise AssertionError("could not extract the COMMANDS_DIR seam or block")
    snippet = "\n".join(
        [
            "set -u",
            'fail() { echo "FAIL:$1"; }',
            seam,
            block,
            "",
        ]
    )
    env = dict(os.environ)
    env["WORKFLOW_VERIFY_COMMANDS_DIR"] = commands_dir
    env["OPENCODE_CONFIG_DIR"] = opencode_config_dir
    proc = subprocess.run(
        ["bash", "-c", snippet],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout


class RealScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            raise AssertionError(f"{SCRIPT} missing")
        cls.text = SCRIPT.read_text(encoding="utf-8")

    def test_array_exists_nonempty_and_has_no_glob_row(self):
        body = array_body(self.text, ARRAY_NAME)
        self.assertIsNotNone(body, f"{ARRAY_NAME} array not found")
        names = array_names(body)
        self.assertEqual(len(names), len(EXPECTED), f"unexpected array size: {names}")
        for name in names:
            for ch in GLOB_METACHARS:
                self.assertNotIn(ch, name, f"glob metacharacter {ch!r} in row {name!r}")

    def test_every_expected_name_present_and_none_empty(self):
        body = array_body(self.text, ARRAY_NAME)
        names = array_names(body)
        self.assertEqual(validate_commands(names, EXPECTED), [])
        for name in names:
            self.assertTrue(name.strip(), f"empty command name in array: {names}")

    def test_commands_dir_seam_declared(self):
        self.assertIn("WORKFLOW_VERIFY_COMMANDS_DIR", self.text)
        match = re.search(
            r'^COMMANDS_DIR="\$\{WORKFLOW_VERIFY_COMMANDS_DIR:-\$OPENCODE_CONFIG_DIR/commands\}"$',
            self.text,
            re.MULTILINE,
        )
        self.assertIsNotNone(match, "COMMANDS_DIR default must be ${OPENCODE_CONFIG_DIR}/commands")

    def test_failure_and_success_message_shapes(self):
        self.assertIn("RETIRED_SDD_COMMAND_PRESENT", self.text)
        self.assertIn("$COMMANDS_DIR/$retired_cmd.md", self.text)
        self.assertIn("rm $COMMANDS_DIR/$retired_cmd.md", self.text)
        self.assertIn("no retired SDD commands present", self.text)


class ExtractedPredicate(unittest.TestCase):
    """Execute the real block logic against override directories."""

    def test_planted_command_in_override_fires(self):
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "override"
            override.mkdir()
            (override / "sdd-code.md").write_text("retired\n", encoding="utf-8")
            out = run_predicate(str(override), str(Path(tmp) / "decoy"))
        self.assertIn("RETIRED_SDD_COMMAND_PRESENT", out)
        self.assertIn("sdd-code.md", out)

    def test_empty_override_dir_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "override"
            override.mkdir()
            out = run_predicate(str(override), str(Path(tmp) / "decoy"))
        self.assertNotIn("RETIRED_SDD_COMMAND_PRESENT", out)
        self.assertIn("no retired SDD commands present", out)

    def test_override_honoured_over_decoy_config_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "override"
            override.mkdir()
            (override / "sdd-code.md").write_text("retired\n", encoding="utf-8")
            decoy = Path(tmp) / "decoy"
            (decoy / "commands").mkdir(parents=True)  # no matching file
            out = run_predicate(str(override), str(decoy))
        self.assertIn("RETIRED_SDD_COMMAND_PRESENT", out)
        self.assertIn(str(override / "sdd-code.md"), out)

    def test_no_fallback_to_real_config_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "override"
            override.mkdir()  # fresh empty override
            real = Path(tmp) / "real"
            (real / "commands").mkdir(parents=True)
            (real / "commands" / "sdd-code.md").write_text("retired\n", encoding="utf-8")
            out = run_predicate(str(override), str(real))
        self.assertNotIn("RETIRED_SDD_COMMAND_PRESENT", out)
        self.assertIn("no retired SDD commands present", out)


class PositiveControl(unittest.TestCase):
    """Prove the validator AND the fixture harness can fail; without these a
    green run proves nothing."""

    def test_glob_row_rejected(self):
        body = array_body('zzCommands=("sdd-apply" "sdd-*")', "zzCommands")
        errors = validate_commands(array_names(body), EXPECTED)
        self.assertTrue(errors)
        self.assertTrue(any("glob metacharacter" in e for e in errors), errors)

    def test_empty_name_rejected(self):
        body = array_body('zzCommands=("sdd-apply" "")', "zzCommands")
        errors = validate_commands(array_names(body), EXPECTED)
        self.assertTrue(any("empty command name" in e for e in errors), errors)

    def test_missing_expected_name_rejected(self):
        body = array_body('zzCommands=("sdd-apply")', "zzCommands")
        errors = validate_commands(array_names(body), EXPECTED)
        self.assertTrue(any("missing expected" in e for e in errors), errors)

    def test_empty_array_rejected(self):
        body = array_body("zzCommands=()", "zzCommands")
        errors = validate_commands(array_names(body), EXPECTED)
        self.assertTrue(any("array is empty" in e for e in errors), errors)

    def test_validator_accepts_a_good_list(self):
        self.assertEqual(validate_commands(list(EXPECTED), EXPECTED), [])

    def test_predicate_harness_can_observe_failure(self):
        # Positive control for run_predicate itself: a planted file MUST produce
        # the failure marker, so the negative fixtures above are meaningful.
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "override"
            override.mkdir()
            (override / "sdd-verify.md").write_text("retired\n", encoding="utf-8")
            out = run_predicate(str(override), str(Path(tmp) / "decoy"))
        self.assertIn("FAIL:RETIRED_SDD_COMMAND_PRESENT", out)


if __name__ == "__main__":
    unittest.main()
