#!/usr/bin/env python3
"""Audit the exact-count wording instrument on stored Gate-2 rows (read-only).

    python3 tools/v8_wording_audit.py --evidence /path/to/dci1/evidence [--workers 3]

Writes ``reports/dci1v8dev/prescreen/wording_audit.json`` and ``.md``: per
(replication, family, severity, wording) exact-count compliance, zero-marker
share, over/undershoot, the gap to sibling wordings; flagged wordings per
family and model; and the MK ladders reconstructed on all four wordings and
on the robust subset, with monotonicity, span and location against iota_A.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev import backtest as B
from dci1v8dev import wording as W

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / "prescreen"


def _job(args):
    tree, model, model_dir = args
    md = Path(model_dir)
    g2 = md / "GATE_2_FOCAL_CALIBRATION" / "backend_runs"
    paths = [p for p in (g2 / "candidates" / "scored.jsonl",
                         g2 / "grid-A" / "scored.jsonl") if p.exists()]
    if not paths:
        return None
    t0 = time.time()
    scan = W.scan_rows(paths)
    rec = _load(md / "GATE_2_FOCAL_CALIBRATION" /
                         "gate2_focal_calibration.json")
    iota_a = float(rec["iota_a"])
    table = W.wording_table(scan)
    flags = W.flag_wordings(table)
    all_w = W.ladders_under(scan, wordings_used=range(4), iota_a=iota_a)
    per_wording = {w: W.ladders_under(scan, wordings_used=[w], iota_a=iota_a)
                   for w in range(4)}
    # drop per-topic vectors from the JSON (kept in memory only)
    slim = {k: {kk: vv for kk, vv in v.items() if kk != "per_topic"}
            for k, v in scan.items()}
    return {"tree": tree, "model": model, "iota_a": iota_a, "scan": slim,
            "table": table, "flags": flags, "ladders_all_wordings": all_w,
            "ladders_per_wording": per_wording,
            "patterns": W.misinterpretation_patterns(table),
            "seconds": time.time() - t0}


def _load(path):
    with open(path) as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    ev = Path(args.evidence)
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(t, m, str(ev / rel)) for t, m, rel in B.REPLICATIONS]
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for r in pool.map(_job, jobs):
            if r is None:
                continue
            results.append(r)
            print(f"{r['tree']}/{r['model']}: {r['seconds']:.0f}s; flagged "
                  f"{ {k: [w for w, v in ws.items() if v['flagged']] for k, ws in r['flags'].items() if any(v['flagged'] for v in ws.values())} } "
                  f"[{time.time() - t0:.0f}s]", flush=True)
    # robust subset per model: wordings NOT flagged for A or any MK family
    # in a majority of that model's replications
    robust = _robust_by_model(results)
    for r in results:
        used = robust[r["model"]]["robust_wordings"]
        # re-scan is expensive; the per-wording ladders are combined instead
        r["ladders_robust"] = _combine(r["ladders_per_wording"], used, r["iota_a"])
    report = {"frames": list(W.WORDING_FRAMES), "results": results,
              "robust_by_model": robust, "seconds": time.time() - t0}
    (OUT / "wording_audit.json").write_text(json.dumps(report, indent=1))
    (OUT / "wording_audit.md").write_text(_md(report))
    print("written", OUT)
    return 0


def _robust_by_model(results):
    out = {}
    models = sorted({r["model"] for r in results})
    for m in models:
        reps = [r for r in results if r["model"] == m]
        votes = {w: 0 for w in range(4)}
        for r in reps:
            for ws in r["flags"].values():
                for w, v in ws.items():
                    if v["flagged"]:
                        votes[int(w)] += 1
        n_cells = len(reps) * 9      # A + 8 MK families
        flagged = [w for w, c in votes.items() if c >= max(2, 0.2 * n_cells)]
        robust = [w for w in range(4) if w not in flagged] or list(range(4))
        out[m] = {"flag_votes": votes, "n_family_replications": n_cells,
                  "flagged_wordings": flagged, "robust_wordings": robust}
    return out


def _combine(per_wording, used, iota_a):
    """Pool the per-wording ladders over ``used`` (n-weighted)."""
    from dci1v8dev.prescreen.ladder import spearman
    out = {}
    fams = sorted(set().union(*[set(per_wording[w]) for w in used]))
    for kind in fams:
        ladder = {}
        for w in used:
            lad = per_wording[w].get(kind, {}).get("ladder", {})
            for q, v in lad.items():
                e = ladder.setdefault(q, {"n": 0, "passed": 0.0})
                e["n"] += v["n"]
                e["passed"] += v["rate"] * v["n"]
        xs = sorted(ladder, key=int)
        ys = [ladder[q]["passed"] / ladder[q]["n"] for q in xs]
        rho = spearman([float(q) for q in xs], ys)
        span = (max(ys) - min(ys)) if len(ys) >= 2 else 0.0
        out[kind] = {"ladder": {q: {"rate": y, "n": ladder[q]["n"]}
                                for q, y in zip(xs, ys)},
                     "rho_severity_iota": rho, "span_all": span,
                     "min_iota": min(ys) if ys else None,
                     "max_iota": max(ys) if ys else None,
                     "reaches_below": min(ys) <= iota_a - 0.15 if ys else None,
                     "reaches_above": max(ys) >= iota_a + 0.10 if ys else None,
                     "classification": W._classify(rho, span, ys, iota_a),
                     "wordings_used": list(used)}
    return out


def _f(x, nd=2):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _md(report):
    L = ["# Wording audit: the exact-count instrument (read-only, exploratory)", "",
         "Frames (w0–w3), shared by A and MK1–MK8:", ""]
    for i, f in enumerate(report["frames"]):
        L.append(f"- w{i}: `{f}`")
    L += ["", "## Misinterpretation patterns per wording (MK families pooled)", ""]
    for r in report["results"]:
        L += [f"### {r['tree']} / {r['model']} (ι_A {r['iota_a']:.3f})", "",
              "| wording | rows | exact | zero-marker | under | over | exactly once (q>1) | mean |miss| |",
              "|---|---|---|---|---|---|---|---|"]
        for w, p in sorted(r["patterns"].items()):
            L.append(f"| w{w} | {p['n_rows']} | {p['exact']:.3f} | {p['zero']:.3f} | "
                     f"{p['under']:.3f} | {p['over']:.3f} | "
                     f"{p['one_regardless_of_q']:.3f} | {p['mean_abs_miss']:.2f} |")
        L.append("")
    L += ["## Flagged wordings (relative to sibling wordings, per family)", "",
          "| tree | model | family | w0 gap / zero-excess | w1 | w2 | w3 | flagged |",
          "|---|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        for kind, ws in sorted(r["flags"].items()):
            cells = [f"{_f(ws[w]['mean_gap_to_others'])} / {_f(ws[w]['mean_zero_excess'])}"
                     if w in ws else "—" for w in sorted(ws)]
            flagged = [f"w{w}" for w, v in ws.items() if v["flagged"]]
            L.append(f"| {r['tree']} | {r['model']} | {kind} | " + " | ".join(cells)
                     + f" | {', '.join(flagged) or '—'} |")
    L += ["", "## Robust wording subset per model", ""]
    for m, v in report["robust_by_model"].items():
        L.append(f"- **{m}**: flag votes {v['flag_votes']} over "
                 f"{v['n_family_replications']} family×replication cells → "
                 f"flagged {v['flagged_wordings']}, robust {v['robust_wordings']}")
    L += ["", "## MK ladders: all four wordings vs the robust subset", "",
          "| tree | model | family | ρ(all) | span(all) | class(all) | ρ(robust) | "
          "span(robust) | class(robust) | min ι | max ι | reaches −0.15 | reaches +0.10 | rungs >0.90 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        for kind in sorted(r["ladders_all_wordings"]):
            a = r["ladders_all_wordings"][kind]
            b = r["ladders_robust"].get(kind, {})
            L.append(f"| {r['tree']} | {r['model']} | {kind} | {_f(a['rho_severity_iota'])} | "
                     f"{_f(a['span_all'])} | {a['classification']} | "
                     f"{_f(b.get('rho_severity_iota'))} | {_f(b.get('span_all'))} | "
                     f"{b.get('classification', '—')} | {_f(b.get('min_iota'))} | "
                     f"{_f(b.get('max_iota'))} | {b.get('reaches_below', '—')} | "
                     f"{b.get('reaches_above', '—')} | {a['n_over_0_90']} |")
    L += ["", "## Per-rung wording table (exact-count compliance by wording)", ""]
    for r in report["results"]:
        L += [f"### {r['tree']} / {r['model']}", "",
              "| family | q | w0 | w1 | w2 | w3 | zero w0..w3 | over w0..w3 |",
              "|---|---|---|---|---|---|---|---|"]
        by = {}
        for t in r["table"]:
            by.setdefault((t["kind"], t["severity"]), {})[t["wording"]] = t
        for (kind, q), ws in sorted(by.items()):
            rates = [(_f(ws[w]["rate"]) if w in ws else "—") for w in range(4)]
            zeros = "/".join(_f(ws[w]["zero"]) if w in ws else "—" for w in range(4))
            overs = "/".join(_f(ws[w]["over"]) if w in ws else "—" for w in range(4))
            L.append(f"| {kind} | {q} | " + " | ".join(rates) + f" | {zeros} | {overs} |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
