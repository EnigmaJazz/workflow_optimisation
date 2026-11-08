#!/usr/bin/env python3
"""Validate V2-only runtime invariants and project the config for the V1 checker; derived refs use the scoped Magic Context pin and the fallback vendor directory.

A removed entry holds no grant absent from its still-projected reference agent or alias base, in the same rule order, so projection hides no authority. Any deviation from the real derivation remains visible to every checker sweep.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path


def error(message):
    print(f"V2_RUNTIME_CONFIG_INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_derivation():
    derive_path = Path(__file__).resolve().parents[2] / "scripts" / "derive-v2-config.py"
    try:
        spec = importlib.util.spec_from_file_location("derive_v2_config", derive_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot create module spec for {derive_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        error(f"cannot load V2 config derivation {derive_path}: {exc}")


def ordered_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


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
    derive = load_derivation()
    aliases = {}
    for name, entry in agents.items():
        if not name.endswith(derive.ASTRA_SUFFIX):
            continue
        base_name = name[:-len(derive.ASTRA_SUFFIX)]
        base = agents.get(base_name)
        if not isinstance(base, dict) or not isinstance(entry, dict):
            continue
        if not derive.astra_alias_wanted(base_name, base):
            continue
        expected = json.loads(json.dumps(base))
        expected.update({
            "description": f"{base.get('description') or base_name} — selectable Astra upgrade",
            "hidden": True,
            "model": derive.ASTRA_MODEL,
            "variant": derive.ASTRA_VARIANT,
        })
        if ordered_json(entry) == ordered_json(expected):
            aliases[name] = base_name

    mirrors = {}
    for name, reference in derive.ACCESS_MIRRORS.items():
        entry = agents.get(name)
        ref = agents.get(reference)
        if not isinstance(entry, dict) or not isinstance(ref, dict):
            continue
        expected = {}
        for field in ("permission", "tools"):
            ref_rules = ref.get(field) or {}
            if not isinstance(ref_rules, dict):
                continue
            rules = {key: value for key, value in ref_rules.items()
                     if isinstance(key, str) and key.startswith(derive.MIRRORED_PREFIXES)}
            if rules:
                expected[field] = rules
        if expected and ordered_json(entry) == ordered_json(expected):
            mirrors[name] = reference

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
    for name, base_name in aliases.items():
        print(f"skipped (V2): {name} = Astra alias of {base_name}", file=sys.stderr)
    for name, reference in mirrors.items():
        print(f"skipped (V2): {name} = mirror of {reference}", file=sys.stderr)
    print("V2 runtime invariants passed; projected V2 plugin and grep shapes for the V1 checker", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error("usage: v2-runtime-config.py <opencode.json>")
    main(sys.argv[1])
