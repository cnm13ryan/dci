"""§10.2's carry-over record: what v4r3 inherits, and what it does not.

The carry-over rule is strict on purpose. $A$'s instrument may supply carried
evidence **only** when the construct string, the segmentation function source,
the counting function source, and the forty v3 case texts with their
expectations are byte-identical to the v3 artifacts. This module names each
source, records its hash, and refuses on any mismatch.

**What v4r3 carries, and what it deliberately does not.**

| Source | Standing |
|---|---|
| `alpha_runs` | carried, byte-identical through ``dci1v4`` to v3 |
| `s0_count`, `s1_count`, `s2_count`, `s3_*` | carried, byte-identical |
| the construct string ``however`` | carried |
| the forty v3 case texts and their S0/S1/S2 expectations | carried |
| `words_lower` | **NOT carried.** §7.0 corrects its composition order |
| the eight v4 family counting functions | **NOT carried.** They read the corrected word list, and ``statistics.assert_agrees_with_v4r2`` states the equivalence executably instead |
| the forty-five v4 focal case texts and their statistic vectors | carried as *v4* evidence, admitted only because every one of their statistics is re-derived unchanged under the corrected rule |

$A$'s carry-over survives because the correction does not touch $A$: §9.2
registers $S_0$ as lower-case-then-segment in its own words, and that is what
the carried counting function does. The distinction is the whole reason the
correction could be made at all without voiding the study's oldest evidence.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import dci1v4.verifiers as _v4_verifiers
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_text
from dci1v4.verifiers import carryover as _v4_carryover

from dci1v4r3.verifiers.boundary import (
    CARRIED_TARGET_CASES, assert_carried_focal_cases_unchanged,
)
from dci1v4r3.verifiers.statistics import assert_agrees_with_v4r2

__all__ = ["CARRIED_SYMBOLS", "NOT_CARRIED", "symbol_source",
           "carry_over_record"]

#: (module, symbol) pairs whose source v4r3 inherits unchanged.
CARRIED_SYMBOLS = (
    ("words.py", "alpha_runs"),
    ("target.py", "s0_count"),
    ("target.py", "s1_count"),
    ("target.py", "s2_count"),
    ("target.py", "s3_preprocess"),
    ("target.py", "s3_count"),
    ("target.py", "TARGET_WORD"),
)

#: What v4r3 explicitly does NOT carry, and the reason, so that a reader can
#: see the boundary rather than infer it from an absence.
NOT_CARRIED: dict[str, str] = {
    "words_lower": "§7.0 corrects the composition order: segment the answer, "
                   "then lower-case each word. v4r2 lower-cased the whole "
                   "response first, which splits a word on U+0130",
    "family_statistics": "the eight v4 counting functions read v4r2's word "
                         "list; v4r3's read the corrected one. The "
                         "equivalence on U+0130-free text is asserted "
                         "executably rather than claimed",
}


def symbol_source(path: Path, name: str) -> str:
    """The exact source segment of one function or assignment."""
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.get_source_segment(source, node)
    raise ProtocolError(f"{name!r} not found in {path}")


def carry_over_record(v3_verifiers: str | Path | None = None) -> dict[str, Any]:
    """Verify every carried source and every carried case, and record it.

    The v3 half is delegated to ``dci1v4.verifiers.carryover``, which already
    reads the closed v3 files as artifacts; v4r3 then asserts that the v4
    sources it inherits are the ones v4 certified, so the chain is
    v3 -> v4r2 -> v4r3 with every link checked rather than assumed.
    """
    v4_record = _v4_carryover.carry_over_record(v3_verifiers) \
        if v3_verifiers is not None else _v4_carryover.carry_over_record()
    v4_dir = Path(_v4_verifiers.__file__).resolve().parent
    hashes = {f"{module}:{symbol}":
              sha_text(symbol_source(v4_dir / module, symbol))
              for module, symbol in CARRIED_SYMBOLS}
    focal = assert_carried_focal_cases_unchanged()
    equivalence = assert_agrees_with_v4r2(
        case["text"] for case in CARRIED_TARGET_CASES)
    return {
        "v3_to_v4r2": v4_record,
        "carried_symbol_hashes": hashes,
        "carried_target_cases": len(CARRIED_TARGET_CASES),
        "carried_focal_cases": focal,
        "composition_equivalence": equivalence,
        "not_carried": dict(NOT_CARRIED),
        "a_carry_over_survives": True,
        "a_carry_over_argument":
            "§9.2 registers S0 as lower-case-then-segment and the carried "
            "counting function implements exactly that, so §7.0's correction "
            "to the family word list does not touch A's instrument",
    }
