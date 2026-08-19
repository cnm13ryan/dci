"""Anti-regression: superseded assumptions cannot be reintroduced.

Three corpora are guarded, and the guard is different for each because the
evidence about each is different.

**Against v3.** Every item below is a v3 design decision v4 replaces, and each
is checked structurally rather than by prose search.

**Against v4 revision 1, which is superseded.** Only what the corpus attests is
asserted, namely the items listed in ``DCI1_v4r2_changelog.md`` and the
revision 1 to revision 2 change table. No revision 1 parameter is invented in
order to ban it. In particular **no allocation is banned**: every row of the
§16.3 menu is a live entry the registered rule may select, so what is asserted
is that the selected allocation carries the menu-rule evidence that chose it.

**Against the legacy corpus.** Ingesting a DEPRECATED or FOREIGN artifact,
counting byte-identical replicate pairs as independent replicates, quoting a
scalar without its configuration, describing author-performed labels as
independent validation, and carrying a threshold without its provenance.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from dci1v4.analysis import claims, estimators, observations
from dci1v4.analysis.variance import select_allocation
from dci1v4.engine.context import DCI1_ROOT
from dci1v4.errors import ClaimError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.stages import freeze as freeze_stage

PACKAGE = DCI1_ROOT / "src" / "dci1v4"


def _all_bound_names() -> set[str]:
    bound: set[str] = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                bound.add(node.id)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                bound.add(node.name)
    return bound


BOUND = _all_bound_names()


# ------------------------------------------------------------- against v3
@pytest.mark.parametrize("name", [
    "primary_draw_index",      # the hash selector of one draw of sixteen
    "pseudo_run_index",        # the pseudo-run machinery
    "pseudo_runs",
    "target_first", "added_first",          # block-level order names
    "REFERENCE_POOL_MISMATCH",              # the terminal reference status
    "E2B_STOP_STATUSES",                    # the early-stop rule
    "failure_rate", "_rates",               # v3's failure-scale helper
    "composed_uptake", "uptake_caliper",
])
def test_v3_construct_is_absent(name):
    assert name not in BOUND, (
        f"{name!r} is bound somewhere in dci1v4; it is a superseded v3 "
        f"construct")


def test_no_draw_selector_exists_and_M_is_four():
    """T-10: v4 averages all M draws and has no selector."""
    assert C.M_DRAWS == 4
    for name in ("select_draw", "primary_draw", "chosen_draw",
                 "draw_selector"):
        assert name not in BOUND, name
    seeds = (PACKAGE / "protocol" / "seeds.py").read_text()
    assert "primary-root" not in seeds
    assert "mod 16" not in seeds


def test_order_is_a_cell_level_factor_not_a_block_stratum():
    """T-5: the block carries no order field and the v3 names are gone."""
    from dci1v4.topics.split import Block

    assert "order" not in Block.__dataclass_fields__
    assert set(C.ORDERS) == {"c1_first", "c2_first"}
    assert "target_first" not in C.ORDERS and "added_first" not in C.ORDERS


def test_every_configuration_uses_all_blocks_not_a_192_block_stratum():
    """The v3 pooling-within-an-order-stratum rule has no analogue."""
    # Every term of every contrast is looked up by the same block id, and the
    # block list is the whole table's, never an order stratum's.
    for fn in (estimators.solo_vector, estimators.composed_vector):
        assert "for b in table.blocks" in inspect.getsource(fn)
    assert "192" not in inspect.getsource(estimators)
    assert len(observations.CONFIGURATIONS) == 2


def test_reference_is_matched_to_A_on_compliance_not_to_B_on_failure():
    """T-8: the matching target and the scale are both inverted from v3."""
    from dci1v4.stages.gates import admit_family

    source = inspect.getsource(admit_family)
    # The matched quantity is A's solo COMPLIANCE, not B's solo failure rate.
    assert "a_mean = sum(a_calibration) / len(a_calibration)" in source
    assert "difference = mean - a_mean" in source
    for banned in ("b_calibration", "focal_compliance", "focal_solo",
                   "failure_rate", "solo_failure"):
        assert banned not in source, banned
    # B appears only where §13.2 condition 5 needs witnesses against it.
    assert source.count("FOCAL_GRID") == 1


def test_the_severity_grid_is_the_complete_integer_ladder():
    """v3 used a four-point grid; v4 fills the interiors."""
    assert C.N_LADDER_SEVERITIES == 94
    for family, ladder in C.REFERENCE_LADDERS.items():
        assert list(ladder) == list(range(0, ladder[-1] + 1)), family
        assert len(ladder) > 4, family


def test_gate3_is_not_terminal_and_the_status_is_an_identification_status():
    from dci1v4.stages.gates import gate3_payload

    result = gate3_payload([], n_star=3)
    assert result["outcome"] == "PASS"
    assert result["identification_statuses"] == ["EXCESS_NOT_IDENTIFIED"]
    assert "EXCESS_NOT_IDENTIFIED" in C.IDENTIFICATION_STATUSES
    assert "EXCESS_NOT_IDENTIFIED" not in C.TERMINAL_STATUSES


def test_withdrawn_statuses_are_not_emittable(tmp_path):
    """The ban is on emission, not on the string: both remain the correct
    historical labels when v4 documents cite them."""
    from dci1v4.engine.context import synthetic_context
    from dci1v4.engine.paths import model_tree
    from dci1v4.engine.transitions import write_terminal_report

    assert set(C.WITHDRAWN_STATUSES) == {"REFERENCE_POOL_MISMATCH",
                                         "COMPOSED_UPTAKE_MISMATCH"}
    assert not set(C.WITHDRAWN_STATUSES) & set(C.TERMINAL_STATUSES)
    context = synthetic_context(tmp_path)
    tree = model_tree(context, "gemma-3n-e2b-it")
    for status in C.WITHDRAWN_STATUSES:
        with pytest.raises(ProtocolError, match="not a registered"):
            write_terminal_report(tree, {"status": status})


def test_the_verdict_model_is_a_vector_not_a_target_plus_manipulation_check():
    """T-1: the row carries one verdict per constituent, neither privileged."""
    from dci1v4.generation.cache import compliance_row

    source = inspect.getsource(compliance_row)
    assert "added_pass" not in source
    assert "target_pass" not in source
    assert "for item in cell.constituents" in source


def test_exchangeability_is_not_a_claim_gate():
    for name in ("exchangeability", "exchangeable"):
        assert name not in BOUND, name


# ------------------------------------ against v4 revision 1, superseded
@pytest.mark.parametrize("name", [
    "iota",                       # the withdrawn outcome-crossing estimand
    "surrogate", "hence",         # the withdrawn surrogate outcome constraint
    "COMPOSED_UPTAKE_MISMATCH",
    "S_side", "eleven_arm",
])
def test_revision_one_construct_is_absent(name):
    assert name not in BOUND, name


def test_no_allocation_is_banned_and_the_selection_carries_its_evidence():
    """Every §16.3 row is selectable; what is asserted is the evidence."""
    assert len(C.ALLOCATION_MENU) == 5
    for entry in C.ALLOCATION_MENU:
        assert entry["blocks"] in (288, 384, 480)
        assert entry["M"] in (4, 8)
    selection = select_allocation()
    assert selection["selected"] == {"blocks": 384, "M": 4,
                                     "generations_per_model": 38400}
    assert selection["rule"].startswith("smallest entry meeting every")
    assert len(selection["candidates"]) == len(C.ALLOCATION_MENU)
    assert "REPORTED, NOT DECIDED" in selection["decision_status"]


def test_the_allocation_justification_is_absolute_not_effect_dependent():
    """Revision 1 sized against a projected effect; v4r2 sizes against the
    absolute preconditions. The reasoning is banned, not the numbers."""
    from dci1v4.analysis import variance

    source = inspect.getsource(variance)
    for marker in ("expected_effect", "projected_effect", "pilot_effect"):
        assert marker not in source, marker
    assert set(C.PRECISION_PRECONDITIONS) == {"D", "Delta_R", "Lambda",
                                              "Delta_j"}


def test_the_open_decision_register_is_V1_to_V9():
    assert freeze_stage.OPEN_DECISIONS == tuple(f"V{i}" for i in range(1, 10))
    for superseded in ("U1", "U12"):
        assert superseded not in freeze_stage.OPEN_DECISIONS


# --------------------------------------------- against the legacy corpus
def test_duplicate_pairs_are_counted_and_bound_qualification():
    from dci1v4.generation.cache import duplicate_report

    rows = [{"cell_id": "c", "response_content_hash": "same"} for _ in range(4)]
    report = duplicate_report(rows)
    assert report["overall_rate"] == 1.0
    assert report["overall_rate"] > C.DUPLICATE_QUALIFICATION_MAX


def test_a_scalar_is_never_quoted_without_its_configuration():
    record = {"claim_level": "L1", "configuration": "", "family": "F1",
              "interval_type": "simultaneous", "identification_status": [],
              "measurement_basis": "human_validated", "outcome_position": 1,
              "estimate": 0.3}
    with pytest.raises(ClaimError):
        claims.assert_scalar_carries_configuration(record)
    with pytest.raises(ClaimError):
        claims.assert_statement_complete(record)


def test_author_performed_labels_are_never_independent_validation():
    from dci1v4.annotation.packets import assert_independent

    with pytest.raises(ProtocolError, match="never described as independent"):
        assert_independent({"annotator_id": "author",
                            "on_design_or_analysis_team": True})


def test_every_threshold_carries_its_registered_provenance():
    table = freeze_stage.assert_threshold_provenance()
    provenances = {name: entry["provenance"] for name, entry in table.items()}
    assert "§G row 1" in provenances["delta_r_generic_threshold"]
    assert "§G row 1" in provenances["delta_r_pair_specific_threshold"]
    assert "v3 §11" in provenances["smallest_effect_of_interest"]
    assert "v3 §11" in provenances["equivalence_region"]
    assert "§16.2" in provenances["precision_preconditions"]
    assert "§13.2" in provenances["reference_caliper"]
    assert "§13.2" in provenances["realised_gap_qualifier"]
    assert len({v for v in provenances.values()}) >= 4
