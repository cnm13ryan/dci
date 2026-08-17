"""The v3 codebook (§28, item 59): one row per recorded variable with name,
type, permitted values or range, units, causal role, and definition.

Executable checks: every table column appears in the codebook and vice
versa; every value satisfies its declared type and domain; no post-treatment
field appears in a primary formula (§21); every execution-constraining field
is consumed by a named §27 check.
"""
from __future__ import annotations

from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C

ROLES = ("Identity", "Treatment", "Design", "Outcome", "Post-treatment",
         "Provenance")

#: name -> (type, domain, units, role, definition, consumed_by)
#: ``domain``: tuple of permitted values, "any", "non-negative", or a range.
#: ``consumed_by`` names the §27/engine check consuming an
#: execution-constraining field (None when not execution-constraining).
GENERATION_CODEBOOK: dict[str, tuple] = {
    "row_id": ("str", "any", None, "Identity",
               "The predetermined cached-draw identity cell_id:draw.",
               "cache_integrity"),
    "stage": ("str", "any", None, "Provenance",
              "The protocol stage that produced this row.",
              "stage_chain"),
    "artifact_state": ("str", C.ARTIFACT_STATES, None, "Provenance",
                       "Storage and acceptance status of this row.",
                       "artifact_states"),
    "model_key": ("str", "any", None, "Identity",
                  "The registered model replication slug.",
                  "model_replication_identity"),
    "model_id": ("str", "any", None, "Provenance",
                 "The canonical model repository.",
                 "model_replication_identity"),
    "model_revision": ("str", "any", None, "Provenance",
                       "The exact pinned repository revision.",
                       "model_replication_identity"),
    "cell_id": ("str", "any", None, "Identity",
                "The logical prompt cell this draw belongs to.",
                "cache_integrity"),
    "topic_id": ("str", "any", None, "Identity",
                 "The topic identity of the block or solo cell.", None),
    "block_id": ("str|null", "any", None, "Identity",
                 "The block identity for arm cells; null for solo cells.",
                 None),
    "arm": ("str|null", C.ARMS, None, "Treatment",
            "The condition assigned to this cell.", None),
    "kind": ("str", "any", None, "Design",
             "The cell kind (arm, solo, or composed).", None),
    "draw_index": ("int", range(0, C.M_DRAWS), None, "Identity",
                   "The predetermined cached-draw index within the cell.",
                   "cache_integrity"),
    "order": ("str|null", C.ORDERS, None, "Design",
              "The block's presentation order.", None),
    "target_wording": ("int|null", range(0, 4), None, "Design",
                       "The frozen wording index of the target constraint.",
                       None),
    "added_wording": ("int|null", range(0, 4), None, "Design",
                      "The frozen wording index of the added constraint.",
                      None),
    "n": ("int|null", C.TARGET_GRID, None, "Design",
          "The target severity active in this cell.", None),
    "constraint_id": ("str|null", ("B",) + C.FAMILY_IDS, None, "Treatment",
                      "The added or solo constraint identity.", None),
    "severity": ("int|null", "non-negative", None, "Design",
                 "The added or solo constraint severity.", None),
    "prompt_hash": ("str", "any", None, "Provenance",
                    "SHA-256 of the exact prompt bytes.",
                    "cache_integrity"),
    "backend_version": ("str", "any", None, "Provenance",
                        "The inference backend version that generated the "
                        "row.", None),
    "interpreter": ("str|null", "any", None, "Provenance",
                    "The scientific interpreter executable.",
                    "dependency_and_interpreter"),
    "dependency_digest": ("str|null", "any", None, "Provenance",
                          "The uv dependency digest active at generation.",
                          "dependency_and_interpreter"),
    "hardware_class": ("str", "any", None, "Provenance",
                       "The GPU class that produced the row.",
                       "hardware_class"),
    "seed": ("int", "non-negative", None, "Design",
             "The frozen per-draw generation seed.", "cache_integrity"),
    "raw_response": ("str", "any", None, "Outcome",
                     "The complete raw response text, write-once.", None),
    "response_content_hash": ("str", "any", None, "Provenance",
                              "SHA-256 of the raw response, recorded at "
                              "write time.", "cache_integrity"),
    "prompt_tokens": ("int", "non-negative", "tokens", "Post-treatment",
                      "Prompt length observed at generation.", None),
    "token_count": ("int", "non-negative", "tokens", "Post-treatment",
                    "Generated token count.", None),
    "finish_reason": ("str", "any", None, "Post-treatment",
                      "Why generation stopped.", None),
    "verdicts": ("dict", "any", None, "Outcome",
                 "Every verifier verdict with the frozen instrument hash.",
                 "cache_integrity"),
    "record_hash": ("str", "any", None, "Provenance",
                    "SHA-256 over the row body.", "cache_integrity"),
}

#: Fields named in a primary formula (§21): none may be Post-treatment.
PRIMARY_FORMULA_FIELDS = ("block_id", "arm", "order", "verdicts")


def validate_codebook() -> dict[str, Any]:
    for name, row in GENERATION_CODEBOOK.items():
        if len(row) != 6:
            raise ProtocolError(f"codebook row {name} malformed")
        if row[3] not in ROLES:
            raise ProtocolError(f"codebook row {name}: unknown role "
                                f"{row[3]!r}")
    for field in PRIMARY_FORMULA_FIELDS:
        role = GENERATION_CODEBOOK[field][3]
        if role == "Post-treatment":
            raise ProtocolError(
                f"primary formula names post-treatment field {field!r}")
    from dci1v3.engine.verify import NAMED_CHECKS
    for name, row in GENERATION_CODEBOOK.items():
        consumer = row[5]
        if consumer is not None and consumer not in NAMED_CHECKS:
            raise ProtocolError(
                f"{name}: declared execution-constraining but its consumer "
                f"{consumer!r} is not a named check")
    return {"rows": len(GENERATION_CODEBOOK), "valid": True}


def _value_ok(value: Any, kind: str, domain: Any) -> bool:
    if value is None:
        return "null" in kind
    base = kind.replace("|null", "")
    types = {"str": str, "int": int, "dict": dict}
    if base == "int" and isinstance(value, bool):
        return False
    if not isinstance(value, types[base]):
        return False
    if domain == "any":
        return True
    if domain == "non-negative":
        return value >= 0
    return value in domain


def validate_row(row: dict[str, Any]) -> None:
    """Every column in the codebook and every value in its domain."""
    unknown = set(row) - set(GENERATION_CODEBOOK)
    if unknown:
        raise ProtocolError(f"columns outside the codebook: "
                            f"{sorted(unknown)}")
    missing = set(GENERATION_CODEBOOK) - set(row)
    if missing:
        raise ProtocolError(f"codebook columns missing from row: "
                            f"{sorted(missing)}")
    for name, (kind, domain, _units, _role, _defn, _consumer) in \
            GENERATION_CODEBOOK.items():
        if not _value_ok(row[name], kind, domain):
            raise ProtocolError(
                f"{row.get('row_id')}: field {name}={row[name]!r} outside "
                f"its declared type or domain")
