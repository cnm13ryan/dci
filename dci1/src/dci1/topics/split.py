"""Seeded stratified split of the topic bank (prereg §6; decision D13).

Within each declared subject area the 48 questions are shuffled with a fixed
per-area seed derived from the frozen ``TOPIC_SPLIT_SEED``, then cut into
8 calibration / 32 confirmatory / 8 sequestered. The three splits are
disjoint; the sequestered topics never enter this study.

The frozen orders this module emits are design facts (D13): calibration
position p (stratum-major) drives the calibration wording rotation, and
confirmatory position i (stratum-major) is the block index.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any

from dci1.protocol.constants import (
    CALIBRATION_PER_AREA,
    CONFIRMATORY_PER_AREA,
    SUBJECT_AREAS,
    TOPIC_SPLIT_SEED,
    ProtocolError,
)
from dci1.topics.bank import load_bank


def _area_seed(root: int, area: str) -> int:
    digest = hashlib.sha256(
        f"dci1:topics:v1\x1f{root}\x1f{area}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def split_bank(topics: list[dict[str, Any]] | None = None,
               ) -> dict[str, list[dict[str, Any]]]:
    """{"calibration": [...96], "confirmatory": [...384], "sequestered": [...96]}
    each stratum-major, in the frozen seeded order."""
    topics = topics if topics is not None else load_bank()
    calibration, confirmatory, sequestered = [], [], []
    for area in SUBJECT_AREAS:
        area_topics = [t for t in topics if t["area"] == area]
        rng = random.Random(_area_seed(TOPIC_SPLIT_SEED, area))
        shuffled = list(area_topics)
        rng.shuffle(shuffled)
        calibration.extend(shuffled[:CALIBRATION_PER_AREA])
        confirmatory.extend(
            shuffled[CALIBRATION_PER_AREA:
                     CALIBRATION_PER_AREA + CONFIRMATORY_PER_AREA])
        sequestered.extend(
            shuffled[CALIBRATION_PER_AREA + CONFIRMATORY_PER_AREA:])
    result = {"calibration": calibration, "confirmatory": confirmatory,
              "sequestered": sequestered}
    ids = [t["topic_id"] for part in result.values() for t in part]
    if len(set(ids)) != len(ids):
        raise ProtocolError("splits are not disjoint")
    return result
