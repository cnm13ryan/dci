"""Tests for everything that could silently invalidate the scientific comparison.

None of these load a model. They are the checks that must pass before any GPU
time is spent, because each one guards a way the focal/reference contrast could
stop measuring interference while still producing plausible numbers.
"""
from __future__ import annotations

import pytest

from dci_exploratory import design, harvest

TASKS = [
    {"task_id": "T1", "split": "pilot", "topic": "Explain how a hinge lets a door swing."},
    {"task_id": "T2", "split": "pilot", "topic": "Explain how a funnel speeds up pouring."},
]


@pytest.fixture(scope="module")
def selection():
    return design.select(load=5)


@pytest.fixture(scope="module")
def rows(selection):
    return design.build_design(selection, TASKS, replicates=2, base_seed=7, stage="test")


# ------------------------------------------------------------------ selection
def test_selection_has_exactly_four_references(selection):
    from dci.v19.families import N_REFERENCES
    assert len(selection.references) == N_REFERENCES
    assert len(set(selection.references)) == N_REFERENCES


def test_references_exclude_the_target_and_focal(selection):
    assert selection.target not in selection.references
    assert selection.focal not in selection.references
    assert selection.focal not in selection.background
    assert selection.target not in selection.background


def test_every_selected_pair_is_jointly_satisfiable(selection):
    assert selection.satisfiability_audit
    assert all(r["satisfiable"] for r in selection.satisfiability_audit)


def test_references_are_hard_eligible_in_the_repository_sense(selection):
    chosen = {r["constraint_id"]: r for r in selection.candidate_audit}
    for ref in selection.references:
        assert chosen[ref]["hard_eligible"], f"{ref} is not hard-eligible"
        assert chosen[ref]["satisfiable_with_A"]
        assert chosen[ref]["satisfiable_with_B"]


def test_reference_weights_are_uniform_and_sum_to_one(selection):
    weights = selection.reference_weights()
    assert set(weights) == set(selection.references)
    assert pytest.approx(sum(weights.values())) == 1.0
    assert len(set(weights.values())) == 1


def test_selection_is_deterministic():
    first, second = design.select(load=5), design.select(load=5)
    assert first.references == second.references
    assert first.background == second.background


def test_background_carries_no_declared_length_side_effect(selection):
    # The registry's own audit flags comma-avoidance as shortening clauses, and
    # sentence length is what the focal constraint orders.
    assert "U_FMT_NOCOMMA" not in selection.background


def test_background_spans_distinct_families(selection):
    S = harvest.load()
    families = [S.CONSTRAINTS[c].u_family for c in selection.background]
    assert len(set(families)) == len(families), families


# --------------------------------------------------------------- design shape
def test_matched_assertions_pass(selection, rows):
    design.assert_matched(rows, selection)


def test_focal_and_reference_rows_share_the_underlying_instance(selection, rows):
    groups: dict[str, list] = {}
    for row in rows:
        if row.condition in ("focal", "reference"):
            groups.setdefault(row.pair_key, []).append(row)
    assert groups
    for group in groups.values():
        assert len({r.task_id for r in group}) == 1
        assert len({r.topic for r in group}) == 1
        assert {r.arm for r in group} == set(selection.arms)


def test_instruction_count_is_matched_across_arms(selection, rows):
    counts = {len(r.ordered_ids) for r in rows if r.condition in ("focal", "reference")}
    assert counts == {selection.load}


def test_focal_and_reference_prompts_differ_in_exactly_one_line(selection, rows):
    for pair_key in {r.pair_key for r in rows if r.condition == "focal"}:
        group = [r for r in rows if r.pair_key == pair_key
                 and r.condition in ("focal", "reference")]
        focal = next(r for r in group if r.condition == "focal")
        focal_lines = focal.user_prompt.splitlines()
        for reference in (r for r in group if r.condition == "reference"):
            ref_lines = reference.user_prompt.splitlines()
            assert len(focal_lines) == len(ref_lines)
            differing = [i for i, (a, b) in enumerate(zip(focal_lines, ref_lines)) if a != b]
            assert len(differing) == 1, (
                f"{pair_key}/{reference.arm}: prompts differ on lines {differing}")


def test_every_row_measures_the_target_in_the_contrast(selection, rows):
    for row in rows:
        if row.condition in ("focal", "reference"):
            assert row.measured == selection.target


def test_order_places_the_swapped_slot_where_it_claims(selection, rows):
    for row in rows:
        if row.condition not in ("focal", "reference"):
            continue
        positions = list(row.ordered_ids)
        target_at, arm_at = positions.index(selection.target), positions.index(row.arm)
        if row.order == design.ORDER_TARGET_FIRST:
            assert (target_at, arm_at) == (0, 1)
        else:
            assert (arm_at, target_at) == (0, 1)
        # Background never moves, so o_A and o_Q differ only in the first two.
        assert tuple(positions[2:]) == selection.background


def test_background_is_identical_across_all_arms(selection, rows):
    for row in rows:
        if row.condition in ("focal", "reference"):
            assert tuple(row.ordered_ids[2:]) == selection.background


def test_row_ids_are_unique(rows):
    ids = [r.row_id for r in rows]
    assert len(set(ids)) == len(ids)


def test_primitive_rows_measure_their_own_constraint(selection, rows):
    primitives = [r for r in rows if r.condition == "primitive"]
    assert {r.arm for r in primitives} == {selection.target, *selection.arms}
    for row in primitives:
        assert row.measured == row.arm
        assert row.ordered_ids == (row.arm,)


def test_extending_the_sample_preserves_earlier_instances(selection):
    """Stage C must add instances, not resample them."""
    small = design.build_design(selection, TASKS[:1], replicates=1, base_seed=7,
                                stage="test")
    large = design.build_design(selection, TASKS, replicates=1, base_seed=7,
                                stage="test")
    assert {r.row_id for r in small} <= {r.row_id for r in large}


# ------------------------------------------------------------ matching guards
def test_assert_matched_rejects_a_missing_arm(selection, rows):
    broken = [r for r in rows if not (r.pair_key == rows[0].pair_key
                                      and r.arm == selection.references[0])]
    with pytest.raises(ValueError, match="arms"):
        design.assert_matched(broken, selection)


def test_assert_matched_rejects_mismatched_instruction_count(selection, rows):
    import dataclasses
    broken = list(rows)
    victim = next(i for i, r in enumerate(broken) if r.condition == "reference")
    broken[victim] = dataclasses.replace(
        broken[victim], ordered_ids=broken[victim].ordered_ids[:-1])
    with pytest.raises(ValueError):
        design.assert_matched(broken, selection)


def test_assert_matched_rejects_a_swapped_underlying_task(selection, rows):
    import dataclasses
    broken = list(rows)
    victim = next(i for i, r in enumerate(broken) if r.condition == "reference")
    broken[victim] = dataclasses.replace(broken[victim], task_id="OTHER")
    with pytest.raises(ValueError, match="several tasks"):
        design.assert_matched(broken, selection)


def test_assert_matched_rejects_measuring_the_wrong_constraint(selection, rows):
    import dataclasses
    broken = list(rows)
    victim = next(i for i, r in enumerate(broken) if r.condition == "focal")
    broken[victim] = dataclasses.replace(broken[victim], measured=selection.focal)
    with pytest.raises(ValueError):
        design.assert_matched(broken, selection)


# ------------------------------------------------------------------ verifiers
def test_the_target_verifier_measures_the_target_rule():
    """A must be scored by sentence count against the configured N, nothing else."""
    S = harvest.load()
    n = int(S.CFG.exact_sentence_count)
    exact = " ".join(f"Sentence number {i} is here." for i in range(1, n + 1))
    assert S.verify(exact, "A").binary_pass == 1
    too_few = " ".join(f"Sentence number {i} is here." for i in range(1, n))
    assert S.verify(too_few, "A").binary_pass == 0
    too_many = " ".join(f"Sentence number {i} is here." for i in range(1, n + 2))
    assert S.verify(too_many, "A").binary_pass == 0


def test_the_target_verifier_ignores_whether_B_is_satisfied():
    """Compliance with A must not move when only B's property changes."""
    S = harvest.load()
    n = int(S.CFG.exact_sentence_count)
    increasing = " ".join(" ".join(["word"] * (3 + i)) + "." for i in range(n))
    decreasing = " ".join(" ".join(["word"] * (3 + n - i)) + "." for i in range(n))
    assert S.verify(increasing, "A").binary_pass == S.verify(decreasing, "A").binary_pass == 1
    # ...while B's own verifier does distinguish them, so the two rules are not
    # measuring the same thing.
    assert S.verify(increasing, "B").binary_pass == 1
    assert S.verify(decreasing, "B").binary_pass == 0


def test_unscorable_is_not_silently_a_failure():
    """An empty answer yields 'unscorable', which the runner must not count."""
    S = harvest.load()
    result = S.verify("", "A")
    assert result.status == "unscorable"


# ------------------------------------------- diagnostic runs (scaffold / arms)
def test_scaffold_is_part_of_the_matching_key(selection):
    """A focal row must be compared with references under the SAME scaffold.

    If the scaffold were not in `pair_key`, the intervention would pair scaffolded
    focal rows against unscaffolded reference rows and measure the scaffold
    instead of the arm.
    """
    rows = design.build_design(selection, TASKS, replicates=1, base_seed=7,
                               stage="test", scaffolds=("", "one_sentence_per_line"))
    design.assert_matched(rows, selection)
    for pair_key in {r.pair_key for r in rows if r.condition == "focal"}:
        group = [r for r in rows if r.pair_key == pair_key
                 and r.condition in ("focal", "reference")]
        assert len({r.scaffold for r in group}) == 1, pair_key


def test_scaffold_crossing_doubles_the_contrast_rows(selection):
    one = design.build_design(selection, TASKS, replicates=1, base_seed=7,
                              stage="test", scaffolds=("",))
    two = design.build_design(selection, TASKS, replicates=1, base_seed=7,
                              stage="test", scaffolds=("", "one_sentence_per_line"))
    contrast = lambda rs: [r for r in rs if r.condition in ("focal", "reference")]
    assert len(contrast(two)) == 2 * len(contrast(one))
    assert len({r.row_id for r in two}) == len(two)


def test_arms_override_replaces_the_panel_and_keeps_the_focal():
    chosen = ["S_SEMICOLON", "C_L3"]
    sel = design.select(load=5, arms_override=chosen)
    assert list(sel.references) == chosen
    assert sel.arms == (design.FOCAL_ID, *chosen)
    rows = design.build_design(sel, TASKS, replicates=1, base_seed=7, stage="test")
    design.assert_matched(rows, sel)


def test_arms_override_refuses_the_target_or_focal():
    with pytest.raises(ValueError, match="target or the focal"):
        design.select(load=5, arms_override=["B", "C_L3"])


def test_scaffold_text_is_appended_to_the_protocol_system_message():
    from dci_exploratory import runner
    base = harvest.load().SYSTEM_MESSAGE
    assert runner.system_message_for("") == base
    scaffolded = runner.system_message_for("one_sentence_per_line")
    assert scaffolded.startswith(base) and len(scaffolded) > len(base)
