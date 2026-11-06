#!/usr/bin/env python3
"""Keep verify-workflow.sh's module manifest and the health plugin's pin in step.

  python3 scripts/verifier_manifest.py check    # exit 1 if the manifest or the pin is stale
  python3 scripts/verifier_manifest.py update   # regenerate the manifest, then re-pin the plugin

The manifest lists every file under verify/ (the *.sh modules in execution order, then checkers/*) with its sha256. The pin is the
sha256 of verify-workflow.sh itself (which embeds the manifest), so one digest covers the whole
verifier. Never hand-edit either value."""
import argparse
import hashlib
import re
import sys
from pathlib import Path

BEGIN, END = "# BEGIN VERIFY_MODULES\n", "# END VERIFY_MODULES"
PIN = re.compile(r'^(const VERIFY_SCRIPT_SHA256 = ")[0-9a-f]{64}(";)', re.M)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(modules_dir):
    base = Path(modules_dir)
    files = sorted(p for p in base.rglob("*") if p.is_file())
    rows = [f'  "{p.relative_to(base)} {digest(p)}"' for p in files]
    return "VERIFY_MODULES=(\n" + "\n".join(rows) + "\n)\n"


def current_block(entry_text):
    m = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), entry_text, re.S)
    if not m:
        raise SystemExit("manifest markers not found in verify-workflow.sh")
    return m


def drift(entry_text, modules_dir):
    """Names of modules whose listed digest is wrong, missing from the manifest, or no longer on disk."""
    listed = dict(re.findall(r'^\s*"([^ "]+) ([0-9a-f]{64})"', current_block(entry_text).group(1), re.M))
    base = Path(modules_dir)
    actual = {str(p.relative_to(base)): digest(p) for p in base.rglob("*") if p.is_file()}
    names = sorted(
        {n for n in listed if listed[n] != actual.get(n)} | {n for n in actual if n not in listed}
    )
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("check", "update"))
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args(argv)
    entry = args.root / "verify-workflow.sh"
    plugin = args.root / "global-config/plugins/workflow-health-check.ts"
    text = entry.read_text(encoding="utf-8")
    want_block = render(args.root / "verify")
    problems = []
    if current_block(text).group(1) != want_block:
        names = drift(text, args.root / "verify")
        problems.append("module manifest in verify-workflow.sh is stale: " + (", ".join(names) or "ordering changed"))
    if args.command == "update":
        if problems:
            m = current_block(text)
            text = text[: m.start(1)] + want_block + text[m.end(1):]
            entry.write_text(text, encoding="utf-8")
            print("manifest regenerated")
        ptext = plugin.read_text(encoding="utf-8")
        new = PIN.sub(lambda m: m.group(1) + digest(entry) + m.group(2), ptext, count=1)
        if new != ptext:
            plugin.write_text(new, encoding="utf-8")
            print("plugin pin updated")
        return 0
    pin = PIN.search(plugin.read_text(encoding="utf-8"))
    if not pin or pin.group(0).split('"')[1] != digest(entry):
        problems.append("VERIFY_SCRIPT_SHA256 in workflow-health-check.ts does not match verify-workflow.sh")
    for p in problems:
        print(f"stale: {p}", file=sys.stderr)
    if not problems:
        print("ok: manifest and pin are current")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
