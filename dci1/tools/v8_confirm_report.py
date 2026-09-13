#!/usr/bin/env python3
"""The study-level confirmatory report, from the signed FINAL_REPORT records.

    python3 tools/v8_confirm_report.py --root <confirm root> [--synthetic]

Reads every model's signed FINAL_REPORT (and the membership lock) and
writes `reports/dci1v8dev/confirmatory/FINAL_REPORT.{md,json}`. Computes
nothing: every number is a field of a signed record.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                          # noqa: E402
from dci1v4.models.registry import MODELS                             # noqa: E402
from dci1v7.protocol import constants as C                            # noqa: E402
from dci1v8dev.confirm import MEMBERSHIP_DOCUMENT                     # noqa: E402
from dci1v8dev.confirm import lifecycle as L                          # noqa: E402

OUT = HERE.parent / "reports" / "dci1v8dev" / "confirmatory" / "FINAL_REPORT"


def collect(root: pathlib.Path, *, synthetic: bool) -> dict[str, Any]:
    ctx = L.confirm_context(root, synthetic=synthetic)
    out: dict[str, Any] = {"root": str(root), "models": {}}
    for spec in MODELS:
        tree = L.confirm_tree(ctx, spec.model_key)
        entry: dict[str, Any] = {"stage_reached": L.stage_reached(tree),
                                 "terminal": L.terminal_status(tree)}
        if tree.stage_record(L.STAGE_REPORT).exists():
            entry["report"] = L.read_stage_record(tree, L.STAGE_REPORT)
            entry["report_hash"] = fs.read_json(tree.stage_record(L.STAGE_REPORT))["record_hash"]
        if tree.stage_record(L.STAGE_FROZEN).exists():
            entry["freeze_hash"] = fs.read_json(tree.stage_record(L.STAGE_FROZEN))["record_hash"]
        out["models"][spec.model_key] = entry
    lock = HERE.parent.parent / MEMBERSHIP_DOCUMENT
    out["membership_lock"] = fs.read_json(lock) if lock.exists() else None
    return out


def _f(x: Any, nd: int = 3) -> str:
    return "—" if x is None else f"{x:+.{nd}f}" if isinstance(x, float) else str(x)


def render(study: dict[str, Any]) -> str:
    L_ = ["# DCI-1 v8 — confirmatory results (frozen design)", "",
          f"Produced by `tools/v8_confirm_report.py` from the signed "
          f"`FINAL_REPORT` records under `{study['root']}`. Every number is a "
          "field of a signed record; nothing is computed here.", ""]
    lock = study.get("membership_lock") or {}
    if lock:
        a = lock["allocation"]
        L_ += ["## Frozen membership and allocation", "",
               "| model | LOCAL frames | SPECTRUM frames | freeze |", "|---|---|---|---|"]
        for m, e in sorted(lock["models"].items()):
            fz = study["models"].get(m, {}).get("freeze_hash")
            L_.append(f"| `{m}` | {e['frames_entering_local']} | "
                      f"{e['frames_entering_spectrum']} | `{(fz or '—')[:12]}` |")
        L_ += ["", f"Allocation: **{a['chosen_blocks_per_frame']} blocks per frame**, "
               f"M = {C.M_DRAWS}; joint family size at decision {a['joint_family_size']}.", ""]
    L_ += ["## Δ_R(f) — the matched-reference contrast, per entering LOCAL frame", "",
           "Positive Δ_R: A costs B more than the matched references do. Decision "
           "intervals are the **joint** simultaneous intervals (topic bootstrap "
           "across frames); the per-frame F1 interval is beside them.", "",
           "| model | cfg | frame | Δ_R | joint interval | frame interval | precision ≤0.05 | levels / markers | ref-sensitivity range (n triples) |",
           "|---|---|---|---:|---|---|---|---|---|"]
    verdicts: list[str] = []
    for m, e in sorted(study["models"].items()):
        rp = e.get("report")
        if not rp:
            verdicts.append(f"| `{m}` | — | {e.get('terminal') or e.get('stage_reached')} |")
            continue
        for cfg in C.CONFIGURATIONS:
            verdicts.append(f"| `{m}` | {cfg} | **{rp['model_verdict'][cfg]}** |")
            for w, fr in sorted(rp["frames"].items()):
                c = fr["configurations"][cfg]
                if "Delta_R" not in c:
                    continue
                j, f = c["Delta_R"]["joint_interval"], c["Delta_R"]["frame_interval"]
                rd = j["reading"] if j else f["reading"]
                rs = c.get("reference_sensitivity") or {}
                L_.append(
                    f"| `{m}` | {cfg} | f{w} | {_f(f['estimate'])} | "
                    f"[{_f(j['lower'])}, {_f(j['upper'])}] | "
                    f"[{_f(f['lower'])}, {_f(f['upper'])}] | "
                    f"{'yes' if (j or f)['meets_precondition'] else 'NO'} | "
                    f"{', '.join(rd.get('levels', [])) or '—'} / "
                    f"{', '.join(rd.get('markers', [])) or '—'}; "
                    f"{rd.get('direction', {}).get('direction', '')} | "
                    f"{_f(rs.get('min'))} … {_f(rs.get('max'))} ({rs.get('n_triples', '—')}) |")
    L_ += ["", "## Model-level LOCAL verdict (conjunction over entering frames)", "",
           "| model | configuration | verdict |", "|---|---|---|"] + verdicts
    L_ += ["", "## SPECTRUM arm — δ_difficulty(f) and the §11.8 slope", "",
           "| model | cfg | frame | δ_difficulty | joint interval | support | slope | slope interval | levels / markers |",
           "|---|---|---|---:|---|---|---:|---|---|"]
    for m, e in sorted(study["models"].items()):
        rp = e.get("report")
        if not rp:
            continue
        for cfg in C.CONFIGURATIONS:
            for w, fr in sorted(rp["frames"].items()):
                c = fr["configurations"][cfg]
                if "delta_difficulty" not in c:
                    continue
                j = c["delta_difficulty"]["joint_interval"] or c["delta_difficulty"]["frame_interval"]
                fit = c.get("spectrum_fit") or {}
                sup = (fit.get("support") or {})
                sl = c.get("slope") or {}
                rd = j["reading"]
                L_.append(
                    f"| `{m}` | {cfg} | f{w} | {_f(j['estimate'])} | "
                    f"[{_f(j['lower'])}, {_f(j['upper'])}] | "
                    f"{'holds' if sup.get('holds') else 'NOT IDENTIFIED'} | "
                    f"{_f(sl.get('estimate'))} | [{_f(sl.get('lower'))}, {_f(sl.get('upper'))}] | "
                    f"{', '.join(rd.get('levels', [])) or '—'} / "
                    f"{', '.join(rd.get('markers', []) + rd.get('statuses', [])) or '—'} |")
    L_ += ["", "## Operating-point stability (P that a topic resample reproduces the frozen n*(f))", "",
           "| model | frame | n* | P(n* reproduced) | m* | P(m* reproduced) |", "|---|---|---|---|---|---|"]
    for m, e in sorted(study["models"].items()):
        rp = e.get("report")
        if not rp:
            continue
        for w, st in sorted((rp.get("stability") or {}).items()):
            if not st:
                continue
            n, mm = st["n_star"], st["m_star"]
            L_.append(f"| `{m}` | f{w} | {n.get('selected')} | {_f(n.get('p_selected_reproduced'), 2)} "
                      f"| {mm.get('selected')} | {_f(mm.get('p_selected_reproduced'), 2)} |")
    L_ += ["", "## Deviations declared on the freeze", ""]
    for m, e in sorted(study["models"].items()):
        rp = e.get("report")
        if rp:
            for d in rp["deviations"]:
                L_.append(f"- {d['what']}: {d['why']}")
            break
    return "\n".join(L_) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    study = collect(pathlib.Path(args.root).resolve(), synthetic=args.synthetic)
    out = pathlib.Path(args.out).with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(study, indent=1, sort_keys=True, default=str) + "\n")
    out.with_suffix(".md").write_text(render(study))
    print(f"wrote {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
