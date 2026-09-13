"""§13.2 matches references to A on a quantity that is not comparable to A's.

NOT a stage. A derived analysis over artifacts that already exist: §25's
registered accidental-compliance measurement, read against §13.2's registered
matching criterion. It uses no outcome, no delivery loss and no contrast between
composed cells, so it decides nothing about the effect and could have been run
before any composed cell was generated.

**The observation.** §13.1 says the reference "estimates the counterfactual
'what would composing B with a comparable non-A companion have cost?'", and
§13.2 operationalises "comparable" as raw solo compliance within 0.10 of A's.
§25 separately measures, for every constraint, the rate at which an answer
carrying no constraint at all satisfies it by chance. Netting the second out of
the first gives the share of compliance the instruction actually produced:

    instructed = (solo - chance) / (1 - chance)

**Why the two diverge systematically and not by accident.** A is an exact-count
production constraint: an unconstrained answer essentially never uses a fixed
word exactly n times, so A's chance rate is 0. Every registered family and B are
`S <= q` budgets whose pass sets are downward-closed under prefix, so an
unconstrained answer satisfies them often. Matching on raw solo compliance
therefore equates a companion that is doing all of its own work with one that is
doing little of it, and the size of the gap is a property of the constraint
class rather than of any model.

Usage:
  PYTHONPATH=src python tools/instructed_compliance_v4.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

MATRIX = DCI1 / "reports" / "matrix_screen_v4" / "results.json"
OUT = DCI1 / "reports" / "section_13_2_v4"


def main() -> int:
    results = json.loads(MATRIX.read_text())
    models = {}
    for model, entry in results["models"].items():
        if "unavailable" in entry:
            continue
        levels = entry["compliance"]["pooled_over_orders"]["levels"]
        chance_by = entry["accidental_compliance"]["by_constraint"]
        rows, set_for = {}, entry.get("constraint_set", {})
        for name in ("A", "B", "R1", "R2", "R3"):
            key = f"p_{name}_solo"
            if key not in levels or name not in chance_by:
                continue
            solo = levels[key]["estimate"]
            chance = chance_by[name]
            instructed = ((solo - chance) / (1 - chance)) if chance < 1 else None
            rows[name] = {
                "solo_compliance": solo,
                "accidental_compliance": chance,
                "instructed_compliance": instructed,
                "identity": set_for.get(name),
            }
        a = rows.get("A")
        refs = {k: v for k, v in rows.items() if k.startswith("R")}
        models[model] = {
            "per_companion": rows,
            "A_accidental_is_zero": a is not None and a["accidental_compliance"] == 0.0,
            "references_within_0_10_of_A_on_solo": sorted(
                k for k, v in refs.items()
                if abs(v["solo_compliance"] - a["solo_compliance"]) <= 0.10),
            "references_within_0_10_of_A_on_instructed": sorted(
                k for k, v in refs.items()
                if v["instructed_compliance"] is not None
                and abs(v["instructed_compliance"] - a["instructed_compliance"]) <= 0.10),
            "references_whose_instruction_is_anti_productive": sorted(
                k for k, v in refs.items()
                if v["instructed_compliance"] is not None
                and v["instructed_compliance"] < 0),
        }
    payload = {
        "artifact": ("§13.2's matching criterion read against §25's accidental "
                     "compliance"),
        "classification": ("DERIVED / POST-HOC. Computed from artifacts that "
                           "already exist. Uses no delivery loss, no composed "
                           "contrast and no outcome; decides nothing."),
        "formula": "instructed = (solo - chance) / (1 - chance)",
        "source": {
            "solo and accidental compliance":
                str(MATRIX.relative_to(DCI1)) + " (NON-CONFIRMATORY screen; the "
                "reference sets are the calibration screen's, not Gate 3's)",
            "§13.2": "matching caliper 0.10 on solo compliance",
            "§25": "accidental compliance measured in every cell where the "
                   "constraint is absent, recorded and not fed into admission",
        },
        "models": models,
        "structural_reading": (
            "A's accidental compliance is 0.000 on all four models because an "
            "exact-count production constraint is essentially never satisfied "
            "by an unconstrained answer. Every registered reference family and "
            "B are prefix-closed budgets and are satisfied by chance often. So "
            "the §13.2 caliper equates companions that differ in how much of "
            "their compliance the instruction produced, and the divergence "
            "tracks the production/budget divide rather than the model."),
        "consequence_for_Delta_R": (
            "A reference whose instructed compliance is near zero is, for most "
            "items, not a binding second instruction, so D(B<-R_j) approaches "
            "the cost of composing B with an inert sentence. That biases "
            "Delta_R = D(B<-A) - mean_j D(B<-R_j) UPWARD. The screen's "
            "Delta_R is nevertheless small on every model, so the bias runs "
            "against the positive reading rather than producing it. This is a "
            "direction-of-bias statement, not a correction, and no estimate "
            "here is adjusted for it."),
        "what_it_does_not_do": [
            "it does not adjust, reweight or re-estimate any quantity",
            "it does not propose a new matching criterion",
            "it does not decide any amendment",
            "it says nothing about Gate 3's reference set, which does not exist",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "instructed_compliance.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    for model, block in models.items():
        print(f"{model:24s} solo-matched {block['references_within_0_10_of_A_on_solo']}"
              f"  instructed-matched {block['references_within_0_10_of_A_on_instructed']}"
              f"  anti-productive {block['references_whose_instruction_is_anti_productive']}")
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
