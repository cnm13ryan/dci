"""Block-level estimators (§11, §12, §14).

The block is the only unit: every estimator consumes a ``BlockTable`` whose
entries are per-(block, arm) scalars — no estimator accepts a response-level
index (§12 function-signature check). Post-treatment quantities exist here
only for the declared diagnostic families (F5, F6) and checks (§16), never
as covariates, filters, stratifiers, or weights of a primary estimand (§21).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C

_REFS = ("AR1", "AR2", "AR3")


@dataclass
class BlockTable:
    """Per-block, per-arm scalars for the four primary arms (+ diagnostics)."""

    block_ids: list[str]
    order: np.ndarray                       # str array len B
    f: dict[str, np.ndarray]                # rule -> [B × 4] failures (0/1)
    non_behavioural: np.ndarray             # [B × 4] 0/1
    uptake: np.ndarray                      # [B × 4] 0/1 (added pass)
    category: np.ndarray                    # [B × 4] object (category | "")
    target_alone_failure: np.ndarray = field(default=None)   # [B] 0/1
    topic_alone_pass: np.ndarray = field(default=None)       # [B] 0/1

    ARM_INDEX = {arm: i for i, arm in enumerate(C.PRIMARY_ARMS)}

    def __post_init__(self):
        b = len(self.block_ids)
        for rule, matrix in self.f.items():
            if matrix.shape != (b, 4):
                raise ProtocolError(f"{rule}: block table shape mismatch")
        if len(set(self.block_ids)) != b:
            raise ProtocolError("duplicate block identities")

    @property
    def n_blocks(self) -> int:
        return len(self.block_ids)

    def stratum(self, order: str) -> np.ndarray:
        return np.flatnonzero(self.order == order)


def from_primary_rows(rows: list[dict], *, n: int) -> BlockTable:
    """Build the block table from accepted primary rows (one per cell)."""
    blocks: dict[str, dict[str, dict]] = {}
    orders: dict[str, str] = {}
    for row in rows:
        arm_map = blocks.setdefault(row["block_id"], {})
        if row["arm"] in arm_map:
            raise ProtocolError(f"duplicate accepted primary row for "
                                f"{row['block_id']}:{row['arm']}")
        arm_map[row["arm"]] = row
        orders[row["block_id"]] = row["order"]
    block_ids = sorted(blocks)
    for block_id in block_ids:
        if set(blocks[block_id]) != set(C.ARMS):
            raise ProtocolError(f"{block_id}: missing cell; the analysis "
                                f"fails closed")
    b = len(block_ids)
    f = {rule: np.zeros((b, 4), dtype=float)
         for rule in ("s0", "s1", "s2", "s3")}
    non_behavioural = np.zeros((b, 4), dtype=float)
    uptake = np.zeros((b, 4), dtype=float)
    category = np.full((b, 4), "", dtype=object)
    target_alone = np.zeros(b, dtype=float)
    topic_alone = np.zeros(b, dtype=float)
    for i, block_id in enumerate(block_ids):
        for arm in C.PRIMARY_ARMS:
            row = blocks[block_id][arm]
            j = BlockTable.ARM_INDEX[arm]
            verdicts = row["verdicts"]
            for rule in ("s0", "s1", "s2", "s3"):
                f[rule][i, j] = 0.0 if verdicts[rule] == n else 1.0
            non_behavioural[i, j] = float(row["non_behavioural"])
            uptake[i, j] = float(verdicts.get("added_pass", False))
            category[i, j] = row.get("failure_category", "")
        target_alone[i] = 0.0 if blocks[block_id]["A"]["verdicts"]["s0"] \
            == n else 1.0
        topic_alone[i] = 1.0 if blocks[block_id]["TOPIC"]["verdicts"]["s0"] \
            == n else 0.0
    return BlockTable(
        block_ids=block_ids,
        order=np.array([orders[b_] for b_ in block_ids], dtype=object),
        f=f, non_behavioural=non_behavioural, uptake=uptake,
        category=category, target_alone_failure=target_alone,
        topic_alone_pass=topic_alone)


def contrast_vector(table: BlockTable, *, rule: str = "s0") -> np.ndarray:
    """D_i = F_i,B − (F_i,R1 + F_i,R2 + F_i,R3) / 3."""
    f = table.f[rule]
    return f[:, 0] - f[:, 1:4].mean(axis=1)


@dataclass(frozen=True)
class Member:
    """One inferential quantity: a per-block vector and a scope."""

    name: str
    family: str
    values: np.ndarray                     # length B
    scope: str                             # order name or "all"


def family_members(table: BlockTable) -> list[Member]:
    """Every member of families F1–F6 (§14), in registered order."""
    members: list[Member] = []
    d0 = contrast_vector(table, rule="s0")
    members.append(Member("tau_target_first", "F1", d0, C.TARGET_FIRST))
    members.append(Member("tau_added_first", "F1", d0, C.ADDED_FIRST))
    f = table.f["s0"]
    for (j, k) in ((1, 2), (1, 3), (2, 3)):
        members.append(Member(f"delta_{j}{k}", "F2",
                              f[:, j] - f[:, k], "all"))
    for j, ref in enumerate(_REFS, start=1):
        for order in C.ORDERS:
            members.append(Member(f"per_ref_{ref}_{order}", "F3",
                                  f[:, 0] - f[:, j], order))
    for rule in ("s1", "s2", "s3"):
        d = contrast_vector(table, rule=rule)
        for order in C.ORDERS:
            members.append(Member(f"tau_{rule}_{order}", "F4", d, order))
    for cat in C.FAILURE_CATEGORIES:
        focal = (table.category[:, 0] == cat).astype(float)
        refs = (table.category[:, 1:4] == cat).astype(float).mean(axis=1)
        members.append(Member(f"failcat_{cat}", "F5", focal - refs, "all"))
    nb = table.non_behavioural
    for j, ref in enumerate(_REFS, start=1):
        members.append(Member(f"nonbehavioural_{ref}", "F6",
                              nb[:, 0] - nb[:, j], "all"))
    counts = {fam: sum(1 for m in members if m.family == fam)
              for fam in C.FAMILY_SIZES}
    if counts != C.FAMILY_SIZES:
        raise ProtocolError(f"family sizes {counts} != registered "
                            f"{C.FAMILY_SIZES}")
    return members


def uptake_members(table: BlockTable) -> list[Member]:
    """§16 manipulation-check differences (focal-to-reference uptake)."""
    up = table.uptake
    return [Member(f"uptake_diff_{ref}", "uptake", up[:, 0] - up[:, j],
                   "all") for j, ref in enumerate(_REFS, start=1)]


def scope_indices(table: BlockTable, scope: str) -> np.ndarray:
    if scope == "all":
        return np.arange(table.n_blocks)
    return table.stratum(scope)


def point_estimate(table: BlockTable, member: Member) -> float:
    return float(member.values[scope_indices(table, member.scope)].mean())
