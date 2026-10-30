"""Resolve one plugin package from the OpenCode V2 npm cache and check it against its configured range (queue Q44).

usage: v2-plugin-resolve.py <v2-opencode.json> <v2-npm-cache> <package-name>
Prints one line: ok <TAB> root <TAB> version <TAB> spec <TAB> note  |  error <TAB> detail. `note` is kept for the shell
sections and is currently always empty: only the newest install is judged.

V2 lists plugins under `plugins` with `~x.y.z` patch ranges and installs each into
<cache>/<scope>/<name>@<spec>/<epoch-ms>/node_modules/<scope>/<name>. The newest epoch directory is the one V2 loads. Read-only."""
import json
import re
import sys
from pathlib import Path

VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[+-][0-9A-Za-z.+-]+)?$")
RANGE = re.compile(r"^([~^]?)(\d+)\.(\d+)\.(\d+)(?:[+-][0-9A-Za-z.+-]+)?$")


def satisfies(version, spec_range):
    """Exact, ~x.y.z (same major.minor, patch >= x.y.z.z) and ^x.y.z (same major, >= x.y.z; 0.y.z stays on 0.y)."""
    v, r = VERSION.match(version), RANGE.match(spec_range)
    if not v or not r:
        return False
    op, want = r.group(1), tuple(int(r.group(i)) for i in (2, 3, 4))
    got = tuple(int(v.group(i)) for i in (1, 2, 3))
    if op == "":
        return got == want
    if got < want:
        return False
    if op == "~":
        return got[:2] == want[:2]
    if want[0] > 0:
        return got[0] == want[0]
    return got[:2] == want[:2] if want[1] > 0 else got == want  # ^0.0.x admits only that exact patch


ENTRY_EXTENSIONS = ("", ".js", ".json", ".node", ".mjs", ".cjs")


def entry_exists(root, entry):
    """Resolve a package `main` the way Node does: the file itself, with an added extension, or a directory's index file."""
    target = root / entry
    if any((target.parent / (target.name + ext)).is_file() for ext in ENTRY_EXTENSIONS):
        return True
    return target.is_dir() and any((target / f"index{ext}").is_file() for ext in ENTRY_EXTENSIONS[1:])


def main(argv):
    config_path, cache, name = Path(argv[1]), Path(argv[2]), argv[3]
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error\tcannot read the V2 config {config_path}: {exc}")
        return 0
    entries = config.get("plugins", config.get("plugin", []))
    specs = [e for e in entries if isinstance(e, str) and (e == name or e.startswith(name + "@"))] if isinstance(entries, list) else []
    if not specs:
        print(f"error\tno {name} plugin entry in {config_path}")
        return 0
    if len(specs) > 1:
        print(f"error\tmultiple {name} plugin entries are configured: {', '.join(specs)}")
        return 0
    spec = specs[0]
    wanted = spec[len(name) + 1:] if "@" in spec[len(name):] else ""
    if not RANGE.match(wanted):
        print(f"error\t{spec} is not pinned to an exact version or a ~/^ range")
        return 0
    package_dir = cache / f"{name}@{wanted}"
    epochs = sorted((p for p in package_dir.glob("*") if p.is_dir() and p.name.isdigit()), key=lambda p: int(p.name), reverse=True)
    if not epochs:
        print(f"error\t{spec} is not materialized in the V2 cache (expected {package_dir}/<epoch>)")
        return 0
    # V2 loads the newest epoch, so only that one is judged: an install in progress (an epoch directory before its
    # package.json exists) is an error, never a pass on an older install. An older complete one is named as a diagnostic only.
    newest = epochs[0]
    root = newest / "node_modules" / name
    try:
        manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        older = next((e.name for e in epochs[1:] if (e / "node_modules" / name / "package.json").is_file()), None)
        hint = f"; an older complete install exists (epoch {older}) but V2 loads the newest" if older else ""
        print(f"error\tthe newest cached install of {spec} (epoch {newest.name}) has no readable package.json, so it is incomplete or still installing: {root}{hint}")
        return 0
    version = str(manifest.get("version", ""))
    if not version:
        print(f"error\tthe cached install of {spec} has no version in its package.json: {root}")
        return 0
    if not satisfies(version, wanted):
        print(f"error\t{spec} resolved to {version} at {root}, which is outside the configured range")
        return 0
    entry = manifest.get("main")
    if isinstance(entry, str) and entry and not entry_exists(root, entry):
        print(f"error\tthe cached install of {spec} is incomplete: its entry file {entry} is missing in {root}")
        return 0
    print(f"ok\t{root}\t{version}\t{spec}\t")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
