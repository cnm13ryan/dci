"""The §25 human-written baseline packet (PENDING_HUMAN, decision D25).

Twelve randomly chosen confirmatory topics; one annotator writes an answer
under the focal composition and one under one reference composition, without
model assistance. This module builds the writing packet deterministically and
scores returned answers with the real verifiers.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from dci1.calibration.gate2 import solo_failure
from dci1.constraints.wordings import wording
from dci1.topics.split import split_bank
from dci1.verifiers.target import s0_count


def build_packet(out_dir: Path, *, n: int, m: int, reference: str,
                 model_key: str) -> dict[str, Any]:
    seed = int.from_bytes(hashlib.sha256(
        f"dci1:human-baseline:{model_key}".encode()).digest()[:8], "big")
    topics = random.Random(seed).sample(split_bank()["confirmatory"], 12)
    items = []
    for topic in topics:
        for composition, added in (("focal", ("B", m)),
                                   ("reference", (reference, None))):
            items.append({
                "topic_id": topic["topic_id"],
                "question": topic["question"],
                "composition": composition,
                "constraints": [wording("A", 0, n=n),
                                wording(added[0], 0, m=added[1])],
            })
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "human_baseline_packet.jsonl"
    path.write_text("".join(json.dumps(i) + "\n" for i in items))
    return {"packet": str(path), "items": len(items),
            "status": "PENDING_HUMAN"}


def score_answers(answers_path: Path, *, n: int, m: int,
                  reference: str) -> dict[str, Any]:
    """{topic_id, composition, answer} rows → target compliance of the 24."""
    rows = [json.loads(line) for line in
            Path(answers_path).read_text().splitlines() if line.strip()]
    scored = []
    for row in rows:
        added = ("B", m) if row["composition"] == "focal" else (reference,
                                                               None)
        scored.append({
            "topic_id": row["topic_id"],
            "composition": row["composition"],
            "target_pass": s0_count(row["answer"]) == n,
            "added_pass": solo_failure(row["answer"], added[0],
                                       m=added[1]) == 0,
        })
    return {"answers": len(scored), "rows": scored,
            "target_compliance": (sum(r["target_pass"] for r in scored)
                                  / len(scored)) if scored else None}
