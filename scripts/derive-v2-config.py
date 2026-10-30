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
COPY_DIRS = ("prompts", "skills", "plugins", "mcp")
# Environment a local MCP server needs under V2: its own credential and log paths, never the V1 data directory.
# `{data}` is the V2 data root (<opencode-v2>/data).
MCP_ENV = {
    "vision-bridge": {
        "VISION_BRIDGE_LEG_LOG": "{data}/vision-bridge/leg.log",
    }
}
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
            notes.append(f"dropped {spec}: V1-only (peer @opencode-ai/plugin <2); retired on V2 (owner decision 2026-10-29)")
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


# (agent, approval tool) pairs the owner decided should be allowed outright even though V2 will not prompt for them
# (owner, 2026-10-30: the orchestrator starts native reviews itself). Anything else that allows an approval tool is reported.
INTENDED_APPROVAL_ALLOWS = {("gentle-orchestrator", "host_review_start")}


def check_rules(config, tools, intended=None):
    """Raise if a tool has no explicit rule; return warnings for agents that allow an approval tool."""
    intended = INTENDED_APPROVAL_ALLOWS if intended is None else intended
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
            if effect not in ("ask", "deny") and (name, tool) not in intended:
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


def rewrite_mcp(config, source_dir, root_path, env_by_server):
    """Local MCP commands under the V1 root that the repo holds move into the V2 root, with V2-owned environment."""
    v1 = str(HOME / ".config" / "opencode")
    root = Path(root_path)
    data = root.parents[1] / "data"
    notes = []
    for name, server in (config.get("mcp") or {}).items():
        command = server.get("command") or []
        changed = False
        for index, part in enumerate(command):
            if isinstance(part, str) and part.startswith(v1 + "/"):
                rel = part[len(v1) + 1:]
                if (Path(source_dir) / rel).is_file():
                    command[index] = str(root / rel)
                    changed = True
        if changed:
            env = {k: v.format(data=data) for k, v in (env_by_server.get(name) or {}).items()}
            if env:
                server["environment"] = {**(server.get("environment") or {}), **env}
            notes.append(f"mcp {name}: command moved into the V2 root" + (" with V2-owned environment (" + ", ".join(env) + ")" if env else ""))
    return notes


def expose_mcp_directly(config):
    """V2 hides an MCP server's tools behind its single `execute` (Code Mode) tool unless the server sets `codemode: false`.
    The V1 agent prompts and permission rules name the tools directly (codegraph_codegraph_explore, github_ro_*), so keep them
    direct; an explicit `codemode` in the source is the owner's choice and stays."""
    exposed = []
    for name, server in (config.get("mcp") or {}).items():
        if "codemode" not in server:
            server["codemode"] = False
            exposed.append(name)
    return [f"mcp {', '.join(exposed)}: codemode=false so the tools stay directly callable (V2 default routes them through `execute`)"] if exposed else []


# Plugin-owned agents whose sandbox access must match a reviewed agent. On V2 the Systematic category rules come AFTER an agent
# overlay in the rule list and V2 takes the last match, so the overlay's `sandbox_*` allows lose to the category denies. A
# permission block in opencode.json is applied last, so mirror the reference agent's sandbox/host rules there (V2 only).
ACCESS_MIRRORS = {
    "systematic-implementer": "gentle-ai-worker",
    "bug-reproduction-validator": "gentle-ai-worker",
    "pr-comment-resolver": "gentle-ai-worker",
    "design-iterator": "gentle-ai-worker",
}
MIRRORED_PREFIXES = ("sandbox_", "host_")


def mirror_agent_access(config, mirrors=None):
    notes = []
    agents = config.setdefault("agent", {})
    for target, reference in (ACCESS_MIRRORS if mirrors is None else mirrors).items():
        ref = agents.get(reference)
        if ref is None:
            notes.append(f"agent {target}: access mirror skipped, reference agent {reference} is not in the source config")
            continue
        entry = agents.setdefault(target, {})
        copied = []
        for field in ("permission", "tools"):
            rules = {k: v for k, v in (ref.get(field) or {}).items() if k.startswith(MIRRORED_PREFIXES)}
            if rules:
                entry[field] = {**(entry.get(field) or {}), **rules}
                copied.append(f"{len(rules)} {field}")
        notes.append(f"agent {target}: sandbox/host access mirrored from {reference} ({', '.join(copied)}) so the V2 category denies do not win")
    return notes


V2_DEAD_MODEL_FLAGS = ("temperature", "reasoning", "attachment")


def apply_v2_grep_policy(config, orchestrator="gentle-orchestrator"):
    """Native grep is the orchestrator's alone, and only with an ask; everyone else uses the sandbox tools.
    V1 expresses that as a global `grep: ask` with `deny` on each agent, because an agent rule beats the global one. V2 uses the
    last matching rule and puts plugin-owned agents (the Systematic ones, which have no entry here) under the global rule only, so
    a global ask would expose native grep to them. On V2 the global rule is therefore `deny` and the orchestrator carries the ask."""
    permission = config.get("permission")
    if not isinstance(permission, dict) or permission.get("grep") != "ask":
        return []
    agent = (config.get("agent") or {}).get(orchestrator)
    if not isinstance(agent, dict):
        return [f"left the global grep policy as ask: there is no {orchestrator} agent to carry it"]
    permission["grep"] = "deny"
    agent_permission = agent.get("permission")
    if agent_permission is None:
        agent_permission = agent["permission"] = {}
    if not isinstance(agent_permission, dict):
        permission["grep"] = "ask"
        return [f"left the global grep policy as ask: {orchestrator}.permission is not an object"]
    agent_permission["grep"] = "ask"
    return [f"native grep: global policy deny and {orchestrator} ask on V2 (V2 uses the last matching rule, so a global ask would expose it to plugin-owned agents)"]


def drop_v2_unsupported(config):
    """Remove keys OpenCode V2 reports on every config load as 'omitted unsupported legacy ...'. Each one is dead on V2:
    - top-level subagent_depth: V2 reads experimental.subagent_depth (the V1 config sets both, so nothing is lost; if only the
      legacy one is set it moves, so the nesting limit never disappears);
    - compaction.prune: no V2 equivalent (compaction is Magic Context's; compaction.auto stays);
    - per-model temperature/reasoning/attachment flags: V2 takes capabilities from its own model catalog;
    - an empty-string agent variant, which already meant 'no variant'."""
    dropped = {"duplicate subagent_depth": 0, "compaction.prune": 0, "model flags": 0, "empty agent variants": 0}
    notes = []
    if "subagent_depth" in config:
        experimental = config.get("experimental")
        if experimental is None:  # an explicit null means 'unset' there too
            experimental = config["experimental"] = {}
        if isinstance(experimental, dict):
            legacy = config.pop("subagent_depth")
            if "subagent_depth" in experimental:
                dropped["duplicate subagent_depth"] += 1
            else:
                experimental["subagent_depth"] = legacy
                notes.append("moved subagent_depth to experimental.subagent_depth, the key V2 reads for the nesting limit")
        else:
            notes.append("kept top-level subagent_depth: experimental is not an object, so there is nowhere to move it")
    compaction = config.get("compaction")
    if isinstance(compaction, dict) and "prune" in compaction:
        del compaction["prune"]
        dropped["compaction.prune"] += 1
    for provider in (config.get("provider") or {}).values():
        for model in ((provider or {}).get("models") or {}).values():
            for flag in V2_DEAD_MODEL_FLAGS:
                if isinstance(model, dict) and flag in model:
                    del model[flag]
                    dropped["model flags"] += 1
    for agent in (config.get("agent") or {}).values():
        if isinstance(agent, dict) and agent.get("variant") == "":
            del agent["variant"]
            dropped["empty agent variants"] += 1
    total = sum(dropped.values())
    if total:
        detail = ", ".join(f"{count} {name}" for name, count in dropped.items() if count)
        notes.insert(0, f"dropped {total} legacy {'setting' if total == 1 else 'settings'} that V2 reports as unsupported and ignores ({detail})")
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
    notes += rewrite_mcp(config, source_dir, root_path, MCP_ENV)
    notes += expose_mcp_directly(config)
    notes += mirror_agent_access(config)
    notes += apply_v2_grep_policy(config)
    notes += drop_v2_unsupported(config)
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


def sync_systematic_home(staging, target, apply):
    """Systematic reads its user config from $HOME/.config/opencode, whatever XDG_CONFIG_HOME says, and the V2 sandbox does not
    grant the V1 tree. The V2 launcher therefore runs the server with HOME=<config root>/home; put the overlay there."""
    overlay = Path(staging) / "systematic.jsonc"
    if not overlay.is_file():
        return
    with tempfile.TemporaryDirectory() as home_staging:
        dest = Path(home_staging) / ".config/opencode/systematic.jsonc"
        dest.parent.mkdir(parents=True)
        shutil.copy2(overlay, dest)
        sync(home_staging, target.parent / "home", apply)


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
                sync_systematic_home(tmp, Path(args.target), args.apply)
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
