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
from typing import Any

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
    unexpected = sorted(set(moved) - set(EXPECTED_TO_MOVE))
    return {
        "sealed_producing_commit": sealed["producing_commit"],
        "current_commit": _commit(),
        "fields_compared": len(F.FREEZE_FIELDS),
        "fields_that_moved": moved,
        "expected_to_move": list(EXPECTED_TO_MOVE),
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
