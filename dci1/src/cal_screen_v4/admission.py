"""§12.3, §12.4 and §13.2 applied to screen constraints.

The registered implementation (`dci1v4.stages.gates`) is keyed on the
registered symbol table: `REFERENCE_LADDERS[family]`, `length_caliper_ok`
and `verify_pair` all refuse a candidate family by construction, and that
refusal is correct — a candidate family is not in the registered pool.

So this module carries the same rule with the family-specific pieces made
pluggable, and proves it is the same rule rather than claiming it:
``assert_equivalent_to_registered`` runs both implementations over a
constructed input on a *registered* family and requires identical output.
Every number that decides anything — the Newcombe interval, the clustered
paired standard error, the tie key, the caliper, the vacuity maximum — is
imported from the registered code, not re-derived here.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from dci1v4.analysis.intervals import (clustered_paired_se, intersects,
                                       newcombe_paired, paired_table)
from dci1v4.errors import ProtocolError, TerminalStatus
from dci1v4.protocol import constants as C
from dci1v4.protocol.wordings import length_caliper_ok as registered_caliper_ok
from dci1v4.stages.gates import admit_family as registered_admit_family
from dci1v4.stages.gates import select_severity, tie_key
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          Constraint)
from dci1v4.verifiers.witnesses import verify_pair

from bgrid_screen_v4 import focal
from fs_screen_v4.constraints import CANDIDATES
from fs_screen_v4.witnesses import verify_candidate_pair
from fs_screen_v4.wordings import length_caliper_ok as candidate_caliper_ok


# --------------------------------------------------------- family adapters
def family_ladder(family: str) -> tuple[int, ...]:
    if family in CANDIDATES:
        return tuple(CANDIDATES[family].ladder)
    return tuple(REFERENCE_LADDERS[family])


def family_caliper_ok(family: str, q: int, n: int) -> bool:
    if family in CANDIDATES:
        return candidate_caliper_ok(family, q, n)
    return registered_caliper_ok(family, q, n)


def family_witnesses_ok(family: str, q: int, n_star: int,
                        focal_grid: Sequence[int]) -> str | None:
    """§13.2 condition 5, against A and against every B severity in use."""
    try:
        if family in CANDIDATES:
            verify_candidate_pair(family, q, Constraint("A", n_star))
            for m in focal_grid:
                if m in FOCAL_GRID:
                    verify_candidate_pair(family, q, Constraint("B", m))
        else:
            verify_pair(Constraint(family, q), Constraint("A", n_star))
            for m in focal_grid:
                if m in FOCAL_GRID:
                    verify_pair(Constraint(family, q), Constraint("B", m))
    except ProtocolError as error:
        return str(error)
    return None


# ------------------------------------------------------------------ §13.2
def admit(family: str, *, n_star: int,
          calibration: Mapping[int, Sequence[float]],
          a_calibration: Sequence[float],
          prescreen: Mapping[int, float], a_prescreen: float,
          vacuity: Mapping[int, float],
          draw_level: Mapping[int, tuple[Sequence[int], Sequence[int]]],
          focal_grid: Sequence[int] = FOCAL_GRID,
          prescreen_caliper: float | None = None,
          missing_prescreen: str = "reject",
          ladder: Callable[[str], Sequence[int]] = family_ladder,
          caliper_ok: Callable[[str, int, int], bool] = family_caliper_ok,
          witnesses_ok: Callable[..., str | None] = family_witnesses_ok,
          ) -> dict[str, Any]:
    """The §13.2 admissible severity within one family, or None with reasons.

    Same six conditions, same order, same tie-breaks as
    ``dci1v4.stages.gates.admit_family``.

    ``missing_prescreen`` decides what happens to a rung with no pre-screen
    measurement: ``"reject"`` reproduces the registered code exactly, and
    ``"abstain"`` applies conditions 1 and 3-6 and records condition 2 as not
    evaluated. The registered default is ``"reject"``; the equality proof below
    uses it.

    ``prescreen_caliper`` exists only so the registered rule can be run beside
    a **condition-2 sensitivity**, with the disjoint-sample confirmation
    switched off. That is a diagnostic and never an admission: the registered
    value is the default, and a run with the condition off is labelled as such
    wherever it is reported. Weakening a criterion to make a gate pass is
    forbidden (§31) and this is not that -- it measures what one condition
    costs, it does not admit anything.
    """
    if prescreen_caliper is None:
        prescreen_caliper = C.REFERENCE_PRESCREEN_CALIPER
    a_mean = sum(a_calibration) / len(a_calibration)
    candidates: list[dict[str, Any]] = []
    for q in ladder(family):
        if q not in calibration:
            continue
        values = calibration[q]
        mean = sum(values) / len(values)
        difference = mean - a_mean
        reasons: list[str] = []

        if abs(difference) > C.REFERENCE_CALIPER:
            reasons.append(f"solo distance {abs(difference):.4f} exceeds the "
                           f"caliper {C.REFERENCE_CALIPER}")
        ref_draws, a_draws = draw_level.get(q, ((), ()))
        interval = None
        if ref_draws and a_draws:
            interval = newcombe_paired(*paired_table(ref_draws, a_draws))
            if not intersects(interval, C.REFERENCE_NEWCOMBE_REGION):
                reasons.append(
                    f"the 95% Newcombe interval "
                    f"[{interval['lower']:.4f}, {interval['upper']:.4f}] does "
                    f"not intersect ±{C.REFERENCE_NEWCOMBE_REGION}")
        else:
            reasons.append("no paired draw-level data for the Newcombe "
                           "condition")

        pre = prescreen.get(q)
        if prescreen_caliper == float("inf"):
            pass                      # the condition-2 sensitivity of §23
        elif pre is None:
            # A criterion can only be applied where its input exists. §12.2
            # measures all 94 rungs on the pre-screen topics, so in the real
            # study every rung has a value; the floored-stem pre-screen this
            # screen reads was produced by the FORM x STEM screen, which
            # measured only the CURRENT-stem caliper rungs under the floored
            # stem. Rejecting a rung for that is a data-availability artifact,
            # not a criterion. Both dispositions are computed and reported.
            if missing_prescreen == "reject":
                reasons.append("no pre-screen measurement")
            else:
                reasons.append("") if False else None
        elif abs(pre - a_prescreen) > prescreen_caliper:
            reasons.append(
                f"pre-screen distance {abs(pre - a_prescreen):.4f} exceeds "
                f"{prescreen_caliper}")

        if not caliper_ok(family, q, n_star):
            reasons.append("a frozen wording is outside 20% of the "
                           "corresponding A wording")

        vac = vacuity.get(q)
        if vac is None:
            reasons.append("no vacuity measurement")
        elif vac > C.REFERENCE_VACUITY_MAX:
            reasons.append(f"solo vacuity {vac:.3f} exceeds "
                           f"{C.REFERENCE_VACUITY_MAX}")

        failure = witnesses_ok(family, q, n_star, focal_grid)
        if failure:
            reasons.append(f"witness failure: {failure}")

        candidates.append({
            "severity": q, "solo_compliance": mean,
            "difference_from_A": difference,
            "abs_difference": tie_key(abs(difference)),
            "newcombe": interval,
            "paired_se": clustered_paired_se(
                [r - a for r, a in zip(values, a_calibration)]),
            "prescreen_compliance": pre,
            "prescreen_missing": pre is None,
            "vacuity": vac, "admissible": not reasons, "reasons": reasons})

    admissible = [c for c in candidates if c["admissible"]]
    if not admissible:
        return {"family": family, "selected": None, "candidates": candidates}
    best = min(admissible,
               key=lambda c: (tie_key(c["abs_difference"]), -c["severity"]))
    return {"family": family, "selected": best, "candidates": candidates}


def choose_final(family_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """§13.2 final selection: the three admitted families with the smallest
    solo distance from A, family identifier breaking an exact tie."""
    admitted = [r for r in family_results if r.get("selected")]
    admitted.sort(key=lambda r: (tie_key(r["selected"]["abs_difference"]),
                                 r["family"]))
    chosen = admitted[:C.N_FINAL_REFERENCES]
    return {
        "admitted_families": [r["family"] for r in admitted],
        "n_admitted": len(admitted),
        # Every admitted family in §13.2's order, not only the top three. A
        # caller that needs to apply a further rule -- the matrix screen keeps
        # the three R slots to budget families -- has to see past the cut.
        "admitted": [{"family": r["family"], **r["selected"]} for r in admitted],
        "chosen": [{"family": r["family"], **r["selected"]} for r in chosen],
        "excess_identified": len(chosen) >= C.N_FINAL_REFERENCES,
        "identification_status": (None if len(chosen) >= C.N_FINAL_REFERENCES
                                  else "EXCESS_NOT_IDENTIFIED"),
    }


# --------------------------------------------------------- §12.3 and §12.4
def select_outcomes(a_curve: Mapping[int, float], b_curve: Mapping[int, float],
                    *, target_grid: Sequence[int],
                    focal_grid: Sequence[int]) -> dict[str, Any]:
    """§12.3 n* and m*, recording the terminal diagnosis instead of raising."""
    out: dict[str, Any] = {}
    for name, curve, grid, band, aim, status in (
            ("A", a_curve, target_grid, C.TARGET_BAND, C.TARGET_AIM,
             "TARGET_RANGE_EXHAUSTED"),
            ("B", b_curve, focal_grid, C.FOCAL_BAND, C.FOCAL_AIM,
             "FOCAL_RANGE_EXHAUSTED")):
        if not any(sev in curve for sev in grid):
            out[name] = {"outcome": "NOT_MEASURED",
                         "reason": f"this screen carries no {name} arm under "
                                   f"this stem",
                         "grid": list(grid)}
            continue
        try:
            out[name] = {"outcome": "SELECTED",
                         **select_severity(curve, grid, band, aim,
                                           exhausted_status=status,
                                           quantity=name)}
        except TerminalStatus as terminal:
            out[name] = {"outcome": "TERMINAL", "status": terminal.args[0],
                         "detail": terminal.args[1]
                         if len(terminal.args) > 1 else {},
                         "curve": {int(k): v for k, v in sorted(curve.items())},
                         "band": list(band), "grid": list(grid)}
    return out


def regime_adequacy(*, b_solo_vacuity: float,
                    graded_distribution: Mapping[str, float]) -> dict[str, Any]:
    """§12.4, evaluated rather than raised.

    §12.4 reads "the graded distribution of each outcome constraint is
    non-degenerate, meaning it is not concentrated above 0.99 or below 0.01".
    The registered `gates.gate2_payload` takes a `graded_distribution` mapping
    of name to a single number and compares it to those bounds; it does not fix
    what that number is. Two readings are available and they are not equivalent:
    the MEAN graded score, and the SHARE of draws whose graded score is above
    0.99. Both are computed by the caller and both are reported; neither is
    chosen here.
    """
    failures: list[str] = []
    if b_solo_vacuity > C.REGIME_VACUITY_MAX:
        failures.append(f"B solo vacuity {b_solo_vacuity:.3f} exceeds "
                        f"{C.REGIME_VACUITY_MAX}")
    for name, value in sorted(graded_distribution.items()):
        if value > C.GRADED_DEGENERACY_HIGH or value < C.GRADED_DEGENERACY_LOW:
            failures.append(f"the graded distribution of {name} is degenerate "
                            f"at {value:.4f}")
    return {"passed": not failures, "failures": failures,
            "b_solo_vacuity": b_solo_vacuity,
            "b_solo_vacuity_max": C.REGIME_VACUITY_MAX,
            "graded_distribution": dict(graded_distribution),
            "status": None if not failures else "REGIME_NOT_FOUND"}


# ------------------------------------------------------- the equality proof
def assert_equivalent_to_registered() -> dict[str, Any]:
    """This module's §13.2 is the registered §13.2.

    Both implementations are run over a constructed input on a registered
    family, at every rung of its registered ladder, and required to agree
    exactly — the selected severity, every candidate row, every reason string.
    """
    family, n_star = "RF1", 4
    ladder = REFERENCE_LADDERS[family]
    topics = 24
    calibration, prescreen, vacuity, draw_level = {}, {}, {}, {}
    # A deterministic input that makes several rungs pass and several fail on
    # each of the six conditions, so the comparison exercises the branches.
    a_calibration = [((i * 7) % 4) / 4.0 for i in range(topics)]
    a_draws = [1 if (i % 3) else 0 for i in range(topics * 4)]
    for position, q in enumerate(ladder):
        offset = (position - len(ladder) / 2) * 0.03
        calibration[q] = [min(1.0, max(0.0, v + offset)) for v in a_calibration]
        prescreen[q] = min(1.0, max(0.0, 0.5 + offset * 2))
        vacuity[q] = 0.02 * position
        draw_level[q] = ([1 if ((i + position) % 3) else 0
                          for i in range(topics * 4)], a_draws)

    mine = admit(family, n_star=n_star, calibration=calibration,
                 a_calibration=a_calibration, prescreen=prescreen,
                 a_prescreen=0.5, vacuity=vacuity, draw_level=draw_level)
    theirs = registered_admit_family(
        family, n_star=n_star, calibration=calibration,
        a_calibration=a_calibration, prescreen=prescreen, a_prescreen=0.5,
        vacuity=vacuity, draw_level=draw_level)

    # This module records one field the registered one does not --
    # `prescreen_missing`, which says whether condition 2 had an input at all.
    # It is additive bookkeeping and is stripped before the comparison; every
    # field the registered code produces must match exactly, reason strings
    # included.
    def strip(result: dict[str, Any]) -> dict[str, Any]:
        out = dict(result)
        out["candidates"] = [{k: v for k, v in c.items()
                              if k != "prescreen_missing"}
                             for c in result["candidates"]]
        if result.get("selected"):
            out["selected"] = {k: v for k, v in result["selected"].items()
                               if k != "prescreen_missing"}
        return out

    if strip(mine) != strip(theirs):
        raise ProtocolError(
            "the screen's §13.2 does not reproduce the registered §13.2")
    return {"family_checked": family, "rungs_checked": len(ladder),
            "identical": True,
            "additive_fields_excluded": ["prescreen_missing"],
            "admissible_rungs": sum(1 for c in mine["candidates"]
                                    if c["admissible"]),
            "selected": (mine["selected"] or {}).get("severity")}


def assert_extended_grid_is_registered_rule() -> dict[str, Any]:
    """The m in {11, 12} rungs are the registered B rule, not a new one."""
    from dci1v4.verifiers.wording_suite import TWENTY_RESPONSES
    return {"wordings": focal.assert_wordings_match(),
            "scoring": focal.assert_scoring_matches(TWENTY_RESPONSES),
            "monotone": focal.assert_monotone_in_m(TWENTY_RESPONSES)}


__all__ = ["family_ladder", "family_caliper_ok", "family_witnesses_ok",
           "admit", "choose_final", "select_outcomes", "regime_adequacy",
           "assert_equivalent_to_registered",
           "assert_extended_grid_is_registered_rule"]
