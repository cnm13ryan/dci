"""F. §13.7's two-split stability rule, and D16's unresolved population."""
from __future__ import annotations

import random

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions
from dci1v7.stages import stability as S
from tests_v7.conftest import calibration_row


def _split_rows(rate_a: float, rate_b: float, *, seed: int = 5,
                n: int = 96):
    rng = random.Random(seed)
    per_a = tuple(1.0 if rng.random() < rate_a else 0.0 for _ in range(n))
    per_b = tuple(1.0 if rng.random() < rate_b else 0.0 for _ in range(n))
    a = calibration_row("MK1", 3, solo=sum(per_a) / n, split=C.CALIBRATION_A,
                        n_topics=n, per_topic=per_a)
    b = calibration_row("MK1", 3, solo=sum(per_b) / n, split=C.CALIBRATION_B,
                        n_topics=n, per_topic=per_b)
    return S.SplitPair("MK1:3", a, b)


def _verdict(pair, **kwargs):
    return S.stability_verdict(
        pair, iota_a_by_split={C.CALIBRATION_A: 0.69, C.CALIBRATION_B: 0.69},
        solo_a_by_split={C.CALIBRATION_A: 0.69, C.CALIBRATION_B: 0.69},
        seed=3, resamples=kwargs.pop("resamples", 400), **kwargs)


def test_a_stable_candidate_passes_on_both_splits():
    verdict = _verdict(_split_rows(0.70, 0.72))
    assert verdict["passed"]
    assert verdict["admissible_on_both_splits"]
    assert verdict["equivalence_bound"] == 0.20


def test_an_unstable_candidate_fails_the_equivalence_rule():
    verdict = _verdict(_split_rows(0.45, 0.85))
    assert not verdict["passed"]
    assert "bootstrap interval" in verdict["reason"]


def test_the_rule_is_an_equivalence_not_a_threshold_on_the_point():
    """An imprecise candidate is PENALISED, which is the correct direction."""
    precise = _verdict(_split_rows(0.70, 0.70, n=96))
    imprecise = _verdict(_split_rows(0.70, 0.70, n=6))
    width = lambda v: (v["iota_split_difference"]["upper"]
                       - v["iota_split_difference"]["lower"])
    assert width(imprecise) > width(precise)


def test_missing_per_topic_values_are_not_a_pass():
    a = calibration_row("MK1", 3, solo=0.70, split=C.CALIBRATION_A,
                        n_topics=96)
    b = calibration_row("MK1", 3, solo=0.71, split=C.CALIBRATION_B,
                        n_topics=96)
    verdict = _verdict(S.SplitPair("MK1:3", a, b))
    assert not verdict["passed"]
    assert "untested equivalence is not a satisfied one" in verdict["reason"]


def test_a_split_pair_refuses_a_mismatch():
    a = calibration_row("MK1", 3, solo=0.7, split=C.CALIBRATION_A)
    b = calibration_row("MK2", 3, solo=0.7, split=C.CALIBRATION_B)
    with pytest.raises(ProtocolError):
        S.SplitPair("MK1:3", a, b)
    with pytest.raises(ProtocolError):
        S.SplitPair("MK1:3", a, a)


def test_a_pooled_table_is_refused_where_a_split_is_expected():
    rows = [calibration_row("MK1", 3, solo=0.7, split="pooled")]
    with pytest.raises(ProtocolError):
        S.assert_not_pooled(rows, split=C.CALIBRATION_A)


def test_iota_a_is_subject_to_the_same_rule():
    rng = random.Random(9)
    a = [1.0 if rng.random() < 0.69 else 0.0 for _ in range(96)]
    b = [1.0 if rng.random() < 0.70 else 0.0 for _ in range(96)]
    out = S.assert_iota_a_stable(per_topic_a=a, per_topic_b=b, chance_a=0.0,
                                 chance_b=0.0, seed=1, resamples=400)
    assert out["passed"]
    far = [1.0 if rng.random() < 0.30 else 0.0 for _ in range(96)]
    out2 = S.assert_iota_a_stable(per_topic_a=a, per_topic_b=far,
                                  chance_a=0.0, chance_b=0.0, seed=1,
                                  resamples=400)
    assert not out2["passed"]


def test_the_bootstrap_is_deterministic_under_the_registered_seed():
    pair = _split_rows(0.70, 0.72)
    first = _verdict(pair)["iota_split_difference"]
    second = _verdict(pair)["iota_split_difference"]
    assert first == second


def test_calibration_b_measures_the_complete_population(restore_decisions):
    """§34 D16, closed at ``complete_population``.

    The whole carried set is remeasured on Calibration-B, not only what
    Calibration-A admitted --- so §13.7 tests the stability of the candidate
    landscape rather than reconfirming a set already selected once (R11).
    """
    assert decisions.value_of("D16") == "complete_population"
    assert S.calibration_b_population(["a", "b"], ["a"]) == ("a", "b")
    restore_decisions.override_for_testing("D16", "a_survivors")
    assert S.calibration_b_population(["a", "b"], ["a"]) == ("a",)


def test_the_split_admissibility_components_are_the_registered_four():
    assert S.SPLIT_ADMISSIBILITY_COMPONENTS == ("V_head", "V_chance",
                                               "V_inter", "V_diff")
