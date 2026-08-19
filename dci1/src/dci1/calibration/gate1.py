"""Gate 1 — measurement (prereg §10, §18), per model.

Executable now: the forty-case boundary suite, the three-process determinism
test over every calibration response, the item-behaviour tabulation, and the
structural discriminant-validity checks. Requiring humans (decision D25,
PENDING_HUMAN): the 150-response blinded agreement test, face validity, and
their derived numbers. Gate 1 cannot pass until the human labels exist; the
packet builder and evaluator are complete so labelling can start immediately.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from dci1.calibration.gate2 import parse_solo_arm
from dci1.constraints.wordings import wording
from dci1.protocol.constants import ProtocolError
from dci1.verifiers.boundary_suite import evaluate_suite
from dci1.verifiers.registry import assert_blindness

#: max human/verifier disagreements per 75-case truth class (§18).
MAX_DISAGREEMENTS = 2
SAMPLE_PER_CLASS = 75

_DETERMINISM_SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[3])
from dci1.constraints.definitions import CANDIDATE_IDS, added_verifier
from dci1.verifiers import target
rows = json.loads(open(sys.argv[1]).read())
out = []
for text in rows:
    verdicts = {"s0": target.s0_count(text), "s1": target.s1_count(text),
                "s2": target.s2_count(text)}
    for cid in CANDIDATE_IDS:
        verdicts[cid] = added_verifier(cid)(text)
    for m in (7, 8, 9, 10):
        verdicts[f"B{m}"] = added_verifier("B", m)(text)
    out.append(verdicts)
open(sys.argv[2], "w").write(json.dumps(out, sort_keys=True))
"""


def determinism_test(responses: list[str]) -> dict[str, Any]:
    """Every verifier, three executions on three separate processes (§10).

    Agreement is the proportion of responses receiving identical verdicts
    across all three executions; the gate requires exactly 1.000.
    """
    src_root = str(Path(__file__).resolve().parents[2])
    with tempfile.TemporaryDirectory() as tmp:
        in_path = Path(tmp) / "responses.json"
        in_path.write_text(json.dumps(responses))
        blobs = []
        for i in range(3):
            out_path = Path(tmp) / f"verdicts_{i}.json"
            completed = subprocess.run(
                [sys.executable, "-c", _DETERMINISM_SCRIPT, str(in_path),
                 str(out_path), src_root],
                capture_output=True, text=True)
            if completed.returncode != 0:
                raise ProtocolError(
                    f"determinism process {i} failed: {completed.stderr[:300]}")
            blobs.append(json.loads(out_path.read_text()))
    identical = sum(1 for triple in zip(*blobs)
                    if triple[0] == triple[1] == triple[2])
    agreement = identical / len(responses) if responses else 1.0
    return {"responses": len(responses), "agreement": agreement,
            "required": 1.0, "passed": agreement == 1.0}


def item_behaviour(per_topic_target: dict[str, dict[int, int]]) -> dict:
    """Target failure tabulated by topic over the A-solo calibration prompts:
    floor (fails every n), ceiling (passes every n), identical verdicts."""
    floor = ceiling = identical = 0
    for verdicts in per_topic_target.values():
        values = list(verdicts.values())
        if all(v == 1 for v in values):
            floor += 1
        if all(v == 0 for v in values):
            ceiling += 1
        if len(set(values)) == 1:
            identical += 1
    n = len(per_topic_target) or 1
    return {"topics": len(per_topic_target), "floor_share": floor / n,
            "ceiling_share": ceiling / n, "identical_share": identical / n}


def wilson_upper(successes: int, trials: int, z: float = 1.96) -> float:
    if trials == 0:
        return float("nan")
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = p + z * z / (2 * trials)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials)
    return (centre + margin) / denominator


def build_annotation_packet(calibration_rows: list[dict[str, Any]],
                            out_dir: Path, model_key: str) -> dict[str, Any]:
    """The blinded 150-response human-agreement packet (§10, §25).

    75 responses S0 passed / 75 S0 failed, drawn deterministically from the
    A-solo calibration responses. Annotators see the response text and the
    target constraint text only — no arm, no added constraint.
    """
    from dci1.calibration.gate2 import solo_failure

    passed, failed = [], []
    for row in calibration_rows:
        condition = parse_solo_arm(row["arm"])
        if condition["constraint_id"] != "A":
            continue
        f = solo_failure(row["raw_response"], "A", n=condition["n"])
        item = {"item_id": f"{model_key}:{row['row_id']}",
                "response_text": row["raw_response"],
                "constraint_text": wording("A", 0, n=condition["n"]),
                "n": condition["n"], "s0_class": "fail" if f else "pass"}
        (failed if f else passed).append(item)

    seed = int.from_bytes(hashlib.sha256(
        f"dci1:gate1-sample:{model_key}".encode()).digest()[:8], "big")
    rng = random.Random(seed)
    shortfall = {}
    sample = []
    for name, pool in (("pass", passed), ("fail", failed)):
        if len(pool) < SAMPLE_PER_CLASS:
            shortfall[name] = len(pool)
            sample.extend(pool)
        else:
            sample.extend(rng.sample(pool, SAMPLE_PER_CLASS))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / "annotation_packet.jsonl"
    blinded = [{k: item[k] for k in
                ("item_id", "response_text", "constraint_text", "n")}
               for item in sample]
    packet_path.write_text("".join(json.dumps(i) + "\n" for i in blinded))
    key_path = out_dir / "annotation_truth.json"
    key_path.write_text(json.dumps(
        {i["item_id"]: i["s0_class"] for i in sample}, indent=1,
        sort_keys=True))
    return {"packet": str(packet_path), "truth": str(key_path),
            "items": len(sample), "shortfall": shortfall,
            "status": "PENDING_HUMAN"}


def evaluate_human_agreement(truth_path: Path,
                             labels_path: Path) -> dict[str, Any]:
    """Evaluate returned annotator labels against the packet truth.

    ``labels_path``: JSONL of {item_id, annotator, label} with label in
    {"pass", "fail"}; three annotators per item; majority taken.
    """
    truth = json.loads(Path(truth_path).read_text())
    by_item: dict[str, list[str]] = {}
    annotators: dict[str, dict[str, str]] = {}
    for line in Path(labels_path).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by_item.setdefault(row["item_id"], []).append(row["label"])
        annotators.setdefault(row["annotator"], {})[row["item_id"]] = \
            row["label"]
    disagreements = {"pass": 0, "fail": 0}
    counts = {"pass": 0, "fail": 0}
    for item_id, verdict in truth.items():
        labels = by_item.get(item_id, [])
        if len(labels) != 3:
            raise ProtocolError(f"{item_id}: expected 3 labels, "
                                f"got {len(labels)}")
        majority = max(set(labels), key=labels.count)
        counts[verdict] += 1
        if majority != verdict:
            disagreements[verdict] += 1
    names = sorted(annotators)
    pairwise = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = set(annotators[a]) & set(annotators[b])
            agree = sum(1 for k in shared
                        if annotators[a][k] == annotators[b][k])
            pairwise[f"{a}|{b}"] = agree / len(shared) if shared else None
    passed = all(disagreements[c] <= MAX_DISAGREEMENTS for c in counts)
    return {"disagreements": disagreements, "class_counts": counts,
            "wilson_upper": {c: wilson_upper(disagreements[c], counts[c])
                             for c in counts},
            "pairwise_agreement": pairwise, "passed": passed}


def run_gate1(calibration_rows: list[dict[str, Any]],
              per_topic_target: dict[str, dict[int, int]], out_dir: Path,
              model_key: str,
              human_labels_path: Path | None = None) -> dict[str, Any]:
    assert_blindness()
    from dci1.constraints.definitions import assert_parse_independence

    boundary = evaluate_suite()
    determinism = determinism_test(
        [row["raw_response"] for row in calibration_rows])
    items = item_behaviour(per_topic_target)
    packet = build_annotation_packet(calibration_rows, Path(out_dir),
                                     model_key)
    human = None
    if human_labels_path is not None:
        human = evaluate_human_agreement(
            Path(out_dir) / "annotation_truth.json", human_labels_path)
    record = {
        "boundary_suite": boundary,
        "determinism": determinism,
        "item_behaviour": items,
        "discriminant_validity": {
            "verifier_blindness": True,
            "parse_independence": assert_parse_independence()},
        "human_agreement": human if human is not None else packet,
        "face_validity": {"status": "PENDING_HUMAN"},
        "passed": bool(
            boundary["handled_as_specified"] == boundary["cases"]
            and determinism["passed"]
            and human is not None and human["passed"]),
        "status": ("PASSED" if human is not None and human["passed"] and
                   determinism["passed"] and
                   boundary["handled_as_specified"] == boundary["cases"]
                   else "PENDING_HUMAN" if human is None
                   else "FAILED"),
    }
    return record
