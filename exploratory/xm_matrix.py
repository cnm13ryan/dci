"""Build the five-model admission matrix from the Stage A–E artefacts.

The matrix is frozen BEFORE the main factorial runs. That ordering is the whole
point: an admission rule written after the estimates are known is not an
admission rule. This script reads only the validation and calibration outputs —
never a generation file from the scientific run — and refuses to run if asked to
read one.

    uv run python xm_matrix.py --validate runs/xm_validate_* \
        --calibrate runs/xm_calibrate_* --out CROSS_MODEL_EXECUTION_MATRIX.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract
from crossmodel.adapters import CHECKPOINTS, REGISTRY

#: Weight sizes measured from the hub file metadata, recorded because two of the
#: five checkpoints have names that understate them: `E4B` is 14.9 GiB of stored
#: bf16 weights, and `A3B` is an ACTIVE parameter count over a 30.6 GiB
#: mixture-of-experts checkpoint. Memory is planned from these, never the name.
WEIGHTS_GIB = {
    "Qwen/Qwen3.5-4B": 8.7,
    "Qwen/Qwen3.5-9B": 18.0,
    "google/gemma-4-E4B-it": 14.9,
    "google/gemma-4-12B-it": 22.3,
    "moonshotai/Kimi-VL-A3B-Thinking-2506": 30.6,
}

NOTES = {
    "Qwen/Qwen3.5-4B": "text-only causal-LM class; multimodal tower not loaded",
    "Qwen/Qwen3.5-9B": "text-only causal-LM class; multimodal tower not loaded",
    "google/gemma-4-E4B-it":
        "text-only load impossible: the checkpoint stores "
        "`model.language_model.*` with vision AND audio towers, so the full "
        "conditional-generation class is used and those towers are allocated",
    "google/gemma-4-12B-it":
        "distinct architecture from E4B (`gemma4_unified`), not merely larger",
    "moonshotai/Kimi-VL-A3B-Thinking-2506":
        "custom modeling code (trust_remote_code); `kimi_vl` is absent from "
        "transformers 5.15.0's registry",
}


def load_records(paths: list[Path], filename: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in paths:
        candidate = path / filename if path.is_dir() else path
        if not candidate.exists():
            continue
        for record in json.loads(candidate.read_text()):
            model = record.get("model_id")
            if model:
                # Later artefacts supersede earlier ones for the same model.
                out[model] = record
    return out


def admission(validate: dict | None, calibrate: dict | None) -> dict:
    """The admission decision and, when it is negative, the reason."""
    if not validate:
        return {"admitted": False,
                "reason": "no Stage B/C record — never validated"}
    status = validate.get("load_status")
    if status != "LOAD_VALID":
        return {"admitted": False,
                "reason": f"{status}: {validate.get('blocked_reason', '')[:200]}"}

    modes = validate.get("modes") or {}
    natural = modes.get("NATURAL_REASONING") or {}
    if natural.get("status") == "MODE_FAILED":
        return {"admitted": False,
                "reason": f"natural reasoning failed: {natural.get('error','')[:160]}"}
    if natural.get("marker_leak_into_answer") or natural.get(
            "control_token_residue"):
        return {"admitted": False,
                "reason": "reasoning or control markup reached the final answer"}

    stage_e = (calibrate or {}).get("stage_e") or {}
    if stage_e and not stage_e.get("validated", False):
        return {"admitted": False,
                "reason": "NATURAL_REASONING_NOT_VALIDATED — "
                          f"{stage_e.get('reasoning_cap_hits', '?')} ceiling "
                          f"hit(s), {stage_e.get('empty_answers', '?')} empty "
                          "answer(s) in the pilot"}
    if not stage_e:
        return {"admitted": False,
                "reason": "no Stage E natural-reasoning calibration"}
    return {"admitted": True, "reason": ""}


def row_for(model_id: str, validate: dict | None, calibrate: dict | None
            ) -> dict:
    cls = REGISTRY[model_id]
    validate = validate or {}
    calibrate = calibrate or {}
    modes = validate.get("modes") or {}
    meta = validate.get("execution_metadata") or {}
    stage_d = calibrate.get("stage_d") or {}
    stage_e = calibrate.get("stage_e") or {}

    def mode_ok(name: str) -> str:
        verdict = modes.get(name)
        if not verdict:
            return "not supported" if name not in cls.SUPPORTED_MODES else "not run"
        return {"MODE_VALID": "yes", "MODE_SUSPECT": "suspect",
                "MODE_FAILED": "no"}.get(verdict.get("status"), "?")

    primitives = {}
    for mode, result in stage_d.items():
        if isinstance(result, dict) and "pass_rates" in result:
            primitives = result["pass_rates"]
            classification = result["classification"]
            break
    else:
        classification = ["NOT MEASURED"]

    decision = admission(validate or None, calibrate or None)
    return {
        "model_id": model_id,
        "family": cls.FAMILY,
        "revision": validate.get("model_revision")
                    or calibrate.get("model_revision") or "",
        "weights_gib": WEIGHTS_GIB.get(model_id),
        "dtype": meta.get("dtype", "bfloat16"),
        "quantization": meta.get("quantization", "none"),
        "backend": meta.get("backend", "transformers"),
        "backend_version": meta.get("backend_version", ""),
        "gpu_layout": validate.get("device_map", ""),
        "loaded_class": meta.get("loaded_class", ""),
        "bf16_load_valid": validate.get("load_status") == "LOAD_VALID",
        "load_status": validate.get("load_status", "NOT RUN"),
        "generation_strategy": getattr(cls, "GENERATION_STRATEGY", ""),
        "reasoning_parser": f"{cls.THINK_OPEN} … {cls.THINK_CLOSE}",
        "no_thinking_supported": "NO_THINKING" in cls.SUPPORTED_MODES,
        "no_thinking_validated": mode_ok("NO_THINKING"),
        "natural_supported": "NATURAL_REASONING" in cls.SUPPORTED_MODES,
        "natural_validated": mode_ok("NATURAL_REASONING"),
        "engineering_ceiling": stage_e.get("engineering_ceiling"),
        "natural_closure_rate": stage_e.get("closure_rate"),
        "ceiling_hit_rate": stage_e.get("cap_hit_rate"),
        "median_reasoning_tokens":
            (stage_e.get("reasoning_tokens") or {}).get("median"),
        "primitive_A": primitives.get(contract.TARGET),
        "primitive_B": primitives.get(contract.FOCAL),
        "primitive_R": primitives.get(contract.REFERENCE),
        "background_semicolon": primitives.get(contract.SEMICOLON_BACKGROUND),
        "background_control": primitives.get(contract.CONTROL_BACKGROUND),
        "primitive_classification": classification,
        "admitted": decision["admitted"],
        "exclusion_reason": decision["reason"],
        "notes": NOTES.get(model_id, ""),
    }


def fmt(value, spec: str = ".2f") -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return format(value, spec)
    return str(value)


def render(rows: list[dict]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Cross-model execution matrix",
        "",
        "**Frozen before the main cross-model factorial ran.** Every entry comes",
        "from the Stage A–E artefacts (`runs/xm_validate_*`,",
        "`runs/xm_calibrate_*`); no generation from the scientific run is read",
        "here. Regenerate with `uv run python xm_matrix.py`.",
        "",
        f"Recorded {stamp}. Machine-readable twin:",
        "`CROSS_MODEL_EXECUTION_MATRIX.json`.",
        "",
        "The question this table answers is not whether a checkpoint shows DCI.",
        "It is whether the checkpoint was executed in a way that preserves the",
        "same scientific treatment, so that a behavioural comparison is even",
        "admissible.",
        "",
        "## Identity and numerical condition",
        "",
        "| model | family | revision | weights | dtype | quant | backend | GPU layout | BF16 load |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id']}` | {row['family']} | "
            f"`{(row['revision'] or '—')[:12]}` | "
            f"{fmt(row['weights_gib'], '.1f')} GiB | {row['dtype']} | "
            f"{row['quantization']} | {row['backend']} "
            f"{row['backend_version']} | {row['gpu_layout'] or '—'} | "
            f"{fmt(row['bf16_load_valid'])} |")

    lines += [
        "",
        "## Reasoning interface",
        "",
        "| model | strategy | parser | no-thinking supported | validated | natural supported | validated | ceiling | closure | ceiling hits |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id'].split('/')[-1]}` | "
            f"{row['generation_strategy'] or '—'} | "
            f"`{row['reasoning_parser']}` | "
            f"{fmt(row['no_thinking_supported'])} | "
            f"{row['no_thinking_validated']} | "
            f"{fmt(row['natural_supported'])} | "
            f"{row['natural_validated']} | "
            f"{fmt(row['engineering_ceiling'])} | "
            f"{fmt(row['natural_closure_rate'], '.3f')} | "
            f"{fmt(row['ceiling_hit_rate'], '.3f')} |")

    lines += [
        "",
        "## Primitive competence (Stage D, isolated, disjoint tasks)",
        "",
        "Each instruction presented ALONE. A focal instruction near floor makes",
        "the four-state table a report on *neither* versus *target only* rather",
        "than on arbitration between two live constraints — recorded here, before",
        "the main result was looked at, so the limit cannot be fitted to it.",
        "",
        "| model | A (target) | B (focal) | R (reference) | semicolon bg | control bg | classification |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id'].split('/')[-1]}` | "
            f"{fmt(row['primitive_A'])} | {fmt(row['primitive_B'])} | "
            f"{fmt(row['primitive_R'])} | {fmt(row['background_semicolon'])} | "
            f"{fmt(row['background_control'])} | "
            f"{', '.join(row['primitive_classification'])} |")

    lines += [
        "",
        "## Admission",
        "",
        "| model | admitted | reason if not |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id']}` | **{fmt(row['admitted'])}** | "
            f"{row['exclusion_reason'] or '—'} |")

    lines += ["", "## Execution notes", ""]
    for row in rows:
        if row["notes"]:
            lines.append(f"* **{row['model_id'].split('/')[-1]}** — {row['notes']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", nargs="*", default=[])
    parser.add_argument("--calibrate", nargs="*", default=[])
    parser.add_argument("--out", default="CROSS_MODEL_EXECUTION_MATRIX.md")
    args = parser.parse_args()

    validate = load_records([Path(p) for p in args.validate], "stage_bc.json")
    calibrate = load_records([Path(p) for p in args.calibrate],
                             "calibration.json")

    rows = [row_for(model_id, validate.get(model_id), calibrate.get(model_id))
            for model_id in CHECKPOINTS]

    out = Path(args.out)
    out.write_text(render(rows))
    out.with_suffix(".json").write_text(json.dumps({
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "contract": {k: v for k, v in contract.as_dict().items()},
        "rows": rows}, indent=1))

    print(render(rows))
    print(f"\nwrote {out} and {out.with_suffix('.json')}")
    admitted = [r['model_id'] for r in rows if r['admitted']]
    print(f"\nadmitted {len(admitted)}/{len(rows)}: {admitted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
