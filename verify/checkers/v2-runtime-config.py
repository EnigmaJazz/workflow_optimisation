#!/usr/bin/env python3
"""Validate V2-only runtime invariants and project the config for the V1 checker; derived refs use the scoped Magic Context pin and the fallback vendor directory."""
import json
import re
import sys
from pathlib import Path


def error(message):
    print(f"V2_RUNTIME_CONFIG_INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(path):
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        error(f"cannot read V2 runtime config: {exc}")

    plugins = config.get("plugin")
    if plugins is None:
        plugins = config.get("plugins")
    if not isinstance(plugins, list):
        error("plugin list is missing")
    magic = [item for item in plugins if isinstance(item, str) and "opencode-magic-context@" in item]
    fallback = [item for item in plugins if isinstance(item, str) and "opencode-rate-limit-fallback-mapped" in item]
    if len(magic) != 1:
        error("expected exactly one opencode-magic-context plugin ref")
    if len(fallback) != 1:
        error("expected exactly one opencode-rate-limit-fallback-mapped fork ref")
    if not (fallback[0].endswith("/index.ts") or fallback[0].endswith("/opencode-rate-limit-fallback-mapped")):
        error("opencode-rate-limit-fallback-mapped fork ref must name its directory or index.ts")
    if not re.fullmatch(r"(?:@[^/]+/)?opencode-magic-context@~[0-9]+\.[0-9]+\.[0-9]+", magic[0]):
        error("opencode-magic-context plugin ref must be an exact V2 version pin")
    permission = config.get("permission")
    orchestrator = (config.get("agent") or {}).get("gentle-orchestrator")
    if not isinstance(permission, dict) or permission.get("grep") != "deny":
        error("global permission.grep must be deny")
    if not isinstance(orchestrator, dict) or not isinstance(orchestrator.get("permission"), dict) or orchestrator["permission"].get("grep") != "allow":
        error("gentle-orchestrator permission.grep must be allow")
    if not isinstance((config.get("mcp") or {}).get("github_ro"), dict):
        error("mcp.github_ro must be present")
    if not isinstance(config.get("tools"), dict) or config["tools"].get("github_ro_*") is not False:
        error('tools["github_ro_*"] must be false')

    agents = config.get("agent")
    if agents is not None and not isinstance(agents, dict):
        error("agent inventory must be an object")
    agents = agents or {}
    aliases = {}
    for name, entry in agents.items():
        if not name.endswith("-astra"):
            continue
        base_name = name[:-6]
        base = agents.get(base_name)
        if not isinstance(base, dict):
            error(f"Astra alias {name} has no base agent {base_name}")
        if not isinstance(entry, dict) or entry.get("hidden") is not True or not entry.get("model"):
            error(f"Astra alias {name} must be hidden and have a model")
        for field in ("permission", "tools"):
            if entry.get(field) != base.get(field):
                error(f"Astra alias {name} {field} differs from base agent {base_name}")
        aliases[name] = entry

    mirrors = {}
    prefix_fields = ("permission", "tools")
    # The derivation copies no other agent metadata beyond optional descriptive/model fields.
    mirror_fields = {"permission", "tools", "description", "model"}
    for name, entry in agents.items():
        if not isinstance(entry, dict):
            continue
        rule_maps = [entry.get(field) for field in prefix_fields if field in entry]
        is_mirror = bool(rule_maps) and all(
            isinstance(rules, dict) and all(
                isinstance(key, str) and key.startswith(("sandbox_", "host_")) for key in rules
            ) for rules in rule_maps
        )
        if not is_mirror:
            continue
        if set(entry) - mirror_fields:
            error(f"access mirror {name} has unsupported fields: {', '.join(sorted(set(entry) - mirror_fields))}")
        rule_count = 0
        for field in prefix_fields:
            rules = entry.get(field, {})
            if not isinstance(rules, dict):
                error(f"access mirror {name} {field} must be an object")
            invalid = [key for key in rules if not isinstance(key, str) or not key.startswith(("sandbox_", "host_"))]
            if invalid:
                error(f"access mirror {name} {field} keys must use sandbox_/host_ prefixes: {', '.join(map(str, invalid))}")
            rule_count += len(rules)
        if not rule_count:
            error(f"access mirror {name} must contain at least one rule")
        mirrors[name] = entry

    projected = dict(config)
    projected["agent"] = {name: entry for name, entry in agents.items() if name not in aliases and name not in mirrors}
    projected.pop("plugins", None)
    projected["plugin"] = [item[1:] if item.startswith("~") else item for item in plugins]
    projected["plugin"] = [item.replace("@~", "@", 1) for item in projected["plugin"]]
    projected["plugin"] = [
        item + "/index.ts" if item.endswith("/opencode-rate-limit-fallback-mapped") else item
        for item in projected["plugin"]
    ]
    # The V1 checker encodes the V2-asserted deny/allow policy as global ask plus agent allow.
    projected["permission"] = dict(permission)
    projected["permission"]["grep"] = "ask"
    print(json.dumps(projected, ensure_ascii=False))
    if aliases:
        names = ", ".join(sorted(aliases))
        print(f"skipped (V2): Astra aliases ({len(aliases)}): {names}; their alias invariants were validated before projecting for the V1 checker", file=sys.stderr)
    if mirrors:
        names = ", ".join(sorted(mirrors))
        print(f"skipped (V2): Systematic access mirrors ({len(mirrors)}): {names}; their sandbox_/host_ access rules were validated before projecting for the V1 checker", file=sys.stderr)
    print("V2 runtime invariants passed; projected V2 plugin and grep shapes for the V1 checker", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error("usage: v2-runtime-config.py <opencode.json>")
    main(sys.argv[1])
