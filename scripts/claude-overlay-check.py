#!/usr/bin/env python3
"""Report or re-apply `changesets/claude-*` overlay sets after a gentle-ai sync.

Sets are reported as applied (already at target), reapplicable (safe to apply),
conflict (changed before-state), reverted (newest journal is a deliberate revert),
or superseded (replaced by a later set). Only sets in PERSISTENT are re-applied;
all others, including trial sets, are reported but never re-applied. Conflicts are
always left alone.
A set stays reapplicable while any of its operations is not yet at its target
bytes, so a sync that restored only one of several managed blocks still triggers
the re-apply.

    claude-overlay-check.py [--root DIR] [--json] [--reapply] [--journal-root DIR]

Exit codes: 0 when settled; 1 when any set conflicts; 2 when a set was re-applied
or a persistent set remains reapplicable. Python 3 stdlib only.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA = "workflow-claude-overlay-check/v1"
OK_OUTCOMES = ("applied", "already_applied")
# Sets whose drift a routine sync may restore, so --reapply may apply them again.
# Every other set is applied deliberately once and never re-applied (trial sets included).
PERSISTENT = {"claude-md-trim"}

# Sets replaced by a later set: their bytes legitimately differ from expect_before,
# so they are reported as `superseded` and never conflict.
SUPERSEDED = {"claude-advisor-triggers": "claude-model-routing"}


def run_changeset(root, args):
    cmd = [sys.executable, str(root / "scripts" / "changeset.py"), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        return proc.returncode, None


def classify(report):
    if report is None:
        return "conflict", "changeset.py produced no JSON report"
    if report.get("refused"):
        return "conflict", "refused: " + str(report["refused"])
    if report.get("error"):
        return "conflict", "error: " + str(report["error"])
    results = report.get("results") or []
    if not results:
        return "conflict", "no results"
    # A remove conflict is superseded only when a later create of that same file
    # confirms the intended final bytes are already present. Other earlier ops on
    # the same file (for example distinct block replacements) remain significant.
    creates = {result.get("file") for result in results
               if result.get("op") == "file_create"
               and result.get("outcome") in OK_OUTCOMES}
    results = [result for result in results
               if not (result.get("op") == "file_remove"
                       and result.get("file") in creates)]
    for result in results:
        if result.get("outcome") not in OK_OUTCOMES:
            return "conflict", "{} {}: {}".format(
                result.get("op"), result.get("file"), result.get("reason"))
    # Keep one outcome per operation, not per file. A set may carry several
    # block_replace operations on the same file and gentle-ai restores each
    # managed block independently, so collapsing by file would hide a block a
    # sync put back behind a sibling block that is still trimmed. Any operation
    # not yet at its target bytes keeps the set reapplicable.
    if all(result.get("outcome") == "already_applied" for result in results):
        return "applied", None
    return "reapplicable", None


def outcomes(report):
    if report is None:
        return []
    return [{"op": r.get("op"), "file": r.get("file"), "outcome": r.get("outcome"),
             "reason": r.get("reason")} for r in report.get("results") or []]


def find_sets(root):
    return sorted(p for p in (root / "changesets").glob("claude-*")
                  if (p / "changeset.json").is_file())


def newest_journal_kind(journal_root, set_id):
    """kind of the newest journal of the set, or None when there is none."""
    best = None
    for journal in (journal_root / set_id).glob("*/journal.jsonl"):
        try:
            with journal.open("rb") as handle:
                header = json.loads(handle.readline().decode("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(header, dict) or header.get("type") != "header":
            continue
        if header.get("kind") not in ("apply", "revert"):
            continue
        key = (str(header.get("started", "")), journal.parent.name)
        if best is None or key > best[0]:
            best = (key, header["kind"])
    return best[1] if best else None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--journal-root", type=Path)
    parser.add_argument("--reapply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    journal_root = args.journal_root or root / "backups" / "changesets"
    report = {"schema": SCHEMA, "root": str(root), "home": os.path.expanduser("~"),
              "journal_root": str(journal_root), "reapply": args.reapply, "sets": []}
    for set_dir in find_sets(root):
        name = set_dir.name
        entry = {"set": name, "state": "applied", "reason": None, "reapplied": False,
                 "persistent": name in PERSISTENT, "outcomes": []}
        if name in SUPERSEDED:
            entry.update(state="superseded", reason="replaced by " + SUPERSEDED[name],
                         persistent=False)
            report["sets"].append(entry)
            continue
        if newest_journal_kind(journal_root, name) == "revert":
            entry.update(state="reverted", reason="newest journal is a revert",
                         persistent=False)
            report["sets"].append(entry)
            continue
        _, status_report = run_changeset(root, ["status", "--set", str(set_dir)])
        state, reason = classify(status_report)
        entry.update(state=state, reason=reason, outcomes=outcomes(status_report))
        if args.reapply and state == "reapplicable" and entry["persistent"]:
            _, apply_report = run_changeset(
                root, ["apply", "--set", str(set_dir), "--journal-root", str(journal_root)])
            apply_state, apply_reason = classify(apply_report)
            if apply_state == "conflict":
                entry.update(state="conflict", reason=apply_reason)
            else:
                entry.update(state="applied", reapplied=True)
            entry["outcomes"] = outcomes(apply_report) or entry["outcomes"]
        report["sets"].append(entry)
    counts = {"applied": 0, "reapplicable": 0, "conflict": 0, "reverted": 0,
              "superseded": 0}
    for entry in report["sets"]:
        counts[entry["state"]] = counts.get(entry["state"], 0) + 1
    report["counts"] = counts
    reapplied = any(entry["reapplied"] for entry in report["sets"])
    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        print("claude overlay check (HOME=%s)" % report["home"])
        for entry in report["sets"]:
            suffix = "  (re-applied)" if entry["reapplied"] else ""
            if entry["state"] == "reapplicable" and not entry["persistent"]:
                suffix += "  (not persistent; not re-applied)"
            reason = ": " + entry["reason"] if entry["reason"] else ""
            print("  %-13s %s%s%s" % (entry["state"], entry["set"], suffix, reason))
        print("%d set(s): %d applied, %d reapplicable, %d conflict, %d reverted, %d superseded" % (
            len(report["sets"]), counts["applied"], counts["reapplicable"], counts["conflict"],
            counts["reverted"], counts["superseded"]))
        if any(entry["persistent"] and entry["state"] == "reapplicable"
               for entry in report["sets"]):
            print("run: python3 scripts/claude-overlay-check.py --reapply")
    if counts["conflict"]:
        return 1
    if reapplied or any(entry["persistent"] and entry["state"] == "reapplicable"
                        for entry in report["sets"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
