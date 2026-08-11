"""Draw the manual-inspection sample and print each output with its labels.

The sample is deterministic in the file it is drawn from, so the same rows come
back on a re-run and the recorded ids stay meaningful.

Each printed row carries, beside the registry's verdict, a count from the
INDEPENDENT segmenter in `independent_segmenter.py` -- a character scanner with
no shared helpers and no shared abbreviation table. Where the two disagree the
row is flagged, so a manual check is looking at a real disagreement rather than
at a reimplementation of the same blind spot.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from independent_segmenter import count as independent_count

SCORED = Path(sys.argv[1])
frame = pd.read_json(SCORED, lines=True)
seed = int.from_bytes(hashlib.blake2b(SCORED.name.encode(), digest_size=8).digest(),
                      "big")
rng = np.random.default_rng(seed % (2 ** 32))


def sample(subset: pd.DataFrame, n: int, label: str) -> pd.DataFrame:
    if subset.empty:
        print(f"\n\n===== {label}: none available =====")
        return subset
    take = min(n, len(subset))
    picked = subset.iloc[rng.choice(len(subset), size=take, replace=False)]
    print(f"\n\n===== {label}: {take} of {len(subset)} available =====")
    return picked


def report(picked: pd.DataFrame) -> None:
    for _, row in picked.iterrows():
        text = row["raw_final_answer"]
        independent = independent_count(text)
        agree = "agree" if independent == row["sentence_count"] else "DISAGREE"
        print(f"\n--- row_id {row['row_id']}  {row['task_id']}  {row['order']}  "
              f"{row['background_name']}  arm={row['arm']}  "
              f"b={row['reasoning_budget']}  rep={row['replicate_id']}  "
              f"seed={row['actual_request_seed']}")
        print(f"    labels: A_pass={row['A_pass']} Q_pass={row['Q_pass']} "
              f"C_pass={row['background_pass']} state={row['arbitration_state']!r}")
        print(f"    sentences: registry={row['sentence_count']} "
              f"independent={independent} [{agree}]  words={row['word_count']} "
              f"leaked={row['scratchpad_leakage']}")
        print("    " + text.replace("\n", "\n    "))


focal = frame[frame["arm"] == "B"]
report(sample(frame, 20, "20 outputs drawn across all conditions"))
report(sample(focal[focal["arbitration_state"] == "target only"], 10, "target only"))
report(sample(focal[focal["arbitration_state"] == "focal only"], 10, "focal only"))
report(sample(focal[focal["arbitration_state"] == "both"], 10, "both"))

# The most surprising cell: the largest change in A-failure between the two
# budgets, chosen from the data rather than named in advance.
pivot = frame.groupby(["order", "background_name", "arm", "reasoning_budget"])[
    "A_failure"].mean().unstack("reasoning_budget")
swing = (pivot.iloc[:, -1] - pivot.iloc[:, 0]).abs().sort_values(ascending=False)
order, background, arm = swing.index[0]
print(f"\n\n(most surprising cell by |A-failure change across budget|: "
      f"{order} {background} arm={arm}, swing {swing.iloc[0]:+.3f})")
surprising = frame[(frame["order"] == order)
                   & (frame["background_name"] == background)
                   & (frame["arm"] == arm)]
report(sample(surprising, 10, f"most surprising cell: {order} {background} {arm}"))
