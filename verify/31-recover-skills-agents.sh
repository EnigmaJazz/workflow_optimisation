recover_reviewed_router_skills() {
  python3 - "$ROUTER_SKILLS_SOURCE" "$SKILLS_DIR" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_ROUTER_SKILLS'
from pathlib import Path
import os
import shutil
import sys
import tempfile

source = Path(sys.argv[1])
target = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]
manifest = {
    "workflow-route": ("SKILL.md", "references/session-decisions.md"),
    "workflow-odd-secure": ("SKILL.md", "references/odd-and-review.md"),
    "workflow-systematic": ("SKILL.md", "references/specialists.md"),
}
errors = []
changed = []
for name, files in manifest.items():
    for directory in (source / name, source / name / "references", target / name, target / name / "references"):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            errors.append(f"unsafe skill directory: {directory}")
    entry = source / name / "SKILL.md"
    if not entry.is_file() or entry.is_symlink():
        errors.append(f"missing reviewed skill: {entry}")
        continue
    text = entry.read_text(encoding="utf-8")
    if not text.startswith(f"---\nname: {name}\n") or "\ndescription: " not in text:
        errors.append(f"invalid skill frontmatter: {entry}")
    for relative in files:
        src = source / name / relative
        dest = target / name / relative
        if not src.is_file() or src.is_symlink():
            errors.append(f"missing reviewed skill file: {src}")
        elif dest.is_symlink() or (dest.exists() and not dest.is_file()):
            errors.append(f"unsafe skill destination: {dest}")
        elif not dest.is_file() or dest.read_bytes() != src.read_bytes():
            changed.append((src,dest))
if errors:
    print("error\t" + "; ".join(errors))
    raise SystemExit(0)
if not changed:
    print("clean\tthree reviewed workflow skills and references are current")
    raise SystemExit(0)
backup = backup_root / run_id / "workflow-skills"
backup.mkdir(parents=True, exist_ok=True)
os.chmod(backup_root / run_id, 0o700)
for src,dest in changed:
    if dest.exists():
        saved = backup / dest.relative_to(target)
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest,saved)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".reviewed-skill.",dir=dest.parent)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(src.read_bytes())
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp_path,0o644)
        os.replace(temp_path,dest)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
print(f"repaired\t{backup}: {len(changed)} reviewed skill file(s)")
PY_RECOVER_ROUTER_SKILLS
}

recover_agents_file() {
  python3 - "$AGENTS_FILE" "$AGENTS_SOURCE" "$ROUTING_CANONICAL" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_AGENTS'
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
routing_path = Path(sys.argv[3])
backup_root = Path(sys.argv[4])
run_id = sys.argv[5]
route_start = "<!-- user:workflow-routing -->"
route_end = "<!-- /user:workflow-routing -->"
legacy_start = "<!-- gentle-ai:engram-protocol -->"
legacy_end = "<!-- /gentle-ai:engram-protocol -->"

try:
    canonical_full = source.read_text(encoding="utf-8")
    canonical_route = routing_path.read_text(encoding="utf-8").rstrip("\n")
except FileNotFoundError as exc:
    print(f"error\tcanonical AGENTS source missing: {exc.filename}")
    raise SystemExit(0)

if canonical_full.count(route_start) != 1 or canonical_full.count(route_end) != 1:
    print("error\tcanonical AGENTS source has malformed workflow-routing markers")
    raise SystemExit(0)

def canonical_block(start, end):
    if canonical_full.count(start) != 1 or canonical_full.count(end) != 1:
        print(f"error\tcanonical AGENTS source has malformed {start} markers")
        raise SystemExit(0)
    a = canonical_full.index(start)
    b = canonical_full.index(end, a) + len(end)
    return canonical_full[a:b]

codegraph_start = "<!-- gentle-ai:codegraph-guidance -->"
codegraph_end = "<!-- /gentle-ai:codegraph-guidance -->"
cancel_start = "<!-- gentle-ai:subagent-cancellation -->"
cancel_end = "<!-- /gentle-ai:subagent-cancellation -->"
search_start = "<!-- user:grep-tool-enforcement -->"
search_end = "<!-- /user:grep-tool-enforcement -->"
sandbox_start = "<!-- gentle-ai:sandbox-tool-contract -->"
sandbox_end = "<!-- /gentle-ai:sandbox-tool-contract -->"
canonical_codegraph = canonical_block(codegraph_start, codegraph_end)
canonical_cancel = canonical_block(cancel_start, cancel_end)
canonical_search = canonical_block(search_start, search_end)
canonical_sandbox = canonical_block(sandbox_start, sandbox_end)

if target.is_file():
    try:
        current = target.read_text(encoding="utf-8")
    except Exception:
        current = ""
else:
    current = ""

new_text = current
fallback_reason = ""
if not current:
    new_text = canonical_full
    fallback_reason = "missing or unreadable active AGENTS.md"
else:
    # Remove only the precisely marked Gentle AI legacy protocol. Unmarked user
    # prose is preserved. Ambiguous marker state falls back to the reviewed full
    # source rather than guessing deletion boundaries.
    ls = new_text.count(legacy_start)
    le = new_text.count(legacy_end)
    if ls == 1 and le == 1 and new_text.index(legacy_start) < new_text.index(legacy_end):
        pattern = re.escape(legacy_start) + r".*?" + re.escape(legacy_end) + r"\n*"
        new_text = re.sub(pattern, "", new_text, count=1, flags=re.DOTALL)
    elif ls or le:
        new_text = canonical_full
        fallback_reason = "ambiguous legacy Engram markers"

    if not fallback_reason:
        starts = new_text.count(route_start)
        ends = new_text.count(route_end)
        if starts == 0 and ends == 0:
            pass
        elif starts == 1 and ends == 1 and new_text.index(route_start) < new_text.index(route_end):
            a = new_text.index(route_start)
            b = new_text.index(route_end, a) + len(route_end)
            new_text = new_text[:a] + new_text[b:]
        else:
            new_text = canonical_full
            fallback_reason = "ambiguous workflow-routing markers"

# Recover only reviewed bounded sections; keep other Gentle AI managed prose,
# generated instructions and unrelated user blocks intact. Unknown or
# partially marked sections fail closed instead of replacing all AGENTS.md.
def replace_marked(text, start, end, canonical, insert_before=None):
    starts, ends = text.count(start), text.count(end)
    if starts == ends == 1 and text.index(start) < text.index(end):
        a = text.index(start)
        b = text.index(end, a) + len(end)
        return text[:a] + canonical + text[b:]
    if starts == ends == 0 and insert_before and text.count(insert_before) == 1:
        a = text.index(insert_before)
        return text[:a] + canonical + "\n\n" + text[a:]
    raise ValueError(f"ambiguous AGENTS section: {start} ({starts} starts, {ends} ends)")

try:
    new_text = replace_marked(new_text, codegraph_start, codegraph_end,
                              canonical_codegraph, "<!-- gentle-ai:persona -->")
    # Repair the previously shipped duplicate closing marker only when its
    # first close precedes the known review extension and the last follows it.
    if new_text.count(cancel_start) == 1 and new_text.count(cancel_end) == 2:
        first = new_text.index(cancel_end)
        second = new_text.index(cancel_end, first + len(cancel_end))
        review = new_text.find("### Review process (extends the rule above)")
        if new_text.index(cancel_start) < first < review < second:
            new_text = new_text[:first] + new_text[first + len(cancel_end):]
    new_text = replace_marked(new_text, cancel_start, cancel_end,
                              canonical_cancel, "<!-- user:grep-tool-enforcement -->")
    new_text = replace_marked(new_text, sandbox_start, sandbox_end,
                              canonical_sandbox, search_start)
    new_text = replace_marked(new_text, search_start, search_end,
                              canonical_search, "<!-- user:workflow-routing -->")
    # gentle-ai v4 retired the host SDD runtime block. Converge the deployed
    # file by REMOVAL only; never re-insert a canonical copy. Zero markers is a
    # no-op; one correct pair is deleted with its trailing newlines; anything
    # ambiguous (differing counts or reversed order) fails closed.
    retired = ("<!-- user:host-sdd-runtime-boundaries -->", "<!-- /user:host-sdd-runtime-boundaries -->")
    hs = new_text.count(retired[0])
    he = new_text.count(retired[1])
    if hs == 0 and he == 0:
        pass
    elif hs == 1 and he == 1 and new_text.index(retired[0]) < new_text.index(retired[1]):
        a = new_text.index(retired[0])
        b = new_text.index(retired[1], a) + len(retired[1])
        while b < len(new_text) and new_text[b] == "\n":
            b += 1
        new_text = new_text[:a] + new_text[b:]
    else:
        raise ValueError(f"ambiguous host SDD runtime boundaries markers ({hs} starts, {he} ends)")
except ValueError as exc:
    print(f"error\tAGENTS bounded-section recovery refused: {exc}")
    raise SystemExit(0)

# Put reviewed user-owned routing after the generator's managed guidance. This
# keeps secure delegation and the Magic Context ODD mirror authoritative after
# a Gentle AI v3 sync, which otherwise reintroduces host-inline/Engram prose.
if new_text.count(route_start) == 1 and new_text.count(route_end) == 1:
    a = new_text.index(route_start)
    b = new_text.index(route_end, a) + len(route_end)
    new_text = new_text[:a] + new_text[b:]
new_text = new_text.rstrip() + "\n\n" + canonical_route + "\n"

if new_text == current:
    print("clean\treviewed AGENTS routing and memory policy are current")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "AGENTS.md.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".AGENTS.md.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(new_text.rstrip("\n") + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

detail = f"{backup}"
if fallback_reason:
    detail += f" (full-source fallback: {fallback_reason})"
print(f"repaired\t{detail}")
PY_RECOVER_AGENTS
}

