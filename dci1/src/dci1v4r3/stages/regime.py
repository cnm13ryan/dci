"""The §12.2 dense screen and the §12.3 shortlist.

v4r2's shortlist kept, per family, the three severities whose solo compliance
was nearest A's. That rule cannot serve a difficulty spectrum: the spectrum
needs rungs a fifth of the scale away from A on both sides, and a
nearest-to-A shortlist is exactly the set that excludes them.

The v4r3 shortlist is built around three targets -- ``iota_A`` and
``iota_A -/+ 0.20`` -- and the ranking that decides which families reach §12.3
at all is *spanning feasibility first, distance second*, so a family that
matches A closely but cannot straddle it does not consume one of the six
slots that a family which can straddle it needs.

Everything here reads pre-screen solo and chance compliance. It reads no
composed cell (§12.5, §13.9).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol import constants as C
from dci1v4r3.stages.selection import instructed_compliance, tie_key
from dci1v4r3.verifiers.constraints import (
    FAMILIES, RESERVES, focal_severities,
)

__all__ = ["ladder_screen_cell_count", "prescreen_difficulty_table",
           "family_ranking", "shortlist", "assert_shortlist_is_measured",
           "regime_screen_payload", "solo_calibration_cell_count"]


def ladder_screen_cell_count() -> int:
    """§12.2 round 0: one unconstrained cell, both grids including the
    extension, and every round-0 ladder severity of all twenty families.

    §12.6's expansion adds rungs to this on top; the round-0 figure is what
    the plan costs before any coverage shortfall is known.
    """
    return (1 + len(C.TARGET_GRID) + len(focal_severities(extended=True))
            + C.N_SEVERITIES)


def solo_calibration_cell_count(*, n_reference_families: int,
                                n_class_families: int,
                                rungs_per_reference: int,
                                rungs_per_class: int,
                                focal_extension: bool = False) -> int:
    """§12.3's measured cell count, from the shortlist it is handed."""
    return (1 + len(C.TARGET_GRID)
            + len(focal_severities(extended=focal_extension))
            + n_reference_families * rungs_per_reference
            + n_class_families * rungs_per_class)


def prescreen_difficulty_table(rows: Sequence[Mapping[str, Any]]
                               ) -> dict[str, dict[str, float]]:
    """§12.2's first output: kappa, solo and iota for every measured instance.

    ``rows`` carry ``kind``, ``severity``, ``solo`` and ``chance``. A row whose
    chance compliance has reached the degeneracy ceiling is recorded with
    ``iota = None`` rather than dividing by zero, and is ineligible everywhere
    downstream.
    """
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        label = f"{row['kind']}:{row['severity']}"
        entry = {"solo": float(row["solo"]), "chance": float(row["chance"])}
        if entry["chance"] < C.CHANCE_DEGENERACY_MAX:
            entry["iota"] = instructed_compliance(entry["solo"],
                                                  entry["chance"])
            entry["lift"] = entry["solo"] - entry["chance"]
        else:
            entry["iota"] = None
            entry["lift"] = entry["solo"] - entry["chance"]
        out[label] = entry
    return out


def _family_rungs(table: Mapping[str, Mapping[str, Any]], family: str
                  ) -> list[tuple[int, float]]:
    """Every **measured** eligible rung of ``family``, not every registered one.

    Reading the round-0 ladder here would make §12.6's expansion invisible to
    the ranking and the shortlist that the expansion exists to feed: a rung
    admitted in round 1 would be generated, scored, and then ignored. The
    declared range still bounds it, so a rung outside §7.0's frozen reserve
    cannot enter through a hand-built table.
    """
    rungs = []
    lo, hi = C.SPECTRUM_ELIGIBILITY_BAND
    for q in RESERVES[family]:
        entry = table.get(f"{family}:{q}")
        if entry is None or entry.get("iota") is None:
            continue
        if lo <= entry["iota"] <= hi:
            rungs.append((q, float(entry["iota"])))
    return rungs


def family_ranking(table: Mapping[str, Mapping[str, Any]], *, iota_a: float,
                   role: str = "reference") -> list[dict[str, Any]]:
    """§12.3's ranking: spanning feasibility first, then distance, then id.

    A family that matches A closely but has no eligible rung on one side of A
    cannot supply a spectrum triple, so ranking it above a family that can
    would spend a shortlist slot on a family Gate 3 must later drop.
    """
    ranked: list[dict[str, Any]] = []
    for family in sorted(f for f, spec in FAMILIES.items()
                         if spec.role == role):
        rungs = _family_rungs(table, family)
        if not rungs:
            ranked.append({"family": family, "straddles": False,
                           "near": None, "distance": None,
                           "reason": "no eligible rung at pre-screen"})
            continue
        near_q, near_iota = min(rungs,
                                key=lambda r: (tie_key(abs(r[1] - iota_a)),
                                               -r[0]))
        below = [r for r in rungs if tie_key(r[1]) < tie_key(iota_a)]
        above = [r for r in rungs if tie_key(r[1]) > tie_key(iota_a)]
        ranked.append({
            "family": family, "straddles": bool(below and above),
            "near": near_q, "near_iota": near_iota,
            "distance": abs(near_iota - iota_a),
            "n_below": len(below), "n_above": len(above)})
    ranked.sort(key=lambda r: (not r["straddles"],
                              tie_key(r["distance"]) if r["distance"] is not None
                              else float("inf"),
                              r["family"]))
    return ranked


def shortlist(table: Mapping[str, Mapping[str, Any]], *, iota_a: float
              ) -> dict[str, list[int]]:
    """§12.3's shortlist: six reference families and both class families.

    Per reference family, at most four severities: the rung nearest iota_A,
    the eligible rung below A nearest ``iota_A - 0.20``, the eligible rung
    above A nearest ``iota_A + 0.20``, and the second-nearest to iota_A. Per
    class family, the two nearest to iota_A.
    """
    out: dict[str, list[int]] = {}
    ranked = family_ranking(table, iota_a=iota_a, role="reference")
    chosen = [r["family"] for r in ranked
              if r["distance"] is not None][:C.SHORTLIST_REFERENCE_FAMILIES]
    for family in chosen:
        rungs = _family_rungs(table, family)
        by_distance = sorted(rungs, key=lambda r: (tie_key(abs(r[1] - iota_a)),
                                                   -r[0]))
        picks: list[int] = [by_distance[0][0]]
        below = [r for r in rungs if tie_key(r[1]) < tie_key(iota_a)]
        above = [r for r in rungs if tie_key(r[1]) > tie_key(iota_a)]
        if below:
            target = iota_a - C.SPECTRUM_OFFSET
            picks.append(min(below, key=lambda r: (tie_key(abs(r[1] - target)),
                                                   -r[0]))[0])
        if above:
            target = iota_a + C.SPECTRUM_OFFSET
            picks.append(min(above, key=lambda r: (tie_key(abs(r[1] - target)),
                                                   -r[0]))[0])
        for q, _ in by_distance[1:]:
            if len(dict.fromkeys(picks)) >= C.SHORTLIST_MAX_PER_REFERENCE_FAMILY:
                break
            picks.append(q)
        out[family] = sorted(dict.fromkeys(picks))[
            :C.SHORTLIST_MAX_PER_REFERENCE_FAMILY]

    for family in sorted(f for f, spec in FAMILIES.items()
                         if spec.role == "class_control"):
        rungs = _family_rungs(table, family)
        if not rungs:
            continue
        by_distance = sorted(rungs, key=lambda r: (tie_key(abs(r[1] - iota_a)),
                                                   -r[0]))
        out[family] = sorted(q for q, _ in
                             by_distance[:C.SHORTLIST_MAX_PER_CLASS_FAMILY])
    return out


def assert_shortlist_is_measured(table: Mapping[str, Mapping[str, Any]],
                                 shortlist_table: Mapping[str, Sequence[int]]
                                 ) -> None:
    """Every shortlisted rung carries the pre-screen value §13.4 reads.

    §13.4 condition 2 is a caliper on the pre-screen measurement, so a record
    that names a rung with no pre-screen value hands that condition an input
    it cannot evaluate. Putting the check on the record-writing path means the
    unevaluable record cannot exist rather than being caught later.
    """
    missing = [f"{family}:{q}" for family, rungs in shortlist_table.items()
               for q in rungs if f"{family}:{q}" not in table]
    if missing:
        raise ProtocolError(
            "the §12.3 shortlist names rungs with no pre-screen measurement, "
            f"so §13.4 condition 2 would be unevaluable for them: {missing}")
    over = {f: len(r) for f, r in shortlist_table.items()
            if FAMILIES[f].role == "reference"
            and len(r) > C.SHORTLIST_MAX_PER_REFERENCE_FAMILY}
    over.update({f: len(r) for f, r in shortlist_table.items()
                 if FAMILIES[f].role == "class_control"
                 and len(r) > C.SHORTLIST_MAX_PER_CLASS_FAMILY})
    if over:
        raise ProtocolError(f"§12.3's shortlist caps are exceeded: {over}")
    families = [f for f in shortlist_table if FAMILIES[f].role == "reference"]
    if len(families) > C.SHORTLIST_REFERENCE_FAMILIES:
        raise ProtocolError(
            f"§12.3 shortlists {C.SHORTLIST_REFERENCE_FAMILIES} reference "
            f"families; got {len(families)}")


def regime_screen_payload(*, selected_cap: int,
                          difficulty_table: Mapping[str, Mapping[str, Any]],
                          shortlist_table: Mapping[str, Sequence[int]],
                          iota_a_prescreen: float,
                          truncation_by_cell: Mapping[str, float],
                          screen_dir: str,
                          vocabulary_freeze: Mapping[str, Any] | None = None
                          ) -> dict[str, Any]:
    """The §12.2 record. The invariant runs before the record can exist.

    ``vocabulary_freeze`` is §12.6's output. It is required: the stage closes
    the candidate vocabulary, and a regime record without it would leave the
    population §13 selects from undefined.
    """
    assert_shortlist_is_measured(difficulty_table, shortlist_table)
    if vocabulary_freeze is None:
        raise ProtocolError(
            "§12.6 closes the candidate vocabulary inside the regime screen; "
            "a record without the freeze leaves the population §13 selects "
            "from undefined")
    return {
        "vocabulary_freeze": dict(vocabulary_freeze),
        "outcome": "PASS", "stage": C.STAGE_REGIME,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_REGIME],
        "selected_cap": selected_cap,
        "ladder_screen_cells": ladder_screen_cell_count(),
        "difficulty_table": {k: dict(v) for k, v in difficulty_table.items()},
        "shortlist": {k: list(v) for k, v in shortlist_table.items()},
        "iota_a_prescreen": iota_a_prescreen,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "truncation_by_cell": dict(truncation_by_cell),
        "screen_dir": screen_dir,
    }
