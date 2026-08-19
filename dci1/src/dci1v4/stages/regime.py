"""Stage 3, REGIME_SCREEN: completion cap and the dense ladder screen (§12.1,
§12.2).

Two things happen here and their order matters: the cap is selected first,
because every later rate is measured under it, and the ladder screen then runs
at the selected cap.

**The cap-selection set contains all three loads (§12.1, T-7).** v3's
no-constraint arm truncated in 322 of 384 and 333 of 384 responses at its
selected cap, so its accidental-compliance base rate was measured on mostly
truncated text. §12.1 answers that by requiring zero-, one- and two-constraint
prompts in the cap set, by selecting on the truncation rate over the
constrained prompts only, and by recording the zero-constraint rate
separately. All three are implemented here.

The dense ladder screen measures the full n grid, the full m grid and all 94
ladder severities on the 24 pre-screen topics at one draw per cell — 2,544
generations — and writes the shortlist of at most three severities per family
nearest A's pre-screen solo compliance. **The shortlist is written before Gate
2 generates anything.**
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from dci1v4.design.cells import Cell, Constituent
from dci1v4.design.prompts import prompt_hash, render
from dci1v4.errors import ProtocolError, TerminalStatus
from dci1v4.protocol import constants as C
from dci1v4.protocol.wordings import wording
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    TARGET_GRID,
)

#: Fixture severities for the cap-selection prompts. They exercise the loads
#: §12.1 requires and cannot become calibration evidence: cap selection happens
#: before n* and m* exist, and no rate measured here enters Gate 2.
CAP_FIXTURE_N = 3
CAP_FIXTURE_M = 8


def _screen_cell(stage: str, topic: dict[str, Any], *, cell_type: str,
                 constituents: tuple[Constituent, ...], draws: int) -> Cell:
    """A screen cell is an ordinary v4 cell whose block is its own topic.

    Reusing ``design.cells.Cell`` keeps the screen on exactly the same row
    schema, seed derivation and integrity path as every other stage; a
    parallel cell type would be a second place for those to drift.
    """
    prompt = render(topic["question"], [c.text for c in constituents])
    return Cell(cell_id=f"{stage}:{topic['topic_id']}:{cell_type}",
                stage=stage, cell_type=cell_type, topic_id=topic["topic_id"],
                block_id=topic["topic_id"], block_index=None,
                constituents=constituents, order=None, prompt=prompt,
                prompt_hash=prompt_hash(prompt), draws=draws)


def cap_selection_cells(prescreen_topics: Sequence[dict[str, Any]]
                        ) -> list[Cell]:
    """The §12.1 subject-balanced 96-prompt set, at loads zero, one and two.

    Four prompts per pre-screen topic: one with no constraint, one with A, one
    with B, and one with both. §12.1 requires all three loads to be present,
    requires the selection to read the constrained prompts only, and requires
    the zero-constraint truncation rate to be recorded separately — the three
    things v3's cap selection did not do, and the reason its no-constraint arm
    was measured on mostly truncated text (T-7).
    """
    cells: list[Cell] = []
    for position, topic in enumerate(prescreen_topics):
        w = position % C.N_WORDINGS
        target = Constituent("A", "A", CAP_FIXTURE_N, 1, w,
                             wording("A", w, CAP_FIXTURE_N))
        focal = Constituent("B", "B", CAP_FIXTURE_M, 1, w,
                            wording("B", w, CAP_FIXTURE_M))
        focal_second = Constituent("B", "B", CAP_FIXTURE_M, 2, w,
                                   wording("B", w, CAP_FIXTURE_M))
        for cell_type, constituents in (("cap:load0", ()),
                                        ("cap:load1:A", (target,)),
                                        ("cap:load1:B", (focal,)),
                                        ("cap:load2:A+B",
                                         (target, focal_second))):
            cells.append(_screen_cell("prescreen", topic,
                                      cell_type=cell_type,
                                      constituents=constituents, draws=1))
    if len(cells) != C.CAP_SELECTION_PROMPTS:
        raise ProtocolError(f"the cap-selection set holds {len(cells)} "
                            f"prompts, not {C.CAP_SELECTION_PROMPTS}")
    loads = {c.load for c in cells}
    if loads != set(C.CAP_SET_LOADS):
        raise ProtocolError(f"the cap-selection set carries loads "
                            f"{sorted(loads)}, and §12.1 requires "
                            f"{list(C.CAP_SET_LOADS)}")
    return cells


def select_cap(truncation_by_cap: dict[int, dict[str, float]]) -> dict[str, Any]:
    """§12.1: the smallest cap whose truncation over the CONSTRAINED prompts
    is at most 0.10. The zero-constraint rate is recorded separately."""
    table = []
    for cap in C.COMPLETION_CAPS:
        rates = truncation_by_cap.get(cap)
        if rates is None:
            raise ProtocolError(f"no truncation measured at cap {cap}")
        table.append({"cap": cap,
                      "constrained_truncation": rates["constrained"],
                      "zero_constraint_truncation": rates["zero_constraint"],
                      "qualifies":
                          rates["constrained"] <= C.CAP_TRUNCATION_MAX})
    qualifying = [row for row in table if row["qualifies"]]
    if not qualifying:
        raise TerminalStatus("RESPONSE_LENGTH_INCOMPATIBLE", {
            "status": "RESPONSE_LENGTH_INCOMPATIBLE", "gate": C.STAGE_REGIME,
            "criterion": "truncation over one- and two-constraint prompts",
            "threshold": C.CAP_TRUNCATION_MAX,
            "observed": {row["cap"]: row["constrained_truncation"]
                         for row in table},
            "curves": table, "artifact_hashes": {},
            "strongest_permissible_statement":
                "no registered completion cap keeps truncation at or below "
                "the registered maximum on constrained prompts",
            "estimands_unanswerable": "all"})
    chosen = min(qualifying, key=lambda row: row["cap"])
    return {"selected_cap": chosen["cap"], "table": table,
            "zero_constraint_truncation":
                chosen["zero_constraint_truncation"],
            "note": ("the zero-constraint truncation rate is recorded "
                     "separately and is not part of the selection criterion "
                     "(§12.1)")}


def ladder_kinds() -> list[tuple[str, int]]:
    """The full n grid, the full m grid, and all 94 ladder severities."""
    kinds: list[tuple[str, int]] = [("A", n) for n in TARGET_GRID]
    kinds += [("B", m) for m in FOCAL_GRID]
    for family, ladder in REFERENCE_LADDERS.items():
        kinds += [(family, q) for q in ladder]
    return kinds


def ladder_screen_cells(prescreen_topics: Sequence[dict[str, Any]]
                        ) -> list[Cell]:
    """§12.2: every registered severity on the 24 pre-screen topics, one draw
    per cell. (8 + 4 + 94) x 24 = 2,544 generations."""
    kinds = ladder_kinds()
    cells: list[Cell] = []
    for position, topic in enumerate(prescreen_topics):
        for offset, (kind, severity) in enumerate(kinds):
            w = (position + offset) % C.N_WORDINGS
            constituent = Constituent(kind, kind, severity, 1, w,
                                      wording(kind, w, severity))
            cells.append(_screen_cell(
                "prescreen", topic, cell_type=f"ladder:{kind}:{severity}",
                constituents=(constituent,), draws=C.LADDER_SCREEN_DRAWS))
    expected = len(kinds) * len(prescreen_topics)
    if len(cells) != expected:
        raise ProtocolError(f"{len(cells)} ladder cells, expected {expected}")
    return cells


def shortlist(solo_compliance: dict[tuple[str, int], float],
              a_compliance: float) -> dict[str, list[dict[str, Any]]]:
    """§12.2: at most three severities per family, nearest A's pre-screen solo
    compliance. Written before Gate 2 generates anything."""
    out: dict[str, list[dict[str, Any]]] = {}
    for family, ladder in REFERENCE_LADDERS.items():
        rungs = []
        for q in ladder:
            value = solo_compliance.get((family, q))
            if value is None:
                continue
            rungs.append({"severity": q, "solo_compliance": value,
                          "distance_from_A": abs(value - a_compliance)})
        rungs.sort(key=lambda r: (r["distance_from_A"], r["severity"]))
        out[family] = rungs[:C.LADDER_SHORTLIST_MAX]
    return out


def regime_screen_payload(*, cap: dict[str, Any],
                          ladder_curves: dict[str, Any],
                          a_prescreen_compliance: float,
                          shortlist_table: dict[str, list[dict[str, Any]]],
                          truncation_by_cell: dict[str, float],
                          screen_dir: Path) -> dict[str, Any]:
    return {
        "outcome": "PASS",
        "completion_cap": cap,
        "ladder_screen": {"curves": ladder_curves,
                          "a_solo_compliance": a_prescreen_compliance,
                          "draws_per_cell": C.LADDER_SCREEN_DRAWS},
        "shortlist": shortlist_table,
        "shortlist_written_before_gate2": True,
        "truncation_by_cell": truncation_by_cell,
        "screen_dir": str(screen_dir),
        "identification_statuses": [],
    }
