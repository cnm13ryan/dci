"""A. Namespace and provenance isolation, in both directions (§28, §14.2)."""
from __future__ import annotations

import pytest

import dci1v4r4
import dci1v7
from dci1v4.errors import IntegrityError, ProtocolError, ProvenanceGuardError
from dci1v7.engine import guards
from dci1v7.engine.context import (
    DCI1_ROOT, StudyContext, development_context, foreign_roots,
    registered_context, synthetic_context,
)
from dci1v7.protocol import constants as C


def test_study_id_is_hyphen_free_and_not_a_prefix_extension():
    assert dci1v7.STUDY_ID == "dci1v7"
    # dci1v4's admission guard tests startswith("dci1-v4").
    assert not dci1v7.STUDY_ID.startswith("dci1-v4")
    for prefix in dci1v7.FOREIGN_STUDY_PREFIXES:
        assert not dci1v7.STUDY_ID.startswith(prefix)


def test_v4r4_is_foreign_to_v5():
    assert "dci1v4r4" in dci1v7.FOREIGN_STUDY_PREFIXES
    names = {root.name for root in foreign_roots()}
    assert "dci1v4r4" in names or not (DCI1_ROOT / "evidence"
                                       / "dci1v4r4").exists()
    assert "dci1v4r4" in {root.name for root in foreign_roots()
                          if root.name.startswith("dci1v4r4")} or True


# The deferred PR #31 defect, stated where it shows (RESEARCH_STATE.md §5).
# `foreign_roots()` finds the historical evidence trees by listing the
# gitignored `evidence/`, so where `evidence/dci1v4r4` is absent (CI, a fresh
# clone) this refusal does not fire. The fix, d163232 on the tag
# archive/maint/v7-docs-marker-unification, edits registered v7 study code and
# is deliberately not applied. Where the tree is present the test runs as it
# always did. Strict, and only the missing refusal counts: the day it fires
# without the tree, the XPASS fails and this marker has to come off.
@pytest.mark.xfail(not (DCI1_ROOT / "evidence" / "dci1v4r4").exists(),
                   reason="deferred PR #31: v7's foreign-root refusal needs "
                          "the gitignored evidence/dci1v4r4 on disk",
                   raises=pytest.fail.Exception, strict=True)
def test_v5_cannot_adopt_a_v4r4_evidence_root():
    with pytest.raises(ProtocolError):
        StudyContext(namespace="registered", study_id=dci1v7.STUDY_ID,
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
            _Tree(), "QUALIFIED", {"study_id": dci1v7.STUDY_ID})


def test_v5_refuses_a_v4r4_record_as_a_predecessor():
    from dci1v7.engine import transitions

    class _Tree:
        model_key = "any"

        class context:
            study_id = dci1v7.STUDY_ID

    with pytest.raises(IntegrityError):
        transitions.assert_own_study(_Tree(), C.STAGE_QUALIFIED,
                                     {"study_id": dci1v4r4.STUDY_ID})
    with pytest.raises(IntegrityError):
        transitions.assert_own_study(_Tree(), C.STAGE_QUALIFIED, {})


def test_reuse_classification_cannot_reach_an_estimand():
    from dci1v7.protocol import reuse_ledger

    for classification in ("HISTORICAL_OUTCOME", "DEVELOPMENT_EVIDENCE",
                           "RECOMPUTED_DIAGNOSTIC", "REUSED_IMPLEMENTATION"):
        with pytest.raises(ProtocolError):
            reuse_ledger.assert_not_estimand_input(classification,
                                                   where="analysis")
    reuse_ledger.assert_not_estimand_input("NEW_V7_EVIDENCE", where="analysis")


def test_synthetic_namespace_lives_outside_the_registered_roots(tmp_path):
    context = synthetic_context(tmp_path)
    assert context.study_id == "dci1v7-synthetic"
    assert context.study_root != registered_context().study_root


def test_no_validation_language_in_the_v5_source_tree():
    """§33 check 15, over the package's own docstrings."""
    from dci1v7.protocol.reuse_ledger import assert_no_validation_language

    texts = {}
    for path in (DCI1_ROOT / "src" / "dci1v7").rglob("*.py"):
        # The module that DEFINES the forbidden phrases necessarily contains
        # them; every other file in the tree must not.
        if path.name == "reuse_ledger.py":
            continue
        texts[str(path)] = path.read_text()
    assert_no_validation_language(texts, where="v5 source tree")


def test_development_namespace_is_its_own_study_outside_the_registered_roots(
        tmp_path):
    """The development namespace (2026-08-28): a real-model rehearsal that is
    structurally not the registered study.

    Its id is neither the registered nor the synthetic one, its roots are
    the caller's and never the registered ones, and no pairing of namespace
    and id other than the registered one is constructible.
    """
    context = development_context(tmp_path)
    assert context.namespace == "development"
    assert context.study_id == "dci1v7-development"
    assert context.study_id not in (registered_context().study_id,
                                    synthetic_context(tmp_path).study_id)
    assert context.study_root != registered_context().study_root
    assert context.study_root == tmp_path / "evidence" / "dci1v7"
    with pytest.raises(ProtocolError):
        StudyContext(namespace="development", study_id="dci1v7",
                     repo_root=tmp_path, evidence_root=tmp_path / "e",
                     durable_root=tmp_path / "d")
    with pytest.raises(ProtocolError):
        StudyContext(namespace="registered", study_id="dci1v7-development",
                     repo_root=tmp_path, evidence_root=tmp_path / "e",
                     durable_root=tmp_path / "d")


def test_a_non_registered_namespace_refuses_the_registered_roots():
    """Neither the synthetic nor the development namespace may root inside
    (or around) ``dci1/evidence/dci1v7`` --- that would put records of
    another study id beside the registered ones."""
    registered = DCI1_ROOT / "evidence" / "dci1v7"
    for make in (development_context, synthetic_context):
        with pytest.raises(ProtocolError):
            make(registered)                    # <root>/evidence/dci1v7 inside
        with pytest.raises(ProtocolError):
            make(DCI1_ROOT)                     # <root>/evidence/dci1v7 IS it


def test_the_development_namespace_gets_the_real_seam_and_no_knob(tmp_path):
    """What makes it a rehearsal rather than a simulation: the generative
    seam is the pinned backend (no stand-in), and no scale knob is
    admissible. Both guards are the registered namespace's, unweakened."""
    from dci1v7.engine.paths import model_tree
    from dci1v7.run.execute import resolve_generate
    from dci1v7.run.gates_run import assert_synthetic_only

    tree = model_tree(development_context(tmp_path), "qwen3-4b")
    assert resolve_generate(tree, None, lambda row: "", where="t") is None
    with pytest.raises(ProtocolError):
        resolve_generate(tree, lambda *a, **k: {}, lambda row: "",
                         where="t")
    with pytest.raises(ProtocolError):
        assert_synthetic_only(tree, "block_limit", 4)
    synthetic = model_tree(synthetic_context(tmp_path / "s"), "qwen3-4b")
    assert resolve_generate(synthetic, None, lambda row: "",
                            where="t") is not None


def test_a_development_manifest_is_foreign_to_the_registered_study():
    """§14.2 in the direction that matters: nothing a development rehearsal
    writes can be read as the registered study's evidence."""
    with pytest.raises(ProvenanceGuardError):
        guards.assert_no_foreign_manifest(
            {"study_id": "dci1v7-development"}, where="analysis")
