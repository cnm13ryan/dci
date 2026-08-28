"""§18 stage 8: ``GATE_2_75_COMPOSED_PROBE`` --- the composed contrast,
measured before reference selection and **recorded** (v7).

**What it was, and what it is.** v6 added this stage so that the composed
compliance §13.14 audited at Gate 4 was measured two stages earlier, while
no reference existed, and it ended a replication when a determinate entry's
projected Gate-4 interval left an absolute band. Both v6 Qwen replications
ended here: B's compliance *rose* under A --- 0.747 to 0.891 on ``qwen3-4b``
and 0.779 to 0.924 on ``qwen3-4b-instruct-2507`` --- and the projected
interval crossed 0.95. A delivery **gain** on the treated arm is a
measurement of the quantity the study exists to estimate, not a reason to
stop estimating it. v7 withdraws the criterion (A1) and keeps the
measurement: this stage measures ``solo:A``, ``solo:B`` and both orders of
``pair:A+B`` on §6.2's 192 calibration topics at ``M_CAL``, forms the paired
per-topic contrasts the estimators form --- ``D(B<-A)`` and ``D(A<-B)`` in
each configuration, ``Lambda``, and the order contrasts ``Ord_A`` and
``Ord_B`` --- bootstraps topics, applies ``analysis/boundary.py``'s three
readings, projects the confirmatory half-width, and **records all of it**.
It reaches one outcome, ``PASS``; it has no terminal status and no raise
path to one, and a test asserts the converse of the A8 regression for the
status it used to raise.

**What the record is for.** It is the first look at ``D(B<-A)`` on a
replication, on 192 topics rather than Gate 4's 24, taken before any
reference is chosen --- so whether the A arm sits where ``Delta_R``'s
positive direction is compressed (v7 §13.14) is on a signed record before
Gate 3B runs and cannot be attributed to the selection. It is a projection,
labelled as one, and every quantity it carries is recomputed on the
confirmatory blocks by the same rule.

**Scope: every slot and order class Gate 4 measures.** Unchanged from v6:
``gate4_exposure_classes`` partitions §8.1's 95 cell x slot entries by (arm,
the roles of the slots in prompt order), one probe cell carries each class,
and ``assert_probe_covers_gate4_classes`` refuses a shape that leaves one
uncovered. The companion role is carried by frozen ``probe_only`` stand-ins
(§34 D24), placed per A5 as amended by A17. A stand-in-dependent entry is
classified for proximity to the band and recorded under
``standin_proximity``; it decides nothing, as before.

**What interaction-blindness means here**, narrowly and checkably: this
stage is blind to any *reference*. Four independent guarantees, each
enforced somewhere a reader can point at:

1. **Temporal.** The stage runs between Gate 2.5 and Gate 3A. No reference
   exists and ``assert_predecessor_passed`` refuses a stage whose
   predecessor has not recorded PASS.
2. **Structural.** A stand-in is a ``probe_only`` family and
   ``verifiers.constraints.assert_selectable`` refuses one everywhere a
   candidate is carried, qualified, calibrated or bound.
3. **Informational.** §13.11's schema refusal rejects a composed outcome
   reaching reference selection, and §33 check 8's name scan reads **this**
   record on the same terms as the Gate-4 record.
4. **Directional.** The one value this stage writes that a later stage
   reads is m*, and m* is B's own severity, frozen at Gate 2 (A13).
   ``assert_probe_reads_no_reference`` refuses, by name and by source, any
   function here that would read a selection record.

**m\\* is frozen at Gate 2 and this stage cannot move it (A13).** It measures
at m* and at no other severity; ``probe_disposition`` refuses a table
carrying any other; ``m_star_out == m_star_in`` on every path there is,
and there is now only one.

**Two things this module does not decide, and refuses to.** The topic split
(§34 D20) and which stand-ins exist (§34 D24) are researcher decisions;
every accessor goes through ``protocol/decisions``. v6's §34 D23 and D26 ---
the residual allowance a projected-interval verdict carried --- have no
consumer in v7 and are withdrawn with the verdict.
"""
from __future__ import annotations

import inspect
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.analysis import boundary
from dci1v7.analysis.bootstrap import bootstrap_family
from dci1v7.design import cells as design_cells
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions
from dci1v7.stages.regime import select_operating_point
from dci1v7.verifiers.constraints import (
    PROBE_ONLY_FAMILY_IDS, focal_severities,
)

__all__ = ["PROBE_SLOTS", "probe_slots",
           "probe_cell_types", "probe_split", "standins",
           "contrast_record", "probe_disposition", "assert_m_star_unmoved",
           "assert_probe_reads_no_reference", "PROBE_DECLARED_REFUSALS",
           "REFERENCE_TOKENS", "FORBIDDEN_SOURCE_READS",
           "PROBE_SCOPE_LIMITS", "assert_probe_severities_are_admissible",
           "SHARED_WITH_GATE2", "shared_cell_verdict",
           "slot_role", "gate4_exposure_classes", "probe_class_coverage",
           "assert_probe_covers_gate4_classes", "DETERMINATE_SLOTS",
           "is_determinate", "cell_slots_of",
           "DESIGNATED_COMPANION_SLOTS", "standin_operating_points",
           "placed_standins", "unplaceable_standins", "unmeasured_probe_cells",
           "PROBE_ONLY_KINDS", "DETERMINATE_CONTRASTS", "PROBE_OUTCOME",
           "PROBE_LADDER_DRAWS", "N_DETERMINATE_ENTRIES",
           "PROBE_FAMILY_SIZES"]

#: The only outcome this stage can record. There is no terminal status.
PROBE_OUTCOME = "PASS"

#: The probe's own slot names. They are deliberately **not** in
#: ``C.REGISTERED_SLOT_ORDER``: a stand-in has no slot in the confirmatory
#: design, so there is no name a probe cell and a design cell could share.
PROBE_SLOTS: tuple[str, ...] = ("P1", "P2", "P3")

#: The slots whose instrument is a real registered one when this stage runs:
#: A at n* and B at m*, both fixed at Gate 2.
DETERMINATE_SLOTS: tuple[str, ...] = C.BASE_SLOTS

#: §12.2's draw count, reused for the stand-in solo ladder. The ladder decides
#: only *which severity* each stand-in is probed at.
PROBE_LADDER_DRAWS = C.LADDER_SCREEN_DRAWS

#: Which stand-ins carry the classes that pair a companion with the target and
#: with another companion. **A stated cap, not an oversight.** Running all
#: three stand-ins through every class would add eight cells per severity to
#: measure the same class three times with three instruments none of which is
#: the reference. The classes are covered; the within-class instrument spread
#: is not, and ``PROBE_SCOPE_LIMITS`` says so.
DESIGNATED_COMPANION_SLOTS: tuple[str, ...] = ("P1", "P2")

#: The six determinate cell x slot entries: A and B each in their solo cell
#: and in both orders of ``pair:A+B``. Every constituent is a real registered
#: instrument that enters the estimand; the shape assertion counts them.
N_DETERMINATE_ENTRIES = 6

#: The paired contrasts this stage forms from the determinate entries, per
#: configuration and across them, as (cell id, slot, signed weight). They are
#: the algebraic forms §11.2 and §11.7 register, on the cells this stage has:
#: B is first in ``pair:B+A`` and second in ``pair:A+B``, and a solo cell
#: serves both configurations. ``tests_v7`` checks each against the
#: estimators on a synthetic observation table.
DETERMINATE_CONTRASTS: dict[str, dict[str, tuple[tuple[str, str, float],
                                                ...]]] = {
    C.OUTCOME_FIRST: {
        "D(B<-A)": (("solo:B", "B", +1.0), ("pair:B+A", "B", -1.0)),
        "D(A<-B)": (("solo:A", "A", +1.0), ("pair:A+B", "A", -1.0)),
        "Lambda": (("solo:B", "B", +1.0), ("pair:B+A", "B", -1.0),
                   ("solo:A", "A", -1.0), ("pair:A+B", "A", +1.0)),
    },
    C.OUTCOME_SECOND: {
        "D(B<-A)": (("solo:B", "B", +1.0), ("pair:A+B", "B", -1.0)),
        "D(A<-B)": (("solo:A", "A", +1.0), ("pair:B+A", "A", -1.0)),
        "Lambda": (("solo:B", "B", +1.0), ("pair:A+B", "B", -1.0),
                   ("solo:A", "A", -1.0), ("pair:B+A", "A", +1.0)),
    },
    "cross": {
        "Ord_A": (("pair:B+A", "A", +1.0), ("pair:A+B", "A", -1.0)),
        "Ord_B": (("pair:A+B", "B", +1.0), ("pair:B+A", "B", -1.0)),
        "Ord_Lambda": (("pair:A+B", "B", +1.0), ("pair:B+A", "B", -1.0),
                       ("pair:B+A", "A", -1.0), ("pair:A+B", "A", +1.0)),
    },
}
#: §16.2 quotes each member's projected half-width at its family's planning
#: constant: F1 for ``D`` and ``Lambda``, F11 for the order contrasts.
PROBE_FAMILY_SIZES: dict[str, int] = {
    "D(B<-A)": len(C.FAMILY_MEMBERS["F1"]),
    "D(A<-B)": len(C.FAMILY_MEMBERS["F1"]),
    "Lambda": len(C.FAMILY_MEMBERS["F1"]),
    "Ord_A": len(C.FAMILY_MEMBERS["F11"]),
    "Ord_B": len(C.FAMILY_MEMBERS["F11"]),
    "Ord_Lambda": len(C.FAMILY_MEMBERS["F11"]),
}


def probe_slots(n: int) -> tuple[str, ...]:
    """The first ``n`` probe slots. Refuses more than the registered three."""
    if not 1 <= n <= len(PROBE_SLOTS):
        raise ProtocolError(
            f"the probe registers {len(PROBE_SLOTS)} stand-in slots "
            f"{PROBE_SLOTS} and {n} were asked for")
    return PROBE_SLOTS[:n]


# ------------------------------------------------- what Gate 4 will audit

def slot_role(slot: str) -> str:
    """``target``, ``focal`` or ``companion``.

    The partition is by **what is known when this stage runs**, which is the
    only distinction that changes what a probed cell can be evidence for. A
    and B are fixed at Gate 2; every other slot is filled two stages later.
    """
    if slot == "A":
        return "target"
    if slot == "B":
        return "focal"
    return "companion"


def gate4_exposure_classes(arms: Sequence[str] | None = None
                           ) -> dict[tuple[str, tuple[str, ...]], list[str]]:
    """Every §13.14 cell x slot entry, grouped by (arm, slot roles in order).

    Derived from ``design.cells.cell_types`` rather than listed here, so that
    admitting an arm, adding a slot or changing §8.4's order rule changes what
    the probe is required to cover **without an edit to this module**. A
    hand-written list is how the first version of this stage came to protect
    one slot while believing it protected the design.
    """
    admitted = tuple(arms) if arms is not None else C.ARMS
    out: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for cell in design_cells.cell_types(admitted):
        key = (cell.arm, tuple(slot_role(s) for s in cell.slots))
        out.setdefault(key, []).append(cell.cell_id)
    return out


def probe_cell_types(standin_slots: Sequence[str]
                     ) -> list[tuple[str, str, tuple[str, ...]]]:
    """``(cell_id, arm, slots)`` for one probed severity, in a stable order.

    One cell per Gate-4 exposure class, with A and B where the class names
    them and a stand-in where it names a companion. The stand-in *solo* cells
    are not optional: they carry the ``solo:companion`` class, which is where
    ``gemma-3n-e4b-it`` failed under v5.
    """
    slots = tuple(standin_slots)
    if len(set(slots)) != len(slots):
        raise ProtocolError(f"duplicate probe slot in {slots}")
    unknown = [s for s in slots if s not in PROBE_SLOTS]
    if unknown:
        raise ProtocolError(f"{unknown} are not registered probe slots")
    designated = [s for s in DESIGNATED_COMPANION_SLOTS if s in slots]
    types: list[tuple[str, str, tuple[str, ...]]] = [
        ("unconstrained", "unconstrained", ()),
        ("solo:A", "solo", ("A",)),
        ("solo:B", "solo", ("B",))]
    types += [(f"solo:{s}", "solo", (s,)) for s in slots]
    types += [("pair:A+B", "composed", ("A", "B")),
              ("pair:B+A", "composed", ("B", "A"))]
    for s in slots:
        types.append((f"pair:B+{s}", "composed", ("B", s)))
        types.append((f"pair:{s}+B", "composed", (s, "B")))
    if designated:
        first = designated[0]
        types.append((f"pair:A+{first}", "composed", ("A", first)))
        types.append((f"pair:{first}+A", "composed", (first, "A")))
    if len(designated) >= 2:
        one, two = designated[0], designated[1]
        types.append((f"pair:{one}+{two}", "composed", (one, two)))
        types.append((f"pair:{two}+{one}", "composed", (two, one)))
    return types


def probe_class_coverage(standin_slots: Sequence[str],
                         arms: Sequence[str] | None = None
                         ) -> dict[str, dict[str, Any]]:
    """Which probe cell carries which Gate-4 exposure class."""
    probe = probe_cell_types(standin_slots)
    by_class: dict[str, dict[str, Any]] = {}
    for key, gate4_cells in gate4_exposure_classes(arms).items():
        arm, roles = key
        name = f"{arm}:{'+'.join(roles)}" if roles else arm
        covering = [cell_id for cell_id, cell_arm, slots in probe
                    if cell_arm == arm
                    and tuple(slot_role(s) for s in slots) == roles]
        by_class[name] = {
            "arm": arm, "roles": list(roles),
            "gate4_cells": len(gate4_cells),
            "gate4_entries": len(gate4_cells) * max(len(roles), 0),
            "probe_cells": covering,
            "covered": bool(covering),
            "determinate": all(r in ("target", "focal") for r in roles)
                           and bool(roles),
        }
    return by_class


def assert_probe_covers_gate4_classes(standin_slots: Sequence[str],
                                      arms: Sequence[str] | None = None
                                      ) -> dict[str, Any]:
    """Refuse a probe shape that leaves a §13.14 exposure class unmeasured."""
    coverage = probe_class_coverage(standin_slots, arms)
    missing = sorted(name for name, entry in coverage.items()
                     if not entry["covered"])
    if missing:
        raise ProtocolError(
            f"the probe shape leaves {missing} unmeasured. Gate 4 audits "
            "every slot of every registered cell type, and a class no probe "
            "cell carries is a class whose failure this stage cannot see")
    return {
        "classes": len(coverage),
        "gate4_entries": sum(e["gate4_entries"] for e in coverage.values()),
        "determinate_classes": sorted(n for n, e in coverage.items()
                                      if e["determinate"]),
        "coverage": coverage,
    }


def cell_slots_of(cell_id: str) -> tuple[str, ...]:
    """The slots a probe cell states, read from its **id**.

    Not from which measurements happen to be present. Determinacy decides
    which of the two verdict rules an entry is judged by, so reading it off
    the measured keys would let a cell with one missing measurement change
    the rule it is judged under --- a stand-in pair whose stand-in slot went
    unmeasured would look like a determinate solo cell and be given a margin
    it is not entitled to.
    """
    if cell_id == "unconstrained":
        return ()
    if cell_id.startswith("solo:"):
        return (cell_id[len("solo:"):],)
    if cell_id.startswith("pair:"):
        first, _, second = cell_id[len("pair:"):].partition("+")
        if not first or not second:
            raise ProtocolError(f"{cell_id!r} is not a probe pair cell")
        return (first, second)
    raise ProtocolError(f"{cell_id!r} is not a probe cell id")


def is_determinate(cell_slots: Sequence[str]) -> bool:
    """Whether every constituent of the cell is a real registered instrument.

    **Every** constituent, not the slot being scored. B's compliance inside
    ``pair:B+P1`` is B's compliance *when composed with that stand-in*, and
    the reference that replaces the stand-in is a different companion; so the
    B entry of a stand-in pair is no more a prediction of Gate 4 than the
    stand-in's own entry is.
    """
    return bool(cell_slots) and all(s in DETERMINATE_SLOTS for s in cell_slots)


# --------------------------------------------------- the open decisions

def probe_split() -> str:
    """§34 D20 (READINESS R2): which topic split the probe runs on.

    Every branch exists in the source and none is reachable while the
    decision is open, which is the whole point of ``choice``.

    * ``reserved_composed`` --- the §6.2 composed set, which §6.2 spends once.
    * ``calibration_with_measured_transfer`` --- the calibration split, with
      every entry measured on **both** 96-topic sub-splits so the realised
      movement between them is recorded beside the contrast. Calibration-A
      comes from §6.2's seeded cut and is exchangeable with the composed and
      confirmatory sets; §34 D3's Calibration-B is newly authored and is
      not, so the sub-split contrast measures the one component of the
      calibration-to-confirmatory difference that is **not** sampling. It
      costs no extra rows, because §13.7 already generates both.
    """
    return decisions.choice(
        "D20",
        {"reserved_composed": "composed",
         "calibration_with_measured_transfer": "calibration_both_subsplits"},
        where="stages.composed_probe.probe_split")


def standins() -> tuple[str, ...]:
    """§34 D24 (READINESS R6): the frozen structural stand-ins.

    Both branches exist. ``probe_only_in_library`` selects the three families
    ``verifiers/constraints`` registers with ``probe_only=True``; the
    alternative registers a separate vocabulary with its own hash, which this
    library does not carry.

    The **severity** each stand-in is probed at is not fixed here: it is read
    per replication from that stand-in's own solo ladder, at the severity
    nearest Gate 2's measured iota_A. See ``standin_operating_points``.
    """
    registered: tuple[str, ...] = decisions.choice(
        "D24",
        {"probe_only_in_library": PROBE_ONLY_FAMILY_IDS,
         "separate_vocabulary": ()},
        where="stages.composed_probe.standins")
    if not registered:
        raise ProtocolError(
            "§34 D24 is closed but no probe-only stand-in is registered. The "
            "probe composes B and A with stand-ins and cannot run without "
            "them; authoring them is a change to §7.10's library and to the "
            "counts `assert_library_sizes` asserts")
    return tuple(registered)


def PROBE_ONLY_KINDS() -> tuple[str, ...]:
    """The registered probe-only family ids.

    A function rather than a re-export, so that
    ``assert_probe_reads_no_reference``'s name scan sees a name with no
    selection token in it and a caller cannot mistake the tuple for a pool
    something may be selected from.
    """
    return PROBE_ONLY_FAMILY_IDS


def standin_operating_points(ladders: Mapping[str, Mapping[int, float]], *,
                             iota_a: float) -> dict[str, dict[str, Any]]:
    """Each stand-in's probe severity, by the rule a reference is chosen by.

    **Not FOCAL_AIM.** A stand-in stands in for a *reference*, and §13.8
    matches a reference's iota(R) to iota_A, so the registered target for a
    companion's compliance is iota_A --- a quantity Gate 2 has already
    measured, that no composed outcome touches and that does not depend on
    m*. Placing a stand-in at B's aim instead would put it where nothing in
    the design ever puts a companion.

    Admissibility is §13.4's own band, so a stand-in is never probed at a
    severity a reference could not be admitted at. ``select_operating_point``
    runs unchanged, with ``aim = iota_a``.
    """
    out: dict[str, dict[str, Any]] = {}
    for kind, curve in sorted(ladders.items()):
        measured = {int(q): float(v) for q, v in curve.items()}
        selection = select_operating_point(
            measured, band=C.HEADROOM_BAND, aim=float(iota_a),
            prefer_smaller=True, grid=tuple(sorted(measured)))
        common = {"aim": float(iota_a),
                  "band": list(C.HEADROOM_BAND),
                  "rule": "§13.8's target for a companion is iota_A, and "
                          "§13.4's band is what admits one",
                  "curve": {str(q): float(v)
                            for q, v in sorted(measured.items())},
                  "selection": selection}
        if selection["selected"] is None:
            # A17. Recorded, not raised. This instrument cannot stand in for
            # a reference on this replication --- no registered severity of
            # its ladder puts its solo compliance inside the band a reference
            # is admitted by --- so every diagnostic cell that needs it goes
            # unmeasured and the six determinate entries decide the verdict,
            # as they already did. Raising here let a `probe_only` instrument
            # end the stage, which is the one power
            # `no_standin_entry_ends_a_replication` exists to deny it.
            out[kind] = {
                **common,
                "severity": None,
                "placed": False,
                "status": C.STANDIN_UNPLACEABLE,
                "reason":
                    f"no registered severity of {kind} has solo compliance "
                    f"inside §13.4's {list(C.HEADROOM_BAND)} on this "
                    f"replication, so it cannot stand in for a reference "
                    f"here. Measured: "
                    f"{dict(sorted((q, round(v, 4)) for q, v in measured.items()))}",
                "best_severity": (max(measured, key=lambda q: measured[q])
                                  if measured else None),
                "best_compliance": (max(measured.values())
                                    if measured else None),
                "gates_nothing":
                    "PS1-PS3 are probe_only and the Gate-2.75 verdict is "
                    "determinate-only, so this costs diagnostic breadth and "
                    "decides nothing about this replication",
            }
            continue
        out[kind] = {**common, "severity": int(selection["selected"]),
                     "placed": True, "status": "PLACED"}
    return out


def placed_standins(operating: Mapping[str, Mapping[str, Any]]
                    ) -> tuple[str, ...]:
    """The stand-ins that have an admissible severity, in a stable order."""
    return tuple(k for k in sorted(operating) if operating[k].get("placed"))


def unplaceable_standins(operating: Mapping[str, Mapping[str, Any]]
                         ) -> tuple[str, ...]:
    """The stand-ins with none (A17)."""
    return tuple(k for k in sorted(operating)
                 if not operating[k].get("placed"))


def unmeasured_probe_cells(shape: Sequence[tuple[str, str, tuple[str, ...]]],
                           unplaceable_slots: Sequence[str]
                           ) -> dict[str, dict[str, Any]]:
    """Which probe cells lose their companion, and to which stand-in (A17).

    Returned as a mapping rather than a filtered shape so the record carries
    what the design *would* have measured beside what it did: a cell that is
    simply absent reads as a cell that was never registered.
    """
    missing = set(unplaceable_slots)
    out: dict[str, dict[str, Any]] = {}
    for cell_id, arm, slots in shape:
        needed = sorted(set(slots) & missing)
        if not needed:
            continue
        out[cell_id] = {
            "cell_id": cell_id, "arm": arm, "slots": list(slots),
            "requires_unplaceable_slots": needed,
            "status": C.NOT_MEASURED_STANDIN_UNPLACEABLE,
            "determinate": is_determinate(slots),
            "enters_the_verdict": False,
            "why": "the cell needs a companion this replication has no "
                   "admissible severity for; it is not measured, and being "
                   "stand-in-dependent it entered no verdict even when it "
                   "was",
        }
    return out


# ------------------------------------------------------------ the P3 rule

def assert_probe_severities_are_admissible(
        severities: Sequence[int], gate2_record: Mapping[str, Any]) -> None:
    """P3.1: the probed set is the set Gate 2 recorded as **admissible**.

    Not the registered grid and not a set this stage chose. ``eligible`` is
    §12.3's band test on the solo curve alone; ``focal_admissible`` is that
    set intersected with §12.4's regime adequacy and §34 D17's construct
    floor, each evaluated *at that severity*. The distinction is the whole
    point: Gate 2 applies §12.4 and D17 at m* and terminates the replication
    when either fails, so probing a merely *eligible* severity would measure
    B at an operating point Gate 2 would itself have refused. Since
    2026-08-26 the probed set is ``[m*]``, so this is a cross-gate agreement
    check rather than a restriction on a search --- and it is kept for
    exactly that: a record whose m* is not in its own ``focal_admissible`` is
    a lifecycle fault this catches before a row is drawn.

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
            "cannot tell whether m* also passed §12.4 and §34 D17 at that "
            "severity. A probe that fell back to `eligible` would measure at "
            "an operating point Gate 2 would have refused")
    outside_admissible = sorted(set(severities) - {int(q) for q
                                                   in admissible})
    if outside_admissible:
        raise ProtocolError(
            f"P3.1: {outside_admissible} are eligible under §12.3 but not "
            f"admissible: Gate 2 records {sorted(int(q) for q in admissible)} "
            "as passing §12.4's regime adequacy and §34 D17's construct "
            "floor at that severity. The probe measures only what Gate 2 "
            "admitted")
    outside = sorted(set(severities) - set(focal_severities(extended=True)))
    if outside:
        raise ProtocolError(
            f"P3.1: {outside} are outside §7.1's grid and §7.2's extension")


#: Probe cells whose value **Gate 2 has already measured**, on the same
#: model, the same constraint, the same topics and the same number of draws.
#: The unconstrained cell carries no constraint and the probe never evaluated
#: it; ``solo:B`` at the frozen m* is a point on Gate 2's own solo B curve
#: --- the curve §12.3 selected m* from --- and ``solo:A`` at n* is Gate 2's
#: iota_A. Re-drawing either would
#: produce a *second* estimate of a number the design was already fixed on,
#: and every lift measured against it would become a difference between two
#: samples instead of a difference from the selection input.
SHARED_WITH_GATE2: tuple[str, ...] = ("unconstrained", "solo:A", "solo:B")


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
    one topic set against a solo cell on another.
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


# ------------------------------------------------ the record, and the P3 rule

def _slot_role_of_cell(cell_slots: Sequence[str], slot: str) -> str:
    return "solo" if len(cell_slots) == 1 else "composed"


def _companion_of(cell_slots: Sequence[str], slot: str) -> str | None:
    others = [s for s in cell_slots if s != slot]
    return others[0] if others else None


def _configuration_of(cell_slots: Sequence[str], slot: str) -> str | None:
    if len(cell_slots) != 2:
        return None
    return C.OUTCOME_FIRST if cell_slots[0] == slot else C.OUTCOME_SECOND


def _entry_classification(cell_id: str, slot: str,
                          measurement: Mapping[str, Any]) -> dict[str, Any]:
    """One cell x slot entry: its level and its proximity to a boundary.

    ``exact_boundary`` needs the per-topic vector; an entry that carries only
    a mean is classified for proximity and says the exact reading was not
    available rather than reporting it as absent.
    """
    cell_slots = cell_slots_of(cell_id)
    per_topic = measurement.get("per_topic")
    base = {"cell": cell_id, "slot": slot,
            "determinate": is_determinate(cell_slots),
            "role": _slot_role_of_cell(cell_slots, slot),
            "companion": _companion_of(cell_slots, slot),
            "configuration": _configuration_of(cell_slots, slot),
            "compliance": float(measurement["compliance"]),
            "s2_topic": float(measurement.get("s2_topic", 0.0)),
            "n_topics": int(measurement["n_topics"])}
    if per_topic:
        cls = boundary.classify_cell(list(per_topic.values()))
        return {**base, **{k: v for k, v in cls.items() if k != "level"},
                "exact_reading_available": True}
    level = float(measurement["compliance"])
    low, high = C.COMPOSED_PROXIMITY_BAND
    return {**base, "exact_boundary": None,
            "near_boundary": ("floor" if level < low else
                              "ceiling" if level > high else None),
            "proximity_band": [low, high],
            "exact_reading_available": False}


def _aligned_vectors(cells: Mapping[str, Mapping[str, Mapping[str, Any]]],
                     parts: Sequence[tuple[str, str, float]]
                     ) -> tuple[list[str], list[list[float]]]:
    """The per-topic vectors of a contrast's constituents, on ONE topic set.

    A contrast is paired inside the topic, so every constituent has to carry
    the same topics; a cell measured on a different set is refused rather
    than aligned by position.
    """
    topic_sets: list[set[str]] = []
    for cell_id, slot, _w in parts:
        per_topic = (cells.get(cell_id) or {}).get(slot, {}).get("per_topic")
        if not per_topic:
            raise ProtocolError(
                f"{cell_id}[{slot}] carries no per-topic vector, and a "
                "paired contrast cannot be formed from a mean alone")
        topic_sets.append(set(per_topic))
    common = topic_sets[0]
    for other in topic_sets[1:]:
        if other != common:
            raise ProtocolError(
                "the determinate cells were measured on different topic "
                f"sets ({len(common)} vs {len(other)} topics); a paired "
                "contrast reads one topic set")
    topics = sorted(common)
    vectors = [[float(cells[cell_id][slot]["per_topic"][t]) for t in topics]
               for cell_id, slot, _w in parts]
    return topics, vectors


def contrast_record(cells: Mapping[str, Mapping[str, Mapping[str, Any]]], *,
                    seed: int,
                    resamples: int = C.BOOTSTRAP_RESAMPLES) -> dict[str, Any]:
    """The composed contrasts at the frozen m*, and their boundary readings.

    ``cells`` maps a probe cell id to slot -> measurement, where a
    measurement carries ``compliance``, ``s2_topic``, ``n_topics`` and, for
    every determinate cell, ``per_topic`` (topic id -> that topic's draw
    mean). The unconstrained cell is recorded, not evaluated.

    **It decides nothing.** Every entry is classified; the six determinate
    entries are combined into the registered contrasts, bootstrapped over
    topics with one index draw per replicate (§17.1's construction, on this
    stage's topics), read through ``analysis.boundary``, and projected to the
    confirmatory half-width. The result is a record. Nothing here returns a
    verdict, because nothing here has one to return.
    """
    verdicts: list[dict[str, Any]] = []
    for cell_id, entry in sorted(cells.items()):
        if cell_id == "unconstrained":
            continue
        cell_slots = cell_slots_of(cell_id)
        measured = tuple(sorted(entry))
        if measured != tuple(sorted(cell_slots)):
            raise ProtocolError(
                f"{cell_id} states {sorted(cell_slots)} and carries a "
                f"measurement for {list(measured)}. A missing entry would "
                "make the cell read as a different cell, so it is refused "
                "rather than skipped")
        for slot in cell_slots:
            verdicts.append(_entry_classification(cell_id, slot, entry[slot]))
    determinate = [v for v in verdicts if v["determinate"]]
    standin = [v for v in verdicts if not v["determinate"]]
    if len(determinate) != N_DETERMINATE_ENTRIES:
        raise ProtocolError(
            f"the probed operating point carries {len(determinate)} "
            f"determinate entries and the registered set is "
            f"{N_DETERMINATE_ENTRIES} (solo:A, solo:B and both orders of "
            "pair:A+B). A missing one would narrow the record silently")

    contrasts: dict[str, dict[str, Any]] = {}
    for group, members in DETERMINATE_CONTRASTS.items():
        configuration = None if group == "cross" else group
        vectors_by_member: dict[str, list[float]] = {}
        constituents_by_member: dict[str, list[tuple[boundary.Constituent,
                                                     list[float]]]] = {}
        n_topics = None
        for member, parts in members.items():
            topics, vectors = _aligned_vectors(cells, parts)
            n_topics = len(topics)
            per_topic = [sum(w * vec[i] for (_c, _s, w), vec
                             in zip(parts, vectors))
                         for i in range(n_topics)]
            vectors_by_member[member] = per_topic
            constituents_by_member[member] = [
                (boundary.Constituent(
                    _slot_role_of_cell(cell_slots_of(cell_id), slot),
                    slot, _companion_of(cell_slots_of(cell_id), slot), w,
                    _configuration_of(cell_slots_of(cell_id), slot)),
                 vec)
                for (cell_id, slot, w), vec in zip(parts, vectors)]
        family = bootstrap_family(
            vectors_by_member, seed=seed, configuration=group,
            family=f"PROBE:{group}", n_blocks=int(n_topics),
            resamples=resamples)
        for member, result in family.members.items():
            reading = boundary.contrast_boundary(
                member, constituents_by_member[member],
                configuration=configuration)
            lower, upper = boundary.apply_allowance(
                result.marginal_lower, result.marginal_upper, reading)
            contrasts[f"{member}|{group}"] = {
                "member": member, "group": group,
                "configuration": configuration,
                "estimate": result.estimate,
                "standard_error": result.standard_error,
                "marginal_lower": result.marginal_lower,
                "marginal_upper": result.marginal_upper,
                "simultaneous_lower": result.simultaneous_lower,
                "simultaneous_upper": result.simultaneous_upper,
                "decision_lower_with_allowance": lower,
                "decision_upper_with_allowance": upper,
                "n_topics": int(n_topics),
                "resamples": resamples,
                "degenerate": result.degenerate,
                "boundary": reading,
                "statuses": list(reading["statuses"]),
                "projected_confirmatory":
                    boundary.projected_confirmatory_halfwidth(
                        vectors_by_member[member],
                        constituents_by_member[member],
                        m_measured=C.M_CAL,
                        family_size=PROBE_FAMILY_SIZES[member]),
                "precision_precondition": C.PRECISION_PRECONDITIONS.get(
                    "D" if member.startswith("D(") else
                    ("Ord_A" if member.startswith("Ord_")
                     and member not in C.PRECISION_PRECONDITIONS
                     else member)),
                "label": "PROJECTION_NOT_REGISTERED_FOR_INFERENCE",
            }
    statuses = sorted({s for c in contrasts.values() for s in c["statuses"]})
    return {
        "outcome": PROBE_OUTCOME,
        "terminates": False,
        "decides": "nothing",
        "entries": verdicts,
        "n_entries_evaluated": len(verdicts),
        "n_determinate_entries": len(determinate),
        "n_standin_dependent_entries": len(standin),
        "standin_proximity": [v for v in standin if v["near_boundary"]],
        "standin_proximity_gates_nothing": True,
        "contrasts": contrasts,
        "contrast_statuses": statuses,
        "any_structural_zero": any(c["boundary"]["structural_zero"]
                                   for c in contrasts.values()),
        "proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
        "proximity_band_is_descriptive": True,
        "boundary_rule": boundary.__doc__.split("\n\n")[0].strip(),
        "n_composed_audited_at": C.N_COMPOSED,
        "what_this_is":
            "the composed contrasts at the frozen m*, on the calibration "
            "topics, before any reference exists: a projection of what the "
            "confirmatory blocks will estimate, labelled as one and read by "
            "no rule. The same readings are recomputed at Gate 4 on the "
            "composed set and at UNMASKED_ANALYSIS on the 384 blocks",
    }


def probe_disposition(*, m_star: int,
                      probed: Mapping[int, Mapping[str, Mapping[str, Any]]],
                      seed: int,
                      resamples: int = C.BOOTSTRAP_RESAMPLES
                      ) -> dict[str, Any]:
    """The frozen m\\* is measured, recorded, and the replication continues.

    ``probed`` maps the probed severity to its cell -> slot -> measurement
    table and **must carry m\\* and nothing else** (A13): a table carrying
    another severity is a search for an operating point and is refused
    rather than truncated. That refusal is the only way out of this function
    other than the record.

    There is no terminal branch. v6's ``COMPOSED_HEADROOM_UNREACHABLE`` was
    raised here and nowhere else; v7 withdraws it (A1) and
    ``tests_v7`` asserts that no module in the package can raise it.
    """
    probed_severities = sorted(int(m) for m in probed)
    if probed_severities != [int(m_star)]:
        raise ProtocolError(
            f"P3.1: this stage measures the composed contrast at the frozen "
            f"m* = {m_star} and at no other severity; the table carries "
            f"{probed_severities}. m* is §12.3's choice at "
            f"{C.STAGE_GATE2} and Gate 2.75 may not move it, so a probe of "
            "more than one severity is a search for an operating point and "
            "is refused rather than truncated")
    record = contrast_record(probed[probed_severities[0]], seed=seed,
                             resamples=resamples)
    return {"m_star_in": int(m_star),
            "m_star_out": int(m_star),
            "reselected": False,
            "probed_severities": [int(m_star)],
            "verdicts": {str(m_star): record},
            "verdict": record,
            "outcome": PROBE_OUTCOME,
            "terminal_status": None,
            "proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
            "proximity_band_is_descriptive": True,
            "operating_point_source":
                f"{C.STAGE_GATE2}'s registered focal rule on the solo B "
                "curve. This stage reads m* and never chooses it",
            "m_star_is_frozen": True,
            "m_star_is_frozen_at": C.STAGE_GATE2,
            "reselection_rule": "none",
            "reselection_rule_is":
                "there is none. m* is frozen at GATE_2_FOCAL_CALIBRATION and "
                "this stage returns m_star_out == m_star_in on its one path. "
                "No entry, determinate or not, terminates a replication, "
                "selects a severity or selects a reference; the record is "
                "the whole output",
            "standin_proximity": record["standin_proximity"],
            "reselections_permitted": 0,
            "reason": "v7 §13.14: the composed contrast at the frozen m* is "
                      "recorded with its boundary readings and its projected "
                      "precision; a composed rate at a boundary terminates "
                      "nothing, and what it does to the contrast is on the "
                      "record"}


def assert_m_star_unmoved(disposition: Mapping[str, Any], *,
                          gate2_m_star: int) -> int:
    """The invariant, executed: this stage returns the m\\* it was given.

    The **producing** half. ``gates_run.gate2_75_payload`` calls it before the
    record is written; the consuming half is
    ``gates_run.assert_probe_m_star_agrees``, which ``effective_m_star`` runs
    on every downstream read of the written record. So "Gate 2.75 cannot move
    the operating point" is checked where the value is made and again wherever
    it is used, rather than asserted in prose.
    """
    for key in ("m_star_in", "m_star_out"):
        if int(disposition[key]) != int(gate2_m_star):
            raise ProtocolError(
                f"{C.STAGE_GATE2_75} recorded {key} = {disposition[key]} and "
                f"{C.STAGE_GATE2} froze m* = {gate2_m_star}. m* is selected "
                "once, by §12.3's focal rule, and no later stage may move it")
    if disposition.get("reselected"):
        raise ProtocolError(
            f"{C.STAGE_GATE2_75} recorded `reselected` true. No reselection "
            "path exists; a record claiming one is a defect, not an outcome")
    return int(gate2_m_star)


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
        "nothing is substituted, promoted, widened or re-selected. This "
        "stage has one outcome, PASS, and records what it measured",
    "no_reselection_of_the_operating_point_exists":
        "A13: m* is frozen by §12.3 at GATE_2_FOCAL_CALIBRATION and this "
        "stage has no branch that returns a different one. "
        "`probe_disposition` refuses a table carrying any severity but m*, "
        "`assert_m_star_unmoved` checks m_star_in == m_star_out on the "
        "producing path, and `gates_run.effective_m_star` checks the written "
        "record against Gate 2's on every downstream read",
    "no_path_back_to_this_stage_exists":
        "the record is write-once and no later stage has a path back here; "
        "assert_transition_legal and assert_no_post_freeze_mutation enforce "
        "it",
    "no_composed_rate_terminates_a_replication":
        "v7 §13.14: the (0.05, 0.95) band is descriptive. No entry of any "
        "kind, at any level, ends the replication here; "
        "COMPOSED_HEADROOM_UNREACHABLE is withdrawn and has no raise path in "
        "this package (tests_v7 asserts the converse of A8 for it)",
    "no_measurement_is_reused_across_different_cases":
        "the cells this stage reads off the Gate-2 record instead of drawing "
        "again are read only when the topic identifiers and the draw count "
        "are identical; `shared_cell_verdict` checks that and records the "
        "reason either way. Nothing is reused across topic sets",
    "the_operating_point_was_frozen_before_any_composed_row":
        "Gate 2 selects m* from B's solo curve and records "
        "`operating_point_search_order` --- §12.3's own preference over "
        "`focal_admissible` --- and Gate 2.5 records which severities could "
        "meet §13.15's five-family minimum. Both are signed before this "
        "stage generates a row, and this stage reads the head of that order "
        "only to check that Gate 2 and Gate 2.5 agree about m*",
    "no_pool_is_chosen_by_a_composed_outcome":
        "§30: Gate 2 records a kappa(R|B) column and Gate 2.5 a §13.1 "
        "qualified pool at the frozen m*, both signed before this stage "
        "generates a row. This stage selects nothing --- not a severity, not "
        "a pool --- so no composed outcome can reach either",
    "no_standin_severity_depends_on_the_operating_point":
        "each stand-in is placed at the severity nearest Gate 2's iota_A "
        "inside §13.4's band, on its own solo ladder. iota_A does not depend "
        "on m*, so the companion a probed cell carries is fixed by a "
        "quantity the operating point cannot move",
    "no_contrast_here_licenses_a_claim":
        "every contrast on this record is a projection on the calibration "
        "topics, labelled PROJECTION_NOT_REGISTERED_FOR_INFERENCE and read "
        "by no rule. The registered estimate is the confirmatory one",
    "no_standin_entry_ends_a_replication":
        "a stand-in-dependent entry is classified for proximity and recorded "
        "under `standin_proximity`; an instrument that can never be selected "
        "as a reference decides nothing, and in v7 neither does a "
        "determinate one",
}

#: Stated on the payload because READINESS §3.2 says a limit discovered at
#: Gate 4 is a limit that should have been registered.
PROBE_SCOPE_LIMITS: tuple[str, ...] = (
    "the probe covers every one of Gate 4's ten slot-and-order exposure "
    "classes, and `assert_probe_covers_gate4_classes` refuses a shape that "
    "does not. What it cannot cover is the *identity* of the companion: the "
    "reference in each companion slot is selected two stages later, so the "
    "composed contrast a stand-in produces is not the contrast that "
    "reference will produce, and no closed measurement bounds the "
    "difference. Gate 4 is the first stage that measures the actual "
    "references, and it too records rather than decides",
    "the contrasts here are D(B<-A), D(A<-B), Lambda and the order contrasts "
    "Ord_A and Ord_B. Delta_R, Delta_j, Delta_near and Delta_broad need a "
    "companion that does not exist yet and are first projected at Gate 4",
    "the stage measures ONE operating point --- the m* §12.3 froze at Gate 2 "
    "--- and cannot move to another. Nothing it measures can stop the "
    "replication either: a composed rate at a boundary is a property of one "
    "arm, and what it does to the contrast is recorded (v7 §13.14)",
    "two stand-ins carry the target-with-companion and companion-with-"
    "companion classes rather than all three, which measures each class once "
    "instead of three times",
    "every interval here is a topic bootstrap on the 192 calibration topics "
    "at M_CAL, and every projected confirmatory half-width is §16.1's form "
    "re-combined at the registered M and block count from variance "
    "components one block set can only partly separate. Both are "
    "projections; §17.3's precision precondition is evaluated on the "
    "realised confirmatory interval",
    "Calibration-B is newly authored (§34 D3) and is not exchangeable with "
    "the confirmatory set the way Calibration-A is; the per-entry sub-split "
    "transfer is recorded beside every contrast and read by nothing",
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
