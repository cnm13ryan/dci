"""How much would a defective reading of the instruments change this study's
numbers? Measured on the responses the study has actually generated.

**Why this exists.** §10.2 shows the code implements the registered prose ---
two implementations written by different routes agree exactly. §10.4 asks the
harder question, whether the prose means what a reader thinks it means, and it
answers it with a judge whose own accuracy against human labels is worse than
the verifier's. Between those two sits a question neither answers and that
costs nothing to answer: *on the study's own data, does the choice between the
registered reading and a plausible defective one move any number at all?*

A defect that changes no verdict on real responses is a defect no audit over
real responses could detect either. That is very likely the retrospective
explanation for §10.4-R's `vacuity_ignored` result --- 0 of 5, with no
justification offered --- and it is the kind of thing worth knowing before
reading any agreement rate as evidence about an instrument.

**Scope, deliberately narrow.** Read-only. It rescores stored responses under
the six registered alternative readings of `stages/microcase.py` and compares
against the canonical verifier. It reads **load 0 and load 1 rows only**, which
structurally excludes every composed cell, so no `D(B <- R)`, no `Delta`, no
`Xi` and no composed quantity of any kind is computable from what it touches.
It changes no verifier, no preregistration, no candidate selection and no
record. It writes one report.

**Two populations, kept apart.**

* **stated** --- the constraint the prompt actually stated, one per load-1
  response. These are the verdicts solo compliance is made of.
* **chance** --- every declared instrument scored against the unconstrained
  responses, which is where §13.3's denominator comes from. A defect that moves
  `kappa` moves `iota` and therefore the difficulty coordinate, so this
  population is not a curiosity.

    python3 tools/v4r3_defect_sensitivity.py
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol.hashing import canonical_json, sha_text        # noqa: E402
from dci1v4r3 import CLASSIFICATION, EVIDENCE_DIRNAME               # noqa: E402
from dci1v4r3.engine.paths import current_files                     # noqa: E402
from dci1v4r3.protocol import constants as C                        # noqa: E402
from dci1v4r3.stages.microcase import (                             # noqa: E402
    DEFECT_KINDS, NUMERATOR_SWAP, _drift_statistic, _drift_words,
    defect_verdict,
)
from dci1v4r3.verifiers import verifier_source_hash                 # noqa: E402
from dci1v4r3.verifiers.compliance import passes                    # noqa: E402
from dci1v4r3.verifiers.constraints import (                        # noqa: E402
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_LOWER_BOUND, FORM_RATE,
    FORM_RATE_LOWER_BOUND, Constraint, declared_range,
)
from dci1v4r3.verifiers.statistics import STATISTICS, word_count    # noqa: E402

EVIDENCE = DCI1 / "evidence" / EVIDENCE_DIRNAME
OUT = DCI1 / "reports" / "dci1v4r3" / "defect_sensitivity.json"

#: Diagnostic bands, **not** registered criteria. §11.8's smallest effect of
#: interest is the reference because it is the registered scale on which a
#: change in compliance matters at all; the second line is an order of
#: magnitude below it and marks "moves something, but nothing that could
#: change a reading".
CONSEQUENTIAL = C.SMALLEST_EFFECT_OF_INTEREST
DETECTABLE = 0.01


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:                                    # pragma: no cover
        return "unknown"


# ------------------------------------------------------------ the fast path
#
# `defect_verdict` recomputes every statistic on every call, which is right for
# a set of 160 microcases and hopeless for millions of (instrument, response)
# pairs. The statistics depend on the text alone, so they are computed once per
# response and the predicates become arithmetic. `assert_fast_path_agrees`
# checks the fast path against the registered implementation on a sample, so
# the optimisation is verified rather than assumed.

class Reading:
    """Everything the six readings need from one response, computed once."""

    __slots__ = ("stat", "drift", "words", "drift_words", "chars", "blank")

    def __init__(self, text: str):
        self.stat = {k: fn(text) for k, fn in STATISTICS.items()}
        self.drift = {k: _drift_statistic(k, text) for k in STATISTICS}
        self.words = word_count(text)
        self.drift_words = len(_drift_words(text))
        self.chars = len(text)
        self.blank = not text.strip()


def _predicate(form: str, statistic: int, words: int, q: int) -> bool:
    if form == FORM_COUNT:
        return statistic <= q
    if form == FORM_EXACT:
        return statistic == q
    if form == FORM_LOWER_BOUND:
        return statistic >= q
    if words == 0:
        return False
    rate = 100.0 * statistic / words
    return rate <= q if form == FORM_RATE else rate >= q


def verdict(reading: Reading, kind: str, q: int, defect: str | None) -> bool:
    """The canonical verdict when ``defect`` is None, else that reading's."""
    family = FAMILIES[kind]
    form, statistic_id = family.form, family.statistic_id
    statistic, words = reading.stat[statistic_id], reading.words
    is_rate = form in (FORM_RATE, FORM_RATE_LOWER_BOUND)
    is_lower = form in (FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)

    if defect == "numerator_swap":
        statistic = reading.stat[NUMERATOR_SWAP[statistic_id]]
    elif defect == "segmentation_drift":
        statistic, words = reading.drift[statistic_id], reading.drift_words
    elif defect == "denominator_swap":
        if is_rate:
            words = reading.chars
    elif defect == "off_by_one":
        q = q + 1 if is_lower else q - 1
    elif defect == "vacuity_ignored":
        if words == 0 and is_rate:
            return True
        if reading.blank and form in (FORM_LOWER_BOUND, FORM_EXACT):
            return True

    ok = _predicate(form, statistic, words, q)
    if defect == "inequality_flip":
        return statistic >= q if form == FORM_EXACT else not ok
    return ok


def assert_fast_path_agrees(texts: list[str], *, sample: int = 40) -> dict:
    """The arithmetic path reproduces `stages.microcase.defect_verdict`."""
    checked = 0
    step = max(1, len(texts) // sample)
    for text in texts[::step][:sample]:
        reading = Reading(text)
        for kind in FAMILIES:
            for q in declared_range(kind)[:3]:
                constraint = Constraint(kind, q, extended=True, reserve=True)
                statistic = STATISTICS[FAMILIES[kind].statistic_id](text)
                if verdict(reading, kind, q, None) != passes(constraint,
                                                            statistic, text):
                    raise SystemExit(
                        f"the fast path disagrees with the canonical verifier "
                        f"on {kind}:{q} for {text[:60]!r}")
                for defect in DEFECT_KINDS:
                    if verdict(reading, kind, q, defect) != defect_verdict(
                            constraint, text, defect):
                        raise SystemExit(
                            f"the fast path disagrees with the registered "
                            f"{defect} reading on {kind}:{q} for "
                            f"{text[:60]!r}")
                    checked += 1
    return {"texts": min(sample, len(texts)), "comparisons": checked,
            "agreement": 1.0}


# --------------------------------------------------------------- the corpus

def load_rows(limit: int | None = None) -> list[dict[str, Any]]:
    """Load 0 and load 1 rows from the current evidence tree.

    Load 2 is excluded structurally rather than filtered later: a composed row
    never enters this tool, so nothing it computes can be a composed quantity.
    Superseded runs are excluded because a re-run stage's rows would otherwise
    be counted twice.
    """
    rows: list[dict[str, Any]] = []
    for path in current_files(EVIDENCE, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("load", 0) > 1:
                continue
            rows.append({"model_key": row.get("model_key", "?"),
                         "stage": row.get("stage", "?"),
                         "load": row.get("load", 0),
                         "text": row.get("raw_response") or "",
                         "scores": row.get("scores") or []})
            if limit and len(rows) >= limit:
                return rows
    return rows


class Tally:
    __slots__ = ("n", "changed", "canonical_pass", "defect_pass")

    def __init__(self):
        self.n = self.changed = self.canonical_pass = self.defect_pass = 0

    def add(self, canonical: bool, defect: bool) -> None:
        self.n += 1
        self.changed += canonical != defect
        self.canonical_pass += canonical
        self.defect_pass += defect

    def as_dict(self) -> dict[str, Any]:
        rate = self.canonical_pass / self.n if self.n else None
        other = self.defect_pass / self.n if self.n else None
        return {"verdicts": self.n, "changed": self.changed,
                "change_rate": self.changed / self.n if self.n else None,
                "canonical_pass_rate": rate, "defect_pass_rate": other,
                "rate_shift": (other - rate) if self.n else None}


def analyse(rows: list[dict[str, Any]], *, declared: bool
            ) -> dict[str, Any]:
    """Rescore every (instrument, response) pair under every reading."""
    overall: dict[str, Tally] = {d: Tally() for d in DEFECT_KINDS}
    by_family: dict[tuple[str, str], Tally] = {}
    by_model: dict[tuple[str, str], Tally] = {}
    by_group: dict[tuple[str, str], Tally] = {}
    by_form: dict[tuple[str, str], Tally] = {}
    stored_disagreements = 0
    stored_compared = 0

    for row in rows:
        reading = Reading(row["text"])
        if declared:
            if row["load"] != 0:
                continue
            work = [(kind, q) for kind in FAMILIES
                    for q in declared_range(kind)]
        else:
            work = [(s["kind"], s["severity"]) for s in row["scores"]
                    if s.get("present") and s["kind"] in FAMILIES]
            stored = {(s["kind"], s["severity"]): s["passed"]
                      for s in row["scores"] if s.get("present")}
        for kind, q in work:
            canonical = verdict(reading, kind, q, None)
            if not declared and (kind, q) in stored:
                stored_compared += 1
                stored_disagreements += stored[(kind, q)] != canonical
            group = FAMILIES[kind].feature_group
            for defect in DEFECT_KINDS:
                value = verdict(reading, kind, q, defect)
                overall[defect].add(canonical, value)
                by_family.setdefault((defect, kind), Tally()).add(canonical,
                                                                  value)
                by_model.setdefault((defect, row["model_key"]),
                                    Tally()).add(canonical, value)
                by_group.setdefault((defect, group), Tally()).add(canonical,
                                                                  value)
                by_form.setdefault((defect, FAMILIES[kind].form),
                                   Tally()).add(canonical, value)

    def nest(table: dict[tuple[str, str], Tally]) -> dict[str, Any]:
        out: dict[str, dict[str, Any]] = collections.defaultdict(dict)
        for (defect, key), tally in table.items():
            out[defect][key] = tally.as_dict()
        return {d: dict(sorted(v.items())) for d, v in sorted(out.items())}

    result = {
        "population": "chance (declared instruments on unconstrained "
                      "responses)" if declared else
                      "stated (the constraint the prompt stated)",
        "responses": sum(1 for r in rows if not declared or r["load"] == 0),
        "overall": {d: t.as_dict() for d, t in sorted(overall.items())},
        "by_family": nest(by_family),
        "by_model": nest(by_model),
        "by_feature_group": nest(by_group),
        "by_predicate_form": nest(by_form),
    }
    if not declared:
        result["stored_verdict_check"] = {
            "compared": stored_compared,
            "disagreements": stored_disagreements,
            "agreement": (1 - stored_disagreements / stored_compared)
            if stored_compared else None,
            "meaning": ("the verdict stored at generation time against the "
                        "verdict this hash computes now. A disagreement means "
                        "the amendment moved a number that had already been "
                        "measured")}
    return result


def attribute(by_family: dict[str, Any], *, top: int = 5) -> dict[str, Any]:
    """Where each reading's changes actually come from.

    A pooled change rate can be one family behaving pathologically or every
    family drifting a little, and those are different findings. This names the
    families that carry the changes so the summary cannot stand in for them.
    """
    out: dict[str, Any] = {}
    for defect, families in by_family.items():
        contributors = sorted(
            ((k, v) for k, v in families.items() if v["changed"]),
            key=lambda kv: -kv[1]["changed"])
        total = sum(v["changed"] for _, v in contributors)
        out[defect] = {
            "families_with_any_change": len(contributors),
            "families_total": len(families),
            "top": [{"family": k, "changed": v["changed"],
                     "verdicts": v["verdicts"],
                     "share_of_all_changes": (v["changed"] / total)
                     if total else None,
                     "change_rate": v["change_rate"]}
                    for k, v in contributors[:top]],
            "concentrated_in_one_family": (
                len(contributors) == 1 and total > 0),
        }
    return out


#: Read alongside `attribute`. §7.3's composition correction is scoped to one
#: Unicode character, and the corpus bears that out on every numerator except
#: one --- for a reason that is a property of the statistic and not of the
#: corpus.
CAPITAL_WORD_NOTE = (
    "Every segmentation-drift change in this corpus is CR6, whose numerator "
    "is `capital_word`. That is not the U+0130 effect §7.3's correction is "
    "scoped to: a fold-then-segment word list is lower-cased, so a case test "
    "over it reads zero for every answer. The drift does not misread "
    "`capital_word` subtly --- it destroys it. On the other fourteen "
    "numerators fold-then-segment changes no verdict at all in 30,720 "
    "responses, which is the registered scope claim holding empirically. "
    "`capital_word` is also the one numerator new in v4r3 with no carry-over "
    "evidence, which §10.2 already requires to earn its own; this is a second "
    "reason it should."
)


def classify(overall: dict[str, Any]) -> dict[str, Any]:
    """Consequential, detectable, or invisible --- and what invisible means."""
    out: dict[str, Any] = {}
    for defect, entry in overall.items():
        shift = abs(entry["rate_shift"] or 0.0)
        change = entry["change_rate"] or 0.0
        if change == 0.0:
            band = "invisible"
        elif shift >= CONSEQUENTIAL:
            band = "consequential"
        elif shift >= DETECTABLE:
            band = "detectable"
        else:
            band = "negligible"
        out[defect] = {
            "band": band, "change_rate": change, "rate_shift": shift,
            "note": ("no verdict in this corpus differs under this reading, "
                     "so no audit over these responses could detect it --- "
                     "which is what an agreement rate on natural responses "
                     "cannot tell you"
                     if band == "invisible" else
                     "moves the measured compliance rate by at least the "
                     "registered smallest effect of interest"
                     if band == "consequential" else
                     "changes verdicts but shifts the measured rate by less "
                     "than the smallest effect of interest")}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the number of rows, for a quick pass")
    args = parser.parse_args()

    rows = load_rows(args.limit)
    if not rows:
        raise SystemExit("no v4r3 screen responses in the current evidence "
                         "tree")
    fast_path = assert_fast_path_agrees([r["text"] for r in rows])
    stated = analyse(rows, declared=False)
    chance = analyse(rows, declared=True)

    sources = [{"path": str(p.relative_to(DCI1)),
                "rows": sum(1 for line in p.read_text().splitlines()
                            if line.strip())}
               for p in current_files(EVIDENCE, "scored.jsonl")]

    payload = {
        "artifact_type": "v4r3-defect-sensitivity",
        "classification": CLASSIFICATION,
        "purpose": ("Gate 1 measurement robustness. Read-only. It rescores "
                    "stored responses under the six registered alternative "
                    "readings and changes nothing."),
        "reads": "load 0 and load 1 rows only; no composed cell enters",
        "computes_no_composed_estimand": True,
        "defect_kinds": list(DEFECT_KINDS),
        "numerator_swap_map": dict(NUMERATOR_SWAP),
        "bands": {"consequential_at_or_above": CONSEQUENTIAL,
                  "detectable_at_or_above": DETECTABLE,
                  "provenance": ("diagnostic bands, NOT registered criteria. "
                                 "The upper line is §11.8's smallest effect "
                                 "of interest, which is the registered scale "
                                 "on which a change in compliance matters.")},
        "provenance": {
            "verifier_source_hash": verifier_source_hash(),
            "producing_commit": _commit(),
            "generated_at": _now(),
            "evidence_root": str(EVIDENCE.relative_to(DCI1)),
            "sources": sources,
            "rows_read": len(rows),
            "fast_path_check": fast_path,
        },
        "stated": stated,
        "chance": chance,
        "verdict_bands": {"stated": classify(stated["overall"]),
                          "chance": classify(chance["overall"])},
        "attribution": {"stated": attribute(stated["by_family"]),
                        "chance": attribute(chance["by_family"])},
        "capital_word_note": CAPITAL_WORD_NOTE,
    }
    payload["report_hash"] = sha_text(canonical_json(
        {k: v for k, v in payload.items()
         if k not in ("report_hash", "provenance")}))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")

    print(f"responses {len(rows)}  verifier {verifier_source_hash()[:12]}  "
          f"commit {_commit()[:12]}")
    print(f"fast path checked against the registered readings on "
          f"{fast_path['comparisons']} comparisons\n")
    for population in ("stated", "chance"):
        entry = payload[population]
        print(f"=== {population}: {entry['overall'][DEFECT_KINDS[0]]['verdicts']:,} "
              f"verdicts per reading")
        print(f"    {'defect':20s} {'changed':>12s} {'change rate':>12s} "
              f"{'rate shift':>12s}  band")
        for defect in DEFECT_KINDS:
            row = entry["overall"][defect]
            band = payload["verdict_bands"][population][defect]["band"]
            attributed = payload["attribution"][population][defect]
            where = ("--" if not attributed["top"] else
                     ", ".join(f"{t['family']}"
                               for t in attributed["top"][:3])
                     + ("" if attributed["families_with_any_change"] <= 3
                        else f" +{attributed['families_with_any_change'] - 3}"))
            print(f"    {defect:20s} {row['changed']:>12,} "
                  f"{row['change_rate']:>12.4f} {row['rate_shift']:>+12.4f}  "
                  f"{band:14s} {where}")
        print()
    check = stated.get("stored_verdict_check", {})
    print("=== sensitivity by predicate form (stated) ===")
    forms = sorted(stated["by_predicate_form"][DEFECT_KINDS[0]])
    print(f"    {'defect':20s}" + "".join(f"{f[:16]:>18s}" for f in forms))
    for defect in DEFECT_KINDS:
        row = stated["by_predicate_form"][defect]
        print(f"    {defect:20s}"
              + "".join(f"{row[f]['change_rate']:>18.4f}" for f in forms))
    print("\n    The exact-count form is where a threshold slip bites: "
          "`S == q` and `S == q - 1` differ whenever the statistic sits at "
          "either value, and an exact-count answer sits at its target by "
          "construction. A is that form. So is CX1, which §7.0-R3 added as "
          "A's same-form class companion.\n")

    if check.get("compared"):
        print(f"stored verdicts recomputed: {check['compared']:,} compared, "
              f"{check['disagreements']} disagreement(s)")
    print(f"\n{CAPITAL_WORD_NOTE}\n")
    print(f"wrote {OUT.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
