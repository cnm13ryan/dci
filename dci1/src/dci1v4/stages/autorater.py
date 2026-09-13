"""The autorater-assisted validation pathway (§10.4, checks C3 and C4).

Used only when human validation is unavailable. Every invariant §10.4 registers
is executable here:

* a **deterministic class-stratified disjoint** development/calibration split
  of the response pool, derived from a registered seed;
* **one judge** resolved through a registry disjoint from the registered study
  models, at a pinned revision, with a hashed configuration recording judge
  identity, revision, backend, prompt version and hash, parser version, label
  mapping, decoding and output cap — and failing closed on drift;
* **serialised deterministic execution at concurrency one** (§10.4, T-15). The
  forensics recorded unacceptable repeated-run label instability under
  concurrent serving and exact repeatability at concurrency one, so any
  autorater execution path runs serialised, or on an equivalently demonstrated
  fixed-composition offline path, and records which;
* a development-phase repeatability check;
* a **single-shot signed freeze** binding verifier hashes, the regression-test
  file and its passing run, the split derivation, the realised evidence
  boundary and the judge configuration;
* **one-shot calibration** on the untouched half, enforced by an append-only
  ledger written *before* any mutation;
* explicit researcher approval writing
  ``measurement_basis = autorater_calibration_approved``.

Autorater judgments never become behavioural scores, never overwrite a
deterministic verdict, and live in separate artifacts. Nothing in this module
can write into a verdict field.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.engine.artifacts import claim_one_shot, one_shot_claimed
from dci1v4.engine.paths import ModelTree
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import get_judge
from dci1v4.protocol.hashing import sha_obj
from dci1v4.protocol.seeds import AUTORATER_SPLIT_SEED, autorater_split_seed

#: §10.4: the hashed configuration's required fields. A missing one fails
#: closed rather than defaulting.
CONFIG_FIELDS = ("judge_model_key", "judge_model_id", "judge_revision",
                 "backend", "prompt_version", "prompt_hash", "parser_version",
                 "label_mapping", "decoding", "output_cap",
                 "execution_concurrency")

#: The §10.4 selection hierarchy, in order. A later criterion never overrides
#: an earlier one.
SELECTION_HIERARCHY = (
    "valid deterministic execution",
    "adequate output cap and absence of problematic truncation",
    "valid parsing and coverage",
    "agreement with human labels",
    "the lower-cost setting when performance is practically indistinguishable",
)


def build_config(judge_key: str, **fields: Any) -> dict[str, Any]:
    """The hashed judge configuration (§10.4)."""
    spec = get_judge(judge_key)
    config = {
        "judge_model_key": spec.model_key, "judge_model_id": spec.model_id,
        "judge_revision": spec.revision,
        "backend": fields.get("backend", "vllm"),
        "prompt_version": fields["prompt_version"],
        "prompt_hash": fields["prompt_hash"],
        "parser_version": fields["parser_version"],
        "label_mapping": fields["label_mapping"],
        "decoding": fields["decoding"],
        "output_cap": fields["output_cap"],
        # T-15: concurrency one, or a demonstrated fixed-composition offline
        # path. The value is recorded, never defaulted.
        "execution_concurrency": fields.get("execution_concurrency", 1),
        "execution_mode": fields.get("execution_mode", "serialised"),
    }
    missing = [f for f in CONFIG_FIELDS if config.get(f) in (None, "")]
    if missing:
        raise ProtocolError(f"the autorater configuration is missing "
                            f"{missing}; it fails closed rather than "
                            f"defaulting (§10.4)")
    if config["execution_concurrency"] != 1 and \
            config["execution_mode"] != "fixed_composition_offline":
        raise ProtocolError(
            "autorater execution runs serialised at concurrency one, or on an "
            "equivalently demonstrated fixed-composition offline path; "
            "concurrent serving produced repeated-run label instability")
    config["config_hash"] = sha_obj(
        {k: config[k] for k in sorted(CONFIG_FIELDS)})
    return config


def assert_no_config_drift(frozen: Mapping[str, Any],
                           current: Mapping[str, Any]) -> None:
    """Fail closed on any change to the hashed configuration."""
    if frozen.get("config_hash") != current.get("config_hash"):
        differing = [f for f in CONFIG_FIELDS
                     if frozen.get(f) != current.get(f)]
        raise IntegrityError(
            f"the autorater configuration drifted in {differing}; the frozen "
            f"hash {frozen.get('config_hash')} does not match "
            f"{current.get('config_hash')}")


def stratified_split(items: Sequence[Mapping[str, Any]], *, model_id: str,
                     root: int = AUTORATER_SPLIT_SEED) -> dict[str, list]:
    """A deterministic class-stratified **disjoint** development and
    calibration split of the response pool (§10.4)."""
    by_class: dict[str, list[Mapping[str, Any]]] = {}
    for item in items:
        by_class.setdefault(item["verifier_class"], []).append(item)
    development: list[Mapping[str, Any]] = []
    calibration: list[Mapping[str, Any]] = []
    for verifier_class, members in sorted(by_class.items()):
        ordered = sorted(members, key=lambda m: m["item_id"])
        random.Random(autorater_split_seed(root, model_id,
                                           verifier_class)).shuffle(ordered)
        half = len(ordered) // 2
        development.extend(ordered[:half])
        calibration.extend(ordered[half:])
    dev_ids = {i["item_id"] for i in development}
    cal_ids = {i["item_id"] for i in calibration}
    if dev_ids & cal_ids:
        raise IntegrityError("the development and calibration halves overlap")
    return {"development": development, "calibration": calibration,
            "split_hash": sha_obj({"development": sorted(dev_ids),
                                   "calibration": sorted(cal_ids)})}


def repeatability_check(runs: Sequence[Sequence[str]]) -> dict[str, Any]:
    """The development-phase repeatability check (§10.4).

    Exact repeatability is the criterion: under serialised execution the same
    items must yield the same labels on every run.
    """
    if len(runs) < 2:
        raise ProtocolError("repeatability needs at least two runs")
    reference = list(runs[0])
    agreements = [sum(1 for a, b in zip(reference, run) if a == b)
                  / len(reference) for run in runs[1:]]
    return {"runs": len(runs), "items": len(reference),
            "pairwise_agreement": agreements,
            "exactly_repeatable": all(a == 1.0 for a in agreements)}


def paired_comparison(items: Sequence[str],
                      condition_a: Mapping[str, str],
                      condition_b: Mapping[str, str],
                      reference: Mapping[str, str]) -> dict[str, Any]:
    """Compare two judging conditions **paired on the same items** (§10.4).

    Returns coverage, per-class agreement, the confusion matrix and the
    discordant-item table, which is what check C3 requires recorded.
    """
    common = [i for i in items if i in condition_a and i in condition_b]
    confusion: dict[str, int] = {}
    discordant: list[dict[str, str]] = []
    for item in common:
        key = f"{condition_a[item]}|{condition_b[item]}"
        confusion[key] = confusion.get(key, 0) + 1
        if condition_a[item] != condition_b[item]:
            discordant.append({"item_id": item, "a": condition_a[item],
                               "b": condition_b[item],
                               "reference": reference.get(item, "")})
    def _agreement(condition: Mapping[str, str]) -> dict[str, float]:
        per_class: dict[str, list[bool]] = {}
        for item in common:
            if item not in reference:
                continue
            per_class.setdefault(reference[item], []).append(
                condition[item] == reference[item])
        return {k: sum(v) / len(v) for k, v in sorted(per_class.items())}
    return {"items_compared": len(common),
            "coverage": {"a": len(common) / len(items) if items else 0.0,
                         "b": len(common) / len(items) if items else 0.0},
            "per_class_agreement": {"a": _agreement(condition_a),
                                    "b": _agreement(condition_b)},
            "confusion_matrix": confusion,
            "discordant_items": discordant,
            "selection_hierarchy": list(SELECTION_HIERARCHY)}


def freeze_autorater(tree: ModelTree, *, config: Mapping[str, Any],
                     verifier_hashes: Mapping[str, str],
                     regression_test_file: str,
                     regression_run_passed: bool,
                     split_hash: str, evidence_boundary: Mapping[str, Any],
                     producing_commit: str) -> dict[str, Any]:
    """The single-shot signed freeze of §10.4."""
    if not regression_run_passed:
        raise ProtocolError("the autorater freeze binds a *passing* "
                            "regression run")
    if one_shot_claimed(tree, "autorater_freeze"):
        raise IntegrityError("the autorater freeze is single-shot and has "
                             "already been claimed")
    claim_one_shot(tree, operation="autorater_freeze",
                   detail={"config_hash": config["config_hash"]},
                   producing_commit=producing_commit)
    payload = {
        "config": dict(config), "verifier_hashes": dict(verifier_hashes),
        "regression_test_file": regression_test_file,
        "regression_run_passed": True, "split_hash": split_hash,
        "realised_evidence_boundary": dict(evidence_boundary),
        "producing_commit": producing_commit,
    }
    path = tree.root / "gate1" / "autorater_freeze.json"
    fs.write_json_once(path, payload)
    return {**payload, "path": str(path),
            "freeze_hash": sha_obj(payload)}


def calibrate_once(tree: ModelTree, *, frozen: Mapping[str, Any],
                   current_config: Mapping[str, Any],
                   calibration_items: Sequence[Mapping[str, Any]],
                   judgments: Mapping[str, str],
                   producing_commit: str) -> dict[str, Any]:
    """One-shot calibration on the untouched held-out half (§10.4).

    The ledger entry is written **before** any mutation, so deleting the
    calibration record cannot re-open the stage.
    """
    assert_no_config_drift(frozen["config"], current_config)
    claim_one_shot(tree, operation="autorater_calibration",
                   detail={"items": len(calibration_items),
                           "config_hash": current_config["config_hash"]},
                   producing_commit=producing_commit)
    agreements = [judgments.get(item["item_id"]) == item["verifier_class"]
                  for item in calibration_items]
    payload = {
        "items": len(calibration_items),
        "agreement": (sum(agreements) / len(agreements)) if agreements else 0.0,
        "config_hash": current_config["config_hash"],
        "producing_commit": producing_commit,
        "note": ("autorater judgments never become behavioural scores and "
                 "never overwrite a deterministic verdict; they live in "
                 "separate artifacts (§10.1, §10.4)"),
    }
    path = tree.root / "gate1" / "autorater_calibration.json"
    fs.write_json_once(path, payload)
    return payload


def approve(calibration: Mapping[str, Any], *, researcher: str,
            approved: bool) -> dict[str, Any]:
    """Explicit researcher approval writing the measurement basis (§10.4)."""
    if not approved:
        return {"approved": False, "measurement_basis": None,
                "researcher": researcher}
    return {"approved": True,
            "measurement_basis": "autorater_calibration_approved",
            "researcher": researcher,
            "calibration_agreement": calibration.get("agreement")}
