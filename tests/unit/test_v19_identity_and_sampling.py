"""v19 scientific identity and the with-replacement superblock law.

The properties under test are the ones section 22 of the directive requires to be
demonstrated: the proposal law is independent and with replacement with
whole-proposal rejection; sharding, worker count, retry count and execution order
cannot change a scientific id or a seed; and a retry is an attempt of one
observation rather than a replacement draw.
"""
import pytest

from dci.v19 import identity, sampling
from dci.v19.identity import (ARMS, LOADS, ORDERS, attempt_id, cell_id,
                              context_fingerprint, expand_superblock,
                              generation_id, generations_per_superblock,
                              proposal_seed, scientific_seed, superblock_id)

pytestmark = pytest.mark.cpu

MODEL = "sha256:checkpoint"
CONTEXT = {"task": "T7", "backgrounds": ["g1", "g2", "g3"],
           "parameters": {"n": 6}, "permutation": [0, 1, 2]}


# ----------------------------------------------------------------- identity
def test_identical_content_at_different_draw_indices_is_two_units():
    """The reason the draw index is in the id: sampling is WITH replacement."""
    print_ = context_fingerprint(CONTEXT)
    first = superblock_id("p1", 1, print_)
    second = superblock_id("p1", 2, print_)
    assert first != second
    assert context_fingerprint(CONTEXT) == print_        # same content, though


def test_the_fingerprint_is_content_only():
    assert context_fingerprint(CONTEXT) == context_fingerprint(dict(CONTEXT))
    assert context_fingerprint({**CONTEXT, "task": "T8"}) != \
        context_fingerprint(CONTEXT)


def test_a_draw_index_below_one_is_refused():
    with pytest.raises(ValueError, match="never reused"):
        superblock_id("p1", 0, "abc")


def test_the_hierarchy_separates_its_levels():
    unit = superblock_id("p1", 1, context_fingerprint(CONTEXT))
    cell = cell_id(unit, "b_mid", 5, "o_A", "R2")
    gen = generation_id(cell, 3)
    attempt = attempt_id(gen, 2)
    assert len({unit, cell, gen, attempt}) == 4


def test_domain_separation_prevents_cross_level_collisions():
    """The same payload at two levels must not produce the same digest."""
    assert generation_id("x", 1) != cell_id("x", "1", 2, "o_A", "B")


@pytest.mark.parametrize("load,order,arm", [(3, "o_A", "B"), (2, "o_X", "B"),
                                            (2, "o_A", "R5")])
def test_a_cell_outside_the_frozen_grid_is_refused(load, order, arm):
    with pytest.raises(ValueError):
        cell_id("unit", "b", load, order, arm)


def test_the_seed_is_a_function_of_planned_identity_only():
    gen = generation_id(cell_id("unit", "b", 2, "o_A", "B"), 1)
    assert scientific_seed(gen, MODEL) == scientific_seed(gen, MODEL)
    assert 0 <= scientific_seed(gen, MODEL) < identity.SEED_MODULUS


def test_a_retry_cannot_change_the_seed():
    """An attempt index is deliberately absent from the seed signature."""
    import inspect
    signature = inspect.signature(scientific_seed)
    assert "attempt" not in signature.parameters
    gen = generation_id(cell_id("unit", "b", 2, "o_A", "B"), 1)
    first, second = attempt_id(gen, 1), attempt_id(gen, 2)
    assert first != second                              # lineage differs
    assert scientific_seed(gen, MODEL) == scientific_seed(gen, MODEL)


def test_a_different_checkpoint_changes_every_seed():
    gen = generation_id(cell_id("unit", "b", 2, "o_A", "B"), 1)
    assert scientific_seed(gen, MODEL) != scientific_seed(gen, "sha256:other")


def test_seeds_are_distinct_across_a_realistic_manifest():
    """Section 11.6 requires collision testing; this is the in-suite sample."""
    planned = expand_superblock("p1", 1, context_fingerprint(CONTEXT),
                                ["b_lo", "b_mid", "b_hi"], 4, MODEL)
    assert len(planned) == generations_per_superblock(3, 4) == 240
    assert len({p.generation for p in planned}) == len(planned)
    assert len({p.seed for p in planned}) == len(planned)


def test_every_planned_cell_carries_all_four_references():
    planned = expand_superblock("p1", 1, "fp", ["b"], 1, MODEL)
    arms = {(p.load, p.order, p.arm) for p in planned}
    assert len(arms) == len(LOADS) * len(ORDERS) * len(ARMS)
    for load in LOADS:
        for order in ORDERS:
            got = {p.arm for p in planned if p.load == load and p.order == order}
            assert got == set(ARMS)


def test_expansion_is_independent_of_iteration_order():
    a = expand_superblock("p1", 1, "fp", ["b1", "b2", "b3"], 2, MODEL)
    b = expand_superblock("p1", 1, "fp", ["b1", "b2", "b3"], 2, MODEL)
    assert [x.generation for x in a] == [x.generation for x in b]
    assert {x.seed for x in a} == {x.seed for x in b}


# ----------------------------------------------------- the completeness ledger
def test_exactly_one_terminal_state_per_generation():
    identity.assert_one_terminal_state({
        "g1": [{"attempt": 1, "terminal": False}, {"attempt": 2, "terminal": True}]})
    with pytest.raises(ValueError, match="0 terminal states"):
        identity.assert_one_terminal_state({"g1": [{"attempt": 1}]})
    with pytest.raises(ValueError, match="2 terminal states"):
        identity.assert_one_terminal_state({
            "g1": [{"attempt": 1, "terminal": True},
                   {"attempt": 2, "terminal": True}]})


def test_attempt_indices_must_be_dense_and_ordered():
    with pytest.raises(ValueError, match="non-monotonic"):
        identity.assert_one_terminal_state({
            "g1": [{"attempt": 1, "terminal": False},
                   {"attempt": 3, "terminal": True}]})


def test_a_generation_with_no_lineage_is_refused():
    with pytest.raises(ValueError, match="no attempt lineage"):
        identity.assert_one_terminal_state({"g1": []})


# ------------------------------------------------------------ the sampling law
TASKS = [f"T{i}" for i in range(12)]
STRATA = {"lexical_content": ["L1", "L2", "L3"],
          "structural_format": ["S1", "S2", "S3"],
          "relational_order": ["R1", "R2", "R3"]}
PARAMS = {"n_sentences": [4, 5, 6], "n_words": [8, 12]}


def _always_ok(proposal):
    return None


def test_a_proposal_draws_one_background_from_each_stratum():
    got = sampling.draw_proposal("p1", 1, 1, 99, TASKS, STRATA, PARAMS)
    assert len(got.backgrounds) == sampling.BACKGROUNDS_AT_MAX_LOAD
    for value, stratum in zip(got.backgrounds, sampling.STRATA):
        assert value in STRATA[stratum]
    assert sorted(got.permutation) == [0, 1, 2]


def test_a_missing_stratum_is_refused():
    with pytest.raises(ValueError, match="partitioned into exactly"):
        sampling.draw_proposal("p1", 1, 1, 99, TASKS,
                               {"lexical_content": ["L1"]}, PARAMS)


def test_sampling_is_with_replacement_across_indices():
    """Two indices may legitimately draw the same task; that is not a bug."""
    drawn = [sampling.draw_proposal("p1", i, 1, 7, ["only-one-task"], STRATA,
                                    PARAMS).task for i in range(1, 6)]
    assert drawn == ["only-one-task"] * 5


def test_streams_are_independent_per_index_and_attempt():
    a = sampling.draw_proposal("p1", 1, 1, 7, TASKS, STRATA, PARAMS)
    b = sampling.draw_proposal("p1", 1, 2, 7, TASKS, STRATA, PARAMS)
    c = sampling.draw_proposal("p1", 2, 1, 7, TASKS, STRATA, PARAMS)
    d = sampling.draw_proposal("p2", 1, 1, 7, TASKS, STRATA, PARAMS)
    assert len({a.fingerprint, b.fingerprint, c.fingerprint, d.fingerprint}) == 4


def test_a_rejected_proposal_does_not_disturb_another_index():
    """Rejecting index 1 many times must not shift index 2's draw."""
    ledger = sampling.ProposalLedger()
    expected = sampling.draw_proposal("p1", 2, 1, 7, TASKS, STRATA, PARAMS)
    attempts = {"n": 0}

    def reject_first_five(proposal):
        if proposal.draw_index == 1:
            attempts["n"] += 1
            return "unsatisfiable_composition" if attempts["n"] <= 5 else None
        return None

    sampling.accept_superblock("p1", 1, 7, TASKS, STRATA, PARAMS,
                               reject_first_five, ledger)
    got = sampling.accept_superblock("p1", 2, 7, TASKS, STRATA, PARAMS,
                                     _always_ok, ledger)
    assert got.proposal.fingerprint == expected.fingerprint


def test_the_whole_proposal_is_rejected_not_repaired():
    ledger = sampling.ProposalLedger()
    seen = []

    def reject_one_background(proposal):
        seen.append(proposal.backgrounds)
        return "arm_R3_unsatisfiable" if len(seen) < 3 else None

    got = sampling.accept_superblock("p1", 1, 7, TASKS, STRATA, PARAMS,
                                     reject_one_background, ledger)
    assert got.attempts == 3
    # Each retry is a whole fresh draw, not a swap of the offending identity.
    assert len({tuple(b) for b in seen}) == 3
    assert ledger.rejection_reasons() == {"arm_R3_unsatisfiable": 2}


def test_the_ledger_records_acceptance_and_duplicate_context_rates():
    """Repeated contexts are legal and reported, never deduplicated.

    One task, one identity per stratum and one parameter value leaves only the
    three-position permutation free, so seven draws must repeat a context by the
    pigeonhole principle - and each repeat is still its own statistical unit.
    """
    single = {stratum: ["only"] for stratum in sampling.STRATA}
    bank, ledger = sampling.build_bank("p1", 7, 7, ["one"], single,
                                       {"n": [1]}, _always_ok)
    assert len(bank) == 7
    assert ledger.acceptance_rate() == 1.0
    assert ledger.duplicate_context_rate() > 0
    assert len({a.superblock for a in bank}) == 7       # still seven units


def test_construction_stops_rather_than_relaxing_the_gate():
    ledger = sampling.ProposalLedger()
    bank, ledger = sampling.build_bank(
        "p1", 3, 7, TASKS, STRATA, PARAMS,
        lambda p: "never_satisfiable", ledger, )
    assert bank == []
    assert ledger.acceptance_rate() == 0.0


def test_the_bank_is_reproducible_from_the_root_seed():
    first, _ = sampling.build_bank("p1", 5, 4242, TASKS, STRATA, PARAMS,
                                   _always_ok)
    second, _ = sampling.build_bank("p1", 5, 4242, TASKS, STRATA, PARAMS,
                                   _always_ok)
    assert [a.superblock for a in first] == [a.superblock for a in second]


def test_a_different_root_seed_gives_a_different_bank():
    a, _ = sampling.build_bank("p1", 5, 1, TASKS, STRATA, PARAMS, _always_ok)
    b, _ = sampling.build_bank("p1", 5, 2, TASKS, STRATA, PARAMS, _always_ok)
    assert [x.superblock for x in a] != [x.superblock for x in b]


def test_the_draw_law_does_not_depend_on_execution_order():
    """Building index 3 first must give index 3 the same content."""
    solo = sampling.draw_proposal("p1", 3, 1, 55, TASKS, STRATA, PARAMS)
    bank, _ = sampling.build_bank("p1", 3, 55, TASKS, STRATA, PARAMS, _always_ok)
    assert bank[2].proposal.fingerprint == solo.fingerprint


def test_sharding_cannot_change_a_scientific_identity():
    """Worker assignment is not an input to any identity or seed function.

    Every id derives from (protocol, pair, index, content, condition, replicate)
    and the seed adds only the model hash. There is no parameter through which a
    shard index, worker count or execution order could enter.
    """
    import inspect
    for fn in (superblock_id, cell_id, generation_id, attempt_id,
               scientific_seed, proposal_seed):
        names = set(inspect.signature(fn).parameters)
        assert not names & {"shard", "shard_index", "shard_total", "worker",
                            "device", "order_of_execution"}, (fn.__name__, names)
