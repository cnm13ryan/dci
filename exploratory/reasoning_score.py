"""Score the vLLM reasoning-budget run and build the compute-response curves.

Generation happened in the ROCm vLLM environment; scoring happens here, against
the same registry every other round used, from the saved ANSWER field only. The
reasoning channel is never scored and never reaches a verifier.

Assigned budget `b` is the treatment. Realised reasoning `M` is post-treatment
and is only ever plotted descriptively, never conditioned on.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vllm_backend.contract import canonicalise_row  # noqa: E402

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest, mechanism

extensions.register()
STATE = harvest.load()
pd.set_option("display.width", 250)

PATH = Path(sys.argv[1])
TARGET = "A"
# ONE migration boundary: these files are archived generations and are not
# being rewritten. Canonical names only, below this line.
rows = [canonicalise_row(json.loads(line)) for line in PATH.open()]
frame = pd.DataFrame(rows)

# --- validity gate: is the answer channel an ANSWER, or continued scratch? ---
# A budget is usable only if exhausting it still yields a comparable surface.
SCRATCH = re.compile(
    r"\b(wait|let me (check|count|think|see)|i need to|hmm|actually,? (no|wait)|"
    r"let'?s count|recount|that'?s wrong)\b", re.IGNORECASE)
frame["scratch_marker"] = frame["final_answer"].str.contains(SCRATCH, na=False)
frame["answer_empty"] = frame["final_answer"].str.len().eq(0)

print("### Validity of the answer channel at each assigned budget\n")
gate = frame.groupby("reasoning_budget").agg(
    n=("final_answer", "size"),
    cap_hit=("reasoning_cap_hit", "mean"),
    reasoning_closed=("reasoning_closed", "mean"),
    realised_reasoning=("reasoning_tokens", "mean"),
    final_answer_tokens=("final_answer_tokens", "mean"),
    answer_truncated=("answer_truncated", "mean"),
    empty=("answer_empty", "mean"),
    scratch_in_answer=("scratch_marker", "mean"))
print(gate.to_string(float_format=lambda v: f"{v:.3f}"))

# --- score ----------------------------------------------------------------
target_id = frame["measured"].iloc[0]


def verify(text, constraint):
    result = STATE.verify(text, constraint)
    return result.binary_pass, result.status


frame["a_pass"], frame["a_status"] = zip(*[
    verify(t, target_id) for t in frame["final_answer"]])
frame["arm_pass"], _ = zip(*[verify(t, a) for t, a in
                             zip(frame["final_answer"], frame["arm"])])
frame["c_pass"], _ = zip(*[verify(t, v) for t, v in
                           zip(frame["final_answer"], frame["variant"])])
frame["scorable"] = frame["a_status"] != "unscorable"
frame["a_failure"] = (1 - np.asarray(frame["a_pass"], float))
frame["joint"] = (np.asarray(frame["a_pass"], float)
                  * np.asarray(frame["arm_pass"], float)
                  * np.asarray(frame["c_pass"], float))
features = pd.DataFrame([mechanism.row_features(t) for t in frame["final_answer"]],
                        index=frame.index)
frame = pd.concat([frame, features], axis=1)

print("\n\n### Compliance against ASSIGNED reasoning budget (the treatment)\n")
comp = frame.groupby(["reasoning_budget", "arm", "variant"]).agg(
    A=("a_pass", "mean"), QC=("arm_pass", "mean"), C=("c_pass", "mean"),
    joint=("joint", "mean"), sentences=("n_sentences", "mean"))
print(comp.to_string(float_format=lambda v: f"{v:.3f}"))

# --- tau and the amplification contrast, paired over tasks ------------------
rng = np.random.default_rng(20260811)


def boot(values, draws=4000):
    idx = rng.integers(0, len(values), size=(draws, len(values)))
    resampled = values[idx].mean(axis=1)
    return float(np.percentile(resampled, 2.5)), float(np.percentile(resampled, 97.5))


per_task = (frame.groupby(["reasoning_budget", "variant", "arm", "task_id"])
            ["a_failure"].mean())
budgets = sorted(frame["reasoning_budget"].unique())
variants = sorted(frame["variant"].unique())
AMP, CTRL = "X_SEMICOLON_FREE", "X_PAREN_FREE"

print("\n\n### tau(B->A) by budget and background, and the amplification delta\n")
out = []
for b in budgets:
    taus = {}
    for v in variants:
        tau = (per_task.loc[(b, v, "B")] - per_task.loc[(b, v, "C_L3")]).dropna()
        taus[v] = tau
        lo, hi = boot(tau.to_numpy(float))
        out.append({"b": b, "variant": v, "tau": tau.mean(), "lo": lo, "hi": hi,
                    "delta_amp": np.nan, "d_lo": np.nan, "d_hi": np.nan})
    delta = (taus[AMP] - taus[CTRL]).dropna().to_numpy(float)
    lo, hi = boot(delta)
    out[-1] if False else None
    out.append({"b": b, "variant": "DELTA (amp - control)", "tau": np.nan,
                "lo": np.nan, "hi": np.nan,
                "delta_amp": delta.mean(), "d_lo": lo, "d_hi": hi})
print(pd.DataFrame(out).to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

# --- arbitration ------------------------------------------------------------
print("\n\n### Arbitration state by budget (B arm only)\n")
b_arm = frame[frame["arm"] == "B"].copy()
b_arm["state"] = np.select(
    [(b_arm["a_pass"] == 1) & (b_arm["arm_pass"] == 1),
     (b_arm["a_pass"] == 1) & (b_arm["arm_pass"] == 0),
     (b_arm["a_pass"] == 0) & (b_arm["arm_pass"] == 1)],
    ["both", "target only", "focal only"], default="neither")
print(pd.crosstab([b_arm["variant"], b_arm["reasoning_budget"]], b_arm["state"],
                  normalize="index").to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n### Descriptive: realised reasoning M by cell (post-treatment)\n")
print(frame.groupby(["reasoning_budget", "variant", "arm"])["reasoning_tokens"]
      .mean().unstack(["variant", "arm"])
      .to_string(float_format=lambda v: f"{v:.1f}"))

frame.drop(columns=["reasoning_text"]).to_json(
    PATH.with_suffix(".scored.jsonl"), orient="records", lines=True)
