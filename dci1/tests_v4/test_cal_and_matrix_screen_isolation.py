"""The calibration and matrix screens must not be able to touch the study.

Two risks specific to these two screens:

* the calibration screen runs the §12.3/§13.2 *procedure* on the registered
  calibration topics, so it looks like Gate 2 and Gate 3 and must not be able
  to become them;
* the matrix screen runs the registered §8.1 cell set, so it looks like the
  confirmatory experiment and must not be able to become that either -- and it
  must not spend the composed-validation topics Gate 4 depends on.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.engine.context import DCI1_ROOT, registered_context
from dci1v4.engine.guards import assert_registered_v4_input
from dci1v4.errors import ProvenanceGuardError
from dci1v4.protocol import constants as C
from dci1v4.protocol import seeds as v4seeds
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID

from bgrid_screen_v4 import plan as bgpl
from cal_screen_v4 import admission as ad
from cal_screen_v4 import plan as calpl
from fs_screen_v4 import plan as fspl
from matrix_screen_v4 import estimators as est
from matrix_screen_v4 import plan as mxpl
from matrix_screen_v4 import run as mxrun


# ------------------------------------------------------------- isolation
@pytest.mark.parametrize("tree", ["cal-screen-v4", "matrix-screen-v4"])
def test_screen_evidence_is_refused_as_v4_analysis_input(tree):
    context = registered_context()
    path = DCI1_ROOT / "evidence" / tree / "any" / "cache.jsonl"
    with pytest.raises(ProvenanceGuardError):
        assert_registered_v4_input(context, path)


def test_screens_write_only_under_their_own_roots():
    import cal_screen_v4.analysis, cal_screen_v4.run
    import matrix_screen_v4.analysis, matrix_screen_v4.run
    forbidden = ("evidence/dci1-v4", "evidence/dci1-v3", "evidence/br-pilot-v4",
                 "durable_root/dci1-v4")
    modules = (cal_screen_v4.run, cal_screen_v4.analysis,
               matrix_screen_v4.run, matrix_screen_v4.analysis)
    for module in modules:
        for line in Path(module.__file__).read_text().splitlines():
            if "write" not in line.lower():
                continue
            assert not any(f in line for f in forbidden), (
                f"{module.__name__} writes into another tree: {line.strip()}")


def test_every_screen_seed_root_is_distinct():
    roots = {fspl.SCREEN_ROOT_SEED, bgpl.SCREEN_ROOT_SEED,
             calpl.SCREEN_ROOT_SEED, mxpl.SCREEN_ROOT_SEED}
    assert len(roots) == 4
    domains = {fspl.DOMAIN_SCREEN_GENERATION, bgpl.DOMAIN_SCREEN_GENERATION,
               calpl.DOMAIN_SCREEN_GENERATION, mxpl.DOMAIN_SCREEN_GENERATION}
    assert len(domains) == 4
    assert not roots & {v4seeds.GENERATION_ROOT_SEED,
                        v4seeds.BOOTSTRAP_ROOT_SEED, v4seeds.TOPIC_SPLIT_SEED,
                        v4seeds.GATE1_SAMPLE_SEED}


def test_the_same_prompt_gets_a_different_seed_in_every_screen():
    seeds = {fspl.screen_seed("m", "deadbeef", 0),
             bgpl.screen_seed("m", "deadbeef", 0),
             calpl.screen_seed("m", "deadbeef", 0),
             mxpl.screen_seed("m", "deadbeef", 0)}
    assert len(seeds) == 4


def test_registered_constants_are_untouched():
    assert FOCAL_GRID == (7, 8, 9, 10)
    assert tuple(TARGET_GRID) == tuple(range(1, 9))
    assert C.REFERENCE_CALIPER == 0.10 and C.REFERENCE_VACUITY_MAX == 0.10
    assert C.REGIME_VACUITY_MAX == 0.10 and C.M_CAL == 4
    assert C.DELTA_R_GENERIC_THRESHOLD == 0.10
    assert C.DELTA_R_PAIR_SPECIFIC_THRESHOLD == 0.25


# --------------------------------- the admission decision is the registered one
def test_screen_admission_reproduces_the_registered_admission():
    proof = ad.assert_equivalent_to_registered()
    assert proof["identical"] is True
    assert proof["rungs_checked"] >= 7
    # the constructed input must actually exercise both outcomes, or the
    # equality is vacuous
    assert 0 < proof["admissible_rungs"] < proof["rungs_checked"]


def test_extended_grid_is_the_registered_b_rule():
    proof = ad.assert_extended_grid_is_registered_rule()
    assert proof["wordings"]["wordings_identical"] is True
    assert proof["scoring"]["agreement"] == 1.0
    assert proof["monotone"]["monotone"] is True


# --------------------------------------------------- the calibration screen
def test_calibration_screen_inherits_rather_than_restates():
    inherited = calpl.assert_inherited_definitions()
    assert inherited["stem_sentence"] == fspl.STEM_SENTENCE
    assert inherited["draws_per_cell"] == C.M_CAL
    assert inherited["candidate_families"] == ["CR7", "CR4", "CR6"]


def test_calibration_screen_uses_only_the_solo_topics():
    from dci1v4.topics.split import split_topics
    split = split_topics()
    topics = split["solo"]
    cells = calpl.build_cells(topics, [("RF1", 1)])
    used = {c.topic_id for c in cells}
    assert used == {t["topic_id"] for t in topics}
    for other in ("prescreen", "composed", "confirmatory"):
        assert not used & {t["topic_id"] for t in split[other]}


# -------------------------------------------------------- the matrix screen
def test_matrix_screen_refuses_the_gate_four_topic_set():
    for excluded in ("composed", "confirmatory", "sequestered"):
        assert excluded in mxrun.EXCLUDED_TOPIC_SETS
        assert excluded not in mxrun.TOPIC_SETS
    with pytest.raises(SystemExit):
        mxrun.build_design("gemma-3n-e2b-it", topic_sets=["composed"],
                           stem="floored")


def test_matrix_wording_allocation_is_the_registered_formula():
    for i in range(64):
        assert mxpl.wording_indices(i, 1) == (i % 4,)
        assert mxpl.wording_indices(i, 2) == (i % 4, (i + i // 4) % 4)


def _matrix_cells(n_blocks=8):
    constraints = [mxpl.Constituent("A", "A", 2), mxpl.Constituent("B", "B", 10),
                   mxpl.Constituent("R1", "CR7", 40),
                   mxpl.Constituent("R2", "CR4", 13),
                   mxpl.Constituent("R3", "CR6", 10)]
    spanning = [mxpl.Constituent("S1", "CR7", 32),
                mxpl.Constituent("S2", "CR7", 48)]
    topics = [{"topic_id": f"t{i}", "question": f"Q{i}?"} for i in range(n_blocks)]
    return mxpl.build_cells(topics, constraints, spanning, stem="floored")


def test_matrix_cell_set_is_exactly_section_8_1():
    cells = _matrix_cells()
    per_block = [c for c in cells if c.topic_id == "t0"]
    assert len([c for c in per_block if c.arm == "unconstrained"]) == 1
    solo = [c for c in per_block if c.arm == "solo"]
    composed = [c for c in per_block if c.arm == "composed"]
    assert len(solo) == 5
    assert len(composed) == 20
    pairs = {tuple(sorted(c.roles)) for c in composed}
    assert len(pairs) == 10
    for pair in pairs:
        orders = {c.order_label for c in composed if tuple(sorted(c.roles)) == pair}
        assert len(orders) == 2, f"{pair} does not carry both orders"


def test_matrix_allocation_assertion_refuses_a_structural_zero():
    cells = _matrix_cells(8)
    mxpl.assert_allocation(cells, 8)
    with pytest.raises(Exception):
        mxpl.assert_allocation([c for c in cells if c.order_label != "B_first"], 8)


def test_delta_r_algebra_matches_the_loss_difference():
    """§11.3: Delta_R written from composed cells must equal
    D(B<-A) - mean_j D(B<-R_j) computed from the losses."""
    blocks = [f"t{i}" for i in range(6)]
    table = {}
    values = {("B", "solo", "B"): 0.80,
              ("A|B", "A_first", "B"): 0.30, ("A|B", "B_first", "B"): 0.40,
              ("A|B", "A_first", "A"): 0.50, ("A|B", "B_first", "A"): 0.55,
              ("A", "solo", "A"): 0.70}
    for j, level in zip(est.REFERENCE_ROLES, (0.55, 0.60, 0.65)):
        values[(est.pair_key("B", j), "B_first", "B")] = level
        values[(est.pair_key("B", j), f"{j}_first", "B")] = level - 0.05
        values[(j, "solo", j)] = 0.72
        values[(est.pair_key("A", j), "A_first", "A")] = 0.60
        values[(est.pair_key("A", j), f"{j}_first", "A")] = 0.58
        values[(est.pair_key("A", j), "A_first", j)] = 0.40
        values[(est.pair_key("A", j), f"{j}_first", j)] = 0.42
        values[(est.pair_key("B", j), "B_first", j)] = 0.45
        values[(est.pair_key("B", j), f"{j}_first", j)] = 0.47
    for j in est.REFERENCE_ROLES:
        for k in est.REFERENCE_ROLES:
            if j == k:
                continue
            values[(est.pair_key(j, k), f"{j}_first", j)] = 0.50
            values[(est.pair_key(j, k), f"{k}_first", j)] = 0.52
    for key, level in values.items():
        table[key] = {b: level for b in blocks}

    out = est.per_block_contributions(table, blocks, order=None)
    direct = [out["D_B_from_A"][i]
              - sum(out[f"D_B_from_{j}"][i] for j in est.REFERENCE_ROLES) / 3
              for i in range(len(blocks))]
    assert all(abs(a - b) < 1e-12 for a, b in zip(direct, out["Delta_R"]))

    xi = [out["Delta_R"][i] - (out["D_Rbar_from_A"][i]
                              - out["D_Rbar_from_Rbar_prime"][i])
          for i in range(len(blocks))]
    assert all(abs(a - b) < 1e-12 for a, b in zip(xi, out["Xi"]))


def test_matrix_protocol_carries_the_no_revision_declaration():
    from matrix_screen_v4 import protocol as mxproto
    assert "may be revised" in mxproto.NO_REVISION_DECLARATION
    assert "§13.3" in mxproto.NO_REVISION_DECLARATION


# ------------------------------------------------ §8.6 is not a terminal status
def test_reduced_design_is_four_cells_and_carries_both_orders():
    constraints = [mxpl.Constituent("A", "A", 2), mxpl.Constituent("B", "B", 12)]
    topics = [{"topic_id": f"t{i}", "question": f"Q{i}?"} for i in range(8)]
    cells = mxpl.build_cells(topics, constraints, [], stem="floored",
                             reduced=True)
    per_block = [c for c in cells if c.topic_id == "t0"]
    # §8.6's two solo cells and A+B in both orders, plus the §25
    # accidental-compliance cell that every block carries.
    assert len(per_block) == 5
    assert {c.arm for c in per_block} == {"solo", "composed", "unconstrained"}
    assert len([c for c in per_block if c.arm == "unconstrained"]) == 1
    assert len([c for c in per_block if c.arm == "solo"]) == 2
    orders = {c.order_label for c in per_block if c.arm == "composed"}
    assert orders == {"A_first", "B_first"}
    mxpl.assert_allocation(cells, 8)


def test_reduced_design_refuses_a_spanning_arm():
    constraints = [mxpl.Constituent("A", "A", 2), mxpl.Constituent("B", "B", 12)]
    topics = [{"topic_id": "t0", "question": "Q?"}]
    with pytest.raises(Exception):
        mxpl.build_cells(topics, constraints,
                         [mxpl.Constituent("S1", "CR7", 32)], stem="floored",
                         reduced=True)


def test_reduced_design_still_identifies_the_three_section_13_5_quantities():
    blocks = ["t0", "t1", "t2"]
    values = {("A", "solo", "A"): 0.70, ("B", "solo", "B"): 0.80,
              ("A|B", "A_first", "A"): 0.50, ("A|B", "B_first", "A"): 0.55,
              ("A|B", "A_first", "B"): 0.30, ("A|B", "B_first", "B"): 0.40}
    table = {k: {b: v for b in blocks} for k, v in values.items()}
    out = est.per_block_contributions(table, blocks, order=None)
    assert out.get("_reduced_design")
    for name in ("D_B_from_A", "D_A_from_B", "Lambda"):
        assert name in out
    for name in ("Delta_R", "Xi", "D_R1_from_A"):
        assert name not in out
    assert abs(out["D_B_from_A"][0] - (0.80 - 0.35)) < 1e-12
    assert abs(out["D_A_from_B"][0] - (0.70 - 0.525)) < 1e-12


# ---------------------------------- the production-class companion (Δ_class)
def test_class_control_arm_is_five_cells_and_both_orders():
    constraints = [mxpl.Constituent("A", "A", 2), mxpl.Constituent("B", "B", 12),
                   mxpl.Constituent("R1", "CR7", 44),
                   mxpl.Constituent("R2", "CR4", 13),
                   mxpl.Constituent("R3", "CR6", 10)]
    topics = [{"topic_id": f"t{i}", "question": f"Q{i}?"} for i in range(4)]
    cells = mxpl.build_cells(topics, constraints, [], stem="floored",
                             class_control=mxpl.Constituent("C1", "CL7", 60))
    block = [c for c in cells if c.topic_id == "t0"]
    klass = [c for c in block if c.arm.startswith("class")]
    assert len(klass) == 5
    assert len([c for c in klass if c.arm == "class_solo"]) == 1
    for outcome in ("A", "B"):
        pair = [c for c in klass if set(c.roles) == {outcome, "C1"}]
        assert {c.order_label for c in pair} == {f"{outcome}_first", "C1_first"}
    mxpl.assert_allocation(cells, 4)


def test_delta_class_is_the_swap_with_class_held_fixed():
    blocks = ["t0", "t1"]
    values = {("A", "solo", "A"): 0.70, ("B", "solo", "B"): 0.80,
              ("C1", "solo", "C1"): 0.68,
              ("A|B", "A_first", "B"): 0.30, ("A|B", "B_first", "B"): 0.40,
              ("A|B", "A_first", "A"): 0.50, ("A|B", "B_first", "A"): 0.55,
              ("B|C1", "B_first", "B"): 0.60, ("B|C1", "C1_first", "B"): 0.64,
              ("B|C1", "B_first", "C1"): 0.50, ("B|C1", "C1_first", "C1"): 0.54,
              ("A|C1", "A_first", "A"): 0.60, ("A|C1", "C1_first", "A"): 0.62,
              ("A|C1", "A_first", "C1"): 0.44, ("A|C1", "C1_first", "C1"): 0.46}
    table = {k: {b: v for b in blocks} for k, v in values.items()}
    out = est.class_control_contributions(table, blocks, "C1")
    # D(B<-A) = 0.80 - 0.35 = 0.45 ; D(B<-C1) = 0.80 - 0.62 = 0.18
    assert abs(out["D_B_from_C1"][0] - 0.18) < 1e-12
    assert abs(out["Delta_class"][0] - (0.45 - 0.18)) < 1e-12
    assert abs(out["D_C1_from_B"][0] - (0.68 - 0.52)) < 1e-12
    assert abs(out["D_C1_from_A"][0] - (0.68 - 0.45)) < 1e-12


# ------------------- the `current` stem IS the registered prompt, byte for byte
def test_current_stem_render_is_the_registered_renderer():
    """The whole §12.4 finding is a claim about the REGISTERED design, so the
    screen's `current` arm has to be the registered prompt and not a lookalike."""
    from dci1v4.design.prompts import render as registered_render
    from fs_screen_v4.plan import render as screen_render

    question = "How does a bar of soap eventually wear away in the shower?"
    one = ["Use the word however exactly 2 times."]
    two = one + ["Every word in the answer must have at most 10 letters."]
    for lines in ([], one, two):
        assert registered_render(question, list(lines)) == screen_render(
            question, list(lines), "current")


def test_floored_stem_differs_from_the_registered_prompt_only_by_the_stem():
    from dci1v4.design.prompts import render as registered_render
    from fs_screen_v4.plan import STEM_SENTENCE, render as screen_render

    question = "Why do onions make people cry?"
    lines = ["Use the word however exactly 3 times."]
    floored = screen_render(question, lines, "floored")
    assert floored == registered_render(question, lines).replace(
        question, f"{question}\n\n{STEM_SENTENCE}", 1)


def test_lower_bound_families_are_reserved_for_the_class_arm():
    """A lower-bound reference would make Δ_R a mixed-class contrast, and on
    some models the same family would fill both the R slot and the class slot."""
    from cal_screen_v4.lowerbound_run import LOWER_BOUND_FAMILIES
    from matrix_screen_v4 import run as run_module

    source = Path(run_module.__file__).read_text()
    assert "LOWER_BOUND_FAMILIES" in source
    assert 'c["family"] not in LOWER_BOUND_FAMILIES' in source
    # and the reservation is stated on the frozen artifact, not only in code
    from matrix_screen_v4 import protocol as mxproto
    assert "reference_slots_exclude_lower_bound_families" in Path(
        mxproto.__file__).read_text()
    assert set(LOWER_BOUND_FAMILIES) == {"CL1", "CL7", "CL8"}


def test_rate_and_lower_bound_families_are_disjoint_and_both_are_candidates():
    from cal_screen_v4.analysis import RATE_FAMILIES
    from cal_screen_v4.lowerbound_run import LOWER_BOUND_FAMILIES
    from fs_screen_v4.constraints import CANDIDATES

    assert not set(RATE_FAMILIES) & set(LOWER_BOUND_FAMILIES)
    assert set(RATE_FAMILIES) | set(LOWER_BOUND_FAMILIES) <= set(CANDIDATES)
    for family in RATE_FAMILIES:
        assert CANDIDATES[family].form == "rate"
    for family in LOWER_BOUND_FAMILIES:
        assert CANDIDATES[family].form == "lower_bound"


def test_A_is_excluded_from_the_line_used_to_predict_A():
    """The V5 difficulty line and the length line must not be fitted through A.

    Both exist to ask whether A's delivery loss is what the *other* companions
    would predict. Fitting the line through A answers a different question and
    shrinks A's residual toward zero by construction -- badly so when A's
    predictor value sits away from the others, because then A carries most of
    the leverage. This was a real defect: with A in the fit, A's residual from
    the length line read within +/-0.010 on all four models; with A removed it
    is -0.117 to +0.126 and, on every model, an extrapolation.
    """
    from matrix_screen_v4 import analysis as mxa
    from matrix_screen_v4 import estimators as est

    # Both fits route through one helper, so the invariant is testable rather
    # than grep-able. A carries extreme leverage here on purpose: its x sits
    # outside the others, which is the case that made the original defect large.
    points = [
        {"companion": "A", "arm": "matched",
         "companion_solo_compliance": 0.20, "D_B_from_companion": 0.00},
        {"companion": "R1", "arm": "matched",
         "companion_solo_compliance": 0.64, "D_B_from_companion": +0.16},
        {"companion": "R2", "arm": "matched",
         "companion_solo_compliance": 0.66, "D_B_from_companion": -0.04},
        {"companion": "R3", "arm": "matched",
         "companion_solo_compliance": 0.60, "D_B_from_companion": 0.00},
        {"companion": "C1", "arm": "class_matched_production",
         "companion_solo_compliance": 0.68, "D_B_from_companion": +0.60},
        {"companion": "S1", "arm": "spanning",
         "companion_solo_compliance": 0.74, "D_B_from_companion": +0.05},
        {"companion": "S2", "arm": "spanning",
         "companion_solo_compliance": 0.80, "D_B_from_companion": +0.10},
    ]

    # 1. A is dropped, and so is the production-class companion.
    assert [p["companion"] for p in mxa.fit_points(points)] == [
        "R1", "R2", "R3", "S1", "S2"]

    def fitted(pts):
        kept = mxa.fit_points(pts)
        return est.weighted_least_squares(
            [p["companion_solo_compliance"] for p in kept],
            [p["D_B_from_companion"] for p in kept])

    # 2. The property that matters: A's own delivery loss cannot move the line
    #    that is then used to predict it. Under the old inline filter this held
    #    only by accident of the literal; here it is what the test checks.
    baseline = fitted(points)
    for injected in (-5.0, 0.0, +5.0, 1e6):
        moved = [dict(p, D_B_from_companion=injected)
                 if p["companion"] == "A" else p for p in points]
        assert fitted(moved) == baseline, (
            "A's observed value moved the line fitted to predict A: the fit is "
            "circular again")
        # ... and neither can the class companion's.
        moved_class = [dict(p, D_B_from_companion=injected)
                       if p["companion"] == "C1" else p for p in points]
        assert fitted(moved_class) == baseline

    # 3. The key must not advertise an exclusion the code does not perform.
    source = Path(mxa.__file__).read_text()
    assert "line_fitted_on_non_A_companions" not in source
    assert source.count("line_fitted_on_budget_companions_excluding_A") == 2


def test_residual_reports_whether_A_is_inside_the_fitted_range():
    """A residual from a line that extrapolates to A is not identified.

    On this companion set A is the only constraint that lengthens responses, so
    the length line never has A's x in its support. Saying so is the finding;
    silently reporting the residual would not be.
    """
    from matrix_screen_v4 import analysis as mxa

    inside = mxa._within_support(0.5, [0.2, 0.9])
    assert inside["inside"] is True
    assert inside["fitted_x_range"] == [0.2, 0.9]

    outside = mxa._within_support(15.0, [-9.0, -1.0])
    assert outside["inside"] is False
    assert "NOT identified" in outside["reading"]


def test_focal_losses_are_reported_beside_the_swaps():
    """Delta_j is a difference of two losses; both losses must be reportable.

    Delta_j = D(B<-A) - D(B<-R_j) hides which side moved. A swap of +0.13 built
    from D(B<-A)=+0.09 and D(B<-R_j)=-0.05 -- a reference that HELPS B -- is a
    different finding from one built from a reference that merely damages B
    less, and only the levels distinguish them.
    """
    from matrix_screen_v4.analysis import FAMILIES

    assert FAMILIES["focal_losses"] == (
        "D_B_from_R1", "D_B_from_R2", "D_B_from_R3")
    # every member is a quantity per_block_contributions actually produces
    from matrix_screen_v4 import estimators as est
    source = Path(est.__file__).read_text()
    assert 'out[f"D_B_from_{j}"] = loss("B", j)' in source
