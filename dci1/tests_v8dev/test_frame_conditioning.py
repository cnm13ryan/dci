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

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages.calibration_table import FORBIDDEN_CALIBRATION_FIELDS
from dci1v7.verifiers.constraints import Constraint
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
             extension: tuple[str, ...] = ()) -> tuple[list[dict], ...]:
    """Scored rows in the run layer's schema for a two-split calibration on
    ``2 * topics_per_split`` blocks (frame = block index % 4). ``rates_by_frame``
    maps frame -> label -> pass probability when the constraint is stated;
    ``chance`` maps label -> pass probability when it is absent on the
    unconstrained cell. ``outcome_key`` (frame, label, topic_index, draw,
    present) -> key decides the pseudo-random outcome; the default keys by
    the topic's global index, so two frames differ; keying by the topic's
    position within its frame makes frames identical (contract 16)."""
    chance = chance or {}
    instances = ([f"A:{q}" for q in A_GRID] + [f"B:{m}" for m in B_GRID]
                 + list(CANDIDATES) + list(extra_instances))
    grid_rows: list[dict] = []
    cand_rows: list[dict] = []
    ext_rows: list[dict] = []
    outcome_key = outcome_key or (lambda f, label, t, d, present: (f, label, t, d, present))
    n = 0
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        for t in range(topics_per_split):
            block_index = n
            n += 1
            frame = block_index % C.N_WORDINGS
            topic = f"{split}-topic-{t:03d}"
            rates = rates_by_frame[frame]

            def score(label: str, stated: str | None, draw: int) -> dict:
                kind, q = label.rpartition(":")[0], int(label.rpartition(":")[2])
                present = label == stated
                p = rates[label] if present else chance.get(label, 0.0)
                passed = _u(*outcome_key(frame, label, block_index, draw, present),
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
        assert hard["n_topics"] == easy["n_topics"] == 48     # the frame's own topics
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
        assert block["n_topics_a"] == 48
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
    assert row["n_topics"] == C.N_CALIBRATION // C.N_WORDINGS
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
    tree, payloads = state["tree"], state["payloads"]
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
            assert row["n_topics"] == len(g2["calibration_topic_ids"]) // C.N_WORDINGS
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
