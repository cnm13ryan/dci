"""A plan-only dry run of the whole v4r3 chain. Generates nothing.

It walks §12.2 -> §12.3 -> Gate 2 -> Gate 3 -> the cell plan -> the
difficulty fit -> the bootstrap -> §17.6's joint reading on **synthetic**
calibration and confirmatory quantities, and writes one machine-readable
artifact. Its purpose is to demonstrate that the registered chain is
executable end to end and that every count the preregistration states is the
count the code produces -- not to produce evidence about anything.

Every number it consumes is fabricated in this file. Nothing it writes is
admissible as evidence and the artifact says so on its face.

Run: ``python tools/dry_run_v4r3.py`` from ``dci1/``.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dci1v4r3 import CLASSIFICATION, STUDY_ID                     # noqa: E402
from dci1v4r3.analysis import claims as CL                        # noqa: E402
from dci1v4r3.analysis import spectrum as SP                      # noqa: E402
from dci1v4r3.analysis.claims import Interval                     # noqa: E402
from dci1v4r3.design import cells as D                            # noqa: E402
from dci1v4r3.protocol import constants as C                      # noqa: E402
from dci1v4r3.stages import freeze as F                           # noqa: E402
from dci1v4r3.stages import gates as G                            # noqa: E402
from dci1v4r3.stages import regime as R                           # noqa: E402
from dci1v4r3.stages import selection as S                        # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash               # noqa: E402
from dci1v4r3.verifiers.constraints import (                      # noqa: E402
    FAMILIES, LADDERS, focal_severities,
)

DISCLAIMER = ("SYNTHETIC. Every rate in this file is fabricated by "
              "tools/dry_run_v4r3.py to exercise the registered chain. It is "
              "not evidence about any model, and no v4r3 estimand is "
              "identified by it.")

OUT = REPO / "reports" / "v4r3_dry_run.json"


@dataclass(frozen=True)
class Block:
    block_id: str
    index: int
    topic_id: str


def synthetic_prescreen(rng: random.Random) -> list[dict]:
    """§12.2's 149 measured instances, with plausible-shaped curves."""
    rows = []
    rows.append({"kind": "UNCONSTRAINED", "severity": 0, "solo": 0.0,
                 "chance": 0.0})
    for n in C.TARGET_GRID:
        rows.append({"kind": "A", "severity": n,
                     "solo": max(0.05, 0.90 - 0.09 * n), "chance": 0.0})
    for m in focal_severities(extended=True):
        rows.append({"kind": "B", "severity": m,
                     "solo": min(0.99, 0.20 + 0.13 * (m - 6)),
                     "chance": min(0.95, 0.05 + 0.16 * (m - 6))})
    for family, ladder in LADDERS.items():
        # a monotone curve across the ladder, with a family-specific chance
        # rate: count budgets are prefix-closed and satisfied often by
        # accident, rate budgets much less so, lower bounds hardly ever.
        chance = {"count_budget": 0.45, "rate_budget": 0.12,
                  "count_lower_bound": 0.04,
                  "rate_lower_bound": 0.08}[FAMILIES[family].form]
        for index, q in enumerate(ladder):
            share = index / max(1, len(ladder) - 1)
            solo = chance + (0.97 - chance) * share
            rows.append({"kind": family, "severity": q,
                         "solo": round(solo + rng.gauss(0, 0.01), 4),
                         "chance": chance})
    return rows


def to_calibration(table: dict, iota_a_prescreen: float,
                   shortlist: dict) -> list[S.CalibrationRow]:
    """§12.3's 96-topic re-measurement of the shortlist, synthesised."""
    rows = []
    for family, rungs in shortlist.items():
        for q in rungs:
            entry = table[f"{family}:{q}"]
            rows.append(dict(
                kind=family, severity=q,
                solo_compliance=entry["solo"],
                chance_compliance=entry["chance"], solo_vacuity=0.01,
                prescreen_solo_compliance=entry["solo"],
                prescreen_chance_compliance=entry["chance"],
                wording_within_caliper=True, witnesses_pass=True))
    return S.load_calibration_table(rows)


def synthetic_confirmatory(slot_map: dict, iota_a: float, rng: random.Random,
                           *, excess: float) -> SP.SpectrumInput:
    """Per-block cell means for the nine fit points and the A+B cell."""
    blocks = tuple(f"blk{i:04d}" for i in range(C.N_BLOCKS))
    fit_slots = {s: f for s, (f, _) in slot_map.items()
                 if s not in ("A", "B", C.CLASS_SLOT)}
    b_solo = [0.79 + rng.gauss(0, 0.03) for _ in blocks]
    companion_solo, companion_chance, b_with = {}, {}, {}
    for slot, family in fit_slots.items():
        chance = {"count_budget": 0.45, "rate_budget": 0.12,
                  "count_lower_bound": 0.04,
                  "rate_lower_bound": 0.08}[FAMILIES[family].form]
        # the design's own targets: the core rung at iota_a, the two spectrum
        # rungs a registered offset away on each side.
        target = iota_a + (-C.SPECTRUM_OFFSET if slot.endswith("-") else
                           C.SPECTRUM_OFFSET if slot.endswith("+") else 0.0)
        solo = chance + target * (1 - chance)
        # a weak difficulty relation, of the order the screens observed
        loss = 0.02 - 0.08 * (target - iota_a)
        companion_chance[slot] = [chance for _ in blocks]
        companion_solo[slot] = [solo + rng.gauss(0, 0.02) for _ in blocks]
        b_with[slot] = [s - loss + rng.gauss(0, 0.03) for s in b_solo]
    b_with["A"] = [s - (0.02 + excess) + rng.gauss(0, 0.03) for s in b_solo]
    return SP.SpectrumInput(
        blocks=blocks, family_of=fit_slots, b_solo=b_solo, b_with=b_with,
        companion_solo=companion_solo, companion_chance=companion_chance,
        a_solo=[iota_a + rng.gauss(0, 0.03) for _ in blocks],
        a_chance=[0.0 for _ in blocks])


def main() -> dict:
    rng = random.Random(20260821)
    out: dict = {"classification": CLASSIFICATION, "study_id": STUDY_ID,
                 "disclaimer": DISCLAIMER, "generations": 0,
                 "canonical_verifier_hash": verifier_source_hash()}

    # ---- §12.2 the dense ladder screen
    prescreen = synthetic_prescreen(rng)
    table = R.prescreen_difficulty_table(
        [r for r in prescreen if r["kind"] != "UNCONSTRAINED"])
    a_curve_pre = {r["severity"]: r["solo"] for r in prescreen
                   if r["kind"] == "A"}
    n_star_pre = G.select_severity(a_curve_pre, band=C.TARGET_BAND,
                                   aim=C.TARGET_AIM)
    iota_a_pre = a_curve_pre[n_star_pre]          # A's chance rate is 0.000
    out["s12_2"] = {"cells_per_topic": R.ladder_screen_cell_count(),
                    "generations": R.ladder_screen_cell_count() * C.N_PRESCREEN,
                    "instances_measured": len(table),
                    "iota_a_prescreen": iota_a_pre}

    # ---- §12.3 the shortlist and the calibration measurement
    short = R.shortlist(table, iota_a=iota_a_pre)
    R.assert_shortlist_is_measured(table, short)
    n_ref = sum(1 for f in short if FAMILIES[f].role == "reference")
    n_cls = sum(1 for f in short if FAMILIES[f].role == "class_control")
    cells = R.solo_calibration_cell_count(
        n_reference_families=n_ref, n_class_families=n_cls,
        rungs_per_reference=C.SHORTLIST_MAX_PER_REFERENCE_FAMILY,
        rungs_per_class=C.SHORTLIST_MAX_PER_CLASS_FAMILY)
    out["s12_3"] = {"shortlist": {f: list(r) for f, r in short.items()},
                    "reference_families": n_ref, "class_families": n_cls,
                    "cells": cells,
                    "generations": cells * C.N_SOLO * C.M_CAL}

    # ---- Gate 2
    b_pre = {r["severity"]: r["solo"] for r in prescreen if r["kind"] == "B"}
    gate2 = G.gate2_payload(
        a_curve=a_curve_pre,
        focal_registered_curve={m: b_pre[m] for m in C.FOCAL_GRID},
        focal_extended_curve=None, b_solo_vacuity=0.03,
        graded_distributions={"A": [0.7] * 60 + [0.2] * 40,
                              "B": [1.0] * 79 + [0.97] * 21},
        a_chance=0.0, b_chance=0.31)
    out["gate2"] = {k: gate2[k] for k in
                    ("outcome", "n_star", "m_star", "iota_a", "iota_b",
                     "graded_clause_reading")}
    iota_a = gate2["iota_a"]

    # ---- Gate 3
    rows = to_calibration(table, iota_a, short)
    result = S.select_all(rows, iota_a=iota_a, prescreen_iota_a=iota_a_pre,
                          solo_compliance_a=gate2["a_solo_compliance"])
    gate3 = G.gate3_payload(result)
    out["gate3"] = {k: gate3[k] for k in
                    ("design", "cells_per_block", "class_arm",
                     "core_references", "spectrum", "identification_statuses")}

    if gate3["design"] != "full":
        out["stopped_at"] = ("GATE_3: fewer than three families supply a "
                             "straddling triple; the reduced design of §8.6 "
                             "runs and L3 is withheld")
        OUT.write_text(json.dumps(out, indent=2, default=str))
        return out

    # ---- the cell plan
    blocks = [Block(f"blk{i:04d}", i, f"t{i:04d}") for i in range(C.N_BLOCKS)]
    plan = D.design_cells(blocks, class_arm=gate3["class_arm"],
                          assert_allocation_over=C.N_BLOCKS)
    out["cell_plan"] = {
        "cells_per_block": len(plan) // C.N_BLOCKS,
        "blocks": C.N_BLOCKS, "M": C.M_DRAWS,
        "generations_per_model": len(plan) * C.M_DRAWS,
        "generations_four_models": len(plan) * C.M_DRAWS * 4}

    # ---- the estimand, its support, and the refitting bootstrap
    slot_map = {**result.slot_map(), "A": ("A", gate2["n_star"]),
                "B": ("B", gate2["m_star"])}
    data = synthetic_confirmatory(slot_map, iota_a, rng, excess=0.09)
    SP.assert_algebraic_forms_agree(data)
    boot = SP.bootstrap_spectrum(data, resamples=400, seed=4242)
    out["spectrum"] = {
        "fit_points": C.N_FIT_POINTS,
        "delta_difficulty": boot["estimate"],
        "bootstrap_se": boot["bootstrap_se"],
        "ci95_percentile": boot["ci95_percentile"],
        "slope": boot["slope_estimate"],
        "support_holds": boot["support"]["holds"],
        "support_bootstrap_share": boot["support_bootstrap_share"],
        "refit_per_replicate": boot["refit_per_replicate"],
        "identification_statuses": boot["identification_statuses"]}

    # ---- §17.6's joint reading, on synthetic intervals
    half = boot["bootstrap_se"] * C.SIDAK_K6
    reading = CL.joint_reading(
        delta_r=Interval("Delta_R", 0.06, 0.02, 0.10),
        delta_difficulty=Interval("delta_difficulty", boot["estimate"],
                                  boot["estimate"] - half,
                                  boot["estimate"] + half),
        xi=Interval("Xi", -0.02, -0.06, 0.02), support=boot["support"])
    out["joint_reading"] = {k: reading[k] for k in
                            ("levels", "markers", "identification_statuses",
                             "row")}
    out["joint_reading"]["wording"] = reading.get("wording")

    # ---- Gate 5: what is still missing
    record = F.build_freeze_record(
        protocol_version="4.0r3", cell_plan=out["cell_plan"],
        difficulty_coordinate=C.DIFFICULTY_COORDINATE,
        spectrum_offset=C.SPECTRUM_OFFSET,
        spectrum_severities=[e["slot"] for e in result.spectrum],
        core_references=[e["slot"] for e in result.core["core_references"]],
        graded_clause_reading=C.GRADED_CLAUSE_READING,
        stem_sentence=C.STEM_SENTENCE)
    status = F.check_completeness(record, decisions={})
    out["gate5"] = {"can_freeze": status["can_freeze"],
                    "missing_fields": status["missing_fields"],
                    "unclosed_decisions": status["unclosed_decisions"]}

    OUT.write_text(json.dumps(out, indent=2, default=str))
    return out


if __name__ == "__main__":
    result = main()
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("gate3",)}, indent=2, default=str)[:4000])
    print(f"\nwritten to {OUT}")
