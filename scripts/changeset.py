#!/usr/bin/env python3
"""Non-destructive change-set apply/revert tool (spec: docs/specs/changeset-tool.md).

    changeset.py apply  --set DIR --journal-root DIR [--allow-root DIR]... [--verify-cmd CMD] [--dry-run]
    changeset.py revert --journal FILE --journal-root DIR [--allow-root DIR]... [--verify-cmd CMD] [--dry-run]
    changeset.py status --set DIR [--allow-root DIR]...

Every invocation prints exactly one JSON report on stdout. Python 3 stdlib only.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

SET_SCHEMA = "workflow-changeset/v1"
JOURNAL_SCHEMA = "workflow-changeset-journal/v1"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
DEFAULT_ROOTS = ("~/.config/opencode", "~/.claude")
ABSENT = {"$absent": True}


class Refuse(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class Concurrent(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# JSON scanner: records the span of every container member
# --------------------------------------------------------------------------
WS = " \t\r\n"


class Node:
    __slots__ = ("kind", "s", "e", "items")

    def __init__(self, kind, s, e=None, items=None):
        self.kind, self.s, self.e, self.items = kind, s, e, items


class Item:
    __slots__ = ("key", "ks", "node")

    def __init__(self, key, ks, node):
        self.key, self.ks, self.node = key, ks, node


def _ws(t, i):
    n = len(t)
    while i < n and t[i] in WS:
        i += 1
    return i


def _string_end(t, i):
    i += 1
    while True:
        c = t[i]
        if c == "\\":
            i += 2
        elif c == '"':
            return i + 1
        else:
            i += 1


def _value(t, i):
    c = t[i]
    if c == "{":
        node = Node("obj", i, items=[])
        i = _ws(t, i + 1)
        if t[i] == "}":
            node.e = i + 1
            return node, node.e
        while True:
            if t[i] != '"':
                raise ValueError("key expected")
            ks = i
            ke = _string_end(t, i)
            key = json.loads(t[ks:ke])
            i = _ws(t, ke)
            if t[i] != ":":
                raise ValueError("colon expected")
            v, i = _value(t, _ws(t, i + 1))
            node.items.append(Item(key, ks, v))
            i = _ws(t, i)
            if t[i] == ",":
                i = _ws(t, i + 1)
            elif t[i] == "}":
                node.e = i + 1
                return node, node.e
            else:
                raise ValueError("bad object")
    if c == "[":
        node = Node("arr", i, items=[])
        i = _ws(t, i + 1)
        if t[i] == "]":
            node.e = i + 1
            return node, node.e
        while True:
            v, i = _value(t, i)
            node.items.append(Item(None, v.s, v))
            i = _ws(t, i)
            if t[i] == ",":
                i = _ws(t, i + 1)
            elif t[i] == "]":
                node.e = i + 1
                return node, node.e
            else:
                raise ValueError("bad array")
    if c == '"':
        e = _string_end(t, i)
        return Node("lit", i, e), e
    j = i
    while j < len(t) and t[j] not in WS + ",]}":
        j += 1
    if j == i:
        raise ValueError("value expected")
    return Node("lit", i, j), j


def scan(text):
    json.loads(text)  # strict validation first
    node, i = _value(text, _ws(text, 0))
    if _ws(text, i) != len(text):
        raise ValueError("trailing data")
    return node


def jeq(a, b):
    """JSON equality that does not conflate booleans with numbers."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, dict):
        return (isinstance(b, dict) and a.keys() == b.keys()
                and all(jeq(a[k], b[k]) for k in a))
    if isinstance(a, list):
        return (isinstance(b, list) and len(a) == len(b)
                and all(jeq(x, y) for x, y in zip(a, b)))
    return a == b


def pointer_tokens(path):
    return [t.replace("~1", "/").replace("~0", "~") for t in path.split("/")[1:]]


def _index(node, tok):
    if node.kind == "obj":
        found = None
        for i, it in enumerate(node.items):
            if it.key == tok:
                found = i
        return found
    if node.kind == "arr" and re.fullmatch(r"0|[1-9][0-9]*", tok) and int(tok) < len(node.items):
        return int(tok)
    return None


def locate(root, tokens):
    """Return (parent, member index or None), or None when the parent is missing."""
    node = root
    for tok in tokens[:-1]:
        if node.kind not in ("obj", "arr"):
            return None
        i = _index(node, tok)
        if i is None:
            return None
        node = node.items[i].node
    if node.kind not in ("obj", "arr"):
        return None
    return node, _index(node, tokens[-1])


# -- byte-exact splicing (spec 4.1) -----------------------------------------
def line_indent(text, pos):
    ls = text.rfind("\n", 0, pos) + 1
    j = ls
    while j < len(text) and text[j] in " \t":
        j += 1
    return text[ls:j]


def multiline(text, parent):
    return "\n" in text[parent.s:parent.e]


def indent_unit(text):
    for line in text.split("\n"):
        ws = line[:len(line) - len(line.lstrip(" \t"))]
        if ws and line.strip():
            return ws
    return "  "


def serialise(text, parent, value, indent):
    plain = json.dumps(value, ensure_ascii=False)
    if not isinstance(value, (dict, list)) or not value or not multiline(text, parent):
        return plain
    lines = json.dumps(value, ensure_ascii=False, indent=indent_unit(text)).split("\n")
    return lines[0] + "".join("\n" + indent + ln for ln in lines[1:])


def splice_replace(text, parent, idx, value):
    it = parent.items[idx]
    ser = serialise(text, parent, value, line_indent(text, it.ks))
    return text[:it.node.s] + ser + text[it.node.e:]


def splice_insert(text, parent, key, value):
    ks = json.dumps(key, ensure_ascii=False)
    if not parent.items:
        body = ks + ": " + json.dumps(value, ensure_ascii=False)
        return text[:parent.s + 1] + body + text[parent.e - 1:]
    last = parent.items[-1]
    end = last.node.e
    if multiline(text, parent):
        ind = line_indent(text, last.ks)
        ins = ",\n" + ind + ks + ": " + serialise(text, parent, value, ind)
    else:
        ins = ", " + ks + ": " + json.dumps(value, ensure_ascii=False)
    return text[:end] + ins + text[end:]


def splice_delete(text, parent, idx):
    items = parent.items
    if len(items) == 1:
        mid = "\n" + line_indent(text, parent.e - 1) if multiline(text, parent) else ""
        return text[:parent.s + 1] + mid + text[parent.e - 1:]
    if idx < len(items) - 1:
        return text[:items[idx].ks] + text[items[idx + 1].ks:]
    comma = text.index(",", items[idx - 1].node.e)
    return text[:comma] + text[items[idx].node.e:]


def splice_reinsert(text, parent, idx, raw, indent):
    """Inverse of splice_delete: put raw member text back at position idx."""
    items = parent.items
    ml = multiline(text, parent)
    if not items:
        if ml:
            return (text[:parent.s + 1] + "\n" + indent + raw + "\n"
                    + line_indent(text, parent.e - 1) + text[parent.e - 1:])
        return text[:parent.s + 1] + raw + text[parent.e - 1:]
    if idx < len(items):
        pos = items[idx].ks
        sep = ",\n" + line_indent(text, pos) if ml else ", "
        return text[:pos] + raw + sep + text[pos:]
    last = items[-1]
    sep = ",\n" + line_indent(text, last.ks) if ml else ", "
    return text[:last.node.e] + sep + raw + text[last.node.e:]


def _checked(new):
    try:
        json.loads(new)
    except ValueError:
        return None
    return new


def json_apply(op, text):
    """Classify and build the new text. Returns (outcome, reason, new_text, extra)."""
    try:
        root = scan(text)
    except (ValueError, IndexError, RecursionError):
        return "conflict", "invalid_json", None, None
    tokens = pointer_tokens(op["path"])
    loc = locate(root, tokens)
    if loc is None:
        return "conflict", "missing_parent", None, None
    parent, idx = loc
    exp = op["expect_before"]
    if op["op"] == "json_set":
        value = op["value"]
        absent_exp = isinstance(exp, dict) and exp == ABSENT
        if idx is None:
            if not absent_exp:
                return "conflict", "member_missing", None, None
            if parent.kind != "obj":
                return "conflict", "parent_not_object", None, None
            new = _checked(splice_insert(text, parent, tokens[-1], value))
            extra = {"before": ABSENT, "target": value, "mode": "insert"}
        else:
            node = parent.items[idx].node
            cur = json.loads(text[node.s:node.e])
            if jeq(cur, value):
                return "already_applied", None, None, None
            if absent_exp or not jeq(cur, exp):
                return "conflict", "value_mismatch", None, None
            new = _checked(splice_replace(text, parent, idx, value))
            extra = {"before": cur, "target": value, "mode": "replace",
                     "before_text": text[node.s:node.e]}
    else:
        if idx is None:
            return "already_applied", None, None, None
        it = parent.items[idx]
        cur = json.loads(text[it.node.s:it.node.e])
        if not jeq(cur, exp):
            return "conflict", "value_mismatch", None, None
        new = _checked(splice_delete(text, parent, idx))
        extra = {"before": cur, "target": ABSENT, "member_text": text[it.ks:it.node.e],
                 "member_indent": line_indent(text, it.ks), "member_index": idx}
        if parent.kind == "arr":
            before_parent = json.loads(text[parent.s:parent.e])
            extra["before_parent"] = before_parent
            extra["after_parent"] = before_parent[:idx] + before_parent[idx + 1:]
    if new is None:
        return "conflict", "splice_invalid", None, None
    return "applied", None, new, extra


def json_revert(r, text):
    """Returns (outcome, reason, new_text)."""
    try:
        root = scan(text)
    except (ValueError, IndexError, RecursionError):
        return "drift", "invalid_json", None
    tokens = pointer_tokens(r["json_path"])
    loc = locate(root, tokens)
    if loc is None:
        return "drift", "missing_parent", None
    parent, idx = loc
    if r["op"] == "json_set" and r["mode"] == "insert":
        if idx is None:
            return "already_reverted", None, None
        node = parent.items[idx].node
        if not jeq(json.loads(text[node.s:node.e]), r["target"]):
            return "drift", "value_changed", None
        new = _checked(splice_delete(text, parent, idx))
    elif r["op"] == "json_set":
        if idx is None:
            return "drift", "member_missing", None
        node = parent.items[idx].node
        cur = json.loads(text[node.s:node.e])
        if jeq(cur, r["target"]):
            new = _checked(text[:node.s] + r["before_text"] + text[node.e:])
        elif jeq(cur, r["before"]):
            return "already_reverted", None, None
        else:
            return "drift", "value_changed", None
    elif parent.kind == "arr" and "before_parent" in r:  # json_delete of an array element
        cur = json.loads(text[parent.s:parent.e])
        if jeq(cur, r["after_parent"]):
            node = root
            for tok in tokens[:-2]:
                node = node.items[_index(node, tok)].node
            container = node if len(tokens) >= 2 else parent
            ind = line_indent(text, parent.s)
            ser = serialise(text, container, r["before_parent"], ind)
            new = _checked(text[:parent.s] + ser + text[parent.e:])
        elif jeq(cur, r["before_parent"]):
            return "already_reverted", None, None
        else:
            return "drift", "value_changed", None
    else:  # json_delete
        if idx is not None:
            node = parent.items[idx].node
            if jeq(json.loads(text[node.s:node.e]), r["before"]):
                return "already_reverted", None, None
            return "drift", "value_changed", None
        new = _checked(splice_reinsert(text, parent, r["member_index"],
                                       r["member_text"], r["member_indent"]))
    if new is None:
        return "drift", "splice_invalid", None
    return "reverted", None, new


# -- block markers ----------------------------------------------------------
def block_span(text, begin, end):
    pos, b, e = 0, [], []
    for line in text.split("\n"):
        if line == begin:
            b.append((pos, len(line)))
        if line == end:
            e.append((pos, len(line)))
        pos += len(line) + 1
    if len(b) != 1 or len(e) != 1 or b[0][0] >= e[0][0]:
        return None
    return b[0][0] + b[0][1] + 1, e[0][0]


# --------------------------------------------------------------------------
# File access: real writes use compare-and-swap, dry runs use an overlay
# --------------------------------------------------------------------------
def read_or_none(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except (FileNotFoundError, NotADirectoryError):
        return None


def fsync_dir(path):
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def cas_write(path, b0, new, mode):
    """Write `new` over `path` only if it still holds b0 (None = absent)."""
    d = os.path.dirname(path)
    if mode is None:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    fd, tmp = tempfile.mkstemp(prefix=".changeset-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(new)
            f.flush()
            os.fchmod(f.fileno(), mode)
            os.fsync(f.fileno())
        hook = os.environ.get("CHANGESET_TEST_BEFORE_COMMIT")
        if hook:
            subprocess.run(["/bin/sh", "-c", hook, "sh", path], stdout=sys.stderr,
                           stdin=subprocess.DEVNULL, check=False)
        if read_or_none(path) != b0:
            raise Concurrent()
        os.replace(tmp, path)
        tmp = None
        fsync_dir(d)
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


class State:
    def __init__(self, dry):
        self.dry = dry
        self.overlay = {}

    def read(self, path):
        if path in self.overlay:
            return self.overlay[path]
        return read_or_none(path)

    def write(self, path, b0, new, mode):
        if self.dry:
            self.overlay[path] = new
        else:
            cas_write(path, b0, new, mode)


# --------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------
def now():
    return datetime.datetime.now(datetime.timezone.utc)


class Journal:
    def __init__(self, directory, header):
        self.dir = directory
        os.makedirs(directory)
        self.path = os.path.join(directory, "journal.jsonl")
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        fsync_dir(directory)
        fsync_dir(os.path.dirname(directory))
        self.h = hashlib.sha256()
        self.row(header)

    def row(self, row):
        data = (json.dumps(row, ensure_ascii=False) + "\n").encode()
        view = memoryview(data)
        while view:
            view = view[os.write(self.fd, view):]
        os.fsync(self.fd)
        self.h.update(data)

    def intent(self, row):
        self.row(row)

    def outcome(self, index, outcome, reason):
        self.row({"type": "outcome", "index": index, "outcome": outcome, "reason": reason})

    def seal(self, ops):
        self.row({"type": "seal", "ops": ops, "sha256": self.h.hexdigest()})

    def close(self):
        os.close(self.fd)


class NullJournal:
    dir = None
    path = None

    def intent(self, row):
        pass

    def outcome(self, *a):
        pass

    def seal(self, ops):
        pass

    def close(self):
        pass


def new_dir_name(set_dir, prefix, started):
    base = prefix + started.strftime("%Y%m%dT%H%M%S%fZ") + "-" + str(os.getpid())
    name, n = base, 0
    while os.path.exists(os.path.join(set_dir, name)):
        n += 1
        name = f"{base}.{n}"
    return os.path.join(set_dir, name)


def load_journal(path):
    """Parse and verify a journal. Returns dict with header, intents, outcomes, sealed."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        raise Refuse("invalid_journal", f"cannot read journal: {e}")
    lines = data.splitlines(keepends=True)
    rows = []
    for n, line in enumerate(lines):
        try:
            row = json.loads(line.decode("utf-8"))
            if not isinstance(row, dict) or "type" not in row:
                raise ValueError
        except ValueError:
            if n == len(lines) - 1 and not line.endswith(b"\n"):
                break  # torn final write of an interrupted run
            raise Refuse("invalid_journal", f"line {n + 1} does not parse")
        rows.append(row)
    if not rows or rows[0].get("type") != "header" or rows[0].get("schema") != JOURNAL_SCHEMA \
            or rows[0].get("kind") not in ("apply", "revert"):
        raise Refuse("invalid_journal", "bad or missing header")
    sealed = False
    for n, row in enumerate(rows):
        if row["type"] == "seal":
            if n != len(rows) - 1:
                raise Refuse("invalid_journal", "seal is not the last line")
            if row.get("sha256") != sha256(b"".join(lines[:n])):
                raise Refuse("invalid_journal", "seal does not match")
            sealed = True
    intents, outcomes = {}, {}
    for row in rows[1:]:
        if row["type"] == "intent" and isinstance(row.get("index"), int):
            intents[row["index"]] = row
        elif row["type"] == "outcome" and isinstance(row.get("index"), int):
            outcomes[row["index"]] = row
    return {"header": rows[0], "intents": intents, "outcomes": outcomes, "sealed": sealed}


def list_journals(set_journal_dir):
    """Apply and revert journals of a set; any unloadable journal refuses (fails closed)."""
    applies, reverts = [], []
    try:
        names = os.listdir(set_journal_dir)
    except OSError:
        return applies, reverts
    for name in names:
        jpath = os.path.join(set_journal_dir, name, "journal.jsonl")
        if not os.path.isfile(jpath):
            continue
        try:
            j = load_journal(jpath)
        except Refuse as e:
            raise Refuse("invalid_journal", f"{jpath}: {e.detail}")
        j["path"] = jpath
        j["name"] = name
        (reverts if j["header"]["kind"] == "revert" else applies).append(j)
    return applies, reverts


def journal_key(j):
    return (j["header"].get("started", ""), j["name"])


# --------------------------------------------------------------------------
# Set loading and path safety
# --------------------------------------------------------------------------
def inside(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def allowed_roots(given):
    roots = given or list(DEFAULT_ROOTS)
    return [os.path.realpath(os.path.expanduser(r)) for r in roots]


def resolve_target(f):
    p = os.path.expanduser(f)
    if not os.path.isabs(p):
        raise Refuse("invalid_set", f"relative path: {f}")
    return os.path.realpath(p)


def check_roots(paths, roots):
    for p in paths:
        if not any(inside(p, r) for r in roots):
            raise Refuse("path_outside_allowed_roots", p)


REQUIRED = {
    "json_set": ("file", "path", "expect_before", "value"),
    "json_delete": ("file", "path", "expect_before"),
    "block_replace": ("file", "begin", "end", "expect_before", "value"),
    "file_create": ("file", "content_file"),
    "file_remove": ("file", "expect_sha256"),
}


def load_set(set_dir):
    path = os.path.join(set_dir, "changeset.json")
    try:
        with open(path, "rb") as f:
            raw = f.read()
        doc = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as e:
        raise Refuse("invalid_set", f"cannot read changeset.json: {e}")
    if not isinstance(doc, dict) or doc.get("schema") != SET_SCHEMA:
        raise Refuse("invalid_set", "unknown schema")
    sid = doc.get("id")
    if not isinstance(sid, str) or not ID_RE.match(sid):
        raise Refuse("invalid_set", "invalid id")
    ops = doc.get("ops")
    if not isinstance(ops, list) or not ops:
        raise Refuse("invalid_set", "ops must be a non-empty array")
    set_real = os.path.realpath(set_dir)
    for n, op in enumerate(ops):
        if not isinstance(op, dict) or op.get("op") not in REQUIRED:
            raise Refuse("invalid_set", f"op {n}: unknown op")
        for field in REQUIRED[op["op"]]:
            if field not in op:
                raise Refuse("invalid_set", f"op {n}: missing {field}")
        for field in ("file", "path", "begin", "end", "content_file", "expect_sha256"):
            if field in op and not isinstance(op[field], str):
                raise Refuse("invalid_set", f"op {n}: {field} must be a string")
        if "path" in op and not op["path"].startswith("/"):
            raise Refuse("invalid_set", f"op {n}: path must be a JSON Pointer")
        if op["op"] == "block_replace" and not all(isinstance(op[k], str) for k in ("expect_before", "value")):
            raise Refuse("invalid_set", f"op {n}: block values must be strings")
        if op["op"] == "file_remove" and not re.fullmatch(r"[0-9a-f]{64}", op["expect_sha256"]):
            raise Refuse("invalid_set", f"op {n}: bad expect_sha256")
        op["_path"] = resolve_target(op["file"])
        if op["op"] == "file_create":
            mode = op.get("mode", "0644")
            if not isinstance(mode, str) or not re.fullmatch(r"0?[0-7]{3,4}", mode):
                raise Refuse("invalid_set", f"op {n}: bad mode")
            op["_mode"] = int(mode, 8)
            cf = os.path.realpath(os.path.join(set_dir, op["content_file"]))
            if not inside(cf, set_real) or not os.path.isfile(cf):
                raise Refuse("invalid_set", f"op {n}: content_file outside the set directory")
            with open(cf, "rb") as f:
                op["_content"] = f.read()
    return {"id": sid, "ops": ops, "sha256": sha256(raw)}


# --------------------------------------------------------------------------
# Evaluating ops
# --------------------------------------------------------------------------
def decode(b0):
    try:
        return b0.decode("utf-8")
    except UnicodeDecodeError:
        return None


def evaluate_apply(op, state):
    """Returns (outcome, reason, plan, intent_extra)."""
    path, kind = op["_path"], op["op"]
    try:
        b0 = state.read(path)
    except OSError:
        return "conflict", "unreadable", None, None
    if kind == "file_create":
        content = op["_content"]
        if b0 is not None:
            return (("already_applied", None, None, None) if b0 == content
                    else ("conflict", "file_exists_different", None, None))
        if not os.path.isdir(os.path.dirname(path)):
            return "conflict", "parent_missing", None, None
        plan = {"kind": "write", "path": path, "b0": None, "new": content, "mode": op["_mode"]}
        return "applied", None, plan, {"before": None, "target": sha256(content),
                                       "content_sha256": sha256(content), "file_mode": op["_mode"]}
    if kind == "file_remove":
        if b0 is None:
            return "already_applied", None, None, None
        if sha256(b0) != op["expect_sha256"]:
            return "conflict", "sha256_mismatch", None, None
        return "applied", None, {"kind": "remove", "path": path}, {
            "before": op["expect_sha256"], "target": None, "expect_sha256": op["expect_sha256"]}
    if b0 is None:
        return "conflict", "file_missing", None, None
    text = decode(b0)
    if text is None:
        return "conflict", "not_utf8", None, None
    if kind == "block_replace":
        span = block_span(text, op["begin"], op["end"])
        if span is None:
            return "conflict", "markers_not_unique", None, None
        cur = text[span[0]:span[1]]
        if cur == op["value"]:
            return "already_applied", None, None, None
        if cur != op["expect_before"]:
            return "conflict", "block_mismatch", None, None
        new = text[:span[0]] + op["value"] + text[span[1]:]
        extra = {"before": cur, "target": op["value"], "begin": op["begin"], "end": op["end"]}
    else:
        outcome, reason, new, extra = json_apply(op, text)
        if outcome != "applied":
            return outcome, reason, None, None
        extra["json_path"] = op["path"]
    plan = {"kind": "write", "path": path, "b0": b0, "new": new.encode("utf-8"), "mode": None}
    return "applied", None, plan, extra


def evaluate_revert(r, state, journal_dir, index):
    """r is the journal intent. Returns (outcome, reason, plan)."""
    path, kind = r["path"], r["op"]
    try:
        b0 = state.read(path)
    except OSError:
        return "drift", "unreadable", None
    if kind == "file_create":
        if b0 is None:
            return "already_reverted", None, None
        if sha256(b0) != r["content_sha256"]:
            return "drift", "content_changed", None
        dest = os.path.join(journal_dir or "", "created", f"{index}-{os.path.basename(path)}")
        return "reverted", None, {"kind": "move", "path": path, "dest": dest}
    if kind == "file_remove":
        if b0 is not None:
            return (("already_reverted", None, None) if sha256(b0) == r["expect_sha256"]
                    else ("drift", "path_exists_different", None))
        copy = read_or_none(r.get("removed_copy") or "")
        if copy is None or sha256(copy) != r["expect_sha256"]:
            return "drift", "journal_copy_unusable", None
        if not os.path.isdir(os.path.dirname(path)):
            return "drift", "parent_missing", None
        return "reverted", None, {"kind": "write", "path": path, "b0": None, "new": copy,
                                  "mode": r.get("mode", 0o644)}
    if b0 is None:
        return "drift", "file_missing", None
    text = decode(b0)
    if text is None:
        return "drift", "not_utf8", None
    if kind == "block_replace":
        span = block_span(text, r["begin"], r["end"])
        if span is None:
            return "drift", "markers_not_unique", None
        cur = text[span[0]:span[1]]
        if cur == r["target"]:
            new = text[:span[0]] + r["before"] + text[span[1]:]
        elif cur == r["before"]:
            return "already_reverted", None, None
        else:
            return "drift", "block_changed", None
    else:
        outcome, reason, new = json_revert(r, text)
        if outcome != "reverted":
            return outcome, reason, None
    return "reverted", None, {"kind": "write", "path": path, "b0": b0,
                              "new": new.encode("utf-8"), "mode": None}


def execute(plan, ok, fail, intent, state, journal, index):
    """Perform a planned step with its write-ahead intent. Returns (outcome, reason)."""
    try:
        kind = plan["kind"]
        if kind == "write":
            journal.intent(intent)
            state.write(plan["path"], plan["b0"], plan["new"], plan["mode"])
        elif kind == "remove":
            if state.dry:
                state.overlay[plan["path"]] = None
            else:
                rdir = os.path.join(journal.dir, "removed")
                os.makedirs(rdir, exist_ok=True)
                copy = os.path.join(rdir, f"{index}-{os.path.basename(plan['path'])}")
                shutil.copy2(plan["path"], copy)
                with open(copy, "rb") as f:
                    os.fsync(f.fileno())
                    good = sha256(f.read()) == intent["expect_sha256"]
                fsync_dir(rdir)
                if not good:
                    os.unlink(copy)
                    return fail, "concurrent_change"
                intent["removed_copy"] = copy
                intent["mode"] = stat.S_IMODE(os.stat(copy).st_mode)
                journal.intent(intent)
                os.unlink(plan["path"])
                fsync_dir(os.path.dirname(plan["path"]))
        elif kind == "move":
            journal.intent(intent)
            if state.dry:
                state.overlay[plan["path"]] = None
            else:
                os.makedirs(os.path.dirname(plan["dest"]), exist_ok=True)
                shutil.move(plan["path"], plan["dest"])
    except Concurrent:
        return fail, "concurrent_change"
    except OSError as e:
        return fail, f"io_error: {e.strerror or e}"
    return ok, None


# --------------------------------------------------------------------------
# Lock and verify
# --------------------------------------------------------------------------
def acquire_lock(set_journal_dir):
    os.makedirs(set_journal_dir, exist_ok=True)
    fd = os.open(os.path.join(set_journal_dir, ".lock"), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise Refuse("lock_held")
    try:
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode())  # diagnostics only
    except OSError:
        pass
    return fd


def run_verify(cmd):
    return subprocess.run(["/bin/sh", "-c", cmd], stdout=sys.stderr,
                          stdin=subprocess.DEVNULL, check=False).returncode


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def new_report(command, dry):
    return {"command": command, "set_id": None, "dry_run": dry, "journal": None,
            "results": [], "counts": {}, "verify": {"before": None, "after": None},
            "refused": None}


def add_result(report, index, op, file, outcome, reason):
    report["results"].append({"index": index, "op": op, "file": file,
                              "outcome": outcome, "reason": reason})


def run_apply_ops(ops, state, journal, report):
    for i, op in enumerate(ops):
        outcome, reason, plan, extra = evaluate_apply(op, state)
        if plan is not None:
            intent = {"type": "intent", "index": i, "op": op["op"], "file": op["file"],
                      "path": op["_path"]}
            intent.update(extra)
            outcome, reason = execute(plan, "applied", "conflict", intent, state, journal, i)
        journal.outcome(i, outcome, reason)
        add_result(report, i, op["op"], op["file"], outcome, reason)


def cmd_apply(a, report, status=False):
    cs = load_set(a.set)
    report["set_id"] = cs["id"]
    ops = cs["ops"]
    check_roots([op["_path"] for op in ops], allowed_roots(a.allow_root))
    if status or a.dry_run:
        run_apply_ops(ops, State(True), NullJournal(), report)
        return
    set_dir = os.path.join(a.journal_root, cs["id"])
    lock = acquire_lock(set_dir)
    try:
        if a.verify_cmd:
            report["verify"]["before"] = run_verify(a.verify_cmd)
            if report["verify"]["before"] != 0:
                raise Refuse("verify_failed")
        applies, _ = list_journals(set_dir)
        prev = max(applies, key=journal_key)["path"] if applies else None
        started = now()
        header = {"type": "header", "schema": JOURNAL_SCHEMA, "kind": "apply",
                  "set_id": cs["id"], "set_sha256": cs["sha256"],
                  "started": started.isoformat(), "previous_journal": prev, "reverts": None}
        journal = Journal(new_dir_name(set_dir, "", started), header)
        report["journal"] = journal.path
        try:
            run_apply_ops(ops, State(False), journal, report)
            journal.seal(len(ops))
        finally:
            journal.close()
        if a.verify_cmd:
            report["verify"]["after"] = run_verify(a.verify_cmd)
    finally:
        os.close(lock)


def cmd_revert(a, report):
    jpath = os.path.abspath(a.journal)
    j = load_journal(jpath)
    hdr = j["header"]
    sid = hdr.get("set_id")
    if hdr["kind"] != "apply" or not isinstance(sid, str) or not ID_RE.match(sid):
        raise Refuse("invalid_journal", "not a revertible apply journal")
    report["set_id"] = sid
    steps = []
    for i in sorted(set(j["intents"]) | set(j["outcomes"]), reverse=True):
        out, intent = j["outcomes"].get(i), j["intents"].get(i)
        if out is not None and out.get("outcome") != "applied":
            continue
        if intent is None or not isinstance(intent.get("path"), str):
            raise Refuse("invalid_journal", f"op {i}: intent missing")
        steps.append((i, intent, out is not None))
    check_roots([s[1]["path"] for s in steps], allowed_roots(a.allow_root))
    set_dir = os.path.join(a.journal_root, sid)
    lock = None if a.dry_run else acquire_lock(set_dir)
    try:
        check_order(set_dir, jpath, hdr)
        if a.verify_cmd and not a.dry_run:
            report["verify"]["before"] = run_verify(a.verify_cmd)
            if report["verify"]["before"] != 0:
                raise Refuse("verify_failed")
        state = State(a.dry_run)
        if a.dry_run:
            journal = NullJournal()
        else:
            started = now()
            header = {"type": "header", "schema": JOURNAL_SCHEMA, "kind": "revert",
                      "set_id": sid, "set_sha256": hdr.get("set_sha256"),
                      "started": started.isoformat(), "previous_journal": None,
                      "reverts": jpath}
            journal = Journal(new_dir_name(set_dir, "revert-", started), header)
            report["journal"] = journal.path
        try:
            for i, intent, has_outcome in steps:
                if not has_outcome and intent["op"] != "file_remove":
                    outcome, reason, plan = "unknown", "intent_without_outcome", None
                else:
                    outcome, reason, plan = evaluate_revert(intent, state, journal.dir, i)
                if plan is not None:
                    row = {"type": "intent", "index": i, "op": intent["op"],
                           "file": intent["file"], "action": "revert"}
                    outcome, reason = execute(plan, "reverted", "drift", row, state, journal, i)
                journal.outcome(i, outcome, reason)
                add_result(report, i, intent["op"], intent["file"], outcome, reason)
            journal.seal(len(steps))
        finally:
            journal.close()
        if a.verify_cmd and not a.dry_run:
            report["verify"]["after"] = run_verify(a.verify_cmd)
    finally:
        if lock is not None:
            os.close(lock)


def check_order(set_dir, jpath, hdr):
    applies, reverts = list_journals(set_dir)
    target = os.path.realpath(jpath)
    mykey = (hdr.get("started", ""), os.path.basename(os.path.dirname(jpath)))
    covered = set()
    for r in reverts:
        rv = r["header"].get("reverts")
        if r["sealed"] and isinstance(rv, str):
            covered.add(os.path.realpath(rv))
    for other in sorted(applies, key=journal_key):
        real = os.path.realpath(other["path"])
        if real == target or journal_key(other) <= mykey or real in covered:
            continue
        pending = any(o.get("outcome") == "applied" for o in other["outcomes"].values()) \
            or any(i not in other["outcomes"] for i in other["intents"])
        if pending:
            raise Refuse("newer_journal_not_reverted", other["path"])


def finish(report):
    counts = {}
    for r in report["results"]:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    report["counts"] = counts
    if report["refused"]:
        return 3
    bad = ("conflict", "drift", "unknown")
    return 2 if any(k in counts for k in bad) else 0


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def build_parser():
    p = Parser(prog="changeset.py")
    sub = p.add_subparsers(dest="command", required=True, parser_class=Parser)
    for name in ("apply", "revert", "status"):
        s = sub.add_parser(name)
        s.add_argument("--allow-root", action="append", default=[])
        if name == "revert":
            s.add_argument("--journal", required=True)
        else:
            s.add_argument("--set", required=True)
        if name != "status":
            s.add_argument("--journal-root", required=True)
            s.add_argument("--verify-cmd")
            s.add_argument("--dry-run", action="store_true")
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    report = new_report(argv[0] if argv else None, "--dry-run" in argv)
    try:
        a = build_parser().parse_args(argv)
        report["command"] = a.command
        report["dry_run"] = bool(getattr(a, "dry_run", False))
        if a.command == "apply":
            cmd_apply(a, report)
        elif a.command == "status":
            cmd_apply(a, report, status=True)
        else:
            cmd_revert(a, report)
        code = finish(report)
    except Refuse as e:
        report["refused"] = e.reason
        if e.detail:
            report["detail"] = e.detail
        code = finish(report)
    except BaseException as e:  # catch-all: always emit a report
        report["error"] = f"{type(e).__name__}: {e}"
        code = 1
        finish(report)
    sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
