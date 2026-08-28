"""Emit the v7 reference-design specification **from the registered code**.

§18 stage 1 binds this file by hash, so it is the machine-readable statement
of what the study's reference-validity rule is. v5's equivalent was written by
hand, which means it could disagree with the implementation and nothing would
notice. This one is derived: every threshold, band, component, tier rule and
support requirement is read out of `dci1v7.protocol.constants`,
`dci1v7.stages.validity`, `dci1v7.stages.support` and
`dci1v7.verifiers.constraints`, so a spec that disagrees with the code is not
expressible.

**Its `_status` is DERIVED, never chosen here.** It reads `ADOPTED` only when
three researcher acts are all on the record: the preregistration's own
`status:` line says `ADOPTED`, `researcher_decisions.json` closes every one of
§34's twenty-six decisions, and no §33 open item that blocks the manifest is
still unresolved. Otherwise it says `DRAFT_NOT_ADOPTED` and
`manifest.assert_documents_adopted` refuses a registration. This tool makes no
adoption claim on the researcher's behalf --- it reports what the researcher
has and has not done, from the files where they did it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v7 import PREREGISTRATION, REFERENCE_DESIGN_SPEC   # noqa: E402
from dci1v7.design import cells as design_cells             # noqa: E402
from dci1v7.protocol import constants as C                  # noqa: E402
from dci1v7.protocol import decisions, identification       # noqa: E402
from dci1v7.run import prefreeze_run                        # noqa: E402
from dci1v7.stages import composed_probe, support, validity  # noqa: E402
from dci1v7.verifiers import constraints as K               # noqa: E402

OUT = DCI1.parent / REFERENCE_DESIGN_SPEC
DRAFT = "DRAFT_NOT_ADOPTED"
ADOPTED = "ADOPTED"


def _adoption() -> dict[str, Any]:
    """The three researcher acts this spec's status is derived from.

    Read rather than asserted, and each named separately, so that a spec
    declaring itself adopted says exactly what it is reporting.
    """
    from dci1v7.protocol import open_items

    prereg = DCI1.parent / PREREGISTRATION
    declared = "missing"
    if prereg.exists():
        lines = [ln.strip() for ln in prereg.read_text().splitlines()]
        declared = next((ln.split(":", 1)[1].strip() for ln in lines
                         if ln.lower().startswith("status:")), "none")
    still_open = list(decisions.open_decisions())
    blocking = list(open_items.blocking_items())
    return {
        "preregistration_status": declared,
        "preregistration": PREREGISTRATION,
        "decision_record": decisions.RECORD_RELPATH,
        "decision_record_present": decisions.record_payload()["present"],
        "n_decisions": len(decisions.DECISIONS),
        "open_decisions": still_open,
        "blocking_open_items": blocking,
        "adopted": (declared == ADOPTED and not still_open and not blocking),
    }


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
            "FEATURE_GROUP_IDS --- whose index `selection._group_order` reads "
            "as a reference-selection tie-break --- does not move."),
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
            "cannot sit on the boundary. The (0.05, 0.95) proximity band "
            "contracted by 0.05 on each side; the value is unchanged from "
            "v5 and the band it was derived from no longer gates."),
        "composed_proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
        "composed_proximity_band_is": (
            "DESCRIPTIVE (v7 A1): it classifies a composed cell as near a "
            "floor or ceiling on a record and anchors the §13.4/§13.6 "
            "derivations; no stage terminates on it"),
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
        # v7 A7: the expansion loop stops on all six; the core arm is gated
        # by C1/C3/C5/C6 and the spectrum arm by C2/C4. `coverage_decisive`
        # (v5/v6: C1-C6 for both arms at once) is withdrawn from this spec.
        "coverage_expansion_conditions":
            list(C.COVERAGE_EXPANSION_CONDITIONS),
        "coverage_core_conditions": list(C.COVERAGE_CORE_CONDITIONS),
        "coverage_spectrum_conditions": list(C.COVERAGE_SPECTRUM_CONDITIONS),
        "coverage_arm_conditions": {k: list(v) for k, v in
                                    C.COVERAGE_ARM_CONDITIONS.items()},
        "coverage_thresholds": {
            name: getattr(C, name) for name in sorted(dir(C))
            if name.startswith("COVERAGE_")
            and isinstance(getattr(C, name), (int, float))},
        "calibrated_iota_a_rule": (
            "§12.6's coverage criterion is re-evaluated at Gate 3A on the "
            "CALIBRATION basis, where iota(R), the difficulty coordinate, the "
            "solo vacuity and iota_A all come from the same 192 topics at "
            "M_CAL draws, and that reading gates. A core condition (C1, C3, "
            "C5, C6) lost there is a §13.15 design-time failure under §34 D6 "
            "(REFERENCE_SUPPORT_NOT_IDENTIFIED; core and spectrum arms "
            "dropped); a spectrum condition (C2, C4) lost there with the core "
            "conditions met is DIFFICULTY_SUPPORT_NOT_IDENTIFIED (spectrum "
            "arm dropped, core arm retained when §13.8, §13.7 and §13.15 "
            "hold). The pre-screen value that §12.6 spent its expansion rounds "
            "at is recorded beside it and gates nothing: on 24 topics at one "
            "draw a ladder's apparent span is inflated by noise, rungs above "
            "0.90 leave the band at calibration, and §12.7's Tier-3 cap keeps "
            "Tier-3 ladders from spanning 0.40 there, so a pre-screen pass "
            "never overrides a calibrated failure (v7 A7)."),
        "unmet_disposition": {
            "decision": "D6", "value": decisions.value_of("D6"),
            "terminal": False, "replication_continues": True,
            "reference_support_not_identified": {
                "drops": ["core", "spectrum"],
                "not_identified_members": len(
                    identification.AFFECTED_ESTIMANDS),
                "irreversible": True},
            "difficulty_support_not_identified_at_design_time": {
                "drops": ["spectrum"],
                "not_identified_members": len(
                    identification.SPECTRUM_ESTIMANDS),
                "irreversible": True},
            "base_arm_always_identified": list(
                identification.BASE_ARM_ESTIMANDS),
            "prefreeze_invariant": (
                "v7 A6: every estimand entering confirmatory generation has "
                "the support it requires, every unsupported estimand and arm "
                "has already been removed, and the frozen design agrees "
                "exactly with Gate 3C's identification state; the audit does "
                "not require support_met"),
            "prefreeze_checks": [cid for cid, _w, _b in
                                 prefreeze_run.ARTIFACT_CHECKS
                                 if cid in ("support_recorded",
                                            "d6_disposition_registered",
                                            "arms_match_identification",
                                            "no_rehabilitation_path",
                                            "freeze_fields_explained")],
        },
    }


def _probe() -> dict[str, Any]:
    slots = composed_probe.probe_slots(len(K.PROBE_ONLY_FAMILY_IDS) or 3)
    coverage = composed_probe.probe_class_coverage(slots)
    return {
        "stage": C.STAGE_GATE2_75,
        "runs_between": [C.STAGE_GATE2_5, C.STAGE_GATE3A],
        "outcomes": [composed_probe.PROBE_OUTCOME],
        "terminal_statuses": [],
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
        "contrasts_recorded": {
            group: list(members)
            for group, members in composed_probe.DETERMINATE_CONTRASTS.items()},
        "record_rule": {
            "what": "the paired per-topic contrasts D(B<-A), D(A<-B) and "
                    "Lambda in each configuration and Ord_A, Ord_B, "
                    "Ord_Lambda across them, formed from the six determinate "
                    "entries on the calibration topics; a topic bootstrap "
                    "with one index draw per replicate; the v7 §13.14 "
                    "boundary reading of each; and the projected "
                    "confirmatory half-width of each at the registered M "
                    "and block count",
            "decides": "nothing. The record is labelled "
                       "PROJECTION_NOT_REGISTERED_FOR_INFERENCE and no rule "
                       "reads it",
            "standin_dependent_entries":
                "classified for proximity to the descriptive band and "
                "recorded under `standin_proximity`; they enter no contrast "
                "and decide nothing",
        },
        "standin_placement":
            "each stand-in is probed at the severity of its own solo ladder "
            "nearest Gate 2's measured iota_A, inside §13.4's band, because "
            "§13.8 matches a reference's iota(R) to iota_A. iota_A does not "
            "depend on m*, so the companion a probed cell carries is fixed "
            "by a quantity the operating point cannot move. A stand-in with "
            "no admissible severity is STANDIN_UNPLACEABLE (v6 A17).",
        "operating_point": {
            "chosen_at": C.STAGE_GATE2,
            "chosen_by": "§12.3's registered focal rule on B's solo curve",
            "frozen": True,
            "severities_probed_here": "m* and no other",
            "reselections_permitted": 0,
            "what_this_stage_decides": "nothing (v7 A1)",
            "what_it_does_not_decide":
                "WHERE Delta_j and Delta_R are measured, and WHETHER the "
                "replication continues. A feasibility measurement that could "
                "choose the operating point would be a selection rule fed "
                "by composed outcomes (v6 A13); a measurement that could end "
                "the replication on a marginal composed rate would be "
                "terminating on a property of one arm of a paired contrast "
                "(v7 A1).",
            "enforced_by": [
                "dci1v7.stages.composed_probe.probe_disposition refuses a "
                "probe table carrying any severity but m*",
                "dci1v7.stages.composed_probe.assert_m_star_unmoved, on the "
                "producing path before the record is written",
                "dci1v7.run.gates_run.effective_m_star, on every downstream "
                "read of the operating point",
            ],
        },
        "scope_limits": list(composed_probe.PROBE_SCOPE_LIMITS),
        "declared_refusals": dict(composed_probe.PROBE_DECLARED_REFUSALS),
    }


def _contrast() -> dict[str, Any]:
    """v7 §13.14: the composed-contrast rule, from the constants it reads."""
    from dci1v7.analysis import boundary
    from dci1v7.stages import composed_contrast

    return {
        "section": "v7 §13.14",
        "module": boundary.__name__,
        "gate4_stage": C.STAGE_GATE4,
        "gate4_outcomes": [composed_contrast.GATE4_OUTCOME],
        "terminal_statuses_withdrawn": sorted(
            s for s in C.WITHDRAWN_STATUSES if "HEADROOM" in s),
        "withdrawn_reasons": {
            s: C.WITHDRAWN_STATUS_REASONS[s] for s in C.WITHDRAWN_STATUSES
            if "HEADROOM" in s},
        "statuses": list(C.V7_IDENTIFICATION_STATUSES),
        "readings": {
            "structural_zero":
                "every cell the contrast differences sits at the SAME exact "
                "boundary (0 or 1 in every block): the contrast is 0 with "
                "zero observed variance, its decision interval is the "
                "allowance alone (symmetric about zero), no directional "
                "classification is reachable, and an equivalence-type "
                "reading is licensed exactly when that interval satisfies "
                "the registered rule (L3c at 384 blocks; nothing at Gate "
                "4's 24 topics). Revised 2026-08-28 by the §13.14 boundary "
                "audit (V10)",
            "arm_at_boundary":
                "a constituent cell is at an exact boundary; the decision "
                "interval is widened, in the open direction only, by that "
                "constituent's weight times the 95% Wilson half-width at the "
                "block count (about 0.010 at 384 blocks)",
            "range_compressed":
                "for a two-arm contrast with observed arm levels L_P and "
                "L_N, the positive direction cannot reach +SESOI when "
                "L_N > 1 - SESOI or L_P < SESOI, and the negative direction "
                "cannot reach -SESOI when L_P > 1 - SESOI or L_N < SESOI; "
                "the compressed direction and the arm that closes it are "
                "recorded on the statement",
        },
        "sesoi": C.SMALLEST_EFFECT_OF_INTEREST,
        "compression_level": C.CONTRAST_COMPRESSION_LEVEL,
        "boundary_allowance_level": C.BOUNDARY_ALLOWANCE_LEVEL,
        "proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
        "proximity_band_is": "DESCRIPTIVE: classifies a cell as near a floor "
                             "or ceiling on a record; gates nothing",
        "projected_families": list(composed_contrast.PROJECTED_FAMILIES),
        "not_projected_members": list(composed_contrast.NOT_PROJECTED_MEMBERS),
        "where_the_readings_run": [
            f"{C.STAGE_GATE2_75}: D(B<-A), D(A<-B), Lambda, Ord_A, Ord_B on "
            "the 192 calibration topics",
            f"{C.STAGE_GATE4}: every projectable registered contrast on "
            "§6.2's 24 composed topics",
            f"{C.STAGE_UNMASKED_ANALYSIS}: the same, realised on the 384 "
            "confirmatory blocks; the decision rules read the widened "
            "interval and the statuses attach to the statement",
        ],
        "direction_outcomes": ["A_HARMS_MORE", "A_COMPARATIVELY_BETTER",
                               "DIRECTION_UNRESOLVED"],
        "terminates": False,
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
    adoption = _adoption()
    payload = {
        "_what_this_is":
            "The reference-validity and composed-contrast rule for DCI-1 v7, "
            "in machine-readable form, DERIVED from the registered "
            "implementation by tools/v7_reference_design_spec.py rather than "
            "transcribed. A spec that disagrees with the code is not "
            "expressible here.",
        "_status": ADOPTED if adoption["adopted"] else DRAFT,
        "_status_is_derived_from": adoption,
        "_status_means":
            "This field is DERIVED from three researcher acts and is never "
            "chosen by the producing tool: the preregistration's own "
            "`status:` line, whether "
            "reports/dci1v7/researcher_decisions.json closes every one of "
            "§34's decisions, and whether any §33 item that blocks the "
            "manifest is still unresolved. `_status_is_derived_from` records "
            "all three. While it reads DRAFT_NOT_ADOPTED, "
            "`manifest.assert_documents_adopted` refuses a registration.",
        "_provenance": {
            "protocol": PREREGISTRATION,
            "predecessor_protocol": "user-notes/DCI1_preregistration_v6.md",
            "producer": "dci1/tools/v7_reference_design_spec.py",
            "development_evidence": [
                "dci1/reports/dci1v6/closure.json",
                "dci1/evidence/dci1v6/*/GATE_2_75_COMPOSED_PROBE",
                "dci1/evidence/dci1v6/*/GATE_4_COMPOSED_HEADROOM"],
            "overfitting_declaration":
                "v7 withdraws the composed-headroom criterion after observing "
                "that it ended three of four v6 replications, two of them on "
                "B's compliance RISING under A. That is a response to an "
                "outcome and is declared as one under §32.2. No quantity in "
                "the replacement rule is fitted to a v6 observation: the "
                "compression level is 1 - SESOI, the allowance is the Wilson "
                "half-width at the registered block count, and the "
                "structural-zero rule reads exact boundaries. Retrospective "
                "behaviour on v6 is NOT prospective validation; v7 is the "
                "prospective test (§30).",
        },
        "design": _design(),
        "candidate_library": _library(),
        "validity_components": _validity(),
        "support_requirements": _support(),
        "composed_probe": _probe(),
        "composed_contrast": _contrast(),
        "open_decisions": {
            "count": len(decisions.open_decisions()),
            "ids": list(decisions.open_decisions()),
            "n_registered": len(decisions.DECISIONS),
            "why": "closing one is a researcher act recorded at "
                   f"{decisions.RECORD_RELPATH}, and no code may write it",
        },
        "researcher_decisions": {
            "record": decisions.RECORD_RELPATH,
            "hash": decisions.record_hash(),
            "closed": {k: decisions.value_of(k)
                       for k in decisions.DECISION_IDS
                       if decisions.is_closed(k)},
            "non_adopted_alternatives": decisions.non_adopted_alternatives(),
            "unimplemented_alternatives": {
                k: list(d.unimplemented_alternatives)
                for k, d in decisions.DECISIONS.items()
                if d.unimplemented_alternatives},
        },
        "what_this_spec_does_not_decide": [
            "any §34 decision. This file REPORTS the closures; the record "
            f"that takes them is {decisions.RECORD_RELPATH} and no code "
            "writes it",
            "whether §6.2's composed set is enlarged (§34 D21): the "
            "sequestered eighth is not materialised in this repository, so "
            "that branch is an act of authoring topics and not a constant",
            "where the study runs. m* is chosen at "
            f"{C.STAGE_GATE2} by §12.3's focal rule and frozen there; "
            "GATE_2_75_COMPOSED_PROBE and GATE_4 record and decide nothing",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(f"{OUT}  ({payload['_status']})")


if __name__ == "__main__":
    main()
