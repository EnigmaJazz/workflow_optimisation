"""The verifier's full source text for tests that parse embedded blocks.

verify-workflow.sh is a thin entry; its checks live in verify/NN-*.sh (queue Q04). Tests that look for
a block inside the verifier read the entry plus every module in manifest order, which is the same
text the shell executes."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def module_paths():
    entry = (REPO / "verify-workflow.sh").read_text(encoding="utf-8")
    block = re.search(r"# BEGIN VERIFY_MODULES\n(.*?)# END VERIFY_MODULES", entry, re.S).group(1)
    return [REPO / "verify" / name for name in re.findall(r'^\s*"([^ "]+) [0-9a-f]{64}"', block, re.M)]


def verifier_text():
    parts = [(REPO / "verify-workflow.sh").read_text(encoding="utf-8")]
    parts += [p.read_text(encoding="utf-8") for p in module_paths()]
    return "\n".join(parts)
