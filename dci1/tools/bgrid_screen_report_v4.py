"""Every §1.3 readout and the §1.4 verdict for the B-grid screen.

NON-CONFIRMATORY. Writes reports/bgrid_screen_v4/results.json and prints the
tables the report quotes. Reads the screen's own evidence and the registered
ladder screen; writes nothing into any registered tree.
"""
from __future__ import annotations

import json
import statistics as stt
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol import constants as C                       # noqa: E402
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID  # noqa: E402

from bgrid_screen_v4 import analysis as an                       # noqa: E402
from bgrid_screen_v4 import focal, plan as pl, protocol as proto  # noqa: E402

OUT = DCI1 / "reports" / "bgrid_screen_v4"


def a_band_status(curve: dict[int, float]) -> dict:
    """§12.3 eligibility of A's curve, with the registered INCLUSIVE bounds."""
    low, high = C.TARGET_BAND
    eligible = [n for n in TARGET_GRID if n in curve and low <= curve[n] <= high]
    n_star, p_star = (an.reanchor_n(curve) if eligible
                      else (None, None)) if curve else (None, None)
    if eligible:
        n_star = min(eligible, key=lambda n: (abs(curve[n] - C.TARGET_AIM), n))
        p_star = curve[n_star]
    return {"curve": {int(k): v for k, v in sorted(curve.items())},
            "band": list(C.TARGET_BAND), "bounds": "inclusive (§12.3)",
            "eligible": eligible,
            "n_star": n_star, "compliance_at_n_star": p_star,
            "would_terminate": not eligible,
            "terminal_status": None if eligible else "TARGET_RANGE_EXHAUSTED"}


def per_model(model: str) -> dict:
    rows = an.load_rows(model)
    floored = an.b_curve(rows, "floored")
    current = an.b_curve(rows, "current")
    verdict_any = an.band_verdict(floored)

    # The §1.4 sentence says "at least one m ... inside the band, and THAT rung
    # sits more than one standard error from both edges". Two readings of the
    # antecedent are possible; both are reported, and they agree here.
    smallest = verdict_any["smallest_in_band"]
    verdict_smallest = {
        "status": ("FAIL" if smallest is None
                   else "PASS" if smallest["clear_of_both_edges"]
                   else "MARGINAL"),
        "rung": smallest}

    a_floored = an.a_curve(rows, "floored")
    in_band_ms = [r["m"] for r in verdict_any["in_band"]]
    return {
        "model_key": model, "short": an.SHORT[model],
        "b_curve_floored": floored, "b_curve_current": current,
        "verdict_any_in_band_rung": verdict_any,
        "verdict_smallest_in_band_rung": verdict_smallest,
        "a_curve_floored": a_band_status(a_floored),
        "d_b_from_a": {m: an.d_b_from_a(rows, m) for m in in_band_ms},
        "d_b_from_a_all_rungs": {m: an.d_b_from_a(rows, m)
                                 for m in focal.SCREEN_FOCAL_GRID},
        "replication_gap": an.replication_gap(model, floored),
        "extrapolation_gap": an.extrapolation_gap(model, floored),
        "stem_satisfaction_floored": stt.fmean(
            [c["stem_satisfied"] for c in floored.values()]),
        "median_words_floored": stt.median(
            [c["words"]["median"] for c in floored.values()]),
        "max_vacuous_share_floored": max(
            c["vacuous_share_of_passes"] for c in floored.values()),
        "max_truncation_floored": max(c["truncation"]
                                      for c in floored.values()),
    }


def main() -> int:
    frozen = proto.load()
    results = {m: per_model(m) for m in an.MODELS}
    study = an.study_verdict(
        {m: r["verdict_any_in_band_rung"] for m, r in results.items()})
    study_alt = an.study_verdict(
        {m: r["verdict_smallest_in_band_rung"] for m, r in results.items()})

    payload = {
        "study_id": "bgrid-screen-v4",
        "classification": "design evidence; non-confirmatory",
        "screen_protocol_hash": frozen["screen_protocol_hash"],
        "producing_commit": frozen["payload"]["producing_commit"],
        "screen_focal_grid": list(focal.SCREEN_FOCAL_GRID),
        "screen_only_extension": list(focal.EXTENSION),
        "registered_focal_grid": list(FOCAL_GRID),
        "seed_root": pl.SCREEN_ROOT_SEED,
        "seed_domain": pl.DOMAIN_SCREEN_GENERATION,
        "analysis_seed": an.ANALYSIS_SEED,
        "bootstrap_draws": an.BOOTSTRAP_DRAWS,
        "verdict": study,
        "verdict_under_the_stricter_reading": study_alt,
        "reading_note": (
            "§1.4 says 'at least one m inside the band, and THAT rung sits more "
            "than one standard error from both band edges'. The permissive "
            "reading takes the antecedent to be any in-band rung; the stricter "
            "reading takes it to be the smallest in-band rung of §1.3. Both are "
            "reported. They give the same study verdict."),
        "models": results,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")

    # ------------------------------------------------------------- tables
    print("### B-solo compliance under the floored stem (raw)\n")
    header = "| model | " + " | ".join(f"m={m}" for m in
                                       focal.SCREEN_FOCAL_GRID) + " |"
    print(header)
    print("|---" * (len(focal.SCREEN_FOCAL_GRID) + 1) + "|")
    for m in an.MODELS:
        c = results[m]["b_curve_floored"]
        cells = " | ".join(f"{c[k]['raw']:.3f}" for k in focal.SCREEN_FOCAL_GRID)
        print(f"| {an.SHORT[m]} | {cells} |")

    print("\n### Topic-clustered standard errors\n")
    print(header)
    print("|---" * (len(focal.SCREEN_FOCAL_GRID) + 1) + "|")
    for m in an.MODELS:
        c = results[m]["b_curve_floored"]
        cells = " | ".join(f"{c[k]['cluster']['se']:.3f}"
                           for k in focal.SCREEN_FOCAL_GRID)
        print(f"| {an.SHORT[m]} | {cells} |")

    print("\n### §1.4 verdict\n")
    print("| model | in-band m | smallest | clear of both edges | permissive | strict |")
    print("|---|---|---|---|---|---|")
    for m in an.MODELS:
        r = results[m]
        v = r["verdict_any_in_band_rung"]
        clear = [x["m"] for x in v["in_band"] if x["clear_of_both_edges"]]
        sm = v["smallest_in_band"]
        print(f"| {an.SHORT[m]} | {[x['m'] for x in v['in_band']]} | "
              f"{sm['m'] if sm else '--'} | {clear or '--'} | {v['status']} | "
              f"{r['verdict_smallest_in_band_rung']['status']} |")
    print(f"\n**study verdict: {study['verdict']}** "
          f"(stricter reading: {study_alt['verdict']})")

    print("\n### Vacuity, truncation, stem satisfaction (floored)\n")
    print("| model | max vacuous share of passes | max truncation | "
          "stem satisfied | median words |")
    print("|---|---|---|---|---|")
    for m in an.MODELS:
        r = results[m]
        print(f"| {an.SHORT[m]} | {r['max_vacuous_share_floored']:.3f} | "
              f"{r['max_truncation_floored']:.3f} | "
              f"{r['stem_satisfaction_floored']:.3f} | "
              f"{r['median_words_floored']:.1f} |")

    print("\n### A under the floored stem: §12.3 target-band eligibility\n")
    print("| model | eligible n | n* | compliance at n* | would terminate |")
    print("|---|---|---|---|---|")
    for m in an.MODELS:
        a = results[m]["a_curve_floored"]
        print(f"| {an.SHORT[m]} | {a['eligible']} | {a['n_star']} | "
              f"{a['compliance_at_n_star']:.3f} | {a['would_terminate']} |")

    print("\n### Replication of the FORM x STEM floored B curve\n")
    print("| model | " + " | ".join(f"m={m}" for m in FOCAL_GRID)
          + " | mean abs gap |")
    print("|---" * (len(FOCAL_GRID) + 2) + "|")
    for m in an.MODELS:
        g = results[m]["replication_gap"]
        cells = " | ".join(
            f"{g['per_m'][k]['fs_screen']:.3f}->{g['per_m'][k]['bgrid_screen']:.3f}"
            if k in g["per_m"] else "--" for k in FOCAL_GRID)
        print(f"| {an.SHORT[m]} | {cells} | {g['mean_abs_gap']:.3f} |")

    print("\n### Pooled extrapolation against direct measurement\n")
    print("| model | m=11 predicted | m=11 measured | gap | m=12 predicted | "
          "m=12 measured | gap |")
    print("|---|---|---|---|---|---|---|")
    for m in an.MODELS:
        e = results[m]["extrapolation_gap"]
        row = []
        for k in focal.EXTENSION:
            v = e["per_m"].get(k)
            row += ([f"{v['predicted']:.3f}", f"{v['measured']:.3f}",
                     f"{v['gap']:+.3f}"] if v else ["--", "--", "--"])
        print(f"| {an.SHORT[m]} | " + " | ".join(row) + " |")

    print("\n### D(B<-A) at every screen rung, floored\n")
    print("| model | " + " | ".join(f"m={m}" for m in focal.SCREEN_FOCAL_GRID)
          + " |")
    print("|---" * (len(focal.SCREEN_FOCAL_GRID) + 1) + "|")
    for m in an.MODELS:
        d = results[m]["d_b_from_a_all_rungs"]
        cells = " | ".join(f"{d[k]['D_B_from_A_raw']:+.3f}"
                           if d[k].get("available") else "--"
                           for k in focal.SCREEN_FOCAL_GRID)
        print(f"| {an.SHORT[m]} | {cells} |")
    print(f"\nwritten: {(OUT / 'results.json').relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
