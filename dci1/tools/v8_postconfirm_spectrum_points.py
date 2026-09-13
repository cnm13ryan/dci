#!/usr/bin/env python3
"""Dump the difficulty/loss points the registered SPECTRUM fit consumed.

The signed analysis record keeps the fit (slope, intercepts, prediction,
residuals) but not the (difficulty, loss) pairs it was fitted to, and a
scatter of those pairs is what the paper's spectrum figure needs. This tool
re-forms them with the SAME frozen functions the analysis used
(``confirm.analysis.spectrum_input`` + ``dci1v7.analysis.spectrum.estimate``
on the observed sample), and asserts that the slope, the prediction at A and
delta_difficulty it recovers equal the record's to 1e-9. Nothing is
re-decided: it is the analysis's own input, written out.

    tools/v8_postconfirm_spectrum_points.py --root <confirm root> --out <csv>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from dci1v7.analysis import spectrum as SP
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.analysis import frame_table, spectrum_input
from dci1v8dev.confirm.freeze import load_freeze
from dci1v8dev.confirm.generation import collect_rows

MODELS = ("qwen3-4b", "qwen3-4b-instruct-2507",
          "gemma-3n-e2b-it", "gemma-3n-e4b-it")
ORDER = {"outcome_first": "B first", "outcome_second": "B second"}
TOL = 1e-9


def companion_points(data: SP.SpectrumInput
                     ) -> list[tuple[str, str, float, float]]:
    """The (slot, family, difficulty, loss) the registered fit is over.

    The same arithmetic ``spectrum.estimate`` does on the observed sample:
    the block mean of each vector, iota on the registered coordinate, loss
    as B solo minus B beside the companion, with the same degeneracy drop.
    The caller checks each rebuilt point against the fit's own residual.
    """
    mean = lambda v: sum(v) / len(v)
    b_solo = mean(data.b_solo)
    out = []
    # b_solo is returned to the caller through the loss; the caller also
    # records it so the scatter can be drawn in compliance units.
    for slot, family in sorted(data.family_of.items()):
        chance = mean(data.companion_chance[slot])
        if chance >= C.CHANCE_DEGENERACY_MAX:
            continue
        solo = mean(data.companion_solo[slot])
        out.append((slot, family,
                    float(SP.instructed_compliance(solo, chance)),
                    float(b_solo - mean(data.b_with[slot]))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    rows_out: list[dict] = []
    for model in MODELS:
        ctx = L.confirm_context(root)
        tree = L.confirm_tree(ctx, model)
        freeze, _ = load_freeze(tree)
        rec = json.loads((root / "durable" / "dci1v8" / model
                          / "CONFIRMATORY_ANALYSIS"
                          / "confirmatory_analysis.json").read_text())
        rows = collect_rows(tree)
        design = freeze["design"]
        m_draws = int(design["draws"])
        for wkey, frozen in sorted(design["frames"].items(),
                                   key=lambda kv: int(kv[0])):
            w = int(wkey)
            table = frame_table(rows, w, m_draws=m_draws)
            for cfg in C.CONFIGURATIONS:
                data = spectrum_input(table, frozen, cfg)
                if data is None:
                    continue
                est = SP.estimate(data)
                stored = (rec["frames"][wkey].get("spectrum_fit") or {}).get(cfg)
                if stored and not stored.get("degenerate"):
                    for key in ("slope", "predicted_at_A", "delta_difficulty",
                                "difficulty_a", "D_B_from_A"):
                        a, b = float(est[key]), float(stored[key])
                        if abs(a - b) > TOL:
                            raise SystemExit(
                                f"{model} f{w} {cfg} {key}: recovered {a} but "
                                f"the signed record says {b}")
                # The companion points, rebuilt from the same input with the
                # same registered coordinate, then CHECKED against the fit's
                # own residuals: if the point set were not the one the fit
                # used, the residual would not reproduce.
                pts = companion_points(data)
                fit = est.get("fit")
                for slot, family, diff, loss in pts:
                    if fit is not None:
                        want = float(fit.residuals[slot])
                        got = loss - (fit.intercepts[family]
                                      + fit.slope * diff)
                        if abs(want - got) > 1e-9:
                            raise SystemExit(
                                f"{model} f{w} {cfg} {slot}: rebuilt point "
                                f"does not reproduce the fit residual")
                    b_solo = sum(data.b_solo) / len(data.b_solo)
                    rows_out.append({
                        "model": model, "frame": w, "order": ORDER[cfg],
                        "configuration": cfg, "slot": slot,
                        "family": family, "is_focal": False,
                        "difficulty_iota": round(diff, 6),
                        "B_loss_pp": round(loss * 100, 4),
                        "c_B_solo": round(b_solo, 6),
                        "c_B_beside_companion": round(b_solo - loss, 6)})
                rows_out.append({
                    "model": model, "frame": w, "order": ORDER[cfg],
                    "configuration": cfg, "slot": "A", "family": "A",
                    "is_focal": True,
                    "difficulty_iota": round(float(est["difficulty_a"]), 6),
                    "B_loss_pp": round(float(est["D_B_from_A"]) * 100, 4),
                    "c_B_solo": round(sum(data.b_solo) / len(data.b_solo), 6),
                    "c_B_beside_companion": round(
                        sum(data.b_solo) / len(data.b_solo)
                        - float(est["D_B_from_A"]), 6),
                    "predicted_B_loss_pp": round(
                        float(est["predicted_at_A"]) * 100, 4),
                    "residual_pp": round(
                        float(est["delta_difficulty"]) * 100, 4),
                    "slope": round(float(est["slope"]), 6)})
        del rows
    cols: list[str] = []
    for r in rows_out:
        for k in r:
            if k not in cols:
                cols.append(k)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w_ = csv.DictWriter(fh, fieldnames=cols)
        w_.writeheader()
        for r in rows_out:
            w_.writerow(r)
    print(json.dumps({"rows": len(rows_out), "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
