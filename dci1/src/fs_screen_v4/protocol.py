"""Freeze the screen protocol to JSON and hash it, before the first generation.

The hash is recorded in every result file. A screen whose protocol hash does not
match the frozen file is not this screen.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          TARGET_GRID)
from dci1v4.verifiers.wording_suite import TWENTY_RESPONSES

from fs_screen_v4 import CLASSIFICATION, STUDY_ID
from fs_screen_v4 import constraints as cc
from fs_screen_v4 import plan as pl
from fs_screen_v4 import suite, witnesses
from fs_screen_v4.wordings import candidate_wordings, caliper_table

DCI1 = Path(__file__).resolve().parent.parent.parent
FROZEN = DCI1 / "reports" / "fs_screen_v4" / "screen_protocol.json"


def build(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or DCI1.parent
    return {
        "study_id": STUDY_ID,
        "classification": CLASSIFICATION,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN. Not a registered v4 stage. "
                   "No Gate 1 dependency. Nothing here may enter a v4 "
                   "estimator, and evidence/fs-screen-v4 is outside the v4 "
                   "namespace so the positive-admission guard refuses it."),
        "producing_commit": gitinfo.head_commit(repo_root),
        "question": {
            "FORM": ("every registered reference family is an S <= q monotone "
                     "count budget whose pass set is downward-closed under "
                     "prefix; the empty string scores 94/94 on the pool, 4/4 "
                     "on B and 0/8 on A"),
            "STEM": ("a uniform answer-length instruction removes the "
                     "shortening escape for B and for every reference at once"),
        },
        "factors": {
            "FORM": ["count", "candidate"],
            "STEM": list(pl.STEM_LEVELS),
            "stem_sentence": pl.STEM_SENTENCE,
            "stem_placement": ("between the topic question and the numbered "
                               "constraint list, in every cell without "
                               "exception"),
            "stem_is_scored": False,
            "stem_counts_toward_load": False,
            "stem_diagnostic": f"realised rate of {pl.STEM_TARGET_MIN}-"
                               f"{pl.STEM_TARGET_MAX} word answers",
        },
        "candidate_families": {
            k: {"form": v.form, "numerator": v.numerator,
                "ladder": list(v.ladder),
                "statistic_source": v.statistic_source,
                "rule_statement": v.rule_statement,
                "wordings_at_first_rung": list(
                    candidate_wordings(k, v.ladder[0]))}
            for k, v in cc.CANDIDATES.items()},
        "excluded_families": cc.EXCLUDED_FROM_CANDIDATES,
        "rf2_conflict_proof": witnesses.assert_rf2_conflict(),
        "discipline": {
            "wordings_per_constraint": pl.N_WORDINGS,
            "length_caliper_against": "A",
            "length_caliper_tolerance": 0.20,
            "wording_equivalence_verdicts": suite.assert_wording_equivalence(),
            "fixture_responses": len(TWENTY_RESPONSES),
            "parse_independence": "asserted on the callable signatures",
            "witness_compositions_certified":
                witnesses.verify_all()["compositions_certified"],
            "caliper_table_at_n4": caliper_table(4),
        },
        "seeds": {
            "screen_root": pl.SCREEN_ROOT_SEED,
            "domain": pl.DOMAIN_SCREEN_GENERATION,
            "stage_label": pl.STAGE,
            "derivation": "domain, root, stage, model_id, prompt hash, draw",
            "distinct_from": {"v3_roots": "202608170-202608175",
                              "v4_roots": "202608190-202608195"},
        },
        "generation": {
            "topics": "the 24 registered pre-screen topics, unchanged",
            "draws_per_cell": 1,
            "completion_cap": "each model's own §12.1 selected cap",
            "decoding": "the registered policy, unchanged",
            "tensor_parallel_size": 1,
        },
        "reused_without_regeneration": {
            "count x current": ("the registered §12.2 ladder screen at "
                                "evidence/dci1-v4/<model>/prescreen/"
                                "ladder-cap512, read only"),
        },
        "success_criteria": {
            "reference": ("at least three families carrying a rung inside the "
                          "0.10 caliper of A AND at solo vacuity <= 0.10, at "
                          "the SAME severity, on all four models"),
            "b_side": ("under the floored stem, B-solo vacuous share of passes "
                       "<= 0.10 on all four models"),
            "fixed_before": "the first generation of this screen",
        },
        "registered_values_untouched": {
            "reference_caliper": C.REFERENCE_CALIPER,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "target_grid": list(TARGET_GRID), "focal_grid": list(FOCAL_GRID),
            "reference_ladders": {k: list(v)
                                  for k, v in REFERENCE_LADDERS.items()},
            "note": ("listed so a later diff proves the screen changed none of "
                     "them; the sensitivity map varies them for reporting only"),
        },
        "verifier_source_hash": verifier_source_hash(),
        "fixture_verdict_table": suite.fixture_verdict_table(),
    }


def protocol_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()


def freeze(repo_root: Path | None = None) -> dict[str, Any]:
    """Write the frozen protocol once; refuse to overwrite a different one."""
    payload = build(repo_root)
    digest = protocol_hash(payload)
    record = {"screen_protocol_hash": digest, "payload": payload}
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    if FROZEN.exists():
        existing = json.loads(FROZEN.read_text())
        if existing["screen_protocol_hash"] != digest:
            raise RuntimeError(
                f"the screen protocol is already frozen at "
                f"{existing['screen_protocol_hash']} and would change to "
                f"{digest}; a frozen screen protocol is never rewritten")
        return existing
    FROZEN.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record


def load() -> dict[str, Any]:
    return json.loads(FROZEN.read_text())
