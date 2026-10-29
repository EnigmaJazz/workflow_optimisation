"""Execute the Q90 T3b Planner production predicate and mutation controls."""

import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path
try:
    from tests.verifier_source import verifier_text
except ImportError:  # run as a script from tests/
    from verifier_source import verifier_text

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH, SCRIPT = REPO / "global-config/opencode.json", REPO / "verify-workflow.sh"
BEGIN, END = "// planner-handoff:begin", "// planner-handoff:end"
PLANNER, EVIDENCE = "planner", "planner-evidence"
COORDINATORS = ("gentle-orchestrator", "pm-odd", "pm-systematic")
ADVISORS = (
    "advisor-design-pre", "advisor-integration-pre", "advisor-testing-pre",
    "advisor-security-pre", "advisor-maintainability-pre", "advisor-design-post",
    "advisor-integration-post", "advisor-testing-post", "advisor-security-post",
    "advisor-maintainability-post", "advisor-gemini-pre", "advisor-gemini-post",
)
READ_TOOLS = ("read", "codegraph_codegraph_explore", "ast_grep_search", "aft_outline",
              "aft_zoom", "aft_search", "aft_callgraph", "aft_inspect", "sandbox_read",
              "sandbox_list", "sandbox_grep", "sandbox_diff")
MUTATION_TOOLS = ("bash", "edit", "write", "sandbox_bash", "sandbox_edit", "sandbox_write",
                  "sandbox_apply_patch", "sandbox_apply", "sandbox_copy_in", "sandbox_copy_out",
                  "sandbox_discard", "sandbox_finish", "aft_import", "aft_safety", "ast_grep_replace")


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def extract_block():
    text = verifier_text()
    start, end = text.find(BEGIN), text.find(END)
    return None if start < 0 or end < 0 or end < start else text[start:end + len(END)]


def run_block(agents, gp):
    """Execute the extracted production predicate and return its failure list."""
    block = extract_block()
    if block is None:
        raise AssertionError("planner-handoff block not found in verify-workflow.sh")
    runtime = shutil.which("bun")
    if runtime is None:
        raise unittest.SkipTest("Bun runtime not found; production predicate cannot execute")
    program = (
        "const show=(v)=>JSON.stringify(v);\n"
        "const cfgTool=(a,t)=>a&&typeof a.tools===\"object\"?a.tools[t]:undefined;\n"
        "const cfgPerm=(a,t)=>a&&typeof a.permission===\"object\"?a.permission[t]:undefined;\n"
        + block
        + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        + "\nprocess.stdout.write(JSON.stringify(plannerHandoffFailures(input.agents,input.gp)))\n"
    )
    try:
        proc = subprocess.run([runtime, "-e", program], input=json.dumps({"agents": agents, "gp": gp}),
                              capture_output=True, text=True, check=False)
    except PermissionError:
        raise unittest.SkipTest("sandbox policy denies Bun execution")
    if proc.returncode != 0:
        raise AssertionError(f"production predicate failed: {proc.stdout}{proc.stderr}")
    return json.loads(proc.stdout)

class RealConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.agents, cls.gp = cls.config["agent"], cls.config["permission"]
    def test_predicate_models_and_read_only_surface(self):
        self.assertEqual(run_block(self.agents, self.gp), [])
        self.assertEqual((self.agents[PLANNER]["model"], self.agents[PLANNER]["variant"],
                          self.agents[PLANNER]["mode"], self.agents[PLANNER]["hidden"]),
                         ("openai/gpt-6.1-sol", "high", "subagent", True))
        self.assertEqual((self.agents[EVIDENCE]["model"], self.agents[EVIDENCE]["variant"],
                          self.agents[EVIDENCE]["mode"], self.agents[EVIDENCE]["hidden"]),
                         ("openai/gpt-6-luna", "medium", "subagent", True))
        for name in (PLANNER, EVIDENCE):
            for tool_id in READ_TOOLS:
                self.assertIs(self.agents[name]["tools"].get(tool_id), True, (name, tool_id))
                self.assertEqual(self.agents[name]["permission"].get(tool_id), "allow", (name, tool_id))
            for tool_id in MUTATION_TOOLS + ("grep", "ctx_memory"):
                self.assertIs(self.agents[name]["tools"].get(tool_id), False, (name, tool_id))
                self.assertEqual(self.agents[name]["permission"].get(tool_id), "deny", (name, tool_id))
        self.assertIs(self.agents[PLANNER]["tools"].get("task"), True)
        self.assertIs(self.agents[EVIDENCE]["tools"].get("task"), False)
        self.assertEqual(self.agents[EVIDENCE]["permission"].get("task"), {"*": "deny"})
    def test_host_acts_task_map_dispatch_grants_and_global_denies(self):
        planner = self.agents[PLANNER]
        self.assertEqual((planner["permission"]["host_plan_write"],
                          planner["permission"]["host_gate_verdict"],
                          planner["permission"]["host_task_mark"]), ("ask", "ask", "deny"))
        self.assertEqual((planner["tools"]["host_plan_write"], planner["tools"]["host_gate_verdict"],
                          planner["tools"]["host_task_mark"]), (True, True, False))
        task = planner["permission"]["task"]
        self.assertEqual(task.get("*"), "deny")
        self.assertEqual(set(task), set(ADVISORS) | {EVIDENCE, "explore", "*"})
        for name in ADVISORS + (EVIDENCE, "explore"):
            self.assertEqual(task.get(name), "allow", name)
        for writer in ("odd-apply", "gentle-ai-worker", "gentle-ai-worker-local",
                       "gentle-ai-verify", "general", "systematic-implementer"):
            self.assertNotEqual(task.get(writer), "allow", writer)
        granted = {name for name, agent in self.agents.items()
                   if agent.get("permission", {}).get("task", {}).get(PLANNER) == "allow"}
        self.assertEqual(granted, set(COORDINATORS))
        for host in ("host_plan_write", "host_gate_verdict", "host_task_mark"):
            self.assertEqual(self.gp.get(host), "deny", host)
    def test_evidence_agent_and_prompts(self):
        evidence = self.agents[EVIDENCE]
        for host in ("host_plan_write", "host_gate_verdict", "host_task_mark"):
            self.assertEqual(evidence["permission"].get(host), "deny", host)
        for needle in ("Gate 1", "Gate 2", "BEFORE the PM completes or ticks the unit",
                       "BEFORE the work-unit commit", "Run Gate 2 again after any revision",
                       "not Gate 2 input",
                       "TECHNICAL verdict only", "never approves delivery",
                       "Never dispatch a writer or a review lens", "host_plan_write",
                       "host_gate_verdict", "`BLOCKED`", "Native built-in `grep` is unavailable"):
            self.assertIn(needle, self.agents[PLANNER]["prompt"], needle)
        for needle in ("facts only", "path:line", "no task dispatch", "EXTERNAL_CONTEXT_REQUIRED",
                       "Native built-in `grep` is unavailable"):
            self.assertIn(needle, evidence["prompt"], needle)
    def test_wiring_and_narrow_sweeps(self):
        verifier = verifier_text()
        for needle in (
            "for (const failure of plannerHandoffFailures(deployedAgents,gp)) fail(failure)",
            'const planWriterAgents=[...coordinatorAgents,"planner"]',
            'const advisorDispatchAgents=[...coordinatorAgents,"planner"]',
            'const coordinatorAgents=["gentle-orchestrator",...pmAgents]',
            "hostPlanWriteGrantSweepFailures(deployedAgents,planWriterAgents)",
            "geminiAdvisorRouteFailures(deployedAgents,geminiFallback,advisorDispatchAgents)",
            '"planner","planner-evidence"',
        ):
            self.assertIn(needle, verifier)
        inventory = next(line for line in verifier.splitlines()
                         if line.startswith("  const mutationTools=["))
        config_text = CONFIG_PATH.read_text(encoding="utf-8")
        for tool_id in ("aft_import", "aft_safety", "ast_grep_replace"):
            self.assertIn(f'"{tool_id}"', inventory, tool_id)
            self.assertEqual(config_text.count(f'"{tool_id}": false'), 2, tool_id)
            self.assertEqual(config_text.count(f'"{tool_id}": "deny"'), 2, tool_id)
        self.assertNotIn('const coordinatorAgents=["gentle-orchestrator",...pmAgents,"planner"]', verifier)

class NegativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
    def mutated(self):
        return copy.deepcopy(self.config["agent"]), copy.deepcopy(self.config["permission"])
    def assert_detected(self, agents, gp, expected):
        failures = run_block(agents, gp)
        self.assertIn(expected, failures, f"expected {expected!r} in {failures!r}")
    def test_planner_mutation_and_host_controls(self):
        agents, gp = self.mutated()
        agents[PLANNER]["permission"]["edit"] = "allow"
        agents[PLANNER]["tools"]["read"] = False
        agents[PLANNER]["permission"]["ctx_memory"] = "allow"
        del agents[PLANNER]["permission"]["task"][EVIDENCE]
        agents[PLANNER]["permission"].update(
            {"host_plan_write": "allow", "host_gate_verdict": "deny", "host_task_mark": "ask"})
        failures = run_block(agents, gp)
        for expected in ("PLANNER_MUTATION_EXPOSED: edit", "PLANNER_READ_TOOL_MISSING: planner.read",
                         "PLANNER_MEMORY_EXPOSED",
                         "PLANNER_EVIDENCE_LANE_MISSING: planner-evidence",
                         'PLANNER_HOST_PLAN_WRITE_NOT_ASK: "allow"',
                         'PLANNER_HOST_GATE_VERDICT_NOT_ASK: "deny"',
                         'PLANNER_HOST_TASK_MARK_NOT_DENY: "ask"'):
            self.assertIn(expected, failures)
    def test_model_variant_task_and_dispatch_controls(self):
        for mutate, expected in (
            (lambda a: a[PLANNER].__setitem__("model", "openai/gpt-6-luna"),
             'PLANNER_MODEL_MISMATCH: "openai/gpt-6-luna"'),
            (lambda a: a[PLANNER].__setitem__("variant", "medium"),
             'PLANNER_VARIANT_MISMATCH: "medium"'),
            (lambda a: a[PLANNER]["tools"].__setitem__("task", False),
             "PLANNER_TASK_TOOL_NOT_ENABLED"),
            (lambda a: a[PLANNER]["permission"]["task"].__setitem__("*", "allow"),
             'PLANNER_TASK_WILDCARD_NOT_DENIED: "allow"'),
            (lambda a: a[PLANNER]["permission"]["task"].__setitem__("odd-apply", "allow"),
             "PLANNER_WRITER_DISPATCH_GRANTED: odd-apply"),
            (lambda a: a["pm-systematic"]["permission"]["task"].pop(PLANNER),
             "PLANNER_NOT_DISPATCHABLE: pm-systematic"),
            (lambda a: a["odd-apply"]["permission"].setdefault("task", {}).__setitem__(PLANNER, "allow"),
             "PLANNER_DISPATCH_GRANT_OUTSIDE_COORDINATORS: odd-apply"),
        ):
            with self.subTest(expected=expected):
                agents, gp = self.mutated()
                mutate(agents)
                self.assert_detected(agents, gp, expected)
    def test_evidence_global_and_empty_controls(self):
        agents, gp = self.mutated()
        agents[EVIDENCE]["tools"]["task"] = True
        agents[EVIDENCE]["permission"]["task"] = {"*": "allow"}
        agents[EVIDENCE]["permission"]["sandbox_bash"] = "allow"
        failures = run_block(agents, gp)
        for expected in ("PLANNER_EVIDENCE_TASK_EXPOSED",
                         "PLANNER_EVIDENCE_MUTATION_EXPOSED: sandbox_bash"):
            self.assertIn(expected, failures)
        for host in ("host_plan_write", "host_gate_verdict", "host_task_mark"):
            with self.subTest(host=host):
                agents, gp = self.mutated()
                gp[host] = "ask"
                self.assert_detected(agents, gp, "PLANNER_GLOBAL_HOST_DENY_CHANGED")
        failures = run_block({}, {})
        self.assertIn("PLANNER_AGENT_MISSING: planner", failures)
        self.assertIn("PLANNER_EVIDENCE_AGENT_MISSING: planner-evidence", failures)

    def test_new_mutator_controls_per_agent_and_surface(self):
        for name, tools_tag, perm_tag in (
            (PLANNER, "PLANNER_MUTATION_TOOL_EXPOSED", "PLANNER_MUTATION_EXPOSED"),
            (EVIDENCE, "PLANNER_EVIDENCE_MUTATION_EXPOSED", "PLANNER_EVIDENCE_MUTATION_EXPOSED"),
        ):
            for tool_id in ("aft_import", "aft_safety", "ast_grep_replace"):
                for key, tag in (("tools", tools_tag), ("permission", perm_tag)):
                    with self.subTest(agent=name, tool=tool_id, surface=key):
                        agents, gp = self.mutated()
                        agents[name][key][tool_id] = True if key == "tools" else "allow"
                        self.assert_detected(agents, gp, f"{tag}: {tool_id}")
