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
