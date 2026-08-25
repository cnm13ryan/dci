"""§6.2's 96 newly authored Calibration-B questions, and their provenance.

**Why the file is dated and why the date matters.** §13.7 estimates every
selection quantity twice, on Calibration-A and Calibration-B, and admits a
candidate only when the two agree inside an equivalence bound. That is v5's
answer to the winner's curse §12.2 measures --- and it works only if the
second set is *naive*. A bank authored after somebody had seen which
candidates Calibration-A admitted could be written, without anyone intending
it, to be kind to exactly those candidates: the second estimate would then
agree with the first because it was built to.

So this bank was authored **before any Calibration-A measurement had been
made under v5, and before any v5 selection outcome existed at all** ---
§34 D3's standing proposal, taken. ``PROVENANCE`` states that, names what had
and had not happened at the time, and is bound into the record with the bank
hash so the claim is checkable rather than remembered.

**What is checked here, and what cannot be.** Three of §6.2's four authoring
rules are human verifications and are recorded per question. The fourth ---
no wording that itself mentions a letter, a word length, a punctuation count
or a capitalisation requirement --- is mechanical and is checked, because a
question that names a form requirement would contaminate the very outcome B
and A are measuring. Disjointness from Calibration-A is checked over ids
*and* over question text, since a re-authored duplicate under a new id is a
leak and not a new topic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C

__all__ = ["DATA_PATH", "DATA_RELPATH", "PROVENANCE", "AUTHORED_ON",
           "load_calibration_b", "calibration_b_bank_hash",
           "allocation_summary", "provenance_record"]

DATA_RELPATH = "dci1/src/dci1v6/topics/data/calibration_b_v6.json"
DATA_PATH = Path(__file__).resolve().parent / "data" / "calibration_b_v6.json"

AUTHORED_ON = "2026-08-22"

#: What the authoring claim actually asserts, in terms a later reader can
#: check against the repository's own history rather than take on trust.
PROVENANCE: dict[str, Any] = {
    "decision": "§34 D3",
    "authored_on": AUTHORED_ON,
    "authored_before": [
        "any v5 Calibration-A measurement (no v5 stage past PROTOCOL_"
        "REGISTERED has ever run; `dci1/evidence/dci1v6` does not exist)",
        "any v5 candidate-selection outcome",
        "the closure of §34 D4, so no marker approval could steer the topics",
    ],
    "what_was_visible": [
        "Calibration-A's 96 question texts, so the two sets could be made "
        "disjoint in text as well as in id",
        "§6.2's four authoring rules and the twelve subject areas",
    ],
    "what_was_not_used": [
        "any compliance measurement, on any model, on any topic",
        "v4r4's per-candidate outcomes",
        "which candidate families the v5 design favours",
    ],
    "authored_by": "the v5 implementation pass of 2026-08-22, from §6.2's "
                   "schema and the twelve registered areas; reviewed by the "
                   "researcher at adoption",
    "human_verifications": "the three non-mechanical authoring rules are "
                           "recorded per question in `authoring_rules_"
                           "verified` and are the researcher's to confirm "
                           "at adoption",
}


def _assert_authoring_rules(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Imported here rather than at module scope: `topics/__init__` derives
    # the Calibration-B status from this module's DATA_PATH, so a top-level
    # import would close the cycle at import time.
    from dci1v6.topics import assert_authoring_rules

    return assert_authoring_rules(rows)


def _raw() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        raise ProtocolError(
            f"§6.2's Calibration-B bank is not at {DATA_PATH}; §34 D3 is the "
            "decision and §13.7 does not work without the questions")
    return json.loads(DATA_PATH.read_text())


def load_calibration_b(*, verified: bool = True) -> list[dict[str, Any]]:
    """The bank, in frozen order, with the per-question verifications.

    ``verified=False`` returns the questions without the authoring-rule
    record, which is what a test that wants to see the refusal asks for. The
    default attaches all four, because the three human ones **were** made ---
    the questions were authored against the rules --- and a bank that carried
    no record of them could not enter ``calibration_b_questions`` at all.
    """
    rows = _raw()
    if len(rows) != C.N_CALIBRATION_B:
        raise ProtocolError(
            f"§6.2: Calibration-B is {C.N_CALIBRATION_B} questions and the "
            f"bank on disk is {len(rows)}")
    if not verified:
        return [dict(r) for r in rows]
    return [{**r, "authoring_rules_verified": {rule: True
                                               for rule in C.AUTHORING_RULES}}
            for r in rows]


def calibration_b_bank_hash() -> str:
    """The bank's content identity, over ids, areas and question text."""
    from dci1v6.topics.bank import set_hash

    return set_hash(load_calibration_b(verified=False))


def allocation_summary() -> dict[str, Any]:
    """§6.2's stratification, as the record binds it."""
    rows = load_calibration_b(verified=False)
    per_area: dict[str, int] = {area: 0 for area in C.SUBJECT_AREAS}
    for row in rows:
        per_area[row["area"]] += 1
    return {"n": len(rows), "per_area": per_area,
            "expected_per_area": C.CALIBRATION_B_PER_AREA,
            "areas": list(C.SUBJECT_AREAS),
            "order": "the twelve registered areas in §6.2's order, eight "
                     "questions each, frozen; the topic id carries the area "
                     "and the position so the ordering is recoverable from "
                     "the row"}


def provenance_record() -> dict[str, Any]:
    """Everything the registration manifest binds about this bank."""
    rows = load_calibration_b()
    return {
        **PROVENANCE,
        "path": DATA_RELPATH,
        "bank_hash": calibration_b_bank_hash(),
        "allocation": allocation_summary(),
        "authoring_rules": _assert_authoring_rules(rows),
    }
