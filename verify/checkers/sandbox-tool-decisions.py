#!/usr/bin/env python3
"""Check explicit permission decisions for the sandbox tool surface fixture."""

import json
import sys
from pathlib import Path


DECISIONS = {"allow", "ask", "deny"}


def enabled_tools(agent, name):
    tools = agent.get("tools")
    if not isinstance(tools, dict):
        return False
    return tools.get(name) is True or (tools.get("*") is True and tools.get(name) is not False)


def check(config, fixture):
    if not isinstance(config, dict):
        return "error", "config must be a JSON object"
    if not isinstance(fixture, dict) or not isinstance(fixture.get("tools"), list) or not fixture["tools"]:
        return "error", "fixture tools must be a non-empty array"
    names = []
    for item in fixture["tools"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            return "error", "fixture tools must contain non-empty names"
        names.append(item["name"])
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        return "error", "duplicate fixture tools: " + ", ".join(duplicates[:5])

    gaps = []
    global_permissions = config.get("permission")
    if not isinstance(global_permissions, dict):
        global_permissions = {}
    for name in names:
        if global_permissions.get(name) not in DECISIONS:
            gaps.append(f"global.{name}")
    agents = config.get("agent")
    if not isinstance(agents, dict):
        agents = {}
    for agent_name, agent in agents.items():
        if not isinstance(agent, dict):
            continue
        permissions = agent.get("permission")
        if not isinstance(permissions, dict):
            permissions = {}
        for name in names:
            if enabled_tools(agent, name) and permissions.get(name) not in DECISIONS:
                gaps.append(f"{agent_name}.{name}")
    if gaps:
        shown = ", ".join(gaps[:5])
        remainder = len(gaps) - min(len(gaps), 5)
        suffix = f" (+{remainder} more; {len(gaps)} total)" if remainder else f" ({len(gaps)} total)"
        return "error", f"missing explicit decisions: {shown}{suffix}"
    return "clean", f"explicit decisions cover {len(names)} fixture tools and enabled agent tools"


def main(argv):
    if len(argv) != 3:
        return "error", "usage: sandbox-tool-decisions.py <config-json> <surface-fixture-json>"
    try:
        config = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        fixture = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return "error", f"could not read valid JSON: {exc}"
    return check(config, fixture)


if __name__ == "__main__":
    status, detail = main(sys.argv)
    print(f"{status}\t{detail}")
    raise SystemExit(0 if status == "clean" else 1)
