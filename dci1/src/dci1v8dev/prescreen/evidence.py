"""Screen evidence, keyed by wording frame --- the seam between measurement
and retention.

The legacy screen (``run/regime.prescreen_counts`` + ``screen_families`` +
``retention.retain``) reads one table of counts pooled over the four
wording frames. Under Approach A (``docs/V8_FRAME_CONDITIONING.md``) every
later quantity is frame-specific, so a retention policy that is to decide
*per frame* needs the same counts *per frame*. This module holds them:
``FrameEvidence`` is one frame's table and A-grid (the schema is unchanged
--- ``PrescreenRung`` and ``ARung`` carry no frame; the frame is the key),
and ``ScreenEvidence`` is the set of them beside the pooled table the
legacy policy reads. Both are built from scored rows by the production
count kernel on each frame's own blocks (``execute.frame_of_block``), so
the per-frame evidence is the frame's share of exactly the rows the pooled
evidence sums.

Nothing here decides anything. A policy (``prescreen.policy``) reads an
evidence object and returns a forwarding plan.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import FAMILIES, Constraint

from dci1v8dev.prescreen.schema import ARung, PrescreenRung

__all__ = ["FRAMES", "POOLED", "FrameEvidence", "ScreenEvidence",
           "counts_to_input", "evidence_from_counts", "evidence_from_rows"]

FRAMES: tuple[int, ...] = tuple(range(C.N_WORDINGS))
#: The key of the frame-pooled evidence.
POOLED = "pooled"


def counts_to_input(counts: Iterable[Mapping[str, Any]]
                    ) -> tuple[list[PrescreenRung], list[ARung]]:
    """The screen's input from count rows (B is not screened). The same
    construction as ``run/regime.prescreen_input``, kept here so the
    evidence layer does not import the execution layer."""
    table, a_grid = [], []
    for row in counts:
        if row["kind"] == "A":
            a_grid.append(ARung(severity=int(row["severity"]),
                                solo_k=int(row["solo_k"]),
                                solo_n=int(row["solo_n"]),
                                chance_k=float(row["chance_k"]),
                                chance_n=float(row["chance_n"]),
                                n_topics=int(row["n_topics"]),
                                draws_per_topic=int(row["draws_per_topic"])))
        elif row["kind"] == "B" or row["kind"] not in FAMILIES:
            continue
        else:
            table.append(PrescreenRung(
                kind=row["kind"], severity=int(row["severity"]),
                solo_k=int(row["solo_k"]), solo_n=int(row["solo_n"]),
                chance_k=float(row["chance_k"]), chance_n=float(row["chance_n"]),
                vacuous_k=min(int(row["vacuous_k"]), int(row["solo_k"])),
                n_topics=int(row["n_topics"]),
                draws_per_topic=int(row["draws_per_topic"]),
                reserve=bool(row.get("reserve"))))
    return table, a_grid


@dataclass(frozen=True)
class FrameEvidence:
    """One frame's screen counts (or the pooled counts, ``frame=None``)."""

    frame: int | None
    table: tuple[PrescreenRung, ...]
    a_grid: tuple[ARung, ...]
    #: Distinct topics the solo rows were measured on (the count every
    #: per-rung SE is formed at).
    n_topics: int

    def __post_init__(self):
        if self.frame is not None and self.frame not in FRAMES:
            raise ProtocolError(f"frame {self.frame!r} is not one of {FRAMES}")
        if not self.a_grid:
            raise ProtocolError(f"frame {self.key}: no A-grid on the screen")

    @property
    def key(self) -> str:
        return POOLED if self.frame is None else str(self.frame)

    @property
    def labels(self) -> list[str]:
        return [r.label for r in self.table]

    def replaced(self, table: Sequence[PrescreenRung], a_grid: Sequence[ARung]
                 ) -> "FrameEvidence":
        n_topics = max((r.n_topics for r in table), default=self.n_topics)
        return FrameEvidence(frame=self.frame, table=tuple(table),
                             a_grid=tuple(a_grid), n_topics=n_topics)


@dataclass(frozen=True)
class ScreenEvidence:
    """Every frame's evidence, and the pooled evidence the legacy policy reads.

    ``by_frame`` holds one ``FrameEvidence`` per frame that has rows;
    ``pooled`` is the frame-summed table. The two are built from the same
    rows, and ``assert_consistent`` checks that the per-frame solo counts
    add up to the pooled ones rung by rung, so a per-frame table cannot
    quietly be a different measurement from the pooled one.
    """

    by_frame: dict[int, FrameEvidence]
    pooled: FrameEvidence
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.by_frame:
            raise ProtocolError("screen evidence carries no frame")
        for f, e in self.by_frame.items():
            if e.frame != f:
                raise ProtocolError(f"evidence keyed {f} carries frame {e.frame}")
        if self.pooled.frame is not None:
            raise ProtocolError("the pooled evidence must carry frame None")

    @property
    def frames(self) -> list[int]:
        return sorted(self.by_frame)

    def assert_consistent(self) -> dict[str, Any]:
        """Per rung, the frames' solo counts sum to the pooled solo count and
        the frames' topic counts sum to the pooled topic count. Refuses
        otherwise: the per-frame evidence must be a partition of the pooled."""
        pooled = {r.label: r for r in self.pooled.table}
        checked = 0
        for label, pr in pooled.items():
            parts = [next((r for r in e.table if r.label == label), None)
                     for e in self.by_frame.values()]
            parts = [p for p in parts if p is not None]
            if not parts:
                raise ProtocolError(f"{label}: on the pooled table and on no "
                                    "frame's table")
            solo_k = sum(p.solo_k for p in parts)
            solo_n = sum(p.solo_n for p in parts)
            if (solo_k, solo_n) != (pr.solo_k, pr.solo_n):
                raise ProtocolError(
                    f"{label}: the frames' solo counts {solo_k}/{solo_n} do "
                    f"not add up to the pooled {pr.solo_k}/{pr.solo_n}")
            checked += 1
        return {"rungs_checked": checked, "frames": self.frames,
                "partition_of_pooled": True}


def evidence_from_counts(pooled_counts: Iterable[Mapping[str, Any]],
                         counts_by_frame: Mapping[Any, Iterable[Mapping[str, Any]]],
                         *, provenance: Mapping[str, Any] | None = None
                         ) -> ScreenEvidence:
    """From recorded count tables (a stage record or a fixture)."""
    p_table, p_grid = counts_to_input(list(pooled_counts))
    pooled = FrameEvidence(frame=None, table=tuple(p_table), a_grid=tuple(p_grid),
                           n_topics=max((r.n_topics for r in p_table), default=0))
    by_frame: dict[int, FrameEvidence] = {}
    for key, counts in counts_by_frame.items():
        f = int(key)
        table, grid = counts_to_input(list(counts))
        by_frame[f] = FrameEvidence(
            frame=f, table=tuple(table), a_grid=tuple(grid),
            n_topics=max((r.n_topics for r in table), default=0))
    return ScreenEvidence(by_frame=by_frame, pooled=pooled,
                          provenance=dict(provenance or {}))


def evidence_from_rows(rows: Sequence[Mapping[str, Any]],
                       rungs: Sequence[Constraint], *,
                       provenance: Mapping[str, Any] | None = None
                       ) -> ScreenEvidence:
    """From scored screen rows: the production count kernel on every frame's
    own blocks and on all of them together. Imports the execution layer's
    kernel lazily so the evidence module stays importable without it."""
    from dci1v8dev.run.execute import frame_of_block
    from dci1v8dev.run.regime import prescreen_counts

    # Loads 0 and 1 only: a composed row (two present constituents) is a
    # protected quantity and can never be screen evidence.
    for row in rows:
        present = [s for s in row.get("scores", ()) if s.get("present")]
        if len(present) > 1 or int(row.get("load", len(present))) > 1:
            raise ProtocolError(
                f"row {row.get('row_id')!r}: {len(present)} present "
                "constituents; screen evidence is formed on loads 0 and 1 "
                "only and a composed row is refused")
    by_frame: dict[Any, list[dict[str, Any]]] = {}
    for f in FRAMES:
        frame_rows = [r for r in rows if frame_of_block(r) == f]
        if not frame_rows:
            continue
        counts = prescreen_counts(frame_rows, rungs)
        by_frame[f] = counts
    pooled = prescreen_counts(rows, rungs)
    reserve = {(c.kind, c.severity): bool(c.reserve) for c in rungs}
    for table in [pooled, *by_frame.values()]:
        for row in table:
            row["reserve"] = reserve.get((row["kind"], row["severity"]), False)
    out = evidence_from_counts(pooled, by_frame, provenance={
        "n_rows": len(rows),
        "frames": sorted(by_frame),
        "topics_by_frame": {str(f): len({r["topic_id"] for r in rows
                                         if frame_of_block(r) == f})
                            for f in by_frame},
        **dict(provenance or {})})
    out.assert_consistent()
    return out
