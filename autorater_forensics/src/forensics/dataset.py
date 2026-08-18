"""Build the diagnostic dataset from frozen registered evidence,
READ-ONLY.

Sources (per model replication):
  * the frozen response pool: pre-screen target-solo rows + Gate 1
    validation rows (the same reservoir the registered Gate 1 uses);
  * the three registered development rounds' judgments (low round 1,
    medium round 2 parked supersessions; high round 3 active), giving
    per-item labels/statuses under every reasoning effort WITHOUT any
    new inference.

Development-half items only — held-out calibration items are never
included, so this diagnostic cannot expose or re-expose calibration
data.

Two components, explicitly separated by the ``contested`` flag:
  contested — the three rounds' valid labels differ, or any valid label
              disagrees with the deterministic verifier, or any round
              recorded a non-valid status (invalid/refusal/failure —
              preserved, never dropped);
  control   — all three rounds valid and agreeing with each other and
              the verifier; stratified one per
              (model, n, verifier class) by sorted item id.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import paths
from .verifier import s0_count

#: The registered judge prompt, byte-identical to gate1-judge/2.0.0 in
#: dci1v3/protocol/constants.py (asserted by tests). Copied so this
#: environment never imports the scientific package.
JUDGE_PROMPT = (
    "You are checking one rule against one text.\n"
    "Rule: {constraint}\n"
    "Text:\n{response}\n"
    "---\n"
    "Does the text satisfy the rule? Answer with exactly one word on "
    "the first line: SATISFIES or VIOLATES. You may add one short "
    "reason on the second line.\n"
    "Answer:")


def wording(n: int) -> str:
    return (f"Use the word however exactly {n} "
            f"{'time' if n == 1 else 'times'}.")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in
            path.read_text().splitlines() if line.strip()]


def pool_items(model_key: str) -> dict[str, dict[str, Any]]:
    """The frozen response pool for one model, keyed by item id."""
    tree = paths.EVIDENCE / model_key
    items: dict[str, dict[str, Any]] = {}
    for rel, source in (("prescreen/full/cache.jsonl", "prescreen"),
                        ("gate1/validation/cache.jsonl", "validation")):
        for row in _read_jsonl(tree / rel):
            if source == "prescreen" and row.get("constraint_id") \
                    is not None:
                continue
            items[row["row_id"]] = {
                "response_text": row["raw_response"],
                "n": row["n"], "source_pool": source,
                "registered_s0": row["verdicts"]["s0"]}
    return items


def round_judgments(model_key: str) -> dict[str, dict[str, Any]]:
    """{effort: {item_id: judgment}} for the three registered rounds."""
    tree = paths.EVIDENCE / model_key
    return {effort: {j["item_id"]: j
                     for j in _read_jsonl(tree / rel)}
            for effort, rel in paths.ROUND_JUDGMENTS.items()}


def build(out_path: Path | None = None) -> dict[str, Any]:
    out_path = out_path or (paths.DATASET / "diagnostic.jsonl")
    samples: list[dict[str, Any]] = []
    counts = {"contested": 0, "control": 0}
    for model_key in paths.MODEL_KEYS:
        pool = pool_items(model_key)
        rounds = round_judgments(model_key)
        dev_ids = sorted(rounds["high"])        # the development half
        controls_by_stratum: dict[tuple, str] = {}
        for item_id in dev_ids:
            item = pool[item_id]
            per = {e: rounds[e][item_id] for e in
                   ("low", "medium", "high")}
            s0 = s0_count(item["response_text"])
            assert s0 == item["registered_s0"], item_id
            verifier = "pass" if s0 == item["n"] else "fail"
            labels = {e: per[e]["label"] for e in per}
            statuses = {e: per[e]["status"] for e in per}
            valid_labels = {v for v in labels.values() if v is not None}
            reasons = []
            if len(valid_labels) > 1:
                reasons.append("labels_differ_across_efforts")
            if any(v is not None and v != verifier
                   for v in labels.values()):
                reasons.append("disagrees_with_verifier")
            if any(s != "valid" for s in statuses.values()):
                reasons.append("non_valid_status")
            sample = {
                "id": f"{model_key}::{item_id}",
                "input": JUDGE_PROMPT.format(
                    constraint=wording(item["n"]),
                    response=item["response_text"]),
                "target": ("SATISFIES" if verifier == "pass"
                           else "VIOLATES"),
                # metadata fields are TOP-LEVEL so Inspect's FieldSpec
                # can select them by name
                **{
                    "item_id": item_id,
                    "source_model": model_key,
                    "source_pool": item["source_pool"],
                    "constraint_text": wording(item["n"]),
                    "response_text": item["response_text"],
                    "target_n": item["n"],
                    "s0_count": s0,
                    "deterministic_verifier_label": verifier,
                    "split_class": per["high"]["split_class"],
                    "response_chars": len(item["response_text"]),
                    "response_words": len(item["response_text"].split()),
                    "prior_low_label": labels["low"],
                    "prior_low_status": statuses["low"],
                    "prior_medium_label": labels["medium"],
                    "prior_medium_status": statuses["medium"],
                    "prior_high_label": labels["high"],
                    "prior_high_status": statuses["high"],
                    "contested": bool(reasons),
                    "contested_reasons": reasons,
                },
            }
            if reasons:
                counts["contested"] += 1
                samples.append(sample)
            else:
                stratum = (model_key, item["n"], verifier)
                if stratum not in controls_by_stratum:
                    controls_by_stratum[stratum] = item_id
                    counts["control"] += 1
                    samples.append(sample)
    samples.sort(key=lambda s: s["id"])           # fixed request order
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(
        json.dumps(s, ensure_ascii=False) + "\n" for s in samples))
    return {"path": str(out_path), "samples": len(samples), **counts}


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
