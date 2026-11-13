import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "dispatch-worker.sh"


class Orca(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.path.expanduser("~"))
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "orca.args"
        self.repo = root / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / ".codegraph").mkdir()

        fake_orca = self.bin / "orca"
        fake_orca.write_text(
            "#!/usr/bin/env bash\n"
            'printf "%s\\n" "$@" >> "$FAKE_LOG"\n'
            'if [ "$1 $2" = "orchestration worker-list" ]; then\n'
            '  printf "%s\\n" "${FAKE_WORKER_LIST-}"\n'
            '  exit "${FAKE_WORKER_RC:-0}"\n'
            'fi\n'
            'if [ "$1 $2" = "terminal list" ]; then\n'
            '  printf "%s\\n" "${FAKE_TERMINAL_LIST-}"\n'
            '  exit "${FAKE_TERMINAL_RC:-0}"\n'
            'fi\n'
            'if [ "$1 $2" = "orchestration worker-start" ]; then\n'
            '  printf "%s\\n" "${FAKE_OUT:-}"\n'
            '  exit "${FAKE_RC:-0}"\n'
            'fi\n'
            "exit 0\n"
        )
        fake_orca.chmod(fake_orca.stat().st_mode | stat.S_IXUSR)

        fake_gentle_ai = self.bin / "gentle-ai"
        fake_gentle_ai.write_text('#!/usr/bin/env bash\nmkdir -p "${@: -1}/.codegraph"\n')
        fake_gentle_ai.chmod(fake_gentle_ai.stat().st_mode | stat.S_IXUSR)

    def run(self, *args, **env):
        if args and isinstance(args[0], unittest.TestResult):
            return super().run(*args, **env)
        process_env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "FAKE_LOG": str(self.log),
            **env,
        }
        result = subprocess.run(
            [str(SCRIPT), str(self.repo), *args],
            env=process_env,
            capture_output=True,
            text=True,
        )
        return type(
            "Result",
            (),
            {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "log": self.log.read_text() if self.log.exists() else "",
            },
        )()

    def test_dispatch_wrapper(self):
        dispatch = lambda value: {"FAKE_OUT": json.dumps({"result": {"dispatch": {"dispatchId": value}}})}
        def worker_list(rows):
            return {"ok": True, "result": {"workers": rows}}
        def worker(handle, dispatch_id="ctx_reuse", run_id="run_x", resource=None):
            row = {"dispatchId": dispatch_id, "taskId": "task_x", "runId": run_id,
                   "workerState": "working", "dispatchStatus": "dispatched",
                   "agentTerminalHandle": handle, "terminalState": "active"}
            if resource is not None:
                row["resource"] = resource
            return worker_list([row])
        def terminal_list(rows):
            return {"ok": True, "result": {"terminals": rows}}
        def terminal(handle, identity="opencode2"):
            return terminal_list([{"handle": handle, "agentIdentity": identity}])
        def config(handle="term_reuse", identity="opencode2", worker_data=None, **extra):
            return {**dispatch("ctx_reuse"), "FAKE_TERMINAL_LIST": json.dumps(terminal(handle, identity)),
                    "FAKE_WORKER_LIST": json.dumps(worker_data if worker_data is not None else
                                                    worker(handle, resource={"ownershipState": "owned"})), **extra}

        injected = 'term_x"; touch INJECTION_PATH; #'
        injection_file = Path(self.tmp.name) / "injected"
        injected = injected.replace("INJECTION_PATH", str(injection_file))
        cases = [
            ("fresh-opencode2-retained", ("--agent", "opencode2", "--spec", "X"), dispatch("ctx_fresh"), True, True),
            ("reused-opencode2-retained", ("--terminal", "term_reuse", "--spec", "X"), config(), True, True),
            ("reused-codex-not-retained", ("--terminal", "term_codex", "--spec", "X"), config("term_codex", "codex"), False, True),
            ("caller-claim-does-not-win", ("--agent", "codex", "--terminal", "term_reuse", "--spec", "X"), config(), True, True),
            ("unresolved-terminal-not-retained", ("--terminal", "term_unknown", "--spec", "X"), {**dispatch("ctx_unknown"), "FAKE_TERMINAL_LIST": "{}"}, False, True),
            ("worker-list-only-fake-does-not-retain", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_LIST": "{}"}, False, True),
            ("terminal-list-failure-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_RC": "1"}, False, True),
            ("worker-list-failure-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_RC": "1"}, False, True),
            ("absent-handle-not-retained", ("--terminal", "term_reuse", "--spec", "X"), config("different"), False, True),
            ("duplicate-rows-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_LIST": json.dumps(terminal_list(terminal("term_reuse")["result"]["terminals"] * 2))}, False, True),
            ("duplicate-with-null-identity-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_LIST": json.dumps(terminal_list([terminal("term_reuse")["result"]["terminals"][0], {"handle": "term_reuse", "agentIdentity": None}]))}, False, True),
            ("null-identity-not-retained", ("--terminal", "term_reuse", "--spec", "X"), config(identity=None), False, True),
            ("ownership-run-and-dispatch-mismatch-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker("term_reuse", "ctx_other", "run_other", {"ownershipState": "owned"}))}, False, True),
            ("ownership-not-owned-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker("term_reuse", "ctx_reuse", resource={"ownershipState": "user_owned"}))}, False, True),
            ("ownership-missing-row-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker_list([]))}, False, True),
            ("injection-handle-not-retained", ("--terminal", injected, "--spec", "X"), {**config(injected), "FAKE_WORKER_LIST": json.dumps(worker_list([]))}, False, True),
            ("other-profile-not-retained", ("--terminal", "term_reuse", "--spec", "X"), config(identity="claude2"), False, True),
            ("ownership-run-tie-retained", ("--terminal", "term_reuse", "--run", "run_x", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker("term_reuse", "ctx_other", "run_x", {"ownershipState": "owned"}))}, True, True),
            ("ownership-state-absent-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker("term_reuse", resource={}))}, False, True),
            ("resource-missing-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker("term_reuse"))}, False, True),
            ("resource-not-object-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps(worker_list([{**worker("term_reuse", resource={})["result"]["workers"][0], "resource": "owned"}]))}, False, True),
            ("terminal-list-ok-false-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_LIST": json.dumps({**terminal("term_reuse"), "ok": False})}, False, True),
            ("worker-list-ok-false-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps({**worker("term_reuse", resource={"ownershipState": "owned"}), "ok": False})}, False, True),
            ("terminal-list-error-with-success-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_TERMINAL_LIST": json.dumps({**terminal("term_reuse"), "error": "reported"})}, False, True),
            ("worker-list-error-with-success-not-retained", ("--terminal", "term_reuse", "--spec", "X"), {**config(), "FAKE_WORKER_LIST": json.dumps({**worker("term_reuse", resource={"ownershipState": "owned"}), "error": "reported"})}, False, True),
            ("nonzero-child-status-preserved", ("--agent", "opencode2", "--spec", "X"), {**dispatch("ctx_nonzero"), "FAKE_RC": "7"}, False, False, 7),
            ("receipt-validated-for-codex-too", ("--agent", "codex", "--spec", "X"), {"FAKE_OUT": "not json"}, False, False, None),
            ("codex-policy-prepended", ("--agent", "codex", "--spec", "REVIEW THE DIFF", "--run", "run_x"), dispatch("ctx_codex"), False, True),
        ]
        receipt_defects = {
            "empty": {"FAKE_OUT": "", "FAKE_RC": "0"},
            "malformed": {"FAKE_OUT": "not json at all"},
            "error-success": {"FAKE_OUT": '{"success":false,"error":"boom","result":{"dispatch":{"dispatchId":"ctx_bad"}}}', "FAKE_RC": "0"},
        }
        for profile in ("opencode2", "codex", "claude2"):
            for defect, env in receipt_defects.items():
                cases.append((f"{profile}-{defect}-rejected", ("--agent", profile, "--spec", "X"), env, False, False, None))

        for case in cases:
            name, args, env, retained, successful, *status = case
            expected_status = status[0] if status else (0 if successful else 0)
            with self.subTest(case=name):
                self.log.unlink(missing_ok=True)
                result = self.run(*args, **env)
                if expected_status is None:
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertEqual(result.returncode, expected_status, result.stderr)
                if successful:
                    dispatch_id = json.loads(env["FAKE_OUT"]) ["result"]["dispatch"]["dispatchId"]
                    self.assertIn(dispatch_id, result.stdout)
                    self.assertEqual(result.stdout.splitlines()[-1], dispatch_id)
                self.assertEqual("worker-retain" in result.log, retained, result.log)
                if retained:
                    self.assertIn(dispatch_id, result.log)
                if not successful:
                    self.assertNotIn("worker-retain", result.log)
                if name == "injection-handle-not-retained":
                    self.assertFalse(injection_file.exists())
                if name == "codex-policy-prepended":
                    self.assertIn("## Command policy (Codex)", result.log)
                    self.assertIn("REVIEW THE DIFF", result.log)
