#!/usr/bin/env python3
"""Post-confirmatory audit: did delta_difficulty's refits cross §13.13's
degenerate-replicate ceiling in the executed v8.1 analysis?

The frozen analysis (dci1v8dev/confirm/analysis.py) enforces
``DEGENERATE_REPLICATE_MAX`` only on the F_SPECTRUM slope family
(``apply_degenerate_ceiling``). ``delta_difficulty`` is also a refit member,
bootstrapped in the per-frame F1 family and in JOINT_F1, and nothing counts
its non-registered refits there; ``bootstrap_family`` drops non-finite
replicates from the standard error and the maximum deviation. The frozen code
is not amended (its module hashes are bound at registration and the analysis
ran once). This tool measures, on the stored confirmatory rows, whether that
gap changed anything.

For every model, spectrum frame and configuration it replays the exact index
draws of F1 (seed ``F1:<cfg>:f<w>``) and of JOINT_F1 (seed ``JOINT_F1:<cfg>``,
topic positions as the analysis forms them). Every replicate is refitted with
the frozen ``spectrum.estimate``, and a replicate is counted exactly as
``RefitCounter`` counts one: the fit was not available, or a point was dropped.
Two fidelity checks tie the replay to the signed record: the refitted point
estimate must equal the recorded delta_difficulty, and the replayed bootstrap
standard error must equal the recorded one. The standard error depends only on
the member's own replicates and the shared index draws, not on the other
family members.

Reads the evidence root read-only (the signed FROZEN, CONFIRMATORY_GENERATION
and CONFIRMATORY_ANALYSIS records, verified, and the generation rows). Writes
one JSON report.

    dci1/.venv/bin/python dci1/tools/v8p1_delta_difficulty_degeneracy_replay.py \\
        --root dci1/evidence/dci1v8p1-confirm \\
        --out dci1/reports/dci1v8dev/postconfirm/audits/delta_difficulty_degeneracy_replay.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError                            # noqa: E402
from dci1v4.models.registry import get_model                        # noqa: E402
from dci1v7.analysis import spectrum as SP                          # noqa: E402
from dci1v7.analysis.bootstrap import bootstrap_family              # noqa: E402
from dci1v7.protocol import constants as C                          # noqa: E402
from dci1v8dev.confirm.analysis import (frame_members, frame_table,  # noqa: E402
                                        joint_members)
from dci1v8dev.run.context import current_files                     # noqa: E402
from dci1v8dev.run.seeds import bootstrap_seed                      # noqa: E402

MODELS = ("qwen3-4b", "qwen3-4b-instruct-2507", "gemma-3n-e2b-it", "gemma-3n-e4b-it")
STUDY_ID = "dci1v8"
TOL = 1e-12


def signed(root: Path, model: str, stage: str, name: str) -> tuple[dict[str, Any], str]:
    rec = json.loads((root / "evidence" / STUDY_ID / model / stage / "records" / name).read_text())
    payload = verify_signed(rec, root / "evidence" / STUDY_ID / "keys" / "signing.key",
                            where=f"{model}:{stage}")
    if payload.get("study_id") != STUDY_ID or payload.get("layer") != "confirm":
        raise IntegrityError(f"{model}:{stage} is not a {STUDY_ID} confirmatory record")
    return payload, rec["record_hash"]


class CountingRefit:
    """delta_difficulty as a function of picks, counting non-registered refits
    the way analysis.RefitCounter does (the first call is the point estimate)."""

    def __init__(self, data: SP.SpectrumInput) -> None:
        self.data = data
        self.calls = self.unavailable = self.dropped = 0

    def __call__(self, picks) -> float:
        est = SP.estimate(self.data, picks)
        self.calls += 1
        if self.calls > 1:
            if est.get("degenerate"):
                self.unavailable += 1
            elif est.get("dropped_points"):
                self.dropped += 1
        return float(est["delta_difficulty"])

    def record(self, resamples: int) -> dict[str, Any]:
        share = (self.unavailable + self.dropped) / resamples
        return {"replicates": self.calls - 1, "fit_unavailable": self.unavailable,
                "dropped_a_point": self.dropped, "degenerate_replicate_share": share,
                "ceiling": C.DEGENERATE_REPLICATE_MAX,
                "status": "DEGENERATE_REPLICATES" if share > C.DEGENERATE_REPLICATE_MAX else "OK"}


def same(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=0.0, abs_tol=TOL)


def replay_model(root: Path, model: str) -> dict[str, Any]:
    t0 = time.time()
    freeze, freeze_hash = signed(root, model, "FROZEN", "freeze.json")
    gen, gen_hash = signed(root, model, "CONFIRMATORY_GENERATION", "confirmatory_generation.json")
    ana, ana_hash = signed(root, model, "CONFIRMATORY_ANALYSIS", "confirmatory_analysis.json")
    if ana["inputs"]["freeze_hash"] != freeze_hash or ana["inputs"]["generation_record_hash"] != gen_hash:
        raise IntegrityError(f"{model}: the analysis record does not name these freeze/generation records")
    resamples = int(ana["resamples"])
    run_root = root / "evidence" / STUDY_ID / model / "CONFIRMATORY_GENERATION" / "backend_runs"
    rows: list[dict[str, Any]] = []
    for path in current_files(run_root, "scored.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    if len(rows) != int(gen["n_rows"]) or len(rows) != int(ana["n_rows"]):
        raise IntegrityError(f"{model}: {len(rows)} rows on disk, records say {gen['n_rows']}/{ana['n_rows']}")
    design = freeze["design"]
    m_draws = int(design["draws"])
    frames = {int(w): e for w, e in design["frames"].items()}
    tables = {w: frame_table(rows, w, m_draws=m_draws) for w in frames}
    del rows
    positions = {w: [int(b.rpartition("-")[2]) // C.N_WORDINGS for b in t.blocks]
                 for w, t in tables.items()}
    n_positions = 1 + max(p for ps in positions.values() for p in ps)
    model_id = get_model(model).model_id

    out: dict[str, Any] = {"record_hashes": {"FROZEN": freeze_hash, "CONFIRMATORY_GENERATION": gen_hash,
                                             "CONFIRMATORY_ANALYSIS": ana_hash},
                           "resamples": resamples, "per_frame_F1": [], "joint_F1": []}
    for cfg in C.CONFIGURATIONS:
        joint_inputs: dict[int, dict[str, Any]] = {}
        counters: dict[int, CountingRefit] = {}
        for w, t in sorted(tables.items()):
            members = frame_members(t, frames[w], cfg)
            point = members.get("_spectrum_point")
            if point is None:
                continue
            frozen_member = members["F1"]["delta_difficulty"]
            recorded = ana["frames"][str(w)]["configurations"][cfg]["F1"]["members"]["delta_difficulty"]
            counter = CountingRefit(point["data"])
            res = bootstrap_family({"delta_difficulty": counter},
                                   seed=bootstrap_seed(f"F1:{cfg}:f{w}", model_id),
                                   configuration=cfg, family="F1",
                                   n_blocks=len(t.blocks), resamples=resamples)
            m = res.members["delta_difficulty"]
            identity = list(range(len(t.blocks)))
            out["per_frame_F1"].append({
                "model": model, "frame": w, "configuration": cfg, **counter.record(resamples),
                "fidelity": {
                    "estimate_matches_frozen_member": same(m.estimate, float(frozen_member(identity))),
                    "estimate_matches_record": same(m.estimate, recorded["estimate"]),
                    "standard_error_matches_record": same(m.standard_error, recorded["standard_error"]),
                    "replayed_standard_error": m.standard_error,
                    "recorded_standard_error": recorded["standard_error"]}})
            joint_inputs[w] = {"delta_difficulty": CountingRefit(point["data"])}
            counters[w] = joint_inputs[w]["delta_difficulty"]
        if not joint_inputs:
            continue
        jm = joint_members(joint_inputs, positions, n_positions)
        res = bootstrap_family(jm, seed=bootstrap_seed(f"JOINT_F1:{cfg}", model_id),
                               configuration=cfg, family="JOINT_F1",
                               n_blocks=n_positions, resamples=resamples)
        for w, counter in sorted(counters.items()):
            name = f"f{w}:delta_difficulty"
            m = res.members[name]
            recorded = ana["joint"][cfg]["members"][name]
            out["joint_F1"].append({
                "model": model, "frame": w, "configuration": cfg, **counter.record(resamples),
                "fidelity": {
                    "estimate_matches_record": same(m.estimate, recorded["estimate"]),
                    "standard_error_matches_record": same(m.standard_error, recorded["standard_error"]),
                    "replayed_standard_error": m.standard_error,
                    "recorded_standard_error": recorded["standard_error"]}})
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    args = ap.parse_args()
    root, out = Path(args.root).resolve(), Path(args.out).resolve()
    report: dict[str, Any] = {
        "audit": "delta_difficulty degenerate-replicate replay (F1 per frame and JOINT_F1)",
        "evidence_root": str(root), "ceiling": C.DEGENERATE_REPLICATE_MAX, "models": {}}
    for model in args.models:
        report["models"][model] = replay_model(root, model)
        print(model, "done", report["models"][model]["seconds"], "s", flush=True)
    entries = [e for m in report["models"].values() for e in m["per_frame_F1"] + m["joint_F1"]]
    report["summary"] = {
        "replayed_bootstraps": len(entries),
        "replicates_refitted": sum(e["replicates"] for e in entries),
        "non_registered_refits": sum(e["fit_unavailable"] + e["dropped_a_point"] for e in entries),
        "max_degenerate_share": max((e["degenerate_replicate_share"] for e in entries), default=None),
        "any_above_ceiling": any(e["status"] != "OK" for e in entries),
        "all_estimates_match_record": all(e["fidelity"]["estimate_matches_record"] for e in entries),
        "all_standard_errors_match_record": all(e["fidelity"]["standard_error_matches_record"] for e in entries),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
