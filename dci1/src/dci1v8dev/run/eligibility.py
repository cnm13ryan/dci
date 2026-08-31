"""The LOCAL frame-eligibility rule (researcher decision of 2026-08-31).

Two statements, both read off pre-freeze reference-survival records:

* **A frame is `LOCAL_SUPPORTED`** iff it satisfies the *full* registered
  LOCAL reference-survival requirements --- an operating point at Gate 2,
  §13.8's three core references, §13.15's ``MIN_LOCAL_FAMILIES`` LOCAL-valid
  families and ``MIN_BACKUPS`` admissible backups --- on its own table at its
  own ι_A(f). Otherwise `LOCAL_UNSUPPORTED`, with every requirement it missed
  named. Nothing rescues an unsupported frame.
* **A model is `LOCAL_ELIGIBLE`** iff at least
  ``rules.LOCAL_ELIGIBILITY_MIN_FRAMES`` of its frames are independently
  LOCAL-supported. For an eligible model **every** supported frame enters the
  LOCAL confirmatory design --- there is no "best two" and no ranking.

**Why this is not the frame state.** ``FRAME_STATES``'s ``LOCAL_AND_SPECTRUM``
says only that the three core references were identified and the spectrum
coverage gate passed. It is deliberately broader than survival: a frame can
reach it on four LOCAL-valid families and one backup, which is §13.15
unsatisfied and one admissible substitute short of the two §13.15 wants
against a reference failing at freeze. Support is the survival requirement,
not the state, and ``local_supported`` is therefore computed from the
survival block and never from ``state``.

**What it may not read.** Δ_R(f), δ_diff, any composed cell, any pooled
statistic over frames, and any quantity of another frame. The inputs are one
frame's own ``survival`` summary and Gate 2's own support status for that
frame; a frame's verdict is a function of that frame alone, so no ordering,
ranking or cross-frame comparison can enter. Choosing frames on an outcome
would be selecting on the quantity the study exists to estimate.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v8dev import rules as R
from dci1v8dev.run import stages as S

__all__ = ["LOCAL_SUPPORTED", "LOCAL_UNSUPPORTED", "LOCAL_SUPPORT_STATES",
           "LOCAL_UNSUPPORTED_REASONS", "local_support",
           "local_eligibility", "LOCAL_ELIGIBILITY_RULE"]

LOCAL_SUPPORTED = "LOCAL_SUPPORTED"
LOCAL_UNSUPPORTED = "LOCAL_UNSUPPORTED"
LOCAL_SUPPORT_STATES = (LOCAL_SUPPORTED, LOCAL_UNSUPPORTED)

#: Every way a frame can miss the LOCAL requirement, in the order they are
#: reported. The order is the order of the §13.15 pipeline --- a frame needs
#: an operating point before it can have a core, a core before the family
#: count means anything, and backups are substitutes for an identified core
#: --- so the *first* reason is the earliest step that failed. It decides
#: which reason is quoted, never which frames pass: every unmet requirement
#: is on the record in ``local_unsupported_reasons``.
NO_OPERATING_POINT = "NO_OPERATING_POINT"
CORE_NOT_IDENTIFIED = "CORE_NOT_IDENTIFIED"
LOCAL_FAMILIES_BELOW_MINIMUM = "LOCAL_FAMILIES_BELOW_MINIMUM"
BACKUPS_BELOW_MINIMUM = "BACKUPS_BELOW_MINIMUM"
LOCAL_UNSUPPORTED_REASONS = (NO_OPERATING_POINT, CORE_NOT_IDENTIFIED,
                             LOCAL_FAMILIES_BELOW_MINIMUM,
                             BACKUPS_BELOW_MINIMUM)

LOCAL_ELIGIBILITY_RULE = (
    "a frame is LOCAL_SUPPORTED iff §13.8 identifies its three core "
    f"references, §13.15 counts >= {S.MIN_LOCAL_FAMILIES} LOCAL-valid "
    f"families and >= {S.MIN_BACKUPS} admissible backups on that frame's own "
    "table at its own iota_A(f); a model is LOCAL_ELIGIBLE iff >= "
    f"{R.LOCAL_ELIGIBILITY_MIN_FRAMES} frames are independently "
    "LOCAL_SUPPORTED, and every supported frame of an eligible model enters "
    "(no best-two selection, no cross-frame pooling, no outcome read)")

#: The survival fields the rule reads. Named so a record that has drifted
#: fails loudly here rather than defaulting a missing requirement to met.
_REQUIRED_FIELDS = ("core_identified", "meets_min_local_families",
                    "meets_min_backups", "n_local_valid_families",
                    "n_backups")


def local_support(survival: Mapping[str, Any] | None, *,
                  frame: int | str, operating_point: str | None = None,
                  unsupported_reason: Any = None) -> dict[str, Any]:
    """One frame's LOCAL support verdict, from its own survival block.

    ``survival`` is ``None`` exactly when Gate 2 gave the frame no operating
    point; then the frame is unsupported for that reason and Gate 2's own
    §12.3/§12.4 status is carried through verbatim.
    """
    if survival is None:
        return {
            "frame": int(frame),
            "local_supported": False,
            "local_support_state": LOCAL_UNSUPPORTED,
            "local_unsupported_reason": NO_OPERATING_POINT,
            "local_unsupported_reasons": [NO_OPERATING_POINT],
            "operating_point": operating_point or S.FRAME_UNSUPPORTED,
            "gate2_unsupported_reason": unsupported_reason,
            "core_identified": None,
            "n_local_valid_families": None,
            "min_local_families": S.MIN_LOCAL_FAMILIES,
            "n_backups": None,
            "min_backups": S.MIN_BACKUPS,
            "rule": LOCAL_ELIGIBILITY_RULE,
        }
    missing = [f for f in _REQUIRED_FIELDS if f not in survival]
    if missing:
        raise ProtocolError(
            f"frame {frame}: the survival record is missing {missing}; LOCAL "
            "support is the full registered survival requirement and cannot "
            "be decided from a record that does not state it")
    reasons: list[str] = []
    if not survival["core_identified"]:
        reasons.append(CORE_NOT_IDENTIFIED)
    if not survival["meets_min_local_families"]:
        reasons.append(LOCAL_FAMILIES_BELOW_MINIMUM)
    if not survival["meets_min_backups"]:
        reasons.append(BACKUPS_BELOW_MINIMUM)
    supported = not reasons
    return {
        "frame": int(frame),
        "local_supported": supported,
        "local_support_state": LOCAL_SUPPORTED if supported else LOCAL_UNSUPPORTED,
        "local_unsupported_reason": None if supported else reasons[0],
        "local_unsupported_reasons": reasons,
        "operating_point": operating_point or S.FRAME_SUPPORTED,
        "gate2_unsupported_reason": None,
        "core_identified": bool(survival["core_identified"]),
        "n_local_valid_families": survival["n_local_valid_families"],
        "min_local_families": S.MIN_LOCAL_FAMILIES,
        "n_backups": survival["n_backups"],
        "min_backups": S.MIN_BACKUPS,
        "rule": LOCAL_ELIGIBILITY_RULE,
    }


def local_eligibility(by_frame: Mapping[str, Mapping[str, Any]], *,
                      frames: Sequence[int] = S.FRAMES) -> dict[str, Any]:
    """The model's LOCAL eligibility, from every frame's own verdict.

    The supported set is **the whole supported set**: it is what the LOCAL
    confirmatory design would generate, and it is not truncated to the
    minimum, ranked, or narrowed by anything.
    """
    per_frame: dict[str, Any] = {}
    for w in frames:
        entry = by_frame[str(w)]
        per_frame[str(w)] = local_support(
            entry.get("survival"), frame=w,
            operating_point=entry.get("status"),
            unsupported_reason=entry.get("unsupported_reason"))
    supported = [int(w) for w in frames if per_frame[str(w)]["local_supported"]]
    unsupported = {
        str(w): {k: per_frame[str(w)][k] for k in
                 ("local_unsupported_reason", "local_unsupported_reasons",
                  "operating_point", "gate2_unsupported_reason",
                  "core_identified", "n_local_valid_families", "n_backups")}
        for w in frames if not per_frame[str(w)]["local_supported"]}
    n = len(supported)
    return {
        "by_frame": per_frame,
        "local_supported_frames": supported,
        "local_unsupported_frames": unsupported,
        "n_local_supported_frames": n,
        "local_eligibility_min_frames": R.LOCAL_ELIGIBILITY_MIN_FRAMES,
        "local_eligible": n >= R.LOCAL_ELIGIBILITY_MIN_FRAMES,
        # Stated so a reader cannot mistake the supported set for a shortlist:
        # these are the frames LOCAL confirmatory generation would run, all
        # of them, and the count is not capped at the minimum.
        "frames_entering_local_confirmatory": supported if
        n >= R.LOCAL_ELIGIBILITY_MIN_FRAMES else [],
        "selection_rule": "every LOCAL_SUPPORTED frame enters; there is no "
                          "best-two selection and no ranking",
        "basis": "pre-freeze reference survival only (GATE_3_REFERENCES "
                 "by_frame[f].survival, GATE_2_CALIBRATION support status); "
                 "no composed cell, no Delta_R(f), no pooled statistic",
        "rule": LOCAL_ELIGIBILITY_RULE,
        "document": "dci1/docs/V8_FRAME_CONDITIONING.md §4d",
        "vocabulary": list(LOCAL_SUPPORT_STATES),
        "reason_vocabulary": list(LOCAL_UNSUPPORTED_REASONS),
    }
