"""Canonical status is a statement about row identity, not about line count.

Defect: `canonical_status` required `len(rows) == contract.EXPECTED_ROWS` and
never consulted `unique_row_ids`, which it computed one field earlier. A
160-line file with one design cell missing and some other cell duplicated in its
place therefore passed: right length, right task count, right arm set, wrong
experiment — one cell contributing two draws and another contributing none.

The replication audit could not catch it either. `replicate_duplication` built
its pairs with `if len(answers) == 2`, so a group of one or three — precisely the
malformed case — was silently dropped before the alarm was computed.

The manifest exists to establish trust in artifacts that are gitignored and
therefore unreviewable. A trust statement that a substitution can satisfy by
arithmetic is not one.

Classification: canonical-data/provenance failure and replicate-independence
failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_manifest  # noqa: E402
from crossmodel import contract, seeds  # noqa: E402

FOCAL, REFERENCE = contract.ARMS
SEMI, CTRL = contract.BACKGROUNDS


def design_rows() -> list[dict]:
    """The exact canonical design: 20 tasks x 2 arms x 2 backgrounds x 2 reps."""
    rows = []
    for t in range(contract.N_TASKS):
        for arm in contract.ARMS:
            for background in contract.BACKGROUNDS:
                for replicate in range(contract.REPLICATES):
                    rows.append({
                        "row_id": f"id-{t}-{arm}-{background}-{replicate}",
                        "task_id": f"PLT{t:02d}",
                        "arm": arm,
                        "background": background,
                        "order": "QAC",
                        "replicate_id": replicate,
                        "model_id": "org/M",
                        "reasoning_mode": "NO_THINKING",
                        "final_answer": f"Answer {t} {arm} {background} {replicate}.",
                    })
    return rows


class TestCompleteDesign:
    def test_the_canonical_design_is_complete(self) -> None:
        audit = xm_manifest.identity_audit(design_rows())
        assert audit["complete"] is True
        assert audit["missing_cells"] == []
        assert audit["duplicated_cells"] == {}
        assert audit["unique_row_ids"] == contract.EXPECTED_ROWS

    def test_row_count_matches_the_contract(self) -> None:
        assert len(design_rows()) == contract.EXPECTED_ROWS


class TestSubstitutedRow:
    """The reviewed case: right line count, wrong design."""

    @staticmethod
    def substituted() -> list[dict]:
        rows = design_rows()
        # Drop one design cell and duplicate another in its place. The file
        # keeps exactly 160 lines.
        victim = rows.pop(0)
        clone = dict(rows[0])
        clone["row_id"] = victim["row_id"]      # even the id count reconciles
        rows.append(clone)
        return rows

    def test_line_count_is_unchanged(self) -> None:
        assert len(self.substituted()) == contract.EXPECTED_ROWS

    def test_identity_audit_rejects_it(self) -> None:
        audit = xm_manifest.identity_audit(self.substituted())
        assert audit["complete"] is False

    def test_the_missing_cell_is_named(self) -> None:
        audit = xm_manifest.identity_audit(self.substituted())
        assert len(audit["missing_cells"]) == 1
        assert "PLT00" in audit["missing_cells"][0]

    def test_the_duplicated_cell_is_named(self) -> None:
        audit = xm_manifest.identity_audit(self.substituted())
        assert audit["duplicated_cells"], "the duplicate cell was not reported"


class TestMalformedReplicateGroups:
    def test_a_group_of_one_is_counted(self) -> None:
        rows = design_rows()
        rows.pop(0)                              # leaves a group of size 1
        audit = seeds.replicate_duplication(rows)
        assert audit["malformed_groups"] == 1
        assert audit["malformed_group_sizes"]

    def test_a_group_of_three_is_counted(self) -> None:
        rows = design_rows()
        rows.append(dict(rows[0], row_id="extra"))
        audit = seeds.replicate_duplication(rows)
        assert audit["malformed_groups"] == 1

    def test_a_clean_design_has_no_malformed_groups(self) -> None:
        assert seeds.replicate_duplication(design_rows())["malformed_groups"] == 0


class TestMissingTasks:
    def test_too_few_tasks_is_not_complete(self) -> None:
        rows = [r for r in design_rows() if r["task_id"] != "PLT19"]
        audit = xm_manifest.identity_audit(rows)
        assert audit["task_count_matches_contract"] is False
        assert audit["complete"] is False
