"""Run the frozen cross-model DCI slice for one checkpoint.

One invocation = one checkpoint x one reasoning mode x 160 rows. Nothing about
the science is settable from the command line: the tasks, arms, backgrounds,
order, replicates, decoding and seeds all come from `crossmodel.contract`. What
IS settable is execution — which card, how large a batch, which shard — because
that is exactly the axis the study allows to differ.

    uv run python xm_run.py --model Qwen/Qwen3.5-4B \
        --mode NATURAL_REASONING --device-map cuda:0 --out runs/XM_...

Sharding across the two cards, for a checkpoint that fits on one:

    uv run python xm_run.py ... --device-map cuda:0 --shard 0 --of 2
    uv run python xm_run.py ... --device-map cuda:1 --shard 1 --of 2

Batch composition does not depend on the shard, so the merged output is the same
file either way. `--merge` checks that and writes the merged result.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, runlock, runner, seeds
from crossmodel.adapters import CHECKPOINTS, get_adapter
from crossmodel.contract import ReasoningMode
from crossmodel.schema import assert_provenance


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=list(CHECKPOINTS))
    parser.add_argument("--mode", default=ReasoningMode.NATURAL_REASONING,
                        choices=[ReasoningMode.NATURAL_REASONING,
                                 ReasoningMode.NO_THINKING])
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    parser.add_argument("--load", type=int, default=contract.LOAD,
                        choices=[3, 5],
                        help="k=5 uses the repository's existing higher-load "
                             "construction, not a new one")
    parser.add_argument("--max-memory-per-gpu", default=None,
                        help="weight budget per card in dual-GPU capacity "
                             "mode, e.g. 14GiB. Lower leaves more room for the "
                             "KV cache, which is what a long reasoning trace "
                             "actually consumes")
    parser.add_argument("--generation-ceiling", type=int, default=None,
                        help="total tokens per request; sets the recorded "
                             "condition to THINKING_ENABLED_BOUNDED")
    parser.add_argument("--out", default=None)
    parser.add_argument("--merge", nargs="*", default=None,
                        help="merge these shard files and exit")
    parser.add_argument("--resume", action="store_true",
                        help="permit writing into a directory that already "
                             "holds output; off by default because appending "
                             "to another run's file corrupts it")
    args = parser.parse_args()

    tag = args.model.split("/")[-1].replace(".", "")
    out_dir = Path(args.out or f"runs/xm_{tag}_{args.mode}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.merge:
        merged = runner.merge_shards([Path(p) for p in args.merge],
                                     expected_rows=contract.EXPECTED_ROWS)
        assert_provenance(merged, expected_model=args.model)
        path = out_dir / "generations.jsonl"
        runner.write_rows(merged, path)
        print(f"merged {len(merged)} rows -> {path}")
        return 0

    # Exclusive ownership, taken BEFORE anything touches a GPU. Everything from
    # here on runs inside it, so a second run cannot start, an orphan of a dead
    # run cannot linger, and an interrupted run cannot leave children behind.
    with runlock.RunLock(out_dir, args.model, run_kind=f"transformers_k{args.load}",
                         gpus=args.device_map,
                         allow_resume=args.resume) as lock:
        return _generate(args, out_dir, lock)


def _generate(args, out_dir: Path, lock) -> int:
    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()

    # The stage string feeds the row_id hash, so k=3 keeps the historical value
    # and only the k=5 extension takes a new one. Scientific seeds do not depend
    # on it either way — they are a function of design identity alone.
    stage = ("XM_cross_model" if args.load == contract.LOAD
             else f"XM_cross_model_k{args.load}")
    design_rows = runner.build_design(state, stage=stage, load=args.load)
    print(f"design: {len(design_rows)} rows "
          f"({contract.N_TASKS} tasks x {contract.REPLICATES} replicates x "
          f"{len(contract.BACKGROUNDS)} backgrounds x {len(contract.ARMS)} arms)")

    adapter = get_adapter(args.model, device_map=args.device_map)
    if args.max_memory_per_gpu:
        adapter.CAPACITY_MAX_MEMORY_PER_GPU = args.max_memory_per_gpu
    if not adapter.supports(args.mode):
        print(f"{args.model} does not natively support {args.mode}; "
              "the cell is left missing rather than emulated")
        return 3

    revision = adapter.resolve_revision()
    print(f"{args.model} @ {revision}")
    # The lock manifest records WHICH checkpoint owns the GPUs, not just that
    # someone does, so a concurrent attempt is refused with a useful message.
    lock.revision = revision
    lock._write_manifest(state="running")

    # -------- the prospective record, written BEFORE generation ------------
    # Written first on purpose. A plan recorded after the estimate is known is
    # not a plan, and the research log is supposed to say what was expected.
    plan_path = out_dir / "run_plan.json"
    plan_path.write_text(json.dumps({
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "started_utc": utc_stamp(),
        "model_id": args.model, "model_revision": revision,
        "reasoning_mode": args.mode, "device_map": args.device_map,
        "batch_size": args.batch_size, "shard": args.shard, "of": args.of,
        "contract": contract.as_dict(state),
        "adapter": type(adapter).__name__,
        "generation_strategy": getattr(adapter, "GENERATION_STRATEGY", None),
        "expected_rows": contract.EXPECTED_ROWS,
    }, indent=1))
    print(f"wrote {plan_path}")

    started = time.perf_counter()
    try:
        adapter.load()
    except Exception as error:                          # noqa: BLE001
        (out_dir / "load_failure.json").write_text(json.dumps({
            "model_id": args.model, "model_revision": revision,
            "error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc()}, indent=1))
        print(f"LOAD FAILED — {error}")
        return 4
    print(f"loaded in {time.perf_counter() - started:.1f}s "
          f"({adapter.execution_metadata()['device_configuration']})")

    records, plan = runner.run_slice(
        adapter, design_rows, state, args.mode,
        run_id=out_dir.name, batch_size=args.batch_size,
        shard=args.shard, of=args.of,
        generation_ceiling=args.generation_ceiling,
        incremental_path=out_dir / "partial_generations.jsonl")

    suffix = "" if args.of == 1 else f".shard{args.shard}of{args.of}"
    path = out_dir / f"generations{suffix}.jsonl"
    # Refuse to publish a file whose rows are not exactly the design's rows.
    # Duplicate ids are the fingerprint of two writers; that went undetected
    # once and produced a plausible-looking but corrupt file.
    integrity = runlock.assert_unique_rows(
        records, expected=len(design_rows) if args.of == 1 else None)
    runner.write_rows(records, path)

    audit = seeds.replicate_duplication(records)
    envelope = plan.envelope or {}
    summary = {
        **plan.as_dict(),
        "finished_utc": utc_stamp(),
        "seconds_total": round(time.perf_counter() - started, 1),
        "rows_written": len(records),
        "output": str(path),
        "replicate_duplication": audit,
        "dataset_integrity": integrity,
        "free_vram_gib_at_start": lock.free_vram_at_start,
        "orphans_reaped_at_start": lock.orphans_reaped,
        "technical_failures": sum(1 for r in records if r["technical_failure"]),
        "empty_answers": sum(1 for r in records if r["answer_empty"]),
        "truncated_answers": sum(1 for r in records if r["answer_truncated"]),
        "cap_hits": sum(1 for r in records if r["reasoning_cap_hit"]),
        "traces_opened": sum(1 for r in records if r.get("reasoning_emitted")),
        "closed_naturally": sum(1 for r in records
                                if r["natural_reasoning_closed"]),
        "median_reasoning_tokens": sorted(
            r["reasoning_tokens"] for r in records)[len(records) // 2],
        "max_reasoning_tokens": max(r["reasoning_tokens"] for r in records),
        "mean_answer_tokens": round(sum(
            r["final_answer_tokens"] for r in records) / len(records), 1),
        "envelope": envelope,
        "execution_metadata": adapter.execution_metadata(),
    }
    (out_dir / f"run_summary{suffix}.json").write_text(
        json.dumps(summary, indent=1, default=str))

    print(f"\n{len(records)} rows -> {path}")
    print(f"  ceiling {plan.engineering_ceiling}  cap hits {summary['cap_hits']}"
          f"  closed {summary['closed_naturally']}/{len(records)}")
    print(f"  empty {summary['empty_answers']}  truncated "
          f"{summary['truncated_answers']}  failures "
          f"{summary['technical_failures']}")
    print(f"  median reasoning {summary['median_reasoning_tokens']}  max "
          f"{summary['max_reasoning_tokens']}  mean answer "
          f"{summary['mean_answer_tokens']}")
    print(f"  replicate duplication {audit['identical_pairs']}/"
          f"{audit['replicate_pairs']} = {audit['identical_rate']:.1%}"
          f"{'  <-- IMPLAUSIBLE' if audit['implausible'] else ''}")
    print(f"  {summary['seconds_total']}s total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
