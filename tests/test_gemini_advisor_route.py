"""Durable checks for the Q76 Gemini API advisor route.

The Argon advisors (``advisor-gemini-pre``/``-post``) may only delegate to the Flash evidence
gatherer (``advisor-gemini-evidence``). The gatherer keeps the shared sandbox-only advisor surface,
so it can run tests but never reach the host. Only the orchestrator and the two PMs may dispatch
the advisors; no other agent may dispatch the gatherer. None of the three may fall back to another
model.

Two layers are checked:

* the tracked ``global-config`` sources, parsed directly;
* the verifier's own ``geminiAdvisorRouteFailures`` block, extracted from ``verify-workflow.sh`` and
  EXECUTED with node against the real sources and against mutated fixtures, so the verifier check
  cannot drift from these rules.

The PositiveControl classes prove each validator can fail, so a green run is not vacuous.

Run: python3 -m unittest tests.test_gemini_advisor_route -v
"""

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"
FALLBACK_PATH = REPO / "global-config" / "rate-limit-fallback.json"
SCRIPT = REPO / "verify-workflow.sh"

ADVISORS = ("advisor-gemini-pre", "advisor-gemini-post")
EVIDENCE = "advisor-gemini-evidence"
ARGON = "google/gemini-4-argon"
FLASH = "google/gemini-3.8-flash"
DISPATCHERS = ("gentle-orchestrator", "pm-odd", "pm-systematic")
HOST_ROUTES = (
    "edit",
    "write",
    "bash",
    "sandbox_apply",
    "sandbox_copy_in",
    "sandbox_copy_out",
    "sandbox_discard",
    "sandbox_finish",
)
GRANTS = ("allow", "ask")

BLOCK_BEGIN = "// gemini-advisor-route:begin"
BLOCK_END = "// gemini-advisor-route:end"


def _load_model_family():
    spec = importlib.util.spec_from_file_location(
        "q76_model_independence", REPO / "tests" / "test_model_independence.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.model_family


model_family = _load_model_family()


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _tools(agent):
    tools = agent.get("tools") if isinstance(agent, dict) else None
    return tools if isinstance(tools, dict) else {}


def _perms(agent):
    perms = agent.get("permission") if isinstance(agent, dict) else None
    return perms if isinstance(perms, dict) else {}


def shape_violations(data):
    """Return (agent, reason) pairs for every S2 shape defect."""
    agents = data.get("agent", {})
    out = []
    for name in ADVISORS:
        agent = agents.get(name)
        if not isinstance(agent, dict):
            out.append((name, "agent is absent"))
            continue
        if agent.get("model") != ARGON:
            out.append((name, f"model is {agent.get('model')!r}, not {ARGON!r}"))
        tools, perms = _tools(agent), _perms(agent)
        if tools.get("*") is not False or tools.get("task") is not True:
            out.append((name, "tools must be '*': false with only task: true"))
        for tool, value in tools.items():
            if value is True and tool != "task":
                out.append((name, f"tool {tool} is enabled"))
        for tool, value in perms.items():
            if tool != "task" and value in GRANTS:
                out.append((name, f"permission {tool} is {value!r}"))
        if perms.get("task") != {"*": "deny", EVIDENCE: "allow"}:
            out.append((name, f"task scope is {perms.get('task')!r}"))
        if perms.get("ctx_memory") != "deny":
            out.append((name, "ctx_memory is not denied"))
    agent = agents.get(EVIDENCE)
    if not isinstance(agent, dict):
        out.append((EVIDENCE, "agent is absent"))
    else:
        if agent.get("model") != FLASH:
            out.append((EVIDENCE, f"model is {agent.get('model')!r}, not {FLASH!r}"))
        tools, perms = _tools(agent), _perms(agent)
        for route in HOST_ROUTES:
            if tools.get(route) is True or perms.get(route) != "deny":
                out.append((EVIDENCE, f"host route {route} is not denied"))
        if tools.get("task") is not False or perms.get("task") != {"*": "deny"}:
            out.append((EVIDENCE, "task is not deny-all"))
        if perms.get("ctx_memory") != "deny":
            out.append((EVIDENCE, "ctx_memory is not denied"))
    return out


def dispatch_violations(data):
    """Return (agent, reason) pairs for every S5 dispatch defect."""
    agents = data.get("agent", {})
    out = []
    for dispatcher in DISPATCHERS:
        task = _perms(agents.get(dispatcher, {})).get("task")
        for advisor in ADVISORS:
            if not isinstance(task, dict) or task.get(advisor) != "allow":
                out.append((dispatcher, f"cannot dispatch {advisor}"))
    for name, agent in agents.items():
        if name in ADVISORS:
            continue
        task = _perms(agent).get("task")
        if not isinstance(task, dict):
            continue
        effective = task[EVIDENCE] if EVIDENCE in task else task.get("*")
        if effective != "deny":
            out.append((name, f"may dispatch {EVIDENCE} ({effective!r})"))
    return out


def fallback_violations(fallback):
    """Return reasons for every S4 fallback-policy defect."""
    out = []
    no_fallback = fallback.get("noFallbackAgents", [])
    for name in (*ADVISORS, EVIDENCE):
        if name not in no_fallback:
            out.append(f"{name} is not in noFallbackAgents")
    if "google" not in fallback.get("startProviders", []):
        out.append("google is not a start provider")
    rule = fallback.get("providerFallbacks", {}).get("google")
    if not isinstance(rule, list) or not rule:
        out.append("providerFallbacks.google is missing or empty")
    elif all(entry.get("providerID") == "google" for entry in rule):
        out.append("providerFallbacks.google has no non-google target")
    return out


def extract_block(text):
    """Return the verifier's marked geminiAdvisorRouteFailures block, or None."""
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start < 0 or end < 0 or end < start:
        return None
    return text[start:end]


def run_verifier_block(agents, fallback):
    """Execute the extracted verifier block under node; return its failure list."""
    block = extract_block(SCRIPT.read_text(encoding="utf-8"))
    if block is None:
        raise AssertionError("gemini-advisor-route block not found in verify-workflow.sh")
    program = (
        block
        + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'))"
        + "\nprocess.stdout.write(JSON.stringify(geminiAdvisorRouteFailures(input.agents,input.fallback)))\n"
    )
    proc = subprocess.run(
        ["node", "-e", program],
        input=json.dumps({"agents": agents, "fallback": fallback}),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"verifier block failed to run: {proc.stderr}")
    return json.loads(proc.stdout)


class RealConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_json(CONFIG_PATH)
        cls.fallback = load_json(FALLBACK_PATH)

    def test_agent_shapes(self):
        self.assertEqual(shape_violations(self.data), [])

    def test_dispatch_scope(self):
        self.assertEqual(dispatch_violations(self.data), [])

    def test_fallback_policy(self):
        self.assertEqual(fallback_violations(self.fallback), [])

    def test_models_are_gemini_family(self):
        for name in (*ADVISORS, EVIDENCE):
            with self.subTest(agent=name):
                self.assertEqual(model_family(self.data["agent"][name]["model"]), "gemini")

    def test_verifier_block_passes_real_sources(self):
        self.assertEqual(run_verifier_block(self.data["agent"], self.fallback), [])


class PositiveControl(unittest.TestCase):
    """Prove every validator, and the extracted verifier block, can fail."""

    @classmethod
    def setUpClass(cls):
        cls.data = load_json(CONFIG_PATH)
        cls.fallback = load_json(FALLBACK_PATH)

    def mutated(self):
        return copy.deepcopy(self.data), copy.deepcopy(self.fallback)

    def test_advisor_with_a_read_tool_fails(self):
        data, fallback = self.mutated()
        data["agent"]["advisor-gemini-pre"]["permission"]["sandbox_read"] = "allow"
        self.assertIn(("advisor-gemini-pre", "permission sandbox_read is 'allow'"), shape_violations(data))
        self.assertIn(
            "GEMINI_ADVISOR_TOOL_EXPOSED: advisor-gemini-pre.sandbox_read",
            run_verifier_block(data["agent"], fallback),
        )

    def test_advisor_with_a_wider_task_scope_fails(self):
        data, fallback = self.mutated()
        data["agent"]["advisor-gemini-post"]["permission"]["task"]["explore"] = "allow"
        self.assertTrue(any(name == "advisor-gemini-post" for name, _ in shape_violations(data)))
        self.assertTrue(
            any(f.startswith("GEMINI_ADVISOR_TASK_SCOPE_MISMATCH: advisor-gemini-post")
                for f in run_verifier_block(data["agent"], fallback))
        )

    def test_evidence_agent_with_a_host_route_fails(self):
        data, fallback = self.mutated()
        data["agent"][EVIDENCE]["permission"]["sandbox_finish"] = "ask"
        self.assertIn((EVIDENCE, "host route sandbox_finish is not denied"), shape_violations(data))
        self.assertIn(
            f"GEMINI_EVIDENCE_HOST_ROUTE_EXPOSED: {EVIDENCE}.sandbox_finish",
            run_verifier_block(data["agent"], fallback),
        )

    def test_pm_dispatching_the_evidence_agent_fails(self):
        data, fallback = self.mutated()
        data["agent"]["pm-odd"]["permission"]["task"][EVIDENCE] = "allow"
        self.assertIn(("pm-odd", f"may dispatch {EVIDENCE} ('allow')"), dispatch_violations(data))
        self.assertIn(
            f"GEMINI_EVIDENCE_DISPATCHABLE: pm-odd={json.dumps('allow')}",
            run_verifier_block(data["agent"], fallback),
        )

    def test_orchestrator_ask_default_reaching_the_evidence_agent_fails(self):
        data, fallback = self.mutated()
        del data["agent"]["gentle-orchestrator"]["permission"]["task"][EVIDENCE]
        self.assertIn(
            ("gentle-orchestrator", f"may dispatch {EVIDENCE} ('ask')"), dispatch_violations(data)
        )

    def test_dispatcher_losing_an_advisor_fails(self):
        data, fallback = self.mutated()
        del data["agent"]["pm-systematic"]["permission"]["task"]["advisor-gemini-pre"]
        self.assertIn(("pm-systematic", "cannot dispatch advisor-gemini-pre"), dispatch_violations(data))
        self.assertIn(
            "GEMINI_ADVISOR_NOT_DISPATCHABLE: pm-systematic.advisor-gemini-pre",
            run_verifier_block(data["agent"], fallback),
        )

    def test_fallback_allowed_fails(self):
        data, fallback = self.mutated()
        fallback["noFallbackAgents"].remove(EVIDENCE)
        self.assertIn(f"{EVIDENCE} is not in noFallbackAgents", fallback_violations(fallback))
        self.assertIn(
            f"GEMINI_ADVISOR_FALLBACK_ALLOWED: {EVIDENCE}",
            run_verifier_block(data["agent"], fallback),
        )

    def test_google_only_emergency_rule_fails(self):
        _, fallback = self.mutated()
        fallback["providerFallbacks"]["google"] = [{"providerID": "google", "modelID": "x"}]
        self.assertIn("providerFallbacks.google has no non-google target", fallback_violations(fallback))

    def test_missing_agents_are_reported_by_the_verifier_block(self):
        failures = run_verifier_block({}, {})
        for name in (*ADVISORS, EVIDENCE):
            self.assertTrue(any(f.endswith(f"_MISSING: {name}") for f in failures), name)


if __name__ == "__main__":
    unittest.main()
