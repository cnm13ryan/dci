"""Stage 1: does `X_NO_SEMI_SPLICE` actually suppress splicing here?

The gate is predeclared and is applied before any outcome is looked at. This
design carries the REFERENCE arm only, so the focal-versus-reference contrast is
not computable from it at all.

One thing is stated plainly rather than glossed: `X_NO_SEMI_SPLICE`'s own
verifier IS `splice_count == 0`. Route-instruction compliance and the
manipulation check are therefore the same measurement, not two agreeing ones.
The off-route instruction is independently verifiable (`v_no_exclamation`) and is
checked separately.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram, extensions, harvest, mechanism
from dci_exploratory.extensions import splice_count

pd.set_option("display.width", 240)
SOURCE = Path(sys.argv[1])
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else None

extensions.register()
STATE = harvest.load()
HIGH = 4096

rows = [json.loads(line) for line in SOURCE.open()]
frame = pd.DataFrame(rows)
answers = frame["raw_final_answer"].fillna("")

frame["semicolon_count"] = answers.str.count(";")
frame["semicolon_compliant"] = [int(STATE.verify(t, "X_SEMICOLON_FREE").binary_pass)
                                for t in answers]
frame["splices"] = [splice_count(t, "semicolon") for t in answers]
frame["spliced"] = (frame["splices"] > 0).astype(int)
frame["route_pass"] = [int(STATE.verify(t, r).binary_pass)
                       for t, r in zip(answers, frame["route_id"])]
frame["A_pass"] = [int(STATE.verify(t, "A").binary_pass) for t in answers]
frame["R_pass"] = [int(STATE.verify(t, "C_L3").binary_pass) for t in answers]
features = pd.DataFrame([mechanism.row_features(t) for t in answers], index=frame.index)
frame["sentence_count"] = features.get("n_sentences", np.nan)
frame["period_count"] = features.get("n_periods", np.nan)
frame["word_count"] = features.get("n_words", np.nan)
frame["leaked"] = answers.str.contains(arbprogram.SCRATCH, na=False)
frame["empty"] = answers.str.len().eq(0)
frame["unscorable"] = [STATE.verify(t, "A").status == "unscorable" for t in answers]
frame["malformed"] = frame["empty"] | frame["unscorable"] | frame["truncated"]

print(f"### {len(frame)} preflight generations on {frame['task_id'].nunique()} "
      f"calibration tasks ({frame['task_id'].min()}..{frame['task_id'].max()}), "
      f"reference arm only\n")

print("### Manipulation measurements, by route and reasoning state\n")
table = frame.groupby(["route", "reasoning_budget"]).agg(
    n=("splices", "size"),
    semicolon_compliance=("semicolon_compliant", "mean"),
    mean_semicolons=("semicolon_count", "mean"),
    mean_splices=("splices", "mean"),
    P_spliced=("spliced", "mean"),
    route_pass=("route_pass", "mean"),
    sentences=("sentence_count", "mean"), periods=("period_count", "mean"),
    words=("word_count", "mean"),
    malformed=("malformed", "mean"), truncated=("truncated", "mean"),
    leaked=("leaked", "mean"),
    reasoning_M=("reasoning_tokens", "mean"))
print(table.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n### Splice rate among rows that DID produce exactly one semicolon\n")
compliant = frame[frame["semicolon_compliant"] == 1]
conditional = compliant.groupby(["route", "reasoning_budget"]).agg(
    n=("spliced", "size"), P_spliced_given_compliant=("spliced", "mean"),
    mean_splices=("splices", "mean"))
print(conditional.to_string(float_format=lambda v: f"{v:.3f}"))
print("\n  Conditioning on semicolon compliance is a MANIPULATION DIAGNOSTIC only.")
print("  It is post-treatment and is never used as a scientific outcome estimator.")

print("\n\n### Predeclared manipulation gate, at the primary reasoning state "
      f"(b = {HIGH})\n")


def cell(route: str, budget: int, subset: pd.DataFrame) -> pd.DataFrame:
    return subset[(subset["route"] == route) & (subset["reasoning_budget"] == budget)]


checks, failures = [], []
for budget in sorted(frame["reasoning_budget"].unique()):
    anti = cell("anti_splice", budget, frame)
    off = cell("off_route", budget, frame)
    anti_c = cell("anti_splice", budget, compliant)
    off_c = cell("off_route", budget, compliant)
    checks.append({
        "b": budget,
        "semicolon_compliance_anti": anti["semicolon_compliant"].mean(),
        "semicolon_compliance_off": off["semicolon_compliant"].mean(),
        "P_spliced_anti": anti["spliced"].mean(),
        "P_spliced_off": off["spliced"].mean(),
        "P_spliced_given_compliant_anti": anti_c["spliced"].mean() if len(anti_c) else np.nan,
        "P_spliced_given_compliant_off": off_c["spliced"].mean() if len(off_c) else np.nan,
    })
gate = pd.DataFrame(checks).set_index("b")
gate["absolute_reduction_conditional"] = (gate["P_spliced_given_compliant_off"]
                                          - gate["P_spliced_given_compliant_anti"])
gate["absolute_reduction_unconditional"] = gate["P_spliced_off"] - gate["P_spliced_anti"]
print(gate.to_string(float_format=lambda v: f"{v:.3f}"))

high = gate.loc[HIGH]
print()
rule_1 = high["semicolon_compliance_anti"] >= 0.70
rule_2 = (high["P_spliced_given_compliant_anti"] <= 0.25
          or high["absolute_reduction_conditional"] >= 0.50)
no_new_problem = (cell("anti_splice", HIGH, frame)["malformed"].mean()
                  <= cell("off_route", HIGH, frame)["malformed"].mean() + 0.05)
both_states = all(
    gate.loc[b, "absolute_reduction_conditional"] > 0
    for b in gate.index if not np.isnan(gate.loc[b, "absolute_reduction_conditional"]))

for name, passed, detail in [
    ("1. the anti-splice instruction does not simply remove the semicolon",
     rule_1, f"semicolon compliance under anti-splice at b={HIGH} = "
             f"{high['semicolon_compliance_anti']:.3f} (need >= 0.70)"),
    ("2. splicing is materially reduced",
     rule_2, f"P(splice>0 | compliant, anti-splice) = "
             f"{high['P_spliced_given_compliant_anti']:.3f} (need <= 0.25) OR "
             f"absolute reduction {high['absolute_reduction_conditional']:.3f} "
             f"(need >= 0.50)"),
    ("3. the reduction is visible at both reasoning states",
     both_states, "reduction positive at every budget"),
    ("4. no new systematic parsing or truncation problem",
     no_new_problem, f"malformed anti-splice "
                     f"{cell('anti_splice', HIGH, frame)['malformed'].mean():.3f} vs "
                     f"off-route {cell('off_route', HIGH, frame)['malformed'].mean():.3f}"),
]:
    print(("  PASS  " if passed else "  FAIL  ") + name)
    print(f"        {detail}")
    if not passed:
        failures.append(name)

print()
verdict = "PASS" if not failures else "ANTI_SPLICE_MANIPULATION_FAILED"
if failures:
    print("ANTI_SPLICE_MANIPULATION_FAILED")
    print("  The main experiment is NOT run and no outcome contrast will be")
    print("  interpreted. A failed manipulation is a valid result.")
else:
    print("MANIPULATION GATE PASSED — proceed to the main experiment.")

if DEST:
    DEST.write_text(json.dumps({
        "verdict": verdict, "failures": failures,
        "primary_budget": HIGH,
        "gate": gate.reset_index().to_dict(orient="records"),
        "n_generations": len(frame),
        "calibration_tasks": sorted(frame["task_id"].unique().tolist()),
        "note": ("X_NO_SEMI_SPLICE's verifier is splice_count == 0, so route "
                 "compliance and the manipulation check are the same "
                 "measurement, not two agreeing ones."),
    }, indent=1))
    print(f"\nwrote {DEST}")
frame.to_json(SOURCE.with_name("scored_generations.jsonl"), orient="records", lines=True)
raise SystemExit(0 if not failures else 2)
