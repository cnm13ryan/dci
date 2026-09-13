"""The targeted second pass and the spaced retention."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import LADDERS
from dci1v8dev.prescreen.legacy import legacy_retention
from dci1v8dev.prescreen.rescreen import (
    AMBIGUOUS_AT_MAX,
    RescreenConfig,
    apply_batch,
    max_cost_generations,
    plan_batch,
    run_rescreen,
)
from dci1v8dev.prescreen.retention import RetentionConfig, retain, spaced_subset
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import (
    SCREEN_ACCEPT,
    SCREEN_REJECT,
    SCREEN_RESAMPLE,
    ScreenConfig,
    screen_families,
)

from .conftest import a_grid, ladder, rung

CFG = ScreenConfig(draws=1200)
#: A ladder whose support below A is genuinely uncertain at 24 topics under
#: the candidate offsets (rules.SPECTRUM_OFFSET_BELOW/ABOVE): P(support both)
#: about 0.35 — the middle band the second pass exists for.
BORDER = [0.84, 0.82, 0.79, 0.76, 0.72, 0.66, 0.61, 0.57]


def _truth_measure(rates):
    """A measure() that returns exact-rate counts (no noise) for the batch."""
    def measure(batch):
        out = []
        for kind, fam in batch.families.items():
            for q in list(fam["severities"]) + list(fam["reserve_picks"]):
                p = rates.get(q, 0.45)
                out.append(PrescreenRung(
                    kind=kind, severity=q, solo_k=round(p * batch.n_topics),
                    solo_n=batch.n_topics, chance_k=0.0,
                    chance_n=float(batch.n_topics), n_topics=batch.n_topics,
                    draws_per_topic=1, reserve=q not in LADDERS[kind]))
        a = ([ARung(severity=q, solo_k=round(r * 24), solo_n=24,
                    chance_k=0.0, chance_n=24.0)
              for q, r in zip(C.TARGET_GRID, (0.92, 0.71, 0.58, 0.54, 0.50,
                                              0.46, 0.42, 0.33))]
             if batch.a_grid else [])
        return out, a
    return measure


def test_the_plan_is_deterministic_and_names_only_undecided_families():
    table = ladder("MK1", BORDER) + ladder("MK2", [0.7] * 8)
    screen = screen_families(table, a_grid(), config=CFG)
    cfg = RescreenConfig()
    p1 = plan_batch(screen, batches_used={}, config=cfg, table=table)
    p2 = plan_batch(screen, batches_used={}, config=cfg, table=table)
    assert p1 == p2
    assert "MK2" not in p1.families                      # flat: rejected
    assert p1.families["MK1"]["severities"] == list(LADDERS["MK1"])
    assert p1.cost_generations == p1.n_topics * p1.draws_per_topic * (
        p1.n_rungs + len(C.TARGET_GRID) + 1)
    assert plan_batch(screen, batches_used={"MK1": 3}, config=cfg,
                      table=table) is None


def test_the_loop_stops_at_the_maximum_and_resolves_by_the_registered_rule():
    table = ladder("MK1", BORDER)
    res = run_rescreen(table, a_grid(), screen_config=CFG,
                       config=RescreenConfig(max_batches=2),
                       measure=_truth_measure(dict(zip(LADDERS["MK1"], BORDER))))
    assert res["batches_used"].get("MK1", 0) <= 2
    v = res["screen"]["families"]["MK1"]
    assert v["status"] in (SCREEN_ACCEPT, SCREEN_REJECT)
    if "MK1" in res["resolved_at_max"]:
        assert v["resolved_by"] == AMBIGUOUS_AT_MAX
    assert res["cost_generations"] == sum(h["batch"]["cost_generations"]
                                          for h in res["history"] if h["batch"])
    assert res["screen"]["statuses"][SCREEN_RESAMPLE] == []


def test_a_reserve_rung_enters_only_through_a_batch_and_only_from_the_reserve():
    table = ladder("MK1", [0.99, 0.98, 0.96, 0.93, 0.90, 0.85, 0.79, 0.72])
    new = [rung("MK1", 9, 14, reserve=True)]
    merged, _ = apply_batch(table, a_grid(), new)
    assert any(r.severity == 9 and r.reserve for r in merged)
    with pytest.raises(ProtocolError):
        PrescreenRung(kind="MK1", severity=13, solo_k=1, solo_n=24, chance_k=0.0,
                      chance_n=24.0, reserve=True)          # outside the reserve
    with pytest.raises(ProtocolError, match="cannot appear for the first time"):
        apply_batch(table[:4], a_grid(), [rung("MK1", 8, 10)])


def test_apply_batch_pools_counts_and_the_a_grid():
    table = ladder("MK1", BORDER)
    merged, a2 = apply_batch(table, a_grid(), [rung("MK1", 1, 20)],
                             [ARung(severity=1, solo_k=20, solo_n=24,
                                    chance_k=0.0, chance_n=24.0)])
    r1 = next(r for r in merged if r.severity == 1)
    assert (r1.solo_n, r1.n_topics, r1.draws_per_topic) == (48, 24, 2)
    assert a2[0].solo_n == 48 and a2[0].draws_per_topic == 2


def test_max_cost_is_a_function_of_the_configuration():
    cost = max_cost_generations(RescreenConfig())
    assert cost["max_total"] == cost["max_per_batch"] * 3
    assert cost["max_per_batch"] > 0
    assert max_cost_generations(RescreenConfig(max_batches=1))["max_total"] \
        == cost["max_per_batch"]


def test_spaced_subset_keeps_the_shape_of_the_ladder():
    rows = [{"candidate": f"MK1:{q}", "severity": q, "iota_mean": v,
             "p_admissible": 0.9}
            for q, v in zip(range(1, 9), [0.92, 0.86, 0.80, 0.73, 0.66, 0.58,
                                          0.50, 0.42])]
    sub = spaced_subset(rows, iota_a=0.68, n=5, admissible_min=0.5)
    roles = {s["role"]: s["severity"] for s in sub}
    assert set(roles) == {"HARD_EXTREME", "EASY_EXTREME", "NEAR_A",
                          "INTERMEDIATE_HARD", "INTERMEDIATE_EASY"}
    assert roles["HARD_EXTREME"] == 8 and roles["EASY_EXTREME"] == 1
    assert roles["NEAR_A"] == 5
    three = spaced_subset(rows, iota_a=0.68, n=3, admissible_min=0.5)
    assert {s["role"] for s in three} == {"HARD_EXTREME", "EASY_EXTREME", "NEAR_A"}
    assert spaced_subset([], iota_a=0.68, n=5, admissible_min=0.5) == []


def test_retention_separates_arms_and_the_legacy_rule_keeps_only_nearest_tier3():
    wide = ladder("MK1", [0.95, 0.90, 0.84, 0.76, 0.66, 0.54, 0.42, 0.30])
    local = ladder("MK2", [0.72, 0.70, 0.69, 0.68, 0.67, 0.66, 0.65, 0.64])
    tier3 = [rung("RF1", q, k) for q, k in zip(range(9),
                                              (2, 4, 7, 10, 13, 16, 18, 20, 22))]
    table = wide + local + tier3
    screen = screen_families(table, a_grid(), config=ScreenConfig(
        draws=1200, accept=0.5))
    kept = retain(screen, config=RetentionConfig())
    roles = {e["candidate"]: e["roles"] for e in kept["forwarded"]}
    assert any("HARD_EXTREME" in r for r in roles.values())
    assert any("LOCAL" in r for c, r in roles.items() if c.startswith("MK2"))
    assert kept["n_forwarded"] < len(table)
    leg = legacy_retention(table, iota_a=0.68)
    assert set(leg["tier12"]) == {r.label for r in wide + local}
    # §12.7 keeps at most 24 Tier-3, nearest A; here all 9 fit
    assert len(leg["tier3_measured"]) == 9
    capped = retain(screen, config=RetentionConfig(total_cap=4))
    assert capped["n_forwarded"] == 4 and capped["dropped_for_cap"]


def test_batch_indices_are_a_sequence_and_the_cap_bounds_the_sequence():
    """Pilot r2 (2026-08-30): the index used to be the largest per-family
    batch count, so a family that re-entered after ι_A moved got index 3
    (a fourth batch on fresh topics) and then index 3 again (the same
    topics; refused by the isolation rule). The index is the batch's
    position in the run and the cap of three bounds that sequence."""
    table = ladder("MK1", BORDER) + ladder("MK2", BORDER)
    res = run_rescreen(table, a_grid(), screen_config=CFG,
                       config=RescreenConfig(max_batches=3),
                       measure=_truth_measure(dict(zip(LADDERS["MK1"], BORDER))))
    indices = [h["batch"]["index"] for h in res["history"] if h["batch"]]
    assert indices == list(range(len(indices)))
    assert len(indices) <= 3
    assert res["screen"]["statuses"][SCREEN_RESAMPLE] == []

    screen = screen_families(table, a_grid(), config=CFG)
    for kind in screen["families"].values():
        kind["status"] = SCREEN_RESAMPLE
    cfg = RescreenConfig(max_batches=3)
    # the r2 shape: MK1 has spent its three batches, MK4-like MK2 only one,
    # three batches have been measured --- no fourth batch exists
    assert plan_batch(screen, batches_used={"MK1": 3, "MK2": 1}, config=cfg,
                      table=table, n_batches=3) is None
    # the index is the position, never the per-family maximum
    b = plan_batch(screen, batches_used={"MK1": 1, "MK2": 1}, config=cfg,
                   table=table, n_batches=2)
    assert b is not None and b.index == 2
    b0 = plan_batch(screen, batches_used={"MK1": 2}, config=cfg,
                    table=table, n_batches=0)
    assert b0 is not None and b0.index == 0 and "MK1" in b0.families
