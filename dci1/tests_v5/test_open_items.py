"""The specification questions §34 does not carry, and what they block."""
from __future__ import annotations

import json
from dataclasses import replace

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.protocol import open_items


def test_every_item_is_classified_and_nothing_blocks_any_more():
    assert set(open_items.OPEN_ITEM_IDS) == {"U1", "U2", "U3", "P1"}
    for item in open_items.OPEN_ITEMS.values():
        assert item.status in open_items.STATUSES
        assert item.question and item.section
    # U2 was the one blocking item; it is resolved at A2 and P1 is confirmed.
    assert open_items.blocking_items() == ()


def test_u2_kept_the_alternatives_it_was_resolved_between():
    """§11.8's secondary was not identified as written and this says so.

    The point of the entry was never that a fit is hard; it is that more than
    one repair is admissible and they do not estimate the same gamma. The
    alternatives stay on the item after the resolution, because a resolution
    that erased what it chose between would leave nobody able to see what was
    given up.
    """
    item = open_items.get_item("U2")
    assert item.resolution == "A2"
    assert not item.blocking
    ids = {a.id for a in item.alternatives}
    assert ids == {"A1", "A2", "A3", "A4"}
    for alternative in item.alternatives:
        assert alternative.estimand and alternative.consequence
    assert "not identified" in dict(
        (a.id, a.estimand) for a in item.alternatives)["A1"]


def test_a_corrected_stale_sentence_is_confirmed_not_decided():
    """P1: the §7.10 correction changed the wording and no rule."""
    item = open_items.get_item("P1")
    assert item.status == open_items.CONFIRM_AT_ADOPTION
    assert item.resolution == "confirmed"
    assert not item.blocking
    assert "CL7" in item.implementation


def test_the_resolutions_come_from_the_researchers_own_record():
    """Not from a module literal, and not from a call in a test fixture."""
    recorded = {e["id"]: e["resolution"]
                for e in open_items.recorded_resolutions()}
    assert recorded == {"U2": "A2", "P1": "confirmed"}
    for item_id, resolution in recorded.items():
        item = open_items.get_item(item_id)
        assert item.resolution == resolution
        assert item.resolved_by and item.resolved_on


def test_a_reopen_restores_the_record_rather_than_a_blank_registry(
        restore_open_items):
    """Same rule as the decision registry: what a fixture found is the record.

    A fixture that reopened U2 would let a later test assert behaviour the
    protocol no longer admits.
    """
    restore_open_items.OPEN_ITEMS["U2"] = replace(
        restore_open_items.OPEN_ITEMS["U2"], resolution=None,
        resolved_by=None, resolved_on=None)
    assert restore_open_items.blocking_items() == ("U2",)
    restore_open_items.reopen_all_for_testing()
    assert restore_open_items.get_item("U2").resolution == "A2"
    assert restore_open_items.blocking_items() == ()


def test_resolving_requires_an_admissible_formulation(restore_open_items):
    restore_open_items.OPEN_ITEMS["U2"] = replace(
        restore_open_items.OPEN_ITEMS["U2"], resolution=None,
        resolved_by=None, resolved_on=None)
    with pytest.raises(ProtocolError):
        restore_open_items.resolve("U2", "A9", resolved_by="t",
                                   resolved_on="t")
    with pytest.raises(ProtocolError):
        restore_open_items.resolve("U2", "A2", resolved_by="", resolved_on="t")
    restore_open_items.resolve("U2", "A2", resolved_by="t", resolved_on="t")
    assert not restore_open_items.blocking_items()
    with pytest.raises(ProtocolError):
        restore_open_items.resolve("U2", "A4", resolved_by="t",
                                   resolved_on="t")


def test_a_record_that_disagrees_with_a_live_resolution_is_an_amendment(
        tmp_path):
    """It does not happen by a file changing under a running process."""
    record = tmp_path / "researcher_decisions.json"
    record.write_text(json.dumps({
        "closures": [],
        "open_items": [{"id": "U2", "resolution": "A4",
                        "resolved_by": "t", "resolved_on": "t"}]}))
    with pytest.raises(ProtocolError, match="amendment"):
        open_items.apply_recorded_resolutions(record)


def test_the_manifest_payload_carries_every_item_and_its_resolution():
    payload = open_items.manifest_payload()
    assert payload["n_items"] == 4
    assert payload["blocking"] == []
    assert payload["resolved"] == {"U2": "A2", "P1": "confirmed"}
    assert payload["record"]["resolved_here"] == ["U2", "P1"]
    assert {i["id"] for i in payload["items"]} == set(
        open_items.OPEN_ITEM_IDS)
