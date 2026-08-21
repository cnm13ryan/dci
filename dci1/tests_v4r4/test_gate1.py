"""§10.7: v4r4's Gate-1 rule must bind in both directions.

A revision that removes a criterion is only trustworthy if the thing it puts
in its place is *harder* to satisfy than the thing it removed, and if the
removal cannot be quietly widened later. So these tests are written to fail if
the rule ever drifts toward permissiveness:

- reviewer agreement must be **unable** to pass the gate and **unable** to fail
  it, at any value, in either direction;
- a specification ambiguity must still stop it;
- every family and form of the final population must be audited, with no
  silent exemption;
- each defect class must be caught by a case that really separates it, checked
  by mutating the verifier and watching the audit notice;
- the independent implementation, the verifier hash and the wording hash must
  each be load-bearing, checked by breaking them one at a time;
- v4r3's §10.3 and §10.4 artifacts must stay readable and stay labelled as
  what they were, and v4r3's failed Gate-1 record must stay exactly as it is.

Several tests below mutate a *copy* of the evidence and assert the gate
refuses. That is the only way to show a condition is load-bearing: a rule that
passes on good evidence proves nothing about what it would do on bad.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError, TerminalStatus

from dci1v4r4.protocol import constants as C
from dci1v4r4.protocol.wordings import wordings
from dci1v4r4.stages.gate1 import (
    MEASUREMENT_RULE, collect_specification_evidence, gate1_payload,
    measurement_rule_hash,
)
from dci1v4r4.stages.microcase import DEFECT_KINDS
from dci1v4r4.stages.mutation import (
    mutation_corpus, run_mutation_validation, sensitivity,
)
from dci1v4r4.stages import specification as specification_module
from dci1v4r4.stages.specification import (
    SPEC_CASE_KINDS, SPEC_FIELDS, WORDING_CLASSES, applicability,
    audit_family, audit_severity, classify_wording, constraint,
    evaluate_specification, form_of, reading_verdict,
    run_specification_audit, spec_cases, specification, statistic_id_of,
    unmatched_wordings, wording_review, wordings_hash,
)
from dci1v4r4.verifiers import verifier_source_hash
from dci1v4r4.verifiers.boundary import ALL_CASES, instrument_population
from dci1v4r4.verifiers.compliance import passes
from dci1v4r4.verifiers.constraints import declared_range
from dci1v4r4.verifiers.statistics import STATISTICS, focal_statistic
from dci1v4.verifiers.target import s0_count

DCI1 = Path(__file__).resolve().parents[1]
REPORTS = DCI1 / "reports" / "dci1v4r4"
SUPERSEDED_REPORTS = DCI1 / "reports" / "dci1v4r3"

#: A family per predicate form. The whole population is exercised by the
#: population-coverage tests; the per-family tests use one of each form so the
#: suite stays inside a CPU minute.
ONE_PER_FORM = ("A", "B", "RF1", "CR1", "CL7", "CX1")


def _count(statistic_id: str, text: str) -> int:
    if statistic_id == "s0":
        return s0_count(text)
    if statistic_id == "focal":
        return focal_statistic(text)
    return STATISTICS[statistic_id](text)


@pytest.fixture(scope="module")
def audit():
    return run_specification_audit()


@pytest.fixture(scope="module")
def mutation():
    return run_mutation_validation()


@pytest.fixture(scope="module")
def evidence():
    path = REPORTS / "gate1_evidence.json"
    if not path.exists():                                # pragma: no cover
        pytest.skip("§10.2 evidence has not been produced in this tree")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def r5_evidence(audit, mutation):
    return collect_specification_evidence(specification=audit,
                                          mutation=mutation,
                                          wordings=wording_review())


GOOD_PROVENANCE = {"predecessor_verified": True, "carry_over_passed": True,
                   "reserved_sets_unspent": True,
                   "producing_commit": "0" * 40,
                   "no_gate1_record_exists_yet": True}


def _pass_once(evidence, r5_evidence, **overrides):
    """The gate on this tree's real evidence, with nothing substituted.

    v4r3's suite had to replace the wording review here, because v4r3's
    population did not satisfy condition 8 and no pass existed to test
    against. v4r4's does: §7.0-R4 removed the two families whose wordings
    named no bound. If a substitution ever becomes necessary again it belongs
    in the open, in this helper, and the test that needs it should say why.
    """
    clean = dict(r5_evidence)
    clean.update(overrides.pop("r5", {}))
    return gate1_payload(evidence=evidence, specification_evidence=clean,
                         provenance=dict(GOOD_PROVENANCE), **overrides)


# ------------------------------------------------------------------ 1 and 2

def test_reviewer_agreement_is_not_a_gate_condition_at_any_value(
        evidence, r5_evidence):
    """1. No human or autorater number can decide this gate, either way."""
    verdicts = []
    for agreement in (0.0, 0.5, 1.0):
        diagnostics = {"section_10_3": {"agreement": agreement,
                                        "status": "HUMAN_VALIDATION_"
                                                  "UNAVAILABLE"},
                       "section_10_4R2": {"outcome": "FAIL",
                                          "sensitivity": agreement}}
        record = _pass_once(evidence, r5_evidence,
                            supplementary_diagnostics=diagnostics)
        verdicts.append(record["outcome"])
        assert record["measurement_basis"] == C.MEASUREMENT_BASIS
    assert verdicts == ["PASS", "PASS", "PASS"], (
        "a reviewer agreement rate changed the gate's outcome")

    # And the reverse: perfect reviewer agreement cannot rescue a broken one.
    broken = copy.deepcopy(evidence)
    broken["determinism"]["agreement"] = 0.0
    with pytest.raises(TerminalStatus):
        _pass_once(broken, r5_evidence,
                   supplementary_diagnostics={"section_10_3":
                                              {"agreement": 1.0}})


def test_reviewer_evidence_cannot_override_the_deterministic_specification(
        evidence, r5_evidence):
    """2. A diagnostic that contradicts the predicate changes nothing."""
    contradicting = {"section_10_3": {"agreement": 1.0,
                                      "claims": "the verifier is wrong on "
                                                "every rate family"},
                     "human_says_verdicts_should_be_inverted": True}
    record = _pass_once(evidence, r5_evidence,
                        supplementary_diagnostics=contradicting)
    assert record["outcome"] == "PASS"
    assert record["supplementary_diagnostics"] == contradicting
    assert "no number under this key was read by the rule" in \
        record["supplementary_diagnostics_are_not_a_criterion"]
    # The recorded predicate still decides every verdict it is asked about.
    for kind in ONE_PER_FORM:
        spec = specification(kind)
        q = audit_severity(kind)
        for case in ALL_CASES[:40]:
            assert (evaluate_specification(spec, q, case["text"])
                    == passes(constraint(kind, q),
                              _count(spec["counted_statistic"],
                                     case["text"]), case["text"]))


# ------------------------------------------------------------------------ 3

def test_specification_ambiguity_still_blocks_the_gate(evidence, r5_evidence):
    """3. An unresolved reading stops Gate 1 with its own status."""
    ambiguous = copy.deepcopy(dict(r5_evidence))
    audit = copy.deepcopy(ambiguous["specification_audit"])
    audit["families"]["RF1"]["ambiguous"] = True
    audit["families"]["RF1"]["unresolved_readings"] = ["off_by_one"]
    audit["ambiguous_kinds"] = ["RF1"]
    audit["passed"] = False
    ambiguous["specification_audit"] = audit
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"specification_audit": audit})
    assert raised.value.status == "SPECIFICATION_AMBIGUOUS"
    assert 2 in raised.value.record["failed_conditions"]
    assert raised.value.record["measurement_basis"] is None


def test_an_incomplete_specification_record_blocks_the_gate(
        evidence, r5_evidence):
    """3, the other half: a missing field is not a pass."""
    audit = copy.deepcopy(r5_evidence["specification_audit"])
    audit["families"]["CR1"]["specification_complete"] = False
    audit["families"]["CR1"]["missing_fields"] = ["vacuity_rule"]
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"specification_audit": audit})
    assert 1 in raised.value.record["failed_conditions"]


# ------------------------------------------------------------------------ 4

def test_every_family_and_form_of_the_final_population_is_audited(audit):
    """4. No silent exemption, and the check is against the population."""
    population = sorted({k for k, _ in instrument_population()})
    assert audit["audited_kinds"] == population
    assert audit["uncovered_kinds"] == []
    # 30, not v4r3's 32: §7.0-R4 removed CP4 and CP7, and the two outcome
    # constraints are audited alongside the 28 families.
    assert len(population) == 30
    assert set(audit["forms"]) == {form_of(k) for k in population}
    for kind, family in audit["families"].items():
        assert not family["missing_fields"], kind
        assert set(SPEC_FIELDS) <= set(family["specification"]), kind
        built = {case["case_kind"] for case in family["cases"]}
        assert set(SPEC_CASE_KINDS) <= built, (kind, SPEC_CASE_KINDS - built)


def test_an_uncovered_family_blocks_the_gate(evidence, r5_evidence):
    audit = copy.deepcopy(r5_evidence["specification_audit"])
    audit["uncovered_kinds"] = ["RF9"]
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"specification_audit": audit})
    assert 1 in raised.value.record["failed_conditions"]


def test_the_recorded_predicate_reproduces_the_verifier_everywhere(audit):
    """A.2 is what makes the specification record load-bearing rather than
    decorative, so it is asserted here as well as inside the audit."""
    for kind, family in audit["families"].items():
        check = family["predicate_check"]
        assert check["agreement"] == 1.0, (kind, check["disagreements"])
        assert check["severities"] == len(declared_range(kind))
        assert check["comparisons"] > check["severities"]


def test_a_wrong_operator_in_the_record_is_caught_by_the_predicate_check():
    """The A.2 check must be able to fail. Flip an operator and watch it."""
    spec = dict(specification("RF1"))
    spec["formal_predicate"] = {**spec["formal_predicate"], "operator": ">="}
    q = audit_severity("RF1")
    statistic_id = spec["counted_statistic"]
    disagreements = [case["text"] for case in ALL_CASES
                     if evaluate_specification(spec, q, case["text"])
                     != passes(constraint("RF1", q),
                               _count(statistic_id, case["text"]),
                               case["text"])]
    assert disagreements, ("flipping the recorded operator changed no verdict "
                           "on the boundary corpus, so A.2 is not binding")


def test_a_dropped_vacuity_rule_in_the_record_is_caught():
    """The rate forms' 0/0 stipulation is in the record, and it matters."""
    spec = dict(specification("CR1"))
    spec["formal_predicate"] = {**spec["formal_predicate"],
                                "zero_denominator": "satisfies"}
    q = audit_severity("CR1")
    wordless = ",,, ;;; ..."
    assert evaluate_specification(spec, q, wordless) is True
    assert passes(constraint("CR1", q), STATISTICS["b_initial"](wordless),
                  wordless) is False


# ------------------------------------------------------------------------ 5

def test_mutation_cases_detect_the_defects_they_are_meant_to(mutation):
    """5. Every meaningful reading is exhibited by a separating case."""
    assert mutation["passed"]
    assert mutation["kinds_with_an_undetected_defect"] == []
    assert mutation["kinds_with_a_contradiction"] == []
    for defect, row in mutation["by_defect"].items():
        assert row["families_detected"] == row["families_where_meaningful"], \
            (defect, row["undetected_kinds"])
        if row["families_not_applicable"]:
            assert row["reasons_for_non_applicability"], defect
            assert row["not_applicable_kinds"], defect


def test_a_separating_case_really_separates(audit):
    """The claim is per-case and is re-derived here from the verifier."""
    for kind in ONE_PER_FORM:
        q = audit_severity(kind)
        statistic_id = statistic_id_of(kind)
        separators = [case for case in audit["families"][kind]["cases"]
                      if case["case_kind"].startswith("separator:")]
        assert separators, kind
        for case in separators:
            defect = case["case_kind"].split(":", 1)[1]
            assert case["text"] is not None, (kind, defect)
            registered = passes(constraint(kind, q),
                                _count(statistic_id, case["text"]),
                                case["text"])
            assert reading_verdict(kind, q, case["text"], defect) \
                != registered, (kind, defect)


def test_a_reading_declared_inapplicable_that_separates_is_a_contradiction():
    """The applicability rule is checked against the corpus, not believed.

    `denominator_swap` is declared inapplicable on every count form. Assert
    the corpus agrees, and then assert that the machinery would have noticed
    if it did not.
    """
    corpus = mutation_corpus("RF1")
    assert applicability("RF1")["denominator_swap"]["meaningful"] is False
    assert sensitivity("RF1", "denominator_swap", corpus)["discriminating"] \
        == 0
    # The same scan on a reading that *is* meaningful finds cases, so a zero
    # above is evidence and not an artefact of the scan.
    assert sensitivity("RF1", "off_by_one", corpus)["discriminating"] > 0


def test_an_undetected_defect_blocks_the_gate(evidence, r5_evidence):
    report = copy.deepcopy(r5_evidence["mutation_validation"])
    report["kinds_with_an_undetected_defect"] = ["CR3"]
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"mutation_validation": report})
    assert 6 in raised.value.record["failed_conditions"]


def test_every_defect_kind_is_covered_by_the_report(mutation):
    assert set(mutation["by_defect"]) == set(DEFECT_KINDS)
    assert set(mutation["defect_kinds"]) == set(DEFECT_KINDS)


# ------------------------------------------------------------------------ 6

def test_the_independent_reimplementation_is_still_required(evidence,
                                                            r5_evidence):
    """6. Removing it is not an option the amended rule offers."""
    for path, value in ((("reimplementation", "per_instrument_min"), 0.99),
                        (("reimplementation", "segmenter_differential",
                          "agreement"), 0.0)):
        broken = copy.deepcopy(evidence)
        target = broken
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(TerminalStatus) as raised:
            _pass_once(broken, r5_evidence)
        assert 4 in raised.value.record["failed_conditions"], path


def test_determinism_witnesses_and_boundary_suites_are_still_required(
        evidence, r5_evidence):
    cases = (
        (("determinism", "agreement"), 0.0, 3),
        (("suites", "agreement"), 0.0, 5),
        (("suites", "cases"), 3, 5),
        (("adversarial", "passed"), False, 5),
        (("witnesses", "passed"), False, 7),
        (("wordings", "passed"), False, 8),
    )
    for path, value, condition in cases:
        broken = copy.deepcopy(evidence)
        target = broken
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(TerminalStatus) as raised:
            _pass_once(broken, r5_evidence)
        assert condition in raised.value.record["failed_conditions"], path


# ------------------------------------------------------------------------ 7

def test_the_canonical_verifier_hash_is_required(evidence, r5_evidence):
    """7. Evidence produced under a different hash does not certify this
    verifier, and the gate says so rather than reporting a number."""
    stale = copy.deepcopy(evidence)
    stale["verifier_hash"] = "0" * 64
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(stale, r5_evidence)
    assert 9 in raised.value.record["failed_conditions"]
    assert evidence["verifier_hash"] == verifier_source_hash()


# ------------------------------------------------------------------------ 8

def test_changing_a_model_facing_wording_invalidates_dependent_evidence(
        evidence, r5_evidence):
    """8. A wording edit moves the wording hash, and a record bound to the old
    hash no longer certifies the population that is rendered now.

    §10.6 binds the *verifier* hash, which a wording cannot move: the wordings
    are not in `verifiers.SEMANTIC_MODULES` and they are not meant to be, since
    a wording changes what the model was asked and not what the program
    computes. That is exactly why R5 binds a second hash, and this test is the
    one that would notice if it stopped being bound.
    """
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"wordings_hash": "0" * 64})
    assert 9 in raised.value.record["failed_conditions"]

    # The hash is a function of the wordings themselves. Edit one word of one
    # wording of one instrument and the binding must move, or the amendment's
    # E clause is decorative.
    before = wordings_hash()
    assert before == r5_evidence["wordings_hash"]
    assert len({wordings_hash() for _ in range(3)}) == 1
    real = wordings
    edited = "RF1", audit_severity("RF1")

    def _edited(kind, severity):
        texts = list(real(kind, severity))
        if (kind, severity) == edited:
            texts[0] = texts[0].replace("At most", "At least")
        return tuple(texts)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(specification_module, "wordings", _edited)
    try:
        after = wordings_hash()
    finally:
        monkeypatch.undo()
    assert after != before, ("one edited wording did not move the hash the "
                             "record binds, so a silent wording change would "
                             "be invisible downstream")
    assert wordings_hash() == before

    # And evidence bound to the pre-edit hash is refused against the post-edit
    # population, which is what "invalidates dependent evidence" means here.
    with pytest.raises(TerminalStatus) as raised:
        _pass_once(evidence, r5_evidence, r5={"wordings_hash": after})
    assert 9 in raised.value.record["failed_conditions"]


def test_a_genuinely_ambiguous_wording_blocks_the_gate(evidence, r5_evidence):
    """A' is a Gate-1 condition, not a note.

    v4r3's population contained such a wording and this test simply ran the
    gate. v4r4's does not --- §7.0-R4 removed the two families carrying one ---
    so the finding has to be injected, and the injection is the v4r3 wording
    verbatim. If the gate ever stops blocking on it, this fails.
    """
    blocking = classify_wording("CL7", 20, 3,
                                "Give 20 percent of words letter a.")
    assert blocking["classification"] == "genuinely_ambiguous"
    ambiguous = {**r5_evidence,
                 "wording_review": {**r5_evidence["wording_review"],
                                    "genuinely_ambiguous": [blocking],
                                    "passed": False}}
    with pytest.raises(TerminalStatus) as raised:
        gate1_payload(evidence=evidence, specification_evidence=ambiguous,
                      provenance=dict(GOOD_PROVENANCE))
    assert raised.value.status == "SPECIFICATION_AMBIGUOUS"
    assert 8 in raised.value.record["failed_conditions"]


def test_a_wording_requiring_correction_blocks_the_gate(evidence,
                                                        r5_evidence):
    wrong = classify_wording("CL7", 20, 0, "At most 20 words may have a.")
    assert wrong["classification"] == "requires_correction"
    broken = {**r5_evidence,
              "wording_review": {**r5_evidence["wording_review"],
                                 "requires_correction": [wrong],
                                 "passed": False}}
    with pytest.raises(TerminalStatus) as raised:
        gate1_payload(evidence=evidence, specification_evidence=broken,
                      provenance=dict(GOOD_PROVENANCE))
    assert raised.value.status == "SPECIFICATION_AMBIGUOUS"
    assert 8 in raised.value.record["failed_conditions"]


def test_the_live_population_carries_no_blocking_wording(r5_evidence):
    """The v4r3 blocker is gone, and the gate is what says so."""
    review = r5_evidence["wording_review"]
    assert review["genuinely_ambiguous"] == []
    assert review["requires_correction"] == []
    assert review["passed"] is True
    assert unmatched_wordings() == []


def test_the_wording_review_covers_every_instrument_and_classifies_all_of_it():
    review = wording_review()
    assert review["instruments"] == len(instrument_population())
    assert review["wordings_checked"] == 4 * review["instruments"]
    # Every wording gets a direction verdict; the q=1 plural findings are
    # additional rows on top of those.
    directional = [f for f in review["findings"]
                   if f["finding"] != "plural_noun_at_q_equals_one"]
    assert len(directional) == review["wordings_checked"]
    for finding in review["findings"]:
        assert finding["classification"] in WORDING_CLASSES
        assert finding["why"]


def test_the_q_equals_one_plural_wordings_are_found_and_do_not_block():
    """The registered A' example, by name: *Exactly 1 semicolons ...*"""
    review = wording_review()
    plural = [f for f in review["findings"]
              if f["finding"] == "plural_noun_at_q_equals_one"]
    assert plural, "the q=1 plural mismatch was not detected"
    assert all(f["severity"] == 1 for f in plural)
    assert {f["classification"] for f in plural} == {"awkward_unambiguous"}
    assert any("semicolons" in f["wording"] for f in plural)
    # A' is what says these do not block: the numeral is unambiguous and it is
    # what the verifier reads.
    assert not [f for f in plural
                if f["classification"] in ("genuinely_ambiguous",
                                           "requires_correction")]


# ------------------------------------------------------------------------ 9

def test_the_old_section_10_3_and_10_4_artifacts_remain_readable():
    """9. Preserved, parseable, and labelled as what they were."""
    for name, expected in (("section_10_4R2_outcome.json", "FAIL"),
                           ("gate1_decision.json",
                            "GATE_1_BLOCKED_MEASUREMENT")):
        path = REPORTS / name
        if not path.exists():                            # pragma: no cover
            pytest.skip(f"{name} has not been produced in this tree")
        record = json.loads(path.read_text())
        assert record
        assert expected in json.dumps(record)


def test_the_record_never_calls_the_old_pathways_successful(evidence,
                                                            r5_evidence):
    record = _pass_once(evidence, r5_evidence,
                        supplementary_diagnostics={"section_10_4R2":
                                                   {"outcome": "FAIL"}})
    text = json.dumps(record)
    assert "retroactive" in text or "not a retroactive pass" in text
    assert record["measurement_basis"] != "human_validated"
    assert record["measurement_basis"] != "autorater_calibration_approved"
    assert record["scope_sentence"] == C.SCOPE_SENTENCE


def test_the_scope_sentence_attaches_and_cannot_be_dropped(evidence,
                                                           r5_evidence):
    record = _pass_once(evidence, r5_evidence)
    assert record["scope_sentence"] == C.SCOPE_SENTENCE
    assert record["scope_sentence_is_permanent"]
    with pytest.raises(ProtocolError):
        gate1_payload(evidence=evidence, specification_evidence=r5_evidence,
                         provenance=dict(GOOD_PROVENANCE),
                         measurement_basis="human_validated")


# ----------------------------------------------------------------------- 10

def test_the_gate_cannot_pass_unless_every_prerequisite_passes(evidence,
                                                               r5_evidence):
    """10. Ten conditions, and each one alone is enough to stop it."""
    assert _pass_once(evidence, r5_evidence)["outcome"] == "PASS"
    for key in ("predecessor_verified", "carry_over_passed",
                "reserved_sets_unspent", "producing_commit"):
        provenance = dict(GOOD_PROVENANCE)
        provenance[key] = False if key != "producing_commit" else ""
        clean = {**r5_evidence,
                 "wording_review": {**r5_evidence["wording_review"],
                                    "genuinely_ambiguous": [],
                                    "requires_correction": [],
                                    "passed": True}}
        with pytest.raises(TerminalStatus) as raised:
            gate1_payload(evidence=evidence, specification_evidence=clean,
                             provenance=provenance)
        assert 10 in raised.value.record["failed_conditions"], key


def test_the_measurement_rule_hash_is_stable_and_covers_the_rule():
    first = measurement_rule_hash()
    assert first == measurement_rule_hash()
    assert MEASUREMENT_RULE["section"] == "10.7"
    assert MEASUREMENT_RULE["revision"] == "v4r4"
    assert len(MEASUREMENT_RULE["conditions"]) == 10
    assert set(MEASUREMENT_RULE["components"]) == set("ABCDE")
    assert MEASUREMENT_RULE["measurement_basis"] == C.MEASUREMENT_BASIS
    # The rule says, in the artifact rather than only in prose, that no
    # reviewer quantity appears in it and what it does not establish.
    assert "agreement" in MEASUREMENT_RULE["no_reviewer_threshold"]
    assert "human_validated" in MEASUREMENT_RULE[
        "what_this_does_not_establish"]


def test_the_new_basis_is_registered_and_is_not_human_validated():
    assert C.MEASUREMENT_BASIS in C.MEASUREMENT_BASES
    assert C.MEASUREMENT_BASIS != "human_validated"
    assert "SPECIFICATION_AMBIGUOUS" in C.TERMINAL_STATUSES


def test_a_pass_record_carries_the_hashes_the_amendment_binds(evidence,
                                                              r5_evidence):
    record = _pass_once(evidence, r5_evidence)
    for key in ("measurement_rule_hash", "specification_hash", "mutation_hash",
                "wordings_hash", "frozen_verifier_hash", "boundary_suite_hash"):
        assert record[key], key
    assert record["frozen_verifier_hash"] == verifier_source_hash()
    assert record["instruments"] == len(instrument_population())


# --------------------------------------------------------- the A/B readings

def test_the_outcome_constraints_have_their_own_registered_readings():
    """A and B are audited too; the readings are §10.7's, not R2's."""
    for kind in ("A", "B"):
        family = audit_family(kind)
        assert "§10.7 A" in family["alternative_readings"]["source"]
        applies = family["alternative_readings"]["applicability"]
        assert applies["denominator_swap"]["meaningful"] is False
        for defect in ("numerator_swap", "inequality_flip", "off_by_one"):
            assert applies[defect]["meaningful"] is True


def test_a_s_segmentation_drift_is_section_7_3_and_not_its_own_rule():
    """§9.2 registers A as fold-then-segment, so the *drift* is §7.3's order.

    Reading it the other way would name A's own registered counter as the
    defect, which would make every A card wrong in the same direction.
    """
    q = audit_severity("A")
    text = "İhowever"
    assert s0_count(text) == 1
    assert reading_verdict("A", q, text, "segmentation_drift") is not \
        passes(constraint("A", q), s0_count(text), text)


def test_the_readings_for_the_families_are_the_frozen_r2_function():
    from dci1v4r4.stages.microcase import defect_verdict
    for kind in ("RF1", "CR1", "CL7", "CX1"):
        q = audit_severity(kind)
        for defect in DEFECT_KINDS:
            for case in ALL_CASES[:20]:
                assert (reading_verdict(kind, q, case["text"], defect)
                        == defect_verdict(constraint(kind, q), case["text"],
                                          defect))


def test_an_unregistered_reading_is_refused():
    with pytest.raises(ProtocolError):
        reading_verdict("RF1", 1, "point", "typo_in_the_prompt")


# ------------------------------------------------------- the audit's shape

def test_the_threshold_sweep_lands_where_it_says_it_does(audit):
    for kind in ONE_PER_FORM:
        q = audit_severity(kind)
        cases = {case["case_kind"]: case
                 for case in audit["families"][kind]["cases"]}
        for name, want in (("threshold_below", q - 1), ("threshold_at", q),
                           ("threshold_above", q + 1)):
            case = cases[name]
            if not case["constructed"]:
                continue
            assert case["derived"] == pytest.approx(float(want)), (kind, name)


def test_the_degenerate_answers_are_present_and_are_what_they_claim(audit):
    for kind, family in audit["families"].items():
        cases = {case["case_kind"]: case for case in family["cases"]}
        assert cases["empty_answer"]["text"] == ""
        wordless = cases["wordless_answer"]
        assert wordless["words"] == 0, kind
        if form_of(kind) in ("rate_budget", "rate_lower_bound"):
            assert wordless["registered_verdict"] is False, kind


def test_the_case_construction_is_deterministic():
    first = [case["text"] for case in spec_cases("CR1")]
    second = [case["text"] for case in spec_cases("CR1")]
    assert first == second
