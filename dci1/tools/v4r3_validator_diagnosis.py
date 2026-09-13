"""Why the §10.4-R2 validator failed, from its own rows.

**The question.** §10.4-R2 returned FAIL on one registered criterion:
per-kind sensitivity 0.231 on `denominator_swap` against a floor of 0.50. The
natural reading is that an external validator cannot check this verifier's
semantics. This asks whether that reading survives contact with the rows.

**The design that makes it answerable.** R2 runs **both arms over the same
cases**. The instruction-only arm shows the wording and the answer; the
conventions arm adds §7.3's registered lexical and rate rules, stated
identically for every case and therefore carrying no information about any
individual verdict. The arm difference is therefore a clean contrast: same
judge, same configuration, same items, one bit of difference --- whether the
registered convention was available. Anything the contrast moves is
convention-access. Anything it does not move is something else.

**What it finds.** Agreement on cases whose answer contains words is 0.929
without the conventions and 0.943 with them: no lift, and high either way. On
cases whose answer contains **no words at all** it is 0.231 without and 0.692
with. The judge is not failing to count and is not failing to reason. It is
failing to guess a stipulation --- what a percentage means when there is
nothing to take a percentage of.

**The specific contradiction.** §10.4-R2 registers exactly that hazard, in
these words: *"A five-word wording says nothing about ... what a percentage
means when there are no words. Judging `segmentation_drift` or
`vacuity_ignored` on the wording alone would score the validator for failing to
guess a convention."* It then assigns those two kinds to the conventions arm
--- and assigns `denominator_swap` to the instruction-only arm, although **8 of
its 14 deciding items have wordless answers**, whose verdict turns on the very
convention that arm withholds. The judge scores 0 of 7 parsed on those, and
0.714 on the same cases in the arm that states it.

So the arm assignment contradicts the amendment's own stated principle, and
that contradiction is what failed the gate.

**What this does not do.** It does not re-score R2, and no number here may be
substituted for one there. The registered arm assignment is the registered arm
assignment; R2 was judged under it and R2 **FAILED**, and §10.4-R2's stopping
rule takes effect on that failure. Re-running with a corrected assignment after
seeing the result is the iterative tuning the researcher's brief prohibits in
terms. What changes is the *interpretation* of the failure, which is a
different thing from the verdict and is recorded as such.

Read-only. It reads the stored R2 rows and the frozen case set, and writes one
report.

    python3 tools/v4r3_validator_diagnosis.py
"""
from __future__ import annotations

import collections
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol.hashing import canonical_json, sha_text     # noqa: E402
from dci1v4r3 import CLASSIFICATION                              # noqa: E402
from dci1v4r3.stages.microcase import (                          # noqa: E402
    ARM_CONVENTIONS, ARM_INSTRUCTION, ARM_OF_DEFECT, DEFECT_KINDS,
    build_cases,
)
from dci1v4r3.verifiers.statistics import word_count             # noqa: E402

RUN = (DCI1 / "reports" / "dci1v4r3"
       / "section_10_4R2_development_mc-medium_rep0.json")
OUT = DCI1 / "reports" / "dci1v4r3" / "validator_diagnosis.json"

VALID = "valid"


def _rate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [r for r in rows if r["status"] == VALID]
    agreed = sum(1 for r in parsed if r["agrees"])
    return {"n": len(rows), "parsed": len(parsed), "agreed": agreed,
            "agreement": agreed / len(parsed) if parsed else None}


def main() -> int:
    run = json.loads(RUN.read_text())
    rows = run["rows"]
    cases = {case.case_id: case for case in build_cases()}
    by_arm: dict[str, dict[str, dict[str, Any]]] = collections.defaultdict(dict)
    for row in rows:
        by_arm[row["arm"]][row["case_id"]] = row

    # The contrast: same cases, one bit of difference.
    contrast: dict[str, Any] = {}
    for label, keep in (("answer_has_no_words",
                         lambda c: word_count(c.text) == 0),
                        ("answer_has_words", lambda c: word_count(c.text) > 0)):
        ids = [cid for cid, case in cases.items()
               if keep(case) and cid in by_arm[ARM_INSTRUCTION]]
        without = _rate([by_arm[ARM_INSTRUCTION][cid] for cid in ids])
        with_it = _rate([by_arm[ARM_CONVENTIONS][cid] for cid in ids])
        contrast[label] = {
            "cases": len(ids),
            "instruction_only": without, "with_conventions": with_it,
            "lift": (None if without["agreement"] is None
                     or with_it["agreement"] is None
                     else with_it["agreement"] - without["agreement"])}

    per_kind: dict[str, Any] = {}
    for defect in DEFECT_KINDS:
        ids = [cid for cid, case in cases.items()
               if case.defect_verdicts.get(defect) is not None
               and case.defect_verdicts[defect] != case.correct
               and cid in by_arm[ARM_INSTRUCTION]]
        wordless = [cid for cid in ids if word_count(cases[cid].text) == 0]
        without = _rate([by_arm[ARM_INSTRUCTION][cid] for cid in ids])
        with_it = _rate([by_arm[ARM_CONVENTIONS][cid] for cid in ids])
        per_kind[defect] = {
            "registered_arm": ARM_OF_DEFECT[defect],
            "deciding_items": len(ids),
            "of_which_the_answer_has_no_words": len(wordless),
            "instruction_only": without,
            "with_conventions": with_it,
            "lift": (None if without["agreement"] is None
                     or with_it["agreement"] is None
                     else with_it["agreement"] - without["agreement"]),
            "wordless_subset_in_its_registered_arm":
                _rate([by_arm[ARM_OF_DEFECT[defect]][cid]
                       for cid in wordless]) if wordless else None,
        }

    failed = per_kind["denominator_swap"]
    payload = {
        "artifact_type": "v4r3-validator-diagnosis",
        "classification": CLASSIFICATION,
        "question": "does §10.4-R2's failure show that an external validator "
                    "cannot check this verifier's semantics, or something "
                    "narrower?",
        "method": "R2 runs both arms over the same cases and the conventions "
                  "arm states §7.3's rules identically for every case, so it "
                  "carries no per-case information. The arm difference is "
                  "therefore convention-access with the judge, the "
                  "configuration and the items all held fixed.",
        "source_run": str(RUN.relative_to(DCI1)),
        "case_set_hash": run["case_set_hash"],
        "config_hash": run["config"]["config_hash"],
        "canonical_verifier_hash": run["config"]["verifier_hash"],
        "contrast": contrast,
        "by_defect_kind": per_kind,
        "finding": {
            "counting_is_not_the_binding_constraint":
                "agreement on cases whose answer contains words is "
                f"{contrast['answer_has_words']['instruction_only']['agreement']:.3f} "
                "without the conventions, and the exact-count form --- the "
                "most arithmetic-heavy --- scored 1.000. R1's diagnosis that "
                "the task was arithmetic is not what this failure is.",
            "the_binding_constraint_is_a_stipulation":
                "agreement on wordless answers is "
                f"{contrast['answer_has_no_words']['instruction_only']['agreement']:.3f} "
                "without the conventions and "
                f"{contrast['answer_has_no_words']['with_conventions']['agreement']:.3f} "
                "with them. What a percentage means when there is nothing to "
                "take a percentage of is a registered stipulation, and a "
                "stipulation cannot be independently reproduced --- only "
                "communicated.",
            "the_arm_assignment_contradicts_the_amendment":
                "§10.4-R2 names 'what a percentage means when there are no "
                "words' as the hazard and assigns segmentation_drift and "
                "vacuity_ignored to the conventions arm for it. It assigns "
                f"denominator_swap to the instruction-only arm, although "
                f"{failed['of_which_the_answer_has_no_words']} of its "
                f"{failed['deciding_items']} deciding items have wordless "
                "answers. That is the kind that failed criterion 5.",
        },
        "what_this_does_not_do": "it does not re-score R2 and no number here "
                                 "may be substituted for one there. R2 was "
                                 "judged under its registered arm assignment "
                                 "and FAILED; §10.4-R2's stopping rule takes "
                                 "effect on that failure, and re-running with "
                                 "a corrected assignment after seeing the "
                                 "result is the iterative tuning the "
                                 "researcher's brief prohibits. Only the "
                                 "interpretation changes.",
        "bearing_on_gate_1": "none by itself. Gate 1's registered rule is "
                             "§10.2 plus §10.3 or §10.4, and neither pathway "
                             "has completed successfully. This artifact "
                             "changes what the §10.4 failure means, not "
                             "whether it occurred.",
        "producing_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=DCI1, capture_output=True,
            text=True, check=False).stdout.strip(),
        "generated_at": _dt.datetime.now(_dt.timezone.utc)
                           .isoformat(timespec="seconds"),
    }
    payload["report_hash"] = sha_text(canonical_json(
        {k: v for k, v in payload.items() if k != "generated_at"}))
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "contrast": {k: {"instruction_only": v["instruction_only"]["agreement"],
                         "with_conventions": v["with_conventions"]["agreement"],
                         "lift": v["lift"], "cases": v["cases"]}
                     for k, v in contrast.items()},
        "denominator_swap": {
            "registered_arm": failed["registered_arm"],
            "deciding_items": failed["deciding_items"],
            "wordless": failed["of_which_the_answer_has_no_words"],
            "in_its_registered_arm": failed["instruction_only"]["agreement"],
            "in_the_other_arm": failed["with_conventions"]["agreement"]},
        "report": str(OUT.relative_to(DCI1)),
    }, indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
