"""Approach A --- the wording frame is part of the experimental condition
(docs/V8_FRAME_CONDITIONING.md). The scientific contracts, tested on the
production functions with constructed rows and on the synthetic lifecycle:

1.  the same family/q under two frames carries different ι without being
    collapsed;
2.  different frames select different q*;
3.  a frame can fail operating-point identification while another continues;
4.  LOCAL matching compares A and R within one frame only;
5.  a reference can be LOCAL-valid under one frame and invalid under another;
6.  SPECTRUM support is constructed per frame;
7.  no spectrum pool combines frame-specific coordinates;
8.  frame-specific references and backups survive into the pre-freeze record;
9.  the records round-trip the frame dimension through signing;
10. the fresh-topic protections still hold (with the existing tests);
11. every generated row is still scored and accounted for (lifecycle);
12. composed cells remain impossible before the freeze;
13. no B+R / R+B information can influence a frame's selection;
14. a pooled frame statistic is descriptive and cannot alter a selection;
15. a synthetic world with genuine frame effects gives frame-specific
    selections (slow, lifecycle);
16. a world where the frames behave identically gives identical selections;
    plus determinism and row-order invariance.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages.calibration_table import FORBIDDEN_CALIBRATION_FIELDS
from dci1v7.verifiers.constraints import Constraint
from dci1v8dev import rules as R
from dci1v8dev.run import calibration as CAL
from dci1v8dev.run import references as REF
from dci1v8dev.run import report as RPT
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import model_tree, synthetic_context
from dci1v8dev.run.execute import UNCONSTRAINED_ARM, frame_of_block, rows_of_frame
from dci1v8dev.run import wording as W
from dci1v8dev.spectrum import precision

MODEL = "qwen3-4b"
CANDIDATES = ("MK1:2", "MK1:5", "MK1:8", "MK2:2", "MK2:5", "MK2:8",
              "MK3:2", "MK3:5", "MK3:8", "MK4:5", "MK5:5", "MK6:5",
              "XC1:2", "XC1:3", "XC1:5")
A_GRID = tuple(C.TARGET_GRID)
B_GRID = tuple(C.FOCAL_GRID)
RESAMPLES = 150


def _topics_per_frame(topics_per_split: int = C.N_CALIBRATION_A) -> int:
    """What one frame is measured on in a fixture of this size: the
    allocation's own arithmetic, so a change to the passes moves the
    fixtures with it instead of leaving them asserting the old design."""
    return 2 * topics_per_split * R.CALIBRATION_FRAME_PASSES // C.N_WORDINGS


def _u(*key) -> float:
    digest = hashlib.sha256("|".join(str(k) for k in key).encode()).hexdigest()
    return int(digest[:12], 16) / float(16 ** 12)


def _default_rates(kind_shift: float = 0.0) -> dict[str, float]:
    """A curve through the target band, B through the focal band, marker
    ladders straddling A --- the fixture geometry the walk uses."""
    rates: dict[str, float] = {}
    for q in A_GRID:
        rates[f"A:{q}"] = max(0.05, min(0.98, 0.95 - 0.07 * q + kind_shift))
    for m in B_GRID:
        rates[f"B:{m}"] = max(0.05, min(0.98, 0.25 + 0.06 * m))
    for label in CANDIDATES:
        kind, q = label.split(":")
        rates[label] = max(0.05, min(0.98, 0.95 - 0.07 * int(q)))
    return rates


def rows_for(rates_by_frame, *, topics_per_split: int = C.N_CALIBRATION_A,
             draws: int = C.M_CAL,
             chance: dict[str, float] | None = None,
             outcome_key=None, extra_instances: tuple[str, ...] = (),
             extension: tuple[str, ...] = (),
             offsets: tuple[int, ...] | None = None) -> tuple[list[dict], ...]:
    """Scored rows in the run layer's schema for a two-split calibration,
    laid out over ``rules.CALIBRATION_FRAME_OFFSETS`` calibration passes
    exactly as ``calibration.calibration_blocks`` lays the real ones out:
    each pass covers ``2 * topics_per_split`` topics under one frame per
    block, and pass p is based at a block index congruent to its offset, so
    ``frame = block index % 4`` holds on every row and each frame ends on
    ``2 * topics_per_split * passes / N_WORDINGS`` distinct topics.

    ``rates_by_frame`` maps frame -> label -> pass probability when the
    constraint is stated; ``chance`` maps label -> pass probability when it
    is absent on the unconstrained cell. ``outcome_key`` (frame, label,
    topic position within the pass, draw, present) -> key decides the
    pseudo-random outcome; the default keys by the frame and the position,
    so two frames differ; keying by ``position // N_WORDINGS`` --- the
    topic's rank within its frame, which the passes preserve --- makes the
    frames identical (contract 16)."""
    chance = chance or {}
    instances = ([f"A:{q}" for q in A_GRID] + [f"B:{m}" for m in B_GRID]
                 + list(CANDIDATES) + list(extra_instances))
    grid_rows: list[dict] = []
    cand_rows: list[dict] = []
    ext_rows: list[dict] = []
    outcome_key = outcome_key or (lambda f, label, t, d, present: (f, label, t, d, present))
    n_topics_total = 2 * topics_per_split
    cursor = 0
    for offset in (R.CALIBRATION_FRAME_OFFSETS if offsets is None else offsets):
        cursor += (offset - cursor) % C.N_WORDINGS
        base, cursor = cursor, cursor + n_topics_total
        n = 0
        for split in (C.CALIBRATION_A, C.CALIBRATION_B):
            for t in range(topics_per_split):
                position, block_index = n, base + n
                n += 1
                frame = block_index % C.N_WORDINGS
                topic = f"{split}-topic-{t:03d}"
                rates = rates_by_frame[frame]

                def score(label: str, stated: str | None, draw: int) -> dict:
                    kind, q = label.rpartition(":")[0], int(label.rpartition(":")[2])
                    present = label == stated
                    p = rates[label] if present else chance.get(label, 0.0)
                    passed = _u(*outcome_key(frame, label, position, draw, present),
                                "outcome") < p
                    return {"kind": kind, "severity": q, "slot": label,
                            "statistic": q if passed else q + 1, "passed": passed,
                            "graded": 0.5, "non_vacuous": True,
                            "vacuous_pass": False, "present": present,
                            "position": 0 if present else None,
                            "configuration": None, "processing_failure": False}

                def row(cell_id: str, stated: str | None, draw: int, run: str) -> dict:
                    block_id = f"g2{run}-{block_index:03d}"
                    # the run's own instance list, as ``generate_and_score`` gets
                    # it: the extension run scores its own candidates, the grid
                    # and candidate runs score what was declared when they ran
                    scored_instances = (list(instances) + [l for l in extension
                                                           if l not in instances]
                                        if run == "extension-1" else instances)
                    return {"row_id": f"{block_id}:{cell_id}:{draw}", "cell_id": cell_id,
                            "block_id": block_id, "block_index": block_index,
                            "block_frame": frame, "draw_index": draw,
                            "arm": UNCONSTRAINED_ARM if stated is None else "solo",
                            "slots": [] if stated is None else [stated],
                            "topic_id": topic, "area": "fixture", "topic_split": split,
                            "load": 0 if stated is None else 1,
                            "wording_indices": [] if stated is None else [frame],
                            "frame": None if stated is None else frame,
                            "word_count": 80, "truncated": False, "empty": False,
                            "run": run, "model_key": MODEL,
                            "scores": [score(label, stated, draw)
                                       for label in scored_instances]}

                for draw in range(draws):
                    grid_rows.append(row("unconstrained", None, draw, "grid-A"))
                    for q in A_GRID:
                        grid_rows.append(row(f"solo:A:{q}", f"A:{q}", draw, "grid-A"))
                    grid_rows.append(row("unconstrained", None, draw, "grid-B"))
                    for m in B_GRID:
                        grid_rows.append(row(f"solo:B:{m}", f"B:{m}", draw, "grid-B"))
                    for label in CANDIDATES:
                        cand_rows.append(row(f"solo:{label}", label, draw, "candidates"))
                    for label in extension:
                        ext_rows.append(row(f"solo:{label}", label, draw, "extension-1"))
    if extension:
        return grid_rows, cand_rows, ext_rows
    return grid_rows, cand_rows


def _candidates() -> list[Constraint]:
    return CAL.constraints_from_labels(CANDIDATES)


def _frames(grid, cand, **kw):
    return CAL.gate2_frames_from_rows(grid, cand, candidates=_candidates(),
                                      model_key=MODEL, **kw)


def _gate2_record(frames_result, grid, cand) -> dict:
    """A Gate-2 record of the shape ``gate2_payload`` writes, from the pure
    per-frame result (no extension round)."""
    supported = frames_result["supported"]
    rows = grid + cand
    by_frame = {str(w): b for w, b in frames_result["by_frame"].items()}
    for w in supported:
        by_frame[str(w)].setdefault("extension_reach", {})
        by_frame[str(w)].setdefault("extension_plan", {"picks": {}})
    pooled = W.frame_table(rows)
    record = {
        "stage": S.STAGE_GATE2, "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE2],
        "outcome": "PASS", "frame_conditioning": CAL.FRAME_CONDITIONING_STATEMENT,
        "frames": list(S.FRAMES), "supported_frames": supported,
        "unsupported_frames": {str(w): f for w, f in frames_result["failures"].items()},
        "by_frame": by_frame,
        "descriptive_pooled": {"read_by": [], "solo_curves": {}},
        "frame_comparison_pooled": W.frame_comparison(pooled),
        "wording_by_frame": {"pooled": pooled},
    }
    return transitions.on_the_wire(REF.jsonable(record))


@pytest.fixture(scope="module")
def two_frame_world():
    """Frames 0 and 2 see a harder A and harder marker ladders (every rate
    shifted down by 0.25); frames 1 and 3 see the fixture geometry."""
    easy = _default_rates()
    hard = {k: max(0.05, v - 0.25) for k, v in easy.items() if not k.startswith("B:")}
    hard.update({k: v for k, v in easy.items() if k.startswith("B:")})
    rates = {0: hard, 1: easy, 2: hard, 3: easy}
    # outcomes keyed by the frame's rate group and the topic's position
    # within its frame, so frames 0 and 2 (and 1 and 3) are exact copies
    key = lambda f, label, t, d, present: (f % 2, label, t // C.N_WORDINGS, d, present)  # noqa: E731
    grid, cand = rows_for(rates, outcome_key=key)
    return {"rates": rates, "grid": grid, "cand": cand,
            "frames": _frames(grid, cand)}


@pytest.fixture(scope="module")
def synthetic_tree(tmp_path_factory):
    return model_tree(synthetic_context(tmp_path_factory.mktemp("fc")), MODEL)


# ------------------------------------------------------------ 1, 2, 3
def test_the_same_rung_under_two_frames_carries_different_iota_uncollapsed(two_frame_world):
    fr = two_frame_world["frames"]
    tables = {w: {r["kind"] + ":" + str(r["severity"]): r
                  for r in fr["by_frame"][w]["calibration_rows"]["pooled"]}
              for w in fr["supported"]}
    assert {0, 1} <= set(tables)
    for label in ("MK1:5", "MK2:5", "MK3:5"):
        hard, easy = tables[0][label], tables[1][label]
        assert hard["solo_compliance"] < easy["solo_compliance"] - 0.10
        assert hard["n_topics"] == easy["n_topics"] == _topics_per_frame()
    # ... and the wording diagnostic keeps them apart as well
    diag = W.frame_table(two_frame_world["grid"] + two_frame_world["cand"])
    by = {(e["frame"], e["candidate"]): e for e in diag}
    assert by[(0, "MK1:5")]["iota"] < by[(1, "MK1:5")]["iota"]


def test_different_frames_select_different_operating_points(two_frame_world):
    fr = two_frame_world["frames"]
    n_star = {w: fr["by_frame"][w]["n_star"] for w in fr["supported"]}
    assert n_star[0] != n_star[1] and n_star[2] == n_star[0] and n_star[3] == n_star[1]
    iota_a = {w: fr["by_frame"][w]["iota_a"] for w in fr["supported"]}
    for w in fr["supported"]:
        block = fr["by_frame"][w]
        assert block["iota_a_basis"].startswith("§13.2")
        assert block["chance_basis"]["cell"] == UNCONSTRAINED_ARM
        assert block["n_topics_a"] == _topics_per_frame()
        # iota_A(f) is A's own solo rate at n*(f) under frame f
        assert block["solo_compliance_a"] == block["solo_curves"]["A"][str(block["n_star"])]
    assert len(set(round(v, 6) for v in iota_a.values())) >= 2


def test_a_frame_can_fail_operating_point_identification_while_others_continue():
    easy = _default_rates()
    exhausted = {k: (0.02 if k.startswith("A:") else v) for k, v in easy.items()}
    grid, cand = rows_for({0: easy, 1: exhausted, 2: easy, 3: easy})
    fr = _frames(grid, cand)
    assert fr["supported"] == [0, 2, 3]
    assert set(fr["failures"]) == {1}
    failure = fr["failures"][1]
    assert failure["status"] == "TARGET_RANGE_EXHAUSTED" and failure["step"] == 1
    assert fr["by_frame"][1]["status"] == S.FRAME_UNSUPPORTED
    assert "calibration_rows" not in fr["by_frame"][1]
    for w in (0, 2, 3):
        assert fr["by_frame"][w]["calibration_rows"]["pooled"]
    # and only when EVERY frame fails is the replication terminal
    with pytest.raises(ProtocolError):
        CAL.terminal_status_over_frames({})
    all_fail = {0: {"status": "REGIME_NOT_FOUND", "step": 3},
                1: {"status": "GRID_RESOLUTION_INSUFFICIENT", "step": 2},
                2: {"status": "FOCAL_RANGE_EXHAUSTED", "step": 2},
                3: {"status": "REGIME_NOT_FOUND", "step": 3}}
    assert CAL.terminal_status_over_frames(all_fail) == "GRID_RESOLUTION_INSUFFICIENT"
    assert set(S.FRAME_FAILURE_STATUSES) <= set(S.TERMINAL_STATUSES)


def test_a_grid_resolution_failure_is_recorded_per_frame_not_raised():
    easy = _default_rates()
    jump = dict(easy)
    for q in A_GRID:                      # 0.95 down to 0.30 between q=4 and q=5
        jump[f"A:{q}"] = 0.97 if q <= 4 else 0.30
    grid, cand = rows_for({0: jump, 1: easy, 2: easy, 3: easy})
    fr = _frames(grid, cand)
    assert 0 in fr["failures"] and fr["failures"][0]["status"] == "GRID_RESOLUTION_INSUFFICIENT"
    assert fr["supported"] == [1, 2, 3]


# ------------------------------------------------------------ 4, 5, 6, 7, 8
@pytest.fixture(scope="module")
def two_frame_gate3(two_frame_world, synthetic_tree):
    record = _gate2_record(two_frame_world["frames"], two_frame_world["grid"],
                           two_frame_world["cand"])
    payload = REF.gate3_payload(synthetic_tree, producing_commit="0" * 40,
                                gate2_record=record, seed=0, resamples=RESAMPLES)
    return {"gate2": record, "gate3": transitions.on_the_wire(payload)}


def test_local_matching_compares_a_and_r_within_the_same_frame_only(two_frame_gate3):
    g2, g3 = two_frame_gate3["gate2"], two_frame_gate3["gate3"]
    for w in g3["supported_frames"]:
        iota_a = g2["by_frame"][str(w)]["iota_a"]
        block = g3["by_frame"][str(w)]
        assert block["iota_a"] == iota_a
        for label, verdict in block["local"].items():
            diff = next((c for c in verdict["components"] if c["component"] == "V_diff"), None)
            if diff and diff["evaluated"]:
                assert diff["values"]["iota_a"] == iota_a, (w, label)
        for label, verdict in block["spectrum"].items():
            pos = next(c for c in verdict["components"] if c["component"] == "V_pos")
            assert pos["values"]["iota_a"] == iota_a, (w, label)
        # the folded stability read A's split coordinates OF THIS FRAME
        for label, st in block["stability"].items():
            for split in (C.CALIBRATION_A, C.CALIBRATION_B):
                comps = st["per_split"][split]["components"]
                diff = next((c for c in comps if c["component"] == "V_diff"), None)
                if diff:
                    assert diff["values"]["iota_a"] == g2["by_frame"][str(w)]["iota_a_by_split"][split]
    a0, a1 = g2["by_frame"]["0"]["iota_a"], g2["by_frame"]["1"]["iota_a"]
    assert a0 != a1


def test_a_reference_can_be_local_valid_under_one_frame_and_not_another(two_frame_gate3):
    g3 = two_frame_gate3["gate3"]
    verdicts = {w: {l: v["passed"] for l, v in g3["by_frame"][str(w)]["local"].items()}
                for w in g3["supported_frames"]}
    differing = [l for l in verdicts[0] if verdicts[0][l] != verdicts[1][l]]
    assert differing, verdicts
    # no rung is asked to qualify under every frame: the frame's own set is
    # what the frame carries
    fam0 = set(g3["by_frame"]["0"]["survival"]["local_valid_families"])
    fam1 = set(g3["by_frame"]["1"]["survival"]["local_valid_families"])
    assert fam0 or fam1
    assert g3["cross_frame"]["local_valid_family_in_every_supported_frame"] == \
        sorted(set.intersection(*[set(g3["by_frame"][str(w)]["survival"]["local_valid_families"])
                                  for w in g3["supported_frames"]]))


def test_spectrum_support_is_constructed_per_frame_from_that_frames_coordinates(two_frame_gate3):
    g2, g3 = two_frame_gate3["gate2"], two_frame_gate3["gate3"]
    for w in g3["supported_frames"]:
        block = g3["by_frame"][str(w)]
        table = {f"{r['kind']}:{r['severity']}": r
                 for r in g2["by_frame"][str(w)]["calibration_rows"]["pooled"]}
        sel = block["spectrum_selection"]
        assert sel["iota_a"] == block["iota_a"]
        for p in sel["points"]:
            row = table[p["candidate"]]
            expected = (row["solo_compliance"] - row["chance_compliance"]) / (1 - row["chance_compliance"])
            assert abs(p["iota"] - expected) < 1e-12, (w, p["candidate"])
        for label, v in block["spectrum"].items():
            if v["passed"]:
                assert label in table
        assert block["coverage"]["rule"]["n_blocks"] == S.CONFIRMATORY_BLOCKS_PER_FRAME
        assert block["coverage"]["projection"]["n_blocks"] == S.CONFIRMATORY_BLOCKS_PER_FRAME
    # the two frames' spectrum-valid pools are their own, not one pool
    pools = {w: {l for l, v in g3["by_frame"][str(w)]["spectrum"].items() if v["passed"]}
             for w in g3["supported_frames"]}
    assert pools[0] != pools[1]


def test_frame_specific_references_and_backups_reach_the_prefreeze_record(two_frame_gate3):
    g3 = two_frame_gate3["gate3"]
    assert set(g3["frame_states"]) == {str(w) for w in S.FRAMES}
    for w in g3["supported_frames"]:
        block = g3["by_frame"][str(w)]
        assert block["state"] in S.FRAME_STATES and block["state"] != "UNSUPPORTED"
        assert set(block["core_references"]) == {e["family"] for e in block["survival"]["core_references"]}
        assert block["survival"]["backups"] == block["backups"]["backups"]
        assert g3["frame_states"][str(w)]["local_identified"] == block["survival"]["core_identified"]
    assert g3["estimands"]["generated_here"] is False
    assert "Delta_R(f)" in g3["estimands"]["primary"]["matched_reference_contrast"]
    assert g3["estimands"]["pooled_over_frames"] == "descriptive only"


# ------------------------------------------------------------ 9
def test_records_round_trip_the_frame_dimension_through_signing(two_frame_gate3, tmp_path):
    from dci1v4.engine.signing import create_signing_key
    tree = model_tree(synthetic_context(tmp_path / "rt"), MODEL)
    create_signing_key(tree.context.signing_key_path)
    for stage, payload in ((S.STAGE_GATE2, two_frame_gate3["gate2"]),
                           (S.STAGE_GATE3, two_frame_gate3["gate3"])):
        transitions.write_stage_record(tree, stage, dict(payload))
        back = transitions.read_stage_record(tree, stage)
        assert back["by_frame"] == payload["by_frame"]
        assert back["supported_frames"] == payload["supported_frames"]
        assert back["frames"] == list(S.FRAMES)
    g2 = transitions.read_stage_record(tree, S.STAGE_GATE2)
    for k in ("iota_a", "m_star", "n_star", "calibration_rows", "core_references"):
        assert k not in g2, f"a pooled top-level {k} came back"


# ------------------------------------------------------------ 12, 13
def test_composed_cells_and_composed_fields_are_refused_at_gate_3(two_frame_gate3, synthetic_tree):
    record = copy.deepcopy(two_frame_gate3["gate2"])
    row = record["by_frame"]["0"]["calibration_rows"]["pooled"][0]
    row["composed_compliance"] = 0.5
    with pytest.raises(ProtocolError, match="composed"):
        REF.gate3_payload(synthetic_tree, producing_commit="0" * 40,
                          gate2_record=record, seed=0, resamples=RESAMPLES)
    # a composed row cannot even be grouped by frame
    with pytest.raises(ProtocolError):
        frame_of_block({"row_id": "x", "block_id": "bad", "wording_indices": [0, 1]})


def test_no_composed_information_can_reach_a_frames_selection():
    import ast
    import inspect
    banned = set(FORBIDDEN_CALIBRATION_FIELDS)
    for module in (CAL, REF, RPT):
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                    and isinstance(node.slice.value, str):
                assert node.slice.value.lower() not in banned, (module.__name__, node.lineno)
            if isinstance(node, ast.Attribute):
                assert node.attr.lower() not in banned, (module.__name__, node.lineno)
    src = inspect.getsource(REF) + inspect.getsource(CAL)
    for forbidden in ("pair:", "B+", "+B", "composed_contrast", "delta_diff"):
        assert f'"{forbidden}"' not in src.replace("B+X", "").replace("X+B", "")


# ------------------------------------------------------------ 14
def test_a_pooled_frame_statistic_is_descriptive_and_cannot_move_a_selection(two_frame_gate3, synthetic_tree):
    import inspect
    record = copy.deepcopy(two_frame_gate3["gate2"])
    record["descriptive_pooled"] = {"read_by": [], "solo_curves": {"A": {"5": 0.99}},
                                    "target_selection": {"selected": None}}
    record["frame_comparison_pooled"] = {}          # the cross-frame comparison
    moved = transitions.on_the_wire(REF.gate3_payload(
        synthetic_tree, producing_commit="0" * 40, gate2_record=record,
        seed=0, resamples=RESAMPLES))
    base = two_frame_gate3["gate3"]
    for w in base["supported_frames"]:
        for key in ("core_references", "spectrum_selection", "backups", "local",
                    "spectrum", "state", "survival"):
            assert moved["by_frame"][str(w)][key] == base["by_frame"][str(w)][key], (w, key)
    assert "descriptive_pooled" not in inspect.getsource(REF)
    assert "descriptive_pooled" not in inspect.getsource(RPT)
    assert CAL.FRAME_CONDITIONING_STATEMENT["pooled"].startswith("descriptive_pooled only")


# ------------------------------------------------------------ 16 + determinism
def test_identical_frames_give_identical_selections_and_the_result_is_deterministic(synthetic_tree):
    easy = _default_rates()
    same = {w: easy for w in S.FRAMES}
    # outcomes keyed by the topic's position WITHIN its frame: frame f's
    # k-th block has the outcomes frame g's k-th block has
    key = lambda f, label, t, d, present: (label, t // C.N_WORDINGS, d, present)  # noqa: E731
    grid, cand = rows_for(same, outcome_key=key)
    fr = _frames(grid, cand)
    assert fr["supported"] == list(S.FRAMES)
    blocks = {w: fr["by_frame"][w] for w in S.FRAMES}
    for w in S.FRAMES[1:]:
        assert blocks[w]["n_star"] == blocks[0]["n_star"]
        assert blocks[w]["m_star"] == blocks[0]["m_star"]
        assert blocks[w]["iota_a"] == blocks[0]["iota_a"]
        rows_w = [{k: v for k, v in r.items()} for r in blocks[w]["calibration_rows"]["pooled"]]
        rows_0 = [{k: v for k, v in r.items()} for r in blocks[0]["calibration_rows"]["pooled"]]
        assert rows_w == rows_0
    record = _gate2_record(fr, grid, cand)
    g3 = transitions.on_the_wire(REF.gate3_payload(
        synthetic_tree, producing_commit="0" * 40, gate2_record=record, seed=0,
        resamples=RESAMPLES))
    for w in S.FRAMES[1:]:
        a, b = g3["by_frame"][str(w)], g3["by_frame"]["0"]
        assert a["core_references"] == b["core_references"]
        assert a["spectrum_selection"]["points"] == b["spectrum_selection"]["points"]
        assert a["backups"]["backups"] == b["backups"]["backups"]
        assert a["state"] == b["state"]
    assert g3["cross_frame"]["core_same_rung_in_every_supported_frame"] == \
        sorted(g3["by_frame"]["0"]["core_references"])
    # determinism and row-order invariance
    again = transitions.on_the_wire(REF.gate3_payload(
        synthetic_tree, producing_commit="0" * 40, gate2_record=record, seed=0,
        resamples=RESAMPLES))
    assert again["by_frame"] == g3["by_frame"]
    shuffled = copy.deepcopy(record)
    for w in S.FRAMES:
        for split in shuffled["by_frame"][str(w)]["calibration_rows"]:
            shuffled["by_frame"][str(w)]["calibration_rows"][split].reverse()
    permuted = transitions.on_the_wire(REF.gate3_payload(
        synthetic_tree, producing_commit="0" * 40, gate2_record=shuffled, seed=0,
        resamples=RESAMPLES))
    for w in S.FRAMES:
        assert permuted["by_frame"][str(w)]["core_references"] == g3["by_frame"][str(w)]["core_references"]
        assert permuted["by_frame"][str(w)]["spectrum_selection"]["points"] == \
            g3["by_frame"][str(w)]["spectrum_selection"]["points"]
    grid_r, cand_r = list(reversed(grid)), list(reversed(cand))
    fr_r = _frames(grid_r, cand_r)
    for w in S.FRAMES:
        assert fr_r["by_frame"][w]["n_star"] == fr["by_frame"][w]["n_star"]
        assert fr_r["by_frame"][w]["iota_a"] == fr["by_frame"][w]["iota_a"]


# ------------------------------------------------------- the extension round
def test_extension_instances_cover_every_rung_the_extension_round_can_pick():
    """Pilot r4's defect: a reserve rung the extension measures has a chance
    column only if it was declared an instance when the grids were scored.
    The declared set is a superset of every pick, under every deficiency
    pattern, and is computed before any calibration value exists."""
    from dci1v8dev.prescreen.extension import (ExtensionRule,
                                               calibration_extension_plan)
    families = ("MK1", "MK6", "XC1", "XC3", "MK5")
    carried = CAL.constraints_from_labels(
        ["MK1:2", "MK1:5", "MK6:3", "MK6:8", "XC1:3", "XC3:4", "MK5:5"])
    declared = {c.label for c in CAL.extension_instances(carried, families)}
    assert declared and all(c.label not in declared for c in carried)
    for below in (True, False):
        for above in (True, False):
            reach = {k: {"measured": sorted(c.severity for c in carried
                                            if c.kind == k),
                         "reaches_below": below, "reaches_above": above,
                         "spectrum_candidate": True} for k in families}
            plan = calibration_extension_plan(reach, rule=ExtensionRule())
            picks = {f"{k}:{q}" for k, qs in plan["picks"].items() for q in qs}
            assert picks <= declared, (below, above, sorted(picks - declared))
    # a family the retention did not forward as a spectrum candidate cannot
    # be picked from, so it is not declared either
    assert not any(l.startswith("MK2:") for l in declared)


def test_an_extension_rung_gets_its_chance_column_and_kappa_under_b():
    """With the reserve rung declared on the grids, the extension round's
    §13.11 row carries a measured chance column (§13.2) and kappa(R|B)
    (§13.6), on the frame's own cells. Undeclared, the producer refuses ---
    the r4 defect, pinned."""
    rates = _default_rates()
    rates["MK1:9"] = 0.30
    rates_by_frame = {w: rates for w in S.FRAMES}
    grid, cand, ext = rows_for(rates_by_frame, extra_instances=("MK1:9",),
                               extension=("MK1:9",), chance={"MK1:9": 0.05})
    fr = _frames(grid, cand)
    assert fr["supported"], fr["failures"]
    w = fr["supported"][0]
    m_star = fr["by_frame"][w]["m_star"]
    kept, withheld, measured = CAL.frame_tables(
        rows_of_frame(grid, w),
        candidate_rows=rows_of_frame(cand, w) + rows_of_frame(ext, w),
        candidates=CAL.constraints_from_labels(["MK1:9"]), m_star=m_star,
        model_key=MODEL, prescreen={}, kappa_column=None)
    row = next(r for r in kept["pooled"]
               if r["kind"] == "MK1" and r["severity"] == 9)
    assert row["chance_compliance"] > 0            # measured, not assumed
    assert row["n_topics"] == _topics_per_frame()
    assert row["kappa_under_b"] is not None        # §13.6 admits no absence
    assert row["kappa_under_b_source"]["m_star"] == m_star
    assert row["per_topic_solo"]                   # §13.7 can be run on it
    bare_grid, bare_cand, bare_ext = rows_for(
        rates_by_frame, extension=("MK1:9",), chance={"MK1:9": 0.05})
    with pytest.raises(ProtocolError, match="no unconstrained cell"):
        CAL.frame_tables(rows_of_frame(bare_grid, w),
                         candidate_rows=rows_of_frame(bare_cand, w)
                         + rows_of_frame(bare_ext, w),
                         candidates=CAL.constraints_from_labels(["MK1:9"]),
                         m_star=m_star, model_key=MODEL, prescreen={},
                         kappa_column=None)


# ------------------------------------------------------------ the report
def test_the_report_aggregates_per_frame_verdicts_without_hiding_a_frame():
    agg = RPT.aggregate({"0": True, "1": False, "3": True})
    assert agg["passed"] and agg["frames_passing"] == [0, 3] and agg["frames_failing"] == [1]
    assert not agg["passed_on_every_supported_frame"]
    assert agg["aggregation"] == S.REPORT_AGGREGATION == "any_supported_frame"
    assert not RPT.aggregate({"0": False})["passed"]
    assert not RPT.aggregate({})["passed"]


def test_the_block_frame_is_defined_on_every_load_and_agrees_with_the_stated_frame():
    assert frame_of_block({"block_frame": 3, "wording_indices": [3]}) == 3
    assert frame_of_block({"block_index": 6, "wording_indices": []}) == 2
    assert frame_of_block({"block_id": "g2grid-A-017", "wording_indices": []}) == 1
    with pytest.raises(ProtocolError, match="frame"):
        frame_of_block({"row_id": "r", "block_frame": 1, "wording_indices": [2]})
    rows = [{"block_index": i, "wording_indices": [i % 4] if i % 2 else [],
             "row_id": str(i)} for i in range(8)]
    assert [r["block_index"] for r in rows_of_frame(rows, 1)] == [1, 5]


def test_the_per_frame_precision_projection_is_the_registered_one_rescaled():
    pts = [("F", 0.5), ("F", 0.7), ("G", 0.5), ("G", 0.7)]
    full = precision.projected_se_beta(pts)
    quarter = precision.projected_se_beta(pts, n_blocks=S.CONFIRMATORY_BLOCKS_PER_FRAME)
    assert full["n_blocks"] == C.N_BLOCKS and quarter["n_blocks"] == C.N_BLOCKS // C.N_WORDINGS
    assert abs(quarter["se_beta"] / full["se_beta"] - 2.0) < 1e-9
    assert precision.se_point_at(C.N_BLOCKS) == precision.MEASURED["se_point"]


# ------------------------------------------------------------------------
# The calibration-allocation amendment (rules.CALIBRATION_FRAME_OFFSETS,
# CHANGES_SCIENTIFIC.md 2026-08-30): two passes over the calibration topics,
# 96 topics per frame, no frame pooled with another and no topic repeated
# inside a frame. Approach A is what makes the allocation a *per-frame*
# question, so these are frame contracts.
# ------------------------------------------------------------------------
def _real_calibration_topics():
    return ([{"topic_id": f"a-{i:03d}"} for i in range(C.N_CALIBRATION_A)]
            + [{"topic_id": f"b-{i:03d}"} for i in range(C.N_CALIBRATION_B)])


def test_each_frame_is_measured_on_the_designed_number_of_topics():
    """Contract: the allocation gives every frame exactly
    ``rules.CALIBRATION_TOPICS_PER_FRAME`` distinct topics --- 96 of the 192
    at the two registered passes, against 48 under one."""
    topics = _real_calibration_topics()
    built = CAL.calibration_blocks(topics, "g2grid-A")
    assert len(built) == C.N_CALIBRATION * R.CALIBRATION_FRAME_PASSES
    by_frame: dict[int, set[str]] = {}
    for block in built:
        by_frame.setdefault(block.index % C.N_WORDINGS, set()).add(block.topic_id)
    assert sorted(by_frame) == list(S.FRAMES)
    for frame, seen in by_frame.items():
        assert len(seen) == R.CALIBRATION_TOPICS_PER_FRAME == 96, frame
    # every topic is met, and met under exactly `passes` distinct frames
    frames_of_topic: dict[str, set[int]] = {}
    for block in built:
        frames_of_topic.setdefault(block.topic_id, set()).add(
            block.index % C.N_WORDINGS)
    assert len(frames_of_topic) == C.N_CALIBRATION
    assert {len(v) for v in frames_of_topic.values()} == {
        R.CALIBRATION_FRAME_PASSES}


def test_no_topic_is_measured_twice_inside_one_frame_and_the_splits_balance():
    """Contract: a frame's topics are distinct (so its per-topic vector has
    one entry per topic and the SE is formed at the topic count that is
    really there) and balanced over §13.7's two splits."""
    topics = _real_calibration_topics()
    built = CAL.calibration_blocks(topics, "g2grid-A")
    assert len({b.block_id for b in built}) == len(built)
    assert len({b.index for b in built}) == len(built)
    per_frame: dict[int, list[str]] = {}
    for block in built:
        per_frame.setdefault(block.index % C.N_WORDINGS, []).append(block.topic_id)
    for frame, seen in per_frame.items():
        assert len(seen) == len(set(seen)), f"frame {frame} repeats a topic"
        a = sum(1 for t in seen if t.startswith("a-"))
        b = sum(1 for t in seen if t.startswith("b-"))
        assert a == b == R.CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT == 48, frame
    # the offsets are what makes this true; a repeated offset would not
    assert len({o % C.N_WORDINGS for o in R.CALIBRATION_FRAME_OFFSETS}) == \
        R.CALIBRATION_FRAME_PASSES


def test_the_frame_is_still_the_block_index_modulo_the_wordings():
    """The passes must not break the one invariant every reader uses
    (``execute.frame_of_block``): a pass is based at an index congruent to
    its offset, so the derived frame and the rendered frame agree on every
    row of every pass."""
    topics = _real_calibration_topics()
    built = CAL.calibration_blocks(topics, "g2cand")
    n = len(topics)
    for pass_index, offset in enumerate(R.CALIBRATION_FRAME_OFFSETS):
        chunk = built[pass_index * n:(pass_index + 1) * n]
        for position, block in enumerate(chunk):
            assert block.index % C.N_WORDINGS == (position + offset) % C.N_WORDINGS


def test_the_allocation_is_asserted_on_the_rows_and_refuses_a_short_frame():
    """``assert_allocation_realised`` runs on the generated rows on the
    mandatory path. A frame short of the allocation, or unbalanced across
    the splits, is refused rather than recorded."""
    grid, _cand = rows_for({w: _default_rates() for w in S.FRAMES},
                           topics_per_split=24, draws=1)
    by_frame = {w: rows_of_frame(grid, w) for w in S.FRAMES}
    expected = 48 * R.CALIBRATION_FRAME_PASSES // C.N_WORDINGS
    realised = CAL.assert_allocation_realised(
        by_frame, expected_topics_per_frame=expected, where="test")
    assert {v["n_topics"] for v in realised.values()} == {expected}
    with pytest.raises(ProtocolError, match="distinct topics"):
        CAL.assert_allocation_realised(by_frame,
                                       expected_topics_per_frame=expected + 1,
                                       where="test")
    lopsided = {w: [r for r in rows if r["topic_split"] == C.CALIBRATION_A]
                for w, rows in by_frame.items()}
    with pytest.raises(ProtocolError, match="§13.7 compares two halves"):
        CAL.assert_allocation_realised(
            lopsided, expected_topics_per_frame=expected // 2, where="test")


def test_the_passes_reach_the_estimator_that_forms_the_coordinate(monkeypatch):
    """The point of the amendment: a frame's §13.11 per-topic vector --- the
    vector ``spectrum.validity._se_iota`` forms SE(iota) at --- is as long
    as the frame's topic count, so two passes halve the variance instead of
    piling extra draws onto the same topics. Measured against one pass on
    the same production path."""
    rates = {w: _default_rates() for w in S.FRAMES}

    def vectors():
        grid, cand = rows_for(rates, topics_per_split=24, draws=2)
        result = _frames(grid, cand)
        block = result["by_frame"][result["supported"][0]]
        return {f"{r['kind']}:{r['severity']}": r
                for r in block["calibration_rows"]["pooled"]}

    two = vectors()
    monkeypatch.setattr(R, "CALIBRATION_FRAME_OFFSETS", (0,))
    one = vectors()
    shared = sorted(set(one) & set(two))
    assert shared
    for label in shared:
        n_one = len(one[label]["per_topic_solo"])
        n_two = len(two[label]["per_topic_solo"])
        assert n_one == one[label]["n_topics"] == 12, label
        assert n_two == two[label]["n_topics"] == 24, label
    # and the standard error the rule reads falls with it
    from dci1v7.stages.calibration_table import load_calibration_table
    from dci1v8dev.spectrum.validity import _se_iota
    def _ses(rows):
        table = load_calibration_table(
            [r for r in rows.values()], model_key=MODEL,
            m_star=int(rows[next(iter(rows))]["kappa_under_b_source"]["m_star"]),
            split="pooled")
        return {r.label: _se_iota(r) for r in table}
    se_one, se_two = _ses(one), _ses(two)
    ratios = [se_one[k] / se_two[k] for k in shared
              if se_one.get(k) and se_two.get(k)]
    assert ratios and sum(ratios) / len(ratios) > 1.2, ratios


def test_the_gate2_record_and_the_manifest_state_the_allocation():
    """A record that does not say what it was measured on cannot be read
    later; the allocation block is on Gate 2, carried to Gate 3, and bound
    by the manifest."""
    allocation = CAL.calibration_allocation(_real_calibration_topics())
    assert allocation["passes"] == R.CALIBRATION_FRAME_PASSES
    assert allocation["topics_per_frame"] == R.CALIBRATION_TOPICS_PER_FRAME
    assert allocation["topics_per_frame_per_split"] * 2 == \
        allocation["topics_per_frame"]
    assert allocation["generations_per_rung"] == \
        R.CALIBRATION_GENERATIONS_PER_RUNG
    from dci1v8dev.run import contracts
    declared = {(f.artifact, f.field) for f in contracts.CONTRACT}
    assert (S.STAGE_GATE2, "calibration_allocation") in declared
    assert (S.STAGE_GATE3, "calibration_allocation") in declared


@pytest.mark.slow
def test_the_extension_round_runs_end_to_end_and_its_rungs_are_calibrated(tmp_path):
    """The round the synthetic walk never reached (`calibration_extension: 0`)
    and the real pilot died in. Driven through the production Gate-2 runner
    with an extension rule no family can satisfy, so every spectrum-candidate
    family is reach-deficient on both sides: the round measures reserve
    rungs, each lands in its frame's §13.11 table with a chance column
    measured on that frame's unconstrained cells and a kappa(R|B) on its
    B-solo cell, and Gate 3 evaluates them like any other rung."""
    from dci1v8dev.prescreen.extension import ExtensionRule
    from dci1v8dev.run import calibration as CALIB
    from tests_v8dev import pilot_harness as H

    try:
        H.walk(tmp_path / "ext", stop_after=S.STAGE_GATE1)
    except H.WalkStopped as stopped:
        state = stopped.state
    else:                                                    # pragma: no cover
        raise AssertionError("the walk did not stop at GATE_1_INSTRUMENT")
    tree = state["tree"]
    outcome = CALIB.run_gate2(
        tree, producing_commit=state["commit"], environment_digest="synthetic",
        bank=state["bank"], generate=H.scripted_generate, topic_limit=96)
    g2 = outcome.payload
    measured = g2["extension"]["measured"]
    assert not measured, "the default rule should reach both offsets here"

    # ... and with a rule nothing can reach, the round fires. A second root,
    # because a stage record is write-once.
    try:
        H.walk(tmp_path / "ext2", stop_after=S.STAGE_GATE1)
    except H.WalkStopped as stopped:
        state = stopped.state
    tree = state["tree"]
    g2 = CALIB.gate2_payload(
        tree, producing_commit=state["commit"],
        second_pass_record=state["payloads"][S.STAGE_SECOND_PASS],
        regime_record=state["payloads"][S.STAGE_REGIME], bank=state["bank"],
        generate=H.scripted_generate, topic_limit=96,
        extension_rule=ExtensionRule(d_below=0.9, d_above=0.9))
    measured = g2["extension"]["measured"]
    assert measured, g2["extension"]["plan_by_frame"]
    declared = set(g2["reserve_instances_declared_on_the_grids"]["labels"])
    assert set(measured) <= declared, sorted(set(measured) - declared)
    seen = 0
    for w in g2["supported_frames"]:
        table = {f"{r['kind']}:{r['severity']}": r
                 for r in g2["by_frame"][str(w)]["calibration_rows"]["pooled"]}
        withheld = {f"{r['kind']}:{r['severity']}"
                    for r in g2["by_frame"][str(w)]["calibration_rows_withheld"]["pooled"]}
        for label in measured:
            assert label in table or label in withheld, (w, label)
            if label not in table:
                continue
            row = table[label]
            seen += 1
            assert row["chance_compliance"] is not None
            assert row["kappa_under_b"] is not None, (w, label)
            assert row["kappa_under_b_source"]["m_star"] == g2["by_frame"][str(w)]["m_star"]
            assert row["n_topics"] == g2["calibration_allocation"][
                "topics_per_frame"] == (
                len(g2["calibration_topic_ids"])
                * R.CALIBRATION_FRAME_PASSES // C.N_WORDINGS)
            assert row["per_topic_solo"]
    assert seen, "no extension rung reached a frame's table"


# ------------------------------------------------------------ 15 (slow)
@pytest.mark.slow
def test_a_world_with_genuine_frame_effects_gives_frame_specific_selections(tmp_path):
    """The synthetic lifecycle with a generator that makes frame 2 read A
    and MK1 as harder and frame 3 read B as harder: the frames' operating
    points and reference sets differ, every frame is calibrated on its own
    rows, and the record keeps them apart."""
    from tests_v8dev import pilot_harness as H
    effects = {"A": {2: 0.75}, "MK1": {2: 0.60}, "MK2": {1: 0.70}, "B": {3: 0.85}}
    walked = H.walk(tmp_path / "fx", generate=H.frame_effect_generate(effects))
    g2 = walked["payloads"][S.STAGE_GATE2]
    g3 = walked["payloads"][S.STAGE_GATE3]
    rp = walked["payloads"][S.STAGE_REPORT]
    assert g2["supported_frames"], g2["unsupported_frames"]
    curves = {w: g2["by_frame"][str(w)]["solo_curves"]["A"] for w in S.FRAMES}
    hard_a = [q for q in map(str, C.TARGET_GRID) if curves[2][q] < curves[0][q] - 0.10]
    assert hard_a, curves
    b_curves = {w: g2["by_frame"][str(w)]["solo_curves"]["B"] for w in S.FRAMES}
    assert any(b_curves[3][m] < b_curves[0][m] - 0.05 for m in map(str, C.FOCAL_GRID)), b_curves
    if 2 in g2["supported_frames"] and 0 in g2["supported_frames"]:
        t2 = {f"{r['kind']}:{r['severity']}": r["solo_compliance"]
              for r in g2["by_frame"]["2"]["calibration_rows"]["pooled"]}
        t0 = {f"{r['kind']}:{r['severity']}": r["solo_compliance"]
              for r in g2["by_frame"]["0"]["calibration_rows"]["pooled"]}
        mk1 = [l for l in t2 if l.startswith("MK1:") and l in t0]
        assert mk1 and sum(t2[l] for l in mk1) < sum(t0[l] for l in mk1)
    states = {w: g3["frame_states"][str(w)]["state"] for w in S.FRAMES}
    assert all(s in S.FRAME_STATES for s in states.values())
    sel = {w: (g3["by_frame"][str(w)]["core_references"],
               [p["candidate"] for p in g3["by_frame"][str(w)]["spectrum_selection"]["points"]])
           for w in g2["supported_frames"]}
    assert len({json.dumps(v, sort_keys=True) for v in sel.values()}) >= 2, sel
    assert set(rp["criteria"]["REFERENCE_SURVIVAL"]["by_frame"]) == \
        {str(w) for w in g2["supported_frames"]}


# ------------------------------------------------------------------------
# The per-model allocation (rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL,
# CHANGES_SCIENTIFIC.md 2026-08-31): four passes for qwen3-4b, 192 topics
# per frame at the topic ceiling, every other model unchanged at two. The
# tests above pin the default; these pin the override and the ceiling.
# ------------------------------------------------------------------------
def _laid_out(model_key):
    """The blocks Gate 2 would build for this model, by frame."""
    topics = _real_calibration_topics()
    built = CAL.calibration_blocks(topics, "g2grid-A", model_key=model_key)
    by_frame: dict[int, list[str]] = {}
    for block in built:
        by_frame.setdefault(block.index % C.N_WORDINGS, []).append(block.topic_id)
    return built, by_frame


def test_qwen3_4b_is_calibrated_on_every_calibration_topic_in_every_frame():
    """Contract 1 and 4: the model the researcher raised gets all
    ``N_CALIBRATION`` distinct topics under each of the four frames, and all
    four frame identities survive."""
    assert R.calibration_frame_offsets(MODEL) == (0, 1, 2, 3)
    assert R.calibration_passes(MODEL) == 4
    built, by_frame = _laid_out(MODEL)
    assert len(built) == C.N_CALIBRATION * 4
    assert sorted(by_frame) == list(S.FRAMES)
    for frame, seen in by_frame.items():
        assert len(set(seen)) == R.calibration_topics_per_frame(MODEL) \
            == C.N_CALIBRATION == 192, frame
    # every topic under every frame: that is what the ceiling means
    frames_of_topic: dict[str, set[int]] = {}
    for block in built:
        frames_of_topic.setdefault(block.topic_id, set()).add(
            block.index % C.N_WORDINGS)
    assert len(frames_of_topic) == C.N_CALIBRATION
    assert all(v == set(S.FRAMES) for v in frames_of_topic.values())


def test_qwen3_4b_has_ninety_six_topics_in_each_registered_split_per_frame():
    """Contract 2 and 3: §13.7's two splits stay balanced at the raised
    allocation and no topic recurs inside a frame --- if one did, the frame's
    per-topic vector would count it twice and every standard error formed
    from it would be wrong."""
    _built, by_frame = _laid_out(MODEL)
    for frame, seen in by_frame.items():
        assert len(seen) == len(set(seen)), f"frame {frame} repeats a topic"
        a = sum(1 for t in seen if t.startswith("a-"))
        b = sum(1 for t in seen if t.startswith("b-"))
        assert a == b == R.calibration_topics_per_frame_per_split(MODEL) \
            == C.N_CALIBRATION_A == 96, frame


def test_the_frame_invariant_holds_across_all_four_passes():
    """Contract 5's precondition: ``frame == block_index % N_WORDINGS`` still
    holds on every row of every pass, so ``execute.frame_of_block`` and
    ``prompt_cell``'s frame assertion keep agreeing at four passes as they do
    at two, and the block ids stay disjoint."""
    topics = _real_calibration_topics()
    built = CAL.calibration_blocks(topics, "g2cand", model_key=MODEL)
    assert len({b.block_id for b in built}) == len({b.index for b in built}) \
        == len(built)
    n = len(topics)
    for pass_index, offset in enumerate(R.calibration_frame_offsets(MODEL)):
        chunk = built[pass_index * n:(pass_index + 1) * n]
        assert len(chunk) == n
        for position, block in enumerate(chunk):
            expected = (position + offset) % C.N_WORDINGS
            assert block.index % C.N_WORDINGS == expected
            assert frame_of_block({"block_index": block.index}) == expected
            assert frame_of_block({"block_id": block.block_id}) == expected


def test_four_passes_is_the_ceiling_and_a_repeated_offset_is_refused():
    """192 topics per frame is the bank's whole calibration allocation: a
    fifth pass would have to repeat an offset, and ``rules`` refuses that
    because the repeat would be counted as a second topic."""
    assert R.CALIBRATION_MAX_PASSES == C.N_WORDINGS == 4
    assert R.CALIBRATION_MAX_TOPICS_PER_FRAME == C.N_CALIBRATION
    assert R.calibration_topics_per_frame(MODEL) == R.CALIBRATION_MAX_TOPICS_PER_FRAME
    with pytest.raises(AssertionError, match="distinct modulo"):
        R._assert_offsets((0, 1, 2, 3, 0), "a fifth pass")
    with pytest.raises(AssertionError, match="distinct modulo"):
        R._assert_offsets((0, 4), "the same frame twice")


def test_every_other_model_keeps_the_two_pass_allocation():
    """The override is per model. A model absent from the table runs at the
    registered default, so r8's meaning --- and any later run of those two
    models --- is untouched by this amendment."""
    for other in ("qwen3-4b-instruct-2507", "gemma-3n-e2b-it", "unknown-model"):
        assert R.calibration_frame_offsets(other) == R.CALIBRATION_FRAME_OFFSETS
        assert R.calibration_topics_per_frame(other) == 96
        assert R.calibration_topics_per_frame_per_split(other) == 48
    assert R.calibration_frame_offsets(None) == R.CALIBRATION_FRAME_OFFSETS
    # and the module constants are still the default, for the model-free paths
    assert R.CALIBRATION_TOPICS_PER_FRAME == 96
    assert S.CALIBRATION_TOPICS_PER_FRAME == 96


def test_the_allocation_record_states_the_model_and_the_ceiling():
    """Contract 8 and 9: the Gate-2 block a run writes says which allocation
    it used, whether that was the default, and what it costs --- so a reader
    of the record never has to guess which design produced the numbers."""
    topics = _real_calibration_topics()
    default = CAL.calibration_allocation(topics)
    raised = CAL.calibration_allocation(topics, model_key=MODEL)
    assert default["passes"] == 2 and default["topics_per_frame"] == 96
    assert default["is_default_allocation"] and not default["at_topic_ceiling"]
    assert raised["model_key"] == MODEL
    assert raised["passes"] == 4
    assert raised["frame_offsets"] == [0, 1, 2, 3]
    assert raised["topics_per_frame"] == 192
    assert raised["topics_per_frame_per_split"] == 96
    assert raised["blocks_per_run"] == 768
    assert raised["at_topic_ceiling"] is True
    assert raised["is_default_allocation"] is False
    assert raised["default_frame_offsets"] == list(R.CALIBRATION_FRAME_OFFSETS)
    assert raised["generations_per_rung"] == C.N_CALIBRATION * C.M_CAL * 4 \
        == R.calibration_generations_per_rung(MODEL) == 3072
    assert raised["generations_per_rung"] == 2 * default["generations_per_rung"]


def test_the_manifest_binds_every_models_allocation():
    """Contract 8: the signed manifest states, per model, the allocation that
    model will be measured at — the override is registered, not implicit."""
    from dci1v8dev.run import manifest as MF
    ctx = synthetic_context("alloc-manifest")
    built = MF.build_manifest(ctx, producing_commit="0" * 40,
                              repo_root=pathlib.Path(__file__).resolve().parents[2])
    alloc = built["design"]["calibration_allocation"]
    assert alloc["max_passes"] == 4 and alloc["max_topics_per_frame"] == 192
    assert alloc["default_frame_offsets"] == list(R.CALIBRATION_FRAME_OFFSETS)
    # every field naming a single number says it is the *default*, so no
    # reader can take the study-level value for the model's own
    assert alloc["default_topics_per_frame"] == 96
    sizes = built["design"]["sample_sizes"]
    assert sizes["calibration_topics_per_frame_default"] == 96
    assert sizes["calibration_frame_passes_default"] == 2
    assert not any(k in sizes for k in ("calibration_topics_per_frame",
                                        "calibration_frame_passes"))
    by_model = alloc["by_model"]
    assert by_model[MODEL] == {
        "frame_offsets": [0, 1, 2, 3], "passes": 4, "topics_per_frame": 192,
        "topics_per_frame_per_split": 96, "generations_per_rung": 3072,
        "is_default": False}
    for other in ("qwen3-4b-instruct-2507", "gemma-3n-e2b-it"):
        if other in by_model:
            assert by_model[other]["passes"] == 2
            assert by_model[other]["topics_per_frame"] == 96
            assert by_model[other]["is_default"] is True


def test_the_realised_allocation_assertion_moves_with_the_model():
    """Contract 9: ``assert_allocation_realised`` is run against the
    *model's* allocation, so a qwen3-4b run that produced only 96 topics per
    frame would be refused rather than recorded as if it were the design."""
    grid, _cand = rows_for({w: _default_rates() for w in S.FRAMES},
                           topics_per_split=24, draws=1)
    by_frame = {w: rows_of_frame(grid, w) for w in S.FRAMES}
    two_pass = 48 * R.CALIBRATION_FRAME_PASSES // C.N_WORDINGS
    CAL.assert_allocation_realised(by_frame,
                                   expected_topics_per_frame=two_pass,
                                   where="test")
    # the same rows read against a four-pass expectation are refused
    with pytest.raises(ProtocolError, match="distinct topics"):
        CAL.assert_allocation_realised(by_frame,
                                       expected_topics_per_frame=two_pass * 2,
                                       where="test")


def test_the_raised_allocation_reaches_the_estimator_that_forms_the_coordinate(
        monkeypatch):
    """The point of the amendment: four passes must put twice as many
    per-topic values into each frame's vector as two do, because that vector
    is what SE(ι) --- and therefore `V_coord` and §13.7's bootstrap --- is
    formed at. Measured, not assumed."""
    from dci1v8dev.spectrum.validity import _se_iota
    from dci1v7.stages.calibration_table import load_calibration_table
    rates = {w: _default_rates() for w in S.FRAMES}

    def vectors(offsets):
        grid, cand = rows_for(rates, topics_per_split=24, draws=2,
                              offsets=offsets)
        result = _frames(grid, cand)
        block = result["by_frame"][result["supported"][0]]
        return {f"{r['kind']}:{r['severity']}": r
                for r in block["calibration_rows"]["pooled"]}

    two, four = vectors((0, 2)), vectors((0, 1, 2, 3))
    shared = sorted(set(two) & set(four))
    assert shared
    for label in shared:
        assert len(two[label]["per_topic_solo"]) == two[label]["n_topics"] == 24
        assert len(four[label]["per_topic_solo"]) == four[label]["n_topics"] == 48
    # and the standard error `V_coord` and §13.7's bootstrap are formed at
    # falls by about the sqrt(2) the design predicts
    def _ses(rows):
        table = load_calibration_table(
            list(rows.values()), model_key=MODEL,
            m_star=int(rows[next(iter(rows))]["kappa_under_b_source"]["m_star"]),
            split="pooled")
        return {r.label: _se_iota(r) for r in table}

    se_two, se_four = _ses(two), _ses(four)
    ratios = [se_two[l] / se_four[l] for l in shared
              if se_two.get(l) and se_four.get(l)]
    assert ratios
    assert 1.2 < sum(ratios) / len(ratios) < 1.7, ratios


@pytest.mark.slow
def test_the_four_pass_allocation_walks_the_whole_lifecycle(tmp_path):
    """Contracts 6, 7, 9 and 10 end to end: the nine-stage lifecycle run for
    ``qwen3-4b`` measures every frame on all 192 calibration topics, asserts
    that on the rows it actually generated, keeps the frame dimension through
    Gate 3 and the report, agrees with its own generation accounting, and
    still offers no composed cell."""
    from tests_v8dev import pilot_harness as H
    walked = H.walk(tmp_path / "four", model_key=MODEL)
    g2 = walked["payloads"][S.STAGE_GATE2]
    g3 = walked["payloads"][S.STAGE_GATE3]
    rp = walked["payloads"][S.STAGE_REPORT]

    alloc = g2["calibration_allocation"]
    assert alloc["model_key"] == MODEL
    assert alloc["passes"] == 4 and alloc["frame_offsets"] == [0, 1, 2, 3]
    assert alloc["at_topic_ceiling"] is True
    assert alloc["is_default_allocation"] is False
    # the *realised* allocation, asserted on the generated rows, per run
    n_expected = alloc["topics_per_frame"]
    per_split = alloc["topics_per_frame_per_split"]
    assert n_expected == 2 * per_split
    for where, realised in alloc["realised"].items():
        for frame, seen in realised.items():
            assert seen["n_topics"] == n_expected, (where, frame)
            assert set(seen["by_split"].values()) == {per_split}, (where, frame)
    # the frame dimension survives, and Gate 3 carries the allocation forward
    assert g3["calibration_allocation"]["passes"] == 4
    assert set(g3["frame_states"]) == {str(w) for w in S.FRAMES}
    # every generated row scored, and the accounting matches the four passes
    assert rp["generations"]["calibration_passes"] == 4
    n_blocks = len(g2["calibration_topic_ids"]) * 4
    assert rp["generations"]["calibration_blocks_per_run"] == n_blocks
    for block in g2["row_accounting"].values():
        assert block["n_scored"] == block.get("n_rows", block["n_scored"])
    # the second pass's own budget statement is scoped to *this* model's
    # allocation, so the plan and the realised Gate-2 candidate count agree
    sp = walked["payloads"][S.STAGE_SECOND_PASS]
    per_rung = sp["retention"]["per_rung_calibration_generations"]
    assert per_rung == R.calibration_generations_per_rung(MODEL)
    assert per_rung == 2 * R.CALIBRATION_GENERATIONS_PER_RUNG
    assert sp["retention"]["config"]["generations_per_rung"] == per_rung
    assert sp["retention"]["calibration_cost_generations"] == \
        sp["retention"]["n_forwarded"] * per_rung
    # and no composed cell exists anywhere before the freeze
    for payload in (g2, g3, rp):
        assert payload["no_composed_cells"] is True


def test_the_report_refuses_a_gate2_record_with_no_pass_count():
    """The generation total is derived from the record's own pass count, and
    `calibration_allocation` is a required Gate-2 contract field. A record
    without it is malformed, not old: silently reading one pass would
    under-count the run's generations by the pass factor, which is the exact
    class of stale number this accounting exists to catch."""
    gate2 = {"grids": {"A": [1], "B": [1], "B_extension": [],
                       "focal_extension_measured": False},
             "calibration_topic_ids": ["t0", "t1"],
             "calibration_population": {"n_measured": 1},
             "extension": {"n_rows": 0}}
    regime = {"n_rungs_measured": 1,
              "cap_selection": {"truncation_by_cap": {}}}
    args = dict(regime=regime, second_pass={"cost_generations": 0},
                gate0={"rows": 0})
    with pytest.raises(ProtocolError, match="calibration_allocation"):
        RPT._generations(gate2=gate2, **args)
    # with the block present it derives the count from the pass factor
    for passes in (2, 4):
        ok = {**gate2, "calibration_allocation": {"passes": passes}}
        out = RPT._generations(gate2=ok, **args)
        assert out["calibration_passes"] == passes
        assert out["calibration_blocks_per_run"] == 2 * passes


def test_the_realised_allocation_refuses_an_unbalanced_frame():
    """The other half of `assert_allocation_realised`, on the mandatory path
    and previously only exercised through the happy case: §13.7 compares two
    halves, so a frame whose topics do not split evenly is refused even when
    the total is right. A frame short of the count is refused too."""
    grid, _cand = rows_for({w: _default_rates() for w in S.FRAMES},
                           topics_per_split=24, draws=1)
    by_frame = {w: rows_of_frame(grid, w) for w in S.FRAMES}
    expected = _topics_per_frame(topics_per_split=24)
    CAL.assert_allocation_realised(by_frame,
                                   expected_topics_per_frame=expected,
                                   where="test")
    # move one topic across the split boundary: the count is unchanged and
    # the balance is not
    skewed = {w: [dict(r) for r in rows] for w, rows in by_frame.items()}
    victim = sorted({r["topic_id"] for r in skewed[0]
                     if r["topic_split"] == C.CALIBRATION_A})[0]
    for r in skewed[0]:
        if r["topic_id"] == victim:
            r["topic_split"] = C.CALIBRATION_B
    with pytest.raises(ProtocolError, match="two halves"):
        CAL.assert_allocation_realised(skewed,
                                       expected_topics_per_frame=expected,
                                       where="test")
    # and a frame carrying only one split at all
    one_sided = {w: [r for r in rows if r["topic_split"] == C.CALIBRATION_A]
                 for w, rows in by_frame.items()}
    with pytest.raises(ProtocolError):
        CAL.assert_allocation_realised(one_sided,
                                       expected_topics_per_frame=expected,
                                       where="test")


def test_an_empty_pass_list_is_refused():
    """A zero-pass allocation would measure nothing; `rules` refuses it at
    import for the table and here for any caller."""
    with pytest.raises(AssertionError, match="at least one calibration pass"):
        R._assert_offsets((), "no passes")
