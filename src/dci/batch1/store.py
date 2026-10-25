"""Run-root storage: strict JSON lines, canonical record hashes, the
duplicate-row policy, the run lock, and documentation-insensitive code hashes.

**Strict reads.** A line that does not parse is an error, never skipped.
The one exception is the last line of a file a crashed writer left
unterminated: ``repair_partial_tail`` removes it (an interrupted append
carries no complete record) and returns what it removed, for provenance.

**Duplicates.** ``index_rows`` maps row id to record. An exact repeat of a
record (byte-identical canonical form) collapses to one and is counted, so
an identical retry can never count twice; two different records under one
row id are a conflict and raise.

**Lock.** ``run_lock`` takes an exclusive, non-blocking ``flock`` on
``RUN.lock`` for the duration of a generation or scoring step, so two
processes cannot append to the same root. The kernel releases it when the
process dies, so a crash never leaves a stale lock.

**Code hashes.** ``code_hash`` hashes a module's token stream with its
comments, docstrings, blank lines and layout removed (``canonical_tokens``):
a documentation or formatting edit leaves the hash, and every approval bound
to it, intact; any change to code or to a string constant changes it.

It is the same under every Python minor version (re-audit R2). The previous
hash, of ``ast.dump``, was not: 3.12 added ``type_params`` to the dump and
3.13 omits empty fields, so one file hashed three ways. Token names and
strings are stable across 3.11-3.13 once the one tokenizer change that
matters here is undone: from 3.12 an f-string arrives as FSTRING_START /
MIDDLE / END pieces, which are merged back into the single STRING token
3.11 produces, taken verbatim from the source. ``ast`` is used only to
locate docstrings (their positions are version-stable).
"""
from __future__ import annotations

import ast
import fcntl
import hashlib
import io
import json
import os
import tokenize
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

__all__ = ["RunError", "canonical", "record_hash", "read_jsonl",
           "repair_partial_tail", "write_jsonl", "append_jsonl", "index_rows",
           "run_lock", "SOURCE_HASH_SCHEME", "canonical_tokens", "code_hash",
           "tree_hash"]


class RunError(RuntimeError):
    """A run root, row set or step that cannot be trusted."""


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def record_hash(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    data = path.read_text(encoding="utf-8")
    for i, line in enumerate(data.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as error:
            raise RunError(f"{path}:{i}: unreadable record ({error}); a "
                           "partial final line is repaired by "
                           "repair_partial_tail, anything else is refused"
                           ) from None
    return rows


def repair_partial_tail(path: Path) -> dict[str, Any] | None:
    """Drop an unterminated, unparsable final line; return what was dropped."""
    path = Path(path)
    if not path.exists():
        return None
    data = path.read_bytes()
    if not data or data.endswith(b"\n"):
        return None
    cut = data.rfind(b"\n") + 1
    tail = data[cut:]
    try:
        json.loads(tail)
        return None                 # complete record; append adds the newline
    except ValueError:
        pass
    with path.open("r+b") as fh:
        fh.truncate(cut)
    return {"file": path.name, "dropped_bytes": len(tail),
            "dropped_sha256": hashlib.sha256(tail).hexdigest()}


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                   encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    if not text:
        return 0
    with path.open("ab") as fh:
        if fh.tell() and not _ends_with_newline(path):
            fh.write(b"\n")
        fh.write(text.encode("utf-8"))
        fh.flush()
        os.fsync(fh.fileno())
    return text.count("\n")


def _ends_with_newline(path: Path) -> bool:
    with path.open("rb") as fh:
        fh.seek(-1, os.SEEK_END)
        return fh.read(1) == b"\n"


def index_rows(rows: Iterable[Mapping[str, Any]], *, what: str
               ) -> tuple[dict[str, dict[str, Any]], int]:
    """Row id -> record, and the number of exact repeats collapsed."""
    out: dict[str, dict[str, Any]] = {}
    repeats = 0
    for r in rows:
        rid = r.get("row_id")
        if not isinstance(rid, str) or not rid:
            raise RunError(f"{what}: a record without a row id")
        if rid in out:
            if canonical(out[rid]) != canonical(r):
                raise RunError(f"{what}: two different records for {rid}; "
                               "a conflicting duplicate is never resolved "
                               "automatically")
            repeats += 1
            continue
        out[rid] = dict(r)
    return out, repeats


@contextmanager
def run_lock(root: Path) -> Iterator[None]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    fh = (root / "RUN.lock").open("a+")
    try:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RunError(f"{root} is in use by another process (RUN.lock); "
                           "concurrent runs on one root are refused") from None
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


SOURCE_HASH_SCHEME = "dci.batch1/source-tokens/v1"
_DROP = {"COMMENT", "NL", "ENCODING", "ENDMARKER"}
_LAYOUT = {"NEWLINE", "INDENT", "DEDENT"}


def _docstring_spans(text: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """(start, end) of every module, class and function docstring, as
    tokenize positions (row, character column)."""
    lines = io.StringIO(text).readlines()

    def char_col(row: int, byte_col: int) -> int:
        return len(lines[row - 1].encode("utf-8")[:byte_col].decode("utf-8"))

    spans = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                e = body[0]
                spans.append(((e.lineno, char_col(e.lineno, e.col_offset)),
                              (e.end_lineno, char_col(e.end_lineno,
                                                      e.end_col_offset))))
    return spans


def canonical_tokens(text: str) -> list[tuple[str, str]]:
    """The code of a module as (token name, string) pairs: no comments,
    docstrings, blank lines or layout, f-strings whole."""
    spans = _docstring_spans(text)
    offsets = [0]
    for line in io.StringIO(text).readlines():
        offsets.append(offsets[-1] + len(line))
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    out: list[tuple[str, str]] = []
    drop_newline = False
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        name = tokenize.tok_name[tok.type]
        string, start = tok.string, tok.start
        if name == "FSTRING_START":           # Python >= 3.12
            depth, j = 0, i
            while True:
                kind = tokenize.tok_name[tokens[j].type]
                depth += (kind == "FSTRING_START") - (kind == "FSTRING_END")
                if depth == 0:
                    break
                j += 1
            (r0, c0), (r1, c1) = tok.start, tokens[j].end
            string = text[offsets[r0 - 1] + c0:offsets[r1 - 1] + c1]
            name, i = "STRING", j
        i += 1
        if name in _DROP:
            continue
        if any(a <= start < b for a, b in spans):
            drop_newline = True
            continue
        if drop_newline and name == "NEWLINE":
            drop_newline = False
            continue
        drop_newline = False
        out.append((name, "" if name in _LAYOUT else string))
    return out


def code_hash(path: Path) -> str:
    """The module's code, independent of comments, docstrings, layout and
    the Python version computing it."""
    tokens = canonical_tokens(Path(path).read_text(encoding="utf-8"))
    return hashlib.sha256(json.dumps([SOURCE_HASH_SCHEME, tokens],
                                     ensure_ascii=False).encode("utf-8")
                          ).hexdigest()


def tree_hash(directory: Path, pattern: str = "*.py") -> dict[str, Any]:
    """Code hashes of every matching file under ``directory``, and their hash."""
    directory = Path(directory)
    files = {p.relative_to(directory).as_posix(): code_hash(p)
             for p in sorted(directory.rglob(pattern))
             if "__pycache__" not in p.parts}
    return {"files": files, "hash": record_hash(files)}
