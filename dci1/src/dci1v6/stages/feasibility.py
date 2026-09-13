"""The §13.15 reference-support criterion, evaluated **once**, in one place.

**Why this module exists.** v5 lost three of four replications at the
registered C4 gate and the fourth at composed headroom, and the development
work that preceded it had asked a *different, easier* question: whether the
reserve rungs the expansion would admit fall inside the solo band. Falling
inside the solo band is a necessary condition for one rung. It is not the
support criterion. The criterion is §13.1's full V(R) on both calibration
splits, §13.6's kappa(R|B) at the operating point, §13.7's stability, §13.8's
caliper against iota_A, §13.15's counts, and the two frozen unused backups ---
a conjunction over the whole library, and a development prescreen that
evaluated a proxy for it could not have predicted what the registered gate
did.

So this module holds the **kernels** the registered stages run, and it is the
same code a development pilot calls. Gate 3A calls ``calibration_at``, Gate 3B
calls ``selection_at`` and Gate 3C calls ``support_at``, and so does
``tools/v6_reference_feasibility.py``. There is no second implementation for
development to drift away from, and ``tests_v6/test_reference_feasibility.py``
pins all three against the four **signed v5 records** so that an extraction
which changed the criterion fails rather than passes quietly.

**The chain is free.** Gate 3A, 3B and 3C generate no rows: every quantity
they read was measured at Gate 2 and Gate 2.5. That is what makes an
operating-point search tractable at all --- the whole of

    m* -> kappa(R|B) -> qualification -> support -> reference selection

is a pure function of two signed records, so it can be evaluated at **every**
candidate operating point before a single composed row exists. Only the last
link, composed headroom, costs generation.

**Two coherent groups live here, and that is the whole scope.** The
criterion --- ``calibration_at``, ``selection_at``, ``support_at`` and the
§12.6 re-reading --- and the machinery that asks *at which operating points*
the criterion can hold: ``operating_point_order``,
``qualified_family_support`` and ``restricted_operating_point_order``. The
second group exists because the first is free, and it reads nothing the first
does not. §12.3's *selection* rule stays in ``stages/regime.py``, which owns
it; what is here is the frozen order that rule induces over an already
admissible set.

**This module selects nothing and it is not a gate.** It computes; the stages
that call it decide, raise and record. Nothing here writes a record and
nothing here raises a terminal status --- a caller evaluating a candidate
operating point needs a verdict, not a stopped replication.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.design.cells import normalise_arms
from dci1v6.protocol import constants as C
from dci1v6.stages import regime, selection, stability, support
from dci1v6.stages.calibration_table import load_calibration_table
from dci1v6.verifiers.constraints import FAMILIES

__all__ = ["calibration_rows_at", "qualification_at", "calibration_at",
           "selection_at", "support_at",
           "SUPPORT_MARGIN_KEYS", "support_margin",
           "coverage_at_calibrated_iota_a", "CALIBRATED_COVERAGE_FAILURE",
           "qualified_family_support", "operating_point_order",
           "restricted_operating_point_order"]


# ------------------------------------------- the two record readers

def calibration_rows_at(gate2_record: Mapping[str, Any], *, m_star: int,
                        split: str) -> list[dict[str, Any]]:
    """Gate 2's §13.11 table, with the kappa(R|B) column at ``m_star``.

    Every other column is a solo or chance quantity measured with B absent and
    does not move with the operating point. kappa(R|B) does; §13.11 makes its
    source travel with the value, and ``assert_kappa_under_b_source`` refuses
    a table read at an operating point the column was not measured at. The
    study runs at the m* §12.3 froze at Gate 2, so the column read is the one
    measured there.

    The column is **selected, never recomputed**: it comes from the map Gate 2
    signed before Gate 2.5 qualified anything and before the probe ran.
    """
    rows = [dict(r) for r in gate2_record["calibration_rows"][split]]
    if int(m_star) == int(gate2_record["m_star"]):
        return rows
    by_severity = gate2_record.get("kappa_under_b_by_severity") or {}
    column = (by_severity.get(str(int(m_star))) or {}).get(split)
    if column is None:
        raise ProtocolError(
            f"§13.6: Gate 2 recorded no kappa(R|B) column at m*={m_star} on "
            f"split {split!r}, so §13.11's table cannot be read at the "
            "operating point Gate 2.75 selected. Gate 2 records a column for "
            "every severity in `focal_admissible` and the probe may select "
            "no other")
    out: list[dict[str, Any]] = []
    for row in rows:
        row.pop("kappa_under_b", None)
        row.pop("kappa_under_b_source", None)
        entry = column.get(f"{row['kind']}:{row['severity']}")
        if entry is not None:
            row["kappa_under_b"] = entry["kappa_under_b"]
            row["kappa_under_b_source"] = dict(entry["kappa_under_b_source"])
        out.append(row)
    return out


def qualification_at(gate2_5_record: Mapping[str, Any], *,
                     m_star: int) -> Mapping[str, Any]:
    """Gate 2.5's §13.6 pool at the frozen operating point.

    Gate 2.5 qualifies at **every** admissible severity because it generates
    nothing, so its record carries a column rather than a pool. This selects
    the entry for the m* §12.3 froze at Gate 2 --- by name, so a stage cannot
    read the column positionally and land on a severity the study does not
    run at.
    """
    by_severity = gate2_5_record.get("qualification_by_severity") or {}
    entry = by_severity.get(str(int(m_star)))
    if entry is None:
        raise ProtocolError(
            f"§13.6: Gate 2.5 recorded no qualified pool at m*={m_star}; it "
            f"holds {sorted(by_severity)}. A stage after Gate 2.75 reads the "
            "pool at the operating point the probe selected, and a missing "
            "one is a lifecycle fault rather than a reason to fall back")
    return entry


# ------------------------------------------------------- the three kernels

def calibration_at(*, model_key: str, gate2_record: Mapping[str, Any],
                   gate2_5_record: Mapping[str, Any], m_star: int,
                   seed: int = 0,
                   resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
                   ) -> dict[str, Any]:
    """§13.7 on both splits and pooled, at one operating point.

    The kernel Gate 3A records. The two split tables are loaded separately and
    ``assert_not_pooled`` refuses a table carrying the other split's rows,
    because §13.7's two estimates are independent only if their rows are.
    """
    tables = {split: calibration_rows_at(gate2_record, m_star=m_star,
                                         split=split)
              for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")}
    qualified_at = qualification_at(gate2_5_record, m_star=m_star)
    qualified = list(qualified_at["qualified_pool"])
    population = stability.calibration_b_population(
        carried=[r["kind"] + ":" + str(r["severity"])
                 for r in tables[C.CALIBRATION_A]],
        a_survivors=qualified)
    table_a = load_calibration_table(tables[C.CALIBRATION_A],
                                     model_key=model_key, m_star=m_star,
                                     split=C.CALIBRATION_A)
    table_b = load_calibration_table(tables[C.CALIBRATION_B],
                                     model_key=model_key, m_star=m_star,
                                     split=C.CALIBRATION_B)
    table_pooled = load_calibration_table(tables["pooled"],
                                          model_key=model_key, m_star=m_star,
                                          split="pooled")
    stability.assert_not_pooled(table_a, split=C.CALIBRATION_A)
    stability.assert_not_pooled(table_b, split=C.CALIBRATION_B)
    pairs = stability.split_pair(table_a, table_b)
    verdicts = {label: stability.stability_verdict(
        pair, iota_a_by_split=gate2_record["iota_a_by_split"],
        solo_a_by_split=gate2_record["solo_a_by_split"], seed=seed,
        resamples=resamples)
        for label, pair in pairs.items()}
    # §13.7: iota_A is subject to the same equivalence rule as every
    # candidate, and §12.2 measured it moving by up to 0.048 between stages.
    a_splits = gate2_record.get("a_per_topic_by_split") or {}
    per_topic = a_splits.get("per_topic") or {}
    chance = a_splits.get("chance") or {}
    if (per_topic.get(C.CALIBRATION_A) and per_topic.get(C.CALIBRATION_B)
            and chance.get(C.CALIBRATION_A) is not None
            and chance.get(C.CALIBRATION_B) is not None):
        iota_a_stability = stability.assert_iota_a_stable(
            per_topic_a=per_topic[C.CALIBRATION_A],
            per_topic_b=per_topic[C.CALIBRATION_B],
            chance_a=chance[C.CALIBRATION_A],
            chance_b=chance[C.CALIBRATION_B], seed=seed + 2,
            resamples=resamples)
    else:
        iota_a_stability = {
            "quantity": "iota_A", "passed": None,
            "reason": "Gate 2 recorded no per-topic vector for A on both "
                      "splits, so §13.7's rule could not be evaluated; that "
                      "is not the same as passing it"}
    return {
        "m_star": int(m_star), "model_key": model_key,
        "tables": tables, "pooled_table": tables["pooled"],
        "calibration_b_population": list(population),
        "n_rows": {C.CALIBRATION_A: len(table_a),
                   C.CALIBRATION_B: len(table_b),
                   "pooled": len(table_pooled)},
        "stability": verdicts,
        # V6-E05. `stability_verdict` returns `passed`; it has never returned
        # `stable`, so `v.get("stable")` was None for every candidate and this
        # count read **0 on every replication**. All four signed v5 records
        # carry `n_stable: 0` beside 9 to 16 candidates whose own verdict says
        # `passed: true`. It gates nothing and no stage reads it --- which is
        # why it survived --- but a reader of those records would take it as
        # "no candidate was stable", and that is not what §13.7 found.
        # v5 is not touched: its records say what its code computed.
        "n_stable": sum(1 for v in verdicts.values() if v.get("passed")),
        "iota_a_stability": iota_a_stability,
        "qualified_pool": qualified,
        "qualified_families": list(qualified_at["qualified_families"]),
        "n_qualified": qualified_at["n_qualified"],
        "iota_a": gate2_record["iota_a"],
        "solo_compliance_a": gate2_record["solo_compliance_a"],
    }


def selection_at(calibration: Mapping[str, Any], *,
                 model_key: str, n_topics_a: int | None = None
                 ) -> dict[str, Any]:
    """§13.8, §13.9, §13.10 and §13.12 on the pooled table. The Gate-3B
    kernel.

    Both coordinates A is matched on come from the calibration kernel, which
    got them from Gate 2. A selection run against an iota_A the caller
    supplied would be a selection against a number with no producer.
    """
    rows = load_calibration_table(calibration["pooled_table"],
                                  model_key=model_key,
                                  m_star=calibration["m_star"], split="pooled")
    result = selection.select_all(
        rows, iota_a=calibration["iota_a"],
        solo_compliance_a=calibration["solo_compliance_a"],
        n_topics_a=n_topics_a,
        stability_by_candidate=dict(calibration.get("stability") or {}))
    return {"core": result.core, "spectrum": result.spectrum,
            "near_form": result.near_form,
            "broad_class": result.broad_class,
            "slot_map": {k: list(v) for k, v in result.slot_map().items()},
            "identification_statuses": result.identification_statuses}


def support_at(chosen: Mapping[str, Any], *, model_key: str,
               calibration: Mapping[str, Any],
               regime_record: Mapping[str, Any],
               extra_design_time_failures: Sequence[str] = ()
               ) -> dict[str, Any]:
    """§13.15's counts and every identification status. The Gate-3C kernel.

    ``chosen`` is ``selection_at``'s result. The arm-availability rules are
    the ones Gate 3C registers: an arm is available when the screen's coverage
    admitted it **and** selection bound a companion for it.
    """
    structurally_eligible = sorted({
        label.rpartition(":")[0] for label in regime_record["carried_set"]
        if FAMILIES[label.rpartition(":")[0]].structural_tier in (1, 2)})
    core_block = chosen.get("core") or {}
    # `evaluate_support` reads `core_references` and `identification_statuses`
    # at the top level of what it is given, and the selection result nests
    # them under the pool they came from.
    flattened = {
        "core_references": core_block.get("core_references") or [],
        "identification_statuses":
            chosen.get("identification_statuses") or [],
    }
    screen_statuses = set(regime_record.get("identification_statuses") or ())
    near_form_available = bool(
        (chosen.get("near_form") or {}).get("controls")
    ) and "NEAR_FORM_ARM_NOT_AVAILABLE" not in screen_statuses
    class_available = bool(
        (chosen.get("broad_class") or {}).get("companion")
    ) and "CLASS_ARM_NOT_AVAILABLE" not in screen_statuses
    spectrum_identified = bool(core_block.get("spectrum_identified"))
    design_time_failures = (
        ["§12.6: the identification-coverage criterion was not met after the "
         "registered expansion rounds, so the replication runs without the "
         "core and spectrum arms"]
        if "REFERENCE_SUPPORT_NOT_IDENTIFIED" in screen_statuses else [])
    # §12.6 re-read at the calibrated iota_A enters here rather than raising
    # its own status: it is the **same criterion** with the same consequence,
    # so it takes §34 D6's registered disposition and cannot acquire a second
    # one. `coverage_at_calibrated_iota_a` produces it and Gate 3A carries it.
    design_time_failures = design_time_failures + list(
        extra_design_time_failures)
    report = support.evaluate_support(
        model_key=model_key,
        structurally_eligible_tier12_families=structurally_eligible,
        qualified_families=list(calibration["qualified_families"]),
        selection=flattened,
        near_form_available=near_form_available,
        class_available=class_available,
        spectrum_identified=spectrum_identified,
        design_time_failures=design_time_failures)
    return {
        "report": report,
        "structurally_eligible_tier12_families": structurally_eligible,
        "screen_statuses": sorted(screen_statuses),
        "design_time_failures": design_time_failures,
        "arms": list(normalise_arms(report["admitted_arms"])),
        "identification_statuses":
            sorted(set(report["identification_statuses"]) | screen_statuses),
    }


# --------------------------------- the operating-point search, at no cost

def operating_point_order(*, m_star: int, admissible: Sequence[int],
                          curve: Mapping[int, float]) -> list[int]:
    """§12.3's own preference over the admissible severities, recorded.

    Ascending distance from §12.3's aim on Gate 2's measured solo curve, ties
    to the smaller severity, with m* first because m* is §12.3's choice.

    **Nothing tries these in turn.** m* is frozen at Gate 2 and
    ``GATE_2_75_COMPOSED_PROBE`` measures composed headroom at m* alone, so
    this is a *record* of how §12.3 ranked the admissible set --- written
    before any composed row exists, and useful for exactly two things: the
    head is where Gate 2 and Gate 2.5 record their agreement about the
    operating point, and the tail says what §12.3 would have preferred next
    had the study been designed to move, which it is not.
    """
    from dci1v6.stages.calibration_table import tie_key

    rest = [int(q) for q in sorted(set(int(x) for x in admissible))
            if int(q) != int(m_star)]
    rest.sort(key=lambda q: (tie_key(abs(curve[q] - C.FOCAL_AIM)), q))
    return [int(m_star)] + rest


def qualified_family_support(gate2_5_record: Mapping[str, Any], *,
                             severities: Sequence[int]) -> dict[str, Any]:
    """§13.15's five-family requirement at each admissible operating point.

    **Already computed and signed; this only reads it.** Gate 2.5 runs the
    full V(R) --- including §13.6's V_inter against that severity's own
    kappa(R|B) column --- at every admissible severity, because it generates
    nothing. So "can this severity support a reference set at all?" is a
    lookup, not a recomputation, and re-running §13.7's bootstrap per
    severity to answer it would resample identical per-topic vectors with
    identical seeds for a verdict Gate 2.5 already holds.

    Since m* is frozen at Gate 2 the study runs at one of these and only one.
    The rest are recorded because a signed prospective statement of where a
    reference set could have existed is evidence about the design, and
    because dropping the column would make Gate 2.5's own m* entry
    unfalsifiable against its neighbours.

    This is a **necessary** condition, exactly evaluated: §13.15 also requires
    three core references over three feature groups with two Tier-1 among them
    and two frozen backups, and those need a selection. A severity that fails
    *this* cannot satisfy the conjunction, which is all a pre-filter needs.
    """
    by_severity = gate2_5_record.get("qualification_by_severity") or {}
    out: dict[str, Any] = {}
    for severity in sorted({int(q) for q in severities}):
        entry = by_severity.get(str(severity))
        if entry is None:
            raise ProtocolError(
                f"§13.15: Gate 2.5 recorded no qualification at m*={severity};"
                f" it holds {sorted(by_severity)}. The recorded order is "
                "Gate 2's `focal_admissible` and Gate 2.5 qualifies at "
                "exactly that set, so a gap is a lifecycle fault")
        families = sorted(set(entry["qualified_families"]))
        out[str(severity)] = {
            "severity": severity,
            "qualified_families": families,
            "n_qualified_families": len(families),
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "can_support": len(families) >= C.MIN_QUALIFIED_FAMILIES,
            "necessary_not_sufficient":
                "§13.15 also requires three core references over three "
                "feature groups, two of them Tier 1, and two frozen backups; "
                "those need a selection and are evaluated at Gate 3C",
        }
    return out


def restricted_operating_point_order(
        search_order: Sequence[int], support: Mapping[str, Any], *,
        m_star: int) -> tuple[list[int], str]:
    """§12.3's recorded order, narrowed to where a reference set can exist.

    Two branches, and the second is the one that matters:

    * **Some severity can support.** The order keeps m* first --- §12.3 chose
      it and it is frozen --- and drops the severities that cannot reach
      §13.15's five-family minimum.
    * **None can.** The order is **not** narrowed to nothing. Whether an unmet
      §13.15 is terminal or an identification status is §34 D6's question and
      it is answered at Gate 3C; narrowing to nothing here would answer it
      two stages early and without a record saying so.

    Returns the order and the reason, so the record carries which branch ran.

    **This narrows a record, not a search.** Gate 2.75 probes the frozen m*
    and nothing else, so nothing downstream consumes the tail. What the head
    is for is the cross-gate agreement check in ``gates_run.gate2_75_payload``:
    a Gate 2.5 record whose order does not start at Gate 2's m* means the two
    gates disagree about the operating point, and that is a lifecycle fault
    caught before a composed row is drawn.
    """
    can_support = [int(q) for q in search_order
                   if support[str(int(q))]["can_support"]]
    if not can_support:
        return (list(int(q) for q in search_order),
                "no admissible severity reaches §13.15's five-family "
                "minimum, so the order is left whole and §34 D6 --- not this "
                "restriction --- decides what that means")
    order = ([int(m_star)] if int(m_star) in
             [int(q) for q in search_order] else []) + [
        q for q in can_support if q != int(m_star)]
    return (order,
            "Gate 2's frozen order restricted to the severities where at "
            "least §13.15's five families pass the full V(R) at that "
            "operating point")


# ------------------------------------ §12.6 re-read where selection matches

#: What Gate 3C is given when the calibrated re-reading loses a decisive
#: condition. The wording mirrors the screen-time failure because it **is**
#: the same criterion and the same consequence: §34 D6 governs both, and
#: neither reopens the candidate library.
CALIBRATED_COVERAGE_FAILURE = (
    "§12.6: the identification-coverage criterion is not met at the iota_A "
    "reference selection matches on, evaluated on the calibration basis where "
    "iota(R), the eligibility coordinate, the vacuity and iota_A are all "
    "measured on the same 192 topics at the same four draws")


def coverage_at_calibrated_iota_a(*, gate2_record: Mapping[str, Any],
                                  regime_record: Mapping[str, Any]
                                  ) -> dict[str, Any]:
    """§12.6's criterion at the iota_A the study actually matches on.

    **Three readings, and the contrast between two of them is paired.**

    1. ``certified`` --- what §12.6 signed: the pre-screen table at
       ``iota_a_prescreen``. 24 topics, one draw, and iota(R) and iota_A
       measured on the same cases.
    2. ``calibration_basis_at_prescreen_iota_a`` --- the calibration table at
       the *same* reference point.
    3. ``calibration_basis`` --- the calibration table at Gate 2's measured
       ``iota_a``. **This is the reading that gates.**

    (2) to (3) varies one quantity over one fixed set of cases, so whatever
    moves between them is the reference point moving and nothing else. (1) to
    (2) is the change of basis. The single number this replaces --- a drift
    between an iota_A on 24 pre-screen topics and an iota_A on 192 calibration
    topics, applied to a table measured on the first --- confounded the two
    and could not report either.

    **No drift threshold exists here and none is proposed.** The criterion is
    §12.6's own, unchanged, and the question is whether it holds where
    selection works, not whether some distance is small.
    """
    formulation = regime_record.get("coverage_eligibility_formulation")
    iota_a_measured = float(gate2_record["iota_a"])
    prescreen = regime_record.get("iota_a_prescreen")
    rows = regime.calibration_coverage_rows(
        gate2_record["calibration_rows"]["pooled"], formulation=formulation)
    at_measured = regime.coverage_criterion(rows, iota_a=iota_a_measured)
    at_prescreen = (None if prescreen is None else
                    regime.coverage_criterion(rows, iota_a=float(prescreen)))
    certified = (regime_record.get("expansion") or {}).get("coverage") or {}
    moved_by_the_reference_point = (
        [] if at_prescreen is None else
        sorted(c for c in C.COVERAGE_CONDITIONS
               if at_prescreen["conditions"].get(c)
               != at_measured["conditions"].get(c)))
    moved_by_the_basis = (
        [] if at_prescreen is None else
        sorted(c for c in C.COVERAGE_CONDITIONS
               if c in (certified.get("conditions") or {})
               and certified["conditions"][c]
               != at_prescreen["conditions"].get(c)))
    decisive_met = bool(at_measured["decisive_met"])
    return {
        "gates": "the decisive conditions on the calibration basis at the "
                 "measured iota_A",
        "costs_no_generation": True,
        "basis": "§13.11's calibration table: 192 pooled calibration topics "
                 "at M_cal draws, the same cases iota_A is measured on",
        "population": "§12.7's calibrated set, which is the set a reference "
                      "can actually be drawn from",
        "formulation": formulation,
        "iota_a_prescreen": prescreen,
        "iota_a_measured": iota_a_measured,
        "iota_a_movement": (None if prescreen is None
                            else iota_a_measured - float(prescreen)),
        "n_rows": len(rows),
        "n_eligible": at_measured["realised"]["n_eligible"],
        "conditions": dict(at_measured["conditions"]),
        "decisive_met": decisive_met,
        "realised": dict(at_measured.get("realised") or {}),
        "conditions_at_prescreen_iota_a": (
            None if at_prescreen is None
            else dict(at_prescreen["conditions"])),
        "decisive_met_at_prescreen_iota_a": (
            None if at_prescreen is None else at_prescreen["decisive_met"]),
        "certified_conditions": dict(certified.get("conditions") or {}),
        "certified_basis": "§12.2's pre-screen table at iota_a_prescreen: 24 "
                           "topics at one draw",
        # The two contrasts, kept apart. The first is paired --- identical
        # rows, one reference point moved. The second is the change of basis.
        "conditions_moved_by_the_reference_point":
            moved_by_the_reference_point,
        "conditions_moved_by_the_basis": moved_by_the_basis,
        "failures": [] if decisive_met else [CALIBRATED_COVERAGE_FAILURE],
    }


# ------------------------------------------------------------- the margin

#: What §13.15 asks for, and therefore what "with margin" is measured against.
#: Each entry is (realised key, registered minimum). ``support_margin``
#: reports realised - minimum, so a **negative** entry is a failure and a
#: **zero** entry is a criterion met with nothing to spare --- which is the
#: state v4r4 was in on three replications and is exactly what §13.15 exists
#: to refuse.
SUPPORT_MARGIN_KEYS: tuple[tuple[str, str], ...] = (
    ("structurally_eligible_tier12_families",
     "min_structurally_eligible_tier12_families"),
    ("qualified_families", "min_qualified_families"),
    ("tier1_core", "min_tier1_core"),
)


def support_margin(report: Mapping[str, Any]) -> dict[str, Any]:
    """§13.15's realised counts minus its registered minima.

    ``support_met`` is a conjunction of equalities and inequalities and it
    answers "did this replication qualify?". It does not answer "by how much?",
    and the second question is the one a development pilot has to answer
    before a library is frozen: a library that clears §13.15 by nothing on
    development data is a library that will not clear it on a fresh draw.
    """
    realised = report.get("realised") or {}
    required = report.get("requirements") or {}
    margins = {realised_key: int(realised.get(realised_key, 0))
                              - int(required.get(required_key, 0))
               for realised_key, required_key in SUPPORT_MARGIN_KEYS}
    # `frozen_backups` is deliberately NOT a margin. `freeze_backups` returns
    # `spare[:N_BACKUP_FAMILIES]`, so its length is a truncation and equals
    # the requirement whenever the requirement is met --- a margin of zero
    # every time, which would dominate `min_margin` and make it meaningless.
    # The quantity it would have measured is the qualified-family margin,
    # because §13.15's five is three used plus two frozen.
    return {
        "margins": margins,
        "min_margin": min(margins.values()) if margins else 0,
        "binding": sorted(k for k, v in margins.items()
                          if v == min(margins.values())),
        "n_backup_families": len(realised.get("frozen_backups") or ()),
        "note": "realised minus the §13.15 minimum, per requirement. Zero "
                "means the criterion is met with nothing to spare. The "
                "backup count is not a margin --- §13.15's five qualified "
                "families ARE three used plus two frozen, so the "
                "qualified-family margin is the spare beyond both",
    }

# NOTE. There is deliberately **no** `reference_feasibility(m_star)` wrapper
# composing the three kernels. Gate 3A, Gate 3B and Gate 3C are three stages
# and each calls one kernel; nothing in the lifecycle wants the composition,
# and the development report builds its inputs from a Gate-3A record rather
# than from a Gate-2 one. A convenience wrapper with no caller is the shape
# the A8 reachability audit exists to catch, so it is not written.
