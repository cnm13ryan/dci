"""The retention seam: evidence -> policy -> forwarding plan.

Contracts on synthetic counts:

1.  frame f's plan under ``FrameAwarePolicy`` is a function of frame f's
    evidence and the config alone --- changing another frame's counts
    cannot move it, and two frames with identical evidence get identical
    plans;
2.  the plan is deterministic and invariant to the order of the table;
3.  every forwarded label carries the frames that selected it, a label
    selected for one frame is not forwarded for another, and the plan
    refuses a forwarded label with no provenance;
4.  the legacy policy forwards one set for every frame, from the pooled
    table, and its union is exactly ``retention.retain`` on the pooled
    screen;
5.  a supplied per-frame target (``coordinate_target``) replaces the frame's
    screen-proxy ι_A and is what the frame's retention then measures
    distances from;
6.  the frame-aware second-pass loop unions the frames' own plans, every
    frame absorbs the batch on its own blocks, a frame's batch count moves
    only for families that frame asked for, and the at-max rule resolves per
    frame;
7.  the evidence container refuses per-frame counts that are not a
    partition of the pooled ones.
"""
from __future__ import annotations

import random

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import LADDERS
from dci1v8dev.prescreen.evidence import (FrameEvidence, ScreenEvidence,
                                          evidence_from_counts)
from dci1v8dev.prescreen.policy import (FRAME_AWARE, LEGACY_POOLED,
                                        TARGET_CALIBRATION,
                                        TARGET_SCREEN_PROXY, ForwardingPlan,
                                        FrameAwarePolicy, LegacyPooledPolicy,
                                        policy_named, screens_by_frame)
from dci1v8dev.prescreen.rescreen import (AMBIGUOUS_AT_MAX, RescreenConfig,
                                          run_rescreen_by_frame, union_batch,
                                          plan_batch)
from dci1v8dev.prescreen.retention import RetentionConfig, retain
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import (ScreenConfig, coordinate_target,
                                        screen_families)

from .conftest import a_grid, ladder, rung

CFG = ScreenConfig(draws=800)
RET = RetentionConfig()

WIDE = [0.98, 0.92, 0.86, 0.78, 0.66, 0.52, 0.38, 0.25]
FLAT = [0.70, 0.69, 0.68, 0.67, 0.67, 0.66, 0.65, 0.64]
NARROW = [0.80, 0.77, 0.74, 0.72, 0.70, 0.68, 0.66, 0.64]
EASY = [0.99, 0.97, 0.95, 0.93, 0.91, 0.89, 0.86, 0.83]
A_HARD = (0.85, 0.66, 0.55, 0.52, 0.48, 0.44, 0.40, 0.31)
A_EASY = (0.98, 0.90, 0.80, 0.72, 0.64, 0.58, 0.52, 0.44)


def _frame(f: int, tables, a_rates=None, n: int = 24) -> FrameEvidence:
    table = []
    for kind, rates in tables:
        table += ladder(kind, rates, n=n)
    grid = a_grid(a_rates, n=n) if a_rates else a_grid(n=n)
    return FrameEvidence(frame=f, table=tuple(table), a_grid=tuple(grid),
                         n_topics=n)


def _pooled_of(frames: dict[int, FrameEvidence]) -> FrameEvidence:
    """The frame-summed table, for a consistent ScreenEvidence."""
    by_label: dict[str, PrescreenRung] = {}
    a_by: dict[int, ARung] = {}
    for e in frames.values():
        for r in e.table:
            if r.label in by_label:
                by_label[r.label] = by_label[r.label].merged(r)
            else:
                by_label[r.label] = r
        for a in e.a_grid:
            old = a_by.get(a.severity)
            a_by[a.severity] = a if old is None else ARung(
                severity=a.severity, solo_k=old.solo_k + a.solo_k,
                solo_n=old.solo_n + a.solo_n, chance_k=old.chance_k + a.chance_k,
                chance_n=old.chance_n + a.chance_n,
                n_topics=old.n_topics + a.n_topics,
                draws_per_topic=old.draws_per_topic)
    return FrameEvidence(frame=None, table=tuple(by_label.values()),
                         a_grid=tuple(a_by[q] for q in sorted(a_by)),
                         n_topics=sum(e.n_topics for e in frames.values()))


def _evidence(frames: dict[int, FrameEvidence]) -> ScreenEvidence:
    return ScreenEvidence(by_frame=dict(frames), pooled=_pooled_of(frames))


@pytest.fixture(scope="module")
def world():
    frames = {
        0: _frame(0, [("MK1", WIDE), ("MK2", FLAT), ("MK3", NARROW)], A_HARD),
        1: _frame(1, [("MK1", EASY), ("MK2", FLAT), ("MK3", NARROW)], A_EASY),
        2: _frame(2, [("MK1", WIDE), ("MK2", FLAT), ("MK3", NARROW)], A_HARD),
        3: _frame(3, [("MK1", WIDE), ("MK2", NARROW), ("MK3", FLAT)], A_EASY),
    }
    return _evidence(frames)


# ------------------------------------------------------------ 1. locality
def test_a_frames_plan_depends_on_its_own_evidence_only(world):
    policy = FrameAwarePolicy(screen_config=CFG, retention_config=RET)
    plan = policy.plan(world)
    # frames 0 and 2 carry identical evidence -> identical plans
    assert plan.by_frame["0"] == plan.by_frame["2"]
    # perturb frame 1 only: frames 0, 2, 3 are untouched
    moved = dict(world.by_frame)
    moved[1] = _frame(1, [("MK1", FLAT), ("MK2", WIDE), ("MK3", EASY)], A_HARD)
    plan2 = policy.plan(_evidence(moved))
    for f in ("0", "2", "3"):
        assert plan2.by_frame[f] == plan.by_frame[f]
    assert plan2.by_frame["1"] != plan.by_frame["1"]
    # and the frames genuinely differ: frame 1's ranking is its own
    assert plan.forwarded(0) != plan.forwarded(1)


def test_the_plan_is_deterministic_and_order_invariant(world):
    policy = FrameAwarePolicy(screen_config=CFG, retention_config=RET)
    one = policy.plan(world).as_record()
    two = policy.plan(world).as_record()
    assert one == two
    shuffled = {}
    for f, e in world.by_frame.items():
        table = list(e.table)
        random.Random(f + 11).shuffle(table)
        shuffled[f] = FrameEvidence(frame=f, table=tuple(table), a_grid=e.a_grid,
                                    n_topics=e.n_topics)
    three = policy.plan(_evidence(shuffled)).as_record()
    assert three == one


# ----------------------------------------------------------- 3. provenance
def test_every_forwarded_label_names_the_frames_that_selected_it(world):
    plan = FrameAwarePolicy(screen_config=CFG, retention_config=RET).plan(world)
    assert plan.policy == FRAME_AWARE and plan.target_basis == TARGET_SCREEN_PROXY
    assert plan.union == sorted(plan.selected_by_frames)
    for label, frames in plan.selected_by_frames.items():
        assert frames == sorted(frames)
        for f in plan.frames:
            assert (f in frames) == (label in plan.forwarded(f)), (label, f)
    # a label selected for one frame is NOT forwarded for another
    only_some = [l for l, fr in plan.selected_by_frames.items() if len(fr) < 4]
    assert only_some, "the world should give some frame-specific rungs"
    for label in only_some:
        absent = [f for f in plan.frames if f not in plan.selected_by_frames[label]]
        assert absent and all(label not in plan.forwarded(f) for f in absent)
    cost = plan.cost
    assert cost["total"] == sum(cost["by_frame"].values())
    assert cost["total"] <= cost["union_on_every_frame"]


def test_a_plan_without_provenance_is_refused():
    with pytest.raises(ProtocolError, match="without provenance"):
        ForwardingPlan(policy=FRAME_AWARE, target_basis=TARGET_SCREEN_PROXY,
                       by_frame={"0": {"forwarded": ["MK1:3"], "retention": {
                           "spectrum_families": [], "local_families": []},
                           "screen_statuses": {}, "screen_labels": {},
                           "iota_a_mean": 0.6, "iota_a_sd": 0.05,
                           "n_topics": 6}},
                       union=["MK1:3"], selected_by_frames={"MK1:3": [1]},
                       generations_per_rung_per_frame=768)
    with pytest.raises(ProtocolError, match="not in the union"):
        ForwardingPlan(policy=FRAME_AWARE, target_basis=TARGET_SCREEN_PROXY,
                       by_frame={}, union=[], selected_by_frames={"MK1:3": [0]},
                       generations_per_rung_per_frame=768)
    with pytest.raises(ProtocolError, match="unknown retention policy"):
        policy_named("frame_blind")


# --------------------------------------------------------------- 4. legacy
def test_the_legacy_policy_forwards_one_pooled_set_for_every_frame(world):
    policy = LegacyPooledPolicy(screen_config=CFG, retention_config=RET)
    plan = policy.plan(world)
    assert plan.policy == LEGACY_POOLED
    pooled_screen = screen_families(list(world.pooled.table),
                                    list(world.pooled.a_grid), config=CFG)
    expected = [e["candidate"] for e in retain(pooled_screen, config=RET)["forwarded"]]
    assert plan.union == expected
    for f in (0, 1, 2, 3):
        assert plan.forwarded(f) == expected
    assert all(v == [0, 1, 2, 3] for v in plan.selected_by_frames.values())
    assert plan.provenance["pooled_over_frames"] is True
    # the legacy set is not any frame's own set in this world
    aware = FrameAwarePolicy(screen_config=CFG, retention_config=RET).plan(world)
    assert any(aware.forwarded(f) != expected for f in aware.frames)


# --------------------------------------------------------------- 5. target
def test_a_supplied_target_replaces_the_frames_screen_proxy(world):
    policy = FrameAwarePolicy(screen_config=CFG, retention_config=RET)
    proxy = policy.plan(world)
    targets = {f: coordinate_target(0.35, 0.03, n_star=6, draws=CFG.draws,
                                    seed=CFG.base_seed, basis=f"frame{f}")
               for f in world.frames}
    aimed = policy.plan(world, targets=targets)
    assert aimed.target_basis == TARGET_CALIBRATION
    for f in world.frames:
        assert aimed.by_frame[str(f)]["iota_a_mean"] == pytest.approx(0.35)
        assert aimed.by_frame[str(f)]["iota_a_sd"] == pytest.approx(0.03)
    assert any(aimed.forwarded(f) != proxy.forwarded(f) for f in world.frames)
    # the target's draw count must match the screen's
    with pytest.raises(ProtocolError, match="draws"):
        screen_families(list(world.by_frame[0].table), (),
                        config=CFG,
                        target=coordinate_target(0.5, 0.05, n_star=5, draws=500,
                                                 seed=1, basis="x"))
    with pytest.raises(ProtocolError):
        coordinate_target(0.5, -0.1, n_star=5, draws=800, seed=1, basis="x")
    # screens_by_frame applies a target to the named frame only
    screens = screens_by_frame(world, screen_config=CFG, targets={1: targets[1]})
    assert screens[1]["iota_a"]["external_target"] is True
    assert "external_target" not in screens[0]["iota_a"]


# ------------------------------------------------------ 6. the shared batch
BORDER = [0.84, 0.82, 0.79, 0.76, 0.72, 0.66, 0.61, 0.57]


def _truth_measure(rates_by_frame):
    """``rates_by_frame[f][kind][q]``: each frame's own truth per family."""
    def measure(batch):
        out = {}
        for f, rates in rates_by_frame.items():
            rungs = []
            for kind, fam in batch.families.items():
                for q in list(fam["severities"]) + list(fam["reserve_picks"]):
                    p = rates.get(kind, {}).get(q, 0.45)
                    rungs.append(PrescreenRung(
                        kind=kind, severity=q, solo_k=round(p * batch.n_topics),
                        solo_n=batch.n_topics, chance_k=0.0,
                        chance_n=float(batch.n_topics), n_topics=batch.n_topics,
                        draws_per_topic=1, reserve=q not in LADDERS[kind]))
            grid = ([ARung(severity=q, solo_k=round(r * batch.n_topics),
                           solo_n=batch.n_topics, chance_k=0.0,
                           chance_n=float(batch.n_topics), n_topics=batch.n_topics)
                     for q, r in zip(C.TARGET_GRID, A_HARD)] if batch.a_grid else [])
            out[f] = (rungs, grid)
        return out
    return measure


def test_the_frame_aware_second_pass_unions_the_frames_plans_and_resolves_per_frame():
    cfg = ScreenConfig(draws=600)
    # frame 0: MK1 borderline (undecided), MK2 flat (rejected);
    # frame 1: MK1 flat (rejected), MK2 borderline (undecided)
    tables = {0: (ladder("MK1", BORDER) + ladder("MK2", FLAT), a_grid()),
              1: (ladder("MK1", FLAT) + ladder("MK2", BORDER), a_grid())}
    screens = {f: screen_families(t, a, config=cfg) for f, (t, a) in tables.items()}
    plans = {f: plan_batch(screens[f], batches_used={}, config=RescreenConfig(),
                           table=tables[f][0]) for f in tables}
    assert plans[0] is not None and "MK1" in plans[0].families
    assert "MK2" not in plans[0].families
    assert plans[1] is not None and "MK2" in plans[1].families
    batch = union_batch(plans, index=0, config=RescreenConfig())
    assert sorted(batch.families) == ["MK1", "MK2"]
    assert batch.families["MK1"]["requested_by_frames"] == [0]
    assert batch.families["MK2"]["requested_by_frames"] == [1]
    assert set(batch.by_frame) == {"0", "1"}
    assert union_batch({0: None, 1: None}, index=0, config=RescreenConfig()) is None

    rates = {0: {"MK1": dict(zip(LADDERS["MK1"], BORDER)),
                 "MK2": dict(zip(LADDERS["MK2"], FLAT))},
             1: {"MK1": dict(zip(LADDERS["MK1"], FLAT)),
                 "MK2": dict(zip(LADDERS["MK2"], BORDER))}}
    res = run_rescreen_by_frame(tables, screen_config=cfg,
                                config=RescreenConfig(max_batches=2),
                                measure=_truth_measure(rates))
    assert res["n_batches"] <= 2
    # a frame's batch count moves only for the families it asked for: the
    # count equals the number of batches on which that frame requested the
    # family, whatever the union measured
    for f in (0, 1):
        requested: dict[str, int] = {}
        for h in res["history"]:
            if h["batch"] is None:
                continue
            for kind, frames in h["batch"]["requested_by_frames"].items():
                if f in frames:
                    requested[kind] = requested.get(kind, 0) + 1
        assert res["batches_used"][str(f)] == requested
    first = res["history"][1]["batch"]["requested_by_frames"]
    assert first["MK1"] == [0] and first["MK2"] == [1]
    # every frame absorbed the batch on its own blocks: both families grew
    for f in (0, 1):
        table, _ = res["tables"][f]
        assert all(r.n_topics > 24 for r in table if not r.reserve)
        assert res["screens"][f]["statuses"]["SCREEN_RESAMPLE"] == []
        for kind, verdict in res["resolved_at_max"][str(f)].items():
            assert res["screens"][f]["families"][kind]["resolved_by"] == AMBIGUOUS_AT_MAX
            assert verdict in ("SCREEN_ACCEPT", "SCREEN_REJECT")
    assert res["config"]["frame_aware"] is True
    assert res["history"][0]["batch"] is None
    assert set(res["history"][0]["statuses"]) == {"0", "1"}


# -------------------------------------------------------------- 7. evidence
def test_per_frame_counts_must_partition_the_pooled_counts():
    frames = {0: _frame(0, [("MK1", WIDE)], n=6), 1: _frame(1, [("MK1", WIDE)], n=6)}
    ok = _evidence(frames)
    assert ok.assert_consistent()["rungs_checked"] == len(LADDERS["MK1"])
    bad_pooled = FrameEvidence(frame=None, table=tuple(ladder("MK1", WIDE, n=24)),
                               a_grid=tuple(a_grid()), n_topics=24)
    with pytest.raises(ProtocolError, match="do not add up"):
        ScreenEvidence(by_frame=frames, pooled=bad_pooled).assert_consistent()
    with pytest.raises(ProtocolError, match="carries frame"):
        ScreenEvidence(by_frame={0: frames[1]}, pooled=_pooled_of(frames))
    counts = [{"kind": "MK1", "severity": 1, "solo_k": 4, "solo_n": 6,
               "chance_k": 0.0, "chance_n": 6.0, "vacuous_k": 0, "n_topics": 6,
               "draws_per_topic": 1, "reserve": False},
              {"kind": "A", "severity": 5, "solo_k": 4, "solo_n": 6,
               "chance_k": 0.0, "chance_n": 6.0, "n_topics": 6,
               "draws_per_topic": 1}]
    ev = evidence_from_counts(counts, {"2": counts})
    assert ev.frames == [2] and ev.by_frame[2].n_topics == 6
    assert ev.by_frame[2].labels == ["MK1:1"]
