"""Freeze the vLLM TP=2 admission matrix.

Reads only Stage A smoke records and Stage B calibration rows — never a k=3 or
k=5 generation from the scientific run. Written before the main outcomes are
read, which is the only thing that makes an admission rule an admission rule.

    uv run python xm_vllm_matrix.py --smoke runs/xmv_smoke2_* \
        --calibration runs/xmv_calib_* \
        --out CROSS_MODEL_VLLM_TP2_EXECUTION_MATRIX.md
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, vllm_models

#: Measured bf16 weight size on the hub. Recorded because two names understate
#: it: `E4B` is 14.9 GiB stored and `A3B` is an ACTIVE count over a 30.6 GiB
#: mixture of experts.
WEIGHTS_GIB = {
    "Qwen/Qwen3.5-4B": 8.7, "Qwen/Qwen3.5-9B": 18.0,
    "google/gemma-4-E4B-it": 14.9, "google/gemma-4-12B-it": 22.3,
    "moonshotai/Kimi-VL-A3B-Thinking-2506": 30.6,
}


def load_smokes(paths: list[Path]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in paths:
        candidate = path / "smoke.json" if path.is_dir() else path
        if candidate.exists():
            record = json.loads(candidate.read_text())
            out[record["model_id"]] = record
    return out


def load_calibrations(paths: list[Path]) -> dict[str, dict]:
    """Summarise each Stage B pilot from its ingested rows."""
    out: dict[str, dict] = {}
    for path in paths:
        rows_path = path / "generations.jsonl"
        if not rows_path.exists():
            continue
        rows = [json.loads(l) for l in rows_path.open()]
        if not rows:
            continue
        tokens = sorted(r["reasoning_tokens"] for r in rows)
        n = len(rows)

        def pct(p: float) -> float:
            return tokens[min(n - 1, int(p * n))]

        out[rows[0]["model_id"]] = {
            "n": n,
            "engineering_ceiling": rows[0]["engineering_ceiling"],
            "reasoning_emitted": sum(1 for r in rows if r["reasoning_emitted"]),
            "closed": sum(1 for r in rows if r["natural_reasoning_closed"]),
            "closure_rate": sum(1 for r in rows
                                if r["natural_reasoning_closed"]) / n,
            "cap_hits": sum(1 for r in rows if r["reasoning_cap_hit"]),
            "cap_hit_rate": sum(1 for r in rows
                                if r["reasoning_cap_hit"]) / n,
            "empty_answers": sum(1 for r in rows if r["answer_empty"]),
            "truncated": sum(1 for r in rows if r["answer_truncated"]),
            "technical_failures": sum(1 for r in rows
                                      if r["technical_failure"]),
            "reasoning_tokens": {
                "mean": round(statistics.mean(tokens), 1),
                "median": pct(0.5), "p25": pct(0.25), "p75": pct(0.75),
                "p90": pct(0.90), "p95": pct(0.95), "max": tokens[-1]},
            "answer_tokens_mean": round(statistics.mean(
                [r["final_answer_tokens"] for r in rows]), 1),
        }
    return out


def admission(model_id: str, smoke: dict | None, calib: dict | None) -> dict:
    """Admitted to the NATURAL_REASONING slice under vLLM TP=2, or not."""
    if not smoke:
        return {"admitted": False, "reason": "no Stage A TP=2 record"}
    status = smoke.get("status")
    if status != "TP2_LOAD_VALID":
        detail = (smoke.get("error_tail", "") or "").strip().splitlines()
        tail = detail[-1][:180] if detail else "; ".join(
            smoke.get("problems", []))[:180]
        return {"admitted": False, "reason": f"{status}: {tail}"}
    if not calib:
        return {"admitted": False, "reason": "no Stage B calibration"}
    if calib["technical_failures"]:
        return {"admitted": False,
                "reason": f"{calib['technical_failures']} technical failure(s) "
                          "in calibration"}
    if calib["empty_answers"]:
        return {"admitted": False,
                "reason": f"{calib['empty_answers']} empty answer(s) in "
                          "calibration"}
    if calib["cap_hit_rate"] > 0.05:
        return {"admitted": False,
                "reason": "NATURAL_REASONING_CENSORED — ceiling reached in "
                          f"{calib['cap_hits']}/{calib['n']} pilot rows"}
    return {"admitted": True, "reason": ""}


def fmt(value, spec: str = ".3f") -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return format(value, spec)
    return str(value)


def render(rows: list[dict], engine: dict) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Cross-model execution matrix — vLLM tensor-parallel 2",
        "",
        "**Experiment `VLLM_TP2_CROSS_MODEL`. Frozen before the k=3 factorial "
        "ran.**",
        "Every entry comes from Stage A (`runs/xmv_smoke2_*`) and Stage B",
        "(`runs/xmv_calib_*`); no k=3 or k=5 generation is read here.",
        "Regenerate with `uv run python xm_vllm_matrix.py`.",
        "",
        f"Recorded {stamp}. Machine-readable twin:",
        "`CROSS_MODEL_VLLM_TP2_EXECUTION_MATRIX.json`.",
        "",
        "This table does **not** say whether a checkpoint shows DCI. It says",
        "whether the checkpoint could be executed at all under the one common",
        "condition this retry exists to impose.",
        "",
        "## Backend",
        "",
        "| field | value |",
        "|---|---|",
    ]
    for key, value in engine.items():
        lines.append(f"| {key} | `{value}` |")

    lines += [
        "",
        "## Identity and numerical condition",
        "",
        "| model | revision | weights | dtype | quant | TP | reasoning parser | chat-template kwargs |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id']}` | `{(row['revision'] or '—')[:12]}` | "
            f"{fmt(row['weights_gib'], '.1f')} GiB | bfloat16 | none | "
            f"{row['tensor_parallel_size']} | "
            f"`{row['reasoning_parser'] or 'delimiters'}` | "
            f"`{row['chat_template_kwargs']}` |")

    lines += [
        "",
        "## Stage A — TP=2 load, both cards, parser, weight integrity",
        "",
        "| model | status | both GPUs active | answers | reasoning emitted | closed | marker leak | control residue | weight integrity |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id'].split('/')[-1]}` | **{row['status']}** | "
            f"{fmt(row['both_gpus_active'])} | "
            f"{fmt(row['answers_non_empty'])}/{fmt(row['n'])} | "
            f"{fmt(row['reasoning_emitted'])} | {fmt(row['closed'])} | "
            f"{fmt(row['marker_leak'])} | {fmt(row['control_residue'])} | "
            f"{fmt(row['weight_integrity_passed'])}/"
            f"{fmt(row['weight_integrity_checks'])} |")

    lines += [
        "",
        "## Stage B — natural-reasoning calibration (DCI-shaped, disjoint tasks)",
        "",
        "| model | n | ceiling | closure | cap-hit rate | empty | truncated | median | p90 | max |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        calib = row.get("calibration") or {}
        tokens = calib.get("reasoning_tokens") or {}
        lines.append(
            f"| `{row['model_id'].split('/')[-1]}` | {fmt(calib.get('n'))} | "
            f"{fmt(calib.get('engineering_ceiling'))} | "
            f"{fmt(calib.get('closure_rate'))} | "
            f"{fmt(calib.get('cap_hit_rate'))} | "
            f"{fmt(calib.get('empty_answers'))} | "
            f"{fmt(calib.get('truncated'))} | {fmt(tokens.get('median'))} | "
            f"{fmt(tokens.get('p90'))} | {fmt(tokens.get('max'))} |")

    lines += [
        "",
        "## Admission to the vLLM TP=2 NATURAL_REASONING slice",
        "",
        "| model | admitted | reason if not |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id']}` | **{fmt(row['admitted'])}** | "
            f"{row['exclusion_reason'] or '—'} |")

    lines += ["", "## Notes", ""]
    for row in rows:
        if row.get("notes"):
            lines.append(f"* **{row['model_id'].split('/')[-1]}** — "
                         f"{row['notes']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", nargs="*", default=[])
    parser.add_argument("--calibration", nargs="*", default=[])
    parser.add_argument("--out",
                        default="CROSS_MODEL_VLLM_TP2_EXECUTION_MATRIX.md")
    args = parser.parse_args()

    smokes = load_smokes([Path(p) for p in args.smoke])
    calibs = load_calibrations([Path(p) for p in args.calibration])

    engine_meta: dict = {}
    for record in smokes.values():
        engine = record.get("engine") or {}
        if engine:
            env = engine.get("env", {})
            engine_meta = {
                "vllm_version": engine.get("vllm_version"),
                "vllm_build_commit": "6e448d0ea9bf3d88d898b65449ca6dc2aec170ac",
                "wheel": "vllm-0.27.1+rocm723-cp312-cp312-manylinux_2_34",
                "torch": "2.11.0+gitd0c8b1f",
                "tensor_parallel_size": 2,
                "dtype": "bfloat16",
                "disable_custom_all_reduce": True,
                "NCCL_P2P_DISABLE": env.get("NCCL_P2P_DISABLE"),
                "HIP_VISIBLE_DEVICES": env.get("HIP_VISIBLE_DEVICES"),
                "gpus": "2 x AMD Radeon RX 7900 XTX (gfx1100), 23.98 GiB each",
                "rocm": "7.2.0 host; wheel built for 7.2.3",
            }
            break

    rows = []
    for model_id in vllm_models.CHECKPOINTS:
        spec = vllm_models.get(model_id)
        smoke = smokes.get(model_id)
        calib = calibs.get(model_id)
        decision = admission(model_id, smoke, calib)
        smoke = smoke or {}
        engine = smoke.get("engine") or {}
        after = engine.get("rocm_smi_after_load") or {}
        rows.append({
            "model_id": model_id,
            "family": spec.family,
            "revision": smoke.get("model_revision"),
            "weights_gib": WEIGHTS_GIB.get(model_id),
            "tensor_parallel_size": smoke.get("tensor_parallel_size", 2),
            "reasoning_parser": spec.reasoning_parser,
            "chat_template_kwargs": spec.chat_template_kwargs,
            "status": smoke.get("status", "NOT RUN"),
            "both_gpus_active": bool(after) and len(after) >= 2,
            "n": smoke.get("n"),
            "answers_non_empty": smoke.get("answers_non_empty"),
            "reasoning_emitted": smoke.get("reasoning_emitted"),
            "closed": smoke.get("closed"),
            "marker_leak": smoke.get("marker_leak_into_answer"),
            "control_residue": smoke.get("control_token_residue"),
            "weight_integrity_passed": smoke.get("weight_integrity_passed"),
            "weight_integrity_checks": smoke.get("weight_integrity_checks"),
            "calibration": calib,
            "admitted": decision["admitted"],
            "exclusion_reason": decision["reason"],
            "notes": spec.notes,
        })

    out = Path(args.out)
    out.write_text(render(rows, engine_meta))
    out.with_suffix(".json").write_text(json.dumps({
        "experiment": "VLLM_TP2_CROSS_MODEL",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "engine": engine_meta,
        "contract": contract.as_dict(),
        "rows": rows}, indent=1))

    print(render(rows, engine_meta))
    admitted = [r["model_id"].split("/")[-1] for r in rows if r["admitted"]]
    print(f"\nwrote {out} and {out.with_suffix('.json')}")
    print(f"admitted to vLLM TP=2 NATURAL_REASONING: "
          f"{len(admitted)}/{len(rows)} — {admitted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
