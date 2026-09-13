#!/usr/bin/env python3
"""Record every measured rung whose difficulty coordinate is undefined.

    python3 tools/v6_degenerate_iota_rungs.py            # write the report
    python3 tools/v6_degenerate_iota_rungs.py --check    # fail if stale

§12.6/A16 drops a rung with no ``iota`` from every coverage condition. The
drop is on the stage record, but the *measurement* that caused it --- the
chance compliance that reached ``CHANCE_DEGENERACY_MAX``, and the solo
compliance that kept the rung eligible under U4's E2 --- lives in the
generated rows. This puts it in one durable, machine-readable place, because
"which rungs were degenerate and by how much" is evidence about the study and
not a note about a run.

It reads **signed records and generated rows only**. It re-runs no model and
regenerates nothing; a replication with no ``REGIME_SCREEN`` rows contributes
an empty entry rather than being skipped, so a reader can tell "measured, none
degenerate" from "not measured".
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.models.registry import MODELS                       # noqa: E402
from dci1v4.protocol.hashing import sha_obj                     # noqa: E402
from dci1v6.engine.context import registered_context            # noqa: E402
from dci1v6.engine.paths import model_tree                      # noqa: E402
from dci1v6.protocol import constants as C                      # noqa: E402
from dci1v6.run.regime_run import difficulty_table              # noqa: E402
from dci1v6.stages import regime as R                           # noqa: E402
from dci1v6.verifiers.constraints import FAMILIES, Constraint    # noqa: E402

OUT = HERE.parent / "reports" / "dci1v6" / "degenerate_iota_rungs.json"


def _scored(run_dir: pathlib.Path) -> list[dict]:
    path = run_dir / "scored.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def _rungs_of(rows: list[dict]) -> list[Constraint]:
    """Every (family, severity) the scored rows actually carry."""
    seen: set[tuple[str, int]] = set()
    for row in rows:
        for score in row.get("scores", ()):
            kind = score.get("kind")
            if kind in FAMILIES and score.get("severity") is not None:
                seen.add((kind, int(score["severity"])))
    out: list[Constraint] = []
    for kind, severity in sorted(seen):
        try:
            out.append(Constraint(kind, severity))
        except Exception:
            # A §12.6 expansion rung is declared rather than measured at round
            # zero, so it is outside the registered ladder by construction and
            # the instrument layer says so with `reserve=True`.
            out.append(Constraint(kind, severity, reserve=True))
    return out


def build() -> dict:
    context = registered_context()
    per_model: dict[str, dict] = {}
    for spec in MODELS:
        tree = model_tree(context, spec.model_key)
        runs = tree.backend_runs(C.STAGE_REGIME)
        entries: list[dict] = []
        measured = 0
        if runs.is_dir():
            for run_dir in sorted(p for p in runs.iterdir() if p.is_dir()):
                rows = _scored(run_dir)
                if not rows:
                    continue
                rungs = _rungs_of(rows)
                for entry in difficulty_table(rows, rungs):
                    measured += 1
                    if entry.get("iota") is not None:
                        continue
                    entries.append({
                        "candidate": entry["candidate"],
                        "family": entry["kind"],
                        "severity": entry["severity"],
                        "structural_tier": entry.get("tier"),
                        "feature_group": FAMILIES[entry["kind"]].feature_group,
                        "constraint_class":
                            FAMILIES[entry["kind"]].constraint_class,
                        "solo_compliance": entry.get("solo"),
                        "chance_compliance": entry.get("chance"),
                        "solo_vacuity": entry.get("vacuity"),
                        "run_dir": run_dir.name,
                        "iota": None,
                        "status": "DIFFICULTY_COORDINATE_DEGENERATE",
                        "eligible_under_e2":
                            entry.get("solo") is not None
                            and C.HEADROOM_BAND[0] <= entry["solo"]
                            <= C.HEADROOM_BAND[1],
                    })
        per_model[spec.model_key] = {
            "rungs_measured": measured,
            "n_degenerate": len(entries),
            "degenerate": sorted(entries,
                                 key=lambda e: (e["run_dir"], e["candidate"])),
        }
    payload = {
        "_what": "every REGIME_SCREEN rung whose difficulty coordinate is "
                 "undefined, with the measurement that made it so",
        "_classification": "REGISTERED_OUTCOME",
        "_reads": "generated rows on the evidence tree. No model is run and "
                  "nothing is regenerated",
        "_rule": "iota is undefined at chance compliance >= "
                 f"{C.CHANCE_DEGENERACY_MAX} (§11.2, "
                 "DIFFICULTY_COORDINATE_DEGENERATE). §12.6/A16 drops such a "
                 "rung from every coverage condition and records it; U4's E2 "
                 "predicate is unchanged and may still call it eligible",
        "study_id": context.study_id,
        "chance_degeneracy_max": C.CHANCE_DEGENERACY_MAX,
        "headroom_band": list(C.HEADROOM_BAND),
        "per_model": per_model,
        "n_degenerate_total": sum(m["n_degenerate"]
                                  for m in per_model.values()),
    }
    payload["payload_sha256"] = sha_obj(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build()
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is STALE")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    print(f"  degenerate rungs: {payload['n_degenerate_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
