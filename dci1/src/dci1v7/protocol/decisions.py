"""The registered open decisions of §34, as executable state (v7: 26).

**This module is why the v5 implementation cannot pretend to be a v5 study.**
§34 says all nineteen must be closed, with the decision and its evidence
recorded in the signed registration manifest, before stage 1 can pass; and
§18 stage 1 fails ``REGISTRATION_INCOMPLETE`` when one is not. Writing that
as prose in a preregistration and as nothing in the code is exactly how a
draft choice becomes an implementation fact --- the code needs a value, the
value gets chosen by whoever writes the line, and the choice is never
recorded as one.

So every decision here carries ``UNRESOLVED`` and a **standing proposal that
is not the decision**. Where a decision selects between behaviours the
implementation expresses *both*, behind ``choice()``, which raises until the
decision is closed. Nothing in this package reads a standing proposal as a
value.

Two shapes of dependence are distinguished, because they refuse at different
times:

* ``blocks_stages`` --- the lifecycle stages that may not run while the
  decision is open. ``assert_decisions_closed_for_stage`` is called by the
  stage machine, so an open decision stops the study rather than the
  function.
* ``blocks_calls`` --- named functions whose *behaviour* the decision selects.
  Those call ``choice()`` and raise where they are used, so a caller cannot
  route around the stage machine and get a default.

**Closing a decision is a researcher act and it happens here, on the record.**
``close()`` requires the resolution, the evidence and who took it; it refuses
a value the decision does not offer; and it is write-once per process.

**And it survives the process, because a closure that lives only in a running
interpreter is not a decision anybody took.** ``RECORD_PATH`` is a committed
file carrying every closure the researcher has actually made, with its
evidence, who took it and when; this module reads it at import and applies it.
So ``value_of("D18")`` answers with what the researcher decided, a test that
reopens the registry restores *that* state rather than a blank one, and the
registration manifest binds the record's hash beside the closures themselves.
A decision absent from the record is ``UNRESOLVED`` and every path that
depends on it still refuses.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj

__all__ = ["UNRESOLVED", "Decision", "DecisionOpenError", "DECISIONS",
           "DECISION_IDS", "open_decisions", "closed_decisions", "is_closed",
           "value_of", "choice", "assert_decisions_closed",
           "assert_decisions_closed_for_stage", "assert_decisions_closed_for",
           "decisions_blocking_stage", "decisions_blocking_call", "close",
           "reopen_all_for_testing", "override_for_testing",
           "registration_payload",
           "REGISTRATION_INCOMPLETE", "RECORD_PATH", "RECORD_RELPATH",
           "recorded_closures", "apply_recorded_closures", "record_hash",
           "record_payload", "non_adopted_alternatives", "recorded_spec",
           "read_record", "V5_DECISION_IDS", "V6_DECISION_IDS",
           "V7_DECISION_IDS", "WITHDRAWN_DECISION_IDS", "READINESS_MEMO_IDS"]

#: The value every decision carries until a researcher closes it.
UNRESOLVED = "UNRESOLVED"

#: §18 stage 1's failure status when a decision is still open.
REGISTRATION_INCOMPLETE = "REGISTRATION_INCOMPLETE"


class DecisionOpenError(ProtocolError):
    """A code path that depends on an unresolved §34 decision was reached."""


@dataclass(frozen=True)
class Decision:
    """One §34 entry.

    ``standing_proposal`` is the preregistration's own proposal, quoted so a
    reader can see what the researcher is being asked to accept or reject. It
    is **not** a default: ``value`` stays ``UNRESOLVED`` until ``close`` is
    called, and no function in this package falls back to the proposal.
    """

    id: str
    question: str
    standing_proposal: str
    #: The values a closure may take, or () when the decision is an
    #: acceptance rather than a selection between coded behaviours.
    admissible_values: tuple[Any, ...] = ()
    #: For a numeric decision: the half-open interval a closure must lie in,
    #: checked by ``close`` so an out-of-range value cannot sign a manifest
    #: and then fail at the stage that reads it.
    admissible_range: tuple[float, float] | None = None
    #: Alternatives the register once offered and the implementation carries
    #: **no branch for**. Recorded rather than deleted, because a value a
    #: researcher could not have executed is a different fact from a value
    #: nobody considered --- and because `choice()` refuses an admissible
    #: value with no branch, which is how these came to be found.
    unimplemented_alternatives: tuple[Any, ...] = ()
    #: Lifecycle stages that may not run while this is open.
    blocks_stages: tuple[str, ...] = ()
    #: Fully-qualified functions whose behaviour this decision selects.
    blocks_calls: tuple[str, ...] = ()
    #: The red-team finding this decision carries, where there is one.
    redteam: str | None = None
    value: Any = UNRESOLVED
    evidence: str | None = None
    decided_by: str | None = None
    decided_on: str | None = None

    @property
    def resolved(self) -> bool:
        return self.value != UNRESOLVED

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "question": self.question,
                "standing_proposal": self.standing_proposal,
                "admissible_values": list(self.admissible_values),
                "admissible_range": (None if self.admissible_range is None
                                     else list(self.admissible_range)),
                "unimplemented_alternatives":
                    list(self.unimplemented_alternatives),
                "blocks_stages": list(self.blocks_stages),
                "blocks_calls": list(self.blocks_calls),
                "redteam": self.redteam, "status":
                    "CLOSED" if self.resolved else "OPEN",
                "value": self.value, "evidence": self.evidence,
                "decided_by": self.decided_by, "decided_on": self.decided_on}


# Stage names are duplicated here as literals rather than imported from
# `constants`, because `constants` imports this module: a decision has to be
# expressible before the constants that depend on one are.
# The suffixes v5 used were sequence positions, and inserting Gate 2.75
# shifted every one after Gate 2.5 by one. Names that encode a position drift
# silently when the sequence changes, so these name the stage instead.
_REGISTERED_STAGE = "PROTOCOL_REGISTERED"
_QUALIFIED = "QUALIFIED"
_REGIME = "REGIME_SCREEN"
_GATE2 = "GATE_2_FOCAL_CALIBRATION"
_GATE2_5 = "GATE_2_5_CANDIDATE_QUALIFICATION"
_GATE2_75 = "GATE_2_75_COMPOSED_PROBE"
_GATE3A = "GATE_3A_REFERENCE_CALIBRATION"
_GATE3B = "GATE_3B_REFERENCE_SELECTION"
_GATE3C = "GATE_3C_IDENTIFICATION"
_GATE4 = "GATE_4_COMPOSED_CONTRAST"
_PREFREEZE = "PREFREEZE_AUDIT"
_CONFIRMATORY = "CONFIRMATORY_GENERATION"
_UNMASKED = "UNMASKED_ANALYSIS"

_REGISTERED: tuple[Decision, ...] = (
    Decision(
        "D0",
        "Whether to adopt v5 at all, given that its matching rule is fitted "
        "to v4r4 and §30 says so plainly",
        "Adopt, with §30's declaration attached permanently",
        admissible_values=("adopt", "do_not_adopt"),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D1",
        "The confirmatory compute budget: which arms and how many models",
        "Four models at 56 cells, with §6.1's execution order and "
        "NOT_EXECUTED for any replication not reached",
        admissible_values=("four_models_56_cells", "four_models_47_cells",
                           "two_models_56_cells", "384_blocks_m4"),
        blocks_stages=(_REGISTERED_STAGE,),
        blocks_calls=("design.cells.admitted_arms_from_decision",),
        redteam="R1 (dropping the near-form arm removes R1's only mitigation)"),
    Decision(
        "D2",
        "Whether a load-three arm is added so that the memo's Gamma becomes "
        "estimable",
        "No load-three arm; §5's exclusion stands",
        admissible_values=(),
        unimplemented_alternatives=('add_load_three',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D3",
        "Whether the 96 new Calibration-B questions are authored before "
        "adoption",
        "Author before adoption; the bank hash enters the registration "
        "manifest",
        admissible_values=("author_before_adoption", "author_after_adoption"),
        blocks_stages=(_REGISTERED_STAGE, _QUALIFIED),
        blocks_calls=("topics.calibration_b_bank",)),
    Decision(
        "D4",
        "The Tier-1 marker vocabulary: the eight registered markers of §7.10",
        "The eight of §7.10, with every rejection reason recorded",
        admissible_values=("approve_eight", "approve_with_substitution",
                           "reject"),
        blocks_stages=(_REGISTERED_STAGE, _REGIME),
        blocks_calls=("verifiers.constraints.assert_marker_vocabulary_"
                      "approved",)),
    Decision(
        "D5",
        "Whether a weighted composite validity score replaces the "
        "lexicographic conjunction",
        "Lexicographic; no composite score, because the development data "
        "cannot fix weights that generalise",
        admissible_values=(),
        unimplemented_alternatives=('weighted_composite',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D6",
        "Whether REFERENCE_SUPPORT_NOT_IDENTIFIED is terminal or an "
        "identification status",
        "Identification status, with §13.15's argument recorded",
        admissible_values=("identification_status", "terminal"),
        blocks_stages=(_REGISTERED_STAGE, _GATE3C),
        blocks_calls=("stages.support.support_disposition",),
        redteam="R16"),
    Decision(
        "D7",
        "The interaction-gate ceiling of 0.90",
        "0.90, with the coincidence recorded and not used as evidence",
        admissible_values=(),
        unimplemented_alternatives=(0.85, 0.95,),
        blocks_stages=(_REGISTERED_STAGE,),
        redteam="R13"),
    Decision(
        "D8",
        "The chance ceiling of 0.75",
        "0.75 on the point, 0.85 on the Wilson upper bound",
        admissible_values=(),
        unimplemented_alternatives=(0.5, 0.9,),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D9",
        "Whether an independent annotator will be available, which decides "
        "whether §10.3 can ever supersede §10.5's basis",
        "Unavailable; deterministic_measurement_validated with the scope "
        "sentence attached permanently",
        admissible_values=(),
        unimplemented_alternatives=('available',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D10",
        "Whether the broad-class arm carries more than one companion",
        "One companion; no class claim is made",
        admissible_values=(),
        unimplemented_alternatives=('several_companions',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D11",
        "Whether the confirmatory topics are re-authored rather than carried "
        "from v4",
        "Carry, with §6.2's statement of the residual",
        admissible_values=(),
        unimplemented_alternatives=('re_author',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D12",
        "Whether delta_difficulty or an order contrast receives a magnitude "
        "threshold of its own",
        "Direction and the SESOI only; the memo's 0.25 is not transferred",
        admissible_values=(),
        unimplemented_alternatives=('own_threshold',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D13",
        "Whether F11 is primary-tier",
        "Primary tier, F11, licensing L4b",
        admissible_values=(),
        unimplemented_alternatives=('secondary',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D14",
        "Whether instructed compliance remains the difficulty coordinate now "
        "that the core pool is chance-free",
        "iota remains primary, raw solo secondary, "
        "DIFFICULTY_COORDINATE_DEPENDENT on disagreement",
        admissible_values=(),
        unimplemented_alternatives=('raw_primary',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D15",
        "Whether the memo's 0.10 and 0.25 apply to a same-form Delta_R",
        "Both transfer, on the ground that the memo defined them for the "
        "shape of the contrast. Recorded as contestable",
        admissible_values=(),
        unimplemented_alternatives=('neither_transfers', 'generic_only',),
        blocks_stages=(_REGISTERED_STAGE,),
        redteam="R2"),
    Decision(
        "D16",
        "Whether Calibration-B measures the full carried set or only "
        "Calibration-A's survivors",
        "`complete_population`, as v5's researcher closed it on 2026-08-22 "
        "(`dci1/reports/dci1v5/researcher_decisions.json`): restricting to "
        "A-survivors makes §13.7 a re-confirmation of an already-selected "
        "set rather than a test of the candidate landscape's stability, and "
        "calling the two splits independent then overstates what the second "
        "buys. NOTE: until 2026-08-26 this field carried v5's PRE-adoption "
        "draft proposal, `a_survivors` --- the branch the researcher "
        "rejected, and the cheaper one by about 35,000 generations per "
        "replication. `design.budget.calibration_burden` and the published "
        "budget already cost `complete_population`",
        admissible_values=("a_survivors", "complete_population"),
        blocks_stages=(_REGISTERED_STAGE, _GATE3A),
        blocks_calls=("stages.stability.calibration_b_population",),
        redteam="R11"),
    Decision(
        "D17",
        "Whether a construct floor is registered for m*",
        "`floor`, as v5's researcher closed it on 2026-08-23 "
        "(`d17_b_strength_decision.md`): C1, the chance-compliance ceiling "
        "kappa_B(m*) <= 0.50 --- already registered, already reported at m*, "
        "computable with no new generation. NOTE: until 2026-08-26 this "
        "field carried v5's PRE-adoption draft proposal, `no_floor`, which "
        "the researcher rejected. It is also the weaker branch twice over: "
        "§13.14 aside, D17's floor is one of the three conditions "
        "`focal_admissible` conjoins, and P3.1 requires the probed m* to be "
        "in that set --- so dropping it would admit an operating point Gate "
        "2 would itself have refused",
        admissible_values=("no_floor", "floor"),
        blocks_stages=(_REGISTERED_STAGE, _GATE2),
        blocks_calls=("stages.regime.assert_construct_floor",),
        redteam="R14"),
    Decision(
        "D18",
        "Whether the near-form arm is a precondition of emitting L3c",
        "`precondition`, as v5's researcher closed it on 2026-08-22: the "
        "core reference pool is same-form with A by construction, so a "
        "Delta_R near zero is a plausible consequence of the DESIGN, and the "
        "strong L3c conclusion requires the near-form arm. NOTE: until "
        "2026-08-26 this field carried v5's PRE-adoption draft proposal, "
        "`not_a_precondition` --- the branch the researcher rejected, and "
        "the one that would let L3c be emitted without the arm. The v6 "
        "preregistration §1 lists this precondition among the substantive "
        "thresholds carried unchanged",
        admissible_values=("not_a_precondition", "precondition"),
        blocks_stages=(_REGISTERED_STAGE, _UNMASKED),
        blocks_calls=("analysis.claims.l3c_requires_near_form",),
        redteam="R1"),

    # ---------------------------------------------------------------- v6
    # D19-D25 are v6's, carried into v7 and requiring their own closure on
    # v7's record. v6's D23 and D26 --- what the Gate-2.75 residual allowance
    # MEANS and how LARGE it is --- are **withdrawn** with the projected-
    # interval verdict they parameterised (v7 A1): no v7 function reads
    # either, and a decision with no consumer is not a decision the study
    # takes. They are named in `WITHDRAWN_DECISION_IDS` with the reason so
    # the numbering stays continuous and a reader is not left to infer why
    # two ids are missing.
    Decision(
        "D19",
        "Whether Change 1 is the V6-E01 reachability repair alone, or that "
        "repair plus newly authored families (READINESS R1)",
        "Reachability only, then re-measure; L1-L4 remain available "
        "afterwards and register nothing that may prove unnecessary",
        admissible_values=(),
        unimplemented_alternatives=('reachability_and_new_families',),
        blocks_stages=(_REGISTERED_STAGE,)),
    Decision(
        "D20",
        "Which topic split GATE_2_75_COMPOSED_PROBE runs on (READINESS R2)",
        "The calibration split, with the realised split-to-split transfer "
        "measured in the same stage across §13.7's two sub-splits and "
        "recorded beside every contrast. `calibration_pooled` was withdrawn "
        "on 2026-08-26 as not a distinct branch. The live choice is whether "
        "the probe spends §6.2's reserved composed set",
        admissible_values=("reserved_composed",
                           "calibration_with_measured_transfer"),
        unimplemented_alternatives=("calibration_pooled",),
        blocks_stages=(_REGISTERED_STAGE, _GATE2_75),
        blocks_calls=("stages.composed_probe.probe_split",)),
    Decision(
        "D21",
        "How many topics Gate 4's composed-contrast projection is taken on "
        "(READINESS R3)",
        "As registered: §6.2's 24 composed-validation topics. Enlarging is "
        "not executable in this repository --- the sequestered eighth was "
        "never materialised here --- and in v7 the projection is a record "
        "read by no rule, so its precision buys diagnostic value and "
        "nothing else. `interval_criterion` is void: v7 §13.14 IS an "
        "interval reading of the contrast, on the estimand rather than on "
        "a marginal rate",
        admissible_values=(),
        unimplemented_alternatives=("enlarge_composed_set",
                                    "interval_criterion"),
        blocks_stages=(_REGISTERED_STAGE, _GATE4),
        blocks_calls=("design.budget.composed_topic_plan",)),
    Decision(
        "D22",
        "What licenses confirmatory generation: two identified Gate-5 "
        "survivors before any, or each frozen replication on its own "
        "(READINESS R4)",
        "Each independently identified and frozen replication may generate; "
        "two or more survivors are required only for replicated or "
        "generalised study-level statements, and v7 registers before data "
        "what it will and will not say when exactly one survives. A Gate-4 "
        "projection is not a licence to withhold generation from a "
        "replication that reaches Gate 5: a replication that reaches the "
        "freeze is run",
        admissible_values=("two_survivors_before_any", "per_replication"),
        blocks_stages=(_REGISTERED_STAGE, _CONFIRMATORY),
        blocks_calls=("run.lifecycle.confirmatory_licensed",)),
    Decision(
        "D24",
        "Whether the Gate-2.75 structural stand-ins are registered as "
        "probe_only families inside §7.10's library or as a separate frozen "
        "probe vocabulary with its own hash (READINESS R6)",
        "Inside the library --- one hash, one certification path, one place "
        "a reviewer looks --- at the cost of changing N_FAMILIES and every "
        "derived count `assert_library_sizes` asserts",
        admissible_values=("probe_only_in_library", "separate_vocabulary"),
        blocks_stages=(_REGISTERED_STAGE, _GATE2_75),
        blocks_calls=("stages.composed_probe.standins",)),
    Decision(
        "D25",
        "What v7 states at study level when exactly one replication reaches "
        "GATE_5_FREEZE identified --- registered before data, so that the "
        "number of survivors cannot be read afterwards as a licence",
        "`survivor_ladder_only`: the surviving replication's own L1-L4 ladder "
        "stands and nothing above it is said; L5 remains permanently "
        "withheld; the study reports the other replications' terminal "
        "statuses as terminal statuses and never as evidence about the "
        "effect. The alternative, `no_study_level_statement`, makes no "
        "study-level statement at all. Both sentences are written out in "
        "`run.lifecycle.SINGLE_SURVIVOR_STATEMENTS`; the caller is "
        "`tools/v7_closure.py`",
        admissible_values=("survivor_ladder_only",
                           "no_study_level_statement"),
        blocks_stages=(_REGISTERED_STAGE, _CONFIRMATORY),
        blocks_calls=("run.lifecycle.study_level_statement",)),

    # ---------------------------------------------------------------- v7
    Decision(
        "D27",
        "Whether GATE_2_75_COMPOSED_PROBE is retained as a recording stage "
        "now that it terminates nothing, or dropped from the sequence",
        "Retain. It is the only pre-selection measurement of D(B<-A) and "
        "D(A<-B) on 192 topics, it records whether the A arm sits where "
        "Delta_R's positive direction is compressed BEFORE any reference is "
        "chosen, and its stand-in cells are a structural-risk record of the "
        "slot-and-order classes Gate 4 measures. It costs 12,096 rows per "
        "replication and decides nothing. Dropping it is a change to §18's "
        "sequence with no implementation here",
        admissible_values=(),
        unimplemented_alternatives=("drop_the_probe_stage",),
        blocks_stages=(_REGISTERED_STAGE,)),
)

#: v6 decisions withdrawn in v7, with the reason. Not registered, not
#: closeable, and not silently renumbered around.
WITHDRAWN_DECISION_IDS: dict[str, str] = {
    "D23": "what the Gate-2.75 residual allowance MEANS. It parameterised a "
           "projected-interval verdict against an absolute band; v7 A1 "
           "withdraws the verdict and no function reads the reading",
    "D26": "how large the Gate-2.75 residual allowance IS. Same consumer, "
           "same withdrawal; the measured 0.0142 remains on v6's record as "
           "development evidence about the authored sub-split",
}

DECISIONS: dict[str, Decision] = {d.id: d for d in _REGISTERED}
DECISION_IDS: tuple[str, ...] = tuple(DECISIONS)

#: §34 says nineteen for v5, v6 added eight, v7 withdraws two of those and
#: adds one; this asserts it rather than describing it, because a summary
#: that drifts from the list is exactly the defect §33 asks for.
V5_DECISION_IDS: tuple[str, ...] = tuple(f"D{i}" for i in range(19))
V6_DECISION_IDS: tuple[str, ...] = ("D19", "D20", "D21", "D22", "D24", "D25")
V7_DECISION_IDS: tuple[str, ...] = ("D27",)
READINESS_MEMO_IDS: dict[str, str] = {
    "D19": "R1", "D20": "R2", "D21": "R3", "D22": "R4", "D24": "R6"}
assert len(DECISIONS) == 26, (
    f"§34 registers D0-D18, v6's D19-D22, D24, D25 and v7's D27; "
    f"this module carries {len(DECISIONS)}")
assert DECISION_IDS == (tuple(f"D{i}" for i in range(23))
                        + ("D24", "D25", "D27"))
assert not set(WITHDRAWN_DECISION_IDS) & set(DECISIONS)
# An alternative is either executable or recorded as not; it is never both,
# because `choice()` refuses an admissible value it has no branch for and a
# researcher must not be offered a value the study cannot run.
for _d in _REGISTERED:
    assert not (set(_d.unimplemented_alternatives)
                & set(_d.admissible_values)), _d.id
assert set(READINESS_MEMO_IDS) <= set(V6_DECISION_IDS)


def open_decisions() -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items() if not d.resolved)


def closed_decisions() -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items() if d.resolved)


def is_closed(decision_id: str) -> bool:
    return _get(decision_id).resolved


def _get(decision_id: str) -> Decision:
    try:
        return DECISIONS[decision_id]
    except KeyError as exc:
        raise ProtocolError(
            f"{decision_id!r} is not a registered §34 decision; registered: "
            f"{DECISION_IDS}") from exc


def value_of(decision_id: str) -> Any:
    """The closed value, or ``UNRESOLVED``. Never a standing proposal."""
    return _get(decision_id).value


def choice(decision_id: str, options: Mapping[Any, Any], *,
           where: str) -> Any:
    """Select the behaviour a closed decision names, or refuse.

    ``options`` maps each admissible value to what the implementation does
    under it, so both branches exist in the source and neither is reachable
    while the decision is open. A decision that offers a value this call has
    no branch for is a defect here, not a researcher error, and it says so.
    """
    decision = _get(decision_id)
    if decision.admissible_values:
        missing = [v for v in decision.admissible_values if v not in options]
        if missing:
            raise ProtocolError(
                f"{where}: §34 {decision_id} admits {missing} and this call "
                "supplies no behaviour for them; both branches of a "
                "researcher decision must exist in the source")
    if not decision.resolved:
        raise DecisionOpenError(
            f"{where}: §34 {decision_id} is UNRESOLVED --- "
            f"{decision.question}. The preregistration's standing proposal is "
            f"{decision.standing_proposal!r} and a standing proposal is not a "
            f"value. Close it with decisions.close({decision_id!r}, ...) and "
            "record it in the signed registration manifest; §18 stage 1 "
            f"returns {REGISTRATION_INCOMPLETE} until then")
    return options[decision.value]


def decisions_blocking_stage(stage: str) -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items()
                 if stage in d.blocks_stages and not d.resolved)


def decisions_blocking_call(call: str) -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items()
                 if call in d.blocks_calls and not d.resolved)


def assert_decisions_closed(ids: Sequence[str], *, where: str) -> None:
    still_open = [i for i in ids if not _get(i).resolved]
    if still_open:
        raise DecisionOpenError(
            f"{where}: these §34 decisions are UNRESOLVED and this path "
            f"depends on them: {still_open}. §34 requires every one closed, "
            "with its evidence, in the signed registration manifest before "
            "stage 1 can pass")


def assert_decisions_closed_for_stage(stage: str) -> None:
    """§18: a stage may not run while a decision it depends on is open.

    Stage 1 depends on **all** of them, so this is also the executable form
    of ``REGISTRATION_INCOMPLETE``.
    """
    blocking = decisions_blocking_stage(stage)
    if blocking:
        raise DecisionOpenError(
            f"{stage} may not run: §34 decisions {list(blocking)} are "
            f"UNRESOLVED. §18 stage 1 records {REGISTRATION_INCOMPLETE}")


def assert_decisions_closed_for(call: str) -> None:
    blocking = decisions_blocking_call(call)
    if blocking:
        raise DecisionOpenError(
            f"{call} depends on §34 decisions {list(blocking)}, which are "
            "UNRESOLVED")


def _assert_in_range(decision: Decision, value: Any) -> None:
    """A numeric decision's closure lies in its registered interval."""
    if decision.admissible_range is None:
        return
    low, high = decision.admissible_range
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolError(
            f"{decision.id} is a numeric decision and admits a number in "
            f"[{low}, {high}); got {value!r}")
    if not low <= float(value) < high:
        raise ProtocolError(
            f"{decision.id} admits a number in [{low}, {high}); got {value}")


def close(decision_id: str, value: Any, *, evidence: str, decided_by: str,
          decided_on: str) -> Decision:
    """Record a researcher's closure. Write-once, and never a default.

    The four arguments are all required because §34 requires the decision
    *and its evidence* in the manifest: a closure with no evidence is a
    default with a signature on it.
    """
    decision = _get(decision_id)
    if decision.resolved:
        raise ProtocolError(
            f"{decision_id} is already closed at {decision.value!r} by "
            f"{decision.decided_by!r}; a decision is closed once and a change "
            "is an amendment under §32, not a re-close")
    if decision.admissible_values and value not in decision.admissible_values:
        raise ProtocolError(
            f"{decision_id} admits {decision.admissible_values}; got "
            f"{value!r}")
    _assert_in_range(decision, value)
    if decision.unimplemented_alternatives and \
            value in decision.unimplemented_alternatives:
        raise ProtocolError(
            f"{decision_id} records {value!r} among its unimplemented "
            "alternatives: the implementation carries no branch for it, so "
            "closing there would register a study the code cannot run. "
            "Adopting it is a §32 amendment with an implementation, not a "
            "closure")
    if not (evidence and decided_by and decided_on):
        raise ProtocolError(
            f"closing {decision_id} requires the evidence, who took it and "
            "when; §34 binds all three into the registration manifest")
    updated = replace(decision, value=value, evidence=evidence,
                      decided_by=decided_by, decided_on=decided_on)
    DECISIONS[decision_id] = updated
    return updated


def override_for_testing(decision_id: str, value: Any) -> Decision:
    """Force a decision to a value, bypassing write-once. **Tests only.**

    It exists for one job: keeping the branch the researcher did *not* adopt
    executed by a test rather than merely present in the source. A retained
    alternative nobody runs rots, and the first time anyone needs it --- to
    reproduce a historical replication, or to see what the refused option
    would have done --- it does not work.

    It cannot affect a run. A run's closures come from ``RECORD_PATH``, this
    writes nothing to it, and ``reopen_all_for_testing`` puts the registry
    back to what the record says.
    """
    decision = _get(decision_id)
    if decision.admissible_values and value not in decision.admissible_values:
        raise ProtocolError(
            f"{decision_id} admits {decision.admissible_values}; got "
            f"{value!r}")
    _assert_in_range(decision, value)
    DECISIONS[decision_id] = replace(
        decision, value=value, evidence="OVERRIDDEN FOR A TEST",
        decided_by="test", decided_on="test")
    return DECISIONS[decision_id]


def reopen_all_for_testing() -> None:
    """Restore the registry to **the recorded state**, not to a blank one.

    Exists so that a test can exercise a closed-decision path and leave the
    module as it found it. What it found it in is the state ``RECORD_PATH``
    describes: a decision the researcher has taken is taken, and a fixture
    that reopened it would let a test assert behaviour the protocol no longer
    admits. Decisions the record does not carry go back to ``UNRESOLVED``.
    """
    for key, decision in list(DECISIONS.items()):
        DECISIONS[key] = replace(decision, value=UNRESOLVED, evidence=None,
                                 decided_by=None, decided_on=None)
    apply_recorded_closures()


# ------------------------------------------------------ the durable record

#: Repository-relative, so the manifest can name it and a reader can find it.
RECORD_RELPATH = "dci1/reports/dci1v7/researcher_decisions.json"
RECORD_PATH = Path(__file__).resolve().parents[3] / "reports" / "dci1v7" / \
    "researcher_decisions.json"


def _read_record(path: Path | str | None = None) -> dict[str, Any]:
    path = Path(path) if path is not None else RECORD_PATH
    if not path.exists():
        return {"closures": [], "source": None, "recorded_on": None,
                "path": str(path), "present": False}
    payload = json.loads(path.read_text())
    closures = payload.get("closures")
    if not isinstance(closures, list):
        raise ProtocolError(
            f"{path}: the researcher-decision record must carry a "
            "'closures' list; a record whose shape is wrong is not a record")
    return {**payload, "path": str(path), "present": True}


def read_record(path: Path | str | None = None) -> dict[str, Any]:
    """The whole record document. ``open_items`` reads its own section."""
    return _read_record(path)


def recorded_closures(path: Path | str | None = None
                      ) -> tuple[dict[str, Any], ...]:
    """Every closure the record carries, validated but not yet applied."""
    record = _read_record(path)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in record["closures"]:
        for field in ("id", "value", "evidence", "decided_by", "decided_on"):
            if not str(entry.get(field, "")).strip():
                raise ProtocolError(
                    f"{record['path']}: a recorded closure needs {field}; §34 "
                    "binds the decision AND its evidence, and an entry "
                    "missing one is a default with a filename on it")
        decision = _get(entry["id"])
        if entry["id"] in seen:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} is recorded twice; a change "
                "to a closed decision is a §32 amendment, not a second entry")
        seen.add(entry["id"])
        if decision.admissible_values and \
                entry["value"] not in decision.admissible_values:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} admits "
                f"{decision.admissible_values} and the record says "
                f"{entry['value']!r}")
        out.append(dict(entry))
    return tuple(out)


def apply_recorded_closures(path: Path | str | None = None) -> tuple[str, ...]:
    """Apply the record to the registry. Idempotent, and never a downgrade.

    Re-applying an identical closure is a no-op rather than the write-once
    refusal ``close`` raises, because importing this module twice is not a
    researcher taking a decision twice. A record that *disagrees* with a
    closure already in force is refused: that is an amendment and it does not
    happen by a file changing under a running process.
    """
    applied: list[str] = []
    for entry in recorded_closures(path):
        current = _get(entry["id"])
        if current.resolved:
            if current.value != entry["value"]:
                raise ProtocolError(
                    f"{entry['id']} is in force at {current.value!r} and the "
                    f"record says {entry['value']!r}; a change to a closed "
                    "decision is a §32 amendment")
            continue
        close(entry["id"], entry["value"], evidence=entry["evidence"],
              decided_by=entry["decided_by"], decided_on=entry["decided_on"])
        applied.append(entry["id"])
    return tuple(applied)


def recorded_spec(decision_id: str, path: Path | str | None = None
                  ) -> dict[str, Any] | None:
    """The registered payload a closure carries beyond its value.

    Some decisions select a *value* and some select a value **and the
    parameters that value has no room for**. §34 D17's ``floor`` is the case
    that forced this: the admissible values are ``no_floor`` and ``floor``,
    and ``floor`` alone says nothing about which quantity is bounded, by what
    number, under which semantics, or on what derivation. Putting those in
    the code would be exactly the move §34 exists to stop, so they live in the
    record beside the closure that requires them, and the module that applies
    the floor reads them from here rather than from a literal.

    Returns ``None`` when the decision is not recorded or carries no spec ---
    which is most of them, and is not an error.
    """
    _get(decision_id)
    for entry in recorded_closures(path):
        if entry["id"] == decision_id:
            spec = entry.get("spec")
            return dict(spec) if isinstance(spec, Mapping) else None
    return None


def record_hash(path: Path | str | None = None) -> str | None:
    """The record's content identity, for the registration manifest.

    Over the closures **and** the open-item resolutions, because both are
    researcher acts recorded in the same file and a hash that covered only
    half of it would let U2's resolution change under a signature that did
    not move.
    """
    record = _read_record(path)
    if not record["present"]:
        return None
    return sha_obj({"path": RECORD_RELPATH, "closures": record["closures"],
                    "open_items": record.get("open_items") or []})


def non_adopted_alternatives() -> dict[str, list[Any]]:
    """Per closed decision, the branches the researcher did **not** take.

    ``choice()`` still carries every branch, because a study has to be able
    to show what it could have done. This names them as not-adopted so that
    a reader of the manifest cannot mistake a retained branch for a live
    scientific alternative.
    """
    return {k: [v for v in d.admissible_values if v != d.value]
            for k, d in DECISIONS.items()
            if d.resolved and d.admissible_values}


def record_payload(path: Path | str | None = None) -> dict[str, Any]:
    record = _read_record(path)
    return {
        "path": RECORD_RELPATH,
        "present": record["present"],
        "hash": record_hash(path),
        "recorded_on": record.get("recorded_on"),
        "source": record.get("source"),
        "closed_here": [e["id"] for e in record["closures"]],
        "resolved_here": [e["id"] for e in (record.get("open_items") or [])],
    }


def registration_payload() -> dict[str, Any]:
    """What §18 stage 1 binds into the signed registration manifest."""
    return {
        "section": "§34",
        "n_decisions": len(DECISIONS),
        "all_closed": not open_decisions(),
        "open": list(open_decisions()),
        "record": record_payload(),
        "non_adopted_alternatives": non_adopted_alternatives(),
        "decisions": [d.as_dict() for d in DECISIONS.values()],
    }


#: Applied at import: a closure the researcher recorded is in force, and a
#: module that reported it open would be reporting a decision nobody may take
#: again as one still to take.
apply_recorded_closures()
