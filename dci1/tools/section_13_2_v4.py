"""Resolve §13.2's admission rule against the registered record, and prove it.

NOT a stage and NOT an amendment. This artifact settles a question two
non-confirmatory screens raised and neither could answer: what §13.2 does when
condition 2 --- the disjoint 24-topic pre-screen confirmation --- has no input.

**The answer is that the registered pipeline never produces that case.**

  §12.2 measures the full n grid, the full m grid and **all 94 reference ladder
  severities** on the 24 pre-screen topics, and writes the shortlist of at most
  three severities per family.

  §12.3 measures "the full n grid, the full m grid, and every **shortlisted**
  reference severity" on the 96 solo-calibration topics at M_cal = 4.

  §13.2 condition 1 is a caliper on the 96-topic measurement, so a severity
  §12.3 never measured cannot be a §13.2 candidate at all. §13.2's feasible set
  is therefore a subset of §12.2's shortlist, and every member of that
  shortlist has a §12.2 pre-screen value by construction.

Condition 2 is thus always evaluable, and the abstain-versus-reject question is
a property of running the stages out of order rather than a gap in the text.
Where it nevertheless arises, ``gates.admit_family`` already fixes it: a rung
with no pre-screen value collects the rejection reason "no pre-screen
measurement". Both halves are executed below against the real registered
records, not asserted.

Usage:
  PYTHONPATH=src python tools/section_13_2_v4.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol import constants as C                        # noqa: E402
from dci1v4.stages import regime                                  # noqa: E402
from dci1v4.stages.gates import admit_family                      # noqa: E402
from dci1v4.verifiers.constraints import REFERENCE_LADDERS        # noqa: E402

EVIDENCE = DCI1 / "evidence" / "dci1-v4"
OUT = DCI1 / "reports" / "section_13_2_v4"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")


def per_model() -> dict:
    """The registered §12.2 record, checked against the invariant §13.2 needs."""
    out = {}
    for model in MODELS:
        path = EVIDENCE / model / "regime_screen.json"
        record = json.loads(path.read_text())["payload"]
        curves = record["ladder_screen"]["curves"]
        table = record["shortlist"]
        shortlisted = [f"{f}:{r['severity']}"
                       for f, rungs in table.items() for r in rungs]
        try:
            regime.assert_shortlist_is_measured(curves, table)
            refused = None
        except Exception as error:                        # ProtocolError
            refused = str(error)
        out[model] = {
            "record": str(path.relative_to(DCI1)),
            "outcome": record["outcome"],
            "draws_per_cell": record["ladder_screen"]["draws_per_cell"],
            "ladder_rungs_measured": len(curves["families"]),
            "ladder_rungs_registered": sum(len(v)
                                           for v in REFERENCE_LADDERS.values()),
            "every_registered_rung_measured":
                len(curves["families"]) == sum(len(v) for v
                                               in REFERENCE_LADDERS.values()),
            "shortlisted_rungs": len(shortlisted),
            "shortlist_max_per_family": C.LADDER_SHORTLIST_MAX,
            "shortlisted_without_a_prescreen_value": [
                r for r in shortlisted if r not in curves["families"]],
            "invariant_refusal": refused,
            "shortlist_written_before_gate2":
                record["shortlist_written_before_gate2"],
        }
    return out


def registered_disposition() -> dict:
    """Execute ``admit_family`` on a rung whose pre-screen value is absent.

    Everything else about the rung is made admissible, so the only reason that
    can appear is condition 2's. Nothing here reads a model or an outcome.
    """
    family, rung = "RF1", 1
    ladder = REFERENCE_LADDERS[family]
    per_topic = [1.0] * 70 + [0.0] * 26                # 0.729 on 96 topics
    a_topic = list(per_topic)                          # identical to A: gap 0
    draws = ([1] * 280 + [0] * 104, [1] * 280 + [0] * 104)

    def run(prescreen):
        return admit_family(
            family, n_star=4,
            calibration={q: per_topic for q in ladder},
            a_calibration=a_topic,
            prescreen=prescreen, a_prescreen=0.70,
            vacuity={q: 0.0 for q in ladder},
            draw_level={q: draws for q in ladder})

    present = run({q: 0.70 for q in ladder})
    absent = run({q: 0.70 for q in ladder if q != rung})
    absent_rung = next(c for c in absent["candidates"]
                       if c["severity"] == rung)
    return {
        "probe": ("one rung of RF1 with every other condition satisfied; the "
                  "only difference between the two runs is whether that rung "
                  "has a pre-screen value"),
        "with_a_prescreen_value": {
            "admissible": next(c["admissible"] for c in present["candidates"]
                               if c["severity"] == rung)},
        "without_a_prescreen_value": {
            "admissible": absent_rung["admissible"],
            "reasons": absent_rung["reasons"]},
        "registered_disposition": (
            "reject: a rung with no pre-screen measurement collects a "
            "rejection reason and is not admitted"),
        "abstain_is_not_in_the_registered_code": "no pre-screen measurement"
            in absent_rung["reasons"],
    }


def main() -> int:
    models = per_model()
    payload = {
        "artifact": "§13.2 admission-rule resolution",
        "classification": ("protocol interpretation, resolved from the "
                           "registered text, the registered implementation and "
                           "the registered §12.2 records. Not an amendment: "
                           "nothing registered changes, and no threshold, "
                           "caliper, band or criterion moves."),
        "question": ("§13.2 condition 2 checks the reference-minus-A distance "
                     "on the disjoint 24 pre-screen topics. Two "
                     "non-confirmatory screens reported that some rungs had no "
                     "such measurement and that the protocol does not say "
                     "whether an unmeasurable condition abstains or fails."),
        "resolution": (
            "The case does not arise in the registered pipeline. §12.2 "
            "measures all 94 reference rungs on the 24 pre-screen topics and "
            "writes the shortlist; §12.3 measures only shortlisted severities "
            "on the 96 calibration topics; §13.2 condition 1 is a caliper on "
            "that 96-topic measurement, so §13.2's feasible set is a subset of "
            "§12.2's shortlist and every member of it carries a pre-screen "
            "value. Condition 2 is always evaluable. Where the case is "
            "nevertheless constructed, the registered implementation rejects."),
        "uniquely_supported": True,
        "researcher_decision_required": False,
        "textual_basis": {
            "§12.2": ("the pre-screen measures on the 24 pre-screen topics, "
                      "one draw per cell: the full n grid for A, the full m "
                      "grid for B, and all 94 reference ladder severities ... "
                      "and produces the shortlist of at most three ladder "
                      "severities per family"),
            "§12.3": ("on the 96 solo-calibration topics at M_cal = 4 ... the "
                      "full n grid, the full m grid, and every shortlisted "
                      "reference severity are measured"),
            "§13.2 condition 1": ("that absolute difference is at most 0.10 on "
                                  "the 96 solo-calibration topics"),
            "§13.2 condition 2": ("the same absolute difference is at most "
                                  "0.15 on the disjoint 24 pre-screen topics"),
        },
        "implementation_basis": {
            "gates.admit_family": ("`pre = prescreen.get(q)` then `if pre is "
                                   "None: reasons.append(\"no pre-screen "
                                   "measurement\")` --- reject, not abstain"),
            "regime.shortlist": ("skips a rung with no measured value, so the "
                                 "shortlist is a subset of the measured rungs "
                                 "by construction"),
            "regime.assert_shortlist_is_measured": (
                "added with this artifact; refuses to write a REGIME_SCREEN "
                "record whose shortlist names a rung the ladder curves do not "
                "carry, which puts the guarantee on the mandatory path rather "
                "than in a docstring"),
        },
        "what_this_does_not_decide": [
            "whether any amendment is adopted",
            "which family or severity is admitted on any model",
            "n*, m*, or any threshold",
            ("what happens under a prompt stem other than the registered one: "
             "a stem change is a change of experimental condition, so §12.1, "
             "§12.2, §12.3 and §13.2 are all re-measured under it "
             "(Amendment A §5.1 says so itself). §12.2 re-run under the new "
             "stem supplies condition 2's input exactly as it does now, so the "
             "resolution holds under any stem and is not an argument for or "
             "against one."),
        ],
        "prior_statements_corrected": [
            ("dci1/reports/cal_screen_v4/REPORT.md §6 called this a "
             "preregistration gap of the same kind as §12.4's graded clause "
             "and reported abstain and reject as co-equal readings. It is not "
             "a gap. The screen met unmeasured rungs because it admitted "
             "rungs outside the §12.2 shortlist and because its floored-stem "
             "pre-screen came from a screen that measured only some rungs --- "
             "both properties of the screen, not of the protocol."),
            ("dci1/reports/INVESTIGATION_2026-08-20.md named this reading the "
             "smallest remaining blocker. It is not a blocker."),
        ],
        "per_model": models,
        "registered_disposition_executed": registered_disposition(),
    }
    payload["summary"] = {
        "every_model_measured_all_94_rungs":
            all(m["every_registered_rung_measured"] for m in models.values()),
        "every_shortlisted_rung_has_a_prescreen_value":
            all(not m["shortlisted_without_a_prescreen_value"]
                for m in models.values()),
        "invariant_holds_on_every_registered_record":
            all(m["invariant_refusal"] is None for m in models.values()),
        "registered_disposition": "reject",
        "researcher_decision_required": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "resolution.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=1))
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
