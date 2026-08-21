"""Walk the whole post-freeze chain on synthetic generations, before it is run
on real ones.

Gate 0's pilot exists so that the apparatus fails now rather than after 144,384
generations. It covers the pilot's own path. **The confirmatory runner, the
masked analysis, the unmask and the final analysis had never executed once**,
and they are the code that runs after the point where a failure is most
expensive: a freeze has happened, the topics are spent, and §18.1 forbids
changing anything scientific to get past a crash.

So this tool runs them, at full registered size --- 384 blocks, M = 8, every
cell of the variant --- with the synthetic generator substituted at the one
seam the protocol registers for it, in a synthetic-namespace context that the
engine refuses to mix with real evidence. Every §8.6 variant is walked, because
the variant a model lands on is decided by its own coverage result and two of
the three have never been materialised end to end.

Nothing here is evidence. The bootstrap runs at a reduced resample count
because this is a test of the path and not of any interval.

    python3 tools/v4r3_pipeline_dryrun.py --resamples 200
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.generation.synthetic import synthetic_generate            # noqa: E402
from dci1v4r3 import CLASSIFICATION                                   # noqa: E402
from dci1v4r3.engine.context import synthetic_context                 # noqa: E402
from dci1v4r3.engine.paths import model_tree                          # noqa: E402
from dci1v4r3.protocol import constants as C                          # noqa: E402
from dci1v4r3.run import analysis_run as AR                           # noqa: E402
from dci1v4r3.run import confirmatory_run as CR                       # noqa: E402
from dci1v4r3.stages.confirmatory import DESIGN_VARIANTS              # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash                   # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r3" / "pipeline_dryrun.json"
MODEL = "gemma-3n-e2b-it"

DISCLAIMER = (
    "SYNTHETIC. Every generation in this walk comes from "
    "dci1v4.generation.synthetic and is a function of the scientific seed "
    "alone. No rate, interval or claim here is evidence about any model. The "
    "walk exists to make the post-freeze code fail on a laptop rather than "
    "after a study's worth of generations.")

#: A slot map that binds every slot of the full design to a registered
#: instance. Fabricated: no Gate 2 or Gate 3 outcome is read, and none exists.
SLOT_MAP: dict[str, list[Any]] = {
    "A": ["A", 3], "B": ["B", 8],
    "R1": ["RF1", 4], "R2": ["RF5", 3], "R3": ["RF8", 5],
    "R1-": ["RF1", 2], "R1+": ["RF1", 6],
    "R2-": ["RF5", 1], "R2+": ["RF5", 6],
    "R3-": ["RF8", 3], "R3+": ["RF8", 7],
    "CL": ["CL7", 30],
}
REDUCED_SLOTS = {"A": ["A", 3], "B": ["B", 8], "CL": ["CL7", 30]}


def _freeze(variant: str) -> dict[str, Any]:
    """The fields the post-freeze code reads, and only those.

    Deliberately not a real freeze record: `run_freeze` builds those and
    refuses while §18.1's list is incomplete. What this walk tests is the code
    downstream of a freeze, so it supplies exactly the keys that code reads.
    """
    slots = REDUCED_SLOTS if variant == "reduced" else dict(SLOT_MAP)
    if variant == "no_spectrum":
        slots = {k: v for k, v in slots.items() if k not in C.SPECTRUM_SLOTS}
    return {
        "outcome": "PASS", "design_variant": variant, "slot_map": slots,
        "blocks": [t["topic_id"] for t in CR._confirmatory_blocks()],
        "m_draws": C.M_DRAWS, "completion_cap": 512,
        "model_revision": "synthetic", "producing_commit": "synthetic",
        "verifier_source_hash": verifier_source_hash(),
    }


def walk(variant: str, *, resamples: int, root: Path) -> dict[str, Any]:
    context = synthetic_context(root / variant)
    from dci1v4.engine.signing import create_signing_key
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    tree = model_tree(context, MODEL)
    freeze = _freeze(variant)
    stages: dict[str, Any] = {}

    started = time.monotonic()
    generation = CR.run_confirmatory(MODEL, tree, freeze_record=freeze,
                                     generate=synthetic_generate)
    stages["CONFIRMATORY_GENERATION"] = {
        "rows": generation["rows"], "blocks": generation["blocks_generated"],
        "complete": generation["completeness"]["complete"],
        "seconds": round(time.monotonic() - started, 1)}

    rows = CR.collect_rows(tree)
    started = time.monotonic()
    masked = AR.run_masked_analysis(MODEL, tree, freeze_record=freeze,
                                    rows=rows, resamples=resamples)
    stages["MASKED_ANALYSIS"] = {
        "blocks": masked["blocks"],
        "maskable_groups": masked["mask_effectiveness"]["maskable_groups"],
        "structurally_unmaskable":
            masked["mask_effectiveness"]["structurally_unmaskable"],
        "families": {cfg: sorted(entry["families"])
                     for cfg, entry in masked["result"].items()},
        "spectrum_fit_ran": masked["spectrum_fit_ran"],
        "artifact_hash": masked["masked_artifact_hash"][:16],
        "seconds": round(time.monotonic() - started, 1)}

    unmasked_key = AR.run_unmasking(MODEL, tree, masked_record=masked)
    stages["UNMASKING"] = {"mask_key_hash": unmasked_key["mask_key_hash"][:16],
                           "bound_to": unmasked_key["masked_outputs_hash"][:16]}

    started = time.monotonic()
    final = AR.run_unmasked_analysis(MODEL, tree, freeze_record=freeze,
                                     rows=rows, masked_record=masked,
                                     resamples=resamples)
    members = {cfg: sorted({m for f in entry["families"].values()
                            for m in f["members"]})
               for cfg, entry in final["result"].items()}
    stages["UNMASKED_ANALYSIS"] = {
        "families": {cfg: sorted(entry["families"])
                     for cfg, entry in final["result"].items()},
        "members": members,
        "precision_checked": {cfg: len(entry["precision"])
                              for cfg, entry in final["result"].items()},
        "spectrum_present": {cfg: "spectrum" in entry
                             for cfg, entry in final["result"].items()},
        "seconds": round(time.monotonic() - started, 1)}
    return {"variant": variant, "outcome": "PASS", "stages": stages}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resamples", type=int, default=200)
    parser.add_argument("--variants", default="full,no_spectrum,reduced")
    parser.add_argument("--keep", action="store_true",
                        help="keep the synthetic tree for inspection")
    args = parser.parse_args()

    root = Path(tempfile.mkdtemp(prefix="v4r3-dryrun-"))
    results = []
    try:
        for variant in args.variants.split(","):
            variant = variant.strip()
            if variant not in DESIGN_VARIANTS:
                raise SystemExit(f"{variant!r} is not a registered variant")
            try:
                results.append(walk(variant, resamples=args.resamples,
                                    root=root))
            except Exception as error:               # the point of the walk
                results.append({"variant": variant, "outcome": "FAILED",
                                "error": f"{type(error).__name__}: {error}",
                                "traceback": traceback.format_exc()
                                             .splitlines()[-12:]})
    finally:
        if not args.keep:
            shutil.rmtree(root, ignore_errors=True)

    payload = {"artifact_type": "v4r3-pipeline-dry-run",
               "classification": CLASSIFICATION, "disclaimer": DISCLAIMER,
               "resamples": args.resamples,
               "blocks": C.N_BLOCKS, "m_draws": C.M_DRAWS,
               "verifier_hash": verifier_source_hash(),
               "results": results,
               "passed": all(r["outcome"] == "PASS" for r in results)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    for result in results:
        print(json.dumps(result, indent=1)[:1800])
    print(f"wrote {OUT.relative_to(DCI1)}  passed={payload['passed']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
