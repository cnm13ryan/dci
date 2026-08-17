"""Per-model no-thinking qualification (task §1.3), executable end to end.

Before any study generation, each model must demonstrate on real generated
text that: thinking is disabled with no hidden default mode; no reasoning
channel is included in or scored as the answer; no reasoning markers or
template control tokens leak into the scored text; answer extraction returns
exactly the complete user-visible response; the requested configuration is
actually consumed by vLLM; and model revision and backend identity are
correctly recorded.

The probe prompts are disjoint from the study topic bank. Trivial prompts
carry an expected substring as a weight-integrity check (a corruption
detector, not a capability test).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from dci1.evidence.store import write_json
from dci1.generation.backend import (
    BACKEND_CWD,
    BACKEND_PYTHON,
    backend_env,
    run_backend,
)
from dci1.generation.pools import backend_config_hash
from dci1.models.adapters import ModelSpec, backend_plan
from dci1.protocol.constants import DECODING, ProtocolError, StudyConfig
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed

#: Chat-control residue of any family (copied from the audited smoke check).
CONTROL_RESIDUE = re.compile(r"<\|[^>]{0,40}\|?>|<[^<>]{0,40}\|>|◁/?[a-z]+▷")

#: (prompt, expected substring or None). Disjoint from the topic bank.
PROBES: tuple[tuple[str, str | None], ...] = (
    ("Name the capital city of Japan.\n\nAnswer:", "tokyo"),
    ("What colour is a ripe banana?\n\nAnswer:", "yellow"),
    ("Name the planet we live on.\n\nAnswer:", "earth"),
    ("How many days are in a week? Reply with the number.\n\nAnswer:", "7"),
    ("Describe why bread rises when baked.\n\n1. Use the word however "
     "exactly 1 time.\n2. Every word in the answer must have at most 8 "
     "letters.\n\nAnswer:", None),
    ("Explain why the sky looks blue.\n\n1. No word in the answer may begin "
     "with the letter t.\n2. Use the word however exactly 2 times.\n\n"
     "Answer:", None),
    ("Describe how rain forms.\n\n1. Use the word however exactly 1 time.\n"
     "\nAnswer:", None),
    ("Explain why ice floats on water.\n\nAnswer:", None),
)


def template_probe(spec: ModelSpec) -> dict[str, Any]:
    """Render the chat template three ways in the backend environment and
    test the model's declared switch expectation (live vs inert)."""
    script = Path(__file__).resolve().parent / "template_probe_script.py"
    env = backend_env(device=0)
    # A script run by path does not put the cwd on sys.path (unlike -m), so
    # the shared backend package is supplied explicitly.
    env["PYTHONPATH"] = str(BACKEND_CWD)
    completed = subprocess.run(
        [str(BACKEND_PYTHON), str(script), spec.model_id, spec.revision,
         "1" if spec.trust_remote_code else "0"],
        capture_output=True, text=True, cwd=str(BACKEND_CWD), env=env,
        timeout=600)
    if completed.returncode != 0:
        raise ProtocolError(
            f"template probe failed for {spec.model_key}: "
            f"{completed.stderr[-500:]}")
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    if spec.switch_expectation == "live":
        ok = not payload["renders_identical_true_vs_false"]
        finding = ("enable_thinking is live (True and False render "
                   "differently)" if ok else
                   "enable_thinking DID NOT change the rendering — the "
                   "no-thinking condition would be a mislabel")
    else:
        ok = (payload["renders_identical_plain_vs_true"]
              and payload["renders_identical_true_vs_false"])
        finding = ("enable_thinking is inert (all renders byte-identical); "
                   "no-thinking is native" if ok else
                   "enable_thinking CHANGED the rendering — the checkpoint "
                   "has an undeclared thinking switch")
    payload["expectation"] = spec.switch_expectation
    payload["passed"] = ok
    payload["finding"] = finding
    return payload


def qualify(spec: ModelSpec, *, config: StudyConfig, model_dir: Path,
            device: int = 0) -> dict[str, Any]:
    """The end-to-end qualification run for one model; writes the report."""
    model_dir = Path(model_dir)
    stage_dir = model_dir / "qualification"
    template = template_probe(spec)

    plan = backend_plan(spec)
    design_rows = []
    for index, (prompt, _) in enumerate(PROBES):
        seed = generation_seed(config.generation_root_seed, "qualification",
                               spec.model_id, sha_text(prompt), 0)
        design_rows.append({"row_id": f"{spec.model_key}:qual:{index}",
                            "user_prompt": prompt, "scientific_seed": seed,
                            "probe_index": index})
    outcome = run_backend(stage_dir, plan, design_rows, device=device)
    rows, provenance = outcome["rows"], outcome["provenance"]

    problems: list[str] = []
    checks: dict[str, Any] = {}

    # 1) engine consumed the requested configuration.
    engine_kwargs = provenance.get("engine_kwargs", {})
    checks["revision_consumed"] = \
        engine_kwargs.get("revision") == spec.revision
    checks["dtype_consumed"] = engine_kwargs.get("dtype") == spec.dtype
    sampling = provenance.get("sampling", {})
    checks["decoding_consumed"] = (
        float(sampling.get("temperature", -1)) == DECODING["temperature"]
        and float(sampling.get("top_p", -1)) == DECODING["top_p"]
        and int(sampling.get("top_k", -1)) == DECODING["top_k"]
        and int(sampling.get("max_tokens", -1)) == DECODING["max_new_tokens"])
    checks["no_thinking_mode_recorded"] = \
        (provenance.get("run", {}).get("reasoning_mode") == "NO_THINKING")
    checks["parser_is_null"] = "NO_THINKING" in str(
        provenance.get("reasoning_parser_used", ""))
    for name, value in checks.items():
        if value is False:
            problems.append(f"configuration check failed: {name}")

    # 2) per-row behavioural checks on the raw generated text.
    row_findings = []
    for row, (prompt, expected) in zip(rows, PROBES):
        raw = row.get("raw_generation", "")
        finding = {"row_id": row["row_id"], "outcome": row.get("outcome")}
        if row.get("outcome") != "OK":
            problems.append(f"{row['row_id']}: outcome {row.get('outcome')}")
            row_findings.append(finding)
            continue
        if not raw.strip():
            problems.append(f"{row['row_id']}: empty generation")
        if row.get("reasoning_text", ""):
            problems.append(f"{row['row_id']}: a reasoning channel appeared "
                            f"in the no-thinking condition")
        if row.get("final_answer", "") != raw.strip():
            problems.append(f"{row['row_id']}: extraction does not return "
                            f"the complete user-visible response")
        leaked = [m for m in spec.leakage_markers if m in raw]
        if leaked:
            problems.append(f"{row['row_id']}: reasoning/template markers "
                            f"in scored text: {leaked}")
        residue = CONTROL_RESIDUE.findall(raw)
        if residue:
            problems.append(f"{row['row_id']}: control-token residue "
                            f"{residue[:3]}")
        if expected is not None and expected not in raw.lower():
            problems.append(f"{row['row_id']}: weight-integrity probe missed "
                            f"expected substring {expected!r}")
        if int(row.get("seed_reasoning", -1)) != \
                design_rows[int(row["probe_index"])]["scientific_seed"]:
            problems.append(f"{row['row_id']}: recorded seed differs from "
                            f"the deterministic derivation")
        finding["truncated"] = row.get("finish_reason") == "length"
        row_findings.append(finding)

    if not template["passed"]:
        problems.append(f"template switch: {template['finding']}")

    report = {
        "model_key": spec.model_key,
        "model_id": spec.model_id,
        "revision": spec.revision,
        "backend_config_hash": backend_config_hash(plan),
        "template_probe": template,
        "configuration_checks": checks,
        "rows": row_findings,
        "problems": problems,
        "verdict": "QUALIFIED" if not problems else "FAILED",
        "vllm_version": (provenance.get("host") or {}).get("vllm_version"),
        "gcn_archs": (provenance.get("host") or {}).get("gcn_archs"),
    }
    write_json(model_dir / "qualification_report.json", report)
    return report
