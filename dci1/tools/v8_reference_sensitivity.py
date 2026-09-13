#!/usr/bin/env python3
"""How tied is the frozen reference triple? (finding 5)

§13.8 picks three core references per frame by one ranking on one number:
|iota_R(f) - iota_A(f)|, with structural side conditions (three feature
groups, at least ``MIN_TIER1_CORE`` Tier-1 members, at least
``MIN_CORE_DISCOURSE_ROLES`` declared roles) and a role substitution. On a
pilot frame the qualifying families' distances sit within a few hundredths
of each other, and the whole selection turns on that ordering. This tool
measures how much of the ordering is signal.

Per model x frame it reports, from the signed pre-freeze records and the
frame's own per-topic vectors:

1.  the number of LOCAL-valid families (§13.15's count);
2.  the number of admissible triples --- §13.8's structural rule, run by
    ``dci1v8dev.confirm.membership.admissible_triples``, the same function
    the ``MEMBERSHIP`` record uses --- over **every** LOCAL-valid family,
    and over the **five frozen** families {R1..R5} alone;
3.  the selected primary triple and each member's |iota_R(f) - iota_A(f)|;
4.  every alternative triple with its distances, and how much total match
    quality it gives up against the primary (``delta_sum``);
5.  the standard error of every distance --- SE(iota_R) mirroring
    ``dci1v8dev.spectrum.validity._se_iota`` on the row's
    ``per_topic_solo``, SE(iota_A) the same statistic on A's per-topic
    vector at n*(f) read from ``backend_runs/grid-A``, and the paired SE of
    the difference on the frame's shared topic index;
6.  the probability, under a topic bootstrap seeded by
    ``seeds.bootstrap_seed("reference_sensitivity:frame<f>", model_key)``,
    that the registered ranking re-selects the frozen triple;
7.  a ``MATERIAL`` flag when some alternative triple's total distance is
    within one bootstrap SE of the primary's, or the primary is re-selected
    on fewer than two thirds of the resamples.

**This tool changes no selection.** R1/R2/R3 remain the frozen primary
triple and R4/R5 the frozen backups; the confirmatory analysis already
re-forms Delta_R(f) over *every* admissible triple of the five frozen
families from the same generated cells (``confirm/analysis.py``, the
``F_REFSENS`` member family, planned on the ``MEMBERSHIP`` record's
``reference_sensitivity`` block). What is measured here is how tied the
ranking that produced R1..R3 was, so that the descriptive family's spread
can be read as a sensitivity rather than as noise.

**What the bootstrap holds fixed.** Family *admission* --- the full V(R) of
§13.4-§13.9, whose components (V_stab, V_chance, V_head, ...) each carry
their own resampling --- is not re-evaluated: the resample re-computes the
difficulty coordinates iota_R and iota_A on resampled topics and re-runs the
*ranking and structural selection* over the families and rungs the pilot
found LOCAL-valid. It therefore measures the stability of the **choice among
qualifying families**, not the stability of qualification, and it is a lower
bound on the total variability of the frozen triple.

    python3 tools/v8_reference_sensitivity.py --root evidence/dci1v8-pilot-r9 \
        --model qwen3-4b
    python3 tools/v8_reference_sensitivity.py --all

Reads the signed ``GATE_2_CALIBRATION`` and ``GATE_3_REFERENCES`` records
(through ``confirm.pilot_import.open_pilot``, so every signature is verified)
and the ``grid-A`` scored rows. Writes only
``reports/dci1v8dev/reference_sensitivity/``; nothing enters an evidence
tree, no threshold moves and no record is rewritten.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import re
import statistics
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.errors import ProtocolError                                # noqa: E402
from dci1v7.protocol import constants as C                             # noqa: E402
from dci1v7.protocol.taxonomy import (TIER_1, assert_core_set_structure,  # noqa: E402
                                      declared_roles)
from dci1v7.stages.calibration_table import (instructed_compliance,     # noqa: E402
                                             tie_key)
from dci1v7.stages.selection import restrictiveness_key                 # noqa: E402
from dci1v7.verifiers.constraints import FAMILIES, FEATURE_GROUP_IDS    # noqa: E402
from dci1v8dev.confirm.membership import admissible_triples             # noqa: E402
from dci1v8dev.confirm.pilot_import import frame_inputs, open_pilot     # noqa: E402
from dci1v8dev.run import seeds                                        # noqa: E402
from dci1v8dev.run import stages as PS                                 # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev" / "reference_sensitivity"
EVIDENCE = HERE.parent / "evidence"

#: The pilot root that measured each model at its final calibration
#: allocation. A later root supersedes an earlier one for the same model;
#: both stay on disk and either can be named with --root.
DEFAULT_SOURCES = (
    ("dci1v8-pilot-r9", "qwen3-4b"),
    ("dci1v8-pilot-r8", "gemma-3n-e2b-it"),
    ("dci1v8-pilot-r10", "qwen3-4b-instruct-2507"),
    ("dci1v8-pilot-r11", "gemma-3n-e4b-it"),
)

#: Reporting conventions. Neither admits anything and neither is a
#: registered threshold: they name, before the table is read, how the
#: printed numbers map onto the one word the finding is asked for. Both are
#: stated in the task that commissioned this tool.
WITHIN_SE = 1.0
MIN_RESELECTION = 2.0 / 3.0
RESAMPLES = 2000

SENSITIVITY_RULE = (
    "MATERIAL when some admissible alternative triple's total distance is "
    f"within {WITHIN_SE:g} bootstrap SE of the primary triple's, or the "
    "registered ranking re-selects the frozen triple on fewer than "
    f"{MIN_RESELECTION:.4f} of {RESAMPLES} topic resamples")


# ------------------------------------------------------------------ points
@dataclass(frozen=True)
class Rung:
    """One LOCAL-valid rung of one family on one frame."""
    family: str
    severity: int
    iota: float
    chance: float
    per_topic: tuple[float, ...]

    @property
    def label(self) -> str:
        return f"{self.family}:{self.severity}"

    @property
    def structural_tier(self) -> int:
        return int(FAMILIES[self.family].structural_tier)

    @property
    def feature_group(self) -> str:
        return FAMILIES[self.family].feature_group

    @property
    def discourse_role(self) -> str:
        return FAMILIES[self.family].discourse_role


@dataclass(frozen=True)
class Point:
    """A family's chosen rung under one realisation of the coordinates."""
    family: str
    severity: int
    iota: float
    distance: float
    structural_tier: int
    feature_group: str
    discourse_role: str


def _entry_dicts(points: Sequence[Point]) -> list[dict[str, Any]]:
    return [{"family": p.family, "structural_tier": p.structural_tier,
             "feature_group": p.feature_group,
             "discourse_role": p.discourse_role} for p in points]


def best_rung(rungs: Sequence[Rung], iota_by_label: Mapping[str, float],
              iota_a: float) -> Point:
    """``selection.admit_family``'s within-family choice: the passing rung
    minimising |iota_R - iota_A|, an exact tie going to the less restrictive
    severity."""
    def key(r: Rung) -> tuple:
        return (tie_key(abs(iota_by_label[r.label] - iota_a)),
                restrictiveness_key(r.family, r.severity))
    best = min(rungs, key=key)
    iota = iota_by_label[best.label]
    return Point(family=best.family, severity=best.severity, iota=iota,
                 distance=abs(iota - iota_a),
                 structural_tier=best.structural_tier,
                 feature_group=best.feature_group,
                 discourse_role=best.discourse_role)


def _group_order(family: str) -> int:
    return FEATURE_GROUP_IDS.index(FAMILIES[family].feature_group)


def rank(points: Sequence[Point]) -> list[Point]:
    """§13.8's registered tie-break, in order: smallest |iota_R - iota_A|;
    lower structural tier; registered feature-group order; the less
    restrictive severity; family identifier."""
    return sorted(points, key=lambda p: (tie_key(p.distance),
                                         p.structural_tier,
                                         _group_order(p.family),
                                         restrictiveness_key(p.family,
                                                             p.severity),
                                         p.family))


def select_core(points: Sequence[Point]) -> tuple[Point, ...]:
    """A mirror of ``dci1v7.stages.selection.admit_core_references``'
    selection loop at ``require_spectrum=False`` --- the call Gate 3 makes
    (``dci1v8dev/run/references.py``) --- over an already-admitted pool.

    The admission itself (the full V(R)) is not re-run here; the pool is the
    frame's LOCAL-valid families. Everything after that is the registered
    rule: the ranking, the feature-group distinctness, the Tier-1
    look-ahead, §13.8's role substitution and the structural assertion.
    Returns () when the rule identifies no set.
    """
    ranked = rank(points)
    chosen: list[Point] = []
    groups_taken: set[str] = set()
    remaining = list(ranked)
    while remaining and len(chosen) < C.N_CORE_REFERENCES:
        slots_left = C.N_CORE_REFERENCES - len(chosen)
        tier1_so_far = sum(1 for p in chosen if p.structural_tier == TIER_1)
        point = remaining.pop(0)
        group = point.feature_group
        if group in groups_taken:
            continue
        if point.structural_tier != TIER_1:
            tier1_available = sum(
                1 for p in remaining
                if p.structural_tier == TIER_1
                and p.feature_group not in groups_taken | {group})
            if tier1_so_far + min(tier1_available, slots_left - 1) < \
                    C.MIN_TIER1_CORE:
                continue
        chosen.append(point)
        groups_taken.add(group)
    if len(chosen) == C.N_CORE_REFERENCES and \
            len(declared_roles(_entry_dicts(chosen))) < \
            C.MIN_CORE_DISCOURSE_ROLES:
        present_roles = declared_roles(_entry_dicts(chosen))
        for candidate in remaining:
            if candidate.discourse_role in present_roles or \
                    candidate.discourse_role == "none":
                continue
            free_groups = {p.feature_group for p in chosen[:-1]}
            if candidate.feature_group in free_groups:
                continue
            trial = chosen[:-1] + [candidate]
            if sum(1 for p in trial if p.structural_tier == TIER_1) < \
                    C.MIN_TIER1_CORE:
                continue
            chosen = trial
            break
    if len(chosen) != C.N_CORE_REFERENCES:
        return ()
    try:
        assert_core_set_structure(
            _entry_dicts(chosen), min_tier1=C.MIN_TIER1_CORE,
            n_groups=C.N_CORE_FEATURE_GROUPS,
            min_roles=C.MIN_CORE_DISCOURSE_ROLES, a_role=C.A_DISCOURSE_ROLE)
    except Exception:
        return ()
    return tuple(chosen)


# -------------------------------------------------------------------- rows
def a_per_topic(model_dir: pathlib.Path, *, n_star_by_frame: Mapping[int, int]
                ) -> dict[int, dict[str, list[float]]]:
    """A's per-topic solo compliance at n*(f) under frame f, from grid-A.

    One pass over ``GATE_2_CALIBRATION/backend_runs/grid-A/scored.jsonl``,
    the same reduction ``dci1v7.run.execute.per_topic_compliance`` makes:
    the mean over a topic's draws, topics sorted --- which is the order
    ``calibration_rows[...]["per_topic_solo"]`` is written in, so the two
    vectors share a topic index.
    """
    path = (model_dir / PS.STAGE_GATE2 / "backend_runs" / "grid-A"
            / "scored.jsonl")
    if not path.exists():
        raise ProtocolError(f"no grid-A rows at {path}")
    needles = {n: f'"cell_id": "solo:A:{n}"'
               for n in sorted(set(n_star_by_frame.values()))}
    per: dict[int, dict[str, list[float]]] = {f: {} for f in n_star_by_frame}
    with open(path) as handle:
        for line in handle:
            for n, needle in needles.items():
                if needle not in line:
                    continue
                row = json.loads(line)
                frame = row.get("block_frame")
                if frame is None or n_star_by_frame.get(frame) != n:
                    break
                if row.get("arm") != "solo":
                    break
                for score in row["scores"]:
                    if (score["kind"] == "A" and int(score["severity"]) == n
                            and score["present"]):
                        per[frame].setdefault(row["topic_id"], []).append(
                            float(bool(score["passed"])))
                break
    return per


def _vector(per_topic: Mapping[str, Sequence[float]]) -> list[float]:
    return [sum(v) / len(v) for _, v in sorted(per_topic.items())]


_TOPIC = re.compile(r'"topic_id": "([^"]+)"')
_BLOCK = re.compile(r'"block_id": "[^"]*-(\d+)"')


def candidate_topics(model_dir: pathlib.Path) -> dict[int, list[str]]:
    """The topics each frame's candidate cells were rendered on, from the
    candidates run's ``design.jsonl`` (identity only, no responses).

    The tool pairs A's per-topic vector with each row's ``per_topic_solo``
    by index, which is sound only because both are sorted by topic id over
    the *same* topic set. That is asserted rather than assumed: the
    allocation puts every frame's grid and candidate cells on one topic
    set (``calibration.assert_allocation_realised``), and this is the read
    that checks it on the run that was actually executed.
    """
    path = (model_dir / PS.STAGE_GATE2 / "backend_runs" / "candidates"
            / "design.jsonl")
    if not path.exists():
        return {}
    per: dict[int, set[str]] = {}
    with open(path) as handle:
        for line in handle:
            block, topic = _BLOCK.search(line), _TOPIC.search(line)
            if block and topic:
                per.setdefault(int(block.group(1)) % C.N_WORDINGS,
                               set()).add(topic.group(1))
    return {frame: sorted(topics) for frame, topics in per.items()}


def se_iota(vector: Sequence[float], chance: float) -> float | None:
    """``dci1v8dev.spectrum.validity._se_iota``, on any per-topic vector."""
    n = len(vector)
    if n < 2:
        return None
    mean = sum(vector) / n
    var = sum((v - mean) ** 2 for v in vector) / (n - 1)
    return math.sqrt(var / n) / (1.0 - chance)


def se_difference(v_r: Sequence[float], kappa_r: float,
                  v_a: Sequence[float], kappa_a: float) -> float | None:
    """The paired SE of iota_R - iota_A on the frame's shared topic index."""
    if len(v_r) != len(v_a) or len(v_r) < 2:
        return None
    diffs = [(r - kappa_r) / (1.0 - kappa_r) - (a - kappa_a) / (1.0 - kappa_a)
             for r, a in zip(v_r, v_a)]
    return statistics.stdev(diffs) / math.sqrt(len(diffs))


# ------------------------------------------------------------------ triples
def _slots_of(frozen: Mapping[str, str], family: str) -> str:
    return frozen.get(family, f"({family})")


def triples_over(points: Sequence[Point], frozen_slot: Mapping[str, str]
                 ) -> list[dict[str, Any]]:
    """§13.8's structural rule over a pool, by the production function."""
    refs = [{"slot": _slots_of(frozen_slot, p.family), "family": p.family}
            for p in points]
    return admissible_triples(refs)


def _triple_key(families: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(families))


# ---------------------------------------------------------------- one frame
def frame_sensitivity(source, frame: int, *, a_vector: Sequence[float],
                      a_topics: Sequence[str] = (),
                      candidate_topics_of_frame: Sequence[str] | None = None,
                      resamples: int = RESAMPLES) -> dict[str, Any]:
    fi = frame_inputs(source, frame)
    g2 = source.gate2["by_frame"][str(frame)]
    g3 = source.gate3["by_frame"][str(frame)]
    if not fi.get("supported"):
        return {"frame": frame, "supported": False,
                "reason": fi.get("unsupported_reason")
                or "no operating point at Gate 2"}
    iota_a = float(g2["iota_a"])
    kappa_a = float(g2["kappa_a"])
    survival = g3["survival"]
    valid_families = list(survival["local_valid_families"])

    table = {f"{r['kind']}:{r['severity']}": r
             for r in g2["calibration_rows"]["pooled"]}
    rungs_by_family: dict[str, list[Rung]] = {}
    for label, verdict in sorted(g3["local"].items()):
        if not verdict["passed"]:
            continue
        row = table.get(label)
        if row is None:                                  # pragma: no cover
            raise ProtocolError(f"{label} is LOCAL-valid on frame {frame} "
                                "but absent from the pooled §13.11 table")
        family = row["kind"]
        rungs_by_family.setdefault(family, []).append(Rung(
            family=family, severity=int(row["severity"]),
            iota=instructed_compliance(float(row["solo_compliance"]),
                                       float(row["chance_compliance"])),
            chance=float(row["chance_compliance"]),
            per_topic=tuple(float(v) for v in row["per_topic_solo"])))
    if sorted(rungs_by_family) != sorted(valid_families):  # pragma: no cover
        raise ProtocolError(
            f"frame {frame}: the LOCAL-valid families {sorted(valid_families)} "
            f"and the passing rungs' families {sorted(rungs_by_family)} "
            "disagree on the signed record")

    n_topics = len(a_vector)
    if candidate_topics_of_frame is not None and \
            list(a_topics) != list(candidate_topics_of_frame):
        raise ProtocolError(
            f"frame {frame}: grid-A was rendered on "
            f"{len(a_topics)} topics and the candidate cells on "
            f"{len(candidate_topics_of_frame)}, and the two sets differ; "
            "the per-topic vectors do not share a topic index and cannot "
            "be paired")
    for family, rungs in rungs_by_family.items():
        for r in rungs:
            if len(r.per_topic) != n_topics:             # pragma: no cover
                raise ProtocolError(
                    f"frame {frame}: {r.label} carries {len(r.per_topic)} "
                    f"per-topic values against A's {n_topics}; the two "
                    "vectors must index the same frame topics")

    observed = {r.label: r.iota
                for rungs in rungs_by_family.values() for r in rungs}
    points = {family: best_rung(rungs, observed, iota_a)
              for family, rungs in sorted(rungs_by_family.items())}

    primary = select_core(list(points.values()))
    recorded = [e["family"] for e in survival["core_references"]]
    frozen_slot = {r["family"]: r["slot"] for r in fi["core"] + fi["backups"]}
    frozen_families = [r["family"] for r in fi["core"] + fi["backups"]]

    # ------------------------------------------------------------ SEs
    def se_block(p: Point) -> dict[str, Any]:
        rung = next(r for r in rungs_by_family[p.family]
                    if r.severity == p.severity)
        return {
            "se_iota_r": se_iota(rung.per_topic, rung.chance),
            "se_iota_a": se_iota(a_vector, kappa_a),
            "se_distance_paired": se_difference(rung.per_topic, rung.chance,
                                                a_vector, kappa_a),
        }

    def point_block(p: Point) -> dict[str, Any]:
        return {"family": p.family, "severity": p.severity,
                "label": f"{p.family}:{p.severity}",
                "slot": frozen_slot.get(p.family),
                "iota": p.iota, "distance": p.distance,
                "structural_tier": p.structural_tier,
                "feature_group": p.feature_group,
                "discourse_role": p.discourse_role, **se_block(p)}

    all_triples = triples_over(list(points.values()), frozen_slot)
    frozen_points = [points[f] for f in frozen_families if f in points]
    frozen_triples = triples_over(frozen_points, frozen_slot)
    primary_key = _triple_key(p.family for p in primary)

    def triple_entry(families: Sequence[str], structure: Mapping[str, Any]
                     ) -> dict[str, Any]:
        members = [points[f] for f in families]
        total = sum(p.distance for p in members)
        return {"families": list(families),
                "slots": list(structure["slots"]),
                "key": list(_triple_key(families)),
                "is_primary": _triple_key(families) == primary_key,
                "all_frozen": all(f in frozen_slot for f in families),
                "contains_contrastive": structure["contains_contrastive"],
                "distances": {p.family: p.distance for p in members},
                "sum_distance": total,
                "max_distance": max(p.distance for p in members)}

    enumerated = {_triple_key(t["families"]): triple_entry(t["families"], t)
                  for t in all_triples}
    for t in frozen_triples:
        enumerated.setdefault(_triple_key(t["families"]),
                              triple_entry(t["families"], t))
    frozen_keys = {_triple_key(t["families"]) for t in frozen_triples}

    # ------------------------------------------------------- the bootstrap
    boot = _bootstrap(rungs_by_family, a_vector=a_vector, kappa_a=kappa_a,
                      n_topics=n_topics, keys=list(enumerated),
                      primary_key=primary_key,
                      seed=seeds.bootstrap_seed(
                          f"reference_sensitivity:frame{frame}",
                          source.model_key),
                      resamples=resamples)

    primary_sum = enumerated[primary_key]["sum_distance"] if primary else None
    for key, entry in enumerated.items():
        entry["p_selected"] = boot["p_selected"].get(key, 0.0)
        entry["delta_sum"] = (None if primary_sum is None
                              else entry["sum_distance"] - primary_sum)
        entry["se_delta_sum"] = boot["se_delta_sum"].get(key)
        entry["within_1se_of_primary"] = bool(
            entry["delta_sum"] is not None and entry["se_delta_sum"]
            and not entry["is_primary"]
            and entry["delta_sum"] <= WITHIN_SE * entry["se_delta_sum"])

    alternatives = [e for e in enumerated.values() if not e["is_primary"]]
    closest = (min(alternatives, key=lambda e: (e["delta_sum"], e["key"]))
               if alternatives and primary_sum is not None else None)
    frozen_alternatives = [e for e in alternatives
                           if _triple_key(e["families"]) in frozen_keys]
    closest_frozen = (min(frozen_alternatives,
                          key=lambda e: (e["delta_sum"], e["key"]))
                      if frozen_alternatives and primary_sum is not None
                      else None)
    p_primary = boot["p_selected"].get(primary_key, 0.0) if primary else None
    tied = [e for e in alternatives if e["within_1se_of_primary"]]
    outranked = sorted((e["key"] for e in alternatives
                        if p_primary is not None
                        and e["p_selected"] > p_primary))
    material = bool(primary) and (bool(tied) or p_primary < MIN_RESELECTION)
    if not primary:
        flag = "NO_CORE"
    elif material:
        flag = "MATERIAL"
    elif len(enumerated) == 1:
        # The rule had no alternative to weigh: the frame's LOCAL-valid pool
        # admits exactly one triple, so a re-selection probability of 1 is a
        # property of the pool's size and not of the ranking's separation.
        flag = "FORCED"
    else:
        flag = "STABLE"

    return {
        "frame": frame, "supported": True, "state": g3["state"],
        "n_star": int(g2["n_star"]), "m_star": int(g2["m_star"]),
        "iota_a": iota_a, "kappa_a": kappa_a, "n_topics": n_topics,
        "se_iota_a": se_iota(a_vector, kappa_a),
        "n_local_valid_families": len(valid_families),
        "local_valid_families": valid_families,
        "n_local_valid_rungs": sum(len(v) for v in rungs_by_family.values()),
        "core_identified": bool(survival["core_identified"]),
        "frozen_families": frozen_families,
        "frozen_slots": {f: frozen_slot[f] for f in frozen_families},
        "n_frozen_families": len(frozen_families),
        "n_admissible_triples_all_valid": len(all_triples),
        "n_admissible_triples_frozen_five": len(frozen_triples),
        "primary": {"families": [p.family for p in primary],
                    "members": [point_block(p) for p in primary],
                    "sum_distance": primary_sum,
                    "reproduces_record": [p.family for p in primary] == recorded,
                    "recorded_core": recorded},
        "families": {f: point_block(p) for f, p in points.items()},
        "triples": sorted(enumerated.values(), key=lambda e: e["key"]),
        "closest_alternative": closest,
        "closest_alternative_over_frozen_five": closest_frozen,
        "p_primary_reselected": p_primary,
        "resamples": resamples,
        "seed_rule": "seeds.bootstrap_seed('reference_sensitivity:frame<f>', "
                     "model_key)",
        "tied_alternatives": [e["key"] for e in tied],
        "alternatives_selected_more_often_than_the_primary": outranked,
        "material": material,
        "flag": flag,
    }


def _bootstrap(rungs_by_family: Mapping[str, Sequence[Rung]], *,
               a_vector: Sequence[float], kappa_a: float, n_topics: int,
               keys: Sequence[tuple[str, ...]],
               primary_key: tuple[str, ...], seed: int, resamples: int
               ) -> dict[str, Any]:
    """A topic bootstrap of the ranking, paired across A and every rung.

    One resample draws ``n_topics`` topic indices with replacement and
    applies them to A's per-topic vector and to every LOCAL-valid rung's,
    so a topic that is easy for A is easy for the references in the same
    resample. iota is re-formed on the fixed chance column (§13.2's kappa is
    measured on the unconstrained cell of the same topics and is held at its
    measured value, which is what ``_se_iota`` does too), the within-family
    rung choice and §13.8's selection are re-run, and the selected triple is
    counted.
    """
    rng = random.Random(seed)
    flat = [r for family in sorted(rungs_by_family)
            for r in rungs_by_family[family]]
    counts: dict[tuple[str, ...], int] = {k: 0 for k in keys}
    counts.setdefault(primary_key, 0)
    sums: dict[tuple[str, ...], list[float]] = {k: [] for k in keys}
    n = n_topics
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        a_mean = sum(map(a_vector.__getitem__, idx)) / n
        iota_a = (a_mean - kappa_a) / (1.0 - kappa_a)
        iota_by_label: dict[str, float] = {}
        for r in flat:
            v = r.per_topic
            mean = sum(map(v.__getitem__, idx)) / n
            iota_by_label[r.label] = (mean - r.chance) / (1.0 - r.chance)
        points = {family: best_rung(rungs, iota_by_label, iota_a)
                  for family, rungs in sorted(rungs_by_family.items())}
        chosen = select_core(list(points.values()))
        if chosen:
            key = _triple_key(p.family for p in chosen)
            if key in counts:
                counts[key] += 1
            else:                                        # pragma: no cover
                counts[key] = 1
            primary_sum = sum(points[f].distance for f in primary_key
                              ) if all(f in points for f in primary_key) else None
            if primary_sum is not None:
                for k in keys:
                    if all(f in points for f in k):
                        sums[k].append(sum(points[f].distance for f in k)
                                       - primary_sum)
    return {
        "p_selected": {k: v / resamples for k, v in counts.items()},
        "se_delta_sum": {k: (statistics.stdev(v) if len(v) > 1 else None)
                         for k, v in sums.items()},
    }


# ----------------------------------------------------------------- a model
def model_report(root: pathlib.Path, model_key: str, *,
                 resamples: int = RESAMPLES) -> dict[str, Any]:
    source = open_pilot(root, model_key)
    supported = [int(f) for f in source.gate2["supported_frames"]]
    n_star = {f: int(source.gate2["by_frame"][str(f)]["n_star"])
              for f in supported}
    vectors = a_per_topic(source.model_dir, n_star_by_frame=n_star)
    cand_topics = candidate_topics(source.model_dir)
    by_frame: dict[str, Any] = {}
    for frame in PS.FRAMES:
        if frame not in supported:
            by_frame[str(frame)] = frame_sensitivity(source, frame,
                                                     a_vector=(),
                                                     resamples=resamples)
            continue
        vector = _vector(vectors[frame])
        by_frame[str(frame)] = frame_sensitivity(
            source, frame, a_vector=vector,
            a_topics=sorted(vectors[frame]),
            candidate_topics_of_frame=cand_topics.get(frame),
            resamples=resamples)
    material = sorted(int(f) for f, b in by_frame.items()
                      if b.get("material"))
    return {
        "tool": "tools/v8_reference_sensitivity.py",
        "finding": "5 --- the reference triple's selection margin",
        "root": str(root), "root_name": root.name, "model_key": model_key,
        "study_id": source.study_id,
        "record_hashes": dict(source.record_hashes),
        "supported_frames": supported,
        "resamples": resamples,
        "topic_pairing_verified": bool(cand_topics),
        "rule": SENSITIVITY_RULE,
        "selection_unchanged": (
            "R1/R2/R3 remain the frozen primary triple and R4/R5 the frozen "
            "backups. Delta_R(f) is re-formed over every admissible triple "
            "of the five frozen families from the same generated cells in "
            "the confirmatory analysis (confirm/analysis.py, member family "
            "F_REFSENS, planned on the MEMBERSHIP record's "
            "reference_sensitivity block). This tool selects nothing."),
        "bootstrap_holds_fixed": (
            "family admission (the full V(R)) is not re-evaluated; the "
            "resample re-forms iota_R and iota_A and re-runs the ranking "
            "and structural selection over the families the pilot found "
            "LOCAL-valid, so the probability is a lower bound on the "
            "frozen triple's total variability"),
        "by_frame": by_frame,
        "n_material_frames": len(material),
        "material_frames": material,
    }


# ------------------------------------------------------------------ report
def _f(value: float | None, places: int = 4) -> str:
    return "—" if value is None else f"{value:.{places}f}"


def markdown(reports: Sequence[Mapping[str, Any]]) -> str:
    out: list[str] = []
    p = out.append
    p("# Reference-triple sensitivity (finding 5)\n")
    p("How tied was §13.8's choice of the three core references on each "
      "pilot frame? Produced by `tools/v8_reference_sensitivity.py` from "
      "the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` records and "
      "the frames' own per-topic vectors. Every signature is verified on "
      "read (`confirm.pilot_import.open_pilot`).\n")
    p("**Nothing here changes a selection.** R1/R2/R3 stay the frozen "
      "primary triple and R4/R5 stay the frozen backups. The confirmatory "
      "analysis already re-forms Δ_R(f) over **every admissible triple of "
      "the five frozen families** from the same generated cells — the "
      "`F_REFSENS` member family in `src/dci1v8dev/confirm/analysis.py`, "
      "planned on the `MEMBERSHIP` record's `reference_sensitivity` block "
      "(`confirm/membership.py`). What this report adds is how much of the "
      "ranking that produced R1..R3 was signal.\n")
    p(f"**Convention.** {SENSITIVITY_RULE}. Neither number is a registered "
      "threshold; both are stated in advance and every count they read is "
      "printed beside them.\n")
    p("**What the bootstrap holds fixed.** Family admission — the full "
      "V(R), whose own components resample — is not re-evaluated. A "
      "resample re-forms ι_R and ι_A on resampled topics (paired: one topic "
      "index for A and every rung) at the measured κ, then re-runs the "
      "within-family rung choice and §13.8's ranking, group distinctness, "
      "Tier-1 look-ahead and role substitution over the families the pilot "
      "found LOCAL-valid. P(primary re-selected) is therefore a **lower "
      "bound** on the frozen triple's total variability.\n")

    p("## 1. Per model × frame\n")
    p("| model | f | LOCAL-valid families | frozen | triples (all valid / "
      "frozen) | primary triple | distances \\|ι_R−ι_A\\| | SE(d) | closest "
      "alternative | Δsum (SE) | P(primary) | flag |")
    p("|---|---:|---:|---:|---:|---|---|---|---|---|---:|---|")
    for rep in reports:
        for key in sorted(rep["by_frame"], key=int):
            b = rep["by_frame"][key]
            if not b.get("supported"):
                p(f"| `{rep['model_key']}` | {key} | — | — | — | "
                  f"*unsupported at Gate 2* | — | — | — | — | — | — |")
                continue
            prim = b["primary"]
            dists = " / ".join(f"{m['label']} {m['distance']:.4f}"
                               for m in prim["members"]) or "—"
            ses = " / ".join(_f(m["se_distance_paired"])
                             for m in prim["members"]) or "—"
            fams = "+".join(prim["families"]) or "*none*"
            alt = b["closest_alternative"]
            alt_s = "—" if alt is None else "+".join(alt["families"])
            gap = ("—" if alt is None else
                   f"{alt['delta_sum']:+.4f} ({_f(alt['se_delta_sum'])})")
            pp = _f(b["p_primary_reselected"], 3)
            p(f"| `{rep['model_key']}` | {key} | "
              f"{b['n_local_valid_families']} | "
              f"{b['n_frozen_families']} | "
              f"{b['n_admissible_triples_all_valid']} / "
              f"{b['n_admissible_triples_frozen_five']} | {fams} | {dists} | "
              f"{ses} | {alt_s} | {gap} | {pp} | **{b['flag']}** |")
    p("")

    p("## 2. Every admissible triple\n")
    for rep in reports:
        p(f"### `{rep['model_key']}` ({rep['root_name']})\n")
        for key in sorted(rep["by_frame"], key=int):
            b = rep["by_frame"][key]
            if not b.get("supported"):
                continue
            frozen = ", ".join(f"{b['frozen_slots'][f]}={f}"
                               for f in b["frozen_families"])
            p(f"**frame {key}** — n\\*={b['n_star']}, m\\*={b['m_star']}, "
              f"ι_A={b['iota_a']:.4f} (SE {_f(b['se_iota_a'])}, "
              f"{b['n_topics']} topics), state {b['state']}, frozen: "
              f"{frozen or '—'}\n")
            if not b["triples"]:
                p(f"*No admissible triple: the frame holds "
                  f"{b['n_local_valid_families']} LOCAL-valid "
                  "family/families and §13.8 needs three feature groups.*\n")
                continue
            p("| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | "
              "within 1 SE | P(selected) |")
            p("|---|---|---:|---:|---:|:-:|---:|")
            for t in b["triples"]:
                mark = " **(primary)**" if t["is_primary"] else ""
                p(f"| {'+'.join(t['families'])}{mark} | "
                  f"{'yes' if t['all_frozen'] else 'no'} | "
                  f"{t['sum_distance']:.4f} | "
                  f"{'—' if t['delta_sum'] is None else format(t['delta_sum'], '+.4f')} | "
                  f"{_f(t['se_delta_sum'])} | "
                  f"{'✓' if t['within_1se_of_primary'] else ''} | "
                  f"{t['p_selected']:.3f} |")
            p("")

    p("## 3. Verdict\n")
    frames = [(r["model_key"], k, b) for r in reports
              for k, b in sorted(r["by_frame"].items(), key=lambda kv: int(kv[0]))
              if b.get("supported") and b["primary"]["families"]]
    n = len(frames)
    n_material = sum(1 for _, _, b in frames if b["material"])
    n_forced = sum(1 for _, _, b in frames if b["flag"] == "FORCED")
    n_tied = sum(1 for _, _, b in frames if b["tied_alternatives"])
    n_low = sum(1 for _, _, b in frames
                if (b["p_primary_reselected"] or 0.0) < MIN_RESELECTION)
    verdict = ("CONFIRMED" if n and n_material >= (n + 1) // 2
               else "PARTIALLY CONFIRMED" if n_material
               else "NOT CONFIRMED")
    p(f"**Finding 5 {verdict}.** Of {n} model × frame cells with an "
      f"identified core triple, {n_material} are MATERIAL: {n_tied} carry an "
      f"admissible alternative triple whose total distance is within "
      f"{WITHIN_SE:g} bootstrap SE of the frozen triple's, and {n_low} "
      f"re-select the frozen triple on fewer than "
      f"{MIN_RESELECTION:.3f} of {RESAMPLES} topic resamples. Of the "
      f"{n - n_material} that are not, {n_forced} are `FORCED` — the "
      "frame's LOCAL-valid pool admits exactly one triple, so nothing was "
      "chosen and P(primary) = 1 says only that there was no alternative. "
      f"That leaves {n - n_material - n_forced} cell(s) on which the "
      "registered ranking was genuinely well separated.\n")
    n_outranked = sum(1 for _, _, b in frames
                      if b["alternatives_selected_more_often_than_the_primary"])
    n_choice = sum(1 for _, _, b in frames if len(b["triples"]) > 1)
    p(f"On {n_outranked} of the {n_choice} cells where the rule had more "
      "than one admissible triple to choose from, the bootstrap selects "
      "some alternative **more often than the frozen one**: the ranking "
      "did not merely fail to separate the candidates, it put a family "
      "first that a resample of the same topics would usually not have "
      "put first.\n")
    if frames:
        worst = min(frames, key=lambda t: t[2]["p_primary_reselected"] or 0.0)
        best = max(frames, key=lambda t: t[2]["p_primary_reselected"] or 0.0)
        p(f"P(primary re-selected) ranges from "
          f"{worst[2]['p_primary_reselected']:.3f} "
          f"(`{worst[0]}` frame {worst[1]}) to "
          f"{best[2]['p_primary_reselected']:.3f} "
          f"(`{best[0]}` frame {best[1]}).\n")
    p("The consequence is a reading instruction, not an amendment: on a "
      "MATERIAL frame the frozen triple is one of several the registered "
      "rule could equally have produced, so `F_REFSENS`'s spread over the "
      "admissible triples of the five frozen families is the estimate's "
      "sensitivity to a selection the data did not determine, and a Δ_R(f) "
      "that moves across those triples should be read as such. On a "
      "`FORCED` frame there was no choice to make and the pool is the "
      "binding constraint (§13.15's five families, not the ranking); on a "
      "`STABLE` frame the spread is a robustness check that the ranking "
      "was well separated.\n")
    p("Every count above is recomputed by "
      "`python3 tools/v8_reference_sensitivity.py --all`; the machine-"
      "readable form is `reference_sensitivity.<root>.<model>.json` beside "
      "this file.\n")
    return "\n".join(out) + "\n"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {("+".join(k) if isinstance(k, tuple) else str(k)):
                _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="a pilot root (e.g. evidence/dci1v8-pilot-r9)")
    ap.add_argument("--model", default=None, help="the model key")
    ap.add_argument("--all", action="store_true",
                    help="every (root, model) of DEFAULT_SOURCES")
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if args.all:
        pairs = [(EVIDENCE / name, model) for name, model in DEFAULT_SOURCES]
    elif args.root and args.model:
        pairs = [(pathlib.Path(args.root).resolve(), args.model)]
    else:
        ap.error("give --root and --model, or --all")
    out = pathlib.Path(args.out) if args.out else REPORTS
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for root, model in pairs:
        rep = model_report(pathlib.Path(root).resolve(), model,
                           resamples=args.resamples)
        reports.append(rep)
        stem = f"reference_sensitivity.{rep['root_name']}.{model}"
        (out / f"{stem}.json").write_text(
            json.dumps(_jsonable(rep), indent=1, sort_keys=True) + "\n")
        print(f"wrote {out / (stem + '.json')}  "
              f"({rep['n_material_frames']} MATERIAL frames)")
    (out / "REPORT.md").write_text(markdown(reports))
    print(f"wrote {out / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
