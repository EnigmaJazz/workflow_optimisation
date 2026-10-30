"""Check the read-only GitHub MCP on OpenCode V2 (queue Q44, section 9b on V2).

usage: v2-github-mcp-check.py <v2-opencode.json> <server-url> <password-file> <directory>
Prints one line: clean|error <TAB> detail.

Two parts, both read-only. Scoping comes from the generated V2 config: github_ro points at the read-only endpoint with the
read-only header, is off for every agent by default, and is granted only to the research agents that may use it. Liveness comes
from the running server: GET /api/mcp (basic auth, the server password) must list github_ro as connected, tried three times."""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

READERS = ("gentle-orchestrator", "explore")
READ_ONLY_URL = "https://api.githubcopilot.com/mcp/readonly"


def scoping_error(config):
    mcp = (config.get("mcp") or {}).get("github_ro") or {}
    if mcp.get("url") != READ_ONLY_URL or (mcp.get("headers") or {}).get("X-MCP-Readonly") != "true":
        return "github_ro must use the read-only endpoint with the X-MCP-Readonly header"
    if (config.get("tools") or {}).get("github_ro_*") is not False:
        return "github_ro_* must be off by default"
    agents = config.get("agent") or {}
    for name in READERS:
        agent = agents.get(name) or {}
        if (agent.get("tools") or {}).get("github_ro_*") is not True or (agent.get("permission") or {}).get("github_ro_*") != "allow":
            return f"{name} must be granted github_ro_* (tools true, permission allow)"
    extra = sorted(n for n, a in agents.items() if n not in READERS and isinstance(a, dict) and (a.get("tools") or {}).get("github_ro_*") is True)
    if extra:
        return f"github_ro_* is granted to agents that are not read-only researchers: {', '.join(extra[:4])}"
    return None


def connected(url, password, directory):
    token = base64.b64encode(f"opencode:{password}".encode()).decode()
    request = urllib.request.Request(url.rstrip("/") + "/api/mcp", headers={"Authorization": f"Basic {token}", "x-opencode-directory": directory})
    with urllib.request.urlopen(request, timeout=12) as response:
        body = json.loads(response.read().decode("utf-8"))
    for server in body.get("data", []) if isinstance(body, dict) else []:
        if isinstance(server, dict) and server.get("name") == "github_ro":
            return (server.get("status") or {}).get("status") == "connected"
    return False


def main(argv):
    config_path, url, password_file, directory = Path(argv[1]), argv[2], Path(argv[3]), argv[4]
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error\tcannot read the V2 config {config_path}: {exc}")
        return 0
    problem = scoping_error(config)
    if problem:
        print(f"error\t{problem}")
        return 0
    try:
        password = password_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        print(f"error\tcannot read the V2 server password file {password_file}: {exc}")
        return 0
    last = "github_ro is not listed as connected"
    for attempt in range(3):
        try:
            if connected(url, password, directory):
                print("clean\tgithub_ro is connected on the V2 server and scoped to the two read-only research agents")
                return 0
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last = f"the V2 server did not answer /api/mcp ({type(exc).__name__}: {exc})"
        if attempt < 2:
            print(f"   info: github_ro not connected yet (attempt {attempt + 1} of 3); retrying", file=sys.stderr)
            time.sleep(float(os.environ.get("WORKFLOW_VERIFY_RETRY_DELAY", "2")))
    print(f"error\tGITHUB_RO_NOT_CONNECTED: {last}; check the token and the sandbox egress")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
