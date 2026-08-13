"""Is A ∧ B ∧ C actually satisfiable? Certified without using model success.

Stage 12 asks whether additional reasoning solves composition or merely improves
prioritisation. That question is only meaningful if joint satisfaction is
possible at all — otherwise "target only" is the best available outcome and
calling it prioritisation would be reading a constraint of the task as a
disposition of the model.

The certificate is a hand-authored witness per background, scored by the SAME
verifiers the experiments use. Model output is never the evidence.

    A = exactly 4 sentences
    B = each sentence strictly longer than the last, by word count
    C = the background instruction under test
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import extensions, harvest, mechanism

# 4 sentences, word counts 2 < 4 < 9 < 12, one instance of the demanded mark.
_BASE = ("Funnels help. They guide liquid downward. The narrow stem speeds the "
         "flow{middle} Anyone pouring oil into a bottle will finish the task "
         "much faster.")
WITNESSES = {
    "X_SEMICOLON_FREE": _BASE.format(middle="; spills become rare."),
    "X_PAREN_FREE": _BASE.format(middle=" (spills become rare)."),
    "X_ELLIPSIS_FREE": _BASE.format(middle=" ... spills become rare."),
    "X_ANCHOR_HOWEVER_FREE2": _BASE.format(middle="; however spills stay rare."),
    "X_ANCHOR_HOWEVER_BEFORE2": _BASE.format(middle="; however spills stay rare."),
}


def main() -> int:
    extensions.register()
    state = harvest.load()
    failures = []
    print("Joint-satisfiability certificate — hand-authored witnesses\n")
    for background, text in WITNESSES.items():
        target = state.verify(text, "A")
        focal = state.verify(text, "B")
        control = state.verify(text, background)
        joint = int(target.binary_pass and focal.binary_pass and control.binary_pass)
        features = mechanism.row_features(text)
        print(f"{background:26s} A={target.binary_pass} B={focal.binary_pass} "
              f"C={control.binary_pass} -> JOINT={joint}  "
              f"(sentences={features['n_sentences']})")
        if not joint:
            failures.append(background)
    if failures:
        print(f"\nNOT CERTIFIED for: {failures}. Arbitration figures for these "
              "backgrounds cannot be read as prioritisation.")
        return 1
    print("\nAll backgrounds certified: joint satisfaction is achievable, so a low "
          "P(both) is a model failure rather than a property of the task.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
