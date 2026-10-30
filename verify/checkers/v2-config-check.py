"""Check that the OpenCode V2 config root matches what `derive-v2-config.py` produces from global-config (queue Q44).

usage: v2-config-check.py <workspace> <sandbox-repo> <v2-config-root>
Prints one line: clean|error <TAB> detail (the verifier's recovery protocol).

Read-only by construction: derive runs as a dry run (never --apply) and this checker writes nothing. V2's config root is
generated and owned by the owner's `derive --apply`, so drift is reported, never repaired by the verifier."""
import subprocess
import sys
from pathlib import Path


def main(argv):
    workspace, sandbox, root = Path(argv[1]), Path(argv[2]), Path(argv[3])
    derive = workspace / "scripts" / "derive-v2-config.py"
    if not derive.is_file():
        print(f"error\tthe derive script is missing: {derive}")
        return 0
    if not root.is_dir():
        print(f"error\tthe V2 config root does not exist: {root}; run derive --apply")
        return 0
    try:
        result = subprocess.run(
            [sys.executable, str(derive), "--source", str(workspace / "global-config"), "--sandbox-repo", str(sandbox), "--target", str(root)],
            capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        print("error\tderive did not finish within 120 seconds")
        return 0
    lines = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
    if result.returncode != 0:
        print(f"error\tderive failed ({result.returncode}): {(lines[-1] if lines else 'no output')[:200]}")
        return 0
    # A healthy dry run ends with this marker. Its absence means derive did not finish or changed its output, which must
    # never read as "no drift".
    if not any("dry-run - nothing was written" in line for line in lines):
        print("error\tderive gave no dry-run completion marker; its output cannot be trusted as a clean result")
        return 0
    pending = [line.split("would ", 1)[1] for line in lines if "would " in line and "dry-run" not in line]
    if pending:
        names = "; ".join(item.split("/")[-1] for item in pending[:5])
        print(f"error\t{len(pending)} V2 config file(s) differ from global-config ({names}); run derive --apply")
        return 0
    # Notes that change what V2 will honour (a setting that moved or could not move) are worth seeing even when nothing drifted.
    notes = [line.split("note: ", 1)[1] for line in lines if "note: " in line and line.split("note: ", 1)[1].startswith(("moved ", "kept "))]
    suffix = "".join(f"; note: {note[:160]}" for note in notes[:3])
    print(f"clean\tthe V2 config root matches global-config ({root}){suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
