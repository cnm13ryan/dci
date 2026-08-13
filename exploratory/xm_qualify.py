"""Qualification ladder for one checkpoint on the Transformers path.

Four rungs, each of which must pass before the next is attempted, so a failure
is attributed to the smallest thing that could have caused it:

    1 LOAD           weights load; where they actually sit is measured, not assumed
    2 ONE REQUEST    a single generation completes at batch size 1
    3 SMALL BATCH    N rows at the intended batch size, the first real memory test
    4 REPEATABILITY  rung 3 again; identical seeds must give identical text

Rung 4 exists because the failure this ladder was written after was a THROUGHPUT
failure, not a crash — two runs contending produced correct-looking rows slowly.
Determinism is the cheapest evidence that a run owned the machine: shared GPUs
change batch composition and OOM-recovery splits, and a split changes which rows
sit together, which is observable in the text.

Every rung records free VRAM per card before and after, so a memory verdict can
prove what the cards held when it was measured.

    uv run python xm_qualify.py --model google/gemma-4-12B-it \\
        --device-map auto --max-memory-per-gpu 13GiB --batch-size 2
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

from crossmodel import contract, runlock, runner
from crossmodel.adapters import CHECKPOINTS, get_adapter
from crossmodel.contract import ReasoningMode


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def vram() -> dict:
    return {"free_gib_per_card": runlock.free_vram_gib(),
            "host": runlock.host_memory_gib()}


def parameter_placement(adapter) -> dict:
    """Where the weights ACTUALLY sit, and how much each card holds.

    `device_map="auto"` is a request, not a guarantee. It fills cards in order
    up to `max_memory`, so a cap set too high puts almost everything on card 0
    and leaves the KV cache nowhere to grow — which is a load that succeeds and
    a generation that cannot.
    """
    try:
        import torch

        by_device: dict[str, float] = {}
        for parameter in adapter._model.parameters():
            key = str(parameter.device)
            by_device[key] = by_device.get(key, 0.0) + (
                parameter.numel() * parameter.element_size() / 2 ** 30)
        buffers: dict[str, float] = {}
        for buffer in adapter._model.buffers():
            key = str(buffer.device)
            buffers[key] = buffers.get(key, 0.0) + (
                buffer.numel() * buffer.element_size() / 2 ** 30)
        return {
            "parameter_gib_per_device": {k: round(v, 2)
                                         for k, v in sorted(by_device.items())},
            "buffer_gib_per_device": {k: round(v, 2)
                                      for k, v in sorted(buffers.items())},
            "total_parameter_gib": round(sum(by_device.values()), 2),
            "devices": sorted(by_device),
            "torch_allocated_gib": {
                f"cuda:{i}": round(torch.cuda.memory_allocated(i) / 2 ** 30, 2)
                for i in range(torch.cuda.device_count())}
            if torch.cuda.is_available() else {},
        }
    except Exception as error:                          # noqa: BLE001
        return {"error": f"{type(error).__name__}: {error}"}


def summarise(records: list[dict]) -> dict:
    return {
        "rows": len(records),
        "answered": sum(1 for r in records
                        if (r["final_answer"] or "").strip()),
        "closed": sum(1 for r in records if r["natural_reasoning_closed"]),
        "cap_hits": sum(1 for r in records if r["reasoning_cap_hit"]),
        "technical_failures": sum(1 for r in records
                                  if r["technical_failure"]),
        "median_reasoning_tokens": sorted(
            r["reasoning_tokens"] for r in records)[len(records) // 2]
        if records else None,
        "max_reasoning_tokens": max((r["reasoning_tokens"] for r in records),
                                    default=None),
        "failure_reasons": sorted({r["technical_failure_reason"][:200]
                                   for r in records
                                   if r["technical_failure"]}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=list(CHECKPOINTS))
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--max-memory-per-gpu", default=None)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--generation-ceiling", type=int, default=8192)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--skip-repeatability", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    tag = args.model.split("/")[-1].replace(".", "")
    out_dir = Path(args.out or f"runs/xmq_{tag}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with runlock.RunLock(out_dir, args.model, run_kind="qualification",
                         gpus=args.device_map) as lock:
        return ladder(args, out_dir, lock)


def ladder(args, out_dir: Path, lock) -> int:
    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()
    design = runner.build_design(state, stage="XM_cross_model",
                                 load=contract.LOAD)

    report = {
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "model_id": args.model,
        "checked_utc": utc_stamp(),
        "configuration": {
            "device_map": args.device_map,
            "max_memory_per_gpu": args.max_memory_per_gpu,
            "batch_size": args.batch_size,
            "generation_ceiling": args.generation_ceiling,
            "reasoning_mode": ReasoningMode.THINKING_ENABLED_BOUNDED,
            "dtype": "bfloat16", "quantization": "none",
        },
        "machine_at_start": {**vram(),
                             "orphans_reaped": lock.orphans_reaped},
        "rungs": {},
    }

    def finish(verdict: str, blocker: str = "") -> int:
        report["verdict"] = verdict
        report["blocker"] = blocker
        (out_dir / "qualification.json").write_text(
            json.dumps(report, indent=1, default=str))
        print(f"\n{'=' * 70}\n{args.model}: {verdict}")
        if blocker:
            print(f"  blocker: {blocker}")
        print(f"  wrote {out_dir}/qualification.json")
        return 0 if verdict == "QUALIFIED" else 1

    adapter = get_adapter(args.model, device_map=args.device_map)
    if args.max_memory_per_gpu:
        adapter.CAPACITY_MAX_MEMORY_PER_GPU = args.max_memory_per_gpu
    revision = adapter.resolve_revision()
    report["model_revision"] = revision
    lock.revision = revision
    lock._write_manifest(state="running")

    # ---------------------------------------------------------- rung 1: load
    print(f"\nRUNG 1 — load {args.model} @ {revision[:12]}", flush=True)
    before = vram()
    started = time.perf_counter()
    try:
        adapter.load()
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["1_load"] = {
            "passed": False, "vram_before": before, "vram_after": vram(),
            "error": f"{type(error).__name__}: {error}"[:600],
            "traceback": traceback.format_exc()[-2500:]}
        return finish("BLOCKED_AT_LOAD", f"{type(error).__name__}: {error}"[:300])

    placement = parameter_placement(adapter)
    report["rungs"]["1_load"] = {
        "passed": True,
        "seconds": round(time.perf_counter() - started, 1),
        "vram_before": before, "vram_after": vram(),
        "placement": placement,
        "execution_metadata": adapter.execution_metadata(),
    }
    print(f"  loaded in {report['rungs']['1_load']['seconds']}s")
    print(f"  weights per device: "
          f"{placement.get('parameter_gib_per_device')}")
    print(f"  free VRAM after load: {vram()['free_gib_per_card']} GiB")

    # ------------------------------------------------- rung 2: one request
    print("\nRUNG 2 — one request at batch size 1", flush=True)
    started = time.perf_counter()
    try:
        one, _ = runner.run_slice(
            adapter, design[:1], state, ReasoningMode.NATURAL_REASONING,
            run_id=out_dir.name + "_rung2", batch_size=1, progress=False,
            generation_ceiling=args.generation_ceiling)
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["2_one_request"] = {
            "passed": False, "error": f"{type(error).__name__}: {error}"[:600],
            "vram": vram()}
        return finish("BLOCKED_AT_ONE_REQUEST",
                      f"{type(error).__name__}: {error}"[:300])
    stats = summarise(one)
    report["rungs"]["2_one_request"] = {
        "passed": stats["technical_failures"] == 0 and stats["answered"] == 1,
        "seconds": round(time.perf_counter() - started, 1),
        "vram_after": vram(), **stats}
    print(f"  {stats['answered']}/1 answered, {stats['cap_hits']} cap hits, "
          f"{stats['technical_failures']} failures, "
          f"{report['rungs']['2_one_request']['seconds']}s")
    if not report["rungs"]["2_one_request"]["passed"]:
        return finish("BLOCKED_AT_ONE_REQUEST",
                      "; ".join(stats["failure_reasons"])
                      or "no final answer from a single request")

    # ------------------------------------------------- rung 3: small batch
    print(f"\nRUNG 3 — {args.rows} rows at batch size {args.batch_size}",
          flush=True)
    started = time.perf_counter()
    try:
        batch, _ = runner.run_slice(
            adapter, design[:args.rows], state,
            ReasoningMode.NATURAL_REASONING,
            run_id=out_dir.name + "_rung3", batch_size=args.batch_size,
            generation_ceiling=args.generation_ceiling,
            incremental_path=out_dir / "rung3_rows.jsonl")
    except Exception as error:                          # noqa: BLE001
        report["rungs"]["3_small_batch"] = {
            "passed": False, "error": f"{type(error).__name__}: {error}"[:600],
            "vram": vram()}
        return finish("BLOCKED_AT_SMALL_BATCH",
                      f"{type(error).__name__}: {error}"[:300])
    elapsed = time.perf_counter() - started
    stats = summarise(batch)
    rate = len(batch) / elapsed * 60
    report["rungs"]["3_small_batch"] = {
        "passed": stats["technical_failures"] == 0,
        "seconds": round(elapsed, 1), "rows_per_minute": round(rate, 2),
        "projected_minutes_for_160": round(160 / rate, 1) if rate else None,
        "vram_after": vram(), **stats}
    print(f"  {stats['answered']}/{len(batch)} answered, "
          f"{stats['technical_failures']} failures, {rate:.2f} rows/min "
          f"→ 160 rows in ~{160 / rate:.0f} min" if rate else "")
    if not report["rungs"]["3_small_batch"]["passed"]:
        return finish("BLOCKED_AT_SMALL_BATCH",
                      "; ".join(stats["failure_reasons"]))

    # --------------------------------------------- rung 4: repeatability
    if args.skip_repeatability:
        return finish("QUALIFIED_WITHOUT_REPEATABILITY")

    print(f"\nRUNG 4 — repeat rung 3; identical seeds must give identical text",
          flush=True)
    repeat, _ = runner.run_slice(
        adapter, design[:args.rows], state, ReasoningMode.NATURAL_REASONING,
        run_id=out_dir.name + "_rung4", batch_size=args.batch_size,
        progress=False, generation_ceiling=args.generation_ceiling)
    first = {r["row_id"]: r["final_answer"] for r in batch}
    second = {r["row_id"]: r["final_answer"] for r in repeat}
    identical = sum(1 for k in first if first.get(k) == second.get(k))
    report["rungs"]["4_repeatability"] = {
        "passed": identical == len(first),
        "identical_answers": identical, "of": len(first),
        "vram_after": vram()}
    print(f"  {identical}/{len(first)} identical")
    if identical != len(first):
        return finish("NOT_REPRODUCIBLE",
                      f"only {identical}/{len(first)} rows reproduced; the run "
                      "may not have owned the machine")

    report["recommended_configuration"] = {
        "device_map": args.device_map,
        "max_memory_per_gpu": args.max_memory_per_gpu,
        "batch_size": args.batch_size,
        "generation_ceiling": args.generation_ceiling,
        "projected_minutes_for_160_rows":
            report["rungs"]["3_small_batch"]["projected_minutes_for_160"],
    }
    return finish("QUALIFIED")


if __name__ == "__main__":
    raise SystemExit(main())
