"""Score the boundary-control preflight and apply the fixed selection rule.

The rule was written down before the numbers existed and is applied here in the
order it was written:

  1. valid literal rendering and verification
  2. no systematic formatting/parser problem
  3. background compliance closest to the semicolon's
  4. response-length behaviour closest to the semicolon's
  5. prefer the degree symbol if still tied

Nothing about focal-versus-reference interference is computable from this design
— it contains no focal-arm rows — so the choice cannot be contaminated by the
outcome the main experiment measures.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram, extensions, harvest, mechanism

pd.set_option("display.width", 240)
SOURCE = Path(sys.argv[1])
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else None

extensions.register()
STATE = harvest.load()

SEMICOLON = "X_SEMICOLON_FREE"
CANDIDATES = ["X_DEGREE_FREE", "X_ASTERISK_FREE"]
MARK_CHAR = {SEMICOLON: ";", "X_DEGREE_FREE": "°", "X_ASTERISK_FREE": "*"}
#: Any markdown structure, anywhere in the answer. Reported, but NOT the gate:
#: the first version of this script used it as criterion 2 and disqualified both
#: candidates, because a model writing `**temperature sensor**` in ordinary prose
#: was scored as a formatting problem for the DEGREE symbol — whose count that
#: markup cannot touch. Kept as a descriptive column and corrected below.
MARKDOWN_ANYWHERE = re.compile(r"\*\*|^\s*[-*•]\s+|^\s*#{1,6}\s+", re.MULTILINE)
#: Characters that carry structural meaning in markdown. A mark drawn from this
#: set can be emitted by the model as MARKUP and then counted as if it were the
#: literal character the instruction asked for; a mark outside it cannot.
MARKUP_ACTIVE = set("*_-#`>")


def markup_collision(text: str, char: str) -> bool:
    """Is the COUNTED character being used as markdown structure?

    This is the hazard, and it is the one pinned by
    `tests/test_boundary_and_ladder.py` before any generation existed:
    `**emphasis**` and a leading `* ` bullet both change the asterisk count,
    while nothing a model can write makes a degree symbol structural.
    """
    if char not in MARKUP_ACTIVE:
        return False
    doubled = re.escape(char) * 2
    bullet = rf"^\s*{re.escape(char)}\s+"
    return bool(re.search(doubled, text) or re.search(bullet, text, re.MULTILINE))

rows = [json.loads(line) for line in SOURCE.open()]
frame = pd.DataFrame(rows)
answers = frame["raw_final_answer"].fillna("")

frame["mark_pass"] = [int(STATE.verify(t, v).binary_pass)
                      for t, v in zip(answers, frame["variant"])]
frame["mark_count"] = [STATE.verify(t, v).detail.get("observed", np.nan)
                       for t, v in zip(answers, frame["variant"])]
frame["A_pass"] = [int(STATE.verify(t, "A").binary_pass) if k == "combined" else np.nan
                   for t, k in zip(answers, frame["prompt_kind"])]
frame["R_pass"] = [int(STATE.verify(t, "C_L3").binary_pass) if k == "combined" else np.nan
                   for t, k in zip(answers, frame["prompt_kind"])]
features = pd.DataFrame([mechanism.row_features(t) for t in answers], index=frame.index)
frame["sentence_count"] = features.get("n_sentences", np.nan)
frame["word_count"] = features.get("n_words", np.nan)
frame["leaked"] = answers.str.contains(arbprogram.SCRATCH, na=False)
frame["empty"] = answers.str.len().eq(0)
frame["markdown_anywhere"] = answers.str.contains(MARKDOWN_ANYWHERE, na=False)
frame["markup_collision"] = [markup_collision(t, MARK_CHAR[v])
                             for t, v in zip(answers, frame["variant"])]
frame["unscorable"] = [STATE.verify(t, v).status == "unscorable"
                       for t, v in zip(answers, frame["variant"])]
#: Malformed = the answer could not be scored, was empty, or was cut off.
frame["malformed"] = frame["empty"] | frame["unscorable"] | frame["truncated"]

print(f"### {len(frame)} preflight generations on {frame['task_id'].nunique()} "
      f"calibration tasks (disjoint from the 20 evaluation tasks)\n")

print("### 1-5. compliance, malformed rate, truncation, answer length\n")
table = frame.groupby(["variant", "prompt_kind", "reasoning_budget"]).agg(
    n=("mark_pass", "size"),
    mark_compliance=("mark_pass", "mean"),
    mean_mark_count=("mark_count", "mean"),
    A_pass=("A_pass", "mean"), R_pass=("R_pass", "mean"),
    malformed=("malformed", "mean"), truncated=("truncated", "mean"),
    leaked=("leaked", "mean"),
    answer_tokens=("final_tokens", "mean"),
    words=("word_count", "mean"), sentences=("sentence_count", "mean"))
print(table.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n### 6. formatting side effects: was the COUNTED mark produced as MARKUP?\n")
side = frame.groupby("variant").agg(
    markdown_anywhere=("markdown_anywhere", "mean"),
    markup_collision=("markup_collision", "mean"),
    mark_count_gt_1=("mark_count", lambda s: float((s > 1).mean())),
    mark_count_0=("mark_count", lambda s: float((s == 0).mean())))
print(side.to_string(float_format=lambda v: f"{v:.3f}"))
print("\n  `markdown_anywhere` counts any markdown in the answer and is NOT the")
print("  gate: a model writing **temperature sensor** in prose cannot change a")
print("  degree-symbol count. `markup_collision` asks whether the COUNTED")
print("  character is itself being used as structure, which is the hazard the")
print("  pre-generation tests pinned.\n")
for variant in frame["variant"].unique():
    bad = frame[(frame["variant"] == variant) & (frame["markup_collision"])]
    if len(bad):
        example = bad.iloc[0]["raw_final_answer"][:150].replace("\n", " / ")
        print(f"  {variant}: {len(bad)} of {(frame['variant'] == variant).sum()} "
              f"answers use the counted mark as markup; e.g.\n    {example}\n")

print("\n\n### Fixed selection rule, applied in order\n")
# Criteria 3 and 4 are read off the COMBINED rows: in the main design the
# background is always carried with A and an arm, so that is the condition whose
# compliance and length have to match. The isolated rows answer preflight item 1
# and are reported separately above. This choice cannot move the selection --
# criterion 2 settles it before 3 and 4 are consulted -- and the pooled table is
# printed beside it so both are visible.
combined = frame[frame["prompt_kind"] == "combined"]
pooled = frame.groupby("variant").agg(
    compliance=("mark_pass", "mean"), malformed=("malformed", "mean"),
    collision=("markup_collision", "mean"), words=("word_count", "mean"),
    tokens=("final_tokens", "mean"), sentences=("sentence_count", "mean"))
print("pooled over both prompt kinds:")
print(pooled.to_string(float_format=lambda v: f"{v:.3f}"))
pooled = combined.groupby("variant").agg(
    compliance=("mark_pass", "mean"), malformed=("malformed", "mean"),
    collision=("markup_collision", "mean"), words=("word_count", "mean"),
    tokens=("final_tokens", "mean"), sentences=("sentence_count", "mean"))
print("\ncombined rows only (the main design's condition):")
print(pooled.to_string(float_format=lambda v: f"{v:.3f}"))

reference = pooled.loc[SEMICOLON]
verdicts, surviving = [], []
for candidate in CANDIDATES:
    row = pooled.loc[candidate]
    # 1. literal rendering and verification
    literal = frame[frame["variant"] == candidate]["mark_count"].notna().all()
    # 2. systematic formatting / parser problem: does markup made of the counted
    #    character corrupt the count, and is the count usually the right one?
    formatting_ok = (row["collision"] <= 0.05 and row["malformed"] <= 0.05
                     and float((combined[combined["variant"] == candidate]
                                ["mark_count"] > 1).mean()) <= 0.35)
    verdicts.append({
        "candidate": candidate,
        "1_literal": "pass" if literal else "FAIL",
        "2_formatting": "pass" if formatting_ok else "FAIL",
        "markup_collision": row["collision"], "malformed_rate": row["malformed"],
        "count_gt_1": float((combined[combined["variant"] == candidate]["mark_count"] > 1).mean()),
        "3_compliance_gap": abs(row["compliance"] - reference["compliance"]),
        "4_length_gap_words": abs(row["words"] - reference["words"]),
        "4_length_gap_tokens": abs(row["tokens"] - reference["tokens"])})
    if literal and formatting_ok:
        surviving.append(candidate)
print()
print(pd.DataFrame(verdicts).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print()
if not surviving:
    print("BOUNDARY_CONTROL_NOT_IDENTIFIED")
    print("  no candidate passed criteria 1-2; the boundary experiment is stopped "
          "rather than run against a weak control.")
    raise SystemExit(2)

table_v = pd.DataFrame(verdicts).set_index("candidate").loc[surviving]
best_gap = table_v["3_compliance_gap"].min()
close = [c for c in surviving
         if table_v.loc[c, "3_compliance_gap"] <= best_gap + 0.05]
if len(close) > 1:
    best_len = table_v.loc[close, "4_length_gap_words"].min()
    close = [c for c in close
             if table_v.loc[c, "4_length_gap_words"] <= best_len + 5.0]
selected = "X_DEGREE_FREE" if "X_DEGREE_FREE" in close else close[0]
print(f"  criteria 1-2 survived by: {', '.join(surviving)}")
print(f"  criterion 3 (compliance closest to semicolon, within 0.05): "
      f"{', '.join(close)}")
print(f"\nSELECTED CONTROL = {selected}")

if DEST:
    DEST.write_text(json.dumps({
        "selected": selected,
        "reference": SEMICOLON,
        "candidates": CANDIDATES,
        "surviving_criteria_1_2": surviving,
        "rule": ["literal rendering and verification",
                 "no systematic formatting/parser problem",
                 "background compliance closest to semicolon",
                 "response length closest to semicolon",
                 "prefer degree symbol on a remaining tie"],
        "pooled": pooled.to_dict(orient="index"),
        "verdicts": verdicts,
        "n_generations": len(frame),
        "calibration_tasks": sorted(frame["task_id"].unique().tolist()),
    }, indent=1, ensure_ascii=False))
    print(f"\nwrote {DEST}")
frame.to_json(SOURCE.with_name("scored_generations.jsonl"), orient="records", lines=True)
