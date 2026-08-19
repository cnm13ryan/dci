"""Reproducible extension sampling for the human calibration set.

PREREGISTERED.md E5 fixes the initial 56-item stratified sample and the
extension rule: *"Extended only if the resulting uncertainty interval is
too wide for a decision, by drawing additional items with the same
procedure."* This module is that procedure, made explicit and testable.

What changes relative to the initial draw, and why
--------------------------------------------------
The initial sample allocated **proportionally over the whole dev-half
population** (680 verifier-pass / 303 verifier-fail), which yields 39
pass-class and 17 fail-class items.  The decision criterion is a
**per-class** one-sided 95% Wilson upper bound on the human-vs-verifier
disagreement rate, so the fail class — the smaller one — governs the
achievable bound.  Extension batches therefore allocate
**disproportionately across classes and proportionally within a class**:
each class is topped up to its own cumulative target.  Within a class the
draw is still a stratified SRS over source models with recorded inclusion
probabilities, so the class-conditional bound stays a valid design-based
bound.  Pooling *across* classes requires the recorded probabilities.

Two components, never silently mixed
------------------------------------
``representative``  SRS within (model x verifier class); the component the
                    per-class bound is computed on.
``boundary``        purposive, deterministic selection of deliberately hard
                    cases (edge-rule morphology, judge/verifier conflict,
                    off-by-one counts, truncation, high n, long text).
                    ``inclusion_probability`` is ``None``: this component is
                    an adversarial stress probe and is NOT a sample of the
                    population.  Its error rate must never be reported as a
                    population estimate; it is reported separately.

Exclusions are hard: anything already labelled by a human, anything whose
hidden fields have been revealed to a human, the initial calibration
sample, and every id in the SEALED reserved final-check set (read only as
an exclusion set, never sampled from, never written).

READ-ONLY over registered evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
WORKSPACE = HERE.parents[1]
for _p in (str(WORKSPACE / "src"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from forensics import dataset as dsmod     # noqa: E402
from forensics import paths                # noqa: E402

#: The registered base seed (PREREGISTERED.md E5/E11).  20260818 drew the
#: calibration sample and 20260819 sealed the reserved set; extension seeds
#: are derived through a separate domain so they can never collide.
BASE_SEED = 20260818
SEED_DOMAIN = "forensics:human-calibration-extension:v1"

CALIBRATION_SET = HERE / "calibration_sample.json"
SEALED_PATH = EXPERIMENTS / "reserved_final_check_ids.json"
RECORDS_DIR = HERE / "records"

#: Case-insensitive substring occurrences, used only to detect responses
#: where the plain substring count differs from the whole-word count
#: (embedded forms such as "howevermore" or "however-" ) — the cases the
#: frozen edge rules 3/4 exist for.
_HOWEVER = re.compile("however", re.IGNORECASE)

#: Purposive boundary categories in priority order, with the per-class
#: quota attempted before the next category is used.  A category that
#: cannot fill its quota rolls the shortfall forward; realised composition
#: and pool sizes are always recorded in the manifest.
BOUNDARY_QUOTAS: tuple[tuple[str, int], ...] = (
    ("embedded_or_adjacent_form", 1),
    ("judge_effort_disagreement", 1),
    ("judge_vs_verifier", 2),
    ("near_miss_count", 1),
    ("judge_non_valid_status", 1),
    ("generation_truncated", 1),
    ("high_n", 1),
    ("long_response", 1),
)

HIGH_N = 7
LONG_RESPONSE_QUANTILE = 0.90


class SamplingError(Exception):
    """A sampling precondition was violated (never a scientific status)."""


# --------------------------------------------------------------- seeding
def batch_seed(batch: int) -> int:
    """Domain-separated, reproducible seed for one extension batch."""
    digest = hashlib.sha256(
        f"{SEED_DOMAIN}:{BASE_SEED}:{batch}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


class _Rng:
    """Deterministic sampling without depending on CPython's ``random``
    internals: repeated SHA-256 draws over a sorted candidate list."""

    def __init__(self, seed: int, label: str):
        self._state = hashlib.sha256(
            f"{SEED_DOMAIN}:{seed}:{label}".encode()).digest()

    def _next(self) -> int:
        self._state = hashlib.sha256(self._state).digest()
        return int.from_bytes(self._state[:8], "big")

    def sample(self, candidates: list[Any], k: int) -> list[Any]:
        pool = list(candidates)
        if k > len(pool):
            raise SamplingError(
                f"cannot draw {k} items from a pool of {len(pool)}")
        chosen = []
        for _ in range(k):
            chosen.append(pool.pop(self._next() % len(pool)))
        return chosen


# ------------------------------------------------------------ population
def population() -> list[dict[str, Any]]:
    """The 983 dev-half items with every field the sampler and the report
    need, read from registered evidence only."""
    items: list[dict[str, Any]] = []
    for model_key in paths.MODEL_KEYS:
        pool = dsmod.pool_items(model_key)
        rounds = dsmod.round_judgments(model_key)
        for item_id in sorted(rounds["high"]):
            item = pool[item_id]
            text = item["response_text"]
            s0 = item["registered_s0"]
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest != item["response_hash"]:
                raise SamplingError(
                    f"{model_key}::{item_id}: response bytes do not match "
                    f"the registered content hash")
            items.append({
                "id": f"{model_key}::{item_id}",
                "model": model_key,
                "item_id": item_id,
                "n": item["n"],
                "s0_count": s0,
                "verifier_class": "pass" if s0 == item["n"] else "fail",
                "source_pool": item["source_pool"],
                "response_sha256": digest,
                "response_words": len(text.split()),
                "finish_reason": item["finish_reason"],
                "judge_round_labels": {
                    e: rounds[e][item_id]["label"] for e in rounds},
                "judge_round_statuses": {
                    e: rounds[e][item_id]["status"] for e in rounds},
                "substring_however": len(_HOWEVER.findall(text)),
            })
    return sorted(items, key=lambda r: r["id"])


# ------------------------------------------------------------ exclusions
def sealed_ids() -> frozenset[str]:
    """The SEALED reserved final-check ids, read ONLY as an exclusion set.

    The file is never written, and its ids are never returned to a caller
    that persists or prints them (the sampler uses this set purely to
    subtract).  ``sealed_digest`` pins the bytes so any modification is
    detectable.
    """
    return frozenset(json.loads(SEALED_PATH.read_text())["ids"])


def sealed_digest() -> str:
    return hashlib.sha256(SEALED_PATH.read_bytes()).hexdigest()


def calibration_ids() -> frozenset[str]:
    return frozenset(s["id"] for s in
                     json.loads(CALIBRATION_SET.read_text())["samples"])


def _record_files(records_dir: Path) -> list[Path]:
    if not records_dir.exists():
        return []
    return sorted(p for p in records_dir.glob("*.jsonl")
                  if not p.name.startswith("reveals_")
                  and p.name != "digests.jsonl")


def labelled_ids(records_dir: Path = RECORDS_DIR) -> frozenset[str]:
    """Every id a human has already committed a judgment on.

    Synthetic (self-test) records are refused outright rather than
    ignored: they must be deleted before real review, and a mixed
    directory is a workflow error, not a sampling input.
    """
    ids: set[str] = set()
    for path in _record_files(records_dir):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("synthetic"):
                raise SamplingError(
                    f"{path.name} contains synthetic self-test records; "
                    f"delete them before extending the human set")
            ids.add(row["id"])
    return frozenset(ids)


def revealed_ids(records_dir: Path = RECORDS_DIR) -> frozenset[str]:
    """Ids whose hidden fields have been shown to a human (no longer
    blind, so never re-presentable)."""
    ids: set[str] = set()
    if not records_dir.exists():
        return frozenset()
    for path in sorted(records_dir.glob("reveals_*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                ids.add(json.loads(line)["id"])
    return frozenset(ids)


def excluded_ids(records_dir: Path = RECORDS_DIR) -> dict[str, frozenset]:
    """The exclusion sets, kept separate so the manifest can record how
    many items each one removed without disclosing sealed identities."""
    return {"sealed": sealed_ids(),
            "calibration": calibration_ids(),
            "already_labelled": labelled_ids(records_dir),
            "revealed": revealed_ids(records_dir)}


def prior_batch_ids(batch: int) -> frozenset[str]:
    """Ids already committed to an earlier extension batch (whether or not
    they have been labelled yet)."""
    ids: set[str] = set()
    for path in sorted(HERE.glob("extension_batch_*.json")):
        index = int(path.stem.rsplit("_", 1)[1])
        if index < batch:
            ids.update(s["id"] for s in
                       json.loads(path.read_text())["samples"])
    return frozenset(ids)


# -------------------------------------------------------------- boundary
def boundary_category(item: dict[str, Any],
                      long_threshold: dict[str, int]) -> str | None:
    """The single boundary category an item belongs to, in the fixed
    priority order, or None when the item is not a boundary case."""
    labels = item["judge_round_labels"]
    statuses = item["judge_round_statuses"]
    valid_labels = {v for v in labels.values() if v is not None}
    if item["substring_however"] != item["s0_count"]:
        return "embedded_or_adjacent_form"
    if len(valid_labels) > 1:
        # the judge itself is unstable across reasoning efforts
        return "judge_effort_disagreement"
    if any(v is not None and v != item["verifier_class"]
           for v in labels.values()):
        # every valid judge label agrees with the others and still
        # contradicts the verifier: the strongest verifier-doubt case
        return "judge_vs_verifier"
    if item["verifier_class"] == "fail" \
            and abs(item["s0_count"] - item["n"]) == 1:
        return "near_miss_count"
    if any(s != "valid" for s in statuses.values()):
        return "judge_non_valid_status"
    if item["finish_reason"] == "length":
        return "generation_truncated"
    if item["n"] >= HIGH_N:
        return "high_n"
    if item["response_words"] >= long_threshold[item["verifier_class"]]:
        return "long_response"
    return None


def long_response_thresholds(items: Iterable[dict[str, Any]]
                             ) -> dict[str, int]:
    """Within-class P90 of response length, computed on the eligible pool
    so the threshold cannot be tuned after the fact."""
    out: dict[str, int] = {}
    for cls in ("pass", "fail"):
        words = sorted(i["response_words"] for i in items
                       if i["verifier_class"] == cls)
        out[cls] = (words[min(int(LONG_RESPONSE_QUANTILE * len(words)),
                              len(words) - 1)] if words else 0)
    return out


# ------------------------------------------------------------ allocation
def allocate(target: int, stratum_sizes: dict[str, int]) -> dict[str, int]:
    """Proportional allocation of ``target`` over strata, with rounding
    drift resolved deterministically on the largest stratum."""
    if target <= 0:
        return {k: 0 for k in stratum_sizes}
    total = sum(stratum_sizes.values())
    alloc = {k: max(1, round(target * size / total))
             for k, size in stratum_sizes.items()}
    keys = sorted(stratum_sizes)
    while sum(alloc.values()) != target:
        delta = 1 if sum(alloc.values()) < target else -1
        key = max(keys, key=lambda k: (stratum_sizes[k], k))
        if delta < 0 and alloc[key] <= 1:
            key = max((k for k in keys if alloc[k] > 1),
                      key=lambda k: (stratum_sizes[k], k))
        alloc[key] += delta
    return alloc


def deficits(cumulative_target: int, stratum_sizes: dict[str, int],
             existing: dict[str, int]) -> dict[str, int]:
    """Per-stratum shortfall against the cumulative per-class target.

    Allocation is computed on the CUMULATIVE target and the already
    labelled items are subtracted, so the combined (initial + extension)
    class sample stays proportionally allocated over source models.
    """
    alloc = allocate(cumulative_target, stratum_sizes)
    return {k: max(0, alloc[k] - existing.get(k, 0)) for k in alloc}


# ---------------------------------------------------------------- build
def build_extension(batch: int, *, class_targets: dict[str, int],
                    boundary_per_class: int = 8,
                    records_dir: Path = RECORDS_DIR
                    ) -> dict[str, Any]:
    """Build one extension batch.  Pure: reads evidence and records, and
    returns the manifest without writing anything."""
    if batch < 1:
        raise SamplingError("batch index starts at 1")
    pop = population()
    excl = excluded_ids(records_dir)
    prior = prior_batch_ids(batch)
    blocked = set().union(*excl.values()) | prior
    eligible = [i for i in pop if i["id"] not in blocked]
    if not eligible:
        raise SamplingError("no eligible items remain")

    seed = batch_seed(batch)
    long_threshold = long_response_thresholds(eligible)
    by_class_existing = _existing_class_strata(pop, excl["already_labelled"])

    samples: list[dict[str, Any]] = []
    chosen: set[str] = set()
    boundary_pools: dict[str, int] = {}
    realised_boundary: dict[str, int] = defaultdict(int)
    allocation: dict[str, dict[str, int]] = {}

    # (1) boundary component first, so the purposive picks cannot be
    #     silently displaced by the random draw; representative strata
    #     are then drawn from what remains.
    for cls in ("pass", "fail"):
        cands = [i for i in eligible if i["verifier_class"] == cls]
        cats: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in cands:
            cat = boundary_category(item, long_threshold)
            if cat is not None:
                cats[cat].append(item)
        for cat, pool in cats.items():
            boundary_pools[f"{cls}|{cat}"] = len(pool)
        picked = _fill_boundary(cats, boundary_per_class, chosen)
        for item, cat in picked:
            chosen.add(item["id"])
            realised_boundary[f"{cls}|{cat}"] += 1
            samples.append(_row(item, component="boundary",
                                boundary_category=cat,
                                inclusion_probability=None))

    # (2) representative component: SRS within (model x class), topping
    #     each class up to its cumulative target.
    for cls in ("pass", "fail"):
        cands = [i for i in eligible
                 if i["verifier_class"] == cls and i["id"] not in chosen]
        sizes = {m: sum(1 for i in cands if i["model"] == m)
                 for m in paths.MODEL_KEYS}
        want = deficits(class_targets[cls], sizes, by_class_existing[cls])
        allocation[cls] = want
        for model in paths.MODEL_KEYS:
            k = want[model]
            if not k:
                continue
            stratum = sorted((i for i in cands if i["model"] == model),
                             key=lambda r: r["id"])
            rng = _Rng(seed, f"{cls}|{model}")
            for item in sorted(rng.sample(stratum, k),
                               key=lambda r: r["id"]):
                chosen.add(item["id"])
                samples.append(_row(
                    item, component="representative",
                    boundary_category=None,
                    inclusion_probability=round(k / len(stratum), 6)))

    samples.sort(key=lambda r: (r["component"], r["id"]))
    sealed = excl["sealed"]
    if any(s["id"] in sealed for s in samples):        # belt and braces
        raise SamplingError("a sealed reserved id entered the sample")
    return {
        "batch": batch,
        "seed_domain": SEED_DOMAIN,
        "base_seed": BASE_SEED,
        "seed": seed,
        "design": (
            "extension of the E5 calibration set; class-balanced "
            "(disproportionate across verifier classes, proportional "
            "across source models within a class), SRS within stratum "
            "for the representative component; deterministic purposive "
            "selection for the boundary component"),
        "population_size": len(pop),
        "eligible_size": len(eligible),
        "excluded": {k: len(v) for k, v in excl.items()},
        "excluded_prior_batches": len(prior),
        "class_targets_cumulative": dict(class_targets),
        "existing_by_class_stratum": by_class_existing,
        "representative_allocation": allocation,
        "boundary_per_class": boundary_per_class,
        "boundary_pool_sizes": dict(sorted(boundary_pools.items())),
        "boundary_realised": dict(sorted(realised_boundary.items())),
        "long_response_threshold_words": long_threshold,
        "sealed_set_sha256": sealed_digest(),
        "verifier_note": (
            "verifier_class / s0_count are recorded for analysis only; "
            "the reviewer interface never loads them"),
        "samples": samples,
    }


def _row(item: dict[str, Any], *, component: str,
         boundary_category: str | None,
         inclusion_probability: float | None) -> dict[str, Any]:
    return {
        "id": item["id"],
        "model": item["model"],
        "item_id": item["item_id"],
        "n": item["n"],
        "source_pool": item["source_pool"],
        "response_sha256": item["response_sha256"],
        "response_words": item["response_words"],
        "finish_reason": item["finish_reason"],
        "verifier_class": item["verifier_class"],
        "s0_count": item["s0_count"],
        "component": component,
        "boundary_category": boundary_category,
        "stratum": [item["model"], item["verifier_class"]],
        "inclusion_probability": inclusion_probability,
    }


def _fill_boundary(cats: dict[str, list[dict[str, Any]]], target: int,
                   taken: set[str]) -> list[tuple[dict[str, Any], str]]:
    """Deterministic purposive fill: quotas in the registered priority
    order, model round-robin by sorted id within a category, shortfalls
    rolled forward to the next category."""
    picked: list[tuple[dict[str, Any], str]] = []
    used = set(taken)
    order = [c for c, _ in BOUNDARY_QUOTAS]
    quotas = dict(BOUNDARY_QUOTAS)
    for pas in (1, 2):          # pass 1 honours quotas; pass 2 tops up
        for cat in order:
            if len(picked) >= target:
                return picked
            limit = quotas[cat] if pas == 1 else target
            room = min(limit, target - len(picked))
            for item in _round_robin(cats.get(cat, []), used):
                if room <= 0:
                    break
                picked.append((item, cat))
                used.add(item["id"])
                room -= 1
    return picked


def _round_robin(items: list[dict[str, Any]],
                 used: set[str]) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in sorted(items, key=lambda r: r["id"]):
        if item["id"] not in used:
            by_model[item["model"]].append(item)
    out: list[dict[str, Any]] = []
    while any(by_model.values()):
        for model in sorted(by_model):
            if by_model[model]:
                out.append(by_model[model].pop(0))
    return out


def _existing_class_strata(pop: list[dict[str, Any]],
                           labelled: Iterable[str]
                           ) -> dict[str, dict[str, int]]:
    """Counts of already-labelled items per (class, model)."""
    index = {i["id"]: i for i in pop}
    out = {cls: {m: 0 for m in paths.MODEL_KEYS}
           for cls in ("pass", "fail")}
    for item_id in labelled:
        item = index.get(item_id)
        if item is not None:
            out[item["verifier_class"]][item["model"]] += 1
    return out
