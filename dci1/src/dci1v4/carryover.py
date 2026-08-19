"""Executable carry-over record against the v3 instrument artifacts (§10.2).

The v4r2 carry-over rule: A's instrument may supply carried evidence only
when the construct string, the segmentation function source, and the
counting function sources are byte-identical to the v3 artifacts; the
record names the source, records every hash, and refuses on any mismatch.

The closed v3 sources are read here as *artifacts* — file bytes parsed for
comparison, never imported and never modified — which keeps the §26
namespace isolation intact. Entries with role ``compatibility`` extend the
same byte-identity evidence to the word-length and family statistics; they
are not required by the carry-over rule but guarantee that the v4 boolean
passes coincide with the frozen v3 verdicts wherever the grids overlap.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from dci1v4.errors import CarryOverMismatch

#: (v4 module, v3 module, symbol, role). Symbols are function definitions,
#: except TARGET_WORD — the construct string, compared as an assignment.
CARRIED: tuple[tuple[str, str, str, str], ...] = (
    ("words.py", "words.py", "alpha_runs", "carry_over"),
    ("words.py", "words.py", "words_lower", "carry_over"),
    ("target.py", "target.py", "TARGET_WORD", "carry_over"),
    ("target.py", "target.py", "s0_count", "carry_over"),
    ("target.py", "target.py", "s1_count", "carry_over"),
    ("target.py", "target.py", "s2_count", "carry_over"),
    ("target.py", "target.py", "s3_preprocess", "carry_over"),
    ("target.py", "target.py", "s3_count", "carry_over"),
    ("statistics.py", "families.py", "focal_statistic", "compatibility"),
    ("statistics.py", "families.py", "_rf1", "compatibility"),
    ("statistics.py", "families.py", "_rf2", "compatibility"),
    ("statistics.py", "families.py", "_rf3", "compatibility"),
    ("statistics.py", "families.py", "_rf4", "compatibility"),
    ("statistics.py", "families.py", "_rf5", "compatibility"),
    ("statistics.py", "families.py", "_rf6", "compatibility"),
    ("statistics.py", "families.py", "_rf7", "compatibility"),
    ("statistics.py", "families.py", "_rf8", "compatibility"),
)

_V4_DIR = Path(__file__).resolve().parent
_DEFAULT_V3_VERIFIERS = _V4_DIR.parent / "dci1v3" / "verifiers"


def _symbol_source(path: Path, name: str) -> str:
    source = path.read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name
                for t in node.targets):
            return ast.get_source_segment(source, node)
    raise CarryOverMismatch(f"{name} not found in {path}")


def carry_over_record(v3_verifiers: Path | None = None) -> dict:
    """Compare every carried symbol byte-for-byte; refuse on any mismatch."""
    source_dir = Path(v3_verifiers) if v3_verifiers is not None \
        else _DEFAULT_V3_VERIFIERS
    entries: list[dict] = []
    mismatches: list[str] = []
    for v4_module, v3_module, symbol, role in CARRIED:
        v4_src = _symbol_source(_V4_DIR / v4_module, symbol)
        v3_src = _symbol_source(source_dir / v3_module, symbol)
        identical = v4_src == v3_src
        entries.append({
            "module": v4_module,
            "v3_module": v3_module,
            "function": symbol,
            "role": role,
            "v3_sha256": hashlib.sha256(v3_src.encode()).hexdigest(),
            "v4_sha256": hashlib.sha256(v4_src.encode()).hexdigest(),
            "identical": identical,
        })
        if not identical:
            mismatches.append(f"{v4_module}:{symbol}")
    if mismatches:
        raise CarryOverMismatch(
            "carried sources differ from the v3 artifacts: "
            + ", ".join(mismatches))
    return {"v3_source": str(source_dir), "entries": entries}
