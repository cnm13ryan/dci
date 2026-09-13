"""Precision of Delta_R(f) at the one confirmatory allocation.

The allocation is ``rules.CONFIRMATORY_BLOCKS_PER_FRAME`` (384 blocks per
frame, the ceiling; rules.py states its history). This module no longer
*chooses* an allocation --- the 2026-09-02 menu rule ({288, 384} at the joint
Šidák constant) is superseded, because two active sources of one number are
one too many --- it **projects** §16.1's variance form at that allocation,
under the registered planning constants and under the adverse scenarios,
and states whether the registered precision precondition
(``C.PRECISION_PRECONDITIONS["Delta_R"]``, 0.05 on the simultaneous
half-width) is projected to hold at the joint constant for a model with
``n_frames`` LOCAL frames. When it is not, nothing moves: §17.3's realised
interval decides (the non-terminal ``INSUFFICIENT_PRECISION``).

Scenarios. ``REGISTERED_PLANNING`` (phi 0.27, rho 0.5, p(1-p) 0.215) is
§16.2's own planning point; ``REGISTERED_ALTERNATE`` (phi 0.37) the
sensitivity value §16.3 carries; ``COMPOSED_AT_HALF`` and
``ALTERNATE_AT_HALF`` put every composed rate at 0.5 (p(1-p) = 0.25);
``WORST_CASE`` also drops the topic correlation to 0. The two the previous
rule read (``RULE_SCENARIOS``) are still the ones the record calls
"adverse"; the bounds are reported beside them.

Multiplicity (``MULTIPLICITY_RULE``) is unchanged from the confirmatory
layer of 2026-09-02: F1 per (model, frame, configuration) by the bootstrap
studentised maximum-modulus; the joint cross-frame family of every F1
member of every entering frame per (model, configuration) from a
topic-level bootstrap; a model-level LOCAL claim is the conjunction over
entering frames.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any

from dci1v4.analysis.variance import variances
from dci1v7.analysis.bootstrap import sidak_critical
from dci1v7.protocol import constants as C
from dci1v8dev import rules as R

__all__ = ["FAMILY_SIZE_PER_FRAME", "ALLOCATION", "SCENARIOS",
           "RULE_SCENARIOS", "PRECONDITION", "joint_family_size",
           "project", "precision_at", "allocation_record",
           "MULTIPLICITY_RULE", "PRECISION_RULE"]

FAMILY_SIZE_PER_FRAME = len(C.FAMILY_MEMBERS[C.PRIMARY_FAMILY])   # 6
#: The one allocation. Stated in ``rules`` and read here; never chosen here.
ALLOCATION = R.CONFIRMATORY_BLOCKS_PER_FRAME
PRECONDITION = C.PRECISION_PRECONDITIONS["Delta_R"]
SCENARIOS: dict[str, dict[str, float]] = {
    "REGISTERED_PLANNING": {"phi": C.PHI_PRIMARY, "rho": C.RHO,
                            "p_one_minus_p": C.P_ONE_MINUS_P},
    "REGISTERED_ALTERNATE": {"phi": C.PHI_ALTERNATE, "rho": C.RHO,
                             "p_one_minus_p": C.P_ONE_MINUS_P},
    "COMPOSED_AT_HALF": {"phi": C.PHI_PRIMARY, "rho": C.RHO,
                         "p_one_minus_p": 0.25},
    "ALTERNATE_AT_HALF": {"phi": C.PHI_ALTERNATE, "rho": C.RHO,
                          "p_one_minus_p": 0.25},
    "WORST_CASE": {"phi": C.PHI_ALTERNATE, "rho": 0.0, "p_one_minus_p": 0.25},
}
#: The scenarios the rule reads; the others are bounds and are reported.
RULE_SCENARIOS = ("REGISTERED_ALTERNATE", "COMPOSED_AT_HALF")

MULTIPLICITY_RULE = (
    "per (model, frame, configuration): F1 as registered (six members), "
    "bootstrap studentised maximum-modulus; per (model, configuration): the "
    "JOINT family of every F1 member of every entering frame, critical value "
    "from a topic-level block bootstrap with one draw shared across frames; "
    "the decision interval of every primary claim is the joint one; a "
    "model-level LOCAL claim is the conjunction over its entering frames "
    "(intersection-union; no further adjustment); no at-least-one-frame "
    "claim exists")
PRECISION_RULE = (
    "one allocation, rules.CONFIRMATORY_BLOCKS_PER_FRAME = 384 blocks per "
    "entering frame (the ceiling), for every model; §16.1's variance form "
    "is projected at it under the registered planning constants and the "
    "adverse scenarios at the joint Šidák constant (k = 6 x LOCAL frames "
    "entering) and the projection is recorded; §16.2's precondition and "
    "§17.3's realised evaluation decide, and no allocation is chosen from "
    "a menu")


def joint_family_size(n_frames: int) -> int:
    return FAMILY_SIZE_PER_FRAME * max(1, int(n_frames))


def project(*, blocks: int, n_frames: int, scenario: str,
            m: int = C.M_DRAWS) -> dict[str, Any]:
    s = SCENARIOS[scenario]
    var = variances(blocks, m, phi=s["phi"], rho=s["rho"],
                    p_one_minus_p=s["p_one_minus_p"])
    se = math.sqrt(var["Delta_R"])
    k = joint_family_size(n_frames)
    crit_joint = sidak_critical(k)
    crit_frame = sidak_critical(FAMILY_SIZE_PER_FRAME)
    z_power = NormalDist().inv_cdf(0.80)
    return {"scenario": scenario, **s, "blocks": blocks, "m_draws": m,
            "n_frames": n_frames, "joint_family_size": k,
            "se_delta_r": se,
            "critical_frame": crit_frame, "critical_joint": crit_joint,
            "half_width_frame": crit_frame * se,
            "half_width_joint": crit_joint * se,
            "mde_80_joint": (crit_joint + z_power) * se,
            "meets_precondition_joint": crit_joint * se <= PRECONDITION,
            "is_rule_scenario": scenario in RULE_SCENARIOS,
            "precondition": PRECONDITION}


def precision_at(n_frames: int, *, blocks: int = ALLOCATION) -> dict[str, Any]:
    """§16.1 projected at the allocation for a model with ``n_frames`` LOCAL
    frames: every scenario, and whether the adverse pair meets the
    precondition at the joint constant. Descriptive; nothing is chosen."""
    table = {sc: project(blocks=blocks, n_frames=n_frames, scenario=sc)
             for sc in SCENARIOS}
    return {"n_frames": n_frames, "joint_family_size": joint_family_size(n_frames),
            "blocks_per_frame": blocks,
            "rule_scenarios": list(RULE_SCENARIOS),
            "precondition_met_adverse": all(
                table[sc]["meets_precondition_joint"] for sc in RULE_SCENARIOS),
            "precondition_met_planning": table["REGISTERED_PLANNING"][
                "meets_precondition_joint"],
            "table": table, "precondition": PRECONDITION,
            "multiplicity_rule": MULTIPLICITY_RULE,
            "precision_rule": PRECISION_RULE}


def allocation_record(n_frames_by_model: dict[str, int]) -> dict[str, Any]:
    """The study-level statement: the one allocation, with the precision
    projected for every model at its LOCAL frame count and at the largest
    count in the study."""
    n_max = max([1] + list(n_frames_by_model.values()))
    at_max = precision_at(n_max)
    return {"frames_entering_local_by_model": dict(n_frames_by_model),
            "chosen_blocks_per_frame": ALLOCATION,
            "source": "rules.CONFIRMATORY_BLOCKS_PER_FRAME",
            "decided_at_n_frames": n_max,
            "joint_family_size": at_max["joint_family_size"],
            "precondition_met_adverse_at_max": at_max["precondition_met_adverse"],
            "table": at_max["table"], "precondition": PRECONDITION,
            "per_model": {m: precision_at(max(1, n))
                          for m, n in sorted(n_frames_by_model.items())},
            "multiplicity_rule": MULTIPLICITY_RULE,
            "precision_rule": PRECISION_RULE}
