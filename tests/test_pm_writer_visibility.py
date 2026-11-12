"""Q137: every writer a project manager may dispatch must be visible to it.

``hidden: true`` keeps an agent out of the runtime delegation catalog, so a PM
that holds ``permission.task.<name> = "allow"`` still cannot dispatch that agent.
The visibility fix must not widen dispatch to anyone else: this module also pins
that every non-PM task-capable agent resolves ``odd-apply`` and ``gentle-ai-worker``
to ``deny``.

Run: python3 -m unittest tests/test_pm_writer_visibility.py -v
"""

import copy
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"

PM_NAMES = ("pm-odd", "pm-systematic")
PM_ONLY_WRITERS = ("odd-apply", "gentle-ai-worker")

# Task-map targets the runtime supplies outside this config (Systematic plugin
# agents and the generated ``-astra`` alias), so they carry no ``hidden`` key here.
RUNTIME_ONLY_AGENTS = frozenset({
    "bug-reproduction-validator",
    "correctness-reviewer",
    "gentle-ai-verify-astra",
    "project-standards-reviewer",
    "repo-research-analyst",
    "systematic-implementer",
    "testing-reviewer",
})

# The writers Q137 unhides, grouped by the PM that dispatches them.
PM_WRITERS = {
    "pm-odd": ("odd-apply", "gentle-ai-worker", "gentle-ai-worker-local"),
    "pm-systematic": (
        "frontend-apply",
        "frontend-apply-local",
        "gentle-ai-worker",
        "gentle-ai-worker-local",
    ),
}

# Pre-existing orchestrator task rules for the ODD writers. The visibility fix
# must not move them; ``gentle-ai-worker-local`` is an existing allow, not a new grant.
ORCHESTRATOR_TASK_RULES = {
    "odd-apply": "deny",
    "gentle-ai-worker": "deny",
    "gentle-ai-worker-local": "allow",
}

# Unhiding a writer must not hand the orchestrator any mutation surface.
ORCHESTRATOR_MUTATION_DENIES = (
    "edit", "write", "bash",
    "sandbox_bash", "sandbox_edit", "sandbox_write", "sandbox_apply_patch",
    "sandbox_apply", "sandbox_copy_in", "sandbox_copy_out",
    "sandbox_discard", "sandbox_finish",
)


def load_agents(path=CONFIG_PATH):
    return json.loads(path.read_text(encoding="utf-8"))["agent"]


def effective_task(agent, target):
    """The rule a task dispatch to ``target`` resolves to inside the agent's own map.

    V2 silently allows a tool or target with no matching rule (the reason
    ``scripts/derive-v2-config.py`` demands an explicit rule per sandbox tool), and
    the global permission block carries no ``task`` rule, so an absent map, an
    absent key and an absent wildcard all resolve to ``"allow"``.
    """
    task = (agent.get("permission") or {}).get("task")
    if not isinstance(task, dict):
        return "allow"
    return task.get(target, task.get("*", "allow"))


def pm_writer_dispatch_failures(agents, writers=PM_ONLY_WRITERS, pms=PM_NAMES):
    """Return ``"<agent> -> <writer>: <effect>"`` for every non-PM task-capable grant."""
    failures = []
    for name, agent in agents.items():
        if name in pms:
            continue
        if (agent.get("tools") or {}).get("task") is False:
            continue
        for writer in writers:
            effect = effective_task(agent, writer)
            if effect != "deny":
                failures.append(f"{name} -> {writer}: {effect} (no deny rule)")
    return failures


def hidden_pm_targets(agents, pms=PM_NAMES, runtime_only=RUNTIME_ONLY_AGENTS):
    """Return ``"<pm> -> <agent>: <reason>"`` for every hidden PM task target.

    A target the config does not define is skipped only when it is a known
    runtime-provided agent; an unknown name is reported, so a typo never passes.
    """
    failures = []
    for pm in pms:
        task = agents[pm]["permission"]["task"]
        for name, effect in task.items():
            if name == "*" or effect != "allow":
                continue
            agent = agents.get(name)
            if agent is None:
                if name not in runtime_only:
                    failures.append(f"{pm} -> {name}: allowed but defined nowhere")
                continue
            if agent.get("hidden") is True:
                failures.append(f"{pm} -> {name}: hidden agent cannot be dispatched")
    return failures


class RealConfig(unittest.TestCase):
    """The live config: every PM task target is dispatchable and authority is unchanged."""

    def setUp(self):
        self.agents = load_agents()

    def test_every_allowed_pm_task_target_is_dispatchable(self):
        self.assertEqual(hidden_pm_targets(self.agents), [])

    def test_pm_writers_are_visible(self):
        for pm, writers in PM_WRITERS.items():
            task = self.agents[pm]["permission"]["task"]
            self.assertEqual(task.get("*"), "deny", pm)
            for writer in writers:
                with self.subTest(pm=pm, writer=writer):
                    self.assertEqual(task.get(writer), "allow")
                    self.assertIs(self.agents[writer]["hidden"], False)

    def test_orchestrator_authority_is_unchanged(self):
        permission = self.agents["gentle-orchestrator"]["permission"]
        for writer, expected in ORCHESTRATOR_TASK_RULES.items():
            self.assertEqual(permission["task"].get(writer), expected, writer)
        for tool in ORCHESTRATOR_MUTATION_DENIES:
            self.assertEqual(permission.get(tool), "deny", tool)

    def test_no_non_pm_task_capable_agent_can_dispatch_a_pm_only_writer(self):
        self.assertEqual(pm_writer_dispatch_failures(self.agents), [])


class PositiveControl(unittest.TestCase):
    """Prove each check can fail; a green run must not be vacuous."""

    def test_hidden_allowed_writer_is_reported(self):
        agents = copy.deepcopy(load_agents())
        for name in ("odd-apply", "gentle-ai-worker", "gentle-ai-worker-local"):
            agents[name]["hidden"] = True
        failures = hidden_pm_targets(agents)
        for pm, name in (
            ("pm-odd", "odd-apply"),
            ("pm-odd", "gentle-ai-worker"),
            ("pm-odd", "gentle-ai-worker-local"),
            ("pm-systematic", "gentle-ai-worker"),
        ):
            with self.subTest(pm=pm, agent=name):
                expected = f"{pm} -> {name}: hidden agent cannot be dispatched"
                self.assertIn(expected, failures)

    def test_unknown_allowed_target_is_reported(self):
        agents = copy.deepcopy(load_agents())
        agents["pm-odd"]["permission"]["task"]["not-a-real-agent"] = "allow"
        self.assertIn(
            "pm-odd -> not-a-real-agent: allowed but defined nowhere",
            hidden_pm_targets(agents),
        )

    def test_a_denied_target_need_not_be_visible(self):
        agents = copy.deepcopy(load_agents())
        agents["odd-apply"]["hidden"] = True
        agents["pm-odd"]["permission"]["task"]["odd-apply"] = "deny"
        self.assertEqual(hidden_pm_targets(agents), [])

    def test_frontend_dev_keeps_its_legitimate_task_allows(self):
        agents = load_agents()
        for target in ("frontend-apply", "frontend-apply-local", "vision"):
            with self.subTest(target=target):
                self.assertEqual(effective_task(agents["frontend-dev"], target), "allow")

    def test_a_missing_wildcard_reopens_the_writer_gap(self):
        agents = copy.deepcopy(load_agents())
        del agents["frontend-dev"]["permission"]["task"]["*"]
        self.assertIn(
            "frontend-dev -> odd-apply: allow (no deny rule)",
            pm_writer_dispatch_failures(agents),
        )

    def test_an_absent_task_map_is_reported(self):
        agents = copy.deepcopy(load_agents())
        del agents["vision"]["permission"]["task"]
        self.assertIn(
            "vision -> gentle-ai-worker: allow (no deny rule)",
            pm_writer_dispatch_failures(agents),
        )


if __name__ == "__main__":
    unittest.main()
