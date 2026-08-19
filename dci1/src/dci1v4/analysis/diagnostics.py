"""Registered secondary analyses and diagnostics (§12.1, §22, §23, §25).

Everything here is Tier-secondary and none of it can change a primary
conclusion. Three pieces carry real weight and are implemented as properties of
the emitter rather than as notes in a report:

* **the truncation-bound rule (§12.1, §25).** Any quantity derived from a cell
  whose realised truncation rate exceeds 0.10 is emitted as a bound and
  labelled as one, at every stage, including every accidental-compliance
  figure. ``bounded`` is the only constructor for such a quantity, so a caller
  cannot forget;
* **the failure taxonomy (§23, T-18).** Nine categories in a fixed priority
  order, applied to the **exact-count outcome only**, split by whether the
  realised margin is exactly one. It does not generalise to the word-length or
  budget outcomes and this module refuses to apply it to them;
* **the mediator (§22).** Response length is reported and never conditioned
  on. ``length_strata_description`` returns a descriptive within-strata
  decomposition and no mediation effect.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C


# ------------------------------------------------------- truncation bounding
def bounded(value: float, truncation_rate: float, *, quantity: str,
            cell_type: str) -> dict[str, Any]:
    """§12.1 / §25: emit a value, marked as a bound above the threshold."""
    is_bound = truncation_rate > C.TRUNCATION_BOUND_THRESHOLD
    record = {"quantity": quantity, "cell_type": cell_type, "value": value,
              "truncation_rate": truncation_rate, "is_bound": is_bound}
    if is_bound:
        record["label"] = (
            f"bound: the realised truncation rate {truncation_rate:.3f} in "
            f"{cell_type} exceeds {C.TRUNCATION_BOUND_THRESHOLD}, so this "
            f"figure is reported as a bound (§12.1)")
    return record


# ------------------------------------------------------------ failure taxonomy
REFUSAL_MARKERS = ("i cannot", "i can't", "i am unable", "as an ai",
                   "i'm sorry", "i am sorry")


def exact_count_failure_class(row: Mapping[str, Any], *, n: int) -> str:
    """§23's nine categories, applied in the registered priority order."""
    text = row.get("raw_response", "")
    lowered = text.lower()
    if row.get("empty") or not text.strip():
        return "empty"
    if row.get("truncated"):
        return "cut_off"
    if any(marker in lowered for marker in REFUSAL_MARKERS):
        return "refusal"
    alternatives = row.get("exact_count_alternatives", {})
    s0 = alternatives.get("s0", 0)
    s3 = alternatives.get("s3", s0)
    if s3 != s0:
        return "restatement"
    s2 = alternatives.get("s2", s0)
    if s2 > s0:
        return "target_inside_longer_word"
    if s0 == 0:
        return "zero_occurrences"
    if s0 < n:
        return "too_few"
    if s0 > n:
        return "too_many"
    return "other"


def failure_taxonomy(rows: Iterable[Mapping[str, Any]], *, n: int,
                     instrument: str = "A") -> dict[str, Any]:
    """The taxonomy with the §10.3 margin split. Exact-count only (T-18)."""
    if instrument != "A":
        raise ProtocolError(
            f"the §23 failure taxonomy describes how an exact-count "
            f"constraint failed and does not generalise to {instrument!r} "
            f"(T-18); the word-length and budget outcomes have no such "
            f"taxonomy registered")
    counts: dict[str, dict[str, int]] = {
        category: {stratum: 0 for stratum in C.FAILURE_MARGIN_STRATA}
        for category in C.FAILURE_TAXONOMY}
    total = 0
    for row in rows:
        entry = next((s for s in row.get("scores", [])
                      if s["kind"] == "A"), None)
        if entry is None or entry["passed"]:
            continue
        total += 1
        realised = row.get("exact_count_alternatives", {}).get("s0", 0)
        margin = abs(realised - n)
        stratum = ("margin_one" if margin == 1 else "margin_larger")
        counts[exact_count_failure_class(row, n=n)][stratum] += 1
    return {"instrument": "A", "n": n, "failures": total, "categories": counts,
            "priority_order": list(C.FAILURE_TAXONOMY)}


# --------------------------------------------------- graded manipulation check
def graded_manipulation_check(present: Sequence[float],
                              absent: Sequence[float]) -> dict[str, Any]:
    """§23: the graded score with the instruction present minus the same score
    on the cell where it is absent. This is the manipulation-check reading the
    construct memo found missing from every shipped analysis."""
    if not present or not absent:
        raise ProtocolError("the manipulation check needs both cells")
    mean_present = sum(present) / len(present)
    mean_absent = sum(absent) / len(absent)
    return {"graded_present": mean_present, "graded_absent": mean_absent,
            "difference": mean_present - mean_absent,
            "n_present": len(present), "n_absent": len(absent)}


# ------------------------------------------------------------- joint states
def joint_state_redistribution(by_configuration: Mapping[str, Mapping[str, Any]]
                               ) -> dict[str, Any]:
    """§11.5: the change in the four-state vector across configurations that
    do not alter which constraints are present.

    Reported **within** cell and never differenced across cells with different
    constituents, and computed post-unmasking like the vectors themselves.
    """
    configurations = sorted(by_configuration)
    cells = set.intersection(*[set(v["cells"]) for v in
                               by_configuration.values()]) \
        if by_configuration else set()
    out: dict[str, Any] = {}
    for cell_type in sorted(cells):
        vectors = {cfg: by_configuration[cfg]["cells"][cell_type]["vector"]
                   for cfg in configurations}
        keys = ("P(0,0)", "P(0,1)", "P(1,0)", "P(1,1)")
        out[cell_type] = {
            "per_configuration": vectors,
            "change": {k: vectors[configurations[-1]][k]
                       - vectors[configurations[0]][k] for k in keys}
            if len(configurations) == 2 else None,
        }
    return {"computed": "post-unmasking",
            "supports_claims": "none; reported within cell only (§11.5)",
            "configurations": configurations, "cells": out}


def joint_states(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """§11.5: the four-state vector per composed cell, and joint success.

    Computed **after unmasking only** and labelled as such: masking permutes
    the two companion labels of one generation independently, so these
    quantities are not computable in the masked phase (§20).
    """
    per_cell: dict[str, list[tuple[bool, bool]]] = {}
    for row in rows:
        if row.get("load") != 2:
            continue
        scores = sorted(row["scores"], key=lambda s: s["position"])
        per_cell.setdefault(row["cell_type"], []).append(
            (bool(scores[0]["passed"]), bool(scores[1]["passed"])))
    out: dict[str, Any] = {}
    for cell_type, pairs in sorted(per_cell.items()):
        total = len(pairs)
        vector = {
            "P(0,0)": sum(1 for a, b in pairs if not a and not b) / total,
            "P(0,1)": sum(1 for a, b in pairs if not a and b) / total,
            "P(1,0)": sum(1 for a, b in pairs if a and not b) / total,
            "P(1,1)": sum(1 for a, b in pairs if a and b) / total,
        }
        out[cell_type] = {"n": total, "vector": vector,
                          "joint_success": vector["P(1,1)"]}
    return {"computed": "post-unmasking",
            "supports_claims": "none; L1, L2 and L3 never read these (§20)",
            "cells": out}


# ---------------------------------------------------------------- mediator
def length_strata_description(observations: Sequence[Any], *,
                              strata: int = 4) -> dict[str, Any]:
    """§22: the registered descriptive within-strata decomposition.

    Response length is a **mediator**: reported, never conditioned on. This
    returns delivery-relevant compliance within strata of realised response
    length and emits **no mediation effect**; there is deliberately no function
    here that returns one.
    """
    lengths = sorted(o.response_words for o in observations)
    if not lengths:
        raise ProtocolError("no observations to stratify")
    cuts = [lengths[int(len(lengths) * (i + 1) / strata) - 1]
            for i in range(strata)]
    buckets: dict[int, list[Any]] = {i: [] for i in range(strata)}
    for obs in observations:
        for index, cut in enumerate(cuts):
            if obs.response_words <= cut:
                buckets[index].append(obs)
                break
    return {
        "role": "mediator",
        "note": ("reported and never conditioned on; no mediation effect is "
                 "claimed and no primary estimand is adjusted for length "
                 "(§22)"),
        "strata": [{"upper_word_count": cuts[i], "n": len(buckets[i]),
                    "mean_compliance": (sum(o.compliance for o in buckets[i])
                                        / len(buckets[i]))
                    if buckets[i] else None}
                   for i in range(strata)],
    }


# ------------------------------------------------- accidental compliance (§25)
def accidental_compliance(rows: Iterable[Mapping[str, Any]]
                          ) -> dict[str, Any]:
    """§25: the base rate at which an answer satisfies an absent constraint.

    Every figure from a cell whose truncation rate exceeds 0.10 is emitted as a
    bound, through ``bounded``.
    """
    per: dict[tuple[str, str], list[tuple[bool, bool]]] = {}
    for row in rows:
        for entry in row.get("accidental", []):
            per.setdefault((row["cell_type"], entry["slot"]), []).append(
                (bool(entry["passed"]), bool(row["truncated"])))
    out: dict[str, Any] = {}
    for (cell_type, slot), values in sorted(per.items()):
        rate = sum(1 for passed, _ in values if passed) / len(values)
        truncation = sum(1 for _, t in values if t) / len(values)
        out[f"{cell_type}|{slot}"] = {
            "n": len(values),
            **bounded(rate, truncation, quantity="accidental_compliance",
                      cell_type=cell_type)}
    return {"role": "accidental-compliance diagnostic; never an outcome (§25)",
            "figures": out}


# ------------------------------------------- the demoted v3 estimand, gated
DELTA_A_GATES = (
    "outcome headroom: the outcome constraint is not at ceiling",
    "a companion matched on measured solo compliance",
    "the configuration is quoted with the number",
)


def report_delta_a(estimate: float, *, configuration: str,
                   outcome_solo_compliance: float,
                   realised_gaps: Mapping[str, float],
                   caliper: float = C.REFERENCE_CALIPER) -> dict[str, Any]:
    """§11.5, §23: Delta^A is reported only with its three gates satisfied.

    It is v3's registered pooled swap effect re-expressed on the compliance
    scale, and v4 demotes it: three sign reversals in the legacy corpus, and it
    is structurally degenerate where the outcome is at ceiling. The gates are
    checked here and the number is **withheld** when any fails, rather than
    reported with a caveat attached.
    """
    at_ceiling = outcome_solo_compliance > 1 - C.GRADED_DEGENERACY_LOW * 10
    unmatched = sorted(name for name, gap in realised_gaps.items()
                       if abs(gap) > caliper)
    gates = {
        DELTA_A_GATES[0]: not at_ceiling,
        DELTA_A_GATES[1]: not unmatched,
        DELTA_A_GATES[2]: bool(configuration),
    }
    satisfied = all(gates.values())
    record: dict[str, Any] = {
        "quantity": "Delta^A", "status": "demoted diagnostic",
        "gates": gates, "gates_satisfied": satisfied,
        "configuration": configuration,
        "outcome_solo_compliance": outcome_solo_compliance,
        "unmatched_references": unmatched,
        "identity": ("Delta^A = mean_j C(A|A+R_j) - C(A|A+B) "
                     "= F(A|A+B) - mean_j F(A|A+R_j), the second form being "
                     "exactly v3's secondary.pooled_swap_effect"),
    }
    if satisfied:
        record["estimate"] = estimate
    else:
        record["withheld"] = ("the demoted diagnostic is reported only with "
                              "all three gates satisfied (§11.5)")
    return record


# -------------------------------------------- companion-difficulty sensitivity
def companion_difficulty_sensitivity(gaps: Mapping[str, float],
                                     losses: Mapping[str, float]
                                     ) -> dict[str, Any]:
    """§23: D(B <- R_j) reported against the realised solo-compliance gap
    between R_j and A. Descriptive only."""
    rows = [{"reference": name, "realised_gap": gaps[name],
             "D(B<-R)": losses.get(name)}
            for name in sorted(gaps)]
    flagged = [r for r in rows
               if abs(r["realised_gap"]) > C.REALISED_GAP_QUALIFIER]
    return {"rows": rows, "qualifier_threshold": C.REALISED_GAP_QUALIFIER,
            "references_exceeding_qualifier": [r["reference"] for r in flagged],
            "status": "descriptive only; supports no claim (§23)"}


# ------------------------------------------------- missingness and duplicates
def missingness_report(expected: Mapping[str, int], observed: Mapping[str, int]
                       ) -> dict[str, Any]:
    """§14.2: missingness per cell type, with the arm-differential rate."""
    per_type: dict[str, dict[str, Any]] = {}
    for cell_type, want in sorted(expected.items()):
        got = observed.get(cell_type, 0)
        rate = (want - got) / want if want else 0.0
        per_type[cell_type] = {"expected": want, "observed": got,
                               "missing_rate": rate,
                               "report_beside_primary":
                                   rate > C.MISSINGNESS_REPORT_THRESHOLD}
    rates = [v["missing_rate"] for v in per_type.values()]
    return {"per_cell_type": per_type,
            "arm_differential": (max(rates) - min(rates)) if rates else 0.0,
            "threshold": C.MISSINGNESS_REPORT_THRESHOLD}


# ------------------------------------------------------- descriptive splits
def by_group(observations: Sequence[Any], key: str) -> dict[str, Any]:
    """§23: compliance by subject area or by wording index, descriptive."""
    groups: dict[Any, list[float]] = {}
    for obs in observations:
        groups.setdefault(getattr(obs, key), []).append(obs.compliance)
    return {str(k): {"n": len(v), "mean_compliance": sum(v) / len(v)}
            for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}
