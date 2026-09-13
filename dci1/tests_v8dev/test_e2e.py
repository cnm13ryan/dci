"""The candidate pipeline end to end on synthetic worlds: determinism, order
invariance, composed-outcome invariance, severity-range exploration, the
spectrum extremes, wording confusion, and the not-identified cases."""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

from dci1v7.stages.calibration_table import FORBIDDEN_CALIBRATION_FIELDS
from dci1v8dev.e2e import FamilyTruth, World, run_candidate, truth_of

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import v8_pipeline_validation as V  # noqa: E402

RES = 120


def _strip(rec):
    return json.loads(json.dumps(rec, sort_keys=True))


@pytest.fixture(scope="module")
def worlds():
    return V.worlds()


def test_same_seed_same_record_and_family_order_does_not_matter(worlds):
    w = worlds["wide"]
    a = _strip(run_candidate(w, stability_resamples=RES))
    b = _strip(run_candidate(w, stability_resamples=RES))
    c = _strip(run_candidate(w, stability_resamples=RES,
                             family_order=list(reversed(sorted(w.families)))))
    assert a == b == c
    assert a["identified"] and a["selection"]["coverage"]["projection"]["se_beta"] < 0.05


def test_a_composed_outcome_in_the_world_cannot_move_the_record(worlds):
    w = worlds["wide"]
    fams = {k: FamilyTruth(**{**f.__dict__, "interference": 0.5}) for k, f in w.families.items()}
    poisoned = World(families=fams, a_curve=w.a_curve, name=w.name, seed=w.seed)
    assert _strip(run_candidate(w, stability_resamples=RES)) == \
        _strip(run_candidate(poisoned, stability_resamples=RES))


def test_no_rule_module_reads_a_composed_field():
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "dci1v8dev"
    banned = set(FORBIDDEN_CALIBRATION_FIELDS)
    for path in list((src / "spectrum").glob("*.py")) + list((src / "prescreen").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Attribute):
                assert node.attr.lower() not in banned, (path.name, node.lineno, node.attr)
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                    and isinstance(node.slice.value, str):
                assert node.slice.value.lower() not in banned, (path.name, node.lineno)


def test_a_too_easy_ladder_is_extended_into_the_reserve_and_identified(worlds):
    """The 2507 case: every marker ladder above 0.90 solo over q ≤ 8; the
    difficulty the spectrum needs sits at q = 9–12. The screen sends the
    families to the second pass with the next reserve severities, the
    posterior accepts them, the spaced retention forwards reserve rungs, and
    the selected set is identified."""
    w = worlds["too_easy_reserve"]
    rec = run_candidate(w, stability_resamples=RES)
    picks = rec["final_screen"]["reserve_picks"]
    picked = {q for batch in picks.values() for qs in batch.values() for q in qs}
    assert picked and min(picked) >= 9
    forwarded_reserve = [c for c in rec["retention"]["forwarded"]
                         if c.startswith("MK") and int(c.split(":")[1]) >= 9]
    assert forwarded_reserve
    accepted = set(rec["final_screen"]["statuses"]["SCREEN_ACCEPT"])
    assert {"MK1", "MK2", "MK3"} & accepted
    assert rec["identified"] and truth_of(w)["identified"]


def test_one_sided_and_flat_worlds_are_not_identified_and_say_why(worlds):
    for name, side_word in (("one_sided", "above"), ("flat", "")):
        rec = run_candidate(worlds[name], stability_resamples=RES)
        assert not rec["identified"], name
        assert not truth_of(worlds[name])["identified"], name
        reasons = " ".join(rec["selection"]["coverage"]["reasons"])
        assert side_word in reasons


def test_extreme_stable_rungs_survive_and_degenerate_chance_vacuous_rungs_fail(worlds):
    rec = run_candidate(worlds["extremes"], stability_resamples=RES)
    valid = set(rec["validity"]["spectrum_valid"])
    high = [c for c in valid if c.startswith(("MK1:", "MK2:", "XC1:"))
            and rec["calibration"]["rows"][c]["solo"] > 0.855]
    assert high, "a chance-free rung beyond V_head's 0.855 cap must be spectrum-valid"
    assert not any(c.startswith(("CR5:", "RF6:", "RF7:")) for c in valid)
    ff = rec["validity"]["first_failing_spectrum"]
    assert all(ff[c] == "V_coord" for c in ff if c.startswith("RF7:"))       # vacuous
    assert all(ff[c] == "V_coord" for c in ff if c.startswith("RF6:"))       # degenerate
    assert all(ff[c] in ("V_coord", "V_chance") for c in ff if c.startswith("CR5:"))
    assert rec["identified"]


def test_wording_confused_families_are_recovered_by_the_v8_frames(worlds):
    v7 = run_candidate(worlds["wording_confusion_v7"], stability_resamples=RES)
    v8 = run_candidate(worlds["wording_confusion_v8"], stability_resamples=RES)
    acc7 = set(v7["final_screen"]["statuses"]["SCREEN_ACCEPT"])
    acc8 = set(v8["final_screen"]["statuses"]["SCREEN_ACCEPT"])
    assert {"MK3", "MK6"} <= acc8
    assert not ({"MK3", "MK6"} <= acc7)
    assert len(v8["selection"]["families"]) > len(v7["selection"]["families"])


def test_the_local_arm_keeps_the_true_local_families(worlds):
    w = worlds["wide"]
    rec = run_candidate(w, stability_resamples=RES)
    found = {c.split(":")[0] for c in rec["validity"]["local_valid"]}
    truth = set(truth_of(w)["local_families"])
    assert len(found & truth) / len(truth) >= 0.75
    assert len(rec["core_references"]) == 3
    assert rec["backups"]["backups"] and all(
        f not in rec["core_references"] for f in rec["backups"]["backups"])


def test_costs_are_stated_and_below_the_v7_retention(worlds):
    rec = run_candidate(worlds["wide"], stability_resamples=RES)
    c = rec["costs"]
    assert c["calibration"] == c["calibration_rungs"] * 768
    assert c["calibration_rungs"] < 112
    assert c["spectrum_confirmatory"] == rec["selection"]["n_spectrum_references"] * 3 * 384 * 8
