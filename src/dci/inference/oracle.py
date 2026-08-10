"""Synthetic-oracle backend: the notebook's dry-run generation branch, verbatim.

The oracle is a fixture, produces no evidence, and is the backend for every
DRY_RUN_MODE profile including `integration_pass`. Its outputs must be
byte-identical to the notebook's dry run: same `synthetic_response`, same rng
keying by row_id, same termination records with `synthetic_eos`.
"""
from __future__ import annotations

from typing import Any

from dci.pipeline import state as S
from dci.provenance.hashes import stable_int
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
        # Per-constraint truncation rates, for TESTING the output-cap gate only.
        # Default {} reproduces the notebook's dry run exactly: every row ends
        # with synthetic_eos and nothing is truncated. A non-empty mapping is a
        # deliberate fixture and is recorded in the profile so it can never be
        # mistaken for measured truncation.
        injected = dict(getattr(S.CFG, "oracle_truncation_by_constraint", ()) or ())
        for r, text in zip(batch_rows, texts):
            tokens = len(word_tokens(text))
            share = float(injected.get(r.get("added_constraint", ""), 0.0))
            truncated = bool(share > 0.0) and (
                stable_int(f"trunc|{r['row_id']}", 10_000) / 10_000.0 < share)
            S.TERMINATION_RECORDS.append({
                "row_id": r["row_id"],
                "generated_token_count": (S.CFG.max_new_tokens if truncated
                                          else tokens),
                "ended_with_eos": not truncated,
                "hit_max_new_tokens": truncated,
                "output_truncated": truncated,
                "stop_reason": "max_new_tokens" if truncated else "synthetic_eos"})
        if injected:
            profile["injected_truncation"] = injected
        return texts, profile
