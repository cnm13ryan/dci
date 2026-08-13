"""Identification verdicts for a primitive DCI cell.

A numerical estimate is not evidence that DCI was estimable. tau can be exactly
0.000 with a zero-width interval because the target never failed in either arm,
and that number means "this instrument had nothing to measure here", not "there
is no interference here". Those two readings are opposite in scientific content
and identical on the page, which is why the verdict is computed beside the
estimate rather than inferred from it afterwards.

The verdict is a property of ONE primitive cell: one checkpoint, one reasoning
condition, one background, one load, one reference. Moderators — background,
order, load, reasoning — are differences BETWEEN cells and are only meaningful
where the cells they difference are themselves identified.

Every verdict carries the constituent quantities that produced it, so a reader
can disagree with a threshold without re-deriving the arithmetic. Nothing here
suppresses an estimate: the estimate is always reported, with its verdict
attached.

Ordering matters. Execution and channel validity are checked before any
behavioural reading, because a cell whose harness failed is not a measurement of
the model at all. Uptake is checked before headroom, because an instruction that
was never delivered explains a floor more simply than the target does.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------- verdicts
IDENTIFIED = "IDENTIFIED"
#: Target essentially never fails in EITHER arm: tau is 0 by construction.
TARGET_CEILING = "TARGET_CEILING"
#: Target essentially always fails in either arm: no room for extra damage.
TARGET_FLOOR = "TARGET_FLOOR"
#: The focal instruction was not followed, so the treatment was not delivered.
FOCAL_NONUPTAKE = "FOCAL_NONUPTAKE"
#: The reference instruction was not followed, so load was not matched.
REFERENCE_NONUPTAKE = "REFERENCE_NONUPTAKE"
#: The reference itself damages the target, so it is not a neutral control.
REFERENCE_CONTAMINATED = "REFERENCE_CONTAMINATED"
#: The composition has no satisfying witness; failure is not informative.
UNSATISFIABLE = "UNSATISFIABLE"
#: The verifier is not certified for this output class.
VERIFIER_UNCERTIFIED = "VERIFIER_UNCERTIFIED"
#: A reasoning or output cap materially binds, so the cap is part of the treatment.
CAP_BOUND = "CAP_BOUND"
#: Reasoning and final answer could not be separated.
CHANNEL_INVALID = "CHANNEL_INVALID"
#: Verified apparatus failure in a material share of rows.
TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
#: Nominal replicates are not independent draws.
REPLICATES_DEPENDENT = "REPLICATES_DEPENDENT"
#: The execution condition was not validated for this cell.
EXECUTION_INVALID = "EXECUTION_INVALID"
#: Required identification evidence was never established, so identification
#: cannot be asserted in EITHER direction.
#:
#: This is distinct from every verdict above, and the distinction is the point.
#: `VERIFIER_UNCERTIFIED` says a certification was attempted and failed;
#: `EVIDENCE_INCOMPLETE` says none was ever recorded. Collapsing the two would
#: let an absent feed read as a passed check — which is precisely the fail-open
#: shape the layer exists to prevent. A cell here is not poolable, and the
#: reason names exactly which evidence is missing so it can be supplied.
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"

#: Only cells carrying this verdict may enter a pooled benchmark mean.
POOLABLE = frozenset({IDENTIFIED})

ALL_VERDICTS = (
    IDENTIFIED, TARGET_CEILING, TARGET_FLOOR, FOCAL_NONUPTAKE,
    REFERENCE_NONUPTAKE, REFERENCE_CONTAMINATED, UNSATISFIABLE,
    VERIFIER_UNCERTIFIED, CAP_BOUND, CHANNEL_INVALID, TECHNICAL_FAILURE,
    REPLICATES_DEPENDENT, EXECUTION_INVALID, EVIDENCE_INCOMPLETE,
)


@dataclass(frozen=True)
class Thresholds:
    """Every threshold in one place, so a sensitivity sweep is one object.

    These are declarations, not discoveries. `ceiling`/`floor` match the values
    the cross-model reporting pass already used, so verdicts stay comparable
    with the frozen documents.
    """
    #: Target failure at or below this in BOTH arms is a ceiling.
    ceiling: float = 0.02
    #: Target failure at or above this in BOTH arms is a floor.
    floor: float = 0.98
    #: Below this uptake, the slot occupant was not delivered.
    uptake: float = 0.50
    #: A reference damaging the target at least this much is not neutral.
    reference_damage: float = 0.50
    #: Cap-hit share at or above this makes the cap part of the treatment.
    cap_bound: float = 0.50
    #: Share of rows that may be apparatus failures before the cell is void.
    technical: float = 0.10
    #: Identical nominal replicate rate at or above this means a shared seed.
    duplicate: float = 0.25
    #: Fewest paired tasks a cell may rest on.
    min_tasks: int = 5


@dataclass
class CellEvidence:
    """The constituent quantities a verdict is computed from.

    Named after what they measure rather than after the column they came from,
    so a second pipeline can populate the same structure without renaming its
    own fields.
    """
    # Execution and channel.
    #
    # These four are tri-state on purpose. `None` means the evidence was never
    # established, and it is NOT the same as False. Defaulting them to True was
    # the fail-open shape a review caught: three preconditions were asserted
    # rather than measured, and two cells reached IDENTIFIED on that assertion.
    # There is no default now — a caller that cannot supply the evidence must
    # say so, and the cell fails closed to EVIDENCE_INCOMPLETE.
    execution_validated: bool | None = None
    channel_valid_rate: float | None = None
    technical_failure_rate: float = 0.0
    verifier_certified: bool | None = None
    # sampling
    replicate_identical_rate: float = 0.0
    n_tasks: int = 0
    n_rows_focal: int = 0
    n_rows_reference: int = 0
    n_answered_focal: int = 0
    n_answered_reference: int = 0
    # treatment delivery
    focal_uptake: float = 1.0
    reference_uptake: float = 1.0
    # target behaviour
    target_failure_focal: float = float("nan")
    target_failure_reference: float = float("nan")
    # caps and satisfiability
    cap_hit_rate: float = 0.0
    satisfiable: bool | None = None
    # estimate, carried through so the verdict travels with it
    tau: float = float("nan")
    lo: float = float("nan")
    hi: float = float("nan")


@dataclass
class Verdict:
    status: str
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def poolable(self) -> bool:
        return self.status in POOLABLE

    def to_dict(self) -> dict[str, Any]:
        return {"identification": self.status, "identification_reason":
                self.reason, **self.evidence}


def _nan(value: float) -> bool:
    return value != value


def classify(evidence: CellEvidence, thresholds: Thresholds | None = None
             ) -> Verdict:
    """The identification verdict for one primitive cell.

    Checked in order of precedence. An earlier verdict is not merely more
    severe, it makes the later questions unanswerable: there is no point asking
    whether the target had headroom in a cell whose harness never produced a
    valid channel.
    """
    t = thresholds or Thresholds()
    e = evidence
    ev = asdict(e)

    def verdict(status: str, reason: str) -> Verdict:
        return Verdict(status, reason, ev)

    # 0. Evidence completeness, before anything else.
    #
    # An absent feed must never read as a passed check. Each of these was
    # previously defaulted to True/1.0, so a caller that supplied nothing got a
    # cell certified on three assertions it had not made. `None` is not False:
    # it means nobody established the fact either way, and a cell in that state
    # is not identifiable in either direction.
    missing = [name for name, value in (
        ("execution_validated", e.execution_validated),
        ("channel_valid_rate", e.channel_valid_rate),
        ("verifier_certified", e.verifier_certified),
        ("satisfiable", e.satisfiable),
    ) if value is None]
    if missing:
        return verdict(EVIDENCE_INCOMPLETE,
                       "identification evidence was never established: "
                       + ", ".join(missing)
                       + ". This is not a finding about the model; it is a "
                         "missing input, and the cell cannot be identified "
                         "either way until it is supplied.")

    # 1. Execution condition. A cell the validator did not clear is a statement
    #    about the harness, not about the checkpoint.
    if not e.execution_validated:
        return verdict(EXECUTION_INVALID,
                       "the execution condition was not validated for this cell")
    if e.technical_failure_rate > t.technical:
        return verdict(TECHNICAL_FAILURE,
                       f"{e.technical_failure_rate:.1%} of rows are verified "
                       f"apparatus failures (> {t.technical:.0%})")
    if e.channel_valid_rate < 1.0 - t.technical:
        return verdict(CHANNEL_INVALID,
                       f"reasoning and final answer separated in only "
                       f"{e.channel_valid_rate:.1%} of rows")
    if not e.verifier_certified:
        return verdict(VERIFIER_UNCERTIFIED,
                       "the verifier is not certified for this output class")

    # 2. Sampling. Dependent replicates and a thin task set both mean the
    #    interval is not what it claims, whatever the point estimate says.
    if e.replicate_identical_rate >= t.duplicate:
        return verdict(REPLICATES_DEPENDENT,
                       f"{e.replicate_identical_rate:.1%} of nominal replicate "
                       f"pairs are identical (>= {t.duplicate:.0%}), which is "
                       "the signature of a shared seed")
    if e.n_tasks < t.min_tasks:
        return verdict(EXECUTION_INVALID,
                       f"only {e.n_tasks} paired task(s), below the minimum "
                       f"of {t.min_tasks}")

    # 3. Satisfiability. If nothing satisfies the composition, failure carries
    #    no information about interference.
    if not e.satisfiable:
        return verdict(UNSATISFIABLE,
                       "the composition has no satisfying witness")

    # 4. Caps. A materially binding cap is part of the treatment, so the cell
    #    does not describe the reasoning condition it is labelled with.
    if e.cap_hit_rate >= t.cap_bound:
        return verdict(CAP_BOUND,
                       f"{e.cap_hit_rate:.1%} of rows hit the generation cap "
                       f"(>= {t.cap_bound:.0%}), so the cap is part of the "
                       "treatment rather than a limit the model worked inside")

    # 5. Treatment delivery, BEFORE headroom. An instruction that was never
    #    followed explains a null more simply than the target's difficulty does,
    #    and identical prompt text does not imply equivalent treatment across
    #    checkpoints.
    if e.focal_uptake < t.uptake:
        return verdict(FOCAL_NONUPTAKE,
                       f"the focal instruction was followed in "
                       f"{e.focal_uptake:.1%} of rows (< {t.uptake:.0%}): the "
                       "treatment was not delivered")
    if e.reference_uptake < t.uptake:
        return verdict(REFERENCE_NONUPTAKE,
                       f"the reference instruction was followed in "
                       f"{e.reference_uptake:.1%} of rows (< {t.uptake:.0%}): "
                       "generic load is not matched")

    # 6. Headroom. Checked BEFORE reference integrity: when both arms saturate,
    #    the reference trivially satisfies the contamination test, but the
    #    binding fact is that the target has no room to move in either arm.
    #    Reporting that as a contaminated reference would blame the control for
    #    a configuration in which nothing could have been detected.
    if _nan(e.target_failure_focal) or _nan(e.target_failure_reference):
        return verdict(EXECUTION_INVALID,
                       "no scoreable rows in at least one arm")
    if (e.target_failure_focal <= t.ceiling
            and e.target_failure_reference <= t.ceiling):
        return verdict(TARGET_CEILING,
                       f"target failure is {e.target_failure_focal:.1%} focal "
                       f"and {e.target_failure_reference:.1%} reference "
                       f"(both <= {t.ceiling:.0%}): tau is 0 by construction "
                       "and the instrument has no headroom here")
    if (e.target_failure_focal >= t.floor
            and e.target_failure_reference >= t.floor):
        return verdict(TARGET_FLOOR,
                       f"target failure is {e.target_failure_focal:.1%} focal "
                       f"and {e.target_failure_reference:.1%} reference "
                       f"(both >= {t.floor:.0%}): no room for extra damage")

    # 7. Reference integrity, once the arms are known to be able to differ. A
    #    reference that itself damages the target is not an uncomplicated
    #    control, and tau measured against it is not focal-specific.
    if e.target_failure_reference >= t.reference_damage:
        return verdict(REFERENCE_CONTAMINATED,
                       f"the reference itself fails the target in "
                       f"{e.target_failure_reference:.1%} of rows "
                       f"(>= {t.reference_damage:.0%}), so it is not a neutral "
                       "control for generic load")

    return verdict(IDENTIFIED,
                   f"focal {e.target_failure_focal:.1%} vs reference "
                   f"{e.target_failure_reference:.1%} target failure, "
                   f"{e.n_tasks} paired tasks, uptake "
                   f"{e.focal_uptake:.0%}/{e.reference_uptake:.0%}")


def poolable(verdicts) -> list:
    """The subset of cells a benchmark mean may be taken over."""
    return [v for v in verdicts if v.poolable]
