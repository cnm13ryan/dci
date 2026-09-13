#!/usr/bin/env python3
"""Read the signed CONFIRMATORY_ANALYSIS records and render the paper's
machine-readable result tables.

This tool computes nothing scientific: every number it writes is copied
from a signed analysis record (or, where a raw compliance level is needed
for the composition story, from the per-block series the record already
carries). It exists so the paper's tables and figures have a durable,
traceable input instead of transcribed terminal output.

Every record is read from ``evidence/dci1v8/<model>/<stage>/records/`` and
verified (content hash and signature, then study and layer) before anything
is extracted from it, exactly as ``lifecycle.read_stage_record`` does. The
unsigned reader copies under ``durable/`` are never used as input; the
provenance file only records whether each one still equals its verified
payload.

    tools/v8_postconfirm_extract.py --root <confirm root> --out <dir>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from dci1v4.engine.signing import verify_signed     # noqa: E402
from dci1v4.errors import IntegrityError             # noqa: E402

PP = 100.0                       # every emitted magnitude is percentage points
STUDY_ID = "dci1v8"              # the confirmatory study every record must declare
LAYER = "confirm"
MODELS = ("qwen3-4b", "qwen3-4b-instruct-2507",
          "gemma-3n-e2b-it", "gemma-3n-e4b-it")
CONFIGS = ("outcome_first", "outcome_second")
ORDER = {"outcome_first": "B first", "outcome_second": "B second"}


def _pp(x: Any) -> Any:
    return None if x is None else round(float(x) * PP, 4)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root: Path, model: str, stage: str, name: str
         ) -> tuple[dict[str, Any], dict[str, Any]]:
    """The verified payload of one signed stage record, and what was checked.

    Refuses (IntegrityError) on a missing record, a content-hash or signature
    mismatch, or a record that declares another study or layer.
    """
    signed_path = root / "evidence" / STUDY_ID / model / stage / "records" / name
    key = root / "evidence" / STUDY_ID / "keys" / "signing.key"
    if not signed_path.exists():
        raise IntegrityError(f"{model}: {stage} signed record missing at {signed_path}")
    signed = json.loads(signed_path.read_text())
    payload = verify_signed(signed, key, where=f"{model}:{stage}")
    if payload.get("study_id") != STUDY_ID:
        raise IntegrityError(f"{model}: the {stage} record declares study_id "
                             f"{payload.get('study_id')!r}, not {STUDY_ID!r}")
    if payload.get("layer") != LAYER:
        raise IntegrityError(f"{model}: the {stage} record is not a "
                             "confirmatory-layer record")
    reader = root / "durable" / STUDY_ID / model / stage / name
    check = {"signed_record": str(signed_path.relative_to(root)),
             "record_hash": signed["record_hash"], "signature_verified": True,
             "reader_copy_matches_payload": (
                 json.loads(reader.read_text()) == payload
                 if reader.exists() else None)}
    return payload, check


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def member(frame: Mapping[str, Any], cfg: str, family: str, name: str):
    return ((frame.get("configurations", {}).get(cfg, {}).get(family) or {})
            .get("members", {}).get(name))


def joint_member(rec: Mapping[str, Any], cfg: str, w: int, name: str):
    return rec["joint"][cfg]["members"].get(f"f{w}:{name}")


def reading_label(reading: Mapping[str, Any]) -> str:
    """The registered disposition, as one label. Levels first, then the
    markers that stand in place of a level."""
    levels = list(reading.get("levels") or ())
    markers = list(reading.get("markers") or ())
    if levels:
        return "+".join(levels)
    if markers:
        return "+".join(markers)
    return "NO_LEVEL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root, out = Path(args.root).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    primary, raw, perref, refsens, runner, spectrum = [], [], [], [], [], []
    gates_rows, order_rows, f5_rows, ledger_rows = [], [], [], []
    model_rows, proj_rows, l4a_rows = [], [], []
    provenance: dict[str, Any] = {"root": str(root), "models": {}}

    for model in MODELS:
        rec, rec_check = load(root, model, "CONFIRMATORY_ANALYSIS",
                              "confirmatory_analysis.json")
        fz, fz_check = load(root, model, "FROZEN", "freeze.json")
        mb, mb_check = load(root, model, "MEMBERSHIP", "membership.json")
        gen, gen_check = load(root, model, "CONFIRMATORY_GENERATION",
                              "confirmatory_generation.json")
        if rec["inputs"]["generation_record_hash"] != gen_check["record_hash"]:
            raise IntegrityError(f"{model}: the analysis record names generation "
                                 f"record {rec['inputs']['generation_record_hash']}, "
                                 f"but the signed generation record is "
                                 f"{gen_check['record_hash']}")
        provenance["models"][model] = {
            "analysis_record_hash": rec_check["record_hash"],
            "verified_records": {"CONFIRMATORY_ANALYSIS": rec_check,
                                 "FROZEN": fz_check, "MEMBERSHIP": mb_check,
                                 "CONFIRMATORY_GENERATION": gen_check},
            "freeze_hash": rec["inputs"]["freeze_hash"],
            "generation_record_hash": rec["inputs"]["generation_record_hash"],
            "producing_commit": rec["producing_commit"],
            "resamples": rec["resamples"], "n_rows": rec["n_rows"],
            "recorded_at": rec["recorded_at"],
            "frames_entering_local": fz["design"]["frames_entering_local"],
            "frames_entering_spectrum": fz["design"]["frames_entering_spectrum"],
            "model_verdict": rec["model_verdict"],
            "methodological_success": rec["methodological_success"],
            "generation_rows": gen["n_rows"],
        }
        by_frame = mb["by_frame"]
        ms = rec["methodological_success"]
        for cfg in CONFIGS:
            lv = rec["joint"][cfg]["local_model_verdict"]
            model_rows.append({
                "model": model, "order": ORDER[cfg], "configuration": cfg,
                "model_verdict": rec["model_verdict"][cfg],
                "n_local_frames": len(fz["design"]["frames_entering_local"]),
                "local_frames": "|".join(str(x) for x in fz["design"]["frames_entering_local"]),
                "spectrum_frames": "|".join(str(x) for x in fz["design"]["frames_entering_spectrum"]),
                "per_frame_reading": json.dumps(lv["frames"]),
                "frames_agree": len(set(lv["frames"].values())) == 1,
                "l3c_disposition": (lv.get("l3c") or {}).get("disposition"),
                "l3c_scope": (lv.get("l3c") or {}).get("scope"),
                "methodological_success": ms["verdict"],
                "methodological_success_reasons": "|".join(ms.get("reasons") or ()),
                "joint_family_size": rec["joint"][cfg]["family_size"],
                "joint_critical_value": round(rec["joint"][cfg]["critical_value"], 5),
                "n_rows": rec["n_rows"], "resamples": rec["resamples"],
            })

        for wkey, fr in sorted(rec["frames"].items(), key=lambda kv: int(kv[0])):
            w = int(wkey)
            fm = by_frame[wkey]
            core = {c["slot"]: c for c in fm.get("core", ())}
            backups = {c["slot"]: c for c in fm.get("backups", ())}
            for entry in (fr.get("projection_audit") or ()):
                proj_rows.append({"model": model, "frame": w,
                                  "configuration": entry.get("configuration"),
                                  "cell": entry.get("cell"),
                                  "companion": entry.get("companion"),
                                  "projected_mean": entry.get("projected_mean"),
                                  "realised_mean": entry.get("realised_mean"),
                                  "absolute_error_mean": entry.get("absolute_error_mean"),
                                  "absolute_error_max": entry.get("absolute_error_max"),
                                  "allowance": entry.get("allowance"),
                                  "within_allowance": entry.get("within_allowance"),
                                  "n_blocks_degenerate": entry.get("n_blocks_degenerate")})
            l4a = fr.get("l4a") or {}
            for mem, ent in (l4a.get("per_member") or {}).items():
                l4a_rows.append({"model": model, "frame": w, "member": mem,
                                 "agree": ent.get("agree"),
                                 "levels": json.dumps(ent.get("levels")),
                                 "frame_consistent": l4a.get("consistent"),
                                 "differing_members": "|".join(l4a.get("differing_members") or ())})
            for cfg in CONFIGS:
                base = {"model": model, "frame": w, "order": ORDER[cfg],
                        "configuration": cfg}
                # ---------------------------------------------- primary
                if fr["enters_local"]:
                    f1 = member(fr, cfg, "F1", "Delta_R")
                    jm = joint_member(rec, cfg, w, "Delta_R")
                    jt = rec["joint"][cfg]
                    row = dict(base)
                    row.update({
                        "n_star": fm.get("n_star"), "m_star": fm.get("m_star"),
                        "iota_a": round(float(fm.get("iota_a", 0)), 6),
                        "R1": core.get("R1", {}).get("label"),
                        "R2": core.get("R2", {}).get("label"),
                        "R3": core.get("R3", {}).get("label"),
                        "delta_r_pp": _pp(f1["estimate"]),
                        "se_pp": _pp(f1["standard_error"]),
                        "marginal_lower_pp": _pp(f1["marginal_lower"]),
                        "marginal_upper_pp": _pp(f1["marginal_upper"]),
                        "within_frame_lower_pp": _pp(f1["simultaneous_lower"]),
                        "within_frame_upper_pp": _pp(f1["simultaneous_upper"]),
                        "joint_lower_pp": _pp(jm["decision_lower"]),
                        "joint_upper_pp": _pp(jm["decision_upper"]),
                        "joint_half_width_pp": _pp(jm["decision_half_width"]),
                        "joint_family_size": jt["family_size"],
                        "joint_critical_value": round(jt["critical_value"], 5),
                        "joint_topics": jt["topics"],
                        "precision_ok": bool(jm["meets_precondition"]),
                        "registered_reading": reading_label(jm["reading"]),
                        "direction": jm["reading"]["direction"]["direction"],
                        "beyond_sesoi": jm["reading"]["direction"]["beyond_sesoi"],
                        "statuses": "|".join(jm["reading"].get("statuses") or ()),
                        "qualifiers": "|".join(jm["reading"].get("qualifiers") or ()),
                        "boundary": json.dumps(f1.get("boundary")),
                        "blocks": fr["blocks"],
                    })
                    primary.append(row)

                    # ------------------------------- raw composition story
                    dba = member(fr, cfg, "F1", "D(B<-A)")
                    dab = member(fr, cfg, "F1", "D(A<-B)")
                    drs = [member(fr, cfg, "F2", f"D(B<-R{i})") for i in (1, 2, 3)]
                    mean_dr = sum(x["estimate"] for x in drs) / 3.0
                    jdba = joint_member(rec, cfg, w, "D(B<-A)")
                    hr = fr["solo_headroom"]
                    raw.append({**base,
                                "delta_A_pp": _pp(dba["estimate"]),
                                "delta_A_joint_lower_pp": _pp(jdba["decision_lower"]),
                                "delta_A_joint_upper_pp": _pp(jdba["decision_upper"]),
                                "mean_delta_R_pp": _pp(mean_dr),
                                "delta_R1_pp": _pp(drs[0]["estimate"]),
                                "delta_R2_pp": _pp(drs[1]["estimate"]),
                                "delta_R3_pp": _pp(drs[2]["estimate"]),
                                "delta_r_contrast_pp": _pp(member(fr, cfg, "F1", "Delta_R")["estimate"]),
                                "D_A_from_B_pp": _pp(dab["estimate"]),
                                "Lambda_pp": _pp(member(fr, cfg, "F1", "Lambda")["estimate"]),
                                "B_solo_compliance": round(float(hr["B"]["realised_solo_compliance"]), 6),
                                "A_solo_compliance": round(float(hr["A"]["realised_solo_compliance"]), 6),
                                "B_frozen_solo_compliance": round(float(hr["B"]["frozen_solo_compliance"]), 6),
                                "c_B_given_B_plus_A": round(float(hr["B"]["realised_solo_compliance"]) - float(dba["estimate"]), 6),
                                "c_B_given_B_plus_Rbar": round(float(hr["B"]["realised_solo_compliance"]) - float(mean_dr), 6),
                                })

                    # ------------------------------- per-reference contrasts
                    het = (jm["reading"].get("reference_heterogeneity") or {})
                    ests = []
                    for i in (1, 2, 3):
                        dj = member(fr, cfg, "F2", f"Delta_{i}")
                        ests.append(float(dj["estimate"]))
                        perref.append({**base, "reference_slot": f"R{i}",
                                       "reference_label": core.get(f"R{i}", {}).get("label"),
                                       "reference_family": core.get(f"R{i}", {}).get("family"),
                                       "reference_iota": core.get(f"R{i}", {}).get("iota"),
                                       "delta_j_pp": _pp(dj["estimate"]),
                                       "se_pp": _pp(dj["standard_error"]),
                                       "within_family_lower_pp": _pp(dj["simultaneous_lower"]),
                                       "within_family_upper_pp": _pp(dj["simultaneous_upper"]),
                                       "excludes_zero": bool(dj["simultaneous_lower"] > 0 or dj["simultaneous_upper"] < 0),
                                       "side_of_threshold": het.get("sides", {}).get(f"Delta_{i}"),
                                       "B_loss_beside_this_ref_pp": _pp(drs[i - 1]["estimate"]),
                                       "c_B_given_B_plus_this_ref": round(
                                           float(hr["B"]["realised_solo_compliance"])
                                           - float(drs[i - 1]["estimate"]), 6),
                                       "c_B_solo": round(float(hr["B"]["realised_solo_compliance"]), 6),
                                       "c_B_given_B_plus_A": round(
                                           float(hr["B"]["realised_solo_compliance"])
                                           - float(dba["estimate"]), 6),
                                       })
                    spread = max(ests) - min(ests)
                    for r in perref[-3:]:
                        r["family_spread_pp"] = _pp(spread)
                        r["heterogeneity_disagrees"] = het.get("disagrees")
                        r["spread_exceeds_abs_delta_r"] = bool(
                            spread > abs(float(f1["estimate"])))

                    # ------------------------------- reference sensitivity
                    rs = fr["configurations"][cfg].get("F_REFSENS", {}).get("members", {})
                    frozen_key = "Delta_R[R1+R2+R3]"
                    vals = {k: float(v["estimate"]) for k, v in rs.items()}
                    for k, v in sorted(rs.items()):
                        refsens.append({**base, "triple": k[len("Delta_R["):-1],
                                        "is_frozen_triple": k == frozen_key,
                                        "delta_r_pp": _pp(v["estimate"]),
                                        "se_pp": _pp(v["standard_error"]),
                                        "simultaneous_lower_pp": _pp(v["simultaneous_lower"]),
                                        "simultaneous_upper_pp": _pp(v["simultaneous_upper"]),
                                        "reading_on_own_interval": reading_label(v["reading"]) if "reading" in v else "",
                                        "n_admissible_triples": len(rs),
                                        "min_pp": _pp(min(vals.values())) if vals else None,
                                        "max_pp": _pp(max(vals.values())) if vals else None,
                                        "spread_pp": _pp(max(vals.values()) - min(vals.values())) if vals else None,
                                        "sign_changes_across_triples": (min(vals.values()) < 0 < max(vals.values())) if vals else None,
                                        "any_upper_above_10pp": any(float(x["simultaneous_upper"]) > 0.10 for x in rs.values()),
                                        })

                    # ------------------------------- runner-up
                    ru = fr["configurations"][cfg].get("F_RUNNER_UP", {}).get("members", {})
                    for k, v in sorted(ru.items()):
                        runner.append({**base, "arm": k,
                                       "frozen_delta_r_pp": _pp(f1["estimate"]),
                                       "frozen_joint_lower_pp": _pp(jm["decision_lower"]),
                                       "frozen_joint_upper_pp": _pp(jm["decision_upper"]),
                                       "frozen_reading": reading_label(jm["reading"]),
                                       "runner_up_delta_r_pp": _pp(v["estimate"]),
                                       "runner_up_lower_pp": _pp(v["simultaneous_lower"]),
                                       "runner_up_upper_pp": _pp(v["simultaneous_upper"]),
                                       "abs_change_pp": _pp(abs(float(v["estimate"]) - float(f1["estimate"]))),
                                       "sign_change": (float(v["estimate"]) * float(f1["estimate"])) < 0,
                                       "runner_up_reading_own_interval": reading_label(v["reading"]) if "reading" in v else "",
                                       "stability_status": (mb["operating_point_stability"]["by_frame"].get(wkey)),
                                       })

                    # ------------------------------- gates
                    g = fr["gates"][cfg]
                    gates_rows.append({**base,
                                       "l1_B_headroom": g["headroom"]["B"]["has_headroom"],
                                       "l1_A_headroom": g["headroom"]["A"]["has_headroom"],
                                       "l2": json.dumps(g.get("l2"))[:400],
                                       "xi_gate": json.dumps(g.get("xi"))[:400],
                                       "vacuity_binds": g["vacuity"].get("binds"),
                                       "vacuity_gate_binds": g["vacuity"].get("gate_binds"),
                                       "vacuity_forced_agrees": g["vacuity"].get("forced_agrees"),
                                       "vacuity_bounds_pp": json.dumps([
                                           _pp(x) for x in (g["vacuity"].get("partial_identification_bounds") or [])]),
                                       "reference_heterogeneity_disagrees": g["reference_heterogeneity"].get("disagrees"),
                                       "projection_audit": json.dumps(fr.get("projection_audit"))[:600],
                                       })

                    # ------------------------------- F5 recodings
                    f5 = fr["configurations"][cfg].get("F5", {}).get("members", {})
                    for k, v in sorted(f5.items()):
                        if not k.startswith("Delta_R|") and not k.startswith("D(B<-A)|"):
                            continue
                        primary_est = (f1["estimate"] if k.startswith("Delta_R|")
                                       else dba["estimate"])
                        f5_rows.append({**base, "member": k,
                                        "primary_pp": _pp(primary_est),
                                        "recoded_pp": _pp(v["estimate"]),
                                        "movement_pp": _pp(float(v["estimate"]) - float(primary_est)),
                                        "recoded_lower_pp": _pp(v["simultaneous_lower"]),
                                        "recoded_upper_pp": _pp(v["simultaneous_upper"]),
                                        "sign_change": (float(v["estimate"]) * float(primary_est)) < 0,
                                        "recoded_reading": reading_label(v["reading"]) if "reading" in v else "",
                                        })

                # ---------------------------------------------- spectrum
                if fr["enters_spectrum"]:
                    fit = (fr.get("spectrum_fit") or {}).get(cfg) or {}
                    sl = member(fr, cfg, "F_SPECTRUM", "slope")
                    dd = member(fr, cfg, "F1", "delta_difficulty")
                    jdd = joint_member(rec, cfg, w, "delta_difficulty")
                    sup = fit.get("support") or {}
                    spectrum.append({
                        **base,
                        "degenerate": fit.get("degenerate"),
                        "difficulty_a": fit.get("difficulty_a"),
                        "D_B_from_A_pp": _pp(fit.get("D_B_from_A")),
                        "slope": None if sl is None else round(float(sl["estimate"]), 6),
                        "slope_lower": None if sl is None else round(float(sl["simultaneous_lower"]), 6),
                        "slope_upper": None if sl is None else round(float(sl["simultaneous_upper"]), 6),
                        "predicted_loss_at_A_pp": _pp(fit.get("predicted_at_A")),
                        "delta_difficulty_pp": _pp(fit.get("delta_difficulty")),
                        "delta_difficulty_joint_lower_pp": (_pp(jdd["decision_lower"]) if jdd else None),
                        "delta_difficulty_joint_upper_pp": (_pp(jdd["decision_upper"]) if jdd else None),
                        "delta_difficulty_precision_ok": (bool(jdd["meets_precondition"]) if jdd else None),
                        "delta_difficulty_reading": (reading_label(jdd["reading"]) if jdd else None),
                        "support_holds": sup.get("holds"),
                        "support_n_above": sup.get("n_above"),
                        "support_n_below": sup.get("n_below"),
                        "support_reasons": "|".join(sup.get("reasons") or ()),
                        "fitted_range": json.dumps(sup.get("fitted_range")),
                        "dropped_points": json.dumps(fit.get("dropped_points")),
                        "intercepts": json.dumps(fit.get("intercepts")),
                        "residuals": json.dumps({k: round(v, 6) for k, v in (fit.get("residuals") or {}).items()}),
                        "enters_local": fr["enters_local"],
                    })

            # ------------------------------------------- order contrasts
            f11 = fr.get("F11", {}).get("members", {})
            for k, v in sorted(f11.items()):
                order_rows.append({"model": model, "frame": w, "member": k,
                                   "estimate_pp": _pp(v["estimate"]),
                                   "se_pp": _pp(v["standard_error"]),
                                   "simultaneous_lower_pp": _pp(v["simultaneous_lower"]),
                                   "simultaneous_upper_pp": _pp(v["simultaneous_upper"]),
                                   "meets_precondition": v.get("meets_precondition"),
                                   "excludes_zero": bool(v["simultaneous_lower"] > 0 or v["simultaneous_upper"] < 0)})

            # ------------------------------------------- ledger
            for cfg, led in (fr.get("identification_ledger", {})
                             .get("configurations", {}) or {}).items():
                for fam, entries in (led or {}).items():
                    if not isinstance(entries, Mapping):
                        continue
                    for mem, st in entries.items():
                        status = st.get("status") if isinstance(st, Mapping) else st
                        ledger_rows.append({"model": model, "frame": w,
                                            "configuration": cfg, "family": fam,
                                            "member": mem, "status": status})

    write_csv(out / "primary_delta_by_frame_order.csv", primary)
    write_csv(out / "raw_vs_reference_loss.csv", raw)
    write_csv(out / "per_reference_contrasts.csv", perref)
    write_csv(out / "reference_sensitivity.csv", refsens)
    write_csv(out / "runner_up_sensitivity.csv", runner)
    write_csv(out / "spectrum_results.csv", spectrum)
    write_csv(out / "registered_gates.csv", gates_rows)
    write_csv(out / "order_contrasts.csv", order_rows)
    write_csv(out / "recoding_robustness.csv", f5_rows)
    write_csv(out / "identification_ledger.csv", ledger_rows)
    write_csv(out / "model_level_verdicts.csv", model_rows)
    write_csv(out / "projection_audit.csv", proj_rows)
    write_csv(out / "cross_configuration_consistency.csv", l4a_rows)
    (out / "provenance.json").write_text(json.dumps(provenance, indent=1) + "\n")
    (out / "primary_delta_by_frame_order.json").write_text(
        json.dumps(primary, indent=1) + "\n")
    print(json.dumps({"primary": len(primary), "raw": len(raw),
                      "per_reference": len(perref), "refsens": len(refsens),
                      "runner_up": len(runner), "spectrum": len(spectrum),
                      "gates": len(gates_rows), "order": len(order_rows),
                      "recoding": len(f5_rows), "ledger": len(ledger_rows),
                      "model_level": len(model_rows), "projection": len(proj_rows),
                      "l4a": len(l4a_rows),
                      "out": str(out)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
