"""Q90 T3.0 Kimi-removal checks over the tracked executable config sources.

Catalog entries, historical prose and the staged variant fixture catalog are not
executable-seat references and stay outside the detector.

Run: python3 -m unittest tests.test_q90_t30_kimi_removal -v
"""

import copy
import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"
FALLBACK_PATH = REPO / "global-config" / "rate-limit-fallback.json"
SYSTEMATIC_PATH = REPO / "global-config" / "systematic.jsonc"
SCRIPT = REPO / "verify-workflow.sh"
WORKFLOW_PATH = REPO / "WORKFLOW.md"
KIMI = "kimi-k2.7-code"
LEGACY_M3 = "opencode-go/minimax-m3"
WRITER = "opencode-go/deepseek-v4.1-flash"
SEATS = {
    "review-reliability": ("opencode-go/minimax-m3.1-flash", "xhigh"),
    "asi-review-reliability": ("opencode-go/minimax-m3.1-flash", "xhigh"),
    "advisor-integration-pre": ("opencode-go/minimax-m3.1-flash", "high"),
    "advisor-integration-post": ("opencode-go/qwen3.8-flash", None),
    "advisor-testing-post": ("opencode-go/qwen3.8-flash", None),
    "advisor-maintainability-post": ("opencode-go/ling-3.1-flash", None),
}
ABSENT = tuple(name for name, (_, variant) in SEATS.items() if variant is None)
READABILITY = ("review-readability", "asi-review-readability")
MUSE = ("opencode-go/muse-spark-1.3-contributor", "high")
REPLACEMENTS = ("opencode-go/minimax-m3.1-flash", "opencode-go/qwen3.8-flash",
                "opencode-go/ling-3.1-flash")
REVIEW_SEATS = (
    "review-risk", "review-resilience", "review-readability", "review-reliability",
    "review-refuter", "review-validator", "asi-review-risk", "asi-review-resilience",
    "asi-review-readability", "asi-review-reliability", "asi-review-refuter",
    "asi-review-validator")
ADVISOR_SEATS = (
    "advisor-design-pre", "advisor-design-post", "advisor-security-pre",
    "advisor-security-post", "advisor-integration-pre", "advisor-integration-post",
    "advisor-testing-pre", "advisor-testing-post", "advisor-maintainability-pre",
    "advisor-maintainability-post", "advisor-gemini-pre", "advisor-gemini-post",
    "advisor-gemini-evidence")
NORMAL_ADVISOR_ROWS = (
    "advisor-design-pre", "advisor-design-post", "advisor-security-pre",
    "advisor-security-post", "advisor-integration-pre", "advisor-integration-post",
    "advisor-testing-pre", "advisor-testing-post", "advisor-maintainability-pre",
    "advisor-maintainability-post")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _family_module():
    spec = importlib.util.spec_from_file_location(
        "q90_model_independence", REPO / "tests" / "test_model_independence.py")
    if spec is None or spec.loader is None:
        raise ImportError("cannot load tests/test_model_independence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAMILY = _family_module()
model_family, assert_independent = FAMILY.model_family, FAMILY.assert_independent


def variant_shape_failures(agents):
    out = []
    for name, (model, variant) in SEATS.items():
        agent = agents.get(name, {})
        if agent.get("model") != model:
            out.append(f"{name}: model {agent.get('model')!r} != {model!r}")
        if variant is None:
            if "variant" in agent:
                out.append(f"{name}: variant must be absent, got {agent['variant']!r}")
        elif agent.get("variant") != variant:
            out.append(f"{name}: variant {agent.get('variant')!r} != {variant!r}")
    for name in READABILITY:
        agent = agents.get(name, {})
        if (agent.get("model"), agent.get("variant")) != MUSE:
            out.append(f"{name}: readability is not Muse high")
    return out


MODEL_KEYS = ("model", "small_model")


def load_jsonc(path):
    """Parse tracked JSONC with the verifier's string/comment state machine."""
    text = path.read_text(encoding="utf-8")
    out, index, in_string, escaped = [], 0, False, False
    while index < len(text):
        char, following = text[index], text[index + 1:index + 2]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            out.append(char)
            index += 1
        elif char == "/" and following == "/":
            while index < len(text) and text[index] not in "\r\n":
                index += 1
        elif char == "/" and following == "*":
            end = text.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            index = end + 2
        else:
            out.append(char)
            index += 1
    return json.loads(re.sub(r",\s*([}\]])", r"\1", "".join(out)))


def model_assignments(node, path=""):
    """Yield every model/small_model assignment; catalog keys are not assignments."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if key in MODEL_KEYS and isinstance(value, str):
                yield here, value
            if isinstance(value, (dict, list)):
                yield from model_assignments(value, here)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from model_assignments(value, f"{path}[{index}]")


def _model_value(entry):
    if not isinstance(entry, dict) or not isinstance(entry.get("modelID"), str):
        return None
    provider = entry.get("providerID")
    return f"{provider}/{entry['modelID']}" if isinstance(provider, str) else entry["modelID"]


def fallback_model_references(fallback):
    """Yield fallback source keys and provider/agent/exact target model values."""
    refs = []

    def add(label, value):
        if isinstance(value, str):
            refs.append((label, value))

    for index, entry in enumerate(fallback.get("fallbackModel", [])):
        add(f"fallbackModel[{index}]", _model_value(entry))
    for model, chain in fallback.get("fallbackModels", {}).items():
        add(f"fallbackModels.{model}", model)
        for index, entry in enumerate(chain):
            add(f"fallbackModels.{model}[{index}]", _model_value(entry))
    for provider, chain in fallback.get("providerFallbacks", {}).items():
        for index, entry in enumerate(chain):
            add(f"providerFallbacks.{provider}[{index}]", _model_value(entry))
    for agent, chain in fallback.get("agentFallbackModels", {}).items():
        for index, entry in enumerate(chain):
            add(f"agentFallbackModels.{agent}[{index}]", _model_value(entry))
    return refs


def executable_kimi_references(config, fallback, systematic=None):
    refs = [("config", label, value) for label, value in model_assignments(config) if KIMI in value]
    refs += [("fallback", label, value) for label, value in fallback_model_references(fallback)
             if KIMI in value]
    if systematic is not None:
        refs += [("systematic", label, value)
                 for label, value in model_assignments(systematic) if KIMI in value]
    return refs


def configured_review_advisor_seats(agents):
    """Native OpenCode review/advisor seats; Systematic reviewers are inventory-only."""
    return sorted(name for name in agents
                  if name.startswith(("review-", "asi-review-", "advisor-")))


def legacy_m3_seats(agents):
    """Exact legacy M3 identity only; minmax-m3.1-flash must not match."""
    return sorted(name for name in configured_review_advisor_seats(agents)
                  if agents[name].get("model") == LEGACY_M3)


def workflow_advisor_rows(text):
    rows = {}
    pattern = re.compile(
        r"^\|\s*`(advisor-[a-z-]+)`\s*\|\s*`([^`]+)`(?:\s*\(`([a-z]+)`\))?\s*\|")
    for line in text.splitlines():
        match = pattern.match(line)
        if match and match.group(1) in NORMAL_ADVISOR_ROWS:
            rows[match.group(1)] = (match.group(2), match.group(3))
    return rows


def advisor_row_failures(agents, rows):
    out = []
    for name in NORMAL_ADVISOR_ROWS:
        if name not in rows:
            out.append(f"{name}: missing WORKFLOW row")
            continue
        model, variant = rows[name]
        agent = agents.get(name, {})
        if agent.get("model") != model:
            out.append(f"{name}: config model {agent.get('model')!r} != WORKFLOW {model!r}")
        if agent.get("variant") != variant:
            out.append(f"{name}: config variant {agent.get('variant')!r} != WORKFLOW {variant!r}")
    return out


def seat_independence_failures(agents, writer_model):
    failures = []
    for name in configured_review_advisor_seats(agents):
        family = model_family(agents[name].get("model"))
        if family is None:
            failures.append(f"{name}: family not proven")
        elif family == model_family(writer_model):
            failures.append(f"{name}: author family")
    return failures


def fallback_shape_failures(fallback):
    out = []
    exact = fallback.get("fallbackModels", {})
    for model in REPLACEMENTS:
        chain = exact.get(model)
        if not isinstance(chain, list) or not chain:
            out.append(f"{model}: missing or empty exact policy")
            continue
        keys = [f"{entry.get('providerID')}/{entry.get('modelID')}" for entry in chain]
        if model in keys:
            out.append(f"{model}: self target")
        if len(set(keys)) != len(keys):
            out.append(f"{model}: duplicate target")
        if all(entry.get("providerID") == "opencode-go" for entry in chain):
            out.append(f"{model}: no non-Go provider-failure target")
    if "opencode-go/kimi-k2.7-code" in exact:
        out.append("inactive Kimi exact policy remains")
    excluded = set(fallback.get("excludeAgents", []))
    out += [f"{name}: missing review exclusion" for name in REVIEW_SEATS if name not in excluded]
    no_fallback = set(fallback.get("noFallbackAgents", []))
    out += [f"{name}: missing no-fallback entry" for name in ADVISOR_SEATS
            if name not in no_fallback]
    return out


def fallback_helper_results(fallback, models):
    """Execute the verifier's own fallback helper functions against the input."""
    text = SCRIPT.read_text(encoding="utf-8")
    start = text.find("function modelString(value)")
    end = text.find("const refs=(Array.isArray(deployed.plugin)")
    if start < 0 or end <= start:
        raise AssertionError("fallback helper block not found in verify-workflow.sh")
    runtime = shutil.which("bun") or shutil.which("node")
    if not runtime:
        raise unittest.SkipTest("Bun or Node is required to execute the extracted fallback helpers")
    program = (
        "const fail=(m)=>{throw new Error(m)};const show=(v)=>JSON.stringify(v);"
        "const hasOwn=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);"
        + text[start:end]
        + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        + "\nconst out=input.models.map((model)=>{try{"
        + "const p=effectiveFallbacks(input.fallback,model,undefined,'provider');"
        + "const m=effectiveFallbacks(input.fallback,model,undefined,'model');"
        + "return p.length&&m.length?'OK':'EMPTY'}catch(e){return 'FAIL:'+e.message}});"
        + "process.stdout.write(JSON.stringify(out))"
    )
    proc = subprocess.run([runtime, "-e", program],
                          input=json.dumps({"fallback": fallback, "models": models}),
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise AssertionError(f"fallback helpers failed to run: {proc.stderr or proc.stdout}")
    return json.loads(proc.stdout)


class LiveSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(CONFIG_PATH)
        cls.fallback = load(FALLBACK_PATH)
        cls.systematic = load_jsonc(SYSTEMATIC_PATH)
        cls.agents = cls.config["agent"]

    def test_exact_six_seat_remaps_with_literal_absence_and_readability(self):
        self.assertEqual(variant_shape_failures(self.agents), [])
        for name in ABSENT:
            self.assertNotIn("variant", self.agents[name], name)
        for name in READABILITY:
            self.assertEqual((self.agents[name]["model"], self.agents[name]["variant"]), MUSE)

    def test_no_executable_kimi_references(self):
        self.assertEqual(
            executable_kimi_references(self.config, self.fallback, self.systematic), [])

    def test_replacement_fallback_policies_are_dormant_complete(self):
        self.assertEqual(fallback_shape_failures(self.fallback), [])

    def test_extracted_fallback_helpers_accept_and_reject(self):
        self.assertEqual(fallback_helper_results(self.fallback, REPLACEMENTS),
                         ["OK"] * len(REPLACEMENTS))
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"][REPLACEMENTS[0]] = []
        self.assertTrue(all(result.startswith("FAIL:")
                            for result in fallback_helper_results(fallback, [REPLACEMENTS[0]])))

    def test_all_review_and_advisor_seats_avoid_author_family(self):
        self.assertEqual(configured_review_advisor_seats(self.agents),
                         sorted(REVIEW_SEATS + ADVISOR_SEATS))
        self.assertEqual(seat_independence_failures(self.agents, WRITER), [])

    def test_four_lens_spread_and_validator_overlap(self):
        families = {model_family(self.agents[name]["model"]) for name in REVIEW_SEATS[:4]}
        self.assertGreaterEqual(len(families), 3, families)
        for name in ("review-validator", "asi-review-validator"):
            self.assertEqual(model_family(self.agents[name]["model"]), "claude")
        self.assertEqual(model_family(self.agents["review-reliability"]["model"]), "minimax")

    def test_no_legacy_minimax_m3_on_review_or_advisor_seats(self):
        self.assertEqual(legacy_m3_seats(self.agents), [])

    def test_workflow_normal_advisor_rows_match_config(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        rows = workflow_advisor_rows(workflow)
        self.assertEqual(set(rows), set(NORMAL_ADVISOR_ROWS))
        self.assertEqual(advisor_row_failures(self.agents, rows), [])


class DetectorControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(CONFIG_PATH)
        cls.fallback = load(FALLBACK_PATH)

    def test_injected_kimi_primary_is_detected(self):
        config = copy.deepcopy(self.config)
        config["agent"]["review-risk"]["model"] = "opencode-go/kimi-k2.7-code"
        refs = executable_kimi_references(config, self.fallback)
        self.assertTrue(any("review-risk" in label for _, label, _ in refs), refs)

    def assert_single_reference(self, config, fallback, kind, label, value, systematic=None):
        self.assertEqual(executable_kimi_references(config, fallback, systematic),
                         [(kind, label, value)])

    def test_fallback_target_controls_are_isolated(self):
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModel"].append(
            {"providerID": "opencode-go", "modelID": KIMI})
        self.assert_single_reference(
            self.config, fallback, "fallback", "fallbackModel[2]",
            "opencode-go/kimi-k2.7-code")
        for container, key, label in (
                ("fallbackModels", REPLACEMENTS[0], f"fallbackModels.{REPLACEMENTS[0]}[2]"),
                ("providerFallbacks", "opencode-go", "providerFallbacks.opencode-go[2]"),
                ("agentFallbackModels", "vision", "agentFallbackModels.vision[3]")):
            fallback = copy.deepcopy(self.fallback)
            fallback[container][key].append(
                {"providerID": "opencode-go", "modelID": KIMI})
            self.assert_single_reference(
                self.config, fallback, "fallback", label, "opencode-go/kimi-k2.7-code")

    def test_fallback_source_key_does_not_stand_in_for_a_target(self):
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"]["opencode-go/kimi-k2.7-code"] = []
        self.assert_single_reference(
            self.config, fallback, "fallback",
            "fallbackModels.opencode-go/kimi-k2.7-code", "opencode-go/kimi-k2.7-code")

    def test_config_systematic_and_catalog_controls(self):
        config = copy.deepcopy(self.config)
        config["agent"]["review-risk"]["model"] = KIMI
        self.assert_single_reference(
            config, self.fallback, "config", "agent.review-risk.model", KIMI)
        config = copy.deepcopy(self.config)
        config["small_model"] = KIMI
        self.assert_single_reference(config, self.fallback, "config", "small_model", KIMI)
        systematic = load_jsonc(SYSTEMATIC_PATH)
        systematic["categories"]["workflow"]["model"] = KIMI
        self.assert_single_reference(
            self.config, self.fallback, "systematic", "categories.workflow.model", KIMI,
            systematic)
        config = copy.deepcopy(self.config)
        config.setdefault("provider", {}).setdefault("opencode-go", {}).setdefault(
            "models", {})[KIMI] = {"name": KIMI}
        self.assertEqual(executable_kimi_references(config, self.fallback), [])

        # No literal per-tool model key exists in the inspected tracked config: the
        # top-level `tools` map (opencode.json:3320-3321) and the agent-level `tools`
        # maps inspected (e.g. :9-31) contain boolean tool toggles only. The actual
        # tool-scoped model surface is the model of the subagent the `task` tool
        # dispatches:
        # `agent.vision` (opencode.json:1079-1083, mode `subagent`), granted at
        # `permission.task.vision` (:171) and named as the read-only vision
        # subagent/tool fallback in WORKFLOW.md:302-305. This fixture injects that
        # real field, not an invented `tools.<tool>.model` key.
        config = copy.deepcopy(self.config)
        self.assertEqual(executable_kimi_references(config, self.fallback), [])
        self.assertEqual(config["agent"]["vision"]["mode"], "subagent")
        self.assertEqual(
            config["agent"]["frontend-dev"]["permission"]["task"]["vision"], "allow")
        config["agent"]["vision"]["model"] = f"opencode-go/{KIMI}"
        self.assert_single_reference(
            config, self.fallback, "config", "agent.vision.model", f"opencode-go/{KIMI}")

    def test_variant_shape_controls_are_isolated_per_seat(self):
        present = {name: variant for name, (_, variant) in SEATS.items() if variant is not None}
        present.update({name: MUSE[1] for name in READABILITY})
        for name in present:
            for mutation in ("wrong", "absent"):
                agents = copy.deepcopy(self.config["agent"])
                if mutation == "wrong":
                    agents[name]["variant"] = "low"
                else:
                    agents[name].pop("variant")
                failures = variant_shape_failures(agents)
                self.assertTrue(any(failure.startswith(f"{name}:") for failure in failures),
                                (name, mutation, failures))
        for name in ABSENT:
            for value in (None, "", "default", "medium"):
                agents = copy.deepcopy(self.config["agent"])
                agents[name]["variant"] = value
                failures = variant_shape_failures(agents)
                self.assertTrue(any(failure.startswith(f"{name}:") for failure in failures),
                                (name, value, failures))

    def test_legacy_minimax_m3_injection_and_near_match_control(self):
        agents = copy.deepcopy(self.config["agent"])
        agents["review-validator"]["model"] = LEGACY_M3
        self.assertEqual(legacy_m3_seats(agents), ["review-validator"])
        agents = copy.deepcopy(self.config["agent"])
        agents["advisor-testing-pre"]["model"] = "opencode-go/minimax-m3.1-flash"
        self.assertEqual(legacy_m3_seats(agents), [])

    def test_workflow_advisor_row_and_config_mismatch_controls(self):
        rows = workflow_advisor_rows(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.assertEqual(advisor_row_failures(self.config["agent"], rows), [])
        for seat, row in (
                ("advisor-design-pre", ("opencode-go/other-model", None)),
                ("advisor-testing-pre", ("opencode-go/glm-5.3-flash", "low"))):
            mutated = dict(rows)
            mutated[seat] = row
            failures = advisor_row_failures(self.config["agent"], mutated)
            self.assertTrue(any(failure.startswith(f"{seat}: config")
                                for failure in failures), (seat, failures))
        for seat, field in (("advisor-design-post", "model"),
                            ("advisor-integration-pre", "variant")):
            agents = copy.deepcopy(self.config["agent"])
            agents[seat][field] = "opencode-go/other-model" if field == "model" else "low"
            failures = advisor_row_failures(agents, rows)
            self.assertTrue(any(failure.startswith(f"{seat}: config {field}")
                                for failure in failures), (seat, field, failures))

    def test_seat_inventory_rejects_non_independent_and_unknown_seats(self):
        for seat in ("review-risk", "advisor-testing-post"):
            for model in ("other/deepseek-v5", "other/unknown-seat"):
                agents = copy.deepcopy(self.config["agent"])
                agents[seat]["model"] = model
                failures = seat_independence_failures(agents, WRITER)
                self.assertTrue(any(failure.startswith(f"{seat}:") for failure in failures),
                                (seat, model, failures))

    def test_family_helper_controls(self):
        self.assertEqual(model_family("other/deepseek-v5"), "deepseek")
        self.assertEqual(model_family("opencode-go/ling-3.1-flash"), "ling")
        self.assertEqual(model_family("opencode-go/claude-haiku-5-5"), "claude")
        with self.assertRaises(AssertionError):
            assert_independent(self, WRITER, "other/deepseek-v5")
        self.assertIsNone(model_family("other/unknown-seat"))
        with self.assertRaisesRegex(AssertionError, "independence is not proven"):
            assert_independent(self, WRITER, "other/unknown-seat")

    def test_fallback_shape_controls(self):
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"][REPLACEMENTS[0]] = [
            {"providerID": "opencode-go", "modelID": "glm-5.3"}]
        self.assertTrue(any("no non-Go" in failure
                            for failure in fallback_shape_failures(fallback)))
        fallback = copy.deepcopy(self.fallback)
        fallback["excludeAgents"].remove("review-reliability")
        self.assertIn("review-reliability: missing review exclusion",
                      fallback_shape_failures(fallback))
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"]["opencode-go/kimi-k2.7-code"] = []
        self.assertIn("inactive Kimi exact policy remains",
                      fallback_shape_failures(fallback))


if __name__ == "__main__":
    unittest.main()
