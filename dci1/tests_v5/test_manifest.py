"""§18 stage 1's manifest: what it binds, and the five reasons it refuses."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.engine.context import registered_context
from dci1v5.protocol import constants as C
from dci1v5.protocol import manifest

REPO = registered_context().repo_root


def _manifest():
    return manifest.build_manifest(registered_context(),
                                   producing_commit="0" * 40,
                                   adoption={"status": "DRAFT"},
                                   repo_root=REPO)


def test_the_manifest_refuses_and_names_all_five_reasons():
    kinds = {b["kind"] for b in manifest.signing_blockers()}
    assert kinds == {"OPEN_DECISION", "UNRESOLVED_SPECIFICATION",
                     "MISSING_TOPIC_HASH", "CANDIDATE_POPULATION_UNAPPROVED",
                     "OPEN_RED_TEAM_FINDING"}
    with pytest.raises(manifest.Blocker):
        manifest.assert_signable()


def test_the_reasons_are_separate_because_they_need_different_actions():
    """'we have not decided' and 'the work is not done' are different facts."""
    by_kind = {b["kind"]: b for b in manifest.signing_blockers()}
    assert by_kind["OPEN_DECISION"]["n"] == 19
    assert by_kind["MISSING_TOPIC_HASH"]["calibration_b_status"] == \
        "NOT_AUTHORED"
    assert by_kind["UNRESOLVED_SPECIFICATION"]["detail"][0]["id"] == "U2"


def test_it_assembles_anyway_so_adoption_can_be_inspected():
    built = _manifest()
    assert not set(manifest.REQUIRED_BINDINGS) - set(built)
    assert built["manifest_hash"]
    assert built["decisions"]["n_decisions"] == 19
    assert built["open_items"]["blocking"] == ["U2"]


def test_it_binds_every_thing_the_registration_must_bind():
    built = _manifest()
    assert built["protocol_hash"] and built["reference_design_spec_hash"]
    assert built["topics"]["calibration_a_hash"]
    assert built["topics"]["calibration_b_hash"] is None
    assert built["instruments"]["canonical_verifier_hash"]
    assert built["constraints"]["wording_hash"]
    assert len(built["models"]) >= 1
    assert built["measurement_basis"]["value"] == C.MEASUREMENT_BASIS
    assert set(built["multiplicity_families"]) == set(C.FAMILY_MEMBERS)
    assert built["order_estimands"]["members"] == list(C.FAMILY_MEMBERS["F11"])
    assert built["design"]["cells_full"] == 56


def test_a_model_adaptive_value_is_refused():
    """§6.1: n*, m*, the arm set and the admitted references never appear."""
    built = _manifest()
    manifest.assert_no_model_adaptive_values(built)
    with pytest.raises(ProtocolError, match="model-adaptive"):
        manifest.assert_no_model_adaptive_values({**built, "m_star": 9})
    with pytest.raises(ProtocolError, match="model-adaptive"):
        manifest.assert_no_model_adaptive_values(
            {**built, "design": {"admitted_arms": ["base"]}})


def test_the_status_vocabulary_is_study_wide_and_the_realised_set_is_not():
    """The distinction the key names carry.

    A replication's realised identification statuses are model-adaptive and
    live on its Gate 3C record; the registered vocabulary is study-wide.
    Naming the manifest key `identification_status_vocabulary` is what stops
    the two being confused by a reader or by the §6.1 guard.
    """
    built = _manifest()
    assert built["lifecycle"]["identification_status_vocabulary"] == \
        list(C.IDENTIFICATION_STATUSES)
    assert "identification_statuses" not in built["lifecycle"]


def test_a_missing_protocol_document_is_a_refusal_not_an_empty_hash():
    with pytest.raises(manifest.Blocker, match="binds the hash"):
        manifest.document_hashes("/nonexistent-root-for-this-test")


def test_signing_writes_nothing_while_it_refuses(tmp_path):
    from dci1v5.engine.context import synthetic_context

    context = synthetic_context(tmp_path)
    with pytest.raises(manifest.Blocker):
        manifest.sign_registration(context, producing_commit="0" * 40,
                                   adoption={}, repo_root=REPO)
    assert not context.registration_manifest.exists()
    assert not context.signing_key_path.exists()
