"""The confirmatory plan: licensed by a freeze, complete, and un-cherry-picked.

The failures these pin are the expensive ones. A run that starts without a
freeze produces evidence no registered analysis may read; a run that quietly
drops a draw produces cell means §14.2 forbids; a run that re-does the cells
whose numbers looked surprising produces a result that is not the registered
experiment at all.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import confirmatory as X

SLOTS = {s: [s, 3] for s in C.REGISTERED_SLOT_ORDER}


def freeze(variant="full", blocks=4, m=2, **over):
    record = {
        "outcome": "PASS", "design_variant": variant,
        "slot_map": SLOTS, "blocks": [f"b{i}" for i in range(blocks)],
        "m_draws": m, "completion_cap": 512, "model_revision": "rev",
        "verifier_source_hash": "v" * 64, "producing_commit": "c" * 40}
    record.update(over)
    return record


def rows_for(record):
    return [{"block_id": key.split("|")[0], "cell_id": key.split("|")[1],
             "draw_index": int(key.split("|")[2])}
            for key in X.expected_row_ids(record)]


# ---------------------------------------------------------------- licensing

def test_no_freeze_means_no_generation():
    for absent in (None, {}, {"outcome": "FAIL"}):
        with pytest.raises(IntegrityError):
            X.assert_generation_licensed(absent)


def test_a_freeze_missing_a_bound_field_does_not_license_generation():
    record = freeze()
    del record["verifier_source_hash"]
    with pytest.raises(IntegrityError) as excinfo:
        X.assert_generation_licensed(record)
    assert "verifier_source_hash" in str(excinfo.value)


def test_an_unregistered_design_variant_is_refused():
    with pytest.raises(ProtocolError):
        X.confirmatory_plan(freeze(variant="whatever_fits"))


# ------------------------------------------------------------------- shape

@pytest.mark.parametrize("variant,cells", [("full", 47), ("no_spectrum", 29),
                                           ("reduced", 8)])
def test_the_plan_is_derived_from_the_freeze(variant, cells):
    plan = X.confirmatory_plan(freeze(variant=variant))
    assert plan["cells_per_block"] == cells
    assert plan["generations"] == 4 * cells * 2
    assert plan["orders"] == C.N_ORDERS == 2


def test_the_registered_allocation_is_recomputed_from_actual_variants():
    report = X.allocation_report(
        {"m1": "full", "m2": "no_spectrum", "m3": "no_spectrum",
         "m4": "no_spectrum"}, blocks=384, m_draws=8)
    assert report["per_model"]["m1"]["generations"] == 144384
    assert report["per_model"]["m2"]["generations"] == 89088
    assert report["total_generations"] == 411648


# -------------------------------------------------------------- completeness

def test_a_complete_row_set_is_complete():
    record = freeze()
    assert X.missing_rows(record, rows_for(record))["complete"]
    X.assert_no_selective_rerun(record, rows_for(record))


def test_a_lost_draw_is_reported_and_never_imputed():
    record = freeze()
    rows = rows_for(record)
    dropped = rows.pop(17)
    report = X.missing_rows(record, rows)
    assert report["missing"] == 1 and not report["complete"]
    assert f"{dropped['block_id']}|{dropped['cell_id']}" in \
        report["first_missing"][0]


def test_a_missing_order_variant_is_missing_rows_not_a_smaller_design():
    record = freeze()
    rows = [r for r in rows_for(record)
            if r["cell_id"] != "pair:B+A"]
    report = X.missing_rows(record, rows)
    assert report["missing"] == 4 * 2       # blocks x M for that one cell


def test_a_selective_rerun_is_refused():
    record = freeze()
    rows = rows_for(record)
    rows.append(dict(rows[3]))              # the same identity generated twice
    with pytest.raises(IntegrityError) as excinfo:
        X.assert_no_selective_rerun(record, rows)
    assert "never selected, replaced or re-run" in str(excinfo.value)


def test_a_row_outside_the_plan_is_refused():
    record = freeze()
    rows = rows_for(record) + [{"block_id": "b9", "cell_id": "solo:A",
                                "draw_index": 0}]
    with pytest.raises(IntegrityError):
        X.assert_no_selective_rerun(record, rows)


# --------------------------------------------------------- post-freeze drift

def test_a_plan_that_differs_from_the_freeze_is_refused():
    record = freeze()
    plan = X.confirmatory_plan(record)
    X.assert_plan_matches_freeze(plan, record)
    for field, value in (("m_draws", 4), ("completion_cap", 1024),
                         ("model_revision", "other"),
                         ("design_variant", "reduced")):
        with pytest.raises(IntegrityError) as excinfo:
            X.assert_plan_matches_freeze({**plan, field: value}, record)
        assert "requires a new protocol revision" in str(excinfo.value)


def test_a_slot_the_freeze_did_not_bind_stops_the_plan():
    record = freeze()
    record["slot_map"] = {"A": ["A", 3], "B": ["B", 8]}
    with pytest.raises(IntegrityError) as excinfo:
        X.confirmatory_plan(record)
    assert "slot map does not bind" in str(excinfo.value)


# ------------------------------------------ the runners the plan feeds into

def test_the_confirmatory_batches_partition_the_block_list_exactly_once():
    """Batching is an operational convenience and must not be a selection: the
    batches have to cover every block, in order, with no overlap."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.confirmatory_run import batches

    for size in (1, 7, 16, 384, 500):
        spans = batches(C.N_BLOCKS, size=size)
        covered = [i for start, stop in spans for i in range(start, stop)]
        assert covered == list(range(C.N_BLOCKS)), size


def test_the_design_materialiser_refuses_a_slot_the_variant_needs():
    from dci1v4.errors import IntegrityError
    from dci1v4r3.run.design_run import assert_slot_map_usable

    partial = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 4)}
    with pytest.raises(IntegrityError):
        assert_slot_map_usable(partial, "full")


def test_two_slots_bound_to_one_instance_are_refused():
    """A verdict is attributed to a slot by (kind, severity). Two slots on one
    instance would make that attribution ambiguous and merge two companions."""
    from dci1v4.errors import IntegrityError
    from dci1v4r3.run.design_run import assert_slot_map_usable

    collided = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 4),
                "R2": ("RF1", 4), "R3": ("RF8", 5)}
    with pytest.raises(IntegrityError):
        assert_slot_map_usable(collided, "reduced")


def test_gate4_and_the_confirmatory_run_build_cells_the_same_way():
    """A headroom result about a cell the study never generates is a check of
    something else, so both stages go through one materialiser."""
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "dci1v4r3" / "run"
    for module in ("gates_run.py", "confirmatory_run.py"):
        tree = ast.parse((src / module).read_text())
        names = {a.name for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) for a in n.names}
        assert "design_cells_for" in names, module


def test_the_freeze_leaves_an_unsourceable_field_unknown_rather_than_default():
    from dci1v4r3.stages.freeze import FREEZE_FIELDS, build_freeze_record

    record = build_freeze_record(n_star=3)
    assert record["n_star"] == 3
    assert all(record[f] == "UNKNOWN" for f in FREEZE_FIELDS if f != "n_star")


def test_the_freeze_refuses_while_the_measurement_basis_is_unavailable():
    from dci1v4r3.run.freeze_run import decision_record

    unavailable = decision_record({"measurement_basis":
                                   "HUMAN_VALIDATION_UNAVAILABLE"})
    assert unavailable["D9"] == "UNKNOWN"
    approved = decision_record({"measurement_basis":
                                "autorater_calibration_approved"})
    assert approved["D9"] != "UNKNOWN"


def test_every_amendment_document_the_freeze_hashes_exists():
    from dci1v4r3.run.freeze_run import amendment_hashes

    assert all(v != "MISSING" for v in amendment_hashes().values())
