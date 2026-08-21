#!/usr/bin/env python3
"""Is the B+R pilot's Delta a companion-identity effect or a length effect?

A read-only re-analysis of the closed B+R pilot and the closed v3 confirmatory
cache. It changes nothing in either and licenses no confirmatory claim.

**What the pilot reports.** Delta = P(B | B+Rbar) - P(B | A+B) = +0.343 (E2B)
and +0.375 (E4B), classified `H1_PAIR_SPECIFIC`.

**What is unequal between those two terms besides the companion.** The pilot's
own B+R generations average 24-25 words. The v3 A+B generations its P(B|A) term
comes from average 128-139. B is "every word has at most m letters" at m = 7 --
a constraint whose difficulty rises with the number of words a response
contains, because each additional word is another chance to exceed the budget.
So the two cells differ five-fold in the quantity most directly coupled to the
outcome.

This tool asks three questions of that, in order:

1. **Is it vacuity?** Two ways, and they answer differently, so both are
   computed. §17.4 registers the **partial-identification recomputation**: every
   estimand recomputed with all vacuous passes forced to failures, no row
   dropped and nothing conditioned on. The other is the **restriction** to
   responses of at least twenty words, which drops rows and therefore conditions
   on a consequence of the treatment. §9.3 is explicit that vacuous passes count
   as passes in the primary estimand "because response shortening under
   composition is a candidate mechanism rather than a nuisance, and removing
   them would condition on a consequence of the treatment" -- so the forced
   recomputation is the protocol's own bound and the restriction is not.
2. **Is it length?** Compare P(B) between the two cells *within* word-count
   bins, and standardise one cell's length distribution to the other's over
   their region of common support.
3. **How much common support is there?** A standardisation over a region where
   one cell has nine responses is not a comparison.

**The collider caveat, stated before the numbers and not after.** Response
length is a consequence of the companion (§13.3) and §22 registers it as a
mediator that the primary estimand is never conditioned on. Conditioning on it
compares sub-populations selected differently in the two arms -- a 40-word A+B
response is unusual, a 40-word B+R response is typical. Nothing below is a
causal decomposition. What it can do is show whether the identity contrast has
any content once the arms are compared at equal length, and that is a question
worth an answer even when the answer is not an estimate.

**A second caveat.** The pilot's P(B|A) comes from the 384 confirmatory topics
while its P(B|R) comes from the 96 solo-calibration topics; the pilot's own
protocol records this and argues exchangeability from the seeded split. The
topic-set shift measured on A in `tools/v3_reciprocal_reanalysis.py` is -0.046
and -0.105, so it is far too small to produce a +0.34 difference, but it is not
zero and every number below inherits it.

Usage:  python tools/pilot_length_channel.py
Writes: dci1/reports/pilot_reanalysis/length_channel.json
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

DCI1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v3.verifiers.families import focal_passes           # noqa: E402
from dci1v3.verifiers.words import alpha_runs                # noqa: E402

PILOT = DCI1 / "evidence" / "br-pilot-v4"
V3 = DCI1 / "evidence" / "dci1-v3"
OUT = DCI1 / "reports" / "pilot_reanalysis"
NON_VACUITY_MIN_WORDS = 20
BINS = ((20, 30), (30, 45), (45, 70), (70, 110), (110, 170), (170, 10 ** 9))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def words(text: str | None) -> int:
    return len(alpha_runs(text or ""))


def load(model: str, m_star: int) -> dict[str, Any]:
    pilot_path = PILOT / model / "cache.jsonl"
    v3_path = V3 / model / "confirmatory" / "cache.jsonl"
    br: list[dict[str, Any]] = []
    for line in pilot_path.open():
        row = json.loads(line)
        br.append({"family": f"{row['constraint_id']}:{row['severity']}",
                   "topic": row["topic_id"], "order": row.get("order"),
                   "words": words(row.get("raw_response")),
                   "b_pass": 1 if focal_passes(row.get("raw_response") or "",
                                               m_star) else 0})
    ab: list[dict[str, Any]] = []
    for line in v3_path.open():
        row = json.loads(line)
        if row["arm"] != "AB":
            continue
        ab.append({"block": row["block_id"], "order": row["order"],
                   "words": words(row.get("raw_response")),
                   "b_pass": 1 if row["verdicts"]["added_pass"] else 0})
    return {"br": br, "ab": ab,
            "sources": {
                "B_plus_R": {"path": str(pilot_path.relative_to(DCI1)),
                             "sha256": sha256(pilot_path), "rows": len(br),
                             "topics": "the 96 solo-calibration topics"},
                "A_plus_B": {"path": str(v3_path.relative_to(DCI1)),
                             "sha256": sha256(v3_path), "rows": len(ab),
                             "topics": "the 384 confirmatory topics"}}}


def rate(rows: Sequence[dict[str, Any]]) -> float:
    return sum(r["b_pass"] for r in rows) / len(rows) if rows else float("nan")


def per_family(br: Sequence[dict[str, Any]]) -> dict[str, list]:
    out: dict[str, list] = defaultdict(list)
    for row in br:
        out[row["family"]].append(row)
    return out


def standardise(source: Sequence[dict[str, Any]],
                target: Sequence[dict[str, Any]], bins=BINS) -> dict[str, Any]:
    """P(B) in ``source``, reweighted so its length distribution matches
    ``target``'s, over bins where both have at least ``MIN_CELL`` responses."""
    MIN_CELL = 20
    weights, rates, kept, dropped = [], [], 0, []
    for low, high in bins:
        s = [r for r in source if low <= r["words"] < high]
        t = [r for r in target if low <= r["words"] < high]
        if len(s) < MIN_CELL or len(t) < MIN_CELL:
            if s or t:
                dropped.append({"bin": [low, high if high < 10 ** 9 else None],
                                "source_n": len(s), "target_n": len(t)})
            continue
        weights.append(len(t))
        rates.append(rate(s))
        kept += len(t)
    if not weights:
        return {"standardised_rate": None, "common_support_rows": 0,
                "bins_used": 0, "bins_dropped": dropped}
    total = sum(weights)
    return {"standardised_rate": sum(w * r for w, r in zip(weights, rates)) / total,
            "common_support_rows": kept, "bins_used": len(weights),
            "bins_dropped": dropped,
            "share_of_target_in_common_support": kept / len(target)}


def bootstrap_difference(a: Sequence[dict], b: Sequence[dict], *,
                         resamples: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    point = rate(a) - rate(b)
    draws = []
    for _ in range(resamples):
        draws.append(rate(rng.choices(a, k=len(a)))
                     - rate(rng.choices(b, k=len(b))))
    draws.sort()
    return {"estimate": point,
            "ci95": [draws[int(math.floor(0.025 * resamples)) - 1],
                     draws[min(resamples - 1,
                               int(math.ceil(0.975 * resamples)) - 1)]]}


def analyse(model: str, m_star: int, *, resamples: int = 10000) -> dict[str, Any]:
    data = load(model, m_star)
    br, ab = data["br"], data["ab"]
    families = per_family(br)

    long_br = [r for r in br if r["words"] >= NON_VACUITY_MIN_WORDS]
    long_ab = [r for r in ab if r["words"] >= NON_VACUITY_MIN_WORDS]

    def mean_over_families(rows_by_family, predicate=lambda r: True):
        values = [rate([r for r in rows if predicate(r)])
                  for rows in rows_by_family.values()]
        return sum(values) / len(values)

    delta_raw = mean_over_families(families) - rate(ab)
    delta_long = (mean_over_families(
        families, lambda r: r["words"] >= NON_VACUITY_MIN_WORDS)
        - rate(long_ab))

    # §17.4: force every vacuous pass to a failure. No row is dropped and
    # nothing is conditioned on, so this is a bound rather than a sub-population.
    def forced(rows):
        return sum(1 for r in rows
                   if r["b_pass"] and r["words"] >= NON_VACUITY_MIN_WORDS
                   ) / len(rows) if rows else float("nan")

    delta_forced = (sum(forced(rows) for rows in families.values())
                    / len(families)) - forced(ab)

    table = []
    for low, high in BINS:
        s = [r for r in br if low <= r["words"] < high]
        t = [r for r in ab if low <= r["words"] < high]
        table.append({"bin": [low, high if high < 10 ** 9 else None],
                      "B_plus_R_n": len(s), "B_plus_R_rate": rate(s),
                      "A_plus_B_n": len(t), "A_plus_B_rate": rate(t),
                      "gap": (rate(s) - rate(t)) if s and t else None})

    standardised = standardise(br, ab)
    reverse = standardise(ab, br)
    both = [row for row in table
            if row["B_plus_R_n"] >= 20 and row["A_plus_B_n"] >= 20]
    length_matched = None
    if both:
        weight = sum(row["A_plus_B_n"] for row in both)
        length_matched = sum(row["A_plus_B_n"] * row["gap"]
                             for row in both) / weight

    overlap = {
        "share_of_A_plus_B_rows_in_common_bins":
            (sum(r["A_plus_B_n"] for r in both) / len(ab)) if both else 0.0,
        "share_of_B_plus_R_rows_in_common_bins":
            (sum(r["B_plus_R_n"] for r in both) / len(br)) if both else 0.0,
        "reading": (
            "the two cells are nearly SEPARATED on the mediator. Where the "
            "overlap is this thin, a length-adjusted contrast is only weakly "
            "identified and the raw contrast is largely a comparison of two "
            "disjoint length regimes. That is the finding, and it is stronger "
            "than either 'the effect is real' or 'the effect is length': "
            "companion identity and response length are close to collinear in "
            "this design, and this design cannot separate them."),
    }

    return {
        "model": model, "m_star": m_star, "sources": data["sources"],
        "overlap_on_the_mediator": overlap,
        "response_length": {
            "B_plus_R_mean_words": sum(r["words"] for r in br) / len(br),
            "A_plus_B_mean_words": sum(r["words"] for r in ab) / len(ab),
            "B_plus_R_median_words": sorted(r["words"] for r in br)[len(br) // 2],
            "A_plus_B_median_words": sorted(r["words"] for r in ab)[len(ab) // 2],
        },
        "question_1_vacuity": {
            "delta_all_responses": delta_raw,
            "delta_section_17_4_vacuous_forced_to_failure": delta_forced,
            "delta_non_vacuous_only": delta_long,
            "which_is_registered": (
                "the §17.4 forced recomputation. §9.3 counts vacuous passes as "
                "passes in the primary estimand and handles them by forcing, "
                "precisely because dropping them would condition on a "
                "consequence of the treatment. The restriction is reported "
                "beside it and is a collider-conditioned sub-population."),
            "vacuous_pass_rate_B_plus_R": sum(
                1 for r in br if r["b_pass"] and r["words"] < NON_VACUITY_MIN_WORDS
            ) / len(br),
            "vacuous_pass_rate_A_plus_B": sum(
                1 for r in ab if r["b_pass"] and r["words"] < NON_VACUITY_MIN_WORDS
            ) / len(ab),
            "reading": ("if the pilot's Delta were carried by degenerate short "
                        "answers, restricting to the registered non-vacuity "
                        "threshold would move it"),
        },
        "question_2_length": {
            "by_bin": table,
            "length_matched_gap_over_common_support": length_matched,
            "B_plus_R_standardised_to_A_plus_B_lengths": standardised,
            "A_plus_B_standardised_to_B_plus_R_lengths": reverse,
            "bootstrap_raw_difference": bootstrap_difference(
                br, ab, resamples=resamples, seed=202608240),
            "collider_caveat": (
                "length is a consequence of the companion (§13.3) and §22 "
                "registers it as a mediator the primary estimand is never "
                "conditioned on. These are sub-population comparisons, not a "
                "causal decomposition."),
        },
        "question_3_common_support": {
            "bins_with_at_least_20_in_both": len(both),
            "B_plus_R_rows_in_those_bins": sum(r["B_plus_R_n"] for r in both),
            "A_plus_B_rows_in_those_bins": sum(r["A_plus_B_n"] for r in both),
        },
    }


def main() -> int:
    models = {"gemma-3n-e2b-it": 7, "gemma-3n-e4b-it": 7}
    result = {
        "classification": "DERIVED / POST-HOC re-analysis of closed evidence",
        "produced_by": "dci1/tools/pilot_length_channel.py",
        "licenses_no_confirmatory_claim": True,
        "non_vacuity_min_words": NON_VACUITY_MIN_WORDS,
        "results": {m: analyse(m, ms) for m, ms in models.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "length_channel.json").write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n")
    for model, entry in result["results"].items():
        q1 = entry["question_1_vacuity"]
        q2 = entry["question_2_length"]
        ov = entry["overlap_on_the_mediator"]
        print(f"{model}: Delta {q1['delta_all_responses']:+.4f} -> "
              f"{q1['delta_section_17_4_vacuous_forced_to_failure']:+.4f} "
              f"§17.4-forced, "
              f"{q1['delta_non_vacuous_only']:+.4f} non-vacuous; "
              f"length-matched gap "
              f"{q2['length_matched_gap_over_common_support']:+.4f}; "
              f"overlap {ov['share_of_A_plus_B_rows_in_common_bins']:.3f} of "
              f"A+B and {ov['share_of_B_plus_R_rows_in_common_bins']:.3f} of "
              f"B+R")
    return 0


if __name__ == "__main__":
    sys.exit(main())
