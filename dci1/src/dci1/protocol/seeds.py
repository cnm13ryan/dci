"""The three registered randomness levels, kept operationally separate.

| Level | Purpose | Derivation |
|---|---|---|
| 1 generation | the M cached responses per prompt | ``generation_seed`` |
| 2 resampling | which cached response represents a cell in a pseudo-run | ``resampling_seed`` / ``select_pool_index`` |
| 3 bootstrap  | the preregistered 10,000-resample block bootstrap | ``bootstrap_seed`` |

Each level uses its own root seed (D06) *and* its own SHA-256 domain string, so
no stream can alias another even under a root-seed collision. The §19 mask
permutation deliberately uses the system random source and none of these.

Every derivation is a pure function of scientific identity — never of batch
position, scheduler order, or wall clock — so any recorded draw is exactly
reconstructable from the frozen record.
"""
from __future__ import annotations

import hashlib

_SEP = b"\x1f"
_MAX63 = (1 << 63) - 1

#: Generation streams: which apparatus stage a generation belongs to. Disjoint
#: streams keep pilot/calibration/qualification draws independent of the
#: confirmatory pools without reusing seeds across stages.
GENERATION_STREAMS = (
    "confirmatory", "pilot", "calibration", "greedy", "qualification")


def _digest(domain: str, *parts: object) -> bytes:
    payload = _SEP.join(str(p).encode("utf-8") for p in parts)
    return hashlib.sha256(domain.encode("utf-8") + _SEP + payload).digest()


def _to_seed(digest: bytes) -> int:
    return int.from_bytes(digest[:8], "big") & _MAX63


def generation_seed(root: int, stream: str, model_id: str,
                    prompt_sha256: str, pool_index: int) -> int:
    """Level 1: the seed for one pool member of one prompt (amendment §2.4).

    Deterministic in (root, stream, model identity, prompt hash, pool index);
    distinct pool indices always receive distinct seeds.
    """
    if stream not in GENERATION_STREAMS:
        raise ValueError(f"unknown generation stream {stream!r}")
    return _to_seed(_digest("dci1:gen:v1", root, stream, model_id,
                            prompt_sha256, pool_index))


def resampling_seed(root: int, model_id: str, pseudo_run_index: int) -> int:
    """Level 2: the per-pseudo-run seed (amendment §2.6)."""
    return _to_seed(_digest("dci1:resample:v1", root, model_id,
                            pseudo_run_index))


def select_pool_index(resampling_seed_value: int, block_id: str, arm: str,
                      pool_size: int) -> int:
    """Level 2: the uniform with-replacement draw for one cell.

    Bias-free for any pool size via rejection sampling over 64-bit draws
    (for the registered M=16, a power of two, the first draw always lands).
    Independent across cells and order-independent, so a selection manifest
    row is reconstructable in isolation.
    """
    if pool_size <= 0:
        raise ValueError("pool_size must be positive")
    limit = (1 << 64) - ((1 << 64) % pool_size)
    counter = 0
    while True:
        digest = _digest("dci1:select:v1", resampling_seed_value, block_id,
                         arm, counter)
        draw = int.from_bytes(digest[:8], "big")
        if draw < limit:
            return draw % pool_size
        counter += 1


def bootstrap_seed(root: int, model_id: str, analysis_label: str) -> int:
    """Level 3: the seed for one block-bootstrap execution."""
    return _to_seed(_digest("dci1:boot:v1", root, model_id, analysis_label))
