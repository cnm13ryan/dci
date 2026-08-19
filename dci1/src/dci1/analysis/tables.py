"""Accepted responses → the scored table (prereg §9, §16, §21, §23).

One scored row per accepted observation. Scoring reads the response text and
design facts only; the arm label reaches the *table* (it is a treatment
variable) but never any verifier. Post-treatment fields are carried for
diagnostics and are excluded from primary formulas by the codebook assertion.
"""
from __future__ import annotations

from typing import Any

from dci1.analysis.taxonomy import classify_failure
from dci1.constraints.definitions import added_verifier
from dci1.design.blocks import Block
from dci1.design.prompts import added_constraint_id, constraint_block_text
from dci1.protocol.constants import (
    ARMS,
    PRIMARY_ARMS,
    SHORT_RESPONSE_WORDS,
    ProtocolError,
)
from dci1.verifiers import target as target_rules
from dci1.verifiers.words import words_lower


def score_row(accepted: dict[str, Any], block: Block, *, n: int, m: int,
              references: tuple[str, str, str]) -> dict[str, Any]:
    arm = accepted["arm"]
    if arm not in ARMS:
        raise ProtocolError(f"unknown arm {arm!r}")
    response = accepted["response"]
    finish_reason = accepted.get("finish_reason", "")
    wordings = constraint_block_text(block, arm, n=n, m=m,
                                     references=references)
    instruction_text = "\n".join(f"{i + 1}. {w}"
                                 for i, w in enumerate(wordings))

    s0 = target_rules.s0_count(response)
    s1 = target_rules.s1_count(response)
    s2 = target_rules.s2_count(response)
    s3 = target_rules.s3_count(response, wordings)

    empty = not response.strip()
    truncated = finish_reason == "length"
    word_count = len(words_lower(response))

    row: dict[str, Any] = {
        # identity / design
        "block_id": accepted["block_id"],
        "arm": arm,
        "order": block.order,
        "wording_target": block.wording_target,
        "wording_added": block.wording_added,
        "topic_id": block.topic_id,
        # outcome (S0) and declared alternatives
        "s0_count": s0, "s1_count": s1, "s2_count": s2, "s3_count": s3,
        "f_s0": 0 if target_rules.passes(s0, n) else 1,
        "f_s1": 0 if target_rules.passes(s1, n) else 1,
        "f_s2": 0 if target_rules.passes(s2, n) else 1,
        "f_s3": 0 if target_rules.passes(s3, n) else 1,
        "graded": target_rules.graded(s0, n),
        # post-treatment diagnostics (§21: never in a primary formula)
        "response_words": word_count,
        "short_flag": word_count <= SHORT_RESPONSE_WORDS,
        "truncated": truncated,
        "empty": empty,
        "finish_reason": finish_reason,
        "token_count": accepted.get("token_count", 0),
        "non_behavioural": bool(empty or truncated),
        # provenance
        "response_content_hash": accepted["response_content_hash"],
        "pool_index": accepted.get("pool_index"),
    }

    added_id = added_constraint_id(arm, references) if arm in PRIMARY_ARMS \
        else None
    if added_id is not None:
        verifier = added_verifier(added_id, m if added_id == "B" else None)
        row["uptake"] = 1 if verifier(response) else 0
        row["joint_compliance"] = 1 if (row["f_s0"] == 0 and
                                        row["uptake"] == 1) else 0
    else:
        row["uptake"] = None
        row["joint_compliance"] = None

    if arm in PRIMARY_ARMS and row["f_s0"] == 1:
        row["failure_category"] = classify_failure(
            response=response, finish_reason=finish_reason, s0=s0, s2=s2,
            n=n, instruction_text=instruction_text)
    else:
        row["failure_category"] = None
    return row


def score_table(accepted_rows: list[dict[str, Any]], blocks: list[Block], *,
                n: int, m: int,
                references: tuple[str, str, str]) -> list[dict[str, Any]]:
    by_id = {b.block_id: b for b in blocks}
    scored = []
    for accepted in accepted_rows:
        block = by_id.get(accepted["block_id"])
        if block is None:
            raise ProtocolError(
                f"accepted row references unknown block "
                f"{accepted['block_id']!r}")
        scored.append(score_row(accepted, block, n=n, m=m,
                                references=references))
    return scored
