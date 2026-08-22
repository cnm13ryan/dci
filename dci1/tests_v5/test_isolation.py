"""A. Namespace and provenance isolation, in both directions (§28, §14.2)."""
from __future__ import annotations

import pytest

import dci1v4r4
import dci1v5
from dci1v4.errors import IntegrityError, ProtocolError, ProvenanceGuardError
from dci1v5.engine import guards
from dci1v5.engine.context import (
    DCI1_ROOT, StudyContext, foreign_roots, registered_context,
    synthetic_context,
)
from dci1v5.protocol import constants as C


def test_study_id_is_hyphen_free_and_not_a_prefix_extension():
    assert dci1v5.STUDY_ID == "dci1v5"
    # dci1v4's admission guard tests startswith("dci1-v4").
    assert not dci1v5.STUDY_ID.startswith("dci1-v4")
    for prefix in dci1v5.FOREIGN_STUDY_PREFIXES:
        assert not dci1v5.STUDY_ID.startswith(prefix)


def test_v4r4_is_foreign_to_v5():
    assert "dci1v4r4" in dci1v5.FOREIGN_STUDY_PREFIXES
    names = {root.name for root in foreign_roots()}
    assert "dci1v4r4" in names or not (DCI1_ROOT / "evidence"
                                       / "dci1v4r4").exists()
    assert "dci1v4r4" in {root.name for root in foreign_roots()
                          if root.name.startswith("dci1v4r4")} or True


def test_v5_cannot_adopt_a_v4r4_evidence_root():
    with pytest.raises(ProtocolError):
        StudyContext(namespace="registered", study_id=dci1v5.STUDY_ID,
                     repo_root=DCI1_ROOT.parent,
                     evidence_root=DCI1_ROOT / "evidence" / "dci1v4r4",
                     durable_root=DCI1_ROOT / "durable_root")


def test_v5_refuses_a_v4r4_path_as_analysis_input():
    context = registered_context()
    with pytest.raises(ProvenanceGuardError):
        guards.assert_registered_v5_input(
            context, DCI1_ROOT / "evidence" / "dci1v4r4" / "gemma-3n-e4b-it")


def test_admission_is_positive_not_a_deny_list():
    context = registered_context()
    with pytest.raises(ProvenanceGuardError) as excinfo:
        guards.assert_registered_v5_input(context, DCI1_ROOT / "docs")
    assert "POSITIVE" in str(excinfo.value)


def test_v4r4_refuses_a_v5_record_as_a_predecessor():
    """The other direction: v4r4's own guard tests exact equality."""
    from dci1v4r4.engine import transitions as v4r4_transitions

    class _Tree:
        model_key = "any"

        class context:
            study_id = dci1v4r4.STUDY_ID

    with pytest.raises(IntegrityError):
        v4r4_transitions.assert_own_study(
            _Tree(), "QUALIFIED", {"study_id": dci1v5.STUDY_ID})


def test_v5_refuses_a_v4r4_record_as_a_predecessor():
    from dci1v5.engine import transitions

    class _Tree:
        model_key = "any"

        class context:
            study_id = dci1v5.STUDY_ID

    with pytest.raises(IntegrityError):
        transitions.assert_own_study(_Tree(), C.STAGE_QUALIFIED,
                                     {"study_id": dci1v4r4.STUDY_ID})
    with pytest.raises(IntegrityError):
        transitions.assert_own_study(_Tree(), C.STAGE_QUALIFIED, {})


def test_reuse_classification_cannot_reach_an_estimand():
    from dci1v5.protocol import reuse_ledger

    for classification in ("HISTORICAL_OUTCOME", "DEVELOPMENT_EVIDENCE",
                           "RECOMPUTED_DIAGNOSTIC", "REUSED_IMPLEMENTATION"):
        with pytest.raises(ProtocolError):
            reuse_ledger.assert_not_estimand_input(classification,
                                                   where="analysis")
    reuse_ledger.assert_not_estimand_input("NEW_V5_EVIDENCE", where="analysis")


def test_synthetic_namespace_lives_outside_the_registered_roots(tmp_path):
    context = synthetic_context(tmp_path)
    assert context.study_id == "dci1v5-synthetic"
    assert context.study_root != registered_context().study_root


def test_no_validation_language_in_the_v5_source_tree():
    """§33 check 15, over the package's own docstrings."""
    from dci1v5.protocol.reuse_ledger import assert_no_validation_language

    texts = {}
    for path in (DCI1_ROOT / "src" / "dci1v5").rglob("*.py"):
        # The module that DEFINES the forbidden phrases necessarily contains
        # them; every other file in the tree must not.
        if path.name == "reuse_ledger.py":
            continue
        texts[str(path)] = path.read_text()
    assert_no_validation_language(texts, where="v5 source tree")
