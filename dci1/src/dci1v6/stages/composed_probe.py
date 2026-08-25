"""§18 stage 8: ``GATE_2_75_COMPOSED_PROBE`` --- composed headroom before
reference selection (v6's addition).

**The problem it exists for.** m* is chosen at Gate 2 from B's *solo* curve,
and §13.14 checks composed compliance only at Gate 4 --- after the references
are selected, calibrated and bound. On the closed v5 study all four
replications sat within 0.054 of the ceiling or over it once B was composed,
and one of them terminated there with every earlier gate passed. The
measurement that would have shown it was available two stages earlier and
nobody took it.

**Scope: every slot and order class §13.14 will audit.** The first version of
this stage probed the B slot only, and READINESS §3.2 recorded that as a scope
limit --- it could not have seen the companion-slot failure that actually
terminated ``gemma-3n-e4b-it``. The scope is now derived from Gate 4's own
cell set rather than hand-listed: ``gate4_exposure_classes`` partitions
§8.1's 95 cell x slot entries by (arm, the roles of the slots in prompt
order), and ``assert_probe_covers_gate4_classes`` refuses a probe shape that
leaves one of the ten classes unmeasured. Two roles exist when this stage
runs --- A at n* and B at m* --- and the third, *companion*, does not, so it
is carried by frozen ``probe_only`` stand-ins.

**Determinate and stand-in-dependent entries are not the same measurement,
and the verdict does not pretend they are.** A cell whose constituents are all
real registered instruments (``solo:A``, ``solo:B``, ``pair:A+B``,
``pair:B+A``) measures, on a development split, the same quantity §13.14 will
measure on the composed split; the only thing between the two is sampling,
and the probe *projects* it. A cell containing a stand-in measures a real
composed cell of a real instrument, but not the one Gate 4 will audit, and no
available evidence bounds the difference between a stand-in and the reference
that replaces it. So:

* a **determinate** entry passes iff its projected Gate-4 interval lies inside
  §13.14's registered band. The projection uses the entry's own in-stage
  between-topic variance at §13.4's registered 95% level --- the same device
  §13.4 already applies to the same band, so the convention is the
  protocol's own and not this stage's. The family-wise half-width over the
  six determinate entries is computed and recorded beside it, so the more
  conservative reading is on the artifact rather than in an argument;
* a **stand-in-dependent** entry passes iff its measured compliance lies
  inside §13.14's registered band, with **no margin at all**. A failure there
  is not an extrapolation: a real composed cell of real instruments at this
  operating point left the band. Its *passing* proves nothing about a
  reference, and this module says so rather than implying otherwise.

**What Gate 4 still detects that this stage cannot** is stated on the record
in ``PROBE_SCOPE_LIMITS`` and is not a residue of forgetting: the reference
identities, their severities, their calibration-split solo values and the
composed lift they specifically produce are all determined two stages later.

**What interaction-blindness means here**, narrowly and checkably: this stage
is blind to any *reference* and to any *composed contrast*. Four independent
guarantees, each enforced somewhere a reader can point at:

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
   §33 check 8's name scan reads **this** record on the same terms as the
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

**§13.14's band is unchanged.** The projection is a margin **inside**
[0.05, 0.95], never a relaxation of it, and Gate 4 still applies the
registered band to the registered composed set.

**Two things this module does not decide, and refuses to.** The topic split
(§34 D20) and the residual allowance (§34 D23) are researcher decisions;
which stand-ins exist is §34 D24 and its closure selects the population
``PROBE_ONLY_FAMILY_IDS`` already carries. Every accessor below goes through
``protocol/decisions``, so no caller gets a default and no stage can run while
one is open.
"""
from __future__ import annotations

import inspect
import math
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.design import cells as design_cells
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.stages.regime import select_operating_point
from dci1v6.verifiers.constraints import (
    PROBE_ONLY_FAMILY_IDS, focal_severities,
)

__all__ = ["COMPOSED_HEADROOM_UNREACHABLE", "PROBE_SLOTS", "probe_slots",
           "probe_cell_types", "probe_split", "margin", "standins",
           "margin_band", "severity_verdict", "probe_disposition",
           "assert_probe_reads_no_reference", "PROBE_DECLARED_REFUSALS",
           "REFERENCE_TOKENS", "FORBIDDEN_SOURCE_READS",
           "PROBE_SCOPE_LIMITS", "assert_probe_severities_are_admissible",
           "SHARED_WITH_GATE2", "shared_cell_verdict",
           "slot_role", "gate4_exposure_classes", "probe_class_coverage",
           "assert_probe_covers_gate4_classes", "DETERMINATE_SLOTS",
           "is_determinate", "cell_slots_of", "projected_halfwidth",
           "entry_verdict",
           "DESIGNATED_COMPANION_SLOTS", "standin_operating_points",
           "PROBE_ONLY_KINDS",
           "RESIDUAL_SD", "PROBE_LADDER_DRAWS", "N_DETERMINATE_ENTRIES"]

#: §28, new in v6. Raised by ``probe_disposition`` and nowhere else.
COMPOSED_HEADROOM_UNREACHABLE = "COMPOSED_HEADROOM_UNREACHABLE"

#: The probe's own slot names. They are deliberately **not** in
#: ``C.REGISTERED_SLOT_ORDER``: a stand-in has no slot in the confirmatory
#: design, so there is no name a probe cell and a design cell could share.
PROBE_SLOTS: tuple[str, ...] = ("P1", "P2", "P3")

#: The slots whose instrument is a real registered one when this stage runs:
#: A at n* and B at m*, both fixed at Gate 2.
DETERMINATE_SLOTS: tuple[str, ...] = C.BASE_SLOTS

#: §12.2's draw count, reused for the stand-in solo ladder. The ladder decides
#: only *which severity* each stand-in is probed at; every quantity a verdict
#: reads is measured on the probe split at ``M_CAL``.
PROBE_LADDER_DRAWS = C.LADDER_SCREEN_DRAWS

#: Which stand-ins carry the classes that pair a companion with the target and
#: with another companion. **A stated cap, not an oversight.** Running all
#: three stand-ins through every class would add eight cells per severity ---
#: 6,144 rows at ``N_CALIBRATION`` x ``M_CAL`` --- to measure the same class
#: three times with three instruments none of which is the reference. The
#: classes are covered; the within-class instrument spread is not, and
#: ``PROBE_SCOPE_LIMITS`` says so.
DESIGNATED_COMPANION_SLOTS: tuple[str, ...] = ("P1", "P2")

#: The residual, non-sampling difference between the split the probe measures
#: on and the split §13.14 audits on, as a standard deviation.
#:
#: **Measured, not chosen, and its value is the derivation.** §6.2 cuts the
#: pre-screen, calibration_a, composed, confirmatory and sequestered sets from
#: one seeded per-area shuffle, so those four are exchangeable and the
#: difference between them is sampling. §34 D3's ``calibration_b`` is newly
#: authored and is *not* part of that cut, and it supplies half the topics a
#: pooled probe measures on --- so a pooled estimate carries half of whatever
#: instrument-specific offset the authored half introduces.
#: ``tools/v6_precision_design.py`` measures that offset on the closed v5
#: record, paired by instrument across §13.7's two sub-splits: residual sd
#: 0.0284 after sampling is removed, halved to **0.0142** by the pooling.
#: ``reports/dci1v6/precision_design.json`` carries the derivation.
#:
#: This is a v5-informed design constant under §30's precedent: v6 tests it
#: prospectively --- §34 D20's ``calibration_with_measured_transfer`` branch
#: records the realised sub-split movement per entry, in this stage --- and v6
#: may not claim it generalises.
RESIDUAL_SD = 0.0142

#: The determinate Gate-4 entries: A and B each in ``solo:A``/``solo:B`` and
#: in both orders of ``pair:A+B``. Six, and the family size the projection is
#: corrected over, because §13.14's verdict is a conjunction across entries.
N_DETERMINATE_ENTRIES = 6

#: §13.4's registered confidence level, as the z a two-sided 95% interval uses.
_Z_95 = 1.959963984540054


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

    * ``calibration_pooled`` --- §6.2's 192 calibration topics, pooled.
    * ``reserved_composed`` --- the §6.2 composed set, which §6.2 spends once.
    * ``calibration_with_measured_transfer`` --- the calibration split, with
      every entry measured on **both** 96-topic sub-splits so the realised
      movement between them is recorded beside the verdict. That movement is
      not a diagnostic: calibration_a comes from §6.2's seeded cut and is
      exchangeable with the composed set, while §34 D3's calibration_b is
      newly authored and is not, so the sub-split contrast measures the one
      component of the calibration-to-composed difference that is **not**
      sampling. It costs no extra rows, because §13.7 already generates both.
    """
    return decisions.choice(
        "D20",
        {"calibration_pooled": "calibration_pooled",
         "reserved_composed": "composed",
         "calibration_with_measured_transfer": "calibration_both_subsplits"},
        where="stages.composed_probe.probe_split")


def margin() -> float:
    """§34 D23 (READINESS R5): the **residual** allowance, in compliance units.

    **This is no longer "the value of delta", because the quantity delta was
    invented to absorb turned out to be measurable.** READINESS §4.a asked a
    margin to cover a calibration-to-composed transfer whose realised
    magnitude reached 0.189 and an unmeasured stand-in-to-reference term. Two
    things changed that question:

    * the transfer is **sampling**. Over the thirteen realised movements the
      observed variance is 0.00430 against the 0.00515 the two sample sizes
      imply, so nothing survives to be a bias --- and §6.2's seeded cut says
      why: the composed set and calibration_a come from one shuffle. What does
      not is calibration_b, and its contribution is carried by ``RESIDUAL_SD``
      and by the in-stage sub-split measurement, per entry, not by a constant;
    * the stand-in-to-reference term is not covered by any margin, because no
      margin can be. Stand-in-dependent entries are therefore judged against
      §13.14's registered band directly, with no margin at all.

    What is left for this decision is the allowance for a residual the
    measurement did not find and the design says should not exist. The
    derivation gives **0.0**; ``reports/dci1v6/precision_design.json`` carries
    it, including the 95% upper bound on what a residual could be and still be
    consistent with thirteen observations.
    """
    decisions.assert_decisions_closed_for("stages.composed_probe.margin")
    value = decisions.value_of("D23")
    low, high = C.COMPOSED_HEADROOM_BAND
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProtocolError(
            f"§34 D23 closed at {value!r}; the residual allowance is a number")
    value = float(value)
    if not 0.0 <= value < (high - low) / 2:
        raise ProtocolError(
            f"§34 D23 closed at {value}, which leaves no interior to "
            f"{list(C.COMPOSED_HEADROOM_BAND)}. It is an allowance inside the "
            "registered band and never a change to it")
    return value


def margin_band() -> tuple[float, float]:
    """§13.14's band contracted by the residual allowance alone.

    The **floor** the projection is applied on top of, not the verdict:
    ``entry_verdict`` adds each entry's own projected half-width to this. It
    exists so a reader can see the constant part separately from the measured
    part, which is what READINESS R2 asks the record to expose.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    residual = margin()
    return (low + residual, high - residual)


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
        selection = select_operating_point(
            {int(q): float(v) for q, v in curve.items()},
            band=C.HEADROOM_BAND, aim=float(iota_a), prefer_smaller=True,
            grid=tuple(sorted(int(q) for q in curve)))
        if selection["selected"] is None:
            raise ProtocolError(
                f"no severity of the stand-in {kind!r} has solo compliance "
                f"inside §13.4's {list(C.HEADROOM_BAND)} on this "
                f"replication, so it cannot stand in for a reference here. "
                f"Measured: {dict(sorted((int(q), round(float(v), 4)) for q, v in curve.items()))}")
        out[kind] = {"severity": int(selection["selected"]),
                     "aim": float(iota_a),
                     "band": list(C.HEADROOM_BAND),
                     "rule": "§13.8's target for a companion is iota_A, and "
                             "§13.4's band is what admits one",
                     "curve": {str(q): float(v) for q, v in sorted(
                         (int(k), v) for k, v in curve.items())},
                     "selection": selection}
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
#: over --- and ``solo:A`` at n* is Gate 2's iota_A. Re-drawing either would
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


# ------------------------------------------------- the projection and P3.2

def projected_halfwidth(s2_topic: float, *, n_probe: int,
                        n_composed: int | None = None,
                        k: int = 1,
                        residual_sd: float = RESIDUAL_SD) -> float:
    """How far a determinate entry can move between this stage and Gate 4.

    Three terms and no fourth:

    1. **Gate 4's own sampling**, ``s2 / n_composed`` --- the dominant one.
       §13.14 takes a binary verdict on ``N_COMPOSED`` topics, and the topic
       is the sampling unit: the measured topic-level ICC on the closed v5
       Gate-4 rows is 0.35, so draws within a topic are not independent
       observations and only topics buy precision.
    2. **This stage's own sampling**, ``s2 / n_probe``.
    3. **The residual**, ``residual_sd`` --- the newly authored calibration
       sub-split's contribution, which is the only part §6.2's seeded cut does
       not make exchangeable.

    ``k`` is the family size the level is corrected over, and it **defaults
    to 1** because that is what the registered protocol does. §13.4 is the
    same device on the same band --- contract it, and apply it to the
    interval so an imprecisely measured value cannot sit on the boundary ---
    and it takes a per-candidate 95% Wilson interval with no correction for
    the number of candidates, even though §13.15 requires several of them to
    pass at once. Using a different convention here for the same device in
    the same protocol would be an unregistered choice made by this function.

    ``k = N_DETERMINATE_ENTRIES`` is the family-wise reading, and every
    verdict records it alongside, because §13.14's verdict *is* a conjunction
    and a reader is entitled to see what a corrected margin would have
    refused.
    """
    if s2_topic < 0:
        raise ProtocolError(f"a variance cannot be {s2_topic}")
    if n_probe <= 0:
        raise ProtocolError("the probe measured no topics")
    if k < 1:
        raise ProtocolError("the family size is at least one entry")
    composed = C.N_COMPOSED if n_composed is None else int(n_composed)
    if composed <= 0:
        raise ProtocolError("§13.14 audits at least one topic")
    variance = s2_topic / composed + s2_topic / n_probe + residual_sd ** 2
    return _z_two_sided(0.05 / k) * math.sqrt(variance)


def _z_two_sided(alpha: float) -> float:
    """The standard-normal quantile at ``1 - alpha/2``, by bisection.

    Written out rather than imported: this runtime carries no scipy, and a
    registered criterion that depends on an optional dependency is a criterion
    that stops reproducing.
    """
    if not 0.0 < alpha < 1.0:
        raise ProtocolError(f"alpha must be in (0, 1) and is {alpha}")
    if abs(alpha - 0.05) < 1e-12:
        return _Z_95
    low, high = 0.0, 12.0
    for _ in range(200):
        mid = (low + high) / 2
        if 0.5 * (1.0 + math.erf(mid / math.sqrt(2.0))) < 1.0 - alpha / 2:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def entry_verdict(entry: Mapping[str, Any], *, cell_id: str, slot: str,
                  cell_slots: Sequence[str], residual: float,
                  n_composed: int | None = None,
                  k: int = 1) -> dict[str, Any]:
    """One cell x slot entry, judged by what it is evidence for.

    ``entry`` carries ``compliance``, the between-topic variance
    ``s2_topic`` and ``n_topics``, all measured in this stage on the same
    rows.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    compliance = float(entry["compliance"])
    determinate = is_determinate(cell_slots)
    familywise = None
    if determinate:
        half = projected_halfwidth(
            float(entry["s2_topic"]), n_probe=int(entry["n_topics"]),
            n_composed=n_composed, k=k, residual_sd=residual)
        familywise = projected_halfwidth(
            float(entry["s2_topic"]), n_probe=int(entry["n_topics"]),
            n_composed=n_composed, k=N_DETERMINATE_ENTRIES,
            residual_sd=residual)
        lower, upper = compliance - half, compliance + half
        passes = low <= lower and upper <= high
        basis = ("the projected Gate-4 interval, from this entry's own "
                 "between-topic variance, at §13.4's level and by §13.4's "
                 "device")
    else:
        half = 0.0
        lower = upper = compliance
        passes = low <= compliance <= high
        basis = ("§13.14's registered band applied to the measured value. No "
                 "margin: a stand-in is not the reference, so a projection "
                 "from it would be a projection of the wrong instrument")
    entry_out = {"cell": cell_id, "slot": slot, "compliance": compliance,
                 "determinate": determinate, "half_width": half,
                 "projected_low": lower, "projected_high": upper,
                 "band": [low, high], "passes": passes, "basis": basis,
                 "s2_topic": float(entry["s2_topic"]),
                 "n_topics": int(entry["n_topics"])}
    if familywise is not None:
        # Recorded, read by nothing. The verdict is §13.4's convention; this
        # is what a Bonferroni reading over §13.14's conjunction would have
        # required, so a reviewer can see the gap rather than take it on
        # trust. It is deliberately conservative: the six entries share one
        # topic set, so their errors are correlated and Bonferroni overstates.
        entry_out["half_width_familywise"] = familywise
        entry_out["passes_familywise"] = (
            low <= compliance - familywise
            and compliance + familywise <= high)
    return entry_out


def severity_verdict(cells: Mapping[str, Mapping[str, Mapping[str, Any]]], *,
                     residual: float, n_composed: int | None = None,
                     k: int = 1) -> dict[str, Any]:
    """P3.2: a severity passes iff **every** probed entry passes its own test.

    ``cells`` maps a probe cell id to slot -> measurement. The unconstrained
    cell carries no constraint and is recorded, not evaluated.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    verdicts = []
    for cell_id, entry in sorted(cells.items()):
        if cell_id == "unconstrained":
            continue
        cell_slots = cell_slots_of(cell_id)
        measured = tuple(sorted(entry))
        if measured != tuple(sorted(cell_slots)):
            raise ProtocolError(
                f"{cell_id} states {sorted(cell_slots)} and carries a "
                f"measurement for {list(measured)}. A missing entry would "
                "change which verdict rule the rest of the cell is judged "
                "under, so it is refused rather than skipped")
        for slot in cell_slots:
            verdicts.append(entry_verdict(
                entry[slot], cell_id=cell_id, slot=slot,
                cell_slots=cell_slots, residual=residual,
                n_composed=n_composed, k=k))
    failures = [v for v in verdicts if not v["passes"]]
    determinate = [v for v in verdicts if v["determinate"]]
    familywise_failures = [v for v in determinate
                           if not v.get("passes_familywise", True)]
    return {
        "passes": not failures, "failures": failures,
        "would_fail_familywise": [
            {"cell": v["cell"], "slot": v["slot"],
             "compliance": v["compliance"],
             "half_width_familywise": v["half_width_familywise"]}
            for v in familywise_failures],
        "entries": verdicts,
        "n_entries_evaluated": len(verdicts),
        "n_determinate_entries": len(determinate),
        "n_standin_dependent_entries": len(verdicts) - len(determinate),
        "registered_band": [low, high],
        "residual_allowance": residual,
        "level_k": k,
        "familywise_k": N_DETERMINATE_ENTRIES,
        "n_composed": C.N_COMPOSED if n_composed is None else int(n_composed),
        "band_is_unchanged": True,
    }


def probe_disposition(*, m_star: int,
                      probed: Mapping[int, Mapping[str, Mapping[str, Any]]],
                      gate2_solo_curve: Mapping[int, float],
                      residual: float,
                      n_composed: int | None = None) -> dict[str, Any]:
    """P3.3 to P3.6: m* stands, m* is re-selected once, or the study stops.

    ``probed`` maps each probed severity to its cell -> slot -> measurement
    table. ``gate2_solo_curve`` is **Gate 2's own** measured solo B curve; it
    is the selection input and the probe is not. The probe decides only which
    severities are admissible.

    Raising is the registered outcome of P3.6 and it is raised here, so the
    A8 AST regression --- every status in force has a reachable ``raise`` ---
    covers ``COMPOSED_HEADROOM_UNREACHABLE`` without modification. That test
    is the V5-E32 fix and it is why this status cannot repeat it.
    """
    from dci1v6.run.lifecycle import TerminalStatus

    verdicts = {m: severity_verdict(table, residual=residual,
                                    n_composed=n_composed)
                for m, table in sorted(probed.items())}
    if m_star not in verdicts:
        raise ProtocolError(
            f"P3.1: m* = {m_star} must be probed first and it was not")
    passing = sorted(m for m, v in verdicts.items() if v["passes"])
    base = {"m_star_in": m_star, "probed_severities": sorted(verdicts),
            "verdicts": {str(m): v for m, v in verdicts.items()},
            "passing_severities": passing,
            "residual_allowance": residual,
            "registered_band": list(C.COMPOSED_HEADROOM_BAND),
            "band_is_unchanged": True,
            "selection_input": "GATE_2_FOCAL_CALIBRATION's solo B curve",
            "reselections_permitted": 1}
    if verdicts[m_star]["passes"]:
        return {**base, "reselected": False, "m_star_out": m_star,
                "reason": "P3.3: m* keeps every probed entry inside its own "
                          "test, so it stands"}
    if not passing:
        raise TerminalStatus(
            COMPOSED_HEADROOM_UNREACHABLE, gate=C.STAGE_GATE2_75,
            criterion=(
                "P3.6: no severity Gate 2 found eligible keeps every probed "
                "entry inside §13.14's unchanged band "
                f"{list(C.COMPOSED_HEADROOM_BAND)} --- determinate entries "
                "through their projected Gate-4 interval, stand-in-dependent "
                "entries through the band itself"),
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
            "reason": "P3.4: m* failed; the registered focal rule re-ran "
                      "unchanged over Gate 2's solo curve restricted to the "
                      "severities the probe admitted"}


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
        "§13.14's [0.05, 0.95] band is unchanged. The projection is a margin "
        "inside it and Gate 4 still applies the registered band",
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
    "no_standin_severity_depends_on_the_operating_point":
        "each stand-in is placed at the severity nearest Gate 2's iota_A "
        "inside §13.4's band, on its own solo ladder. iota_A does not depend "
        "on m*, so re-selecting the operating point does not move a stand-in "
        "and a probed severity is never compared against a different "
        "companion from the one before it",
    "no_margin_is_claimed_for_a_stand_in_dependent_entry":
        "a cell containing a stand-in is judged against §13.14's registered "
        "band with no margin. Its failure is a real composed cell leaving the "
        "band; its passing is not evidence that the reference which replaces "
        "the stand-in will also be inside it, and nothing here treats it as "
        "though it were",
}

#: Stated on the payload because READINESS §3.2 says a limit discovered at
#: Gate 4 is a limit that should have been registered.
PROBE_SCOPE_LIMITS: tuple[str, ...] = (
    "the probe covers every one of §13.14's ten slot-and-order exposure "
    "classes, and `assert_probe_covers_gate4_classes` refuses a shape that "
    "does not. What it cannot cover is the *identity* of the companion: the "
    "reference in each companion slot is selected two stages later, so the "
    "composed lift a stand-in produces is not the lift that reference will "
    "produce, and no closed measurement bounds the difference. Gate 4 remains "
    "the only stage that measures the actual references",
    "for the same reason a stand-in-dependent entry carries no margin. It "
    "gates only when a real composed cell of real instruments leaves the "
    "registered band, and it never certifies that a reference would not",
    "two stand-ins carry the target-with-companion and companion-with-"
    "companion classes rather than all three, which measures each class once "
    "instead of three times. Running all three through every class would add "
    "eight cells and 6,144 rows per probed severity",
    "the projected interval is a statement about **sampling** between this "
    "stage's split and §13.14's. It cannot see a reference's calibration-"
    "split solo value, its severity, or the arm set Gate 3C will admit, and "
    "succeeding at the reference-supply change raises the number of Gate-4 "
    "entries from 6 to as many as 95",
    "Gate 4 audits the composed topic set, which this stage never touches. "
    "The composed set is spent once (§6.2) and its 24 topics are the "
    "registered precision of the verdict; a joint topic bootstrap over the "
    "closed v5 tables puts the chance that a replication whose entries are "
    "all in band nonetheless fires at 0.12 to 0.19, and no probe removes it",
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
