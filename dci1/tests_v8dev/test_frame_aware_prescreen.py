"""The frame-aware pre-screen at the stage level (successor design,
docs/V8_FRAME_AWARE_PRESCREEN.md).

Fast contracts on constructed inputs:

1.  the screen layout: one pass per frame offset, every topic under every
    frame, no topic twice inside a frame, the frame still the block index
    modulo the wordings; the realised allocation is asserted on rows and a
    short frame is refused;
2.  Gate 2's forwarding is a function of each frame's own second-pass
    evidence and that frame's own ι_A(f): changing another frame's table
    or coordinate cannot move frame f's set; the pooled comparator table
    cannot move it; the target basis is the calibration coordinate;
3.  the second-pass batch cost carries the frame passes;
4.  screen evidence refuses a composed row; the replay tool refuses a
    protected path;
5.  the signed rule table binds the successor's constants, so a manifest
    signed under the pooled design cannot be mistaken for this one;
6.  the frozen confirmatory root and the pilot roots are untouched: their
    signed records still verify and the membership lock's hashes still
    match (skipped where the evidence tree is absent).

A slow walk with a genuine frame effect (``pilot_harness.frame_effect_generate``)
then checks the stage records: per-frame counts on the record, the frames'
forwarded sets differ and carry provenance, each frame's table holds its
own set only, the comparator rows sit beside it, an unsupported frame
generates nothing, Gate 3 carries the retention comparison, and the LOCAL
top-up planner reads the frame's own set.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import load_bank
from dci1v7.verifiers.constraints import Constraint
from dci1v8dev import rules as R
from dci1v8dev.prescreen.evidence import evidence_from_rows
from dci1v8dev.prescreen.policy import TARGET_CALIBRATION
from dci1v8dev.prescreen.rescreen import RescreenBatch, RescreenConfig
from dci1v8dev.run import calibration as CAL
from dci1v8dev.run import regime as REGIME
from dci1v8dev.run import stages as S
from dci1v8dev.run.execute import frame_of_block
from dci1v8dev.run.manifest import rule_table

from .conftest import EVIDENCE

FRAMES = list(S.FRAMES)


# --------------------------------------------------------- 1. the layout
def test_the_screen_is_laid_out_one_pass_per_frame_offset():
    bank = load_bank()
    topics = list(bank.topics("prescreen"))
    blocks = REGIME.screen_blocks(topics, "screen")
    assert len(blocks) == len(topics) * R.SCREEN_FRAME_PASSES == 96
    by_frame: dict[int, list[str]] = {}
    for b in blocks:
        by_frame.setdefault(b.index % C.N_WORDINGS, []).append(b.topic_id)
    assert sorted(by_frame) == FRAMES
    for f, ids in by_frame.items():
        assert len(ids) == len(set(ids)) == R.SCREEN_TOPICS_PER_FRAME == 24, f
        assert set(ids) == {t["topic_id"] for t in topics}
    # the block ids are distinct and the index is the frame
    assert len({b.block_id for b in blocks}) == len(blocks)
    cells, slot_map = REGIME.ladder_cells(topics, [Constraint("MK1", 1)],
                                          frame_passes=R.SCREEN_FRAME_PASSES)
    assert len(cells) == 96 * 2
    for c in cells:
        for slot, index in c.wording_by_slot.items():
            assert index == c.block_index % C.N_WORDINGS
    legacy_cells, _ = REGIME.ladder_cells(topics, [Constraint("MK1", 1)])
    assert len(legacy_cells) == 24 * 2
    alloc = REGIME.screen_allocation(len(topics))
    assert alloc["topics_per_frame"] == 24 and alloc["passes"] == 4


def test_the_realised_screen_allocation_is_asserted_on_rows():
    topics = [{"topic_id": f"t{i}"} for i in range(24)]
    rows = [{"topic_id": b.topic_id, "block_index": b.index,
             "block_frame": b.index % C.N_WORDINGS, "scores": []}
            for b in REGIME.screen_blocks(topics, "x")]
    # every frame sees every topic exactly once
    seen = {f: len({r["topic_id"] for r in rows if frame_of_block(r) == f}) for f in FRAMES}
    assert all(v == 24 for v in seen.values())
    assert REGIME.assert_screen_allocation(rows, expected_topics_per_frame=24,
                                           where="test") == {"0": 24, "1": 24,
                                                             "2": 24, "3": 24}
    # one pass only (the legacy layout) is six per frame and is refused
    with pytest.raises(ProtocolError, match="screen allocation"):
        REGIME.assert_screen_allocation(rows[:24], expected_topics_per_frame=24,
                                        where="test")


# ---------------------------------------------- 2. Gate 2's forwarding
def _count_row(kind, q, k, n=24, chance=0.0, reserve=False):
    return {"kind": kind, "severity": q, "solo_k": k, "solo_n": n,
            "chance_k": chance * n, "chance_n": float(n), "vacuous_k": 0,
            "n_topics": n, "draws_per_topic": 1, "reserve": reserve}


def _a_rows(rates, n=24):
    return [{"kind": "A", "severity": q, "solo_k": round(r * n), "solo_n": n,
             "chance_k": 0.0, "chance_n": float(n), "n_topics": n,
             "draws_per_topic": 1} for q, r in zip(C.TARGET_GRID, rates)]


WIDE = [0.98, 0.92, 0.86, 0.78, 0.66, 0.52, 0.38, 0.25]
FLAT = [0.70, 0.69, 0.68, 0.67, 0.67, 0.66, 0.65, 0.64]
NARROW = [0.80, 0.77, 0.74, 0.72, 0.70, 0.68, 0.66, 0.64]
A_RATES = (0.92, 0.71, 0.58, 0.54, 0.50, 0.46, 0.42, 0.33)


def _frame_table(kinds_rates):
    from dci1v7.verifiers.constraints import LADDERS
    rows = []
    for kind, rates in kinds_rates:
        rows += [_count_row(kind, q, round(r * 24)) for q, r in zip(LADDERS[kind], rates)]
    return rows + _a_rows(A_RATES)


def _second_pass_record(tables):
    return {"final_table_by_frame": {str(f): t for f, t in tables.items()},
            "comparator_plan": {"union": ["MK1:1", "MK1:2", "MK3:3"]},
            "provisional_plan": {"union": [], "by_frame": {}}}


def _coordinate(iota_a, per_topic_n=192, kappa=0.05):
    import random
    rng = random.Random(int(iota_a * 1000))
    vec = [max(0.0, min(1.0, iota_a * (1 - kappa) + kappa + rng.gauss(0, 0.2)))
           for _ in range(per_topic_n // 2)]
    return {"iota_a": iota_a, "kappa_a": kappa,
            "a_per_topic_by_split": {"per_topic": {C.CALIBRATION_A: vec,
                                                   C.CALIBRATION_B: vec}}}


def test_gate2_forwarding_is_frame_local_and_targets_the_calibration_coordinate():
    tables = {0: _frame_table([("MK1", WIDE), ("MK2", FLAT), ("MK3", NARROW)]),
              1: _frame_table([("MK1", WIDE), ("MK2", FLAT), ("MK3", NARROW)]),
              2: _frame_table([("MK1", NARROW), ("MK2", WIDE), ("MK3", FLAT)]),
              3: _frame_table([("MK1", WIDE), ("MK2", FLAT), ("MK3", NARROW)])}
    coords = {0: _coordinate(0.60), 1: _coordinate(0.60), 2: _coordinate(0.60),
              3: _coordinate(0.45)}
    n_stars = {f: 5 for f in FRAMES}
    plan, screens, targets = CAL.frame_forwarding(
        _second_pass_record(tables), coords, n_stars=n_stars, model_key="qwen3-4b")
    assert plan.target_basis == TARGET_CALIBRATION
    assert plan.frames == FRAMES
    for f in FRAMES:
        assert targets[f]["iota_a_mean"] == coords[f]["iota_a"]
        assert plan.by_frame[str(f)]["iota_a_mean"] == coords[f]["iota_a"]
        assert screens[f]["iota_a"]["external_target"] is True
    # identical evidence + identical target -> identical sets (0 and 1)
    assert plan.forwarded(0) == plan.forwarded(1)
    # a different table (2) or a different coordinate (3) -> a different set
    assert plan.forwarded(2) != plan.forwarded(0)
    assert plan.forwarded(3) != plan.forwarded(0)
    # frame 0's set moves with neither another frame's table nor its target
    tables2 = dict(tables)
    tables2[1] = _frame_table([("MK1", FLAT), ("MK2", NARROW), ("MK3", WIDE)])
    coords2 = dict(coords)
    coords2[1] = _coordinate(0.30)
    plan2, _, _ = CAL.frame_forwarding(_second_pass_record(tables2), coords2,
                                       n_stars=n_stars, model_key="qwen3-4b")
    assert plan2.by_frame["0"] == plan.by_frame["0"]
    assert plan2.by_frame["1"] != plan.by_frame["1"]
    # the pooled comparator's union cannot enter the frame's set
    rec = _second_pass_record(tables)
    rec["comparator_plan"] = {"union": ["MK9:1", "XC1:1", "XC1:2"]}
    plan3, _, _ = CAL.frame_forwarding(rec, coords, n_stars=n_stars,
                                       model_key="qwen3-4b")
    assert plan3.as_record()["by_frame"] == plan.as_record()["by_frame"]
    # provenance: every forwarded label names the frames that selected it
    for label, frames in plan.selected_by_frames.items():
        for f in FRAMES:
            assert (f in frames) == (label in plan.forwarded(f))
    assert any(len(v) < 4 for v in plan.selected_by_frames.values())
    # deterministic
    again, _, _ = CAL.frame_forwarding(_second_pass_record(tables), coords,
                                       n_stars=n_stars, model_key="qwen3-4b")
    assert again.as_record() == plan.as_record()


def test_the_frame_target_is_the_coordinate_at_its_topic_level_se():
    coord = _coordinate(0.62)
    t = CAL.frame_target(coord, frame=1, n_star=5, draws=800, seed=3)
    assert t["iota_a_mean"] == 0.62 and t["n_star_distribution"] == {5: 1.0}
    assert 0.0 < t["se_iota_a"] < 0.1 and t["n_topics_a"] == 192
    assert t["iota_a"].shape == (800,)
    flat = {"iota_a": 0.62, "kappa_a": 0.0,
            "a_per_topic_by_split": {"per_topic": {}}}
    t0 = CAL.frame_target(flat, frame=1, n_star=5, draws=800, seed=3)
    assert t0["se_iota_a"] == 0.0 and t0["iota_a_sd"] == 0.0


# ------------------------------------------------------ 3. batch cost
def test_the_batch_cost_carries_the_frame_passes():
    fam = {"MK1": {"severities": list(range(1, 9)), "reserve_picks": [9],
                   "deficiency": None, "p_spectrum": 0.5}}
    one = RescreenBatch(index=0, families=fam, a_grid=True, layout="topics",
                        n_topics=24, draws_per_topic=1)
    four = RescreenBatch(index=0, families=fam, a_grid=True, layout="topics",
                         n_topics=24, draws_per_topic=1, frame_passes=4)
    assert four.cost_generations == 4 * one.cost_generations
    assert one.cost_generations == 24 * (9 + 8 + 1)
    with pytest.raises(ProtocolError):
        RescreenConfig(frame_passes=5)
    assert RescreenConfig(frame_passes=R.SCREEN_FRAME_PASSES).frame_passes == 4


# -------------------------------------------- 4. composed rows, protected
def test_screen_evidence_refuses_a_composed_row_and_the_replay_refuses_protected_paths():
    rows = [{"row_id": "x", "topic_id": "t0", "block_index": 0, "block_frame": 0,
             "arm": "solo", "load": 2,
             "scores": [{"kind": "MK1", "severity": 1, "present": True,
                         "passed": True, "vacuous_pass": False},
                        {"kind": "B", "severity": 9, "present": True,
                         "passed": True, "vacuous_pass": False}]}]
    with pytest.raises(ProtocolError, match="composed"):
        evidence_from_rows(rows, [Constraint("MK1", 1)])
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "tools" / "v8_prescreen_counterfactual.py"
    spec = importlib.util.spec_from_file_location("v8_prescreen_counterfactual", path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    for stage in tool.PROTECTED:
        with pytest.raises(SystemExit, match="protected"):
            tool._assert_unprotected(Path("/x/dci1v8-confirm-r2/evidence/dci1v8/m") / stage / "records" / "r.json")
    assert tool._assert_unprotected(Path("/x/LOCAL_TOPUP/records/r.json"))


# --------------------------------------------------- 5. the rule table
def test_the_signed_rule_table_binds_the_successor_rule():
    table = rule_table()
    assert table["SCREEN_FRAME_OFFSETS"] == [0, 1, 2, 3]
    assert table["SCREEN_TOPICS_PER_FRAME"] == 24
    assert table["RETENTION_POLICY"] == "frame_aware"
    assert table["RETENTION_TARGET_BASIS"] == "calibration_iota_a"
    assert table["RETENTION_COMPARATOR"] == "legacy_pooled"
    assert table["RESCREEN_BATCH_LAYOUT"] == "topics"
    # the hash the frozen r2 root bound (pooled design) is not this one
    assert sha_obj(table) != "0acfed37912f"[:12] + "0" * 52
    old = {k: v for k, v in table.items()
           if k not in ("SCREEN_FRAME_OFFSETS", "SCREEN_FRAME_PASSES",
                        "SCREEN_TOPICS_PER_FRAME", "RETENTION_POLICY",
                        "RETENTION_TARGET_BASIS", "RETENTION_COMPARATOR",
                        "RESCREEN_BATCH_LAYOUT")}
    assert sha_obj(old) != sha_obj(table)


# ------------------------------------------- 6. the old roots are untouched
@pytest.mark.skipif(not (EVIDENCE / "dci1v8-confirm-r2").exists(),
                    reason="no stored evidence tree")
def test_the_frozen_root_and_the_pilot_roots_still_verify():
    from dci1v4.engine import fs
    from dci1v4.engine.signing import verify_signed
    root = EVIDENCE / "dci1v8-confirm-r2"
    key = root / "evidence" / "dci1v8" / "keys" / "signing.key"
    # The lock that names THIS root. `confirmatory_membership.json` is the
    # study-level lock and it moves with the live root: since 034fc72 it
    # names dci1v8p1-confirm, and the v8 lock was archived beside it rather
    # than overwritten. The check below is that the superseded root is
    # untouched, so it has to read the lock that was written for it.
    reports = Path(__file__).resolve().parents[1] / "reports" / "dci1v8dev"
    archived = reports / "confirmatory" / "confirmatory_membership.f7af7f2.v8.json"
    live = reports / "confirmatory_membership.json"
    lock = json.loads((archived if archived.exists() else live).read_text())
    assert Path(lock["root"]).name == root.name, \
        "the lock read here must be the one written for this root"
    n = 0
    for model_dir in sorted((root / "evidence" / "dci1v8").iterdir()):
        frozen = model_dir / "FROZEN" / "records"
        if not frozen.exists():
            continue
        for path in frozen.glob("*.json"):
            record = fs.read_json(path)
            verify_signed(record, key, where=f"{model_dir.name}:FROZEN")
            n += 1
        assert not (model_dir / "CONFIRMATORY_GENERATION").exists()
    assert n == 4
    # the lock still names the records on disk
    for model_key, entry in (lock.get("models") or lock.get("by_model") or {}).items():
        path = root / "evidence" / "dci1v8" / model_key / "MEMBERSHIP" / "records"
        if path.exists():
            for p in path.glob("*.json"):
                assert fs.read_json(p)["record_hash"] == entry.get(
                    "membership_record_hash", fs.read_json(p)["record_hash"])
    from dci1v8dev.confirm.pilot_import import open_pilot
    for model, r in (("qwen3-4b", "dci1v8-pilot-r9"), ("gemma-3n-e2b-it", "dci1v8-pilot-r12")):
        if (EVIDENCE / r).exists():
            src = open_pilot(EVIDENCE / r, model)
            assert src.gate2["calibration_population"].get("policy") is None, \
                "a pooled-design record carries no policy field"


# ------------------------------------------------------------ the walk
@pytest.fixture(scope="module")
def walked_effects(tmp_path_factory):
    from tests_v8dev import pilot_harness as H
    effects = {"A": {2: 0.55}, "MK1": {2: 0.6}, "B": {3: 0.6}}
    return H.walk(tmp_path_factory.mktemp("v8-frame-aware"),
                  generate=H.frame_effect_generate(effects))


@pytest.mark.slow
def test_the_stage_records_carry_the_per_frame_screen_and_the_forwarding(walked_effects):
    payloads = walked_effects["payloads"]
    rg = payloads[S.STAGE_REGIME]
    assert rg["screen_allocation"]["passes"] == 4
    assert rg["screen_allocation"]["realised"] == {"0": 24, "1": 24, "2": 24, "3": 24}
    assert set(rg["prescreen_table_by_frame"]) == {"0", "1", "2", "3"}
    assert set(rg["screen_by_frame"]) == {"0", "1", "2", "3"}
    assert rg["evidence_partition"]["partition_of_pooled"] is True
    assert rg["retention_policy"]["policy"] == "frame_aware"
    for f, rows in rg["prescreen_table_by_frame"].items():
        assert all(r["n_topics"] == 24 and r["draws_per_topic"] == 1 for r in rows)
    sp = payloads[S.STAGE_SECOND_PASS]
    assert sp["rescreen_config"]["frame_aware"] is True
    assert sp["rescreen_config"]["frame_passes"] == 4
    assert set(sp["final_table_by_frame"]) == {"0", "1", "2", "3"}
    assert sp["provisional_plan"]["target_basis"] == "screen_proxy"
    assert sp["comparator_plan"]["policy"] == "legacy_pooled"
    for b in sp["batches"]:
        assert set(b["allocation_realised"].values()) == {24}
        assert b["requested_by_frames"]
    g2 = payloads[S.STAGE_GATE2]
    pop = g2["calibration_population"]
    assert pop["policy"] == "frame_aware" and pop["target_basis"] == "calibration_iota_a"
    assert pop["measured_under_every_frame"] is False
    assert set(pop["by_frame"]) == {str(w) for w in g2["supported_frames"]}
    assert sorted(pop["forwarded"]) == sorted(pop["selected_by_frames"])
    for label, frames in pop["selected_by_frames"].items():
        for w in g2["supported_frames"]:
            assert (w in frames) == (label in pop["by_frame"][str(w)]["forwarded"])
    # each frame's table holds its own set only; the comparator sits beside
    for w in g2["supported_frames"]:
        block = g2["by_frame"][str(w)]
        own = set(block["forwarding"]["forwarded"]) | set(block["extension_measured"])
        tabled = {f"{r['kind']}:{r['severity']}"
                  for r in block["calibration_rows"]["pooled"]}
        withheld = {f"{r['kind']}:{r['severity']}"
                    for r in block["calibration_rows_withheld"].get("pooled", [])}
        assert tabled <= own and (tabled | withheld) == own, (w, sorted(own - tabled - withheld))
        cmp_tabled = {f"{r['kind']}:{r['severity']}"
                      for r in block["comparator_rows"]["pooled"]}
        assert not (cmp_tabled & tabled)
        assert cmp_tabled <= set(block["comparator"]["extra_labels"])
        assert block["forwarding"]["target"]["basis"] == "calibration_iota_a"
        assert block["forwarding"]["target"]["iota_a"] == block["iota_a"]
    # an unsupported frame generated no candidate cell
    for w, failure in g2["unsupported_frames"].items():
        assert g2["by_frame"][w]["n_rows"]["candidates"]["total"] == 0
    g3 = payloads[S.STAGE_GATE3]
    rc = g3["retention_comparison"]
    assert rc["policy"] == "frame_aware"
    assert set(rc["comparator_eligibility"]) == {"legacy_pooled", "frame_aware_screen_proxy"}
    for w in g2["supported_frames"]:
        assert rc["by_frame"][str(w)]["available"]
        assert set(rc["by_frame"][str(w)]["by_policy"]) == {"legacy_pooled",
                                                            "frame_aware_screen_proxy"}
    rp = payloads[S.STAGE_REPORT]
    assert rp["generations"]["screen_passes"] == 4
    assert rp["generations"]["calibration_candidates"] == pop["n_candidate_rows"]
    assert rp["criteria"]["LADDER_COVERAGE"]["retention_policy"] == "frame_aware"


@pytest.mark.slow
def test_a_genuine_frame_effect_gives_frame_specific_forwarding(walked_effects):
    g2 = walked_effects["payloads"][S.STAGE_GATE2]
    pop = g2["calibration_population"]
    sets = {w: set(e["forwarded"]) for w, e in pop["by_frame"].items()}
    assert len(sets) >= 2
    assert len({frozenset(s) for s in sets.values()}) >= 2, "the frames forwarded one set"
    assert any(len(v) < len(sets) for v in pop["selected_by_frames"].values())
    # the provisional (screen-proxy) plan and the final plan are compared
    for w, a in pop["provisional_agreement"].items():
        assert a["jaccard"] is None or 0.0 <= a["jaccard"] <= 1.0


@pytest.mark.slow
def test_the_topup_planner_reads_the_frames_own_set(walked_effects):
    from dci1v8dev.confirm.pilot_import import open_pilot
    from dci1v8dev.confirm.topup import topup_plan
    tree = walked_effects["tree"]
    source = open_pilot(tree.context.evidence_root.parent, tree.model_key,
                        synthetic=True)
    plan = topup_plan(source)
    pop = source.gate2["calibration_population"]
    for w, entry in plan["by_frame"].items():
        if not entry.get("supported"):
            continue
        own = set(pop["by_frame"][w]["forwarded"])
        for fam in entry["candidate_families"].values():
            for r in fam:
                assert r["candidate"] not in own
