"""Synthetic-oracle backend: the notebook's dry-run generation branch, verbatim.

The oracle is a fixture, produces no evidence, and is the backend for every
DRY_RUN_MODE profile including `integration_pass`. Its outputs must be
byte-identical to the notebook's dry run: same `synthetic_response`, same rng
keying by row_id, same termination records with `synthetic_eos`.
"""
from __future__ import annotations

from typing import Any

from dci.pipeline import state as S
from dci.verifiers.rules import word_tokens


class OracleBackend:
    name = "oracle"

    def load_model(self):
        return None, None

    def free_model(self) -> None:
        pass

    @property
    def tokenizer(self):
        return None

    def generate(self, batch_rows: list[dict[str, Any]],
                 batch_seed: int) -> tuple[list[str], dict[str, Any]]:
        # --- moved verbatim from cells/192.py generate_batch (dry-run branch)
        profile: dict[str, Any] = {}
        texts = [S.synthetic_response(r) for r in batch_rows]
        for r, text in zip(batch_rows, texts):
            tokens = len(word_tokens(text))
            S.TERMINATION_RECORDS.append({
                "row_id": r["row_id"], "generated_token_count": tokens,
                "ended_with_eos": True, "hit_max_new_tokens": False,
                "output_truncated": False, "stop_reason": "synthetic_eos"})
        return texts, profile
