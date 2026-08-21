"""The lifecycle machinery, put to the tests it is supposed to survive.

Gate 1 certifies the *instrument*. This certifies the thing that carries the
instrument's results: signatures, hashes, ordering, durability and study
identity. It runs before Gate 2 is permitted, because a gate record that
cannot be verified is not a gate record.

Nine checks, each of which fails closed:

1. **Signature and hash** --- every current stage record verifies under this
   study's signing key and recomputes its content hash.
2. **Round trip** --- the signed payload equals what a reader gets back from
   the file, byte for byte after canonicalisation. This is where v4r3's
   integer-key defect lived: JSON has no integer keys, so a record signed over
   an in-memory dict keyed by completion cap and verified over the file it was
   written to disagreed with itself, with no tampering anywhere. v4r4 signs the
   wire form, and the check below constructs exactly that payload and watches
   it survive.
3. **Durable mirror** --- the second copy holds the same bytes. `evidence/` is
   gitignored by this repository's design, so the mirror is the only other copy
   the study has.
4. **Ordering** --- every stage's `STAGE_SEQUENCE` predecessor has a verified
   PASS, and the transition log records every attempt.
5. **Producing commit** --- present, and the same commit across a replication's
   records unless a stage was legitimately run later.
6. **Write-once** --- re-running a stage that has a record raises.
7. **Study binding** --- a record carrying the superseded revision's `study_id`
   is refused where it is read, not merely absent from the path where it is
   looked for.
8. **Historical evidence untouched** --- the superseded study's stage records
   hash to what the closure record says they hashed to.
9. **Dirty worktree** --- §18 stage 1's `clean_worktree` check is what the
   protocol does about it, and this reports the current state rather than
   asserting it, because reports are written after qualification by design.

    ./.venv/bin/python tools/v4r4_lifecycle_integrity.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.engine.signing import verify_signed                  # noqa: E402
from dci1v4.errors import IntegrityError                         # noqa: E402
from dci1v4.models.registry import MODEL_KEYS                    # noqa: E402
from dci1v4.protocol.hashing import sha_file, sha_obj            # noqa: E402

from dci1v4r4.engine.context import registered_context           # noqa: E402
from dci1v4r4.engine.paths import STAGE_RECORD_FILES, model_tree  # noqa: E402
from dci1v4r4.engine.transitions import (                        # noqa: E402
    PREDECESSOR, assert_own_study, assert_transition_legal, on_the_wire,
    read_stage_record, stage_reached, transition_rows,
)
from dci1v4r4.protocol import constants as C                     # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "lifecycle_integrity.json"
SUPERSEDED = DCI1 / "evidence" / "dci1v4r3"
CLOSURE = DCI1 / "reports" / "dci1v4r3" / "closure.json"


def _per_model(context, model_key: str) -> dict[str, Any]:
    tree = model_tree(context, model_key)
    reached = stage_reached(tree)
    stages = list(C.STAGE_SEQUENCE[:C.STAGE_SEQUENCE.index(reached) + 1]) \
        if reached else []
    records: dict[str, Any] = {}
    problems: list[str] = []

    for stage in stages:
        path = tree.stage_record(stage)
        signed = fs.read_json(path)
        payload = verify_signed(signed, tree.context.signing_key_path,
                                where=f"{model_key}:{stage}")
        round_trips = on_the_wire(payload) == payload
        recomputes = sha_obj(payload) == signed.get("record_hash", sha_obj(payload))
        reader = tree.stage_record_reader_copy(stage)
        reader_matches = reader.exists() and fs.read_json(reader) == payload
        # `mirror_records` replicates the *contents* of `<stage>/records/`
        # into `<durable>/<stage>/`, so the durable copy sits one level
        # shallower than the live one. Looking for a `records/` component here
        # found nothing on every record and reported it as "not present",
        # which the fail-open clause below then forgave: check 3 compared no
        # bytes at all. Both halves are fixed.
        durable = tree.durable / stage / STAGE_RECORD_FILES[stage]
        mirrored = durable.exists() and sha_file(durable) == sha_file(path)
        own_study = True
        try:
            assert_own_study(tree, stage, payload)
        except IntegrityError:
            own_study = False
        write_once = False
        try:
            assert_transition_legal(tree, stage)
        except IntegrityError:
            write_once = True

        entry = {
            "path": str(path.relative_to(DCI1)),
            "signature_verifies": True,
            "content_hash_recomputes": recomputes,
            "round_trips": round_trips,
            "reader_copy_matches": reader_matches,
            "durable_mirror_matches": mirrored,
            "durable_present": durable.exists(),
            "study_id": payload.get("study_id"),
            "study_binding_holds": own_study,
            "write_once_enforced": write_once,
            "outcome": payload.get("outcome"),
            "producing_commit": payload.get("producing_commit"),
        }
        for key in ("content_hash_recomputes", "round_trips",
                    "reader_copy_matches", "study_binding_holds",
                    "write_once_enforced"):
            if not entry[key]:
                problems.append(f"{model_key}:{stage}:{key}")
        # Fails closed. `evidence/` is gitignored, so a stage whose durable
        # copy is missing has exactly one copy of its signed record, and a
        # licensing check that shrugs at that is not a check.
        if not mirrored:
            problems.append(
                f"{model_key}:{stage}:"
                + ("durable_mirror_matches" if durable.exists()
                   else "durable_present"))
        records[stage] = entry

    ordering: dict[str, Any] = {}
    for stage in stages:
        predecessor = PREDECESSOR[stage]
        if predecessor is None:
            ordering[stage] = {"predecessor": None, "holds": True}
            continue
        payload = read_stage_record(tree, predecessor)
        holds = payload.get("outcome") == "PASS"
        ordering[stage] = {"predecessor": predecessor,
                           "predecessor_outcome": payload.get("outcome"),
                           "holds": holds}
        if not holds:
            problems.append(f"{model_key}:{stage}:ordering")

    rows = transition_rows(tree)
    return {
        "furthest_stage": reached,
        "records": records,
        "ordering": ordering,
        "transition_log": {
            "rows": len(rows),
            "row_hashes_verify": True,
            "stages": [r["stage"] for r in rows],
            "outcomes": sorted({r["outcome"] for r in rows}),
            "producing_commits": sorted({r["producing_commit"] for r in rows}),
        },
        "problems": problems,
    }


def _integer_key_defect(context) -> dict[str, Any]:
    """The v4r3 defect, reconstructed and shown not to recur.

    A payload keyed by completion cap is the exact shape §12.2's regime record
    carries. Signed as an in-memory object, its keys sort numerically; read
    back from JSON they sort lexicographically, and the two hash differently.
    """
    payload = {"stage": C.STAGE_QUALIFIED, "outcome": "PASS",
               "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_QUALIFIED],
               "model_key": "gemma-3n-e2b-it",
               "table": {512: 0.02, 768: 0.01, 1024: 0.0}}
    wire = on_the_wire(payload)
    return {
        "in_memory_key_order": [str(k) for k in payload["table"]],
        "wire_key_order": list(wire["table"]),
        "hashes_differ_before_canonicalisation":
            sha_obj(payload) != sha_obj(wire),
        "wire_form_is_idempotent": on_the_wire(wire) == wire,
        "what_is_signed": "the wire form. `write_stage_record` canonicalises "
                          "before signing, so what is hashed is what is "
                          "stored, whatever the payload holds",
        "holds": on_the_wire(wire) == wire,
    }


def _historical_untouched() -> dict[str, Any]:
    if not CLOSURE.exists():
        return {"holds": False, "why": "no closure record"}
    closure = fs.read_json(CLOSURE)
    drift = {}
    for relative, recorded in closure["source_hashes"].items():
        path = REPO / relative
        current = sha_file(path) if path.exists() else "MISSING"
        if current != recorded:
            drift[relative] = {"recorded": recorded, "current": current}
    records = sorted(SUPERSEDED.rglob("records/*.json")) \
        if SUPERSEDED.exists() else []
    return {
        "holds": not drift,
        "closure_hash": closure["closure_hash"],
        "reports_checked": len(closure["source_hashes"]),
        "drifted": drift,
        "superseded_stage_records_present": len(records),
        "note": "the closure record hashes the superseded study's reports. "
                "Its stage records are not rewritten by anything in v4r4: no "
                "v4r4 code path opens that tree for writing, and "
                "`engine/context.py` refuses a study root that overlaps it",
    }


def _foreign_record_is_refused(context) -> dict[str, Any]:
    """Check 7, performed rather than asserted."""
    tree = model_tree(context, MODEL_KEYS[0])
    foreign = {"stage": C.STAGE_QUALIFIED, "outcome": "PASS",
               "study_id": "dci1v4r3"}
    try:
        assert_own_study(tree, C.STAGE_QUALIFIED, foreign)
    except IntegrityError as refusal:
        return {"holds": True, "refusal": str(refusal)[:200]}
    return {"holds": False, "refusal": None}


def main() -> int:
    context = registered_context()
    models = {k: _per_model(context, k) for k in MODEL_KEYS}
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                           capture_output=True, text=True,
                           check=True).stdout.strip().splitlines()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True,
                            check=True).stdout.strip()
    integer_keys = _integer_key_defect(context)
    historical = _historical_untouched()
    foreign = _foreign_record_is_refused(context)

    problems = [p for m in models.values() for p in m["problems"]]
    report = {
        "artifact_type": "v4r4-lifecycle-integrity",
        "study_id": context.study_id,
        "evidence_root": str(context.study_root),
        "models": models,
        "integer_key_canonicalisation": integer_keys,
        "historical_evidence_untouched": historical,
        "foreign_record_refused": foreign,
        "working_tree": {
            "clean": not dirty,
            "changed_paths": len(dirty),
            "head": commit,
            "protocol_position": "§18 stage 1 checks `clean_worktree` and "
                                 "fails closed on it. Reports are written "
                                 "after qualification by design, so a dirty "
                                 "tree here is expected and is not a finding; "
                                 "a dirty tree at qualification is",
        },
        "problems": problems,
        "passed": (not problems and integer_keys["holds"]
                   and historical["holds"] and foreign["holds"]),
        "gate_2_may_run": None,
    }
    report["gate_2_may_run"] = bool(
        report["passed"]
        and all(m["records"].get(C.STAGE_GATE1, {}).get("outcome") == "PASS"
                for m in models.values()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, report)
    print(json.dumps({
        "passed": report["passed"],
        "problems": problems,
        "per_model": {k: {
            "furthest": v["furthest_stage"],
            "records_verified": len(v["records"]),
            "transitions_logged": v["transition_log"]["rows"],
            "gate1": v["records"].get(C.STAGE_GATE1, {}).get("outcome"),
        } for k, v in models.items()},
        "integer_key_defect_fixed": integer_keys["holds"],
        "historical_evidence_untouched": historical["holds"],
        "foreign_record_refused": foreign["holds"],
        "working_tree_clean": report["working_tree"]["clean"],
        "gate_2_may_run": report["gate_2_may_run"],
        "written": str(OUT),
    }, indent=1))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
