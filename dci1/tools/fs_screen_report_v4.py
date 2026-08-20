#!/usr/bin/env python3
"""Produce the FORM x STEM screen report tables. NON-CONFIRMATORY."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dci1v4.protocol import constants as C
from dci1v4.verifiers.constraints import FOCAL_GRID, REFERENCE_LADDERS, TARGET_GRID

from fs_screen_v4 import analysis as an
from fs_screen_v4 import constraints as cc
from fs_screen_v4 import plan as pl
from fs_screen_v4 import protocol as proto

CELLS = [("count", "current"), ("count", "floored"),
         ("candidate", "current"), ("candidate", "floored")]


def out(*a):
    print(*a)


def main() -> int:
    frozen = proto.load()
    out("# FORM x STEM screen — results\n")
    out(f"**Screen protocol hash:** `{frozen['screen_protocol_hash']}`  ")
    out(f"**Producing commit:** `{frozen['payload']['producing_commit']}`  ")
    out("**Classification: NON-CONFIRMATORY DESIGN SCREEN.** Not a registered "
        "v4 stage; no Gate 1 dependency; nothing here may enter a v4 "
        "estimator.\n")

    data, tables, anchors = {}, {}, {}
    for model in an.MODELS:
        rows = an.load_cells(model)
        data[model] = rows
        tables[model] = an.severity_table(rows, threshold=20)
        anchors[model] = {}
        for stem in pl.STEM_LEVELS:
            try:
                anchors[model][stem] = an.anchor_for(tables[model], stem)
            except KeyError:
                anchors[model][stem] = None

    # ---------------------------------------------------------------- plan
    out("## Cells generated\n")
    out("| model | rows analysed | screen rows generated | reused (registered) | stem obeyed (floored) |")
    out("|---|---:|---:|---:|---:|")
    for model in an.MODELS:
        rows = data[model]
        screen = [r for r in rows if r.get("source") is None]
        reused = len(rows) - len(screen)
        floored = [r for r in rows if r["stem"] == "floored"]
        obeyed = (sum(1 for r in floored if r["stem_satisfied"]) / len(floored)
                  if floored else float("nan"))
        out(f"| {an.SHORT[model]} | {len(rows)} | {len(screen)} | {reused} | "
            f"{obeyed:.3f} |")

    # ------------------------------------------------------- the criterion
    out("\n## The §2.4 reference criterion, by FORM x STEM cell\n")
    out("Families carrying a rung inside the 0.10 caliper of A **and** at solo "
        "vacuity ≤ 0.10, **at the same severity**. Three needed, on all four "
        "models.\n")
    out("| model | " + " | ".join(f"{f} × {s}" for f, s in CELLS) + " |")
    out("|---|" + "---|" * len(CELLS))
    results = {}
    for model in an.MODELS:
        cells = []
        for form, stem in CELLS:
            a = anchors[model].get(stem)
            if a is None:
                cells.append("—")
                continue
            r = an.families_meeting_conjunction(
                tables[model], form=form, stem=stem, anchor=a[1])
            results[(model, form, stem)] = r
            mark = "**" if r["meets_criterion"] else ""
            fams = ",".join(r["families"]) or "none"
            cells.append(f"{mark}{r['n_families']}{mark} ({fams})")
        out(f"| {an.SHORT[model]} | " + " | ".join(cells) + " |")

    out("\n### Which rungs, where the criterion is met\n")
    any_met = False
    for (model, form, stem), r in sorted(results.items()):
        if not r["rungs"]:
            continue
        any_met = True
        out(f"\n**{an.SHORT[model]} — {form} × {stem}** (A anchor "
            f"{r['anchor']:.3f})\n")
        out("| family | severity | raw compliance | solo vacuity | distance from A |")
        out("|---|---:|---:|---:|---:|")
        for fam, rungs in sorted(r["rungs"].items()):
            for g in rungs:
                out(f"| {fam} | {g['severity']} | {g['raw']:.3f} | "
                    f"{g['vacuity']:.3f} | {g['distance']:.3f} |")
    if not any_met:
        out("\nNo (model, FORM, STEM) cell produced a single family meeting "
            "the conjunction.\n")

    # ------------------------------------------------------------- B side
    out("\n## B-side: vacuity and D(B←A) at the fixture severities\n")
    out("| model | stem | B-solo compliance | vacuous share of B passes | "
        "B-solo med words | A+B med words | D(B←A) raw | **D(B←A) §17.4 "
        "forced** | D(B←A) ≥20w only |")
    out("|---|---|---:|---:|---:|---:|---:|---:|")
    for model in an.MODELS:
        for stem in pl.STEM_LEVELS:
            b = an.b_side(data[model], stem)
            if not b.get("available"):
                out(f"| {an.SHORT[model]} | {stem} | — | — | — | — | — | — | — |")
                continue
            out(f"| {an.SHORT[model]} | {stem} | {b['b_solo_compliance']:.3f} | "
                f"**{b['b_solo_vacuous_share_of_passes']:.3f}** | "
                f"{b['b_solo_median_words']:.0f} | "
                f"{b['composed_median_words']:.0f} | "
                f"{b['D_B_from_A_raw']:+.3f} | "
                f"**{b['D_B_from_A_forced']:+.3f}** | "
                f"{b['D_B_from_A_long_only']:+.3f} |")
    out("\nTwo different operations on the same vacuous passes, and only one "
        "of them is registered.\n")
    out("- **§17.4 forced** — every vacuous pass recomputed as a **failure**, "
        "no row dropped, nothing conditioned on. This is the registered "
        "partial-identification bound (§9.3 item 3), and §17.4 licenses a "
        "claim only when it and the raw estimate license the *same* claim.\n")
    out("- **≥20w only** — rows failing the non-vacuity predicate are "
        "**dropped**, separately in each arm. That conditions on a "
        "post-treatment variable and a collider. It is not a corrected "
        "estimate of D(B←A) and must not be used as one.\n")
    out("\nUnder the **current** stem the two disagree completely: on E2B the "
        "raw +0.375 becomes **+0.000** when the bound is applied, and on both "
        "Qwens the sign flips. Vacuous shares there run 0.389–**1.000**. Under "
        "the **floored** stem raw and forced are *identical* on three of four "
        "models and differ by 0.041 on the fourth, because vacuity falls to "
        "0.000–0.167. This is an argument for Amendment A independent of the "
        "reference pool and of the focal grid: without the stem, the "
        "registered bound and the point estimate do not license the same "
        "claim, so §17.4 reports the axis unresolved.\n")

    # ------------------------------------------------------- per severity
    out("\n## Per-severity readouts\n")
    for model in an.MODELS:
        out(f"\n### {an.SHORT[model]}\n")
        out("| form | stem | kind | q | n | raw | non-vac | vac share | trunc | "
            "P(pass\\|<20w) | P(pass\\|≥20w) | mean w | med | q10 | q25 | q75 | q90 | <20w |")
        out("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for key in sorted(tables[model]):
            form, stem, kind, q = key
            c = tables[model][key]
            w = c["words"]
            ps = "—" if c["p_pass_short"] != c["p_pass_short"] else f"{c['p_pass_short']:.2f}"
            plg = "—" if c["p_pass_long"] != c["p_pass_long"] else f"{c['p_pass_long']:.2f}"
            out(f"| {form} | {stem} | {kind} | {q} | {c['n']} | {c['raw']:.3f} | "
                f"{c['non_vacuous']:.3f} | {c['vacuous_share_of_passes']:.2f} | "
                f"{c['truncation']:.2f} | {ps} | {plg} | {w['mean']:.0f} | "
                f"{w['median']:.0f} | {w['q10']:.0f} | {w['q25']:.0f} | "
                f"{w['q75']:.0f} | {w['q90']:.0f} | {w['share_under_threshold']:.2f} |")

    # ------------------------------------------------------- sensitivity
    out("\n## Sensitivity map (a map only)\n")
    out("Registered values are caliper 0.10 and threshold 20 words. "
        "**Not changed by this screen.**\n")
    for form, stem in CELLS:
        out(f"\n**{form} × {stem}** — families meeting the conjunction\n")
        out("| model | " + " | ".join(
            f"T={t}, cal={c}" for t in (10, 20, 30)
            for c in (0.05, 0.10, 0.15)) + " |")
        out("|---|" + "---|" * 9)
        for model in an.MODELS:
            m = an.sensitivity_map(data[model], form=form, stem=stem)
            cells = [str(m.get(f"T={t},caliper={c}", {}).get("n_families", "—"))
                     for t in (10, 20, 30) for c in (0.05, 0.10, 0.15)]
            out(f"| {an.SHORT[model]} | " + " | ".join(cells) + " |")

    # ------------------------------------------------------------- dumps
    dump = {"screen_protocol_hash": frozen["screen_protocol_hash"],
            "classification": "NON-CONFIRMATORY DESIGN SCREEN",
            "criterion_results": {
                f"{m}|{f}|{s}": {k: v for k, v in r.items() if k != "rungs"}
                for (m, f, s), r in results.items()},
            "b_side": {f"{m}|{s}": an.b_side(data[m], s)
                       for m in an.MODELS for s in pl.STEM_LEVELS},
            "severity_tables": {
                m: {f"{k[0]}|{k[1]}|{k[2]}|{k[3]}": v
                    for k, v in tables[m].items()} for m in an.MODELS}}
    path = Path(__file__).resolve().parent.parent / "reports" / "fs_screen_v4" / "results.json"
    path.write_text(json.dumps(dump, indent=1, sort_keys=True, default=str) + "\n")
    out(f"\nMachine-readable results: `{path.relative_to(path.parent.parent.parent)}`\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
