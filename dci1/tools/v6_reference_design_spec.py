"""Emit the v6 reference-design specification **from the registered code**.

§18 stage 1 binds this file by hash, so it is the machine-readable statement
of what the study's reference-validity rule is. v5's equivalent was written by
hand, which means it could disagree with the implementation and nothing would
notice. This one is derived: every threshold, band, component, tier rule and
support requirement is read out of `dci1v6.protocol.constants`,
`dci1v6.stages.validity`, `dci1v6.stages.support` and
`dci1v6.verifiers.constraints`, so a spec that disagrees with the code is not
expressible.

**It emits a DRAFT.** `_status` is `DRAFT_NOT_ADOPTED` and
`manifest.assert_documents_adopted` refuses a registration whose spec says so.
Adopting it is a researcher act: it means the design below is the one the
study commits to, and neither this tool nor any other code may make that
claim on the researcher's behalf.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v6 import PREREGISTRATION, REFERENCE_DESIGN_SPEC   # noqa: E402
from dci1v6.design import cells as design_cells             # noqa: E402
from dci1v6.protocol import constants as C                  # noqa: E402
from dci1v6.protocol import decisions                       # noqa: E402
from dci1v6.stages import composed_probe, support, validity  # noqa: E402
from dci1v6.verifiers import constraints as K               # noqa: E402

OUT = DCI1.parent / REFERENCE_DESIGN_SPEC
DRAFT = "DRAFT_NOT_ADOPTED"


def _library() -> dict[str, Any]:
    return {
        "sizes": K.assert_library_sizes(),
        "selectable_families": list(K.SELECTABLE_FAMILY_IDS),
        "probe_only_families": {
            kind: {"statistic": K.FAMILIES[kind].statistic_id,
                   "form": K.FAMILIES[kind].form,
                   "feature_group": K.FAMILIES[kind].feature_group,
                   "ladder": list(K.FAMILIES[kind].ladder),
                   "rule": K.FAMILIES[kind].rule,
                   "selectable": False}
            for kind in K.PROBE_ONLY_FAMILY_IDS},
        "probe_only_is": (
            "§34 D24. A registered instrument that can never be selected: "
            "scored by the same verifiers, hashed into the same "
            "verifier_source_hash and certified by the same Gate-1 suites, "
            "and refused by `assert_selectable` everywhere a candidate is "
            "carried, qualified, calibrated or bound. It reuses a registered "
            "counted statistic under a form no selectable family carries, so "
            "FEATURE_GROUP_IDS --- whose index `selection.group_key` reads as "
            "a reference-selection tie-break --- does not move."),
        "tiers": {"tier_1": list(K.TIER1_FAMILY_IDS),
                  "tier_2": list(K.TIER2_FAMILY_IDS),
                  "tier_3": list(K.TIER3_FAMILY_IDS)},
        "forms": list(K.FORMS),
        "feature_groups": list(K.FEATURE_GROUP_IDS),
        "statistics": list(K.STATISTIC_IDS),
    }


def _validity() -> dict[str, Any]:
    return {
        "_form": ("V(R) = " + " AND ".join(C.VALIDITY_COMPONENTS)
                  + ". Evaluated lexicographically in that order; the first "
                    "failing component is the recorded rejection reason and "
                    "later components are not evaluated."),
        "components": list(C.VALIDITY_COMPONENTS),
        "gate_2_5_components": list(validity.GATE_2_5_COMPONENTS),
        "headroom_band": list(C.HEADROOM_BAND),
        "headroom_is_applied_to": (
            "the 95% Wilson interval on the candidate's own topic count, not "
            "to the point estimate, so an imprecisely measured candidate "
            "cannot sit on the boundary. §13.14's [0.05, 0.95] contracted by "
            "0.05 on each side."),
        "composed_headroom_band": list(C.COMPOSED_HEADROOM_BAND),
        "instruction_lift_min": C.INSTRUCTION_LIFT_MIN,
        "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
        "chance_max": C.CHANCE_MAX,
        "stability_bootstrap_resamples": C.STABILITY_BOOTSTRAP_RESAMPLES,
        "components_documented_at": validity.__name__,
    }


def _support() -> dict[str, Any]:
    return {
        "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
        "n_core_feature_groups": C.N_CORE_FEATURE_GROUPS,
        "evaluated_by": f"{support.__name__}.evaluate_support",
        "coverage_conditions": list(C.COVERAGE_CONDITIONS),
        "coverage_decisive": list(C.COVERAGE_DECISIVE),
        "coverage_thresholds": {
            name: getattr(C, name) for name in sorted(dir(C))
            if name.startswith("COVERAGE_")
            and isinstance(getattr(C, name), (int, float))},
        "calibrated_iota_a_rule": (
            "§12.6's coverage criterion is re-evaluated at Gate 3A on the "
            "CALIBRATION basis, where iota(R), the difficulty coordinate, the "
            "solo vacuity and iota_A all come from the same 192 topics at "
            "M_CAL draws. A decisive condition lost there is a §13.15 "
            "design-time failure under §34 D6. The pre-screen value that "
            "§12.6 spent its expansion rounds at is recorded beside it and "
            "gates nothing."),
    }


def _probe() -> dict[str, Any]:
    slots = composed_probe.probe_slots(len(K.PROBE_ONLY_FAMILY_IDS) or 3)
    coverage = composed_probe.probe_class_coverage(slots)
    return {
        "stage": C.STAGE_GATE2_75,
        "runs_between": [C.STAGE_GATE2_5, C.STAGE_GATE3A],
        "gate4_exposure_classes": {
            name: {"gate4_cells": entry["gate4_cells"],
                   "gate4_entries": entry["gate4_entries"],
                   "probe_cells": entry["probe_cells"],
                   "determinate": entry["determinate"]}
            for name, entry in sorted(coverage.items())},
        "cell_types": [cid for cid, _a, _s
                       in composed_probe.probe_cell_types(slots)],
        "shared_with_gate2": list(composed_probe.SHARED_WITH_GATE2),
        "determinate_slots": list(composed_probe.DETERMINATE_SLOTS),
        "n_determinate_entries": composed_probe.N_DETERMINATE_ENTRIES,
        "residual_sd": composed_probe.RESIDUAL_SD,
        "residual_sd_is": (
            "half the measured calibration_a-vs-calibration_b residual. §6.2 "
            "cuts calibration_a and the composed set from one seeded per-area "
            "shuffle so they are exchangeable; §34 D3's calibration_b is "
            "newly authored and is not, and supplies half a pooled probe's "
            "topics. reports/dci1v6/precision_design.json carries it."),
        "verdict_rule": {
            "determinate_entry":
                "passes iff its projected Gate-4 interval lies inside "
                "§13.14's registered band. Half-width "
                "z * sqrt(s2/N_COMPOSED + s2/n_probe + residual_sd^2), with "
                "s2 the entry's own between-topic variance measured in this "
                "stage and z at §13.4's registered 95%.",
            "standin_dependent_entry":
                "passes iff the measured value lies inside §13.14's "
                "registered band, with NO margin. A failure is a real "
                "composed cell of real instruments leaving the band; a pass "
                "certifies nothing about the reference that replaces the "
                "stand-in.",
            "severity": "passes iff every entry passes its own test",
            "familywise_reading":
                "computed and recorded per determinate entry and read by "
                "nothing, because §13.14's verdict is a conjunction and the "
                "conservative reading belongs on the artifact.",
        },
        "standin_placement":
            "each stand-in is probed at the severity of its own solo ladder "
            "nearest Gate 2's measured iota_A, inside §13.4's band, because "
            "§13.8 matches a reference's iota(R) to iota_A. iota_A does not "
            "depend on m*, so re-selecting the operating point never moves a "
            "stand-in.",
        "reselection": "one, by §12.3's registered focal rule run unchanged "
                       "over Gate 2's own solo B curve restricted to the "
                       "severities the probe admitted",
        "terminal_status": composed_probe.COMPOSED_HEADROOM_UNREACHABLE,
        "scope_limits": list(composed_probe.PROBE_SCOPE_LIMITS),
        "declared_refusals": dict(composed_probe.PROBE_DECLARED_REFUSALS),
    }


def _design() -> dict[str, Any]:
    return {
        "arms": list(C.ARMS),
        "slots": list(C.REGISTERED_SLOT_ORDER),
        "n_cells_by_arm": dict(C.N_CELLS_BY_ARM),
        "cells_full_arm_set": design_cells.n_cells_for(C.ARMS),
        "gate4_entries_full_arm_set": sum(
            len(t.slots) for t in design_cells.cell_types(C.ARMS)),
        "topic_sets": dict(C.SET_SIZES),
        "m_cal": C.M_CAL,
        "focal_band": list(C.FOCAL_BAND),
        "focal_aim": C.FOCAL_AIM,
        "focal_grid": list(C.FOCAL_GRID),
        "focal_extension": list(C.FOCAL_EXTENSION),
        "target_grid": list(C.TARGET_GRID),
    }


def main() -> None:
    payload = {
        "_what_this_is":
            "The frozen reference-validity and composed-headroom rule for "
            "DCI-1 v6, in machine-readable form, DERIVED from the registered "
            "implementation by tools/v6_reference_design_spec.py rather than "
            "transcribed. A spec that disagrees with the code is not "
            "expressible here.",
        "_status": DRAFT,
        "_status_means":
            "NOT ADOPTED. No v6 registration exists, no v6 stage has run, and "
            "all twenty-six §34 decisions are UNRESOLVED because "
            "reports/dci1v6/researcher_decisions.json does not exist and no "
            "code may create it. `manifest.assert_documents_adopted` refuses "
            "a registration while this field says DRAFT_NOT_ADOPTED. Adopting "
            "it is a researcher act.",
        "_provenance": {
            "protocol": PREREGISTRATION,
            "predecessor_protocol": "user-notes/DCI1_preregistration_v5.md",
            "producer": "dci1/tools/v6_reference_design_spec.py",
            "development_evidence": [
                "dci1/reports/dci1v6/readiness_evidence.json",
                "dci1/reports/dci1v6/precision_design.json",
                "dci1/reports/dci1v6/expansion_dryrun.json",
                "dci1/reports/dci1v6/reference_feasibility.json"],
            "overfitting_declaration":
                "Two quantities here are fitted to closed v5 observations and "
                "are labelled as such: composed_probe.RESIDUAL_SD, and the "
                "choice to leave §13.14 as registered. Retrospective "
                "behaviour on v5 is NOT prospective validation; v6 is the "
                "prospective test and may not claim these generalise (§30).",
        },
        "design": _design(),
        "candidate_library": _library(),
        "validity_components": _validity(),
        "support_requirements": _support(),
        "composed_probe": _probe(),
        "open_decisions": {
            "count": len(decisions.open_decisions()),
            "ids": list(decisions.open_decisions()),
            "why": "closing one is a researcher act recorded at "
                   f"{decisions.RECORD_RELPATH}, and no code may write it",
        },
        "what_this_spec_does_not_decide": [
            "any §34 decision; every one of them is still open",
            "the value of §34 D23's residual allowance, whose derivation is "
            "0.0 and whose closure is the researcher's",
            "whether §6.2's composed set is enlarged (§34 D21): the "
            "sequestered eighth is not materialised in this repository, so "
            "that branch is an act of authoring topics",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(f"{OUT}  ({payload['_status']})")


if __name__ == "__main__":
    main()
