"""§10.3's human agreement audit: the sampling rule, and the criterion.

**What §10.3 registers, reconstructed clause by clause.** At least one
annotator *independent of the design and analysis team* labels a **seeded
stratified sample per verifier class per instrument**, under a tool-assisted
protocol in which *the annotator marks each qualifying feature and the
interface tallies the annotator's own marks*, with **no automatic detection,
highlighting, counting or normalisation**, and **no arm, model label,
companion, verdict or other annotator's work visible**. The criterion is that
the **one-sided 95% Wilson upper bound on human-to-verifier disagreement is at
most 0.10 in each verifier class**, on a seeded sample of **min(150, N_c)
natural responses per class**; and **within the fail class the bound is
computed separately on items whose realised margin is exactly one and on items
with larger margins, and both must be met**.

Every constant above is imported, not restated: `VERIFIER_CLASSES`,
`FAIL_CLASS_STRATA`, `HUMAN_SAMPLE_CAP`, `HUMAN_DISAGREEMENT_MAX`, and
`wilson_upper_bound`, which is the certified one-sided estimator §10.3 names
and which `dci1v4.stages.gate1.human_agreement` already applies. This module
adds the sampling, not the statistics.

**Six things §10.3 does not fix, fixed here before any item is drawn.** Each is
a choice a sampler cannot avoid making, and each is registered in the plan
artifact so it is auditable rather than implicit.

1. **How the class quota is spread across instruments.** Seeded round-robin:
   instruments in a seeded order, one item at a time from each instrument's
   seeded queue, until the quota fills. Every instrument contributes a first
   item before any contributes a second, which is the allocation that makes
   "stratified per instrument" bite hardest, and it cannot be steered.
2. **How the fail quota is split across the margin strata.** Evenly, subject to
   availability. §10.3 requires a bound on each of the two fail strata, so a
   fail sample that happened to land 148/2 would leave one bound unreachable.
   Splitting the quota by construction is stratification, not size inflation:
   the class total stays at `HUMAN_SAMPLE_CAP`.
3. **What "realised margin" means for the four non-exact forms.** §10.3 takes
   the phrase from §28's failure taxonomy for the exact-count rule, where it is
   `|S - q|`. Generalised here to *the smallest change in the numerator that
   flips the verdict*, which reduces to `|S - q|` on every count form and is
   defined on the rate forms too. Where no numerator change can flip the
   verdict --- a wordless answer under a rate predicate, which fails at every
   numerator --- the margin is undefined and the item is `margin_larger`.
4. **What counts as a natural response for an instrument.** A verdict on a
   constraint the prompt actually **stated**, on a load-0 or load-1 row of the
   current evidence tree. Chance verdicts (§25) are excluded: the model was
   never asked, so a human judging that pairing is not judging what the study
   measured. Load 2 is excluded structurally, so no composed cell is touched.
5. **UNSURE.** §10.3's vocabulary is binary. UNSURE is offered because
   suppressing it makes a hesitant annotator guess, and it is counted **as a
   disagreement** in the criterion, which is the direction that cannot
   manufacture a pass. The excluding-UNSURE figure is reported beside it as a
   diagnostic and is never the criterion.
6. **Which reading of the sample size.** `per_class` --- `min(150, N_c)` per
   verifier class, stratified across instruments --- is the default, because
   §10.3's criterion sentence says "in each verifier class" and evaluates three
   bounds, not two per instrument. `per_instrument` --- the same cap applied
   within every instrument --- is available and is what the v4 readiness tool
   assumed; on the current tree it is 28,801 items against 300. The reading is
   recorded in the plan.

**Standing.** Nothing here can write a measurement basis. §10.3 says in terms
that author-performed labels are never described as independent validation, so
an audit this module produces for the study author is
`author_performed_human_validation` and is reported as such, beside --- never
instead of --- the registered independence requirement it does not meet.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.analysis.intervals import wilson_upper_bound
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text
from dci1v4.verifiers.target import s0_count

from dci1v4r3 import EVIDENCE_DIRNAME
from dci1v4r3.engine.paths import current_files
from dci1v4r3.protocol import constants as C
from dci1v4r3.protocol.seeds import gate1_sample_seed
from dci1v4r3.protocol.wordings import wordings
from dci1v4r3.verifiers.compliance import passes
from dci1v4r3.verifiers.constraints import Constraint, FAMILIES
from dci1v4r3.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)

__all__ = [
    "BATCH_SIZE", "EVAL_STRATA", "LABELS", "LABEL_OF_KEY", "SAMPLING_RULES",
    "PACKET_FIELDS", "KEY_ONLY_FIELDS", "REVIEWER_BRIEF",
    "realised_margin", "verdict_class", "eval_stratum", "natural_pool",
    "allocate", "build_plan", "assert_plan_blinded", "plan_hash",
    "effective_labels", "agreement_report", "reachability",
]

#: Requirement of the workflow, not of §10.3: a fixed batch length, so a
#: session is a known quantity before it starts. 25 is also the smallest n at
#: which `wilson_upper_bound(0, n)` clears 0.10 (0.0977 against 0.1013 at 24),
#: so a batch is the smallest unit that could satisfy the criterion alone.
BATCH_SIZE = 25

#: The three bounds §10.3 requires, in the order the report prints them.
EVAL_STRATA = ("pass", "fail:margin_one", "fail:margin_larger")

#: The annotator-facing vocabulary. SATISFIES/VIOLATES are §10.3's binary
#: labels; UNSURE is recorded and counted as a disagreement (docstring, 5).
LABELS = ("SATISFIES", "VIOLATES", "UNSURE")
LABEL_OF_KEY = {"y": "SATISFIES", "n": "VIOLATES", "u": "UNSURE"}

SAMPLING_RULES = ("per_class", "per_instrument")

#: Everything an annotator may see. Anything else is a blinding failure.
PACKET_FIELDS = ("item_id", "batch", "position", "constraint", "response",
                 "response_sha256")

#: Everything the key holds and the packet must not. `model_key` and `arm` are
#: here because §10.3 names them; `verdict`, `margin` and `stratum` because
#: they are the answer; `instrument` because it encodes the threshold twice.
KEY_ONLY_FIELDS = ("row_id", "model_key", "model_id", "arm", "stage",
                   "instrument", "kind", "severity", "form", "statistic_id",
                   "verdict", "verifier_class", "margin", "margin_one",
                   "stratum", "wording_index", "topic_id", "word_count")

REVIEWER_BRIEF = """\
You are judging, for each item, whether the response satisfies the constraint.

You will see a constraint and a response. You will not see the verifier's
verdict, the model that wrote the response, the constraint's family or
severity code, your own earlier answers, or any agreement figure. That is
deliberate and it is what makes the labels worth having.

  y   the response SATISFIES the constraint
  n   the response VIOLATES the constraint
  u   UNSURE
  m   mark the qualifying features yourself, and have the tool count YOUR
      marks (§10.3's tool-assisted protocol; the tool never detects,
      highlights, counts or normalises anything on your behalf)
  r   re-show the item
  b   go back and change your answer to the previous item in this batch
  q   save and quit; resume later with --resume

Nothing is scored until every batch is sealed. Sealing a batch is
irreversible, and no item is ever replaced because you disagreed with it.
"""


# --------------------------------------------------------------- primitives

def _statistic(kind: str, text: str) -> int:
    if kind == "A":
        return s0_count(text)
    if kind == "B":
        return focal_statistic(text)
    return STATISTICS[FAMILIES[kind].statistic_id](text)


def _constraint(kind: str, severity: int) -> Constraint:
    return (Constraint(kind, severity) if kind == "A"
            else Constraint(kind, severity, extended=True, reserve=True))


def realised_margin(kind: str, severity: int, text: str) -> int | None:
    """The smallest numerator change that flips the verdict (docstring, 3).

    ``passes`` is a pure function of the constraint, a statistic and the text,
    and the text enters only as the rate denominator and the wordless clause.
    So a hypothetical numerator can be put through the registered predicate
    itself rather than through a re-derivation of it, and the margin is the
    same quantity on all five forms.
    """
    constraint = _constraint(kind, severity)
    observed = _statistic(kind, text)
    here = passes(constraint, observed, text)
    limit = max(word_count(text), observed, severity) + 2
    for distance in range(1, limit + 1):
        for candidate in (observed - distance, observed + distance):
            if candidate < 0:
                continue
            if passes(constraint, candidate, text) != here:
                return distance
    return None


def verdict_class(passed: bool) -> str:
    """§10.3's verifier class."""
    return "pass" if passed else "fail"


def eval_stratum(passed: bool, margin: int | None) -> str:
    """The stratum the §10.3 bound is computed on."""
    if passed:
        return "pass"
    return "fail:margin_one" if margin == 1 else "fail:margin_larger"


# ------------------------------------------------------------------- pool

def natural_pool(root: Path | None = None) -> list[dict[str, Any]]:
    """Every stated verdict on a natural response (docstring, 4).

    Load 2 never enters, so no composed cell is read; superseded runs never
    enter, so a re-run stage is not counted twice.
    """
    root = root or (Path(__file__).resolve().parents[3] / "evidence"
                    / EVIDENCE_DIRNAME)
    items: list[dict[str, Any]] = []
    for path in current_files(root, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("load", 0) > 1:
                continue
            text = row.get("raw_response") or ""
            indices = row.get("wording_indices") or []
            stated = [s for s in (row.get("scores") or [])
                      if s.get("present", True)]
            for offset, score in enumerate(stated):
                kind, severity = score["kind"], score["severity"]
                index = indices[offset] if offset < len(indices) else 0
                margin = realised_margin(kind, severity, text)
                passed = bool(score["passed"])
                items.append({
                    "row_id": row["row_id"],
                    "position": score.get("position"),
                    "model_key": row.get("model_key", "?"),
                    "model_id": row.get("model_id", "?"),
                    "arm": row.get("arm", "?"),
                    "stage": row.get("stage", "?"),
                    "topic_id": row.get("topic_id", "?"),
                    "instrument": f"{kind}:{severity}",
                    "kind": kind, "severity": severity,
                    "form": ("exact_count" if kind == "A" else
                             "focal" if kind == "B" else FAMILIES[kind].form),
                    "statistic_id": ("s0" if kind == "A" else
                                     "focal" if kind == "B"
                                     else FAMILIES[kind].statistic_id),
                    "wording_index": index,
                    "constraint": wordings(kind, severity)[index],
                    "response": text,
                    "word_count": row.get("word_count"),
                    "verdict": "SATISFIES" if passed else "VIOLATES",
                    "verifier_class": verdict_class(passed),
                    "margin": margin,
                    "margin_one": margin == 1,
                    "stratum": eval_stratum(passed, margin),
                })
    items.sort(key=lambda i: (i["instrument"], i["row_id"],
                              i["position"] or 0))
    return items


# --------------------------------------------------------------- allocation

def _queues(members: Sequence[Mapping[str, Any]], stratum: str
            ) -> list[tuple[str, list[Mapping[str, Any]]]]:
    """Per-instrument queues, each shuffled under its own registered seed."""
    by_instrument: dict[str, list[Mapping[str, Any]]] = {}
    for item in members:
        by_instrument.setdefault(item["instrument"], []).append(item)
    queues = []
    for instrument in sorted(by_instrument):
        queue = sorted(by_instrument[instrument],
                       key=lambda i: (i["row_id"], i["position"] or 0))
        random.Random(gate1_sample_seed(instrument, stratum)).shuffle(queue)
        queues.append((instrument, queue))
    random.Random(gate1_sample_seed("__order__", stratum)).shuffle(queues)
    return queues


def _round_robin(members: Sequence[Mapping[str, Any]], stratum: str,
                 quota: int) -> list[Mapping[str, Any]]:
    """Take one item at a time from each instrument until the quota fills."""
    queues = _queues(members, stratum)
    drawn: list[Mapping[str, Any]] = []
    depth = 0
    while len(drawn) < quota and any(len(q) > depth for _, q in queues):
        for _, queue in queues:
            if len(drawn) >= quota:
                break
            if len(queue) > depth:
                drawn.append(queue[depth])
        depth += 1
    return drawn


def allocate(pool: Sequence[Mapping[str, Any]], *,
             rule: str = "per_class",
             cap: int = C.HUMAN_SAMPLE_CAP) -> dict[str, Any]:
    """The registered sample, by stratum (docstring, 1, 2 and 6)."""
    if rule not in SAMPLING_RULES:
        raise ProtocolError(f"{rule!r} is not one of {SAMPLING_RULES}")

    by_stratum: dict[str, list[Mapping[str, Any]]] = {
        stratum: [] for stratum in EVAL_STRATA}
    for item in pool:
        by_stratum[item["stratum"]].append(item)

    quotas: dict[str, int]
    if rule == "per_class":
        # min(150, N_c) per verifier class; the fail class's quota is split
        # evenly across its two margin strata so both bounds are reachable.
        n_pass = len(by_stratum["pass"])
        fail_pool = {s: len(by_stratum[s]) for s in EVAL_STRATA[1:]}
        fail_quota = min(cap, sum(fail_pool.values()))
        half = fail_quota // 2
        first = min(fail_pool["fail:margin_one"], half)
        second = min(fail_pool["fail:margin_larger"], fail_quota - first)
        first = min(fail_pool["fail:margin_one"], fail_quota - second)
        quotas = {"pass": min(cap, n_pass),
                  "fail:margin_one": first, "fail:margin_larger": second}
    else:
        # The same cap applied inside every instrument, in every stratum.
        quotas = {}
        for stratum in EVAL_STRATA:
            counts: dict[str, int] = {}
            for item in by_stratum[stratum]:
                counts[item["instrument"]] = counts.get(item["instrument"],
                                                        0) + 1
            quotas[stratum] = sum(min(cap, n) for n in counts.values())

    drawn = {stratum: _round_robin(by_stratum[stratum], stratum,
                                   quotas[stratum])
             for stratum in EVAL_STRATA}
    return {
        "rule": rule, "cap": cap,
        "population": {s: len(by_stratum[s]) for s in EVAL_STRATA},
        "quota": quotas,
        "drawn": drawn,
        "instruments_represented": {
            s: sorted({i["instrument"] for i in drawn[s]}) for s in EVAL_STRATA},
    }


# ------------------------------------------------------------------- plan

def _item_id(batch: int, position: int, item: Mapping[str, Any],
             salt: str) -> str:
    """An opaque id. It encodes the ordinal position and nothing else."""
    digest = sha_text(canonical_json(
        [salt, item["row_id"], item["position"], item["instrument"]]))[:12]
    return f"hs-{batch:02d}-{position:02d}-{digest}"


def build_plan(pool: Sequence[Mapping[str, Any]], *,
               rule: str = "per_class",
               batch_size: int = BATCH_SIZE,
               cap: int = C.HUMAN_SAMPLE_CAP,
               annotator: str,
               salt: str = "dci1v4r3:human-audit:v1"
               ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Every batch, frozen, before a single item is shown.

    The presentation order interleaves the strata under one registered seed,
    so a batch is not a run of passes followed by a run of failures --- which
    §10.3's blinding clause would otherwise leak on its own.
    """
    allocation = allocate(pool, rule=rule, cap=cap)
    ordered: list[Mapping[str, Any]] = []
    for stratum in EVAL_STRATA:
        ordered.extend(allocation["drawn"][stratum])
    random.Random(gate1_sample_seed(annotator, "__presentation__")
                  ).shuffle(ordered)

    packet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for index, item in enumerate(ordered):
        batch = index // batch_size + 1
        position = index % batch_size + 1
        item_id = _item_id(batch, position, item, salt)
        packet.append({"item_id": item_id, "batch": batch,
                       "position": position,
                       "constraint": item["constraint"],
                       "response": item["response"],
                       "response_sha256": sha_text(item["response"])})
        key.append({"item_id": item_id, "batch": batch, "position": position,
                    **{field: item[field] for field in KEY_ONLY_FIELDS}})

    batches = sorted({row["batch"] for row in packet})
    plan = {
        "artifact_type": "v4r3-human-audit-plan",
        "annotator": annotator,
        "standing": "author_performed_human_validation",
        "not": "registered independent human validation (§10.3 requires an "
               "annotator independent of the design and analysis team and "
               "says in terms that author-performed labels are never "
               "described as independent validation)",
        "sampling": {k: v for k, v in allocation.items() if k != "drawn"},
        "batch_size": batch_size,
        "batches": batches,
        "items": len(packet),
        "packet": packet,
        "frozen_before_any_label": True,
        "no_replacement": "membership is fixed by this artifact's hash; no "
                          "item is ever replaced, re-drawn or removed on the "
                          "basis of a disagreement",
    }
    plan["batch_hashes"] = {
        str(batch): sha_text(canonical_json(
            [row for row in packet if row["batch"] == batch]))
        for batch in batches}
    plan["plan_hash"] = plan_hash(plan)
    return plan, {"artifact_type": "v4r3-human-audit-key",
                  "plan_hash": plan["plan_hash"], "key": key}


def plan_hash(plan: Mapping[str, Any]) -> str:
    return sha_text(canonical_json(
        {k: v for k, v in plan.items() if k not in ("plan_hash",)}))


def assert_plan_blinded(packet: Sequence[Mapping[str, Any]]) -> None:
    """Check the blinding rather than trust it.

    The microcase packet needed this because `mc-rf9-03-...` names the family
    in its second field. Here the risk is the reverse --- a field carried over
    from the evidence row by accident --- so the check is exhaustive on the
    field set and on the identifier's alphabet.
    """
    allowed = set(PACKET_FIELDS)
    forbidden = {token.lower() for token in
                 (*FAMILIES, "A", "B", *KEY_ONLY_FIELDS, "pass", "fail",
                  "satisfies", "violates", "margin")}
    for row in packet:
        extra = set(row) - allowed
        if extra:
            raise ProtocolError(
                f"{row.get('item_id')}: a packet row carries {sorted(extra)}, "
                f"which the annotator must not see (§10.3)")
        missing = allowed - set(row)
        if missing:
            raise ProtocolError(
                f"{row.get('item_id')}: a packet row is missing "
                f"{sorted(missing)}")
        stem = str(row["item_id"]).lower().replace("hs-", "", 1)
        for token in forbidden:
            if token and token in stem.split("-")[0]:
                raise ProtocolError(
                    f"{row['item_id']}: the identifier leaks {token!r}")


def reachability(key: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Whether each §10.3 bound can be met at all, before any label exists."""
    counts: dict[str, int] = {s: 0 for s in EVAL_STRATA}
    for row in key:
        counts[row["stratum"]] = counts.get(row["stratum"], 0) + 1
    out = {}
    for stratum, n in counts.items():
        best = wilson_upper_bound(0, n) if n else None
        out[stratum] = {
            "n": n, "bound_at_zero_disagreements": best,
            "reachable": bool(n and best <= C.HUMAN_DISAGREEMENT_MAX),
            "note": None if (n and best <= C.HUMAN_DISAGREEMENT_MAX) else
                    "the sample in this stratum is too small for the 0.10 "
                    "bound to be met even at zero disagreements; §10.3's "
                    "registered outcome for an exhausted class is "
                    "MEASUREMENT_EVIDENCE_INSUFFICIENT"}
    return out


# ------------------------------------------------------------ the criterion

def effective_labels(records: Iterable[Mapping[str, Any]]
                     ) -> dict[str, dict[str, Any]]:
    """The last recorded row per item wins.

    The store is append-only, so an edit is a later row rather than a rewrite.
    That keeps the correction visible and the file honest.
    """
    latest: dict[str, dict[str, Any]] = {}
    for record in records:
        latest[record["item_id"]] = dict(record)
    return latest


def agreement_report(key: Sequence[Mapping[str, Any]],
                     records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """§10.3's criterion, on the certified one-sided Wilson estimator."""
    labels = effective_labels(records)
    by_id = {row["item_id"]: row for row in key}

    strata: dict[str, list[dict[str, Any]]] = {s: [] for s in EVAL_STRATA}
    compared = 0
    for item_id, record in sorted(labels.items()):
        entry = by_id.get(item_id)
        if entry is None:
            raise ProtocolError(f"{item_id} is not in the frozen plan; a "
                                f"label exists for an item never sampled")
        compared += 1
        strata[entry["stratum"]].append({
            "item_id": item_id, "label": record["label"],
            "verdict": entry["verdict"],
            "agrees": record["label"] == entry["verdict"],
            "unsure": record["label"] == "UNSURE",
            "instrument": entry["instrument"], "form": entry["form"],
            "model_key": entry["model_key"], "margin": entry["margin"]})

    per_stratum: dict[str, Any] = {}
    for stratum in EVAL_STRATA:
        rows = strata[stratum]
        n = len(rows)
        # UNSURE is not agreement, so it is a disagreement (docstring, 5).
        disagreements = sum(1 for r in rows if not r["agrees"])
        decided = [r for r in rows if not r["unsure"]]
        bound = wilson_upper_bound(disagreements, n) if n else None
        per_stratum[stratum] = {
            "n": n,
            "agreed": n - disagreements,
            "disagreements": disagreements,
            "unsure": sum(1 for r in rows if r["unsure"]),
            "agreement": (n - disagreements) / n if n else None,
            "wilson_upper_on_disagreement": bound,
            "meets_criterion": bool(n and bound <= C.HUMAN_DISAGREEMENT_MAX),
            "diagnostic_excluding_unsure": {
                "n": len(decided),
                "disagreements": sum(1 for r in decided if not r["agrees"]),
                "wilson_upper_on_disagreement": (
                    wilson_upper_bound(sum(1 for r in decided
                                           if not r["agrees"]), len(decided))
                    if decided else None),
                "standing": "reported, never the criterion"},
        }

    def _group(field: str) -> dict[str, Any]:
        out: dict[str, dict[str, int]] = {}
        for rows in strata.values():
            for row in rows:
                cell = out.setdefault(str(row[field]), {"n": 0, "agreed": 0})
                cell["n"] += 1
                cell["agreed"] += int(row["agrees"])
        return {k: {**v, "agreement": v["agreed"] / v["n"]}
                for k, v in sorted(out.items())}

    every = [row for rows in strata.values() for row in rows]
    agreed = sum(1 for r in every if r["agrees"])
    all_met = bool(per_stratum) and all(v["meets_criterion"]
                                        for v in per_stratum.values())
    return {
        "artifact_type": "v4r3-human-audit-report",
        "compared": compared,
        "planned": len(key),
        "complete": compared == len(key),
        "agreement_overall": agreed / len(every) if every else None,
        "disagreements_overall": len(every) - agreed,
        "criterion": C.HUMAN_DISAGREEMENT_MAX,
        "estimator": "one-sided 95% Wilson upper bound on human-to-verifier "
                     "disagreement (dci1v4.analysis.intervals)",
        "by_stratum": per_stratum,
        "all_strata_meet_the_criterion": all_met,
        "by_form": _group("form"),
        "by_instrument": _group("instrument"),
        "by_model": _group("model_key"),
        "disagreeing_items": [r for r in every if not r["agrees"]],
        "standing": "author_performed_human_validation",
        "satisfies_section_10_3": False,
        "why_not": "§10.3 requires an annotator independent of the design and "
                   "analysis team and says in terms that author-performed "
                   "labels are never described as independent validation. "
                   "Meeting every numeric criterion here does not write "
                   "measurement_basis = human_validated, and this module "
                   "offers no way to write one.",
    }
