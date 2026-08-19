"""Subprocess worker for the §10 determinism test: read response items,
emit one digest over every verifier verdict. Three separate processes must
produce identical digests (agreement 1.000)."""
from __future__ import annotations

import json
import sys

from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj
from dci1v3.verifiers.families import family_statistic, focal_statistic
from dci1v3.verifiers.target import s0_count, s1_count, s2_count


def verdict_digest(items: list[dict]) -> str:
    verdicts = []
    for item in items:
        text = item["response_text"]
        verdicts.append({
            "item_id": item["item_id"],
            "s0": s0_count(text), "s1": s1_count(text),
            "s2": s2_count(text),
            "focal": focal_statistic(text),
            "families": {f: family_statistic(f, text)
                         for f in C.FAMILY_IDS},
        })
    return sha_obj(verdicts)


def main() -> None:
    items = json.loads(sys.stdin.read())
    print(verdict_digest(items))


if __name__ == "__main__":
    main()
