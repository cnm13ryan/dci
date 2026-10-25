"""Synthetic stand-ins for CPU tests and the end-to-end demonstration.

Nothing here is evidence. Two kinds of stand-in:

* ``synthetic_generate`` replaces the backend: for each design row it draws
  success with a configured probability and returns a constructed witness
  (compliant) or a violation text, so the real verifiers, scoring, tables,
  calibration, references and freezes all run on real text;
* ``tables_from_rates`` builds compliance tables directly from stated rates,
  for scenario tests of the selection logic.

Rows and tables produced here carry ``synthetic = True``, and a Freeze 2
built from them says so; ``freeze.py`` refuses to treat them as pilot data.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Callable, Mapping

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1.design import TASK_ONLY, condition_constraint
from dci.batch1.scoring import Count, PilotTables, _key
from dci.provenance.hashes import sha

__all__ = ["default_truth", "synthetic_generate", "tables_from_rates"]

Truth = Callable[[str, str | None, str], float]

_MODEL_SHIFT = {"gemma-3n-e2b-it": -0.08, "gemma-3n-e4b-it": 0.02,
                "qwen3-4b": 0.06, "qwen3-4b-instruct-2507": 0.10}
_FRAME_SHIFT = {"F0": 0.0, "F1": -0.03, None: 0.0}
_FAMILY_BASE = {
    "exact_char_count": 0.30, "exact_sentence_count": 0.45,
    "exact_paragraph_count": 0.55, "include_words": 0.80,
    "forbid_words": 0.35, "forbid_letter": 0.40,
    "sentence_word_bound": 0.50, "no_repeated_words": 0.15,
    "no_repeated_bigrams": 0.25, "distinct_openers": 0.70,
    "length_order": 0.12, "alphabetical_openers": 0.10, "chain_word": 0.08,
    "chain_letter": 0.05, "adjacent_shared_word": 0.30,
}


def default_truth(model: str, frame: str | None, condition: str) -> float:
    """A plausible-looking, entirely invented compliance surface."""
    if condition == TASK_ONLY:
        return 0.0
    c = L.constraint_by_id()[condition]
    p = c.p
    if c.family_id == "exact_word_count":
        base = 0.62 - 0.07 * (p["n"] - 2) - 0.02 * (len(p["word"]) - 6)
    elif c.family_id == "max_word_length":
        base = 0.08 + 0.15 * (p["m"] - 8)
    else:
        base = _FAMILY_BASE[c.family_id]
    jitter = (int(sha(["jitter", model, frame, condition])[:6], 16)
              / 0xFFFFFF - 0.5) * 0.06
    return min(0.98, max(0.01, base + _MODEL_SHIFT.get(model, 0.0)
                         + _FRAME_SHIFT.get(frame, 0.0) + jitter))


_TASK_ONLY_TEXTS = COMPAT._VIOLATION_CANDIDATES


def synthetic_generate(truth: Truth = default_truth, *,
                       truncation_rate: float = 0.01, empty_rate: float = 0.0,
                       technical: Callable[[Mapping[str, Any]], str | None]
                       | None = None, returncode: int = 0,
                       blocked: bool = False) -> Callable[..., dict[str, Any]]:
    """A stand-in backend writing rows in the seam's shape.

    ``empty_rate``: share of rows that are completed blank generations,
    written as the seam writes them under NO_THINKING (``CHANNEL_INVALID``,
    blank raw text, ``finish_reason`` stop). ``technical(row)`` may name a
    technical outcome for a row (e.g. ``"TECHNICAL_FAILURE"``).
    ``returncode`` and ``blocked`` imitate the seam's exit code and sidecar.
    """
    witnesses: dict[str, str] = {}
    violations: dict[str, str] = {}

    def text_for(row: Mapping[str, Any], rng: random.Random) -> str:
        c = condition_constraint(row["condition"])
        if c is None:
            return rng.choice(_TASK_ONLY_TEXTS)
        if c.cid not in witnesses:
            witnesses[c.cid] = COMPAT.build_witness(c) or ""
            violations[c.cid] = COMPAT.violation_text(c)
        ok = rng.random() < truth(row["model"], row["frame"], row["condition"])
        return witnesses[c.cid] if ok else violations[c.cid]

    def generate(run_dir: Path, plan: Mapping[str, Any],
                 design_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
        rows = []
        for row in design_rows:
            rng = random.Random(row["scientific_seed"])
            text = text_for(row, rng)
            truncated = rng.random() < truncation_rate
            empty = rng.random() < empty_rate
            failure = technical(row) if technical else None
            base = {**row, "seed_reasoning": row["scientific_seed"],
                    "reasoning_emitted": False, "outcome_detail": ""}
            if blocked or failure:
                rows.append({**base, "outcome": "CAPACITY_EXCEEDED" if blocked
                             else failure, "final_answer": "",
                             "raw_generation": "", "answer_truncated": False,
                             "finish_reason": "", "total_generated_tokens": 0})
            elif empty:
                rows.append({**base, "outcome": "CHANNEL_INVALID",
                             "final_answer": "", "raw_generation": "  \n",
                             "answer_truncated": False, "finish_reason": "stop",
                             "channel_valid": False,
                             "total_generated_tokens": 2})
            else:
                rows.append({**base, "outcome": "OK", "final_answer": text,
                             "raw_generation": text, "channel_valid": True,
                             "answer_truncated": truncated,
                             "finish_reason": "length" if truncated else "stop",
                             "total_generated_tokens": len(text.split())})
        return {"rows": rows, "returncode": returncode,
                "provenance": {"synthetic": True, "blocked": blocked,
                               "generator": "dci.batch1.synthetic"}}
    return generate


def tables_from_rates(rates: Mapping[tuple[str, str, str], float], *,
                      n: int = 96,
                      kappa: Mapping[tuple[str, str], float] | None = None,
                      kappa_n: int = 64) -> PilotTables:
    """Tables whose explicit cells hold round(p * n) of n, and whose
    task-only kappa cells hold the stated rates (default 0)."""
    t = PilotTables(synthetic=True)
    for (model, frame, cid), p in rates.items():
        t.explicit[_key(model, frame, cid)] = Count(k=round(p * n), n=n)
    for (model, cid), p in (kappa or {}).items():
        t.task_only[_key(model, cid)] = Count(k=round(p * kappa_n), n=kappa_n)
    return t


def full_rates(truth: Truth = default_truth,
               cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG
               ) -> dict[tuple[str, str, str], float]:
    """Every explicit cell of the planned panel, from a truth surface."""
    cids = ([c.cid for c in L.a_candidates()] + [c.cid for c in L.b_candidates()]
            + [c.cid for c in L.reference_library()])
    return {(m, f, cid): truth(m, f, cid) for m in cfg.models
            for f in cfg.frames for cid in cids}
