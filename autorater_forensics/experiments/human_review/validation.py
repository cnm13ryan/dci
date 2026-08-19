"""Human-vs-verifier validation statistics and the sequential stopping
rule for the calibration set.

The quantity under test is the **disagreement rate of the frozen
deterministic S0 verifier against a blind human reading, conditional on
the verifier's own class** — exactly the criterion the registered Gate 1
human audit applies (``dci1v3/stages/gate1.py::human_audit``), with the
same one-sided 95% Wilson upper bound.  Nothing here can change (F_A):
the verifier remains the primary instrument; these labels bound how often
it is wrong.

Two bounds are reported per class:

``representative``  the SRS component — a design-based bound on the
                    population disagreement rate.  The >=5% claim is made
                    on this component and on no other.
``boundary``        the purposive stress component — deliberately hard
                    cases.  Conservative by construction and NOT a
                    population estimate; reported so a systematic verifier
                    failure cannot hide behind a clean random sample.

Wilson bounds mirror ``dci1v3.analysis.stats`` numerically; the forensics
workspace never imports the scientific package, and a test asserts the two
implementations agree.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parents[1] / "src"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import records_io                          # noqa: E402
import sampling                            # noqa: E402

Z_TWO_SIDED_95 = 1.959963984540054
Z_ONE_SIDED_95 = 1.6448536269514722

#: The registered Gate 1 bound (A1, ``GATE1_DISAGREEMENT_MAX``) and the
#: strengthened target this extension exists to reach.
TARGETS = (0.10, 0.05)
REGISTERED_TARGET = 0.10
STRENGTHENED_TARGET = 0.05

#: Refuse to plan beyond this; a requirement above it means the bound is
#: not reachable with a plausible annotation budget.
MAX_PLANNED_N = 10_000

H2V = {"SATISFIES": "pass", "VIOLATES": "fail"}


class ValidationError(Exception):
    """A precondition for computing the validation report failed."""


# ------------------------------------------------------------- intervals
def wilson_interval(successes: int, trials: int,
                    z: float = Z_TWO_SIDED_95) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("Wilson interval needs at least one trial")
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / trials
                                   + z * z / (4 * trials * trials))
    return (max(0.0, centre - half), min(1.0, centre + half))


def wilson_upper_one_sided(disagreements: int, trials: int) -> float:
    """The one-sided 95% Wilson upper bound on a proportion."""
    return wilson_interval(disagreements, trials, z=Z_ONE_SIDED_95)[1]


def required_n(errors: int, target: float,
               limit: int = MAX_PLANNED_N) -> int | None:
    """The smallest class size whose one-sided 95% Wilson upper bound
    meets ``target`` **assuming no further disagreements**.

    This is a planning number, not a prediction: it answers "how many more
    clean labels would close the gap", which is the only question the
    sequential rule needs.  It is finite for any fixed error count because
    the observed rate falls as n grows; ``reachable_at_observed_rate``
    reports the separate question of whether the bound is attainable if
    the *rate* persists.
    """
    if errors < 0 or not 0 < target < 1:
        raise ValueError("errors >= 0 and 0 < target < 1 required")
    n = max(errors, 1)
    while n <= limit:
        if wilson_upper_one_sided(errors, n) <= target:
            return n
        n += 1
    return None


def reachable_at_observed_rate(errors: int, trials: int,
                               target: float) -> bool:
    """Whether the target is attainable at all if the observed
    disagreement rate persists (the Wilson upper bound converges to the
    point estimate, so a rate at or above the target never meets it)."""
    if trials <= 0:
        return True
    return errors / trials < target


# ------------------------------------------------------------ population
def _index_population() -> dict[str, dict[str, Any]]:
    return {i["id"]: i for i in sampling.population()}


def _component_map(review_dir: Path) -> dict[str, dict[str, Any]]:
    """id -> {component, boundary_category, batch, inclusion_probability}.

    The initial 56-item E5 sample is the representative component of
    batch 0; every extension batch declares its own components.
    """
    out: dict[str, dict[str, Any]] = {}
    cal = json.loads((review_dir / "calibration_sample.json").read_text())
    for row in cal["samples"]:
        out[row["id"]] = {"component": "representative",
                          "boundary_category": None, "batch": 0,
                          "inclusion_probability":
                              row.get("inclusion_probability")}
    for path in sorted(review_dir.glob("extension_batch_*.json")):
        data = json.loads(path.read_text())
        for row in data["samples"]:
            out[row["id"]] = {
                "component": row["component"],
                "boundary_category": row["boundary_category"],
                "batch": data["batch"],
                "inclusion_probability": row["inclusion_probability"]}
    return out


# --------------------------------------------------------------- records
def load_human_records(paths_: Iterable[Path], *,
                       allow_synthetic: bool = False
                       ) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths_:
        for row in records_io.read_records(Path(path)):
            if row.get("synthetic") and not allow_synthetic:
                raise ValidationError(
                    f"{Path(path).name} contains synthetic (self-test) "
                    f"judgments — not usable as human evidence")
            records_io.validate_label(row["label"])
            rows.append(row)
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["id"] in seen and seen[row["id"]]["label"] != row["label"]:
            raise ValidationError(
                f"{row['id']} carries conflicting labels "
                f"({seen[row['id']]['label']} vs {row['label']}); a human "
                f"record is append-only and never re-judged")
        seen[row["id"]] = row
    return sorted(seen.values(), key=lambda r: r["id"])


def _check_hashes(records: list[dict[str, Any]],
                  pop: dict[str, dict[str, Any]]) -> None:
    for row in records:
        item = pop.get(row["id"])
        if item is None:
            raise ValidationError(
                f"{row['id']} is not in the registered dev-half "
                f"population; the record does not describe this study")
        recorded = row.get("response_sha256")
        if recorded and recorded != item["response_sha256"]:
            raise ValidationError(
                f"{row['id']}: the response the human judged "
                f"({recorded[:12]}) is not the response in registered "
                f"evidence ({item['response_sha256'][:12]})")


# ----------------------------------------------------------- class stats
def class_block(cases: int, disagreements: int) -> dict[str, Any]:
    block: dict[str, Any] = {
        "cases": cases,
        "disagreements": disagreements,
        "error_rate": (disagreements / cases) if cases else None,
        "wilson_upper_one_sided_95": (
            wilson_upper_one_sided(disagreements, cases)
            if cases else None),
    }
    block["meets"] = {}
    block["required_n"] = {}
    block["additional_labels_required"] = {}
    block["reachable_at_observed_rate"] = {}
    for target in TARGETS:
        key = f"{target:.2f}"
        upper = block["wilson_upper_one_sided_95"]
        block["meets"][key] = bool(upper is not None and upper <= target)
        need = required_n(disagreements, target)
        block["required_n"][key] = need
        block["additional_labels_required"][key] = (
            None if need is None else max(0, need - cases))
        block["reachable_at_observed_rate"][key] = \
            reachable_at_observed_rate(disagreements, cases, target)
    return block


def _blocks(pairs: list[tuple[str, str]]) -> dict[str, dict[str, Any]]:
    """pairs of (verifier_class, human_label) restricted to semantic
    labels; returns the per-class block keyed by verifier class."""
    out = {}
    for cls in ("pass", "fail"):
        cases = [h for c, h in pairs if c == cls]
        disagreements = sum(1 for h in cases if H2V[h] != cls)
        out[cls] = class_block(len(cases), disagreements)
    return out


# ---------------------------------------------------------------- report
def build_report(*, review_dir: Path, record_paths: Iterable[Path],
                 allow_synthetic: bool = False,
                 max_total_labels: int | None = 150) -> dict[str, Any]:
    review_dir = Path(review_dir)
    record_paths = [Path(p) for p in record_paths]
    records = load_human_records(record_paths,
                                 allow_synthetic=allow_synthetic)
    pop = _index_population()
    _check_hashes(records, pop)
    components = _component_map(review_dir)
    sealed = sampling.sealed_ids()
    leaked = sorted(r["id"] for r in records if r["id"] in sealed)
    if leaked:
        raise ValidationError(
            f"{len(leaked)} human record(s) fall inside the SEALED "
            f"reserved final-check set; the seal is broken")

    labelled = [r for r in records
                if r["label"] in records_io.SEMANTIC_LABELS]
    abstentions = [r for r in records
                   if r["label"] == records_io.ABSTENTION]
    unassigned = sorted(r["id"] for r in records
                        if r["id"] not in components)

    def pairs(rows, component=None):
        return [(pop[r["id"]]["verifier_class"], r["label"]) for r in rows
                if component is None
                or components.get(r["id"], {}).get("component") == component]

    table = Counter((r["label"], pop[r["id"]]["verifier_class"])
                    for r in records)
    agreements = sum(1 for r in labelled
                     if H2V[r["label"]] == pop[r["id"]]["verifier_class"])
    presented = len(components)
    by_component = {
        "representative": _blocks(pairs(labelled, "representative")),
        "boundary": _blocks(pairs(labelled, "boundary")),
        "pooled": _blocks(pairs(labelled)),
    }
    # The per-class target is defined on the design-based component only.
    # The purposive stress component is conservative by construction, so a
    # Wilson bound over it is not a population bound and no target applies.
    for component, applies in (("representative", True),
                               ("boundary", False), ("pooled", False)):
        for cls in ("pass", "fail"):
            by_component[component][cls]["target_applies"] = applies

    discordant = [{
        "id": r["id"],
        "human": r["label"],
        "verifier_class": pop[r["id"]]["verifier_class"],
        "target_n": pop[r["id"]]["n"],
        "s0_count": pop[r["id"]]["s0_count"],
        "response_words": pop[r["id"]]["response_words"],
        "finish_reason": pop[r["id"]]["finish_reason"],
        "component": components.get(r["id"], {}).get("component"),
        "boundary_category":
            components.get(r["id"], {}).get("boundary_category"),
    } for r in labelled
        if H2V[r["label"]] != pop[r["id"]]["verifier_class"]]

    operational = {
        "note": ("reported for the instrument, never merged into a human "
                 "label: an operational failure is not a judgment"),
        "human_abstentions": len(abstentions),
        "abstention_ids": sorted(r["id"] for r in abstentions),
        "pool_finish_reason": dict(Counter(
            pop[r["id"]]["finish_reason"] for r in records)),
        "registered_judge_statuses": dict(Counter(
            status for r in records
            for status in pop[r["id"]]["judge_round_statuses"].values())),
    }

    report = {
        "criterion": {
            "quantity": ("human-vs-verifier disagreement rate, "
                         "conditional on the deterministic verifier's "
                         "class"),
            "interval": "one-sided 95% Wilson upper bound",
            "registered_target": REGISTERED_TARGET,
            "strengthened_target": STRENGTHENED_TARGET,
            "claim_component": "representative",
        },
        "integrity": {
            "records": [records_io.verify_all(d) for d in
                        sorted({p.parent for p in record_paths})],
            "sealed_set_sha256": sampling.sealed_digest(),
            "sealed_ids_labelled": 0,
        },
        "counts": {
            "presented": presented,
            "records": len(records),
            "labelled": len(labelled),
            "abstentions": len(abstentions),
            "coverage": (len(labelled) / len(records)) if records else None,
            "response_rate": (len(records) / presented) if presented else None,
            "unassigned_to_a_sample_set": unassigned,
        },
        "table_human_x_verifier": {
            f"{human}|{cls}": count for (human, cls), count
            in sorted(table.items())},
        "overall_accuracy": (agreements / len(labelled)) if labelled else None,
        "by_component": by_component,
        "discordant": discordant,
        "operational": operational,
    }
    report["stopping"] = stopping_decision(
        report, max_total_labels=max_total_labels)
    return report


# ------------------------------------------------------- sequential rule
def stopping_decision(report: dict[str, Any], *,
                      max_total_labels: int | None = 150
                      ) -> dict[str, Any]:
    """After each completed batch: does each class already meet the bound,
    and if not, how many further clean labels does it need?

    The requirement is recomputed from the *observed* disagreement count,
    never assumed to stay at the original target — that is the whole point
    of the rule.  When the observed rate is at or above a target, the rule
    reports UNREACHABLE rather than a larger number, because no amount of
    additional labelling meets the bound at that rate.
    """
    primary = report["by_component"]["representative"]
    per_class: dict[str, Any] = {}
    decision = "STOP"
    for cls in ("pass", "fail"):
        block = primary[cls]
        entry: dict[str, Any] = {"cases": block["cases"],
                                 "disagreements": block["disagreements"]}
        for target in TARGETS:
            key = f"{target:.2f}"
            if block["meets"][key]:
                status = "MET"
            elif not block["reachable_at_observed_rate"][key]:
                status = "UNREACHABLE_AT_OBSERVED_RATE"
            elif block["required_n"][key] is None:
                status = "UNREACHABLE_WITHIN_PLANNING_LIMIT"
            else:
                status = "CONTINUE"
            entry[key] = {
                "status": status,
                "additional_labels_required":
                    block["additional_labels_required"][key],
            }
        per_class[cls] = entry
        strengthened = entry[f"{STRENGTHENED_TARGET:.2f}"]
        if strengthened["status"].startswith("UNREACHABLE"):
            decision = "ESCALATE"
        elif strengthened["status"] == "CONTINUE" and decision != "ESCALATE":
            decision = "CONTINUE"

    extra = sum(e[f"{STRENGTHENED_TARGET:.2f}"]
                ["additional_labels_required"] or 0
                for e in per_class.values())
    # everything already drawn will be labelled, plus whatever the rule
    # still requires on top of it
    projected = max(report["counts"]["presented"],
                    report["counts"]["records"] + extra)
    budget = None
    if max_total_labels is not None:
        budget = {
            "max_total_labels": max_total_labels,
            "projected_total_labels": projected,
            "within_budget": projected <= max_total_labels,
        }
    return {
        "decision": decision,
        "per_class": per_class,
        "next_batch_representative_targets": {
            cls: per_class[cls][f"{STRENGTHENED_TARGET:.2f}"]
            ["additional_labels_required"] or 0
            for cls in ("pass", "fail")},
        "budget": budget,
        "interpretation": {
            "STOP": "both classes meet the strengthened bound; stop",
            "CONTINUE": "draw the next batch with the stated per-class "
                        "targets, then re-run this report",
            "ESCALATE": "the observed disagreement rate cannot meet the "
                        "target at any sample size; this is a finding "
                        "about the verifier, not a sampling shortfall",
        }[decision],
    }
