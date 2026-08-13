"""Score a raw generation file from the arbitration programme.

Usage: arb_score.py <raw_generations.jsonl> <scored_generations.jsonl>

Runs in the study venv against the same registry every earlier round used, from
the ANSWER field only. Prints the validity gate -- whether the answer channel
still holds an answer at each budget -- before any scientific quantity, because a
budget whose answers are continued scratch work is not a low-reasoning
observation and must not be read as one.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram

pd.set_option("display.width", 250)

SOURCE = Path(sys.argv[1])
DEST = Path(sys.argv[2])

rows = [json.loads(line) for line in SOURCE.open()]
frame = arbprogram.score(rows)

print(f"### {len(frame)} generations from {SOURCE}\n")
print("### Validity of the answer channel at each assigned budget\n")
gate = frame.groupby("reasoning_budget").agg(
    n=("raw_final_answer", "size"),
    cap_hit=("reasoning_cap_hit", "mean"),
    closed=("closed_naturally", "mean"),
    realised_M=("reasoning_tokens", "mean"),
    answer_tokens=("final_tokens", "mean"),
    truncated=("truncated", "mean"),
    technical_failure=("technical_failure", "mean"),
    leaked=("scratchpad_leakage", "mean"),
    unscorable=("A_status", lambda s: (s == "unscorable").mean()))
print(gate.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n### Compliance by cell (assigned budget is the treatment)\n")
compliance = frame.groupby(
    ["reasoning_budget", "order", "background_name", "arm"]).agg(
    A=("A_pass", "mean"), Q=("Q_pass", "mean"), C=("background_pass", "mean"),
    sentences=("sentence_count", "mean"), words=("word_count", "mean"))
print(compliance.to_string(float_format=lambda v: f"{v:.3f}"))

frame.to_json(DEST, orient="records", lines=True)
print(f"\nwrote {DEST} {len(frame)} scored rows")
