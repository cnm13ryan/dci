"""Q1/Q2/Q7. Registered effects read from signed records, plus one clearly
labelled POST-HOC cross-configuration contrast.

The registered half copies estimate/se/half-width/marginal/simultaneous
straight out of the signed UNMASKED_ANALYSIS record and recomputes each
point estimate from the raw rows as a check.

The post-hoc half exists because **no registered cross-configuration
contrast is defined anywhere in v4r4** --- `FAMILY_MEMBERS` has no order
member and the analysis stores no bootstrap replicates, so an order contrast
cannot be read off the artifact. The block-paired difference below is a
descriptive diagnostic: it carries no claim level, no multiplicity
adjustment and no identification status, and it is not evidence at the
registered confidence level. It is here so a reader can tell
"the two point estimates differ" from "a direct contrast was tested".

Writes 06_effects_and_order.json.
"""
import json, sys, pathlib, random, statistics
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record
from dci1v4r4.protocol import constants as C
from dci1v4r4.run.analysis_run import observation_table
from dci1v4r4.analysis import estimators as E
from dci1v4r4.run.confirmatory_run import collect_rows

OUT = pathlib.Path(__file__).resolve().parent / "06_effects_and_order.json"
SURVIVORS = ("qwen3-4b", "gemma-3n-e4b-it")
EV = DCI1 / "evidence" / "dci1v4r4"
ctx = registered_context()


def rows_for(model):
    """The same `resolved.jsonl` rows the registered analysis reads."""
    return collect_rows(model_tree(ctx, model))


def paired_ci(diff, resamples=10000, seed=20260822):
    """Percentile bootstrap over blocks. POST-HOC; no multiplicity."""
    rng = random.Random(seed)
    n = len(diff)
    means = []
    for _ in range(resamples):
        means.append(sum(diff[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return {"estimate": sum(diff) / n,
            "ci95": [means[int(0.025 * resamples)], means[int(0.975 * resamples)]],
            "se": statistics.pstdev(means), "resamples": resamples,
            "n_blocks": n}


rec = {"_provenance": "registered values copied from signed records; the "
                      "cross-configuration contrast is POST-HOC and carries "
                      "no claim",
       "registered_family_members": {k: list(v) for k, v in C.FAMILY_MEMBERS.items()},
       "no_registered_order_contrast":
           "v4r4 registers no cross-configuration contrast: FAMILY_MEMBERS has "
           "no order member, and the UNMASKED_ANALYSIS record stores no "
           "bootstrap replicates, so no registered artifact tests an order "
           "difference. L4 is the only registered cross-configuration "
           "statement, and its emitter is defective (see 07_claim_ladder).",
       "not_registered_quantities": {
           "D(CL<-B)": "the data exist (CL's compliance in the B+CL and CL+B "
                       "cells against solo:CL) but no registered family "
                       "contains it; reported below as POST-HOC only",
           "D(A<-CL)": "NOT_IDENTIFIED and NOT_REGISTERED: no A+CL cell exists "
                       "in any §8.6 design, so the data do not exist either"},
       "models": {}}

for model in SURVIVORS:
    t = model_tree(ctx, model)
    freeze = read_stage_record(t, C.STAGE_GATE5)
    final = read_stage_record(t, C.STAGE_UNMASKED_ANALYSIS)
    table = observation_table(rows_for(model), m_draws=int(freeze["m_draws"]),
                              variant=freeze["design_variant"])
    entry = {"design_variant": freeze["design_variant"],
             "slot_map": freeze["slot_map"],
             "identification_statuses": freeze["identification_statuses"],
             "registered": {}, "post_hoc": {}}
    # ---- registered, copied verbatim
    for cfg, e in sorted(final["result"].items()):
        entry["registered"][cfg] = {
            "f6_gate": e.get("f6_gate"), "precision": e.get("precision"),
            "families": {fam: {"critical_value": f["critical_value"],
                               "sidak_reference": f["sidak_reference"],
                               "family_size": len(f["members"]),
                               "members": f["members"]}
                         for fam, f in sorted(e["families"].items())}}
    # ---- raw cell means, and the registered point estimates recomputed
    raw, check = {}, {}
    for slot in ("A", "B", C.CLASS_SLOT):
        raw[f"solo:{slot}"] = statistics.fmean(E.solo_vector(table, slot))
    for outcome, companion in (("A", "B"), ("B", "A"), ("B", C.CLASS_SLOT),
                               (C.CLASS_SLOT, "B")):
        for cfg in C.CONFIGURATIONS:
            try:
                v = E.composed_vector(table, outcome, companion, cfg)
            except Exception as exc:
                raw[f"{outcome}|{outcome}+{companion}|{cfg}"] = f"UNAVAILABLE: {exc}"
                continue
            raw[f"{outcome}|{outcome}+{companion}|{cfg}"] = statistics.fmean(v)
            d = E.delivery_loss(table, outcome, companion, cfg)
            check[f"D({outcome}<-{companion})|{cfg}"] = statistics.fmean(d)
    for cfg in C.CONFIGURATIONS:
        check[f"Lambda|{cfg}"] = statistics.fmean(E.asymmetry(table, cfg))
        check[f"Delta_class|{cfg}"] = statistics.fmean(E.delta_class(table, cfg))
    entry["raw_cell_means"] = raw
    entry["recomputed_point_estimates"] = check
    entry["recomputation_agrees_with_record"] = {}
    for cfg, e in final["result"].items():
        for fam, f in e["families"].items():
            for name, m in f["members"].items():
                key = f"{name}|{cfg}"
                if key in check:
                    entry["recomputation_agrees_with_record"][f"{fam}:{key}"] = {
                        "record": m["estimate"], "recomputed": check[key],
                        "abs_diff": abs(m["estimate"] - check[key]),
                        "agrees_to_1e-9": abs(m["estimate"] - check[key]) < 1e-9}
    # ---- POST-HOC cross-configuration contrasts, block-paired
    post = {}
    for outcome, companion in (("A", "B"), ("B", "A"), ("B", C.CLASS_SLOT)):
        try:
            a = E.delivery_loss(table, outcome, companion, "outcome_first")
            b = E.delivery_loss(table, outcome, companion, "outcome_second")
        except Exception:
            continue
        post[f"D({outcome}<-{companion}): outcome_first - outcome_second"] = \
            paired_ci([x - y for x, y in zip(a, b)])
    la = E.asymmetry(table, "outcome_first")
    lb = E.asymmetry(table, "outcome_second")
    post["Lambda: outcome_first - outcome_second"] = paired_ci(
        [x - y for x, y in zip(la, lb)])
    ca = E.delta_class(table, "outcome_first")
    cb = E.delta_class(table, "outcome_second")
    post["Delta_class: outcome_first - outcome_second"] = paired_ci(
        [x - y for x, y in zip(ca, cb)])
    # D(CL<-B): registered nowhere; the cells exist, so it is computable
    for cfg in C.CONFIGURATIONS:
        try:
            post[f"D(CL<-B)|{cfg} [NOT_REGISTERED]"] = {
                "estimate": statistics.fmean(
                    E.delivery_loss(table, C.CLASS_SLOT, "B", cfg))}
        except Exception as exc:
            post[f"D(CL<-B)|{cfg} [NOT_REGISTERED]"] = f"UNAVAILABLE: {exc}"
    entry["post_hoc"] = {
        "_label": "POST-HOC DESCRIPTIVE. No claim level, no multiplicity "
                  "adjustment, not a registered estimand.",
        "cross_configuration_paired_differences": post}
    rec["models"][model] = entry
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
