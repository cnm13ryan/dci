"""The whole registered lifecycle, executed with no model and no science.

Marked ``slow`` because it runs eighteen stages over a reduced but real
design. It is the test that finds what only appears when a path executes; the
defects it found while it was being written are recorded in
``dci1/reports/dci1v5/v5_reconciliation.md``.

Its artifacts live in ``tmp_path`` under the ``synthetic`` namespace and are
deleted with the test. ``StudyContext`` refuses a synthetic root that overlaps
the registered evidence tree or any historical study's, so this cannot write
into one however it is invoked.
"""
from __future__ import annotations

import pytest

from dci1v7 import STUDY_ID
from dci1v7.engine import transitions
from dci1v7.protocol import constants as C
from dci1v7.run import contracts, final_report_checks
from dci1v7.stages import audit_prefreeze

from tests_v7 import synthetic_lifecycle as SL


@pytest.fixture(scope="module")
def walked(tmp_path_factory):
    """The walk, against an isolated repository it builds and commits.

    ``walk`` builds that repository itself, so every provenance rule --- clean
    worktree, resolvable head, protocol document hashes --- runs unwaived
    against a tree that genuinely satisfies it rather than being excused.
    """
    SL.resolved_manifest()
    try:
        yield SL.walk(tmp_path_factory.mktemp("v5-synthetic"))
    finally:
        SL.restore()


@pytest.mark.slow
def test_every_registered_stage_produced_a_signed_record(walked):
    payloads = walked["payloads"]
    assert list(payloads) == list(C.STAGE_SEQUENCE)
    tree = walked["tree"]
    for stage in C.STAGE_SEQUENCE:
        record = transitions.read_stage_record(tree, stage)
        assert record["outcome"] in ("PASS", "FAIL")
        assert record["artifact_type"] == C.STAGE_ARTIFACT_TYPE[stage]
        assert record["study_id"] == tree.context.study_id


@pytest.mark.slow
def test_the_producer_consumer_contract_holds_against_real_payloads(walked):
    """The point of the harness: a required field with no producer.

    The static audit can only check that the *declared* producer precedes the
    reader. Whether the producer actually writes the field is a fact about the
    payload, and this is where it becomes one.
    """
    result = contracts.audit_contracts(walked["payloads"])
    assert result["clean"], result["defects"]
    assert result["n_checked_against_payloads"] == result["n_fields"]


@pytest.mark.slow
def test_nothing_it_wrote_can_be_mistaken_for_v5_evidence(walked):
    tree = walked["tree"]
    assert tree.context.study_id == f"{STUDY_ID}-synthetic"
    assert tree.context.study_id != STUDY_ID
    rows = __import__("dci1v7.run.confirmatory_run", fromlist=["x"]) \
        .collect_rows(tree)
    assert rows and all(r["synthetic"] for r in rows)
    assert all(r["study_id"] == tree.context.study_id for r in rows)


@pytest.mark.slow
def test_the_freeze_binds_the_design_the_confirmatory_run_used(walked):
    freeze = walked["payloads"][C.STAGE_GATE5]
    confirmatory = walked["payloads"][C.STAGE_CONFIRMATORY]
    assert confirmatory["freeze_hash"] == freeze["freeze_hash"]
    assert confirmatory["cells_per_block"] == freeze["cells_per_block"]
    assert confirmatory["admitted_arms"] == freeze["admitted_arms"]
    assert confirmatory["completeness"]["complete"]
    assert confirmatory["completeness"]["n_missing"] == 0
    assert confirmatory["completeness"]["n_duplicate"] == 0


@pytest.mark.slow
def test_gate4_measured_every_registered_cell_type(walked):
    gate4 = walked["payloads"][C.STAGE_GATE4]
    gate3c = walked["payloads"][C.STAGE_GATE3C]
    assert gate4["n_cell_types"] == gate3c["derived_cell_count"]
    assert gate4["rows"] == gate4["expected_rows"]
    assert gate4["selects_nothing"] is True
    # §33 check 8 requires the refusal to be *declared*, not merely absent.
    declared = gate4[audit_prefreeze.DECLARED_REFUSALS_KEY]
    assert "no_substitution_after_a_reading" in declared
    assert "no_composed_rate_terminates_a_replication" in declared
    assert gate4["outcome"] == "PASS" and gate4["terminates_nothing"] is True
    assert "composed_contrast" in gate4


@pytest.mark.slow
def test_the_mask_is_sealed_before_the_unmask_and_the_unmask_is_once(walked):
    tree = walked["tree"]
    masked = walked["payloads"][C.STAGE_MASKED_ANALYSIS]
    unmask = walked["payloads"][C.STAGE_UNMASKING]
    assert masked["sealed"] is True
    assert unmask["analysis_code_hash"] == masked["analysis_code_hash"]
    from dci1v4.errors import IntegrityError

    # Write-once, by the stage machine. Naming the error matters: a second
    # unmask failing for some *other* reason would pass a blind assertion and
    # leave the one-shot guarantee untested.
    with pytest.raises(IntegrityError, match="write-once"):
        __import__("dci1v7.run.analysis_run", fromlist=["x"]) \
            .run_unmasking(tree, producing_commit="0" * 40)


@pytest.mark.slow
def test_an_unidentified_quantity_is_named_not_zeroed(walked):
    analysis = walked["payloads"][C.STAGE_UNMASKED_ANALYSIS]
    for bucket in analysis["estimands"]["configurations"].values():
        for entry in bucket.values():
            assert entry["status"] in ("IDENTIFIED", "NOT_IDENTIFIED")
            if entry["status"] == "NOT_IDENTIFIED":
                assert entry["reason"]
                assert "point" not in entry


@pytest.mark.slow
def test_the_final_report_traces_every_row_to_a_stage_record(walked):
    report = walked["payloads"][C.STAGE_FINAL_REPORT]
    assert report["results"]
    assert report["n_result_rows"] == len(report["results"])
    for row in report["results"]:
        assert row["source_stage"] == C.STAGE_UNMASKED_ANALYSIS
        assert row["freeze_hash"]
    assert report["stage_record_hashes"]


@pytest.mark.slow
def test_no_stage_may_run_twice(walked):
    from dci1v4.errors import IntegrityError

    tree = walked["tree"]
    with pytest.raises(IntegrityError, match="write-once"):
        transitions.assert_transition_legal(tree, C.STAGE_GATE4)


@pytest.mark.slow
def test_a_scale_parameter_is_refused_in_the_registered_namespace():
    from dci1v7.engine.context import registered_context
    from dci1v7.engine.paths import model_tree
    from dci1v7.run.gates_run import assert_synthetic_only

    tree = model_tree(registered_context(), SL.MODEL_KEY)
    with pytest.raises(Exception, match="synthetic namespace"):
        assert_synthetic_only(tree, "topic_limit", 24)


# ---------------------------------------------------- stage 14, in detail

@pytest.mark.slow
def test_the_confirmatory_row_identities_are_exactly_the_licensed_plan(walked):
    """Every (block, cell, draw) once: none missing, duplicated or extra."""
    from dci1v7.run import confirmatory_run

    tree, payload = walked["tree"], walked["payloads"][C.STAGE_CONFIRMATORY]
    design = confirmatory_run.licensed_design(tree, bank=walked["bank"])
    design = {**design, "blocks": design["blocks"][:payload["blocks"]]}
    rows = confirmatory_run.collect_rows(tree)
    report = confirmatory_run.completeness(design, rows)
    assert report["complete"]
    assert report["n_missing"] == report["n_duplicate"] == 0
    assert report["n_unexpected"] == 0
    expected = (payload["blocks"] * payload["cells_per_block"]
                * payload["draws"])
    assert report["expected"] == expected == len(rows)
    assert len({r["row_id"] for r in rows}) == len(rows)
    assert {r["block_id"] for r in rows} == {
        b.block_id for b in design["blocks"]}
    assert {r["draw_index"] for r in rows} == set(range(payload["draws"]))


@pytest.mark.slow
def test_every_confirmatory_row_carries_its_execution_identity(walked):
    from dci1v7.run import confirmatory_run

    rows = confirmatory_run.collect_rows(walked["tree"])
    for row in rows:
        assert row["prompt_hash"] and row["seed"]
        assert row["verifier_hash"]
        assert row["truncated"] in (True, False)
        assert row["empty"] in (True, False)
        assert "finish_reason" in row and "token_count" in row
        assert row["topic_split"] == "confirmatory"
    # The seed is a function of (stage, model, prompt, draw), so two draws of
    # one cell differ and two cells never share one.
    assert len({r["seed"] for r in rows}) == len(rows)
    by_cell = {}
    for row in rows:
        by_cell.setdefault((row["block_id"], row["cell_id"]), set()).add(
            row["prompt_hash"])
    assert all(len(v) == 1 for v in by_cell.values())


@pytest.mark.slow
def test_the_presence_rule_holds_on_every_confirmatory_row(walked):
    """§9.1 per row: stated is present, everything else is absent, and every
    registered instance carries a verdict."""
    from dci1v7.run import confirmatory_run

    tree = walked["tree"]
    design = confirmatory_run.licensed_design(tree, bank=walked["bank"])
    instances = {c.label for c in design["slot_map"].values()}
    slot_of = {c.label: s for s, c in design["slot_map"].items()}
    for row in confirmatory_run.collect_rows(tree):
        labels = {f"{s['kind']}:{s['severity']}" for s in row["scores"]}
        assert labels == instances
        stated = {slot_of[f"{s['kind']}:{s['severity']}"]
                  for s in row["scores"] if s["present"]}
        assert stated == set(row["slots"])
        assert all(s["slot"] for s in row["scores"])


@pytest.mark.slow
def test_a_resumed_batch_reproduces_every_row_identity(walked):
    """§26: a restart is cheap and a *silent* restart is impossible."""
    from dci1v7.run import confirmatory_run

    tree = walked["tree"]
    design = confirmatory_run.licensed_design(tree, bank=walked["bank"])
    design = {**design,
              "blocks": design["blocks"][
                  :walked["payloads"][C.STAGE_CONFIRMATORY]["blocks"]]}
    before = {r["row_id"]: r for r in confirmatory_run.collect_rows(tree)}
    again = confirmatory_run.run_batch(
        tree, design, start=0, stop=len(design["blocks"]),
        generate=SL._scripted_for(SL.screen_rungs() + SL._bound_constraints(
            tree)))
    assert {r["row_id"] for r in again} == set(before)
    assert all(r["resumed"] for r in again)
    # `resumed` is provenance and it is the ONLY field a resume may change.
    # Nothing scientific --- not the text, not the seed, not the prompt, not a
    # single verdict --- differs from the committed row.
    for row in again:
        original = before[row["row_id"]]
        differing = {k for k in row
                     if row[k] != original.get(k)}
        assert differing == {"resumed"}, differing
    # Re-running a batch outside a stage leaves the durable mirror one field
    # stale, because `run_stage` is what mirrors. Restore it, so this test
    # does not make a later durability check fail for a reason it did not
    # cause.
    from dci1v7.run.lifecycle import mirror_records

    mirror_records(tree, C.STAGE_CONFIRMATORY)


@pytest.mark.slow
def test_a_design_that_does_not_match_the_freeze_is_refused(walked):
    from dci1v4.errors import ProtocolError
    from dci1v7.run.freeze_run import assert_matches_freeze
    from dci1v7.run.confirmatory_run import load_freeze

    record = load_freeze(walked["tree"])
    with pytest.raises(ProtocolError):
        assert_matches_freeze(record, claimed={"admitted_arms": ["base"]},
                              where="test")


# ------------------------------------------- stages 15-17, in detail

@pytest.mark.slow
def test_the_masked_artifact_carries_no_companion_identity(walked):
    import json

    from dci1v7.analysis import masking

    tree = walked["tree"]
    lines = tree.masked_view("confirmatory_mask").read_text().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    assert records
    masking.assert_masked_view_clean(records)
    assert all("companion_label" in r and "masked_cell_id" in r
               for r in records)
    masked = walked["payloads"][C.STAGE_MASKED_ANALYSIS]
    assert masked["masked_result_hash"]
    assert masked["mask_effectiveness"]
    # §20's one named function, recorded rather than assumed.
    contrasts = masked["masked_phase_order_contrasts"]
    assert set(contrasts["computable"]) | set(contrasts["not_computable"]) \
        == set(C.FAMILY_MEMBERS["F11"])
    assert contrasts["rule"].startswith("§20")
    # `arm` is carried and cannot discriminate among permuted labels: it takes
    # three design-level values, and every observation the mask could have
    # swapped with another shares one of them. A permutation moves labels
    # *within* an (outcome, configuration, block) group, and every composed
    # observation in such a group has arm "composed" --- so knowing the arm
    # narrows the true companion not at all.
    assert {r["arm"] for r in records} <= {"unconstrained", "solo",
                                           "composed"}
    groups: dict[tuple, set] = {}
    for record in records:
        if record["companion_label"] is None:
            continue
        assert record["arm"] == "composed"
        groups.setdefault((record["outcome_slot"], record["configuration"],
                           record["block_id"]), set()).add(record["arm"])
    assert groups and all(v == {"composed"} for v in groups.values())


@pytest.mark.slow
def test_delta_difficulty_is_post_unmask_and_only_post_unmask(walked):
    """§20: A's point is inside the permuted group, so the masked phase has
    no value for it --- and the unmasked phase must have one."""
    masked = walked["payloads"][C.STAGE_MASKED_ANALYSIS]["masked_result"]
    unmasked = walked["payloads"][C.STAGE_UNMASKED_ANALYSIS]["estimands"]
    assert masked["spectrum_phase"] == "masked"
    assert unmasked["spectrum_phase"] == "post_unmask"
    for bucket in masked["configurations"].values():
        # §20 names both: A's point is inside the permuted group, so neither
        # the residual nor the excess has a masked-phase value.
        for member in ("delta_difficulty", "Delta_R"):
            entry = bucket[member]
            assert entry["status"] == "NOT_IDENTIFIED"
            assert entry["reason"] == "MASKED_PHASE"
            assert "point" not in entry
    assert set(masked["masked_phase_members_withheld"]) >= {
        "delta_difficulty", "Delta_R"}
    assert masked["intervals"]
    for family in masked["intervals"].values():
        if isinstance(family, dict):
            assert "Delta_R" not in family
            assert "delta_difficulty" not in family
    for configuration, bucket in unmasked["configurations"].items():
        entry = bucket["delta_difficulty"]
        assert entry["status"] in ("IDENTIFIED", "NOT_IDENTIFIED")
        if entry["status"] == "IDENTIFIED":
            assert entry["refit_per_replicate"] is True
            # And it is a member of F1's simultaneous interval, which is what
            # the multiplicity correction is computed over.
            family = unmasked["intervals"][f"F1:{configuration}"]
            assert "delta_difficulty" in family


@pytest.mark.slow
def test_every_registered_quantity_is_named_with_a_status(walked):
    analysis = walked["payloads"][C.STAGE_UNMASKED_ANALYSIS]
    estimands = analysis["estimands"]
    registered = {"D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "Xi",
                  "Delta_1", "Delta_2", "Delta_3", "Delta_near",
                  "Delta_broad", "Delta^A", "D(Rbar<-A)", "D(Rbar<-B)",
                  "D(Rbar<-Rbar')", "delta_difficulty"}
    for configuration in C.CONFIGURATIONS:
        assert registered <= set(estimands["configurations"][configuration])
    assert set(estimands["cross_configuration"]) == set(
        C.FAMILY_MEMBERS["F11"])


@pytest.mark.slow
def test_a_headline_estimate_recomputes_from_the_rows(walked):
    """D(B<-A) recomputed by hand from the committed rows.

    Deliberately not through ``ObservationTable``: the point is a second
    path to the same number, not the same path twice.
    """
    from dci1v7.run import confirmatory_run

    rows = confirmatory_run.collect_rows(walked["tree"])
    per_cell: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        for score in row["scores"]:
            if not score["present"] or score["slot"] != "B":
                continue
            per_cell.setdefault((row["block_id"], row["cell_id"]), []).append(
                1.0 if score["passed"] else 0.0)
    means = {k: sum(v) / len(v) for k, v in per_cell.items()}
    blocks = sorted({k[0] for k in means})
    losses = [means[(b, "solo:B")] - means[(b, "pair:A+B")] for b in blocks]
    expected = sum(losses) / len(losses)
    entry = walked["payloads"][C.STAGE_UNMASKED_ANALYSIS]["estimands"][
        "configurations"][C.OUTCOME_SECOND]["D(B<-A)"]
    assert entry["status"] == "IDENTIFIED"
    assert entry["point"] == pytest.approx(expected, abs=1e-9)


@pytest.mark.slow
def test_re_masking_after_the_unmask_is_refused(walked):
    from dci1v4.errors import IntegrityError

    from dci1v7.run import analysis_run

    tree = walked["tree"]
    with pytest.raises(IntegrityError, match="write-once"):
        transitions.assert_transition_legal(tree, C.STAGE_MASKED_ANALYSIS)
    with pytest.raises(IntegrityError, match="write-once"):
        transitions.assert_transition_legal(tree, C.STAGE_UNMASKING)
    with pytest.raises(IntegrityError, match="write-once"):
        analysis_run.run_masked_analysis(tree, producing_commit="0" * 40)


# ------------------------------------------------------ stage 18, in detail

@pytest.mark.slow
def test_the_final_report_runs_its_own_checks_and_they_pass(walked):
    report = walked["payloads"][C.STAGE_FINAL_REPORT]
    assert report["outcome"] == "PASS"
    assert report["blocked"] == []
    checks = {c["check"]: c for c in report["final_report_checks"]}
    assert len(checks) == len(final_report_checks.FINAL_REPORT_CHECKS)
    for name, _why, mandatory in final_report_checks.FINAL_REPORT_CHECKS:
        assert checks[name]["verdict"] == "PASS", checks[name]
        assert checks[name]["mandatory"] is mandatory


@pytest.mark.slow
def test_the_deferred_prefreeze_check_is_discharged_at_the_final_report(
        walked):
    """§33 check 14 reads the table, so stage 12 deferred it to here."""
    audit = walked["payloads"][C.STAGE_PREFREEZE_AUDIT]["checklist"]
    deferred = {c["n"] for c in audit["deferred_to_final_report"]}
    assert deferred == {14}
    report = walked["payloads"][C.STAGE_FINAL_REPORT]
    entry = next(c for c in report["final_report_checks"]
                 if c["check"] == "deferred_prefreeze_checks_discharged")
    assert entry["verdict"] == "PASS"
    assert entry["detail"]["deferred_by_the_audit"] == [14]
    assert entry["detail"]["not_run"] == []
    assert entry["detail"]["n_numbers_traced"] == report["n_result_rows"]
    assert all(r["verdict"] == "PASS"
               for r in entry["detail"]["rerun_over_the_report_text"])


@pytest.mark.slow
def test_every_result_row_carries_every_field_section_31_lists(walked):
    from dci1v7.stages.final_report import ROW_FIELDS

    report = walked["payloads"][C.STAGE_FINAL_REPORT]
    assert report["results"]
    for row in report["results"]:
        assert not [f for f in ROW_FIELDS if f not in row]
        assert row["stage_record"] == C.STAGE_UNMASKED_ANALYSIS
        assert row["stage_record_hash"]
        assert row["measurement_basis"] == C.MEASUREMENT_BASIS
        assert row["cell_counts"]["blocks"] > 0
        assert row["variance_decomposition"]
        if row["status"] == "IDENTIFIED":
            assert row["estimate"] is not None
            assert row["simultaneous_lower"] <= row["simultaneous_upper"]
            assert row["standard_error"] is not None


@pytest.mark.slow
def test_a_failing_mandatory_final_report_check_fails_the_stage(walked):
    """Stage 18 has no successor to refuse it, so the failure is its own."""
    from dci1v7.run import final_report_checks as frc

    tree = walked["tree"]
    report = dict(walked["payloads"][C.STAGE_FINAL_REPORT])
    report["identification_statuses"] = ["POSITION_CONFOUNDED"]
    checks = frc.final_report_checks(tree, report,
                                     repo_root=tree.context.repo_root)
    failed = [c for c in checks
              if c["mandatory"] and c["verdict"] != "PASS"]
    assert [c["check"] for c in failed] == [
        "identification_statuses_trace_to_the_freeze"]


# ------------------------------------------------------------ isolation

@pytest.mark.slow
def test_no_synthetic_artifact_reached_the_real_v5_roots(walked):
    """§28: the registered roots hold nothing this harness wrote."""
    import json

    from dci1v7.engine.context import registered_context

    registered = registered_context()
    synthetic_id = walked["tree"].context.study_id
    leaked: list[str] = []
    for root in (registered.study_root,
                 registered.durable_root / "dci1v7"):
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            try:
                payload = json.loads(path.read_text())
            except Exception:                               # pragma: no cover
                continue
            body = payload.get("payload", payload)
            if isinstance(body, dict) and body.get("study_id") == synthetic_id:
                leaked.append(str(path))
    assert leaked == []
    # And the harness's own roots are outside both.
    assert not walked["tree"].root.is_relative_to(registered.study_root)
    assert not walked["tree"].durable.is_relative_to(registered.durable_root)
