"""Protocol v2 (revision 2026-10, R1-R13): library v2, bank v2, the Stage B
forecast, the carry rule, the fixed-A-and-B verdict, and a synthetic run of
the whole v2 pilot. v1 stays as it was: its library, matrix and pilot are
pinned by ``test_pilot_regression`` and the v1 checks below."""
from __future__ import annotations

import json
import random
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import library as L
from dci.batch1 import pipeline as P
from dci.batch1 import references as R
from dci.batch1 import revision as REV
from dci.batch1 import runner as RUN
from dci.batch1 import synthetic as SY
from dci.batch1 import topics as TOP
from dci.batch1 import verifiers as V
from dci.batch1.scoring import Count
from tests.batch1.helpers import make_root

pytestmark = pytest.mark.cpu
V2 = CFG.REVISION_CONFIG
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pilot_2026_10_25b"
V21 = CFG.CONFIGS["v2.1"]
#: The v2.1 pilot at reduced size: one topic per area in T1 and in T2.
SMALL_V2 = replace(V21, stage1_topics=12, stage2_topics=12, pilot_topics=24,
                   stability_replicates=4, forecast_draws=200)


@pytest.fixture(autouse=True)
def library_version():
    L.set_library_version("v2")
    yield "v2"
    L.set_library_version("v1")


@pytest.fixture(scope="module")
def matrix():
    with L.using_library_version("v2"):
        return COMPAT.compatibility_matrix()


def _rates(seed: int, spread: float):
    rng = random.Random(seed)
    return {k: min(1.0, max(0.0, v + rng.uniform(-spread, spread)))
            for k, v in SY.full_rates(cfg=V2).items()}


# ------------------------------------------------------------- v1 untouched

def test_v1_library_and_matrix_are_the_frozen_pilot_s():
    """Every v1 constraint's specification (wording, parameters, its own
    verifier's source) and the v1 matrix are the pilot's. The library hash
    itself moves: it carries the whole verifiers file, which v2 extends."""
    freeze1 = json.loads((FIXTURE / "freeze1.json").read_text())
    with L.using_library_version("v1"):
        library = L.library_manifest()
        assert library["schema"] == "dci.batch1/library/v1"
        specs = {c["cid"]: c["spec_hash"] for c in library["focal_a"]
                 + library["focal_b"] + library["references"]}
        assert specs == freeze1["library"]["spec_hashes"]
        assert COMPAT.matrix_hash(COMPAT.compatibility_matrix()) == \
            freeze1["compatibility"]["hash"]


# --------------------------------------------------------------- library v2

def test_library_v2_has_the_approved_shape(matrix):
    refs = L.reference_library()
    assert len(refs) == 161
    new = [c for c in refs if c.family_id == "exact_word_count"
           and c.p["word"] in L.V2_WORDS]
    assert {c.p["word"] for c in new} == set(L.V2_WORDS)
    assert all(len(c.p["word"]) <= 8 for c in new)
    assert [c.p["n"] for c in L.a_candidates()] == [4, 5, 6]
    assert {c.operation for c in refs} >= {"positional"}
    assert '"indeed"' in L.constraint_by_id()["ew.indeed.2"].render("F0")
    assert matrix["counts"]["UNRESOLVED"] == 0
    assert matrix["task_level"]["counts"].get("TASK_UNRESOLVED", 0) == 0


@pytest.mark.parametrize("text, n", [("In 1990 there were 3,500 of them.", 2),
                                     ("Version 2.5 of B12 shipped.", 1),
                                     ("No numbers here.", 0)])
def test_numerals_are_counted_as_digit_runs(text, n):
    assert V.exact_numeral_count(text, n=n).passed


def test_positional_verifiers():
    assert V.positional_word("Today, it rains.", where="start",
                             word="today").passed
    assert V.positional_word("We go onward.", where="end",
                             word="onward").passed
    assert not V.positional_word("Onward we go.", where="end",
                                 word="onward").passed
    assert V.positional_question("Is it so?\n").passed
    assert V.positional_question('He asked "why?"').passed
    assert not V.positional_question("It is so.").passed


# ------------------------------------------------------------------ bank v2

def test_bank_v2_is_fresh_screened_and_split_t1_t2():
    bank = TOP.load_bank(TOP.SOURCE_PATH_V2)
    split = TOP.split_for(V2)
    assert (len(split.stage1), len(split.stage2), len(split.confirmatory)) \
        == (48, 96, 0)
    v1 = TOP.load_bank()
    assert not {t.topic_id for t in bank} & {t.topic_id for t in v1}
    assert not {t.question for t in bank} & {t.question for t in v1}
    overlap = TOP.overlap_report(bank, bank="v2")
    assert overlap["clean"], overlap["unreviewed"]
    assert "dci/batch1/bank_v1" in overlap["historical_sources"]
    assert TOP.hygiene_report(bank, split)["clean"]


def test_bank_v3_is_fresh_against_every_earlier_bank_and_screened():
    """v2.1's topics (the researcher's condition of 2026-10-26): new T1 and
    T2, disjoint from bank v1 (and so from the 480 reserved) and from bank
    v2, which the v2 run measured."""
    bank = TOP.load_bank(TOP.SOURCE_PATH_V3)
    split = TOP.split_for(V21)
    assert (len(split.stage1), len(split.stage2), len(split.confirmatory)) \
        == (48, 96, 0)
    for earlier in (TOP.load_bank(), TOP.load_bank(TOP.SOURCE_PATH_V2)):
        assert not {t.topic_id for t in bank} & {t.topic_id for t in earlier}
        assert not {t.question for t in bank} & {t.question for t in earlier}
    v2_old = {r["previous_question"] for r in json.loads(
        TOP.SOURCE_PATH_V2.read_text())["revisions"]}
    assert not {t.question for t in bank} & v2_old
    overlap = TOP.overlap_report(bank, bank="v3")
    assert overlap["clean"], overlap["unreviewed"]
    assert {"dci/batch1/bank_v1", "dci/batch1/bank_v2"} <= \
        set(overlap["historical_sources"])
    assert TOP.hygiene_report(bank, split)["clean"]


# ------------------------------------------------- the forecast is the rule

@pytest.mark.parametrize("seed, spread", [(1, 0.3), (2, 0.45), (3, 0.6),
                                          (4, 0.6)])
def test_forecast_rules_equal_the_package_rules(matrix, seed, spread):
    """On point estimates the vectorised D09-D11 give exactly what
    ``references.configuration_report`` gives, configuration by
    configuration."""
    tables = SY.tables_from_rates(_rates(seed, spread), n=48)
    rules = REV._Rules(V2, matrix)
    cids = [c.cid for c in rules.refs]
    k, n = REV._cells(tables, V2, cids)
    ka, na = REV._cells(tables, V2, [V2.fixed_a])
    fast = rules.supported(k / n, (ka / na)[0])
    elig = R.eligibility(tables, V2)
    focal = L.constraint_by_id()[V2.fixed_a]
    slow = {p: [] for p in REV.CONTRASTS}
    for model, frame in R.model_frames(V2):
        for m in V2.b_limits:
            rep = R.configuration_report(tables, V2, matrix, elig, focal,
                                         model, frame, m)
            for p in REV.CONTRASTS:
                if rep["coverage"][p]["supported"] and rep["a_informative"]:
                    slow[p].append((model, m))
    assert {p: sorted(v) for p, v in fast.items()} == \
        {p: sorted(v) for p, v in slow.items()}
    feas = R.feasibility([R.configuration_report(tables, V2, matrix, elig,
                                                 focal, mo, fr, m)
                          for mo, fr in R.model_frames(V2)
                          for m in V2.b_limits], V2, V2.b_limits)
    for p in REV.CONTRASTS:
        assert rules.feasible(fast[p]) == feas[p]["feasible"]


def test_forecast_stops_early_when_a_is_never_admissible(matrix):
    rates = _rates(5, 0.2)
    for key in list(rates):
        if key[2] == V2.fixed_a:
            rates[key] = 0.97                  # A at ceiling everywhere
    fc = REV.forecast(SY.tables_from_rates(rates, n=48),
                      replace(V2, forecast_draws=50), matrix)
    assert not fc["point_gates_pass"]
    assert all(fc["contrasts"][p]["p_feasible"] == 0 for p in REV.CONTRASTS)
    assert fc["early_stop"] and fc["stopped_contrasts"] == ["P1", "P2", "P3"]
    # The fixed A, not the library, is what failed.
    assert fc["fixed_gates_limited"] and fc["p_fixed_gates_pass"] == 0
    assert fc["library_limited"] == [] and fc["stop_reason"] == "fixed_gates"
    assert fc["library_undetermined"]         # no draw passes the gates
    early = CAL.finalize(SY.tables_from_rates({}, n=96), V2, matrix,
                         early_stop=fc["stop_reason"])
    assert early["status"] == "EARLY_STOP_FIXED_A_OR_B"     # not R9's trigger


def test_carry_selection_is_bounded_and_empty_on_early_stop(matrix):
    tables = SY.tables_from_rates(_rates(2, 0.1), n=48)
    cfg = replace(V2, forecast_draws=100)
    sel = REV.select_carry(tables, cfg)
    assert sel["status"] == "CARRIED" and sel["truncated_by_cap"]
    mfs = len(R.model_frames(cfg))
    carried = {c["condition"] for c in sel["cells"] if c["class"] == "CARRY"}
    assert len(carried) == len(sel["carried"]) <= cfg.carry_max_references
    fixed = {c["condition"] for c in sel["cells"] if c["class"] == "FIXED"}
    assert fixed == {cfg.fixed_a, "B.max8", "B.max10"}
    assert len(sel["cells"]) == (len(carried) + 3) * mfs + len(cfg.models)
    assert sel["max_stage2_rows"] <= cfg.max_total_rows
    assert all(c["max_posterior_match"] >= cfg.carry_min_posterior
               for c in sel["carried"])
    tight = REV.select_carry(tables, replace(cfg, carry_max_references=5))
    assert len(tight["carried"]) == 5 and tight["truncated_by_cap"]
    stopped = REV.select_carry(tables, replace(cfg, forecast_min_feasible=1.0))
    if stopped["forecast"]["early_stop"]:
        assert stopped["status"] == "EARLY_STOP" and stopped["cells"] == []


# ------------------------------------------------------- the fixed verdict

def test_fixed_verdict_checks_a_and_b_instead_of_selecting(matrix):
    rates = {k: (0.5 if k[2].startswith("B.") else v)
             for k, v in _rates(1, 0.3).items()}
    ok = CAL.finalize(SY.tables_from_rates(rates, n=96), V2, matrix)
    assert ok["schema"] == "dci.batch1/calibration/v3-fixed"
    assert ok["b"]["selected"] == [8, 10]
    if ok["a"]:
        assert ok["a"]["selected"] == V2.fixed_a
    b_dead = {k: (0.99 if k[2] in ("B.max8", "B.max10") else v)
              for k, v in rates.items()}
    res = CAL.finalize(SY.tables_from_rates(b_dead, n=96), V2, matrix)
    assert res["status"] == "B_NOT_INFORMATIVE"
    a_dead = {k: (0.99 if k[2] == V2.fixed_a else v) for k, v in rates.items()}
    res = CAL.finalize(SY.tables_from_rates(a_dead, n=96), V2, matrix)
    assert res["status"] == "A_NOT_ADMISSIBLE"
    early = CAL.finalize(SY.tables_from_rates({}, n=96), V2, matrix,
                         early_stop=True)
    assert early["status"] == "EARLY_STOP_LIBRARY_LIMITED"


def test_truncation_review_needs_two_rows_in_v2():
    tables = SY.tables_from_rates({("qwen3-4b", "F0", "ew.indeed.2"): 0.5,
                                   ("qwen3-4b", "F1", "ew.indeed.2"): 0.5},
                                  n=24)
    one, two = tables.explicit.values()
    one.truncated, two.truncated = 1, 2     # both above 2% of 24
    flagged = REV.truncation_review(tables, V2)
    assert flagged == [next(k for k, c in tables.explicit.items()
                            if c.truncated == 2)]
    v1 = replace(V2, truncation_review_min_rows=1)
    assert len(REV.truncation_review(tables, v1)) == 2


def test_word_then_count_weights_split_equally_over_words():
    w = R.hierarchical_weights(["ew.indeed.2", "ew.indeed.3", "ew.thus.4"],
                               "word_then_count")
    assert w == {"ew.indeed.2": Fraction(1, 4), "ew.indeed.3": Fraction(1, 4),
                 "ew.thus.4": Fraction(1, 2)}
    v = R.hierarchical_weights(["ew.indeed.2", "ew.indeed.3", "ew.thus.4"])
    assert set(v.values()) == {Fraction(1, 3)}


# ------------------------------------------------- the v2 pilot, end to end
# About five minutes on a laptop (16k Stage A rows, the full library):
# ``pytest -m slow tests/batch1/test_revision.py``.

def _informative_b(model, frame, condition):
    """The default surface, with both B limits mid-band so the run carries."""
    if condition.startswith("B."):
        return 0.5
    return SY.default_truth(model, frame, condition)


@pytest.fixture(scope="module")
def run_v2(tmp_path_factory):
    from dci.batch1 import scoring as S
    S.SCORING_WORKERS = 8                    # the CLI's pool, in a test
    L.set_library_version("v2")
    base = make_root(tmp_path_factory.mktemp("batch1v2"), cfg=SMALL_V2)
    root, f1, approvals = base["root"], base["freeze1"], base["approvals"]
    gen = SY.synthetic_generate(_informative_b, empty_rate=0.01)
    d1 = P.write_stage1_plan(root, f1)
    RUN.execute(root, d1, freeze1=f1, approvals=approvals, generate=gen)
    P.score_stage(root, D.STAGE1)
    d2 = P.write_stage2_plan(root, f1)
    RUN.execute(root, d2, freeze1=f1, approvals=approvals, generate=gen)
    P.score_stage(root, D.STAGE2)
    result = P.finalize(root, f1)
    f2 = P.freeze_membership(root, f1, approvals)
    return {**base, "d1": d1, "d2": d2, "result": result, "f2": f2}


@pytest.mark.slow
def test_v2_freeze1_binds_the_v2_protocol(run_v2):
    f1 = run_v2["freeze1"]
    assert f1["config"]["protocol"] == "v2"
    assert f1["library"]["n_references"] == 161
    # The reduced panel leaves 120 of the 144 v2 topics unused; the full v2
    # configuration uses all of them (test_bank_v2_is_fresh_...).
    assert f1["topics"]["counts"] == {"stage1": 12, "stage2": 12,
                                      "confirmatory_reserved": 120}
    assert f1["topics"]["overlap_clean"] and f1["topics"]["hygiene_clean"]
    assert f1["compatibility"]["unresolved"] == []


@pytest.mark.slow
def test_v2_stage1_screens_every_reference_on_t1(run_v2):
    cfg = EV.config_of(run_v2["freeze1"])
    conds = {r["condition"] for r in run_v2["d1"]}
    assert len(conds) == 161 + 3 + 2 + 1
    t1 = {t.topic_id for t in TOP.split_for(cfg).stage1}
    assert {r["topic_id"] for r in run_v2["d1"]} == t1


@pytest.mark.slow
def test_v2_1_measures_every_reference_on_t2(run_v2):
    sel = json.loads((run_v2["root"] / "plan" /
                      "stage2_selection.json").read_text())
    if sel["status"] == "EARLY_STOP":
        pytest.skip("the synthetic run stopped early")
    assert sel["carry_mode"] == "all" and len(sel["carried"]) == 161
    assert len(run_v2["d2"]) == (161 + 3) * 8 * 12 + 4 * 12


@pytest.mark.slow
def test_v2_stage2_measures_on_t2_only_and_decides_from_t2(run_v2):
    cfg = EV.config_of(run_v2["freeze1"])
    split = TOP.split_for(cfg)
    if not run_v2["d2"]:
        pytest.skip("the synthetic run stopped early")
    assert {r["topic_id"] for r in run_v2["d2"]} == \
        {t.topic_id for t in split.stage2}
    tables = json.loads((run_v2["root"] / "tables.json").read_text())
    assert {v["n"] for v in tables["explicit"].values()} <= \
        set(range(len(split.stage2) * cfg.stage2_draws + 1))
    carried = {c["condition"] for c in json.loads(
        (run_v2["root"] / "plan" / "stage2_selection.json").read_text())["cells"]}
    assert {k.split("|")[-1] for k in tables["explicit"]} == carried - {"task_only"}


@pytest.mark.slow
def test_v2_freeze2_is_complete_and_validates(run_v2):
    f2 = run_v2["f2"]
    assert f2["schema"] == "dci.batch1/freeze2/v5" and f2["protocol"] == "v2"
    assert f2["synthetic"]
    assert "forecast" in f2["stability"]
    assert f2["selected"]["a"] in (V2.fixed_a, None)
    confirmatory = f2["confirmatory_interface"]["confirmatory_topics"]
    assert confirmatory["bank"] == "v1" and confirmatory["reserved"] == 480
    rep = f2["reporting"]
    assert not rep["deciding"]
    assert len(rep["a_diagnostics_t1"]) == 3
    if f2["calibration_status"] != "EARLY_STOP_LIBRARY_LIMITED":
        assert set(rep["sensitivities"]) == {"tolerance_0.15", "tolerance_0.2",
                                             "confident", "iota", "primary"}
        assert rep["agreement"]["references"] == 161
    assert P.validate_membership(run_v2["root"], run_v2["freeze1"],
                                 run_v2["approvals"]) == []


@pytest.mark.slow
def test_v2_cli_summaries_and_report_work(run_v2, capsys):
    """The CLI summaries and the readable report must not assume v1's
    shapes (the first v2 pilot's select-refinement and finalize-calibration
    exited 1 after writing their outputs)."""
    from dci.batch1 import cli
    root = str(run_v2["root"])
    assert cli.main(["select-refinement", "--root", root]) == 0
    assert '"carried"' in capsys.readouterr().out
    assert cli.main(["finalize-calibration", "--root", root]) == 0
    report = (run_v2["root"] / "reference_selection.md").read_text()
    assert "Stage B forecast on T1" in report
    assert "R4: fixed" in report


# ---------------------------------------------------------------- v2.1

def test_v2_1_carries_everything_within_its_budget(matrix):
    tables = SY.tables_from_rates(_rates(2, 0.1), n=48)
    sel = REV.select_carry(tables, replace(V21, forecast_draws=50))
    if sel["status"] == "CARRIED":
        assert len(sel["carried"]) == 161 and not sel["truncated_by_cap"]
        assert sel["max_stage2_rows"] == (161 + 3) * 8 * 96 + 4 * 96
    assert sel["stage1_rows"] == sum(c.n for c in tables.explicit.values())
    from dci.batch1.store import RunError
    with pytest.raises(RunError, match="budget"):
        REV.select_carry(tables, replace(V21, forecast_draws=50,
                                         max_total_rows=150000))


def test_v2_decisions_page_has_v2_notes_and_modules():
    from dci.batch1 import report as REP
    V21.activate()
    page = REP.decisions_review(F.approvals_template(V21), V21)
    assert "Changes from v1" in page and "`revision.py`" in page
    assert "three variant shares" not in page and "Unchanged wordings" \
        not in page


def test_v2_decision_texts_describe_v2_and_bind_its_code():
    V21.activate()
    ds = {d.decision_id: d for d in CFG.decisions(V21)}
    text = " ".join(d.title + " " + d.summary for d in ds.values())
    for stale in ("Stage 1 + 2", "32 new topics", "Selecting the two B",
                  "Selecting the global A", "boundary cells ranked"):
        assert stale not in text
    assert "every reference in the library" in ds["D06"].summary
    for did in ("D06", "D07", "D08", "D10", "D11", "D14"):
        assert "revision.py" in ds[did].payload["implementation"]
    assert "compatibility.py" in ds["D11"].payload["implementation"]
    with L.using_library_version("v1"):
        v1 = {d.decision_id: d for d in CFG.decisions(CFG.DEFAULT_CONFIG)}
    assert all("revision.py" not in d.payload["implementation"]
               for d in v1.values())
    assert v1["D09"].summary.endswith("(disclosed).") and \
        "Stage 1 + 2" in v1["D09"].summary


def test_reporting_never_decides_and_covers_r5(matrix):
    rates = {k: (0.5 if k[2].startswith("B.") else v)
             for k, v in _rates(1, 0.2).items()}
    t1 = SY.tables_from_rates(rates, n=48)
    t2 = SY.tables_from_rates(rates, n=96)
    cfg = replace(V2, forecast_draws=50)
    result = CAL.finalize(t2, cfg, matrix)
    fc = REV.forecast(t1, cfg, matrix)
    rep = REV.reporting(t2, t1, cfg, matrix, result, fc)
    assert [r["a"] for r in rep["a_diagnostics_t1"]] and \
        {r["n"] for r in rep["a_diagnostics_t1"]} == {4, 5, 6}
    if result.get("configurations"):
        sens = rep["sensitivities"]
        assert sens["primary"]["all_feasible"] == \
            result["feasibility"]["all_feasible"]
        for name in ("tolerance_0.15", "tolerance_0.2", "confident", "iota"):
            assert set(sens[name]) == {"P1", "P2", "P3", "all_feasible"}
        assert sum(rep["agreement"]["eligibility"].values()) == 161
        assert len(rep["posterior_match_t2"]["by_model_frame"]) == 8
    again = CAL.finalize(t2, cfg, matrix)
    assert again["status"] == result["status"]       # reporting changed nothing


def test_an_early_stop_names_every_cause_that_holds(matrix):
    """v2.1 audit MAJOR-2: references that never comply limit the library
    even when the fixed A also fails often; both causes are named, and a
    library limit is judged on the draws where the gates pass."""
    refs = {c.cid for c in L.reference_library()}
    mfs = R.model_frames(V2)
    base = {k: (0.0 if k[2] in refs else 0.5) for k in _rates(1, 0.0)}
    cfg = replace(V2, forecast_draws=400)
    library_only = REV.forecast(SY.tables_from_rates(base, n=48), cfg, matrix)
    assert library_only["stop_reason"] == "library"
    assert library_only["library_limited"] == ["P1", "P2", "P3"]
    both = dict(base)
    for j, (model, frame) in enumerate(mfs):     # A informative in 5 of 8
        both[(model, frame, V2.fixed_a)] = 0.5 if j < 5 else 0.98
    fc = REV.forecast(SY.tables_from_rates(both, n=48), cfg, matrix)
    assert 0 < fc["p_fixed_gates_pass"] < cfg.forecast_min_feasible
    assert fc["stop_reason"] == "library+fixed_gates"
    assert REV.EARLY_STOP_STATUS[fc["stop_reason"]] == \
        "EARLY_STOP_LIBRARY_LIMITED_AND_FIXED_A_OR_B"


def test_v2_1_reports_the_forecast_and_always_runs_stage_c(matrix):
    """The researcher's decision of 2026-10-26: no early stop in v2.1."""
    refs = {c.cid for c in L.reference_library()}
    rates = {k: (0.0 if k[2] in refs else 0.5) for k in _rates(1, 0.0)}
    tables = SY.tables_from_rates(rates, n=48)
    v21 = REV.select_carry(tables, replace(V21, forecast_draws=50))
    assert v21["forecast"]["early_stop"] and not v21["early_stop_enabled"]
    assert v21["status"] == "CARRIED" and len(v21["carried"]) == 161
    v2 = REV.select_carry(tables, replace(V2, forecast_draws=50))
    assert v2["status"] == "EARLY_STOP" and v2["cells"] == []


def test_accounting_reports_undelivered_rows_without_charging_them(tmp_path):
    """Reported, not a gate: a crashed backend's rows are NOT_RETURNED."""
    base = make_root(tmp_path, cfg=SMALL_V2)
    d1 = P.write_stage1_plan(base["root"], base["freeze1"])
    good = SY.synthetic_generate()

    def crash(attempt_dir, plan, design_rows, *args, **kwargs):
        out = good(attempt_dir, plan, design_rows, *args, **kwargs)
        return {**out, "rows": [], "returncode": 3}        # a crash
    from dci.batch1.store import RunError
    try:
        RUN.execute(base["root"], d1[:500], freeze1=base["freeze1"],
                    approvals=base["approvals"], generate=crash)
    except RunError:
        pass                                  # the runner reports the crash
    report = EV.budget_report(base["root"])
    assert report["charged"] == 0 and report["uncharged"]["NOT_RETURNED"] > 0
