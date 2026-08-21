"""Stage 3, `REGIME_SCREEN`: §12.1's cap, §12.2's dense ladder, §12.6's loop.

The stage does three things in order and writes one record:

1. **§12.1 completion cap.** 96 pre-screen prompts at each of three caps; the
   smallest cap whose truncation rate over the one- and two-constraint prompts
   is at most 0.10 is selected and held fixed.
2. **§12.2 dense ladder screen.** At that cap, one draw per cell on the 24
   pre-screen topics: the unconstrained cell, A's full grid, B's grid
   including the conditional extension, and every round-0 ladder severity of
   all twenty families. The unconstrained rows additionally carry a chance
   verdict for every declared instance, which is where kappa comes from.
3. **§12.6 candidate expansion.** The identification-coverage criterion is
   evaluated on that table; while it is short and rounds remain, the frozen
   reserve supplies the next rungs and only those rungs are re-measured. The
   loop stops the moment coverage passes, and the vocabulary is then frozen.

No composed cell is generated here and none is read. The stage is complete
before Gate 1 in the registered order, so the vocabulary Gate 1 certifies is
the vocabulary this stage closes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import fs, store
from dci1v4.models.registry import get_model

from dci1v4r3 import EVIDENCE_DIRNAME
from dci1v4r3.protocol import constants as C
from dci1v4r3.run.execute import (
    EVIDENCE, Cell, cell_rates, generate_and_score, solo_cell,
    unconstrained_cell,
)
from dci1v4r3.stages import cap_probe
from dci1v4r3.stages import library as lib
from dci1v4r3.stages import regime
from dci1v4r3.topics import split_topics
from dci1v4r3.verifiers.constraints import (
    FAMILIES, RESERVES, Constraint, TARGET_GRID, focal_severities,
)

DCI1 = Path(__file__).resolve().parents[3]

STAGE_CAP = "v4r3-cap-selection"
STAGE_LADDER = "v4r3-ladder-screen"

#: §12.1's registered pre-screen prompt set: four prompts per pre-screen
#: topic, deterministic, covering loads 0, 1, 1 and 2. The one- and
#: two-constraint prompts use the **most restrictive** registered severity of
#: each grid, because the cap has to be adequate where the answer is hardest
#: to write, not where it is easiest.
CAP_SET_A_SEVERITY = max(TARGET_GRID)          # n = 8
CAP_SET_B_SEVERITY = min(focal_severities())   # m = 7

__all__ = ["STAGE_CAP", "STAGE_LADDER", "cap_selection_cells", "ladder_cells",
           "select_cap", "difficulty_table_from_rows", "run_regime_screen"]


def cap_selection_cells(topics: Sequence[dict[str, Any]]) -> list[Cell]:
    a = Constraint("A", CAP_SET_A_SEVERITY)
    b = Constraint("B", CAP_SET_B_SEVERITY)
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        index = position % C.N_WORDINGS
        cells.append(unconstrained_cell(topic, arm="cap", prefix="cap"))
        cells.append(solo_cell(topic, a, index, arm="cap", prefix="cap"))
        cells.append(solo_cell(topic, b, index, arm="cap", prefix="cap"))
        from dci1v4r3.run.execute import composed_cell
        cells.append(composed_cell(topic, a, b, (index, index), arm="cap",
                                   prefix="cap"))
    return cells


def ladder_cells(topics: Sequence[dict[str, Any]],
                 rungs: Sequence[tuple[str, int]], *,
                 include_outcomes: bool = True,
                 prefix: str = "ladder") -> list[Cell]:
    """§12.2's cells. ``rungs`` are family severities; the outcome grids and
    the unconstrained cell are added unless this is an expansion round, which
    re-measures only what it admitted."""
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        index = position % C.N_WORDINGS
        if include_outcomes:
            cells.append(unconstrained_cell(topic, arm="load0", prefix=prefix))
            for n in TARGET_GRID:
                cells.append(solo_cell(topic, Constraint("A", n), index,
                                       arm="A", prefix=prefix))
            for m in focal_severities(extended=True):
                cells.append(solo_cell(topic, Constraint("B", m, extended=True),
                                       index, arm="B", prefix=prefix))
        for kind, q in rungs:
            cells.append(solo_cell(topic, Constraint(kind, q, reserve=True),
                                   index, arm=FAMILIES[kind].role,
                                   prefix=prefix))
    return cells


def select_cap(truncation_by_cap: dict[int, dict[str, float]]) -> dict[str, Any]:
    """§12.1: the smallest qualifying cap, or RESPONSE_LENGTH_INCOMPATIBLE."""
    for cap in C.COMPLETION_CAPS:
        entry = truncation_by_cap.get(cap)
        if entry is None:
            continue
        if entry["constrained"] <= C.CAP_TRUNCATION_MAX:
            return {"selected_cap": cap, "table": truncation_by_cap,
                    "criterion": "truncation over load 1 and 2 prompts "
                                 f"<= {C.CAP_TRUNCATION_MAX}"}
    return {"selected_cap": None, "table": truncation_by_cap,
            "status": "RESPONSE_LENGTH_INCOMPATIBLE"}


def difficulty_table_from_rows(rows: Sequence[dict[str, Any]],
                               instances: Sequence[tuple[str, int]]
                               ) -> dict[str, dict[str, Any]]:
    """§12.2's first output: solo, kappa and iota for every measured instance.

    Solo compliance is read from the instance's own solo cell; chance
    compliance from the load-0 rows, where the same verifier scored the same
    responses without the instruction being present.
    """
    table: dict[str, dict[str, Any]] = {}
    for kind, severity in instances:
        solo = cell_rates(rows, kind=kind, severity=severity, present=True)
        if kind in ("A", "B"):
            # A and B are outcome constraints; kappa is still measured for
            # them, on the same load-0 rows, and reported.
            chance = cell_rates(rows, kind=kind, severity=severity,
                                present=False)
        else:
            chance = cell_rates(rows, kind=kind, severity=severity,
                                present=False)
        entry = {
            "kind": kind, "severity": severity,
            "solo": solo["compliance"], "chance": chance["compliance"],
            "solo_vacuity": solo["vacuity"],
            "chance_vacuity": chance["vacuity"],
            "graded_mean": solo["graded_mean"],
            "median_words": solo["median_words"],
            "truncation": solo["truncation"],
            "n_topics": solo["n_topics"],
        }
        entry["lift"] = entry["solo"] - entry["chance"]
        if entry["chance"] < C.CHANCE_DEGENERACY_MAX:
            entry["iota"] = ((entry["solo"] - entry["chance"])
                             / (1.0 - entry["chance"]))
        else:
            entry["iota"] = None
        table[f"{kind}:{severity}"] = entry
    return table


def _library_rows(table: dict[str, dict[str, Any]], *, round_of: dict[str, int]
                  ) -> list[lib.LibraryRow]:
    rows = []
    for label, entry in table.items():
        if entry["kind"] not in FAMILIES:
            continue
        rows.append(lib.LibraryRow(
            kind=entry["kind"], severity=entry["severity"],
            solo_compliance=entry["solo"],
            chance_compliance=min(entry["chance"], 0.9899),
            solo_vacuity=entry["solo_vacuity"],
            admitted_in_round=round_of.get(label, 0),
            median_words=entry["median_words"],
            graded_mean=entry["graded_mean"]))
    return rows


def _mirror(model_key: str, out_dir: Path) -> None:
    """§26: every stage record gets a durable copy the moment it is written.

    ``evidence/`` is gitignored by this repository's own design -- a run must
    never dirty the worktree -- so the durable mirror is not a convenience, it
    is the only second copy the study has. Replicating at write time rather
    than at the end of a session means an interrupted run still leaves one.
    """
    durable = (DCI1 / "durable_root" / EVIDENCE_DIRNAME / model_key
               / C.STAGE_REGIME)
    records = out_dir / "records"
    records.mkdir(parents=True, exist_ok=True)
    for name in ("regime_record.json",):
        source = out_dir / name
        if source.exists():
            (records / name).write_bytes(source.read_bytes())
    store.replicate(records, durable)
    store.assert_replicated(records, durable)


def run_regime_screen(model_key: str, *, device: int, cap: int | None = None,
                      limit: int | None = None, generate=None
                      ) -> dict[str, Any]:
    """The whole stage for one model. Returns the record it writes."""
    spec = get_model(model_key)
    topics = split_topics()["prescreen"]
    out_dir = EVIDENCE / model_key / C.STAGE_REGIME
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------- §12.1 the cap
    if cap is None:
        cap_cells = cap_selection_cells(topics)
        truncation: dict[int, dict[str, float]] = {}
        for candidate in C.COMPLETION_CAPS:
            rows = generate_and_score(
                model_key, cap_cells, stage=f"{STAGE_CAP}-{candidate}",
                cap=candidate, draws=1, device=device,
                run_dir=out_dir / "backend_runs" / f"cap{candidate}",
                limit=limit, generate=generate)
            # §12.1's probe includes composed A+B prompts, so its scored rows
            # carry per-constituent verdicts. Project them onto the three
            # registered fields *here*, before anything else can see them:
            # the cap decision must not be reachable from a composed outcome
            # and neither must anything downstream of it (§12.5, §13.9).
            truncation[candidate] = cap_probe.truncation_by_load(
                cap_probe.restrict(rows))
        # Every cap is generated, not only those up to the first that
        # qualifies: §12.1 registers the whole table as the diagnostic, and a
        # loop that stopped early would report a cap as unmeasured rather than
        # as measured and not needed.
        chosen = select_cap(truncation)
        # The restricted artifact is durable and is what a later stage reads;
        # the raw probe rows stay in place for provenance and are never
        # aggregated again.
        fs.write_json(
            EVIDENCE / model_key / "cap_probe_truncation.json",
            cap_probe.cap_probe_artifact(
                truncation, model_key=model_key,
                selected_cap=chosen["selected_cap"]))
        if chosen["selected_cap"] is None:
            record = {"stage": C.STAGE_REGIME, "model_key": model_key,
                      "outcome": "TERMINAL",
                      "status": "RESPONSE_LENGTH_INCOMPATIBLE",
                      "completion_cap": chosen,
                      "terminal_sentence": C.TERMINAL_SENTENCE}
            fs.write_json(out_dir / "regime_record.json", record)
            _mirror(model_key, out_dir)
            return record
        cap = chosen["selected_cap"]
    else:
        chosen = {"selected_cap": cap, "table": {},
                  "criterion": "supplied by the caller and recorded as such"}

    # -------------------------------------------- §12.2 the dense ladder
    round_zero = lib.round_zero_plan()
    declared = [(k, q) for k, q in round_zero]
    cells = ladder_cells(topics, round_zero)
    # §25's chance verdicts cover the **whole declared range**, not only the
    # round-0 rungs: a rung §12.6 admits in round 1 needs a kappa measured on
    # the same load-0 responses as every other rung, and re-running the
    # unconstrained cell later would measure it on different draws.
    absent = (tuple(Constraint("A", n) for n in TARGET_GRID)
              + tuple(Constraint("B", m, extended=True)
                      for m in focal_severities(extended=True))
              + tuple(Constraint(kind, q, reserve=True)
                      for kind in FAMILIES for q in RESERVES[kind]))
    rows = generate_and_score(
        model_key, cells, stage=STAGE_LADDER, cap=cap, draws=C.LADDER_SCREEN_DRAWS,
        device=device, run_dir=out_dir / "backend_runs" / "ladder",
        absent=absent, limit=limit, generate=generate)

    instances = ([("A", n) for n in TARGET_GRID]
                 + [("B", m) for m in focal_severities(extended=True)]
                 + declared)
    table = difficulty_table_from_rows(rows, instances)
    round_of: dict[str, int] = {}

    # ------------------------------------------------ §12.6 the expansion
    iota_a_entries = [table[f"A:{n}"] for n in TARGET_GRID
                      if table[f"A:{n}"]["iota"] is not None]
    anchor = min(iota_a_entries,
                 key=lambda e: (abs(e["solo"] - C.TARGET_AIM), e["severity"]))
    iota_a = anchor["iota"]

    all_rows = list(rows)

    def measure(plan: Sequence[tuple[str, int]], round_index: int):
        extra_cells = ladder_cells(topics, plan, include_outcomes=False,
                                   prefix=f"expand{round_index}")
        extra = generate_and_score(
            model_key, extra_cells, stage=f"{STAGE_LADDER}-r{round_index}",
            cap=cap, draws=C.LADDER_SCREEN_DRAWS, device=device,
            run_dir=out_dir / "backend_runs" / f"expand{round_index}",
            generate=generate)
        all_rows.extend(extra)
        added = difficulty_table_from_rows(all_rows, plan)
        table.update(added)
        for label in added:
            round_of[label] = round_index
        return _library_rows({k: added[k] for k in added},
                             round_of={k: round_index for k in added})

    result = lib.run_expansion(_library_rows(table, round_of=round_of),
                               iota_a, measure=measure)
    freeze = lib.freeze_vocabulary(model_key, result, iota_a=iota_a)

    # ------------------------------------------------ §12.3's shortlist
    short = regime.shortlist(table, iota_a=iota_a)
    record = regime.regime_screen_payload(
        selected_cap=cap, difficulty_table=table, shortlist_table=short,
        iota_a_prescreen=iota_a,
        truncation_by_cell={label: entry["truncation"]
                            for label, entry in table.items()},
        screen_dir=str(out_dir), vocabulary_freeze=freeze.as_dict())
    record.update({
        "model_key": model_key, "model_id": spec.model_id,
        "model_revision": spec.revision,
        "completion_cap": chosen,
        "a_anchor": {"severity": anchor["severity"], "solo": anchor["solo"],
                     "iota": anchor["iota"],
                     "rule": "the A severity whose pre-screen solo compliance "
                             "is nearest §12.3's target aim; a pre-screen "
                             "anchor only, never n*"},
        "family_ranking": regime.family_ranking(table, iota_a=iota_a),
        "expansion": result,
        "rows_generated": len(all_rows),
    })
    fs.write_json(out_dir / "regime_record.json", record)
    _mirror(model_key, out_dir)
    return record
