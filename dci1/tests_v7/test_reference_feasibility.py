"""One implementation of the support criterion, pinned to the signed records.

**Why these tests exist.** v6's central repair is that the question a
development pilot asks and the question the registered gate asks must be the
same question. Making them the same means extracting the criterion into
``stages/feasibility`` and having Gate 3A, Gate 3B, Gate 3C, the
operating-point search and the pilot all call it. An extraction is only safe
if it is behaviour-preserving, and "behaviour" here is four signed v5 records
and one synthetic walk captured **before** the extraction was made.

So the first three tests are characterization tests. They do not describe what
the criterion *should* say; they pin what it *did* say, on data nobody can
change, so that a future edit to the criterion fails here rather than
succeeding quietly.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C
from dci1v7.run import gates_run
from dci1v7.stages import composed_probe, feasibility, regime

FIXTURE = Path(__file__).resolve().parent / \
    "fixture_reference_chain_characterization.json"

V5_MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
             "qwen3-4b-instruct-2507")


def _v5_records(model_key: str):
    """The signed v5 records, or a skip when the evidence tree is absent.

    ``runs/`` is gitignored and does not survive a clone, so these tests are
    conditional on the closed study being present. They are not conditional on
    anything a developer can influence.
    """
    v5ctx = pytest.importorskip("dci1v5.engine.context")
    from dci1v5.engine import transitions as v5tx
    from dci1v5.engine.paths import model_tree
    from dci1v5.protocol import constants as C5

    tree = model_tree(v5ctx.registered_context(), model_key)
    stages = (C5.STAGE_REGIME, C5.STAGE_GATE2, C5.STAGE_GATE2_5,
              C5.STAGE_GATE3A, C5.STAGE_GATE3B, C5.STAGE_GATE3C)
    if not all(tree.stage_record(s).exists() for s in stages):
        pytest.skip(f"{model_key}: the closed v5 records are not present")
    return {s: v5tx.read_stage_record(tree, s) for s in stages}, C5


# --------------------------------------------------- characterization: v5

@pytest.mark.parametrize("model_key", V5_MODELS)
def test_the_kernels_reproduce_the_signed_v5_selection(model_key,
                                                       harness_decisions):
    """§13.8-§13.12 through the shared kernel, against the signed slot map."""
    rec, C5 = _v5_records(model_key)
    g3a = rec[C5.STAGE_GATE3A]
    chosen = feasibility.selection_at(
        {"pooled_table": g3a["pooled_table"], "m_star": g3a["m_star"],
         "iota_a": g3a["iota_a"],
         "solo_compliance_a": g3a["solo_compliance_a"],
         "stability": g3a.get("stability") or {}},
        model_key=model_key)
    signed = {k: list(v) for k, v in rec[C5.STAGE_GATE3B]["slot_map"].items()}
    assert chosen["slot_map"] == signed


@pytest.mark.parametrize("model_key", V5_MODELS)
def test_the_kernels_reproduce_the_signed_v5_support(model_key,
                                                     harness_decisions):
    """§13.15 through the shared kernel, against the signed support block.

    Three of these four replications did **not** meet §13.15 and the fourth
    did. Reproducing both outcomes is the point: a kernel that only agreed on
    the passing replication would be pinned to nothing.
    """
    rec, C5 = _v5_records(model_key)
    g3a = rec[C5.STAGE_GATE3A]
    calibration = {
        "pooled_table": g3a["pooled_table"], "m_star": g3a["m_star"],
        "iota_a": g3a["iota_a"],
        "solo_compliance_a": g3a["solo_compliance_a"],
        "stability": g3a.get("stability") or {},
        "qualified_families": rec[C5.STAGE_GATE2_5]["qualified_families"]}
    chosen = feasibility.selection_at(calibration, model_key=model_key)
    supported = feasibility.support_at(
        chosen, model_key=model_key, calibration=calibration,
        regime_record=rec[C5.STAGE_REGIME])
    signed = rec[C5.STAGE_GATE3C]
    assert supported["report"]["support_met"] == signed["support"]["support_met"]
    assert supported["report"]["realised"] == signed["support"]["realised"]
    assert supported["report"]["failures"] == signed["support"]["failures"]
    assert supported["arms"] == list(signed["admitted_arms"])


@pytest.mark.parametrize("model_key", V5_MODELS)
def test_the_margin_is_reported_and_the_backup_count_is_not_a_margin(
        model_key, harness_decisions):
    """The quantity the boolean does not carry, and one it must not fake.

    ``freeze_backups`` returns ``spare[:N_BACKUP_FAMILIES]``, so its length
    equals the requirement whenever the requirement is met. Reporting that as
    a margin would put a zero in every replication and make ``min_margin``
    say nothing.
    """
    rec, C5 = _v5_records(model_key)
    g3a = rec[C5.STAGE_GATE3A]
    calibration = {
        "pooled_table": g3a["pooled_table"], "m_star": g3a["m_star"],
        "iota_a": g3a["iota_a"],
        "solo_compliance_a": g3a["solo_compliance_a"],
        "stability": g3a.get("stability") or {},
        "qualified_families": rec[C5.STAGE_GATE2_5]["qualified_families"]}
    chosen = feasibility.selection_at(calibration, model_key=model_key)
    report = feasibility.support_at(
        chosen, model_key=model_key, calibration=calibration,
        regime_record=rec[C5.STAGE_REGIME])["report"]
    margin = feasibility.support_margin(report)
    assert "frozen_backups" not in margin["margins"]
    assert set(margin["margins"]) == {
        "structurally_eligible_tier12_families", "qualified_families",
        "tier1_core"}
    assert margin["min_margin"] == min(margin["margins"].values())


# -------------------------------------------- characterization: synthetic

def test_the_seam_did_not_move_the_synthetic_chain():
    """The Gate 3A/3B/3C chain, captured before the extraction.

    The fixture was written by a walk of the harness against the code as it
    stood before ``stages/feasibility`` existed. It is regenerated only when
    a change to the criterion is intended and registered.
    """
    snapshot = json.loads(FIXTURE.read_text())
    # V6-E05: one field in this snapshot was corrected rather than reproduced,
    # and the fixture records which, from what, to what and why. A snapshot
    # that could be edited silently would pin nothing.
    corrected = snapshot["_corrected"]
    assert corrected["field"] == "gate3a.n_stable"
    assert corrected["change"] == "V6-E05"
    assert snapshot["gate3a"]["n_stable"] == corrected["now"] != corrected["was"]
    assert snapshot["gate3c"]["support_met"] is True
    assert snapshot["gate3a"]["m_star"] == snapshot["gate3c"]["m_star"]
    # The walk that reproduces it is the slow one; `test_synthetic_lifecycle`
    # runs it. What is pinned here is that the fixture is present, coherent,
    # and names the stages the seam now serves.
    assert set(snapshot) >= {"gate3a", "gate3b", "gate3c", "focal_admissible"}


# ------------------------------------------------------------ the seam

def test_no_public_name_in_the_seam_is_without_a_caller():
    """A convenience wrapper nobody calls is the A8 defect shape.

    Every name the seam exports is either used inside the module or read by
    production code or by the development report. This is why
    ``reference_feasibility`` was removed rather than kept for a future
    caller: the lifecycle has three stages and each calls one kernel, and a
    composition with no caller is exactly what the reachability audit exists
    to find.

    The check is on the parsed source, not on a grep: a name that appears
    only in a docstring or a comment is not a caller.
    """
    import subprocess

    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src" / "dci1v7" / "stages"
                      / "feasibility.py").read_text())
    loaded_here: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            loaded_here.add(node.id)

    orphans = []
    for name in feasibility.__all__:
        if name in loaded_here:
            continue
        hits = subprocess.run(
            ["grep", "-rlF", name, "--include=*.py", "src/", "tools/"],
            cwd=root, capture_output=True, text=True).stdout.splitlines()
        if not [h for h in hits if "stages/feasibility.py" not in h]:
            orphans.append(name)
    assert orphans == [], f"{orphans} are exported by the seam and unused"


def test_the_registered_stages_and_the_pilot_call_one_implementation():
    """No second copy of the criterion exists to drift from the first."""
    assert "calibration_at(" in inspect.getsource(gates_run.gate3a_payload)
    assert "selection_at(" in inspect.getsource(gates_run.gate3b_payload)
    assert "support_at(" in inspect.getsource(gates_run.gate3c_payload)
    tool = (Path(__file__).resolve().parents[1] / "tools"
            / "v6_reference_feasibility.py").read_text()
    assert "feasibility.selection_at(" in tool
    assert "feasibility.support_at(" in tool
    # And the pilot refuses to report unless it reproduces the signature.
    assert "baseline does not reproduce" in tool


def test_the_chain_generates_nothing():
    """Why an operating-point search is affordable at all.

    Every quantity §13.7, §13.8-§13.12 and §13.15 read was measured at Gate 2
    or Gate 2.5. A kernel that generated would make the search cost rows and
    would put a composed outcome upstream of a reference.
    """
    for fn in (feasibility.calibration_at, feasibility.selection_at,
               feasibility.support_at,
               feasibility.coverage_at_calibrated_iota_a,
               feasibility.qualified_family_support):
        source = inspect.getsource(fn)
        assert "generate_and_score" not in source
        assert "prompt_cell" not in source


# ------------------------------- §12.6 re-read on the calibration basis

def test_the_calibrated_coverage_is_evaluated_on_paired_cases(
        harness_decisions):
    """iota(R), the coordinate, the vacuity and iota_A from one set of cases.

    The reading this replaces took iota(R) from 24 pre-screen topics at one
    draw and compared it against an iota_A from 192 calibration topics at
    four, so whatever moved was part the reference point and part the two
    samples. Here the reference point is the only thing that moves between
    the two calibration-basis readings.
    """
    rows = [{"kind": "MK1", "severity": 3, "solo_compliance": 0.5,
             "chance_compliance": 0.0, "solo_vacuity": 0.0}]
    shaped = regime.calibration_coverage_rows(rows, formulation="E2")
    assert shaped[0]["iota"] == pytest.approx(0.5)
    assert shaped[0]["solo"] == pytest.approx(0.5)
    assert shaped[0]["eligible"] is True
    # The same formulation function the pre-screen basis runs.
    assert shaped[0]["eligibility"]["formulation"] == "E2"


def test_the_calibrated_coverage_gates_through_the_registered_disposition(
        harness_decisions):
    """A lost CORE condition (C1, C3, C5, C6) is a §13.15 design-time
    failure, not a new status and not a drift threshold. (v7 A7: a lost
    spectrum condition is the spectrum arm's own failure; see the next
    test.)"""
    source = inspect.getsource(feasibility.coverage_at_calibrated_iota_a)
    assert "COVERAGE_MAX_DRIFT" not in source
    assert "drift" not in source.lower().split("iota_a_movement")[0][-400:]
    report = feasibility.support_at(
        {"core": {"core_references": []}, "identification_statuses": []},
        model_key="fixture-model",
        calibration={"qualified_families": ["MK1"] * 5},
        regime_record={"carried_set": [], "identification_statuses": []},
        extra_design_time_failures=[
            feasibility.CALIBRATED_COVERAGE_FAILURE])["report"]
    assert not report["support_met"]
    assert feasibility.CALIBRATED_COVERAGE_FAILURE in report["failures"]
    assert "core" not in report["admitted_arms"]


def test_a7_the_calibrated_spectrum_verdict_costs_the_spectrum_only(
        harness_decisions):
    """v7 A7: a lost C2/C4 on the calibrated basis is a spectrum failure,
    not a §13.15 failure, and the core arm stands."""
    core = [{"structural_tier": 1, "feature_group": g, "family": f}
            for f, g in (("MK1", "marker_thus"), ("MK2", "marker_hence"),
                         ("MK3", "marker_though"))]
    report = feasibility.support_at(
        {"core": {"core_references": core, "spectrum_identified": True},
         "identification_statuses": []},
        model_key="fixture-model",
        calibration={"qualified_families": ["MK1", "MK2", "MK3", "MK4",
                                            "MK5"]},
        regime_record={"carried_set": [f"MK{i}:1" for i in range(1, 9)],
                       "identification_statuses": []},
        extra_spectrum_failures=[
            feasibility.CALIBRATED_SPECTRUM_COVERAGE_FAILURE])
    assert report["report"]["support_met"]
    assert report["report"]["failures"] == []
    assert feasibility.CALIBRATED_SPECTRUM_COVERAGE_FAILURE in \
        report["spectrum_failures"]
    assert "core" in report["arms"] and "spectrum" not in report["arms"]
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in \
        report["identification_statuses"]
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in \
        report["identification_statuses"]


def test_the_calibrated_re_read_reports_both_arms():
    """`coverage_at_calibrated_iota_a` carries a core verdict and a spectrum
    verdict, and the pre-screen certificate beside them gates neither."""
    source = inspect.getsource(feasibility.coverage_at_calibrated_iota_a)
    for key in ("core_met", "spectrum_met", "spectrum_failures",
                "core_failed", "spectrum_failed"):
        assert f'"{key}"' in source


# ------------------------------------------- the frozen search order

def test_the_search_order_is_frozen_finite_and_the_registered_rule():
    curve = {7: 0.95, 8: 0.86, 9: 0.79, 10: 0.62}
    order = feasibility.operating_point_order(
        m_star=9, admissible=[7, 8, 9, 10], curve=curve)
    assert order[0] == 9                       # P3.1: m* is probed first
    assert sorted(order) == [7, 8, 9, 10]      # finite, and no severity added
    # §12.3's own preference: ascending |solo - FOCAL_AIM|, ties to smaller.
    assert order == [9, 8, 7, 10]   # |.79-.8|, |.86-.8|, .15, .18
    assert C.FOCAL_AIM == 0.80


def test_the_order_is_restricted_by_a_condition_signed_before_the_probe(
        harness_decisions):
    """§13.15's five-family minimum, per candidate, from Gate 2.5's record."""
    record = {"qualification_by_severity": {
        "8": {"qualified_families": ["A", "B", "C", "D", "E", "F"]},
        "9": {"qualified_families": ["A", "B"]}}}
    support = feasibility.qualified_family_support(record, severities=[8, 9])
    assert support["8"]["can_support"] is True
    assert support["9"]["can_support"] is False
    assert support["8"]["min_qualified_families"] == C.MIN_QUALIFIED_FAMILIES
    with pytest.raises(ProtocolError, match="recorded no qualification"):
        feasibility.qualified_family_support(record, severities=[10])


def test_the_pre_filter_is_a_lookup_and_not_a_second_bootstrap():
    """Gate 2.5 already ran the full V(R) at every admissible severity.

    Re-deriving the filter per candidate would resample §13.7's identical
    per-topic vectors with identical seeds, 10,000 times per candidate per
    split, for a verdict that is already on a signed record.
    """
    fn = feasibility.qualified_family_support
    body = inspect.getsource(fn).split('"""')[2]   # past the docstring
    assert "stability_verdict" not in body
    assert "bootstrap" not in body
    assert "qualification_by_severity" in body
    assert C.STABILITY_BOOTSTRAP_RESAMPLES == 10_000


# ------------------------------------------------- controlled reuse

def test_a_gate2_cell_is_reused_only_when_the_case_is_identical():
    same = composed_probe.shared_cell_verdict(
        gate2_topic_ids=["t1", "t2"], probe_topic_ids=["t2", "t1"],
        gate2_draws=C.M_CAL, probe_draws=C.M_CAL)
    assert same["shared"] is True
    assert set(same["cells"]) == set(composed_probe.SHARED_WITH_GATE2)

    # A different topic set is a different sample, whatever its size.
    other = composed_probe.shared_cell_verdict(
        gate2_topic_ids=["t1", "t2"], probe_topic_ids=["t3", "t4"],
        gate2_draws=C.M_CAL, probe_draws=C.M_CAL)
    assert other["shared"] is False and other["cells"] == []

    # Same topics, different draws: still not the same case.
    draws = composed_probe.shared_cell_verdict(
        gate2_topic_ids=["t1"], probe_topic_ids=["t1"],
        gate2_draws=C.M_CAL, probe_draws=C.M_CAL + 1)
    assert draws["shared"] is False
    assert "drew" in draws["reason"]

    # An empty Gate-2 topic list can never authorise reuse.
    empty = composed_probe.shared_cell_verdict(
        gate2_topic_ids=[], probe_topic_ids=[], gate2_draws=C.M_CAL,
        probe_draws=C.M_CAL)
    assert empty["shared"] is False


def test_the_probe_generates_only_what_gate2_did_not_measure():
    source = inspect.getsource(gates_run.gate2_75_payload)
    assert "shared_cell_verdict(" in source
    assert "generated_shape" in source
    # The evaluated shape is unchanged: §13.14's band still reaches solo:B.
    shape = [c for c, _a, _s in composed_probe.probe_cell_types(("P1",))]
    assert "solo:B" in shape and "unconstrained" in shape
    assert set(composed_probe.SHARED_WITH_GATE2) <= set(shape)


def test_the_diagnostic_from_existing_rows_cannot_reach_the_selection_input():
    """kappa(B|R) is free, recorded, and structurally unable to select.

    §13.11's schema is closed, so the column has nowhere to land on the
    calibration table --- which is why it lives on the Gate-2 record instead.
    """
    from dci1v7.stages.calibration_table import load_calibration_table

    source = inspect.getsource(gates_run._kappa_b_under_candidate)
    assert "generate" not in source
    with pytest.raises(ProtocolError, match="schema is closed"):
        load_calibration_table(
            [{"kind": "MK1", "severity": 3, "split": "pooled",
              "model_key": "fixture-model", "solo_compliance": 0.5,
              "chance_compliance": 0.1, "solo_vacuity": 0.0,
              "kappa_b_under_candidate": 0.2}],
            model_key="fixture-model", m_star=9, split="pooled")


# ------------------------- value tests for the three new computations

@pytest.mark.parametrize("model_key", V5_MODELS)
def test_calibration_at_reproduces_the_signed_v5_stability(model_key,
                                                           harness_decisions):
    """The largest extracted kernel, against signed §13.7 verdicts.

    ``calibration_at`` is the body Gate 3A used to hold inline. v5's Gate-2.5
    record predates ``qualification_by_severity``, so the pool is presented in
    the shape the kernel reads **at v5's own m\\***; every other input is v5's
    record unchanged, and ``calibration_rows_at`` returns Gate 2's rows
    untouched when the operating point is Gate 2's.

    **This costs about 50 seconds per replication** --- §13.7's two bootstraps
    at the registered 10,000 resamples, over ~113 candidates --- and it is
    kept at all four because the four differ in m*, in population and in
    whether §13.15 was met, and because they are the only real data v6 has
    before it runs. It is what found V6-E05.
    """
    rec, C5 = _v5_records(model_key)
    gate2, g25, g3a = (rec[C5.STAGE_GATE2], rec[C5.STAGE_GATE2_5],
                       rec[C5.STAGE_GATE3A])
    m_star = int(g3a["m_star"])
    shaped = {"qualification_by_severity": {str(m_star): {
        "qualified_pool": g25["qualified_pool"],
        "qualified_families": g25["qualified_families"],
        "n_qualified": g25["n_qualified"]}}}
    out = feasibility.calibration_at(
        model_key=model_key, gate2_record=gate2, gate2_5_record=shaped,
        m_star=m_star, seed=0,
        resamples=C.STABILITY_BOOTSTRAP_RESAMPLES)
    assert out["n_rows"] == g3a["n_rows"]
    assert sorted(out["calibration_b_population"]) == sorted(
        g3a["calibration_b_population"])
    assert out["iota_a"] == g3a["iota_a"]
    # The verdicts themselves, candidate by candidate, at the registered
    # resample count and seed. This is the pin that matters: §13.7's answer
    # for every candidate on a replication nobody can re-run.
    assert {k: v["passed"] for k, v in out["stability"].items()} == {
        k: v["passed"] for k, v in g3a["stability"].items()}

    # V6-E05, and it is deliberately asserted rather than skipped. The signed
    # record's own `n_stable` is 0 while its verdicts say otherwise, because
    # the count read a key `stability_verdict` never returns. The kernel now
    # counts `passed`; v5's records are not touched and still say 0.
    n_passed = sum(1 for v in g3a["stability"].values() if v["passed"])
    assert g3a["n_stable"] == 0
    assert n_passed > 0
    assert out["n_stable"] == n_passed


def test_kappa_b_under_candidate_averages_topics_not_draws():
    """B scored ABSENT on each candidate's own solo cell.

    The unit is the TOPIC: each topic's draws are averaged first, then the
    topics. A draw-weighted mean would let a topic with more completions
    speak louder, which is the error §13.6's own kappa avoids.
    """
    def row(topic, label, passed):
        return {"cell_id": f"solo:{label}", "topic_id": topic,
                "scores": [{"kind": "B", "severity": 9, "present": False,
                            "passed": p} for p in passed]
                          + [{"kind": label.split(":")[0],
                              "severity": int(label.split(":")[1]),
                              "present": True, "passed": True}]}
    rows = [row("t1", "MK1:3", [1, 0]),      # topic mean 0.5
            row("t2", "MK1:3", [1, 1, 1, 1]),  # topic mean 1.0 -> (0.5+1)/2
            row("t1", "MK2:4", [0, 0])]
    out = gates_run._kappa_b_under_candidate(
        rows, m_star=9, model_key="fixture-model")["by_candidate"]
    assert out["MK1:3"]["kappa_b_under_candidate"] == pytest.approx(0.75)
    assert out["MK1:3"]["n_topics"] == 2
    assert out["MK2:4"]["kappa_b_under_candidate"] == pytest.approx(0.0)
    # A present score for B is a different cell type and is not this quantity.
    present = [{"cell_id": "solo:MK1:3", "topic_id": "t1",
                "scores": [{"kind": "B", "severity": 9, "present": True,
                            "passed": 1}]}]
    assert gates_run._kappa_b_under_candidate(
        present, m_star=9, model_key="m")["by_candidate"] == {}


def test_prescreen_to_calibration_pairs_and_skips_what_it_cannot_pair():
    """Paired by instrument, and silent about what it has no pair for."""
    rows = [
        # solo 0.90 vs 0.50 at chance 0.0 -> d_solo = d_iota = +0.40
        {"kind": "MK1", "severity": 3, "solo_compliance": 0.90,
         "chance_compliance": 0.0, "prescreen_solo_compliance": 0.50,
         "prescreen_chance_compliance": 0.0},
        # no pre-screen pair: skipped rather than counted as zero movement
        {"kind": "MK2", "severity": 4, "solo_compliance": 0.70,
         "chance_compliance": 0.1},
        # degenerate chance: iota is undefined, so the row is skipped
        {"kind": "MK3", "severity": 5, "solo_compliance": 0.99,
         "chance_compliance": 0.995, "prescreen_solo_compliance": 0.5,
         "prescreen_chance_compliance": 0.0},
    ]
    out = gates_run._prescreen_to_calibration(rows)
    assert out["n_paired"] == 1
    assert out["per_candidate"][0]["candidate"] == "MK1:3"
    assert out["per_candidate"][0]["d_solo"] == pytest.approx(0.40)
    assert out["per_candidate"][0]["d_iota"] == pytest.approx(0.40)
    assert out["solo"]["mean_abs"] == pytest.approx(0.40)
    assert out["read_by"] == []
    # Nothing pairable at all reports None, never a spurious zero.
    empty = gates_run._prescreen_to_calibration([rows[1]])
    assert empty["n_paired"] == 0
    assert empty["solo"]["mean_abs"] is None
    assert empty["iota"]["max_abs"] is None


# ---------------------------------------------- branches and edge cases

def _support(**pairs):
    return {str(q): {"severity": q, "can_support": ok,
                     "qualified_families": [], "n_qualified_families": 0,
                     "min_qualified_families": C.MIN_QUALIFIED_FAMILIES}
            for q, ok in pairs.items()}


def test_the_order_drops_severities_that_cannot_support_and_keeps_m_star():
    order, reason = feasibility.restricted_operating_point_order(
        [9, 8, 11], _support(**{"9": True, "8": False, "11": True}),
        m_star=9)
    assert order == [9, 11]
    assert "five families" in reason


def test_m_star_leads_the_order_even_when_it_cannot_support():
    """P3.1 probes m* first by rule. The filter narrows what m* may move
    *to*; it never removes §12.3's own choice from the front."""
    order, _ = feasibility.restricted_operating_point_order(
        [9, 8, 11], _support(**{"9": False, "8": False, "11": True}),
        m_star=9)
    assert order == [9, 11]


def test_no_supporting_severity_leaves_the_order_whole_for_d6():
    """The branch that had no test, and the one that would have been wrong.

    Narrowing to nothing would have the probe answer §34 D6 --- terminal or
    identification status --- two stages before Gate 3C, and without a record
    saying it had.
    """
    order, reason = feasibility.restricted_operating_point_order(
        [9, 8, 11], _support(**{"9": False, "8": False, "11": False}),
        m_star=9)
    assert order == [9, 8, 11]
    assert "D6" in reason and "left whole" in reason


def test_the_order_rule_tolerates_an_m_star_outside_the_admissible_set():
    """Defensive, and it must not invent a severity nobody measured."""
    curve = {7: 0.95, 8: 0.86}
    order = feasibility.operating_point_order(
        m_star=9, admissible=[7, 8], curve=curve)
    assert order[0] == 9
    assert sorted(order) == [7, 8, 9]


def test_the_calibrated_coverage_reports_nothing_it_cannot_pair(
        harness_decisions):
    """No ``iota_a_prescreen`` means no paired contrast --- and the fields say
    so with None rather than with a number that would read as zero drift."""
    gate2 = {"iota_a": 0.5, "calibration_rows": {"pooled": []}}
    regime = {"coverage_eligibility_formulation": "E2",
              "iota_a_prescreen": None, "expansion": {}}
    out = feasibility.coverage_at_calibrated_iota_a(
        gate2_record=gate2, regime_record=regime)
    assert out["iota_a_prescreen"] is None
    assert out["iota_a_movement"] is None
    assert out["conditions_at_prescreen_iota_a"] is None
    assert out["conditions_moved_by_the_reference_point"] == []
    assert out["conditions_moved_by_the_basis"] == []
    # It still gates: an empty table meets no decisive condition.
    assert out["decisive_met"] is False
    assert out["failures"] == [feasibility.CALIBRATED_COVERAGE_FAILURE]
