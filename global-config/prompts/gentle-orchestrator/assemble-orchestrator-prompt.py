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
ATTR_RE = re.compile(r"(?:^|\s)(?P<key>id|kind|after|supersedes|sha256)=")
KNOWN_KINDS = ("add", "replace", "remove")
HEX64_RE = re.compile(r"[0-9a-f]{64}")


class AssemblyError(Exception):
    """Raised on any malformed overlay or base input; the CLI exits non-zero."""


def parse_attrs(raw, line_no):
    attrs = {}
    matches = list(ATTR_RE.finditer(raw))
    if not matches:
        raise AssemblyError("overlay line %d: SECURE:BEGIN carries no attributes" % line_no)
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        attrs[match.group("key")] = raw[start:end].strip()
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
                add_cursors[anchor] = cursor + delta
            elif cursor > start:
                add_cursors[anchor] = start

    for block in blocks:
        context = "overlay id=%s" % block["id"]
        if block["kind"] == "add":
            section = find_section(working, block["after"], context)
            position = add_cursors.get(block["after"], section["end"])
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
    except AssemblyError as error:
        print("assemble-orchestrator-prompt: FAILED: %s" % error, file=sys.stderr)
        return 2
    if not assembled.endswith("\n"):
        assembled += "\n"
    sys.stdout.write(assembled)
    return 0


if __name__ == "__main__":
    sys.exit(main())
