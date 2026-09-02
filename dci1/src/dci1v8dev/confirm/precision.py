"""The prospective allocation and multiplicity rule (decided 2026-09-02).

**The family.** Under Approach A a model's primary claims are Delta_R(f)
and its F1 companions on every frame that enters the LOCAL arm, and
delta_difficulty(f) on every frame that enters the SPECTRUM arm; each in
both registered configurations. §15's F1 is the registered per-frame
family and keeps its six members. What frame conditioning adds is a
**joint family per (model, configuration)**: every F1 member of every
entering frame, whose simultaneous critical value is the studentised
maximum-modulus over a *topic*-level bootstrap (one draw of the 384
confirmatory topics shared by every frame's members --- the same topic
underlies each frame's block, so the joint variation is the real one).
The decision interval of every primary claim is the **joint** one; the
per-frame F1 interval is reported beside it. A model-level LOCAL claim is
the conjunction over its entering frames (an intersection-union test,
which needs no further adjustment); "supported on at least one frame" is
never emitted.

**The precision rule.** The confirmatory allocation --- blocks per frame,
from {288, 384} --- is the smallest that meets Delta_R's registered
precondition (simultaneous half-width <= 0.05) at the joint family's
Šidák planning constant, k = |F1| x (frames entering LOCAL), under the
registered variance model (§16.1, ``dci1v4.analysis.variance``) at **both**
of: (i) ``REGISTERED_ALTERNATE`` (phi 0.37, rho 0.5, p(1-p) 0.215), the
sensitivity value §16.3 carries; (ii) ``COMPOSED_AT_HALF`` (phi 0.27, rho
0.5, p(1-p) 0.25): the composed cell at 0.5, which is what the hypothesis
predicts and what the pre-freeze anchor at B's *solo* rate understates.
The two explicit bounds (``WORST_CASE``: rho 0; ``ALTERNATE_AT_HALF``:
phi 0.37 and p(1-p) 0.25 together) are reported and gate nothing. The
Šidák value is an upper bound on the bootstrap's maximum-modulus value,
so it is the conservative planning constant, exactly as §16.2 uses it.

384 blocks per frame is every confirmatory topic under every entering
frame --- the ceiling --- and it is what the rule selects for two entering
frames (k = 12) and three (k = 18); at four (k = 24) the alternate row sits
on the line and the realised interval decides (§17.3's non-terminal
``INSUFFICIENT_PRECISION``). No threshold moves.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any

from dci1v4.analysis.variance import variances
from dci1v7.analysis.bootstrap import sidak_critical
from dci1v7.protocol import constants as C

__all__ = ["FAMILY_SIZE_PER_FRAME", "ALLOCATION_MENU", "SCENARIOS",
           "RULE_SCENARIOS", "PRECONDITION", "joint_family_size",
           "project", "choose_allocation", "allocation_record",
           "MULTIPLICITY_RULE", "PRECISION_RULE"]

FAMILY_SIZE_PER_FRAME = len(C.FAMILY_MEMBERS[C.PRIMARY_FAMILY])   # 6
ALLOCATION_MENU = (288, 384)
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
    "the smallest allocation in {288, 384} blocks per frame whose projected "
    "simultaneous half-width for Delta_R at the joint Šidák constant "
    "(k = 6 x LOCAL frames entering) is <= 0.05 under BOTH "
    "REGISTERED_ALTERNATE and COMPOSED_AT_HALF; §16.1's variance form, "
    "§16.2's precondition and §17.3's realised evaluation unchanged")


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


def choose_allocation(n_frames: int) -> dict[str, Any]:
    """The rule, applied: the smallest menu entry passing both rule
    scenarios at the joint constant; the ceiling if none does, with the
    fact recorded."""
    table = {b: {sc: project(blocks=b, n_frames=n_frames, scenario=sc)
                 for sc in SCENARIOS} for b in ALLOCATION_MENU}
    chosen = None
    for b in ALLOCATION_MENU:
        if all(table[b][sc]["meets_precondition_joint"] for sc in RULE_SCENARIOS):
            chosen = b
            break
    at_ceiling_by_default = chosen is None
    if chosen is None:
        chosen = ALLOCATION_MENU[-1]
    return {"n_frames": n_frames, "joint_family_size": joint_family_size(n_frames),
            "menu": list(ALLOCATION_MENU), "rule_scenarios": list(RULE_SCENARIOS),
            "chosen_blocks_per_frame": chosen,
            "rule_met_at_chosen": not at_ceiling_by_default,
            "note": ("no menu entry meets the rule; the ceiling is taken and "
                     "§17.3 evaluates the realised interval"
                     if at_ceiling_by_default else "rule met"),
            "table": {str(b): table[b] for b in ALLOCATION_MENU},
            "precondition": PRECONDITION,
            "multiplicity_rule": MULTIPLICITY_RULE,
            "precision_rule": PRECISION_RULE}


def allocation_record(n_frames_by_model: dict[str, int]) -> dict[str, Any]:
    """The study-level decision: one allocation for every model, chosen at
    the largest entering frame count, so the design is one design."""
    n_max = max([1] + list(n_frames_by_model.values()))
    decision = choose_allocation(n_max)
    return {"frames_entering_local_by_model": dict(n_frames_by_model),
            "decided_at_n_frames": n_max, **decision,
            "per_model": {m: choose_allocation(n)["chosen_blocks_per_frame"]
                          for m, n in n_frames_by_model.items()}}
