"""Emit the five-model vLLM TP=2 qualification matrix.

Reads only qualification artefacts — Stage A smokes, the Kimi capacity grid, and
the Qwen single-request probes. Never a DCI generation, because the whole point
of this gate is that it is settled before the experiment runs.

Final status per checkpoint is one of:

    TP2_THINKING_VALID     loads TP=2 in BF16, native thinking on, parser
                           separates reasoning from answer, and DCI-SHAPED
                           prompts close their reasoning naturally
    TP2_BACKEND_BLOCKED    the engine cannot build the model at all
    TP2_CAPACITY_BLOCKED   BF16 weights do not fit at any tested envelope
    TP2_REASONING_UNCLOSED loads and parses, but reasoning does not terminate
                           on DCI-shaped prompts

    uv run python xm_vllm_final_qualification.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import vllm_models

RUNS = Path("runs")


def read(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:                                   # noqa: BLE001
        return None


def status_for(model_id: str, smoke, capacity, probe) -> dict:
    spec = vllm_models.get(model_id)
    row = {
        "model_id": model_id,
        "family": spec.family,
        "revision": (smoke or {}).get("model_revision")
                    or (probe or {}).get("revision")
                    or (capacity or {}).get("revision") or "",
        "tensor_parallel_size": 2,
        "dtype": "bfloat16",
        "quantization": "none",
        "reasoning_parser": spec.reasoning_parser or "delimiters",
        "chat_template_kwargs": spec.chat_template_kwargs,
        "loads_tp2": None, "bf16": True, "thinking_enabled": None,
        "simple_smoke": None, "dci_shaped_closure": None,
        "parser_valid": None, "final_status": "NOT RUN", "evidence": "",
    }

    smoke_status = (smoke or {}).get("status")
    if smoke_status == "TP2_BACKEND_BLOCKED":
        row.update(loads_tp2=False, thinking_enabled=False,
                   parser_valid=None, final_status="TP2_BACKEND_BLOCKED",
                   evidence="engine cannot build the model; see execution "
                            "matrix for the exception")
        return row
    if smoke_status == "TP2_CAPACITY_BLOCKED" or (
            capacity and capacity.get("first_working") is None):
        tried = len((capacity or {}).get("attempts", []))
        row.update(loads_tp2=False, thinking_enabled=None, parser_valid=None,
                   final_status="TP2_CAPACITY_BLOCKED",
                   evidence=f"BF16 weights did not load in {tried} tested "
                            "envelope(s); failure is at weight load, not KV")
        return row

    if smoke:
        row["loads_tp2"] = True
        row["thinking_enabled"] = bool(smoke.get("reasoning_emitted"))
        row["simple_smoke"] = (
            f"{smoke.get('answers_non_empty')}/{smoke.get('n')} answers, "
            f"{smoke.get('closed')}/{smoke.get('n')} closed, "
            f"weights {smoke.get('weight_integrity_passed')}/"
            f"{smoke.get('weight_integrity_checks')}")
        row["parser_valid"] = (not smoke.get("marker_leak_into_answer")
                               and not smoke.get("control_token_residue"))

    if probe:
        cases = probe.get("cases", [])
        closed = sum(1 for c in cases if c["close_marker_in_raw"])
        answered = sum(1 for c in cases if c["answer_chars"] > 0)
        capped = sum(1 for c in cases if c["hit_cap"])
        row["dci_shaped_closure"] = f"{closed}/{len(cases)} closed, " \
                                    f"{answered}/{len(cases)} answered, " \
                                    f"{capped} hit the cap"
        row["thinking_enabled"] = bool(
            probe.get("interface", {}).get("template_actually_differs"))
        if cases and closed == len(cases) and answered == len(cases):
            row["final_status"] = "TP2_THINKING_VALID"
            row["evidence"] = "all DCI-shaped probes closed and answered"
        elif cases:
            row["final_status"] = "TP2_REASONING_UNCLOSED"
            worst = max(cases, key=lambda c: c["generated_tokens"])
            row["evidence"] = (
                f"{capped}/{len(cases)} DCI-shaped probes ran to the cap; "
                f"longest {worst['generated_tokens']} tokens in "
                f"{worst['elapsed_seconds']}s at "
                f"{worst['tokens_per_second']} tok/s; trailing-line "
                f"repetition share {worst['repetition']['top_line_share']}")
        row["probe_cases"] = cases
    elif row["loads_tp2"]:
        row["final_status"] = "TP2_DCI_SHAPED_NOT_MEASURED"
        row["evidence"] = ("simple smoke passed; the DCI-shaped probe did not "
                           "complete, so DCI-shaped closure is UNMEASURED — "
                           "not a closure failure and not a pass")
        if smoke and smoke.get("cap_hits"):
            row["final_status"] = "TP2_REASONING_UNCLOSED"
            row["evidence"] = (
                f"loads and parses, but {smoke['cap_hits']}/{smoke['n']} "
                "composed-constraint smoke prompts ran to the ceiling without "
                "closing")
    return row


def render(rows: list[dict]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    valid = [r for r in rows if r["final_status"] == "TP2_THINKING_VALID"]

    def cell(value):
        if value is None:
            return "—"
        if isinstance(value, bool):
            return "yes" if value else "**no**"
        return str(value)

    lines = [
        "# vLLM TP=2 final qualification — five checkpoints",
        "",
        f"Recorded {stamp}. Machine-readable twin:",
        "`CROSS_MODEL_VLLM_TP2_FINAL_QUALIFICATION.json`.",
        "",
        "Fixed condition: vLLM 0.27.1+rocm723, BF16, `tensor_parallel_size=2`,",
        "2 × RX 7900 XTX (gfx1100), `disable_custom_all_reduce=True`,",
        "`NCCL_P2P_DISABLE=1`, native thinking enabled, no quantization.",
        "",
        f"**Result: {len(valid)}/5 `TP2_THINKING_VALID`.**",
        "",
        "| model | loads TP=2 | BF16 | thinking enabled | DCI-shaped closure | parser valid | final status |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model_id'].split('/')[-1]}` | "
            f"{cell(row['loads_tp2'])} | {cell(row['bf16'])} | "
            f"{cell(row['thinking_enabled'])} | "
            f"{cell(row['dci_shaped_closure'])} | "
            f"{cell(row['parser_valid'])} | **{row['final_status']}** |")

    lines += ["", "## Evidence", ""]
    for row in rows:
        lines.append(f"* **{row['model_id'].split('/')[-1]}** — "
                     f"{row['evidence'] or '—'}")
        if row.get("simple_smoke"):
            lines.append(f"  * simple smoke: {row['simple_smoke']}")
    lines += [
        "",
        "## Gate",
        "",
        "The DCI k=3 slice runs only at 5/5. Anything less means at least one",
        "checkpoint would enter the comparison under a different execution",
        "condition from the others, which is the confound this whole retry",
        "exists to remove.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="CROSS_MODEL_VLLM_TP2_FINAL_QUALIFICATION.md")
    args = parser.parse_args()

    # A checkpoint may have several smoke records (different envelopes, or a
    # run stopped by hand). Prefer the most informative: one that loaded and
    # generated beats one that was interrupted before writing any output, and
    # a killed run must never be reported as "the engine cannot build it".
    def rank(record: dict) -> int:
        if record.get("status") == "TP2_LOAD_VALID":
            return 3
        if record.get("n"):            # generated something
            return 2
        if record.get("status") == "TP2_CAPACITY_BLOCKED":
            return 1
        return 0

    smokes = {}
    for path in sorted(RUNS.glob("xmv_smoke*/smoke.json")):
        record = read(path)
        if not record:
            continue
        model = record["model_id"]
        if model not in smokes or rank(record) > rank(smokes[model]):
            smokes[model] = record

    capacity = {}
    for path in sorted(RUNS.glob("xmv_*capacity*/capacity.json")):
        record = read(path)
        if record:
            capacity[record["model"]] = record

    probes = {}
    for path in sorted(RUNS.glob("xmv_probe_*/probe.json")):
        record = read(path)
        if record:
            probes[record["model"]] = record

    rows = [status_for(model_id, smokes.get(model_id),
                       capacity.get(model_id), probes.get(model_id))
            for model_id in vllm_models.CHECKPOINTS]

    out = Path(args.out)
    out.write_text(render(rows))
    out.with_suffix(".json").write_text(json.dumps({
        "experiment": "VLLM_TP2_CROSS_MODEL",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "condition": {
            "backend": "vllm 0.27.1+rocm723",
            "tensor_parallel_size": 2, "dtype": "bfloat16",
            "quantization": "none",
            "disable_custom_all_reduce": True,
            "NCCL_P2P_DISABLE": "1",
            "gpus": "2 x AMD Radeon RX 7900 XTX (gfx1100)"},
        "rows": rows}, indent=1))

    print(render(rows))
    valid = [r["model_id"] for r in rows
             if r["final_status"] == "TP2_THINKING_VALID"]
    print(f"\nwrote {out}")
    print(f"TP2_THINKING_VALID: {len(valid)}/5 — {valid}")
    return 0 if len(valid) == 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
