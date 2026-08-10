"""What is fixed, what is frozen, and what does not have a value yet.

The v19 preregistration deliberately distinguishes several kinds of "not yet
decided", and conflating them is how a study ends up with a fabricated number in
a freeze bundle. Section 1.3 gives the vocabulary: \\FIXED is a scientific
commitment or fully specified method; \\PFD is a numerical value or artifact
identity that *will* be produced by an already-frozen rule; \\GATE is an
acceptance condition. Section 1.3 also warns that "a row marked \\PFD is not
permission for implementer discretion: its value is produced only by the rule
cited in that row".

So this module models a slot rather than a value. A slot knows:

  * which preregistration section or decision-register row governs it;
  * whether it is fixed by the document, frozen by a completed procedure, or
    still pending - and if pending, *why*, because "we have not run the
    calibration yet" and "the investigators have not made the scientific
    judgement yet" are different blockers with different remedies;
  * the frozen rule that will produce it;
  * what it depends on.

Two invariants do the real work:

  * a pending slot may not carry a value. A default would be indistinguishable
    from a legitimately produced output once it reached an artifact, so there is
    no `default=` parameter anywhere in this module and `get()` raises.
  * a resolved slot may not be re-frozen. Freezing returns a new table; the
    dataclasses are frozen, so an accidental in-place mutation fails at the
    attribute level rather than silently rewriting a frozen commitment.

The pending reasons map onto the implementation-status vocabulary used by the
completion audit, which is why `blocking_status()` exists: an audit row saying
BLOCKED_BY_PROSPECTIVE_DECISION is then derived from the same declaration the
runtime gate reads, not maintained separately by hand.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Optional, Sequence

from dci.provenance.hashes import sha


class Resolution(str, enum.Enum):
    """Why a slot does or does not have a value."""

    # Fixed by the preregistration text itself. Changing it needs a new
    # protocol version, not a procedure.
    FIXED = "FIXED"

    # Produced by its frozen rule and now immutable.
    FROZEN = "FROZEN"

    # The rule is fixed; the empirical output has not been generated yet.
    PENDING_EMPIRICAL = "PENDING_EMPIRICAL"

    # Awaiting a prospective scientific judgement by the investigators, which
    # code must never make on their behalf (for example exact epsilon, D27).
    PENDING_DECISION = "PENDING_DECISION"

    # Awaiting hardware or runtime certification (for example the certified GPU
    # interchangeability class, D20).
    PENDING_CERTIFICATION = "PENDING_CERTIFICATION"

    # Awaiting authored and signed scientific content (for example the frozen
    # task and background pools, section 8.2).
    PENDING_CONTENT = "PENDING_CONTENT"


RESOLVED = (Resolution.FIXED, Resolution.FROZEN)
PENDING = (Resolution.PENDING_EMPIRICAL, Resolution.PENDING_DECISION,
           Resolution.PENDING_CERTIFICATION, Resolution.PENDING_CONTENT)

# The completion-audit status implied by each pending reason. Derived here so an
# audit cannot drift from the declaration the runtime gate actually enforces.
_BLOCKING_STATUS = {
    Resolution.PENDING_EMPIRICAL: "BLOCKED_BY_UPSTREAM_FREEZE",
    Resolution.PENDING_DECISION: "BLOCKED_BY_PROSPECTIVE_DECISION",
    Resolution.PENDING_CERTIFICATION: "BLOCKED_BY_HARDWARE",
    Resolution.PENDING_CONTENT: "BLOCKED_BY_CONTENT",
}


class UnresolvedDependency(RuntimeError):
    """A procedure asked for a value its own dependency order has not produced.

    Deliberately not a ValueError: this is a dependency-ordering failure in the
    stage sequence, not a malformed argument, and section 14 makes that ordering
    mandatory rather than advisory.
    """

    def __init__(self, message: str, slots: Sequence["Slot"] = ()):
        super().__init__(message)
        self.slots = tuple(slots)

    @property
    def statuses(self) -> tuple[str, ...]:
        return tuple(blocking_status(s) for s in self.slots)


class AlreadyFrozen(RuntimeError):
    """An attempt to give a value to a slot that already has one."""


class _Missing:
    """Sentinel for "no value", distinct from None which could be a value."""

    def __repr__(self) -> str:                       # pragma: no cover - debug
        return "<no value>"

    def __bool__(self) -> bool:
        return False


MISSING = _Missing()


def blocking_status(slot: "Slot") -> str:
    """The completion-audit status this slot implies."""
    if slot.resolution in RESOLVED:
        return "IMPLEMENTED_AND_TESTED"
    return _BLOCKING_STATUS[slot.resolution]


@dataclass(frozen=True)
class Slot:
    """One preregistered quantity, artifact identity, or decision.

    `rule` is the frozen procedure that produces the value. It is required for
    every pending slot: a pending quantity with no stated production rule is an
    open question rather than a preregistered deliverable, and the protocol has
    none of those left by design.
    """
    name: str
    prereg: str
    resolution: Resolution
    rule: str
    value: Any = MISSING
    depends_on: tuple[str, ...] = ()
    frozen_by: str = ""
    note: str = ""

    def __post_init__(self):
        if not self.name or not self.prereg:
            raise ValueError("a slot needs a name and a preregistration citation")
        if not isinstance(self.resolution, Resolution):
            raise ValueError(f"{self.name}: {self.resolution!r} is not a Resolution")
        if self.resolution in RESOLVED:
            if isinstance(self.value, _Missing):
                raise ValueError(
                    f"{self.name} is {self.resolution.value} but carries no "
                    "value; a resolved slot without a value is a claim that "
                    "something was decided when it was not")
        else:
            if not isinstance(self.value, _Missing):
                raise ValueError(
                    f"{self.name} is {self.resolution.value} yet carries the "
                    f"value {self.value!r}. A pending slot with a value is a "
                    "fabricated pre-freeze output: once it reaches an artifact "
                    "nothing distinguishes it from a legitimately produced one")
            if not self.rule:
                raise ValueError(
                    f"{self.name} is pending with no stated production rule; "
                    "every PFD names the rule that produces it (section 1.3)")
        if self.resolution is Resolution.FROZEN and not self.frozen_by:
            raise ValueError(
                f"{self.name} is FROZEN without naming the procedure or artifact "
                "that froze it, so its provenance cannot be audited")

    @property
    def resolved(self) -> bool:
        return self.resolution in RESOLVED

    @property
    def pending(self) -> bool:
        return not self.resolved

    @property
    def status(self) -> str:
        return blocking_status(self)

    def get(self) -> Any:
        """The value, or refuse. There is deliberately no default parameter."""
        if not self.resolved:
            raise UnresolvedDependency(
                f"{self.name} ({self.prereg}) is {self.resolution.value} and has "
                f"no value. It is produced by: {self.rule}"
                + (f". Waiting on: {', '.join(self.depends_on)}"
                   if self.depends_on else ""),
                slots=[self])
        return self.value

    def freeze(self, value: Any, by: str) -> "Slot":
        """Record a value produced by this slot's own frozen rule.

        Returns a new Slot. Refuses to overwrite an existing value, because
        section 14 allows a later stage to consume a frozen output but never to
        retrospectively change it.
        """
        if self.resolved:
            raise AlreadyFrozen(
                f"{self.name} is already {self.resolution.value} with value "
                f"{self.value!r}; a frozen pre-confirmatory output cannot be "
                "changed by a later stage (section 14)")
        if isinstance(value, _Missing):
            raise ValueError(f"{self.name}: cannot freeze the missing sentinel")
        if not by:
            raise ValueError(
                f"{self.name}: freezing requires the producing procedure or "
                "artifact, so the value's provenance is recorded with it")
        return replace(self, resolution=Resolution.FROZEN, value=value,
                       frozen_by=by)

    def describe(self) -> dict[str, Any]:
        """A serialisable audit row."""
        return {"name": self.name, "prereg": self.prereg,
                "resolution": self.resolution.value, "status": self.status,
                "rule": self.rule, "resolved": self.resolved,
                "depends_on": list(self.depends_on),
                "frozen_by": self.frozen_by, "note": self.note}


def fixed(name: str, prereg: str, value: Any, *, rule: str = "",
          note: str = "") -> Slot:
    """A quantity the preregistration fixes directly."""
    return Slot(name=name, prereg=prereg, resolution=Resolution.FIXED,
                rule=rule or "fixed by the preregistration text", value=value,
                note=note)


def pending(name: str, prereg: str, resolution: Resolution, rule: str, *,
            depends_on: Iterable[str] = (), note: str = "") -> Slot:
    """A pre-freeze deliverable whose frozen rule has not yet been executed."""
    if resolution not in PENDING:
        raise ValueError(f"{resolution} is not a pending resolution")
    return Slot(name=name, prereg=prereg, resolution=resolution, rule=rule,
                depends_on=tuple(depends_on), note=note)


@dataclass(frozen=True)
class SlotTable:
    """An immutable table of slots, addressable by name.

    Freezing returns a new table rather than mutating this one, so a stage that
    holds a reference to the pre-freeze table cannot observe a later stage's
    output appearing underneath it.
    """
    slots: tuple[Slot, ...]

    def __post_init__(self):
        seen: set[str] = set()
        for slot in self.slots:
            if slot.name in seen:
                raise ValueError(f"duplicate slot name {slot.name!r}")
            seen.add(slot.name)

    @classmethod
    def of(cls, *slots: Slot) -> "SlotTable":
        return cls(slots=tuple(slots))

    def __contains__(self, name: object) -> bool:
        return any(s.name == name for s in self.slots)

    def __len__(self) -> int:
        return len(self.slots)

    def __iter__(self):
        return iter(self.slots)

    def __getitem__(self, name: str) -> Slot:
        for slot in self.slots:
            if slot.name == name:
                return slot
        raise KeyError(
            f"{name!r} is not a declared slot; known: "
            f"{', '.join(sorted(s.name for s in self.slots))}")

    def value(self, name: str) -> Any:
        return self[name].get()

    def resolved(self) -> tuple[Slot, ...]:
        return tuple(s for s in self.slots if s.resolved)

    def unresolved(self) -> tuple[Slot, ...]:
        return tuple(s for s in self.slots if s.pending)

    def blockers(self, *names: str) -> tuple[Slot, ...]:
        """Which of the named slots are still pending, in declaration order."""
        wanted = set(names)
        return tuple(s for s in self.slots if s.name in wanted and s.pending)

    def require(self, *names: str, what: str = "") -> None:
        """Fail closed unless every named slot is resolved.

        This is the gate a stage calls before doing anything that numerically
        depends on a pre-freeze output. It reports *all* the blockers at once,
        with their production rules, so an operator learns the whole dependency
        set rather than discovering it one exception at a time.
        """
        for name in names:
            self[name]                                  # KeyError if undeclared
        missing = self.blockers(*names)
        if not missing:
            return
        subject = what or "this procedure"
        lines = [f"{subject} needs {len(missing)} unresolved pre-freeze "
                 f"{'output' if len(missing) == 1 else 'outputs'}:"]
        for slot in missing:
            lines.append(f"  - {slot.name} ({slot.prereg}) "
                         f"[{slot.status}] produced by: {slot.rule}")
            if slot.depends_on:
                lines.append(f"      waiting on: {', '.join(slot.depends_on)}")
        raise UnresolvedDependency("\n".join(lines), slots=missing)

    def freeze(self, name: str, value: Any, by: str) -> "SlotTable":
        """A new table with one slot resolved."""
        target = self[name]
        return SlotTable(slots=tuple(
            target.freeze(value, by) if s.name == name else s
            for s in self.slots))

    def merged(self, other: "SlotTable") -> "SlotTable":
        """Union of two tables; overlapping names are an error, not a silent win."""
        clash = sorted({s.name for s in self.slots} & {s.name for s in other.slots})
        if clash:
            raise ValueError(f"slot names declared twice: {clash}")
        return SlotTable(slots=self.slots + other.slots)

    def audit(self) -> tuple[dict[str, Any], ...]:
        return tuple(s.describe() for s in self.slots)

    @property
    def fingerprint(self) -> str:
        """Hash of the DECLARATION: names, citations, rules, dependencies.

        Deliberately excludes resolution state and values, so it is stable while
        pre-freeze outputs arrive. That is what makes it useful as an identity:
        two runs at different points in the stage sequence can be shown to be
        working from the same registry declaration. Use `state_fingerprint` to
        capture which outputs have actually been produced.

        Order-independent, so declaration order carries no meaning.
        """
        return sha(sorted(
            [s.name, s.prereg, s.rule, list(s.depends_on)]
            for s in self.slots))

    @property
    def state_fingerprint(self) -> str:
        """Hash of the declaration TOGETHER WITH what has been resolved.

        This is the freeze-state identity: it changes when a slot is frozen,
        which is exactly what Stage 12 and the Stage 14 root manifest need to
        record. It also changes if a PFD is illegitimately relabelled FIXED, so
        the two fingerprints together distinguish "same registry, further along"
        from "registry altered".

        Frozen values enter through their canonical serialisation, so a value
        with no reproducible form is refused rather than hashed by identity.
        """
        return sha([self.fingerprint, sorted(
            [s.name, s.resolution.value, s.frozen_by,
             sha(s.value) if s.resolved else ""]
            for s in self.slots)])

    def statuses(self) -> dict[str, int]:
        """How many slots sit at each audit status."""
        out: dict[str, int] = {}
        for slot in self.slots:
            out[slot.status] = out.get(slot.status, 0) + 1
        return out


def assert_no_fabricated_values(table: SlotTable,
                               forbidden: Mapping[str, Optional[str]]) -> None:
    """Check that named quantities the protocol reserves are still unresolved.

    Section 16 of the implementation directive lists quantities that must never
    be invented in code - exact epsilon, admitted reference identities, retained
    budgets, V, the selected inference method, the certified GPU class, final H
    and G. This turns that prohibition into an assertion a test can run, so an
    accidental placeholder is caught rather than shipped.
    """
    wrong = []
    for name, expected_rule in forbidden.items():
        slot = table[name]
        if slot.resolution is Resolution.FIXED:
            wrong.append(f"{name} is marked FIXED, but it is a pre-freeze output "
                         "produced by a procedure, not a value the "
                         "preregistration states")
        elif slot.resolution is Resolution.FROZEN:
            wrong.append(f"{name} carries a frozen value ({slot.value!r}) "
                         f"attributed to {slot.frozen_by!r}; confirm that "
                         "procedure genuinely ran")
        if expected_rule and expected_rule not in slot.rule:
            wrong.append(f"{name} cites rule {slot.rule!r}, which does not "
                         f"mention {expected_rule!r}")
    if wrong:
        raise AssertionError("reserved pre-freeze outputs are misdeclared:\n  "
                             + "\n  ".join(wrong))
