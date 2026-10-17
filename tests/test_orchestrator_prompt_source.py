"""Source tests for the Q31 S5a orchestrator prompt pipeline (unwired).

These tests execute the real assembler and verify the committed source files:
base.md must be a byte-exact render of the two vendored upstream sources; every
overlay replace/remove must carry a verifiable sha256 over the base section it
supersedes; the assembled output must be free of retired residue - and the
residue check is proven non-vacuous by a planted positive control.
"""

import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

BASE = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "base.md"
OVERLAY = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "overlay.md"
LEDGER = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "normative-ledger.md"
TEMPLATE = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "upstream" / "orchestrator.template.md"
SECTIONS = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "upstream" / "odd-orchestrator-sections.md"
ASSEMBLER = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "assemble-orchestrator-prompt.py"

CURRENT_PROMPT_SHA256 = "a56c4f5dd7014089226877dce2bb011bb32fc84760a3d7fb7f4c30d5f0d0dcec"

REQUIRED_IDS = (
    "user:read-only-boundary",
    "user:always-delegate",
    "user:technical-lead-contract",
    "user:workflow-routing",
    "user:secure-odd-protocol",
    "user:review-boundary",
    "user:magic-context",
    "user:advisory-lifecycle",
    "user:host-tools-relay",
    "user:project-registration",
    "user:shell-environment",
    "user:frontend-lane",
)

SIGNATURES = {
    "user:read-only-boundary": "### Secure Read-only Orchestrator Boundary",
    "user:always-delegate": "### Secure Always-Delegate Rules (MANDATORY)",
    "user:technical-lead-contract": "### Secure Technical-Lead Contract (MANDATORY)",
    "user:workflow-routing": "### Secure Route Loading and Task Classification (MANDATORY)",
    "user:secure-odd-protocol": "### ODD protocol",
    "user:review-boundary": "#### Secure Native Review Boundary (MANDATORY)",
    "user:magic-context": "### Secure Magic Context Contract (MANDATORY)",
    "user:advisory-lifecycle": "#### Secure Advisory Lifecycle (MANDATORY)",
    "user:host-tools-relay": "### Secure Fixed Host Tools and Review Relay",
    "user:project-registration": "### Secure Project Registration — Pre-Routing Gate",
    "user:shell-environment": "### Interactive Shell Environment",
    "user:frontend-lane": "### Frontend / UI Lane and Premium Escalation",
}

FORBIDDEN_RESIDUE = ("engram", "mem_", "sdd-", "openspec", "/sdd")
# Explicit allowlist of (term, allowed line substring, reason); empty by design.
ALLOWED_RESIDUE = ()
VALID_CLASSIFICATIONS = ("kept", "moved", "split", "superseded-by-base", "removed-by-design")

HEADING_RE = re.compile(r"^#{1,6} ")
BEGIN_RE = re.compile(r"^<!-- SECURE:BEGIN (?P<attrs>.*) -->$")
END_RE = re.compile(r"^<!-- SECURE:END id=(?P<id>[^ ]+) -->$")
ATTR_RE = re.compile(r"(?:^|\s)(?P<key>id|kind|after|supersedes|sha256)=")
HEX64_RE = re.compile(r"[0-9a-f]{64}")
PLACEHOLDER_RE = re.compile(r"\{\{GENTLE_AI_ODD_SECTION:(?P<name>[^}]+)\}\}")
SECTION_RE = re.compile(
    r"<!-- sdd-orchestrator-section:(?P<name>.+?):start -->\n(?P<body>.*?)"
    r"<!-- sdd-orchestrator-section:(?P=name):end -->",
    re.S,
)


def strip_metadata_header(text):
    assert text.startswith("<!--"), "base.md must start with a metadata header"
    marker = "\n-->\n"
    idx = text.find(marker)
    assert idx >= 0, "base.md metadata header is not closed"
    body = text[idx + len(marker):]
    if body.startswith("\n"):
        body = body[1:]
    return body


def section_bodies():
    text = SECTIONS.read_text(encoding="utf-8")
    return {m.group("name"): m.group("body") for m in SECTION_RE.finditer(text)}


def render_base_body():
    text = TEMPLATE.read_text(encoding="utf-8")
    for name, body in section_bodies().items():
        text = text.replace("{{GENTLE_AI_ODD_SECTION:%s}}" % name, body)
    return text


def base_sections(lines):
    headings = [i for i, line in enumerate(lines) if HEADING_RE.match(line)]
    sections = []
    for pos, start in enumerate(headings):
        end = headings[pos + 1] if pos + 1 < len(headings) else len(lines)
        segment = lines[start:end]
        while segment and not segment[-1].strip():
            segment.pop()
        sections.append({"heading": lines[start], "text": "\n".join(segment)})
    return sections


def section_sha256(section_text):
    return hashlib.sha256(section_text.encode("utf-8")).hexdigest()


def parse_attrs(raw):
    matches = list(ATTR_RE.finditer(raw))
    if not matches:
        raise ValueError("SECURE:BEGIN carries no attributes: %r" % raw)
    attrs = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        attrs[match.group("key")] = raw[start:end].strip()
    return attrs


def parse_overlay(text):
    """Strict, independent parser for overlay.md (raises ValueError)."""
    blocks = []
    current = None
    for line_no, line in enumerate(text.split("\n"), 1):
        begin = BEGIN_RE.match(line)
        end = END_RE.match(line)
        if begin:
            if current is not None:
                raise ValueError("line %d: nested SECURE:BEGIN before SECURE:END" % line_no)
            attrs = parse_attrs(begin.group("attrs"))
            block = {
                "line": line_no,
                "id": attrs.get("id", ""),
                "kind": attrs.get("kind", ""),
                "after": attrs.get("after"),
                "supersedes": attrs.get("supersedes"),
                "sha256": attrs.get("sha256"),
                "body": [],
            }
            if not block["id"] or block["kind"] not in ("add", "replace", "remove"):
                raise ValueError("line %d: invalid id/kind: %r" % (line_no, line))
            current = block
            continue
        if end:
            if current is None:
                raise ValueError("line %d: SECURE:END without SECURE:BEGIN" % line_no)
            if end.group("id") != current["id"]:
                raise ValueError(
                    "line %d: SECURE:END id=%s does not match BEGIN id=%s"
                    % (line_no, end.group("id"), current["id"])
                )
            body = list(current["body"])
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            if not body:
                raise ValueError("id=%s: empty body" % current["id"])
            current["body"] = body
            blocks.append(current)
            current = None
            continue
        if "<!-- SECURE:" in line:
            raise ValueError("line %d: malformed SECURE marker" % line_no)
        if current is not None:
            current["body"].append(line)
    if current is not None:
        raise ValueError("missing SECURE:END for id=%s" % current["id"])
    if not blocks:
        raise ValueError("overlay contains no SECURE blocks")
    ids = [block["id"] for block in blocks]
    if len(ids) != len(set(ids)):
        raise ValueError("overlay ids must be unique")
    return blocks


def run_assembler(extra_args=()):
    return subprocess.run(
        [sys.executable, str(ASSEMBLER), *extra_args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


# A minimal valid base for the failure-path and ordering probes: one metadata
# header plus unique '### ' headings. Body prose deliberately avoids any
# `<!-- SECURE:` substring so probes fail for the intended reason.
OVERRIDE_BASE = (
    "<!--\nprobe header\n-->\n\n"
    "### Anchor\n\nanchor body\n\n"
    "### Next\n\nnext body\n"
)


def run_with_files(base_text, overlay_text):
    """Run the assembler over temp --base/--overlay files (never the real ones)."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base.md"
        overlay = Path(tmp) / "overlay.md"
        base.write_text(base_text, encoding="utf-8")
        overlay.write_text(overlay_text, encoding="utf-8")
        return run_assembler(("--base", str(base), "--overlay", str(overlay)))


def scan_residue(text):
    """Return [(term, line_no, line)] for forbidden residue not on the allowlist."""
    violations = []
    for line_no, line in enumerate(text.split("\n"), 1):
        for term in FORBIDDEN_RESIDUE:
            if term in line:
                allowed = any(
                    entry[0] == term and entry[1] in line for entry in ALLOWED_RESIDUE
                )
                if not allowed:
                    violations.append((term, line_no, line.strip()[:160]))
    return violations


class OrchestratorPromptSourceTests(unittest.TestCase):
    def test_base_renders_upstream_sources_without_placeholders(self):
        text = BASE.read_text(encoding="utf-8")
        body = strip_metadata_header(text)

        template = TEMPLATE.read_text(encoding="utf-8")
        names = PLACEHOLDER_RE.findall(template)
        self.assertEqual(len(names), 5, "template must carry exactly five placeholders")
        self.assertEqual(body.count("{{GENTLE_AI_ODD_SECTION"), 0, "base.md must have 0 remaining placeholders")

        bodies = section_bodies()
        for name in names:
            self.assertIn(name, bodies, "sections file must carry an exact-name body for %r" % name)
            self.assertIn(bodies[name], body, "resolved body must appear verbatim in base.md: %r" % name)
        self.assertEqual(body, render_base_body(), "base.md must equal a byte-exact render of the vendored sources")

        odd_only = bodies.get("Delegated Verification Gate (MANDATORY) (ODD only)")
        reduced = bodies.get("Delegated Verification Gate (Reduced Form)")
        self.assertTrue(odd_only and odd_only not in body, "the (ODD only) variant must not be rendered")
        self.assertTrue(reduced and reduced not in body, "the (Reduced Form) variant must not be rendered")

        for needle in (
            "Gentleman-Programming/gentle-ai",
            "Tag: v4.0.0",
            "bb8b9ac34962d0be407f8b895fa1c0429b280b37",
            "6a5fde7b3a5df218e12902ea4663dbcab783726aa3bd66a7e1b33b2dc6248c91",
            "5dc3be455da7284d710767acd762bcc5cb9595f9",
            "f75b016c2964bdf45d7f4f76cdeeaa401e1e7d26737370a96c00dd2481fa5508",
            "NEVER hand-edit this file; upstream changes arrive by re-render.",
        ):
            self.assertIn(needle, text, "base.md metadata must record %r" % needle)

    def test_base_headings_are_unique(self):
        base_lines = strip_metadata_header(BASE.read_text(encoding="utf-8")).split("\n")
        headings = [section["heading"] for section in base_sections(base_lines)]
        duplicates = sorted({heading for heading in headings if headings.count(heading) > 1})
        self.assertEqual(duplicates, [], "base.md anchor headings must be unique: %s" % duplicates)

    def test_overlay_markers_balanced_and_ids_unique(self):
        blocks = parse_overlay(OVERLAY.read_text(encoding="utf-8"))
        ids = [block["id"] for block in blocks]
        self.assertEqual(len(ids), len(set(ids)), "overlay ids must be unique")
        for block in blocks:
            self.assertTrue(block["body"], "block %s must have a body" % block["id"])
        missing = [item for item in REQUIRED_IDS if item not in ids]
        self.assertEqual(missing, [], "required overlay ids missing: %s" % missing)
        self.assertGreaterEqual(sum(1 for block in blocks if block["kind"] == "add"), 1)
        self.assertGreaterEqual(sum(1 for block in blocks if block["kind"] == "replace"), 1)

    def test_replace_remove_declarations_carry_verifiable_hashes(self):
        base_lines = strip_metadata_header(BASE.read_text(encoding="utf-8")).split("\n")
        sections = base_sections(base_lines)
        by_heading = {}
        for section in sections:
            by_heading.setdefault(section["heading"], []).append(section)

        blocks = parse_overlay(OVERLAY.read_text(encoding="utf-8"))
        for block in blocks:
            if block["kind"] == "add":
                self.assertTrue(block["after"], "add block %s must declare after=" % block["id"])
                continue
            self.assertTrue(block["supersedes"], "block %s must declare supersedes=" % block["id"])
            self.assertTrue(
                block["sha256"] and HEX64_RE.fullmatch(block["sha256"]),
                "block %s must declare a 64-hex sha256" % block["id"],
            )
            matches = by_heading.get(block["supersedes"], [])
            self.assertEqual(
                len(matches), 1, "block %s: superseded heading must be unique in base.md" % block["id"]
            )
            self.assertEqual(
                section_sha256(matches[0]["text"]),
                block["sha256"],
                "block %s: declared sha256 must match the base section %r" % (block["id"], block["supersedes"]),
            )

    def test_shared_anchor_adds_insert_in_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.md"
            overlay = Path(tmp) / "overlay.md"
            base.write_text(
                "<!--\nprobe header\n-->\n\n### Anchor\n\nanchor body\n\n### Next\n\nnext body\n",
                encoding="utf-8",
            )
            overlay.write_text(
                "<!-- SECURE:BEGIN id=test:first kind=add after=### Anchor -->\n"
                "### First\n\nfirst body\n<!-- SECURE:END id=test:first -->\n\n"
                "<!-- SECURE:BEGIN id=test:second kind=add after=### Anchor -->\n"
                "### Second\n\nsecond body\n<!-- SECURE:END id=test:second -->\n",
                encoding="utf-8",
            )
            result = run_assembler(("--base", str(base), "--overlay", str(overlay)))
            self.assertEqual(result.returncode, 0, "assembler must exit 0: %s" % result.stderr)
            self.assertIn("### First", result.stdout)
            self.assertIn("### Second", result.stdout)
            self.assertLess(
                result.stdout.index("### First"),
                result.stdout.index("### Second"),
                "add blocks sharing one anchor must land in file order",
            )

    def test_assembled_output_is_clean_and_complete(self):
        result = run_assembler()
        self.assertEqual(result.returncode, 0, "assembler must exit 0: %s" % result.stderr)
        self.assertTrue(result.stdout.strip(), "assembler output must be non-empty")

        self.assertEqual(scan_residue(result.stdout), [], "assembled output must contain no forbidden residue")

        planted = result.stdout + "\nCONTROL: engram mem_ sdd- openspec /sdd\n"
        planted_terms = {violation[0] for violation in scan_residue(planted)}
        self.assertEqual(
            planted_terms,
            set(FORBIDDEN_RESIDUE),
            "positive control: the residue check must fire on every planted forbidden term",
        )
        self.assertEqual(scan_residue(result.stdout + "\nordinary clean text\n"), [])

        self.assertEqual(
            result.stdout.count("<!-- gentle-ai:opencode-desktop-delegation-progress -->"),
            result.stdout.count("<!-- /gentle-ai:opencode-desktop-delegation-progress -->"),
            "the desktop delegation-progress comment pair must stay balanced",
        )
        self.assertGreaterEqual(
            result.stdout.count("<!-- gentle-ai:opencode-desktop-delegation-progress -->"), 1
        )

        for block_id, signature in SIGNATURES.items():
            self.assertIn(signature, result.stdout, "required overlay %s must land in the output" % block_id)

    def test_assembler_fails_loudly_on_missing_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "overlay.md"
            bad.write_text(
                "<!-- SECURE:BEGIN id=test:missing kind=replace supersedes=### No Such Heading "
                "sha256=%s -->\n### Body\n\ncontent\n<!-- SECURE:END id=test:missing -->\n" % ("0" * 64),
                encoding="utf-8",
            )
            result = run_assembler(("--overlay", str(bad)))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("not found", result.stderr)

    def test_assembler_fails_loudly_on_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "overlay.md"
            bad.write_text(
                "<!-- SECURE:BEGIN id=test:hash kind=replace supersedes=### Mental Model "
                "sha256=%s -->\n### Body\n\ncontent\n<!-- SECURE:END id=test:hash -->\n" % ("0" * 64),
                encoding="utf-8",
            )
            result = run_assembler(("--overlay", str(bad)))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("sha256 mismatch", result.stderr)

    def test_assembler_fails_loudly_on_unbalanced_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "overlay.md"
            bad.write_text(
                "<!-- SECURE:BEGIN id=test:unbalanced kind=add after=### Mental Model -->\n"
                "### Body\n\ncontent\n",
                encoding="utf-8",
            )
            result = run_assembler(("--overlay", str(bad)))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("missing SECURE:END", result.stderr)

    def test_assembler_fails_loudly_on_missing_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist.md"
            result = run_assembler(("--base", str(missing)))
        self.assertEqual(result.returncode, 2, result.stderr)
        # The FAILED prefix is the control that the handled AssemblyError/OSError
        # path was taken rather than Python's default traceback (which exits 1).
        self.assertIn("FAILED", result.stderr)

    def test_assembler_fails_loudly_on_nested_begin(self):
        nested = (
            "<!-- SECURE:BEGIN id=test:outer kind=add after=### Anchor -->\n"
            "### Outer\n\nouter body\n"
            "<!-- SECURE:BEGIN id=test:inner kind=add after=### Anchor -->\n"
            "### Inner\n\ninner body\n"
            "<!-- SECURE:END id=test:inner -->\n"
            "<!-- SECURE:END id=test:outer -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, nested)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("nested SECURE:BEGIN", result.stderr)
        # Positive control: closing the outer block before the second BEGIN
        # differs by exactly the nesting property and must assemble cleanly.
        control = (
            "<!-- SECURE:BEGIN id=test:outer kind=add after=### Anchor -->\n"
            "### Outer\n\nouter body\n<!-- SECURE:END id=test:outer -->\n\n"
            "<!-- SECURE:BEGIN id=test:inner kind=add after=### Anchor -->\n"
            "### Inner\n\ninner body\n<!-- SECURE:END id=test:inner -->\n"
        )
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_assembler_fails_loudly_on_unknown_kind(self):
        unknown = (
            "<!-- SECURE:BEGIN id=test:bad kind=upsert after=### Anchor -->\n"
            "### Body\n\ncontent\n<!-- SECURE:END id=test:bad -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, unknown)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("kind must be one of", result.stderr)
        control = unknown.replace("kind=upsert", "kind=add")
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_attribute_value_may_contain_equals_sequences(self):
        # R3-ATTR-PARSER-REGRESSION: an `identifier=` sequence inside a value
        # must not be read as an unknown attribute. `after=### Foo=Bar` is the
        # regression case: key `after`, value `### Foo=Bar` (intact), not a key
        # `Foo`. The heading anchor being found proves the value survived whole.
        base_text = (
            "<!--\nprobe header\n-->\n\n"
            "### Foo=Bar\n\nfoo body\n\n"
            "### Next\n\nnext body\n"
        )
        overlay = (
            "<!-- SECURE:BEGIN id=test:equals kind=add after=### Foo=Bar -->\n"
            "### Added\n\nadded body\n<!-- SECURE:END id=test:equals -->\n"
        )
        result = run_with_files(base_text, overlay)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("### Added", result.stdout)
        # The heading value anchors the insert: `Added` lands after `foo body`,
        # so `after` carried the full `### Foo=Bar` value.
        self.assertLess(result.stdout.index("foo body"), result.stdout.index("### Added"))

    def test_assembler_fails_loudly_on_unknown_attribute(self):
        # R3-ATTR-VALIDATION-UNTESTED (unknown key): an unknown name where a key
        # is expected fails loudly.
        unknown = (
            "<!-- SECURE:BEGIN id=test:attr bogus=1 kind=add after=### Anchor -->\n"
            "### Body\n\ncontent\n<!-- SECURE:END id=test:attr -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, unknown)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unknown SECURE:BEGIN attribute", result.stderr)
        # Positive control: dropping the one unknown attribute differs by one
        # edit and reaches the same parse_overlay path.
        control = unknown.replace("bogus=1 ", "")
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_assembler_fails_loudly_on_duplicate_attribute(self):
        # R3-ATTR-VALIDATION-UNTESTED (duplicate key): an empty value makes the
        # repeat look like a second key; the pair must still be rejected.
        duplicate = (
            "<!-- SECURE:BEGIN id=test:dupa kind= kind=add after=### Anchor -->\n"
            "### Body\n\ncontent\n<!-- SECURE:END id=test:dupa -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, duplicate)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("duplicate SECURE:BEGIN attribute", result.stderr)
        # Positive control: giving the first `kind` a value leaves one `kind=`.
        control = duplicate.replace("kind= kind=add", "kind=add")
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_assembler_fails_loudly_on_empty_body(self):
        empty = (
            "<!-- SECURE:BEGIN id=test:empty kind=add after=### Anchor -->\n"
            "\n"
            "<!-- SECURE:END id=test:empty -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, empty)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("empty body", result.stderr)
        control = (
            "<!-- SECURE:BEGIN id=test:empty kind=add after=### Anchor -->\n"
            "### Body\n\ncontent\n<!-- SECURE:END id=test:empty -->\n"
        )
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_assembler_fails_loudly_on_duplicate_ids(self):
        duplicate = (
            "<!-- SECURE:BEGIN id=test:dup kind=add after=### Anchor -->\n"
            "### One\n\none body\n<!-- SECURE:END id=test:dup -->\n\n"
            "<!-- SECURE:BEGIN id=test:dup kind=add after=### Anchor -->\n"
            "### Two\n\ntwo body\n<!-- SECURE:END id=test:dup -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, duplicate)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("ids must be unique", result.stderr)
        # Positive control: the same overlay with the second id made unique.
        control = (
            "<!-- SECURE:BEGIN id=test:dup kind=add after=### Anchor -->\n"
            "### One\n\none body\n<!-- SECURE:END id=test:dup -->\n\n"
            "<!-- SECURE:BEGIN id=test:dup2 kind=add after=### Anchor -->\n"
            "### Two\n\ntwo body\n<!-- SECURE:END id=test:dup2 -->\n"
        )
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_assembler_fails_loudly_on_malformed_marker(self):
        malformed = (
            "<!-- SECURE:BEGIN id=test:ok kind=add after=### Anchor -->\n"
            "### Body\n\ncontent\n"
            "<!-- SECURE:END test:ok -->\n"
        )
        result = run_with_files(OVERRIDE_BASE, malformed)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("malformed SECURE marker", result.stderr)
        control = malformed.replace(
            "<!-- SECURE:END test:ok -->", "<!-- SECURE:END id=test:ok -->"
        )
        ok = run_with_files(OVERRIDE_BASE, control)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_overlapping_regions_preserve_file_order(self):
        # The positive control proving this probe can detect an anchor-ordering
        # violation is test_shared_anchor_adds_insert_in_file_order.
        base_text = (
            "<!--\nprobe header\n-->\n\n"
            "### A\n\na body\n\n"
            "### B\n\nb body\n\n"
            "### C\n\nc body\n"
        )
        base_body = strip_metadata_header(base_text)
        sections = {s["heading"]: s for s in base_sections(base_body.split("\n"))}
        overlay = (
            "<!-- SECURE:BEGIN id=test:added1 kind=add after=### A -->\n"
            "### Added1\n\nadded1 body\n<!-- SECURE:END id=test:added1 -->\n\n"
            "<!-- SECURE:BEGIN id=test:remove kind=remove supersedes=### B sha256=%s -->\n"
            "placeholder\n<!-- SECURE:END id=test:remove -->\n\n"
            "<!-- SECURE:BEGIN id=test:added2 kind=add after=### A -->\n"
            "### Added2\n\nadded2 body\n<!-- SECURE:END id=test:added2 -->\n"
            % section_sha256(sections["### B"]["text"])
        )
        result = run_with_files(base_text, overlay)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("### Added1", result.stdout)
        self.assertIn("### Added2", result.stdout)
        # The PROPERTY: two add blocks sharing one anchor land in file order
        # even across an intervening remove of another section.
        self.assertLess(
            result.stdout.index("### Added1"),
            result.stdout.index("### Added2"),
            "later add blocks on a shared anchor must land after earlier ones",
        )

    def test_replace_body_carrying_half_a_marker_pair_drops_the_other_half(self):
        begin = "<!-- gentle-ai:opencode-desktop-delegation-progress -->"
        end = "<!-- /gentle-ai:opencode-desktop-delegation-progress -->"
        base_text = (
            "<!--\nprobe header\n-->\n\n"
            "### Anchor\n\n" + begin + "\nanchor body\n" + end + "\n"
        )
        anchor = [
            s for s in base_sections(strip_metadata_header(base_text).split("\n"))
            if s["heading"] == "### Anchor"
        ][0]
        sha = section_sha256(anchor["text"])
        partial = (
            "<!-- SECURE:BEGIN id=test:partial kind=replace supersedes=### Anchor sha256=%s -->\n"
            "### Anchor\n\n" + begin + "\nreplaced body\n<!-- SECURE:END id=test:partial -->\n"
        ) % sha
        result = run_with_files(base_text, partial)
        self.assertEqual(result.returncode, 0, result.stderr)
        # The count-based balance check in test_assembled_output_is_clean_and_complete
        # is vacuous here (a dropped END still counts 0 == 0); this pins the
        # partial-drop hazard so the invariant is asserted rather than assumed.
        self.assertIn(begin, result.stdout)
        self.assertNotIn(end, result.stdout)
        # Positive control A: a replace body carrying BOTH halves keeps the pair.
        both = (
            "<!-- SECURE:BEGIN id=test:both kind=replace supersedes=### Anchor sha256=%s -->\n"
            "### Anchor\n\n" + begin + "\nreplaced body\n" + end
            + "\n<!-- SECURE:END id=test:both -->\n"
        ) % sha
        ok = run_with_files(base_text, both)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn(begin, ok.stdout)
        self.assertIn(end, ok.stdout)
        # Positive control B: without touching the anchor the base pair is intact.
        untouched = run_with_files(
            base_text,
            "<!-- SECURE:BEGIN id=test:noop kind=add after=### Anchor -->\n"
            "### Noop\n\nnoop body\n<!-- SECURE:END id=test:noop -->\n",
        )
        self.assertEqual(untouched.returncode, 0, untouched.stderr)
        self.assertIn(begin, untouched.stdout)
        self.assertIn(end, untouched.stdout)

    def test_file_substitution_report(self):
        result = run_assembler(("--report-file-substitution",))
        self.assertEqual(result.returncode, 0)
        self.assertIn("{file:", result.stdout)
        self.assertIn("cannot replace this assembler", result.stdout)
        self.assertIn("UNVERIFIED", result.stdout)

    def test_normative_ledger_rows_are_classified(self):
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn(CURRENT_PROMPT_SHA256, text, "ledger must cite the current prompt sha256")
        rows = []
        for line in text.split("\n"):
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells and cells[0].isdigit():
                rows.append(cells)
        self.assertGreaterEqual(len(rows), 60, "ledger must classify every extracted candidate sentence")
        for cells in rows:
            self.assertGreaterEqual(len(cells), 5, "ledger row must carry five columns: %r" % cells)
            classification, destination = cells[3], cells[4]
            self.assertIn(
                classification,
                VALID_CLASSIFICATIONS,
                "unclassified ledger row: %r" % cells[:4],
            )
            self.assertTrue(destination and destination not in ("-", "n/a"),
                            "ledger row lacks a destination: %r" % cells[:4])


if __name__ == "__main__":
    unittest.main()
