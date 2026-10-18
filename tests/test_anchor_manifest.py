"""Durable structural checks for the Q26 anchor manifest and token table.

Parses verify-workflow.sh and validates the ANCHOR_MANIFEST and ANCHOR_TOKENS
tables: every row has non-empty fields, every token row's anchor id exists in
the manifest, and the literal is the last (remainder) field. ANCHOR_MANIFEST
holds exactly one structural row per anchor, so its ids are unique.
ANCHOR_TOKENS repeats an anchor id, one row per contractual literal, so its ids
are intentionally NOT unique. A positive control proves the validator rejects a
synthetic empty-token row, an unknown anchor, or a duplicated manifest id.

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


def duplicate_manifest_ids(body):
    """Anchor ids appearing more than once in a manifest body; [] when unique."""
    ids = [row.split(SEP)[0] for _, row in rows(body)]
    return sorted({i for i in ids if ids.count(i) > 1})


def validate_manifest_keystones(body):
    """Reject a manifest row whose keystone repeats its own anchor id."""
    errors = []
    for index, row in rows(body):
        fields = row.split(SEP)
        if len(fields) < 4:
            continue
        anchor_id, keystone = fields[0], SEP.join(fields[3:])
        if anchor_id == keystone:
            errors.append(f"row {index}: keystone repeats anchor id {anchor_id!r}")
    return errors


class RealTables(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), f"{SCRIPT} missing")
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_manifest_keystones_are_not_self_referential(self):
        body = table_body(self.text, "ANCHOR_MANIFEST")
        self.assertIsNotNone(body, "ANCHOR_MANIFEST table not found")
        self.assertEqual(validate_manifest_keystones(body), [])

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

    def test_mirror_sha256_token_is_literal_and_non_vacuous(self):
        import subprocess
        import tempfile

        token_body = table_body(self.text, "ANCHOR_TOKENS")
        self.assertIsNotNone(token_body, "ANCHOR_TOKENS table not found")
        row = next(
            line.strip()
            for line in token_body.splitlines()
            if "mirror_sha256" in line
        )
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "command-substitution-ran"
            script = f'''set -eu
WORKSPACE={str(REPO)!r}
marker={str(marker)!r}
mirror_sha256() {{ printf invoked > "$marker"; }}
ANCHOR_TOKENS=(
  {row}
)
IFS='~' read -r _ _ _ token_literal <<< "${{ANCHOR_TOKENS[0]}}"
expected='`mirror_sha256` is optional and must be absent'
[ "$token_literal" = "$expected" ] || {{ printf 'LITERAL_MISMATCH:%s\\n' "$token_literal"; exit 10; }}
compare_token() {{ printf '%s\\n' "$1" | grep -Fq -- "$token_literal"; }}
compare_token "$expected" || exit 11
removed=${{expected//mirror_sha256/}}
if compare_token "$removed"; then
  printf 'REMOVAL_NOT_DETECTED\\n'
  exit 12
fi
[ ! -e "$marker" ] || {{ printf 'COMMAND_SUBSTITUTION_OCCURRED\\n'; exit 13; }}
printf 'LITERAL_PRESERVED; PRESENT=PASS; REMOVED=FAIL; COMMAND_SUBSTITUTION=NONE\\n'
'''
            result = subprocess.run(
                ["bash", "-c", script], cwd=REPO, capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "LITERAL_PRESERVED; PRESENT=PASS; REMOVED=FAIL; COMMAND_SUBSTITUTION=NONE",
            result.stdout,
        )

    def test_every_manifest_anchor_is_unique(self):
        body = table_body(self.text, "ANCHOR_MANIFEST")
        self.assertEqual(duplicate_manifest_ids(body), [], "duplicate anchor id in ANCHOR_MANIFEST")

    def test_extracted_verifier_loops_pass_against_real_files(self):
        import subprocess

        def extract_function(name):
            start = self.text.index(f"{name}() {{")
            end = self.text.index("\n}\n", start) + 2
            return self.text[start:end]

        manifest = table_body(self.text, "ANCHOR_MANIFEST")
        token_table = table_body(self.text, "ANCHOR_TOKENS")
        self.assertIsNotNone(manifest, "ANCHOR_MANIFEST table not found")
        self.assertIsNotNone(token_table, "ANCHOR_TOKENS table not found")
        root = str(REPO)
        script = f'''set -u
WORKSPACE="{root}"
WORKFLOW="$WORKSPACE/WORKFLOW.md"
ROUTING_GUARD_SOURCE="$WORKSPACE/global-config/plugins/systematic-routing-guard.ts"
ROUTER_SKILLS_SOURCE="$WORKSPACE/global-config/skills"
AGENTS_SOURCE="$WORKSPACE/global-config/AGENTS.md"
FAIL_MESSAGES=()
ANCHOR_FILES=("$WORKFLOW" "$ROUTING_GUARD_SOURCE" "$ROUTER_SKILLS_SOURCE/workflow-odd-secure/SKILL.md" "$ROUTER_SKILLS_SOURCE/workflow-systematic/SKILL.md" "$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md" "$AGENTS_SOURCE")
fail() {{ FAIL_MESSAGES+=("$1"); printf 'FAIL %s\\n' "$1"; }}
{extract_function("anchor_block_body")}
{extract_function("anchor_has")}
{extract_function("anchor_check_row")}
ANCHOR_MANIFEST=(
{manifest}
)
for anchor_row in "${{ANCHOR_MANIFEST[@]}}"; do
  IFS='~' read -r anchor_id anchor_file anchor_label anchor_key <<< "$anchor_row"
  before=${{#FAIL_MESSAGES[@]}}
  anchor_check_row "$anchor_id" "$anchor_file" "$anchor_label" "$anchor_key"
  if [ "${{#FAIL_MESSAGES[@]}}" -eq "$before" ]; then printf 'PASS %s\\n' "$anchor_id"; fi
done
printf 'ANCHOR_LOOP_RESULT rows=%s failures=%s\\n' "${{#ANCHOR_MANIFEST[@]}}" "${{#FAIL_MESSAGES[@]}}"
ANCHOR_TOKENS=(
{token_table}
)
for token_row in "${{ANCHOR_TOKENS[@]}}"; do
  IFS='~' read -r token_anchor token_file token_label token_literal <<< "$token_row"
  if anchor_has "$token_file" "$token_anchor" "$token_literal"; then :; else fail "ANCHOR_TOKEN_MISSING: $token_anchor $token_file $token_literal"; fi
done
printf 'TOKEN_LOOP_RESULT rows=%s failures=%s\\n' "${{#ANCHOR_TOKENS[@]}}" "${{#FAIL_MESSAGES[@]}}"
[ "${{#FAIL_MESSAGES[@]}}" -eq 0 ]'''
        result = subprocess.run(["bash", "-c", script], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout, end="")
        self.assertIn(f"ANCHOR_LOOP_RESULT rows={len(rows(manifest))} failures=0", result.stdout)
        self.assertIn(f"TOKEN_LOOP_RESULT rows={len(rows(token_table))} failures=0", result.stdout)
        self.assertEqual(result.stdout.count("PASS "), len(rows(manifest)), result.stdout)


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

    def test_duplicate_manifest_id_is_detected(self):
        body = '"a.anchor~$FILE~FILE~one"\n"a.anchor~$FILE~FILE~two"\n'
        self.assertEqual(duplicate_manifest_ids(body), ["a.anchor"])

    def test_self_referential_keystone_is_rejected(self):
        manifest = '"workflow.tiny-fix~$FILE~WORKFLOW.md~workflow.tiny-fix"\n'
        errors = validate_manifest_keystones(manifest)
        self.assertTrue(errors, "a self-referential manifest keystone must be rejected")
        self.assertIn("keystone repeats anchor id", errors[0])


if __name__ == "__main__":
    unittest.main()
