"""Cell means and the observation table (§11.1, §14.1, §21).

The **block** is the assignment, pairing, clustering and generalisation unit.
Cached draws are never independent observations and cells are never resampled:
this module turns raw rows into one cell mean per (cell, constituent) over
**all M draws**, refuses any partial cell, and hands the analysis a table whose
only index is the block.

**A configuration is (model, position of the outcome constraint).** §11.4 fixes
this reading. A solo cell states its single constraint in position one, so
``D(c <- g)`` is position-matched to its baseline exactly in the configuration
where c is stated first, and Delta-type quantities difference two composed
cells with c in the *same* position. Under a slot-order reading ``Delta_R``
would difference ``D(B <- A)`` with B second against ``D(B <- R_j)`` with B
first and would not be position-clean. The two configurations are therefore
``outcome_first`` and ``outcome_second``, both order variants run in every
block, and each configuration is estimated on all 384 blocks.

**What differs from v4r2.** v4r2's block is a full matrix over five slots, so
its within-block check could assert that every slot pairs with every other. A
v4r3 block is four arms with different pairing rules --- the spectrum rungs and
the class companion pair with ``B`` alone --- so the expected cell set is
*derived* from `design.cells.cell_types` rather than assumed. Asserting a full
matrix here would demand ninety composed cells per block that no registered
estimand reads, and asserting nothing would let a missing spectrum cell through.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r4.design.cells import cell_types
from dci1v4r4.protocol import constants as C

__all__ = ["Observation", "ObservationTable", "build_observations",
           "OUTCOME_FIRST", "OUTCOME_SECOND", "CONFIGURATIONS"]

OUTCOME_FIRST = C.OUTCOME_FIRST
OUTCOME_SECOND = C.OUTCOME_SECOND
CONFIGURATIONS = C.CONFIGURATIONS

#: Position -> configuration. A solo cell is position one and serves both.
_POSITION_CONFIG = {1: OUTCOME_FIRST, 2: OUTCOME_SECOND}


@dataclass(frozen=True)
class Observation:
    """One cell mean of one constituent of one cell of one block."""

    block_id: str
    cell_id: str
    arm: str
    outcome_slot: str
    companion_slot: str | None      # None for a solo cell
    position: int                   # 1 or 2
    configuration: str | None       # None for solo cells: they serve both
    draws: int
    compliance: float               # mean X over all M draws
    graded: float                   # mean G over all M draws
    vacuity: float                  # share of draws that were vacuous passes
    truncation: float               # share of draws truncated at the cap
    non_vacuous_compliance: float   # mean of (X and non-vacuous): §17.4
    graded_threshold: float         # mean of 1[G >= 0.99]: the F5 recoding
    response_words: float           # mean word count: registered mediator
    processing_failures: int


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def build_observations(rows: Iterable[dict[str, Any]], *, m_draws: int,
                       exact_count_rule: str = "s0") -> list[Observation]:
    """Form one cell mean per (cell, constituent) over exactly ``m_draws``.

    ``exact_count_rule`` re-scores the A-side under one of §9.2's registered
    alternatives. S0 is the outcome and applies unchanged in every cell; S1,
    S2 and S3 belong to §23's robustness family and never redefine X_A, which
    is why the rule is a parameter of this builder and not of the verifier:
    the stored verdict is always S0's.
    """
    if exact_count_rule.upper() not in C.EXACT_COUNT_RULES:
        raise ProtocolError(f"{exact_count_rule!r} is not a registered "
                            f"exact-count rule {C.EXACT_COUNT_RULES}")
    rule = exact_count_rule.lower()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["block_id"], row["cell_id"]), []).append(row)

    observations: list[Observation] = []
    for (block_id, cell_id), members in sorted(grouped.items()):
        indices = sorted(r["draw_index"] for r in members)
        if indices != list(range(m_draws)):
            raise IntegrityError(
                f"{cell_id}@{block_id}: accepted draws {indices} are not "
                f"exactly the {m_draws} registered identities; a cell mean is "
                f"never formed from a partial cell and no draw is imputed "
                f"(§14.2)")
        first = members[0]
        slots = [s["slot"] for s in first["scores"]]
        for slot in slots:
            scored = []
            for row in members:
                entry = next(s for s in row["scores"] if s["slot"] == slot)
                if entry["kind"] == "A" and rule != "s0":
                    realised = row["exact_count_alternatives"][rule]
                    entry = {**entry,
                             "passed": realised == entry["severity"]}
                scored.append((entry, row))
            if first["arm"] == "unconstrained":
                # §25's chance cell states nothing and is scored against every
                # registered instrument, so its scores carry as many entries
                # as there are instruments. None of them is a companion of
                # another and none has a position in the §11.4 sense: the
                # cell has no stated constraint to be first or second.
                position, companion, configuration = 1, None, None
            else:
                position = scored[0][0]["position"]
                companion = next((s for s in slots if s != slot), None)
                configuration = (None if companion is None
                                 else _POSITION_CONFIG[position])
            observations.append(Observation(
                block_id=block_id, cell_id=cell_id, arm=first["arm"],
                outcome_slot=slot, companion_slot=companion,
                position=position, configuration=configuration,
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
                # §15 F5's graded recoding thresholds the DRAW-level graded
                # score, so it is formed here and never by thresholding a
                # cell mean afterwards.
                graded_threshold=_mean(
                    [1.0 if float(e["graded"]) >= C.GRADED_ROBUSTNESS_THRESHOLD
                     else 0.0 for e, _ in scored]),
                response_words=_mean([float(r["word_count"])
                                      for _, r in scored]),
                processing_failures=sum(1 for e, _ in scored
                                        if e.get("processing_failure")),
            ))
    return observations


class ObservationTable:
    """Block-indexed access to cell means.

    No draw-level or response-level index is reachable from here, which is
    §14.1's executable check rather than its restatement.
    """

    def __init__(self, observations: Sequence[Observation]):
        self.observations = list(observations)
        self.blocks = sorted({o.block_id for o in self.observations})
        self._solo: dict[tuple[str, str], Observation] = {}
        self._chance: dict[tuple[str, str], Observation] = {}
        self._composed: dict[tuple[str, str, str, str], Observation] = {}
        for obs in self.observations:
            # §25's chance verdicts come from the load-0 cell, which is scored
            # against every registered instrument while stating none of them.
            # They are observations of the same slots as the solo cells and
            # would collide with them in the same index -- and the collision
            # is not a naming accident: p(c | nothing stated) and
            # p(c | c stated) are different quantities and the difficulty
            # coordinate is built from both.
            if obs.arm == "unconstrained":
                key = (obs.block_id, obs.outcome_slot)
                if key in self._chance:
                    raise IntegrityError(f"duplicate chance observation {key}")
                self._chance[key] = obs
                continue
            if obs.companion_slot is None:
                key = (obs.block_id, obs.outcome_slot)
                if key in self._solo:
                    raise IntegrityError(f"duplicate solo observation {key}")
                self._solo[key] = obs
            else:
                ckey = (obs.block_id, obs.outcome_slot, obs.companion_slot,
                        obs.configuration)
                if ckey in self._composed:
                    raise IntegrityError(
                        f"duplicate composed observation {ckey}")
                self._composed[ckey] = obs

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

    def chance(self, block_id: str, slot: str) -> Observation:
        """§25: the slot's compliance on the load-0 cell of that block."""
        try:
            return self._chance[(block_id, slot)]
        except KeyError:
            raise IntegrityError(
                f"no §25 chance observation for {slot} in block {block_id}; "
                f"the difficulty coordinate is (solo - chance)/(1 - chance) "
                f"and cannot be formed without it") from None

    def has_chance(self, slot: str) -> bool:
        return any(k[1] == slot for k in self._chance)

    def has_composed(self, outcome: str, companion: str,
                     configuration: str) -> bool:
        return any(k[1] == outcome and k[2] == companion
                   and k[3] == configuration for k in self._composed)

    def slots(self) -> tuple[str, ...]:
        """Slots that have a SOLO cell. The chance index is not a slot source:
        the load-0 cell is scored against instruments the design may not carry
        as slots at all."""
        return tuple(sorted({o.outcome_slot for o in self.observations
                             if o.arm != "unconstrained"}))

    def companions_of(self, outcome: str) -> tuple[str, ...]:
        return tuple(sorted({k[2] for k in self._composed if k[1] == outcome}))

    def assert_within_block(self, *, reduced: bool = False,
                            class_arm: bool = True, spectrum: bool = True,
                            expected_blocks: int | None = None
                            ) -> dict[str, Any]:
        """§14.1 / C16: every registered contrast is formed inside a block.

        Executable form: every block carries exactly the cells the design in
        force requires, so no estimand can reach across blocks. A cross-block
        term is impossible when every term of every contrast is looked up by
        the same ``block_id``.

        The expected set comes from `cell_types`, not from a full matrix: the
        spectrum and class arms pair with ``B`` alone, and demanding a full
        matrix would require ninety composed cells per block that no
        registered estimand reads.
        """
        expected = cell_types(reduced=reduced, class_arm=class_arm,
                              spectrum=spectrum)
        missing: list[str] = []
        for block in self.blocks:
            for cell in expected:
                if cell.arm == "unconstrained":
                    continue
                if cell.arm == "solo":
                    if (block, cell.slots[0]) not in self._solo:
                        missing.append(f"solo:{cell.slots[0]}@{block}")
                    continue
                first, second = cell.slots
                for outcome, companion in ((first, second), (second, first)):
                    configuration = (OUTCOME_FIRST if outcome == first
                                     else OUTCOME_SECOND)
                    if (block, outcome, companion,
                            configuration) not in self._composed:
                        missing.append(f"{outcome}+{companion}:"
                                       f"{configuration}@{block}")
        if missing:
            raise IntegrityError(
                f"{len(missing)} cell(s) missing from the within-block set, "
                f"first: {missing[0]}")
        if expected_blocks is not None and len(self.blocks) != expected_blocks:
            raise ProtocolError(f"{len(self.blocks)} blocks, expected "
                                f"{expected_blocks}")
        return {"blocks": len(self.blocks), "slots": list(self.slots()),
                "cells_per_block": (len(self.observations)
                                    // max(len(self.blocks), 1)),
                "design": ("reduced" if reduced else
                           "full" if spectrum else "no_spectrum"),
                "cross_block_terms": 0}
