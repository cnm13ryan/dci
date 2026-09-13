"""The analysis pipeline, end to end on synthetic rows.

Every number here is fabricated and no conclusion is drawn from any of it. The
point is the *shape*: that rows become cell means, that cell means become the
registered contrasts, that the contrasts become simultaneous intervals with
`delta_difficulty` refit inside every replicate, and that the guards refuse
what they are supposed to refuse.

§19 requires exactly this before any real generation: the full analysis
pipeline running to a structurally complete result table with a fitted
difficulty relation, a support diagnostic and a delta_difficulty row.
"""
from __future__ import annotations

import random

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r3.analysis import estimators as E
from dci1v4r3.analysis import run as R
from dci1v4r3.analysis.masking import (
    MASKED_VIEW_EXCLUDED_FIELDS, apply_mask, assert_delta_difficulty_not_masked,
    assert_mask_effective, assert_masked_view_clean, build_mask,
)
from dci1v4r3.analysis.observations import (
    ObservationTable, build_observations,
)
from dci1v4r3.design.cells import cell_types
from dci1v4r3.protocol import constants as C

M = 4
BLOCKS = 24
SPECTRUM_FAMILY = {"R1": "f_one", "R1-": "f_one", "R1+": "f_one",
                   "R2": "f_two", "R2-": "f_two", "R2+": "f_two",
                   "R3": "f_three", "R3-": "f_three", "R3+": "f_three"}

#: Fabricated per-slot behaviour: (solo compliance, chance compliance).
PROFILE = {
    "A": (0.62, 0.20), "B": (0.70, 0.05),
    "R1": (0.60, 0.10), "R1-": (0.45, 0.10), "R1+": (0.78, 0.10),
    "R2": (0.58, 0.12), "R2-": (0.40, 0.12), "R2+": (0.80, 0.12),
    "R3": (0.64, 0.08), "R3-": (0.48, 0.08), "R3+": (0.82, 0.08),
    "CL": (0.61, 0.15),
}


def _row(block, cell, arm, slots, draw, rng, *, chance=False):
    scores = []
    for position, slot in enumerate(slots, start=1):
        solo_p, chance_p = PROFILE[slot]
        p = chance_p if chance else solo_p
        if not chance and len(slots) == 2:
            p -= 0.12 if slot == "B" else 0.08     # a generic composed cost
        passed = rng.random() < p
        scores.append({
            "slot": slot, "kind": slot, "severity": 3, "position": position,
            "passed": passed, "graded": 1.0 if passed else 0.4,
            "non_vacuous": True, "vacuous_pass": False,
            "processing_failure": False})
    return {"block_id": block, "cell_id": cell, "arm": arm,
            "draw_index": draw, "scores": scores, "truncated": False,
            "word_count": 100.0}


def synthetic_rows(*, spectrum=True, class_arm=True, seed=11):
    rng = random.Random(seed)
    types = cell_types(reduced=False, class_arm=class_arm, spectrum=spectrum)
    all_slots = [s for s in C.REGISTERED_SLOT_ORDER
                 if any(s in t.slots for t in types)]
    rows = []
    for index in range(BLOCKS):
        block = f"blk{index:03d}"
        for cell in types:
            for draw in range(M):
                if cell.arm == "unconstrained":
                    # §25: the load-0 cell is scored against every instrument.
                    rows.append(_row(block, "unconstrained", "unconstrained",
                                     all_slots, draw, rng, chance=True))
                else:
                    rows.append(_row(block, cell.cell_id, cell.arm,
                                     list(cell.slots), draw, rng))
    return rows


@pytest.fixture(scope="module")
def table():
    return ObservationTable(
        build_observations(synthetic_rows(), m_draws=M))


# ------------------------------------------------------------- cell means

def test_a_partial_cell_never_becomes_a_cell_mean():
    rows = [r for r in synthetic_rows() if not
            (r["cell_id"] == "solo:B" and r["draw_index"] == 3)]
    with pytest.raises(IntegrityError) as excinfo:
        build_observations(rows, m_draws=M)
    assert "no draw is imputed" in str(excinfo.value)


def test_chance_observations_do_not_collide_with_solo_cells(table):
    # p(c | nothing stated) and p(c | c stated) are different quantities and
    # the difficulty coordinate is built from both. Indexing them together
    # would have raised "duplicate solo observation"; indexing them apart is
    # what makes the coordinate formable at all.
    assert table.chance("blk000", "A") is not table.solo("blk000", "A")
    assert table.has_chance("R1+")
    assert "unconstrained" not in table.slots()


def test_every_registered_cell_of_every_block_is_present(table):
    report = table.assert_within_block(expected_blocks=BLOCKS)
    assert report["cross_block_terms"] == 0
    assert report["design"] == "full"


def test_the_within_block_check_is_derived_not_a_full_matrix(table):
    # The spectrum and class arms pair with B alone. A full matrix would want
    # R1+ x R2- and ninety other cells no registered estimand reads.
    assert not table.has_composed("R1+", "R2-", C.OUTCOME_FIRST)
    table.assert_within_block()          # and it still passes


# ------------------------------------------------------------- estimators

def test_reference_slots_exclude_the_spectrum_rungs(table):
    # "R1-".startswith("R") is true, which is why the test is exact.
    assert E.reference_slots(table) == ("R1", "R2", "R3")
    assert set(E.spectrum_slots(table)) == set(C.SPECTRUM_SLOTS)


def test_the_two_algebraic_forms_of_delta_r_agree(table):
    for configuration in C.CONFIGURATIONS:
        E.assert_delta_r_forms(table, configuration)


def test_every_estimator_returns_one_value_per_block(table):
    configuration = C.OUTCOME_FIRST
    for vector in (E.delivery_loss(table, "B", "A", configuration),
                   E.asymmetry(table, configuration),
                   E.delta_r(table, configuration),
                   E.xi(table, configuration),
                   E.delta_class(table, configuration),
                   E.delta_a(table, configuration)):
        assert len(vector) == BLOCKS


def test_d_rbar_refuses_a_companion_inside_the_reference_set(table):
    with pytest.raises(ProtocolError):
        E.d_rbar_from(table, "R1", C.OUTCOME_FIRST)


# --------------------------------------------------------- the full family

@pytest.fixture(scope="module")
def analysis(table):
    spectrum_input = R.build_spectrum_input(
        table, C.OUTCOME_FIRST,
        family_of={k: v for k, v in SPECTRUM_FAMILY.items()})
    return R.analyse_configuration(
        table, C.OUTCOME_FIRST, spectrum_input=spectrum_input,
        design="full", seed=99, resamples=200)


def test_the_result_table_is_structurally_complete(analysis):
    assert set(analysis) >= {"F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
                             "F9"}
    f1 = analysis["F1"]["members"]
    for member in ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R",
                   "delta_difficulty", "Xi"):
        assert member in f1, member
        assert set(f1[member]) >= {"estimate", "se", "simultaneous",
                                   "half_width"}


def test_delta_difficulty_refits_inside_every_replicate(analysis):
    assert analysis["F1"]["members"]["delta_difficulty"]["refit_per_replicate"]
    # and the plain contrasts do not, because for them a replicate is a mean
    assert not analysis["F1"]["members"]["Delta_R"]["refit_per_replicate"]


def test_the_fit_coefficients_are_also_refit(analysis):
    for member in ("beta", "alpha_1"):
        assert analysis["F8"]["members"][member]["refit_per_replicate"]


def test_a_is_excluded_from_the_fit_that_predicts_a(table):
    spectrum_input = R.build_spectrum_input(
        table, C.OUTCOME_FIRST, family_of=dict(SPECTRUM_FAMILY))
    assert "A" not in spectrum_input.family_of
    assert C.CLASS_SLOT not in spectrum_input.family_of
    # ...and A's loss is still available to the estimator, as the thing the
    # fit is compared against rather than fitted to.
    assert "A" in spectrum_input.b_with


def test_the_class_companion_cannot_enter_the_fit(table):
    from dci1v4r3.analysis.spectrum import SpectrumInput
    with pytest.raises(ProtocolError):
        SpectrumInput(blocks=("b",), family_of={C.CLASS_SLOT: "f"},
                      b_solo=[0.5], b_with={"A": [0.4]},
                      companion_solo={C.CLASS_SLOT: [0.5]},
                      companion_chance={C.CLASS_SLOT: [0.1]},
                      a_solo=[0.6], a_chance=[0.2])


def test_the_no_spectrum_design_identifies_delta_r_but_not_delta_difficulty():
    rows = synthetic_rows(spectrum=False)
    t = ObservationTable(build_observations(rows, m_draws=M))
    t.assert_within_block(spectrum=False, expected_blocks=BLOCKS)
    result = R.analyse_configuration(t, C.OUTCOME_FIRST, spectrum_input=None,
                                     design="no_spectrum", seed=5,
                                     resamples=100)
    f1 = result["F1"]["members"]
    assert "Delta_R" in f1 and "Xi" in f1
    assert "delta_difficulty" not in f1
    assert "F8" not in result


def test_precision_and_the_f6_gate_are_reported(analysis):
    precision = R.precision_report(analysis)
    assert any(k.endswith("Delta_R") for k in precision)
    gate = R.f6_gate(analysis)
    assert gate["applicable"] and gate["threshold"] == C.F6_VACUITY_GATE


# ------------------------------------------------------------- masking

def test_the_mask_permutes_companions_and_is_effective(table):
    mask = build_mask(table.observations, namespace="pilot_mask", entropy=7)
    report = assert_mask_effective(table.observations, mask)
    assert report["min_differing_share"] >= C.MASK_MIN_DIFFERING_FRACTION
    masked = apply_mask(table.observations, mask)
    assert len(masked) == len(table.observations)
    # solo and chance observations carry no companion and are not permuted
    assert all(m.companion_label is None for m in masked
               if m.configuration is None)


def test_single_companion_groups_are_declared_unmaskable_not_silently_passed(
        table):
    """A property of v4r3's design, absent from v4r2's full matrix.

    The spectrum rungs and the class companion pair with B alone, so with one
    of them as the OUTCOME the only companion is B and a permutation of one
    element is the identity. "The companion was B" is not information because
    it could not have been anything else -- but the mask report has to say so
    rather than let the effectiveness check quietly skip it.
    """
    mask = build_mask(table.observations, namespace="pilot_mask", entropy=7)
    report = assert_mask_effective(table.observations, mask)
    unmaskable = {tuple(k) for k in report["structurally_unmaskable"]}
    outcomes = {k[0] for k in unmaskable}
    assert outcomes == set(C.SPECTRUM_SLOTS) | {C.CLASS_SLOT}
    # B, whose companion swaps carry every primary contrast, is maskable.
    assert "B" not in outcomes
    assert report["maskable_groups"] < report["groups"]
    assert report["min_differing_share"] >= C.MASK_MIN_DIFFERING_FRACTION


def test_the_masked_view_carries_no_companion_identifying_field(table):
    mask = build_mask(table.observations, namespace="pilot_mask", entropy=7)
    records = [m.__dict__ for m in apply_mask(table.observations, mask)]
    assert_masked_view_clean(records)
    for field in ("cell_id", "companion_slot", "raw_response"):
        assert field in MASKED_VIEW_EXCLUDED_FIELDS
        assert all(field not in r for r in records)


def test_delta_difficulty_may_not_appear_in_a_masked_phase_result(analysis):
    # A's point is inside the permuted group, so a masked value for it would
    # be a value against a permuted assignment of difficulties.
    with pytest.raises(IntegrityError):
        assert_delta_difficulty_not_masked({"families": analysis})
    clean = {"families": {"F2": analysis["F2"]}}
    assert_delta_difficulty_not_masked(clean)


def test_an_unregistered_mask_namespace_is_refused(table):
    with pytest.raises(ProtocolError):
        build_mask(table.observations, namespace="whatever", entropy=1)


# ------------------------------------------------- §20-R4: the stratified mask

def _observations_for(companions, blocks=384):
    """Solo and composed observations for one outcome with `n` companions."""
    from dci1v4r3.analysis.observations import Observation
    out = []
    for index in range(blocks):
        block = f"b{index:03d}"
        for companion in companions:
            out.append(Observation(
                block_id=block, cell_id=f"pair:B+{companion}", arm="composed",
                outcome_slot="B", companion_slot=companion, position=1,
                configuration="outcome_first", draws=8, compliance=0.5,
                graded=0.5, vacuity=0.0, truncation=0.0,
                non_vacuous_compliance=0.5, graded_threshold=0.5,
                response_words=80.0, processing_failures=0))
    return out


def test_a_two_companion_group_meets_the_criterion_every_time():
    """An independent uniform permutation moves a label with probability
    1 - 1/k, which for k = 2 is the threshold exactly, so the check failed
    about half the time on §8.6's reduced design."""
    from dci1v4r3.analysis.masking import assert_mask_effective, build_mask

    observations = _observations_for(("A", "CL"))
    for entropy in range(25):
        mask = build_mask(observations, namespace="pilot_mask",
                          entropy=entropy)
        report = assert_mask_effective(observations, mask)
        assert report["min_differing_share"] >= 0.5, entropy


def test_the_stratification_is_recorded_and_matches_the_group_size():
    import math

    from dci1v4r3.analysis.masking import build_mask
    from dci1v4r3.protocol import constants as C

    for companions in (("A", "CL"), ("A", "R1", "R2", "R3", "CL")):
        observations = _observations_for(companions, blocks=384)
        mask = build_mask(observations, namespace="pilot_mask", entropy=1)
        entry = mask["stratification"]["B|outcome_first"]
        target = max(C.MASK_MIN_DIFFERING_FRACTION,
                     1.0 - 1.0 / len(companions))
        assert entry["companions"] == len(companions)
        assert entry["non_identity"] == math.ceil(384 * target)


def test_a_moved_block_has_no_companion_left_in_place():
    """A chosen block gets a permutation with no fixed point, so 'moved' is a
    property of the block and not of one label in it."""
    from dci1v4r3.analysis.masking import build_mask

    companions = ("A", "R1", "R2", "R3", "CL")
    observations = _observations_for(companions, blocks=64)
    mask = build_mask(observations, namespace="pilot_mask", entropy=3)
    by_block: dict[str, list[bool]] = {}
    for obs in observations:
        key = f"B|outcome_first|{obs.block_id}|{obs.companion_slot}"
        by_block.setdefault(obs.block_id, []).append(
            mask["mapping"][key] != obs.companion_slot)
    for block, moved in by_block.items():
        assert all(moved) or not any(moved), block


def test_the_mask_is_still_unpredictable_from_registered_values_alone():
    """Stratifying fixes how many blocks move, which is a constant anyone can
    compute. It must not fix which."""
    from dci1v4r3.analysis.masking import build_mask

    observations = _observations_for(("A", "R1", "R2", "R3", "CL"), blocks=64)
    first = build_mask(observations, namespace="pilot_mask", entropy=11)
    second = build_mask(observations, namespace="pilot_mask", entropy=12)
    assert first["mapping"] != second["mapping"]
    assert (first["stratification"]["B|outcome_first"]["non_identity"]
            == second["stratification"]["B|outcome_first"]["non_identity"])
