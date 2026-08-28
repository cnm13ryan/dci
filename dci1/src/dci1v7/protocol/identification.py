"""§34 D6: what an unmet reference-support requirement costs, and for how long.

**The decision.** §13.15 registers what a replication needs before the primary
reference set exists: five families through the full V(R), three used and two
frozen, at least two of them Tier 1, three distinct feature groups. D6 asked
whether failing that is *terminal* --- the replication stops --- or an
*identification status*. The researcher closed it at ``identification_status``
(``reports/dci1v7/researcher_decisions.json``): a replication that cannot
build the reference set keeps running and keeps every estimand that does not
depend on one.

**v7 A7 adds a second, smaller block under the same rule.** When §13.15 and
§12.6's core conditions hold but a spectrum condition (C2, C4) is lost at
design time --- or §13.12 finds no three straddling triples --- the core arm
stands and only the spectrum-dependent members (``SPECTRUM_ESTIMANDS``) are
``NOT_IDENTIFIED``, irreversibly, on a block whose ``status`` is
``DIFFICULTY_SUPPORT_NOT_IDENTIFIED``. ``assert_not_rehabilitated`` reads the
members and not the status, so the permanence is one mechanism.

**And the failure is irreversible, which is the half that needs code.** An
identification status that a later stage could quietly lift would be worse
than a terminal status, because the replication would carry an
``EXCESS_NOT_IDENTIFIED`` label through Gate 4 and emerge with an excess
estimate anyway. So:

* the affected estimand set is **derived** from §15's registered families by
  a stated rule, not restated as a list that can drift from them;
* Gate 3C writes a ``NonIdentification`` record naming that set, and it is
  signed with the stage record like everything else;
* ``assert_not_rehabilitated`` is called by the freeze, by the analysis and
  by the final report, and refuses any later record that offers an estimate,
  an interval or an ``IDENTIFIED`` verdict for a member the Gate-3C record
  marked ``NOT_IDENTIFIED``.

**The four rehabilitation paths §34 D6 names are named here**, because each is
a thing somebody might reasonably try: a later gate passing, a frozen backup
being substituted in, the broad-class control standing in for the core pool,
or an observed composed outcome being read as evidence that the references
were adequate after all. The last is the dangerous one --- it is the
``observe B+R -> choose R`` loop §30 exists to forbid --- and it is refused by
name.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C

__all__ = ["CORE_SLOT_TOKENS", "REFERENCE_AGGREGATES", "REHABILITATION_PATHS",
           "NOT_IDENTIFIED", "reference_dependent",
           "AFFECTED_ESTIMANDS", "AFFECTED_BY_FAMILY", "UNAFFECTED_ESTIMANDS",
           "SPECTRUM_SLOT_TOKENS", "SPECTRUM_AGGREGATES", "spectrum_dependent",
           "SPECTRUM_ESTIMANDS", "SPECTRUM_BY_FAMILY", "BASE_ARM_ESTIMANDS",
           "affected_members", "status_of_members",
           "NonIdentification", "non_identification",
           "assert_not_rehabilitated", "identification_payload"]

#: The registered verdict a reference-dependent estimand carries once §13.15
#: is unmet. It is one word and it is permanent for the replication.
NOT_IDENTIFIED = "NOT_IDENTIFIED"

#: Slot names whose appearance in a member's name makes it reference-dependent:
#: the three core references, their six spectrum rungs, and the reference mean.
CORE_SLOT_TOKENS: tuple[str, ...] = (
    tuple(C.CORE_SLOTS) + tuple(C.SPECTRUM_SLOTS) + ("Rbar",))

#: Members whose *name* does not contain a slot but whose value is computed
#: from the reference set: the aggregates, the §11.8 fit's own parameters and
#: the quantity that reads that fit.
REFERENCE_AGGREGATES: tuple[str, ...] = (
    "Delta_R", "Delta_1", "Delta_2", "Delta_3", "Delta^A", "Xi",
    "delta_difficulty", "beta", "alpha_1", "alpha_2", "alpha_3", "gamma_tier",
)

#: §34 D6: the four ways a later stage might try to lift the status, each
#: refused by name because each is a thing a reasonable reader might attempt.
REHABILITATION_PATHS: dict[str, str] = {
    "later_gate": "Gate 4 passing does not rebuild a reference set Gate 3C "
                  "could not construct; §26's methodological success "
                  "criterion is judged NOT_MET and stays NOT_MET",
    "frozen_backup": "§13.14: the two frozen backups are frozen. They are "
                     "recorded so a reader can see the pool had depth, and "
                     "substituting one after a failure is the selection path "
                     "§13.14 forbids",
    # Named `..._substitution` and not `broad_class_control`: that string is
    # a §6.1 model-adaptive key, and the manifest's own guard walks keys.
    "broad_class_substitution": "§13.10 admits the broad-class companion to its "
                           "own slot and to no fit; Delta_broad is identified "
                           "on its own and is not a substitute for Delta_R",
    "observed_composed_outcome": "§30: no v5 B+R outcome may influence "
                                 "reference selection or its adequacy. "
                                 "Reading a composed result as evidence that "
                                 "the pool was sufficient after all is "
                                 "exactly the observe-then-choose loop the "
                                 "causal-design rule forbids",
}


def reference_dependent(member: str) -> bool:
    """Does this registered estimand need the primary reference set?

    The rule, stated once: a member is reference-dependent when its name
    names a core reference, a spectrum rung or the reference mean, or when it
    is one of the aggregates computed from them. Everything else --- D(B<-A),
    D(A<-B), Lambda, the near-form and broad-class quantities, the vacuity
    contrasts against A, and the order contrasts that do not involve Rbar ---
    is identified without one, which is the whole content of D6's closure.
    """
    # F5's `|` separates a member from its variant, so the aggregate test
    # reads the stem; F6's `|` is the conditional bar inside `vac(B|B+R1)`,
    # so the slot test reads the whole name. Splitting once for both would
    # classify every F6 contrast against a reference as reference-free.
    if member.split("|", 1)[0] in REFERENCE_AGGREGATES:
        return True
    for token in CORE_SLOT_TOKENS:
        if f"<-{token})" in member or f"({token}<-" in member or \
                f"+{token})" in member or member.endswith(f"_{token}"):
            return True
    return False


AFFECTED_BY_FAMILY: dict[str, tuple[str, ...]] = {
    family: tuple(m for m in members if reference_dependent(m))
    for family, members in C.FAMILY_MEMBERS.items()}
AFFECTED_ESTIMANDS: tuple[str, ...] = tuple(
    dict.fromkeys(m for members in AFFECTED_BY_FAMILY.values()
                  for m in members))
UNAFFECTED_ESTIMANDS: tuple[str, ...] = tuple(
    dict.fromkeys(m for members in C.FAMILY_MEMBERS.values() for m in members
                  if not reference_dependent(m)))

#: v7 A7: the members that need the SPECTRUM arm --- the six spectrum
#: companions' cells, or §11.8's fit on them. A subset of the
#: reference-dependent set, because the spectrum is drawn from admitted core
#: families (§13.12) and cannot exist without them.
SPECTRUM_SLOT_TOKENS: tuple[str, ...] = tuple(C.SPECTRUM_SLOTS)
SPECTRUM_AGGREGATES: tuple[str, ...] = (
    "delta_difficulty", "beta", "alpha_1", "alpha_2", "alpha_3", "gamma_tier",
)


def spectrum_dependent(member: str) -> bool:
    """Does this registered estimand need the difficulty-spectrum arm?

    The rule, stated once: a member is spectrum-dependent when its name names
    a spectrum rung, or when it is §11.8's residual or one of the fit's own
    parameters. Delta_R, Delta_j, Xi and the reciprocal matrix are NOT:
    §8.1 registers that a replication which cannot identify the spectrum
    still estimates them, and that is the whole content of A7.
    """
    if member.split("|", 1)[0] in SPECTRUM_AGGREGATES:
        return True
    for token in SPECTRUM_SLOT_TOKENS:
        if f"<-{token})" in member or f"({token}<-" in member or \
                f"+{token})" in member or member.endswith(f"_{token}"):
            return True
    return False


SPECTRUM_BY_FAMILY: dict[str, tuple[str, ...]] = {
    family: tuple(m for m in members if spectrum_dependent(m))
    for family, members in C.FAMILY_MEMBERS.items()}
SPECTRUM_ESTIMANDS: tuple[str, ...] = tuple(
    dict.fromkeys(m for members in SPECTRUM_BY_FAMILY.values()
                  for m in members))
#: §8.1's unconditional arm: what every replication that reaches Gate 3C
#: keeps whatever else it loses.
BASE_ARM_ESTIMANDS: tuple[str, ...] = (
    "D(B<-A)", "D(A<-B)", "Lambda", "Ord_A", "Ord_B", "Ord_Lambda")

assert set(SPECTRUM_ESTIMANDS) <= set(AFFECTED_ESTIMANDS), (
    "a spectrum-dependent member is reference-dependent: the spectrum is "
    "drawn from admitted core families")
assert "delta_difficulty" in SPECTRUM_ESTIMANDS
assert "D(B<-R1-)" in SPECTRUM_ESTIMANDS
assert "vac(B|B+R1-)-vac(B solo)" in SPECTRUM_ESTIMANDS
assert "gamma_tier" in SPECTRUM_ESTIMANDS
for _kept in ("Delta_R", "Delta_1", "Xi", "D(B<-R1)", "Ord_Rbar",
              "D(Rbar<-A)"):
    assert _kept not in SPECTRUM_ESTIMANDS, _kept
assert set(BASE_ARM_ESTIMANDS) <= set(UNAFFECTED_ESTIMANDS)


def affected_members(statuses: Iterable[str]) -> tuple[str, ...]:
    """The estimand set a design-time status makes NOT_IDENTIFIED (A7).

    ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` (or ``EXCESS_NOT_IDENTIFIED``) takes
    the whole reference-dependent set; ``DIFFICULTY_SUPPORT_NOT_IDENTIFIED``
    alone takes the spectrum-dependent set; nothing else takes anything here
    --- the near-form and class arms' absences are handled by the analysis
    on their own statuses and are not irreversible non-identifications.
    """
    present = set(statuses)
    if present & {"REFERENCE_SUPPORT_NOT_IDENTIFIED", "EXCESS_NOT_IDENTIFIED"}:
        return AFFECTED_ESTIMANDS
    if "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in present:
        return SPECTRUM_ESTIMANDS
    return ()


def status_of_members(statuses: Iterable[str]) -> str | None:
    """Which status a Gate-3C non-identification block carries, or None."""
    present = set(statuses)
    if present & {"REFERENCE_SUPPORT_NOT_IDENTIFIED", "EXCESS_NOT_IDENTIFIED"}:
        return "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    if "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in present:
        return "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    return None


# The primary quantity and the two the study can still answer without a
# reference set have to survive the rule, or the rule is wrong.
assert "D(B<-A)" in UNAFFECTED_ESTIMANDS
assert "Delta_near" in UNAFFECTED_ESTIMANDS
assert "vac(B|B+R1)-vac(B solo)" in AFFECTED_ESTIMANDS
assert "vac(B|A+B)-vac(B solo)" in UNAFFECTED_ESTIMANDS
assert "Delta_broad" in UNAFFECTED_ESTIMANDS
assert "Delta_R" in AFFECTED_ESTIMANDS
assert "Xi" in AFFECTED_ESTIMANDS
assert "delta_difficulty" in AFFECTED_ESTIMANDS


#: The two sentences a block can carry, by the status it records.
_SENTENCES = {
    "REFERENCE_SUPPORT_NOT_IDENTIFIED": (
        "the primary reference set could not be constructed under §13.15 or "
        "§12.6's core coverage conditions, so every estimand that needs one "
        "is NOT_IDENTIFIED for this replication and stays NOT_IDENTIFIED; "
        "the replication continues for the estimands that do not need one"),
    "DIFFICULTY_SUPPORT_NOT_IDENTIFIED": (
        "the difficulty spectrum could not be constructed under §12.6's "
        "spectrum coverage conditions or §13.12, so every estimand that "
        "needs the spectrum arm is NOT_IDENTIFIED for this replication and "
        "stays NOT_IDENTIFIED; the core reference set stands and the "
        "replication continues for every estimand that does not need the "
        "spectrum"),
}


@dataclass(frozen=True)
class NonIdentification:
    """The Gate-3C record of an unmet support requirement, and its permanence.

    v7 A7: the block carries the status it records. For
    ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` the members are the whole
    reference-dependent set; for a design-time
    ``DIFFICULTY_SUPPORT_NOT_IDENTIFIED`` they are the spectrum-dependent
    set. Either way ``assert_not_rehabilitated`` reads ``not_identified_
    members`` and nothing else, so the permanence is the same rule.
    """

    model_key: str
    failures: tuple[str, ...]
    members: tuple[str, ...]
    status: str = "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    irreversible: bool = True

    def as_dict(self) -> dict[str, Any]:
        if self.status not in _SENTENCES:
            raise ProtocolError(
                f"{self.status!r} is not a status a Gate-3C non-"
                "identification block may carry")
        still = tuple(m for members in C.FAMILY_MEMBERS.values()
                      for m in members if m not in set(self.members))
        return {
            "decision": "D6", "value": "identification_status",
            "status": self.status,
            "model_key": self.model_key,
            "terminal": False,
            "replication_continues": True,
            "irreversible": self.irreversible,
            "failures": list(self.failures),
            "not_identified_members": list(self.members),
            "still_identified_members": list(dict.fromkeys(still)),
            "rehabilitation_forbidden": dict(REHABILITATION_PATHS),
            "sentence": _SENTENCES[self.status],
        }


def non_identification(*, model_key: str, support_met: bool,
                       failures: Sequence[str] = (),
                       spectrum_identified: bool = True,
                       spectrum_failures: Sequence[str] = ()
                       ) -> dict[str, Any] | None:
    """Gate 3C's D6 record, or ``None`` when every support requirement was met.

    v7 A7: an unmet §13.15 or core coverage takes the reference-dependent
    set; a met §13.15 with the spectrum lost at design time takes the
    spectrum-dependent set, under the same irreversibility.
    """
    if not support_met:
        return NonIdentification(model_key=model_key,
                                 failures=tuple(failures),
                                 members=AFFECTED_ESTIMANDS).as_dict()
    if not spectrum_identified:
        return NonIdentification(
            model_key=model_key, failures=tuple(spectrum_failures),
            members=SPECTRUM_ESTIMANDS,
            status="DIFFICULTY_SUPPORT_NOT_IDENTIFIED").as_dict()
    return None


def _offered_members(record: Mapping[str, Any]) -> set[str]:
    """Every member a later record offers a number or a verdict for."""
    offered: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if isinstance(value, Mapping) and (
                        "estimate" in value or "lower" in value
                        or "simultaneous_lower" in value):
                    offered.add(str(key))
                walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                if isinstance(item, Mapping) and "member" in item and (
                        item.get("estimate") is not None
                        or item.get("simultaneous_lower") is not None):
                    offered.add(str(item["member"]))
                walk(item)

    walk(record)
    return offered


def assert_not_rehabilitated(later: Mapping[str, Any], *,
                             gate3c: Mapping[str, Any] | None,
                             where: str,
                             extra_members: Iterable[str] = ()) -> None:
    """§34 D6: a later stage may not lift a Gate-3C non-identification.

    ``gate3c`` is the Gate-3C payload, or its ``non_identification`` block, or
    ``None`` when §13.15 was met and there is nothing to protect. ``later`` is
    any stage payload; every member it offers an estimate or an interval for
    is checked against the frozen set.
    """
    if not gate3c:
        return
    block = gate3c.get("non_identification", gate3c)
    if not block or not block.get("not_identified_members"):
        return
    frozen = set(block["not_identified_members"]) | set(extra_members)
    offered = _offered_members(later) & frozen
    if offered:
        raise ProtocolError(
            f"{where}: {sorted(offered)} were marked {NOT_IDENTIFIED} at "
            f"Gate 3C ({block.get('status', 'REFERENCE_SUPPORT_NOT_IDENTIFIED')}"
            "), and this record offers an estimate for them. §34 D6 closed at "
            "'identification_status' with the non-identification irreversible "
            f"for the replication; the paths it forbids by name are "
            f"{sorted(REHABILITATION_PATHS)}")
    if block.get("irreversible") is False:
        raise ProtocolError(
            f"{where}: the Gate-3C record declares its non-identification "
            "reversible; §34 D6 admits no such record")


def identification_payload() -> dict[str, Any]:
    """What the registration manifest binds about D6's closure."""
    return {
        "decision": "D6",
        "rule": "a member is reference-dependent when its name names a core "
                "reference, a spectrum rung or the reference mean, or when it "
                "is one of the aggregates computed from them",
        "status_when_unmet": "REFERENCE_SUPPORT_NOT_IDENTIFIED",
        "terminal": False,
        "irreversible": True,
        "replication_continues": True,
        # v7 A7: the spectrum-dependent subset, NOT_IDENTIFIED on its own
        # when only the spectrum arm is lost at design time.
        "spectrum_rule": "a member is spectrum-dependent when its name names "
                         "a spectrum rung, or when it is delta_difficulty or "
                         "one of the §11.8 fit's own parameters",
        "spectrum_status_when_unmet": "DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
        "n_spectrum_affected": len(SPECTRUM_ESTIMANDS),
        "spectrum_affected": list(SPECTRUM_ESTIMANDS),
        "base_arm_always_identified": list(BASE_ARM_ESTIMANDS),
        "n_affected": len(AFFECTED_ESTIMANDS),
        "affected_by_family": {k: list(v) for k, v in
                               AFFECTED_BY_FAMILY.items() if v},
        "affected": list(AFFECTED_ESTIMANDS),
        "still_identified": list(UNAFFECTED_ESTIMANDS),
        "rehabilitation_forbidden": dict(REHABILITATION_PATHS),
    }
