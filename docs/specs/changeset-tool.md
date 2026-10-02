# Change-set tool — specification (v1.3)

Status: specification for queue Q36. The implementation is `scripts/changeset.py`, and the
acceptance tests are `tests/test_changeset.py`. Where this document and the tests disagree, the
tests win, and this document is corrected in the same change.

v1.1 (2026-10-02) folds in two reviews and the `advisor-design` advice:
- a compare-and-swap write;
- reconciling an interrupted `file_remove`;
- enforced revert order;
- exact JSON splice and indent rules;
- `content_file` containment;
- missing parent is a conflict;
- file modes;
- a per-set lock.

v1.2 records the implementation's choices for cases the spec left open: relative paths are
invalid, no-op ops are `already_applied`, torn final journal lines are tolerated, the report gains
`detail`/`error`, and dry run evaluates against an overlay.

v1.3 (implementation review): a middle-array-element delete is now revertible, and journal
discovery fails closed.

## 1. Purpose

Apply a declared set of edits to files outside git (live OpenCode and Claude Code configuration,
gentle-ai-managed blocks), and revert them later, without overwriting anything another actor
changed in between: gentle-ai sync, other sessions, or hand edits. Repo-tracked files do not use
this tool; they ride git branches.

**Out of scope:** preflight policy gates such as the in-flight SDD check (queue Q39). The caller
supplies them through `--verify-cmd` (section 9), which must exit 0 before any write.

## 2. Command line

```
python3 scripts/changeset.py apply  --set <dir> --journal-root <dir> [--allow-root <dir>]... [--verify-cmd <cmd>] [--dry-run]
python3 scripts/changeset.py revert --journal <file> --journal-root <dir> [--allow-root <dir>]... [--verify-cmd <cmd>] [--dry-run]
python3 scripts/changeset.py status --set <dir> [--allow-root <dir>]...
```

- `--set <dir>` holds `changeset.json` and any content files it references.
- `--journal-root <dir>` holds the journals and the per-set locks. Production uses
  `<repo>/backups/changesets`.
- `--allow-root <dir>` can be repeated. Every target path must resolve inside one of the allowed
  roots (section 10). If none is given, the allowed roots are `~/.config/opencode` and
  `~/.claude`.
- `--verify-cmd <cmd>` is a shell command run with `/bin/sh -c`.
- **Output:** exactly one JSON object on stdout (the report, section 7), including on refusal.
  Diagnostics go to stderr.

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
- `file` is an absolute path, or one starting with `~` (which expands to `$HOME`). A relative
  `file` makes the set invalid.
- **Invalid set:** an unknown `schema`, unknown `op`, missing required field, invalid `id`, or a
  `content_file` that does not resolve inside the set directory (section 10). The tool refuses
  (exit 3, `refused: invalid_set`) before touching any file.

### 3.1 Operation types

`expect_before` states the exact current value the op is written against. "Exact" means JSON
equality for JSON values, and byte-for-byte equality for text.

| `op` | Fields | Meaning |
|---|---|---|
| `json_set` | `file`, `path`, `expect_before`, `value` | Set the value at `path` |
| `json_delete` | `file`, `path`, `expect_before` | Remove the member or element at `path` |
| `block_replace` | `file`, `begin`, `end`, `expect_before`, `value` | Replace the text strictly between the `begin` and `end` marker lines |
| `file_create` | `file`, `content_file`, optional `mode` | Create `file` with the bytes of `<set>/<content_file>`, mode `mode` (octal string, default `"0644"`) |
| `file_remove` | `file`, `expect_sha256` | Move `file` into the journal directory |

- **`path`** is an RFC 6901 JSON Pointer, including the `~1` (`/`) and `~0` (`~`) escapes, for
  example `/agent/gentle-orchestrator/prompt` or `/plugin/1`.
  - The parent of the target must exist for both `json_set` and `json_delete`. A missing parent
    is a `conflict`, so a pointer typo can never pass as success.
  - For `json_delete`, a missing member under an existing parent is `already_applied`.
- **`expect_before` for `json_set`** may be `{"$absent": true}`, meaning the member must not
  exist yet. The op then inserts it, which is only valid where the parent is an object.
- **JSON files** are plain JSON. JSONC is out of scope in v1, and a file that fails to parse as
  JSON is a conflict for that op.
- **`block_replace`:** `begin` and `end` are whole lines without their newline, and each must
  occur exactly once in the file, `begin` before `end`. The block is everything after the
  `begin` line's newline, up to the start of the `end` line. Zero, or more than one, occurrence
  of a marker is a conflict.
- **`file_create`** never creates directories. If the parent directory is missing, the outcome is
  `conflict`.

## 4. Evaluating an op

The full outcome vocabulary:
- apply and status: `applied`, `already_applied`, `conflict`;
- revert: `reverted`, `already_reverted`, `drift`, `unknown`.

`unknown` is used only by revert (section 6).

For each op, the tool reads the current state (the bytes of the file) and classifies it:

| Current state | Outcome | Write? |
|---|---|---|
| equals `expect_before` | `applied` | yes (section 4.2) |
| already equals the target (`value`; member absent after a delete; created bytes; file gone after a remove) | `already_applied` | no |
| anything else, including a missing file, missing parent or a parse failure | `conflict` | no |

- **`file_create`:** an absent file (with an existing parent directory) applies. If the file
  exists, the outcome is `already_applied` when its bytes equal the content, and `conflict`
  otherwise.
- **`file_remove`:** a present file applies when its SHA-256 equals `expect_sha256`. An absent
  file is `already_applied`, and anything else is `conflict`.
- **No-op ops:** an op whose `expect_before` already equals its target evaluates as
  `already_applied` and never writes.
- **Conflicts:** a conflicting op is skipped and the run continues with the next op. A conflict
  never changes any byte of any file.

### 4.1 Byte rules for JSON edits

`json_set`, `json_delete` and `block_replace` change only the bytes defined below. Every other
byte of the file stays identical, including key order, trailing newline and formatting.

**Terms**
- **Container:** the object or array that is the target's parent.
- **Multi-line container:** its opening and closing brackets are on different lines.
- **Indent unit:** the leading whitespace of the first line of the file that has any, made of
  spaces or tabs. If no line has leading whitespace, two spaces.
- **Line indent:** the leading whitespace of the line on which a given member or element begins.

**Serialising a new value**
- In a single-line container, and for any scalar or empty array or object:
  `json.dumps(value, ensure_ascii=False)`.
- Otherwise: `json.dumps(value, ensure_ascii=False, indent=<indent unit>)`, with every line after
  the first prefixed by the line indent of the target (for insertion, the line indent of the
  container's last member).
- Example: setting `/agent/x` in `{\n  "agent": {\n    "x": 1\n  }\n}\n` to
  `{"model": "m"}` gives `{\n  "agent": {\n    "x": {\n      "model": "m"\n    }\n  }\n}\n`.

**Replace** (`json_set` on an existing member or element): only the bytes of the old value
change, and they become the serialised new value.

**Insert** (`json_set` with `$absent`; objects only). Key `k` is serialised with `json.dumps`.
- Non-empty single-line object: insert `, "k": <value>` immediately after the end of the last
  member's value. `{"a": 1}` becomes `{"a": 1, "b": 2}`.
- Non-empty multi-line object: insert `,` immediately after the end of the last member's value,
  then `\n` + that member's line indent + `"k": <value>`. `{\n  "a": 1\n}` becomes
  `{\n  "a": 1,\n  "b": 2\n}`.
- Empty object: replace the whole interior with `"k": <value>`. `{}` and `{ }` both become
  `{"b": 2}`.

**Delete** (`json_delete`; members and elements alike):
- Not the last of several: remove from the start of the member (its key's opening quote) or
  element, up to the start of the next one. That removes its value, its comma, and the whitespace
  after the comma. `{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}` with `/b` removed becomes
  `{\n  "a": 1,\n  "c": 3\n}`; `["x", "y", "z"]` with `/1` removed becomes `["x", "z"]`.
- The last of several: remove from the comma after the previous member's value, up to the end of
  the removed value. `{\n  "a": 1,\n  "c": 3\n}` with `/c` removed becomes `{\n  "a": 1\n}`.
- The only member or element: replace the interior with `""` in a single-line container, or with
  `"\n"` followed by the closing bracket's line indent in a multi-line one. `{\n  "a": 1\n}`
  becomes `{\n}`.

### 4.2 Writes: atomic and compare-and-swap

1. Read the target's bytes, B0. All classification uses B0.
2. Build the new bytes and write them to a temporary file in the same directory. Set the mode,
   flush and `fsync`.
3. Re-read the target. If its bytes differ from B0, delete the temporary file, write nothing, and
   record the outcome `conflict` with reason `concurrent_change`.
4. Otherwise rename the temporary file over the target.

A concurrent writer can still change the file in the short window between steps 3 and 4. Other
actors take no lock, so that window cannot be closed; it is documented as a residual risk.

**Test hook:** when the environment variable `CHANGESET_TEST_BEFORE_COMMIT` is set, step 3 first
runs it with `/bin/sh -c "$CHANGESET_TEST_BEFORE_COMMIT" sh <target-path>`. It exists only to make
the race testable; production never sets it.

**Modes:**
- Replacing an existing file keeps its mode bits.
- `file_create` uses the op's `mode`.
- The `removed/` copy and a restored file keep the original mode (`shutil.copy2` semantics).
- Ownership is never changed.

## 5. Journal, lock and resume

- **Lock:** an exclusive, non-blocking `fcntl.flock` on `<journal-root>/<set-id>/.lock`, one lock
  per set. The file is created if missing; the holder writes its PID into it for diagnostics only.
  - If another process holds the flock, refuse (exit 3, `refused: lock_held`).
  - The file's existence or content never decides anything, and the report never carries
    `stale_lock_cleared`. The kernel releases the flock when its holder exits or crashes.
  - Different sets do not block each other; section 4.2's compare-and-swap protects a file two
    sets both touch.
  - The flock is released on every exit path. The lock file may remain.
- **Journal:** one directory per run, `<journal-root>/<set-id>/<UTC timestamp>-<pid>/`,
  containing `journal.jsonl` plus copies of removed files under `removed/`.
- **Line types** in `journal.jsonl`, each one JSON object followed by `\n`, flushed and `fsync`ed
  before the tool proceeds:
  - `{"type":"header","schema":"workflow-changeset-journal/v1","kind":"apply"|"revert","set_id":…,"set_sha256":…,"started":…,"previous_journal":<path|null>,"reverts":<path|null>}`
    - `previous_journal` is the newest existing apply journal for the same set, sealed or not, at
      start.
    - `reverts` is set only on revert journals.
  - `{"type":"intent","index":i,"op":…,"file":…,"before":…,"target":…}`, written BEFORE the
    file write. `before` and `target` are the values or text involved. For `file_remove`, the
    intent also records the path of the copy under `removed/` and the original mode.
  - `{"type":"outcome","index":i,"outcome":…,"reason":…}`, written after the write.
  - `{"type":"seal","ops":n,"sha256":<sha256 of all preceding lines>}`, the last line, written
    only after every op has an outcome.
- **Ordering for `file_remove`:** copy the file into `removed/` (`fsync`ed, mode kept), then write
  the intent, then unlink the original. A crash between these steps loses nothing; section 6
  reconciles it.
- **Resume:** re-running `apply` after an interrupted run starts a new journal whose
  `previous_journal` names the interrupted one. Ops that already took effect evaluate as
  `already_applied`, and the rest apply normally. The interrupted journal is left as it is.

## 6. Revert

`revert --journal <dir>/journal.jsonl` undoes, in reverse order, the ops the journal recorded as
`applied`.

| Current state | Outcome | Write? |
|---|---|---|
| equals what apply wrote (`target`) | `reverted` | restore `before` (section 4.2 compare-and-swap) |
| already equals `before` | `already_reverted` | no |
| anything else | `drift` | no; reported and left as it is |

- **Not reverted:** ops whose outcome was `already_applied` or `conflict`; apply wrote nothing for
  them. A journal with only such ops reverts cleanly (exit 0, empty `results`).
- **`file_remove`:** if the original path is absent, copy the journal copy back with its mode. If
  the path exists, the outcome is `already_reverted` when its SHA-256 equals the copy's, and
  `drift` otherwise.
- **`json_delete` of an array element:** the index alone cannot identify the removed element
  after the delete, because later elements shift. So the intent records the parent array's full
  value before and after (`before_parent`, `after_parent`). Revert restores the element only when
  the current parent array equals `after_parent`, by replacing the parent array's bytes with the
  serialised `before_parent`. It is `already_reverted` when the parent equals `before_parent`,
  and `drift` otherwise.
- **`file_create`:** if the file's bytes equal the created content, move it into the revert
  journal directory (never delete). If the file is absent, the outcome is `already_reverted`;
  otherwise it is `drift`.
- **Intent without outcome** (interrupted apply):
  - A `file_remove` is reconciled. If the original path is absent and the journal copy's SHA-256
    equals `expect_sha256`, the copy is restored (`reverted`). If the original is present, the
    outcome is `already_reverted`.
  - Every other op is reported `unknown` and not touched, because whether its write happened
    cannot be proven.
- **Enforced order:** revert refuses (exit 3, `refused: newer_journal_not_reverted`, naming it)
  while a newer apply journal for the same set exists that has an `applied` outcome or an
  `unknown`-eligible intent, unless a sealed revert journal whose `reverts` names it already
  exists. Revert the newest journal first.
- **Refusal (exit 3, nothing touched):** a missing journal; a journal with a line that does not
  parse; an unknown journal schema; or a sealed journal whose seal `sha256` does not match. An
  unsealed journal is accepted.
  - **Exception, a torn final line:** an unparseable LAST line with no trailing newline is a torn
    write from a crash, and is ignored.
    - Safe for a torn intent: the intent is written and fsynced before its write, so a torn
      intent means the write never happened.
    - Safe for a torn outcome: the op then has an intent without an outcome, and the
      intent-without-outcome rules apply.
    - Safe for a torn seal: the journal is then unsealed.
  - An unparseable line that ends in a newline is never torn; it refuses with `invalid_journal`.
- **Journal discovery fails closed.** Both the revert-order check and apply's `previous_journal`
  lookup read every journal of the set. If any of them fails to load (it does not parse, has an
  unknown schema or a bad seal; a torn final line is still tolerated), the run refuses with
  `invalid_journal`, and `detail` names the bad journal. An operator must inspect it and move it
  aside. It is never skipped silently.
- Revert writes its own journal (`<journal-root>/<set-id>/revert-<timestamp>-<pid>/`), with
  `kind: "revert"` and `reverts` set, and takes the set's lock.

## 7. Report and exit codes

The report always includes:
- `command`, `set_id`, `dry_run`, `journal` (path or null);
- `results`: a list of `{"index", "op", "file", "outcome", "reason"}`;
- `counts`: a map from outcome to count;
- `verify`: `{"before": exit code|null, "after": exit code|null}`;
- `refused`: a reason string, or null.

On a refusal the report may add `detail` (for example the newer journal for
`newer_journal_not_reverted`); on exit 1 it adds `error`.

| Exit | Meaning |
|---|---|
| 0 | every op `applied`/`already_applied` (or `reverted`/`already_reverted`), or nothing to revert |
| 2 | finished, but at least one `conflict`, `drift` or `unknown` |
| 3 | refused before any file write: `invalid_set`, `invalid_journal`, `lock_held`, `path_outside_allowed_roots`, `verify_failed`, `newer_journal_not_reverted` |
| 1 | internal error |

## 8. Dry run

`--dry-run` evaluates and reports outcomes exactly as a real run would, but writes nothing: no
file, no journal, no lock file, and no directory. `--verify-cmd` is not run. Dry run and `status`
evaluate against an in-memory overlay, so a later op on the same file sees the earlier ops'
results, as in a real run.

## 9. Verification gate

With `--verify-cmd`, the command runs before any write. A non-zero exit refuses the run (exit 3,
`refused: verify_failed`, `verify.before` set). After the run, the command runs again and
`verify.after` records its exit code. A failing post-run check does not change the outcomes; it
is reported.

In production the command is the verifier, plus any preflight the caller needs (for example the
Q39 in-flight SDD check).

## 10. Path safety

Before anything is written, every `file` in the set is resolved: `~` expanded, then
`os.path.realpath` (for a file that does not exist yet, the realpath of its parent joined with the
name).
- Any target outside every allowed root refuses the whole run (exit 3,
  `refused: path_outside_allowed_roots`).
- Every `content_file` must resolve (realpath) inside the set directory. Otherwise the set is
  invalid (exit 3, `refused: invalid_set`).

## 11. `status`

Read-only and best-effort. It evaluates every op as `apply` would and reports, in the same
format with `command: "status"`, without lock, journal or writes. It may observe a concurrent
apply mid-run. The exit code follows section 7.
