"""Entry point: one command runs one stage of the exploratory DCI probe.

    uv run --project exploratory python -m dci_exploratory.experiment \
        --stage B --tasks 20 --replicates 3 --load 5

Every run gets its own directory under `--out`, named by stage and start time,
and nothing ever overwrites a previous run.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dci_exploratory import design, harvest, runner

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "runs"

# The exploratory study draws from the PILOT split. That split exists so that
# looking at outcomes cannot burn a topic the confirmatory study will later use;
# drawing from the confirmatory split would spend it for a non-evidence run.
TASK_SPLIT = "pilot"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal DCI directional-interference probe on local ROCm.")
    parser.add_argument("--stage", default="B", help="stage label, e.g. A, B, C")
    parser.add_argument("--tasks", type=int, default=20,
                        help="number of matched underlying instances X_i")
    parser.add_argument("--replicates", type=int, default=3,
                        help="generations per (task, arm, order)")
    parser.add_argument("--load", type=int, default=5, choices=(2, 5),
                        help="compositional load k (v19 LOADS)")
    parser.add_argument("--orders", default="both", choices=("both", "o_A", "o_Q"))
    parser.add_argument("--no-primitives", action="store_true",
                        help="skip the isolated single-instruction rows")
    parser.add_argument("--model", default=runner.ModelConfig.model_id)
    parser.add_argument("--revision", default=runner.ModelConfig.revision)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=runner.ModelConfig.base_seed)
    parser.add_argument("--max-new-tokens", type=int,
                        default=runner.ModelConfig.max_new_tokens)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--arms", default=None,
                        help="comma-separated reference ids replacing the admitted "
                             "panel; DIAGNOSTIC runs only, recorded in config.json")
    parser.add_argument("--target", default=None,
                        help="measured constraint, if not the v19 pair-3 target. "
                             "Selects the HYPOTHESIS-DRIVEN design path, which "
                             "makes no outcome-blind selection claim.")
    parser.add_argument("--focal", default=None,
                        help="focal constraint, if not the v19 pair-3 focal")
    parser.add_argument("--background", default=None,
                        help="comma-separated background ids; only with --target "
                             "or --focal. Defaults to the same rule the admitted "
                             "design uses.")
    parser.add_argument("--task-split", default=TASK_SPLIT,
                        help="task bank split to draw from. 'pilot' is the "
                             "default; 'burned' holds topics already spent by "
                             "development and therefore unusable by the "
                             "confirmatory study, which makes it the right "
                             "source of FRESH instances for a replication.")
    parser.add_argument("--task-offset", type=int, default=0,
                        help="skip this many tasks before taking --tasks, so a "
                             "replication can draw instances the first run did "
                             "not see")
    parser.add_argument("--paraphrase", type=int, default=0,
                        help="wording index; a replication under a different "
                             "wording tests whether the effect is phrasing")
    parser.add_argument("--extensions", action="store_true",
                        help="register the constraints authored in "
                             "dci_exploratory/extensions.py")
    parser.add_argument("--scaffolds", default="",
                        help="comma-separated system-message variants to cross, "
                             f"from {sorted(runner.SCAFFOLDS)}")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and validate the design, write it, load no model")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    S = harvest.load()

    extensions_manifest = None
    if args.extensions:
        from dci_exploratory import extensions
        extensions_manifest = extensions.register()

    arms_override = ([a.strip() for a in args.arms.split(",")] if args.arms else None)
    if args.target or args.focal:
        if not arms_override:
            raise SystemExit("--target/--focal require an explicit --arms list; "
                             "the admitted selection rule is defined for pair 3 "
                             "only and cannot be reused for another target")
        selection = design.custom_selection(
            target=args.target or design.TARGET_ID,
            focal=args.focal or design.FOCAL_ID,
            references=arms_override, load=args.load,
            background=([b.strip() for b in args.background.split(",")]
                        if args.background else None))
    else:
        if args.background:
            raise SystemExit("--background applies only to the hypothesis-driven "
                             "design path (--target/--focal); the admitted design "
                             "chooses its own background by a fixed rule")
        selection = design.select(load=args.load, arms_override=arms_override)

    scaffolds = tuple(s.strip() for s in args.scaffolds.split(","))
    tasks = [t for t in S.TASKS.to_dict("records") if t["split"] == args.task_split]
    if not tasks:
        raise SystemExit(f"no tasks in split {args.task_split!r}; known splits: "
                         f"{sorted(S.TASKS['split'].unique())}")
    if args.task_offset + args.tasks > len(tasks):
        raise SystemExit(f"asked for tasks [{args.task_offset}:"
                         f"{args.task_offset + args.tasks}]; the "
                         f"{args.task_split} split holds {len(tasks)}")
    # A deterministic SLICE, so stage B's tasks are stage A's tasks plus more and
    # a replication with a non-zero offset draws instances no earlier run saw.
    # Extending the sample must not resample the instances already seen.
    tasks = tasks[args.task_offset:args.task_offset + args.tasks]

    orders = design.ORDERS if args.orders == "both" else (args.orders,)
    rows = design.build_design(
        selection, tasks, replicates=args.replicates, base_seed=args.seed,
        stage=args.stage, orders=orders, scaffolds=scaffolds,
        paraphrase_id=args.paraphrase,
        include_primitives=not args.no_primitives)
    # Refuses to spend a second of GPU time on a design that is not matched.
    design.assert_matched(rows, selection)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) / f"stage{args.stage}_{stamp}"
    if out_dir.exists():
        raise SystemExit(f"{out_dir} already exists; runs are never overwritten")
    out_dir.mkdir(parents=True)

    config = runner.ModelConfig(
        model_id=args.model, revision=args.revision, device_index=args.device,
        batch_size=args.batch_size, base_seed=args.seed,
        max_new_tokens=args.max_new_tokens)

    resolved: dict[str, Any] = {
        "stamp": runner.EXPLORATORY_STAMP,
        "stage": args.stage,
        "created_utc": stamp,
        "argv": sys.argv[1:] if argv is None else argv,
        "task_split": args.task_split,
        "task_offset": args.task_offset,
        "n_tasks": len(tasks),
        "task_ids": [t["task_id"] for t in tasks],
        "replicates": args.replicates,
        "orders": list(orders),
        "scaffolds": list(scaffolds),
        "scaffold_text": {s: runner.SCAFFOLDS[s] for s in scaffolds},
        "scaffold_compliance_definition": {
            s: runner.SCAFFOLD_COMPLIANCE[s] for s in scaffolds},
        "arms_override": arms_override,
        "design_path": ("hypothesis-driven (custom_selection)"
                        if (args.target or args.focal) else "admitted v19 rule"),
        "extensions_manifest": extensions_manifest,
        "load": selection.load,
        "paraphrase_id": args.paraphrase,
        "n_rows": len(rows),
        "model": asdict(config),
        "selection": {
            "target": selection.target, "focal": selection.focal,
            "references": list(selection.references),
            "background": list(selection.background),
            "reference_weights": selection.reference_weights(),
            "rule": selection.rule,
        },
        "harvest_provenance": harvest.provenance(),
    }
    (out_dir / "config.json").write_text(json.dumps(resolved, indent=2), encoding="utf-8")
    (out_dir / "selection_audit.json").write_text(json.dumps({
        "rule": selection.rule,
        "candidates": selection.candidate_audit,
        "background": selection.background_audit,
        "satisfiability": selection.satisfiability_audit,
    }, indent=2), encoding="utf-8")
    (out_dir / "design.jsonl").write_text(
        "".join(json.dumps(r.as_dict(), ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    (out_dir / "environment.json").write_text(
        json.dumps(runner.environment_record(), indent=2), encoding="utf-8")

    print(f"[design] {len(rows)} rows | {len(tasks)} tasks | load {selection.load} "
          f"| arms {selection.arms} | orders {orders}")
    print(f"[out] {out_dir}")
    if args.dry_run:
        print("[dry-run] design written and validated; no model loaded")
        return 0

    summary = runner.run(rows, selection, config, out_dir, stage=args.stage)
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("model", "model_fingerprint")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
