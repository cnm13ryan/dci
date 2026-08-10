"""The declared kappa audit must actually gate, with support required of candidates.

`coupling_audit_max` was declared in ProtocolConfig, printed to the operator as
"a hard measurement-coupling audit at |kappa_C - kappa_B| <= 0.20", and consumed
by nothing: the entire codebase referenced it once, inside that f-string. The
executed `primary_total` reference definition therefore differed from the declared
one.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.coupling_audit import (audit_summary, coupling_audit,
                                         coupling_support, kappa_is_degenerate,
                                         passthrough_audit)

pytestmark = pytest.mark.cpu

FOCAL = "B"
LIMITS = dict(max_gap=0.20, min_probes=20, max_se=0.15)


def _series(values: dict) -> pd.Series:
    return pd.Series(values, dtype=float)


def _bank(kappas: dict, ses=None, ns=None):
    ses = ses or {k: 0.02 for k in kappas}
    ns = ns or {k: 40 for k in kappas}
    return _series(kappas), _series(ses), pd.Series(ns, dtype=int)


# ---------------------------------------------------------------- the tolerance
def test_close_coupling_passes():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.55})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert bool(out.loc["C1", "coupling_audit_ok"])
    assert out.loc["C1", "coupling_gap"] == pytest.approx(0.05)


def test_far_coupling_is_rejected_with_a_reason():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.85})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not bool(out.loc["C1", "coupling_audit_ok"])
    assert "coupling audit" in out.loc["C1", "coupling_audit_reason"]
    assert out.loc["C1", "adjusted_gap"] > 0.20


def test_uncertainty_makes_admission_harder_never_easier():
    """A candidate just inside the tolerance is pushed out by imprecision."""
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.68}, ses={FOCAL: 0.01, "C1": 0.01})
    tight = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert bool(tight.loc["C1", "coupling_audit_ok"])
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.68}, ses={FOCAL: 0.10, "C1": 0.10})
    loose = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not bool(loose.loc["C1", "coupling_audit_ok"])
    assert (float(loose.loc["C1", "adjusted_gap"])
            > float(tight.loc["C1", "adjusted_gap"]))


# ------------------------------------------------------ candidate-level support
def test_candidate_with_too_few_probes_fails_the_audit():
    """Unmeasurable is not matched: it has failed to take the audit."""
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.50}, ns={FOCAL: 40, "C1": 3})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not bool(out.loc["C1", "coupling_audit_ok"])
    assert not bool(out.loc["C1", "support_ok"])
    assert "informative probes" in out.loc["C1", "coupling_audit_reason"]


def test_candidate_with_imprecise_kappa_fails_the_audit():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.50}, ses={FOCAL: 0.02, "C1": 0.40})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not bool(out.loc["C1", "coupling_audit_ok"])
    assert "exceeds the ceiling" in out.loc["C1", "coupling_audit_reason"]


def test_candidate_with_undefined_kappa_fails_the_audit():
    k, se, n = _bank({FOCAL: 0.50, "C1": np.nan})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not bool(out.loc["C1", "coupling_audit_ok"])
    assert "undefined" in out.loc["C1", "coupling_audit_reason"]


def test_unusable_focal_estimate_fails_every_candidate():
    """A control may not be judged against an unusable focal reference point."""
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.50, "C2": 0.52},
                     ns={FOCAL: 2, "C1": 40, "C2": 40})
    out = coupling_audit(k, se, n, FOCAL, ["C1", "C2"], uncertainty_q=1.0, **LIMITS)
    assert not out["coupling_audit_ok"].any()
    assert all("focal coupling unusable" in r
               for r in out["coupling_audit_reason"])


def test_support_rule_matches_the_focal_rule():
    assert coupling_support(0.5, 0.02, 40, 20, 0.15)[0]
    assert not coupling_support(0.5, 0.02, 19, 20, 0.15)[0]
    assert not coupling_support(0.5, 0.16, 40, 20, 0.15)[0]
    assert not coupling_support(np.nan, 0.02, 40, 20, 0.15)[0]
    assert not coupling_support(0.5, np.nan, 40, 20, 0.15)[0]


def test_focal_is_never_audited_against_itself():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.50})
    out = coupling_audit(k, se, n, FOCAL, [FOCAL, "C1"], uncertainty_q=1.0, **LIMITS)
    assert FOCAL not in out.index


def test_summary_separates_no_support_from_over_tolerance():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.52, "C2": 0.95, "C3": 0.50},
                     ns={FOCAL: 40, "C1": 40, "C2": 40, "C3": 1})
    out = coupling_audit(k, se, n, FOCAL, ["C1", "C2", "C3"], uncertainty_q=1.0,
                        **LIMITS)
    s = audit_summary(out)
    assert s["n_candidates"] == 3
    assert s["n_passed"] == 1
    assert s["n_over_tolerance"] == 1     # C2: measurable but too far
    assert s["n_no_support"] == 1         # C3: not measurable


# ------------------------------------------------------ measurement quality
def test_degenerate_kappa_is_detected():
    """A kappa collapsing onto one or two values makes the audit vacuous."""
    flat = kappa_is_degenerate(_series({"a": 0.0, "b": 0.0, "c": 0.0}),
                               _series({"a": 0.0, "b": 0.0, "c": 0.0}))
    assert flat["degenerate"] and flat["all_zero"] and flat["n_distinct"] == 1
    two = kappa_is_degenerate(_series({"a": 0.0, "b": 0.5, "c": 0.5}),
                              _series({"a": 0.01, "b": 0.01, "c": 0.01}))
    assert two["degenerate"] and two["n_distinct"] == 2
    rich = kappa_is_degenerate(_series({"a": 0.1, "b": 0.4, "c": 0.7, "d": 0.9}),
                               _series({k: 0.01 for k in "abcd"}))
    assert not rich["degenerate"] and rich["spread"] == pytest.approx(0.8)


# ------------------------------------------------------------------ fixtures
def test_passthrough_is_marked_and_only_for_fixtures():
    out = passthrough_audit(["X", "Y"])
    assert out.attrs.get("passthrough_fixture") is True
    assert bool(out["coupling_audit_ok"].all())
    # An empty passthrough still carries the marker, which is what lets Gate 0's
    # synthetic ids fill True while real admission fills False.
    assert passthrough_audit([]).attrs.get("passthrough_fixture") is True


def test_real_audit_is_not_marked_as_a_fixture():
    k, se, n = _bank({FOCAL: 0.50, "C1": 0.50})
    out = coupling_audit(k, se, n, FOCAL, ["C1"], uncertainty_q=1.0, **LIMITS)
    assert not out.attrs.get("passthrough_fixture", False)
