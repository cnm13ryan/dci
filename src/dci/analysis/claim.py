"""The reference-robust claim rule, and the invariants that make it fail closed.

WHY THIS MODULE EXISTS
----------------------
The primary v15 result is not "is one reference beaten". It is the INTERSECTION
claim: adding B changes failure on A relative to EVERY admitted reference, under
simultaneous uncertainty, separately per prompt order. An intersection claim is
only as strong as its least favourable member, so anything that removes a member
from the family strengthens the claim for free. That is a false positive.

Two pandas defaults conspire to do exactly that. `bootstrap_se` maps an exactly
zero bootstrap SD to NaN (it must: studentising by zero is undefined), and
`Series.min()`/`.max()` skip NaN by default. A reference whose task-level
contrast is identical on every task therefore produces NaN simultaneous bounds
and then vanishes from `sim_lower.min()`. The pre-repair implementation could
report `robust_positive=True` on five references while naming the sixth, at
tau=0.000, as the least favourable one in the same row of the same artifact.

The rule here refuses to answer instead. A degenerate contrast is an unanswered
hypothesis, never an absent one, and the remedy is precision -- not omission.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Iterable, Optional

from dci.statuses import GateStatus

# Columns the claim rule reads. Every one must be finite for every member of the
# family before the intersection claim may be evaluated.
REQUIRED_FINITE = ("estimate", "se", "sim_lower", "sim_upper")

CLAIM_PASS = GateStatus.PASS
CLAIM_INCONCLUSIVE = GateStatus.INCONCLUSIVE_PRECISION


def expected_family(references: Iterable[str],
                    orders: Iterable[str]) -> list[tuple[str, str]]:
    """The (reference, order) cells the primary estimator must deliver."""
    return [(str(j), str(o)) for o in orders for j in references]


def family_problems(primary: pd.DataFrame, references: Iterable[str],
                    orders: Iterable[str]) -> list[str]:
    """Structural defects in the primary table, as human-readable strings.

    Structural means: wrong cardinality, a missing or duplicated reference-order
    cell, a missing column. Non-finiteness is reported separately, because it is
    a precision failure rather than a construction failure and it carries a
    different remedy.
    """
    refs, ords_ = [str(r) for r in references], [str(o) for o in orders]
    want = expected_family(refs, ords_)
    problems: list[str] = []

    missing_cols = [c for c in (*REQUIRED_FINITE, "reference", "order")
                    if c not in primary.columns]
    if missing_cols:
        return [f"primary table is missing columns {missing_cols}"]

    if len(primary) != len(want):
        problems.append(
            f"primary family has {len(primary)} rows, expected "
            f"{len(want)} = {len(refs)} references x {len(ords_)} orders")

    seen = pd.Series(list(zip(primary["reference"].astype(str),
                              primary["order"].astype(str)))).value_counts()
    for cell in want:
        n = int(seen.get(cell, 0))
        if n == 0:
            problems.append(f"missing primary contrast for reference/order {cell}")
        elif n > 1:
            problems.append(f"reference/order {cell} appears {n} times, expected once")
    for cell in seen.index:
        if cell not in want:
            problems.append(f"unexpected primary contrast {tuple(cell)} in the family")
    return problems


def nonfinite_cells(primary: pd.DataFrame) -> pd.DataFrame:
    """One row per (reference, order) carrying a non-finite required quantity."""
    rows = []
    for key, row in primary.iterrows():
        bad = [c for c in REQUIRED_FINITE
               if not np.isfinite(pd.to_numeric(row.get(c), errors="coerce"))]
        if bad:
            rows.append({"contrast": str(key),
                         "reference": str(row.get("reference", "")),
                         "order": str(row.get("order", "")),
                         "nonfinite": ";".join(bad)})
    return pd.DataFrame(rows, columns=["contrast", "reference", "order", "nonfinite"])


def reference_robust_claim(primary: pd.DataFrame, references: Iterable[str],
                           orders: Iterable[str],
                           sim_attrs: Optional[dict] = None) -> pd.DataFrame:
    """Evaluate the intersection claim per order, failing closed.

    The claim is evaluated with skipna=False throughout, so a NaN propagates into
    the comparison and makes it False rather than disappearing. `inference_status`
    records WHY an order could not be claimed, which is the information the
    pre-repair artifact destroyed.

    `sim_attrs` is the `attrs` dict from `simultaneous_bounds`; when supplied, the
    calibrated family size is cross-checked against the requested one so that a
    critical value calibrated on 11 columns can never certify a 12-column claim.
    """
    refs = [str(r) for r in references]
    ords_ = [str(o) for o in orders]
    structural = family_problems(primary, refs, ords_)
    if structural:
        raise ValueError(
            "the primary inference family is structurally incomplete, so the "
            "reference-robust claim cannot be evaluated:\n  - "
            + "\n  - ".join(structural))

    nonfinite = nonfinite_cells(primary)
    degenerate_by_order = {
        o: sorted(nonfinite.query("order == @o")["reference"].astype(str).tolist())
        for o in ords_}

    attr_problems: list[str] = []
    if sim_attrs is not None:
        want_n = len(refs) * len(ords_)
        got_requested = int(sim_attrs.get("n_family_requested", want_n))
        got_calibrated = int(sim_attrs.get("n_family_calibrated", want_n))
        if got_requested != want_n:
            attr_problems.append(
                f"max-T family was built over {got_requested} contrasts, but the "
                f"declared primary family is {want_n}")
        if got_calibrated != got_requested:
            attr_problems.append(
                f"max-T critical value was calibrated on {got_calibrated} of "
                f"{got_requested} contrasts; the omitted ones are "
                f"{sim_attrs.get('degenerate', [])}")

    rows = []
    for o in ords_:
        sub = primary[primary["order"].astype(str) == o]
        bad = degenerate_by_order[o]
        # skipna=False: a degenerate member must poison the reduction, not vanish.
        lower_min = float(sub["sim_lower"].min(skipna=False))
        upper_max = float(sub["sim_upper"].max(skipna=False))
        est = pd.to_numeric(sub["estimate"], errors="coerce")
        tau_min = float(est.min(skipna=False))
        least = str(sub.loc[est.idxmin(), "reference"]) if est.notna().all() else ""
        ok = not bad and not attr_problems
        robust_positive = bool(ok and np.isfinite(lower_min) and lower_min > 0)
        robust_negative = bool(ok and np.isfinite(upper_max) and upper_max < 0)
        signs = np.sign(est.to_numpy(dtype=float))
        rows.append({
            "order": o,
            "inference_status": CLAIM_PASS if ok else CLAIM_INCONCLUSIVE,
            "n_references_declared": len(refs),
            "n_references_in_inference": int(len(sub) - len(bad)),
            "degenerate_references": ";".join(bad),
            "family_problems": "; ".join(attr_problems),
            "tau_min": tau_min,
            "least_favourable_reference": least,
            "simultaneous_lower_bound_on_min": lower_min,
            "simultaneous_upper_bound_on_max": upper_max,
            # all_same_sign is about DIRECTION, so an exact zero is not a third
            # sign: it is the absence of a direction and breaks unanimity.
            "all_same_sign": bool(np.all(signs > 0) or np.all(signs < 0)),
            "robust_positive": robust_positive,
            "robust_negative": robust_negative,
        })

    claim = pd.DataFrame(rows).set_index("order")
    claim["reference_robust_claim_supported"] = (
        claim["robust_positive"] | claim["robust_negative"])
    return claim


def claim_blockers(claim: pd.DataFrame) -> list[str]:
    """Per-order reasons the claim rule could not be evaluated, for the gate."""
    out = []
    for order, row in claim.iterrows():
        if row["inference_status"] == CLAIM_PASS:
            continue
        detail = []
        if row["degenerate_references"]:
            detail.append("degenerate contrasts for reference(s) "
                          + row["degenerate_references"])
        if row["family_problems"]:
            detail.append(row["family_problems"])
        out.append(f"[{order}] " + "; ".join(detail or ["non-finite inference"]))
    return out
