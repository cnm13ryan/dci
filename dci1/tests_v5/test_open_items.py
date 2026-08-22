"""The specification questions §34 does not carry, and what they block."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.protocol import open_items


def test_every_item_is_classified_and_the_blocking_one_is_named():
    assert set(open_items.OPEN_ITEM_IDS) == {"U1", "U2", "U3", "P1"}
    for item in open_items.OPEN_ITEMS.values():
        assert item.status in open_items.STATUSES
        assert item.question and item.section
    assert open_items.blocking_items() == ("U2",)


def test_u2_blocks_because_the_alternatives_estimate_different_things():
    """§11.8's secondary is not identified as written and this says so.

    The point of the entry is not that a fit is hard; it is that more than
    one repair is admissible and they do not estimate the same gamma. The
    item therefore carries the alternatives and what each one changes.
    """
    item = open_items.get_item("U2")
    assert item.blocking
    ids = {a.id for a in item.alternatives}
    assert ids == {"A1", "A2", "A3", "A4"}
    for alternative in item.alternatives:
        assert alternative.estimand and alternative.consequence
    assert "not identified" in dict(
        (a.id, a.estimand) for a in item.alternatives)["A1"]


def test_a_corrected_stale_sentence_does_not_block():
    """P1: the §7.10 correction changed the wording and no rule."""
    item = open_items.get_item("P1")
    assert item.status == open_items.CONFIRM_AT_ADOPTION
    assert not item.blocking
    assert "CL7" in item.implementation


def test_resolving_requires_an_admissible_formulation(restore_open_items):
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


def test_the_manifest_payload_carries_every_item():
    payload = open_items.manifest_payload()
    assert payload["n_items"] == 4
    assert payload["blocking"] == ["U2"]
    assert {i["id"] for i in payload["items"]} == set(
        open_items.OPEN_ITEM_IDS)
