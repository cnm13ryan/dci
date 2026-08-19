"""Characterization of the completed v3 registered results (read-only).

Pins the numbers and claim outcomes that RESULTS_V3.md reports against
the stored evidence, and re-derives every claim label through the
registered emitters, so any future drift between documentation, claim
logic, and the signed artifacts fails loudly. The real evidence tree is
gitignored and machine-local; every test here skips cleanly where it is
absent. Nothing is written.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v3.analysis import claims
from dci1v3.engine.context import DCI1_ROOT

EVIDENCE = DCI1_ROOT / "evidence" / "dci1-v3"

pytestmark = pytest.mark.skipif(
    not (EVIDENCE / "gemma-3n-e2b-it" / "analysis" / "unmasked"
         / "result.json").exists(),
    reason="completed registered evidence tree not present")

#: (estimate, simultaneous, marginal) per primary member, from the
#: registered unmasked analyses — the numbers RESULTS_V3.md §2 reports.
REGISTERED_F1 = {
    "gemma-3n-e2b-it": {
        "tau_target_first": (0.006944444444444478,
                             (-0.07986111111111109, 0.09375000000000004),
                             (-0.0677083333333333, 0.08333333333333337)),
        "tau_added_first": (-0.026041666666666644,
                            (-0.11680122031404971, 0.06471788698071643),
                            (-0.10590277777777775, 0.053819444444444475)),
    },
    "gemma-3n-e4b-it": {
        "tau_target_first": (0.09027777777777783,
                             (-0.003472222222222196, 0.18402777777777785),
                             (0.00694444444444448, 0.17187500000000003)),
        "tau_added_first": (0.03993055555555559,
                            (-0.047304266359941706, 0.1271653774710529),
                            (-0.03645833333333331, 0.11631944444444446)),
    },
}

EXPECTED_CLAIMS = {
    "gemma-3n-e2b-it": {
        "tau_target_first": {"direction": claims.DIRECTION_UNRESOLVED,
                             "magnitude": claims.EQUIVALENCE,
                             "status": "OK"},
        "tau_added_first": {"direction": claims.DIRECTION_UNRESOLVED,
                            "magnitude": claims.MAGNITUDE_UNRESOLVED,
                            "status": "OK"},
    },
    "gemma-3n-e4b-it": {
        "tau_target_first": {"direction": claims.DIRECTION_UNRESOLVED,
                             "magnitude": claims.MAGNITUDE_UNRESOLVED,
                             "status": "OK"},
        "tau_added_first": {"direction": claims.DIRECTION_UNRESOLVED,
                            "magnitude": claims.MAGNITUDE_UNRESOLVED,
                            "status": "OK"},
    },
}


def _result(model: str) -> dict:
    path = EVIDENCE / model / "analysis" / "unmasked" / "result.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("model", sorted(REGISTERED_F1))
def test_primary_estimates_and_intervals_pinned(model):
    f1 = {e["name"]: e for e in _result(model)["families"]["F1"]["members"]}
    for name, (est, sim, marg) in REGISTERED_F1[model].items():
        entry = f1[name]
        assert entry["estimate"] == pytest.approx(est, abs=1e-12)
        assert tuple(entry["simultaneous"]) == pytest.approx(sim, abs=1e-12)
        assert tuple(entry["marginal"]) == pytest.approx(marg, abs=1e-12)
        assert entry["status"] == "OK"


@pytest.mark.parametrize("model", sorted(EXPECTED_CLAIMS))
def test_claims_rederive_from_registered_emitter(model):
    result = _result(model)
    f1 = {e["name"]: e for e in result["families"]["F1"]["members"]}
    for name, expected in EXPECTED_CLAIMS[model].items():
        rederived = claims.primary_claims(tuple(f1[name]["simultaneous"]))
        assert rederived == expected == result["primary_claims"][name]


@pytest.mark.parametrize("model", sorted(REGISTERED_F1))
def test_exchangeability_rederives_false(model):
    result = _result(model)
    intervals = [tuple(e["simultaneous"]) if e["status"] == "OK" else None
                 for e in result["families"]["F2"]["members"]]
    assert claims.exchangeability_holds(intervals) is False
    assert result["exchangeability_holds"] is False


def test_e2b_equivalence_is_the_only_resolved_magnitude():
    resolved = [
        (model, name, entry["magnitude"])
        for model in REGISTERED_F1
        for name, entry in _result(model)["primary_claims"].items()
        if entry["magnitude"] != claims.MAGNITUDE_UNRESOLVED]
    assert resolved == [
        ("gemma-3n-e2b-it", "tau_target_first", claims.EQUIVALENCE)]


def test_qwen_terminals_are_reference_pool_mismatch():
    for model in ("qwen3-4b", "qwen3-4b-instruct-2507"):
        report = json.loads(
            (EVIDENCE / model / "terminal_report.json").read_text())
        assert report["payload"]["status"] == "REFERENCE_POOL_MISMATCH"
        eligible = [
            (family, severity)
            for family, entry
            in report["payload"]["body"]["admission_table"].items()
            for severity, cell in entry["severities"].items()
            if all(cell["conditions"].values())]
        assert len(eligible) < 3
