"""Characterization of the v3 evidence the B+R pilot reuses (read-only).

The B+R discriminating pilot (user-notes/dci-construct-pass2.md §G row 1)
reuses three registered v3 quantities as its B-alone, B+A, and R-alone
baselines. These tests pin every reused number and every reuse-validity
condition from user-notes/prompt-to-red-team.md (provenance, verifier
hash, content hashes, configuration) so the pilot's baselines cannot
drift from the signed evidence. Written before the pilot tool existed;
nothing here writes, and everything skips cleanly where the machine-local
evidence tree is absent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from dci1v3.engine.context import DCI1_ROOT
from dci1v3.models.registry import MODEL_BY_KEY
from dci1v3.protocol.hashing import sha_text
from dci1v3.verifiers import verifier_source_hash
from dci1v3.verifiers.families import added_verifier

EVIDENCE = DCI1_ROOT / "evidence" / "dci1-v3"

pytestmark = pytest.mark.skipif(
    not (EVIDENCE / "gemma-3n-e2b-it" / "gate2a" / "cache.jsonl").exists(),
    reason="completed registered evidence tree not present")

#: The frozen verifier at the time the reused verdicts were produced.
REUSED_VERIFIER_HASH = \
    "2059509dc0892a3a01928194e2c8a3431b0c07a81f33c235a0d77f1f29ad4f1b"

#: Frozen design parameters per Gemma replication (gate3_freeze.json).
FROZEN = {
    "gemma-3n-e2b-it": {
        "final_references": [["RF1", 5], ["RF2", 5], ["RF6", 4]],
        "m_star": 7, "n_star": 5, "completion_cap": 512,
    },
    "gemma-3n-e4b-it": {
        "final_references": [["RF2", 2], ["RF6", 4], ["RF4", 4]],
        "m_star": 7, "n_star": 7, "completion_cap": 512,
    },
}

#: Reused baseline cells: gate2a solo cache, (rows, added_pass count).
GATE2A_SOLO = {
    "gemma-3n-e2b-it": {
        "solo:B:7": (96, 78),
        "solo:RF1:5": (96, 83),
        "solo:RF2:5": (96, 83),
        "solo:RF6:4": (96, 83),
    },
    "gemma-3n-e4b-it": {
        "solo:B:7": (96, 73),
        "solo:RF2:2": (96, 75),
        "solo:RF4:4": (96, 77),
        "solo:RF6:4": (96, 75),
    },
}

#: Reused B+A cell: confirmatory AB arm, (draw rows, added_pass count).
CONFIRMATORY_AB = {
    "gemma-3n-e2b-it": (6144, 2115),
    "gemma-3n-e4b-it": (6144, 2730),
}

#: sha256 over the sorted, 0x1f-joined 96 solo topic ids (both models).
SOLO_TOPIC_LIST_SHA256 = \
    "b99af9c4e50f14a491fab8e4a7a50901ce0906281229039026504aed5fb01ee1"

GEMMAS = tuple(sorted(FROZEN))


def _gate2a_rows(model: str) -> dict[str, list[dict]]:
    wanted = set(GATE2A_SOLO[model])
    rows: dict[str, list[dict]] = {k: [] for k in wanted}
    with (EVIDENCE / model / "gate2a" / "cache.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row["kind"] in wanted:
                rows[row["kind"]].append(row)
    return rows


@pytest.mark.parametrize("model", GEMMAS)
def test_frozen_design_parameters_pinned(model):
    body = json.loads(
        (EVIDENCE / model / "gate3_freeze.json").read_text()
    )["payload"]["body"]
    for key, value in FROZEN[model].items():
        assert body[key] == value


@pytest.mark.parametrize("model", GEMMAS)
def test_reused_solo_cells_counts_and_provenance(model):
    spec = MODEL_BY_KEY[model]
    topics = set()
    for kind, rows in _gate2a_rows(model).items():
        expected_rows, expected_passes = GATE2A_SOLO[model][kind]
        assert len(rows) == expected_rows
        assert sum(bool(r["verdicts"]["added_pass"]) for r in rows) \
            == expected_passes
        for row in rows:
            assert row["model_id"] == spec.model_id
            assert row["model_revision"] == spec.revision
            assert row["verdicts"]["verifier_source_hash"] \
                == REUSED_VERIFIER_HASH
            assert sha_text(row["raw_response"]) \
                == row["response_content_hash"]
            if kind == "solo:B:7":
                topics.add(row["topic_id"])
    digest = hashlib.sha256(
        "\x1f".join(sorted(topics)).encode()).hexdigest()
    assert digest == SOLO_TOPIC_LIST_SHA256


def test_current_verifier_is_the_frozen_instrument():
    assert verifier_source_hash() == REUSED_VERIFIER_HASH


@pytest.mark.parametrize("model", GEMMAS)
def test_reused_verdicts_recompute_under_current_verifier(model):
    for kind, rows in _gate2a_rows(model).items():
        _, constraint_id, severity = kind.split(":")
        verifier = added_verifier(constraint_id, int(severity))
        for row in rows:
            assert verifier(row["raw_response"]) \
                == row["verdicts"]["added_pass"]


@pytest.mark.parametrize("model", GEMMAS)
def test_reused_confirmatory_ab_uptake_pinned(model):
    total = passes = 0
    with (EVIDENCE / model / "confirmatory" / "cache.jsonl").open() as fh:
        for line in fh:
            if '"arm": "AB"' not in line:
                continue
            row = json.loads(line)
            assert row["arm"] == "AB"
            total += 1
            passes += bool(row["verdicts"]["added_pass"])
    assert (total, passes) == CONFIRMATORY_AB[model]


def test_implied_delivery_losses_from_reused_cells():
    """D(B<-A) implied by the reused cells; the pilot's fixed points."""
    for model, expected in (("gemma-3n-e2b-it", 0.46826171875),
                            ("gemma-3n-e4b-it", 0.31608072916666663)):
        solo_rows, solo_passes = GATE2A_SOLO[model]["solo:B:7"]
        ab_rows, ab_passes = CONFIRMATORY_AB[model]
        d_b_a = solo_passes / solo_rows - ab_passes / ab_rows
        assert d_b_a == pytest.approx(expected, abs=1e-12)
