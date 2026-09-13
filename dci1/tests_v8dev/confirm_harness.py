"""The confirmatory lifecycle with no model: a composed-aware scripted
generator, a fabricated freeze for the analysis unit test, and the
seven-stage walk on a synthetic pilot root."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v7.protocol import constants as C
from dci1v7.run.gates_run import focal_constraint
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.execute import fake_backend
from dci1v8dev.confirm.membership import constraint_of
from tests_v7 import synthetic_lifecycle as V7


def slots_of_cell(cell_id: str) -> tuple[str, ...]:
    if cell_id == "unconstrained":
        return ()
    if cell_id.startswith("solo:"):
        return (cell_id[5:],)
    return tuple(cell_id[5:].split("+"))


def composed_generate(slot_maps: Mapping[int, Mapping[str, Constraint]]):
    """v7's scripted composer over the frozen slot maps: the stated
    constraints of a cell are resolved through the block's frame."""
    def responder(row: Mapping[str, Any]) -> str:
        frame = int(str(row["block_id"]).rpartition("-")[2]) % C.N_WORDINGS
        slots = slots_of_cell(row["cell_id"])
        present: list[Constraint] = []
        for s in slots:
            if s in slot_maps.get(frame, {}):
                present.append(slot_maps[frame][s])
            else:                                   # a top-up solo:<label>
                kind, _, q = s.rpartition(":")
                present.append(Constraint(kind, int(q), reserve=True))
        return V7._compose(row["row_id"], tuple(present))
    return fake_backend(responder)


def fabricated_frame(frame: int, *, local: bool, spectrum: bool) -> dict[str, Any]:
    """A frozen-frame block of the shape ``freeze.frozen_frames`` writes."""
    core = [{"slot": "R1", "family": "MK1", "severity": 3, "label": "MK1:3"},
            {"slot": "R2", "family": "XC3", "severity": 8, "label": "XC3:8"},
            {"slot": "R3", "family": "MK5", "severity": 3, "label": "MK5:3"}]
    backups = [{"slot": "R4", "family": "MK2", "severity": 3, "label": "MK2:3"},
               {"slot": "R5", "family": "MK4", "severity": 3, "label": "MK4:3"}]
    slot_map = {"A": ["A", 3, {}], "B": ["B", 9, {"extended": False}]}
    arms = ["base"]
    if local:
        arms += ["core", "backup"]
        for r in core + backups:
            slot_map[r["slot"]] = [r["family"], r["severity"], {"reserve": True}]
    points: list[dict[str, Any]] = []
    n_spec = 0
    if spectrum:
        arms.append("spectrum")
        spec = [("MK1", 1, "above"), ("MK1", 6, "below"), ("MK2", 1, "above"),
                ("MK2", 6, "below"), ("MK5", 1, "above"), ("MK5", 6, "below")]
        for i, (fam, q, side) in enumerate(spec):
            slot = f"S{i + 1}"
            slot_map[slot] = [fam, q, {"reserve": True}]
            points.append({"slot": slot, "candidate": f"{fam}:{q}",
                           "family": fam, "iota": 0.5, "side": side,
                           "role": "SPECTRUM", "aliased": False})
        n_spec = len(spec)
    from dci1v8dev.confirm.design import n_cells_for
    from dci1v8dev.confirm.membership import admissible_triples
    return {
        "frame": frame, "state": "LOCAL_AND_SPECTRUM",
        "enters_local": local, "enters_spectrum": spectrum, "arms": arms,
        "cells_per_block": n_cells_for(arms, n_spectrum=n_spec),
        "slot_map": slot_map, "spectrum_points": points,
        "spectrum_aliases": {}, "n_spectrum_slots": n_spec,
        "n_star": 3, "m_star": 9, "iota_a": 0.67, "solo_compliance_b": 0.8,
        "core": core if local else [], "backups": backups if local else [],
        "local_valid_families": ["MK1", "XC3", "MK5", "MK2", "MK4"],
        "identification_statuses": [], "stability": None,
        "reference_sensitivity": ({
            "families": [r["family"] for r in core + backups],
            "admissible_triples": admissible_triples(core + backups)}
            if local else None)}


def fabricated_freeze(frames: Mapping[int, dict[str, Any]], *,
                      blocks_per_frame: int) -> dict[str, Any]:
    return {"design": {"blocks_per_frame": blocks_per_frame, "draws": C.M_DRAWS,
                       "completion_cap": 512,
                       "frames": {str(w): e for w, e in frames.items()},
                       "frames_entering_local": [w for w, e in frames.items()
                                                 if e["enters_local"]],
                       "frames_entering_spectrum": [w for w, e in frames.items()
                                                    if e["enters_spectrum"]]},
            "deviations": [], "estimands": {}, "thresholds": {}}


def slot_maps_of(freeze: Mapping[str, Any]) -> dict[int, dict[str, Constraint]]:
    return {int(w): {s: constraint_of(v) for s, v in e["slot_map"].items()}
            for w, e in freeze["design"]["frames"].items()}


def effect_generate(slot_maps: Mapping[int, Mapping[str, Constraint]], *,
                    spoil_b_under: Mapping[str, float]):
    """The scripted composer with a companion-dependent interference on B:
    in a composed cell that states B and companion slot X, a scripted-
    compliant answer has B spoiled (one over-long word appended) with
    probability ``spoil_b_under[X]``, by a hash of the row id. So
    P(B | B+A) < P(B | B+R) when A's spoil rate is the larger, and
    Delta_R is positive in the registered sign (A_HARMS_MORE)."""
    import hashlib
    base = composed_generate(slot_maps)

    def generate(run_dir, plan, rows):
        out = base(run_dir, plan, rows)
        by_id = {r["row_id"]: r for r in rows}
        for produced in out["rows"]:
            row = by_id[produced["row_id"]]
            slots = slots_of_cell(row["cell_id"])
            if len(slots) != 2 or "B" not in slots:
                continue
            other = slots[0] if slots[1] == "B" else slots[1]
            rate = spoil_b_under.get(other)
            if rate is None:
                continue
            digest = hashlib.sha256(f"spoil|{row['row_id']}".encode()).hexdigest()
            if int(digest[:12], 16) / float(16 ** 12) < rate:
                text = produced["final_answer"].rstrip(".")
                produced["final_answer"] = text + " consideration" + "a" * 8 + "."
                produced["raw_generation"] = produced["final_answer"]
        return out
    return generate


def with_iota(frame: Mapping[str, Any], *, core: float = 0.6,
              backups: float = 0.55, iota_a: float | None = None
              ) -> dict[str, Any]:
    """The same frozen frame with difficulty coordinates on its references.

    ``membership.frame_membership`` carries ``iota`` on every core and
    backup entry; ``fabricated_frame`` does not, because most tests do not
    read it. §23's projection audit does, so it is added here rather than
    invented inside the audit.
    """
    out = {k: (list(v) if isinstance(v, list) else v)
           for k, v in frame.items()}
    out["core"] = [{**r, "iota": core} for r in frame["core"]]
    out["backups"] = [{**r, "iota": backups} for r in frame["backups"]]
    if iota_a is not None:
        out["iota_a"] = iota_a
    return out


def with_runner_up(frame: Mapping[str, Any], *, slots: Sequence[str]
                   ) -> dict[str, Any]:
    """The same frozen frame with the runner-up arm for ``slots``.

    The shape ``membership.frame_membership`` writes when a coordinate is
    ``OPERATING_POINT_UNSTABLE``: A2 is A at the runner-up n, B2 is B at the
    runner-up m, and the arm licenses no claim.
    """
    from dci1v8dev.confirm.design import n_cells_for
    out = dict(frame)
    slot_map = dict(frame["slot_map"])
    values: dict[str, int] = {}
    for slot in slots:
        if slot == "A2":
            q = int(frame["n_star"]) + 1
            slot_map["A2"] = ["A", q, {"runner_up": True}]
        elif slot == "B2":
            q = int(frame["m_star"]) + 1
            slot_map["B2"] = ["B", q, {"runner_up": True,
                                       "extended": q in C.FOCAL_EXTENSION}]
        else:
            raise AssertionError(f"{slot!r} is not a runner-up slot")
        values[slot] = q
    arms = list(frame["arms"]) + ["runner_up"]
    out.update({
        "arms": arms, "slot_map": slot_map,
        "runner_up_slots": list(slots),
        "runner_up": {"slots": list(slots), "values": values,
                      "status": "OPERATING_POINT_UNSTABLE",
                      "rule": "sensitivity only; the frozen n*(f), m*(f) stand"},
        "cells_per_block": n_cells_for(
            arms, n_spectrum=int(frame["n_spectrum_slots"]),
            runner_up=tuple(slots))})
    return out


def confirmatory_rows(frames: Mapping[int, Mapping[str, Any]], *,
                      root: Path, blocks: int, generate=None,
                      model_key: str = "qwen3-4b") -> list[dict[str, Any]]:
    """One scored confirmatory row set for every frame of a fabricated
    freeze: the frame's cells on the first ``blocks`` confirmatory topics,
    through the production planner, prompt renderer and scorer."""
    from dci1v7.topics.bank import load_bank
    from dci1v8dev.confirm.design import FrameBlock, design_cells
    from dci1v8dev.confirm.execute import generate_and_score, prompt_cell

    slot_maps = {int(w): {s: constraint_of(v) for s, v in e["slot_map"].items()}
                 for w, e in frames.items()}
    if generate is None:
        generate = composed_generate(slot_maps)
    topics = list(load_bank().topics("confirmatory"))[:blocks]
    by_id = {t["topic_id"]: t for t in topics}
    rows: list[dict[str, Any]] = []
    for w, e in frames.items():
        fb = [FrameBlock(position=i, frame=int(w), topic_id=t["topic_id"],
                         area=t["area"]) for i, t in enumerate(topics)]
        cells = design_cells(fb, e["arms"], n_spectrum=e["n_spectrum_slots"],
                             runner_up=tuple(e.get("runner_up_slots") or ()))
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_maps[int(w)])
                   for c in cells]
        rows += generate_and_score(
            model_key, prompts, stage=L.STAGE_GENERATION, cap=512, device=0,
            run_dir=Path(root) / f"frame-{w}",
            instances=tuple(dict.fromkeys(slot_maps[int(w)].values())),
            slot_map=slot_maps[int(w)], study_id="dci1v8-synthetic",
            protocol_identity={"test": True}, generate=generate,
            composed_licensed=True)
    return rows
