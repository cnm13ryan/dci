"""§13.2's chance basis, guarded on the path the production code takes.

**The defect this is about.** Until 2026-08-29 (fixed by commit `7f89dae`)
§13.11's chance column was obtained through
``execute.instance_rates(chance_rows, ...)``, whose *solo* scan runs first
and finds no grid row that states a non-outcome candidate; the call raised
``ProtocolError`` and an ``except`` handler substituted
``chance = {"compliance": 0.0}``. Every v5/v6/v7 replication therefore
recorded kappa_R = 0 for every reference candidate --- iota(R) was the raw
solo rate --- while kappa_A came from a *different* denominator (v7's
all-absent basis, every row on which A was scored absent, the other
candidates' solo answers included). A and R were being compared on two
different chance bases, and §13.4's ceiling and §13.6's displacement were
measured against zero.

v8 defines kappa for A and for every reference on **the same unconstrained
cell of the same frame** (``run/calibration.py``: ``_unconstrained_rate``,
``frame_a_coordinate``, ``frame_tables``), and the v7 producer now refuses
rather than substituting (``run/gates_run.py``, the ``n_unconstrained == 0``
branch).

Three guards, on the mandatory path:

1.  the producer **raises** when a candidate's unconstrained cell is absent,
    and never yields a 0.0 chance in its place;
2.  on rows whose unconstrained cell has a known non-zero pass rate, the
    kappa Gate 2 records for A and for every reference on a frame is that
    rate --- the same cell, the same basis string --- and iota is
    ``(p - kappa) / (1 - kappa)`` for both;
3.  a static guard: no ``except`` handler in the three sources that own the
    chance basis substitutes a literal zero for a chance or kappa. The
    detector is checked against the historical pattern itself, so a guard
    that silently stopped matching would fail.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.run.execute import cell_rates
from dci1v7.run.gates_run import _calibration_rows
from dci1v7.stages.calibration_table import instructed_compliance
from dci1v7.verifiers.constraints import Constraint
from dci1v8dev.run import calibration as CAL
from dci1v8dev.run.execute import UNCONSTRAINED_ARM, rows_of_frame

from tests_v8dev.test_frame_conditioning import (A_GRID, B_GRID, CANDIDATES,
                                                 MODEL, _default_rates, _u,
                                                 rows_for)

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"

#: The absent-outcome probability that makes the unconstrained cell's rate
#: exactly known: the fixture's outcome hash is keyed on the draw index
#: alone for an absent instance (see ``_absent_key``), so the cell's
#: topic-mean compliance is the share of the M_cal draw keys below it.
ABSENT_P = 0.51


def _absent_key(frame, label, topic, draw, present):
    """Solo outcomes vary by frame/label/topic/draw as usual; an *absent*
    outcome is keyed by the draw alone, so every instance's unconstrained
    cell carries the same exactly-computable rate on every frame."""
    return (frame, label, topic, draw) if present else (draw, "absent")


def _expected_kappa() -> float:
    return sum(1 for d in range(C.M_CAL)
               if _u(d, "absent", "outcome") < ABSENT_P) / C.M_CAL


# ------------------------------------------------------------------ guard 1
def _solo_rows(label: str, *, n_topics: int = 4, draws: int = 2):
    kind, _, severity = label.rpartition(":")
    q = int(severity)
    rows = []
    for t in range(n_topics):
        for d in range(draws):
            rows.append({
                "row_id": f"b-{t:03d}:solo:{label}:{d}", "cell_id": f"solo:{label}",
                "block_id": f"b-{t:03d}", "block_index": t, "block_frame": 0,
                "arm": "solo", "slots": [label], "draw_index": d,
                "topic_id": f"topic-{t:03d}", "topic_split": C.CALIBRATION_A,
                "word_count": 80, "truncated": False, "load": 1,
                "scores": [{"kind": kind, "severity": q, "present": True,
                            "passed": (t + d) % 2 == 0, "graded": 1.0,
                            "vacuous_pass": False, "non_vacuous": True}]})
    return rows


def _unconstrained_rows(label: str, *, n_topics: int = 4, draws: int = 2,
                        passed: bool = True):
    kind, _, severity = label.rpartition(":")
    q = int(severity)
    rows = []
    for t in range(n_topics):
        for d in range(draws):
            rows.append({
                "row_id": f"u-{t:03d}:unconstrained:{d}",
                "cell_id": "unconstrained", "block_id": f"u-{t:03d}",
                "block_index": t, "block_frame": 0, "arm": UNCONSTRAINED_ARM,
                "slots": [], "draw_index": d, "topic_id": f"topic-{t:03d}",
                "topic_split": C.CALIBRATION_A, "word_count": 80,
                "truncated": False, "load": 0,
                "scores": [{"kind": kind, "severity": q, "present": False,
                            "passed": passed and d == 0, "graded": 1.0,
                            "vacuous_pass": False, "non_vacuous": True}]})
    return rows


def _rows_table(*, chance_rows):
    # a second candidate's solo cells so the split holds rows that do NOT
    # state MK1:3 --- §13.11's producer skips a candidate every solo row of
    # the split states, and the chance column is what is under test here
    solo = _solo_rows("MK1:3") + _solo_rows("MK2:3")
    return _calibration_rows(
        MODEL, [Constraint("MK1", 3, reserve=True)], m_star=9,
        solo_rows=solo, chance_rows=chance_rows,
        b_solo_rows=[], kappa_column={"pooled": {}, C.CALIBRATION_A: {},
                                      C.CALIBRATION_B: {}})


def test_the_producer_refuses_a_candidate_with_no_unconstrained_cell():
    """§13.2: no unconstrained cell is a broken run, not a chance of zero."""
    with pytest.raises(ProtocolError) as exc:
        _rows_table(chance_rows=[])
    assert "unconstrained cell" in str(exc.value)
    assert "records no chance it did not measure" in str(exc.value)


def test_the_producer_refuses_when_the_grid_never_scored_the_candidate():
    """The historical shape of the defect: the grid rows exist and carry an
    unconstrained cell, but the candidate is not among the instances scored
    absent on it. That is the call that used to raise and be swallowed."""
    with pytest.raises(ProtocolError):
        _rows_table(chance_rows=_unconstrained_rows("XC3:8"))


def test_the_producer_refuses_a_chance_measured_on_another_topic_set():
    with pytest.raises(ProtocolError) as exc:
        _rows_table(chance_rows=_unconstrained_rows("MK1:3", n_topics=2))
    assert "same topic set" in str(exc.value)


def test_a_measured_cell_yields_that_cell_and_never_a_zero_by_default():
    table = _rows_table(chance_rows=_unconstrained_rows("MK1:3"))
    rows = table[C.CALIBRATION_A]
    assert rows, table
    reference = cell_rates(_unconstrained_rows("MK1:3"), kind="MK1",
                           severity=3, present=False, split=C.CALIBRATION_A,
                           arm=UNCONSTRAINED_ARM)
    for row in rows:
        assert row["chance_compliance"] == reference["compliance"]
        assert row["chance_compliance"] > 0.0
    # ... and a cell that really is zero is recorded as zero, from the cell
    zero = _rows_table(chance_rows=_unconstrained_rows("MK1:3", passed=False))
    assert [r["chance_compliance"] for r in zero[C.CALIBRATION_A]] == [0.0]


# ------------------------------------------------------------------ guard 2
@pytest.fixture(scope="module")
def frames_with_a_known_chance():
    """A four-frame Gate 2 whose unconstrained cell has an exactly known,
    non-zero pass rate for every instance --- A, B and every candidate."""
    rates = _default_rates()
    labels = ([f"A:{q}" for q in A_GRID] + [f"B:{m}" for m in B_GRID]
              + list(CANDIDATES))
    chance = {label: ABSENT_P for label in labels}
    grid, cand = rows_for({w: rates for w in range(C.N_WORDINGS)},
                          topics_per_split=12, chance=chance,
                          outcome_key=_absent_key)
    result = CAL.gate2_frames_from_rows(
        grid, cand, candidates=CAL.constraints_from_labels(CANDIDATES),
        model_key=MODEL)
    return {"grid": grid, "cand": cand, "frames": result}


def test_the_gate2_record_names_the_unconstrained_cell_as_the_basis(
        frames_with_a_known_chance):
    """Guard 4: the Gate-2 record's ``chance_basis.cell`` on a synthetic
    walk of the production producer. A full pilot lifecycle is not needed
    to reach it --- ``gate2_frames_from_rows`` is the function that writes
    the block."""
    frames = frames_with_a_known_chance["frames"]
    assert frames["supported"], frames["failures"]
    for w in frames["supported"]:
        block = frames["by_frame"][w]
        assert block["chance_basis"]["cell"] == UNCONSTRAINED_ARM
        assert "unconstrained cell" in block["chance_basis"]["rule"]
        assert block["iota_a_basis"].startswith("§13.2")
        assert "the same basis as every candidate's on this frame" in \
            block["iota_a_basis"]


def test_kappa_for_a_and_for_every_reference_is_the_same_cell_on_the_frame(
        frames_with_a_known_chance):
    expected = _expected_kappa()
    assert 0.0 < expected < C.CHANCE_DEGENERACY_MAX
    grid = frames_with_a_known_chance["grid"]
    frames = frames_with_a_known_chance["frames"]
    for w in frames["supported"]:
        block = frames["by_frame"][w]
        frame_grid = rows_of_frame(grid, w)
        n_star = int(block["n_star"])

        # kappa_A(f): A's compliance on the unconstrained cell of THIS
        # frame's blocks, and nothing else.
        kappa_a = float(block["kappa_a"])
        measured_a = cell_rates(frame_grid, kind="A", severity=n_star,
                                present=False, arm=UNCONSTRAINED_ARM)
        assert kappa_a == measured_a["compliance"] == pytest.approx(expected)
        assert block["iota_a"] == pytest.approx(
            instructed_compliance(block["solo_compliance_a"], kappa_a))

        # kappa_R(f) for every reference, on the same cell of the same frame
        rows = block["calibration_rows"]["pooled"]
        assert rows
        for row in rows:
            kappa_r = float(row["chance_compliance"])
            measured_r = cell_rates(frame_grid, kind=row["kind"],
                                    severity=row["severity"], present=False,
                                    arm=UNCONSTRAINED_ARM)
            assert kappa_r == measured_r["compliance"] == pytest.approx(expected)
            assert kappa_r > 0.0
            # the same basis for A and for R, so the difference of the two
            # iotas is a difference of difficulties and not of denominators
            assert kappa_r == kappa_a
            iota_r = instructed_compliance(row["solo_compliance"], kappa_r)
            assert iota_r == pytest.approx(
                (row["solo_compliance"] - kappa_r) / (1.0 - kappa_r))


def test_the_other_denominators_are_recorded_beside_iota_a_not_as_iota_a(
        frames_with_a_known_chance):
    """v7's all-absent denominator and the chance pooled over every frame's
    blocks stay on the record as cross-checks. Neither may be the basis
    iota_A(f) is formed on: that is ``kappa_a``, the frame's own
    unconstrained cell, and the record says so in ``iota_a_basis``.

    (On this fixture every absent outcome is drawn from one rate, so the
    three numbers coincide numerically; what is asserted is which one the
    coordinate is *defined* by, which is the thing the defect got wrong.)
    """
    frames = frames_with_a_known_chance["frames"]
    for w in frames["supported"]:
        block = frames["by_frame"][w]
        for key in ("iota_a_all_absent_v7_basis",
                    "iota_a_all_frames_chance_basis",
                    "kappa_a_all_frames_blocks",
                    "chance_curves_all_absent_v7_basis"):
            assert key in block, (w, key)
        assert block["iota_a"] == pytest.approx(instructed_compliance(
            block["solo_compliance_a"], block["kappa_a"]))
        assert block["iota_a_basis"].startswith("§13.2")


# ------------------------------------------------------------------ guard 3
GUARDED_SOURCES = (
    SRC / "dci1v7" / "run" / "gates_run.py",
    SRC / "dci1v8dev" / "run" / "calibration.py",
    SRC / "dci1v8dev" / "chance_basis.py",
)

_CHANCE_NAMES = ("chance", "kappa")


def _is_chance_name(name: str | None) -> bool:
    return bool(name) and any(w in name.lower() for w in _CHANCE_NAMES)


def _target_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.append(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.append(sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            names.append(sub.value)
    return names


def _is_zero(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
            and node.value == 0)


def _holds_zero(node: ast.AST) -> bool:
    """A literal zero anywhere in the value --- bare, or inside the
    ``{"compliance": 0.0}`` mapping the historical fallback wrote."""
    return any(_is_zero(sub) for sub in ast.walk(node))


def substituted_zeros(source: str, where: str) -> list[str]:
    """Every place an ``except`` handler substitutes a literal zero for a
    chance or kappa. The historical defect's exact shape, generalised."""
    found: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        for stmt in ast.walk(node):
            targets: list[ast.AST] = []
            value: ast.AST | None = None
            if isinstance(stmt, ast.Assign):
                targets, value = list(stmt.targets), stmt.value
            elif isinstance(stmt, (ast.AnnAssign, ast.NamedExpr)):
                targets, value = [stmt.target], stmt.value
            if value is not None and _holds_zero(value) and any(
                    _is_chance_name(n) for t in targets
                    for n in _target_names(t)):
                found.append(f"{where}:{stmt.lineno}: assignment to a chance "
                             "name from a literal zero inside an except "
                             "handler")
            # `return {"chance_compliance": 0.0}` and `= {"compliance": 0.0}`
            for sub in ast.walk(stmt):
                if not isinstance(sub, ast.Dict):
                    continue
                for key, val in zip(sub.keys, sub.values):
                    if (isinstance(key, ast.Constant)
                            and _is_chance_name(str(key.value))
                            and _is_zero(val)):
                        found.append(f"{where}:{sub.lineno}: a chance key "
                                     "set to a literal zero inside an except "
                                     "handler")
    return sorted(set(found))


HISTORICAL = '''
def _entry(rows, candidate):
    try:
        chance = instance_rates(rows, kind=candidate.kind,
                                severity=candidate.severity)
    except ProtocolError:
        chance = {"compliance": 0.0}
    return {"chance_compliance": chance["compliance"]}
'''

HISTORICAL_BROAD = '''
def _entry(rows):
    try:
        kappa_c = measure(rows)
    except Exception:
        kappa_c = 0.0
    return kappa_c
'''


def test_the_detector_catches_the_historical_fallback():
    """A guard that stopped matching would pass vacuously; this is the
    positive control, and it is the code commit 7f89dae removed."""
    assert substituted_zeros(HISTORICAL, "historical")
    assert substituted_zeros(HISTORICAL_BROAD, "historical_broad")
    assert not substituted_zeros(
        "try:\n    x = f()\nexcept ProtocolError:\n    raise\n", "clean")


@pytest.mark.parametrize("path", GUARDED_SOURCES, ids=lambda p: p.name)
def test_no_except_handler_substitutes_a_zero_chance(path):
    assert path.exists(), path
    offenders = substituted_zeros(path.read_text(),
                                  str(path.relative_to(SRC.parent)))
    assert offenders == [], offenders


def test_the_refusal_is_a_raise_and_not_a_fallback():
    """The §13.2 branch that replaced the fallback: it raises, and it is
    not inside an except handler that could swallow it."""
    path = SRC / "dci1v7" / "run" / "gates_run.py"
    tree = ast.parse(path.read_text())
    raises = [n for n in ast.walk(tree)
              if isinstance(n, ast.Raise) and ast.dump(n).count(
                  "records no chance it did not measure")]
    assert len(raises) == 1, "the §13.2 refusal is gone or duplicated"
    guarded = [n for n in ast.walk(tree)
               if isinstance(n, ast.If)
               and any(r in ast.walk(n) for r in raises)
               and "n_unconstrained" in ast.dump(n.test)]
    assert guarded, "the refusal is no longer guarded on n_unconstrained == 0"
