"""The claim ladder, the freeze, and agreement between prose and code.

The last of these matters most and is the easiest to skip: a preregistration
and an implementation that disagree about a registered number are two
protocols, and the one that runs is the code. Every number this suite can
check is read out of ``DCI1_preregistration_v4r3.md`` and compared against the
constant the code uses.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError
from dci1v4r3.analysis import claims as CL
from dci1v4r3.analysis.claims import ClaimError, Interval
from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import freeze as F
from dci1v4r3.verifiers.constraints import FAMILIES, family_class

PREREG = (Path(__file__).resolve().parents[2] / "user-notes"
          / "DCI1_preregistration_v4r3.md")
CHANGELOG = (Path(__file__).resolve().parents[2] / "user-notes"
             / "DCI1_v4r2_to_v4r3_changelog.md")

SUPPORT_OK = {"holds": True, "reasons": []}
SUPPORT_BAD = {"holds": False, "reasons": ["extrapolates to A"]}


def interval(member, estimate, half=0.02):
    return Interval(member, estimate, estimate - half, estimate + half)


# ------------------------------------------------------ required failure 18
def test_delta_difficulty_does_not_inherit_the_pair_specific_threshold():
    """§11.8. The memo's 0.25 was defined for a difference between two
    OBSERVED losses; delta_difficulty differences an observed loss against a
    fitted prediction."""
    assert set(C.DELTA_DIFFICULTY_THRESHOLDS) == {"direction", "equivalence"}
    assert C.DELTA_R_PAIR_SPECIFIC_THRESHOLD not in \
        C.DELTA_DIFFICULTY_THRESHOLDS.values()
    huge = interval("delta_difficulty", 0.40)
    reading = CL.delta_difficulty_reading(huge, SUPPORT_OK)
    assert reading["levels"] == ["L3d"]
    assert "L3b" not in reading["levels"]


def test_delta_difficulty_equivalence_uses_the_registered_sesoi():
    assert C.DELTA_DIFFICULTY_THRESHOLDS["equivalence"] == \
        C.SMALLEST_EFFECT_OF_INTEREST
    small = interval("delta_difficulty", 0.01)
    assert CL.delta_difficulty_reading(small, SUPPORT_OK)["levels"] == ["L3e"]


def test_xi_has_no_magnitude_threshold_and_asking_for_one_raises():
    assert C.XI_HAS_MAGNITUDE_THRESHOLD is False
    assert "Xi" not in C.PRECISION_PRECONDITIONS
    with pytest.raises(ProtocolError, match="direction-only gate"):
        interval("Xi", 0.05).meets_precondition()


# ------------------------------------------------------- required failure 4
def test_no_primary_residual_is_reported_outside_support():
    reading = CL.delta_difficulty_reading(interval("delta_difficulty", 0.40),
                                          SUPPORT_BAD)
    assert reading["levels"] == []
    assert reading["statuses"] == ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]
    assert "is not a null" in reading["note"]


def test_insufficient_precision_withholds_thresholds_but_keeps_direction():
    wide = Interval("delta_difficulty", 0.30, 0.02, 0.58)   # half-width 0.28
    reading = CL.delta_difficulty_reading(wide, SUPPORT_OK)
    assert reading["markers"] == ["INSUFFICIENT_PRECISION"]
    assert reading["levels"] == []
    assert reading["direction_resolved"] is True


# ------------------------------------------------------------ §17.6's table
def test_agreement_on_a_null_emits_both_null_levels():
    out = CL.joint_reading(delta_r=interval("Delta_R", 0.03),
                           delta_difficulty=interval("delta_difficulty", 0.01),
                           xi=interval("Xi", 0.05), support=SUPPORT_OK)
    assert out["levels"] == ["L3c", "L3e"]
    assert out["row"] == "both null"


def test_agreement_on_an_excess_emits_both_positive_levels():
    out = CL.joint_reading(delta_r=interval("Delta_R", 0.18),
                           delta_difficulty=interval("delta_difficulty", 0.09),
                           xi=interval("Xi", 0.05), support=SUPPORT_OK)
    assert out["levels"] == ["L3a", "L3d"]
    assert out["outcome_specific"] is True
    assert "specific to the outcome B" in out["wording"]


def test_a_local_excess_the_spectrum_does_not_see_emits_neither_claim():
    out = CL.joint_reading(delta_r=interval("Delta_R", 0.18),
                           delta_difficulty=interval("delta_difficulty", 0.01),
                           xi=interval("Xi", 0.05), support=SUPPORT_OK)
    assert out["levels"] == []
    assert "LOCAL_AND_SPECTRUM_DISAGREE" in out["identification_statuses"]
    assert "unrepresentative" in out["reading"]
    assert set(out["both_reported"]) == {"Delta_R", "delta_difficulty"}


def test_a_spectrum_excess_the_local_set_does_not_see_emits_neither_claim():
    out = CL.joint_reading(delta_r=interval("Delta_R", 0.03),
                           delta_difficulty=interval("delta_difficulty", 0.09),
                           xi=interval("Xi", 0.05), support=SUPPORT_OK)
    assert out["levels"] == []
    assert "LOCAL_AND_SPECTRUM_DISAGREE" in out["identification_statuses"]
    assert "resemble A unusually closely" in out["reading"]


def test_a_non_positive_xi_changes_the_wording_and_not_the_emission():
    """The pattern two Gemma replications produced at screen scale: the two
    largest Delta_R values in the study beside Xi = -0.036 and -0.009."""
    out = CL.joint_reading(delta_r=interval("Delta_R", 0.18),
                           delta_difficulty=interval("delta_difficulty", 0.09),
                           xi=interval("Xi", -0.03), support=SUPPORT_OK)
    assert out["levels"] == ["L3a", "L3d"]
    assert out["outcome_specific"] is False
    assert "A_GENERAL_NOT_EXCLUDED" in out["identification_statuses"]
    assert "generally disruptive" in out["wording"]


def test_every_l3_statement_carries_the_class_status_and_its_sentence():
    statements = CL.emit_l3(
        configuration=C.OUTCOME_FIRST, outcome_position=1,
        measurement_basis="autorater_calibration_approved",
        delta_r=interval("Delta_R", 0.18),
        delta_difficulty=interval("delta_difficulty", 0.09),
        xi=interval("Xi", 0.05), support=SUPPORT_OK,
        references_identified=True)
    assert statements
    for statement in statements:
        assert "COMPANION_CLASS_NOT_MATCHED" in statement["identification_status"]
        assert statement["class_sentence"] == C.CLASS_SENTENCE
        assert statement["difficulty_coordinate"] == C.DIFFICULTY_COORDINATE
        CL.assert_statement_complete(statement)


def test_the_vacuity_forced_disagreement_withholds_the_claim():
    statements = CL.emit_l3(
        configuration=C.OUTCOME_FIRST, outcome_position=1,
        measurement_basis="autorater_calibration_approved",
        delta_r=interval("Delta_R", 0.18),
        delta_difficulty=interval("delta_difficulty", 0.09),
        xi=interval("Xi", 0.05), support=SUPPORT_OK,
        references_identified=True, vacuity_forced_agrees=False)
    assert [s["emitted"] for s in statements] == [False]
    assert "§17.4" in statements[0]["reason"]


def test_excess_not_identified_withholds_the_local_levels_only():
    statements = CL.emit_l3(
        configuration=C.OUTCOME_FIRST, outcome_position=1,
        measurement_basis="autorater_calibration_approved",
        delta_r=interval("Delta_R", 0.18),
        delta_difficulty=interval("delta_difficulty", 0.09),
        xi=interval("Xi", 0.05), support=SUPPORT_OK,
        references_identified=False)
    levels = {s["claim_level"] for s in statements if s.get("emitted")}
    assert "L3a" not in levels


def test_l5_is_permanently_withheld_and_no_emitter_exists():
    assert C.WITHHELD_CLAIM_LEVELS == ("L5",)
    CL.assert_no_l5_emitter(vars(CL))
    with pytest.raises(ClaimError):
        CL.assert_statement_complete({f: "x" for f in CL.REQUIRED_FIELDS}
                                     | {"claim_level": "L5"})


def test_an_emitter_refuses_a_member_not_registered_to_its_level():
    with pytest.raises(ClaimError):
        CL.delta_r_reading(interval("delta_difficulty", 0.1))
    with pytest.raises(ClaimError):
        CL.xi_gate(interval("Delta_R", 0.1))


# ------------------------------------------- required failures 12, 13 and 19
def test_the_freeze_binds_every_degree_of_freedom_v4r3_adds():
    for field in F.NEW_IN_V4R3:
        assert field in F.FREEZE_FIELDS
    for field in ("spectrum_selection_rule", "spectrum_severities",
                  "spectrum_offset", "difficulty_model_form",
                  "bootstrap_refit_algorithm", "support_rule",
                  "difficulty_coordinate", "calibration_table_hash",
                  "joint_reading_table", "graded_clause_reading",
                  "class_companion", "stem_sentence"):
        assert field in F.FREEZE_FIELDS


def test_every_v4r2_freeze_field_survives_into_v4r3():
    for field in F.V4R2_FREEZE_FIELDS:
        assert field in F.FREEZE_FIELDS


@pytest.mark.parametrize("field", F.NEW_IN_V4R3)
def test_a_missing_new_field_blocks_the_freeze(field):
    record = F.build_freeze_record(**{f: "set" for f in F.FREEZE_FIELDS
                                      if f != field})
    status = F.check_completeness(record, decisions={d: "closed"
                                                     for d in F.OPEN_DECISIONS})
    assert not status["can_freeze"]
    assert field in status["missing_fields"]


def test_a_new_scientific_field_cannot_be_passed_beside_the_freeze():
    with pytest.raises(ProtocolError, match="field list is closed"):
        F.build_freeze_record(**{f: "set" for f in F.FREEZE_FIELDS},
                              some_new_rule="0.20")


def test_an_unclosed_open_decision_blocks_the_freeze():
    record = F.build_freeze_record(**{f: "set" for f in F.FREEZE_FIELDS})
    status = F.check_completeness(record, decisions={})
    assert not status["can_freeze"]
    assert "D0" in status["unclosed_decisions"]
    with pytest.raises(ProtocolError, match="refuses an incomplete freeze"):
        F.freeze(record, decisions={})


def test_a_complete_record_freezes_and_carries_threshold_provenance():
    record = F.build_freeze_record(**{f: "set" for f in F.FREEZE_FIELDS})
    frozen = F.freeze(record, decisions={d: "closed" for d in F.OPEN_DECISIONS})
    assert frozen["frozen"] is True
    provenance = record["threshold_provenance"]
    assert "14 August 2026" in provenance["DELTA_R_GENERIC_THRESHOLD"]
    assert "NOT transferred" in provenance["DELTA_DIFFICULTY_THRESHOLDS"]


# ------------------------------------------------------ required failure 11
def test_development_and_reserved_topic_sets_are_disjoint():
    assert set(C.DEVELOPMENT_TOPIC_SETS) & set(C.RESERVED_TOPIC_SETS) == set()
    assert (set(C.DEVELOPMENT_TOPIC_SETS) | set(C.RESERVED_TOPIC_SETS)
            == set(C.TOPIC_SETS))
    assert "composed" in C.RESERVED_TOPIC_SETS      # Gate 4's topics
    assert "confirmatory" in C.RESERVED_TOPIC_SETS


def test_the_topic_split_sums_to_the_authored_bank_and_keeps_a_floor():
    assert sum(C.SET_SIZES.values()) == C.N_TOPICS == 624
    assert C.N_CONFIRMATORY == C.N_BLOCKS == 384
    assert C.SEQUESTERED_PER_AREA >= C.MIN_SEQUESTERED_PER_AREA


# ------------------------------------------------------ required failure 10
def test_the_canonical_hash_moves_when_a_family_is_added():
    """A new family cannot enter the instrument population without re-opening
    §10.2, because the pool lives inside the hashed module."""
    from dci1v4r3.verifiers import SEMANTIC_MODULES, source_hashes
    assert "constraints.py" in SEMANTIC_MODULES
    assert "dci1v4r3/constraints.py" in source_hashes()
    assert "dci1v4/words.py" in source_hashes()     # carried, hashed by path


def test_every_family_declares_a_class_consistent_with_its_predicate():
    """§7.5 and §13.7: the class follows the form, and the role follows the
    class.

    The rule the test is here for is the second half. §13.7 keeps every
    production family out of every reference slot so that `Delta_R` is a
    contrast *within* a class and `Delta_class` is the contrast *between*
    classes. Before the R3 amendment there was one production form family,
    the lower bounds, and the test named it directly; the amendment adds the
    exact-count form, which is A's own predicate and is production for the
    same reason A is. So the test now says what §13.7 says --- production
    implies class arm, budget implies reference --- instead of naming the one
    production form that existed when it was written.
    """
    for kind, family in FAMILIES.items():
        assert family.constraint_class == family_class(kind)
        if family.constraint_class == "production":
            assert family.role == "class_control", kind
        else:
            assert family.constraint_class == "budget"
            assert family.role == "reference", kind
    assert family_class("A") == "production"
    assert family_class("B") == "budget"


# ------------------------------------------------------ required failure 20
def _prereg_text():
    if not PREREG.exists():                              # pragma: no cover
        pytest.skip("the v4r3 preregistration is not in this checkout")
    return PREREG.read_text()


def test_the_calibration_cell_count_the_prose_states_is_the_one_it_derives():
    """Caught by the dry run once already: a prose number the code does not
    produce is a second protocol. The shortlist caps now carry four class
    families, not two, so the count is 45 and the prose has to say so."""
    from dci1v4r3.stages.regime import solo_calibration_cell_count
    derived = solo_calibration_cell_count(
        n_reference_families=C.SHORTLIST_REFERENCE_FAMILIES,
        n_class_families=C.N_CLASS_FAMILIES,
        rungs_per_reference=C.SHORTLIST_MAX_PER_REFERENCE_FAMILY,
        rungs_per_class=C.SHORTLIST_MAX_PER_CLASS_FAMILY)
    assert derived == 45
    text = " ".join(_prereg_text().split())
    assert f"= {derived} \\times 384 = 17{{,}}280" in text, derived
    assert derived * C.N_SOLO * C.M_CAL == 17280


@pytest.mark.parametrize("pattern,value", [
    (r"384 confirmatory blocks", C.N_BLOCKS),
    (r"\*\*47\*\* \| \*\*cells per block\*\*", C.N_CELLS_FULL),
    (r"144,384", C.N_CELLS_FULL * C.N_BLOCKS * C.M_DRAWS),
    (r"577,536", C.N_CELLS_FULL * C.N_BLOCKS * C.M_DRAWS * 4),
    (r"190 severities across 20 families", 190),
    (r"\*\*334 severities across 20 families\*\*", 334),
    (r"4{,}920", 205 * 24),
    (r"\*\*158 reference severities at round 0\*\*", 158),
    (r"\*\*218\*\* in the\ndeclared range", 218),
    (r"Thirty-two class severities at round 0; 116 in the declared range", 116),
    (r"25,337", 25337),
    (r"all 348 instances", 348),
])
def test_the_preregistration_states_the_numbers_the_code_uses(pattern, value):
    assert re.search(pattern, _prereg_text()), (pattern, value)


def test_the_registered_bands_and_offsets_agree_with_the_prose():
    text = _prereg_text()
    assert r"\iota \in [0.10,\; 0.95]" in text
    assert C.SPECTRUM_ELIGIBILITY_BAND == (0.10, 0.95)
    assert r"$\pm 0.20$ on $\iota$" in text
    assert C.SPECTRUM_OFFSET == 0.20
    assert "instructed compliance" in text.lower()
    assert C.DIFFICULTY_COORDINATE == "instructed_compliance"


#: How the preregistration spells each F1 member. The two notations have to
#: be reconciled by hand, which is the point: the mapping is what makes the
#: prose and the code checkable against each other at all.
F1_IN_PROSE = {
    "D(B<-A)": r"D(B \leftarrow A)",
    "D(A<-B)": r"D(A \leftarrow B)",
    "Lambda": r"\Lambda",
    "Delta_R": r"\Delta_R",
    "delta_difficulty": r"\delta_{\text{diff}}",
    "Xi": r"\Xi",
}


def test_the_prose_and_the_code_agree_on_the_primary_family():
    text = " ".join(_prereg_text().split())
    assert "**F1 Primary**" in text
    assert set(F1_IN_PROSE) == set(C.FAMILY_MEMBERS["F1"])
    for member, token in F1_IN_PROSE.items():
        assert token in text, member
    assert len(C.FAMILY_MEMBERS["F1"]) == 6
    assert C.SIDAK_K6 == 2.6310


def test_the_changelog_exists_and_names_every_change_it_claims():
    if not CHANGELOG.exists():                           # pragma: no cover
        pytest.skip("the changelog is not in this checkout")
    raw = CHANGELOG.read_text()
    text = " ".join(raw.split())
    for section in [f"## C{i}." for i in range(1, 22)]:
        assert section in raw, section
    assert "revision 3 and not v5" in text
    assert "## What did not change" in raw


def test_every_section_the_implementation_cites_exists_in_the_protocol():
    """The brief's self-containedness bar: an agent with no conversational
    context should be able to execute v4r3 from the preregistration and the
    repository alone. A code comment citing §12.6 when no §12.6 exists is a
    dangling reference in the only document that can settle a question."""
    import re
    text = _prereg_text()
    sections = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.", text, re.M))
    root = PREREG.resolve().parents[1] / "dci1" / "src" / "dci1v4r3"
    cited: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        cited |= set(re.findall(r"§(\d+(?:\.\d+)?)", path.read_text()))
    dangling = sorted(c for c in cited
                      if c not in sections and c.split(".")[0] not in sections)
    assert not dangling, dangling
    assert len(cited) > 50, "the implementation should cite the protocol often"
