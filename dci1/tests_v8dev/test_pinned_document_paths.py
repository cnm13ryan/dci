"""Every document path a registered revision pins in code resolves.

Manifests, registrations and freeze records name their preregistration,
decision packets and audits by repository path, and a signed record keeps that
path after the file has moved. So a tidy that moves a pinned document breaks a
citation that nothing else would notice; this makes the move fail here instead.

Scope is code, not prose: every string literal in ``src/dci``, ``dci1/src`` and
``dci1/tools`` that is a whole repository path to a document. The sources are
parsed, never imported, so the v2-v7 packages need no environment of their
own. ``test_documentation_paths`` covers the paths v8's prose cites.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
SCANNED = ("src/dci", "dci1/src", "dci1/tools")
DOCUMENT = re.compile(r"^(?:user-notes|docs|manuscript|exploratory|configs|reports"
                      r"|dci1/docs|dci1/reports)/[\w./() -]+\.(?:md|json|csv|tsv|txt|toml)$")

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


def pinned_paths(roots=SCANNED) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for root in roots:
        for py in sorted((REPO / root).rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            for node in ast.walk(ast.parse(py.read_text())):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and DOCUMENT.match(node.value)):
                    found.setdefault(node.value, []).append(str(py.relative_to(REPO)))
    return found


def _exists(path: str, users: list[str]) -> bool:
    """Repository-relative, or dci1-relative when only dci1 code names it."""
    bases = [REPO] + ([DCI1] if any(u.startswith("dci1/") for u in users) else [])
    return any((base / path).exists() for base in bases)


def test_every_pinned_document_exists():
    missing = {p: u for p, u in pinned_paths().items()
               if not _exists(p, u) and p not in KNOWN_MISSING}
    assert not missing, (
        f"code pins documents that are not in this tree: {missing}. A signed "
        "record keeps the path; move the document back or record why it moved.")


def test_the_known_missing_set_is_exactly_what_is_missing():
    """Strict: a packet that reappears, or one that stops being pinned, must
    come off the list rather than leave an exemption nothing needs."""
    pinned = pinned_paths()
    still = {p for p in KNOWN_MISSING if p in pinned and not _exists(p, pinned[p])}
    assert still == KNOWN_MISSING, sorted(KNOWN_MISSING - still)


def test_the_scanner_finds_the_pins_that_matter():
    """Guard against the check silently matching nothing."""
    pinned = pinned_paths()
    assert "user-notes/DCI1_preregistration_v7.md" in pinned
    assert "dci1/docs/DCI1_preregistration_v8.1.md" in pinned
    assert len(pinned) > 50
