"""Close v4r3: record where it stopped, under which rule, and what survives.

**It writes one new file and edits nothing.** Every v4r3 artifact --- the
signed stage records, the failed Gate-1 decision, the reviewer evidence, the
generated rows --- stays exactly as it is. Closure is a statement *about* a
study, not a change *to* it, and a closure procedure that rewrote a record
would be the thing it exists to prevent.

What the record says is assembled from the artifacts themselves and hashed, so
a reader can check the summary against what it summarises rather than trusting
the transcription.

    ./.venv/bin/python tools/v4r3_closure.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.protocol.hashing import canonical_json, sha_file, sha_text  # noqa: E402
from dci1v4.models.registry import MODEL_KEYS                    # noqa: E402

from dci1v4r3.engine.context import registered_context           # noqa: E402
from dci1v4r3.engine.paths import model_tree                     # noqa: E402
from dci1v4r3.protocol import constants as C3                    # noqa: E402

EVIDENCE = DCI1 / "evidence" / "dci1v4r3"
REPORTS = DCI1 / "reports" / "dci1v4r3"
OUT = REPORTS / "closure.json"


def _stage_reached() -> dict[str, object]:
    context = registered_context()
    out: dict[str, object] = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        present = [stage for stage in C3.STAGE_SEQUENCE
                   if tree.stage_record(stage).exists()]
        out[model_key] = {
            "records": present,
            "furthest": present[-1] if present else None,
            "terminal_report": tree.terminal_report.exists(),
        }
    return out


def _absent() -> dict[str, bool]:
    """The things whose absence is the load-bearing fact about v4r3."""
    def _none(pattern: str) -> bool:
        return not list(EVIDENCE.rglob(pattern))
    return {
        "no_gate1_measurement_record": _none("gate1_measurement.json"),
        "no_gate2_regime_record": _none("gate2_regime.json"),
        "no_gate3_references_record": _none("gate3_references.json"),
        "no_gate4_composed_record": _none("gate4_composed.json"),
        "no_freeze_record": _none("gate5_freeze.json"),
        "no_confirmatory_manifest": _none("confirmatory_manifest.json"),
        "no_masked_result": _none("masked_result.json"),
        "no_unmask_record": _none("unmask_record.json"),
        "no_unmasked_result": _none("unmasked_result.json"),
    }


def main() -> int:
    decision = fs.read_json(REPORTS / "gate1_decision.json")
    r2 = fs.read_json(REPORTS / "section_10_4R2_outcome.json")
    absent = _absent()
    record = {
        "artifact_type": "v4r3-closure-record",
        "revision": "v4r3",
        "status": "CLOSED",
        "closed_on": "2026-08-21",
        "closed_at_stage": "GATE_1_MEASUREMENT",
        "terminal_status": decision["status_written_by_the_gate"],
        "criterion_in_force_at_the_time": decision["registered_rule"],
        "what_happened": {
            "section_10_2": "PASSED. Determinism 1.000 over three processes; "
                            "the frozen boundary suites 1.000 over all 584 "
                            "registered instruments; the independent "
                            "reimplementation 1.000 with its segmenter "
                            "differential; the §24 adversarial corpus, the "
                            "§7.5 witness and wording suites and the "
                            "carry-over record all held",
            "section_10_3": "NOT ESTABLISHED. Independent human validation "
                            "requires at least one annotator independent of "
                            "the design and analysis team. None was available "
                            "and none could be obtained. Author-performed "
                            "labels are not independent validation and were "
                            "never counted as such",
            "section_10_4": "NOT ESTABLISHED. The autorater pathway ran three "
                            "times --- §10.4, the repaired §10.4-R, and the "
                            "microcase validator §10.4-R2 --- and the last "
                            "returned FAIL on its own registered criterion 5, "
                            "whose stopping rule then ends the pathway",
            "gate_1": "REFUSED with MEASUREMENT_EVIDENCE_INSUFFICIENT. §18 "
                      "stage 4 required §10.2 plus §10.3 or §10.4, and "
                      "neither of the two pathways completed",
            "after_gate_1": "nothing. No Gate 2, no reference selection, no "
                            "composed-headroom check, no freeze, no "
                            "confirmatory generation, no masked or unmasked "
                            "analysis, and no DCI estimand of any kind",
        },
        "section_10_4R2": {"outcome": r2.get("outcome"),
                           "failed": r2.get("failed"),
                           "artifact": "reports/dci1v4r3/"
                                       "section_10_4R2_outcome.json"},
        "stage_records": _stage_reached(),
        "absent_by_inspection": absent,
        "every_downstream_artifact_absent": all(absent.values()),
        "preserved": {
            "evidence": "dci1/evidence/dci1v4r3 (gitignored; mirrored under "
                        "dci1/durable_root/dci1v4r3)",
            "reports": "dci1/reports/dci1v4r3",
            "decisions": "dci1/DECISIONS_V4R3.md",
            "preregistration": "user-notes/DCI1_preregistration_v4r3.md",
            "source": "dci1/src/dci1v4r3, dci1/tests_v4r3",
            "rule": "nothing under these paths is modified by the closure or "
                    "by the revision that follows it",
        },
        "what_this_record_does_not_say": [
            "that v4r3 passed Gate 1. It did not, and no later revision "
            "changes that",
            "that the criterion v4r3 registered was wrong to ask. §10.5's "
            "second question --- would an independent human reproduce these "
            "verdicts? --- is a real question and v4r4 does not answer it "
            "either",
            "that the reviewer evidence was worthless. It is what showed the "
            "architecture was mismatched to a mechanically decidable "
            "instrument, and it is preserved and cited for that",
        ],
        "superseded_by": {
            "revision": "v4r4",
            "prospective": "adopted before Gate 2 and before any confirmatory "
                           "scientific outcome was observed",
            "boundary": "user-notes/DCI1_v4r3_to_v4r4_changelog.md",
            "what_carries": "generations, through the explicit ledger at "
                            "reports/dci1v4r4/evidence_reuse_ledger.json. No "
                            "v4r3 stage record satisfies a v4r4 predecessor "
                            "check",
        },
        # Keyed by path from the repository root, so a later check can find
        # the file it is being asked to compare against.
        "source_hashes": {
            str((REPORTS / name).relative_to(REPO)): sha_file(REPORTS / name)
            for name in ("gate1_decision.json", "gate1_outcome.json",
                         "gate1_evidence.json",
                         "section_10_4R2_outcome.json",
                         "section_10_4R_outcome.json",
                         "validator_diagnosis.json")
        },
        "producing_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.strip(),
    }
    record["closure_hash"] = sha_text(canonical_json(record))
    fs.write_json(OUT, record)
    print(json.dumps({
        "status": record["status"],
        "closed_at_stage": record["closed_at_stage"],
        "terminal_status": record["terminal_status"],
        "every_downstream_artifact_absent":
            record["every_downstream_artifact_absent"],
        "stage_records": {k: v["furthest"] for k, v
                          in record["stage_records"].items()},
        "closure_hash": record["closure_hash"],
        "written": str(OUT),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
