#!/usr/bin/env python3
"""Validate security-relevant invariants in the OpenCode V2 runtime config."""

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
    if not isinstance(config, dict):
        error("runtime config must be an object")
    plugins = config.get("plugin")
    if plugins is None:
        plugins = config.get("plugins")
    if not isinstance(plugins, list):
        error("plugin list is missing")
    magic = [item for item in plugins if isinstance(item, str) and "opencode-magic-context@" in item]
    fallback = [item for item in plugins if isinstance(item, str) and "opencode-rate-limit-fallback-mapped" in item]
    if len(magic) != 1:
        error("expected exactly one opencode-magic-context plugin ref")
    if not re.fullmatch(r"@cortexkit/opencode-magic-context@~[0-9]+\.[0-9]+\.[0-9]+", magic[0]):
        error("opencode-magic-context plugin ref must be a scoped exact V2 version pin")
    if len(fallback) != 1:
        error("expected exactly one opencode-rate-limit-fallback-mapped fork ref")
    if not (fallback[0].endswith("/opencode-rate-limit-fallback-mapped") or fallback[0].endswith("/index.ts")):
        error("opencode-rate-limit-fallback-mapped fork ref must name its directory or index.ts")
    permission = config.get("permission")
    if not isinstance(permission, dict) or permission.get("grep") != "deny":
        error("global permission.grep must be deny")
    agents = config.get("agent")
    orchestrator = agents.get("gentle-orchestrator") if isinstance(agents, dict) else None
    if not isinstance(orchestrator, dict) or not isinstance(orchestrator.get("permission"), dict) or orchestrator["permission"].get("grep") != "allow":
        error("gentle-orchestrator permission.grep must be allow")
    mcp = config.get("mcp")
    if not isinstance(mcp, dict) or not isinstance(mcp.get("github_ro"), dict):
        error("mcp.github_ro must be present as an object")
    tools = config.get("tools")
    if not isinstance(tools, dict) or tools.get("github_ro_*") is not False:
        error('tools["github_ro_*"] must be false')
    print("V2 runtime invariants passed: plugin refs, grep permissions, github_ro MCP and tool disablement", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error("usage: v2-runtime-config.py <config-json>")
    main(sys.argv[1])
