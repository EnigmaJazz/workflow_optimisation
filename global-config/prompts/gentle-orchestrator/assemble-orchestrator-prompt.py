#!/usr/bin/env python3
"""Deterministic assembler for the gentle-orchestrator prompt source (Q31 S5).

Reads `global-config/prompts/gentle-orchestrator/base.md` (skipping its metadata
header) plus `global-config/prompts/gentle-orchestrator/overlay.md` and writes the
assembled prompt to stdout.

Section semantics: a base section starts at a heading line (^#{1,6} + space) and
runs to the next heading line of any level; trailing blank lines are excluded.
`replace`/`remove` verify the declared sha256 over that exact section text
(heading included) before applying. Every block fails loudly (exit 2) on a
missing anchor, a hash mismatch, an unknown kind, or unbalanced markers.

Managed-marker invariant: a paired HTML-comment marker (for example the
`<!-- gentle-ai:opencode-desktop-delegation-progress -->` /
`<!-- /gentle-ai:opencode-desktop-delegation-progress -->` pair) must not
straddle a section boundary. The assembler deliberately does not lint block
bodies for balanced pairs: a `replace`/`remove` body that carries only one half
of a pair drops the other half instead of failing. Keep both halves inside one
base section, and carry both halves in any replacement body.

`add` inserts its body at the END of the anchor section (immediately after the
section's last line). When several `add` blocks share one anchor, each later body
is appended after the bodies already added at that anchor, so shared-anchor adds
land in file order (deterministic).

OpenCode `{file:./...}` substitution: literal prompt includes of that form are
used live in this repository (five `{file:./prompts/...}` includes in
`global-config/opencode.json` for frontend/vision agents), so the mechanism
exists. It cannot replace this assembler: inclusion is positional and cannot
express the overlay's replace/remove-of-base-section semantics, and it would
move prompt content out of the string that verifier content assertions read.
OpenCode V2 support for `{file:...}` includes is recorded as UNVERIFIED in
`docs/TODO.md` (Q41 side-by-side V2 probe). Run with
`--report-file-substitution` for this finding as reproducible output.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

# This script lives in global-config/prompts/gentle-orchestrator/, so the repo
# root is four levels above the file.
REPO = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_BASE = REPO / "global-config" / "prompts" / "gentle-orchestrator" / "base.md"
DEFAULT_OVERLAY = REPO / "global-config" / "prompts" / "gentle-orchestrator" / "overlay.md"

HEADING_RE = re.compile(r"^#{1,6} ")
BEGIN_RE = re.compile(r"^<!-- SECURE:BEGIN (?P<attrs>.*) -->$")
END_RE = re.compile(r"^<!-- SECURE:END id=(?P<id>[^ ]+) -->$")
# A key is recognised only where a key is expected: the start of the attribute
# region, or the end of the previous value. An `identifier=` sequence inside a
# value (for example a heading value such as `after=### Foo=Bar`) is therefore
# value text, never a key. A key position accepts only a known attribute name;
# an unknown name there fails loudly, and a repeated name is a duplicate.
ATTR_NAME_RE = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=")
KNOWN_ATTRS = ("id", "kind", "after", "supersedes", "sha256")
# `after`/`supersedes` take a markdown heading, which may itself contain `=`
# and ` X=`; every other value is a single whitespace-delimited token.
HEADING_VALUE_ATTRS = ("after", "supersedes")
KNOWN_ATTR_KEY_RE = re.compile(r"(?:^|\s)(?P<key>%s)=" % "|".join(KNOWN_ATTRS))
KNOWN_KINDS = ("add", "replace", "remove")
HEX64_RE = re.compile(r"[0-9a-f]{64}")


class AssemblyError(Exception):
    """Raised on any malformed overlay or base input; the CLI exits non-zero."""


def parse_attrs(raw, line_no):
    """Parse `key=value` pairs, recognising keys only where a key is expected.

    Scanning left to right, each key position reads `name=`: the name must be a
    known attribute, and a repeated name is a duplicate. The value runs to the
    next key position — for a heading-valued attribute (`after`, `supersedes`)
    that is the next known key, so a heading value may contain `=` and ` X=`; for
    every other attribute the value is one whitespace-delimited token. An unknown
    name in key position raises AssemblyError, as does a duplicate; an
    `identifier=` sequence inside a value is value text, never a key.
    """
    attrs = {}
    length = len(raw)
    pos = 0
    while pos < length:
        while pos < length and raw[pos].isspace():
            pos += 1
        if pos >= length:
            break
        name_match = ATTR_NAME_RE.match(raw, pos)
        if not name_match:
            raise AssemblyError(
                "overlay line %d: malformed SECURE:BEGIN attribute near %r"
                % (line_no, raw[pos:pos + 40])
            )
        key = name_match.group("key")
        if key not in KNOWN_ATTRS:
            raise AssemblyError(
                "overlay line %d: unknown SECURE:BEGIN attribute %r" % (line_no, key)
            )
        if key in attrs:
            raise AssemblyError(
                "overlay line %d: duplicate SECURE:BEGIN attribute %r" % (line_no, key)
            )
        value_start = name_match.end()
        if key in HEADING_VALUE_ATTRS:
            next_key = KNOWN_ATTR_KEY_RE.search(raw, value_start)
            value_end = next_key.start() if next_key else length
        else:
            value_end = value_start
            while value_end < length and not raw[value_end].isspace():
                value_end += 1
        attrs[key] = raw[value_start:value_end].strip()
        pos = value_end
    if not attrs:
        raise AssemblyError("overlay line %d: SECURE:BEGIN carries no attributes" % line_no)
    return attrs


def strip_metadata_header(text):
    if not text.startswith("<!--"):
        raise AssemblyError("base.md does not start with a metadata header")
    marker = "\n-->\n"
    idx = text.find(marker)
    if idx < 0:
        raise AssemblyError("base.md metadata header is not closed")
    body = text[idx + len(marker):]
    if body.startswith("\n"):
        body = body[1:]
    return body


def parse_overlay(text):
    blocks = []
    current = None
    for line_no, line in enumerate(text.split("\n"), 1):
        begin = BEGIN_RE.match(line)
        end = END_RE.match(line)
        if begin:
            if current is not None:
                raise AssemblyError(
                    "overlay line %d: nested SECURE:BEGIN before SECURE:END for id=%s"
                    % (line_no, current["id"])
                )
            attrs = parse_attrs(begin.group("attrs"), line_no)
            block = {
                "line": line_no,
                "id": attrs.get("id", ""),
                "kind": attrs.get("kind", ""),
                "after": attrs.get("after"),
                "supersedes": attrs.get("supersedes"),
                "sha256": attrs.get("sha256"),
                "body": [],
            }
            if not block["id"]:
                raise AssemblyError("overlay line %d: SECURE:BEGIN is missing id=" % line_no)
            if block["kind"] not in KNOWN_KINDS:
                raise AssemblyError(
                    "overlay id=%s: kind must be one of add|replace|remove, got %r"
                    % (block["id"], block["kind"])
                )
            if block["kind"] == "add":
                if not block["after"]:
                    raise AssemblyError("overlay id=%s: add requires after=<base-heading>" % block["id"])
            else:
                if not block["supersedes"] or not block["sha256"]:
                    raise AssemblyError(
                        "overlay id=%s: %s requires supersedes=<base-heading> and sha256=<hash>"
                        % (block["id"], block["kind"])
                    )
                if not HEX64_RE.fullmatch(block["sha256"]):
                    raise AssemblyError(
                        "overlay id=%s: sha256 must be 64 lowercase hex characters" % block["id"]
                    )
            current = block
            continue
        if end:
            if current is None:
                raise AssemblyError("overlay line %d: SECURE:END without SECURE:BEGIN" % line_no)
            if end.group("id") != current["id"]:
                raise AssemblyError(
                    "overlay line %d: SECURE:END id=%s does not match SECURE:BEGIN id=%s"
                    % (line_no, end.group("id"), current["id"])
                )
            body = list(current["body"])
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            if not body:
                raise AssemblyError("overlay id=%s: empty body" % current["id"])
            current["body"] = body
            blocks.append(current)
            current = None
            continue
        if "<!-- SECURE:" in line:
            raise AssemblyError("overlay line %d: malformed SECURE marker: %s" % (line_no, line[:120]))
        if current is not None:
            current["body"].append(line)
    if current is not None:
        raise AssemblyError("overlay: missing SECURE:END for id=%s" % current["id"])
    if not blocks:
        raise AssemblyError("overlay contains no SECURE blocks")
    ids = [block["id"] for block in blocks]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise AssemblyError("overlay ids must be unique; duplicated: %s" % ", ".join(duplicates))
    return blocks


def split_sections(lines):
    headings = [i for i, line in enumerate(lines) if HEADING_RE.match(line)]
    sections = []
    for pos, start in enumerate(headings):
        end = headings[pos + 1] if pos + 1 < len(headings) else len(lines)
        segment = lines[start:end]
        while segment and not segment[-1].strip():
            segment.pop()
        sections.append({
            "heading": lines[start],
            "start": start,
            "end": start + len(segment),
            "text": "\n".join(segment),
        })
    return sections


def find_section(lines, heading, context):
    matches = [s for s in split_sections(lines) if s["heading"] == heading]
    if not matches:
        raise AssemblyError("%s: anchor heading not found in the working prompt: %r" % (context, heading))
    if len(matches) > 1:
        raise AssemblyError("%s: anchor heading is not unique: %r" % (context, heading))
    return matches[0]


def apply_overlay(base_body, blocks):
    working = base_body.split("\n")
    # Insertion cursor per `add` anchor. An `add` inserts its body at the END of
    # the anchor section; when several add blocks share one anchor, each later
    # body is appended after the bodies already added there, so they land in
    # file order. Splices shift every recorded cursor so the map stays absolute.
    add_cursors = {}

    def splice(start, end, new_lines):
        working[start:end] = new_lines
        delta = len(new_lines) - (end - start)
        for anchor, cursor in list(add_cursors.items()):
            if cursor >= end:
                # The splice lies entirely at or before the cursor: shift it.
                add_cursors[anchor] = cursor + delta
            elif cursor > start:
                # The cursor fell inside the spliced region: pin it to the
                # region start so a later add stays in file order.
                add_cursors[anchor] = start
            # A cursor strictly before `start` is already correctly placed.

    for block in blocks:
        context = "overlay id=%s" % block["id"]
        if block["kind"] == "add":
            section = find_section(working, block["after"], context)
            position = add_cursors.get(block["after"], section["end"])
            # Ordering guard: an add must never land before the current end of
            # its anchor section, so bodies sharing one anchor stay in file
            # order even across intervening replace/remove splices.
            position = max(position, section["end"])
            body = [""] + list(block["body"])
            splice(position, position, body)
            add_cursors[block["after"]] = position + len(body)
            continue
        section = find_section(working, block["supersedes"], context)
        actual = hashlib.sha256(section["text"].encode("utf-8")).hexdigest()
        if actual != block["sha256"]:
            raise AssemblyError(
                "%s: sha256 mismatch for %r\ndeclared %s\nactual   %s"
                % (context, block["supersedes"], block["sha256"], actual)
            )
        if block["kind"] == "replace":
            splice(section["start"], section["end"], list(block["body"]))
        else:
            splice(section["start"], section["end"], [])
    return "\n".join(working)


def report_file_substitution():
    config_path = REPO / "global-config" / "opencode.json"
    occurrences = config_path.read_text(encoding="utf-8").count("{file:")
    return (
        "file-substitution finding: OpenCode prompt includes of the form {file:./...} are used live "
        "in this repository (%d occurrences in global-config/opencode.json, frontend/vision agent "
        "prompts), so literal inclusion exists. It cannot replace this assembler: inclusion is "
        "positional and cannot express the overlay's replace/remove-of-base-section semantics, and "
        "it would move prompt content out of the string that verifier content assertions read. "
        "OpenCode V2 support for {file:...} includes is recorded as UNVERIFIED in docs/TODO.md (Q41). "
        "Verdict: keep the rendered base + overlay + assembler pipeline." % occurrences
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Assemble the gentle-orchestrator prompt from base.md + overlay.md (stdout)."
    )
    parser.add_argument("--base", default=str(DEFAULT_BASE), help="path to base.md")
    parser.add_argument("--overlay", default=str(DEFAULT_OVERLAY), help="path to overlay.md")
    parser.add_argument(
        "--report-file-substitution",
        action="store_true",
        help="print the {file:./...} substitution finding and exit",
    )
    args = parser.parse_args(argv)
    if args.report_file_substitution:
        print(report_file_substitution())
        return 0
    try:
        base_text = Path(args.base).read_text(encoding="utf-8")
        overlay_text = Path(args.overlay).read_text(encoding="utf-8")
        base_body = strip_metadata_header(base_text)
        blocks = parse_overlay(overlay_text)
        assembled = apply_overlay(base_body, blocks)
    except (AssemblyError, OSError) as error:
        print("assemble-orchestrator-prompt: FAILED: %s" % error, file=sys.stderr)
        return 2
    if not assembled.endswith("\n"):
        assembled += "\n"
    sys.stdout.write(assembled)
    return 0


if __name__ == "__main__":
    sys.exit(main())
