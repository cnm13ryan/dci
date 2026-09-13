"""What moved between the freeze's producing commit and the code that runs.

§18.1 binds the scientific state and forbids changing it afterwards, and the
machinery enforces that literally: `supersede_stage_records` calls
`assert_no_post_freeze_mutation` on every stage it is asked to retire, so a
passed `GATE_5_FREEZE` cannot be superseded and re-run. That is deliberate ---
"superseding is exactly the mutation §18.1 forbids" --- and it means a defect
found *below* the freeze cannot be answered by re-freezing under corrected
code. It has to be answered by showing that nothing the freeze bound moved.

That is what this does. It re-assembles each frozen replication's §18.1 record
from the same signed inputs under the code as it stands now, and compares it
field by field against the sealed record. `producing_commit` is expected to
differ and is reported rather than excluded; every other field must be
byte-identical after canonicalisation, and the tool fails if one is not.

The change this was written for: §21's `assert_generation_licensed` demanded a
freeze field named `verifier_source_hash`, which §18.1 does not register --- it
binds `canonical_verifier_hash` --- so the licence check refused every valid
freeze record and no confirmatory generation was possible. Correcting the name
changes what the licence check reads. It changes no frozen value, and that
claim is checkable rather than asserted.

    ./.venv/bin/python tools/v4r4_post_freeze_delta.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                    # noqa: E402
from dci1v4.models.registry import MODEL_KEYS                   # noqa: E402
from dci1v4.protocol.hashing import canonical_json, sha_text    # noqa: E402

from dci1v4r4.engine.context import registered_context          # noqa: E402
from dci1v4r4.engine.paths import model_tree                    # noqa: E402
from dci1v4r4.engine.transitions import (                       # noqa: E402
    read_stage_record, terminal_status,
)
from dci1v4r4.protocol import constants as C                    # noqa: E402
from dci1v4r4.run.freeze_run import run_freeze                  # noqa: E402
from dci1v4r4.stages import freeze as F                         # noqa: E402
from dci1v4r4.stages import registration                        # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "post_freeze_delta.json"
PROVENANCE = DCI1 / "reports" / "dci1v4r4" / "backend_provenance.json"
DURABILITY = DCI1 / "reports" / "dci1v4r4" / "durability.json"

#: Fields whose value is *about* the run rather than about the science, and
#: which a later commit legitimately moves. Reported, never silently dropped.
EXPECTED_TO_MOVE = ("producing_commit",)

#: Three §18.1 fields *enumerate the evidence tree*, so they necessarily move
#: as the study produces evidence: `hardware_record` lists the backend
#: provenance sidecars it read, `environment_digest` hashes a record that
#: contains it, and `durability_record` counts the files in both roots. A
#: field that can only move is not evidence that the frozen science changed,
#: and treating it as one trains a reader to ignore the alarm.
#:
#: They are **not** allowlisted. Each is re-compared on the part that would
#: mean something --- the hardware the evidence came off, the environment
#: minus that accreting sub-record, and whether durability still passed
#: without a missing or diverged critical file. Only a move that survives
#: that comparison stays unexpected, and the comparison is reported either
#: way so the reader sees what was checked rather than what was excused.
ACCRETIVE = ("hardware_record", "environment_digest", "durability_record")

#: The keys of `hardware_record` that enumerate rather than describe.
_HARDWARE_ENUMERATIONS = ("backend_runs", "hip_visible_devices_used")


def _substantive_hardware(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    return {k: v for k, v in record.items()
            if k not in _HARDWARE_ENUMERATIONS}


def _substantive_durability(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    comparison = record.get("comparison") or {}
    rehearsal = record.get("restore_rehearsal") or {}
    return {
        "passed": record.get("passed"),
        "manifest_tracked_in_git": record.get("manifest_tracked_in_git"),
        "roots_on_one_device": record.get("roots_on_one_device"),
        "off_machine_copy": record.get("off_machine_copy"),
        "restore_failures": rehearsal.get("failures"),
        "n_critical_missing": comparison.get("n_critical_missing"),
        "n_critical_diverged": comparison.get("n_critical_diverged"),
        "critical_matched": comparison.get("matched"),
    }


def _accretion(field: str, sealed: Mapping[str, Any],
               fresh: Mapping[str, Any]) -> dict[str, Any]:
    """Did this field move only where it enumerates? Content, not digest."""
    if field == "hardware_record":
        before = _substantive_hardware(sealed.get(field))
        after = _substantive_hardware(fresh.get(field))
        what = ("the hardware the evidence came off, with the backend-sidecar "
                "list and the visible-device list set aside as enumerations")
    elif field == "durability_record":
        before = _substantive_durability(sealed.get(field))
        after = _substantive_durability(fresh.get(field))
        what = ("whether §26's gate still passes with no critical artifact "
                "missing from or diverged in the mirror")
    elif field == "environment_digest":
        # The digest hashes a record containing `hardware`, which accretes.
        # Recompute it over the same record *without* that sub-record: the
        # sealed-era provenance file is in git at the sealing commit.
        before, after = _environment_minus_hardware()
        what = ("the environment digest recomputed over the provenance "
                "record with the accreting `hardware` sub-record removed")
    else:
        return {"checked": False}
    same = canonical_json(before) == canonical_json(after)
    return {"checked": True, "what_was_compared": what,
            "substantively_unchanged": same,
            "sealed": before, "recomputed": after}


def _environment_minus_hardware() -> tuple[Any, Any]:
    """The provenance record at the sealing commit, and now, minus hardware."""
    current = json.loads(PROVENANCE.read_text())
    sealing = subprocess.run(
        ["git", "show", f"{_sealing_commit()}:"
         f"dci1/reports/dci1v4r4/backend_provenance.json"],
        cwd=REPO, capture_output=True, text=True)
    if sealing.returncode != 0:
        return ("SEALING_COMMIT_PROVENANCE_UNAVAILABLE", None)
    def _strip(record: dict[str, Any]) -> str:
        return sha_text(json.dumps(
            {k: v for k, v in record.items()
             if k not in ("environment_digest", "hardware")},
            sort_keys=True))
    return _strip(json.loads(sealing.stdout)), _strip(current)


def _sealing_commit() -> str:
    context = registered_context()
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        if tree.stage_record(C.STAGE_GATE5).exists():
            return read_stage_record(tree, C.STAGE_GATE5)["producing_commit"]
    return "HEAD"


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()


def compare(model_key: str) -> dict[str, Any]:
    context = registered_context()
    tree = model_tree(context, model_key)
    sealed = read_stage_record(tree, C.STAGE_GATE5)
    records = {stage: read_stage_record(tree, stage) for stage in
               (C.STAGE_REGIME, C.STAGE_GATE2, C.STAGE_GATE3, C.STAGE_GATE4)}
    fresh = run_freeze(
        model_key, manifest=registration.load_manifest(context),
        records=records, gate1=read_stage_record(tree, C.STAGE_GATE1),
        durability=json.loads(DURABILITY.read_text()),
        provenance=json.loads(PROVENANCE.read_text()),
        producing_commit=_commit())
    moved: dict[str, Any] = {}
    for field in F.FREEZE_FIELDS:
        before = canonical_json(sealed.get(field))
        after = canonical_json(fresh.get(field))
        if before != after:
            moved[field] = {"sealed": sha_text(before)[:16],
                            "recomputed": sha_text(after)[:16]}
    accretion = {field: _accretion(field, sealed, fresh)
                 for field in moved if field in ACCRETIVE}
    excused = {f for f, a in accretion.items()
               if a.get("substantively_unchanged")}
    unexpected = sorted(set(moved) - set(EXPECTED_TO_MOVE) - excused)
    return {
        "sealed_producing_commit": sealed["producing_commit"],
        "current_commit": _commit(),
        "fields_compared": len(F.FREEZE_FIELDS),
        "fields_that_moved": moved,
        "expected_to_move": list(EXPECTED_TO_MOVE),
        "accretive_fields_re_compared": accretion,
        "moved_only_where_they_enumerate": sorted(excused),
        "unexpectedly_moved": unexpected,
        "scientific_state_unchanged": not unexpected,
        "sealed_record_still_verifies": True,   # read_stage_record verified it
    }


def main() -> int:
    context = registered_context()
    frozen = [m for m in MODEL_KEYS
              if terminal_status(model_tree(context, m)) is None
              and model_tree(context, m).stage_record(C.STAGE_GATE5).exists()]
    per_model = {m: compare(m) for m in frozen}
    record = {
        "artifact_type": "v4r4-post-freeze-delta",
        "why": "§18.1 forbids changing the scientific state after the freeze "
               "and the machinery refuses to supersede a passed GATE_5_FREEZE,"
               " so a defect found below the freeze is answered by showing "
               "that nothing the freeze bound moved -- not by re-freezing",
        "change": "§21's assert_generation_licensed asked for a freeze field "
                  "named verifier_source_hash; §18.1 binds "
                  "canonical_verifier_hash. The licence check refused every "
                  "valid freeze record. Also: §21's assert_no_selective_rerun "
                  "was documented and not called, and is now called",
        "frozen_replications": frozen,
        "per_model": per_model,
        "passed": all(e["scientific_state_unchanged"]
                      for e in per_model.values()),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, record)
    print(json.dumps({k: v for k, v in record.items() if k != "per_model"},
                     indent=1))
    for model_key, entry in per_model.items():
        print(json.dumps({model_key: {
            "sealed_producing_commit": entry["sealed_producing_commit"][:12],
            "current_commit": entry["current_commit"][:12],
            "fields_compared": entry["fields_compared"],
            "fields_that_moved": sorted(entry["fields_that_moved"]),
            "unexpectedly_moved": entry["unexpectedly_moved"],
            "scientific_state_unchanged": entry["scientific_state_unchanged"],
        }}, indent=1))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
