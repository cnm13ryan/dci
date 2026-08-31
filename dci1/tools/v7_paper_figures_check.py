#!/usr/bin/env python3
"""Independent audit of the generated main-paper figures and Table 1.

Deliberately does NOT import the generator. It re-reads the signed
`FINAL_REPORT` records, re-derives every number the outputs claim, and parses
`table1_primary_results.tex` back out of LaTeX to compare it digit for digit.

Also checks the properties that cannot be seen in a number: that no repeat lane
reached an output, that every figure carries eight canonical configurations,
that the vector outputs exist and are non-trivial, and that the CSV each figure
consumes agrees with the signed records.

Two halves, and only one of them runs from a bare checkout. The
**signed-record** half re-reads `FINAL_REPORT/final_report.json` under
`dci1/evidence`, which is gitignored and absent from a clone; the
**committed-extract** half checks the figures against the CSVs and LaTeX that
ship beside them. When the evidence tree is absent the tool says so, skips the
first half and runs the second, and exits non-zero only on a real failure ---
rather than dying on a `FileNotFoundError` that reads like a bug.

Usage:  python dci1/tools/v7_paper_figures_check.py
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIGS = REPO / "dci1" / "reports" / "dci1v7" / "paper_figures"
EVIDENCE = REPO / "dci1" / "evidence"
DOSSIER = REPO / "dci1" / "reports" / "dci1v7" / "dossier"

fails: list[str] = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def close(a, b, tol=1e-12):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=tol)


def load_csv(p):
    with p.open() as fh:
        return list(csv.DictReader(fh))


# ---- the signed truth ------------------------------------------------------
lanes = {l["model"]: l for l in load_csv(DOSSIER / "lanes.csv")
         if l["lane_role"] == "canonical"}
repeat_lanes = {l["lane_id"] for l in load_csv(DOSSIER / "lanes.csv")
                if l["lane_role"] != "canonical"}
signed = {}
missing_records = []
for lane in lanes.values():
    root, model = lane["lane_id"].split("/", 1)
    record = (EVIDENCE / root / "evidence" / "dci1v7" / model / "FINAL_REPORT"
              / "final_report.json")
    if not record.exists():
        missing_records.append(str(record.relative_to(REPO)))
        continue
    with record.open() as fh:
        for res in json.load(fh)["results"]:
            signed[(lane["lane_id"], res["member"],
                    res["configuration"] or "cross")] = res

HAVE_SIGNED = not missing_records
if not HAVE_SIGNED:
    print("The signed FINAL_REPORT records are not in this checkout, so the "
          "half of this audit that re-derives every number from them cannot "
          "run. `dci1/evidence` is gitignored: obtain the evidence trees to "
          "get the full audit. Checking the committed extracts instead.")
    print(f"  {len(missing_records)} record(s) absent, first: "
          f"{missing_records[0]}\n")

check(len(lanes) == 4, f"expected 4 canonical lanes, found {len(lanes)}")

# ---- figure CSVs -----------------------------------------------------------
f2 = load_csv(FIGS / "figure2_delta_r_forest_data.csv")
f3 = load_csv(FIGS / "figure3_loss_decomposition_data.csv")
f4 = load_csv(FIGS / "figure4_direction_position_data.csv")
f4o = load_csv(FIGS / "figure4_order_contrasts_data.csv")
t1 = load_csv(FIGS / "table1_primary_results_data.csv")

for name, rows, n in (("figure2", f2, 8), ("figure3", f3, 8), ("figure4", f4, 8),
                      ("table1", t1, 8), ("figure4 order contrasts", f4o, 8)):
    check(len(rows) == n, f"{name}: expected {n} rows, got {len(rows)}")
    used = {r["lane_id"] for r in rows}
    check(not (used & repeat_lanes),
          f"{name}: repeat lane present -> {used & repeat_lanes}")
    check(len({(r.get('model'), r.get('b_position') or r.get('member'))
               for r in rows}) == n, f"{name}: duplicate configurations")

cfg_of = {"first": "outcome_first", "second": "outcome_second"}

for r in f2:
    if not HAVE_SIGNED:
        continue
    s = signed[(r["lane_id"], "Delta_R", cfg_of[r["b_position"]])]
    check(close(float(r["Delta_R"]), s["point"]),
          f"fig2 {r['lane_id']} {r['b_position']} Delta_R point")
    check(close(float(r["Delta_R_sim_lower"]), s["simultaneous_lower"]),
          f"fig2 {r['lane_id']} {r['b_position']} lower")
    check(close(float(r["Delta_R_sim_upper"]), s["simultaneous_upper"]),
          f"fig2 {r['lane_id']} {r['b_position']} upper")
    # the L3c reading the figure asserts by placing the threshold at +10
    check(s["simultaneous_upper"] < 0.10,
          f"fig2 {r['lane_id']} {r['b_position']}: upper bound is not below +0.10")

for r in f3:
    if not HAVE_SIGNED:
        continue
    cfg = cfg_of[r["b_position"]]
    s_dr = signed[(r["lane_id"], "Delta_R", cfg)]
    s_ba = signed[(r["lane_id"], "D(B<-A)", cfg)]
    check(close(float(r["D_B_from_A"]), s_ba["point"]),
          f"fig3 {r['lane_id']} {r['b_position']} D(B<-A)")
    check(close(float(r["D_B_from_Rbar_DERIVED"]), s_ba["point"] - s_dr["point"]),
          f"fig3 {r['lane_id']} {r['b_position']} D(B<-Rbar) identity")
    check(close(float(r["solo_B"]) - float(r["B_given_A"]), s_ba["point"]),
          f"fig3 {r['lane_id']} {r['b_position']} cell levels reproduce D(B<-A)")
    check(close(float(r["D_B_from_A"]) - float(r["D_B_from_Rbar_DERIVED"]),
                s_dr["point"]),
          f"fig3 {r['lane_id']} {r['b_position']} plotted separation == Delta_R")

for r in f4:
    if not HAVE_SIGNED:
        continue
    b_cfg = cfg_of[r["b_position"]]
    a_cfg = cfg_of[r["A_measured_position"]]
    check(b_cfg != a_cfg,
          f"fig4 {r['lane_id']} {r['prompt_order']}: the two losses of one prompt "
          "must come from complementary configurations")
    s_b = signed[(r["lane_id"], "D(B<-A)", b_cfg)]
    s_a = signed[(r["lane_id"], "D(A<-B)", a_cfg)]
    check(close(float(r["D_B_from_A"]), s_b["point"]),
          f"fig4A {r['lane_id']} {r['prompt_order']} D(B<-A)")
    check(close(float(r["D_A_from_B"]), s_a["point"]),
          f"fig4A {r['lane_id']} {r['prompt_order']} D(A<-B)")
    check((r["D_B_from_A_position_confounded"] == "True") == (r["b_position"] == "second"),
          f"fig4A {r['lane_id']}: B confound flag disagrees with B's position")
    check((r["D_A_from_B_position_confounded"] == "True")
          == (r["A_measured_position"] == "second"),
          f"fig4A {r['lane_id']}: A confound flag disagrees with A's position")
    # exactly one of the two marks in a row is position-confounded
    check((r["D_B_from_A_position_confounded"] == "True")
          != (r["D_A_from_B_position_confounded"] == "True"),
          f"fig4A {r['lane_id']} {r['prompt_order']}: expected exactly one "
          "confounded mark per prompt")

for r in f4o:
    if not HAVE_SIGNED:
        continue
    s = signed[(r["lane_id"], r["member"], "cross")]
    check(close(float(r["estimate"]), s["point"]), f"fig4B {r['lane_id']} {r['member']}")
    check(close(float(r["sim_lower"]), s["simultaneous_lower"]),
          f"fig4B {r['lane_id']} {r['member']} lower")
    check(close(float(r["sim_upper"]), s["simultaneous_upper"]),
          f"fig4B {r['lane_id']} {r['member']} upper")
    check(s["status"] == "IDENTIFIED",
          f"fig4B {r['lane_id']} {r['member']} is not IDENTIFIED and must not be drawn")

# ---- Table 1, parsed back out of the LaTeX --------------------------------
tex = (FIGS / "table1_primary_results.tex").read_text()
body = tex.split(r"\midrule")[1].split(r"\bottomrule")[0]
rowpat = re.compile(
    r"^\s*(?P<model>[^&]*?)\s*&\s*(?P<pos>first|second)\s*\((?P<prompt>[AB]\+[AB])\)\s*"
    r"&\s*\$(?P<dba>[+-][\d.]+)\$\s*&\s*\$(?P<drb>[+-][\d.]+)\$\s*&\s*"
    r"\$(?P<dr>[+-][\d.]+)\$(?P<dag>(\\,\$\^\{\\dagger\}\$)?)\s*&\s*"
    r"\$\[(?P<lo>[+-][\d.]+),\\;(?P<hi>[+-][\d.]+)\]\$"
    r"\s*\\\\\s*$")
parsed = [m.groupdict() for line in body.splitlines() if (m := rowpat.match(line))]
check(len(parsed) == 8, f"table1: parsed {len(parsed)} data rows, expected 8")

for p, r in zip(parsed, t1):
    check(p["pos"] == r["b_position"], f"table1 order mismatch at {p}")
    check(p["prompt"] == r["prompt_order"], f"table1 prompt mismatch at {p}")
    for key, col in (("dba", "D_B_from_A"), ("drb", "D_B_from_Rbar_DERIVED"),
                     ("dr", "Delta_R")):
        check(close(float(p[key]), round(float(r[col]) * 100, 1), tol=5e-2),
              f"table1 {p['prompt']} {key}: tex {p[key]} vs data "
              f"{float(r[col]) * 100:.1f}")
    for key, col in (("lo", "Delta_R_sim_lower"), ("hi", "Delta_R_sim_upper")):
        check(close(float(p[key]), round(float(r[col]) * 100, 1), tol=5e-2),
              f"table1 {p['prompt']} CI {key}: tex {p[key]} vs data "
              f"{float(r[col]) * 100:.1f}")
    compressed = (r["positive_direction_compressed"] == "True"
                  or r["negative_direction_compressed"] == "True")
    check(bool(p["dag"]) == compressed,
          f"table1 {p['prompt']}: dagger marks compression={bool(p['dag'])} but "
          f"the record says {compressed}")

check(r"\usepackage{booktabs}" in tex, "table1: booktabs requirement not stated")
check("Development-rehearsal evidence" in tex,
      "table1 caption does not calibrate to development evidence")

# ---- outputs exist and are real -------------------------------------------
for stem in ("figure2_delta_r_forest", "figure3_loss_decomposition",
             "figure4_direction_position"):
    for ext, floor in (("pdf", 8_000), ("svg", 20_000), ("png", 40_000)):
        p = FIGS / f"{stem}.{ext}"
        check(p.exists(), f"missing {p.name}")
        if p.exists():
            check(p.stat().st_size > floor,
                  f"{p.name} is only {p.stat().st_size} bytes")
    svg = (FIGS / f"{stem}.svg").read_text()
    check("Gemma 3n E2B" in svg and "Qwen3 4B Instruct" in svg,
          f"{stem}.svg: model labels are not live text")
    for repeat in repeat_lanes:
        check(repeat.split("/")[0] not in svg, f"{stem}.svg mentions a repeat lane")

cap = (FIGS / "captions.md").read_text() if (FIGS / "captions.md").exists() else ""
# Phrase checks below run against whitespace-normalised text. A caption is
# markdown: where its lines wrap is a formatting accident, and a check that a
# claim is *present* must not depend on one. `cap` itself is kept for the
# checks that look for a literal token such as "$+9.9$ pp".
cap_flat = " ".join(cap.split())
check(cap, "captions.md missing")
for token in ("Figure 2", "Figure 3", "Figure 4", "Table 1"):
    check(token in cap, f"captions.md has no entry for {token}")
check(cap.lower().count("development") >= 4,
      "captions.md: every caption must calibrate to development evidence")

# the load-bearing numeric claims inside the captions
n_below_zero = sum(1 for r in f2 if float(r["Delta_R_sim_upper"]) < 0)
# Case-insensitive, as the "development" check above already is: the claim
# under audit is the count, not whether it opens a sentence.
check("in three of the eight" in cap_flat.lower() and n_below_zero == 3,
      f"captions.md claims a count of intervals wholly below zero; the data say "
      f"{n_below_zero}")
attainable = sorted({round(float(r["attainable_max"]) * 100, 1) for r in f2
                     if r["positive_direction_compressed"] == "True"})
check(attainable == [9.9] and "$+9.9$ pp" in cap,
      f"captions.md quotes the attainable bound; the data say {attainable}")
e4b = next(r for r in f3 if r["model"] == "gemma-3n-e4b-it"
           and r["b_position"] == "second")
check(f"{float(e4b['D_B_from_A']) * 100:.1f}" == "39.2"
      and f"{float(e4b['D_B_from_Rbar_DERIVED']) * 100:.1f}" == "46.4"
      and "$39.2$ pp" in cap and "$46.4$" in cap,
      "captions.md quotes the Gemma E4B loss pair; it disagrees with the data")
check("equivalen" not in cap.lower(),
      "captions.md must not claim equivalence to zero")
check("pooled" not in cap.lower(),
      "captions.md must not describe anything as pooled across models")

# ---- report ----------------------------------------------------------------
print(f"ran {checks} checks")
if fails:
    for f in fails:
        print("  FAIL:", f)
    raise SystemExit(f"{len(fails)} check(s) failed")
print("all checks passed")
