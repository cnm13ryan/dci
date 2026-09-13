"""§34 D6: what an unmet reference-support requirement costs, and for how long.

**The decision.** §13.15 registers what a replication needs before the primary
reference set exists: five families through the full V(R), three used and two
frozen, at least two of them Tier 1, three distinct feature groups. D6 asked
whether failing that is *terminal* --- the replication stops --- or an
*identification status*. The researcher closed it at ``identification_status``
(``reports/dci1v5/researcher_decisions.json``): a replication that cannot
build the reference set keeps running and keeps every estimand that does not
depend on one.

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

from dci1v5.protocol import constants as C

__all__ = ["CORE_SLOT_TOKENS", "REFERENCE_AGGREGATES", "REHABILITATION_PATHS",
           "NOT_IDENTIFIED", "reference_dependent",
           "AFFECTED_ESTIMANDS", "AFFECTED_BY_FAMILY", "UNAFFECTED_ESTIMANDS",
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


@dataclass(frozen=True)
class NonIdentification:
    """The Gate-3C record of an unmet §13.15, and its permanence."""

    model_key: str
    failures: tuple[str, ...]
    members: tuple[str, ...]
    irreversible: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": "D6", "value": "identification_status",
            "status": "REFERENCE_SUPPORT_NOT_IDENTIFIED",
            "model_key": self.model_key,
            "terminal": False,
            "irreversible": self.irreversible,
            "failures": list(self.failures),
            "not_identified_members": list(self.members),
            "still_identified_members": list(UNAFFECTED_ESTIMANDS),
            "rehabilitation_forbidden": dict(REHABILITATION_PATHS),
            "sentence": (
                "the primary reference set could not be constructed under "
                "§13.15, so every estimand that needs one is NOT_IDENTIFIED "
                "for this replication and stays NOT_IDENTIFIED; the "
                "replication continues for the estimands that do not need one"),
        }


def non_identification(*, model_key: str, support_met: bool,
                       failures: Sequence[str] = ()) -> dict[str, Any] | None:
    """Gate 3C's D6 record, or ``None`` when §13.15 is met."""
    if support_met:
        return None
    return NonIdentification(model_key=model_key,
                             failures=tuple(failures),
                             members=AFFECTED_ESTIMANDS).as_dict()


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
            "Gate 3C because §13.15's reference support was unmet, and this "
            "record offers an estimate for them. §34 D6 closed at "
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
        "n_affected": len(AFFECTED_ESTIMANDS),
        "affected_by_family": {k: list(v) for k, v in
                               AFFECTED_BY_FAMILY.items() if v},
        "affected": list(AFFECTED_ESTIMANDS),
        "still_identified": list(UNAFFECTED_ESTIMANDS),
        "rehabilitation_forbidden": dict(REHABILITATION_PATHS),
    }
