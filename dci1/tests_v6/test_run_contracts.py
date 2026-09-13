"""Every field a v5 stage reads is a field some earlier stage writes."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.run import cli, contracts


def test_every_registered_stage_has_a_runner():
    """§18: a stage with no runner is a lifecycle with a hole in it."""
    cli.assert_every_stage_has_a_runner()
    assert set(cli.RUNNERS) == set(C.STAGE_SEQUENCE)
    assert len(cli.RUNNERS) == 19


def test_the_static_contract_audit_is_clean():
    result = contracts.audit_contracts()
    assert result["clean"], result["defects"]
    assert result["n_fields"] > 80


def test_a_reader_may_not_precede_its_producer():
    """The defect this audit caught while it was being written.

    ``CONFIRMATORY_GENERATION.completeness`` was declared as read by
    ``PREFREEZE_AUDIT``, which runs two stages earlier. The audit is worth
    having because it found that without anything executing.
    """
    original = contracts.CONTRACT
    bad = contracts.Field(
        artifact=C.STAGE_GATE5, field="freeze", producer=C.STAGE_GATE5,
        readers=(C.STAGE_GATE2,), required=True, test="test")
    contracts.CONTRACT = original + (bad,)
    try:
        defects = contracts.audit_contracts()["defects"]
        assert any(d["kind"] == "READER_PRECEDES_PRODUCER" for d in defects)
    finally:
        contracts.CONTRACT = original


def test_a_required_field_with_no_producer_is_a_blocking_defect():
    payloads = {C.STAGE_GATE5: {"freeze_hash": "x"}}
    defects = contracts.audit_contracts(payloads)["defects"]
    missing = {d["field"] for d in defects
               if d["kind"] == "REQUIRED_FIELD_NOT_PRODUCED"}
    assert "freeze" in missing and "blocks" in missing
    with pytest.raises(ProtocolError, match="no producer"):
        contracts.assert_contracts_clean(payloads)


def test_the_matrix_has_a_row_for_every_field():
    rows = contracts.matrix_rows()
    assert len(rows) == len(contracts.CONTRACT)
    for row in rows:
        assert row["producer"] and row["stage_introduced"] and row["test"]
        assert row["status"] == "NOT_EXERCISED"
    table = contracts.matrix_markdown()
    assert table.startswith("| artifact | field | producer |")
    assert table.count("\n") == len(rows) + 1
