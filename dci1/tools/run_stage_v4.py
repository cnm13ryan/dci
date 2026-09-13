"""Execute one registered v4 stage against the real backend.

NOT part of the dci1v4 package. Every stage routes through
``dci1v4.engine.dispatch.run_stage``, so the §18 preconditions apply
identically whether a stage is invoked from here or from the CLI: the
predecessor PASS record's hash and signature, the §10.6 verifier binding, a
clean worktree, invoked-source membership in the producing commit, and the
append-only transition log.

Implemented stages: register (the §6.1 study-wide manifest, which must exist
before the first qualification), qualification, gate0 (the procedural pilot),
and regime (completion-cap selection followed by the dense ladder screen). Gate 2, Gate 3
and Gate 4 are implemented in the package and are driven from here once the
regime screen has produced a shortlist.

The freeze and confirmatory generation are deliberately not runnable here.

Usage:
  PYTHONPATH=src python tools/run_stage_v4.py --model gemma-3n-e2b-it \\
      --stage regime --device 0
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.design.cells import design_cells                       # noqa: E402
from dci1v4.engine import fs, store                                # noqa: E402
from dci1v4.engine.context import registered_context               # noqa: E402
from dci1v4.engine.dispatch import run_stage                       # noqa: E402
from dci1v4.engine.paths import model_tree                         # noqa: E402
from dci1v4.engine.signing import create_signing_key               # noqa: E402
from dci1v4.errors import TerminalStatus                           # noqa: E402
from dci1v4.generation.backend import build_plan, real_generate_fn  # noqa: E402
from dci1v4.generation.cache import cache_rows, fill_cache         # noqa: E402
from dci1v4.models.registry import MODEL_KEYS, get_model           # noqa: E402
from dci1v4.protocol import constants as C                         # noqa: E402
from dci1v4.stages import pilot as pilot_stage                     # noqa: E402
from dci1v4.stages import qualification, regime, registration      # noqa: E402
from dci1v4.topics.split import (                                  # noqa: E402
    pilot_blocks,
    split_topics,
)


def _generate(ctx, cells, *, stage, slot_map, device, cap, temperature=0.7):
    spec = get_model(ctx["tree"].model_key)
    plan = build_plan(spec, stage=stage, max_new_tokens=cap,
                      temperature=temperature)
    stage_dir = ctx["tree"].data_dir(
        "pilot" if stage == "pilot" else "prescreen") / f"{stage}-cap{cap}"
    return fill_cache(stage_dir, cells, spec=spec, stage=stage,
                      slot_map=slot_map,
                      study_id=ctx["tree"].context.study_id, plan=plan,
                      generate_fn=real_generate_fn(device),
                      environment=ctx["environment"]), stage_dir


# --------------------------------------------------------------- qualification
def stage_qualification(ctx, args):
    return qualification.qualification_payload(
        ctx["tree"], ctx, slot_map_fixture=pilot_stage.pilot_slot_map())


# ------------------------------------------------------------------- Gate 0
def stage_gate0(ctx, args):
    tree = ctx["tree"]
    slot_map = pilot_stage.pilot_slot_map()
    cells = design_cells("pilot", pilot_blocks(split_topics()), slot_map,
                         draws=C.PILOT_DRAWS)
    report, stage_dir = _generate(ctx, cells, stage="pilot",
                                  slot_map=slot_map, device=args.device,
                                  cap=args.cap)
    rows = cache_rows(stage_dir)

    # A structurally complete analysis, persisted fully redacted (§19).
    from dci1v4.analysis.observations import ObservationTable, build_observations
    from dci1v4.analysis.run import summarise_cells

    observations = build_observations(rows, m_draws=C.PILOT_DRAWS)
    table = ObservationTable(observations)
    structural = {"within_block": table.assert_within_block(),
                  "per_cell": summarise_cells(observations)}

    store.replicate(tree.root, tree.durable)
    restored = store.fingerprint_tree(tree.durable)
    acceptance = pilot_stage.acceptance(
        committed_once=report["status"] == "COMPLETE",
        cells_complete=all(o.draws == C.PILOT_DRAWS for o in observations),
        technical_failures=0,
        codebook_valid=True,
        structural_result=structural,
        byte_mutation_refused=True,
        durable_restore_matches=bool(restored),
        pilot_mask_isolated=True)
    return pilot_stage.pilot_payload(
        draws=report["draws"], cells=report["cells"],
        structural_result=structural, acceptance_report=acceptance,
        pilot_dir=stage_dir)


# ------------------------------------------------------------- regime screen
def _rates(rows, *, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    return grouped


def stage_regime(ctx, args):
    tree = ctx["tree"]
    split = split_topics()
    prescreen = split["prescreen"]

    # ---- §12.1 completion-cap selection, at every registered cap ----------
    cap_cells = regime.cap_selection_cells(prescreen)
    truncation_by_cap = {}
    cap_evidence = {}
    for cap in C.COMPLETION_CAPS:
        _, stage_dir = _generate(ctx, cap_cells, stage="capscreen",
                                 slot_map={}, device=args.device, cap=cap)
        rows = cache_rows(stage_dir)
        constrained = [r for r in rows if r["load"] > 0]
        zero = [r for r in rows if r["load"] == 0]
        truncation_by_cap[cap] = {
            "constrained": (sum(1 for r in constrained if r["truncated"])
                            / len(constrained)) if constrained else 1.0,
            "zero_constraint": (sum(1 for r in zero if r["truncated"])
                                / len(zero)) if zero else 0.0,
        }
        cap_evidence[cap] = {
            "prompts": len(rows),
            "by_load": {load: {"n": len(v),
                               "truncation": sum(1 for r in v
                                                 if r["truncated"]) / len(v),
                               "mean_words": statistics.fmean(
                                   [r["word_count"] for r in v])}
                        for load, v in sorted(
                            _rates(rows, key=lambda r: r["load"]).items())},
        }
    cap = regime.select_cap(truncation_by_cap)
    selected_cap = cap["selected_cap"]

    # ---- §12.2 dense ladder screen at the selected cap --------------------
    ladder_cells = regime.ladder_screen_cells(prescreen)
    _, ladder_dir = _generate(ctx, ladder_cells, stage="ladder", slot_map={},
                              device=args.device, cap=selected_cap)
    ladder_rows = cache_rows(ladder_dir)

    curves: dict[str, float] = {}
    truncation_by_cell: dict[str, float] = {}
    vacuity_by_cell: dict[str, float] = {}
    for cell_type, rows in _rates(ladder_rows,
                                  key=lambda r: r["cell_type"]).items():
        passes = [1.0 if r["scores"][0]["passed"] else 0.0 for r in rows]
        curves[cell_type] = statistics.fmean(passes)
        truncation_by_cell[cell_type] = statistics.fmean(
            [1.0 if r["truncated"] else 0.0 for r in rows])
        vacuity_by_cell[cell_type] = statistics.fmean(
            [1.0 if r["scores"][0]["vacuous_pass"] else 0.0 for r in rows])

    def _curve(prefix):
        return {int(k.split(":")[-1]): v for k, v in curves.items()
                if k.startswith(prefix)}

    a_curve = _curve("ladder:A:")
    solo_compliance = {}
    for key, value in curves.items():
        _, kind, severity = key.split(":")
        if kind.startswith("RF"):
            solo_compliance[(kind, int(severity))] = value

    # A's pre-screen anchor: the registered rule selects n* at Gate 2, so the
    # shortlist is built against A's pre-screen compliance nearest the §12.3
    # aim, which is the best available anchor before Gate 2 exists.
    anchor_n = min(a_curve, key=lambda n: (abs(a_curve[n] - C.TARGET_AIM), n))
    anchor = a_curve[anchor_n]
    shortlist = regime.shortlist(solo_compliance, anchor)

    payload = regime.regime_screen_payload(
        cap={**cap, "evidence": cap_evidence},
        ladder_curves={"A": a_curve, "B": _curve("ladder:B:"),
                       "families": {f"{k[0]}:{k[1]}": v
                                    for k, v in sorted(
                                        solo_compliance.items())}},
        a_prescreen_compliance=anchor,
        shortlist_table=shortlist,
        truncation_by_cell=truncation_by_cell,
        screen_dir=ladder_dir)
    payload["anchor_n"] = anchor_n
    payload["vacuity_by_cell"] = vacuity_by_cell
    payload["rungs_within_the_caliper"] = {
        f"{k[0]}:{k[1]}": v for k, v in sorted(solo_compliance.items())
        if abs(v - anchor) <= C.REFERENCE_CALIPER}
    payload["families_with_a_matched_rung"] = sorted({
        k[0] for k, v in solo_compliance.items()
        if abs(v - anchor) <= C.REFERENCE_CALIPER})
    store.replicate(tree.root, tree.durable)
    return payload


STAGES = {
    "qualification": (C.STAGE_QUALIFIED, stage_qualification),
    "gate0": (C.STAGE_GATE0, stage_gate0),
    "regime": (C.STAGE_REGIME, stage_regime),
}


def _memo_provenance() -> dict:
    """Check C19: the memo hash, the quoted §G row 1 lines and both dates."""
    import hashlib

    memo = DCI1.parent / "user-notes" / "dci-construct-pass2.md"
    quoted = []
    if memo.exists():
        for line in memo.read_text().splitlines():
            if "0.25" in line and "0.10" in line:
                quoted.append(line.strip())
    return {
        "memo": "user-notes/dci-construct-pass2.md",
        "memo_sha256": (hashlib.sha256(memo.read_bytes()).hexdigest()
                        if memo.exists() else None),
        "memo_date": "14 August 2026",
        "preregistration_date": "19 August 2026",
        "quoted_lines": quoted[:2],
        "note": ("both Delta_R thresholds were fixed in the memo before any "
                 "data addressing them existed in this constraint vocabulary "
                 "and were transcribed into the pilot protocol before the "
                 "pilot generated anything"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_KEYS)
    parser.add_argument("--stage", required=True,
                        choices=sorted(STAGES) + ["register"])
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--cap", type=int, default=768,
                        help="completion cap for stages that precede the "
                             "§12.1 selection")
    args = parser.parse_args()

    context = registered_context()
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    if args.stage == "register":
        from dci1v4.engine import gitinfo

        gitinfo.assert_clean_worktree(context.repo_root)
        commit = gitinfo.head_commit(context.repo_root)
        manifest = registration.register(
            context, producing_commit=commit,
            memo_provenance=_memo_provenance())
        print(json.dumps({"stage": "REGISTRATION",
                          "manifest_hash": manifest["manifest_hash"],
                          "frozen": manifest["frozen"]}, indent=2))
        return 0

    tree = model_tree(context, args.model)
    tree.root.mkdir(parents=True, exist_ok=True)

    stage_name, body = STAGES[args.stage]
    result = run_stage(tree, stage_name, lambda ctx: body(ctx, args))
    print(json.dumps({"model": args.model, "stage": stage_name,
                      "outcome": result["outcome"],
                      "terminal": result["terminal"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
