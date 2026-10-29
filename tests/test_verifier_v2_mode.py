"""Verifier V2 mode (queue Q44): version detection and the probe wrapper.

Facts from the B1 probe on OpenCode V2 2.2.0: `opencode run` hangs unless stdin is closed, a plain call
joins a shared background service on a fixed port (use --standalone), `agent list` / `debug agent`
do not exist. V1 behaviour must stay exactly as it was."""
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULES = REPO / "verify"
VERSION_MODULE = MODULES / "21-opencode-major.sh"
PROBE = MODULES / "checkers" / "oc-probe.sh"


class Stub:
    """A fake `opencode` on PATH that records argv and stdin and prints a chosen version."""

    def __init__(self, version_output):
        self.dir = Path(tempfile.mkdtemp())
        self.log = self.dir / "calls.log"
        script = self.dir / "opencode"
        script.write_text(
            "#!/usr/bin/env bash\n"
            f'if [ "${{1:-}}" = "--version" ]; then printf %s\\\\n {version_output!r}; exit 0; fi\n'
            f'printf "ARGS:%s\\n" "$*" >> "{self.log}"\n'
            f'if [ -t 0 ]; then echo "STDIN:tty" >> "{self.log}"; else printf "STDIN:%s\\n" "$(timeout 2 cat | head -c 40)" >> "{self.log}"; fi\n'
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    def env(self, **extra):
        return {**os.environ, "PATH": f"{self.dir}:{os.environ['PATH']}", **extra}

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def detect(version_output=None, env_major=None):
    stub = Stub(version_output) if version_output is not None else None
    try:
        env = stub.env() if stub else {**os.environ, "PATH": "/nonexistent-dir"}
        if env_major is not None:
            env["WORKFLOW_VERIFY_OPENCODE_MAJOR"] = env_major
        script = f'VERIFY_MODULE_DIR="{MODULES}"\nsource "{VERSION_MODULE}"\necho "MAJOR=$OC_MAJOR"\n'
        r = subprocess.run([shutil.which("bash"), "-c", script], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout.strip(), r.stderr
    finally:
        if stub:
            stub.close()


class VersionDetection(unittest.TestCase):
    def test_v1_plain_version(self):
        self.assertEqual(detect("1.19.5")[:2], (0, "MAJOR=1"))

    def test_v2_prefixed_version(self):
        self.assertEqual(detect("opencode v2.2.0")[:2], (0, "MAJOR=2"))

    def test_unparseable_output_is_unknown_not_a_guess(self):
        self.assertEqual(detect("garbage")[:2], (0, "MAJOR=0"))

    def test_a_missing_opencode_is_unknown(self):
        self.assertEqual(detect(None)[:2], (0, "MAJOR=0"))

    def test_the_override_wins_for_fixtures(self):
        self.assertEqual(detect("1.19.5", env_major="2")[:2], (0, "MAJOR=2"))

    def test_a_non_numeric_override_is_ignored(self):
        self.assertEqual(detect("1.19.5", env_major="two")[:2], (0, "MAJOR=1"))


def probe(major, version="1.19.5", stdin_data=b"piped-input", args=("run", "--format", "json", "hello")):
    stub = Stub(version)
    try:
        env = stub.env(OC_MAJOR=major)
        r = subprocess.run(["bash", str(PROBE), *args], input=stdin_data, capture_output=True, env=env)
        return r.returncode, stub.calls()
    finally:
        stub.close()


class ProbeWrapper(unittest.TestCase):
    def test_v1_call_is_unchanged_and_stdin_is_inherited(self):
        rc, calls = probe("1")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], "ARGS:run --format json hello")
        self.assertEqual(calls[1], "STDIN:piped-input")

    def test_v2_call_is_standalone_with_closed_stdin(self):
        rc, calls = probe("2")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], "ARGS:--standalone run --format json hello")
        self.assertEqual(calls[1], "STDIN:")

    def test_unknown_major_behaves_as_v1(self):
        self.assertEqual(probe("0")[1][0], "ARGS:run --format json hello")

    def test_the_exit_status_of_opencode_is_preserved(self):
        stub = Stub("1.19.5")
        try:
            (stub.dir / "opencode").write_text('#!/usr/bin/env bash\nexit 7\n')
            r = subprocess.run(["bash", str(PROBE), "run"], capture_output=True, env=stub.env(OC_MAJOR="1"), stdin=subprocess.DEVNULL)
            self.assertEqual(r.returncode, 7)
        finally:
            stub.close()


class Wiring(unittest.TestCase):
    def test_no_module_calls_opencode_directly_for_probes(self):
        import re
        for module in sorted(MODULES.glob("*.sh")):
            for number, line in enumerate(module.read_text().splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") or "command_exists" in stripped or "echo " in stripped or "fail " in stripped:
                    continue
                self.assertIsNone(re.search(r"\bopencode (agent|debug|run)\b", stripped), f"{module.name}:{number}: {stripped}")

    def test_probes_go_through_the_wrapper(self):
        text = (MODULES / "61-section-10-behavioural.sh").read_text()
        self.assertGreaterEqual(text.count('bash "$OC_PROBE" run'), 3)

    def test_the_version_module_runs_before_the_sections(self):
        names = sorted(p.name for p in MODULES.glob("*.sh"))
        self.assertLess(names.index("21-opencode-major.sh") if "21-opencode-major.sh" in names else 99, names.index("50-section-0-recover.sh"))


if __name__ == "__main__":
    unittest.main()
