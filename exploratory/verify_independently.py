#!/usr/bin/env python3
"""Independent recomputation of the headline numbers from the raw artifact.

Deliberately imports NOTHING from `dci_exploratory.analysis` — not the pairing
helper, not the tables, not the bootstrap. It reads `generations.jsonl` with the
standard library alone and rebuilds the contrast from scratch, so a bug in the
analysis module cannot hide inside its own verification.

It also re-derives the verifier verdict for the target from the response text
using `dci.verifiers.rules` directly, which checks that the stored `a_failure`
column really is "did this answer contain exactly N sentences" and not something
that drifted.

    uv run --project exploratory python exploratory/verify_independently.py RUN_DIR

Exit code is non-zero if any check fails.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    run_dir = Path(argv[0])
    rows = load_jsonl(run_dir / "generations.jsonl")
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    target = config["selection"]["target"]
    focal = config["selection"]["focal"]
    references = config["selection"]["references"]

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not ok:
            failures.append(name)

    print(f"\n=== independent verification of {run_dir} ===")
    print(f"rows={len(rows)} target={target} focal={focal} references={references}\n")

    # ---------------------------------------------------- structural checks
    print("structure:")
    contrast = [r for r in rows if r["condition"] in ("focal", "reference")]
    by_key: dict[str, list[dict]] = defaultdict(list)
    for row in contrast:
        by_key[row["pair_key"]].append(row)

    check("every matched group holds exactly the five arms",
          all(sorted(r["arm"] for r in g) == sorted([focal, *references])
              for g in by_key.values()),
          f"{len(by_key)} groups")
    check("matched rows share one underlying task X_i",
          all(len({r["task_id"] for r in g}) == 1 for g in by_key.values()))
    check("matched rows share one topic",
          all(len({r["topic"] for r in g}) == 1 for g in by_key.values()))
    check("instruction count is identical across arms",
          all(len({len(r["ordered_ids"]) for r in g}) == 1
              for g in by_key.values()),
          f"k={len(contrast[0]['ordered_ids'])}")
    check("every contrast row scores the target",
          all(r["measured"] == target for r in contrast))
    check("focal and reference prompts differ in exactly one line",
          all(_one_line_apart(g, focal) for g in by_key.values()))
    check("reference identities are exactly the four declared",
          {r["arm"] for r in contrast if r["condition"] == "reference"} == set(references))
    check("reference weights are uniform and sum to 1",
          abs(sum(config["selection"]["reference_weights"].values()) - 1.0) < 1e-12
          and len(set(config["selection"]["reference_weights"].values())) == 1,
          str(config["selection"]["reference_weights"]))
    check("row ids are unique", len({r["row_id"] for r in rows}) == len(rows))

    # ------------------------------------------- technical vs behavioural
    print("\ntechnical failures are not behavioural failures:")
    tech = [r for r in rows if r["technical_failure"]]
    check("no technical failure carries an a_failure value",
          all(r["a_failure"] is None for r in tech), f"{len(tech)} technical failures")
    unscorable = [r for r in rows if not r["scorable"]]
    check("no unscorable row carries an a_failure value",
          all(r["a_failure"] is None for r in unscorable),
          f"{len(unscorable)} unscorable")
    check("every scorable row carries a 0/1 a_failure",
          all(r["a_failure"] in (0, 1) for r in rows if r["scorable"]))

    # ------------------------------------- verifier re-derived from raw text
    print("\nverifier re-derived from the stored response text:")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from dci.verifiers.rules import split_sentences, v_exact_sentence_count

    n_sentences = config["harvest_provenance"]["exact_sentence_count"]
    mismatches = []
    for row in contrast:
        if not row["scorable"]:
            continue
        recomputed = v_exact_sentence_count(row["response"], n_sentences)
        expected = 1 - int(recomputed.binary_pass)
        if expected != row["a_failure"]:
            mismatches.append((row["row_id"], expected, row["a_failure"]))
    check(f"stored a_failure == recomputed 'exactly {n_sentences} sentences'",
          not mismatches, f"{len(mismatches)} mismatches")

    # A must not be scored on B's property. Re-derive on a synthetic pair.
    increasing = " ".join(" ".join(["word"] * (3 + i)) + "." for i in range(n_sentences))
    decreasing = " ".join(" ".join(["word"] * (3 + n_sentences - i)) + "."
                          for i in range(n_sentences))
    check("the target verifier ignores B's ordering property",
          v_exact_sentence_count(increasing, n_sentences).binary_pass
          == v_exact_sentence_count(decreasing, n_sentences).binary_pass == 1)
    check("the target verifier really counts segments",
          len(split_sentences(increasing)) == n_sentences)

    # --------------------------------------------- the contrast, rebuilt
    print("\nheadline contrasts, recomputed from raw rows:")
    outcome: dict[tuple[str, str], int] = {}
    for row in contrast:
        if row["scorable"]:
            outcome[(row["pair_key"], row["arm"])] = row["a_failure"]

    recomputed_tau = {}
    for reference in references:
        diffs = [outcome[(key, focal)] - outcome[(key, reference)]
                 for key in by_key
                 if (key, focal) in outcome and (key, reference) in outcome]
        recomputed_tau[reference] = sum(diffs) / len(diffs) if diffs else float("nan")
        print(f"    tau[B - {reference:12s}] = {recomputed_tau[reference]:+.4f}  "
              f"(n={len(diffs)} matched units)")

    # Uniform-weighted aggregate over units where all five arms scored.
    complete = [k for k in by_key
                if all((k, a) in outcome for a in (focal, *references))]
    weights = config["selection"]["reference_weights"]
    weighted = [outcome[(k, focal)] - sum(weights[r] * outcome[(k, r)] for r in references)
                for k in complete]
    tau_weighted = sum(weighted) / len(weighted) if weighted else float("nan")
    print(f"    tau[weighted, uniform]  = {tau_weighted:+.4f}  (n={len(complete)} complete units)")
    print(f"    tau[min over references]= {min(recomputed_tau.values()):+.4f}")

    # ------------------------------------- compare against the analysis output
    headline_path = run_dir / "analysis" / "headline.json"
    if headline_path.exists():
        print("\nagreement with the analysis module:")
        headline = json.loads(headline_path.read_text(encoding="utf-8"))
        stored = {r["reference"]: r["tau"] for r in headline["contrasts"]
                  if r["order"] == "pooled"}
        for reference in references:
            delta = abs(stored.get(reference, float("nan")) - recomputed_tau[reference])
            check(f"tau[B - {reference}] matches analysis.py", delta < 1e-9,
                  f"analysis={stored.get(reference):+.4f} independent="
                  f"{recomputed_tau[reference]:+.4f}")
        pooled = [a for a in headline["aggregate"] if a["order"] == "pooled"]
        if pooled:
            check("weighted aggregate matches analysis.py",
                  abs(pooled[0]["tau_weighted"] - tau_weighted) < 1e-9,
                  f"analysis={pooled[0]['tau_weighted']:+.4f} independent={tau_weighted:+.4f}")
    else:
        print("\n(no analysis/headline.json yet — run analysis.py to cross-check)")

    print(f"\n{'ALL CHECKS PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
    return 1 if failures else 0


def _one_line_apart(group: list[dict], focal: str) -> bool:
    focal_rows = [r for r in group if r["arm"] == focal]
    if not focal_rows:
        return False
    focal_lines = focal_rows[0]["user_prompt"].splitlines()
    for row in group:
        if row["arm"] == focal:
            continue
        lines = row["user_prompt"].splitlines()
        if len(lines) != len(focal_lines):
            return False
        if sum(1 for a, b in zip(focal_lines, lines) if a != b) != 1:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
