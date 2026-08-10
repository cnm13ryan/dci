"""Every Stage 1 scientific hash must commit to the content it protects.

A hash over a hand-picked subset of a specification's fields is how a frozen
commitment quietly stops being covered. Four cases were live before this file:

  * `design.field_roles` hashed the seven role NAMES, so moving `f_a` from
    `outcome` to `diagnostic` - which changes what primary analysis may consume -
    altered no fingerprint;
  * `decoder.specification` omitted `forbidden_controls`, which is exactly the
    list the resolved-configuration assertion will check;
  * `controller.specification` omitted the seven section 9.7 prohibitions and the
    required per-generation instrumentation;
  * `proposal.law` omitted the seed derivation and its domain-separation key -
    the mechanism section 8.3 relies on for per-index independence.

The pair rule definitions were hashed nowhere at all.

The method here is mutation: change one scientifically relevant field, and assert
the fingerprint moves. That is stronger than asserting a field is present, because
it fails if the field is included in a way that cannot distinguish values.
"""
import dataclasses

import pytest

from dci.v19 import PROTOCOL_VERSION, field_roles, pairs, registry, specs
from dci.v19.registry import REGISTRY, Registry
from dci.v19.resolution import SlotTable, fixed
from dci.v19.specs import CONTROLLER, DECODER, PROPOSAL_LAW, frozen_state

pytestmark = pytest.mark.cpu


def state_of(name, value):
    """The state fingerprint of a one-slot table holding `value`."""
    return SlotTable.of(fixed(name, "probe", value)).state_fingerprint


def spec_state(spec):
    return state_of("spec", frozen_state(spec))


# ------------------------------------------------- the whole-object serialisation
def test_frozen_state_covers_every_declared_field():
    for spec, cls in [(DECODER, specs.DecoderSpec),
                      (CONTROLLER, specs.ControllerSpec),
                      (PROPOSAL_LAW, specs.ProposalLawSpec)]:
        got = frozen_state(spec)
        assert set(got) == {f.name for f in dataclasses.fields(cls)}


def test_frozen_state_refuses_a_non_specification():
    for bad in (specs.DecoderSpec, {"temperature": 0.7}, "decoder", None):
        with pytest.raises(TypeError, match="not a specification instance"):
            frozen_state(bad)


def test_an_equivalent_specification_hashes_identically():
    assert spec_state(DECODER) == spec_state(specs.DecoderSpec())


# ------------------------------------------------------------ decoder mutations
@pytest.mark.parametrize("field,value", [
    ("temperature", 0.71),
    ("top_p", 0.94),
    ("top_k", 50),
    ("do_sample", False),
    ("num_beams", 2),
    ("repetition_penalty", 1.05),
    ("no_repeat_ngram_size", 3),
    ("forbidden_controls", ("min_p",)),
])
def test_every_decoder_field_changes_the_specification_hash(field, value):
    mutated = dataclasses.replace(DECODER, **{field: value})
    assert spec_state(mutated) != spec_state(DECODER), field


def test_dropping_one_forbidden_control_changes_the_hash():
    """The omission that mattered: this list is what the assertion will check."""
    fewer = dataclasses.replace(
        DECODER, forbidden_controls=DECODER.forbidden_controls[:-1])
    assert spec_state(fewer) != spec_state(DECODER)


# --------------------------------------------------------- controller mutations
@pytest.mark.parametrize("field,value", [
    ("forced_transition_flag", "CAP_HIT"),
    ("final_truncated_flag", "TRUNCATED"),
    ("sample_token_beyond_allowance", True),
    ("cache_continues_within_generation", False),
    ("cache_crosses_generations", True),
    ("prohibited", ("best_of_n",)),
    ("required_instrumentation", ("hard_budget",)),
])
def test_every_controller_field_changes_the_specification_hash(field, value):
    mutated = dataclasses.replace(CONTROLLER, **{field: value})
    assert spec_state(mutated) != spec_state(CONTROLLER), field


def test_removing_a_section_nine_seven_prohibition_changes_the_hash():
    fewer = dataclasses.replace(CONTROLLER,
                                prohibited=CONTROLLER.prohibited[:-1])
    assert spec_state(fewer) != spec_state(CONTROLLER)


def test_removing_a_required_instrumentation_field_changes_the_hash():
    fewer = dataclasses.replace(
        CONTROLLER,
        required_instrumentation=CONTROLLER.required_instrumentation[:-1])
    assert spec_state(fewer) != spec_state(CONTROLLER)


# ------------------------------------------------------- proposal-law mutations
@pytest.mark.parametrize("field,value", [
    ("with_replacement", False),
    ("whole_proposal_rejection", False),
    ("repair_failed_proposal", True),
    ("default_within_stratum_pmf", "weighted"),
    ("seed_derivation", "counter-based BLAKE2"),
    ("seed_stream_key", ("pair", "draw_index")),
    ("backgrounds_at_max_load", 2),
    ("lower_load_backgrounds", 1),
])
def test_every_proposal_law_field_changes_the_specification_hash(field, value):
    mutated = dataclasses.replace(PROPOSAL_LAW, **{field: value})
    assert spec_state(mutated) != spec_state(PROPOSAL_LAW), field


def test_dropping_the_domain_separation_key_changes_the_hash():
    """Section 8.3's per-index independence rests on this key."""
    mutated = dataclasses.replace(PROPOSAL_LAW,
                                  seed_stream_key=("pair", "draw_index", "field"))
    assert spec_state(mutated) != spec_state(PROPOSAL_LAW)


# --------------------------------------------------------------- field roles
def test_the_registry_hashes_the_field_to_role_assignment():
    value = REGISTRY.slots.value("design.field_roles")
    assert isinstance(value, dict)
    assert value["outcome"] == list(field_roles.FIELD_ROLES["outcome"])


def test_moving_a_field_between_roles_changes_the_hash():
    """The exact defect: this used to alter nothing."""
    base = REGISTRY.slots.value("design.field_roles")
    moved = {role: list(fields) for role, fields in base.items()}
    moved["diagnostic"] = moved["diagnostic"] + ["f_a"]
    moved["outcome"] = [f for f in moved["outcome"] if f != "f_a"]
    assert state_of("design.field_roles", moved) != \
        state_of("design.field_roles", base)


def test_adding_a_field_to_a_role_changes_the_hash():
    base = REGISTRY.slots.value("design.field_roles")
    added = {role: list(fields) for role, fields in base.items()}
    added["treatment"] = added["treatment"] + ["new_column"]
    assert state_of("design.field_roles", added) != \
        state_of("design.field_roles", base)


def test_the_role_names_alone_are_no_longer_what_is_hashed():
    names_only = tuple(sorted(field_roles.FIELD_ROLES))
    assert REGISTRY.slots.value("design.field_roles") != names_only


# ------------------------------------------------------- hardware-selection rule
def test_the_structured_hardware_rule_is_hashed_not_just_the_prose():
    value = REGISTRY.slots.value("design.hardware_selection_rule")
    assert "summary" in value
    for key in ("primary_ranking_metric", "tie_breaks", "forbidden_inputs",
                "measured_quantities", "eligibility_preconditions"):
        assert key in value, key


@pytest.mark.parametrize("key,value", [
    ("primary_ranking_metric", "throughput"),
    ("tie_breaks", ("lexicographic_frozen_configuration_id",)),
    ("forbidden_inputs", ("dci_effect_estimate",)),
    ("measured_quantities", ("cost_per_1000_valid_logical_generations",)),
])
def test_changing_the_hardware_rule_changes_the_hash(key, value):
    base = REGISTRY.slots.value("design.hardware_selection_rule")
    mutated = {**base, key: value}
    assert state_of("design.hardware_selection_rule", mutated) != \
        state_of("design.hardware_selection_rule", base)


def test_reordering_the_tie_breaks_changes_the_hash():
    """The chain is applied in order, so its order is part of the commitment."""
    base = REGISTRY.slots.value("design.hardware_selection_rule")
    reversed_chain = {**base, "tie_breaks": tuple(reversed(base["tie_breaks"]))}
    assert state_of("design.hardware_selection_rule", reversed_chain) != \
        state_of("design.hardware_selection_rule", base)


# ------------------------------------------------------------ pair definitions
def test_the_pair_rule_definitions_are_now_hashed():
    value = REGISTRY.slots.value("design.pair_definitions")
    assert set(value) == set(pairs.PAIR_IDS)
    assert value["p1"]["target"]["constraint_id"] == \
        "v19:p1.target.exact_bullet_count"


@pytest.mark.parametrize("mutation", [
    ("statement", "Produce exactly N+1 bullet-list items."),
    ("constraint_id", "v19:p1.target.renamed"),
    ("family", "structural"),
    ("generative_scope", "sentence"),
    ("parameters", ["n_items", "extra"]),
    ("verifier_id", "v19:verifier.something_else"),
    ("verifier_callable", "v_exact_sentence_count"),
    ("verifier_span", "sentence_segmentation"),
])
def test_changing_any_pair_rule_field_changes_the_hash(mutation):
    field, value = mutation
    base = REGISTRY.slots.value("design.pair_definitions")
    mutated = {p: {k: (dict(v) if isinstance(v, dict) else v)
                   for k, v in body.items()} for p, body in base.items()}
    mutated["p1"]["target"][field] = value
    assert state_of("design.pair_definitions", mutated) != \
        state_of("design.pair_definitions", base)


def test_the_definition_hash_excludes_editorial_prose():
    """Rewording the risk commentary is not a protocol change."""
    value = REGISTRY.slots.value("design.pair_definitions")
    flat = repr(value)
    assert "measurement_risk" not in flat
    assert pairs.PAIR_1.measurement_risk not in flat


def test_the_definitions_record_the_four_reference_arms():
    value = REGISTRY.slots.value("design.pair_definitions")
    for pair in pairs.PAIR_IDS:
        assert value[pair]["reference_arms"] == ["R1", "R2", "R3", "R4"]


# --------------------------------------------------------- the registry overall
def test_the_registry_state_fingerprint_moves_with_any_of_these():
    """End to end: a specification edit must reach the registry's own hash."""
    base = REGISTRY.state_fingerprint
    for name, mutate in [
            ("decoder.specification",
             lambda v: {**v, "top_k": 40}),
            ("controller.specification",
             lambda v: {**v, "sample_token_beyond_allowance": True}),
            ("proposal.law",
             lambda v: {**v, "with_replacement": False}),
            ("design.field_roles",
             lambda v: {**v, "outcome": []}),
            ("design.hardware_selection_rule",
             lambda v: {**v, "primary_ranking_metric": "speed"}),
    ]:
        slots = SlotTable(slots=tuple(
            fixed(s.name, s.prereg, mutate(s.value)) if s.name == name else s
            for s in REGISTRY.slots))
        assert Registry(protocol=PROTOCOL_VERSION,
                        slots=slots).state_fingerprint != base, name


def test_the_declaration_fingerprint_is_unaffected_by_value_edits():
    """Declaration identity and freeze state remain separable."""
    slots = SlotTable(slots=tuple(
        fixed(s.name, s.prereg, {**s.value, "top_k": 40})
        if s.name == "decoder.specification" else s for s in REGISTRY.slots))
    assert Registry(protocol=PROTOCOL_VERSION,
                    slots=slots).fingerprint == REGISTRY.fingerprint


def test_no_ephemeral_runtime_value_entered_a_specification_hash():
    """Specification hashes must not drift between processes or runs."""
    import subprocess
    import sys
    code = ("from dci.v19 import registry; "
            "print(registry.REGISTRY.state_fingerprint)")
    seen = {subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, check=True).stdout.strip()
            for _ in range(2)}
    assert seen == {REGISTRY.state_fingerprint}


def test_the_registry_still_reports_nothing_fabricated():
    registry.assert_nothing_fabricated()
