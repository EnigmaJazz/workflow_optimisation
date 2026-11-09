#!/usr/bin/env python3
"""Verify skills named by workflow prompts against an installed skill registry."""
import os
import sys
from pathlib import Path

# Named by the global prompt and workflow route handoff: pm-handoff.
REQUIRED_SKILLS = (
    "pm-handoff",
    # Named by the workflow-odd-secure delivery handoff reference.
    "work-unit-commits",
    # Named by the workflow-odd-secure delivery handoff reference.
    "chained-pr",
    # Named by the global routing entrypoint.
    "workflow-route",
    # Named by the secure ODD adapter handoff.
    "workflow-odd-secure",
    # Named by the Systematic route adapter handoff.
    "workflow-systematic",
)


def usage():
    print("error\tusage: check-prompt-references.py <foreign-repo> <skills-root> [--this-repo PATH] [--probe NAME]…")
    return 2


def parse_args(argv):
    if len(argv) < 2:
        return None
    foreign_repo, skills_root = argv[:2]
    this_repo = None
    probes = []
    index = 2
    while index < len(argv):
        arg = argv[index]
        if arg == "--this-repo" and index + 1 < len(argv) and this_repo is None:
            this_repo = argv[index + 1]
            index += 2
        elif arg == "--probe" and index + 1 < len(argv):
            probes.append(argv[index + 1])
            index += 2
        else:
            return None
    return foreign_repo, skills_root, this_repo, probes


def error(message):
    print(f"error\t{message}")
    return 0


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        return usage()
    foreign_arg, skills_arg, this_arg, probes = parsed
    foreign_repo = Path(foreign_arg)
    try:
        foreign_real = foreign_repo.resolve(strict=True)
    except OSError:
        return error(f"foreign repo {foreign_arg} is not an existing directory")
    if not foreign_real.is_dir():
        return error(f"foreign repo {foreign_arg} is not an existing directory")

    if this_arg is not None:
        try:
            this_real = Path(this_arg).resolve(strict=True)
        except OSError:
            return error(f"this repo {this_arg} cannot be resolved")
        if foreign_real == this_real:
            return error(f"foreign repo {foreign_arg} resolves to this repo {this_arg}")

    skills_root = Path(skills_arg).resolve()
    os.chdir(foreign_real)
    inventory = list(probes)
    inventory.extend(REQUIRED_SKILLS)
    for name in inventory:
        skill_path = skills_root / name / "SKILL.md"
        if not skill_path.exists() and not skill_path.is_symlink():
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                f"(missing file); frontmatter must declare name: {name}"
            )
        if skill_path.is_symlink() or not skill_path.is_file():
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                f"(not a regular file); frontmatter must declare name: {name}"
            )
        try:
            lines = skill_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                f"(not a regular file); frontmatter must declare name: {name}"
            )
        if not lines or lines[0].strip() != "---":
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                f"(frontmatter name mismatch); frontmatter must declare name: {name}"
            )
        frontmatter = []
        terminated = False
        for line in lines[1:]:
            if line.strip() == "---":
                terminated = True
                break
            frontmatter.append(line)
        if not terminated:
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                "(unterminated frontmatter); frontmatter must open and close with --- "
                f"and declare name: {name}"
            )
        if f"name: {name}" not in [line.strip() for line in frontmatter]:
            return error(
                f"prompt-named skill {name} does not resolve: expected {skill_path} "
                f"(frontmatter name mismatch); frontmatter must declare name: {name}"
            )

    print(
        f"ok\t{len(inventory)} prompt-named skills resolve from {skills_root} "
        f"(checked from {foreign_real}; cwd {Path.cwd()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
