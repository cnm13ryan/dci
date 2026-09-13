"""Every headline number in SCIENTIFIC_FOLLOWUP_EVIDENCE.md, checked against
the artifact it was read from. Writes 11_crosscheck.json.
"""
import json, pathlib
H = pathlib.Path(__file__).resolve().parent
OUT = H / "11_crosscheck.json"
L = json.loads((H / "08_claim_ladder_audit.json").read_text())
E = json.loads((H / "06_effects_and_order.json").read_text())
G = json.loads((H / "03_gate4_anatomy.json").read_text())
A = json.loads((H / "02_admission_landscape.json").read_text())
C = json.loads((H / "09_coverage_vs_calibration.json").read_text())
O = json.loads((H / "07_operating_points.json").read_text())
checks = []


def chk(name, ok, detail=""):
    checks.append({"check": name, "passed": bool(ok), "detail": detail})


for m, want in [("qwen3-4b", {"D(A<-B)|outcome_first": 0.3919,
                              "D(B<-A)|outcome_first": -0.1227,
                              "Lambda|outcome_first": -0.5146,
                              "D(B<-CL)|outcome_first": -0.1341,
                              "Delta_class|outcome_second": 0.0384}),
                ("gemma-3n-e4b-it", {"D(A<-B)|outcome_first": 0.1159,
                                     "D(B<-A)|outcome_second": 0.2832,
                                     "D(B<-CL)|outcome_second": 0.7946,
                                     "Delta_class|outcome_second": -0.5114})]:
    for key, v in want.items():
        name, cfg = key.split("|")
        row = next(r for r in L["models"][m]["rows"]
                   if r["estimand"] == name and r["configuration"] == cfg
                   and r["family"] in ("F1", "F9"))
        chk(f"{m} registered {key}", abs(row["estimate"] - v) < 5e-5,
            f"record {row['estimate']:.6f} vs report {v}")
for m, want in [("qwen3-4b", {"solo:A": 0.7197, "solo:B": 0.7793,
                              "solo:CL": 0.6292,
                              "B|B+CL|outcome_first": 0.9134,
                              "B|B+CL|outcome_second": 0.8298}),
                ("gemma-3n-e4b-it", {"solo:A": 0.7718, "solo:B": 0.8512,
                                     "solo:CL": 0.7152,
                                     "B|B+CL|outcome_second": 0.0566})]:
    for k, v in want.items():
        got = E["models"][m]["raw_cell_means"][k]
        chk(f"{m} raw {k}", abs(got - v) < 5e-5, f"{got:.6f} vs {v}")
chk("e2b Gate-4 failures = 5",
    G["models"]["gemma-3n-e2b-it"]["n_failing"] == 5)
chk("qwen-instruct Gate-4 failures = 1",
    G["models"]["qwen3-4b-instruct-2507"]["n_failing"] == 1)
cl = G["models"]["qwen3-4b-instruct-2507"]["companion_trajectories"]["CL"]
chk("CL8:3 calibration solo 0.9740",
    abs(cl["calibration_solo_compliance"] - 0.9740) < 5e-4)
chk("CL8:3 calibration chance 0.9323",
    abs(cl["calibration_chance_compliance"] - 0.9323) < 5e-4)
chk("CL8:3 Gate-4 solo 0.9896",
    abs(cl["gate4_solo_compliance"] - 0.9896) < 5e-4)
for m, n in [("gemma-3n-e2b-it", 3), ("qwen3-4b", 2),
             ("gemma-3n-e4b-it", 0), ("qwen3-4b-instruct-2507", 0)]:
    chk(f"{m} core references = {n}", A["models"][m]["n_core_references"] == n)
for m, n in [("gemma-3n-e2b-it", 7), ("gemma-3n-e4b-it", 5),
             ("qwen3-4b", 4), ("qwen3-4b-instruct-2507", 4)]:
    chk(f"{m} C4 straddling families = {n}",
        C["models"][m]["n_prescreen_straddling_families_C4"] == n)
chk("all four models passed C1-C7 at pre-screen",
    all(all(v["met"] for v in e["prescreen_coverage_conditions"].values())
        for e in C["models"].values()))
chk("m* is the last measured rung on all four models",
    all(e["m_star_is_last_measured_rung"] for e in O["models"].values()))
chk("qwen3-4b B curve at m=10 is 0.4115",
    abs(O["models"]["qwen3-4b"]["B_solo_compliance_curve_by_m"]["10"] - 0.4115)
    < 5e-4)
chk("e4b B curve at m=10 is 0.8490",
    abs(O["models"]["gemma-3n-e4b-it"]["B_solo_compliance_curve_by_m"]["10"]
        - 0.8490) < 5e-4)
chk("e4b emitted L4 is invalidated by the per-member gate",
    L["models"]["gemma-3n-e4b-it"]["L4_reread_per_member_READ_ONLY"]
    ["emitted_field_is_invalidated"] is True)
chk("qwen3-4b emitted L4 agrees with the per-member gate",
    L["models"]["qwen3-4b"]["L4_reread_per_member_READ_ONLY"]
    ["licensed_by_the_registered_per_member_gate"] is True)
for m in ("qwen3-4b", "gemma-3n-e4b-it"):
    agree = E["models"][m]["recomputation_agrees_with_record"]
    chk(f"{m}: all 10 registered estimates reproduce from rows to 1e-9",
        len(agree) == 10 and all(v["agrees_to_1e-9"] for v in agree.values()),
        f"{len(agree)} estimands compared")
rec = {"_provenance": "POST-HOC: every headline number in "
                      "SCIENTIFIC_FOLLOWUP_EVIDENCE.md checked against the "
                      "artifact it was read from",
       "n_checks": len(checks),
       "n_passed": sum(c["passed"] for c in checks),
       "all_passed": all(c["passed"] for c in checks),
       "checks": checks}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name, rec["n_passed"], "/", rec["n_checks"])
