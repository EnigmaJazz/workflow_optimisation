"""Build changeset.json for the Q76 Antigravity agents.

Run from the repository root: python3 changesets/q76-antigravity-agents/build_changeset.py

`expect_before` for each skill edit is read from the live skill file, so the set is written
against the exact current bytes; the change-set tool then refuses if anything changed since.
"""

import json
from pathlib import Path

SET_DIR = Path(__file__).resolve().parent
SKILL_REF = "~/.gemini/antigravity/skills/argon-subagent/SKILL.md"
SKILL = Path(SKILL_REF).expanduser()
AGENTS = "~/.gemini/config/agents"

TRIGGER_BEGIN = "name: argon-subagent"
TRIGGER_END = "# Argon Subagent (`gemini-4-argon`) Execution Guidelines"
RULES_BEGIN = "## 1. Strict Invocation Rules"
RULES_END = "## 2. Environment & Execution Binary"

NEW_TRIGGER = (
    "description: Delegates hard reasoning, complex architectural refactoring, and deep debugging tasks "
    "to gemini-4-argon via API using developer credits. Trigger ONLY when user explicitly includes the "
    'phrase "use Argon API", "ask Argon API", or "run Argon API". Argon is also available on the '
    "Antigravity subscription: for advice, use the `argon_advisor` agent instead, which costs no "
    "developer credits. Execute with `/usr/bin/python3 ~/.gemini/config/skills/argon-subagent/scripts/"
    "call_argon.py` (or direct script execution). Never invoke automatically.\n"
    "---\n"
    "\n"
)
NEW_RULES = (
    '- **Explicit Trigger Only:** Never invoke this skill automatically. Only run when the user '
    'explicitly requests the API route ("use Argon API", "ask Argon API", "run Argon API"). A plain '
    '"use Argon" means the subscription `argon_advisor` agent, not this skill.\n'
    "- **Single Execution:** Do NOT run unattended execution loops or retry loops that burn developer "
    "credits. Run **once** per explicit user request.\n"
    "\n"
)


def between(text, begin, end):
    """Return the text strictly between the BEGIN and END marker lines (each exactly once)."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\n") == begin]
    ends = [i for i, line in enumerate(lines) if line.rstrip("\n") == end]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise SystemExit(f"markers not unique or out of order: {begin!r} / {end!r}")
    return "".join(lines[starts[0] + 1 : ends[0]])


def main():
    text = SKILL.read_text(encoding="utf-8")
    changeset = {
        "schema": "workflow-changeset/v1",
        "id": "q76-antigravity-agents",
        "description": (
            "Q76: Antigravity Argon advisor that delegates evidence gathering to a Gemini 3.8 Flash "
            "subagent, and the argon-subagent API skill moved to an explicit 'use Argon API' trigger."
        ),
        "ops": [
            {
                "op": "file_create",
                "file": f"{AGENTS}/evidence_collector/agent.md",
                "content_file": "evidence_collector.agent.md",
            },
            {
                "op": "file_create",
                "file": f"{AGENTS}/argon_advisor/agent.md",
                "content_file": "argon_advisor.agent.md",
            },
            {
                "op": "block_replace",
                "file": SKILL_REF,
                "begin": TRIGGER_BEGIN,
                "end": TRIGGER_END,
                "expect_before": between(text, TRIGGER_BEGIN, TRIGGER_END),
                "value": NEW_TRIGGER,
            },
            {
                "op": "block_replace",
                "file": SKILL_REF,
                "begin": RULES_BEGIN,
                "end": RULES_END,
                "expect_before": between(text, RULES_BEGIN, RULES_END),
                "value": NEW_RULES,
            },
        ],
    }
    (SET_DIR / "changeset.json").write_text(json.dumps(changeset, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
