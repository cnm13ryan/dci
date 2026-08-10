#!/usr/bin/env python3
"""How much does the a.m./p.m. segmentation bug change the headline numbers?

The blinded three-way audit found 9 disagreements in 43 cases, ALL with one
cause: both segmenters treat the full stop in "a.m." / "p.m." (and similar
lower-case abbreviations) as a sentence end, so "Sales spike at 6 a.m. when
others sleep." is counted as two sentences.

The production verifier and the "independent" checker share the bug — the
checker's abbreviation list omitted `m`, so on this specific point it was not
independent. That is a real limitation of the Step-1 agreement result and is
reported as such.

This script recounts every contrast row with the abbreviation handled, and
reports every headline both ways. It changes no stored artifact.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"

# Lower-case dotted abbreviations the segmenters mis-split on. Deliberately
# narrow: only forms actually observed in these generations plus the obvious
# time/measure companions.
_DOTTED = r"(?:a\.m|p\.m|e\.g|i\.e|etc|vs|approx|no|fig|cf|al)"


def protect(text: str) -> str:
    """Neutralise full stops that are not sentence ends, then hand back text."""
    work = text
    work = re.sub(r"(\d)\.(\d)", r"\1․\2", work)                  # decimals
    work = re.sub(rf"\b{_DOTTED}\.", lambda m: m.group(0).replace(".", "․"),
                  work, flags=re.IGNORECASE)
    # single-letter initials: "J. R. Tolkien"
    work = re.sub(r"\b([A-Z])\.(?=\s*[A-Z][.\s])", r"\1․", work)
    return work


def count_corrected(text: str | None) -> int:
    """Production segmentation semantics, with abbreviations protected."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from dci.verifiers.rules import split_sentences
    if not text:
        return 0
    return len(split_sentences(protect(text)))


def main() -> int:
    runs = {
        "stageB": "stageB_20260810T183206Z",
        "D2": "stageD2_anticollapse_20260810T192423Z",
        "D3": "stageD3_semicolon_20260810T192430Z",
    }
    n_target = 4
    print("Recounting every contrast row with a.m./p.m. protected.\n")

    for tag, run in runs.items():
        rows = [json.loads(l) for l in
                (RUNS / run / "generations.jsonl").read_text(encoding="utf-8").splitlines()
                if l.strip()]
        contrast = [r for r in rows
                    if r["condition"] in ("focal", "reference") and r["scorable"]]

        changed = 0
        cells: dict[tuple, dict] = defaultdict(
            lambda: {"n": 0, "fail_old": 0, "fail_new": 0,
                     "collapse_old": 0, "collapse_new": 0})
        transitions: Counter = Counter()
        for row in contrast:
            old = row["verifier_detail"]["observed"]
            new = count_corrected(row["response"])
            if old != new:
                changed += 1
                transitions[(old, new)] += 1
            key = (row.get("scaffold", "") or "none", row["order"], row["arm"])
            cell = cells[key]
            cell["n"] += 1
            cell["fail_old"] += int(old != n_target)
            cell["fail_new"] += int(new != n_target)
            cell["collapse_old"] += int(old <= 2)
            cell["collapse_new"] += int(new <= 2)

        print("=" * 92)
        print(f"{tag} — {run}")
        print(f"  rows whose sentence count CHANGES when abbreviations are protected: "
              f"{changed}/{len(contrast)} ({changed / len(contrast):.2%})")
        print(f"  transitions (old -> new): {dict(sorted(transitions.items()))}")
        print(f"  {'cell':44s} {'n':>4s} {'fail_old':>9s} {'fail_new':>9s} "
              f"{'delta':>7s} {'coll_old':>9s} {'coll_new':>9s}")
        for key in sorted(cells):
            c = cells[key]
            fo, fn = c["fail_old"] / c["n"], c["fail_new"] / c["n"]
            co, cn = c["collapse_old"] / c["n"], c["collapse_new"] / c["n"]
            label = "/".join(key)
            print(f"  {label:44s} {c['n']:4d} {fo:9.3f} {fn:9.3f} {fn - fo:+7.3f} "
                  f"{co:9.3f} {cn:9.3f}")
        print()

    # ---- the headline contrasts, both ways --------------------------------
    print("=" * 92)
    print("HEADLINE CONTRASTS, old segmentation vs abbreviation-protected")
    rows = [json.loads(l) for l in
            (RUNS / runs["stageB"] / "generations.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    contrast = [r for r in rows
                if r["condition"] in ("focal", "reference") and r["scorable"]]
    outcome_old, outcome_new = {}, {}
    for row in contrast:
        key = (row["pair_key"], row["arm"])
        outcome_old[key] = int(row["verifier_detail"]["observed"] != n_target)
        outcome_new[key] = int(count_corrected(row["response"]) != n_target)
    keys = {k for k, _ in outcome_old}
    print(f"  {'tau (B - reference), pooled':44s} {'old':>8s} {'corrected':>10s}")
    for reference in ("C_L3", "C_O2", "C_W3", "S_SEMICOLON"):
        pairs = [k for k in keys if (k, "B") in outcome_old and (k, reference) in outcome_old]
        old = sum(outcome_old[(k, "B")] - outcome_old[(k, reference)] for k in pairs) / len(pairs)
        new = sum(outcome_new[(k, "B")] - outcome_new[(k, reference)] for k in pairs) / len(pairs)
        print(f"  {'B - ' + reference:44s} {old:8.4f} {new:10.4f}")

    print("\n  order effect on the focal arm (B):")
    for order in ("o_A", "o_Q"):
        sel = [r for r in contrast if r["arm"] == "B" and r["order"] == order]
        old = sum(int(r["verifier_detail"]["observed"] != n_target) for r in sel) / len(sel)
        new = sum(int(count_corrected(r["response"]) != n_target) for r in sel) / len(sel)
        print(f"    {order}: old={old:.4f} corrected={new:.4f}")

    # ---- D2 excess, both ways ---------------------------------------------
    print("\n  D2 paired excess over C_L3:")
    d2 = [json.loads(l) for l in
          (RUNS / runs["D2"] / "generations.jsonl").read_text(encoding="utf-8").splitlines()
          if l.strip()]
    d2 = [r for r in d2 if r["condition"] in ("focal", "reference") and r["scorable"]]
    for scaffold in ("", "one_sentence_per_line"):
        for order in ("o_A", "o_Q"):
            ctrl = {r["pair_key"]: r for r in d2 if r.get("scaffold", "") == scaffold
                    and r["order"] == order and r["arm"] == "C_L3"}
            for arm in ("B", "S_SEMICOLON"):
                sel = {r["pair_key"]: r for r in d2 if r.get("scaffold", "") == scaffold
                       and r["order"] == order and r["arm"] == arm}
                shared = sorted(set(ctrl) & set(sel))
                old = sum(int(sel[k]["verifier_detail"]["observed"] != n_target)
                          - int(ctrl[k]["verifier_detail"]["observed"] != n_target)
                          for k in shared) / len(shared)
                new = sum(int(count_corrected(sel[k]["response"]) != n_target)
                          - int(count_corrected(ctrl[k]["response"]) != n_target)
                          for k in shared) / len(shared)
                print(f"    {(scaffold or 'none'):22s} {order} {arm:12s} "
                      f"old={old:+.4f} corrected={new:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
