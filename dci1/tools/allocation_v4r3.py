"""The v4r3 allocation: projected simultaneous half-widths for a 47-cell block.

v4r2 §16.2 registered 384 blocks at M = 4 over a 25-cell block, sized so that
every primary member met its precision precondition under *both* fitted values
of phi. v4r3 changes three inputs to that calculation and none of them can be
assumed away:

1. the block carries 47 cells, not 25 (the difficulty spectrum, the class arm
   and the load-0 cell);
2. the primary family F1 grows from four members to six, because
   ``delta_difficulty`` and ``Xi`` both license claims under the v4r3 claim
   ladder, so the Sidak planning bound moves from k=2.4909 to k=2.6310;
3. ``delta_difficulty`` is a new estimand with its own variance, which this
   module derives rather than borrows.

The variance model is v4r2 §16.1 unchanged -- same p(1-p), same phi pair, same
rho -- so the D, Lambda, Delta_R and Delta_j formulas here reproduce v4r2's
published table exactly when asked for 384 blocks at k4. ``verify_v4r2_table``
asserts that, which is what makes the new row trustworthy: the only thing that
changed is the estimand set.

Run: ``python tools/allocation_v4r3.py`` from ``dci1/``.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# ------------------------------------------------------ v4r2 §16.1 constants
P_ONE_MINUS_P = 0.215
PHI_PRIMARY = 0.27
PHI_ALTERNATE = 0.37
RHO = 0.5

#: §16.2's reference Sidak critical values, by family size.
SIDAK = {1: 1.9600, 4: 2.4909, 5: 2.5697, 6: 2.6310, 7: 2.6900, 9: 2.7729}

#: v4r3 precision preconditions. D, Delta_R and delta_difficulty are half the
#: registered smallest effect of interest (0.10); Lambda and Delta_j keep
#: v4r2's values, which were set from what a design with more terms can reach.
#: Xi carries NO precondition: under the v4r3 claim ladder it is a
#: direction-only gate, and an unresolved direction is reported as
#: A_GENERAL_NOT_EXCLUDED rather than compared against a magnitude.
PRECONDITIONS = {"D": 0.05, "Delta_R": 0.05, "delta_difficulty": 0.05,
                 "Lambda": 0.08, "Delta_j": 0.06}


def sidak(k: int) -> float:
    """Two-sided Sidak critical value for a family of size k."""
    if k in SIDAK:
        return SIDAK[k]
    alpha = 1.0 - 0.95 ** (1.0 / k)
    # inverse normal by bisection; the planning table needs four decimals only
    lo, hi = 0.0, 10.0
    target = 1.0 - alpha / 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        cdf = 0.5 * (1.0 + math.erf(mid / math.sqrt(2.0)))
        lo, hi = (mid, hi) if cdf < target else (lo, mid)
    return (lo + hi) / 2.0


def components(phi: float) -> tuple[float, float]:
    return phi * P_ONE_MINUS_P, (1.0 - phi) * P_ONE_MINUS_P


def var_D(T: int, M: int, phi: float) -> float:
    topic, draw = components(phi)
    return (2 * (1 - RHO) * topic + 2 * draw / M) / T


def var_Lambda(T: int, M: int, phi: float) -> float:
    topic, draw = components(phi)
    return (4 * (1 - RHO) * topic + 4 * draw / M) / T


def var_weighted_contrast(T: int, M: int, phi: float, sum_w_squared: float
                          ) -> float:
    """A contrast of one composed cell against a weighted average of others.

    Both ``Delta_R`` (uniform weights over three references, sum of squares
    1/3) and ``delta_difficulty`` (regression prediction weights) have this
    shape: the solo baseline cancels because the weights sum to one, leaving a
    difference of composed cell means. The topic term is v4r2's, which treats
    the weighted average as carrying one cell's topic variance -- the
    among-companion topic correlation is taken as 1, exactly as §16.1 does for
    the three-reference average.
    """
    topic, draw = components(phi)
    return (2 * (1 - RHO) * topic + draw * (1.0 + sum_w_squared) / M) / T


def var_delta_difficulty(T: int, M: int, phi: float, *, beta: float,
                         sum_w_squared: float) -> float:
    """``delta_difficulty`` with the difficulty coordinate itself estimated.

    Write the fit as ``Yhat_A = Ybar + beta*(d_A - dbar)`` over the nine non-A
    companions (three families, three rungs, family-aware intercepts averaged).
    Then ``delta_difficulty = D(B<-A) - Yhat_A`` and, to first order,

        d(delta)/d(d_A) = -beta,   d(delta)/d(dbar) = +beta,

    so an error in the measured difficulties enters multiplied by the slope.
    ``d_A - dbar`` is itself a contrast of one solo cell against a weighted
    average of nine, which carries the same variance shape as the estimand.
    The result is a clean inflation factor:

        Var[delta] ~ (1 + beta^2) * Var[delta | difficulties known].

    The cross-covariance between the difficulty error and the loss error is
    dropped: it is order 1/T and can take either sign, so no planning claim
    rests on it. §16.1's stance on rho applies here too -- the projection is a
    projection, and an unfavourable realisation appears as
    INSUFFICIENT_PRECISION rather than as a silent widening.
    """
    return (1.0 + beta * beta) * var_weighted_contrast(T, M, phi,
                                                       sum_w_squared)


def half_widths(T: int, M: int, phi: float, *, k_primary: float,
                k_secondary: float, beta: float, sum_w_squared: float
                ) -> dict[str, float]:
    return {
        "D": k_primary * math.sqrt(var_D(T, M, phi)),
        "Delta_R": k_primary * math.sqrt(
            var_weighted_contrast(T, M, phi, 1.0 / 3.0)),
        "delta_difficulty": k_primary * math.sqrt(
            var_delta_difficulty(T, M, phi, beta=beta,
                                 sum_w_squared=sum_w_squared)),
        "Lambda": k_primary * math.sqrt(var_Lambda(T, M, phi)),
        "Delta_j": k_secondary * math.sqrt(var_D(T, M, phi)),
    }


def meets(hw: dict[str, float]) -> bool:
    return all(hw[q] <= PRECONDITIONS[q] + 1e-12 for q in PRECONDITIONS)


def verify_v4r2_table() -> dict[str, float]:
    """v4r2 §16.2's published row, reproduced from these formulas.

    If this drifts, the v4r3 numbers below are not comparable to the
    registered ones and the discrepancy is the finding, not the new row.
    """
    published = {"D": 0.0470, "Delta_R": 0.0422, "Lambda": 0.0664,
                 "Delta_j": 0.0496}
    got = {
        "D": SIDAK[4] * math.sqrt(var_D(384, 4, PHI_PRIMARY)),
        "Delta_R": SIDAK[4] * math.sqrt(
            var_weighted_contrast(384, 4, PHI_PRIMARY, 1.0 / 3.0)),
        "Lambda": SIDAK[4] * math.sqrt(var_Lambda(384, 4, PHI_PRIMARY)),
        "Delta_j": SIDAK[6] * math.sqrt(var_D(384, 4, PHI_PRIMARY)),
    }
    for name, want in published.items():
        if abs(got[name] - want) > 5e-5:
            raise AssertionError(
                f"v4r2 §16.2 {name}: published {want}, recomputed "
                f"{got[name]:.6f} -- the variance model has drifted")
    return got


# ---------------------------------------------------------------- the design
N_UNCONSTRAINED = 1          # the load-0 cell: the chance-compliance baseline
                             # of every constraint, on the confirmatory blocks
N_CORE_SOLO = 5              # A, B, R1, R2, R3
N_CORE_COMPOSED = 20         # 10 unordered pairs x 2 orders
N_SPECTRUM_COMPANIONS = 6    # 3 families x 2 straddling rungs
N_SPECTRUM_SOLO = N_SPECTRUM_COMPANIONS
N_SPECTRUM_COMPOSED = N_SPECTRUM_COMPANIONS * 2      # B + companion, 2 orders
N_CLASS_SOLO = 1             # the production-class control companion
N_CLASS_COMPOSED = 2         # B + class companion, 2 orders
N_CELLS = (N_UNCONSTRAINED + N_CORE_SOLO + N_CORE_COMPOSED
           + N_SPECTRUM_SOLO + N_SPECTRUM_COMPOSED
           + N_CLASS_SOLO + N_CLASS_COMPOSED)        # 47

#: Weights on the nine non-A companion losses when the fit predicts at A's
#: difficulty. With the registered offsets straddling A the spectrum is
#: centred on A, ``dbar = d_A``, and every weight is 1/9 exactly, giving
#: sum-of-squares 1/9. Realised rungs will not hit their targets, so the
#: planning value carries an off-centre allowance: ``(d_A - dbar)^2 / Sxx``
#: with the centre off by 0.05 and Sxx from three families straddling by 0.20.
SUM_W_SQUARED_IDEAL = 1.0 / 9.0
OFF_CENTRE_ALLOWANCE = 0.05
SXX_AT_REGISTERED_OFFSETS = 3 * (0.20 ** 2 + 0.0 + 0.20 ** 2)
SUM_W_SQUARED_PLANNING = (SUM_W_SQUARED_IDEAL
                          + OFF_CENTRE_ALLOWANCE ** 2
                          / SXX_AT_REGISTERED_OFFSETS)

#: Candidate block counts. Every entry is a whole number of confirmatory
#: topics per subject area, because §6.2 cuts the bank stratum by stratum:
#: ``blocks = 12 * per_area`` and the sequestered set takes what is left of
#: the 52 authored questions after 2 pre-screen, 8 solo and 2 composed.
def split_for(blocks: int) -> dict[str, int]:
    per_area, remainder = divmod(blocks, 12)
    if remainder:
        raise ValueError(f"{blocks} blocks is not 12 whole strata")
    sequestered_per_area = 52 - 2 - 8 - 2 - per_area
    return {"confirmatory_per_area": per_area,
            "sequestered_per_area": sequestered_per_area,
            "sequestered_total": sequestered_per_area * 12}


MENU_BLOCKS = (384, 408, 432, 456)
MENU_DRAWS = (4, 8)
#: §25 needs a withheld set for a future uncontaminated rerun. Four per area,
#: 48 topics, is the registered floor: below it the sequestered set stops
#: being able to reconstitute a subject-balanced replication.
MIN_SEQUESTERED_PER_AREA = 4


def menu(beta: float) -> list[dict]:
    rows = []
    for blocks in MENU_BLOCKS:
        split = split_for(blocks)
        for M in MENU_DRAWS:
            row = {
                "blocks": blocks, "M": M,
                "cells": N_CELLS,
                "generations_per_model": N_CELLS * blocks * M,
                "generations_four_models": N_CELLS * blocks * M * 4,
                "sequestered_total": split["sequestered_total"],
                "sequestered_admissible":
                    split["sequestered_per_area"] >= MIN_SEQUESTERED_PER_AREA,
            }
            for label, phi in (("phi_0.27", PHI_PRIMARY),
                               ("phi_0.37", PHI_ALTERNATE)):
                hw = half_widths(blocks, M, phi, k_primary=SIDAK[6],
                                 k_secondary=SIDAK[6], beta=beta,
                                 sum_w_squared=SUM_W_SQUARED_PLANNING)
                row[label] = {k: round(v, 4) for k, v in hw.items()}
                row[f"meets_{label}"] = meets(hw)
            row["registrable"] = (row["meets_phi_0.27"]
                                  and row["meets_phi_0.37"]
                                  and row["sequestered_admissible"])
            rows.append(row)
    return rows


def minimum_blocks(beta: float, M: int = 4) -> int:
    """The smallest whole-strata block count meeting every precondition."""
    for blocks in range(120, 12 * 41, 12):
        if split_for(blocks)["sequestered_per_area"] < MIN_SEQUESTERED_PER_AREA:
            break
        ok = all(meets(half_widths(blocks, M, phi, k_primary=SIDAK[6],
                                   k_secondary=SIDAK[6], beta=beta,
                                   sum_w_squared=SUM_W_SQUARED_PLANNING))
                 for phi in (PHI_PRIMARY, PHI_ALTERNATE))
        if ok:
            return blocks
    return -1


def main(beta: float) -> dict:
    out = {
        "v4r2_table_reproduced": {k: round(v, 4)
                                  for k, v in verify_v4r2_table().items()},
        "design": {
            "cells_per_block": N_CELLS,
            "unconstrained": N_UNCONSTRAINED,
            "core_solo": N_CORE_SOLO, "core_composed": N_CORE_COMPOSED,
            "spectrum_solo": N_SPECTRUM_SOLO,
            "spectrum_composed": N_SPECTRUM_COMPOSED,
            "class_solo": N_CLASS_SOLO, "class_composed": N_CLASS_COMPOSED,
            "primary_family_size": 6,
            "sidak_primary": SIDAK[6],
        },
        "delta_difficulty_planning": {
            "beta": beta,
            "sum_w_squared": round(SUM_W_SQUARED_PLANNING, 6),
            "variance_inflation": round(1.0 + beta * beta, 4),
        },
        "preconditions": PRECONDITIONS,
        "minimum_blocks_at_M4": minimum_blocks(beta, 4),
        "menu": menu(beta),
    }
    return out


if __name__ == "__main__":
    beta = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    print(json.dumps(main(beta), indent=2))
