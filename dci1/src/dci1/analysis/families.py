"""Multiplicity families F1–F6 (prereg §14) as data, closed at freeze.

Every quantity carrying an inferential statement belongs to exactly one family
declared here; anything computed and absent from these lists is exploratory
and labelled so. Family sizes are asserted against the registered sizes.

`assemble_stats` turns the scored table into per-block columns: every family
member is the mean of a per-block column (possibly within one order stratum),
so all members evaluate on the same bootstrap draws.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from dci1.analysis.bootstrap import ColumnStat
from dci1.analysis.taxonomy import CATEGORIES
from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST
from dci1.protocol.constants import ARMS, FAMILY_SIZES, ProtocolError

_ORDERS = (TARGET_FIRST, ADDED_FIRST)
_REFS = ("ref1", "ref2", "ref3")


def family_members() -> dict[str, list[str]]:
    """The closed family declaration (prereg §14). Sizes asserted."""
    families = {
        "F1": [f"tau_{o}" for o in _ORDERS],
        "F2": ["delta_12", "delta_13", "delta_23"],
        "F3": [f"f3_{r}_{o}" for r in _REFS for o in _ORDERS],
        "F4": [f"tau_{o}_s{k}" for k in (1, 2, 3) for o in _ORDERS],
        "F5": [f"f5_{c}" for c in CATEGORIES],
        "F6": [f"f6_{r}" for r in _REFS],
    }
    for name, members in families.items():
        if len(members) != FAMILY_SIZES[name]:
            raise ProtocolError(
                f"family {name} has {len(members)} members, registered size "
                f"is {FAMILY_SIZES[name]}")
    return families


#: §16 gate quantities with simultaneous intervals; not a claim family.
CHECK_FAMILIES = {"uptake_diff": [f"uptake_diff_{r}" for r in _REFS]}

#: §22 quantities with marginal intervals only, supporting no claim.
SECONDARY_MARGINAL = (
    ["tau_pooled", "order_interaction", "target_alone_failure",
     "topic_alone_pass", "joint_compliance_focal"]
    + [f"uptake_{a}" for a in ("focal",) + _REFS]
    + [f"graded_{a}" for a in ("focal",) + _REFS]
)


def _grouped(scored_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}
    for row in scored_rows:
        entry = blocks.setdefault(row["block_id"],
                                  {"order": row["order"],
                                   "area": row["topic_id"].rsplit("-", 1)[0],
                                   "arms": {}})
        if row["arm"] in entry["arms"]:
            raise ProtocolError(
                f"duplicate row for cell ({row['block_id']}, {row['arm']})")
        entry["arms"][row["arm"]] = row
    for block_id, entry in blocks.items():
        if set(entry["arms"]) != set(ARMS):
            raise ProtocolError(f"block {block_id} lacks a complete six-arm "
                                f"matrix")
    return blocks


def assemble_stats(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-block columns for every family, check and secondary quantity."""
    blocks = _grouped(scored_rows)
    ids_by_stratum = {
        o: sorted(b for b, e in blocks.items() if e["order"] == o)
        for o in _ORDERS}

    def column(fn) -> dict[str, np.ndarray]:
        return {o: np.array([fn(blocks[b]) for b in ids_by_stratum[o]],
                            dtype=float)
                for o in _ORDERS}

    def f(entry, arm, rule="f_s0") -> float:
        return float(entry["arms"][arm][rule])

    def d_column(rule) :
        return column(lambda e: f(e, "focal", rule) -
                      (f(e, "ref1", rule) + f(e, "ref2", rule) +
                       f(e, "ref3", rule)) / 3.0)

    stats: list[ColumnStat] = []
    d0 = d_column("f_s0")
    for o in _ORDERS:
        stats.append(ColumnStat(f"tau_{o}", d0, o))
    stats.append(ColumnStat("tau_pooled", d0, "all"))
    for j, k in ((1, 2), (1, 3), (2, 3)):
        stats.append(ColumnStat(
            f"delta_{j}{k}",
            column(lambda e, j=j, k=k: f(e, f"ref{j}") - f(e, f"ref{k}")),
            "all"))
    for r in _REFS:
        col = column(lambda e, r=r: f(e, "focal") - f(e, r))
        for o in _ORDERS:
            stats.append(ColumnStat(f"f3_{r}_{o}", col, o))
    for k in (1, 2, 3):
        dk = d_column(f"f_s{k}")
        for o in _ORDERS:
            stats.append(ColumnStat(f"tau_{o}_s{k}", dk, o))
    for c in CATEGORIES:
        def cat_diff(e, c=c):
            def ind(arm):
                return 1.0 if e["arms"][arm]["failure_category"] == c else 0.0
            return ind("focal") - (ind("ref1") + ind("ref2") +
                                   ind("ref3")) / 3.0
        stats.append(ColumnStat(f"f5_{c}", column(cat_diff), "all"))
    for r in _REFS:
        stats.append(ColumnStat(
            f"f6_{r}",
            column(lambda e, r=r: float(e["arms"]["focal"]["non_behavioural"])
                   - float(e["arms"][r]["non_behavioural"])),
            "all"))
        stats.append(ColumnStat(
            f"uptake_diff_{r}",
            column(lambda e, r=r: float(e["arms"]["focal"]["uptake"]) -
                   float(e["arms"][r]["uptake"])),
            "all"))
    for arm in ("focal",) + _REFS:
        stats.append(ColumnStat(
            f"uptake_{arm}",
            column(lambda e, a=arm: float(e["arms"][a]["uptake"])), "all"))
        stats.append(ColumnStat(
            f"graded_{arm}",
            column(lambda e, a=arm: float(e["arms"][a]["graded"])), "all"))
    stats.append(ColumnStat(
        "joint_compliance_focal",
        column(lambda e: float(e["arms"]["focal"]["joint_compliance"])),
        "all"))
    stats.append(ColumnStat(
        "target_alone_failure",
        column(lambda e: f(e, "target_alone")), "all"))
    stats.append(ColumnStat(
        "topic_alone_pass",
        column(lambda e: 1.0 - f(e, "topic_alone")), "all"))

    # Descriptive per-area target failure in the focal arm (§22), via masks.
    areas = sorted({e["area"] for e in blocks.values()})
    for area in areas:
        stats.append(ColumnStat(
            f"area_focal_failure_{area}",
            column(lambda e: f(e, "focal")),
            "all",
            mask_by_stratum={
                o: np.array([1.0 if blocks[b]["area"] == area else 0.0
                             for b in ids_by_stratum[o]])
                for o in _ORDERS}))

    return {"stats": stats, "blocks": blocks,
            "ids_by_stratum": ids_by_stratum, "areas": areas}
