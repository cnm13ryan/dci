"""Executable carry-over record against the v3 instrument artifacts (§10.2).

The v4r2 carry-over rule, in full: A's instrument may supply carried evidence
only when the construct string, the word-segmentation function source, the
counting function source, **and the forty boundary case texts with their
expectations** are byte-identical to the v3 artifacts. The record names the
source, records every hash, and refuses on any mismatch; on refusal the
exact-count instrument needs new v4 measurement evidence and carries none.

The closed v3 sources are read here as *artifacts* — file bytes parsed for
comparison, never imported, never executed and never modified — which is what
keeps the §26 namespace isolation intact while the comparison happens. The v4
copies in this package are the operative implementation; the v3 files are read
as data exactly once, here, and never at runtime.

Entries with role ``compatibility`` extend the same byte-identity evidence to
the word-length and family statistics. The carry-over rule does not require
them — under §10.2 those instruments are authored for v4 — but the identity
guarantees that a v4 boolean pass coincides with the frozen v3 verdict
wherever the two grids overlap, which is what lets check C6 read v3 solo cells
as an anchor without re-scoring them under a different rule.
""" 
from __future__ import annotations

import ast
import hashlib
import json
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
_DEFAULT_V3_VERIFIERS = _V4_DIR.parents[1] / "dci1v3" / "verifiers"


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


def _v3_boundary_cases(path: Path) -> list[dict]:
    """The v3 forty, read as data: parse the module, take the literal
    arguments of every ``_case(...)`` call in ``BOUNDARY_CASES``.

    Nothing is imported and nothing is executed; ``ast.literal_eval`` reads
    only literals, so a v3 file that had been altered to do work could not do
    it here.
    """
    source = path.read_text()
    for node in ast.walk(ast.parse(source)):
        target_is_cases = (
            isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
            and node.target.id == "BOUNDARY_CASES")
        if isinstance(node, ast.Assign):
            target_is_cases = any(isinstance(t, ast.Name)
                                  and t.id == "BOUNDARY_CASES"
                                  for t in node.targets)
        if not target_is_cases:
            continue
        cases = []
        for call in node.value.elts:
            args = [ast.literal_eval(a) for a in call.args]
            cases.append({"case_id": args[0], "text": args[1], "s0": args[2],
                          "s1": args[3], "s2": args[4]})
        return cases
    raise CarryOverMismatch(f"BOUNDARY_CASES not found in {path}")


def boundary_carry_over(v3_boundary: Path | None = None) -> dict:
    """§10.2: the forty case texts and their expectations, byte-identical."""
    from dci1v4.verifiers.boundary import (
        CARRIED_CASES,
        carried_specification,
        carried_specification_hash,
    )

    path = (Path(v3_boundary) if v3_boundary is not None
            else _DEFAULT_V3_VERIFIERS / "boundary.py")
    v3_cases = _v3_boundary_cases(path)
    v4_cases = [{"case_id": c["case_id"], "text": c["text"], "s0": c["s0"],
                 "s1": c["s1"], "s2": c["s2"]} for c in CARRIED_CASES]
    if len(v3_cases) != 40:
        raise CarryOverMismatch(
            f"{path} carries {len(v3_cases)} boundary cases, not forty")
    differing = [a["case_id"] for a, b in zip(v4_cases, v3_cases) if a != b]
    if differing or len(v4_cases) != len(v3_cases):
        raise CarryOverMismatch(
            f"carried boundary cases differ from the v3 artifact: "
            f"{differing[:5]}")
    v3_hash = hashlib.sha256(
        json.dumps(v3_cases, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode()).hexdigest()
    v4_hash = carried_specification_hash()
    if v3_hash != v4_hash:
        raise CarryOverMismatch("carried boundary specification hash differs "
                                f"from the v3 artifact ({v3_hash} != {v4_hash})")
    return {"v3_source": str(path), "cases": len(v4_cases),
            "v3_sha256": v3_hash, "v4_sha256": v4_hash,
            "specification_bytes": len(carried_specification())}


def carry_over_record(v3_verifiers: Path | None = None) -> dict:
    """Compare every carried symbol and the forty boundary cases byte-for-
    byte; refuse on any mismatch (§10.2)."""
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
    boundary = boundary_carry_over(source_dir / "boundary.py")
    record = {
        "rule": "DCI1_preregistration_v4r2.md §10.2",
        "v3_source": str(source_dir),
        "construct_string": "however",
        "entries": entries,
        "boundary": boundary,
        "provenance": ("the v3 files are read as data for this comparison "
                       "and are never imported, executed or modified"),
    }
    record["record_hash"] = hashlib.sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode()).hexdigest()
    return record
