"""Characterization of the legacy (frame-pooled) pre-screen, pinned against
the signed pilot records of r12 (gemma-3n-e2b-it) and r9 (qwen3-4b).

Golden-master tests in the Feathers sense: they describe what the code
does *today* on frozen historical screen counts, awkward behaviour
included, and they fail if any of it moves. The fixtures under
``fixtures/legacy_prescreen/`` were extracted from the evidence roots by
``tools/v8_prescreen_fixture.py`` (read-only; loads 0 and 1 only) and carry
the record hashes they came from.

What is pinned:

* the pooled screen --- statuses, labels, both rankings, ι_A's posterior
  summary, every family's score and local rungs --- reproduces the signed
  ``REGIME_SCREEN`` record from its recorded counts and seed;
* the second pass, replayed from the recorded batch counts through the
  production loop, plans exactly the recorded batches, spends the recorded
  budget, resolves the recorded families at the maximum, and its retention
  forwards exactly the recorded set with the recorded roles and reasons;
* the pooled target: one ι_A for all four frames, while Gate 2's own
  ι_A(f) differs across frames by more than the caliper --- the
  inconsistency the successor removes, stated as a fact about the record;
* the per-frame counts partition the pooled counts rung by rung, and the
  per-frame screen statistics Gate 1 already recorded were formed on six
  topics per frame;
* the generation and calibration accounting.

The legacy path is reached through ``policy.LegacyPooledPolicy`` as well
as through the raw functions, so the seam is shown to be behaviour-
preserving on real evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v7.protocol import constants as C
from dci1v8dev import rules as R
from dci1v8dev.prescreen.evidence import evidence_from_counts
from dci1v8dev.prescreen.policy import (LEGACY_POOLED, LegacyPooledPolicy,
                                        TARGET_SCREEN_PROXY)
from dci1v8dev.prescreen.rescreen import (RescreenConfig,
                                          max_cost_generations, run_rescreen)
from dci1v8dev.prescreen.retention import RetentionConfig, retain
from dci1v8dev.prescreen.screen import ScreenConfig, screen_families
from dci1v8dev.run.regime import jsonable, prescreen_input

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "legacy_prescreen"
CASES = ("gemma-3n-e2b-it.r12", "qwen3-4b.r9")


def _expand(table):
    cols = table["columns"]
    return [dict(zip(cols, row)) for row in table["rows"]]


@pytest.fixture(scope="module", params=CASES)
def case(request):
    path = FIXTURES / f"{request.param}.json"
    fixture = json.loads(path.read_text())
    fixture["_name"] = request.param
    return fixture


def _screen_config(cfg: dict) -> ScreenConfig:
    return ScreenConfig(draws=cfg["draws"], base_seed=cfg["base_seed"],
                        icc=cfg["icc"], accept=cfg["accept"],
                        reject=cfg["reject"], local_accept=cfg["local_accept"],
                        spectrum_event=cfg["spectrum_event"],
                        chance_max=cfg["chance_max"], lift_min=cfg["lift_min"],
                        shrinkage=cfg["shrinkage"])


def _family_view(screen: dict) -> dict:
    return {k: {"status": v["status"], "labels": list(v["labels"]),
                "p_spectrum": v["p_spectrum"], "score_local": v["score_local"],
                "local_rungs": list(v["local_rungs"]),
                "deficiency": v.get("deficiency"),
                "resolved_by": v.get("resolved_by"),
                "rungs": [[r["candidate"], r["p_admissible"], r["p_local"],
                           r["iota_mean"]] for r in v["rungs"]]}
            for k, v in sorted(screen["families"].items())}


def _expected_family_view(expected: dict) -> dict:
    return {k: {**{kk: vv for kk, vv in v.items() if kk != "rungs"},
                "rungs": [list(r) for r in v["rungs"]["rows"]]}
            for k, v in expected.items()}


# --------------------------------------------------------- the first pass
def test_the_pooled_screen_reproduces_the_signed_regime_record(case):
    table, a_grid = prescreen_input(_expand(case["prescreen_table"]))
    screen = jsonable(screen_families(table, a_grid,
                                      config=_screen_config(case["screen_config"])))
    exp = case["expected"]["regime"]
    assert screen["statuses"] == exp["statuses"]
    assert screen["labels"] == exp["labels"]
    assert screen["ranking_spectrum"] == exp["ranking_spectrum"]
    assert screen["ranking_local"] == exp["ranking_local"]
    assert screen["iota_a"] == exp["iota_a"]
    assert screen["iota_a_prescreen_point"] == exp["iota_a_prescreen_point"]
    assert screen["summary"] == exp["summary"]
    assert _family_view(screen) == _expected_family_view(exp["families"])


def test_the_ranking_is_score_order_with_the_family_id_as_the_tie_break(case):
    exp = case["expected"]["regime"]
    fam = exp["families"]
    assert exp["ranking_spectrum"] == sorted(
        fam, key=lambda k: (-fam[k]["p_spectrum"], k))
    assert exp["ranking_local"] == sorted(
        fam, key=lambda k: (-fam[k]["score_local"], k))
    # a label is separate from a status: SPECTRUM needs ACCEPT, LOCAL needs
    # a rung with P(local) >= LOCAL_LABEL_MIN
    for k, v in fam.items():
        assert ("SPECTRUM_REFERENCE_CANDIDATE" in v["labels"]) == (
            v["status"] == "SCREEN_ACCEPT")
        assert ("LOCAL_REFERENCE_CANDIDATE" in v["labels"]) == bool(v["local_rungs"])
        assert v["local_rungs"] == [r[0] for r in v["rungs"]["rows"]
                                    if r[2] >= R.LOCAL_LABEL_MIN]


# ---------------------------------------------------- the second pass loop
def _replay(case):
    table, a_grid = prescreen_input(_expand(case["prescreen_table"]))
    batches = {int(k): v for k, v in case["batches"].items()}
    seen: list[int] = []

    def measure(batch):
        rec = batches[batch.index]
        planned = sorted({f"{k}:{q}" for k, fam in batch.families.items()
                          for q in list(fam["severities"]) + list(fam["reserve_picks"])}
                         | ({f"A:{q}" for q in C.TARGET_GRID} if batch.a_grid
                            else set()))
        assert planned == sorted(rec["rungs"]), (batch.index, planned, rec["rungs"])
        assert sorted(batch.families) == sorted(rec["families"])
        assert batch.n_topics == rec["n_topics"]
        seen.append(batch.index)
        return prescreen_input(_expand(rec["counts"]))

    rc = case["rescreen_config"]
    result = run_rescreen(
        table, a_grid,
        screen_config=_screen_config(case["second_pass_screen_config"]),
        config=RescreenConfig(max_batches=rc["max_batches"], layout=rc["layout"],
                              batch_topics=rc["batch_topics"],
                              batch_draws=rc["batch_draws"],
                              reserve_picks_per_batch=rc["reserve_picks_per_batch"],
                              include_a_grid=rc["include_a_grid"],
                              final_accept_at=rc["final_accept_at"]),
        measure=measure)
    assert seen == sorted(batches)
    return result


@pytest.fixture(scope="module")
def replayed(case):
    return case, _replay(case)


def test_the_second_pass_plans_exactly_the_recorded_batches(replayed):
    case, result = replayed
    exp = case["expected"]["second_pass"]
    assert result["batches_used"] == exp["batches_used"]
    assert result["resolved_at_max"] == exp["resolved_at_max"]
    assert result["cost_generations"] == exp["cost_generations"]
    history = jsonable(result["history"])
    assert [h["batch"] for h in history] == [h["batch"] for h in exp["history"]]
    assert [h["statuses"] for h in history] == [h["statuses"] for h in exp["history"]]
    for got, want in zip(history, exp["history"]):
        assert {k: round(v, 6) for k, v in got["p_spectrum"].items()} == want["p_spectrum"]
    screen = jsonable(result["screen"])
    assert screen["statuses"] == exp["statuses"]
    assert screen["labels"] == exp["labels"]
    assert screen["iota_a"] == exp["iota_a"]
    assert _family_view(screen) == _expected_family_view(exp["families"])


def test_the_retention_forwards_exactly_the_recorded_set(replayed):
    case, result = replayed
    exp = case["expected"]["second_pass"]
    rcfg = case["retention_config"]
    config = RetentionConfig(**rcfg)
    retention = jsonable(retain(result["screen"], config=config))
    assert [e["candidate"] for e in retention["forwarded"]] == exp["forwarded_set"]
    assert retention == exp["retention"]
    assert retention["n_forwarded"] == exp["n_forwarded"]
    assert retention["calibration_cost_generations"] == \
        exp["calibration_cost_generations"]
    assert exp["calibration_cost_generations"] == \
        exp["n_forwarded"] * rcfg["generations_per_rung"]
    # the seam reproduces the raw path: the legacy policy on the same screen
    policy = LegacyPooledPolicy(retention_config=config)
    plan = policy.plan_from_screen(result["screen"], n_topics=C.N_PRESCREEN)
    assert plan.policy == LEGACY_POOLED
    assert plan.target_basis == TARGET_SCREEN_PROXY
    assert plan.union == exp["forwarded_set"]
    assert plan.frames == [0, 1, 2, 3]
    for f in plan.frames:
        assert plan.forwarded(f) == exp["forwarded_set"]
        assert jsonable(plan.by_frame[str(f)]["retention"]) == exp["retention"]
    assert all(v == [0, 1, 2, 3] for v in plan.selected_by_frames.values())


# --------------------------------------------------- the pooled target
def test_one_pooled_iota_a_targets_every_frame_while_gate2_disagrees(replayed):
    """The awkward behaviour, stated: retention measured every rung's
    distance from ONE ι_A (the pooled posterior mean), and forwarded one
    set for all four frames, although Gate 2 then fixed a different ι_A(f)
    on every frame --- spread across frames beyond the 0.10 caliper on
    both stored models."""
    case, result = replayed
    exp = case["expected"]["second_pass"]
    pooled_target = result["screen"]["iota_a"]["iota_a_mean"]
    assert pooled_target == exp["iota_a"]["iota_a_mean"]
    # every forwarded rung's recorded coordinate is the pooled posterior mean
    fam = result["screen"]["families"]
    for e in exp["retention"]["forwarded"]:
        rung = next(r for r in fam[e["family"]]["rungs"]
                    if r["candidate"] == e["candidate"])
        assert e["iota_mean"] == rung["iota_mean"]
    # the retention config names no frame anywhere
    assert "frame" not in json.dumps(case["retention_config"])
    # Gate 2's own coordinate differs across the supported frames: by 0.207
    # on r12 (twice the caliper) and by 0.089 on r9 (nine tenths of it)
    g2 = {int(f): v["iota_a"] for f, v in case["gate2_by_frame"].items()
          if v["status"] == "SUPPORTED"}
    assert len(g2) >= 2
    spread = max(g2.values()) - min(g2.values())
    assert spread > C.REFERENCE_CALIPER / 2
    assert spread == pytest.approx(
        {"gemma-3n-e2b-it.r12": 0.2068, "qwen3-4b.r9": 0.0885}[case["_name"]],
        abs=0.001)
    # and the calibrated set Gate 2 measured is the pooled forwarded set
    assert sorted(case["gate2_calibration_population"]["forwarded"]) == \
        sorted(exp["forwarded_set"])
    assert case["gate2_calibration_population"]["measured_under_every_frame"] is True


# ----------------------------------------- what per-frame evidence exists
def test_the_per_frame_counts_partition_the_pooled_counts_on_six_topics(case):
    pooled = _expand(case["prescreen_table"])
    by_frame = {f: _expand(t) for f, t in case["prescreen_table_by_frame"].items()}
    evidence = evidence_from_counts(pooled, by_frame)
    check = evidence.assert_consistent()
    assert check["frames"] == [0, 1, 2, 3]
    assert check["rungs_checked"] == len(evidence.pooled.table)
    for f in evidence.frames:
        e = evidence.by_frame[f]
        assert e.n_topics == C.N_PRESCREEN // C.N_WORDINGS == 6
        assert case["screen_rows_by_frame"][str(f)]["n_topics"] == 6
        assert len(e.a_grid) == len(C.TARGET_GRID)
        assert all(r.draws_per_topic == 1 for r in e.table)
    assert evidence.pooled.n_topics == C.N_PRESCREEN
    # the Gate-1 per-frame screen coordinate the pilot recorded and no stage
    # read: six topics per frame, one draw, for every rung with a coordinate
    g1 = case["gate1_frame_comparison_screen"]
    cols = g1["columns"]
    n_topics_at = cols.index("n_topics")
    counted = 0
    for label, frames in g1["by_label"].items():
        for f, values in frames.items():
            assert values[n_topics_at] == 6, (label, f)
            counted += 1
    assert counted >= 4 * 300


def test_the_generation_accounting_is_the_recorded_one(case):
    exp = case["expected"]["second_pass"]
    rc = case["rescreen_config"]
    ceiling = max_cost_generations(RescreenConfig(
        max_batches=rc["max_batches"], batch_topics=rc["batch_topics"],
        reserve_picks_per_batch=rc["reserve_picks_per_batch"]))
    assert exp["cost_generations"] <= ceiling["max_total"]
    assert len(case["batches"]) <= rc["max_batches"]
    for b in case["batches"].values():
        assert b["n_topics"] == rc["batch_topics"] == C.N_PRESCREEN
        # each batch measured the same rungs under every frame, six topics each
        for f, table in b["counts_by_frame"].items():
            rows = _expand(table)
            assert {r["n_topics"] for r in rows} == {6}
            assert sorted(f"{r['kind']}:{r['severity']}" for r in rows) == \
                sorted(b["rungs"])
    # the per-rung calibration cost the record priced retention at is the
    # all-frames cost of the universal four-pass allocation
    assert case["retention_config"]["generations_per_rung"] == \
        R.calibration_generations_per_rung(case["model_key"]) == 3072
