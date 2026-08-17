"""The single configured autorater (amendment A2): instrument mechanics.

A proxy instrument for verifier development and held-out evaluation —
never human validation, never ground truth, never part of scoring. One
configuration-driven judge; every judgment carries full reproduction
provenance; parse errors, refusals, and generation failures are recorded
as distinct statuses and never recoded into labels.

Layout under a model tree's ``gate1/autorater/``:

    split.json                     the deterministic dev/calibration split
    dev/judge_rows.jsonl           raw judge generations (append-once)
    dev/judgments.jsonl            parsed judgments with provenance
    dev/report.json                development disagreement report
    calibration/...                same three, for the held-out half
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from dci1v3.engine import fs
from dci1v3.engine.store import CacheWriter
from dci1v3.errors import IntegrityError, ProtocolError
from dci1v3.models.registry import get_model
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import domain_int, sha_obj, sha_text

VALID = "valid"
INVALID_OUTPUT = "invalid_output"
REFUSAL = "refusal"
GENERATION_FAILURE = "generation_failure"
STATUSES = (VALID, INVALID_OUTPUT, REFUSAL, GENERATION_FAILURE)

_CONFIG_PATH = (Path(__file__).resolve().parents[1] / "protocol" / "data"
                / "autorater.json")


def load_config(path: Path | None = None) -> dict[str, Any]:
    config = fs.read_json(path or _CONFIG_PATH)
    for key in ("schema_version", "judge_model_key", "prompt_version",
                "decoding"):
        if key not in config:
            raise ProtocolError(f"autorater config missing {key!r}")
    if config["prompt_version"] not in C.AUTORATER_PROMPTS:
        raise ProtocolError(
            f"unknown autorater prompt version "
            f"{config['prompt_version']!r}")
    get_model(config["judge_model_key"])       # must be registered
    config["config_hash"] = sha_obj(
        {k: v for k, v in config.items() if k != "config_hash"})
    config["prompt_hash"] = sha_text(
        C.AUTORATER_PROMPTS[config["prompt_version"]])
    return config


# ------------------------------------------------------------------ split
def make_split(pool: list[dict[str, Any]], *, model_id: str
               ) -> dict[str, Any]:
    """Deterministic, disjoint, class-stratified halves of the response
    pool. Development first, calibration second, per class."""
    ids = [item["item_id"] for item in pool]
    if len(set(ids)) != len(ids):
        raise ProtocolError("duplicate item ids in the response pool")
    split: dict[str, list[str]] = {"development": [], "calibration": []}
    for cls in ("pass", "fail"):
        members = sorted(i["item_id"] for i in pool
                         if i["verifier_class"] == cls)
        rng = random.Random(domain_int(
            C.DOMAIN_AUTORATER_SPLIT, C.AUTORATER_SPLIT_SEED, model_id,
            cls))
        rng.shuffle(members)
        half = len(members) // 2
        split["development"].extend(sorted(members[:half]))
        split["calibration"].extend(sorted(members[half:]))
    if set(split["development"]) & set(split["calibration"]):
        raise ProtocolError("split halves are not disjoint")
    return {"seed": C.AUTORATER_SPLIT_SEED,
            "domain": C.DOMAIN_AUTORATER_SPLIT, "model_id": model_id,
            "pool_items": len(pool), **split,
            "split_hash": sha_obj(split)}


# ------------------------------------------------------------- judgments
def judge_prompt(config: dict[str, Any], item: dict[str, Any]) -> str:
    template = C.AUTORATER_PROMPTS[config["prompt_version"]]
    return template.format(constraint=item["constraint_text"],
                           response=item["response_text"])


def parse_judgment(raw: str) -> tuple[str, str | None, str | None]:
    """(status, label, justification). Labels are only pass/fail; every
    other outcome keeps its own status and is never recoded."""
    text = raw.strip()
    if not text:
        return INVALID_OUTPUT, None, None
    first, _, rest = text.partition("\n")
    token = "".join(ch for ch in first.strip().upper()
                    if ch.isalpha())
    if token.startswith("YES"):
        return VALID, "pass", rest.strip() or None
    if token.startswith("NO"):
        return VALID, "fail", rest.strip() or None
    from dci1v3.analysis.taxonomy import is_refusal
    if is_refusal(text):
        return REFUSAL, None, None
    return INVALID_OUTPUT, None, None


def run_autorater(phase_dir: Path, items: list[dict[str, Any]], *,
                  config: dict[str, Any], phase: str, generate_fn,
                  environment: dict[str, Any]) -> list[dict[str, Any]]:
    """Judge every item once; append-once storage; full provenance."""
    phase_dir = Path(phase_dir)
    phase_dir.mkdir(parents=True, exist_ok=True)
    judge = get_model(config["judge_model_key"])
    run_id = sha_obj({"config": config["config_hash"], "phase": phase,
                      "items": sorted(i["item_id"] for i in items)})[:16]

    from dci1v3.generation.plans import backend_plan
    plan = backend_plan(judge, cap=C.AUTORATER_CAP, decoding="greedy")

    writer = CacheWriter(phase_dir / "judge_rows.jsonl")
    have = writer.existing_ids()
    missing = [i for i in items if f"judge:{i['item_id']}" not in have]
    if missing:
        design_rows = []
        for item in sorted(missing, key=lambda i: i["item_id"]):
            prompt = judge_prompt(config, item)
            design_rows.append({
                "row_id": f"judge:{item['item_id']}",
                "user_prompt": prompt,
                "scientific_seed": domain_int(
                    C.DOMAIN_AUTORATER_SEED, C.AUTORATER_SPLIT_SEED,
                    judge.model_id, sha_text(prompt)),
                "item_id": item["item_id"],
                "prompt_hash": sha_text(prompt)})
        outcome = generate_fn(phase_dir / "backend_runs", plan, design_rows)
        by_id = {row["row_id"]: row for row in outcome["rows"]}
        writer.append([
            {"row_id": design["row_id"],
             "item_id": design["item_id"],
             "prompt_hash": design["prompt_hash"],
             "raw_generation": by_id.get(design["row_id"], {}).get(
                 "raw_generation", ""),
             "finish_reason": by_id.get(design["row_id"], {}).get(
                 "finish_reason", ""),
             "outcome": by_id.get(design["row_id"], {}).get(
                 "outcome", "MISSING")}
            for design in design_rows])

    raw_rows = {row["item_id"]: row for row in writer.rows()}
    judgments = []
    for item in items:
        raw = raw_rows.get(item["item_id"])
        if raw is None or raw["outcome"] != "OK":
            status, label, justification = GENERATION_FAILURE, None, None
            raw_text = "" if raw is None else raw["raw_generation"]
        else:
            raw_text = raw["raw_generation"]
            status, label, justification = parse_judgment(raw_text)
        judgments.append({
            "schema_version": C.AUTORATER_SCHEMA_VERSION,
            "run_id": run_id, "phase": phase,
            "item_id": item["item_id"],
            "response_hash": item["response_hash"],
            "judge_model_key": judge.model_key,
            "judge_model_id": judge.model_id,
            "judge_revision": judge.revision,
            "backend": environment.get("backend",
                                       {"kind": "vllm-subprocess"}),
            "prompt_version": config["prompt_version"],
            "prompt_hash": config["prompt_hash"],
            "decoding": config["decoding"],
            "config_hash": config["config_hash"],
            "status": status, "label": label,
            "justification": justification,
            "verifier_label": item["verifier_class"],
        })
    path = phase_dir / "judgments.jsonl"
    fs.atomic_write_text(path, "".join(
        json.dumps(j, sort_keys=True, ensure_ascii=False) + "\n"
        for j in judgments))
    return judgments


# --------------------------------------------------------------- reports
def judgment_report(judgments: list[dict[str, Any]]) -> dict[str, Any]:
    """Coverage, marginals, disagreement, and the 2x2 contingency table.
    No threshold and no acceptance decision live here."""
    total = len(judgments)
    by_status = {status: sum(1 for j in judgments
                             if j["status"] == status)
                 for status in STATUSES}
    valid = [j for j in judgments if j["status"] == VALID]
    table = {"verifier_pass_autorater_pass": 0,
             "verifier_pass_autorater_fail": 0,
             "verifier_fail_autorater_pass": 0,
             "verifier_fail_autorater_fail": 0}
    for j in valid:
        key = (f"verifier_{j['verifier_label']}"
               f"_autorater_{j['label']}")
        table[key] += 1
    disagreements = (table["verifier_pass_autorater_fail"]
                     + table["verifier_fail_autorater_pass"])
    return {
        "items": total,
        "valid": len(valid),
        "invalid": {k: v for k, v in by_status.items() if k != VALID},
        "coverage": len(valid) / total if total else None,
        "verifier_marginal": {
            "pass": sum(1 for j in judgments
                        if j["verifier_label"] == "pass"),
            "fail": sum(1 for j in judgments
                        if j["verifier_label"] == "fail")},
        "autorater_marginal": {
            "pass": sum(1 for j in valid if j["label"] == "pass"),
            "fail": sum(1 for j in valid if j["label"] == "fail")},
        "contingency": table,
        "disagreements": disagreements,
        "directional_disagreement": {
            "verifier_pass_autorater_fail":
                table["verifier_pass_autorater_fail"],
            "verifier_fail_autorater_pass":
                table["verifier_fail_autorater_pass"]},
        "disagreement_rate": (disagreements / len(valid)
                              if valid else None),
        "not_human_validation": True,
    }


def disagreement_listing(items_by_id: dict[str, dict[str, Any]],
                         judgments: list[dict[str, Any]],
                         *, limit: int = 200) -> list[dict[str, Any]]:
    """Inspection material for the development phase."""
    listing = []
    for j in judgments:
        if j["status"] == VALID and j["label"] != j["verifier_label"]:
            item = items_by_id[j["item_id"]]
            listing.append({
                "item_id": j["item_id"],
                "verifier": j["verifier_label"],
                "autorater": j["label"],
                "justification": j["justification"],
                "constraint_text": item["constraint_text"],
                "response_excerpt": item["response_text"][:400]})
    return listing[:limit]


# --------------------------------------------------- verifier freeze check
def verifier_source_state() -> dict[str, str]:
    """Behaviorally relevant verifier code, hashed for the freeze
    manifest and for the change check before calibration/approval."""
    from dci1v3.verifiers import source_hashes
    from dci1v3.protocol.hashing import sha_file
    root = Path(__file__).resolve().parents[1] / "verifiers"
    hashes = dict(source_hashes())
    hashes["reimplementation.py"] = sha_file(root / "reimplementation.py")
    return hashes


def assert_verifier_unchanged(manifest_payload: dict[str, Any]) -> None:
    current = verifier_source_state()
    frozen = manifest_payload["verifier_sources"]
    changed = sorted(name for name in set(current) | set(frozen)
                     if current.get(name) != frozen.get(name))
    if changed:
        raise IntegrityError(
            f"behaviorally relevant verifier code changed since the "
            f"verifier freeze: {changed}; calibration evidence produced "
            f"before this change is contaminated and a fresh held-out "
            f"split is required before independent calibration can be "
            f"claimed again")
