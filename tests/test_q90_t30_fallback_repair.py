"""Q90 T3.0 fallback exact-policy repair checks over tracked canonical sources.

The verifier requires every active primary model (non-disabled openCode agents plus
Systematic inventory assignments) to have an exact ``fallbackModels`` policy, and
every exact source key to be an active primary model. Provider-catalog keys and
fallback target refs are not primary assignments.

Run: python3 -m unittest tests.test_q90_t30_fallback_repair -v
"""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"
FALLBACK_PATH = REPO / "global-config" / "rate-limit-fallback.json"
SYSTEMATIC_PATH = REPO / "global-config" / "systematic.jsonc"

HAIKU = "opencode-go/claude-haiku-5-5"
MINIMAX_M31 = "opencode-go/minimax-m3.1-flash"
SOL = "openai/gpt-6.1-sol"
ASTRA = "openai/gpt-6-astra"
REMOVED_SOURCES = ("opencode-go/mimo-v2.6-flash", "opencode-go/minimax-m3")
VALIDATOR_SEATS = ("review-validator", "asi-review-validator")
SHARED_CHAIN = [
    {
        "providerID": "deepseek",
        "modelID": "deepseek-flash",
        "variant": "max",
        "capabilities": ["files", "tools", "vision"],
    },
    {
        "providerID": "openrouter",
        "modelID": "deepseek/deepseek-v4.1-flash",
        "variant": "default",
        "capabilities": ["files", "tools", "vision"],
    },
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _kimi_module():
    """Reuse the existing verifier-helper extraction fixture."""
    spec = importlib.util.spec_from_file_location(
        "q90_t30_kimi_removal", REPO / "tests" / "test_q90_t30_kimi_removal.py")
    if spec is None or spec.loader is None:
        raise ImportError("cannot load tests/test_q90_t30_kimi_removal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


KIMI = _kimi_module()
load_jsonc = KIMI.load_jsonc
model_assignments = KIMI.model_assignments
fallback_helper_results = KIMI.fallback_helper_results


def active_assignments(config, systematic):
    """Map active primary models to openCode seat / Systematic inventory roles."""
    roles = {}
    for name, agent in config.get("agent", {}).items():
        if not isinstance(agent, dict) or agent.get("disable") is True:
            continue
        model = agent.get("model")
        if isinstance(model, str) and model:
            roles.setdefault(model, []).append(f"opencode:{name}")
    for label, model in model_assignments(systematic):
        roles.setdefault(model, []).append(f"systematic:{label}")
    # The verifier derives an Astra alias for every eligible non-implementation Sol
    # base; the canonical config always has such a base (the PMs).
    if SOL in roles:
        roles.setdefault(ASTRA, []).append("derived-astra-aliases")
    return roles


def exact_policy_failures(config, fallback, systematic):
    """Return the verifier's exact-policy diagnostics for the canonical inputs."""
    roles = active_assignments(config, systematic)
    exact = fallback.get("fallbackModels", {})
    failures = []
    for model in sorted(roles):
        if model not in exact:
            failures.append(
                "FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: "
                f"{model}; roles={','.join(roles[model])}")
    for source in exact:
        if source not in roles:
            failures.append(f"FALLBACK_EXACT_SOURCE_INACTIVE: {source}")
    return failures


class LiveSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(CONFIG_PATH)
        cls.fallback = load(FALLBACK_PATH)
        cls.systematic = load_jsonc(SYSTEMATIC_PATH)

    def test_active_models_have_exact_policy(self):
        self.assertEqual(
            exact_policy_failures(self.config, self.fallback, self.systematic), [])

    def test_repaired_exact_policies_and_preserved_targets(self):
        exact = self.fallback["fallbackModels"]
        remaining = [stale for stale in REMOVED_SOURCES if stale in exact]
        self.assertEqual(remaining, [])
        self.assertEqual(exact.get(HAIKU), SHARED_CHAIN)
        self.assertEqual(exact.get(HAIKU), exact.get(MINIMAX_M31))

        deepseek_chain = exact["opencode-go/deepseek-v4.1-flash"]
        targets = [f"{entry['providerID']}/{entry['modelID']}" for entry in deepseek_chain]
        self.assertIn("opencode-go/mimo-v2.6-flash", targets)

        for seat in VALIDATOR_SEATS:
            self.assertIn(seat, self.fallback["excludeAgents"])

    def test_haiku_assignments_are_the_two_validator_seats(self):
        roles = active_assignments(self.config, self.systematic)
        self.assertEqual(
            [role for role in roles[HAIKU] if role.startswith("opencode:")],
            ["opencode:review-validator", "opencode:asi-review-validator"])

    def test_extracted_fallback_helpers_accept_haiku(self):
        self.assertEqual(fallback_helper_results(self.fallback, [HAIKU]), ["OK"])


class DetectorControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(CONFIG_PATH)
        cls.fallback = load(FALLBACK_PATH)
        cls.systematic = load_jsonc(SYSTEMATIC_PATH)

    def failures(self, config=None, fallback=None):
        return exact_policy_failures(
            config if config is not None else self.config,
            fallback if fallback is not None else self.fallback,
            self.systematic)

    def test_missing_haiku_policy_reproduces_owner_diagnostic(self):
        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"].pop(HAIKU, None)
        self.assertIn(
            "FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: "
            "opencode-go/claude-haiku-5-5; "
            "roles=opencode:review-validator,opencode:asi-review-validator",
            self.failures(fallback=fallback))

    def test_injected_active_model_rejected_then_accepted_with_policy(self):
        config = copy.deepcopy(self.config)
        config["agent"]["review-validator"]["model"] = "opencode-go/unmapped-validator"
        self.assertIn(
            "FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: "
            "opencode-go/unmapped-validator; roles=opencode:review-validator",
            self.failures(config=config))

        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"]["opencode-go/unmapped-validator"] = copy.deepcopy(
            SHARED_CHAIN)
        self.assertEqual(self.failures(config=config, fallback=fallback), [])

    def test_reintroduced_removed_sources_are_rejected(self):
        for stale in REMOVED_SOURCES:
            fallback = copy.deepcopy(self.fallback)
            fallback["fallbackModels"][stale] = copy.deepcopy(SHARED_CHAIN)
            self.assertIn(f"FALLBACK_EXACT_SOURCE_INACTIVE: {stale}",
                          self.failures(fallback=fallback))
        self.assertEqual(self.failures(), [])

    def test_target_reference_is_not_an_active_source(self):
        roles = active_assignments(self.config, self.systematic)
        self.assertNotIn("opencode-go/mimo-v2.6-flash", roles)

        fallback = copy.deepcopy(self.fallback)
        fallback["fallbackModels"]["opencode-go/mimo-v2.6-flash"] = copy.deepcopy(
            SHARED_CHAIN)
        self.assertIn("FALLBACK_EXACT_SOURCE_INACTIVE: opencode-go/mimo-v2.6-flash",
                      self.failures(fallback=fallback))


if __name__ == "__main__":
    unittest.main()
