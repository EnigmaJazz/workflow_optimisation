# Change-set tool — specification (v1)

Status: specification for queue Q36. The implementation is `scripts/changeset.py`, and the
acceptance tests are `tests/test_changeset.py`. Where this document and the tests disagree, the
tests win, and this document is corrected in the same change.

## 1. Purpose

Apply a declared set of edits to files outside git (live OpenCode and Claude Code configuration,
gentle-ai-managed blocks), and revert them later, without overwriting anything another actor
changed in between: gentle-ai sync, other sessions, or hand edits. Repo-tracked files do not use
this tool; they ride git branches.

## 2. Command line

```
python3 scripts/changeset.py apply  --set <dir> --journal-root <dir> [--allow-root <dir>]... [--verify-cmd <cmd>] [--dry-run]
python3 scripts/changeset.py revert --journal <file> --journal-root <dir> [--allow-root <dir>]... [--verify-cmd <cmd>] [--dry-run]
python3 scripts/changeset.py status --set <dir> [--allow-root <dir>]...
```

- `--set <dir>` holds `changeset.json` and any content files it references.
- `--journal-root <dir>` holds journals and the lock. Production uses
  `<repo>/backups/changesets`.
- `--allow-root <dir>` can be repeated. Every target path must resolve, after `~` expansion and
  symlink resolution, to a path inside one of the allowed roots. If none is given, the allowed
  roots are `~/.config/opencode` and `~/.claude`.
- `--verify-cmd <cmd>` is a shell command run with `/bin/sh -c`.
- **Output:** exactly one JSON object on stdout (the report, section 7). Diagnostics go to
  stderr.

## 3. Change-set file (`changeset.json`)

```json
{
  "schema": "workflow-changeset/v1",
  "id": "gentle-ai-v4",
  "description": "free text",
  "ops": [ { "op": "...", "file": "...", ... } ]
}
```

- `id` matches `^[a-z0-9][a-z0-9._-]{0,63}$`.
- `ops` is a non-empty array. Ops run in array order, and each op sees the file state left by
  the ops before it.
- `file` is a path; `~` expands to `$HOME`.
- An unknown `schema`, unknown `op`, missing required field, or invalid `id` makes the whole set
  invalid. The tool refuses (exit 3) before touching any file.

### 3.1 Operation types

`expect_before` states the exact current value the op is written against. "Exact" means JSON
equality for JSON values, and byte-for-byte equality for text.

| `op` | Fields | Meaning |
|---|---|---|
| `json_set` | `file`, `path`, `expect_before`, `value` | Set the value at `path` |
| `json_delete` | `file`, `path`, `expect_before` | Remove the member or element at `path` |
| `block_replace` | `file`, `begin`, `end`, `expect_before`, `value` | Replace the text strictly between the `begin` and `end` marker lines |
| `file_create` | `file`, `content_file` | Create `file` with the bytes of `<set>/<content_file>` |
| `file_remove` | `file`, `expect_sha256` | Move `file` into the journal directory |

- **`path`** is an RFC 6901 JSON Pointer, for example `/agent/gentle-orchestrator/prompt` or
  `/plugin/1`. The parent of the target must exist.
- **`expect_before` for `json_set`** may be `{"$absent": true}`, meaning the member must not
  exist yet. The op then adds it, which is only valid where the parent is an object.
- **JSON files** are plain JSON. JSONC is out of scope in v1, and a file that fails to parse as
  JSON is a conflict for that op.
- **`block_replace`:** `begin` and `end` are whole lines without their newline, and each must
  occur exactly once in the file, `begin` before `end`. The block is everything after the
  `begin` line's newline, up to the start of the `end` line. Zero, or more than one, occurrence
  of a marker is a conflict.

## 4. Evaluating an op

For each op, the tool reads the current state and classifies it:

| Current state | Outcome | Write? |
|---|---|---|
| equals `expect_before` | `applied` | yes |
| already equals the target (`value`; `$absent` after a delete; created bytes; file gone after a remove) | `already_applied` | no |
| anything else, including a missing file or a parse failure | `conflict` | no |

`file_create` treats an absent file as applying. If the file exists, the outcome is
`already_applied` when its bytes equal the content, and `conflict` otherwise.

`file_remove` treats a present file as applying when its SHA-256 equals `expect_sha256`, an
absent file as `already_applied`, and anything else as `conflict`.

A conflicting op is skipped and the run continues with the next op. A conflict never changes
any byte of any file.

### 4.1 Byte preservation

`json_set`, `json_delete` and `block_replace` change only the bytes of the target. Every byte
outside the edited value or member span (JSON) or the block (text) stays identical, including
indentation, key order, trailing newline and other formatting.

- New JSON values are serialised with `json.dumps(value, ensure_ascii=False)`, and indented to
  match the target's line when the value spans several lines.
- `json_delete` also removes the separating comma and the whitespace that belong only to the
  removed member or element.

### 4.2 Atomic writes

Each changed file is written to a temporary file in the same directory, flushed, `fsync`ed, and
renamed over the target. The original mode bits are preserved.

## 5. Journal, lock and resume

- **Lock:** `<journal-root>/.lock`, created with `O_CREAT|O_EXCL`, containing the PID.
  - If the lock exists and its PID is alive, refuse (exit 3, `refused: lock_held`).
  - If the PID is dead, remove the stale lock, report `stale_lock_cleared: true`, and continue.
  - The lock is released on every exit path.
- **Journal:** one directory per run, `<journal-root>/<set-id>/<UTC timestamp>-<pid>/`,
  containing `journal.jsonl` plus copies of removed files under `removed/`.
- **Line types** in `journal.jsonl`, each one JSON object followed by `\n`, flushed and `fsync`ed
  before the tool proceeds:
  - `{"type":"header","schema":"workflow-changeset-journal/v1","set_id":…,"set_sha256":…,"started":…}`
  - `{"type":"intent","index":i,"op":…,"file":…,"before":…,"target":…}`, written BEFORE the
    file write. `before` and `target` are the values or text involved. For `file_remove`, the
    journal also records the path of the copy under `removed/`.
  - `{"type":"outcome","index":i,"outcome":"applied|already_applied|conflict","reason":…}`,
    written after the write.
  - `{"type":"seal","ops":n,"sha256":<sha256 of all preceding lines>}`, the last line, written
    only after every op has an outcome.
- **Ordering for `file_remove`:** copy the file into `removed/` (and `fsync`) first, then write
  the intent, then unlink the original. A crash between these steps loses nothing.
- **Resume:** re-running `apply` after an interrupted run starts a new journal. Ops that already
  took effect evaluate as `already_applied`, and the rest apply normally. The interrupted journal
  is left as it is.

## 6. Revert

`revert --journal <dir>/journal.jsonl` undoes the ops recorded as `applied`, in reverse order.

| Current state | Outcome | Write? |
|---|---|---|
| equals what apply wrote (`target`) | `reverted` | restore `before` |
| already equals `before` | `already_reverted` | no |
| anything else | `drift` | no; reported and left as it is |

- Ops whose outcome was `already_applied` or `conflict` are not reverted; apply wrote nothing for
  them.
- `file_remove` revert: if the original path is absent, move the journal copy back. If the path
  exists, the outcome is `already_reverted` when its SHA-256 equals the copy's, and `drift`
  otherwise.
- `file_create` revert: if the file's bytes equal the created content, move it into the revert
  journal directory (never delete). If the file is absent, the outcome is `already_reverted`;
  otherwise it is `drift`.
- **Refusal (exit 3, nothing touched):** a missing journal; a journal whose lines do not parse;
  an unknown journal schema; or a sealed journal whose seal `sha256` does not match.
  - An unsealed journal, from an interrupted apply, is accepted. Only ops with an `applied`
    outcome line are reverted. An intent with no outcome line is reported as `unknown` and not
    touched.
- Revert writes its own journal (`<journal-root>/<set-id>/revert-<timestamp>-<pid>/`), with the
  same line types, and takes the same lock.

## 7. Report and exit codes

The report always includes:
- `command`, `set_id`, `dry_run`, `journal` (path or null);
- `results`: a list of `{"index", "op", "file", "outcome", "reason"}`;
- `counts`: a map from outcome to count;
- `verify`: `{"before": exit code|null, "after": exit code|null}`;
- `refused`: a reason string, or null.

| Exit | Meaning |
|---|---|
| 0 | every op `applied`/`already_applied` (or `reverted`/`already_reverted`) |
| 2 | finished, but at least one `conflict`, `drift` or `unknown` |
| 3 | refused before any file write: invalid set or journal, lock held, path outside the allowed roots, `--verify-cmd` failed before the run |
| 1 | internal error |

## 8. Dry run

`--dry-run` evaluates and reports outcomes exactly as a real run would, but writes nothing: no
file, no journal, no lock. `--verify-cmd` is not run.

## 9. Verification gate

With `--verify-cmd`, the command runs before any write. A non-zero exit refuses the run (exit 3,
`refused: verify_failed`, `verify.before` set). After the run, the command runs again and
`verify.after` records its exit code. A failing post-run check does not change the outcomes; it
is reported. In production the command is `bash verify-workflow.sh`.

## 10. Path safety

Before anything is written, every `file` in the set is resolved: `~` expanded, then
`os.path.realpath` (for a file that does not exist yet, the realpath of its parent). Any target
outside every allowed root refuses the whole run (exit 3, `refused: path_outside_allowed_roots`).

## 11. `status`

Read-only. It evaluates every op as `apply` would and reports, without lock, journal or writes,
in the same report format with `command: "status"`. The exit code follows section 7.
