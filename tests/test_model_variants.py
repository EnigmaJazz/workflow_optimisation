"""Q90 T3.0.1 staged supported-variant validator tests.

The verifier carries ``supportedVariantFailure(model, variant)`` between the
``// supported-variant-validator:begin`` and ``:end`` markers. These tests extract and EXECUTE
that production block with Bun/Node against JSON input; they do not reimplement it in Python.
The catalog is the owner/tracker-approved target subset, not the full provider catalog.

Run: python3 -m unittest discover -s tests -p test_model_variants.py -v
"""

import hashlib, json, re, shutil, subprocess, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "verify-workflow.sh"
PLUGIN = REPO / "global-config" / "plugins" / "workflow-health-check.ts"
TRACKER = REPO / "odd" / "tasks" / "multi-agent-v2-queue.md"

BEGIN = "// supported-variant-validator:begin"
END = "// supported-variant-validator:end"
FUNCTION = "supportedVariantFailure"

EMPTY = "SUPPORTED_VARIANT_EMPTY_REFUSED"
TYPE = "SUPPORTED_VARIANT_TYPE_REFUSED"
MODEL_INVALID = "SUPPORTED_VARIANT_MODEL_INVALID"
UNCLASSIFIED = "SUPPORTED_VARIANT_MODEL_UNCLASSIFIED"
UNKNOWN = "SUPPORTED_VARIANT_UNKNOWN_REFUSED"

ACTIVATION_REQUIREMENT = (
    "set the orchestrator to `high` and activate the strict validator for all confirmed models; "
    "the validator is staged and untested against live seats until this step"
)

# Allowed target subset from the owner evidence and tracker plan. Empty means absence only.
TARGETS = {
    "openai/gpt-6-luna": ("none", "low", "medium", "high", "xhigh", "max"),
    "opencode-go/glm-5.3-flash": ("low", "high", "max"),
    "opencode-go/glm-5.3": ("low", "high", "max"),
    "opencode-go/deepseek-v4.1-flash": ("low", "high"),
    "opencode-go/deepseek-v4.1-flash@worker": ("low", "high", "max"),
    "opencode-go/deepseek-v4-pro": ("high",),
    "opencode-go/claude-haiku-5-5": ("high",),
    "opencode-go/minimax-m3.1-flash": ("high", "xhigh"),
    "opencode-go/qwen3.8-flash": (),
    "opencode-go/qwen3.8-max": (),
    "opencode-go/kimi-k2.7-code": (),
    "opencode-go/mimo-v2.6-flash": (),
    "google/gemini-flash-latest": (),
    "google/gemini-4-argon": (),
}
ABSENT_ONLY = ("opencode-go/qwen3.8-flash", "opencode-go/qwen3.8-max",
               "opencode-go/kimi-k2.7-code", "opencode-go/mimo-v2.6-flash")
ALL_NAMED = ("none", "low", "medium", "high", "xhigh", "max", "default")


def extract_block(text=None):
    text = SCRIPT.read_text(encoding="utf-8") if text is None else text
    start, end = text.find(BEGIN), text.find(END)
    return None if start < 0 or end < 0 or end < start else text[start:end + len(END)]


def required_block(text=None):
    block = extract_block(text)
    if block is None:
        raise AssertionError("supported-variant-validator block not found in verify-workflow.sh")
    return block


def run_validator(entries, block=None):
    """Execute the extracted production block; return one result per entry (None = accepted)."""
    block = extract_block() if block is None else block
    if block is None:
        raise AssertionError("supported-variant-validator block not found in verify-workflow.sh")
    runtime = shutil.which("bun") or shutil.which("node")
    if not runtime:
        raise AssertionError("Bun or Node is required to execute the extracted production block")
    program = (block + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'))"
               + "\nprocess.stdout.write(JSON.stringify(input.map((entry)=>{"
               + "const has=Object.prototype.hasOwnProperty.call(entry,'variant');"
               + "return has?supportedVariantFailure(entry.model,entry.variant):supportedVariantFailure(entry.model)})))")
    proc = subprocess.run([runtime, "-e", program], input=json.dumps(entries),
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise AssertionError(f"extracted validator failed to run: {proc.stderr or proc.stdout}")
    return json.loads(proc.stdout)


class StagedValidator(unittest.TestCase):
    def test_block_is_marked_and_defines_the_production_function(self):
        block = required_block()
        self.assertIn(f"function {FUNCTION}(", block)
        self.assertIn("SUPPORTED_VARIANT_TARGETS", block)

    def test_full_model_ids_and_worker_alias_are_used(self):
        block = required_block()
        self.assertIn('"opencode-go/deepseek-v4.1-flash@worker"', required_block())
        self.assertIn('"openai/gpt-6-luna"', required_block())
        self.assertNotIn("providers", block)
        self.assertNotIn("gpt-6-luna-fast", block.split(BEGIN, 1)[-1])

    def test_absent_variant_is_accepted_for_every_target(self):
        results = run_validator([{"model": model} for model in TARGETS])
        self.assertEqual(results, [None] * len(TARGETS))

    def test_every_declared_name_is_accepted(self):
        entries = [{"model": m, "variant": n} for m, names in TARGETS.items() for n in names]
        self.assertEqual(run_validator(entries), [None] * len(entries))

    def test_empty_string_is_refused_by_name_with_model_and_variant(self):
        entries = [{"model": model, "variant": ""} for model in TARGETS]
        for model, result in zip(TARGETS, run_validator(entries)):
            self.assertTrue(result.startswith(EMPTY), (model, result))
            self.assertIn(model, result)
            self.assertIn('variant=""', result)

    def test_unknown_names_are_refused_with_model_and_variant(self):
        cases = [("openai/gpt-6-luna", "ultra"), ("opencode-go/glm-5.3-flash", "medium"),
                 ("opencode-go/glm-5.3", "none"), ("opencode-go/minimax-m3.1-flash", "low"),
                 ("opencode-go/deepseek-v4.1-flash", "max"), ("opencode-go/deepseek-v4-pro", "medium"),
                 ("opencode-go/claude-haiku-5-5", "low"),
                 ("opencode-go/deepseek-v4.1-flash@worker", "none")]
        results = run_validator([{"model": m, "variant": n} for m, n in cases])
        for (model, name), result in zip(cases, results):
            self.assertTrue(result.startswith(UNKNOWN), (model, name, result))
            self.assertIn(model, result)
            self.assertIn(name, result)

    def test_qwen_kimi_and_mimo_refuse_every_named_variant(self):
        entries = [{"model": m, "variant": n} for m in ABSENT_ONLY for n in ALL_NAMED]
        results = run_validator(entries)
        self.assertEqual(len(results), len(entries))
        for entry, result in zip(entries, results):
            self.assertTrue(result.startswith(UNKNOWN), (entry, result))

    def test_minimax_accepts_only_high_and_xhigh(self):
        model = "opencode-go/minimax-m3.1-flash"
        self.assertEqual(run_validator([{"model": model, "variant": n}
                                        for n in ("high", "xhigh")]), [None, None])
        refused = run_validator([{"model": model, "variant": n}
                                 for n in ("low", "medium", "max", "default")])
        self.assertTrue(all(result.startswith(UNKNOWN) for result in refused), refused)

    def test_luna_accepts_every_listed_name(self):
        self.assertEqual(run_validator([{"model": "openai/gpt-6-luna", "variant": n}
                                        for n in ("none", "low", "medium", "high", "xhigh", "max")]),
                         [None] * 6)

    def test_glm_accepts_low_high_max_only(self):
        for model in ("opencode-go/glm-5.3-flash", "opencode-go/glm-5.3"):
            self.assertEqual(run_validator([{"model": model, "variant": n}
                                            for n in ("low", "high", "max")]), [None, None, None])
            result = run_validator([{"model": model, "variant": "medium"}])[0]
            self.assertTrue(result.startswith(UNKNOWN), (model, result))

    def test_worker_alias_identity_is_isolated_from_the_base_model(self):
        worker, base = "opencode-go/deepseek-v4.1-flash@worker", "opencode-go/deepseek-v4.1-flash"
        self.assertEqual(run_validator([{"model": worker, "variant": n}
                                        for n in ("low", "high", "max")]), [None] * 3)
        self.assertEqual(run_validator([{"model": base, "variant": n}
                                        for n in ("low", "high")]), [None, None])
        self.assertTrue(run_validator([{"model": base, "variant": "max"}])[0].startswith(UNKNOWN))

    def test_unclassified_model_does_not_authorize_a_named_variant(self):
        result = run_validator([{"model": "openai/gpt-6-luna-fast", "variant": "high"}])[0]
        self.assertTrue(result.startswith(UNCLASSIFIED), result)
        self.assertIn("openai/gpt-6-luna-fast", result)
        self.assertIn("high", result)

    def test_malformed_types_fail_closed_and_are_never_coerced(self):
        for value in (None, 1, True, [], {}):
            with self.subTest(value=value):
                result = run_validator([{"model": "openai/gpt-6-luna", "variant": value}])[0]
                self.assertTrue(result.startswith(TYPE), (value, result))
                self.assertIn("openai/gpt-6-luna", result)
        for model in (None, 7, ""):
            with self.subTest(model=model):
                result = run_validator([{"model": model}])[0]
                self.assertTrue(result.startswith(MODEL_INVALID), (model, result))

    def test_absent_is_not_the_same_as_null(self):
        self.assertIsNone(run_validator([{"model": "openai/gpt-6-luna"}])[0])
        null = run_validator([{"model": "openai/gpt-6-luna", "variant": None}])[0]
        self.assertTrue(null.startswith(TYPE), null)

    def test_gemini_default_is_rejected_as_an_undeclared_name(self):
        self.assertNotIn('"default"', required_block())
        result = run_validator([{"model": "google/gemini-flash-latest", "variant": "default"}])[0]
        self.assertTrue(result.startswith(UNKNOWN), result)

    def test_inherited_object_keys_are_unclassified_not_crashed(self):
        # The first three are inherited Object properties; the last is the ordinary unclassified control.
        for model in ("constructor", "__proto__", "toString", "openai/gpt-6-luna-fast"):
            result = run_validator([{"model": model, "variant": "high"}])[0]
            self.assertTrue(result.startswith(UNCLASSIFIED), (model, result))


class MutationControls(unittest.TestCase):
    def test_missing_marker_is_detected(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIsNone(extract_block(text.replace(BEGIN, "", 1)))

    def test_removed_function_is_detected(self):
        block = required_block().replace(f"function {FUNCTION}(", "function removedVariantValidator(")
        with self.assertRaises(AssertionError):
            run_validator([{"model": "openai/gpt-6-luna", "variant": "high"}], block=block)

    def test_removed_empty_string_check_is_detected(self):
        block = required_block().replace('if (typeof variant === "string" && variant === "")', "if (false)")
        result = run_validator([{"model": "openai/gpt-6-luna", "variant": ""}], block=block)[0]
        self.assertTrue(result.startswith(UNKNOWN), result)

    def test_removed_luna_name_is_detected(self):
        block = required_block().replace('"none","low","medium","high","xhigh","max"', '"none","low"')
        result = run_validator([{"model": "openai/gpt-6-luna", "variant": "max"}], block=block)[0]
        self.assertTrue(result.startswith(UNKNOWN), result)


class TrackerActivation(unittest.TestCase):
    @staticmethod
    def activation_line(text):
        for line in text.splitlines():
            if ACTIVATION_REQUIREMENT in line and FUNCTION in line:
                return line
        return None

    def test_tracker_activation_note_references_the_exact_function(self):
        line = self.activation_line(TRACKER.read_text(encoding="utf-8"))
        self.assertIsNotNone(line, "tracker activation note must name the staged validator")

    def test_negative_control_missing_function_reference_is_detected(self):
        text = TRACKER.read_text(encoding="utf-8").replace(FUNCTION, "removedVariantReference")
        self.assertIsNone(self.activation_line(text))


class DigestPin(unittest.TestCase):
    def test_verifier_sha256_matches_the_plugin_pin(self):
        match = re.search(r'const VERIFY_SCRIPT_SHA256 = "([0-9a-f]{64})"',
                          PLUGIN.read_text(encoding="utf-8"))
        if match is None:
            raise AssertionError("workflow-health-check.ts must carry a single-line pin")
        self.assertEqual(match.group(1), hashlib.sha256(SCRIPT.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
