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
    """Return malformed advisor tables and rows that disagree with config."""
    violations = []
    expected = {
        "pre": {name for name in agents if name.startswith("advisor-") and name.endswith("-pre")},
        "post": {name for name in agents if name.startswith("advisor-") and name.endswith("-post")},
    }
    headings = (("**Pre-code advisors**", "pre", "**Post-code advisors**"),
                ("**Post-code advisors**", "post", None))
    for heading, suffix, next_heading in headings:
        if heading not in markdown:
            violations.append(f"missing advisor table heading {heading}")
            continue
        section = markdown.split(heading, 1)[1]
        if next_heading is not None:
            section = section.split(next_heading, 1)[0]
        else:
            next_heading_match = re.search(r"(?m)^\*\*.+\*\*\s*$", section)
            if next_heading_match is not None:
                section = section[:next_heading_match.start()]
        table = re.search(
            r"(?m)^\| Advisor \| Model \|\n^\|---\|---\|\n(?P<rows>(?:^\|.*\|\n?)+)",
            section,
        )
        if table is None:
            violations.append(f"missing advisor table after {heading}")
            continue
        observed = set()
        for row in table.group("rows").splitlines():
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) != 2:
                violations.append(f"malformed advisor row in {heading}: {row}")
                continue
            name_match = re.fullmatch(r"`([^`]+)`", cells[0])
            if name_match is None:
                violations.append(f"advisor row name must be a single backticked name: {cells[0]}")
                continue
            name = name_match.group(1)
            if name not in expected[suffix]:
                violations.append(f"unknown {suffix} advisor table name {name}")
                continue
            if name in observed:
                violations.append(f"duplicate {suffix} advisor table row {name}")
                continue
            observed.add(name)
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
        for name in sorted(expected[suffix] - observed):
            violations.append(f"missing {suffix} advisor table row {name}")
        for name in sorted(observed - expected[suffix]):
            violations.append(f"unexpected {suffix} advisor table row {name}")
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

    def test_variant_positive_control_rejects_wrong_annotation(self):
        workflow = (REPO / "WORKFLOW.md").read_text(encoding="utf-8")
        row = re.search(r"(?m)^\| `([^`]+-pre)` \| ([^|]+) \|$", workflow)
        self.assertIsNotNone(row)
        name = row.group(1)
        configured = self.agents[name].get("variant")
        wrong = "wrong-variant" if configured is None else "wrong-variant"
        mutated = workflow[:row.start()] + row.group(0).replace(
            row.group(2), f"{row.group(2).rstrip()} (`{wrong}`) "
        ) + workflow[row.end():]
        self.assertTrue(any(name in issue and "table variant" in issue
                            for issue in advisor_variant_violations(mutated, self.agents)))

    def test_variant_controls_reject_missing_heading_dropped_backtick_and_unknown_name(self):
        workflow = (REPO / "WORKFLOW.md").read_text(encoding="utf-8")
        missing_heading = workflow.replace("**Pre-code advisors**", "**Pre-code review**", 1)
        self.assertTrue(any("missing advisor table heading" in issue
                            for issue in advisor_variant_violations(missing_heading, self.agents)))

        dropped_backtick = workflow.replace("`advisor-design-pre`", "advisor-design-pre", 1)
        self.assertTrue(any("single backticked name" in issue
                            for issue in advisor_variant_violations(dropped_backtick, self.agents)))

        unknown_name = workflow.replace("`advisor-design-pre`", "`advisor-unknown-pre`", 1)
        self.assertTrue(any("unknown pre advisor table name advisor-unknown-pre" in issue
                            for issue in advisor_variant_violations(unknown_name, self.agents)))

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
