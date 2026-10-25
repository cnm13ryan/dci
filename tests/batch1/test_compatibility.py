"""B-specific logical compatibility: proofs, witnesses, the full matrix."""
from __future__ import annotations

import pytest

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import library as L
from dci.batch1 import text as T
from dci.batch1 import verifiers as V

pytestmark = pytest.mark.cpu

BY_ID = L.constraint_by_id()


@pytest.fixture(scope="module")
def matrix():
    return COMPAT.compatibility_matrix()


def test_the_pool_satisfies_its_declared_properties():
    assert COMPAT.assert_pool()["max_letters"] <= 7


def test_full_matrix_is_resolved(matrix):
    assert len(matrix["cells"]) == 51 + 3
    assert all(len(row) == 6 for row in matrix["cells"].values())
    assert matrix["counts"] == {"COMPATIBLE": 305, "INCOMPATIBLE": 19,
                                "UNRESOLVED": 0}


@pytest.mark.parametrize("cid, incompatible", [
    ("ew.therefore.2", {8}), ("ew.nonetheless.4", {8, 9, 10}),
    ("ew.consequently.2", {8, 9, 10, 11}), ("inc.remarkable", {8, 9}),
    ("ew.although.6", set()), ("ew.moreover.2", set()),
    ("A.however.4", set()), ("pro.letter.b", set()), ("ord.inc6", set()),
])
def test_incompatibility_is_exactly_the_long_word_cases(matrix, cid,
                                                        incompatible):
    row = matrix["cells"][cid]
    assert {int(m) for m, c in row.items()
            if c["status"] == COMPAT.INCOMPATIBLE} == incompatible
    for m, c in row.items():
        if c["status"] == COMPAT.INCOMPATIBLE:
            assert "letters" in c["reason"] and c["witness"] is None


def test_every_compatible_cell_carries_a_witness_that_passes_both(matrix):
    for cid, row in matrix["cells"].items():
        c = BY_ID[cid]
        for m, cell in row.items():
            if cell["status"] != COMPAT.COMPATIBLE:
                continue
            b = next(x for x in L.b_candidates() if x.p["m"] == int(m))
            for k in (c, b):
                s = V.score_constraint(k.cid, k.family.verifier_id,
                                       k.verifier_params(), k.family.vacuity,
                                       cell["witness"], present=True)
                assert s.compliant, (cid, m, k.cid)


def test_b9_and_b12_have_different_compatible_libraries(matrix):
    b9, b12 = (COMPAT.compatible_ids(matrix, m) for m in (9, 12))
    assert b9 < b12
    assert b12 - b9 == {"ew.nonetheless.2", "ew.nonetheless.4",
                        "ew.consequently.2", "ew.consequently.4",
                        "inc.remarkable"}


def test_difficult_but_possible_is_not_incompatible():
    for cid in ("pro.letter.b", "ord.inc6", "rel.word3", "unq.word5"):
        assert COMPAT.check(BY_ID[cid], 8)["status"] == COMPAT.COMPATIBLE


def test_missing_witness_is_unresolved_never_compatible(monkeypatch):
    monkeypatch.setattr(COMPAT, "build_witness", lambda c: None)
    cell = COMPAT.check(BY_ID["ord.inc4"], 10)
    assert cell["status"] == COMPAT.UNRESOLVED
    matrix = COMPAT.compatibility_matrix((BY_ID["ord.inc4"],), (10,))
    with pytest.raises(ValueError, match="unresolved"):
        COMPAT.assert_resolved(matrix, (10,))


def test_a_failing_witness_is_unresolved(monkeypatch):
    monkeypatch.setattr(COMPAT, "build_witness", lambda c: "Short.")
    assert COMPAT.check(BY_ID["ord.inc4"], 10)["status"] == COMPAT.UNRESOLVED


def test_matrix_is_reproducible(matrix):
    assert COMPAT.matrix_hash(matrix) == \
        COMPAT.matrix_hash(COMPAT.compatibility_matrix())


# ------------------------------------------- full-length witnesses (§11)

def test_the_long_pool_satisfies_its_declared_properties():
    info = COMPAT.assert_long_pool()
    assert info["sentences"] == len(COMPAT.LONG_POOL) >= 30


def test_every_compatible_cell_has_a_full_length_witness(matrix):
    task = matrix["task_level"]
    assert task["counts"] == {"TASK_COMPATIBLE": 305, "TASK_UNRESOLVED": 0}
    assert task["unresolved"] == []
    by_id = L.constraint_by_id()
    for cid, row in task["cells"].items():
        witness = task["witnesses"][cid]
        words = T.word_count(witness)
        assert COMPAT.TASK_MIN_WORDS <= words <= COMPAT.TASK_MAX_WORDS
        c = by_id[cid]
        assert COMPAT._compliant(c, witness).compliant, cid
        for m in row:
            b = next(x for x in L.b_candidates() if x.p["m"] == int(m))
            assert COMPAT._compliant(b, witness).compliant, (cid, m)


def test_task_level_never_changes_logical_compatibility(matrix):
    assert matrix["counts"] == {"COMPATIBLE": 305, "INCOMPATIBLE": 19,
                                "UNRESOLVED": 0}
    for cid, row in matrix["task_level"]["cells"].items():
        assert all(matrix["cells"][cid][m]["status"] == COMPAT.COMPATIBLE
                   for m in row)


def test_no_full_length_witness_is_unresolved_not_incompatible(monkeypatch):
    c = L.constraint_by_id()["es.4"]
    monkeypatch.setattr(COMPAT, "task_witness", lambda c: "Too short.")
    out = COMPAT.task_level((c,), {c.cid: {"9": {"status": COMPAT.COMPATIBLE}}})
    assert out["cells"]["es.4"]["9"]["status"] == COMPAT.TASK_UNRESOLVED
    assert out["unresolved"] == [["es.4", 9]]
