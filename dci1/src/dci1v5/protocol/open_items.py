"""Specification questions §34 does not carry, as executable state.

§34 registers nineteen **researcher decisions**, and ``protocol/decisions.py``
blocks on them. This module carries a different thing: places where the
preregistration, the machine-readable spec and the implementation *disagree
about what a rule means*, found by implementing them. §33 of the
implementation brief asks for exactly four classifications --- stale
documentation, unresolved scientific choice, implementation defect, true
protocol contradiction --- and says only the first and third may be fixed.

The first and third are fixed and leave no trace here. The other two live
here, with a status that says what a reader must do about them, because a
discrepancy recorded only in a report is a discrepancy nothing enforces:

* ``RESEARCHER_DECISION_REQUIRED`` --- the documents do not determine the
  rule, more than one formulation is mathematically admissible, and they
  differ in what they estimate. **These block adoption.**
  ``assert_no_blocking_open_items`` refuses the registration manifest and the
  pre-freeze audit reports them.
* ``CONFIRM_AT_ADOPTION`` --- a stale sentence was corrected so the documents
  agree with the rule the other sections and the code already implement. The
  correction changes nothing executable, and the researcher confirms it at
  adoption rather than discovering it afterwards. **Not blocking.**
* ``SINGLE_ADMISSIBLE_READING`` --- the preregistration leaves a term
  undefined and exactly one reading is executable. The implementation takes
  it and says where. **Not blocking**, recorded so the reading is visible.

Nothing here invents a rule. An item at ``RESEARCHER_DECISION_REQUIRED``
carries the admissible alternatives and what each one changes in the
estimand, and the code path it governs fails closed rather than choosing.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from dci1v4.errors import ProtocolError

__all__ = ["OpenItem", "OpenItemError", "STATUSES", "BLOCKING_STATUSES",
           "OPEN_ITEMS", "OPEN_ITEM_IDS", "get_item", "blocking_items",
           "assert_no_blocking_open_items", "assert_item_resolved",
           "resolve", "reopen_all_for_testing", "manifest_payload",
           "recorded_resolutions", "apply_recorded_resolutions"]

RESEARCHER_DECISION_REQUIRED = "RESEARCHER_DECISION_REQUIRED"
CONFIRM_AT_ADOPTION = "CONFIRM_AT_ADOPTION"
SINGLE_ADMISSIBLE_READING = "SINGLE_ADMISSIBLE_READING"
STATUSES = (RESEARCHER_DECISION_REQUIRED, CONFIRM_AT_ADOPTION,
            SINGLE_ADMISSIBLE_READING)
#: Statuses that stop adoption. Only the first: a corrected stale sentence and
#: a uniquely executable reading are both reported, and neither is a choice
#: nobody has made.
BLOCKING_STATUSES = (RESEARCHER_DECISION_REQUIRED,)


class OpenItemError(ProtocolError):
    """A code path governed by an unresolved specification question."""


@dataclass(frozen=True)
class Alternative:
    """One mathematically admissible formulation of a disputed rule."""

    id: str
    form: str
    estimand: str
    consequence: str


@dataclass(frozen=True)
class OpenItem:
    id: str
    title: str
    section: str
    status: str
    question: str
    #: Where the disagreement is visible, artifact by artifact.
    artifacts: dict[str, str] = field(default_factory=dict)
    alternatives: tuple[Alternative, ...] = ()
    #: What the implementation does today, and why it is not a decision.
    implementation: str = ""
    #: Fully-qualified functions that refuse while this is unresolved.
    blocks_calls: tuple[str, ...] = ()
    resolution: Any = None
    resolved_by: str | None = None
    resolved_on: str | None = None

    @property
    def blocking(self) -> bool:
        return self.status in BLOCKING_STATUSES and self.resolution is None

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "section": self.section,
                "status": self.status, "question": self.question,
                "artifacts": dict(self.artifacts),
                "alternatives": [a.__dict__ for a in self.alternatives],
                "implementation": self.implementation,
                "blocks_calls": list(self.blocks_calls),
                "blocking": self.blocking, "resolution": self.resolution,
                "resolved_by": self.resolved_by,
                "resolved_on": self.resolved_on}


_ITEMS: tuple[OpenItem, ...] = (
    OpenItem(
        "U1",
        "What a Tier-2 core reference contributes to §13.8's discourse-role "
        "spread",
        "§13.8, §7.6",
        SINGLE_ADMISSIBLE_READING,
        "§13.8 requires the three core references to span at least two "
        "declared discourse roles. §7.6 assigns a discourse role to marker "
        "families and to no others, so a Tier-2 member declares none, and "
        "§13.8 does not say what it contributes to the count.",
        artifacts={
            "preregistration": "§13.8 states the requirement and the "
                               "substitution; neither mentions `none`",
            "implementation": "protocol.taxonomy.declared_roles excludes "
                              "`none`"},
        implementation="`none` is not a role. §13.15 guarantees at least two "
                       "Tier-1 members, so at least two members always "
                       "declare one and the requirement is always well "
                       "defined. `assert_core_set_structure` records both "
                       "the counted set and the set as declared."),
    OpenItem(
        "U2",
        "§11.8's tier-indicator secondary fit is not identified as written",
        "§11.8, §15 F8",
        RESEARCHER_DECISION_REQUIRED,
        "§11.8 registers `Y = alpha_f + beta*d + gamma*1[Tier 2]` over twelve "
        "points and does not say what `alpha_f` is for the three near-form "
        "controls. Giving each its own family intercept makes `gamma` exactly "
        "collinear with the sum of those three dummies: the design matrix is "
        "singular and `gamma` identifies nothing.",
        artifacts={
            "preregistration": "§11.8 writes alpha_f over `families` without "
                               "saying which families the twelve points span",
            "families": "§15 F8 registers eleven members including three "
                        "family intercepts and one gamma_tier, which is "
                        "consistent with A2 and inconsistent with A1 and A4, "
                        "but F8's `three family intercepts` is equally "
                        "readable as the PRIMARY fit's three",
            "spec": "reference_design_spec.json does not carry the secondary "
                    "fit at all",
            "implementation": "analysis.spectrum.fit_with_tier_indicator "
                              "refuses until this is resolved"},
        alternatives=(
            Alternative(
                "A1", "alpha_f over all six families (three core, three "
                      "near-form), gamma free",
                "not identified",
                "the design matrix is exactly singular; gamma has no unique "
                "least-squares value. Admissible only if the protocol also "
                "registers a coding constraint, which it does not."),
            Alternative(
                "A2", "alpha_f over the three CORE families; a Tier-2 point "
                      "sits at the unweighted mean core intercept plus gamma",
                "gamma = the Tier-2 offset from the difficulty line the three "
                "core families define, at equal weight over core families",
                "identified with 12 points and 5 parameters. Equivalent in "
                "fitted values to giving Tier 2 one shared free intercept, "
                "with gamma = alpha_near - mean(alpha_core). Matches §11.8's "
                "own prediction-at-A convention, which also uses the average "
                "intercept. Reports three intercepts, as F8 lists."),
            Alternative(
                "A3", "one intercept per core family and one shared intercept "
                      "for the pooled Tier-2 group; gamma NOT estimated",
                "no gamma; the tier's contribution is read from the fourth "
                "intercept against the core three",
                "identified, but F8 loses `gamma_tier` and §11.8's own "
                "sentence registers gamma and its interval."),
            Alternative(
                "A4", "a single common intercept; Y = alpha + beta*d + "
                      "gamma*1[Tier 2]",
                "gamma = the Tier-2 offset from a pooled difficulty line "
                "that ignores between-family level differences",
                "identified, but beta then absorbs between-family level "
                "differences that §11.8's primary form deliberately removes "
                "with family intercepts, so beta means something different in "
                "the secondary than in the primary."),
        ),
        implementation="RESOLVED at A2. `fit_with_tier_indicator` reads this "
                       "item's resolution rather than a literal, so it still "
                       "refuses --- rather than defaulting to A2 --- if the "
                       "resolution goes away. A1 is refused as singular by "
                       "name; A3 is not constructed because it removes a "
                       "registered F8 member; A4 is constructed and "
                       "NON-ADOPTED, kept because the decisive comparison in "
                       "u2_tier_model_decision.md is computed from it on "
                       "every test run, and refused on any reporting path by "
                       "`assert_adopted_formulation`. §11.8's sentence is "
                       "amended to name the three core families explicitly. "
                       "gamma licenses no claim, so the resolution costs and "
                       "buys no claim level.",
        blocks_calls=("analysis.spectrum.fit_with_tier_indicator",)),
    OpenItem(
        "U3",
        "Which direction 'the less restrictive severity' runs, per predicate "
        "form",
        "§13.8, §12.6, §7.10",
        SINGLE_ADMISSIBLE_READING,
        "§13.8 states the within-family tie-break as 'the less restrictive "
        "severity' and leaves the word to the form.",
        artifacts={
            "preregistration": "§7.10 states the exact-count direction in its "
                               "own words: 'Higher q is harder, so extending "
                               "the reserve extends the span downward in "
                               "iota'",
            "implementation": "stages.selection.restrictiveness_key"},
        implementation="derived from the family's form: a budget loosens "
                       "upward, a lower bound and an exact count loosen "
                       "downward. The same function fixes §12.6's expansion "
                       "direction."),
    OpenItem(
        "U4",
        "What makes a pre-screen rung *eligible* for §12.6's coverage "
        "criterion",
        "§12.6, §13.4",
        RESEARCHER_DECISION_REQUIRED,
        "§12.6 evaluates the identification-coverage criterion \"on the "
        "pre-screen table with eligibility as §13's band on iota and its "
        "vacuity ceiling\". §13 registers a vacuity ceiling of 0.10 and one "
        "band, [0.10, 0.90], and that band is registered on the RAW SOLO "
        "COMPLIANCE p_solo(R), not on iota. §13 registers no band on iota at "
        "all --- §13.8 constrains iota only through calipers relative to "
        "iota_A. So the sentence names a band on a quantity §13 does not "
        "band, and the eligible set is not determined.",
        artifacts={
            "preregistration": "§12.6 says 'eligibility as §13's band on "
                               "iota'; §13.4's table bands p_solo and §13.8 "
                               "gives iota calipers, not a band",
            "implementation": "stages.regime.coverage_criterion reads an "
                              "`eligible` flag on every row and NOTHING in "
                              "the repository ever set it; the production "
                              "caller passed the §12.2 carried set, whose "
                              "rows carry no such key, so the criterion "
                              "evaluated on an empty set and C1-C6 were "
                              "False on every replication",
            "evidence": "the synthetic lifecycle records "
                        "coverage.decisive_met False with 73 rungs carried"},
        alternatives=(
            Alternative(
                "E1",
                "iota inside [0.10, 0.90] and pre-screen solo vacuity <= 0.10",
                "the coverage criterion's C1-C8 counted over rungs whose "
                "INSTRUCTED compliance sits in the band",
                "reads the sentence literally: §13's band numbers applied to "
                "iota, the coordinate every one of C1-C4 is stated in. A "
                "high-chance rung with p_solo in band but iota outside is "
                "excluded"),
            Alternative(
                "E2",
                "raw solo compliance inside [0.10, 0.90] and pre-screen solo "
                "vacuity <= 0.10",
                "the coverage criterion's C1-C8 counted over rungs that pass "
                "§13.4's V_head band on the quantity §13.4 states it on",
                "reads '§13's band' as the rule §13 actually registers, and "
                "uses iota only where C1-C4 use it, for position relative to "
                "iota_A. A rung with p_solo outside the band but iota inside "
                "is excluded"),
        ),
        implementation="not chosen. `stages.regime.coverage_eligibility` "
                       "constructs both named formulations and refuses to "
                       "run either until U4 is resolved, so no replication "
                       "can measure a §12.6 expansion round or record a "
                       "REFERENCE_SUPPORT_NOT_IDENTIFIED disposition under a "
                       "rule nobody chose. The two eligible sets differ, so "
                       "C1-C6 can differ, so the admitted arm set and "
                       "therefore whether Delta_R is identified at all can "
                       "differ: this is not a formatting choice."),
    OpenItem(
        "P1",
        "§7.10 admitted Tier 3 'to the spectrum'; §7.4, §11.8 and §13.12 make "
        "that unreachable",
        "§7.10, §7.4, §11.8, §13.12",
        CONFIRM_AT_ADOPTION,
        "§7.10 said the twenty-six Tier-3 families were 'admissible to the "
        "spectrum and to the broad-class slot only', and drew the further "
        "conclusion that CL7 and CL8 are 'spectrum-eligible and "
        "broad-class-ineligible'. §7.4's slot table gives a spectrum rung "
        "'the tier of its own core family' and admits Tier 1 and Tier 2 to "
        "the core slot alone; §13.12 draws both spectrum rungs from the core "
        "family; §11.8's fit is registered over three families of three "
        "severities, the three core references and their six spectrum "
        "companions. No Tier-3 family can supply a spectrum rung.",
        artifacts={
            "preregistration": "§7.10's sentence was the only text admitting "
                               "Tier 3 to the spectrum, against three "
                               "sections that exclude it; corrected to match "
                               "them",
            "spec": "reference_design_spec.json already carried "
                    "`broad_class_control` alone for Tier 3 (reconciliation "
                    "S6)",
            "implementation": "taxonomy.assert_tier_admits_slot requires the "
                              "core family's tier for a spectrum slot"},
        implementation="The wording was corrected, not the rule: nothing "
                       "executable changed and no verdict moves, because "
                       "under either reading of §7.10 the code admitted no "
                       "Tier-3 spectrum rung. Making Tier 3 *reachable* "
                       "instead would change the spectrum candidate "
                       "population, §11.8's three-families-of-three fit "
                       "structure and the derived cell set, so it is a "
                       "protocol amendment and was not made. The consequence "
                       "the corrected sentence must own: CL7 and CL8 are "
                       "count lower bounds, §13.10 admits budget class to the "
                       "broad-class slot only, and with the spectrum closed "
                       "to Tier 3 they are admissible to no design slot. They "
                       "remain in the instrument population §10.2 measures."),
)

OPEN_ITEMS: dict[str, OpenItem] = {i.id: i for i in _ITEMS}
OPEN_ITEM_IDS: tuple[str, ...] = tuple(OPEN_ITEMS)


def get_item(item_id: str) -> OpenItem:
    try:
        return OPEN_ITEMS[item_id]
    except KeyError as exc:
        raise ProtocolError(
            f"{item_id!r} is not a registered specification question; "
            f"registered: {OPEN_ITEM_IDS}") from exc


def blocking_items() -> tuple[str, ...]:
    return tuple(k for k, i in OPEN_ITEMS.items() if i.blocking)


def assert_no_blocking_open_items(*, where: str) -> None:
    """§33: adoption may not proceed over an unresolved scientific meaning."""
    blocking = blocking_items()
    if blocking:
        detail = "; ".join(f"{k}: {OPEN_ITEMS[k].title}" for k in blocking)
        raise OpenItemError(
            f"{where}: {list(blocking)} are specification questions the "
            f"documents do not settle --- {detail}. Each carries the "
            "mathematically admissible alternatives and what each changes in "
            "the estimand; resolving one is a researcher act, recorded with "
            "open_items.resolve(), and an amendment to the preregistration")


def assert_item_resolved(item_id: str, *, where: str) -> Any:
    item = get_item(item_id)
    if item.blocking:
        raise OpenItemError(
            f"{where}: specification question {item_id} is unresolved --- "
            f"{item.question} Admissible formulations: "
            f"{[a.id for a in item.alternatives]}. This implementation does "
            "not choose between them, because they estimate different things")
    return item.resolution


def resolve(item_id: str, resolution: Any, *, resolved_by: str,
            resolved_on: str) -> OpenItem:
    """Record a researcher's resolution. Write-once, and never a default."""
    item = get_item(item_id)
    if item.resolution is not None:
        raise ProtocolError(
            f"{item_id} is already resolved as {item.resolution!r}; a change "
            "is a preregistration amendment, not a re-resolution")
    admissible = {a.id for a in item.alternatives}
    if admissible and resolution not in admissible:
        raise ProtocolError(
            f"{item_id} offers {sorted(admissible)}; got {resolution!r}. A "
            "formulation outside that set is a new one and belongs in the "
            "preregistration first")
    if not (resolved_by and resolved_on):
        raise ProtocolError(
            f"resolving {item_id} requires who resolved it and when")
    updated = replace(item, resolution=resolution, resolved_by=resolved_by,
                      resolved_on=resolved_on)
    OPEN_ITEMS[item_id] = updated
    return updated


def reopen_all_for_testing() -> None:
    """Restore every item to **the recorded state**, not to a blank one.

    Same reason as ``decisions.reopen_all_for_testing``: what a fixture found
    the module in is what the record says, and a fixture that reopened a
    resolved question would let a test assert behaviour the protocol no
    longer admits.
    """
    for key, item in list(OPEN_ITEMS.items()):
        OPEN_ITEMS[key] = replace(item, resolution=None, resolved_by=None,
                                  resolved_on=None)
    apply_recorded_resolutions()


# ------------------------------------------------------ the durable record

def recorded_resolutions(path: Any = None) -> tuple[dict[str, Any], ...]:
    """The resolutions the researcher's record carries.

    U2 and P1 are as much a researcher act as any §34 closure --- U2 blocks
    the manifest outright --- and a resolution that lived only in a running
    interpreter would be a choice nobody took. They live in the **same** file
    as the decisions, under ``open_items``, so one hash covers everything the
    researcher settled and the manifest binds it once.
    """
    from dci1v5.protocol import decisions

    record = decisions.read_record(path)
    entries = record.get("open_items") or []
    if not isinstance(entries, list):
        raise ProtocolError(
            f"{record['path']}: 'open_items' must be a list of resolutions")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        for field_name in ("id", "resolution", "resolved_by", "resolved_on"):
            if not str(entry.get(field_name, "")).strip():
                raise ProtocolError(
                    f"{record['path']}: a recorded resolution needs "
                    f"{field_name}; a resolution with no author is a default "
                    "with a filename on it")
        item = get_item(entry["id"])
        if entry["id"] in seen:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} is recorded twice; a change "
                "is a preregistration amendment, not a second entry")
        seen.add(entry["id"])
        admissible = {a.id for a in item.alternatives}
        if admissible and entry["resolution"] not in admissible:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} offers {sorted(admissible)} "
                f"and the record says {entry['resolution']!r}")
        out.append(dict(entry))
    return tuple(out)


def apply_recorded_resolutions(path: Any = None) -> tuple[str, ...]:
    """Apply the record. Idempotent, and a disagreement is an amendment."""
    applied: list[str] = []
    for entry in recorded_resolutions(path):
        current = get_item(entry["id"])
        if current.resolution is not None:
            if current.resolution != entry["resolution"]:
                raise ProtocolError(
                    f"{entry['id']} is in force as {current.resolution!r} and "
                    f"the record says {entry['resolution']!r}; a change is a "
                    "preregistration amendment")
            continue
        resolve(entry["id"], entry["resolution"],
                resolved_by=entry["resolved_by"],
                resolved_on=entry["resolved_on"])
        applied.append(entry["id"])
    return tuple(applied)


def manifest_payload() -> dict[str, Any]:
    """What the registration manifest binds about specification questions."""
    return {
        "source": "found by implementing the preregistration; §34 does not "
                  "carry them",
        "n_items": len(OPEN_ITEMS),
        "blocking": list(blocking_items()),
        "resolved": {k: i.resolution for k, i in OPEN_ITEMS.items()
                     if i.resolution is not None},
        "record": {"path": _record_relpath(),
                   "resolved_here": [e["id"]
                                     for e in recorded_resolutions()]},
        "items": [i.as_dict() for i in OPEN_ITEMS.values()],
    }


def _record_relpath() -> str:
    from dci1v5.protocol import decisions

    return decisions.RECORD_RELPATH


#: Applied at import, for the same reason the decision record is.
apply_recorded_resolutions()
