"""The v8 wording instrument: the four frames, A/MK identity, grammatical
number everywhere, byte-identity with v7 where nothing changed, the hash."""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v7.protocol.wordings import wording_source_hash as v7_hash
from dci1v7.protocol.wordings import wordings as v7_wordings
from dci1v7.verifiers.constraints import FAMILIES, TIER1_FAMILY_IDS, declared_range
from dci1v8dev import wordings as W

EXPECTED = ("Use the word X exactly 3 times.",
            "Your answer must contain the word X exactly 3 times.",
            "Include the word X exactly 3 times in your answer.",
            "The word X must appear exactly 3 times.")


def test_the_four_frames_are_the_repair_and_a_and_mk_differ_only_in_the_marker():
    assert W.v8_wordings("A", 3) == tuple(f.replace("X", "however") for f in EXPECTED)
    for kind in TIER1_FAMILY_IDS:
        marker = W._frames._marker(kind)
        assert W.v8_wordings(kind, 3) == tuple(f.replace("X", marker) for f in EXPECTED)
    assert W.v8_wordings("A", 1)[0] == "Use the word however exactly 1 time."


def test_the_instrument_passes_every_structural_guarantee():
    r = W.assert_v8_instrument()
    assert r["differences_by_reason"]["the_word"] > 0
    assert r["differences_by_reason"]["number"] > 0
    assert sum(r["renderings_checked"].values()) > 2000


def test_grammatical_number_at_q_equals_one_and_byte_identity_elsewhere():
    assert W.v8_wordings("XC1", 1)[0] == "Your answer must use exactly 1 semicolon."
    assert W.v8_wordings("RF1", 1)[0] == "At most 1 word may begin with b."
    assert W.v8_wordings("RF12", 1)[2] == "No more than 1 sentence may appear."
    for kind in FAMILIES:
        if kind in TIER1_FAMILY_IDS:
            continue
        for q in declared_range(kind):
            if q != 1:
                assert W.v8_wordings(kind, q) == v7_wordings(kind, q), (kind, q)
    assert W.grammatical_number_defects("Use exactly 1 semicolons.", 1)
    assert not W.grammatical_number_defects("Use exactly 1 semicolon.", 1)
    assert W.grammatical_number_defects("At most 2 word may begin with b.", 2)


def test_the_hash_is_stable_and_is_not_v7s():
    assert W.v8_wording_source_hash() == W.v8_wording_source_hash()
    assert W.v8_wording_source_hash() != v7_hash()


def test_out_of_range_and_unknown_kinds_are_refused():
    import pytest
    with pytest.raises(ProtocolError):
        W.v8_wordings("CL7", 1)
    with pytest.raises(ProtocolError):
        W.v8_wordings("ZZ9", 1)
