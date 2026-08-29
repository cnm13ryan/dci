#!/usr/bin/env python3
"""Replay the separated local/spectrum validity, the new spectrum selection,
the selected-coverage criterion and the admissible-backup count over stored
evidence (read-only; development candidate).

    python3 tools/v8_spectrum_backtest.py --evidence /path/to/dci1/evidence \\
        [--resamples 10000]

Writes ``reports/dci1v8dev/prescreen/spectrum_backtest.json`` and ``.md``.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev import backtest as B
from dci1v8dev.spectrum.selection import SelectionRule

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / "prescreen"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--resamples", type=int, default=10_000)
    ap.add_argument("--chance-cache", default=str(DCI1 / "reports" / "dci1v8dev" / "chance_basis"))
    args = ap.parse_args()
    ev = Path(args.evidence)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = []
    for tree, model, rel in B.REPLICATIONS:
        rep = B.load_replication(ev, rel, chance_cache_dir=Path(args.chance_cache),
                                 tree=tree, model=model)
        if rep["gate2"] is None:
            print(f"skip {tree}/{model}")
            continue
        r = B.spectrum_backtest(rep, label=tree, model=model,
                                rule=SelectionRule(), resamples=args.resamples)
        results.append(r)
        sel = r["selection"]
        print(f"{tree}/{model}: folded-stable {r['n_folded_stable']} (span "
              f"{r['folded_pool_range']['span']:.2f}) | unfolded-stable "
              f"{r['n_unfolded_stable']} | spectrum-valid {r['n_spectrum_valid']} "
              f"({r['spectrum_valid_below']} below / {r['spectrum_valid_above']} above) "
              f"| selected {sel['families']} -> {sel['status']} "
              f"SE(beta)={_f(sel['coverage']['projection']['se_beta'], 3)} | "
              f"v7 spectrum {r['v7_spectrum_identified']} | backups admissible "
              f"{r['backups']['n_fully_admissible']} recorded-inadmissible "
              f"{r['backups']['recorded_backups_inadmissible']} "
              f"[{time.time() - t0:.0f}s]", flush=True)
    report = {"resamples": args.resamples, "results": results,
              "chance_basis": results[0]["chance_basis"] if results else None,
              "seconds": time.time() - t0,
              "summary": {
                  "n_replications": len(results),
                  "v7_spectrum_identified": sum(
                      1 for r in results if r["v7_spectrum_identified"]),
                  "new_spectrum_identified": sum(
                      1 for r in results if r["selection"]["identified"]),
                  "recorded_backup_inadmissible_replications": sum(
                      1 for r in results
                      if r["backups"]["recorded_backups_inadmissible"]),
                  "meets_min_qualified_on_admissible_basis": sum(
                      1 for r in results if r["backups"]["meets_min_qualified"])}}
    (OUT / "spectrum_backtest.json").write_text(json.dumps(report, indent=1))
    (OUT / "spectrum_backtest.md").write_text(_md(report))
    print("written", OUT)
    return 0


def _f(x, nd=3):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _md(report: dict) -> str:
    s = report["summary"]
    L = ["# Spectrum replay on stored evidence (development candidate)", "",
         f"Bootstrap resamples for the unfolded stability: {report['resamples']}. "
         f"Chance basis: {report.get('chance_basis')} (both the folded and the unfolded "
         "verdicts are recomputed on it; the signed Gate-3A verdicts used the zero column). "
         "Read-only. Folded = v7's §13.7 with V_diff in condition 1; unfolded = "
         "condition 1 on V_coord, V_chance, V_inter_s.", "",
         f"Spectrum identified: v7 {s['v7_spectrum_identified']}/{s['n_replications']}, "
         f"new rule {s['new_spectrum_identified']}/{s['n_replications']}. Replications "
         f"with a recorded frozen backup that is not an admissible core reference: "
         f"{s['recorded_backup_inadmissible_replications']}/{s['n_replications']}.", "",
         "| tree | model | ι_A | folded-stable (v7 pool span) | unfolded-stable | "
         "spectrum-valid (below/above, range) | families selected | points | "
         "offset below/above | SE(β̂) | status | v7 spectrum | admissible families | "
         "new backups | recorded backups (inadmissible) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        sel, cov, bk = r["selection"], r["selection"]["coverage"], r["backups"]
        rng = r["spectrum_valid_range"]
        L.append(f"| {r['tree']} | {r['model']} | {r['iota_a']:.3f} | "
                 f"{r['n_folded_stable']} ({r['folded_pool_range']['span']:.2f}) | "
                 f"{r['n_unfolded_stable']} | {r['n_spectrum_valid']} "
                 f"({r['spectrum_valid_below']}/{r['spectrum_valid_above']}, "
                 f"{_f(rng[0] if rng else None, 2)}–{_f(rng[1] if rng else None, 2)}) | "
                 f"{', '.join(sel['families'])} | {sel['n_spectrum_references']} | "
                 f"{_f(cov['offset_below'], 2)}/{_f(cov['offset_above'], 2)} | "
                 f"{_f(cov['projection']['se_beta'])} | {sel['status']} | "
                 f"{r['v7_spectrum_identified']} | {bk['n_fully_admissible']} | "
                 f"{', '.join(bk['backups'])} | {', '.join(bk['recorded_backups'])} "
                 f"({', '.join(bk['recorded_backups_inadmissible'])}) |")
    L += ["", "## Selected points", ""]
    for r in report["results"]:
        pts = ", ".join(f"{p['candidate']}={p['iota']:.3f} [{p['role']}]"
                        for p in r["selection"]["points"])
        reasons = "; ".join(r["selection"]["coverage"]["reasons"]) or "—"
        L.append(f"- **{r['tree']} / {r['model']}** (ι_A {r['iota_a']:.3f}): {pts}. "
                 f"Coverage reasons: {reasons}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
