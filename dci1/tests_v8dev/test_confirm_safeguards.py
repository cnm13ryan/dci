"""The v7 safeguards, frame-conditioned: the gates, audits and ledgers the
confirmatory analysis records beside its estimates.

Every test here is on synthetic rows built through the production planner,
prompt renderer and scorer (``confirm_harness``), or on the gate function
itself with a planted input --- because a guard that is only ever reached
with well-behaved data is a guard that has never been tested.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError
from dci1v4.models.registry import get_model
from dci1v7.analysis import claims as CL
from dci1v7.analysis import estimators as E
from dci1v7.analysis.bootstrap import sidak_critical
from dci1v7.analysis.observations import Observation, ObservationTable
from dci1v7.protocol import constants as C
from dci1v8dev.confirm import analysis as A
from dci1v8dev.confirm import report as RP
from tests_v8dev import confirm_harness as H

MODEL = "qwen3-4b"
BLOCKS = 8
RESAMPLES = 80


def _analyse(frames, rows, *, resamples=RESAMPLES):
    freeze = H.fabricated_freeze(frames, blocks_per_frame=BLOCKS)
    return A.analyse_model(rows, freeze, model_id=get_model(MODEL).model_id,
                           resamples=resamples), freeze


@pytest.fixture(scope="module")
def analysed(tmp_path_factory):
    """One LOCAL+SPECTRUM frame and one LOCAL-only frame, with difficulty
    coordinates on the references so §23's audit has something to audit."""
    frames = {0: H.with_iota(H.fabricated_frame(0, local=True, spectrum=True)),
              2: H.with_iota(H.fabricated_frame(2, local=True, spectrum=False))}
    root = tmp_path_factory.mktemp("safeguards")
    rows = H.confirmatory_rows(frames, root=root, blocks=BLOCKS)
    result, freeze = _analyse(frames, rows)
    return {"frames": frames, "rows": rows, "result": result, "freeze": freeze}


def _iv(member, estimate, lower, upper, boundary=None):
    return CL.Interval(member=member, estimate=estimate, lower=lower,
                       upper=upper, boundary=boundary)


# ------------------------------------------------------- 1. L1 headroom, L2
def test_headroom_and_l1_l2_gates_are_recorded_per_configuration(analysed):
    fr = analysed["result"]["frames"]["0"]
    headroom = fr["solo_headroom"]
    assert headroom["floor"] == C.L1_SOLO_HEADROOM_FLOOR
    assert headroom["B"]["realised_solo_compliance"] > C.L1_SOLO_HEADROOM_FLOOR
    assert headroom["B"]["has_headroom"] and headroom["A"]["has_headroom"]
    assert headroom["B"]["frozen_solo_compliance"] == 0.8
    for cfg in C.CONFIGURATIONS:
        gates = fr["gates"][cfg]
        assert set(gates["l1"]) == {"D(B<-A)", "D(A<-B)"}
        for member, entry in gates["l1"].items():
            assert entry["solo_headroom"] is True
            assert isinstance(entry["licensed"], bool)
            reading = fr["configurations"][cfg]["F1"]["members"][member]["reading"]
            assert reading["l1"] == entry
        assert gates["l2"]["status"] in ("READ", "NOT_LICENSED")
        lam = fr["configurations"][cfg]["F1"]["members"]["Lambda"]["reading"]
        assert lam["l2"] == gates["l2"]


def test_an_outcome_at_the_compliance_floor_is_not_licensed(tmp_path):
    """B fails everywhere, so its realised solo compliance is at the floor:
    §3.2's L1 gate does not hold, and L2 --- whose gate is L1 for both
    directions --- is NOT_LICENSED rather than unresolved."""
    frames = {0: H.with_iota(H.fabricated_frame(0, local=True, spectrum=False))}
    slot_maps = H.slot_maps_of(H.fabricated_freeze(frames,
                                                   blocks_per_frame=BLOCKS))
    base = H.composed_generate(slot_maps)

    def spoil_every_answer(run_dir, plan, rows):
        out = base(run_dir, plan, rows)
        for produced in out["rows"]:
            text = produced["final_answer"].rstrip(".")
            produced["final_answer"] = text + " consideration" + "a" * 8 + "."
            produced["raw_generation"] = produced["final_answer"]
        return out

    rows = H.confirmatory_rows(frames, root=tmp_path, blocks=BLOCKS,
                               generate=spoil_every_answer)
    result, _ = _analyse(frames, rows, resamples=40)
    fr = result["frames"]["0"]
    assert fr["solo_headroom"]["B"]["realised_solo_compliance"] == 0.0
    assert fr["solo_headroom"]["B"]["has_headroom"] is False
    for cfg in C.CONFIGURATIONS:
        gates = fr["gates"][cfg]
        entry = gates["l1"]["D(B<-A)"]
        assert entry["licensed"] is False
        assert "no solo headroom" in entry["reason"]
        assert gates["l2"]["status"] == "NOT_LICENSED"
        assert "did not reach L1" in gates["l2"]["reason"]


def test_l1_gate_orders_its_refusals_like_the_registered_emitter():
    headroom = {"B": {"has_headroom": False, "realised_solo_compliance": 0.02},
                "A": {"has_headroom": True, "realised_solo_compliance": 0.7}}
    ivs = {"D(B<-A)": _iv("D(B<-A)", 0.3, 0.2, 0.4),
           "D(A<-B)": _iv("D(A<-B)", 0.3, 0.2, 0.4)}
    gate = A.l1_gate(headroom, ivs, {})
    assert gate["D(B<-A)"]["licensed"] is False   # headroom beats a good bound
    assert gate["D(A<-B)"]["licensed"] is True
    # §17.4 beats the bound too: the recomputation licenses the other claim
    forced = {"D(A<-B)|vacuity_forced": _iv("D(A<-B)|vacuity_forced",
                                            -0.1, -0.3, 0.1)}
    gate = A.l1_gate(headroom, ivs, forced)
    assert gate["D(A<-B)"]["licensed"] is False
    assert "vacuity-forced" in gate["D(A<-B)"]["reason"]
    assert A.lambda_gate(_iv("Lambda", 0.2, 0.1, 0.3), gate,
                         None)["status"] == "NOT_LICENSED"


# ---------------------------------------------------------- 2. the Xi gate
def test_xi_direction_gate_rides_on_the_delta_r_reading(analysed):
    for cfg in C.CONFIGURATIONS:
        for w in ("0", "2"):
            fr = analysed["result"]["frames"][w]
            xi_iv = fr["configurations"][cfg]["F1"]["members"]["Xi"]
            reading = fr["configurations"][cfg]["F1"]["members"]["Delta_R"]["reading"]
            gate = reading["xi_gate"]
            assert gate == fr["gates"][cfg]["xi"]
            assert gate["outcome_specific"] == (xi_iv["decision_lower"] > 0.0)
            assert reading["outcome_specificity_wording"] == gate["wording"]
            if not gate["outcome_specific"]:
                assert "A_GENERAL_NOT_EXCLUDED" in reading["statuses"]
            # the gate decides the WORDING and never whether there is a
            # reading: Delta_R still carries its levels either way
            assert "levels" in reading
            # the joint (decision) interval carries the same qualification
            joint = analysed["result"]["joint"][cfg]["members"][f"f{w}:Delta_R"]
            assert joint["reading"]["xi_gate"] == gate


# --------------------------------------------- 3. within-frame heterogeneity
def test_within_frame_reference_heterogeneity_is_recorded(analysed):
    for cfg in C.CONFIGURATIONS:
        gates = analysed["result"]["frames"]["0"]["gates"][cfg]
        het = gates["reference_heterogeneity"]
        assert het["asked"] is True
        assert set(het["sides"]) == {"Delta_1", "Delta_2", "Delta_3"}
        assert het["threshold"] == C.DELTA_R_GENERIC_THRESHOLD
        reading = (analysed["result"]["frames"]["0"]["configurations"][cfg]
                   ["F1"]["members"]["Delta_R"]["reading"])
        assert reading["reference_heterogeneity"] == het
        assert ("REFERENCE_HETEROGENEOUS" in reading["qualifiers"]) is \
            het["disagrees"]


def test_a_heterogeneous_delta_j_set_attaches_the_qualifier():
    ivs = {"Delta_1": _iv("Delta_1", 0.4, 0.3, 0.5),      # above
           "Delta_2": _iv("Delta_2", -0.1, -0.2, 0.0),    # below
           "Delta_3": _iv("Delta_3", 0.1, 0.0, 0.2)}      # straddles
    het = A.reference_heterogeneity(ivs)
    assert het["disagrees"] is True
    assert het["sides"] == {"Delta_1": "above", "Delta_2": "below",
                            "Delta_3": "straddles"}
    reading = {"levels": ["L3a"], "markers": [], "statuses": []}
    A._qualify_delta_r(reading, {"reference_heterogeneity": het,
                                 "vacuity": {}, "xi": None})
    assert "REFERENCE_HETEROGENEOUS" in reading["qualifiers"]
    # agreement attaches nothing
    agreed = {name: _iv(name, 0.4, 0.3, 0.5) for name in
              ("Delta_1", "Delta_2", "Delta_3")}
    assert A.reference_heterogeneity(agreed)["disagrees"] is False
    # a frame that was never asked is not a disagreement
    assert A.reference_heterogeneity({})["asked"] is False


# ------------------------------------------------------ 4. projection audit
def test_projection_audit_reports_every_companion_beside_b(analysed):
    audit = analysed["result"]["frames"]["0"]["projection_audit"]
    frozen = analysed["frames"][0]
    companions = set(A.b_companions(frozen))
    assert companions >= {"A", "R1", "R2", "R3", "R4", "R5", "S1"}
    assert {e["companion"] for e in audit} == companions
    assert {e["configuration"] for e in audit} == set(C.CONFIGURATIONS)
    for entry in audit:
        assert entry["allowance"] == C.PROJECTION_ERROR_ALLOWANCE
        assert entry["iota"] is not None
        assert entry["projected_mean"] == pytest.approx(
            entry["chance_mean"] + entry["iota"] * (1 - entry["chance_mean"]))
        assert entry["within_allowance"] == (
            entry["absolute_error_mean"] <= C.PROJECTION_ERROR_ALLOWANCE)


def test_projection_audit_flags_a_planted_displacement(analysed):
    """Displacing the frozen coordinate displaces the projection by exactly
    ``(1 - kappa)`` times the displacement, and the audit says so."""
    rows, frozen = analysed["rows"], analysed["frames"][0]
    table = A.frame_table(rows, 0, m_draws=C.M_DRAWS)
    blocks = len(table.blocks)
    realised = sum(E.composed_vector(table, "R1", "B",
                                     C.OUTCOME_FIRST)) / blocks
    chance = sum(E.chance_vector(table, "R1")) / blocks
    honest = (realised - chance) / (1 - chance)

    def audit(iota):
        doctored = {**frozen,
                    "core": [{**r, "iota": iota} if r["slot"] == "R1" else r
                             for r in frozen["core"]]}
        entry = next(e for e in A.projection_audit(table, doctored)
                     if e["companion"] == "R1"
                     and e["configuration"] == C.OUTCOME_FIRST)
        assert entry["iota"] == iota
        return entry

    at_honest = audit(honest)
    assert at_honest["projected_mean"] == pytest.approx(realised)
    for displaced in (audit(honest - 0.3), audit(min(1.0, honest + 0.2))):
        assert displaced["absolute_error_mean"] > \
            at_honest["absolute_error_mean"]
        assert displaced["within_allowance"] is False


def _mini_table(*, r1_chance: float) -> ObservationTable:
    """Two blocks carrying only what §23's audit reads for R1 and A2: the
    unconstrained cell, and the composed cell with B in both orders."""
    obs: list[Observation] = []

    def make(block, cell_id, arm, slot, companion, position, configuration,
             compliance, present=True):
        return Observation(
            block_id=block, cell_id=cell_id, arm=arm, outcome_slot=slot,
            companion_slot=companion, position=position,
            configuration=configuration, draws=1, compliance=compliance,
            graded=compliance, vacuity=0.0, truncation=0.0,
            non_vacuous_compliance=compliance, graded_threshold=compliance,
            response_words=10.0, processing_failures=0, present=present)

    for block in ("conf-0000", "conf-0004"):
        for slot, chance in (("R1", r1_chance), ("A2", 0.1)):
            obs.append(make(block, "unconstrained", "unconstrained", slot,
                            None, 1, None, chance, present=False))
            for cfg, position in ((C.OUTCOME_FIRST, 1), (C.OUTCOME_SECOND, 2)):
                obs.append(make(block, f"pair:{slot}+B", "composed", slot, "B",
                                position, cfg, 0.5))
    return ObservationTable(obs)


def test_projection_audit_records_degeneracy_and_unprojectable_slots():
    frozen = {"arms": ["base", "core", "backup", "runner_up"],
              "n_spectrum_slots": 0, "runner_up_slots": ["A2"],
              "iota_a": 0.6, "core": [{"slot": "R1", "iota": 0.9}],
              "backups": [], "spectrum_points": []}
    audit = A.projection_audit(_mini_table(r1_chance=0.999), frozen)
    r1 = next(e for e in audit if e["companion"] == "R1"
              and e["configuration"] == C.OUTCOME_FIRST)
    assert r1["status"] == "DIFFICULTY_COORDINATE_DEGENERATE"
    assert r1["n_blocks"] == 0 and r1["n_blocks_degenerate"] == 2
    assert r1["within_allowance"] is None
    a2 = next(e for e in audit if e["companion"] == "A2")
    assert a2["status"] == "NOT_PROJECTABLE"
    assert "no difficulty coordinate" in a2["reason"]
    # below the degeneracy ceiling the same slot is audited normally
    ok = next(e for e in A.projection_audit(_mini_table(r1_chance=0.2), frozen)
              if e["companion"] == "R1" and e["configuration"] == C.OUTCOME_FIRST)
    assert ok["n_blocks"] == 2 and "status" not in ok


def test_the_projection_allowance_is_the_registered_one():
    """A table whose composed rate is 0.5 in every block: the coordinate
    that reproduces it exactly has zero error, and one displaced past the
    registered allowance is outside it."""
    frozen = {"arms": ["base", "core"], "n_spectrum_slots": 0,
              "runner_up_slots": [], "iota_a": 0.6, "backups": [],
              "spectrum_points": []}
    table = _mini_table(r1_chance=0.2)          # composed R1|B = 0.5 always
    honest = (0.5 - 0.2) / (1 - 0.2)

    def audit(iota):
        return next(e for e in A.projection_audit(
            table, {**frozen, "core": [{"slot": "R1", "iota": iota}]})
            if e["companion"] == "R1"
            and e["configuration"] == C.OUTCOME_FIRST)

    exact = audit(honest)
    assert exact["projected_mean"] == pytest.approx(0.5)
    assert exact["absolute_error_mean"] == pytest.approx(0.0)
    assert exact["within_allowance"] is True
    displaced = audit(honest + 0.2)
    assert displaced["absolute_error_mean"] == pytest.approx(0.2 * 0.8)
    assert displaced["within_allowance"] is False


# --------------------------------------------------- 5. identification ledger
def test_every_registered_member_carries_a_ledger_status(analysed):
    result = analysed["result"]
    for w, fr in result["frames"].items():
        ledger = fr["identification_ledger"]
        for cfg in C.CONFIGURATIONS:
            families = ledger["configurations"][cfg]
            assert set(families) >= {"F1", "F2", "F3", "F4", "F5", "F6", "F7",
                                     "F_REFSENS", "F_SPECTRUM", "F_RUNNER_UP"}
            for members in families.values():
                for entry in members.values():
                    assert entry["status"] in A.LEDGER_STATUSES
            # a frame with no runner-up arm is NOT_ASKED, never absent
            for entry in families["F_RUNNER_UP"].values():
                assert entry["status"] == "NOT_ASKED"
                assert "stable on this coordinate" in entry["reason"]
        f11 = ledger["cross_configuration"]["F11"]
        assert f11["Ord_CL"]["status"] == "NOT_ASKED"
        assert "CLASS_ARM_NOT_AVAILABLE" in f11["Ord_CL"]["reason"]
        assert f11["Ord_Rbar"]["status"] == "ESTIMATED"
    # the spectrum-less frame records delta_difficulty as NOT_ASKED, which is
    # a different fact from NOT_IDENTIFIED
    f2 = result["frames"]["2"]["identification_ledger"]["configurations"]
    entry = f2[C.OUTCOME_FIRST]["F1"]["delta_difficulty"]
    assert entry["status"] == "NOT_ASKED" and "SPECTRUM" in entry["reason"]
    joint = result["joint"][C.OUTCOME_FIRST]["identification_ledger"]["JOINT_F1"]
    assert joint["f0:Delta_R"]["status"] == "ESTIMATED"
    assert joint["f2:delta_difficulty"]["status"] == "NOT_ASKED"


def test_a_silently_missing_member_raises(analysed):
    fr = analysed["result"]["frames"]["0"]
    cfg = C.OUTCOME_FIRST
    ledger = {fam: dict(members) for fam, members in
              fr["identification_ledger"]["configurations"][cfg].items()}
    formed = fr["configurations"][cfg]
    # the safeguard passes on the record as it stands
    summary = A.assert_every_member_ledgered(ledger, formed, where="test")
    assert summary["by_status"]["ESTIMATED"] > 0
    # drop one estimated member's entry: an omission, not a status
    ledger["F1"] = {k: v for k, v in ledger["F1"].items() if k != "Delta_R"}
    with pytest.raises(ProtocolError, match="F1:Delta_R"):
        A.assert_every_member_ledgered(ledger, formed, where="test")
    # an unregistered status is refused too
    ledger["F1"]["Delta_R"] = {"status": "PROBABLY_FINE"}
    with pytest.raises(ProtocolError, match="outside"):
        A.assert_every_member_ledgered(ledger, formed, where="test")


def test_a_missing_cell_makes_a_member_not_identified_rather_than_absent():
    frozen = H.with_iota(H.fabricated_frame(0, local=True, spectrum=True))
    expectations = A.frame_expectations(frozen)
    # the analysis formed everything except Delta_R
    formed = {"F1": {"members": {m: {} for m in C.FAMILY_MEMBERS["F1"]
                                if m != "Delta_R"}}}
    ledger = A.identification_ledger({"F1": expectations["F1"]}, formed)
    assert ledger["F1"]["Delta_R"]["status"] == "NOT_IDENTIFIED"
    assert "could not be formed" in ledger["F1"]["Delta_R"]["reason"]
    assert ledger["F1"]["Xi"]["status"] == "ESTIMATED"


# ---------------------------------------------------------------- 6. L4a
def test_l4a_is_per_named_member(analysed):
    l4a = analysed["result"]["frames"]["0"]["l4a"]
    assert l4a["configurations"] == list(C.CONFIGURATIONS)
    assert "Delta_R" in l4a["per_member"]
    for entry in l4a["per_member"].values():
        assert set(entry["levels"]) == set(C.CONFIGURATIONS)
        assert entry["agree"] == (len(set(entry["levels"].values())) == 1)
    assert l4a["consistent"] is (not l4a["differing_members"])


def test_l4a_records_v4r4s_swap_pattern_as_a_disagreement():
    """The pattern that produced v4r4's defect: both configurations reach a
    level, but not for the same member. Comparing the SETS says replication;
    per member says configuration dependence."""
    readings = {
        C.OUTCOME_FIRST: {"D(B<-A)": {"levels": ["L1"]},
                          "D(A<-B)": {"levels": []}},
        C.OUTCOME_SECOND: {"D(B<-A)": {"levels": []},
                           "D(A<-B)": {"levels": ["L1"]}}}
    out = A.l4a_consistency(readings)
    assert out["differing_members"] == ["D(A<-B)", "D(B<-A)"]
    assert out["consistent"] is False
    assert out["registered_reading"] == "Configuration dependence (§28.1)"


# ----------------------------------------------------------------- 7. L3c
def test_the_strong_l3c_verdict_is_unreachable():
    assert "LOCAL_EQUIVALENT_L3c" not in A.MODEL_VERDICTS
    verdict = A.local_model_verdict({0: {"levels": ["L3c"], "markers": []},
                                     2: {"levels": ["L3c"], "markers": []}})
    assert verdict["verdict"] == "LOCAL_EQUIVALENT_SAME_FORM_ONLY"
    assert verdict["l3c"]["disposition"] == A.L3C_DISPOSITION
    assert verdict["l3c"]["scope"] == "same_form_only"
    assert "NEAR_FORM_ARM_NOT_AVAILABLE" in verdict["l3c"]["statuses"]
    assert "L3C_STRONG_CONCLUSION_WITHHELD" in verdict["l3c"]["statuses"]
    assert verdict["l3c"]["frames"] == ["0", "2"]
    # the supported readings are untouched
    assert A.local_model_verdict(
        {0: {"levels": ["L3a"], "markers": []}})["verdict"] == \
        "LOCAL_SUPPORTED_L3a"


# ------------------------------------------------------------ 8. spectrum
def test_spectrum_algebraic_forms_agree_and_the_ceiling_is_enforced(analysed):
    fr = analysed["result"]["frames"]["0"]
    for cfg in C.CONFIGURATIONS:
        forms = fr["algebraic_forms"][cfg]
        assert forms["delta_difficulty_status"] == "AGREE"
        assert abs(forms["Delta_R"]) < 1e-9
        record = fr["configurations"][cfg]["F_SPECTRUM"]["degenerate_replicates"]
        assert record["ceiling"] == C.DEGENERATE_REPLICATE_MAX
        assert record["replicates"] == RESAMPLES
        assert record["status"] == "OK"
        assert fr["configurations"][cfg]["F_SPECTRUM"]["members"]["slope"][
            "decision_lower"] is not None


def test_the_degenerate_replicate_ceiling_refuses_the_interval():
    counter = A.RefitCounter()
    counter.observe({"degenerate": False, "dropped_points": []})   # the point
    for i in range(100):
        counter.observe({"degenerate": i < 2, "dropped_points": []})
    record = counter.record(100)
    assert record["fit_unavailable"] == 2
    assert record["degenerate_replicate_share"] == pytest.approx(0.02)
    assert record["status"] == "DEGENERATE_REPLICATES"
    fam = {"members": {"slope": {"decision_lower": 0.1, "decision_upper": 0.3,
                                 "decision_half_width": 0.1,
                                 "meets_precondition": True,
                                 "reading": {"levels": []}}}}
    A.apply_degenerate_ceiling(fam, counter, 100)
    slope = fam["members"]["slope"]
    assert slope["status"] == "DEGENERATE_REPLICATES"
    assert slope["decision_lower"] is None and slope["decision_upper"] is None
    assert slope["reading"]["markers"] == ["DEGENERATE_REPLICATES"]
    # a dropped point counts the same way, and one below the ceiling does not
    below = A.RefitCounter()
    below.observe({"degenerate": False})
    for i in range(1000):
        below.observe({"degenerate": False,
                       "dropped_points": ["S1"] if i < 5 else []})
    assert below.record(1000)["dropped_a_point"] == 5
    assert below.record(1000)["status"] == "OK"


# -------------------------------------------------- 9. vacuity (F5, F6, §17.4)
def test_f5_and_f6_are_formed_from_the_row_recodings(analysed):
    fr = analysed["result"]["frames"]["0"]
    for cfg in C.CONFIGURATIONS:
        f5 = fr["configurations"][cfg]["F5"]["members"]
        assert set(f5) == {f"{base}|{suffix}"
                           for suffix in A.F5_RECODINGS
                           for base in A.F5_MEMBERS[suffix]}
        f6 = fr["configurations"][cfg]["F6"]["members"]
        assert "vac(B|A+B)-vac(B solo)" in f6
        assert set(f6) - {"vac(B|A+B)-vac(B solo)"} == {
            f"vac(B|B+{c})-vac(B solo)"
            for c in A.b_companions(analysed["frames"][0]) if c != "A"}
        # the recodings are their own estimands, on their own scale
        primary = fr["configurations"][cfg]["F1"]["members"]["D(B<-A)"]
        assert f5["D(B<-A)|vacuity_forced"]["per_block"] is not None
        assert len(f5["D(B<-A)|vacuity_forced"]["per_block"]) == BLOCKS
        assert primary["per_block"] is not None
    vac = fr["gates"][C.OUTCOME_FIRST]["vacuity"]
    assert vac["gate"] == C.F6_VACUITY_GATE
    assert vac["n_members"] == len(
        fr["configurations"][C.OUTCOME_FIRST]["F6"]["members"])
    assert vac["forced_agrees"] in (True, False)


def test_the_f6_gate_binds_only_on_a_resolved_difference_above_the_gate():
    def member(estimate, lo, hi):
        return {"estimate": estimate, "simultaneous_lower": lo,
                "simultaneous_upper": hi}
    # small, or straddling zero: no qualification (§17.4's own words)
    quiet = {"a": member(0.02, 0.0, 0.05), "b": member(0.4, -0.1, 0.9)}
    assert A.vacuity_gate_binds(quiet)["binds"] is False
    loud = {**quiet, "c": member(0.3, 0.2, 0.4)}
    gate = A.vacuity_gate_binds(loud)
    assert gate["binds"] is True and gate["binding_members"] == ["c"]


def test_a_disagreeing_vacuity_recomputation_withholds_the_level():
    """§17.4's both-bounds rule: when the primary and the recomputation do
    not license the same claim the level is withheld, exactly as emit_l3
    withheld it, and the frame enters the conjunction as INDETERMINATE."""
    delta_r = _iv("Delta_R", 0.40, 0.37, 0.43)
    forced = _iv("Delta_R|vacuity_forced", 0.02, 0.00, 0.04)
    assert CL.l3_vacuity_agrees(delta_r, forced) is False
    reading = dict(CL.delta_r_reading(delta_r))
    assert reading["levels"] == ["L3a", "L3b"]
    A._qualify_delta_r(reading, {"xi": None, "reference_heterogeneity": {},
                                 "vacuity": {"gate_binds": False,
                                             "forced_agrees": False}})
    assert reading["vacuity_withholds_levels"] is True
    assert "VACUITY_DEPENDENT" in reading["qualifiers"]
    assert A.local_model_verdict({0: reading})["verdict"] == "INDETERMINATE"
    # the reporting half attaches on its own
    other = dict(CL.delta_r_reading(delta_r))
    A._qualify_delta_r(other, {"xi": None, "reference_heterogeneity": {},
                               "vacuity": {"gate_binds": True,
                                           "forced_agrees": True}})
    assert "VACUITY_DEPENDENT" in other["qualifiers"]
    assert other["vacuity_withholds_levels"] is False
    assert A.local_model_verdict({0: other})["verdict"] == "LOCAL_SUPPORTED_L3b"


# -------------------------------------------------------------------- 10. F7
def test_f7_reciprocal_losses_are_formed_with_their_own_interval(analysed):
    rows = analysed["rows"]
    table = A.frame_table(rows, 0, m_draws=C.M_DRAWS)
    for cfg in C.CONFIGURATIONS:
        f7 = (analysed["result"]["frames"]["0"]["configurations"][cfg]["F7"])
        assert set(f7["members"]) == set(C.FAMILY_MEMBERS["F7"])
        # its own simultaneous interval, over its own six members
        assert f7["blocks"] == BLOCKS and f7["resamples"] == RESAMPLES
        assert f7["sidak_reference"] == pytest.approx(
            sidak_critical(len(C.FAMILY_MEMBERS["F7"])))
        expected = E.delivery_loss(table, "R1", "B", cfg)
        assert f7["members"]["D(R1<-B)"]["per_block"] == pytest.approx(expected)
        for entry in f7["members"].values():
            assert entry["decision_lower"] <= entry["estimate"] <= \
                entry["decision_upper"]
            # descriptive: it licenses no claim level
            assert entry["reading"]["levels"] == []
    # a member of F7 is a member of no other family
    fams = analysed["result"]["frames"]["0"]["configurations"][C.OUTCOME_FIRST]
    for other in ("F1", "F2", "F3", "F4"):
        assert not set(fams[other]["members"]) & set(C.FAMILY_MEMBERS["F7"])


# ------------------------------------------------------------- 11. runner-up
def test_the_runner_up_contrast_recovers_a_planted_effect(tmp_path):
    """B is spoiled under A with probability 0.6 and under A2 and the
    references with 0.1. Delta_R(f) is large and Delta_R(f; A2) is not: the
    runner-up contrast says the excess belongs to the frozen n*(f)."""
    frames = {0: H.with_runner_up(
        H.with_iota(H.fabricated_frame(0, local=True, spectrum=False)),
        slots=["A2"])}
    slot_maps = H.slot_maps_of(H.fabricated_freeze(frames,
                                                   blocks_per_frame=24))
    gen = H.effect_generate(slot_maps, spoil_b_under={
        "A": 0.6, "A2": 0.1, "R1": 0.1, "R2": 0.1, "R3": 0.1,
        "R4": 0.1, "R5": 0.1})
    rows = H.confirmatory_rows(frames, root=tmp_path, blocks=24, generate=gen)
    freeze = H.fabricated_freeze(frames, blocks_per_frame=24)
    result = A.analyse_model(rows, freeze, model_id=get_model(MODEL).model_id,
                             resamples=200)
    for cfg in C.CONFIGURATIONS:
        fams = result["frames"]["0"]["configurations"][cfg]
        delta_r = fams["F1"]["members"]["Delta_R"]["estimate"]
        runner = fams["F_RUNNER_UP"]["members"]["Delta_R[A2]"]
        assert set(fams["F_RUNNER_UP"]["members"]) == {"Delta_R[A2]"}
        assert delta_r > 0.3, (cfg, delta_r)
        assert abs(runner["estimate"]) < 0.15, (cfg, runner["estimate"])
        assert runner["decision_lower"] <= runner["estimate"] <= \
            runner["decision_upper"]
    ledger = (result["frames"]["0"]["identification_ledger"]["configurations"]
              [C.OUTCOME_FIRST]["F_RUNNER_UP"])
    assert ledger["Delta_R[A2]"]["status"] == "ESTIMATED"
    assert ledger["Delta_R[B2]"]["status"] == "NOT_ASKED"


def test_the_runner_up_m_contrast_is_formed_from_the_b2_cells(tmp_path):
    frames = {0: H.with_runner_up(
        H.with_iota(H.fabricated_frame(0, local=True, spectrum=False)),
        slots=["B2"])}
    rows = H.confirmatory_rows(frames, root=tmp_path, blocks=BLOCKS)
    result, _ = _analyse(frames, rows, resamples=40)
    fams = result["frames"]["0"]["configurations"][C.OUTCOME_FIRST]
    members = fams["F_RUNNER_UP"]["members"]
    assert set(members) == {"Delta_R[B2]"}
    table = A.frame_table(rows, 0, m_draws=C.M_DRAWS)
    # it is B2's own delivery that is contrasted: mean_j p(B2 | B2+R_j)
    # minus p(B2 | B2+A), from the cells the runner-up arm adds
    with_refs = E.mean_vectors([E.composed_vector(table, "B2", r,
                                                  C.OUTCOME_FIRST)
                                for r in C.CORE_SLOTS])
    with_a = E.composed_vector(table, "B2", "A", C.OUTCOME_FIRST)
    expected = [r - a for r, a in zip(with_refs, with_a)]
    assert members["Delta_R[B2]"]["per_block"] == pytest.approx(expected)
    assert A.delta_r_against(table, C.CORE_SLOTS, "A",
                             C.OUTCOME_FIRST) == pytest.approx(expected)
    claims = RP.frame_claims(result, 0, frames[0])
    runner = claims["configurations"][C.OUTCOME_FIRST]["runner_up"]
    assert runner["frozen_operating_point"] == {"n_star": 3, "m_star": 9}
    assert runner["runner_up"]["values"] == {"B2": 10}
    assert runner["licenses"].startswith("nothing")


# --------------------------------------- 12. §26 methodological success
def test_methodological_success_is_met_and_says_why_when_it_is_not(analysed):
    result = analysed["result"]
    success = result["methodological_success"]
    assert success["verdict"] in C.SUCCESS_CRITERION_VALUES
    assert (success["verdict"] == "MET") == (not success["reasons"])
    frames = analysed["frames"]
    # a member that could not be formed
    doctored = {**result, "frames": {**result["frames"]}}
    fr = {k: v for k, v in result["frames"]["0"].items()}
    ledger = {k: {kk: dict(vv) for kk, vv in v.items()}
              for k, v in fr["identification_ledger"]["configurations"].items()}
    ledger[C.OUTCOME_FIRST]["F1"]["Delta_R"] = {"status": "NOT_IDENTIFIED",
                                                "reason": "planted"}
    fr["identification_ledger"] = {**fr["identification_ledger"],
                                   "configurations": ledger}
    doctored["frames"]["0"] = fr
    out = A.methodological_success(doctored, frames)
    assert out["verdict"] == "NOT_MET"
    assert any("Delta_R is NOT_IDENTIFIED" in r for r in out["reasons"])
    # a primary interval that misses its precision precondition
    wide = {k: v for k, v in result["frames"]["2"].items()}
    cfgs = {c: {f: dict(v) for f, v in fams.items()}
            for c, fams in wide["configurations"].items()}
    members = {k: dict(v) for k, v in
               cfgs[C.OUTCOME_FIRST]["F1"]["members"].items()}
    members["Delta_R"] = {**members["Delta_R"], "meets_precondition": False}
    cfgs[C.OUTCOME_FIRST]["F1"] = {**cfgs[C.OUTCOME_FIRST]["F1"],
                                   "members": members}
    wide["configurations"] = cfgs
    doctored["frames"]["2"] = wide
    out = A.methodological_success(doctored, frames)
    assert any("precision precondition" in r for r in out["reasons"])


# ------------------------------------------------------- 13. report.py
def test_the_report_renders_the_new_blocks(analysed):
    result, frames = analysed["result"], analysed["frames"]
    claims = RP.frame_claims(result, 0, frames[0])
    cfg = claims["configurations"][C.OUTCOME_FIRST]
    assert set(cfg) >= {"Delta_R", "F2", "F5", "F6", "F7", "l1", "l2",
                        "xi_gate", "reference_heterogeneity", "vacuity",
                        "identification_ledger", "reference_sensitivity",
                        "slope", "degenerate_replicates"}
    assert claims["solo_headroom"]["floor"] == C.L1_SOLO_HEADROOM_FLOOR
    assert claims["projection_audit"] and claims["l4a"]["per_member"]
    assert claims["identification_ledger_cross_configuration"]["F11"]
    assert cfg["Delta_R"]["joint_interval"]["reading"]["xi_gate"]


def test_report_traceability_checks_pass_and_catch_a_broken_chain(analysed):
    result, freeze, frames = (analysed["result"], analysed["freeze"],
                              analysed["frames"])
    signed = {**result, "freeze_hash": "FREEZE"}
    claims = {w: RP.frame_claims(signed, int(w), frames.get(int(w)))
              for w in signed["frames"]}
    checks = RP.report_checks(signed, freeze, claims, freeze_hash="FREEZE")
    assert [c["check"] for c in checks] == [c[0] for c in RP.REPORT_CHECKS]
    assert all(c["verdict"] == "PASS" for c in checks), checks
    ledgered = next(c for c in checks
                    if c["check"] ==
                    "every_registered_member_is_estimated_or_ledgered")
    assert ledgered["detail"]["by_status"]["ESTIMATED"] > 0
    assert ledgered["detail"]["by_status"]["NOT_ASKED"] > 0

    def verdicts(analysis, claims_table, freeze_hash="FREEZE"):
        return {c["check"]: c["verdict"] for c in
                RP.report_checks(analysis, freeze, claims_table,
                                 freeze_hash=freeze_hash)}

    # a frame the freeze carries and the analysis does not
    dropped = {**signed, "frames": {"0": signed["frames"]["0"]}}
    assert verdicts(dropped, {"0": claims["0"]})[
        "every_frame_has_an_analysis_entry"] == "FAIL"
    # an analysis signed under another freeze
    assert verdicts(signed, claims, freeze_hash="OTHER")[
        "analysis_signed_under_this_freeze"] == "FAIL"
    # the strong L3c verdict, if anything ever produced one
    strong = {**signed, "model_verdict": {C.OUTCOME_FIRST:
                                          "LOCAL_EQUIVALENT_L3c"}}
    assert verdicts(strong, claims)["no_strong_l3c_verdict"] == "FAIL"
    # an estimate that does not trace to the record
    moved = {w: {**c, "configurations": {
        cc: {**vals, "Delta_R": {**vals["Delta_R"],
                                 "frame_interval": {
                                     **vals["Delta_R"]["frame_interval"],
                                     "estimate": 42.0}}}
        for cc, vals in c["configurations"].items()}}
        for w, c in claims.items()}
    assert verdicts(signed, moved)[
        "estimates_trace_to_the_analysis_record"] == "FAIL"
    # a ledger entry quietly removed
    stripped = {**signed, "frames": {
        w: {**fr, "identification_ledger": {
            "configurations": {}, "cross_configuration": {}}}
        for w, fr in signed["frames"].items()}}
    assert verdicts(stripped, claims)[
        "every_registered_member_is_estimated_or_ledgered"] == "FAIL"
