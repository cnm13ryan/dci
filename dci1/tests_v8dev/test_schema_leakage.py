"""§13 of the task: no composed outcome can reach the screen or the spectrum
selection. The schema is closed, the forbidden list is generous, and the
package's imports carry no composed table."""
from __future__ import annotations

import ast
import pathlib

import pytest

from dci1v4.errors import ProtocolError
from dci1v8dev.prescreen.schema import (
    FORBIDDEN_PRESCREEN_FIELDS,
    PrescreenRung,
    load_prescreen_table,
    rung_from_rates,
)
from dci1v8dev.spectrum.selection import select_spectrum

from .conftest import calibration_row, rung

ROW = {"kind": "MK1", "severity": 3, "solo_k": 12, "solo_n": 24,
       "chance_k": 0.0, "chance_n": 24.0, "vacuous_k": 0, "n_topics": 24,
       "draws_per_topic": 1}


@pytest.mark.parametrize("field", ["delta_r", "d_b_from_r", "composed_rate",
                                   "B_plus_R", "interference", "delta_diff",
                                   "calibration_c4", "gate3_verdict",
                                   "survived_calibration", "v_stab"])
def test_a_composed_or_downstream_field_is_refused_by_name(field):
    with pytest.raises(ProtocolError, match="pre-screen rule may read only"):
        load_prescreen_table([{**ROW, field: 0.3}])


def test_an_unknown_field_is_refused_because_the_schema_is_closed():
    with pytest.raises(ProtocolError, match="closed"):
        load_prescreen_table([{**ROW, "score": 0.3}])


def test_the_forbidden_list_includes_every_v7_calibration_name():
    from dci1v7.stages.calibration_table import FORBIDDEN_CALIBRATION_FIELDS
    assert set(FORBIDDEN_CALIBRATION_FIELDS) <= set(FORBIDDEN_PRESCREEN_FIELDS)


def test_counts_are_validated_not_trusted():
    with pytest.raises(ProtocolError):
        PrescreenRung(**{**ROW, "solo_k": 30})
    with pytest.raises(ProtocolError):
        PrescreenRung(**{**ROW, "solo_k": 12.0})
    with pytest.raises(ProtocolError):
        PrescreenRung(**{**ROW, "n_topics": 12})       # layout != solo_n
    with pytest.raises(ProtocolError, match="probe-only"):
        PrescreenRung(**{**ROW, "kind": "PS1"})        # probe-only stand-in
    with pytest.raises(ProtocolError, match="not a registered"):
        PrescreenRung(**{**ROW, "kind": "ZZ9"})
    with pytest.raises(ProtocolError, match="can only pick"):
        PrescreenRung(**{**ROW, "severity": 99})       # outside the reserve


def test_rates_from_a_record_must_be_multiples_of_a_draw():
    r = rung_from_rates("MK1", 3, solo=0.5, chance=0.0261, n_topics=24)
    assert (r.solo_k, r.solo_n) == (12, 24)
    assert abs(r.chance_k - 0.0261 * 24) < 1e-9        # effective count
    with pytest.raises(ProtocolError, match="multiple"):
        rung_from_rates("MK1", 3, solo=0.51, chance=0.0, n_topics=24)


def test_merging_a_batch_pools_counts_and_refuses_a_mixed_layout():
    a = rung("MK1", 3, 12)
    b = rung("MK1", 3, 10)
    m = a.merged(b)
    assert (m.solo_k, m.solo_n, m.n_topics, m.draws_per_topic) == (22, 48, 24, 2)
    c = PrescreenRung(kind="MK1", severity=3, solo_k=6, solo_n=12, chance_k=0.0,
                      chance_n=12.0, n_topics=6, draws_per_topic=2)
    with pytest.raises(ProtocolError, match="batch must add draws"):
        a.merged(c)
    with pytest.raises(ProtocolError):
        a.merged(rung("MK1", 4, 1))


def test_the_spectrum_selection_accepts_only_calibration_rows_with_no_composed_field():
    rows = [calibration_row("MK1", q, solo=s)
            for q, s in ((2, 0.85), (5, 0.70), (8, 0.45))]
    out = select_spectrum(rows, iota_a=0.68)
    assert set(out) >= {"points", "coverage", "identified"}
    # CalibrationRow is frozen: a composed attribute cannot be attached
    with pytest.raises((AttributeError, TypeError)):
        rows[0].delta_r = 0.1              # frozen dataclass
    from dci1v7.stages.calibration_table import load_calibration_table
    with pytest.raises(ProtocolError):
        load_calibration_table(
            [{"kind": "MK1", "severity": 2, "split": "pooled",
              "model_key": "fixture-model", "solo_compliance": 0.8,
              "chance_compliance": 0.0, "solo_vacuity": 0.0,
              "composed_compliance": 0.5}],
            model_key="fixture-model", m_star=9, split="pooled")


def test_the_package_imports_no_composed_observation_module():
    """The pre-freeze package never imports the modules that hold composed
    outcomes (observations, estimators, claims, masking). The one place in
    v8 that may is the post-freeze half of ``dci1v8dev.confirm`` ---
    ``analysis.py`` (the registered estimators, called per frame after a
    verified freeze) --- and nothing before the freeze, the confirm
    layer's own pre-freeze stages included."""
    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "dci1v8dev"
    banned = {"dci1v7.analysis.observations", "dci1v7.analysis.estimators",
              "dci1v7.analysis.claims", "dci1v7.analysis.masking",
              "dci1v7.run.analysis_run", "dci1v7.run.confirmatory_run"}
    allowed = {root / "confirm" / "analysis.py"}
    imported_by_allowed = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            # `from dci1v7.analysis import estimators` names the banned
            # module through the alias, not through `node.module`; both
            # spellings are resolved (the earlier form of this test read
            # `node.module` alone and would have let that spelling through).
            names = ([node.module] + [f"{node.module}.{a.name}" for a in node.names]
                     if isinstance(node, ast.ImportFrom) else
                     [a.name for a in node.names] if isinstance(node, ast.Import)
                     else [])
            for name in names:
                if name in banned:
                    if path in allowed:
                        imported_by_allowed.add(name)
                        continue
                    raise AssertionError(f"{path.relative_to(root)} imports {name}")
    # the post-freeze analysis does read them --- that is what it is for
    assert {"dci1v7.analysis.observations",
            "dci1v7.analysis.estimators"} <= imported_by_allowed
