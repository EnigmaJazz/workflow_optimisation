#!/usr/bin/env python3
"""Derive the OpenCode V2 config root from global-config/ (queue Q46).

  derive-v2-config.py --source global-config --sandbox-repo ~/agent-sandbox-integration --out DIR
  derive-v2-config.py --source global-config --sandbox-repo ... --target ~/.local/share/opencode-v2/config/opencode [--apply]

global-config/ stays the single source of truth. The V2 root differs only where V2 requires it:
  * `plugin` becomes `plugins`; registry pins become `~x.y.z` patch ranges (the guarded auto-update job moves them);
    the rate-limit fork becomes a DIRECTORY entry (V2 does not load a single-file path) pointing at a copy under
    <root>/vendor/; the auto-update fork and V1-only packages are dropped and reported; anything else needs a decision.
  * tui.json is not carried over (V2 reads cli.json; tui.jsonc is never migrated).
Permissions are NOT rewritten: the V1 policy denies the sandbox and host tools globally and grants them per agent, and the
V2 fragment (global allow/ask) would weaken that. Instead the V2 rule "a tool with no rule is silently allowed" is checked:
every tool of the sandbox tool table needs an explicit rule, and an agent that allows an approval tool is reported.

--out writes a staging tree. --target compares against a live V2 root and, with --apply, copies it in: a differing file gets
a timestamped .bak first, nothing is deleted, and the V1 config directories are refused. Without --apply it only reports.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HOME = Path.home()
V1_ROOTS = (HOME / ".config" / "opencode", HOME / ".opencode")
DEFAULT_ROOT = HOME / ".local" / "share" / "opencode-v2" / "config" / "opencode"
NAME = r"(?:@[A-Za-z0-9][\w.-]*/)?[A-Za-z0-9][\w.-]*"
EXACT = re.compile(rf"^(?P<name>{NAME})@(?P<version>\d+\.\d+\.\d+)$")
FORK_NAME = "opencode-rate-limit-fallback-mapped"
COPY_FILES = ("cli.json", "AGENTS.md", "systematic.jsonc", "rate-limit-fallback.json")
COPY_DIRS = ("prompts", "skills", "plugins")
FORK_IGNORE = shutil.ignore_patterns(".git", ".gitignore", ".atl", "node_modules", "odd", "tests", "CLAUDE.md", "tsconfig.json", "bunfig.toml", "bun.lock", "*.bak*", ".backup*")


class DeriveError(Exception):
    pass


def derive_plugins(plugins, fork_dir=None, fork_ref=None):
    """-> (V2 plugin list, notes). `fork_dir` is where the fork copy is checked for `exports`; `fork_ref` is the final path."""
    out, notes = [], []
    for spec in plugins:
        if "opencode-plugin-auto-update" in spec:
            notes.append(f"dropped {spec}: auto-update is retired on V2 (guarded updates use scripts/v2-plugin-autoupdate.py)")
        elif re.match(r"^opencode-usage-total@", spec):
            notes.append(f"dropped {spec}: V1-only (peer @opencode-ai/plugin <2); confirm retiring it on V2")
        elif spec.startswith("file://") and spec.endswith(f"/{FORK_NAME}/index.ts"):
            if fork_dir is None:
                fork_dir = Path(spec[len("file://"):-len("/index.ts")])
            package = Path(fork_dir) / "package.json"
            if not package.is_file() or "exports" not in json.loads(package.read_text()):
                raise DeriveError(f"the rate-limit fork at {fork_dir} must declare `exports` in package.json to load on V2")
            out.append(f"file://{fork_ref or fork_dir}")
        else:
            m = EXACT.match(spec)
            if not m:
                raise DeriveError(f"plugin entry needs a decision (not an exact registry pin, the fork or a known drop): {spec}")
            out.append(f"{m.group('name')}@~{m.group('version')}")
    return out, notes


def scan_tools(sandbox_repo):
    """The sandbox tool table: {tool: asks for approval in code}."""
    tools = {}
    for path in sorted((Path(sandbox_repo) / "opencode/plugins/lib").glob("tool-specs-*.ts")):
        parts = re.split(r"\n  ([a-z_]+): defineTool\(\{", path.read_text(encoding="utf-8"))
        for i in range(1, len(parts), 2):
            tools[parts[i]] = bool(re.search(r"ask\(", parts[i + 1]))
    return tools


def check_rules(config, tools):
    """Raise if a tool has no explicit rule; return warnings for agents that allow an approval tool."""
    permission = config.get("permission") or {}
    missing = sorted(t for t in tools if t not in permission)
    if missing:
        raise DeriveError("tools without an explicit permission rule (V2 would allow them silently): " + ", ".join(missing))
    warnings = []
    for name, agent in (config.get("agent") or {}).items():
        rules = agent.get("permission") or {}
        for tool, asks in tools.items():
            if not asks:
                continue
            effect = rules.get(tool, permission.get(tool))
            if isinstance(effect, dict):
                effect = effect.get("*")
            if effect not in ("ask", "deny"):
                warnings.append(f"agent {name}: approval tool {tool} is '{effect}', so V2 will not prompt for it")
    return warnings


def check_v1_paths(config):
    v1 = str(HOME / ".config" / "opencode")
    warnings = []
    for name, server in (config.get("mcp") or {}).items():
        command = server.get("command") or []
        if any(isinstance(part, str) and part.startswith(v1) for part in command):
            warnings.append(f"mcp {name}: command uses a path under {v1}, which the V2 nono profile does not grant")
    return warnings


def resolve_file_refs(config_text, source_dir, live_root, staging):
    """Every `{file:./x}` in the config must resolve inside the V2 root. Files missing from global-config/ but present in
    the live V1 root are copied from there (read-only use of the V1 tree) and reported; anything else is an error."""
    notes = []
    for ref in sorted(set(re.findall(r"\{file:(\./[^}]+)\}", config_text))):
        rel = Path(ref)
        if ".." in rel.parts:
            raise DeriveError(f"file reference escapes the config root: {ref}")
        if (Path(source_dir) / rel).is_file():
            continue
        live = Path(live_root) / rel
        if live.is_file():
            (Path(staging) / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live, Path(staging) / rel)
            notes.append(f"{ref} is not in global-config/; copied from the live V1 root (add it to global-config/ to keep it in the repo)")
        else:
            raise DeriveError(f"file reference {ref} resolves neither in global-config/ nor in {live_root}")
    return notes


def derive_config(source, fork_dir=None, fork_ref=None):
    plugins, notes = derive_plugins(source.get("plugin") or [], fork_dir, fork_ref)
    out = {}
    for key, value in source.items():
        if key == "plugin":
            out["plugins"] = plugins
        else:
            out[key] = value
    return out, notes


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def build(source_dir, sandbox_repo, staging, root_path, live_root=None):
    source_dir, staging = Path(source_dir), Path(staging)
    source = json.loads((source_dir / "opencode.json").read_text(encoding="utf-8"))
    fork_src = None
    for spec in source.get("plugin") or []:
        if spec.startswith("file://") and spec.endswith(f"/{FORK_NAME}/index.ts"):
            fork_src = Path(spec[len("file://"):-len("/index.ts")])
    vendor = staging / "vendor" / FORK_NAME
    if fork_src is not None:
        if not fork_src.is_dir():
            raise DeriveError(f"the rate-limit fork is not at {fork_src}")
        shutil.copytree(fork_src, vendor, ignore=FORK_IGNORE, dirs_exist_ok=True)
    config, notes = derive_config(source, vendor if fork_src else None, Path(root_path) / "vendor" / FORK_NAME)
    tools = scan_tools(sandbox_repo)
    warnings = check_rules(config, tools) + check_v1_paths(config)
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "opencode.json").write_text(dump(config), encoding="utf-8")
    for name in COPY_FILES:
        if (source_dir / name).is_file():
            shutil.copy2(source_dir / name, staging / name)
    for name in COPY_DIRS:
        if (source_dir / name).is_dir():
            shutil.copytree(source_dir / name, staging / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.bak*", "__pycache__"))
    notes += resolve_file_refs((source_dir / "opencode.json").read_text(encoding="utf-8"), source_dir, live_root or V1_ROOTS[0], staging)
    return notes, warnings, len(tools)


def files(root):
    return sorted(p.relative_to(root) for p in Path(root).rglob("*") if p.is_file())


def sync(staging, target, apply):
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    for rel in files(staging):
        src, dest = Path(staging) / rel, Path(target) / rel
        if dest.is_file() and dest.read_bytes() == src.read_bytes():
            continue
        action = "replace" if dest.is_file() else "write"
        print(f"[derive-v2] {'would ' if not apply else ''}{action} {dest}")
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_file():
                shutil.copy2(dest, dest.with_name(dest.name + ".bak-" + stamp))
            shutil.copy2(src, dest)
    if not apply:
        print("[derive-v2] dry-run - nothing was written. Re-run with --apply to write.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--sandbox-repo", required=True)
    ap.add_argument("--out")
    ap.add_argument("--target")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root-path", help="final location of the V2 config root, used in the fork's file:// entry (default: the --target, or ~/.local/share/opencode-v2/config/opencode)")
    args = ap.parse_args(argv)
    if bool(args.out) == bool(args.target):
        ap.error("give exactly one of --out or --target")
    if args.target:
        target = Path(args.target).resolve()
        for v1 in V1_ROOTS:
            if target == v1 or v1 in target.parents:
                print(f"[derive-v2] refused: {target} is inside the V1 tree", file=sys.stderr)
                return 2
    try:
        if args.out:
            notes, warnings, count = build(args.source, args.sandbox_repo, args.out, args.root_path or DEFAULT_ROOT)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                notes, warnings, count = build(args.source, args.sandbox_repo, tmp, args.root_path or args.target)
                for line in notes:
                    print(f"[derive-v2] note: {line}")
                for line in warnings:
                    print(f"[derive-v2] WARNING: {line}")
                sync(tmp, args.target, args.apply)
            return 0
    except DeriveError as err:
        print(f"[derive-v2] refused: {err}", file=sys.stderr)
        return 2
    for line in notes:
        print(f"[derive-v2] note: {line}")
    for line in warnings:
        print(f"[derive-v2] WARNING: {line}")
    print(f"[derive-v2] ok: {count} sandbox tools all have an explicit rule; staged in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
