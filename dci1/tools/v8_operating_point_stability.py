"""The operating-point stability report (pre-freeze audit of 2026-09-02,
finding 4): for every model x frame of a confirmatory root, what the signed
``MEMBERSHIP`` record says about how reproducible the frozen n*(f) and m*(f)
are under topic resampling of the calibration set.

Reads signed records only; computes nothing new; changes nothing. The
status rule (``rules.OPERATING_POINT_MIN_RECOVERY``) and the runner-up
sensitivity arm are the confirmatory layer's; this tool renders them.

    tools/v8_operating_point_stability.py --root <confirm root>
        [--out reports/dci1v8dev/freeze_readiness/<operating_point_stability>]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

DCI1 = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.models.registry import MODELS                             # noqa: E402
from dci1v8dev import rules as R                                      # noqa: E402
from dci1v8dev.confirm import lifecycle as L                          # noqa: E402


def collect(root: pathlib.Path, *, synthetic: bool) -> dict:
    ctx = L.confirm_context(root, synthetic=synthetic)
    out: dict = {"root": str(root), "min_recovery": R.OPERATING_POINT_MIN_RECOVERY,
                 "resamples": R.OPERATING_POINT_BOOTSTRAP_RESAMPLES, "models": {}}
    for spec in MODELS:
        tree = L.confirm_tree(ctx, spec.model_key)
        if not tree.stage_record(L.STAGE_MEMBERSHIP).exists():
            continue
        payload = L.read_stage_record(tree, L.STAGE_MEMBERSHIP)
        frames = {}
        for w, e in payload["by_frame"].items():
            st = e.get("stability") or {}
            row = {"supported": bool(e.get("supported")),
                   "enters_local": bool(e.get("enters_local")),
                   "enters_spectrum": bool(e.get("enters_spectrum")),
                   "status": st.get("status"),
                   "runner_up_slots": e.get("runner_up_slots") or []}
            for coord in ("n_star", "m_star"):
                c = st.get(coord) or {}
                row[coord] = {"selected": c.get("selected"),
                              "p_selected_reproduced": c.get("p_selected_reproduced"),
                              "status": c.get("status"),
                              "runner_up": c.get("runner_up"),
                              "p_runner_up": c.get("p_runner_up"),
                              "distribution": c.get("distribution"),
                              "n_topics": c.get("n_topics"), "seed": c.get("seed")}
            row["iota_a_bootstrap"] = (st.get("n_star") or {}).get("iota_a_bootstrap")
            frames[w] = row
        out["models"][spec.model_key] = {
            "record_hash": json.load(open(tree.stage_record(L.STAGE_MEMBERSHIP)))["record_hash"],
            "seed_rule": (payload.get("operating_point_stability") or {}).get("seed_rule"),
            "frames": frames}
    return out


def render(rep: dict) -> str:
    lines = ["# Operating-point stability (signed MEMBERSHIP records)", "",
             f"Root `{rep['root']}`; §12.3 re-run on {rep['resamples']} topic-level "
             f"resamples per supported frame; a coordinate is OPERATING_POINT_UNSTABLE "
             f"when the frozen value is re-selected on fewer than "
             f"{rep['min_recovery']:.3f} of them. The frozen n*(f), m*(f) are never "
             "replaced; Δ_R(f) is conditional on them; an unstable coordinate on a "
             "LOCAL frame adds the runner-up sensitivity arm (A2 / B2).", "",
             "| model | f | arm | n* | P(n* rep.) | runner-up (P) | m* | P(m* rep.) | runner-up (P) | status | runner-up slots |",
             "|---|---|---|---:|---:|---|---:|---:|---|---|---|"]
    for m, e in sorted(rep["models"].items()):
        for w, r in sorted(e["frames"].items()):
            if not r["supported"]:
                lines.append(f"| `{m}` | {w} | — | — | — | — | — | — | — | unsupported | — |")
                continue
            arm = "+".join(a for a, on in (("LOCAL", r["enters_local"]),
                                            ("SPECTRUM", r["enters_spectrum"])) if on) or "none"
            n, mm = r["n_star"], r["m_star"]
            def _ru(c):
                return (f"{c['runner_up']} ({c['p_runner_up']:.2f})"
                        if c.get("runner_up") is not None else "—")
            def _p(c):
                return f"{c['p_selected_reproduced']:.3f}" if c.get("p_selected_reproduced") is not None else "—"
            lines.append(f"| `{m}` | {w} | {arm} | {n['selected']} | {_p(n)} | {_ru(n)} | "
                         f"{mm['selected']} | {_p(mm)} | {_ru(mm)} | {r['status']} | "
                         f"{', '.join(r['runner_up_slots']) or '—'} |")
    lines += ["", "Distributions (share of resamples selecting each severity):", ""]
    for m, e in sorted(rep["models"].items()):
        for w, r in sorted(e["frames"].items()):
            if not r["supported"]:
                continue
            lines.append(f"- `{m}` f{w}: n* {json.dumps(r['n_star']['distribution'])}; "
                         f"m* {json.dumps(r['m_star']['distribution'])}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", default=str(DCI1 / "reports" / "dci1v8dev" / "freeze_readiness"
                                         / "operating_point_stability"))
    args = ap.parse_args(argv)
    rep = collect(pathlib.Path(args.root), synthetic=args.synthetic)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    out.with_suffix(".md").write_text(render(rep))
    print(f"wrote {out.with_suffix('.md')} ({len(rep['models'])} models)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
