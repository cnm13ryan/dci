"""Stages D and E: primitive competence, then natural-reasoning calibration.

**Stage D — can the checkpoint do the pieces at all?** Each of the five
instructions is presented ALONE, on tasks drawn from a split the scientific
slice never touches. If the focal instruction B is near floor on a checkpoint,
the four-state table for that checkpoint is mostly a report on "neither" versus
"target only" rather than on arbitration between two live constraints, and that
limit has to be recorded BEFORE the main result is looked at — not discovered
afterwards in a way that could be fitted to whatever the result turned out to be.

Floor-limited does not mean excluded. It means the interpretation is constrained.

**Stage E — how much reasoning does this checkpoint actually use?** The Qwen
reasoning-budget grid found capped conditions heavily censored while the natural
endpoint closed cleanly, so no budget from that study transfers here. Each
checkpoint gets its own ceiling, derived from its own context envelope, and its
own measured distribution. A ceiling that binds at a meaningful rate is a failed
calibration, not a dose.

    uv run python xm_calibrate.py --models ... [--stage D|E|DE]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract
from crossmodel.adapters import CHECKPOINTS, get_adapter
from crossmodel.adapters.base import GenerationConfig
from crossmodel.contract import ReasoningMode

#: The five instructions whose isolated compliance Stage D measures.
PRIMITIVES = (contract.TARGET, contract.FOCAL, contract.REFERENCE,
              contract.SEMICOLON_BACKGROUND, contract.CONTROL_BACKGROUND)

#: Disjoint from the scientific slice, which uses `pilot`.
CALIBRATION_SPLIT = "calibration"
N_CALIBRATION_TASKS = 10
CALIBRATION_REPLICATES = 1

#: Generation chunk. Small on purpose: under natural reasoning the ceiling is
#: ~39,500 tokens and a batch's peak KV footprint is set by whichever member
#: reasons longest, which is not knowable before it runs.
CHUNK = 4


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def calibration_tasks(state, n: int) -> list[dict]:
    bank = state.TASKS
    split = bank[bank["split"] == CALIBRATION_SPLIT]
    if len(split) < n:
        # Fall back to any split the scientific slice does not use.
        used = {t["task_id"] for t in contract.resolve_tasks(state)}
        split = bank[~bank["task_id"].isin(used)]
    chosen = split.head(n)
    return [{"task_id": r.task_id, "topic": r.topic}
            for r in chosen.itertuples()]


# ------------------------------------------------------------------ Stage D
def stage_d(adapter, state, mode: str, tasks: list[dict]) -> dict:
    """Isolated compliance with each instruction, one instruction per prompt."""
    from dci_exploratory import harvest

    requests, meta = [], []
    for task in tasks:
        for constraint in PRIMITIVES:
            for replicate in range(CALIBRATION_REPLICATES):
                requests.append(harvest.compose_prompt(
                    task["topic"], [constraint], contract.PARAPHRASE_ID))
                meta.append((task["task_id"], constraint, replicate))

    prompts = [adapter.render_prompt(
        [{"role": "system", "content": state.SYSTEM_MESSAGE},
         {"role": "user", "content": text}], mode) for text in requests]

    ceiling = 0
    if mode != ReasoningMode.NO_THINKING:
        ceiling = adapter.natural_reasoning_ceiling(
            prompts, contract.ANSWER_TOKENS)["derived_ceiling"]
    config = GenerationConfig(
        reasoning_mode=mode, max_answer_tokens=contract.ANSWER_TOKENS,
        temperature=contract.TEMPERATURE, top_p=contract.TOP_P,
        top_k=contract.TOP_K, max_reasoning_tokens=ceiling)

    from crossmodel.runner import _generate_with_recovery

    generations = []
    for start in range(0, len(prompts), CHUNK):
        chunk = prompts[start:start + CHUNK]
        seeds = [(90000 + start + i, 91000 + start + i)
                 for i in range(len(chunk))]
        generations.extend(_generate_with_recovery(
            adapter, chunk, seeds, config, start // CHUNK))

    scores: dict[str, list[float]] = {c: [] for c in PRIMITIVES}
    records = []
    for (task_id, constraint, replicate), generation in zip(meta, generations):
        answer = generation.final_answer
        if answer.strip():
            passed = float(state.verify(answer, constraint).binary_pass)
        else:
            passed = float("nan")
        if passed == passed:
            scores[constraint].append(passed)
        records.append({
            "task_id": task_id, "constraint": constraint,
            "replicate": replicate, "passed": passed,
            "final_answer": answer, "reasoning_tokens": generation.reasoning_tokens,
            "answer_empty": generation.answer_empty})

    rates = {c: (statistics.mean(v) if v else float("nan"))
             for c, v in scores.items()}
    verdict = classify_primitives(rates)
    return {"reasoning_mode": mode, "n_prompts": len(prompts),
            "pass_rates": rates, "classification": verdict,
            "technical_validity": 1.0 - sum(
                1 for r in records if r["answer_empty"]) / max(len(records), 1),
            "records": records}


#: A pass rate at or below this is treated as floor for interpretation.
FLOOR = 0.15


def classify_primitives(rates: dict[str, float]) -> list[str]:
    """Constrain the interpretation; do not exclude the checkpoint."""
    labels = []
    if rates.get(contract.TARGET, 0) <= FLOOR:
        labels.append("TARGET_FLOOR_LIMITED")
    if rates.get(contract.FOCAL, 0) <= FLOOR:
        labels.append("FOCAL_FLOOR_LIMITED")
    if rates.get(contract.REFERENCE, 0) <= FLOOR:
        labels.append("REFERENCE_INVALID")
    background = [rates.get(contract.SEMICOLON_BACKGROUND, 0),
                  rates.get(contract.CONTROL_BACKGROUND, 0)]
    if min(background) <= FLOOR:
        labels.append("BACKGROUND_COMPLIANCE_LIMITED")
    return labels or ["PRIMITIVE_VALID"]


# ------------------------------------------------------------------ Stage E
def stage_e(adapter, state, tasks: list[dict]) -> dict:
    """A natural-reasoning pilot on a small matched sample of full prompts."""
    from dci_exploratory import harvest

    requests, meta = [], []
    for task in tasks:
        for background in contract.BACKGROUNDS:
            for arm in (contract.FOCAL, contract.REFERENCE):
                # QAC: focal slot, target, background slot — the frozen order.
                ordered = [arm, contract.TARGET, background]
                requests.append(harvest.compose_prompt(
                    task["topic"], ordered, contract.PARAPHRASE_ID))
                meta.append((task["task_id"], arm, background))

    prompts = [adapter.render_prompt(
        [{"role": "system", "content": state.SYSTEM_MESSAGE},
         {"role": "user", "content": text}], mode)
        for text, mode in ((r, ReasoningMode.NATURAL_REASONING)
                           for r in requests)]

    envelope = adapter.natural_reasoning_ceiling(
        prompts, contract.ANSWER_TOKENS)
    config = GenerationConfig(
        reasoning_mode=ReasoningMode.NATURAL_REASONING,
        max_answer_tokens=contract.ANSWER_TOKENS,
        temperature=contract.TEMPERATURE, top_p=contract.TOP_P,
        top_k=contract.TOP_K,
        max_reasoning_tokens=envelope["derived_ceiling"])

    from crossmodel.runner import _generate_with_recovery

    generations = []
    started = time.perf_counter()
    for start in range(0, len(prompts), CHUNK):
        chunk = prompts[start:start + CHUNK]
        seeds = [(70000 + start + i, 71000 + start + i)
                 for i in range(len(chunk))]
        generations.extend(_generate_with_recovery(
            adapter, chunk, seeds, config, start // CHUNK))
    elapsed = time.perf_counter() - started

    lengths = sorted(g.reasoning_tokens for g in generations)
    n = len(generations)

    def percentile(p: float) -> float:
        return lengths[min(n - 1, int(p * n))] if n else float("nan")

    cap_hits = sum(1 for g in generations if g.reasoning_cap_hit)
    return {
        "n": n,
        "envelope": envelope,
        "engineering_ceiling": envelope["derived_ceiling"],
        "natural_closures": sum(1 for g in generations
                                if g.natural_reasoning_closed),
        "closure_rate": sum(1 for g in generations
                            if g.natural_reasoning_closed) / max(n, 1),
        "reasoning_cap_hits": cap_hits,
        "cap_hit_rate": cap_hits / max(n, 1),
        "empty_answers": sum(1 for g in generations if g.answer_empty),
        "answers_truncated": sum(1 for g in generations if g.answer_truncated),
        "reasoning_tokens": {
            "mean": statistics.mean(lengths) if lengths else float("nan"),
            "median": percentile(0.5), "p25": percentile(0.25),
            "p75": percentile(0.75), "p90": percentile(0.90),
            "p95": percentile(0.95), "max": lengths[-1] if lengths else 0},
        "final_answer_tokens_mean": statistics.mean(
            [g.final_answer_tokens for g in generations]) if n else 0,
        "seconds_total": round(elapsed, 1),
        "seconds_per_generation": round(elapsed / max(n, 1), 2),
        "validated": cap_hits == 0 and all(not g.answer_empty
                                           for g in generations),
        "records": [{
            "task_id": task_id, "arm": arm, "background": background,
            "reasoning_tokens": g.reasoning_tokens,
            "closed": g.natural_reasoning_closed,
            "cap_hit": g.reasoning_cap_hit,
            "final_answer": g.final_answer,
            "reasoning_text": g.reasoning_text}
            for (task_id, arm, background), g in zip(meta, generations)],
    }


# --------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="*", default=list(CHECKPOINTS))
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--stages", default="DE")
    parser.add_argument("--tasks", type=int, default=N_CALIBRATION_TASKS)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()
    tasks = calibration_tasks(state, args.tasks)
    print(f"calibration tasks ({len(tasks)}, disjoint from the slice): "
          f"{[t['task_id'] for t in tasks]}")

    out_dir = Path(args.out or f"runs/xm_calibrate_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for model_id in args.models:
        print(f"\n=== {model_id}")
        record: dict = {"model_id": model_id, "checked_utc": utc_stamp()}
        adapter = get_adapter(model_id, device_map=args.device_map)
        try:
            record["model_revision"] = adapter.resolve_revision()
            adapter.load()
            record["execution_metadata"] = {
                k: v for k, v in adapter.execution_metadata().items()
                if k not in ("supported_reasoning_modes",)}
        except Exception as error:                      # noqa: BLE001
            record["error"] = f"{type(error).__name__}: {error}"
            record["traceback"] = traceback.format_exc()[-2000:]
            print(f"  LOAD FAILED — {record['error'][:200]}")
            summary.append(record)
            continue

        if "D" in args.stages:
            record["stage_d"] = {}
            for mode in adapter.SUPPORTED_MODES:
                print(f"  Stage D [{mode}] ...", flush=True)
                try:
                    result = stage_d(adapter, state, mode, tasks)
                except Exception as error:              # noqa: BLE001
                    result = {"error": f"{type(error).__name__}: {error}"}
                    traceback.print_exc()
                record["stage_d"][mode] = result
                if "pass_rates" in result:
                    rates = "  ".join(
                        f"{c}={result['pass_rates'][c]:.2f}" for c in PRIMITIVES)
                    print(f"    {rates}")
                    print(f"    -> {', '.join(result['classification'])}")

        if "E" in args.stages and adapter.supports(
                ReasoningMode.NATURAL_REASONING):
            print("  Stage E [natural-reasoning pilot] ...", flush=True)
            try:
                result = stage_e(adapter, state, tasks)
                print(f"    n={result['n']} ceiling={result['engineering_ceiling']} "
                      f"closure={result['closure_rate']:.3f} "
                      f"cap_hits={result['reasoning_cap_hits']} "
                      f"median_r={result['reasoning_tokens']['median']} "
                      f"max_r={result['reasoning_tokens']['max']} "
                      f"{'VALIDATED' if result['validated'] else 'NATURAL_REASONING_NOT_VALIDATED'}")
            except Exception as error:                  # noqa: BLE001
                result = {"error": f"{type(error).__name__}: {error}"}
                traceback.print_exc()
            record["stage_e"] = result

        adapter.unload()
        summary.append(record)
        (out_dir / "calibration.json").write_text(json.dumps(summary, indent=1))

    (out_dir / "calibration.json").write_text(json.dumps(summary, indent=1))
    print(f"\nwrote {out_dir}/calibration.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
