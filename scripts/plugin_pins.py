#!/usr/bin/env python3
"""Consume the auto-update plugin's pending-updates.json and bump pins in global-config/.

The plugin only proposes. This tool is the human-approved apply step: it edits the canonical
source (global-config/opencode.json and tui.json), never the live ~/.config/opencode. The
verifier then mirrors the reviewed source as usual. Only entries named on the command line are
changed, and only when the proposal verdict is "propose" and the source still holds the
proposal's `current` pin.

  plugin_pins.py report
  plugin_pins.py apply --approve NAME[=VERSION] [--approve ...] [--dry-run]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = "opencode-plugin-auto-update.pending/v1"
CONFIG_FILES = ("opencode.json", "tui.json")
ROOT = Path(__file__).resolve().parent.parent


class Refusal(Exception):
    pass


def default_pending() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "opencode-plugin-auto-update" / "pending-updates.json"


def load_pending(path: Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal(f"cannot read pending updates {path}: {exc}")
    if doc.get("schema") != SCHEMA:
        raise Refusal(f"unexpected pending-updates schema: {doc.get('schema')!r}")
    return doc


def versions_in(text: str, name: str) -> list:
    return re.findall(r'"' + re.escape(name) + r'@([^"@]+)"', text)


def report(pending: Path, config_dir: Path) -> list:
    doc = load_pending(pending)
    texts = [(config_dir / f).read_text(encoding="utf-8") for f in CONFIG_FILES if (config_dir / f).exists()]
    rows = []
    for p in doc["proposals"]:
        found = [v for t in texts for v in versions_in(t, p["name"])]
        rows.append({**p, "in_source": bool(found) and all(v == p.get("current") for v in found)})
    return rows


def parse_approval(item: str):
    name, sep, version = item.rpartition("=")
    return (name, version) if sep else (item, None)


def apply(pending: Path, config_dir: Path, approve: list, dry_run: bool = False) -> list:
    doc = load_pending(pending)
    by_name = {p["name"]: p for p in doc["proposals"]}
    plan = []
    for item in approve:
        name, version = parse_approval(item)
        p = by_name.get(name)
        if p is None:
            raise Refusal(f"{name}: no proposal")
        if p["verdict"] != "propose":
            raise Refusal(f"{name}: verdict is {p['verdict']} ({p['reason']}), not approvable")
        if version is not None and version != p.get("candidate"):
            raise Refusal(f"{name}: approved {version} but the proposal is {p.get('candidate')}")
        plan.append(p)

    edits, changes = {}, []
    for p in plan:
        name, cur, new = p["name"], p["current"], p["candidate"]
        touched = False
        for f in CONFIG_FILES:
            path = config_dir / f
            if not path.exists():
                continue
            text = edits.get(f, path.read_text(encoding="utf-8"))
            found = versions_in(text, name)
            if not found:
                continue
            if any(v != cur for v in found):
                raise Refusal(f"{name}: {f} holds {sorted(set(found))}, proposal was made against {cur} (stale)")
            edits[f] = text.replace(f'"{name}@{cur}"', f'"{name}@{new}"')
            changes.append((f, name, cur, new))
            touched = True
        if not touched:
            raise Refusal(f"{name}: no pinned entry found in {', '.join(CONFIG_FILES)}")

    for f, text in edits.items():
        try:
            json.loads(text)
        except ValueError as exc:
            raise Refusal(f"{f}: result is not valid JSON ({exc}); nothing written")
    if not dry_run:
        for f, text in edits.items():
            path = config_dir / f
            tmp = path.with_name(f".{f}.tmp")
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
    order = {f: i for i, f in enumerate(CONFIG_FILES)}
    return sorted(changes, key=lambda c: (order[c[0]], c[1]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pending", type=Path, default=None)
    ap.add_argument("--config-dir", type=Path, default=ROOT / "global-config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report")
    a = sub.add_parser("apply")
    a.add_argument("--approve", action="append", required=True, metavar="NAME[=VERSION]")
    a.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    pending = args.pending or default_pending()
    try:
        if args.cmd == "report":
            for r in report(pending, args.config_dir):
                src = "" if r["in_source"] else "  (source differs from proposal base)"
                print(f"{r['name']:<40} {str(r.get('current')):<9} -> {str(r.get('candidate')):<9} {r['verdict']:<8} {r['reason']}{src}")
        else:
            for f, name, cur, new in apply(pending, args.config_dir, args.approve, args.dry_run):
                print(f"{'would change' if args.dry_run else 'changed'} {f}: {name} {cur} -> {new}")
            if not args.dry_run:
                print("Next: run the tests and the verifier, review the diff, then commit.")
    except Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
