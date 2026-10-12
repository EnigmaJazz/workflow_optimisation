"""Durable structural checks for the Q26 anchor manifest and token table.

Parses verify-workflow.sh and validates the ANCHOR_MANIFEST and ANCHOR_TOKENS
tables: every row has non-empty fields, every token row's anchor id exists in
the manifest, and the literal is the last (remainder) field. A positive control
proves the validator rejects a synthetic empty-token row and an unknown anchor,
so a clean result cannot be vacuous. Dependency-free and fast.

Run: python3 -m unittest tests/test_anchor_manifest.py -v
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "verify-workflow.sh"
SEP = "~"


def table_body(text, name):
    """Return the raw text inside NAME=( ... ) or None when the table is absent."""
    match = re.search(
        r"^" + re.escape(name) + r"=\(\n(.*?)^\)\n",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def rows(body):
    """Yield (index, row) for each non-comment, non-blank array element."""
    out = []
    for index, line in enumerate(body.splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'":
            stripped = stripped[1:-1]
        out.append((index, stripped))
    return out


def validate_rows(body, manifest_ids=None):
    """Shared structural validator; returns a list of error strings."""
    errors = []
    for index, row in rows(body):
        fields = row.split(SEP)
        if len(fields) < 4:
            errors.append(f"row {index}: expected at least 4 fields, got {len(fields)}: {row!r}")
            continue
        anchor_id, file_field, label = fields[0], fields[1], fields[2]
        # The literal is the LAST field: rejoin the remainder so a literal that
        # itself contained the separator would still be preserved intact.
        literal = SEP.join(fields[3:])
        for name, value in (("id", anchor_id), ("file", file_field),
                            ("label", label), ("literal", literal)):
            if not value.strip():
                errors.append(f"row {index}: empty {name} field in {row!r}")
        if manifest_ids is not None and anchor_id.strip() and anchor_id not in manifest_ids:
            errors.append(f"row {index}: anchor {anchor_id!r} is not registered in ANCHOR_MANIFEST")
    return errors


class RealTables(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), f"{SCRIPT} missing")
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_manifest_rows_have_non_empty_fields(self):
        body = table_body(self.text, "ANCHOR_MANIFEST")
        self.assertIsNotNone(body, "ANCHOR_MANIFEST table not found")
        self.assertGreater(len(rows(body)), 20, "manifest is unexpectedly small")
        self.assertEqual(validate_rows(body), [])

    def test_token_rows_have_non_empty_fields_and_known_anchors(self):
        manifest_body = table_body(self.text, "ANCHOR_MANIFEST")
        token_body = table_body(self.text, "ANCHOR_TOKENS")
        self.assertIsNotNone(manifest_body, "ANCHOR_MANIFEST table not found")
        self.assertIsNotNone(token_body, "ANCHOR_TOKENS table not found")
        manifest_ids = {row.split(SEP)[0] for _, row in rows(manifest_body)}
        self.assertNotIn("", manifest_ids)
        self.assertGreater(len(rows(token_body)), 50, "token table is unexpectedly small")
        self.assertEqual(validate_rows(token_body, manifest_ids), [])

    def test_every_manifest_anchor_is_unique(self):
        body = table_body(self.text, "ANCHOR_MANIFEST")
        ids = [row.split(SEP)[0] for _, row in rows(body)]
        self.assertEqual(sorted(ids), sorted(set(ids)), "duplicate anchor id in ANCHOR_MANIFEST")


class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    def test_empty_literal_token_row_is_rejected(self):
        manifest = '"a.anchor~$FILE~FILE~keystone"\n'
        self.assertEqual(validate_rows(manifest), [])
        token = '"a.anchor~$FILE~FILE~"\n'
        errors = validate_rows(token, {"a.anchor"})
        self.assertTrue(errors, "an empty-literal token row must be rejected")
        self.assertIn("empty literal", errors[0])

    def test_unknown_anchor_token_row_is_rejected(self):
        token = '"nope.anchor~$FILE~FILE~some literal"\n'
        errors = validate_rows(token, {"a.anchor"})
        self.assertTrue(errors, "an unknown-anchor token row must be rejected")
        self.assertIn("not registered", errors[0])

    def test_malformed_row_is_rejected(self):
        errors = validate_rows('"only~two"\n')
        self.assertTrue(errors)
        self.assertIn("at least 4 fields", errors[0])


if __name__ == "__main__":
    unittest.main()
