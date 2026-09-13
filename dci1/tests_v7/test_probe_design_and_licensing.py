"""What the 2026-08-25 design pass added, and the invariants it turns on.

Four groups, and they are not the same kind of claim. **Placement** is the rule
that puts a stand-in where the design puts a companion. **Isolation** is the
set of populations a `probe_only` family must stay out of, checked one by one
rather than by asserting the flag exists. **Licensing** is what v7 says at
study level, registered before data. **Adoption** is the refusal that keeps a
complete draft from being mistaken for a registration by being present.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v7.design import budget
from dci1v7.engine.context import REPO_ROOT
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, manifest
from dci1v7.run import lifecycle, regime_run
from dci1v7.stages import composed_probe as P
from dci1v7.verifiers import constraints as K

REPORTS = Path(__file__).resolve().parents[1] / "reports" / "dci1v7"


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
        terminal={"qwen3-4b": "REGIME_NOT_FOUND"})
    assert out["n_survivors"] == 1
    assert out["rule"] == "§34 D25"
    assert "L5 is withheld by design" in out["statement"]
    assert "never evidence about the effect" in out["statement"]
    assert out["terminal"] == {"qwen3-4b": "REGIME_NOT_FOUND"}


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

def test_the_governed_documents_declare_the_state_the_record_is_in():
    """Adoption is a researcher act recorded in the documents themselves,
    where the manifest guard reads it, and in the decision record.

    While v7 is a draft both documents say so, the decision record is absent
    and `DRAFT_DOCUMENT` is among the signing blockers; once the researcher
    adopts, all three flip together. What is pinned is the correspondence,
    never the state --- a test that asserted ADOPTED would make the
    researcher's act an expectation of the code.
    """
    from dci1v7 import PREREGISTRATION, REFERENCE_DESIGN_SPEC

    verdict = manifest.assert_documents_adopted(REPO_ROOT)
    prereg = (REPO_ROOT / PREREGISTRATION).read_text()
    spec = json.loads((REPO_ROOT / REFERENCE_DESIGN_SPEC).read_text())
    record = REPO_ROOT / decisions.RECORD_RELPATH
    if not record.exists():
        assert verdict["adopted"] is False
        assert {f["document"] for f in verdict["findings"]} == {
            PREREGISTRATION, REFERENCE_DESIGN_SPEC}
        assert f"status: {manifest.DRAFT_MARKER}" in prereg
        assert spec["_status"] == manifest.DRAFT_MARKER
        assert "DRAFT_DOCUMENT" in {b["kind"]
                                    for b in manifest.signing_blockers(
                                        repo_root=REPO_ROOT)}
        return
    assert verdict["adopted"] is True and verdict["findings"] == []
    assert "\n    status: ADOPTED\n" in prereg
    assert spec["_status"] == "ADOPTED"


def test_a_missing_declaration_reads_as_a_draft(tmp_path):
    """The safe reading of silence is the one that refuses."""
    from dci1v7 import PREREGISTRATION, REFERENCE_DESIGN_SPEC

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
    assert spec["design"]["gate4_entries_full_arm_set"] == 95
    derived = spec["_status_is_derived_from"]
    assert derived["n_decisions"] == 26
    assert spec["_status"] == (
        "ADOPTED" if derived["adopted"] else manifest.DRAFT_MARKER)
    assert derived["adopted"] == (
        derived["preregistration_status"] == "ADOPTED"
        and not derived["open_decisions"]
        and not derived["blocking_open_items"])
    # Generated against the REAL decision registry, not this process's fixture
    # one, so what it reports is what the researcher recorded.
    real = (REPO_ROOT / decisions.RECORD_RELPATH)
    recorded = ({e["id"] for e in decisions.recorded_closures(real)}
                if real.exists() else set())
    assert set(spec["researcher_decisions"]["closed"]) == recorded
    assert set(spec["open_decisions"]["ids"]) == set(
        decisions.DECISION_IDS) - recorded
    # v7: the band is descriptive and says so; the contrast rule is spelled
    # out from the constants it reads.
    assert spec["validity_components"]["composed_proximity_band"] == list(
        C.COMPOSED_PROXIMITY_BAND)
    assert spec["validity_components"]["composed_proximity_band_is"] \
        .startswith("DESCRIPTIVE")
    contrast = spec["composed_contrast"]
    assert contrast["compression_level"] == C.CONTRAST_COMPRESSION_LEVEL
    assert contrast["terminal_statuses_withdrawn"] == [
        "COMPOSED_HEADROOM_FAILURE", "COMPOSED_HEADROOM_UNREACHABLE"]
    assert contrast["statuses"] == list(C.V7_IDENTIFICATION_STATUSES)
    assert spec["composed_probe"]["outcomes"] == ["PASS"]
    assert "residual" not in json.dumps(spec["composed_probe"]).lower()


# --------------------------------------------- the record rule's own inputs

def test_determinacy_is_read_from_the_cell_and_not_from_what_was_measured():
    """Which entries the contrasts are formed from is a property of the
    **design**, not of which measurements happened to arrive.

    Reading it off the measured keys would let a stand-in pair whose stand-in
    slot went unmeasured look like a determinate solo cell. So the slots come
    from the cell id, and a table whose measurements disagree with them is
    refused rather than silently read under the wrong shape.
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
        P.contrast_record({"pair:B+P1": {"B": entry}}, seed=1, resamples=10)
    assert "carries a measurement for" in str(excinfo.value)


def test_the_measured_split_transfer_is_recorded_and_parameterises_nothing():
    """§34 D20's branch, as the thing it is in v7: the estimator of the only
    non-sampling term between the probe's pooled topics and the confirmatory
    set, put on the record beside the contrasts --- and reading nothing,
    because there is no longer a projected-interval verdict for it to enter."""
    from dci1v7.run.gates_run import _measured_split_transfer

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
    out = _measured_split_transfer(probed)
    assert out["gates_nothing"] is True and out["read_by"] == []
    assert out["parameterises_nothing"] is True
    assert "residual" not in json.dumps(
        {k: v for k, v in out.items() if k != "why_it_gates_nothing"}).lower()
    assert out["n_entries"] == 3
    assert {(r["cell"], r["slot"]) for r in out["entries"]} == {
        ("solo:B", "B"), ("pair:B+P1", "B"), ("pair:B+P1", "P1")}
    carried = {r["slot"] + r["cell"]: r["carried_by_the_pooled_estimate"]
               for r in out["entries"]}
    assert carried["Bsolo:B"] == pytest.approx(0.05)
    assert out["max_absolute_carried_offset"] == pytest.approx(0.05)
    assert out["mean_absolute_carried_offset"] == pytest.approx(0.07 / 3)
    assert out["mean_carried_offset"] == pytest.approx(0.03 / 3)


# ------------------------- the 2026-08-26 red team, as executable assertions

def test_an_unimplemented_alternative_cannot_be_closed_at(restore_decisions):
    """Thirteen entries offered values the implementation had no branch for.
    Closing at one would have registered a study the code cannot run, and
    nothing read the value, so nothing would have said so."""
    restore_decisions.reopen_all_for_testing()
    # D19, D21 and D27 are v6's and v7's own, so the session fixture leaves
    # them open and `close` is reachable. The guard is in `close` and is
    # id-agnostic; the v5-era acceptances (D2, D5, D7-D15) carry the same
    # field and are asserted below without closing anything.
    for did in ("D19", "D21", "D27"):
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
    from dci1v7.protocol import manifest

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
