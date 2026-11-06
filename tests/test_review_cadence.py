"""Structural checks for the Q73 review-cadence anchors.

These checks prove only that the registered keystone prose is present in each
owning anchor block. They cannot prove the orchestrator acts on the rule.
"""

import re
import unittest
from pathlib import Path
try:
    from tests.verifier_source import verifier_text
except ImportError:  # run as a script from tests/
    from verifier_source import verifier_text

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "verify-workflow.sh"
EXPECTED = {
    "$WORKFLOW": "Close the open medium-risk slice before the next high-risk commit.",
    "$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md": (
        "Close the pending medium-risk slice before the next high-risk commit."
    ),
    "$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md": (
        "Close the accumulated medium-risk slice before the next high-risk commit."
    ),
}
SURFACES = {
    "$WORKFLOW": (REPO / "WORKFLOW.md", "workflow.work-unit-review"),
    "$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md": (
        REPO / "global-config/skills/workflow-odd-secure/references/odd-and-review.md",
        "workflow.odd-and-review.work-unit-review",
    ),
    "$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md": (
        REPO / "global-config/skills/workflow-route/references/session-decisions.md",
        "workflow.session-decisions.reviewability-budget",
    ),
}


def table_body(text):
    match = re.search(r"^ANCHOR_TOKENS=\(\n(.*?)^\)\n", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def cadence_rows(body):
    found = {}
    for line in body.splitlines():
        row = line.strip().strip("\\\"'")
        for file_field, (_, anchor) in SURFACES.items():
            prefix = f"{anchor}~{file_field}~"
            if row.startswith(prefix):
                fields = row.split("~", 3)
                if len(fields) == 4 and fields[3] == EXPECTED[file_field]:
                    found[file_field] = fields[3]
    return found


def anchor_interior(text, anchor):
    match = re.search(
        rf"<!-- workflow:anchor {re.escape(anchor)}:begin -->(.*?)<!-- workflow:anchor {re.escape(anchor)}:end -->",
        text,
        re.DOTALL,
    )
    return match.group(1) if match else None


def cadence_errors(contents, tokens):
    errors = []
    for file_field, (path, anchor) in SURFACES.items():
        token = tokens.get(file_field)
        if not token:
            errors.append(f"missing cadence token row for {file_field}")
            continue
        text = contents.get(file_field, path.read_text(encoding="utf-8"))
        interior = anchor_interior(text, anchor)
        if interior is None or token not in interior:
            errors.append(f"{file_field}: cadence keystone absent from {anchor}")
    return errors


class ReviewCadence(unittest.TestCase):
    def test_keystone_literals_are_pinned_in_each_owning_anchor(self):
        script = verifier_text()
        body = table_body(script)
        self.assertIsNotNone(body, "ANCHOR_TOKENS table not found")
        tokens = cadence_rows(body)
        self.assertEqual(set(tokens), set(SURFACES), "expected one cadence token row per prose surface")
        self.assertEqual(cadence_errors({}, tokens), [])


class PositiveControl(unittest.TestCase):
    def test_reworded_away_rule_is_rejected(self):
        script = verifier_text()
        tokens = cadence_rows(table_body(script))
        contents = {
            file_field: path.read_text(encoding="utf-8")
            for file_field, (path, _) in SURFACES.items()
        }
        file_field = "$WORKFLOW"
        token = tokens[file_field]
        contents[file_field] = contents[file_field].replace(token, "The next review may be considered later", 1)
        errors = cadence_errors(contents, tokens)
        self.assertTrue(errors, "rewriting the cadence keystone must fail the structural check")
        self.assertIn("cadence keystone absent", errors[0])


if __name__ == "__main__":
    unittest.main()
