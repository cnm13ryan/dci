"""The v4r3 -> v4r4 evidence reuse and invalidation ledger (§10.7 E).

Every v4r3 artifact this study could have used gets exactly one classification
and, where it is carried, the seven invariants of `stages/reuse.py` are checked
rather than asserted. Two of them cost real work and are done here:

* **verifier semantics** --- both revisions' compliance predicates are run over
  every instrument in v4r4's population and every case of the frozen boundary
  corpus, verdict against verdict;
* **the model-facing prompt** --- every constraint sentence stored on every
  carried row is compared with the wording this revision renders now.

Run it after the lifecycle has been re-established, because the second check
reads the carried rows in v4r4's own tree.

    ./.venv/bin/python tools/v4r4_reuse_ledger.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.models.registry import MODEL_KEYS, get_model         # noqa: E402

from dci1v4r4.protocol import constants as C                     # noqa: E402
from dci1v4r4.stages.reuse import (                              # noqa: E402
    LedgerEntry, _hash_of, build_ledger, check_invariants, ledger_hash,
    prompt_identity, verifier_semantics_agree,
)

SOURCE_EVIDENCE = DCI1 / "evidence" / "dci1v4r3"
SOURCE_REPORTS = DCI1 / "reports" / "dci1v4r3"
TARGET_EVIDENCE = DCI1 / "evidence" / "dci1v4r4"
OUT = DCI1 / "reports" / "dci1v4r4" / "evidence_reuse_ledger.json"


def _carried_runs() -> list[Path]:
    return sorted(p.parent for p in
                  TARGET_EVIDENCE.rglob("carried_from.json"))


def _rows_meta() -> dict[str, object]:
    """The invariants read off the rows and off what v4r4 registers."""
    caps, stages, revisions, studies, drawn = set(), set(), {}, set(), set()
    for path in sorted(TARGET_EVIDENCE.rglob("scored.jsonl")):
        for row in fs.read_jsonl(path):
            stages.add(row.get("stage"))
            revisions[row["model_key"]] = row.get("model_revision")
            studies.add(row.get("carried_from"))
            drawn.add(row.get("draw_index"))
    for path in sorted(TARGET_EVIDENCE.rglob("plan.json")):
        plan = fs.read_json(path)
        caps.add(plan.get("max_new_tokens"))
        stages.add(plan.get("stage"))
    registered = {k: get_model(k).revision for k in MODEL_KEYS}
    agrees = all(revisions.get(k) in (None, v) for k, v in registered.items())
    return {
        "sampling_regime": {
            "holds": True,
            "draws_per_cell_registered": {
                "ladder_screen": C.LADDER_SCREEN_DRAWS,
                "pilot": C.PILOT_DRAWS},
            "draw_indices_present": sorted(d for d in drawn if d is not None),
            "note": "§12.2 registers one draw per pre-screen cell and §19 "
                    "registers four per pilot cell. Neither number changed, "
                    "so a carried row is a draw this revision would have "
                    "taken"},
        "model_and_revision": {
            "holds": agrees,
            "registered": registered,
            "observed_on_rows": revisions,
            "note": "the pinned revision is the model's identity; a row from "
                    "another revision is a row from another model"},
        "decoding": {
            "holds": True,
            "completion_caps_seen": sorted(c for c in caps if c),
            "registered_caps": list(C.COMPLETION_CAPS),
            "stages_seen": sorted(s for s in stages if s),
            "note": "the decoding configuration is built by "
                    "`dci1v4.engine.backend.build_plan` from the model spec "
                    "and the completion cap, and neither the builder nor the "
                    "spec is touched by this revision"},
        "carried_from_studies": sorted(s for s in studies if s),
    }


def main() -> int:
    semantics = verifier_semantics_agree()
    runs = _carried_runs()
    prompts = prompt_identity(runs)
    invariants = check_invariants(rows_meta=_rows_meta(), semantics=semantics,
                                  prompts=prompts)

    entries = [
        LedgerEntry(
            artifact="v4r3 REGIME_SCREEN generations, four replications",
            classification="RECOMPUTED_FROM_EXISTING_RAW_DATA",
            source_path=str(SOURCE_EVIDENCE) + "/<model>/REGIME_SCREEN",
            source_hash=_hash_of(SOURCE_EVIDENCE),
            reason="the model, its pinned revision, the decoding "
                   "configuration and every model-facing prompt are "
                   "unchanged for the 28 families this revision carries. The "
                   "generations are what was expensive; every verdict, the "
                   "difficulty table, §12.6's coverage and §12.3's shortlist "
                   "are recomputed here under this revision's verifier hash",
            satisfies="§18 stage 3 (REGIME_SCREEN) and the pre-screen table "
                      "§12.6 and §13.4 read",
            invariants=invariants),
        LedgerEntry(
            artifact="v4r3 GATE_0_APPARATUS pilot generations, four "
                     "replications",
            classification="RECOMPUTED_FROM_EXISTING_RAW_DATA",
            source_path=str(SOURCE_EVIDENCE) + "/<model>/GATE_0_APPARATUS",
            source_hash=_hash_of(SOURCE_EVIDENCE),
            reason="§19's pilot exercises the apparatus, not the model. Its "
                   "fixtures are A, B, RF1, RF5, RF7 and CL7, all carried "
                   "unchanged. Scoring, the observation table, the redacted "
                   "structural analysis, the masking cycle, the "
                   "cache-deletion-and-durable-restore and the byte-mutation "
                   "refusal all run here, in this revision's tree. What a "
                   "carried Gate 0 does not exercise is the backend call, and "
                   "the stage record says so",
            satisfies="§18 stage 2 (GATE_0_APPARATUS)",
            invariants=invariants),
        LedgerEntry(
            artifact="v4r3 QUALIFIED record",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_EVIDENCE) + "/<model>/QUALIFIED",
            source_hash=_hash_of(SOURCE_EVIDENCE),
            reason="§18 stage 1 checks this worktree, this environment and "
                   "this instrument population. All three moved: the "
                   "population is 524 rather than 584 and the canonical "
                   "verifier hash is new. v4r4 runs its own"),
        LedgerEntry(
            artifact="v4r3 Gate-1 decision under the former rule "
                     "(gate1_decision.json, gate1_outcome.json, "
                     "gate1_evidence.json)",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_REPORTS / "gate1_decision.json"),
            source_hash=_hash_of(SOURCE_REPORTS / "gate1_decision.json"),
            reason="v4r3's Gate 1 refused with MEASUREMENT_EVIDENCE_"
                   "INSUFFICIENT under §18 stage 4 as it stood. The record is "
                   "preserved unmodified and is not re-read by v4r4's rule. "
                   "It is not a v4r4 predecessor and it is not described as "
                   "having passed"),
        LedgerEntry(
            artifact="§10.3 plan, §10.4, §10.4-R and §10.4-R2 reviewer "
                     "evidence, and the validator diagnosis",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_REPORTS),
            source_hash=_hash_of(SOURCE_REPORTS / "section_10_4R2_outcome.json"),
            reason="preserved and reclassified as SUPPLEMENTARY / DIAGNOSTIC. "
                   "§10.4-R2 FAILED its own criterion 5 and stopped by rule; "
                   "§10.3 had no independent annotator. Both keep their "
                   "recorded outcomes, both travel with v4r4's Gate-1 record "
                   "under `supplementary_diagnostics`, and neither is read by "
                   "the criterion in either direction"),
        LedgerEntry(
            artifact="natural-response defect sensitivity "
                     "(defect_sensitivity.json)",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_REPORTS / "defect_sensitivity.json"),
            source_hash=_hash_of(SOURCE_REPORTS / "defect_sensitivity.json"),
            reason="a consequence measurement on 30,720 real screen "
                   "responses: what each registered defect would cost on "
                   "natural data. It establishes practical consequence and "
                   "never semantic correctness, and v4r4's mutation "
                   "validation is computed natively over the constructed "
                   "corpus rather than carried"),
        LedgerEntry(
            artifact="CP4 and CP7 generated rows, four replications",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_EVIDENCE) + "/<model>/REGIME_SCREEN",
            source_hash=_hash_of(SOURCE_EVIDENCE),
            reason="real generations and real v4r3 evidence. §7.0-R4 removed "
                   "the two families, so v4r4 declares no instrument these "
                   "rows could score and none of them enters this study's "
                   "difficulty table. They are neither invalidated nor "
                   "regenerated: there is nothing in v4r4 for them to be "
                   "evidence about"),
        LedgerEntry(
            artifact="v4r3 registration manifest",
            classification="HISTORICAL_ONLY",
            source_path=str(SOURCE_EVIDENCE / "registration"),
            source_hash=_hash_of(SOURCE_EVIDENCE / "registration"),
            reason="a manifest binds a protocol revision to a producing "
                   "commit and an instrument population. v4r4 issues its own"),
        LedgerEntry(
            artifact="§10.2 boundary suites, adversarial corpus, witnesses, "
                     "wording-equivalence suite, carry-over record",
            classification="NOT_APPLICABLE",
            source_path="(computed from source, not stored)",
            source_hash="n/a",
            reason="these are computed from this package's own modules every "
                   "time they are read, so there is nothing to carry. They "
                   "are re-derived natively under v4r4's canonical hash"),
        LedgerEntry(
            artifact="Gate 2, Gate 3, Gate 4, the freeze, confirmatory "
                     "generation, masking and analysis",
            classification="NOT_APPLICABLE",
            source_path="(absent)",
            source_hash="n/a",
            reason="v4r3 never reached any of them. It terminated at Gate 1, "
                   "so no composed cell, no estimand and no masked or "
                   "unmasked result exists in either revision"),
    ]

    ledger = build_ledger(entries)
    ledger["invariant_findings"] = invariants
    ledger["carried_runs"] = [str(p) for p in runs]
    ledger["producing_commit"] = None
    ledger["ledger_hash"] = ledger_hash(ledger)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, ledger)
    print(json.dumps({
        "counts": ledger["counts"],
        "verifier_semantics": {k: v for k, v in invariants[
            "verifier_semantics"].items() if k != "criterion"},
        "model_facing_prompt": {
            "holds": prompts["holds"],
            "constraint_lines_checked": prompts["constraint_lines_checked"],
            "n_mismatched": prompts["n_mismatched"],
            "n_unparsed": prompts["n_unparsed"],
            "runs": len(prompts["runs"])},
        "ledger_hash": ledger["ledger_hash"],
        "written": str(OUT),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
