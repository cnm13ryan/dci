"""The claim ladder, §17.6's joint readings, and the corrected L4 (§3.2, §17).

Three estimands answer the study's third question --- ``Delta_R`` against
same-form controls, ``Delta_near`` against near-form ones, and
``delta_difficulty`` against a fitted relation --- and a fourth, ``Xi``,
decides how any of them may be worded. All of that is decided *before* a
number is seen, so ``joint_reading`` is a lookup rather than a judgement.

**Adding a route to L3 does not make a positive result easier to reach.** In
every row where two estimands disagree, **neither** claim is emitted:
agreement is necessary, so v5's ladder is strictly harder to climb than
v4r4's, not easier.

**L4 is the correction of v4r4's defect and it is per named member.** v4r4's
``emit_l4`` received ``per_configuration: Mapping[configuration,
Sequence[level]]`` and compared the **sets** of levels reached; its caller
built that input as ``[s["claim_level"] for s in statements if emitted]``,
discarding member identity before the emitter could see it. For
`gemma-3n-e4b-it` both configurations reached L1 --- but ``D(A<-B)`` reached
it in ``outcome_first`` only and ``D(B<-A)`` in ``outcome_second`` only --- so
the sets matched and the emitted L4 asserted replication for the replication
that least replicates. ``emit_l4a`` takes a mapping of mappings, is
keyword-only, and validates its shape, so the level-sequence call site cannot
be written at all. v4r4's own emitted field stays invalidated and is **not**
recomputed inside v4r4: the fix is prospective and repairs nothing
retrospectively.

**``emit_l4b`` is new**, reads F11, and emits per named order contrast. L4a
and L4b are complementary and neither implies the other: a member can
replicate its classification across configurations while its magnitude differs
by a resolved amount, and it can fail to replicate while the order contrast is
unresolved. Both are reported.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions

__all__ = ["Interval", "ClaimError", "position_status", "delta_r_reading",
           "l3_vacuity_agrees",
           "delta_near_reading", "delta_difficulty_reading", "xi_gate",
           "joint_reading", "tier_reading", "emit_l1", "emit_l2", "emit_l3",
           "emit_l4a", "emit_l4b", "assert_no_l5_emitter", "LEVEL_MEMBERS",
           "REQUIRED_FIELDS", "assert_statement_complete",
           "l3c_requires_near_form", "l3c_disposition",
           "assert_l3c_scope", "precondition_key",
           "CONFIGURATION_SCOPE", "CONFIGURATION_SCOPE_DERIVATION",
           "assert_configuration_scope"]


#: **L4a is within one replication, and the registered text determines it.**
#:
#: The question is real: §11.1's glossary defines a configuration as the tuple
#: *(model checkpoint, position of the outcome constraint)*, while
#: ``protocol/constants.CONFIGURATIONS`` is ``(outcome_first,
#: outcome_second)`` --- position only. Read naively, L4a's gate ("every
#: registered configuration was analysed") could mean the two positions of one
#: model or all four models times two positions, and those license different
#: claims. Four registered passages settle it, and none of them is code:
#:
#: 1. **§15, first paragraph.** "Families are declared per configuration,
#:    meaning per (model, position of the outcome constraint) --- with one
#:    exception, F11, which is declared **across the two configurations of one
#:    model**. **There is no cross-model multiplicity family, because this
#:    protocol licenses no pooled-across-model estimand.**" So in this
#:    protocol the phrase "across configurations", applied to a family or a
#:    contrast, names the two positions of one model.
#: 2. **§3.2's L4b row** gates on "Both configurations analysed" and reads
#:    F11, which §15 has just declared across the two configurations of one
#:    model. L4a and L4b are registered as complementary and indexed the same
#:    way, so L4a's "every registered configuration" is that same pair.
#: 3. **§11.1.** "There are two configurations per model", and the analysis
#:    runs per replication --- so the model index is the ``ModelTree`` the
#:    analysis is running under, and the tuple that varies inside it is the
#:    position. ``CONFIGURATIONS`` and the glossary agree once the model index
#:    is read as the tree rather than as an element of the tuple.
#: 4. **§6.1 and L5.** Replications are "each analysed separately, each a
#:    moderator level and never pooled", no cross-model scalar carries a
#:    claim, and L5 --- generalisation --- is never licensed by this design.
#:    A cross-model L4a would be a claim §6.1 forbids and a level L5
#:    permanently withholds.
#:
#: §19's registered L4a regression test is the same reading made executable:
#: it reproduces v4r4's ``gemma-3n-e4b-it`` pattern, which is a pattern
#: **within one model** across its two positions.
#:
#: This is therefore a resolved definitional item and **not** a researcher
#: decision. What v6 must still register explicitly is the wording of a
#: study-level statement when replications differ --- see §34 D22.
CONFIGURATION_SCOPE = "within_replication"
CONFIGURATION_SCOPE_DERIVATION = (
    "§15 declares every family per configuration and F11 across the two "
    "configurations of ONE model, and states that there is no cross-model "
    "multiplicity family; §3.2's L4b gate says 'both configurations'; §11.1 "
    "says there are two configurations per model; §6.1 forbids pooling "
    "across replications and L5 withholds generalisation permanently")


def assert_configuration_scope(configurations=None) -> dict:
    """Refuse an L4a input whose configurations are not one model's two.

    ``emit_l4a`` compares each member's classification across
    ``C.CONFIGURATIONS``. This states, and checks, what that set is allowed to
    be: exactly the two registered outcome positions. A caller that widened it
    to a model-crossing set would be emitting the cross-model replication
    claim §6.1 forbids and L5 permanently withholds, and it would do so
    through a data shape rather than through a rule anybody registered.
    """
    values = tuple(configurations if configurations is not None
                   else C.CONFIGURATIONS)
    if values != tuple(C.CONFIGURATIONS):
        raise ClaimError(
            f"L4a is {CONFIGURATION_SCOPE}: its configurations are the two "
            f"registered outcome positions {tuple(C.CONFIGURATIONS)}, and "
            f"{values} is not that set. {CONFIGURATION_SCOPE_DERIVATION}")
    return {"scope": CONFIGURATION_SCOPE, "configurations": list(values),
            "derivation": CONFIGURATION_SCOPE_DERIVATION}


class ClaimError(ProtocolError):
    """A guarded emitter was reached with its precondition false."""


#: §17.5: one emitter per level, each refusing a member not registered to it.
LEVEL_MEMBERS: dict[str, tuple[str, ...]] = {
    "L1": ("D(B<-A)", "D(A<-B)"),
    "L2": ("Lambda",),
    "L3a": ("Delta_R",), "L3b": ("Delta_R",), "L3c": ("Delta_R",),
    "L3d": ("delta_difficulty",), "L3e": ("delta_difficulty",),
    "L4a": ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "delta_difficulty",
            "Xi"),
    "L4b": C.FAMILY_MEMBERS["F11"],
}

#: §17.5's machine fields. Every emitted statement carries all of them, and
#: **``cell`` is the field v4r4's reports needed and did not carry**: a
#: Delta-type quantity differences two composed cells, and
#: ``D(A<-B)|outcome_first`` and ``D(B<-A)|outcome_first`` are read from
#: *different* cells.
REQUIRED_FIELDS = ("claim_level", "configuration", "cell", "family",
                   "interval_type", "identification_status",
                   "measurement_basis", "difficulty_coordinate",
                   "structural_tier_of_reference_pool", "outcome_position")


@dataclass(frozen=True)
class Interval:
    """One simultaneous interval, with the realised half-width §17.3 reads."""

    member: str
    estimate: float
    lower: float
    upper: float

    @property
    def half_width(self) -> float:
        return (self.upper - self.lower) / 2.0

    def excludes_zero_from_below(self) -> bool:
        return self.lower > 0.0

    def excludes_zero(self) -> bool:
        return self.lower > 0.0 or self.upper < 0.0

    def wholly_inside(self, region: float) -> bool:
        return -region <= self.lower and self.upper <= region

    def meets_precondition(self) -> bool:
        precondition = C.PRECISION_PRECONDITIONS.get(
            _precondition_key(self.member))
        if precondition is None:
            raise ProtocolError(
                f"{self.member} has no registered precision precondition. Xi "
                "deliberately has none: §11.9 registers it as a "
                "direction-only gate, and an unresolved direction is "
                "A_GENERAL_NOT_EXCLUDED, not a comparison against a magnitude "
                "it does not have.")
        return self.half_width <= precondition


def precondition_key(member: str) -> str:
    """§16.2's row for a member. The table is by contrast *shape*.

    ``D`` covers every delivery loss, ``Delta_j`` every per-reference excess,
    and the two F11 rows §16.2 does not name are quoted at ``Ord_A``'s
    precondition, which is what §16.2's note says is done.
    """
    if member.startswith("Ord_"):
        return member if member in C.PRECISION_PRECONDITIONS else "Ord_A"
    if member.startswith("Delta_") and member[6:].isdigit():
        return "Delta_j"
    if member.startswith("D(") and "<-" in member:
        return "Delta_j" if member.startswith("D(B<-R") else "D"
    return member


#: Kept as the private name the rest of this module already used.
_precondition_key = precondition_key


def position_status(outcome_position: int) -> list[str]:
    """§11.4: L1 in the position-shifted configuration is confounded."""
    return [] if outcome_position == 1 else ["POSITION_CONFOUNDED"]


def delta_r_reading(interval: Interval) -> dict[str, Any]:
    """§3.2's L3a / L3b / L3c geometry against the two memo thresholds."""
    if interval.member != "Delta_R":
        raise ClaimError(f"{interval.member} is not Delta_R")
    generic = C.DELTA_R_GENERIC_THRESHOLD
    specific = C.DELTA_R_PAIR_SPECIFIC_THRESHOLD
    levels: list[str] = []
    markers: list[str] = []
    if not interval.meets_precondition():
        markers.append("INSUFFICIENT_PRECISION")
        return {"levels": [], "markers": markers,
                "direction_resolved": interval.excludes_zero_from_below()}
    if interval.lower > generic:
        levels.append("L3a")
        if interval.lower > specific:
            levels.append("L3b")
        elif interval.upper > specific:
            markers.append("INDETERMINATE@0.25")
    elif interval.upper < generic:
        levels.append("L3c")
    else:
        markers.append("INDETERMINATE@0.10")
    return {"levels": levels, "markers": markers,
            "direction_resolved": interval.excludes_zero_from_below()}


def delta_near_reading(interval: Interval | None) -> dict[str, Any]:
    """§11.9: Delta_near carries the 0.10 threshold and **not** the 0.25.

    The memo's 0.25 is defined for a matched-reference contrast and is not
    transferred to a different reference tier. The reading is three-valued ---
    above, below, or spanning the generic-load threshold --- because §17.6's
    second table is a comparison of classifications and not of magnitudes.
    """
    if interval is None:
        return {"classification": None, "markers": [],
                "statuses": ["NEAR_FORM_ARM_NOT_AVAILABLE"]}
    if interval.member != "Delta_near":
        raise ClaimError(f"{interval.member} is not Delta_near")
    generic = C.DELTA_R_GENERIC_THRESHOLD
    if not interval.meets_precondition():
        return {"classification": None, "markers": ["INSUFFICIENT_PRECISION"],
                "statuses": []}
    if interval.lower > generic:
        classification = "above"
    elif interval.upper < generic:
        classification = "below"
    else:
        classification = "indeterminate"
    return {"classification": classification, "markers": [], "statuses": []}


def delta_difficulty_reading(interval: Interval | None,
                             support: Mapping[str, Any]) -> dict[str, Any]:
    """§3.2's L3d / L3e, gated on §13.13's support.

    ``delta_difficulty`` licenses a DIRECTION claim and an EQUIVALENCE claim
    and no pair-specific claim at any magnitude. The memo's 0.25 was defined
    for a difference between two observed losses; this quantity differences an
    observed loss against a fitted prediction, and transferring the number
    would be inventing a threshold in someone else's provenance (§11.9).

    ``interval`` is ``None`` when the member is not identified at all --- the
    spectrum arm was not admitted, so §13.12's exhaustion dropped it. §17.6's
    fifth row registers that case: *"support fails ...
    `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`; the local reading stands alone with
    that status; **L3a/L3b/L3c only**"*. The support check therefore runs
    first, because with no fit there is no interval to name.
    """
    if not support.get("holds"):
        return {"levels": [], "markers": [],
                "statuses": ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"],
                "note": ("the fit extrapolates to A; the point estimate is "
                         "descriptive and is not a null")}
    if interval is None:
        raise ClaimError(
            "delta_difficulty has no interval and the support says it holds; "
            "one of the two is wrong and the reading is not defined")
    if interval.member != "delta_difficulty":
        raise ClaimError(f"{interval.member} is not delta_difficulty")
    if not interval.meets_precondition():
        return {"levels": [], "markers": ["INSUFFICIENT_PRECISION"],
                "statuses": [],
                "direction_resolved": interval.excludes_zero_from_below()}
    levels: list[str] = []
    if interval.excludes_zero_from_below():
        levels.append("L3d")
    elif interval.wholly_inside(C.EQUIVALENCE_REGION):
        levels.append("L3e")
    return {"levels": levels, "markers": [], "statuses": []}


def xi_gate(interval: Interval) -> dict[str, Any]:
    """§3.2: Xi decides the *wording*, not whether a statement is emitted."""
    if interval.member != "Xi":
        raise ClaimError(f"{interval.member} is not Xi")
    specific = interval.excludes_zero_from_below()
    return {
        "outcome_specific": specific,
        "statuses": [] if specific else ["A_GENERAL_NOT_EXCLUDED"],
        "wording": ("the excess is specific to the outcome B" if specific else
                    "the excess is not distinguishable from A being generally "
                    "disruptive as a companion"),
    }


def tier_reading(delta_r: Interval, delta_near: Interval | None
                 ) -> dict[str, Any]:
    """§17.6's second table: Delta_R against Delta_near.

    A ``Delta_R ~ 0`` with ``Delta_near > 0.10`` is **not** emitted as L3c but
    as a registered disagreement. That is the mitigation the red team's R1
    asks for: if the mechanism by which A damages B is a property of the
    *form*, every Tier-1 control reproduces it and Delta_R goes to zero for a
    reason that belongs to the design rather than to A --- and L3c is the
    source memo's refutation verdict.

    §34 D18 asks whether the near-form arm should be a **precondition** of
    emitting L3c at all. It is not decided here; ``l3c_requires_near_form``
    refuses until it is.
    """
    local = delta_r_reading(delta_r)
    near = delta_near_reading(delta_near)
    local_class = ("above" if "L3a" in local["levels"] else
                   "below" if "L3c" in local["levels"] else "indeterminate")
    if near["classification"] is None:
        return {"agree": None, "local": local_class,
                "near": None, "statuses": near["statuses"],
                "note": "Delta_R's reading stands alone with that status"}
    agree = local_class == near["classification"]
    statuses: list[str] = []
    if local_class in ("above", "below") and \
            near["classification"] in ("above", "below") and not agree:
        statuses.append("LOCAL_TIER_DISAGREE")
    return {"agree": agree, "local": local_class,
            "near": near["classification"], "statuses": statuses,
            "reading": (
                "A exceeds same-form markers but not other exact counts: the "
                "excess is specific relative to markers and not relative to "
                "the operator"
                if local_class == "above" and near["classification"] == "below"
                else
                "the marker controls resemble A unusually closely, which is "
                "what a same-form control is supposed to do; the near-form "
                "comparison is the informative one"
                if local_class == "below" and near["classification"] == "above"
                else
                "the excess, or its absence, is not a property of the "
                "predicate form")}


def l3c_requires_near_form() -> bool:
    """§34 D18: is the near-form arm a precondition of the **strong** L3c?

    L3c is the source memo's refutation verdict --- *an upper bound below 0.10
    supports H2 and refutes the pairwise framing entirely* --- and v5's core
    pool is chosen to resemble A closely enough that ``Delta_R ~ 0`` is a
    plausible consequence of the **design**. The near-form arm is what
    distinguishes the two, and §34 D1 lists dropping it as a compute option.

    **Closed at ``precondition``.** The researcher took the strong version:
    the strong conclusion --- *no pair-specific excess* --- requires the arm,
    and a same-form Tier-1 pool alone licenses only the narrower statement
    that there is no excess relative to same-form exact-count companions. The
    ``not_a_precondition`` branch is retained and is **not** a live v5
    alternative: under it a replication with no near-form arm emitted the
    strong conclusion with §17.6's sentence attached as a qualifier, which is
    exactly what R1 says a reader will not hear.
    """
    return decisions.choice("D18", {"not_a_precondition": False,
                                    "precondition": True},
                            where="analysis.claims.l3c_requires_near_form")


def l3c_disposition(*, near_form_available: bool,
                    delta_near: "Interval | None") -> dict[str, Any]:
    """§34 D18 applied to one L3c that is otherwise licensed.

    **What the disposition returns is a SCOPE, not a permission.** §34 D18 is
    closed at ``precondition`` and the researcher's words fix what that gates:

    > A strong L3c conclusion such as "no pair-specific excess" requires the
    > near-form arm. Same-form Tier-1 references alone may only justify the
    > narrower conclusion: no excess relative to same-form exact-count
    > companions.

    So the arm decides **which of two registered conclusions** is licensed,
    and the scope travels on the statement:

    * arm present --- scope ``strong``. The refutation verdict is available.
    * arm absent, D18 at ``precondition`` --- scope ``same_form_only``. The
      narrow conclusion is emitted, ``strong`` is unreachable, and the
      statement says so in its own text rather than in a footnote.
    * arm absent, D18 at ``not_a_precondition`` (**not adopted**) --- scope
      ``strong`` with §17.6's sentence attached as a qualifier. Retained so
      the branch v5 refused is visible, and reachable only by reopening D18.

    **The precondition is the arm's existence, not its verdict.** It is met
    when the arm ran and produced a Delta_near interval. Requiring a
    *classified* Delta_near instead would let the precision of a secondary
    quantity decide which conclusion may be drawn, which is a different rule
    and one no section registers.

    The decision is consulted **only where the modes differ** --- an L3c with
    the arm present is ``strong`` either way --- so a replication that
    retained the near-form arm is not blocked by a decision that would change
    nothing for it.
    """
    if near_form_available and delta_near is not None:
        return {"emit": True, "mode": "arm_present",
                "scope": "strong",
                "consulted_d18": False,
                "statuses": [],
                "scope_sentence": C.L3C_STRONG_SENTENCE,
                "qualifier": None}
    required = l3c_requires_near_form()
    if required:
        return {"emit": True, "mode": "precondition",
                "scope": "same_form_only",
                "consulted_d18": True,
                "statuses": ["NEAR_FORM_ARM_NOT_AVAILABLE",
                             "L3C_STRONG_CONCLUSION_WITHHELD"],
                "scope_sentence": C.L3C_SAME_FORM_ONLY_SENTENCE,
                "reason": (
                    "§34 D18 was closed at 'precondition': L3c is the source "
                    "memo's refutation verdict and v5's core reference pool "
                    "is same-form with A, so an L3c with no near-form "
                    "comparison cannot distinguish 'A is not special' from "
                    "'the excess is a property of the exact-count form'. The "
                    "narrow conclusion is emitted, the strong one is not, and "
                    "Delta_R is reported with its interval either way"),
                "qualifier": C.L3C_WITHOUT_NEAR_FORM_SENTENCE}
    return {"emit": True, "mode": "not_a_precondition",
            "scope": "strong",
            "consulted_d18": True,
            "statuses": ["NEAR_FORM_ARM_NOT_AVAILABLE"],
            "scope_sentence": C.L3C_STRONG_SENTENCE,
            "qualifier": C.L3C_WITHOUT_NEAR_FORM_SENTENCE}


def assert_l3c_scope(statement: Mapping[str, Any], *,
                     near_form_available: bool, where: str) -> None:
    """§34 D18's invariant: no strong L3c without the near-form arm.

    Checked on the emitted statement rather than trusted from the emitter,
    because the emitter is one call site and the freeze, the final report and
    any future renderer are others. A study without the arm must be *unable*
    to emit the strong conclusion, and this is where that is unable rather
    than merely not done.
    """
    if statement.get("claim_level") != "L3c" or not statement.get("emitted"):
        return
    scope = statement.get("l3c_scope")
    if scope not in C.L3C_SCOPES:
        raise ClaimError(
            f"{where}: an emitted L3c carries one of {C.L3C_SCOPES} and this "
            f"one carries {scope!r}; §34 D18 makes the scope part of the "
            "statement")
    if scope == "strong" and not near_form_available and \
            l3c_requires_near_form():
        raise ClaimError(
            f"{where}: a strong L3c --- the refutation verdict --- was "
            "emitted with no near-form arm. §34 D18 is closed at "
            "'precondition': the same-form pool licenses "
            f"{C.L3C_SAME_FORM_ONLY_SENTENCE!r} and nothing stronger")


def joint_reading(*, delta_r: Interval, delta_difficulty: Interval | None,
                  xi: Interval, support: Mapping[str, Any],
                  delta_near: Interval | None = None) -> dict[str, Any]:
    """§17.6's two tables, applied in advance of any number.

    The mixed rows of either table --- a local excess the other lens does not
    see, or the reverse --- emit **neither** claim and record
    ``LOCAL_AND_SPECTRUM_DISAGREE`` or ``LOCAL_TIER_DISAGREE``. A disagreement
    is a result, is reported as one with both quantities and the diagnostics
    that distinguish them, and never resolves toward whichever estimand
    crossed a threshold.
    """
    local = delta_r_reading(delta_r)
    spectrum = delta_difficulty_reading(delta_difficulty, support)
    gate = xi_gate(xi)
    tier = tier_reading(delta_r, delta_near)

    statuses = sorted(set(
        spectrum.get("statuses", []) + gate["statuses"]
        + tier.get("statuses", [])
        # §28.2: attached to every L3 statement, always. v5's analogue of
        # v4r4's COMPANION_CLASS_NOT_MATCHED, pointing the opposite way.
        + ["REFERENCE_POOL_SAME_FORM"]))
    markers = sorted(set(local["markers"] + spectrum["markers"]))

    local_positive = "L3a" in local["levels"]
    local_null = "L3c" in local["levels"]
    spectrum_positive = "L3d" in spectrum["levels"]
    spectrum_null = "L3e" in spectrum["levels"]

    if "LOCAL_TIER_DISAGREE" in tier.get("statuses", []):
        return {
            "levels": [], "markers": markers,
            "identification_statuses": sorted(set(statuses)),
            "row": "local tier disagreement",
            "reading": tier["reading"],
            "tier_reading": tier,
            "both_reported": {"Delta_R": vars(delta_r),
                              "Delta_near": vars(delta_near)},
        }

    disagree = ((local_positive and spectrum_null)
                or (local_null and spectrum_positive))
    if disagree:
        statuses.append("LOCAL_AND_SPECTRUM_DISAGREE")
        return {
            "levels": [], "markers": markers,
            "identification_statuses": sorted(set(statuses)),
            "row": ("local excess, spectrum null" if local_positive else
                    "local null, spectrum excess"),
            "reading": (
                "the three core references were unrepresentative of the "
                "difficulty relation" if local_positive else
                "the core references resemble A unusually closely relative to "
                "the relation"),
            "tier_reading": tier,
            "both_reported": {
                "Delta_R": vars(delta_r),
                "delta_difficulty": (vars(delta_difficulty)
                                     if delta_difficulty is not None else None)},
        }

    levels = sorted(set(local["levels"] + spectrum["levels"]))
    return {
        "levels": levels, "markers": markers,
        "identification_statuses": sorted(set(statuses)),
        "row": ("both null" if (local_null and spectrum_null) else
                "both positive" if (local_positive and spectrum_positive) else
                "partially resolved"),
        "outcome_specific": gate["outcome_specific"],
        "wording": gate["wording"],
        "tier_reading": tier,
        "reference_pool_sentence": C.REFERENCE_POOL_SAME_FORM_SENTENCE,
    }


def coordinate_agreement(*, delta_difficulty: Interval | None,
                         support: Mapping[str, Any],
                         secondary: Interval | None,
                         secondary_support: Mapping[str, Any] | None
                         ) -> dict[str, Any]:
    """§17.6's coordinate-agreement rule, closed by §34 D14.

    *"The §11.8 fit is computed on the registered instructed-compliance
    coordinate and, separately, on raw solo compliance. When the two give
    different L3d/L3e classifications the statement carries
    `DIFFICULTY_COORDINATE_DEPENDENT` and both readings are reported; the
    registered coordinate decides which classification is emitted and the
    secondary decides whether it carries the status."*

    So this returns a **status**, never a level: the primary reading is
    returned untouched and the secondary appears only as the reported
    comparison. That is the whole of what the raw coordinate is licensed to
    do --- §15 registers the raw-coordinate replication among the quantities
    *"reported with marginal intervals only and supporting no claim"*, so it
    has no simultaneous interval, no declared family and no claim of its own.

    ``secondary`` is ``None`` when the replication was not computable, which
    is not a disagreement: with nothing to compare, the status cannot be
    earned and the primary stands alone.
    """
    primary = delta_difficulty_reading(delta_difficulty, support)
    if secondary is None:
        return {"compared": False, "statuses": [],
                "primary_levels": list(primary["levels"]),
                "secondary_levels": None,
                "note": ("no raw-coordinate replication was computable; §17.6 "
                         "compares two classifications and there is one")}
    other = delta_difficulty_reading(
        secondary, secondary_support if secondary_support is not None
        else support)
    mine = [level for level in primary["levels"] if level in ("L3d", "L3e")]
    theirs = [level for level in other["levels"] if level in ("L3d", "L3e")]
    agrees = mine == theirs
    return {
        "compared": True,
        "agrees": agrees,
        "statuses": [] if agrees else ["DIFFICULTY_COORDINATE_DEPENDENT"],
        "primary_levels": mine,
        "secondary_levels": theirs,
        "primary_coordinate": C.DIFFICULTY_COORDINATE,
        "secondary_coordinate": C.SECONDARY_DIFFICULTY_COORDINATE,
        "note": ("the registered coordinate decides the classification; the "
                 "secondary decides only whether the statement carries the "
                 "status"),
    }


def l3_vacuity_agrees(delta_r: Interval, forced: Interval | None) -> bool:
    """§17.4 for L3: do the primary and the recomputation license the same
    claim?

    Agreement is on the *claim* and L3's claim is its sub-level, so the two
    readings are compared and not the two numbers. ``emit_l3`` takes the
    verdict as a boolean; this is the function that forms it, and it was
    missing because F5 had no member with a producer to form it from.
    """
    if forced is None:
        return True
    recoded = Interval("Delta_R", forced.estimate, forced.lower, forced.upper)
    return (delta_r_reading(delta_r)["levels"]
            == delta_r_reading(recoded)["levels"])


def assert_statement_complete(statement: Mapping[str, Any]) -> None:
    """§17.5: every emitted statement carries every machine field.

    Three refusals: a missing field; a withheld claim level; and --- the one
    v4r4's reports needed --- an L1, L2 or L3 statement that does not name the
    **cell** the composed term was read from.
    """
    missing = [f for f in REQUIRED_FIELDS if f not in statement]
    if missing:
        raise ClaimError(f"an emitted statement is missing {missing}")
    if statement["claim_level"] in C.WITHHELD_CLAIM_LEVELS:
        raise ClaimError(f"{statement['claim_level']} is permanently withheld")
    level = str(statement["claim_level"])
    if level.startswith(("L1", "L2", "L3")) and not statement.get("cell"):
        raise ClaimError(
            f"§17.5: an {level} statement names the cell the composed term "
            "was read from. D(A<-B)|outcome_first and D(B<-A)|outcome_first "
            "are read from DIFFERENT cells and a statement that does not say "
            "which is not checkable")


def _base_fields(*, level: str, configuration: str, cell: str,
                 outcome_position: int, measurement_basis: str,
                 statuses: Sequence[str], family: str = C.PRIMARY_FAMILY
                 ) -> dict[str, Any]:
    return {
        "claim_level": level, "configuration": configuration, "cell": cell,
        "family": family, "interval_type": "simultaneous",
        "identification_status": sorted(set(statuses)),
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "structural_tier_of_reference_pool": "same_form_tier_1_and_2",
        "outcome_position": outcome_position,
        "scope_sentence": C.SCOPE_SENTENCE,
    }


def _direction_statuses(interval: Interval, outcome_position: int,
                        extra: Sequence[str] = ()) -> list[str]:
    """§17.3 and §11.4, as statuses on a direction statement.

    A direction claim survives a half-width above the precondition --- §17.3
    withholds equivalence and threshold statements and *"still reports a
    resolved direction if one exists"* --- so ``INSUFFICIENT_PRECISION``
    attaches here rather than suppressing the statement.
    """
    statuses = list(extra) + position_status(outcome_position)
    if not interval.meets_precondition():
        statuses.append("INSUFFICIENT_PRECISION")
    return sorted(set(statuses))


def _vacuity_agrees(primary: Interval, forced: Interval | None,
                    licensed: bool) -> bool:
    """§17.4: the primary and the vacuity-forced recomputation must agree.

    Agreement is on the *claim*, not on the numbers, so it is the licensing
    predicate that is compared.
    """
    if forced is None:
        return True
    return licensed == forced.excludes_zero_from_below()


def _vacuity_qualification(vacuity_gate_binds: bool,
                           forced: Interval | None) -> dict[str, Any]:
    """§17.4's *reporting* half, separate from its licensing half."""
    if not vacuity_gate_binds:
        return {}
    out: dict[str, Any] = {
        "vacuity_qualification": C.VACUITY_QUALIFICATION_SENTENCE,
        "f6_vacuity_gate_binds": True}
    if forced is not None:
        out["partial_identification_bounds"] = [forced.lower, forced.upper]
    return out


def emit_l1(*, configuration: str, cell: str, outcome_position: int,
            measurement_basis: str, member: str, interval: Interval,
            solo_headroom: bool,
            identification_statuses: Sequence[str] = (),
            vacuity_forced: Interval | None = None,
            vacuity_gate_binds: bool = False) -> dict[str, Any]:
    """§3.2 L1: compositional delivery loss exists, for one named D(c <- g)."""
    if member not in LEVEL_MEMBERS["L1"]:
        raise ClaimError(f"{member} is not registered to L1; L1 names "
                         f"{LEVEL_MEMBERS['L1']}")
    licensed = interval.excludes_zero_from_below()
    statuses = _direction_statuses(interval, outcome_position,
                                   identification_statuses)
    statement = {
        **_base_fields(level="L1", configuration=configuration, cell=cell,
                       outcome_position=outcome_position,
                       measurement_basis=measurement_basis,
                       statuses=statuses),
        "member": member,
        "interval": [interval.lower, interval.upper],
        "estimate": interval.estimate, "half_width": interval.half_width,
        **_vacuity_qualification(vacuity_gate_binds, vacuity_forced),
    }
    if not solo_headroom:
        return {**statement, "emitted": False,
                "reason": "§12: the outcome constraint has no solo headroom, "
                          "so the L1 identification gate does not hold"}
    if not _vacuity_agrees(interval, vacuity_forced, licensed):
        return {**statement, "emitted": False,
                "reason": "§17.4: the primary and the vacuity-forced "
                          "recomputation do not license the same claim; the "
                          "axis is unresolved with both bounds",
                "vacuity_forced_interval": [vacuity_forced.lower,
                                            vacuity_forced.upper]}
    if not licensed:
        return {**statement, "emitted": False,
                "reason": f"the F1 simultaneous interval for {member} does "
                          "not have a lower bound above 0"}
    assert_statement_complete(statement)
    return {**statement, "emitted": True,
            "statement": f"composing the two instructions costs {member} a "
                         "delivery loss whose simultaneous interval lies "
                         f"wholly above zero, read from cell {cell}"}


def emit_l2(*, configuration: str, cell: str, outcome_position: int,
            measurement_basis: str, interval: Interval,
            l1_licensed: Mapping[str, bool],
            identification_statuses: Sequence[str] = (),
            vacuity_forced: Interval | None = None,
            vacuity_gate_binds: bool = False) -> dict[str, Any]:
    """§3.2 L2: the loss is directionally asymmetric."""
    if interval.member not in LEVEL_MEMBERS["L2"]:
        raise ClaimError(f"{interval.member} is not registered to L2; L2 "
                         f"names {LEVEL_MEMBERS['L2']}")
    excludes_zero = interval.excludes_zero()
    statuses = _direction_statuses(interval, outcome_position,
                                   identification_statuses)
    statement = {
        **_base_fields(level="L2", configuration=configuration, cell=cell,
                       outcome_position=outcome_position,
                       measurement_basis=measurement_basis,
                       statuses=statuses),
        "member": interval.member,
        "interval": [interval.lower, interval.upper],
        "estimate": interval.estimate, "half_width": interval.half_width,
        "l1_licensed": dict(l1_licensed),
        **_vacuity_qualification(vacuity_gate_binds, vacuity_forced),
    }
    missing = sorted(m for m in LEVEL_MEMBERS["L1"] if not l1_licensed.get(m))
    if missing:
        return {**statement, "emitted": False,
                "reason": f"L2's gate is L1 for both directions and {missing} "
                          "did not reach L1"}
    if not _vacuity_agrees(interval, vacuity_forced, excludes_zero):
        return {**statement, "emitted": False,
                "reason": "§17.4: the primary and the vacuity-forced "
                          "recomputation do not license the same claim",
                "vacuity_forced_interval": [vacuity_forced.lower,
                                            vacuity_forced.upper]}
    if not excludes_zero:
        return {**statement, "emitted": False,
                "reason": "the F1 simultaneous interval for Lambda does not "
                          "exclude 0"}
    assert_statement_complete(statement)
    direction = ("B <- A" if interval.estimate > 0 else "A <- B")
    return {**statement, "emitted": True,
            "statement": "the delivery loss is directionally asymmetric; the "
                         f"larger loss is on {direction}"}


def emit_l3(*, configuration: str, cell: str, outcome_position: int,
            measurement_basis: str, delta_r: Interval,
            delta_difficulty: Interval | None, xi: Interval,
            support: Mapping[str, Any], references_identified: bool,
            delta_near: Interval | None = None,
            near_form_available: bool = True,
            heterogeneity_disagrees: bool = False,
            realised_gaps: Mapping[str, float] | None = None,
            interaction_drift: Sequence[str] = (),
            vacuity_forced_agrees: bool = True,
            coordinate_statuses: Sequence[str] = ()
            ) -> list[dict[str, Any]]:
    """The guarded L3 emitter. One statement per licensed sub-level.

    Every returned statement carries ``REFERENCE_POOL_SAME_FORM`` and §28.2's
    fixed sentence, at every sub-level, without exception: v5's core pool is
    same-form and same-class with A by construction, so its excess is relative
    to companions that are *very* like A, and the reader must be told which
    limitation applies.

    **An L3c carries a registered scope** (§34 D18, closed at
    ``precondition``). With the near-form arm the scope is ``strong`` and the
    statement is the memo's refutation verdict; without it the scope is
    ``same_form_only`` and the statement is the narrower conclusion a
    same-form pool licenses. ``assert_l3c_scope`` re-checks the invariant on
    the built statement, so the strong conclusion is *unreachable* without the
    arm rather than merely not produced here.
    """
    reading = joint_reading(delta_r=delta_r,
                            delta_difficulty=delta_difficulty, xi=xi,
                            support=support, delta_near=delta_near)
    statuses = list(reading["identification_statuses"])
    if not references_identified:
        statuses += ["EXCESS_NOT_IDENTIFIED",
                     "REFERENCE_SUPPORT_NOT_IDENTIFIED"]
    if not near_form_available:
        statuses.append("NEAR_FORM_ARM_NOT_AVAILABLE")
    statuses += list(interaction_drift)
    # §17.6's coordinate-agreement rule (§34 D14). The status rides on the
    # statement; it never changes which level was emitted.
    unregistered = [s for s in coordinate_statuses
                    if s not in C.IDENTIFICATION_STATUSES]
    if unregistered:
        raise ClaimError(
            f"{unregistered} are not registered identification statuses; "
            "§17.6's coordinate rule attaches DIFFICULTY_COORDINATE_DEPENDENT "
            "and nothing else")
    statuses += list(coordinate_statuses)

    if not vacuity_forced_agrees:
        return [{**_base_fields(level="L3", configuration=configuration,
                                cell=cell,
                                outcome_position=outcome_position,
                                measurement_basis=measurement_basis,
                                statuses=statuses),
                 "emitted": False,
                 "reason": ("§17.4: the primary and the vacuity-forced "
                            "recomputation do not license the same claim; the "
                            "axis is unresolved with both bounds")}]

    statements: list[dict[str, Any]] = []
    for level in reading["levels"]:
        if level in ("L3a", "L3b", "L3c") and not references_identified:
            continue
        if level == "L3c":
            disposition = l3c_disposition(
                near_form_available=near_form_available,
                delta_near=delta_near)
        statement = {
            **_base_fields(level=level, configuration=configuration,
                           cell=cell, outcome_position=outcome_position,
                           measurement_basis=measurement_basis,
                           statuses=statuses),
            "emitted": True,
            "reference_pool_sentence": C.REFERENCE_POOL_SAME_FORM_SENTENCE,
            "outcome_specificity_wording": reading.get("wording"),
            "markers": reading["markers"],
            "tier_reading": reading.get("tier_reading"),
        }
        if level == "L3c":
            statement["d18_mode"] = disposition["mode"]
            statement["l3c_scope"] = disposition["scope"]
            statement["l3c_scope_sentence"] = disposition["scope_sentence"]
            statement["identification_status"] = sorted(
                set(statement["identification_status"])
                | set(disposition["statuses"]))
            if disposition["qualifier"]:
                statement["near_form_absent_sentence"] = \
                    disposition["qualifier"]
        if level in ("L3a", "L3b") and heterogeneity_disagrees:
            statement["heterogeneity_qualifier"] = (
                "the three Delta_j intervals do not agree on one side of the "
                "threshold used")
        gaps = {k: v for k, v in (realised_gaps or {}).items()
                if abs(v) > C.REALISED_GAP_QUALIFIER}
        if gaps:
            statement["companion_difficulty_qualifier"] = gaps
        assert_statement_complete(statement)
        if level == "L3c":
            assert_l3c_scope(statement,
                             near_form_available=near_form_available,
                             where=f"emit_l3:{configuration}")
        statements.append(statement)
    if not statements:
        statements.append({
            **_base_fields(level="L3", configuration=configuration, cell=cell,
                           outcome_position=outcome_position,
                           measurement_basis=measurement_basis,
                           statuses=statuses),
            "emitted": False, "markers": reading["markers"],
            "tier_reading": reading.get("tier_reading"),
            "reason": reading.get("reading", "no L3 sub-level is licensed"),
        })
    return statements


def emit_l4a(*, per_member: Mapping[str, Mapping[str, str | None]],
             measurement_basis: str,
             identification_statuses: Sequence[str] = ()) -> dict[str, Any]:
    """§3.2 L4a: the same classification, **for the named member**, everywhere.

    ``per_member`` maps each registered member name to a mapping from
    configuration to that member's classification in that configuration, or
    ``None`` where the member reached no level. L4a is licensed iff:

    1. every registered configuration appears for every member;
    2. at least one member reached a classification in at least one
       configuration;
    3. **for every member, the classification is identical across every
       registered configuration.**

    A member reaching a level in one configuration and not the other makes
    condition 3 false and L4a is not emitted; the registered reading is
    §28.1's *Configuration dependence*, and the reported table is the
    per-member classification map itself.

    The parameter is keyword-only and its value is validated as a mapping of
    mappings, so **no code path can call an L4 emitter with a bare sequence of
    levels** --- which is the shape that produced v4r4's defect.
    """
    if not isinstance(per_member, Mapping):
        raise ClaimError(
            "emit_l4a takes a mapping of member -> configuration -> "
            "classification. v4r4's emitter took a mapping of configuration "
            "-> sequence of levels and compared the SETS, and its caller had "
            "already discarded member identity; that shape is not callable "
            "here")
    for member, by_configuration in per_member.items():
        if member not in LEVEL_MEMBERS["L4a"]:
            raise ClaimError(
                f"{member!r} is not a registered L4a member; L4a names "
                f"{list(LEVEL_MEMBERS['L4a'])}")
        if not isinstance(by_configuration, Mapping):
            raise ClaimError(
                f"{member}: L4a needs a configuration -> classification "
                f"mapping, got {type(by_configuration).__name__}. A bare "
                "sequence of levels is exactly what v4r4's defect looked like")
        for value in by_configuration.values():
            if value is not None and not isinstance(value, str):
                raise ClaimError(
                    f"{member}: a classification is a level name or None, "
                    f"got {value!r}")

    configurations = sorted({c for m in per_member.values() for c in m})
    statement = {
        "claim_level": "L4a", "configuration": "|".join(configurations),
        "cell": "cross-configuration",
        "family": C.PRIMARY_FAMILY, "interval_type": "simultaneous",
        "identification_status": sorted(set(identification_statuses)),
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "structural_tier_of_reference_pool": "same_form_tier_1_and_2",
        "outcome_position": 0,
        "scope_sentence": C.SCOPE_SENTENCE,
        "per_member": {m: dict(v) for m, v in per_member.items()},
        "reference_pool_sentence": C.REFERENCE_POOL_SAME_FORM_SENTENCE,
    }
    if not per_member:
        return {**statement, "emitted": False,
                "reason": "no member was analysed, so there is no "
                          "classification to replicate"}
    incomplete = sorted(m for m, v in per_member.items()
                        if set(v) != set(C.CONFIGURATIONS))
    if incomplete:
        return {**statement, "emitted": False,
                "reason": "not every registered configuration was analysed "
                          f"for {incomplete}, so replication across them "
                          "cannot be read"}
    if all(v is None for m in per_member.values() for v in m.values()):
        return {**statement, "emitted": False,
                "reason": "no member reached a classification in any "
                          "configuration"}
    differing = sorted(m for m, v in per_member.items()
                       if len({v[c] for c in C.CONFIGURATIONS}) != 1)
    if differing:
        return {**statement, "emitted": False,
                "differing_members": differing,
                "registered_reading": "Configuration dependence (§28.1)",
                "reason": "these named members do not carry the same "
                          f"classification in every configuration: "
                          f"{differing}. §3.2's L4a gate is per member, and "
                          "comparing the SETS of levels reached is v4r4's "
                          "defect"}
    assert_statement_complete(statement)
    stable = {m: next(iter(v.values())) for m, v in per_member.items()}
    return {**statement, "emitted": True, "stable_classifications": stable,
            "statement": "every named member carries the same classification "
                         "in every registered configuration"}


def emit_l4b(*, member: str, interval: Interval, measurement_basis: str,
             both_configurations_analysed: bool,
             identification_statuses: Sequence[str] = ()) -> dict[str, Any]:
    """§3.2 L4b: the named quantity depends on the position of the outcome.

    Reads F11's simultaneous interval. An interval excluding zero licenses
    L4b for that named quantity and **nothing more**: it says the quantity
    depends on position and it does not say why. §22's length and register
    diagnostics are descriptive and §29 records that the mechanism is not
    identified.

    An interval containing zero is **not** order-invariance. This emitter
    never produces such a statement: §17.3's guarded equivalence function is
    the only route to the word, and it has its own precision precondition.
    """
    if member not in LEVEL_MEMBERS["L4b"]:
        raise ClaimError(
            f"{member!r} is not a registered L4b member; F11 names "
            f"{list(LEVEL_MEMBERS['L4b'])}. §33 check 9 requires that no "
            "unregistered order comparison is emitted")
    if interval.member != member:
        raise ClaimError(
            f"the interval is for {interval.member!r} and the statement names "
            f"{member!r}")
    statuses = list(identification_statuses)
    if not interval.meets_precondition():
        statuses.append("INSUFFICIENT_PRECISION")
    statement = {
        "claim_level": "L4b", "configuration": "|".join(C.CONFIGURATIONS),
        "cell": "cross-configuration composed pair",
        "family": "F11", "interval_type": "simultaneous",
        "identification_status": sorted(set(statuses)),
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "structural_tier_of_reference_pool": "same_form_tier_1_and_2",
        "outcome_position": 0,
        "scope_sentence": C.SCOPE_SENTENCE,
        "member": member,
        "interval": [interval.lower, interval.upper],
        "estimate": interval.estimate, "half_width": interval.half_width,
    }
    if not both_configurations_analysed:
        return {**statement, "emitted": False,
                "reason": "L4b's gate requires both configurations analysed"}
    if not interval.meets_precondition():
        return {**statement, "emitted": False,
                "reason": "the realised half-width exceeds the registered "
                          "precision precondition for this contrast"}
    if not interval.excludes_zero():
        return {**statement, "emitted": False,
                "reason": "the F11 simultaneous interval does not exclude 0. "
                          "That is NOT order-invariance: an equivalence "
                          "statement requires §17.3's guarded function and "
                          "its precision precondition"}
    assert_statement_complete(statement)
    return {**statement, "emitted": True,
            "statement": f"{member} depends on the position of the outcome "
                         "constraint, by the registered contrast"}


def assert_no_l5_emitter(namespace: Mapping[str, Any]) -> None:
    """§3.2: L5 is permanently withheld and no code path emits it."""
    offenders = [name for name in namespace
                 if name.startswith("emit_") and "l5" in name.lower()]
    if offenders:
        raise ClaimError(f"L5 is permanently withheld; found {offenders}")
