"""What the 2026-08-25 design pass added, and the invariants it turns on.

Four groups, and they are not the same kind of claim. **Placement** is the rule
that puts a stand-in where the design puts a companion. **Isolation** is the
set of populations a `probe_only` family must stay out of, checked one by one
rather than by asserting the flag exists. **Licensing** is what v6 says at
study level, registered before data. **Adoption** is the refusal that keeps a
complete draft from being mistaken for a registration by being present.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v6.design import budget
from dci1v6.engine.context import REPO_ROOT
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions, manifest
from dci1v6.run import lifecycle, regime_run
from dci1v6.stages import composed_probe as P
from dci1v6.verifiers import constraints as K

REPORTS = Path(__file__).resolve().parents[1] / "reports" / "dci1v6"


# ------------------------------------------------------------- placement

def _ladder(values: dict[int, float]) -> dict[str, dict[int, float]]:
    return {"PS1": dict(values)}


def test_a_standin_is_placed_where_the_design_puts_a_companion():
    """§13.8 matches a reference's iota(R) to iota_A, so that is the target.

    Not FOCAL_AIM: B's aim is where the design puts the *focal* constraint,
    and a stand-in that stood in for a companion by sitting at B's operating
    point would sit where nothing in the design ever puts one.
    """
    curve = {1: 0.20, 2: 0.35, 3: 0.55, 4: 0.72, 5: 0.88}
    out = P.standin_operating_points(_ladder(curve), iota_a=0.56)
    assert out["PS1"]["severity"] == 3
    assert out["PS1"]["aim"] == 0.56
    assert out["PS1"]["band"] == list(C.HEADROOM_BAND)
    # A different iota_A moves it, and nothing else does.
    assert P.standin_operating_points(
        _ladder(curve), iota_a=0.85)["PS1"]["severity"] == 5


def test_a_standin_severity_does_not_depend_on_the_operating_point():
    """The invariant that lets a re-selection re-probe a severity without
    changing the companion it is composed with.

    iota_A is measured at Gate 2 and does not move with m*, so the same
    ladder and the same iota_A give the same severity however many severities
    the probe walks.
    """
    curve = {1: 0.20, 2: 0.35, 3: 0.55, 4: 0.72, 5: 0.88}
    first = P.standin_operating_points(_ladder(curve), iota_a=0.56)
    again = P.standin_operating_points(_ladder(curve), iota_a=0.56)
    assert first["PS1"]["severity"] == again["PS1"]["severity"]
    assert "m_star" not in json.dumps(first)


def test_a_standin_outside_section_13_4s_band_is_not_clamped(): 
    """A stand-in no severity of which could be admitted as a companion is
    not a stand-in for one, and it is **never** clamped to a severity outside
    §13.4's band. That property is what this has always protected and it is
    unchanged.

    What changed on 2026-08-27 (A17) is the *shape* of the answer. It used to
    raise, which let a `probe_only` instrument end the stage --- the one power
    `no_standin_entry_ends_a_replication` exists to deny it. It now records
    `STANDIN_UNPLACEABLE` with the measured ladder and the reason, and the
    verdict is left to the six determinate entries, as it already was.
    """
    out = P.standin_operating_points(
        _ladder({1: 0.97, 2: 0.98, 3: 0.99}), iota_a=0.6)["PS1"]
    assert out["severity"] is None            # not clamped to 1, 2 or 3
    assert out["placed"] is False
    assert out["status"] == C.STANDIN_UNPLACEABLE
    assert "§13.4" in out["reason"]
    assert out["curve"] == {"1": 0.97, "2": 0.98, "3": 0.99}
    assert P.unplaceable_standins({"PS1": out}) == ("PS1",)
    assert P.placed_standins({"PS1": out}) == ()


def test_an_unplaceable_standin_costs_cells_and_decides_nothing():
    """A17. Every cell that loses its companion is marked, and every one of
    them is stand-in-dependent --- so the set that cannot be measured and the
    set that could never have entered the verdict are the same set.

    Asserted over the whole registered shape rather than a hand-picked cell,
    so a future cell type that put a stand-in on a determinate entry would
    fail here instead of quietly entering a feasibility verdict.
    """
    slots = P.probe_slots(3)
    shape = P.probe_cell_types(slots)
    unmeasured = P.unmeasured_probe_cells(shape, ["P1"])
    assert unmeasured, "P1 carries cells"
    for cell_id, entry in unmeasured.items():
        assert "P1" in entry["requires_unplaceable_slots"]
        assert entry["status"] == C.NOT_MEASURED_STANDIN_UNPLACEABLE
        assert entry["determinate"] is False
        assert entry["enters_the_verdict"] is False
    # the determinate six are untouched, whichever stand-in is unplaceable
    for slot in slots:
        lost = set(P.unmeasured_probe_cells(shape, [slot]))
        assert lost.isdisjoint({"solo:A", "solo:B", "pair:A+B", "pair:B+A"})
    # and with every stand-in unplaceable, what remains is exactly the
    # determinate shape plus the unconstrained cell
    all_lost = set(P.unmeasured_probe_cells(shape, list(slots)))
    remaining = [c for c, _a, _s in shape if c not in all_lost]
    assert remaining == ["unconstrained", "solo:A", "solo:B",
                         "pair:A+B", "pair:B+A"]


def test_the_probe_diagnostic_statuses_decide_nothing():
    """Neither status is a §28 terminal outcome nor a stage-1 readiness
    refusal. A `probe_only` instrument cannot end anything."""
    assert C.STANDIN_UNPLACEABLE in C.PROBE_DIAGNOSTIC_STATUSES
    assert C.NOT_MEASURED_STANDIN_UNPLACEABLE in C.PROBE_DIAGNOSTIC_STATUSES
    assert set(C.PROBE_DIAGNOSTIC_STATUSES).isdisjoint(C.TERMINAL_STATUSES)
    assert set(C.PROBE_DIAGNOSTIC_STATUSES).isdisjoint(
        C.READINESS_REFUSAL_STATUSES)


# ------------------------------------------------------------- isolation

def test_the_screen_measures_the_selectable_pool_and_asserts_it():
    """§12.2's table is the candidate population and §12.6 counts feature
    groups and straddling families over it, so a stand-in screened there
    would enter a count it can never be selected from."""
    rungs = regime_run._screen_rungs()
    kinds = {r.kind for r in rungs}
    assert kinds.isdisjoint(K.PROBE_ONLY_FAMILY_IDS)
    assert kinds == set(K.SELECTABLE_FAMILY_IDS) | {"A", "B"}


def test_the_candidate_budget_counts_the_selectable_pool_only():
    """Three families were added to the library and none of them is a
    candidate, so every term costing the candidate pipeline is unmoved."""
    lib = budget.library()
    assert lib["tier_1"]["families"] == 8
    assert lib["tier_2"]["families"] == 3
    assert lib["tier_3"]["families"] == 26
    assert lib["probe_only"]["families"] == 3
    assert lib["probe_only"]["counted_in_the_candidate_pipeline"] is False
    # v5's screen, exactly: 326 selectable round-0 rungs + A's 8 + B's 8.
    assert budget.screen_rungs() == 326 + 8 + 8


def test_the_probe_burden_is_derived_from_the_shape_and_not_a_formula():
    """A formula in the budget stops tracking the shape the first time a
    Gate-4 exposure class is added."""
    burden = budget.probe_burden()
    assert burden["cell_types"] == len(
        P.probe_cell_types(P.probe_slots(3)))
    assert burden["cells_read_from_gate2"] == len(P.SHARED_WITH_GATE2)
    assert burden["gate4_classes_covered"] == 10
    assert burden["gate4_entries_audited_later"] == 95
    assert burden["rows_at_the_operating_point"] == (
        burden["cells_generated_per_severity"] * C.N_CALIBRATION * C.M_CAL)
    assert burden["ladder_rows"] == (
        burden["ladder_rungs"] * C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS)
    # m* is frozen, so the cost is exact rather than a ceiling: one severity,
    # and no parameter by which a caller could cost a search.
    assert burden["severities"] == 1
    assert burden["rows"] == (
        burden["ladder_rows"] + burden["rows_at_the_operating_point"])
    import inspect
    assert "n_severities" not in inspect.signature(
        budget.probe_burden).parameters


# ------------------------------------------------------------- licensing

def test_a_single_survivor_licenses_its_own_ladder_and_nothing_above_it(
        restore_decisions):
    restore_decisions.override_for_testing("D25", "survivor_ladder_only")
    out = lifecycle.study_level_statement(
        survivors=["gemma-3n-e2b-it"],
        terminal={"qwen3-4b": "COMPOSED_HEADROOM_FAILURE"})
    assert out["n_survivors"] == 1
    assert out["rule"] == "§34 D25"
    assert "L5 is withheld by design" in out["statement"]
    assert "never evidence about the effect" in out["statement"]
    assert out["terminal"] == {"qwen3-4b": "COMPOSED_HEADROOM_FAILURE"}


def test_the_other_single_survivor_reading_exists_and_is_different(
        restore_decisions):
    restore_decisions.override_for_testing("D25", "no_study_level_statement")
    out = lifecycle.study_level_statement(survivors=["qwen3-4b"])
    assert out["statement"] == \
        lifecycle.SINGLE_SURVIVOR_STATEMENTS["no_study_level_statement"]
    assert out["statement"] != \
        lifecycle.SINGLE_SURVIVOR_STATEMENTS["survivor_ladder_only"]


def test_the_zero_and_many_survivor_sentences_are_not_decisions(
        restore_decisions):
    """They follow from §6.1 and the claim ladder, so they are emitted with
    D25 open --- which is also the check that D25 gates only the case it is
    about."""
    restore_decisions.reopen_all_for_testing()
    assert "D25" in decisions.open_decisions()
    none = lifecycle.study_level_statement(survivors=[])
    assert none["rule"] == "§6.1"
    assert "no claim about the effect at any level" in none["statement"]
    many = lifecycle.study_level_statement(survivors=["a", "b", "c"])
    assert "never pooled" in many["statement"]
    assert "L5 is withheld" in many["statement"]
    for out in (none, many):
        assert out["l5_withheld"].startswith("generalisation is never")


def test_the_single_survivor_case_refuses_while_d25_is_open(
        restore_decisions):
    restore_decisions.reopen_all_for_testing()
    assert "D25" in decisions.open_decisions()
    with pytest.raises(decisions.DecisionOpenError):
        lifecycle.study_level_statement(survivors=["one"])


def test_per_replication_licensing_does_not_read_another_replication(
        restore_decisions):
    """Another model's failure must not suppress a valid model-specific
    result: that is the whole content of §34 D22's per-replication branch."""
    restore_decisions.override_for_testing("D22", "per_replication")
    alone = lifecycle.confirmatory_licensed(
        this_replication_frozen=True, survivors=["me"])
    assert alone["licensed"] is True
    assert lifecycle.confirmatory_licensed(
        this_replication_frozen=False, survivors=["me", "you"]
    )["licensed"] is False
    restore_decisions.override_for_testing("D22", "two_survivors_before_any")
    withheld = lifecycle.confirmatory_licensed(
        this_replication_frozen=True, survivors=["me"])
    assert withheld["licensed"] is False


# ------------------------------------------------------------- adoption

def test_both_governed_documents_declare_themselves_adopted():
    """Adoption is a researcher act and it is recorded in the documents
    themselves, where the manifest guard reads it.

    The refusal for a document that does NOT say so is exercised in
    ``test_a_missing_declaration_reads_as_a_draft`` and in
    ``test_lifecycle.test_the_adoption_guard_reads_what_each_document_says_``
    ``about_itself``, both against roots built for the purpose --- so this
    pair of assertions is not the only thing standing between a draft and a
    registration.
    """
    from dci1v6 import PREREGISTRATION, REFERENCE_DESIGN_SPEC

    verdict = manifest.assert_documents_adopted(REPO_ROOT)
    assert verdict["adopted"] is True
    assert verdict["findings"] == []
    prereg = (REPO_ROOT / PREREGISTRATION).read_text()
    assert "\n    status: ADOPTED\n" in prereg
    assert manifest.DRAFT_MARKER not in prereg.split("## 2. The amendments")[0]
    spec = json.loads((REPO_ROOT / REFERENCE_DESIGN_SPEC).read_text())
    assert spec["_status"] == "ADOPTED"
    assert "DRAFT_DOCUMENT" not in {b["kind"]
                                    for b in manifest.signing_blockers()}


def test_a_missing_declaration_reads_as_a_draft(tmp_path):
    """The safe reading of silence is the one that refuses."""
    from dci1v6 import PREREGISTRATION, REFERENCE_DESIGN_SPEC

    prereg = tmp_path / PREREGISTRATION
    prereg.parent.mkdir(parents=True, exist_ok=True)
    prereg.write_text("# a document that says nothing about its status\n")
    spec = tmp_path / REFERENCE_DESIGN_SPEC
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"whatever": True}))
    verdict = manifest.assert_documents_adopted(tmp_path)
    assert verdict["adopted"] is False
    assert {f["declared"] for f in verdict["findings"]} == {"none"}


def test_the_reference_design_spec_is_generated_from_the_code():
    """It is derived from the registered code, so a spec that disagrees with
    the implementation is not expressible --- and its `_status` is derived
    too, from the three researcher acts it names, never chosen by the tool."""
    spec = json.loads((REPORTS / "reference_design_spec.json").read_text())
    assert spec["candidate_library"]["sizes"] == K.assert_library_sizes()
    assert spec["composed_probe"]["measured_residual_sd"] == P.RESIDUAL_SD
    assert spec["composed_probe"]["residual_readings"] == list(
        P.RESIDUAL_READINGS)
    assert spec["design"]["gate4_entries_full_arm_set"] == 95
    derived = spec["_status_is_derived_from"]
    assert derived["n_decisions"] == 27
    assert spec["_status"] == (
        "ADOPTED" if derived["adopted"] else manifest.DRAFT_MARKER)
    assert derived["adopted"] == (
        derived["preregistration_status"] == "ADOPTED"
        and not derived["open_decisions"]
        and not derived["blocking_open_items"])
    # Generated against the REAL decision registry, not this process's fixture
    # one, so what it reports is what the researcher recorded.
    assert sorted(spec["researcher_decisions"]["closed"]) == sorted(
        decisions.DECISION_IDS)
    assert spec["open_decisions"]["ids"] == []
    assert spec["validity_components"]["composed_headroom_band"] == list(
        C.COMPOSED_HEADROOM_BAND)


def test_the_precision_report_reproduces_the_signed_gate4_verdicts():
    """The tool refuses to report anything unless its baseline reproduces the
    two signed Gate-4 tables and the two signed terminal reports, and the
    committed artifact carries the count."""
    report = json.loads((REPORTS / "precision_design.json").read_text())
    assert report["_classification"] == "DEVELOPMENT_EVIDENCE"
    assert report["_baseline_checks_against_signed_records"] == 21
    assert report["gate4_precision"]["n_entries"] == 73
    assert report["split_transfer"]["verdict"] == "consistent with sampling"
    assert report["policies"]["materialised_sequestered_topics"] == 0
    assert all(row["topics_that_must_be_authored"] > 0
               for row in report["policies"]["rows"]
               if row["n_composed"] > C.N_COMPOSED)
    feasibility = report["operating_point_feasibility"]
    # The frozen-m* rule, applied to closed v5's own solo-B curves. What is
    # pinned is the SHAPE --- that the artifact reports the verdict at the
    # frozen m* and names the replications it would have stopped --- not the
    # count. A test that asserted a survival number would make the number an
    # expectation, and the number is a finding.
    assert feasibility["residual_used"] == 0.0
    assert isinstance(feasibility["every_frozen_m_star_passes"], bool)
    stopped = feasibility["replications_whose_frozen_m_star_fails"]
    assert (stopped == []) == feasibility["every_frozen_m_star_passes"]
    assert set(stopped) <= set(feasibility["per_model"])
    for entry in feasibility["per_model"].values():
        assert entry["m_star_passes"] == entry["per_severity"][
            str(entry["m_star"])]["passes"]


# --------------------------------------------- the verdict rule's own inputs

def test_determinacy_is_read_from_the_cell_and_not_from_what_was_measured():
    """Which of the two verdict rules an entry is judged by is a property of
    the **design**, not of which measurements happened to arrive.

    Reading it off the measured keys would let a stand-in pair whose stand-in
    slot went unmeasured look like a determinate solo cell and be given a
    margin it is not entitled to. So the slots come from the cell id, and a
    table whose measurements disagree with them is refused rather than
    silently judged under the wrong rule.
    """
    assert P.cell_slots_of("solo:B") == ("B",)
    assert P.cell_slots_of("pair:B+P1") == ("B", "P1")
    assert P.cell_slots_of("unconstrained") == ()
    for bad in ("pair:B", "gate3b", "pair:+B"):
        with pytest.raises(ProtocolError):
            P.cell_slots_of(bad)
    assert P.is_determinate(P.cell_slots_of("pair:A+B"))
    assert not P.is_determinate(P.cell_slots_of("pair:B+P1"))
    entry = {"compliance": 0.9, "s2_topic": 0.0, "n_topics": 192}
    with pytest.raises(ProtocolError) as excinfo:
        P.severity_verdict({"pair:B+P1": {"B": entry}}, residual_sd=0.0)
    assert "would change which verdict rule" in str(excinfo.value)


def test_the_measured_split_transfer_is_recorded_and_gates_nothing():
    """§34 D20's branch, as the thing it is: the estimator of the only
    non-sampling term, put on the record beside the verdict it is an
    assumption in --- and reading nothing, because a rule that re-tuned the
    margin from the transfer it was measuring would fit a design constant to
    the replication it is about to judge."""
    from dci1v6.run.gates_run import _measured_split_transfer

    def entry(a, b):
        return {"compliance": (a + b) / 2, "s2_topic": 0.05, "n_topics": 192,
                "a_minus_b": a - b,
                "by_split": {C.CALIBRATION_A: {"compliance": a,
                                               "n_topics": 96},
                             C.CALIBRATION_B: {"compliance": b,
                                               "n_topics": 96}}}

    probed = {10: {"unconstrained": {"unconstrained": entry(1.0, 1.0)},
                   "solo:B": {"B": entry(0.80, 0.70)},
                   "pair:B+P1": {"B": entry(0.60, 0.64),
                                 "P1": entry(0.50, 0.50)}}}
    out = _measured_split_transfer(
        probed, v5_fitted_residual_sd=P.RESIDUAL_SD,
        carried_by_the_verdict=0.0)
    assert out["gates_nothing"] is True and out["read_by"] == []
    # Two numbers, named apart, because under §34 D23's `projection_sd`
    # reading they differ: the verdict carries D26's magnitude and not the
    # v5-fitted estimate. Calling the fitted value "assumed" while the
    # verdict assumed something else is the D23 defect one field down.
    assert out["v5_fitted_residual_sd"] == P.RESIDUAL_SD
    assert out["carried_by_the_verdict"] == 0.0
    assert out["n_entries"] == 3
    assert {(r["cell"], r["slot"]) for r in out["entries"]} == {
        ("solo:B", "B"), ("pair:B+P1", "B"), ("pair:B+P1", "P1")}
    carried = {r["slot"] + r["cell"]: r["carried_by_the_pooled_estimate"]
               for r in out["entries"]}
    assert carried["Bsolo:B"] == pytest.approx(0.05)
    assert out["max_absolute_carried_offset"] == pytest.approx(0.05)
    # (|0.05| + |-0.02| + |0.00|) / 3
    assert out["mean_absolute_carried_offset"] == pytest.approx(0.07 / 3)
    assert out["mean_carried_offset"] == pytest.approx(0.03 / 3)


# ------------------------- the 2026-08-26 red team, as executable assertions

def test_the_sensitivity_tool_mirrors_the_production_readings(
        restore_decisions):
    """`v6_residual_sensitivity` computes the band and the projection sd
    without going through `decisions`, so that the table is readable while
    §34 D23 and D26 are open. That shortcut is only safe if it agrees with
    the production accessors, so this checks it rather than trusting it."""
    import importlib.util
    from pathlib import Path as _P

    root = _P(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "_sens", root / "tools" / "v6_residual_sensitivity.py")
    sens = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sens)

    for reading in P.RESIDUAL_READINGS:
        for magnitude in (0.0, P.RESIDUAL_SD, 0.0687):
            band, sd = sens._band_and_sd(reading, magnitude)
            restore_decisions.reopen_all_for_testing()
            restore_decisions.override_for_testing("D23", reading)
            restore_decisions.override_for_testing("D26", magnitude)
            assert P.margin_band() == pytest.approx(band)
            assert P.projection_residual_sd() == pytest.approx(sd)


def test_the_sensitivity_artifact_is_committed_and_sweeps_both_readings():
    """§34 D26 is the one decision with no derivation, so the grid it is to be
    chosen on has to exist as an artifact and not as a paragraph."""
    report = json.loads((REPORTS / "residual_sensitivity.json").read_text())
    assert report["operating_point_rule"] == "frozen_at_gate2"
    seen = {(p["reading"], round(p["magnitude"], 4))
            for p in report["policies"]}
    assert seen == {(r, round(m, 4)) for r in P.RESIDUAL_READINGS
                    for m in (0.0, P.RESIDUAL_SD, 0.0687)}
    # What the grid actually discriminates, under the frozen-m* rule: at the
    # measured 0.0142 one of the four closed replications' m* fails the
    # projection --- the one v5 terminated at Gate 4 --- and at the 95% upper
    # bound all four do. Asserted as a shape, not as a number: the artifact
    # must report the per-policy verdict and name the replications, so that
    # no policy can be read as costless.
    for policy in report["policies"]:
        assert isinstance(policy["every_frozen_m_star_passes"], bool)
        assert (policy["replications_whose_frozen_m_star_fails"] == []) == \
            policy["every_frozen_m_star_passes"]
        assert policy["n_replications_terminating_here"] == len(
            policy["replications_whose_frozen_m_star_fails"])
    assert report["_scope_limit"].startswith("solo:B is one of the six")


def test_an_unimplemented_alternative_cannot_be_closed_at(restore_decisions):
    """Thirteen entries offered values the implementation had no branch for.
    Closing at one would have registered a study the code cannot run, and
    nothing read the value, so nothing would have said so."""
    restore_decisions.reopen_all_for_testing()
    # D19 and D21 are v6's own, so the session fixture leaves them open and
    # `close` is reachable. The guard is in `close` and is id-agnostic; the
    # v5-era acceptances (D2, D5, D7-D15) carry the same field and are
    # asserted below without closing anything.
    for did in ("D19", "D21"):
        decision = decisions.DECISIONS[did]
        assert decision.admissible_values == ()
        assert decision.unimplemented_alternatives
        with pytest.raises(ProtocolError) as excinfo:
            decisions.close(did, decision.unimplemented_alternatives[0],
                            evidence="e", decided_by="t", decided_on="t")
        assert "unimplemented" in str(excinfo.value)
    for did in ("D2", "D5", "D7", "D13", "D15"):
        decision = decisions.DECISIONS[did]
        assert decision.admissible_values == (), did
        assert decision.unimplemented_alternatives, did


def test_d0_do_not_adopt_actually_refuses_a_registration(restore_decisions):
    """It is the one value in the register meaning `this study does not run`,
    and until 2026-08-26 it signed a manifest exactly as `adopt` did."""
    from dci1v6.protocol import manifest

    restore_decisions.reopen_all_for_testing()
    restore_decisions.override_for_testing("D0", "do_not_adopt")
    kinds = [b["kind"] for b in manifest.signing_blockers()]
    assert "NOT_ADOPTED" in kinds


def test_the_register_quotes_v5s_closures_and_not_its_draft_proposals():
    """D16, D17 and D18 carried v5's PRE-adoption text --- in every case the
    branch the researcher rejected, and in every case the weaker one."""
    from pathlib import Path as _P

    v5 = json.loads((_P(__file__).resolve().parents[1] / "reports" / "dci1v5"
                     / "researcher_decisions.json").read_text())
    closed = {c["id"]: c["value"] for c in v5["closures"]}
    assert closed["D16"] == "complete_population"
    assert closed["D17"] == "floor"
    assert closed["D18"] == "precondition"
    for did in ("D16", "D17", "D18"):
        proposal = decisions.DECISIONS[did].standing_proposal
        assert str(closed[did]) in proposal, did
        # And the withdrawn text is named, so the correction is legible.
        assert "until 2026-08-26" in proposal, did
