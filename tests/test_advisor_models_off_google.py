"""Advisor model policy: no Google agents and independent pre/post seats."""
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"


def advisor_model_violations(agents: dict) -> list[str]:
    """Return Google-model assignments and advisor pairs sharing a model."""
    violations = []
    for name, agent in agents.items():
        model = agent.get("model") if isinstance(agent, dict) else None
        if isinstance(model, str) and model.startswith("google/"):
            violations.append(f"{name} uses Google model {model}")
    pairs = {}
    for name, agent in agents.items():
        if not name.startswith("advisor-") or not isinstance(agent, dict):
            continue
        if name.endswith("-pre"):
            pairs.setdefault(name[:-4], {})["pre"] = agent.get("model")
        elif name.endswith("-post"):
            pairs.setdefault(name[:-5], {})["post"] = agent.get("model")
    for pair, seats in pairs.items():
        if "pre" in seats and "post" in seats and seats["pre"] == seats["post"]:
            violations.append(f"{pair} pre/post share model {seats['pre']}")
    return violations


def advisor_variant_violations(markdown: str, agents: dict) -> list[str]:
    """Return advisor table rows whose effort annotation disagrees with config."""
    violations = []
    for heading in ("**Pre-code advisors**", "**Post-code advisors**"):
        if heading not in markdown:
            violations.append(f"missing advisor table heading {heading}")
            continue
        section = markdown.split(heading, 1)[1]
        table = re.search(
            r"(?m)^\| Advisor \| Model \|\n^\|---\|---\|\n(?P<rows>(?:^\|.*\|\n?)+)",
            section,
        )
        if table is None:
            violations.append(f"missing advisor table after {heading}")
            continue
        for row in table.group("rows").splitlines():
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) != 2:
                continue
            name_match = re.fullmatch(r"`([^`]+)`", cells[0])
            if name_match is None:
                continue
            name = name_match.group(1)
            annotation_match = re.search(r"\(([^()]*)\)\s*$", cells[1])
            annotation = (
                annotation_match.group(1).strip().strip("`")
                if annotation_match is not None
                else None
            )
            agent = agents.get(name)
            configured = agent.get("variant") if isinstance(agent, dict) else None
            if annotation != configured:
                violations.append(
                    f"{name} table variant {annotation!r} does not match config {configured!r}"
                )
    return violations


class AdvisorModelPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]

    def test_real_agent_inventory_satisfies_model_policy(self):
        self.assertEqual(advisor_model_violations(self.agents), [])

    def test_workflow_advisor_table_variants_match_agent_config(self):
        workflow = (REPO / "WORKFLOW.md").read_text(encoding="utf-8")
        self.assertEqual(advisor_variant_violations(workflow, self.agents), [])

    def test_variant_positive_control_rejects_annotation_without_config_variant(self):
        synthetic = """**Pre-code advisors**

| Advisor | Model |
|---|---|
| `advisor-design-pre` | `opencode-go/glm-5.3-flash` (`high`) |

**Post-code advisors**

| Advisor | Model |
|---|---|
| `advisor-spec-post` | `opencode-go/glm-5.3-flash` |
"""
        violations = advisor_variant_violations(synthetic, self.agents)
        self.assertEqual(
            violations,
            ["advisor-design-pre table variant 'high' does not match config None"],
        )

    def test_google_model_positive_control_names_agent(self):
        self.assertEqual(
            advisor_model_violations({"example-agent": {"model": "google/gemini-4-argon"}}),
            ["example-agent uses Google model google/gemini-4-argon"],
        )

    def test_duplicate_pair_positive_control_names_pair(self):
        agents = {
            "advisor-x-pre": {"model": "opencode-go/model-a"},
            "advisor-x-post": {"model": "opencode-go/model-a"},
        }
        self.assertEqual(
            advisor_model_violations(agents),
            ["advisor-x pre/post share model opencode-go/model-a"],
        )

    def test_six_distinct_non_google_pairs_are_accepted(self):
        agents = {}
        for index in range(6):
            agents[f"advisor-lens{index}-pre"] = {"model": f"opencode-go/pre-{index}"}
            agents[f"advisor-lens{index}-post"] = {"model": f"opencode-go/post-{index}"}
        self.assertEqual(advisor_model_violations(agents), [])

    def test_removed_gemini_identifiers_are_absent_from_inventory_files(self):
        for relative in (
            "global-config/opencode.json",
            "global-config/rate-limit-fallback.json",
            "verify/checkers/check-runtime-agents.cjs",
            "verify/30-recover-config.sh",
            "WORKFLOW.md",
        ):
            with self.subTest(path=relative):
                self.assertNotIn("advisor-gemini-", (REPO / relative).read_text(encoding="utf-8"))

    def test_evidence_agent_is_renamed_and_not_granted_under_old_name(self):
        self.assertEqual(self.agents["advisor-evidence"]["model"], "opencode-go/qwen3.8-flash")
        for name, agent in self.agents.items():
            task = agent.get("permission", {}).get("task", {})
            if isinstance(task, dict):
                self.assertNotIn("advisor-gemini-evidence", task, name)


if __name__ == "__main__":
    unittest.main()
