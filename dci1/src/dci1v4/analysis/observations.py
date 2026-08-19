"""Cell means and the observation table (§11.1, §14.1, §21 steps 3-6).

The **block** is the assignment, pairing, clustering and generalisation unit.
Cached draws are never independent observations and cells are never resampled:
this module turns raw rows into one cell mean per (cell, constituent) over
**all M draws**, refuses any partial cell, and hands the analysis a table whose
only index is the block.

**A configuration is (model, position of the outcome constraint).** §11.4 fixes
this reading: a solo cell states its single constraint in position one, so
``D(c <- g)`` is position-matched to its baseline exactly in the configuration
where c is stated first, and Delta-type quantities "difference two composed
cells with c in the same position and are position-clean in both
configurations". That last clause only holds if the configuration fixes the
*outcome's* position — under a slot-order reading, ``Delta_R`` would difference
``D(B <- A)`` with B second against ``D(B <- R_j)`` with B first and would not
be position-clean. So the two configurations are ``outcome_first`` and
``outcome_second``, every pair runs both order variants in every block, and
each configuration is estimated on all 384 blocks.

One composed generation yields **two** observations, one per constituent, with
the other constituent as companion (§8.1, T-1). Neither is a manipulation
check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from dci1v4.errors import IntegrityError, ProtocolError

OUTCOME_FIRST = "outcome_first"
OUTCOME_SECOND = "outcome_second"
CONFIGURATIONS = (OUTCOME_FIRST, OUTCOME_SECOND)

#: Position -> configuration. A solo cell is position one and belongs to both.
_POSITION_CONFIG = {1: OUTCOME_FIRST, 2: OUTCOME_SECOND}


@dataclass(frozen=True)
class Observation:
    """One cell mean of one constituent of one cell of one block."""

    block_id: str
    cell_id: str
    cell_type: str
    outcome_slot: str
    companion_slot: str | None      # None for a solo cell
    position: int                   # 1 or 2
    configuration: str | None       # None for solo cells: they serve both
    draws: int
    compliance: float               # mean X over all M draws
    graded: float                   # mean G over all M draws
    vacuity: float                  # share of draws that were vacuous passes
    truncation: float               # share of draws truncated at the cap
    non_vacuous_compliance: float   # mean of (X and non-vacuous): §17.4 bound
    response_words: float           # mean word count: registered mediator
    processing_failures: int


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def build_observations(rows: Iterable[dict[str, Any]], *, m_draws: int,
                       ) -> list[Observation]:
    """Form one cell mean per (cell, constituent) over exactly ``m_draws``."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["cell_id"], []).append(row)

    observations: list[Observation] = []
    for cell_id, members in sorted(grouped.items()):
        indices = sorted(r["draw_index"] for r in members)
        if indices != list(range(m_draws)):
            raise IntegrityError(
                f"{cell_id}: accepted draws {indices} are not exactly the "
                f"{m_draws} registered identities; a cell mean is never formed "
                f"from a partial cell and no draw is imputed (§14.2)")
        first = members[0]
        slots = [s["slot"] for s in first["scores"]]
        for slot in slots:
            scored = []
            for row in members:
                entry = next(s for s in row["scores"] if s["slot"] == slot)
                scored.append((entry, row))
            position = scored[0][0]["position"]
            companion = next((s for s in slots if s != slot), None)
            observations.append(Observation(
                block_id=first["block_id"], cell_id=cell_id,
                cell_type=first["cell_type"], outcome_slot=slot,
                companion_slot=companion, position=position,
                configuration=(None if companion is None
                               else _POSITION_CONFIG[position]),
                draws=len(members),
                compliance=_mean([1.0 if e["passed"] else 0.0
                                  for e, _ in scored]),
                graded=_mean([float(e["graded"]) for e, _ in scored]),
                vacuity=_mean([1.0 if e["vacuous_pass"] else 0.0
                               for e, _ in scored]),
                truncation=_mean([1.0 if r["truncated"] else 0.0
                                  for _, r in scored]),
                non_vacuous_compliance=_mean(
                    [1.0 if (e["passed"] and e["non_vacuous"]) else 0.0
                     for e, _ in scored]),
                response_words=_mean([float(r["word_count"])
                                      for _, r in scored]),
                processing_failures=sum(1 for e, _ in scored
                                        if e["processing_failure"]),
            ))
    return observations


class ObservationTable:
    """Block-indexed access to cell means. No draw- or response-level index
    is reachable from here, which is the §14.1 executable check."""

    def __init__(self, observations: Sequence[Observation]):
        self.observations = list(observations)
        self.blocks = sorted({o.block_id for o in self.observations})
        self._solo: dict[tuple[str, str], Observation] = {}
        self._composed: dict[tuple[str, str, str, str], Observation] = {}
        for obs in self.observations:
            if obs.companion_slot is None:
                key = (obs.block_id, obs.outcome_slot)
                if key in self._solo:
                    raise IntegrityError(f"duplicate solo observation {key}")
                self._solo[key] = obs
            else:
                key = (obs.block_id, obs.outcome_slot, obs.companion_slot,
                       obs.configuration)
                if key in self._composed:
                    raise IntegrityError(f"duplicate composed observation "
                                         f"{key}")
                self._composed[key] = obs

    def solo(self, block_id: str, slot: str) -> Observation:
        try:
            return self._solo[(block_id, slot)]
        except KeyError:
            raise IntegrityError(
                f"missing solo cell for {slot} in block {block_id}; the "
                f"analysis fails closed on a missing cell (§21)") from None

    def composed(self, block_id: str, outcome: str, companion: str,
                 configuration: str) -> Observation:
        try:
            return self._composed[(block_id, outcome, companion,
                                   configuration)]
        except KeyError:
            raise IntegrityError(
                f"missing composed cell {outcome}+{companion} in "
                f"{configuration} for block {block_id}") from None

    def has_composed(self, outcome: str, companion: str,
                     configuration: str) -> bool:
        return any(key[1] == outcome and key[2] == companion
                   and key[3] == configuration for key in self._composed)

    def slots(self) -> tuple[str, ...]:
        return tuple(sorted({o.outcome_slot for o in self.observations}))

    def assert_within_block(self, *, expected_blocks: int | None = None
                            ) -> dict[str, Any]:
        """Check C16: every registered contrast is formed inside a block.

        Executable form: every block carries the complete set of cells the
        design in force requires, so no estimand can reach across sets. A
        cross-set term is impossible when every term of every contrast is
        looked up by the same ``block_id``.
        """
        slots = self.slots()
        missing: list[str] = []
        for block in self.blocks:
            for slot in slots:
                if (block, slot) not in self._solo:
                    missing.append(f"solo:{slot}@{block}")
            for outcome in slots:
                for companion in slots:
                    if outcome == companion:
                        continue
                    for configuration in CONFIGURATIONS:
                        if (block, outcome, companion,
                                configuration) not in self._composed:
                            missing.append(
                                f"{outcome}+{companion}:{configuration}@"
                                f"{block}")
        if missing:
            raise IntegrityError(
                f"{len(missing)} cell(s) missing from the within-block "
                f"matrix, first: {missing[0]}")
        if expected_blocks is not None and len(self.blocks) != expected_blocks:
            raise ProtocolError(f"{len(self.blocks)} blocks, expected "
                                f"{expected_blocks}")
        return {"blocks": len(self.blocks), "slots": list(slots),
                "cells_per_block": len(self.observations) // len(self.blocks),
                "cross_set_terms": 0}
