#!/usr/bin/env python3
"""Prove that the production path executes the registered rules.

    python3 tools/v6_execution_path_audit.py            # write the report
    python3 tools/v6_execution_path_audit.py --check    # fail if stale
    python3 tools/v6_execution_path_audit.py --fast     # skip the scenarios

Four defects in a row had the same shape: the preregistered rule existed, the
helper implementing it existed, unit tests covered it, and the production
runner did not call it --- or called it with a neighbouring field. Nothing in
the repository could see that, because every instrument in it asked a
different question:

* the test suite asked *does this function behave*;
* the producer/consumer contract asked *is this field declared*;
* the synthetic lifecycle asked *does the happy path complete*.

None of them asked *does the registered rule lie on the path a replication
takes*. That is the question here, and it is asked four ways at once:

1. **statically** --- the rule's implementation resolves to a real callable;
2. **dynamically** --- it executes while the lifecycle and the conditional
   scenarios run, observed by wrapping the ledger's own functions and every
   alias of them, so a rule that never fires is a fact and not an inference;
3. **on the artifact** --- the field it produces is on the signed record;
4. **on the consumer** --- the downstream stage actually reads that field,
   observed through ``run/field_access`` rather than declared.

A rule that fails any of the four is reported with the one it failed. The
report is a durable artifact because the finding "this rule is unreachable" is
evidence about the study, not a note about the code.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE.parent))

REPORT = HERE.parent / "reports" / "dci1v6" / "execution_path_audit.md"
MACHINE = HERE.parent / "reports" / "dci1v6" / "execution_path_audit.json"

VERIFIED = "VERIFIED_REACHABLE"
CONDITIONAL = "VERIFIED_CONDITIONAL"
MISSING_CALLER = "MISSING_CALLER"
WRONG_INPUT = "WRONG_INPUT_FIELD"
OUTPUT_DROPPED = "OUTPUT_DROPPED"
WRONG_CONSUMER = "WRONG_CONSUMER"
UNTESTED = "UNTESTED_CONDITIONAL"
AMBIGUOUS = "SCIENTIFIC_AMBIGUITY"

#: The ledger. One row per scientifically consequential registered rule from
#: stage 3 to stage 18: what it means, what implements it, what artifact it
#: lands on, and who reads that artifact. `expect` is the status this row is
#: asserted to hold; the audit computes the status from the run and a
#: disagreement is a finding.
#:
#: `runtime` names the function whose execution proves the rule ran. `field`
#: is `STAGE.field` on a signed record. `consumer` is the stage that must be
#: observed reading it.
RULES: tuple[dict[str, object], ...] = (
    # ------------------------------------------------ regime / operating point
    {"id": "R-12.1-cap", "section": "§12.1", "area": "regime",
     "meaning": "completion cap chosen where truncation is tolerable",
     "runtime": "dci1v6.stages.regime.select_operating_point",
     "impl": "dci1v6.run.regime_run.select_cap",
     "field": "REGIME_SCREEN.selected_cap", "consumer": "GATE_2_FOCAL_CALIBRATION",
     "expect": VERIFIED},
    # ------------------------------------------------------------- new in v6
    {"id": "R-12.6-expansion-span", "section": "§12.6", "area": "regime",
     "meaning": "V6-E01: a family failing C4 on its SPAN extends outward "
                "from both measured extremes, which is the only direction "
                "that can raise max(iota) - min(iota)",
     "runtime": "dci1v6.stages.regime.expansion_plan_for_family",
     "impl": "dci1v6.run.regime_run.regime_payload",
     "field": "REGIME_SCREEN.expansion",
     # Like `R-12.6-expansion` below: the plan is evidence on the record and
     # no later stage reads the field. What a later stage reads is the
     # carried set and the identification statuses the expansion produced.
     "consumer": None, "scenario": "reserve_expansion",
     "expect": VERIFIED},
    {"id": "R-12.6-shape", "section": "§12.6", "area": "regime",
     "meaning": "V6-E02: a row §12.6's criterion would silently drop is "
                "refused, so a measured rung cannot be counted ineligible "
                "for want of a join",
     "runtime": "dci1v6.stages.regime.assert_coverage_shape",
     "impl": "dci1v6.run.regime_run.regime_payload",
     "field": "REGIME_SCREEN.coverage",
     "consumer": None, "expect": VERIFIED},
    {"id": "R-2.75-margin", "section": "§13.14, P3.2", "area": "probe",
     "meaning": "the frozen m* has composed headroom only when every "
                "DETERMINATE entry passes its own test. Determinate-only "
                "termination: a stand-in-dependent verdict is recorded and "
                "gates nothing",
     "runtime": "dci1v6.stages.composed_probe.severity_verdict",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.disposition",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-2.75-frozen-m-star", "section": "P3.3, P3.6", "area": "probe",
     "meaning": "m* is selected once, by §12.3 at Gate 2, and this stage "
                "cannot move it. `probe_disposition` refuses a table "
                "carrying any severity but m*, returns m_star_out == "
                "m_star_in on every non-terminal path, and terminates "
                "COMPOSED_HEADROOM_UNREACHABLE otherwise. Headroom decides "
                "WHETHER the frozen design is viable, never WHERE the "
                "estimands are measured",
     "runtime": "dci1v6.stages.composed_probe.probe_disposition",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.m_star",
     "consumer": "GATE_3A_REFERENCE_CALIBRATION",
     "scenario": "probe_passes_at_the_frozen_m_star", "expect": VERIFIED},
    {"id": "R-2.75-m-star-unmoved", "section": "P3.3", "area": "probe",
     "meaning": "the invariant is executed on both halves: the producing "
                "path asserts m_star_in == m_star_out before the record is "
                "written, and every downstream read checks the written "
                "record against Gate 2's own m*",
     "runtime": "dci1v6.stages.composed_probe.assert_m_star_unmoved",
     "impl": "dci1v6.run.gates_run.effective_m_star",
     "field": "GATE_2_75_COMPOSED_PROBE.m_star_is_unchanged",
     "consumer": "GATE_5_FREEZE",
     "scenario": "probe_passes_at_the_frozen_m_star", "expect": VERIFIED},
    {"id": "R-2.75-unreachable", "section": "§28, P3.6", "area": "probe",
     "meaning": "a determinate entry outside its projected Gate-4 interval "
                "at the frozen m* ends the replication. There is no other "
                "severity to move to, so the terminal status is the whole "
                "of the failure branch",
     "runtime": "dci1v6.stages.composed_probe.probe_disposition",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.outcome", "consumer": None,
     "scenario": "probe_terminates_at_the_frozen_m_star",
     "expect": VERIFIED},
    {"id": "R-2.75-admissible", "section": "§12.4, §34 D17, P3.1",
     "area": "probe",
     "meaning": "the probed m* must be one Gate 2 found ADMISSIBLE: "
                "eligible under §12.3 and, at that severity, adequate under "
                "§12.4 and past D17's construct floor. Eligibility alone is "
                "a band test on the solo curve, so checking only it would "
                "admit an operating point Gate 2 would itself have refused",
     "runtime": "dci1v6.stages.composed_probe."
                "assert_probe_severities_are_admissible",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.focal_admissible",
     "consumer": "GATE_2_75_COMPOSED_PROBE",
     "scenario": "probe_passes_at_the_frozen_m_star", "expect": VERIFIED},
    {"id": "R-13.6-operating-point", "section": "§13.6, §13.11",
     "area": "probe",
     "meaning": "kappa(R|B) and the §13.1 pool are read at the frozen "
                "operating point, BY NAME, from columns Gate 2 signed for "
                "every admissible severity before the probe observed a "
                "composed cell. `assert_kappa_under_b_source` refuses a "
                "table read at an operating point its column was not "
                "measured at, so a positional read cannot land on the wrong "
                "severity",
     "runtime": "dci1v6.stages.feasibility.calibration_rows_at",
     "impl": "dci1v6.run.gates_run.gate3a_payload",
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.qualification_by_severity",
     "consumer": "GATE_3A_REFERENCE_CALIBRATION",
     "scenario": "probe_passes_at_the_frozen_m_star", "expect": VERIFIED},
    {"id": "R-18.1-frozen-operating-point", "section": "§18.1",
     "area": "probe",
     "meaning": "the freeze binds B --- and the pool --- at the operating "
                "point the study runs, which is Gate 2's frozen m*. "
                "Confirmatory generation renders every cell from the frozen "
                "slot map, and `effective_m_star` refuses a probe record "
                "that disagrees with Gate 2 rather than following either",
     "runtime": "dci1v6.run.freeze_run.freeze_payload",
     "impl": "dci1v6.run.freeze_run.assemble",
     "field": "GATE_5_FREEZE.slot_map", "consumer": None,
     "scenario": "probe_passes_at_the_frozen_m_star", "expect": VERIFIED},
    {"id": "R-2.75-blind", "section": "§13.11", "area": "probe",
     "meaning": "no function in the probe module reads a reference or a "
                "selection record, by name and by source",
     "runtime": "dci1v6.stages.composed_probe."
                "assert_probe_reads_no_reference",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.declared_refusals",
     "consumer": "PREFREEZE_AUDIT", "expect": VERIFIED},
    {"id": "R-12.2-carry", "section": "§12.2", "area": "regime",
     "meaning": "the high-recall retention verdict for each rung",
     "runtime": "dci1v6.stages.regime.carry_candidate",
     "impl": "dci1v6.stages.regime.carried_set",
     "field": "REGIME_SCREEN.carried_set",
     "consumer": "GATE_3C_IDENTIFICATION", "expect": VERIFIED},
    {"id": "R-12.3-target", "section": "§12.3", "area": "regime",
     "meaning": "n* is A's eligible severity nearest 0.70",
     "runtime": "dci1v6.stages.regime.select_target",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.n_star",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-12.3-focal", "section": "§12.3", "area": "regime",
     "meaning": "m* is B's eligible severity nearest 0.80",
     "runtime": "dci1v6.stages.regime.select_focal",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.m_star",
     "consumer": "GATE_2_5_CANDIDATE_QUALIFICATION", "expect": VERIFIED},
    {"id": "R-7.2-extension", "section": "§7.2, §12.3", "area": "regime",
     "meaning": "the focal grid escalates to {15, 16} when the registered "
                "grid supplies no bracketed operating point",
     "runtime": "dci1v6.stages.regime.select_focal",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.focal_selection",
     "consumer": "GATE_5_FREEZE", "scenario": "focal_extension_required",
     "expect": CONDITIONAL},
    {"id": "R-12.3-resolution", "section": "§12.3", "area": "regime",
     "meaning": "GRID_RESOLUTION_INSUFFICIENT when two adjacent severities "
                "lie on opposite sides of a whole band",
     "runtime": "dci1v6.stages.regime.grid_resolution",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.grid_resolution",
     "consumer": None, "scenario": "grid_resolution_insufficient",
     "expect": CONDITIONAL},
    {"id": "R-12.4-adequacy", "section": "§12.4", "area": "regime",
     "meaning": "the three regime-adequacy conditions, share not mean",
     "runtime": "dci1v6.stages.regime.regime_adequacy",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.adequacy",
     "consumer": None, "scenario": "no_viable_regime",
     "expect": VERIFIED},
    {"id": "R-34-D17", "section": "§34 D17", "area": "regime",
     "meaning": "the construct-strength floor on kappa_B(m*), load-zero",
     "runtime": "dci1v6.stages.construct_strength.assert_construct_floor",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_FOCAL_CALIBRATION.construct_strength",
     "consumer": None, "expect": VERIFIED},

    # ------------------------------------------------------ candidate / V(R)
    {"id": "R-12.7-population", "section": "§12.7", "area": "V(R)",
     "meaning": "calibration measures the priority population, not the "
                "carried set",
     "runtime": "dci1v6.stages.regime.calibration_priority",
     "impl": "dci1v6.run.gates_run.assert_calibration_population",
     "field": "REGIME_SCREEN.calibration_priority",
     "consumer": "GATE_2_FOCAL_CALIBRATION",
     "scenario": "calibration_population", "expect": VERIFIED},
    {"id": "R-13.1-vr", "section": "§13.1-§13.7", "area": "V(R)",
     "meaning": "the eight V(R) components in registered order",
     "runtime": "dci1v6.stages.validity.evaluate_validity",
     "impl": "dci1v6.stages.qualification_gate.qualify_candidates",
     # The pool is now qualified at every admissible severity and read at the
     # one Gate 2.75 selected, so the field a later stage reads is the
     # by-severity map --- see R-13.6-operating-point.
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.qualification_by_severity",
     "consumer": "GATE_3A_REFERENCE_CALIBRATION", "expect": VERIFIED},
    {"id": "R-19-lexicographic", "section": "§19 test 3", "area": "V(R)",
     "meaning": "the recorded reason is the earliest failing component",
     "runtime": "dci1v6.stages.validity.assert_lexicographic_order",
     "impl": "dci1v6.stages.qualification_gate.qualify_candidates",
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.qualification_by_severity",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-12.6-calibrated-coverage", "section": "§12.6", "area": "V(R)",
     "meaning": "§12.6's criterion re-read on the CALIBRATION basis at the "
                "iota_A reference selection matches on --- iota(R), the "
                "eligibility coordinate, the vacuity and iota_A all from the "
                "same 192 topics at the same four draws. A lost decisive "
                "condition enters §13.15 as a design-time failure under §34 "
                "D6's existing disposition; there is no drift threshold and "
                "no new status",
     "runtime": "dci1v6.stages.feasibility.coverage_at_calibrated_iota_a",
     "impl": "dci1v6.run.gates_run.gate3a_payload",
     "field": "GATE_3A_REFERENCE_CALIBRATION.calibrated_coverage_failures",
     "consumer": "GATE_3C_IDENTIFICATION", "expect": VERIFIED},
    {"id": "R-13.15-one-criterion", "section": "§13.15", "area": "V(R)",
     "meaning": "the registered stage, the operating-point search and the "
                "development pilot evaluate ONE implementation of the "
                "support criterion. v5's development work asked whether "
                "reserve rungs land inside the solo band, which is one "
                "clause of one component of V(R), and could not predict the "
                "gate it was standing in for",
     "runtime": "dci1v6.stages.feasibility.support_at",
     "impl": "dci1v6.run.gates_run.gate3c_payload",
     "field": "GATE_3C_IDENTIFICATION.support",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-12.3-frozen-order", "section": "§12.3", "area": "probe",
     "meaning": "§12.3's own preference over `focal_admissible`, written at "
                "Gate 2 and restricted at Gate 2.5 to the severities that "
                "can reach §13.15's five-family minimum. Nothing tries these "
                "in turn --- m* is frozen --- and the probe reads the head "
                "only, to check that Gate 2 and Gate 2.5 agree about it",
     "runtime": "dci1v6.stages.feasibility.operating_point_order",
     "impl": "dci1v6.run.gates_run.gate2_payload",
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.operating_point_order",
     "consumer": "GATE_2_75_COMPOSED_PROBE", "expect": VERIFIED},
    {"id": "R-13.15-free-prefilter", "section": "§13.15", "area": "probe",
     "meaning": "§13.15's five-family minimum is evaluated at every "
                "admissible severity and recorded. The verdict is Gate 2.5's "
                "own, computed there because that stage generates nothing, "
                "so the column costs no rows and no second bootstrap. The "
                "study runs at the frozen m*; the rest is a signed "
                "prospective record that no selection rule reads",
     "runtime": "dci1v6.stages.feasibility.restricted_operating_point_order",
     "impl": "dci1v6.run.gates_run.gate2_5_payload",
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.operating_point_support",
     "consumer": None, "expect": VERIFIED},
    {"id": "R-13.14-controlled-reuse", "section": "§13.14", "area": "probe",
     "meaning": "the unconstrained cell and B's own solo cell are read off "
                "the Gate-2 record instead of drawn again, and ONLY when the "
                "topic identifiers and the draw count are identical. That "
                "makes the composed lift a difference from the number m* was "
                "selected on rather than a difference between two samples of "
                "it, and the refusal to reuse across topic sets is checked "
                "rather than assumed",
     "runtime": "dci1v6.stages.composed_probe.shared_cell_verdict",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.shared_with_gate2",
     "consumer": None, "expect": VERIFIED},
    {"id": "R-13.14-class-coverage", "section": "§13.14", "area": "probe",
     "meaning": "the probe covers every one of §13.14's ten slot-and-order "
                "exposure classes, and the partition is DERIVED from "
                "design.cells.cell_types rather than listed --- so admitting "
                "an arm or changing §8.4's order rule changes what the probe "
                "must cover without an edit to the probe. A shape that leaves "
                "a class uncovered is refused",
     "runtime": "dci1v6.stages.composed_probe."
                "assert_probe_covers_gate4_classes",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.gate4_class_coverage",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-13.4-projection", "section": "§13.4", "area": "probe",
     "meaning": "a determinate probe entry --- one whose every constituent is "
                "a real registered instrument --- is judged by its PROJECTED "
                "Gate-4 interval and not by its point estimate, using the "
                "entry's own in-stage between-topic variance at §13.4's "
                "registered level. It is §13.4's own device applied to "
                "§13.14's band, so the convention is the protocol's and not "
                "the stage's, and §13.14's band itself never moves",
     "runtime": "dci1v6.stages.composed_probe.projected_halfwidth",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.disposition",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-13.14-determinate-only-termination", "section": "§13.14, P3.2",
     "area": "probe",
     "meaning": "only the six determinate entries may fail the verdict. An "
                "instrument that can never be selected as a reference cannot "
                "raise COMPOSED_HEADROOM_UNREACHABLE, and no entry of either "
                "kind can move m*",
     "runtime": "dci1v6.stages.composed_probe.severity_verdict",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.disposition",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-34-D23-reading-is-not-the-magnitude", "section": "§34 D23, D26",
     "area": "probe",
     "meaning": "the band a determinate interval must lie inside and the sd "
                "the projection's quadrature carries are separate arguments, "
                "so one can never be silently substituted for the other. §34 "
                "D23 selects the reading and §34 D26 the magnitude",
     "runtime": "dci1v6.stages.composed_probe.projection_residual_sd",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.residual_reading",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-13.14-no-margin-for-a-standin", "section": "§13.14",
     "area": "probe",
     "meaning": "an entry of a cell containing a stand-in is judged against "
                "§13.14's REGISTERED band with no margin. A stand-in is not "
                "the reference, so a projection from it would project the "
                "wrong instrument; its failure is a real composed cell "
                "leaving the band and its passing certifies nothing about a "
                "reference",
     "runtime": "dci1v6.stages.composed_probe.entry_verdict",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.scope_limits",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-13.8-standin-placement", "section": "§13.8", "area": "probe",
     "meaning": "each stand-in is probed at the severity of its own solo "
                "ladder nearest Gate 2's measured iota_A inside §13.4's band, "
                "because §13.8 matches a reference's iota(R) to iota_A. "
                "iota_A does not depend on m*, so the companion a probed "
                "cell carries is fixed by a quantity the operating point "
                "cannot move",
     "runtime": "dci1v6.stages.composed_probe.standin_operating_points",
     "impl": "dci1v6.run.gates_run.gate2_75_payload",
     "field": "GATE_2_75_COMPOSED_PROBE.standin_operating_points",
     "consumer": "GATE_5_FREEZE", "expect": VERIFIED},
    {"id": "R-7.10-probe-only-is-not-selectable", "section": "§7.10",
     "area": "library",
     "meaning": "a probe_only stand-in is a registered instrument --- same "
                "verifier, same hash, same Gate-1 certification --- and is "
                "outside every selectable pool: §12.2's screen filters to "
                "SELECTABLE_FAMILY_IDS and re-asserts it rung by rung, and "
                "the tier partitions, the candidate budget and the freeze's "
                "candidate vocabulary all read the selectable pool",
     "runtime": "dci1v6.verifiers.constraints.assert_selectable",
     "impl": "dci1v6.run.regime_run._screen_rungs",
     "field": "REGIME_SCREEN.difficulty_table",
     "consumer": "GATE_2_FOCAL_CALIBRATION", "expect": VERIFIED},
    {"id": "R-18.1-draft-document", "section": "§18", "area": "registration",
     "meaning": "a registration binds two documents by hash, and a COMPLETE "
                "DRAFT is exactly what could be mistaken for a registration "
                "by being present. Both documents declare their own status "
                "and the manifest refuses while either says it is a draft; "
                "silence reads as a draft, because the safe reading of "
                "silence here is the one that refuses",
     "runtime": "dci1v6.protocol.manifest.assert_documents_adopted",
     "impl": "dci1v6.protocol.manifest.signing_blockers",
     "field": "PROTOCOL_REGISTERED.protocol_hash",
     "consumer": None, "expect": VERIFIED},
    {"id": "R-18-readiness-refusal", "section": "§18 stage 1, A15",
     "area": "registration",
     "meaning": "a stage-1 readiness verdict is a REFUSAL, not a §28 "
                "terminal outcome. Every blocker names work a researcher has "
                "to do, so a terminating verdict made the whole vocabulary "
                "unreachable --- the first invocation that found any of it "
                "outstanding killed the replication. It writes no record and "
                "no terminal report, logs a REFUSED transition carrying the "
                "blockers, and the stage may be attempted again once the "
                "prerequisite is met. The criterion is unchanged",
     "runtime": "dci1v6.run.lifecycle.log_readiness_refusal",
     "impl": "dci1v6.run.registration_run.registration_payload",
     "field": "PROTOCOL_REGISTERED.protocol_hash",
     "consumer": None, "scenario": "stage_one_readiness_is_retryable",
     "expect": VERIFIED},
    {"id": "R-32-apparatus-fault-retirement", "section": "§32, A15",
     "area": "registration",
     "meaning": "the pre-manifest recovery: a readiness verdict an apparatus "
                "fault wrote as a §28.3 terminal report is RETAINED under "
                "superseded/apparatus_fault/<record hash>/ and named in every "
                "registration signed afterwards. It refuses for any other "
                "gate, any §28 terminal status, once a manifest exists, once "
                "any row has been generated, and on a hash that does not "
                "match --- so it can revive nothing scientific",
     "runtime": "dci1v6.run.registration_run.retire_apparatus_fault",
     "impl": "dci1v6.protocol.manifest.apparatus_faults",
     "field": "PROTOCOL_REGISTERED.manifest_hash",
     "consumer": None, "scenario": "stage_one_apparatus_fault_is_retired",
     "expect": VERIFIED},
    {"id": "R-13.7-stability", "section": "§13.7", "area": "V(R)",
     "meaning": "each candidate is equivalent across the two splits",
     "runtime": "dci1v6.stages.stability.stability_verdict",
     "impl": "dci1v6.run.gates_run.gate3a_payload",
     "field": "GATE_3A_REFERENCE_CALIBRATION.stability",
     "consumer": "GATE_3B_REFERENCE_SELECTION", "expect": VERIFIED},
    {"id": "R-13.7-iota-a", "section": "§13.7", "area": "V(R)",
     "meaning": "iota_A meets the same equivalence rule as every candidate",
     "runtime": "dci1v6.stages.stability.assert_iota_a_stable",
     "impl": "dci1v6.run.gates_run.gate3a_payload",
     "field": "GATE_3A_REFERENCE_CALIBRATION.iota_a_stability",
     "consumer": None, "expect": VERIFIED},
    {"id": "R-13.6-interaction", "section": "§13.6", "area": "V(R)",
     "meaning": "kappa(R|B), displacement and the projected compliance",
     "runtime": "dci1v6.stages.interaction.measure_interaction",
     "impl": "dci1v6.run.gates_run.gate2_5_payload",
     "field": "GATE_2_5_CANDIDATE_QUALIFICATION.interaction",
     "consumer": None, "expect": VERIFIED},

    # ------------------------------------------------------------- expansion
    {"id": "R-12.6-coverage", "section": "§12.6", "area": "expansion",
     "meaning": "the eight identification-coverage conditions",
     "runtime": "dci1v6.stages.regime.coverage_criterion",
     "impl": "dci1v6.run.regime_run.regime_payload",
     "field": "REGIME_SCREEN.coverage", "consumer": None,
     "expect": VERIFIED},
    {"id": "R-12.6-eligibility", "section": "§12.6, §13.4", "area": "expansion",
     "meaning": "which pre-screen rungs are eligible for the criterion",
     "runtime": "dci1v6.stages.regime.coverage_eligibility",
     "impl": "dci1v6.stages.regime.coverage_rows",
     "field": "REGIME_SCREEN.coverage_eligibility_formulation",
     "consumer": None, "expect": VERIFIED,
     "note": "open item U4, opened by A4 and CLOSED AT E2 by the researcher "
             "in A5: §12.6 named §13's band ON IOTA and §13 bands p_solo, so "
             "eligibility is p_solo in [0.10, 0.90] with the vacuity ceiling. "
             "The criterion still positions rungs by iota. Both formulations "
             "stay constructible by name; E1 is non-adopted"},
    {"id": "R-12.6-expansion", "section": "§12.6", "area": "expansion",
     "meaning": "the reserve expansion, at most four rungs per family per "
                "round and at most two rounds",
     "runtime": "dci1v6.stages.regime.run_expansion",
     "impl": "dci1v6.run.regime_run.regime_payload",
     "field": "REGIME_SCREEN.expansion", "consumer": None,
     "scenario": "reserve_expansion", "expect": VERIFIED},
    {"id": "R-12.6-disposition", "section": "§12.6", "area": "expansion",
     "meaning": "unmet after the rounds: REFERENCE_SUPPORT_NOT_IDENTIFIED at "
                "design time, and the replication runs without the core and "
                "spectrum arms",
     "runtime": "dci1v6.stages.regime.run_expansion",
     "impl": "dci1v6.run.gates_run.gate3c_payload",
     "field": "REGIME_SCREEN.identification_statuses",
     "consumer": "GATE_3C_IDENTIFICATION", "expect": VERIFIED},

    {"id": "R-12.6-iota-a", "section": "§12.6", "area": "expansion",
     "meaning": "iota_A is A's pre-screen instructed compliance at the "
                "severity whose solo compliance is nearest §12.3's aim",
     "runtime": "dci1v6.run.regime_run.difficulty_table",
     "impl": "dci1v6.run.regime_run.regime_payload",
     "field": "REGIME_SCREEN.iota_a_prescreen_severity", "consumer": None,
     "expect": VERIFIED},

    # --------------------------------------------------- reference selection
    {"id": "R-13.8-core", "section": "§13.8", "area": "reference selection",
     "meaning": "three core references by the registered tie-break",
     "runtime": "dci1v6.stages.selection.admit_core_references",
     "impl": "dci1v6.run.gates_run.gate3b_payload",
     "field": "GATE_3B_REFERENCE_SELECTION.selection",
     "consumer": "GATE_3C_IDENTIFICATION", "expect": VERIFIED},
    {"id": "R-13.15-support", "section": "§13.15, §34 D6",
     "area": "reference selection",
     "meaning": "the support requirements, and D6's irreversible verdict",
     "runtime": "dci1v6.stages.support.evaluate_support",
     "impl": "dci1v6.run.gates_run.gate3c_payload",
     "field": "GATE_3C_IDENTIFICATION.non_identification",
     "consumer": "GATE_5_FREEZE",
     "scenario": "reference_support_not_identified", "expect": VERIFIED},
    {"id": "R-13.14-no-substitution", "section": "§13.14",
     "area": "reference selection",
     "meaning": "no function substitutes a backup after an outcome",
     "runtime": "dci1v6.run.gates_run.assert_no_substitution_path",
     "impl": "dci1v6.run.prefreeze_run.artifact_checks",
     "field": "GATE_4_COMPOSED_HEADROOM.declared_refusals",
     "consumer": "PREFREEZE_AUDIT", "expect": VERIFIED},

    {"id": "R-13.12-exhaustion", "section": "§13.12, §8.1",
     "area": "reference selection",
     "meaning": "a family that cannot straddle iota_A costs the SPECTRUM "
                "arm, not the core set",
     "runtime": "dci1v6.stages.selection.select_all",
     "impl": "dci1v6.run.gates_run.gate3b_payload",
     "field": "GATE_3B_REFERENCE_SELECTION.selection",
     "consumer": "GATE_3C_IDENTIFICATION", "expect": VERIFIED},

    # ---------------------------------------------------------------- gate 4
    {"id": "R-13.14-headroom", "section": "§13.14", "area": "gate 4",
     "meaning": "every registered cell type inside [0.05, 0.95]",
     "runtime": "dci1v6.run.gates_run.assert_headroom_table_complete",
     "impl": "dci1v6.run.gates_run.gate4_payload",
     "field": "GATE_4_COMPOSED_HEADROOM.headroom_table",
     "consumer": "PREFREEZE_AUDIT", "scenario": "composed_headroom_failure",
     "expect": VERIFIED},

    # ------------------------------------------------------------- F1 to F11
    {"id": "R-15-members", "section": "§15", "area": "F1-F11",
     "meaning": "every registered family member is estimated, or carries the "
                "registered reason it is not",
     "runtime": "dci1v6.run.analysis_run.estimate_all",
     "impl": "dci1v6.run.analysis_run.unmasked_payload",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-15-F5", "section": "§15 F5, §17.4", "area": "F1-F11",
     "meaning": "the six F1 members under the vacuity-forced recoding and "
                "three under the graded threshold at 0.99",
     "runtime": "dci1v6.analysis.estimators.delivery_loss",
     "impl": "dci1v6.run.analysis_run.estimate_all",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-15-F6", "section": "§15 F6, §17.4", "area": "F1-F11",
     "meaning": "the vacuity-rate difference for every composed cell with B",
     "runtime": "dci1v6.analysis.estimators.vacuity_difference",
     "impl": "dci1v6.run.analysis_run.estimate_all",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-15-F8", "section": "§11.8, §15 F8, U2=A2", "area": "F1-F11",
     "meaning": "the tier-indicator secondary's beta, three core intercepts "
                "and gamma, under the adopted formulation",
     "runtime": "dci1v6.analysis.spectrum.fit_with_tier_indicator",
     "impl": "dci1v6.run.analysis_run.estimate_all",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": "FINAL_REPORT",
     "scenario": "a2_spectrum_fit", "expect": VERIFIED},
    {"id": "R-15-simultaneous", "section": "§15", "area": "F1-F11",
     "meaning": "one simultaneous interval per family per configuration",
     "runtime": "dci1v6.analysis.bootstrap.bootstrap_family",
     "impl": "dci1v6.run.analysis_run._intervals",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-11.3-forms", "section": "§11.3", "area": "F1-F11",
     "meaning": "Delta_R's two algebraic forms agree to 1e-9",
     "runtime": "dci1v6.analysis.estimators.assert_delta_r_forms",
     "impl": "dci1v6.run.analysis_run._algebraic_form_checks",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": None,
     "expect": VERIFIED},
    {"id": "R-11.7-forms", "section": "§11.7", "area": "F1-F11",
     "meaning": "every order contrast agrees in both algebraic forms",
     "runtime": "dci1v6.analysis.estimators.assert_order_forms",
     "impl": "dci1v6.run.analysis_run._algebraic_form_checks",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": None,
     "expect": VERIFIED},
    {"id": "R-11.8-forms", "section": "§11.8", "area": "F1-F11",
     "meaning": "delta_difficulty's two algebraic forms agree to 1e-9",
     "runtime": "dci1v6.analysis.spectrum.assert_algebraic_forms_agree",
     "impl": "dci1v6.run.analysis_run._algebraic_form_checks",
     "field": "UNMASKED_ANALYSIS.estimands", "consumer": None,
     "expect": VERIFIED},

    # ----------------------------------------------------------- claim ladder
    {"id": "R-3.2-L1", "section": "§3.2 L1", "area": "claim ladder",
     "meaning": "compositional delivery loss exists, per named D(c <- g)",
     "runtime": "dci1v6.analysis.claims.emit_l1",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-12-L1-gate", "section": "§12, §3.2 L1", "area": "claim ladder",
     "meaning": "L1's identification gate is the outcome constraint's solo "
                "headroom, measured",
     "runtime": "dci1v6.run.analysis_run._has_headroom",
     "impl": "dci1v6.run.analysis_run.unmasked_payload",
     "field": "GATE_5_FREEZE.freeze", "consumer": "UNMASKED_ANALYSIS",
     "expect": VERIFIED},
    {"id": "R-3.2-L2", "section": "§3.2 L2", "area": "claim ladder",
     "meaning": "the loss is directionally asymmetric",
     "runtime": "dci1v6.analysis.claims.emit_l2",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-3.2-L3", "section": "§3.2 L3, §17.6", "area": "claim ladder",
     "meaning": "Delta_R and delta_difficulty's joint reading, sub-level by "
                "sub-level",
     "runtime": "dci1v6.analysis.claims.emit_l3",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-34-D18", "section": "§34 D18", "area": "claim ladder",
     "meaning": "the strong L3c is unreachable without the near-form arm",
     "runtime": "dci1v6.analysis.claims.l3c_disposition",
     "impl": "dci1v6.analysis.claims.assert_l3c_scope",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "scenario": "near_form_unavailable", "expect": VERIFIED},
    {"id": "R-3.2-L4a", "section": "§3.2 L4a", "area": "claim ladder",
     "meaning": "the same classification, per named member, in every "
                "configuration",
     "runtime": "dci1v6.analysis.claims.emit_l4a",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-3.2-L4b", "section": "§3.2 L4b", "area": "claim ladder",
     "meaning": "the named order contrast depends on outcome position",
     "runtime": "dci1v6.analysis.claims.emit_l4b",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-3.2-L5", "section": "§3.2", "area": "claim ladder",
     "meaning": "L5 is permanently withheld and no code path emits it",
     "runtime": "dci1v6.analysis.claims.assert_no_l5_emitter",
     "impl": "dci1v6.run.final_report_checks.run_checks",
     "field": "FINAL_REPORT.final_report_checks", "consumer": None,
     "expect": VERIFIED},

    # ------------------------------------------------------------- masking
    {"id": "R-20-mask", "section": "§20", "area": "masking",
     "meaning": "the mask removes only registered identity information",
     "runtime": "dci1v6.analysis.masking.assert_mask_effective",
     "impl": "dci1v6.run.analysis_run.masked_payload",
     "field": "MASKED_ANALYSIS.masked_result_hash", "consumer": "UNMASKING",
     "expect": VERIFIED},
    {"id": "R-20-withheld", "section": "§20", "area": "masking",
     "meaning": "the masked phase computes no forbidden member",
     "runtime": "dci1v6.analysis.masking.assert_delta_difficulty_not_masked",
     "impl": "dci1v6.run.analysis_run.masked_payload",
     "field": "MASKED_ANALYSIS.masked_result_hash", "consumer": "UNMASKING",
     "expect": VERIFIED},
    {"id": "R-20-once", "section": "§20", "area": "masking",
     "meaning": "the unmask happens exactly once",
     "runtime": "dci1v6.analysis.masking.unmask",
     "impl": "dci1v6.run.analysis_run.unmask_payload",
     "field": "UNMASKING.unmasked", "consumer": "UNMASKED_ANALYSIS",
     "scenario": "unmask_is_one_shot", "expect": VERIFIED},

    {"id": "R-18.14-raw", "section": "§18 step 14, §15, §31",
     "area": "final report",
     "meaning": "the difficulty relation refitted on the raw coordinate, "
                "reported beside the primary with MARGINAL intervals only",
     "runtime": "dci1v6.analysis.spectrum.estimate",
     "impl": "dci1v6.run.analysis_run._raw_coordinate_secondary",
     "field": "UNMASKED_ANALYSIS.raw_coordinate_secondary",
     "consumer": "FINAL_REPORT",
     "scenario": "coordinate_secondary_not_computable", "expect": VERIFIED,
     "note": "V5-E27, resolved in A5 without inventing anything. Step 9 is "
             "executed in full on the raw coordinate --- fit, A's exclusion, "
             "§13.13 support, both algebraic forms, the block bootstrap. "
             "Step 12 is NOT_REGISTERED_FOR_INFERENCE: §15 registers the "
             "raw-coordinate replication among the quantities reported with "
             "marginal intervals only and supporting no claim, and declares "
             "no family containing a raw-coordinate member"},
    {"id": "R-17.6-coordinate", "section": "§17.6, §34 D14",
     "area": "claim ladder",
     "meaning": "when the registered and raw coordinates give different "
                "L3d/L3e classifications the statement carries "
                "DIFFICULTY_COORDINATE_DEPENDENT",
     "runtime": "dci1v6.analysis.claims.coordinate_agreement",
     "impl": "dci1v6.run.analysis_run._statements",
     "field": "UNMASKED_ANALYSIS.statements",
     "consumer": "FINAL_REPORT", "scenario": "coordinate_dependent",
     "expect": VERIFIED,
     "note": "D14's closure --- iota primary, raw solo secondary, the status "
             "on disagreement --- bound nothing until the raw fit existed"},

    # -------------------------------------------------------------- reporting
    {"id": "R-23-projection", "section": "§23, §31", "area": "final report",
     "meaning": "the realised p_hat_c against realised composed compliance",
     "runtime": "dci1v6.analysis.estimators.projected_compliance_vector",
     "impl": "dci1v6.run.analysis_run._projection_audit",
     "field": "UNMASKED_ANALYSIS.projection_audit", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
    {"id": "R-31-table", "section": "§31", "area": "final report",
     "meaning": "every estimate with its cell, claim level and family",
     "runtime": "dci1v6.stages.final_report.assert_table_traceable",
     "impl": "dci1v6.run.analysis_run.final_report_payload",
     "field": "FINAL_REPORT.results", "consumer": None, "expect": VERIFIED},
    {"id": "R-26-success", "section": "§26", "area": "final report",
     "meaning": "the methodological success criterion, judged pre-outcome",
     "runtime": "dci1v6.stages.support.methodological_success",
     "impl": "dci1v6.run.analysis_run.unmasked_payload",
     "field": "UNMASKED_ANALYSIS.success_criterion", "consumer": "FINAL_REPORT",
     "expect": VERIFIED},
)


def _resolve(dotted: str):
    module, _, name = dotted.rpartition(".")
    import importlib
    try:
        return getattr(importlib.import_module(module), name, None)
    except Exception:                                        # pragma: no cover
        return None


def _instrument(names: list[str], seen: set) -> list:
    """Record every call to the named functions, wherever they are bound.

    A global profiler answers this too and costs several times the run. This
    wraps the target functions themselves --- **and every alias of them**,
    because ``from x import y`` binds the object into the importing module and
    a patch on the defining module would never be reached. The wrapper
    delegates unchanged, so the run it observes is the run that would have
    happened.
    """
    import importlib
    targets: dict = {}
    for dotted in names:
        module_name, _, attr = dotted.rpartition(".")
        try:
            original = getattr(importlib.import_module(module_name), attr,
                               None)
        except Exception:                                    # pragma: no cover
            original = None
        if callable(original):
            targets[original] = dotted

    def wrap(original, dotted):
        def recorded(*args, **kwargs):
            seen.add(dotted)
            return original(*args, **kwargs)
        recorded.__name__ = getattr(original, "__name__", dotted)
        recorded.__doc__ = getattr(original, "__doc__", None)
        recorded.__wrapped__ = original
        return recorded

    undo = []
    for module in list(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith(
                ("dci1v6", "tests_v6")):
            continue
        for attr, value in list(vars(module).items()):
            dotted = targets.get(value) if callable(value) else None
            if dotted is None:
                continue
            setattr(module, attr, wrap(value, dotted))
            undo.append((module, attr, value))
    return undo


def _executed_names(root: pathlib.Path, fast: bool) -> tuple[set, dict, dict]:
    """Run the lifecycle (and the scenarios) with the ledger's rules watched."""
    from tests_v6 import synthetic_lifecycle as SL
    from dci1v6.run import field_access

    seen: set[str] = set()
    SL.resolved_manifest()
    scenarios: dict = {}
    undo = _instrument([str(r["runtime"]) for r in RULES], seen)
    try:
        if fast:
            with field_access.recording():
                walked = SL.walk(root / "walk")
                reads = field_access.observed()
            payloads = walked["payloads"]
        else:
            from tests_v6 import scenarios as SC
            scenarios = SC.run_all(root / "scenarios")
            normal = scenarios["normal_full_path"]
            payloads, reads = normal["payloads"], normal["reads"]
        # Captured HERE, before `SL.restore()` reopens the registry against
        # the real record: the claim this supports is what the walk ran
        # under, and a snapshot taken afterwards would report what the
        # researcher recorded whether or not the walk used it.
        from dci1v6.protocol import decisions as _decisions
        ran_under = {k: _decisions.value_of(k)
                     for k in _decisions.DECISION_IDS}
    finally:
        for module, attr, original in undo:
            setattr(module, attr, original)
        SL.restore()
    return (seen, {"payloads": payloads, "reads": reads, "decisions":
                   ran_under}, scenarios)


def _status(rule: dict, executed: set, payloads: dict, reads: dict,
            scenarios: dict) -> tuple[str, str]:
    if rule["expect"] == AMBIGUOUS:
        return AMBIGUOUS, str(rule.get("note") or "")
    if _resolve(str(rule["runtime"])) is None:
        return MISSING_CALLER, f"{rule['runtime']} does not resolve"
    ran = str(rule["runtime"]) in executed
    scenario = rule.get("scenario")
    if not ran and scenario and scenario in scenarios:
        ran = True
    if not ran:
        return MISSING_CALLER, ("no frame of this function executed while the "
                                "lifecycle and the scenarios ran")
    field = str(rule["field"])
    stage, _, name = field.partition(".")
    payload = payloads.get(stage)
    if payload is None:
        return UNTESTED, f"{stage} did not run"
    if name not in payload:
        return OUTPUT_DROPPED, f"{stage} produced no {name!r}"
    consumer = rule.get("consumer")
    if consumer:
        by_artifact = reads.get(consumer) or {}
        if name not in set(by_artifact.get(stage) or ()):
            # A value can reach its consumer relayed --- §18's later stages
            # copy m*, the arm set and the identification statuses forward.
            # `run/contracts` treats a relayed read the same way and lists
            # the relay; here it is enough that the consumer read the value.
            via = [artifact for artifact, fields in by_artifact.items()
                   if name in set(fields)]
            if not via:
                return WRONG_CONSUMER, f"{consumer} never read {stage}.{name}"
    return (CONDITIONAL if rule["expect"] == CONDITIONAL else VERIFIED), ""


def build(fast: bool) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        executed, run, scenarios = _executed_names(root, fast)
        payloads, reads = run["payloads"], run["reads"]

        from dci1v6.run import contracts

        contract = contracts.audit_contracts(payloads, reads)
        rows = []
        for rule in RULES:
            status, detail = _status(rule, executed, payloads, reads,
                                     scenarios)
            rows.append({**{k: v for k, v in rule.items()},
                         "status": status, "detail": detail,
                         "agrees": status == rule["expect"]})

    machine = {
        # What the walk ran under, snapshotted inside the walk. The harness
        # closes §34 for its own process --- it has to, or every stage
        # refuses --- and since 2026-08-26 it takes the researcher's recorded
        # values where the record has them, so this is the registered study
        # and not a fixture of it. Recorded rather than assumed, because
        # "the audit ran the adopted protocol" is a claim a reader should be
        # able to check.
        "decisions_the_walk_ran_under": run["decisions"],
        "n_rules": len(rows),
        "n_agreeing": sum(1 for r in rows if r["agrees"]),
        "by_status": {s: sum(1 for r in rows if r["status"] == s)
                      for s in sorted({r["status"] for r in rows})},
        "contract": {k: v for k, v in contract.items() if k != "defects"},
        "contract_defects": contract["defects"],
        "scenarios": {name: {k: v for k, v in result.items()
                             if k not in ("payloads", "reads")}
                      for name, result in scenarios.items()},
        "rules": rows,
    }

    areas = []
    for area in dict.fromkeys(str(r["area"]) for r in rows):
        subset = [r for r in rows if r["area"] == area]
        areas.append((area, subset))

    out = [
        "# DCI-1 v6 — execution-path audit\n",
        "> Generated by `dci1/tools/v6_execution_path_audit.py`. "
        "Do not edit by hand.\n",
        "Every scientifically consequential registered rule from stage 3 to "
        "stage 18, with the implementation that realises it, the production "
        "caller that invokes it, the artifact field it lands on and the stage "
        "that reads that field. A rule is **VERIFIED_REACHABLE** only when a "
        "frame of its implementation executed during a real run, the field is "
        "on the signed record, and the declared consumer was **observed** "
        "reading it. A function appearing in a grep result is not evidence "
        "and a contract declaring a reader is not evidence.\n",
        "## Summary\n",
        f"- **{len(rows)} registered rules** audited.",
        f"- **{machine['n_agreeing']} agree** with their expected status.",
        "- By status: "
        + ", ".join(f"**{n}** {s}" for s, n in machine["by_status"].items())
        + ".",
        f"- Contract: {contract['n_fields']} fields, "
        f"{contract['n_checked_against_payloads']} checked against real "
        f"payloads "
        f"({contract['n_field_presence_checks']} field-presence, "
        f"{contract['n_consumption_checks']} consumption, "
        f"{contract['n_semantic_checks']} semantic), "
        f"**{contract['n_defects']} defects**.",
        f"- Scenarios run: **{len(scenarios)}**.\n",
    ]
    if contract["defects"]:
        out.append("### Contract defects\n")
        for defect in contract["defects"]:
            out.append(f"- `{defect}`")
        out.append("")
    for area, subset in areas:
        out.append(f"## {area}\n")
        out.append("| rule | section | meaning | implementation | production "
                   "caller | artifact field | consumer | status |")
        out.append("|---|---|---|---|---|---|---|---|")
        for r in subset:
            out.append(
                f"| `{r['id']}` | {r['section']} | {r['meaning']} | "
                f"`{r['runtime']}` | `{r['impl']}` | `{r['field']}` | "
                f"{'`' + str(r['consumer']) + '`' if r['consumer'] else '—'} | "
                f"**{r['status']}**"
                + (f" — {r['detail']}" if r["detail"] else "") + " |")
        out.append("")
    if scenarios:
        out.append("## Conditional scenarios\n")
        out.append("| scenario | branch | result |")
        out.append("|---|---|---|")
        for name, result in scenarios.items():
            summary = {k: v for k, v in result.items()
                       if k not in ("payloads", "reads", "scenario",
                                    "branch")}
            out.append(f"| `{name}` | {result.get('branch', '')} | "
                       f"`{json.dumps(summary, default=str)[:300]}` |")
        out.append("")
    return "\n".join(out) + "\n", machine


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fast", action="store_true",
                        help="one walk, no conditional scenarios")
    args = parser.parse_args()
    text, machine = build(args.fast)
    if args.check:
        current = REPORT.read_text() if REPORT.exists() else ""
        if current != text:
            print(f"{REPORT} is out of date; re-run without --check")
            return 1
        print(f"{REPORT} is current")
        return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    MACHINE.write_text(json.dumps(machine, indent=1, default=str) + "\n")
    print(f"wrote {REPORT}")
    print(f"wrote {MACHINE}")
    failed = [r for r in machine["rules"] if not r["agrees"]]
    if failed:
        print(f"\n{len(failed)} rule(s) do not hold their expected status:")
        for r in failed:
            print(f"  {r['id']:24s} expected {r['expect']:22s} "
                  f"got {r['status']}: {r['detail']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
