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
from dci1v3.models.registry import get_judge
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
    """The frozen autorater protocol: judge identity and pinned revision,
    backend, prompt version, parser version, binary label mapping, and
    greedy decoding — all covered by config_hash, all recorded with every
    judgment. Fails closed on any drift from the registered constants."""
    config = fs.read_json(path or _CONFIG_PATH)
    for key in ("schema_version", "judge_model_key", "judge_model_id",
                "judge_revision", "backend", "prompt_version",
                "parser_version", "label_mapping", "decoding"):
        if key not in config:
            raise ProtocolError(f"autorater config missing {key!r}")
    if config["prompt_version"] not in C.AUTORATER_PROMPTS:
        raise ProtocolError(
            f"unknown autorater prompt version "
            f"{config['prompt_version']!r}")
    if config["parser_version"] != C.AUTORATER_PARSER_VERSION:
        raise ProtocolError(
            f"autorater config names parser {config['parser_version']!r} "
            f"but this code implements {C.AUTORATER_PARSER_VERSION!r}")
    if config["label_mapping"] != C.AUTORATER_LABEL_MAPPING:
        raise ProtocolError(
            "autorater config's binary label mapping differs from the "
            "registered SATISFIES/VIOLATES mapping")
    judge = get_judge(config["judge_model_key"])
    if (config["judge_model_id"], config["judge_revision"]) != \
            (judge.model_id, judge.revision):
        raise ProtocolError(
            f"autorater config pins {config['judge_model_id']}@"
            f"{config['judge_revision'][:12]} but the judge registry pins "
            f"{judge.model_id}@{judge.revision[:12]}")
    if int(config["decoding"]["max_new_tokens"]) != C.AUTORATER_CAP:
        raise ProtocolError(
            f"autorater config cap {config['decoding']['max_new_tokens']} "
            f"differs from the registered AUTORATER_CAP {C.AUTORATER_CAP}")
    if config["decoding"]["policy"] != "greedy":
        raise ProtocolError("the registered autorater decoding is greedy")
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


#: Harmony channel markers (gpt-oss). The judge's transcript interleaves
#: an analysis channel and a final channel, separated only by special
#: tokens; the parser reads ONLY the final channel. A transcript that
#: never reaches its final channel (e.g. truncated at the cap) is
#: invalid_output, never a label.
_HARMONY_FINAL = "<|channel|>final<|message|>"
_HARMONY_STOPS = ("<|return|>", "<|end|>", "<|call|>")


def parse_judgment(raw: str) -> tuple[str, str | None, str | None]:
    """(status, label, justification) — parser gate1-parse/2.0.0.

    The registered vocabulary is SATISFIES/VIOLATES on the first line of
    the judge's final message, mapped by AUTORATER_LABEL_MAPPING; every
    other outcome keeps its own operational status and is never recoded
    into a label."""
    text = raw.strip()
    if not text:
        return INVALID_OUTPUT, None, None
    if "<|channel|>" in text:                  # a harmony transcript
        if _HARMONY_FINAL not in text:
            return INVALID_OUTPUT, None, None  # never reached its verdict
        text = text.rsplit(_HARMONY_FINAL, 1)[1]
        for stop in _HARMONY_STOPS:
            text = text.split(stop, 1)[0]
        text = text.strip()
        if not text:
            return INVALID_OUTPUT, None, None
    first, _, rest = text.partition("\n")
    token = "".join(ch for ch in first.strip().upper()
                    if ch.isalpha())
    if token.startswith("SATISF"):
        return VALID, C.AUTORATER_LABEL_MAPPING["SATISFIES"], \
            rest.strip() or None
    if token.startswith("VIOLAT"):
        return VALID, C.AUTORATER_LABEL_MAPPING["VIOLATES"], \
            rest.strip() or None
    from dci1v3.analysis.taxonomy import is_refusal
    if is_refusal(text):
        return REFUSAL, None, None
    return INVALID_OUTPUT, None, None


def run_autorater(phase_dir: Path, items: list[dict[str, Any]], *,
                  config: dict[str, Any], phase: str, generate_fn,
                  environment: dict[str, Any]) -> list[dict[str, Any]]:
    """Judge every item once; append-once storage; full provenance.

    Only successful judge generations are committed, so a transient
    backend failure is retried on the next run (a still-missing row is
    reported as ``generation_failure``, never recoded). Each generation
    attempt keeps its own raw run directory. The comparison label is the
    CURRENT verifier's live verdict — the development loop exists to
    refine the verifier, so judgments must track it — while the
    development/calibration split stays stratified on the frozen
    generation-time classes (split stability across refinement).
    """
    from dci1v3.verifiers.target import s0_count

    phase_dir = Path(phase_dir)
    phase_dir.mkdir(parents=True, exist_ok=True)
    judge = get_judge(config["judge_model_key"])
    run_id = sha_obj({"config": config["config_hash"], "phase": phase,
                      "items": sorted(i["item_id"] for i in items)})[:16]

    from dci1v3.generation.plans import backend_plan
    plan = backend_plan(
        judge, cap=C.AUTORATER_CAP, decoding="greedy",
        skip_special_tokens=bool(
            config["decoding"].get("skip_special_tokens", True)))

    writer = CacheWriter(phase_dir / "judge_rows.jsonl")
    # Cached judgments are reusable ONLY while their provenance is valid:
    # every stored row must have been produced under this exact autorater
    # configuration and this exact rendered prompt.
    for row in writer.rows():
        item = next((i for i in items
                     if f"judge:{i['item_id']}" == row["row_id"]), None)
        if row.get("config_hash") != config["config_hash"] or (
                item is not None and
                row["prompt_hash"] != sha_text(judge_prompt(config, item))):
            raise IntegrityError(
                f"cached judge row {row['row_id']!r} in {phase_dir} was "
                f"produced under a different autorater configuration or "
                f"prompt; stale judgments cannot be reused — resolving "
                f"this requires an audited decision about the phase "
                f"directory, never silent regeneration")
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
        attempt = 0
        while (phase_dir / "backend_runs" / f"attempt{attempt}").exists():
            attempt += 1
        run_dir = phase_dir / "backend_runs" / f"attempt{attempt}"
        run_dir.mkdir(parents=True, exist_ok=True)
        outcome = generate_fn(run_dir, plan, design_rows)
        by_id = {row["row_id"]: row for row in outcome["rows"]}
        writer.append([
            {"row_id": design["row_id"],
             "item_id": design["item_id"],
             "prompt_hash": design["prompt_hash"],
             "config_hash": config["config_hash"],
             "raw_generation": by_id[design["row_id"]]["raw_generation"],
             "finish_reason": by_id[design["row_id"]].get(
                 "finish_reason", ""),
             "outcome": "OK"}
            for design in design_rows
            if by_id.get(design["row_id"], {}).get("outcome") == "OK"])

    raw_rows = {row["item_id"]: row for row in writer.rows()}
    judgments = []
    for item in items:
        live_verifier = ("pass" if s0_count(item["response_text"])
                         == item["n"] else "fail")
        raw = raw_rows.get(item["item_id"])
        if raw is None:
            status, label, justification = GENERATION_FAILURE, None, None
        else:
            status, label, justification = parse_judgment(
                raw["raw_generation"])
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
            "verifier_label": live_verifier,
            "split_class": item["verifier_class"],   # frozen stratum
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
        # The full-set identification interval [a/N, (a+(N-N_v))/N]: the
        # agreement rate is only interval-identified when some judgments
        # are invalid. Not an acceptance threshold; nothing decides on it.
        "agreement_identification_interval": (
            {"agree_valid": len(valid) - disagreements,
             "lower": (len(valid) - disagreements) / total,
             "upper": (len(valid) - disagreements + total - len(valid))
                      / total}
            if total else None),
        "label_mapping": dict(C.AUTORATER_LABEL_MAPPING),
        "not_human_validation": True,
    }


def disagreement_listing(items_by_id: dict[str, dict[str, Any]],
                         judgments: list[dict[str, Any]]
                         ) -> list[dict[str, Any]]:
    """EVERY disagreement, complete: item identity, constraint, the full
    response, both labels, the judge's short justification, and the
    frozen split stratum. Inspection material — never truncated."""
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
                "response_text": item["response_text"],
                "n": item.get("n"),
                "source": item.get("source"),
                "split_class": j.get("split_class")})
    return listing


def disagreement_breakdown(items_by_id: dict[str, dict[str, Any]],
                           judgments: list[dict[str, Any]]
                           ) -> dict[str, dict[str, int]]:
    """Descriptive disagreement concentrations by target severity ``n``
    and by source pool. Counts only; no threshold reads them."""
    by_n: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for j in judgments:
        if j["status"] == VALID and j["label"] != j["verifier_label"]:
            item = items_by_id[j["item_id"]]
            n = str(item.get("n"))
            source = str(item.get("source"))
            by_n[n] = by_n.get(n, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
    return {"by_n": dict(sorted(by_n.items())),
            "by_source": dict(sorted(by_source.items()))}


def stability_comparison(primary: list[dict[str, Any]],
                         repeat: list[dict[str, Any]]
                         ) -> dict[str, Any]:
    """Development-only repeated-run check: the identical prompt, model,
    decoding, and configuration judged twice. Reports label flips and
    operational-status changes with the affected item IDs. The repeated
    labels are never averaged and never voted; the primary run remains
    the development evidence. Unexpected variation under greedy decoding
    means model/backend reproducibility needs investigation before the
    verifier freeze."""
    second = {j["item_id"]: j for j in repeat}
    label_flips, status_changes = [], []
    for j in primary:
        twin = second.get(j["item_id"])
        if twin is None:
            status_changes.append({"item_id": j["item_id"],
                                   "first": j["status"],
                                   "second": "missing"})
            continue
        if j["status"] != twin["status"]:
            status_changes.append({"item_id": j["item_id"],
                                   "first": j["status"],
                                   "second": twin["status"]})
        elif j["status"] == VALID and j["label"] != twin["label"]:
            label_flips.append({"item_id": j["item_id"],
                                "first": j["label"],
                                "second": twin["label"]})
    return {"items": len(primary),
            "label_flips": len(label_flips),
            "status_changes": len(status_changes),
            "flipped_items": label_flips,
            "status_changed_items": status_changes,
            "stable": not label_flips and not status_changes}


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
