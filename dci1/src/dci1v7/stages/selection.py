"""Core, spectrum, near-form and broad-class selection (§13.8-§13.12).

Everything here reads **solo, chance and counterfactual-chance quantities on
the calibration topics, and nothing else**. It could have been executed before
a single composed cell existed anywhere in this programme, and
``stages/calibration_table.py`` is the structure that makes that true rather
than asserted.

**Four pools, four purposes, and they are not one mechanism.** v4r4 used one
admission rule for every scientific job and then discovered that the job
changes what "valid" means:

* **core references** carry Delta_j, Delta_R, the reciprocal local effects and
  Xi. Tier 1 or Tier 2, at least two Tier 1, three feature groups, at least
  two discourse roles;
* **spectrum companions** carry delta_difficulty. Drawn from an admitted core
  reference's **own family**, and deliberately **exempt from V_diff**, whose
  whole purpose is proximity to iota_A and which a spectrum rung exists to
  violate in a controlled direction;
* **near-form controls** carry Delta_near and the second half of the answer to
  H_form. Three Tier-2 companions, beside B only, and never in the core set,
  the spectrum, the fit, Delta_R, Rbar or Xi;
* **the broad-class control** bounds how much structural class could matter.
  One Tier-3 **budget** companion, beside B only, with its own claim
  interpretation.

**"The less restrictive severity breaks an exact within-family tie."** The
preregistration states the rule and leaves the word to the form, so the
derivation is here: for a budget (``<=``) a larger q admits more answers and
is less restrictive; for a lower bound (``>=``) and for an exact count
(``==``) a smaller q is. §7.10 states the exact-count direction in its own
words --- *higher q is harder, so extending the reserve extends the span
downward in iota* --- so this is a reading of the protocol and not a choice
made here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C
from dci1v7.protocol.taxonomy import (
    SLOT_BROAD_CLASS, SLOT_CORE, SLOT_NEAR_FORM, SLOT_SPECTRUM, TIER_1, TIER_2,
    TIER_3, assert_core_set_structure, declared_roles,
)
from dci1v7.stages.calibration_table import CalibrationRow, tie_key
from dci1v7.stages.validity import (
    VALIDITY_COMPONENTS, ReferenceValidity, evaluate_validity,
)
from dci1v7.verifiers.constraints import (
    CLASS_BUDGET, FAMILIES, FEATURE_GROUP_IDS, LOWER_BOUND_FORMS, FORM_EXACT,
)

__all__ = ["restrictiveness_key", "FamilyAdmission", "admit_family",
           "admit_core_references", "select_spectrum_triple",
           "select_spectrum", "admit_near_form_controls",
           "admit_broad_class_control", "SelectionResult", "select_all",
           "SPECTRUM_COMPONENTS", "assert_no_backup_substitution"]

#: §13.12: a spectrum rung passes every component **except** V_diff.
SPECTRUM_COMPONENTS = tuple(c for c in VALIDITY_COMPONENTS if c != "V_diff")


def restrictiveness_key(kind: str, severity: int) -> int:
    """Sort key in which the **less restrictive** severity comes first.

    See the module docstring. Budgets loosen upward, lower bounds and exact
    counts loosen downward.
    """
    family = FAMILIES[kind]
    if family.form in LOWER_BOUND_FORMS or family.form == FORM_EXACT:
        return severity
    return -severity


def _group_order(kind: str) -> int:
    return FEATURE_GROUP_IDS.index(FAMILIES[kind].feature_group)


def _entry_dicts(chosen) -> list[dict[str, Any]]:
    return [{"family": v.family, "structural_tier": v.structural_tier,
             "feature_group": v.feature_group,
             "discourse_role": v.discourse_role} for v in chosen]


@dataclass(frozen=True)
class FamilyAdmission:
    """§13.8's per-family verdict, with every rejection reason kept.

    ``rungs`` carries one ``ReferenceValidity`` per measured severity, so the
    Gate 3B record can print why each rung of a rejected family failed rather
    than only that the family did.
    """

    family: str
    admitted: bool
    severity: int | None
    iota: float | None
    distance: float | None
    structural_tier: int
    feature_group: str
    discourse_role: str
    rungs: tuple[ReferenceValidity, ...] = ()

    @property
    def first_failing_components(self) -> dict[str, str | None]:
        return {v.candidate: v.first_failing_component for v in self.rungs}

    def as_dict(self) -> dict[str, Any]:
        return {"family": self.family, "admitted": self.admitted,
                "severity": self.severity, "iota": self.iota,
                "distance": self.distance,
                "structural_tier": self.structural_tier,
                "feature_group": self.feature_group,
                "discourse_role": self.discourse_role,
                "rungs": [v.as_dict() for v in self.rungs]}


def admit_family(family: str, rows: Sequence[CalibrationRow], *, slot: str,
                 iota_a: float, solo_compliance_a: float,
                 n_topics_a: int | None = None,
                 stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
                 components: Sequence[str] = VALIDITY_COMPONENTS,
                 ) -> FamilyAdmission:
    """Evaluate every measured rung of one family and pick its best.

    The best rung minimises |iota_R - iota_A| among those passing the full
    V(R); an exact tie goes to the less restrictive severity. At most one
    severity per family enters the core set (§13.8).
    """
    stability_by_candidate = dict(stability_by_candidate or {})
    verdicts: list[ReferenceValidity] = []
    for row in [r for r in rows if r.kind == family]:
        verdicts.append(evaluate_validity(
            row, slot=slot, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
            n_topics_a=n_topics_a, components=components,
            stability=stability_by_candidate.get(row.label),
            provenance={"split": row.split, "n_topics": row.n_topics,
                        "n_draws": row.n_draws}))
    meta = FAMILIES[family]
    passing = [(v, r) for v, r in zip(verdicts,
                                      [r for r in rows if r.kind == family])
               if v.passed]
    if not passing:
        return FamilyAdmission(family, False, None, None, None,
                               meta.structural_tier, meta.feature_group,
                               meta.discourse_role, tuple(verdicts))
    _, best_row = min(
        passing,
        key=lambda pair: (tie_key(abs(pair[1].iota - iota_a)),
                          restrictiveness_key(family, pair[1].severity)))
    return FamilyAdmission(
        family, True, best_row.severity, best_row.iota,
        abs(best_row.iota - iota_a), meta.structural_tier, meta.feature_group,
        meta.discourse_role, tuple(verdicts))


def select_spectrum_triple(family: str, rows: Sequence[CalibrationRow], *,
                           core_severity: int, iota_a: float,
                           solo_compliance_a: float,
                           stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
                           ) -> dict[str, Any] | None:
    """§13.12: one rung strictly below iota_A and one strictly above.

    **Strict straddling is the rule and not an accident of the targets.**
    Selecting the two rungs nearest iota_A +/- 0.20 without it permits both on
    the same side, which is what a difficulty-spanning arm run at screen scale
    actually produced on two of four v4r4 models --- one point below A and
    four above. One strictly below and one strictly above in every family
    guarantees three below and three above, which is what §13.13's support
    rule needs and what keeps the fit centred on A.

    A spectrum rung is not subject to V_diff (§13.12).
    """
    stability_by_candidate = dict(stability_by_candidate or {})
    pool: list[CalibrationRow] = []
    for row in rows:
        if row.kind != family or row.severity == core_severity:
            continue
        verdict = evaluate_validity(
            row, slot=SLOT_SPECTRUM, iota_a=iota_a,
            solo_compliance_a=solo_compliance_a,
            components=SPECTRUM_COMPONENTS,
            core_family_tier=FAMILIES[family].structural_tier,
            stability=stability_by_candidate.get(row.label))
        selected = [c for c in verdict.components
                    if c.name in SPECTRUM_COMPONENTS]
        if all(c.passed for c in selected):
            pool.append(row)
    below = [r for r in pool if tie_key(r.iota) < tie_key(iota_a)]
    above = [r for r in pool if tie_key(r.iota) > tie_key(iota_a)]
    if not below or not above:
        return None
    lower_target = iota_a - C.SPECTRUM_OFFSET
    upper_target = iota_a + C.SPECTRUM_OFFSET
    lower = min(below, key=lambda r: (tie_key(abs(r.iota - lower_target)),
                                      restrictiveness_key(family, r.severity)))
    upper = min(above, key=lambda r: (tie_key(abs(r.iota - upper_target)),
                                      restrictiveness_key(family, r.severity)))
    return {"family": family, "core_severity": core_severity,
            "structural_tier": FAMILIES[family].structural_tier,
            "lower": {"severity": lower.severity, "iota": lower.iota,
                      "target": lower_target},
            "upper": {"severity": upper.severity, "iota": upper.iota,
                      "target": upper_target}}


def admit_core_references(rows: Sequence[CalibrationRow], *, iota_a: float,
                          solo_compliance_a: float,
                          n_topics_a: int | None = None,
                          stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
                          require_spectrum: bool = True) -> dict[str, Any]:
    """§13.8 and §13.12 together: three families that each supply a triple.

    The registered tie-break, in order: smallest |iota_R - iota_A|; then lower
    structural tier, Tier 1 before Tier 2; then registered feature-group
    order; then the less restrictive severity; then family identifier.

    Three structural conditions run alongside it. **Three feature groups**,
    not merely three families: two families over one measurement would give
    the §11.8 fit three intercepts over one property of an answer, and would
    put in one cell a pair whose non-entailment obligation §7.7 cannot
    discharge. **At least two Tier 1**, because the primary local estimand is
    a same-form contrast. **At least two discourse roles**, and when none of
    the three shares A's contrastive role the set still stands and records
    ``REFERENCE_ROLE_NOT_MATCHED`` --- role is a *declared* property, and a
    design that refused to run without a contrastive control would be refusing
    on an unmeasured attribute.

    ``require_spectrum`` expresses §13.12's retry loop: a family that cannot
    straddle A cannot be a core reference, because its core rung would
    contribute a point to the fit with no siblings on one side, so admission
    and spectrum feasibility are decided together and the next qualifying
    family takes a dropped family's slot. Setting it False admits the core arm
    without the spectrum, which §8.1 permits and which drops only
    delta_difficulty.
    """
    stability_by_candidate = dict(stability_by_candidate or {})
    families = sorted({r.kind for r in rows
                       if FAMILIES[r.kind].structural_tier in (TIER_1, TIER_2)})
    verdicts = [admit_family(f, rows, slot=SLOT_CORE, iota_a=iota_a,
                             solo_compliance_a=solo_compliance_a,
                             n_topics_a=n_topics_a,
                             stability_by_candidate=stability_by_candidate)
                for f in families]
    qualified = [v for v in verdicts if v.admitted]
    ranked = sorted(qualified,
                    key=lambda v: (tie_key(v.distance), v.structural_tier,
                                   _group_order(v.family),
                                   restrictiveness_key(v.family, v.severity),
                                   v.family))

    chosen: list[FamilyAdmission] = []
    triples: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    groups_taken: set[str] = set()
    remaining = list(ranked)
    while remaining and len(chosen) < C.N_CORE_REFERENCES:
        # §13.8: when the next qualifying family would take the Tier-1 count
        # below two, it is skipped and the following one takes the slot. The
        # look-ahead is over the slots still to fill.
        slots_left = C.N_CORE_REFERENCES - len(chosen)
        tier1_so_far = sum(1 for v in chosen if v.structural_tier == TIER_1)
        verdict = remaining.pop(0)
        group = verdict.feature_group
        if group in groups_taken:
            dropped.append({"family": verdict.family,
                            "reason": f"the {group} feature group is already "
                                      "represented; §13.8 admits three "
                                      "different measurements, not three "
                                      "different families"})
            continue
        if verdict.structural_tier != TIER_1:
            tier1_available = sum(
                1 for v in remaining
                if v.structural_tier == TIER_1
                and v.feature_group not in groups_taken | {group})
            if tier1_so_far + min(tier1_available, slots_left - 1) < \
                    C.MIN_TIER1_CORE:
                dropped.append({
                    "family": verdict.family,
                    "reason": "admitting this Tier-2 family would take the "
                              f"core set below §13.15's minimum of "
                              f"{C.MIN_TIER1_CORE} Tier-1 members"})
                continue
        triple = None
        if require_spectrum:
            triple = select_spectrum_triple(
                verdict.family, rows, core_severity=verdict.severity,
                iota_a=iota_a, solo_compliance_a=solo_compliance_a,
                stability_by_candidate=stability_by_candidate)
            if triple is None:
                dropped.append({
                    "family": verdict.family,
                    "reason": "no eligible severity strictly on one side of "
                              "A: the family cannot straddle, so §13.12 "
                              "cannot draw its triple"})
                continue
        chosen.append(verdict)
        groups_taken.add(group)
        if triple is not None:
            triples.append(triple)

    # §13.8's role substitution. "When the three otherwise-chosen references
    # share one role, the third slot goes to the highest-ranked qualifying
    # family of a different role and the substitution is recorded." The
    # replaced member is the lowest-ranked one, because the tie-break has
    # already put the best-matched family first and the rule buys the spread
    # at the smallest cost in match quality.
    substitutions: list[dict[str, Any]] = []
    if len(chosen) == C.N_CORE_REFERENCES and \
            len(declared_roles(_entry_dicts(chosen))) < \
            C.MIN_CORE_DISCOURSE_ROLES:
        present_roles = declared_roles(_entry_dicts(chosen))
        replaced = chosen[-1]
        for candidate in remaining:
            if candidate.discourse_role in present_roles or \
                    candidate.discourse_role == "none":
                continue
            free_groups = {v.feature_group for v in chosen[:-1]}
            if candidate.feature_group in free_groups:
                continue
            triple = None
            if require_spectrum:
                triple = select_spectrum_triple(
                    candidate.family, rows, core_severity=candidate.severity,
                    iota_a=iota_a, solo_compliance_a=solo_compliance_a,
                    stability_by_candidate=stability_by_candidate)
                if triple is None:
                    continue
            trial = chosen[:-1] + [candidate]
            if sum(1 for v in trial if v.structural_tier == TIER_1) < \
                    C.MIN_TIER1_CORE:
                continue
            chosen = trial
            if require_spectrum:
                triples = triples[:-1] + [triple]
            substitutions.append({
                "replaced": replaced.family, "with": candidate.family,
                "reason": "§13.8: the three otherwise-chosen references "
                          f"shared the role {sorted(present_roles)}; the "
                          "third slot goes to the highest-ranked qualifying "
                          "family of a different role"})
            break

    identified = len(chosen) == C.N_CORE_REFERENCES
    structure: dict[str, Any] = {}
    statuses: list[str] = []
    if identified:
        try:
            structure = assert_core_set_structure(
                _entry_dicts(chosen),
                min_tier1=C.MIN_TIER1_CORE, n_groups=C.N_CORE_FEATURE_GROUPS,
                min_roles=C.MIN_CORE_DISCOURSE_ROLES,
                a_role=C.A_DISCOURSE_ROLE)
            statuses = list(structure["identification_statuses"])
        except Exception as exc:
            # A structural condition the greedy pass could not satisfy is a
            # verdict about the pool, not a crash: §13.15's own answer is
            # REFERENCE_SUPPORT_NOT_IDENTIFIED, written at design time.
            identified = False
            structure = {"error": str(exc)}
            dropped.append({"family": None, "reason": str(exc)})
            statuses = ["EXCESS_NOT_IDENTIFIED"]
    else:
        statuses = ["EXCESS_NOT_IDENTIFIED"]
    #: §28.2, attached to every L3 statement whatever else happened.
    statuses.append("REFERENCE_POOL_SAME_FORM")

    return {
        "qualified_families": [v.family for v in ranked],
        "family_verdicts": [v.as_dict() for v in verdicts],
        "core_references": [
            {"slot": f"R{i + 1}", "family": v.family, "severity": v.severity,
             "iota": v.iota, "distance": v.distance,
             "structural_tier": v.structural_tier,
             "feature_group": v.feature_group,
             "discourse_role": v.discourse_role}
            for i, v in enumerate(chosen)],
        "structure": structure,
        "spectrum_triples": triples,
        "dropped": dropped,
        "role_substitutions": substitutions,
        "references_identified": identified,
        "spectrum_identified": identified and len(triples) ==
        C.N_CORE_REFERENCES,
        "identification_statuses": sorted(set(statuses)),
    }


def select_spectrum(triples: Sequence[Mapping[str, Any]]
                    ) -> list[dict[str, Any]]:
    """The six spectrum companions, in registered slot order."""
    out: list[dict[str, Any]] = []
    for index, triple in enumerate(triples, start=1):
        for side, mark in (("lower", "-"), ("upper", "+")):
            out.append({"slot": f"R{index}{mark}", "family": triple["family"],
                        "severity": triple[side]["severity"],
                        "iota": triple[side]["iota"],
                        "target": triple[side]["target"], "side": side,
                        "structural_tier": triple["structural_tier"]})
    return out


def admit_near_form_controls(rows: Sequence[CalibrationRow], *, iota_a: float,
                             solo_compliance_a: float,
                             n_topics_a: int | None = None,
                             stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
                             exclude_families: Sequence[str] = (),
                             ) -> dict[str, Any]:
    """§13.9: three Tier-2 controls from three distinct feature groups.

    Admitted by the same V(R) with the same thresholds, minimising
    |iota_N - iota_A| within family and then by §13.8's tie-break. They occupy
    the companion slot **beside B only** and never enter the core reference
    set, the spectrum, the difficulty fit, Delta_R, Rbar or Xi; an executable
    check in ``analysis/estimators.py`` refuses an analysis input that places
    one in any of them.

    When fewer than three qualify the arm is dropped, its nine cells are not
    generated, and ``NEAR_FORM_ARM_NOT_AVAILABLE`` is recorded.
    """
    excluded = set(exclude_families)
    families = sorted({r.kind for r in rows
                       if FAMILIES[r.kind].structural_tier == TIER_2
                       and r.kind not in excluded})
    verdicts = [admit_family(f, rows, slot=SLOT_NEAR_FORM, iota_a=iota_a,
                             solo_compliance_a=solo_compliance_a,
                             n_topics_a=n_topics_a,
                             stability_by_candidate=dict(
                                 stability_by_candidate or {}))
                for f in families]
    ranked = sorted([v for v in verdicts if v.admitted],
                    key=lambda v: (tie_key(v.distance), _group_order(v.family),
                                   restrictiveness_key(v.family, v.severity),
                                   v.family))
    chosen: list[FamilyAdmission] = []
    groups_taken: set[str] = set()
    for verdict in ranked:
        if len(chosen) == C.N_NEAR_FORM_CONTROLS:
            break
        if verdict.feature_group in groups_taken:
            continue
        chosen.append(verdict)
        groups_taken.add(verdict.feature_group)
    available = len(chosen) == C.N_NEAR_FORM_CONTROLS
    return {"available": available,
            "controls": [
                {"slot": f"N{i + 1}", "family": v.family,
                 "severity": v.severity, "iota": v.iota,
                 "distance": v.distance, "structural_tier": v.structural_tier,
                 "feature_group": v.feature_group}
                for i, v in enumerate(chosen)] if available else [],
            "family_verdicts": [v.as_dict() for v in verdicts],
            "identification_statuses":
                [] if available else ["NEAR_FORM_ARM_NOT_AVAILABLE"]}


def admit_broad_class_control(rows: Sequence[CalibrationRow], *,
                              iota_a: float, solo_compliance_a: float,
                              n_topics_a: int | None = None,
                              stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
                              ) -> dict[str, Any]:
    """§13.10: one Tier-3 **budget-class** companion, or the arm is dropped.

    The qualifying severity across all Tier-3 budget families minimising
    |iota_CL - iota_A|, ties broken by family identifier then by the less
    restrictive severity, subject to the same V(R).

    `CL7` and `CL8` are the two count lower bounds: Tier 3, production class,
    and therefore **broad-class-ineligible**, which ``assert_slot_allowed``
    refuses by name rather than by their absence from a list.

    **The arm's direction is inverted from v4r4's, and the inversion is the
    point.** v4r4's reference pool was budget class and its class control was
    production; v5's reference pool is production and its class control is
    budget. Both bound the same gap from opposite sides, and v5's is the one
    in which the *references* --- the quantities that carry the primary claim
    --- match A's class rather than differ from it.
    """
    families = sorted({r.kind for r in rows
                       if FAMILIES[r.kind].structural_tier == TIER_3
                       and FAMILIES[r.kind].constraint_class == CLASS_BUDGET})
    verdicts = [admit_family(f, rows, slot=SLOT_BROAD_CLASS, iota_a=iota_a,
                             solo_compliance_a=solo_compliance_a,
                             n_topics_a=n_topics_a,
                             stability_by_candidate=dict(
                                 stability_by_candidate or {}))
                for f in families]
    qualified = [v for v in verdicts if v.admitted]
    if not qualified:
        return {"available": False, "companion": None,
                "family_verdicts": [v.as_dict() for v in verdicts],
                "identification_statuses": ["CLASS_ARM_NOT_AVAILABLE"]}
    best = min(qualified, key=lambda v: (tie_key(v.distance), v.family,
                                         restrictiveness_key(v.family,
                                                             v.severity)))
    statuses = ["COMPANION_CLASS_NOT_MATCHED"]
    if best.distance > C.CLASS_MATCH_CALIPER:
        statuses.append("CLASS_ARM_NOT_MATCHED")
    return {"available": True,
            "companion": {"slot": C.CLASS_SLOT, "family": best.family,
                          "severity": best.severity, "iota": best.iota,
                          "distance": best.distance,
                          "structural_tier": best.structural_tier,
                          "constraint_class": CLASS_BUDGET},
            "family_verdicts": [v.as_dict() for v in verdicts],
            "identification_statuses": sorted(statuses)}


@dataclass
class SelectionResult:
    """Everything Gate 3B decides, in one record."""

    core: dict[str, Any]
    spectrum: list[dict[str, Any]] = field(default_factory=list)
    near_form: dict[str, Any] = field(default_factory=dict)
    broad_class: dict[str, Any] = field(default_factory=dict)

    @property
    def identification_statuses(self) -> list[str]:
        return sorted(set(
            self.core.get("identification_statuses", [])
            + self.near_form.get("identification_statuses", [])
            + self.broad_class.get("identification_statuses", [])))

    def slot_map(self) -> dict[str, tuple[str, int]]:
        out: dict[str, tuple[str, int]] = {}
        for entry in self.core.get("core_references", []):
            out[entry["slot"]] = (entry["family"], entry["severity"])
        for entry in self.spectrum:
            out[entry["slot"]] = (entry["family"], entry["severity"])
        for entry in self.near_form.get("controls", []):
            out[entry["slot"]] = (entry["family"], entry["severity"])
        companion = self.broad_class.get("companion")
        if companion:
            out[C.CLASS_SLOT] = (companion["family"], companion["severity"])
        return out


def select_all(rows: Sequence[CalibrationRow], *, iota_a: float,
               solo_compliance_a: float, n_topics_a: int | None = None,
               stability_by_candidate: Mapping[str, Mapping[str, Any]] = (),
               ) -> SelectionResult:
    """§13.8, §13.12, §13.9 and §13.10 in the registered order."""
    stability_by_candidate = dict(stability_by_candidate or {})
    core = admit_core_references(
        rows, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
        n_topics_a=n_topics_a, stability_by_candidate=stability_by_candidate)
    # §13.12: "core selection re-runs excluding it and the next qualifying
    # family takes the slot, until three families each supply a complete
    # triple **or the qualified list is exhausted. Exhaustion sets
    # DIFFICULTY_SUPPORT_NOT_IDENTIFIED and the spectrum arm is not
    # generated.**" Exhaustion drops the SPECTRUM, not the core: §8.1
    # registers that "a replication that cannot identify the spectrum still
    # estimates Delta_R, Delta_j, Xi and the reciprocal matrix". This ran the
    # spectrum-coupled pass and stopped there, so a pool that could not
    # straddle iota_A lost its core references too --- which is the exact
    # coupling that produced v4r4's F5 failure.
    if not core["references_identified"]:
        without = admit_core_references(
            rows, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
            n_topics_a=n_topics_a,
            stability_by_candidate=stability_by_candidate,
            require_spectrum=False)
        if without["references_identified"]:
            core = {**without,
                    "spectrum_identified": False,
                    "spectrum_triples": [],
                    "spectrum_exhausted": True,
                    "spectrum_exhaustion_note":
                        "§13.12: no three qualifying families each supply a "
                        "complete triple, so the spectrum arm is not "
                        "generated. §8.1: the core set stands and Delta_R, "
                        "Delta_j, Xi and the reciprocal matrix are still "
                        "estimated",
                    "identification_statuses": sorted(
                        set(without["identification_statuses"])
                        | {"DIFFICULTY_SUPPORT_NOT_IDENTIFIED"})}
    spectrum = (select_spectrum(core["spectrum_triples"])
                if core["spectrum_identified"] else [])
    used = {e["family"] for e in core["core_references"]}
    near_form = admit_near_form_controls(
        rows, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
        n_topics_a=n_topics_a, stability_by_candidate=stability_by_candidate,
        exclude_families=sorted(used))
    broad = admit_broad_class_control(
        rows, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
        n_topics_a=n_topics_a, stability_by_candidate=stability_by_candidate)
    return SelectionResult(core=core, spectrum=spectrum, near_form=near_form,
                           broad_class=broad)


def assert_no_backup_substitution(namespace: Mapping[str, Any]) -> None:
    """§13.14 and §19 test 4: **the substitution path must not exist**.

    §13.15 freezes two qualifying families beyond the three used. They exist
    so the support requirement is a real requirement rather than a formality
    --- a replication that qualifies exactly three families has no evidence
    that its pool was anything but lucky --- and so that a future protocol
    version has a documented, pre-committed pool. They are **never**
    substituted into a design after Gate 4, because substituting a companion
    after observing a composed rate is outcome-based selection with an extra
    step.

    The registered test is that no such function exists, not that none is
    called, so this reads the module namespace.
    """
    offenders = sorted(
        name for name in namespace
        if not name.startswith("assert_no_")   # the guard is not the offence
        and any(token in name.lower()
               for token in ("substitute", "replace_reference",
                             "swap_reference", "promote_backup",
                             "backup_into"))) 
    if offenders:
        raise ProtocolError(
            "§13.14: a frozen backup is never substituted into an admitted "
            f"slot after Gate 4, and the path must not exist; found "
            f"{offenders}")
