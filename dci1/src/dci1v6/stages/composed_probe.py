"""§18 stage 8: ``GATE_2_75_COMPOSED_PROBE`` --- composed headroom before
reference selection (v6's addition).

**The problem it exists for.** m* is chosen at Gate 2 from B's *solo* curve,
and §13.14 checks composed compliance only at Gate 4 --- after the references
are selected, calibrated and bound. On the closed v5 study all four
replications sat within 0.054 of the ceiling or over it once B was composed,
and one of them terminated there with every earlier gate passed. The
measurement that would have shown it was available two stages earlier and
nobody took it.

**What the probe measures, stated correctly.** It measures **compliance** ---
the same kind of quantity §13.14 already governs --- for B and for frozen
structural stand-ins, composed and solo, on a development split. It is *not*
free of outcomes and this module never says it is. What makes it
interaction-blind is narrower and checkable: it is blind to any *reference*
and to any *composed contrast*. Four independent guarantees, and each is
enforced somewhere a reader can point at:

1. **Temporal.** The stage runs between Gate 2.5 and Gate 3A. No reference
   exists: Gate 3B has not run, the slot map is empty, and
   ``assert_predecessor_passed`` refuses a stage whose predecessor has not
   recorded PASS. There is no R to compose.
2. **Structural.** A stand-in is a ``probe_only`` family and
   ``verifiers.constraints.assert_selectable`` refuses one everywhere a
   candidate is carried, qualified, calibrated or bound. No probed cell can
   be a B+R cell even by coincidence of instrument identity.
3. **Informational.** §13.11's schema refusal already rejects a composed
   outcome reaching reference selection --- ``load_calibration_table`` takes a
   closed schema and a composed-outcome field has nowhere to land --- and
   §33 check 8's name scan now reads **this** record on the same terms as the
   Gate-4 record, with its own declared refusals.
4. **Directional.** The one value this stage writes that a later stage reads
   is m*, and m* is B's own severity. ``assert_probe_reads_no_reference``
   refuses, by name and by source, any function here that would read a
   selection record.

**One re-selection, by a rule fixed before data (P3).** If m* fails the
margin the probe re-runs ``regime.select_operating_point`` **unchanged** over
**Gate 2's own solo B curve**, restricted to the severities the probe found
admissible. The probe decides *which severities are admissible*; it never
decides which is chosen. There is exactly one re-selection, there is no path
from a Gate-3, Gate-4 or pre-freeze outcome back to this stage, and when no
severity is admissible the replication terminates
``COMPOSED_HEADROOM_UNREACHABLE``.

**§13.14's band is unchanged.** delta is a **margin inside** [0.05, 0.95],
not a relaxation of it. Gate 4 still applies the registered band to the
registered composed set.

**Three things this module does not decide, and refuses to.** The topic split
(§34 D20), the margin's value (D23) and which stand-ins exist (D24) are open
researcher decisions. Every accessor below goes through
``protocol/decisions``, so no caller gets a default and no stage can run while
one is open. The two scope limits READINESS §3.2 states also stand and are
recorded on the payload: the probe protects the **B slot only** --- it cannot
see a companion-slot Gate-4 failure like the one that terminated
``gemma-3n-e4b-it`` --- and Change 1 succeeding raises Gate-4 exposure from 6
to as many as 95 cell x slot entries.
"""
from __future__ import annotations

import inspect
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.stages.regime import select_operating_point
from dci1v6.verifiers.constraints import (
    PROBE_ONLY_FAMILY_IDS, Constraint, focal_severities,
)

__all__ = ["COMPOSED_HEADROOM_UNREACHABLE", "PROBE_SLOTS", "probe_slots",
           "probe_cell_types", "probe_split", "margin", "standins",
           "margin_band", "severity_verdict", "probe_disposition",
           "assert_probe_reads_no_reference", "PROBE_DECLARED_REFUSALS",
           "REFERENCE_TOKENS", "FORBIDDEN_SOURCE_READS",
           "PROBE_SCOPE_LIMITS", "assert_probe_severities_are_admissible",
           "SHARED_WITH_GATE2", "shared_cell_verdict"]

#: §28, new in v6. Raised by ``probe_disposition`` and nowhere else.
COMPOSED_HEADROOM_UNREACHABLE = "COMPOSED_HEADROOM_UNREACHABLE"

#: The probe's own slot names. They are deliberately **not** in
#: ``C.REGISTERED_SLOT_ORDER``: a stand-in has no slot in the confirmatory
#: design, so there is no name a probe cell and a design cell could share.
PROBE_SLOTS: tuple[str, ...] = ("P1", "P2", "P3")


def probe_slots(n: int) -> tuple[str, ...]:
    """The first ``n`` probe slots. Refuses more than the registered three."""
    if not 1 <= n <= len(PROBE_SLOTS):
        raise ProtocolError(
            f"the probe registers {len(PROBE_SLOTS)} stand-in slots "
            f"{PROBE_SLOTS} and {n} were asked for")
    return PROBE_SLOTS[:n]


def probe_cell_types(standin_slots: Sequence[str]
                     ) -> list[tuple[str, str, tuple[str, ...]]]:
    """``(cell_id, arm, slots)`` for one probed severity, in a stable order.

    Per severity: the unconstrained cell, B solo, each stand-in solo, and
    both orders of B with each stand-in. The stand-in solo cells are what S4's
    operating point is read from and what the composed lift is measured
    *against*, so they are not optional.

    Stand-ins are never paired with each other: the quantity the probe is
    after is the lift on **B**, and a stand-in pair would measure something no
    registered rule reads.
    """
    slots = tuple(standin_slots)
    if len(set(slots)) != len(slots):
        raise ProtocolError(f"duplicate probe slot in {slots}")
    unknown = [s for s in slots if s not in PROBE_SLOTS]
    if unknown:
        raise ProtocolError(f"{unknown} are not registered probe slots")
    types: list[tuple[str, str, tuple[str, ...]]] = [
        ("unconstrained", "unconstrained", ()),
        ("solo:B", "solo", ("B",))]
    types += [(f"solo:{s}", "solo", (s,)) for s in slots]
    for s in slots:
        types.append((f"pair:B+{s}", "composed", ("B", s)))
        types.append((f"pair:{s}+B", "composed", (s, "B")))
    return types


# --------------------------------------------------- the open decisions

def probe_split() -> str:
    """§34 D20 (READINESS R2): which topic split the probe runs on.

    Both branches exist in the source and neither is reachable while the
    decision is open, which is the whole point of ``choice``.

    * ``calibration_pooled`` --- §6.2's 192 calibration topics, pooled. The
      most precise option and it spends no reserved topics; delta then has to
      absorb the calibration-to-composed transfer, whose realised magnitude on
      closed v5 reached +0.189.
    * ``reserved_composed`` --- the §6.2 composed set. Removes the transfer as
      a *bias* and buys roughly 2.8x the sampling variance in exchange, and it
      spends a set §6.2 spends once, so it couples to D21.
    * ``calibration_with_measured_transfer`` --- the calibration split, with
      the stand-ins measured on **both** 96-topic sub-splits so the realised
      split-to-split movement is recorded beside the margin verdict. It makes
      the size of delta's assumption visible on the record instead of buried
      in a constant, and it costs no extra rows because §13.7 already
      generates both sub-splits.
    """
    return decisions.choice(
        "D20",
        {"calibration_pooled": "calibration_pooled",
         "reserved_composed": "composed",
         "calibration_with_measured_transfer": "calibration_both_subsplits"},
        where="stages.composed_probe.probe_split")


def margin() -> float:
    """§34 D23 (READINESS R5): the margin delta inside §13.14's band.

    **No value is proposed and none is coded.** The closed-v5 evidence in
    ``reports/dci1v6/readiness_evidence.json`` establishes that the error the
    margin has to absorb lies *above* the examined range {0.025, 0.05, 0.075},
    which is a finding about the range and not a choice within it. This reads
    the researcher's closure and validates that it leaves §13.14's band with
    something inside it.
    """
    decisions.assert_decisions_closed_for(
        "stages.composed_probe.margin")
    value = decisions.value_of("D23")
    low, high = C.COMPOSED_HEADROOM_BAND
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProtocolError(
            f"§34 D23 closed at {value!r}; the margin is a number")
    value = float(value)
    if not 0.0 <= value < (high - low) / 2:
        raise ProtocolError(
            f"§34 D23 closed at {value}, which leaves no interior to "
            f"{list(C.COMPOSED_HEADROOM_BAND)}. delta is a margin inside the "
            "registered band and never a change to it")
    return value


def margin_band() -> tuple[float, float]:
    """[0.05 + delta, 0.95 - delta]. §13.14's band is unchanged and unread
    here; this is the *interior* the probe requires."""
    low, high = C.COMPOSED_HEADROOM_BAND
    delta = margin()
    return (low + delta, high - delta)


def standins() -> tuple[Constraint, ...]:
    """§34 D24 (READINESS R6): the frozen structural stand-ins.

    Both branches exist. Neither yields an instrument today, because no
    ``probe_only`` family is authored --- that authoring is the researcher's
    act and it changes ``assert_library_sizes``' counts, which is exactly the
    visibility R6 asks for.

    The severity each stand-in is probed at is **not** fixed here: S4 reads it
    from that stand-in's own solo curve measured in this stage, by
    ``select_operating_point``'s existing rule. No reference, no candidate and
    no composed contrast enters that choice.
    """
    registered = decisions.choice(
        "D24",
        {"probe_only_in_library": PROBE_ONLY_FAMILY_IDS,
         "separate_vocabulary": ()},
        where="stages.composed_probe.standins")
    if not registered:
        raise ProtocolError(
            "§34 D24 is closed but no probe-only stand-in is registered. The "
            "probe composes B with stand-ins and cannot run without them; "
            "authoring them is a change to §7.10's library and to the counts "
            "`assert_library_sizes` asserts")
    return tuple(registered)


# ------------------------------------------------------------ the P3 rule

def assert_probe_severities_are_admissible(
        severities: Sequence[int], gate2_record: Mapping[str, Any]) -> None:
    """P3.1: the probed set is the set Gate 2 recorded as **admissible**.

    Not the registered grid and not a set this stage chose. ``eligible`` is
    §12.3's band test on the solo curve alone; ``focal_admissible`` is that
    set intersected with §12.4's regime adequacy and §34 D17's construct
    floor, each evaluated *at that severity*. The distinction is the whole
    point: Gate 2 applies §12.4 and D17 at m* and terminates the replication
    when either fails, so probing --- and re-selecting to --- a merely
    *eligible* severity would move B to an operating point Gate 2 would itself
    have refused.

    Both sets are checked, so a record written before ``focal_admissible``
    existed fails here rather than being silently read as unrestricted.
    """
    eligible = tuple(gate2_record.get("focal_selection", {}).get("eligible")
                     or ())
    extra = sorted(set(severities) - set(eligible))
    if extra:
        raise ProtocolError(
            f"P3.1: {extra} are not in Gate 2's eligible set "
            f"{list(eligible)}. The probe measures the severities Gate 2 "
            "found eligible and never widens the grid")
    admissible = gate2_record.get("focal_admissible")
    if admissible is None:
        raise ProtocolError(
            "P3.1: Gate 2 recorded no `focal_admissible` set, so the probe "
            "cannot tell which eligible severities also passed §12.4 and §34 "
            "D17. A probe that fell back to `eligible` could re-select an "
            "operating point Gate 2 would have refused")
    outside_admissible = sorted(set(severities) - {int(q) for q
                                                   in admissible})
    if outside_admissible:
        raise ProtocolError(
            f"P3.1: {outside_admissible} are eligible under §12.3 but not "
            f"admissible: Gate 2 records {sorted(int(q) for q in admissible)} "
            "as passing §12.4's regime adequacy and §34 D17's construct floor "
            "at that severity. The probe may not move B to the others")
    outside = sorted(set(severities) - set(focal_severities(extended=True)))
    if outside:
        raise ProtocolError(
            f"P3.1: {outside} are outside §7.1's grid and §7.2's extension")


#: Probe cells whose value **Gate 2 has already measured**, on the same
#: model, the same constraint, the same topics and the same number of draws.
#: The unconstrained cell carries no constraint and the probe never evaluated
#: it; ``solo:B`` at a probed severity is a point on Gate 2's own solo B
#: curve --- the curve §12.3 selected m* from and the curve P3.4 re-selects
#: over. Re-drawing it here would produce a *second* estimate of the number
#: the operating point was chosen on, and the composed lift would then be a
#: difference between two independent samples instead of a difference from
#: the selection input.
SHARED_WITH_GATE2: tuple[str, ...] = ("unconstrained", "solo:B")


def shared_cell_verdict(*, gate2_topic_ids: Sequence[str],
                        probe_topic_ids: Sequence[str],
                        gate2_draws: int, probe_draws: int) -> dict[str, Any]:
    """May this stage read ``SHARED_WITH_GATE2`` off the Gate-2 record?

    **Only when the case is identical**, and identity is checked rather than
    assumed: the same topic identifiers, not merely the same split name or
    the same count, and the same number of draws. §34 D20 may put the probe
    on §6.2's reserved composed set, where Gate 2 measured nothing, and a
    harness may truncate either set; in both cases the two are different
    samples and the probe measures its own.

    Refusing to reuse is always safe here --- it costs rows and nothing else.
    Reusing when the cases differ would silently compare a composed cell on
    one topic set against a solo cell on another, which is the error §4.a of
    the readiness memo measures at up to 0.189.
    """
    gate2_ids, probe_ids = sorted(gate2_topic_ids), sorted(probe_topic_ids)
    same_topics = bool(gate2_ids) and gate2_ids == probe_ids
    same_draws = int(gate2_draws) == int(probe_draws)
    shared = same_topics and same_draws
    if shared:
        reason = (f"Gate 2 measured these cells on the same {len(probe_ids)} "
                  f"topics at {probe_draws} draws, so the probe reads its "
                  "values instead of drawing a second sample of them")
    elif not same_topics:
        reason = (f"Gate 2 measured {len(gate2_ids)} topics and this stage "
                  f"measures {len(probe_ids)}; the intersection is "
                  f"{len(set(gate2_ids) & set(probe_ids))} and only an "
                  "identical case may be reused")
    else:
        reason = (f"Gate 2 drew {gate2_draws} per cell and this stage draws "
                  f"{probe_draws}")
    return {"shared": shared, "cells": list(SHARED_WITH_GATE2) if shared
            else [], "same_topics": same_topics, "same_draws": same_draws,
            "n_topics": len(probe_ids), "reason": reason}


def severity_verdict(cells: Mapping[str, Mapping[str, float]], *,
                     band: tuple[float, float]) -> dict[str, Any]:
    """P3.2: a severity passes iff **every** probed cell, on **every**
    evaluated slot, lies inside the margin band.

    ``cells`` maps a probe cell id to slot -> compliance. The unconstrained
    cell carries no constraint and is recorded, not evaluated.
    """
    low, high = band
    failures = [{"cell": cell_id, "slot": slot, "compliance": value}
                for cell_id, entry in sorted(cells.items())
                if cell_id != "unconstrained"
                for slot, value in sorted(entry.items())
                if not (low <= value <= high)]
    return {"passes": not failures, "failures": failures,
            "margin_band": [low, high],
            "registered_band": list(C.COMPOSED_HEADROOM_BAND),
            "n_cells_evaluated": len([k for k in cells
                                      if k != "unconstrained"])}


def probe_disposition(*, m_star: int,
                      probed: Mapping[int, Mapping[str, Mapping[str, float]]],
                      gate2_solo_curve: Mapping[int, float],
                      band: tuple[float, float]) -> dict[str, Any]:
    """P3.3 to P3.6: m* stands, m* is re-selected once, or the study stops.

    ``probed`` maps each probed severity to its cell -> slot -> compliance
    table. ``gate2_solo_curve`` is **Gate 2's own** measured solo B curve; it
    is the selection input and the probe is not. The probe decides only which
    severities are admissible.

    Raising is the registered outcome of P3.6 and it is raised here, so the
    A8 AST regression --- every status in force has a reachable ``raise`` ---
    covers ``COMPOSED_HEADROOM_UNREACHABLE`` without modification. That test
    is the V5-E32 fix and it is why this status cannot repeat it.
    """
    from dci1v6.run.lifecycle import TerminalStatus

    verdicts = {m: severity_verdict(table, band=band)
                for m, table in sorted(probed.items())}
    if m_star not in verdicts:
        raise ProtocolError(
            f"P3.1: m* = {m_star} must be probed first and it was not")
    passing = sorted(m for m, v in verdicts.items() if v["passes"])
    base = {"m_star_in": m_star, "probed_severities": sorted(verdicts),
            "verdicts": {str(m): v for m, v in verdicts.items()},
            "passing_severities": passing,
            "margin_band": list(band),
            "registered_band": list(C.COMPOSED_HEADROOM_BAND),
            "band_is_unchanged": True,
            "selection_input": "GATE_2_FOCAL_CALIBRATION's solo B curve",
            "reselections_permitted": 1}
    if verdicts[m_star]["passes"]:
        return {**base, "reselected": False, "m_star_out": m_star,
                "reason": "P3.3: m* keeps every probed cell inside the "
                          "margin, so it stands"}
    if not passing:
        raise TerminalStatus(
            COMPOSED_HEADROOM_UNREACHABLE, gate=C.STAGE_GATE2_75,
            criterion=(
                f"P3.6: no severity Gate 2 found eligible keeps every probed "
                f"cell inside {list(band)}, the registered margin inside "
                f"§13.14's unchanged band "
                f"{list(C.COMPOSED_HEADROOM_BAND)}"),
            observed={"verdicts": base["verdicts"],
                      "probed_severities": base["probed_severities"]},
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    # P3.4: the registered focal rule, unchanged, over Gate 2's own curve,
    # restricted to the severities the probe found admissible.
    reselection = select_operating_point(
        {m: v for m, v in gate2_solo_curve.items() if m in passing},
        band=C.FOCAL_BAND, aim=C.FOCAL_AIM, prefer_smaller=True,
        grid=tuple(passing))
    if reselection["selected"] is None:
        raise TerminalStatus(
            COMPOSED_HEADROOM_UNREACHABLE, gate=C.STAGE_GATE2_75,
            criterion=("P3.4: the registered focal rule found no eligible "
                       "severity among those the probe admitted"),
            observed={"passing_severities": passing,
                      "reselection": reselection},
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    return {**base, "reselected": True,
            "m_star_out": reselection["selected"],
            "reselection": reselection,
            "reason": "P3.4: m* failed the margin; the registered focal rule "
                      "re-ran unchanged over Gate 2's solo curve restricted "
                      "to the severities the probe admitted"}


# ------------------------------------------------------------- the guards

#: The declared refusals §33 check 8 requires on this record. They live under
#: one key the name scan skips, for the same reason the Gate-4 block does: "no
#: field says substitute" and "the record states that no substitution path
#: exists" are different facts and the audit is here for the second.
PROBE_DECLARED_REFUSALS: dict[str, str] = {
    "no_reference_is_read_or_selected_here":
        "§13.11: the probe runs before GATE_3A. No reference exists, no "
        "selection record is read, and no probed cell is a B+R cell",
    "no_substitution_or_backup_promotion":
        "a probe failure re-selects m* once by the registered focal rule or "
        "terminates COMPOSED_HEADROOM_UNREACHABLE. Nothing is substituted, "
        "promoted or widened",
    "no_second_reselection_exists":
        "P3.5: the record is write-once and no later stage has a path back "
        "here; assert_transition_legal and assert_no_post_freeze_mutation "
        "enforce it",
    "band_not_relaxed":
        "§13.14's [0.05, 0.95] band is unchanged. delta is a margin inside "
        "it and Gate 4 still applies the registered band",
    "no_measurement_is_reused_across_different_cases":
        "the cells this stage reads off the Gate-2 record instead of drawing "
        "again are read only when the topic identifiers and the draw count "
        "are identical; `shared_cell_verdict` checks that and records the "
        "reason either way. Nothing is reused across topic sets",
    "the_order_of_operating_points_was_frozen_before_any_composed_row":
        "Gate 2 records `operating_point_search_order` --- the registered "
        "focal rule's own preference over `focal_admissible` --- and Gate "
        "2.5 restricts it to the severities that can meet §13.15's five-"
        "family minimum. Both are signed before this stage generates a row, "
        "so a candidate is never re-ranked by how a composed cell looked",
    "no_pool_is_chosen_by_a_composed_outcome":
        "§30: Gate 2 records a kappa(R|B) column and Gate 2.5 a §13.1 "
        "qualified pool for EVERY admissible severity, both signed before "
        "this stage generates a row. Moving m* therefore reads a pool that "
        "was already fixed; it does not build one from what the probe saw",
}

#: Stated on the payload because READINESS §3.2 says a limit discovered at
#: Gate 4 is a limit that should have been registered.
PROBE_SCOPE_LIMITS: tuple[str, ...] = (
    "the probe protects the B slot only. Gate 4 evaluates every slot of "
    "every registered cell type, and a companion-slot failure in a solo "
    "cell --- which is what terminated gemma-3n-e4b-it under v5 --- is "
    "invisible to a probe at m* against a stand-in, because the companion is "
    "selected two stages later",
    "a stand-in is not the eventual reference, so the composed lift it "
    "measures carries a stand-in-to-reference error that delta must absorb "
    "and that no v5 measurement bounds",
    "succeeding at the reference-supply change raises the number of Gate-4 "
    "cell x slot entries from 6 to as many as 95, so the two bottlenecks are "
    "coupled going forward in the direction that makes v6 harder",
)

#: Names that would betray a path from this stage into reference selection.
REFERENCE_TOKENS: tuple[str, ...] = (
    "reference", "slot_map_from_record", "selection_record", "shortlist",
    "qualified_pool", "backup", "gate3", "candidate")


#: Stage constants and loaders whose *records do not exist* when this stage
#: runs. A body naming one would be reading a stage that has not happened.
FORBIDDEN_SOURCE_READS: tuple[str, ...] = (
    "STAGE_GATE3A", "STAGE_GATE3B", "STAGE_GATE3C",
    "slot_map_from_record", "load_calibration_table")


def assert_probe_reads_no_reference(namespace: Mapping[str, Any] | None = None
                                    ) -> dict[str, Any]:
    """Static, twice: no name here reads a reference, and no source line does.

    The same shape as ``gates_run.assert_no_substitution_path`` --- the
    guarantee worth having is that no such function exists --- with a second
    pass over this module's own source, because a name scan cannot see a
    stage constant used inside a body. ``STAGE_GATE3A``, ``STAGE_GATE3B`` and
    ``STAGE_GATE3C`` may not appear here at all: those records do not exist
    when this stage runs, and code that reads one would be reading a stage
    that has not happened.
    """
    namespace = dict(namespace if namespace is not None else globals())
    found = sorted(
        name for name in namespace
        if any(token in name.lower() for token in REFERENCE_TOKENS)
        and not name.startswith(("assert_", "REFERENCE_TOKENS",
                                 "FORBIDDEN_SOURCE_READS")))
    if found:
        raise ProtocolError(
            f"{found} would give the composed probe a path into reference "
            "selection. The probe runs before any reference exists and the "
            "guarantee is that no such function is here")
    # The source pass skips this function, because naming what is forbidden
    # is how a guard is written and a scan that flagged its own vocabulary
    # would be unsatisfiable.
    module = inspect.getmodule(probe_disposition)
    bodies = "\n".join(
        inspect.getsource(obj) for name, obj in vars(module).items()
        if inspect.isfunction(obj) and obj.__module__ == module.__name__
        and obj is not assert_probe_reads_no_reference)
    forbidden_reads = sorted(name for name in FORBIDDEN_SOURCE_READS
                             if name in bodies)
    if forbidden_reads:
        raise ProtocolError(
            f"the composed-probe module names {forbidden_reads}. Those "
            "records do not exist when this stage runs")
    return {"checked": len(namespace), "forbidden_tokens":
            list(REFERENCE_TOKENS), "found": [],
            "source_reads_no_selection_stage": True,
            "declared_refusals": sorted(PROBE_DECLARED_REFUSALS)}
