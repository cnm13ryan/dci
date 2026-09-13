"""§18 stage 1's manifest: what it binds, and the five reasons it refuses."""
from __future__ import annotations

import json

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v5.engine.context import registered_context
from dci1v5.protocol import constants as C
from dci1v5.protocol import manifest

REPO = registered_context().repo_root


def _manifest():
    return manifest.build_manifest(registered_context(),
                                   producing_commit="0" * 40,
                                   adoption={"status": "DRAFT"},
                                   repo_root=REPO)


def test_the_signature_is_refused_if_a_question_reopens(restore_open_items):
    """§18 stage 1's fifth refusal: an unresolved specification question.

    A4 opened U4 --- §12.6 made eligibility "§13's band on iota" and §13
    bands p_solo --- and A5 closed it at E2, so the refusal has to be
    provoked. A guard nothing provokes is a guard that quietly stopped
    working the moment the last question was answered.
    """
    restore_open_items.reopen_one_for_testing("U4")
    assert restore_open_items.blocking_items() == ("U4",)
    blockers = manifest.signing_blockers()
    kinds = {b["kind"] if isinstance(b, dict) else b.kind for b in blockers}
    assert "UNRESOLVED_SPECIFICATION" in kinds, blockers
    with pytest.raises(ProtocolError):
        manifest.assert_signable()


def test_nothing_else_blocks_the_signature():
    """The shape the refusals were built for, run to its end.

    Every one of them names a thing somebody has to do, and every one has
    been done: nineteen decisions closed, U2 resolved, P1 confirmed, the
    Calibration-B bank authored and hashed, the marker population approved,
    the model revisions pinned, the floor specified and the design derivable.
    A blocker disappears when the work it names is finished, and this asserts
    the list is empty for that reason rather than because it stopped looking.
    """
    assert manifest.signing_blockers() == []
    manifest.assert_signable()


def test_every_refusal_still_fires_when_its_reason_comes_back():
    """An empty blocker list is only evidence if a non-empty one is reachable.

    Each of these puts one condition back and asserts the named refusal
    returns --- so the list above is empty because the conditions hold, not
    because the checks were removed.
    """
    from dataclasses import replace as _replace

    from dci1v5.protocol import decisions, open_items

    def kinds():
        return {b["kind"] for b in manifest.signing_blockers()}

    original = dict(decisions.DECISIONS)
    try:
        decisions.DECISIONS["D5"] = _replace(
            decisions.DECISIONS["D5"], value=decisions.UNRESOLVED)
        assert "OPEN_DECISION" in kinds()
        decisions.DECISIONS.update(original)

        decisions.DECISIONS["D4"] = _replace(
            decisions.DECISIONS["D4"], value=decisions.UNRESOLVED)
        assert "CANDIDATE_POPULATION_UNAPPROVED" in kinds()
        decisions.DECISIONS.update(original)

        decisions.DECISIONS["D18"] = _replace(
            decisions.DECISIONS["D18"], value=decisions.UNRESOLVED)
        assert "OPEN_RED_TEAM_FINDING" in kinds()
        decisions.DECISIONS.update(original)

        decisions.DECISIONS["D1"] = _replace(
            decisions.DECISIONS["D1"], value=decisions.UNRESOLVED)
        assert {"OPEN_DECISION", "DESIGN_NOT_DERIVABLE"} <= kinds()
    finally:
        decisions.DECISIONS.clear()
        decisions.DECISIONS.update(original)

    u2 = open_items.OPEN_ITEMS["U2"]
    p1 = open_items.OPEN_ITEMS["P1"]
    try:
        open_items.OPEN_ITEMS["U2"] = _replace(u2, resolution=None)
        assert "UNRESOLVED_SPECIFICATION" in kinds()
        open_items.OPEN_ITEMS["U2"] = u2
        open_items.OPEN_ITEMS["P1"] = _replace(p1, resolution=None)
        assert "UNCONFIRMED_AT_ADOPTION" in kinds()
    finally:
        open_items.OPEN_ITEMS["U2"] = u2
        open_items.OPEN_ITEMS["P1"] = p1
    assert manifest.signing_blockers() == []


def test_an_unpinned_model_revision_refuses_the_signature(monkeypatch):
    """§6.1 binds the exact revision; a tag or a branch binds nothing."""
    from dataclasses import replace as _replace

    pinned = manifest.MODELS
    monkeypatch.setattr(
        manifest, "MODELS",
        (_replace(pinned[0], revision="main"),) + pinned[1:])
    by_kind = {b["kind"]: b for b in manifest.signing_blockers()}
    assert by_kind["MODEL_REVISION_UNPINNED"]["detail"] == \
        [pinned[0].model_key]


def test_a_floor_closure_with_no_spec_refuses_the_signature(
        tmp_path, monkeypatch):
    """§34 D17 at `floor` and no FloorSpec is a rule with no rule in it."""
    from dci1v5.protocol import decisions

    record = tmp_path / "researcher_decisions.json"
    record.write_text(json.dumps({
        "closures": [{"id": "D17", "value": "floor", "evidence": "e",
                      "decided_by": "t", "decided_on": "t"}]}))
    monkeypatch.setattr(decisions, "RECORD_PATH", record)
    by_kind = {b["kind"]: b for b in manifest.signing_blockers()}
    assert "FLOOR_NOT_SPECIFIED" in by_kind
    assert "does not invent" in by_kind["FLOOR_NOT_SPECIFIED"]["detail"]


def test_a_missing_topic_hash_is_still_a_refusal(restore_decisions):
    restore_decisions.override_for_testing("D3", "author_after_adoption")
    by_kind = {b["kind"]: b for b in manifest.signing_blockers()}
    assert by_kind["MISSING_TOPIC_HASH"]["calibration_b_status"] == \
        "AUTHORED_PENDING_D3"


def test_it_binds_the_nineteen_closures_and_what_they_did_not_take():
    built = _manifest()
    assert not set(manifest.REQUIRED_BINDINGS) - set(built)
    assert built["manifest_hash"]
    assert built["decisions"]["n_decisions"] == 19
    assert built["decisions"]["all_closed"] is True
    assert built["decisions"]["open"] == []
    assert built["open_items"]["blocking"] == []
    assert built["protocol_version"] == "5.0"
    # Every closure carries its evidence and who took it: §34 binds the
    # decision AND its evidence, and a closure with neither is a default.
    for entry in built["decisions"]["decisions"]:
        assert entry["status"] == "CLOSED"
        assert entry["evidence"] and entry["decided_by"] and \
            entry["decided_on"]
    # And the branches nobody took are named as not-adopted rather than
    # quietly retained, so a reader cannot mistake one for a live option.
    non_adopted = built["decisions"]["non_adopted_alternatives"]
    assert non_adopted["D17"] == ["no_floor"]
    assert set(non_adopted["D1"]) == {"four_models_47_cells",
                                      "two_models_56_cells", "384_blocks_m4"}


def test_it_binds_the_design_d1_actually_registered():
    """The arms, the scale and the budget --- recomputed, not quoted."""
    from dci1v5.design import budget

    built = _manifest()["design"]
    assert built["d1_value"] == "four_models_56_cells"
    registered = built["d1_registered"]
    assert registered["arms"] == list(C.ARMS)
    assert registered["cells_per_block"] == 56
    assert registered["models"] == 4
    assert registered["blocks"] == C.N_BLOCKS
    assert registered["draws_per_cell"] == C.M_DRAWS
    assert registered["total_generations"] == \
        registered["per_model"]["total"] * registered["models"]
    assert registered == budget.registered_budget()


def test_every_registered_threshold_is_a_value_and_not_a_branch_name():
    """`thresholds` is where a reader looks for what value refuses what.

    D17's entry named the *branch* — `"floor"` — and left the number in
    another file, which made the one threshold D17 registers the only one not
    readable in the block that carries every threshold. It is bound by value
    now, and this is what stops it becoming a label again.
    """
    from dci1v5.stages import construct_strength as CS

    thresholds = _manifest()["thresholds"]
    floor = thresholds["construct_floor"]
    assert floor["branch"] == "floor"
    assert floor["quantity"] == "chance_compliance"
    assert floor["value"] == 0.50
    assert floor["direction"] == "lower_is_stronger"
    assert floor["semantics"] == CS.POINT_REFUSES
    assert floor["marginal_status"] == CS.MARGINAL_STATUS
    assert floor["failure_status"] == "FOCAL_RANGE_EXHAUSTED"
    assert "load-zero" in floor["measured_on"]
    assert floor["derivation"] and floor["decided_by"] and floor["decided_on"]
    # And no other entry in the block is a bare branch name either.
    for name, value in thresholds.items():
        assert not (isinstance(value, str) and value.isidentifier()), \
            f"thresholds.{name} is a label, not a threshold"


def test_it_binds_the_eight_markers_and_their_accepted_limitations():
    built = _manifest()["marker_population"]
    assert built["approval_status"] == "approve_eight"
    assert built["n_markers"] == 8
    assert [m["word"] for m in built["markers"]] == [
        "thus", "hence", "though", "whereas", "indeed", "namely", "instead",
        "overall"]
    assert len(built["roles"]) == 6
    assert built["population_hash"]
    accepted = {x["word"] for x in built["accepted_limitations"]}
    assert {"though", "namely", "overall"} <= accepted


def test_it_binds_every_thing_the_registration_must_bind():
    built = _manifest()
    assert built["protocol_hash"] and built["reference_design_spec_hash"]
    assert built["topics"]["calibration_a_hash"]
    assert built["topics"]["calibration_b_hash"]
    assert built["topics"]["calibration_b_provenance"]["bank_hash"] == \
        built["topics"]["calibration_b_hash"]
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
    """A refused registration leaves no directory, key or partial artifact.

    Exercised by putting one blocker back rather than by relying on the
    repository being unready --- it is ready now, and a test that could only
    run before adoption is a test that stops testing at adoption.
    """
    from dataclasses import replace as _replace

    from dci1v5.engine.context import synthetic_context
    from dci1v5.protocol import decisions

    context = synthetic_context(tmp_path)
    held = decisions.DECISIONS["D5"]
    try:
        decisions.DECISIONS["D5"] = _replace(held,
                                             value=decisions.UNRESOLVED)
        with pytest.raises(manifest.Blocker):
            manifest.sign_registration(context, producing_commit="0" * 40,
                                       adoption={}, repo_root=REPO)
    finally:
        decisions.DECISIONS["D5"] = held
    assert not context.registration_manifest.exists()
    assert not context.signing_key_path.exists()


def test_signing_writes_a_verifiable_manifest_once(tmp_path):
    """The other half: what happens when nothing refuses.

    Signed into the **synthetic** namespace, which has its own root and its
    own key, so a test can exercise the signature without writing anything a
    reader could mistake for the registered study's registration.
    """
    from dci1v5.engine.context import synthetic_context

    context = synthetic_context(tmp_path)
    signed = manifest.sign_registration(
        context, producing_commit="0" * 40,
        adoption={"status": "TEST"}, repo_root=REPO)
    assert context.registration_manifest.exists()
    assert context.signing_key_path.exists()
    loaded = manifest.load_manifest(context)
    assert loaded["manifest_hash"] == signed["manifest_hash"]
    assert loaded["decisions"]["all_closed"] is True
    # Write-once: a second signature over the same root is refused, so a
    # registration cannot be quietly replaced by a later one.
    with pytest.raises(IntegrityError, match="write-once"):
        manifest.sign_registration(context, producing_commit="0" * 40,
                                   adoption={"status": "TEST"},
                                   repo_root=REPO)
