"""Every document path the code pins resolves.

Manifests, registrations and freeze records name their preregistration,
decision packets and audits by repository path, and a signed record keeps that
path after the file has moved. So a tidy that moves a pinned document breaks a
citation that nothing else would notice; this makes the move fail here instead.

A pin is a document path that code uses or writes, in any of three forms: a
string literal holding the path, a path inside a longer string (a registration
writes "see user-notes/<file>.md"), or a path assembled from literals
(``REPO_ROOT / "user-notes" / "<file>.md"``, ``Path("a", "b")``,
``x.joinpath("a", "b")``). Docstrings are mentions, not pins, and are skipped;
comments never reach the parser. Every tracked non-test Python file is
scanned. Sources are parsed, never imported, so the closed packages need no
environment of their own. ``test_documentation_paths`` covers the paths v8's
prose cites.
"""
from __future__ import annotations

import ast
import functools
import re
import subprocess
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
_PREFIX = (r"(?:user-notes|docs|manuscript|exploratory|configs|reports"
           r"|dci1/docs|dci1/reports)")
_EXT = r"\.(?:md|json|csv|tsv|txt|toml)"
WHOLE = re.compile(rf"^{_PREFIX}/[\w./() -]+{_EXT}$")
INSIDE = re.compile(rf"(?<![\w/.-]){_PREFIX}/[\w./()-]+?{_EXT}(?![\w])")
NOT_SCANNED = re.compile(r"(^|/)tests?(_\w+)?/|(^|/)(test_[^/]*|conftest)\.py$"
                         r"|^(\.provenance|notebook_source)/")

#: Pinned in registered v6/v7 code and absent. dci1v6 and dci1v7 were derived
#: from dci1v5 with the revision renamed throughout, which moved these two
#: decision packets' paths along with it; the packets were only ever committed
#: under dci1/reports/dci1v5/ (6760c2b). The strings sit in closed studies'
#: registration code, which is not edited after the fact (RESEARCH_STATE.md §5).
#: Built from parts so that test_documentation_paths, which reads this file as
#: prose, does not take the four absent paths for citations of its own.
KNOWN_MISSING: frozenset[str] = frozenset(
    f"dci1/reports/dci1v{revision}/{packet}"
    for revision in (6, 7)
    for packet in ("d4_marker_audit.md", "u2_tier_model_decision.md"))

#: Read only if present, and never produced: tools/run_v4r3.py's Gate 5 runner
#: guards it with `.exists()`, and v4r3 closed at Gate 1 before Gate 5 could run.
#: Built from parts for the same reason as KNOWN_MISSING.
OPTIONAL_INPUTS: frozenset[str] = frozenset(
    {"/".join(("reports", "dci1v4r3", "gate1_measurement.json"))})


def _literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _assembled(node: ast.AST) -> str | None:
    """The literal path of ``root / "a" / "b"``, ``Path("a", "b")`` or
    ``x.joinpath("a", "b")``; None when any part after the root is computed."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts: list[str] = []
        while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            part = _literal(node.right)
            if part is None:
                return None
            parts.append(part)
            node = node.left
        head = _assembled(node) if isinstance(node, ast.Call) else _literal(node)
        if head is not None:
            parts.append(head)
        return "/".join(reversed(parts))
    if isinstance(node, ast.Call) and node.args:
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name in ("Path", "PurePath", "joinpath"):
            args = [_literal(a) for a in node.args]
            if all(a is not None for a in args):
                return "/".join(a for a in args if a is not None)
    return None


def _docstrings(tree: ast.AST) -> set[int]:
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and _literal(first.value) is not None:
                found.add(id(first.value))
    return found


def _pins_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    docstrings, inner, pins = _docstrings(tree), set(), set()
    for node in ast.walk(tree):
        if id(node) in inner:               # a sub-chain of a path already read
            continue
        if isinstance(node, ast.BinOp):
            left = node.left
            while isinstance(left, ast.BinOp):
                inner.add(id(left))
                left = left.left
        assembled = _assembled(node)
        if assembled and WHOLE.match(assembled):
            pins.add(assembled)
        text = _literal(node)
        if text is not None and id(node) not in docstrings:
            pins.update(INSIDE.findall(text))
    return pins


@functools.cache          # one scan of the tree serves every test here
def pinned_paths() -> dict[str, list[str]]:
    tracked = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO, check=True,
                             capture_output=True, text=True).stdout.split()
    found: dict[str, list[str]] = {}
    for rel in tracked:
        if NOT_SCANNED.search(rel):
            continue
        for pin in _pins_in(REPO / rel):
            found.setdefault(pin, []).append(rel)
    return found


def _exists(path: str, users: list[str]) -> bool:
    """Relative to the repository, to dci1/ for dci1 code, or to the citing
    file's own directory or its parent (``HERE / ...``, ``HERE.parent / ...``)."""
    bases = {REPO}
    for user in users:
        here = (REPO / user).parent
        bases |= {here, here.parent}
        if user.startswith("dci1/"):
            bases.add(DCI1)
    return any((base / path).exists() for base in bases)


def test_every_pinned_document_exists():
    missing = {p: u for p, u in pinned_paths().items()
               if not _exists(p, u) and p not in KNOWN_MISSING | OPTIONAL_INPUTS}
    assert not missing, (
        f"code pins documents that are not in this tree: {missing}. A signed "
        "record keeps the path; move the document back or record why it moved.")


def test_the_exemptions_are_exactly_what_is_missing():
    """Strict: a packet that reappears, or a path no longer pinned, must come
    off its list rather than leave an exemption nothing needs."""
    pinned = pinned_paths()
    exempt = KNOWN_MISSING | OPTIONAL_INPUTS
    still = {p for p in exempt if p in pinned and not _exists(p, pinned[p])}
    assert still == exempt, sorted(exempt - still)


def test_user_notes_readme_marks_exactly_the_pinned_files():
    """user-notes/README.md says which files must not move. That claim is this
    test's detection, not a hand-kept list."""
    readme = (REPO / "user-notes" / "README.md").read_text()
    marked = {m.group(1) for m in
              re.finditer(r"^\| `([^`]+)` \|[^\n]*\bpinned\b", readme, re.M)}
    detected = {p.removeprefix("user-notes/") for p in pinned_paths()
                if p.startswith("user-notes/")}
    assert marked == detected, {"marked, not pinned": sorted(marked - detected),
                                "pinned, not marked": sorted(detected - marked)}


def test_the_scanner_reads_every_form_of_pin(tmp_path):
    """Guard against the check silently matching nothing, form by form. The
    fixture uses manuscript/ and configs/, prefixes test_documentation_paths
    does not read as citations."""
    source = tmp_path / "pins.py"
    source.write_text(
        '"""A docstring mention: manuscript/mentioned.md"""\n'
        'A = "manuscript/literal.md"\n'
        'B = ROOT / "manuscript" / "assembled.md"\n'
        'C = Path("configs", "called.md")\n'
        'D = ROOT.joinpath("configs", "joined.md")\n'
        'E = "V1 to V9 remain open; see manuscript/inside.md"\n'
        'F = ROOT / name / "computed.md"\n')
    assert _pins_in(source) == {
        "manuscript/literal.md", "manuscript/assembled.md", "configs/called.md",
        "configs/joined.md", "manuscript/inside.md"}
    pinned = pinned_paths()                       # and in the real tree
    assert "user-notes/DCI1_preregistration_v7.md" in pinned
    assert "user-notes/DCI-1_preregistration_v2.md" in pinned
    assert "user-notes/DCI1_v4r2_unresolved_decisions.md" in pinned
    assert "dci1/docs/DCI1_preregistration_v8.1.md" in pinned
