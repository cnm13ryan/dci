"""Measure, not assume, whether fixed-seed generation on the pinned backend
is bit-for-bit deterministic (pre-freeze audit of 2026-09-02, finding 12.3).

Takes a stored backend run directory (a pilot stage's ``backend_runs/<run>``:
``plan.json``, ``design.jsonl``, ``rows.jsonl``), re-generates the first
``--n`` design rows twice under the same plan and the same scientific seeds
on one card, and reports three agreements on the raw generated text: the two
fresh runs against each other, and each against the stored rows. Nothing is
scored, nothing is written under an evidence root, and no protected
directory is read (the run directory must belong to a pilot stage).

    tools/v8_backend_determinism.py --run-dir <backend run dir> --device N
        [--n 64] --out reports/dci1v8dev/freeze_readiness/backend_determinism
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import sys

DCI1 = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                          # noqa: E402
from dci1v4.generation.backend import run_backend                     # noqa: E402

PROTECTED = ("CONFIRMATORY_GENERATION", "CONFIRMATORY_ANALYSIS", "FINAL_REPORT")


def _text(row: dict) -> str:
    return str(row.get("raw_generation", row.get("final_answer", "")))


def _agreement(a: list[dict], b: list[dict]) -> dict:
    by_a = {r["row_id"]: _text(r) for r in a}
    by_b = {r["row_id"]: _text(r) for r in b}
    shared = sorted(set(by_a) & set(by_b))
    same = [rid for rid in shared if by_a[rid] == by_b[rid]]
    prefix = []
    for rid in shared:
        x, y = by_a[rid], by_b[rid]
        k = 0
        while k < min(len(x), len(y)) and x[k] == y[k]:
            k += 1
        prefix.append(k / max(1, max(len(x), len(y))))
    return {"n_shared": len(shared), "n_identical": len(same),
            "share_identical": (len(same) / len(shared)) if shared else None,
            "mean_common_prefix_share": (sum(prefix) / len(prefix)) if prefix else None,
            "identical_row_ids": same[:20]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--device", type=int, required=True)
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--out", required=True, help="output path stem (.json/.md)")
    ap.add_argument("--scratch", required=True, help="scratch directory for the two runs")
    args = ap.parse_args(argv)
    run_dir = pathlib.Path(args.run_dir).resolve()
    if any(p in run_dir.parts for p in PROTECTED):
        raise SystemExit("refusing a protected run directory")
    plan = fs.read_json(run_dir / "plan.json")
    design = fs.read_jsonl(run_dir / "design.jsonl")[: args.n]
    stored = {r["row_id"]: r for r in fs.read_jsonl(run_dir / "rows.jsonl")}
    stored_rows = [stored[r["row_id"]] for r in design if r["row_id"] in stored]
    plan = {k: v for k, v in plan.items() if k != "expected_rows"}
    scratch = pathlib.Path(args.scratch)
    outs = []
    for i in (1, 2):
        out = run_backend(scratch / f"run{i}", plan, design, device=args.device,
                          timeout_seconds=3600)
        outs.append(out["rows"])
    result = {
        "run_dir": str(run_dir), "n_rows": len(design), "device": args.device,
        "plan_digest": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:16],
        "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "fresh_vs_fresh": _agreement(outs[0], outs[1]),
        "fresh1_vs_stored": _agreement(outs[0], stored_rows),
        "fresh2_vs_stored": _agreement(outs[1], stored_rows),
        "engine": {k: (fs.read_json(scratch / f"run{k}" / "rows_engine.json")
                       if (scratch / f"run{k}" / "rows_engine.json").exists() else None)
                   for k in (1, 2)},
        "reading": None,
    }
    fv = result["fresh_vs_fresh"]["share_identical"]
    result["reading"] = (
        "bit-for-bit deterministic on this sample" if fv == 1.0 else
        f"NOT bit-for-bit deterministic: {fv:.3f} of rows identical across two "
        "fresh runs under identical plan and seeds; the design, seeds and "
        "verdicts are reproducible as data, the sampled text is not promised")
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    md = [f"# Backend determinism measurement ({result['measured_at']})", "",
          f"Run directory: `{run_dir}`; {len(design)} design rows re-generated twice on "
          f"card {args.device} under the stored plan (digest {result['plan_digest']}) "
          "and the stored scientific seeds.", "",
          "| comparison | rows | identical | share | mean common-prefix share |",
          "|---|---:|---:|---:|---:|"]
    for k in ("fresh_vs_fresh", "fresh1_vs_stored", "fresh2_vs_stored"):
        a = result[k]
        md.append(f"| {k} | {a['n_shared']} | {a['n_identical']} | "
                  f"{a['share_identical']:.3f} | {a['mean_common_prefix_share']:.3f} |"
                  if a["n_shared"] else f"| {k} | 0 | — | — | — |")
    md += ["", f"**Reading.** {result['reading']}", "",
           "What is promised (preregistration §8): every prompt, seed, verdict "
           "and analysis is reproducible as data from the stored rows and the "
           "frozen design; the sampled text is reproducible only to the extent "
           "measured here."]
    out.with_suffix(".md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: result[k] for k in ("fresh_vs_fresh", "fresh1_vs_stored",
                                              "reading")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
