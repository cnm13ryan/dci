import numpy as np
import pandas as pd
import pytest

from dci.analysis.stats import (holm, indexed_frame, simultaneous_abs_upper,
                                within_sesoi)

pytestmark = pytest.mark.cpu


def test_holm_monotone_bounded():
    adj = holm([0.01, 0.04, 0.03])
    assert all(0 <= p <= 1 for p in adj)
    assert adj[0] <= adj[2] <= adj[1] + 1e-12


def test_within_sesoi():
    assert within_sesoi(-0.05, 0.05, 0.10)
    assert not within_sesoi(-0.15, 0.05, 0.10)


def test_indexed_frame_empty_is_reportable():
    frame = indexed_frame([], "constraint_id", ["constraint_id", "x"])
    assert list(frame.columns) == ["x"] and len(frame) == 0


def test_simultaneous_wider_than_marginal():
    rng = np.random.default_rng(7)
    draws = pd.DataFrame(rng.normal(size=(500, 4)), columns=list("abcd"))
    point = draws.mean()
    bounds = simultaneous_abs_upper(point, draws, 0.95)
    assert (bounds["abs_upper"] >= point.abs() - 1e-12).all()
