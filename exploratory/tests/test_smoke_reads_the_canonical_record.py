"""`xm_vllm_smoke.py` reads the BACKEND record, and must use its field names.

There are two record schemas in this repository, deliberately:

  * the backend record in `raw_generations.jsonl`, whose fields are
    `contract.GenerationResult`; and
  * the scored row `xm_vllm_ingest` builds from it, whose fields are
    `crossmodel.schema`.

They differ on purpose — `reasoning_closed` becomes `natural_reasoning_closed`
at the ingest boundary — so a consumer has to know which side it is on. The
smoke driver generates and then summarises straight from the backend record, so
it is on the backend side.

It was half-migrated: `final_answer`, `reasoning_emitted`, `reasoning_cap_hit`
and `answer_truncated` were updated to the canonical names, while
`natural_reasoning_closed` and `technical_failure` were left behind. Both are
read AFTER generation completes, so nothing failed until a real run had loaded
weights, generated, and written its rows — the whole test suite passed, and the
live run died on the summary with `KeyError: 'natural_reasoning_closed'`.

`technical_failure` is worse than a rename: it is a flag the canonical record
does not carry at all. The outcome taxonomy replaced the boolean flags, so that
subscript could never have succeeded.
"""
from __future__ import annotations

import ast
import dataclasses
import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

from vllm_backend.contract import GenerationResult, Outcome  # noqa: E402

pytestmark = pytest.mark.cpu

#: Serialised backend record keys: every dataclass field except `identity`,
#: which is merged into the row rather than nested under a key.
CANONICAL_KEYS = {f.name for f in dataclasses.fields(GenerationResult)} - {"identity"}

#: Design-row and identity keys the smoke driver legitimately reads alongside
#: the generation result, since the backend merges identity into each row.
IDENTITY_KEYS = {"task_id", "arm", "variant", "paraphrase_id", "replicate",
                 "prompt_id", "condition"}

CONSUMERS = ("xm_vllm_smoke.py",)


def _row_subscripts(source: str) -> set[str]:
    """Every `r["key"]` / `row["key"]` string subscript in the module."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            continue
        target = node.value
        if isinstance(target, ast.Name) and target.id in ("r", "row"):
            found.add(node.slice.value)
    return found


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_every_field_it_reads_exists_on_the_backend_record(consumer) -> None:
    read = _row_subscripts((EXPLORATORY / consumer).read_text(encoding="utf-8"))
    unknown = sorted(read - CANONICAL_KEYS - IDENTITY_KEYS)
    assert not unknown, (
        f"{consumer} reads {unknown} off a backend record. Canonical fields are "
        f"{sorted(CANONICAL_KEYS)}. If one of these is a SCORED-row field, the "
        "consumer is on the wrong side of the ingest boundary.")


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_it_does_not_read_a_scored_row_field(consumer) -> None:
    """The specific confusion: the ingest renames, and this runs before it."""
    from vllm_backend.contract import LEGACY_RENAMES
    read = _row_subscripts((EXPLORATORY / consumer).read_text(encoding="utf-8"))
    renamed = sorted(read & set(LEGACY_RENAMES))
    assert not renamed, (
        f"{consumer} reads {renamed}, which the canonical record renamed to "
        f"{[LEGACY_RENAMES[k] for k in renamed]}")


def test_the_outcome_taxonomy_replaced_the_boolean_failure_flags() -> None:
    """`technical_failure` is not a field; it is an outcome value."""
    assert "technical_failure" not in CANONICAL_KEYS
    assert "not_generated" not in CANONICAL_KEYS
    assert "outcome" in CANONICAL_KEYS
    assert Outcome.TECHNICAL_FAILURE.value == "TECHNICAL_FAILURE"


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_it_compares_outcome_against_a_declared_value(consumer) -> None:
    source = (EXPLORATORY / consumer).read_text(encoding="utf-8")
    if 'r["outcome"]' not in source:
        pytest.skip(f"{consumer} does not inspect outcome")
    declared = {o.value for o in Outcome}
    quoted = {node.value for node in ast.walk(ast.parse(source))
              if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert quoted & declared, (
        f"{consumer} inspects outcome but names no declared Outcome value")
