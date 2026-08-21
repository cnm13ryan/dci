"""The 47-cell plan, the §8.4 allocation, and the three gate payloads.

Two of these pin registered *defect resolutions* rather than preferences:
§12.4's graded clause is read as a share, and the focal grid escalates rather
than widening. Both were ambiguities in v4r2 that its code did not settle, and
both are now shapes the code refuses to leave open.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from dci1v4.errors import InstrumentError, ProtocolError
from dci1v4r3.design import cells as D
from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import gates as G
from dci1v4r3.stages import regime as R
from dci1v4r3.verifiers.constraints import Constraint, focal_severities


@dataclass(frozen=True)
class Block:
    block_id: str
    index: int
    topic_id: str


def blocks(n):
    return [Block(f"b{i:04d}", i, f"t{i:04d}") for i in range(n)]


# ------------------------------------------------------------- the cell plan
def test_the_block_carries_forty_seven_cells_derived_from_its_arms():
    types = D.cell_types()
    assert len(types) == C.N_CELLS_FULL == 47
    by_arm = {}
    for t in types:
        by_arm[t.arm] = by_arm.get(t.arm, 0) + 1
    assert by_arm == {"unconstrained": 1, "solo": 12, "composed": 34}


def test_the_arm_counts_are_the_registered_ones():
    types = D.cell_types()
    composed = [t for t in types if t.arm == "composed"]
    core = [t for t in composed
            if all(s in C.CORE_SLOTS for s in t.slots)]
    spectrum = [t for t in composed
                if any(s in C.SPECTRUM_SLOTS for s in t.slots)]
    klass = [t for t in composed if C.CLASS_SLOT in t.slots]
    assert len(core) == C.N_CORE_COMPOSED_CELLS == 20
    assert len(spectrum) == C.N_SPECTRUM_COMPOSED_CELLS == 12
    assert len(klass) == C.N_CLASS_COMPOSED_CELLS == 2


def test_a_spectrum_companion_is_only_ever_paired_with_B():
    for t in D.cell_types():
        if t.arm != "composed":
            continue
        for slot in t.slots:
            if slot in C.SPECTRUM_SLOTS or slot == C.CLASS_SLOT:
                assert "B" in t.slots, (
                    f"{t.cell_id} pairs {slot} with something other than B; "
                    "crossing the spectrum with A or with itself would add "
                    "ninety cells no registered estimand reads")


# ------------------------------------------------------- required failure 7
def test_both_order_variants_of_every_composed_cell_are_in_every_block():
    plan = D.design_cells(blocks(8), draws=C.M_DRAWS)
    variants = {}
    for cell in plan:
        if cell.arm == "composed":
            key = tuple(sorted(cell.slots, key=D.slot_order_key))
            variants.setdefault(key, set()).add(cell.slots)
    assert variants, "no composed cells in the plan"
    for key, seen in variants.items():
        assert len(seen) == 2, f"{key} is not run in both orders"


def test_an_unbalanced_spectrum_arm_is_refused():
    """Dropping one order variant of a spectrum cell is refused.

    Two clauses of ``assert_allocation`` can catch it and the coverage clause
    fires first, because a variant that is absent everywhere also empties its
    own wording counts. The order clause is the second line of defence, for a
    variant that is present but short in some blocks.
    """
    plan = [c for c in D.design_cells(blocks(8))
            if not (c.arm == "composed" and c.slots == ("B", "R1+"))]
    with pytest.raises(ProtocolError,
                       match="structural zero|both order variants"):
        D.assert_allocation(plan, blocks_expected=8)


def test_a_structural_zero_in_the_wording_allocation_is_refused():
    plan = [c for c in D.design_cells(blocks(8))
            if not (c.arm == "solo" and c.slots == ("R2-",)
                    and c.wording_by_slot.get("R2-") == 3)]
    with pytest.raises(ProtocolError, match="structural zero|skew"):
        D.assert_allocation(plan, blocks_expected=8)


def test_the_registered_allocation_passes_its_own_assertion():
    D.design_cells(blocks(8), assert_allocation_over=8)


def test_wordings_and_order_are_orthogonal_by_construction():
    """The wording index follows the slot's place in the REGISTERED order, not
    its prompt position, which is what keeps the two factors independent."""
    plan = D.design_cells(blocks(8))
    for cell in plan:
        if cell.arm != "composed":
            continue
        ordered = tuple(sorted(cell.slots, key=D.slot_order_key))
        expected = dict(zip(ordered, D.wording_indices(cell.block_index, 2)))
        assert cell.wording_by_slot == expected


# ------------------------------------------------------- required failure 8
def test_every_cell_carries_exactly_M_draws():
    for cell in D.design_cells(blocks(4)):
        assert cell.draws == C.M_DRAWS


def test_the_configuration_of_a_cell_is_the_outcomes_position():
    """§11.1: not the slot order. Under a slot-order reading Delta_R would
    difference D(B<-A) with B second against D(B<-R_j) with B first."""
    plan = {(c.slots): c for c in D.block_cells(Block("b0", 0, "t0"))
            if c.arm == "composed"}
    ab = plan[("A", "B")]
    assert ab.configuration_of("B") == C.OUTCOME_SECOND
    assert ab.configuration_of("A") == C.OUTCOME_FIRST
    br = plan[("B", "R1")]
    assert br.configuration_of("B") == C.OUTCOME_FIRST


def test_the_reduced_design_drops_the_spectrum_and_keeps_the_class_arm():
    assert len(D.cell_types(reduced=True)) == C.N_CELLS_REDUCED_WITH_CLASS
    assert len(D.cell_types(reduced=True,
                            class_arm=False)) == C.N_CELLS_REDUCED
    slots = {s for t in D.cell_types(reduced=True) for s in t.slots}
    assert not slots & set(C.SPECTRUM_SLOTS)


# --------------------------------------------------- §12.4's graded clause
def test_the_graded_clause_refuses_a_summary_and_reads_a_distribution():
    with pytest.raises(ProtocolError, match="distribution, not a summary"):
        G.graded_degeneracy(0.995)


def test_the_share_reading_does_not_fire_on_an_in_band_focal_severity():
    """The v4r2 defect, pinned.

    B's graded score rises with compliance and crosses 0.99 inside the focal
    band, so a MEAN reading declares degenerate exactly the severities §12.3
    declares eligible. A share reading does not.
    """
    # A realistic B-solo distribution at an in-band severity: compliance 0.79,
    # and the responses that fail B fail it by one word out of thirty-odd, so
    # their graded score is just under 1.
    distribution = [1.0] * 79 + [0.97] * 21
    summary = G.graded_degeneracy(distribution)
    mean = sum(distribution) / len(distribution)
    assert mean > C.GRADED_DEGENERACY_HIGH        # the mean reading fires
    assert summary["share_above_high"] == pytest.approx(0.79)
    assert summary["share_above_high"] <= C.GRADED_DEGENERACY_SHARE_MAX


def test_the_share_reading_still_catches_a_genuinely_degenerate_constraint():
    summary = G.graded_degeneracy([1.0] * 100)
    assert summary["share_above_high"] == 1.0
    assert summary["share_above_high"] > C.GRADED_DEGENERACY_SHARE_MAX


# --------------------------------------------------------- §7.2's escalation
def test_the_focal_extension_is_not_selectable_by_default():
    with pytest.raises(InstrumentError, match="outside the registered"):
        Constraint("B", 11)
    assert Constraint("B", 11, extended=True).severity == 11
    assert focal_severities() == (7, 8, 9, 10)


def test_a_working_registered_grid_never_measures_the_extension():
    """A flat six-rung grid would move m* on a model that does not need it."""
    curve = {7: 0.41, 8: 0.67, 9: 0.71, 10: 0.88}
    out = G.select_focal_severity(curve)
    assert out["m_star"] == 10                   # nearest 0.80 inside the band
    assert out["extension_measured"] is False


def test_an_exhausted_registered_grid_asks_for_the_extension_before_selecting():
    curve = {7: 0.04, 8: 0.13, 9: 0.17, 10: 0.38}
    pending = G.select_focal_severity(curve)
    assert pending["m_star"] is None
    assert pending["extension_required"] is True
    resolved = G.select_focal_severity(curve, {11: 0.63, 12: 0.88})
    assert resolved["m_star"] == 12              # nearest 0.80 of the two
    assert resolved["extension_measured"] is True


def test_an_extension_rung_cannot_be_smuggled_into_the_registered_curve():
    with pytest.raises(ProtocolError, match="not in the registered focal"):
        G.select_focal_severity({7: 0.4, 11: 0.8})


def test_a_grid_exhausted_even_after_the_extension_is_terminal():
    with pytest.raises(G.TerminalStatus) as exc:
        G.select_focal_severity({7: 0.01, 8: 0.02, 9: 0.03, 10: 0.04},
                                {11: 0.05, 12: 0.06})
    assert exc.value.status == "FOCAL_RANGE_EXHAUSTED"
    assert C.TERMINAL_SENTENCE in exc.value.detail["terminal_sentence"]


# ----------------------------------------------------------------- Gate 2
def _gate2(**kw):
    base = dict(a_curve={n: 0.30 + 0.06 * n for n in C.TARGET_GRID},
                focal_registered_curve={7: 0.62, 8: 0.71, 9: 0.79, 10: 0.90},
                focal_extended_curve=None, b_solo_vacuity=0.02,
                graded_distributions={"A": [0.7] * 50 + [0.3] * 50,
                                      "B": [0.995] * 70 + [0.9] * 30},
                a_chance=0.0, b_chance=0.31)
    base.update(kw)
    return G.gate2_payload(**base)


def test_gate2_passes_a_regime_the_share_reading_admits():
    out = _gate2()
    assert out["outcome"] == "PASS"
    assert out["m_star"] == 9
    assert out["graded_clause_reading"] == "share"
    assert out["iota_a"] == pytest.approx(out["a_solo_compliance"])
    assert out["iota_b"] < out["b_solo_compliance"]


def test_gate2_fails_closed_on_the_registered_vacuity_maximum():
    with pytest.raises(G.TerminalStatus) as exc:
        _gate2(b_solo_vacuity=0.42)
    assert exc.value.status == "REGIME_NOT_FOUND"
    assert "never reported as a failure of the model" in exc.value.detail["note"]


# ----------------------------------------------------------------- Gate 4
def test_gate4_tests_every_cell_independently_and_computes_no_contrast():
    out = G.gate4_payload({"pair:A+B": {"A": 0.4, "B": 0.5},
                           "pair:B+R1-": {"B": 0.6, "R1-": 0.5}})
    assert out["computes_no_contrast"] and out["ranks_nothing"]
    with pytest.raises(G.TerminalStatus) as exc:
        G.gate4_payload({"pair:A+B": {"A": 0.4, "B": 0.99}})
    assert exc.value.status == "COMPOSED_HEADROOM_FAILURE"


# ------------------------------------------------------ §12.3's shortlist
def test_the_shortlist_reaches_for_rungs_a_fifth_of_the_scale_from_A():
    """v4r2's nearest-to-A shortlist is exactly the set that excludes them."""
    table = {f"RF1:{q}": {"solo": v, "chance": 0.0, "iota": v}
             for q, v in enumerate([0.20, 0.40, 0.58, 0.62, 0.80, 0.92])}
    picks = R.shortlist(table, iota_a=0.60)["RF1"]
    iotas = [table[f"RF1:{q}"]["iota"] for q in picks]
    assert any(v < 0.50 for v in iotas), iotas
    assert any(v > 0.70 for v in iotas), iotas


def test_a_shortlist_naming_an_unmeasured_rung_is_refused():
    table = {"RF1:3": {"solo": 0.6, "chance": 0.0, "iota": 0.6}}
    with pytest.raises(ProtocolError, match="unevaluable"):
        R.assert_shortlist_is_measured(table, {"RF1": [3, 4]})


def test_the_regime_record_cannot_be_written_without_that_guarantee():
    with pytest.raises(ProtocolError, match="unevaluable"):
        R.regime_screen_payload(
            selected_cap=768,
            difficulty_table={"RF1:3": {"solo": 0.6, "chance": 0.0,
                                        "iota": 0.6}},
            shortlist_table={"RF1": [3, 7]}, iota_a_prescreen=0.6,
            truncation_by_cell={}, screen_dir=".")


def test_the_ranking_puts_a_straddling_family_above_a_closer_one_that_cannot():
    table = {}
    for q, v in enumerate([0.61, 0.62]):
        table[f"RF1:{q}"] = {"solo": v, "chance": 0.0, "iota": v}
    for q, v in enumerate([0.35, 0.59, 0.85]):
        table[f"RF2:{q}"] = {"solo": v, "chance": 0.0, "iota": v}
    ranked = R.family_ranking(table, iota_a=0.60)
    assert ranked[0]["family"] == "RF2"
    assert ranked[0]["straddles"] and not ranked[1]["straddles"]
