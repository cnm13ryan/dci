"""Scientific material: the disjoint splits, the background strata, and pools.

Preregistration sections 8.2, 11.1 and 11.2. Three separate commitments live
here, and each has a failure mode that is invisible without a mechanical check.

**Disjoint splits (11.1).** All material that can affect a frozen scientific
choice is partitioned before confirmation into six pools - development,
parameter calibration, reference construction, independent reference validation,
confirmation, terminal falsification - plus an optional adapter/manipulation bank
that must be "demonstrably disjoint from all DCI content pools". The point is
that no confirmatory task, wording, answer or model output may enter a pre-freeze
design decision. An item silently present in two splits breaks that firewall
without producing any visible error, so `assert_splits_disjoint` exists.

**Three strata, one home (8.2).** The background pool is partitioned into exactly
three strata - lexical/content, structural/format, relational/order - and "a
constraint belongs to only one background-sampling stratum". That is not
bookkeeping: section 8.3 draws exactly one background identity with replacement
from *each* stratum, so a constraint listed in two strata could be drawn twice
into the same superblock and the stated proposal law would no longer describe
what the sampler does.

**Pools are signed, then immutable (11.2).** "Once a pool is signed and hashed,
later movement of items between pools is prohibited." Signing is therefore a
one-way operation over a populated pool, and the fingerprint covers the pool's
identity together with its contents.

Nothing here invents content. Every pool's contents is a PENDING_CONTENT slot: a
pair that cannot populate its required pools without reuse is a pre-freeze
feasibility failure (11.2), which is a fact to be discovered by authoring the
material, not asserted by a registry.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from dci.provenance.hashes import sha
from dci.v19.pairs import GENERATIVE_SCOPES, PAIR_IDS
from dci.v19.resolution import (Resolution, Slot, SlotTable,
                                UnresolvedDependency, pending)
from dci.v19.sampling import STRATA

# Section 11.1, in the document's order. Membership is exclusive.
MATERIAL_SPLITS = ("development", "parameter_calibration",
                   "reference_construction", "independent_validation",
                   "confirmation", "terminal_falsification")

# A separate adapter/manipulation prompt bank is permitted for hard-budget
# validation "when it is demonstrably disjoint from all DCI content pools", so it
# is tracked alongside the six rather than inside them.
ADAPTER_SPLIT = "adapter_manipulation"
ALL_SPLITS = MATERIAL_SPLITS + (ADAPTER_SPLIT,)

POOL_KINDS = ("task", "background", "unrelated_target", "coupling_probe",
              "audit", "wording_calibration", "manipulation_prompt")

# Section 11.2's sufficiency report, counted separately by pair and scope.
SUFFICIENCY_COUNTS = (
    "eligible_tasks",
    "target_wordings",
    "focal_wordings",
    "candidate_reference_identities",
    "unrelated_targets",
    "parameter_calibration_instances",
    "audit_true_pass_examples",
    "audit_true_fail_examples",
    "feasible_background_candidates",
    "independent_validation_items",
    "terminal_falsification_items",
)


class PoolViolation(ValueError):
    """A material-split or stratum invariant failed. Fail closed."""


@dataclass(frozen=True)
class BackgroundEntry:
    """One background constraint, with the metadata section 8.2 requires.

    Every field listed in section 8.2 is required rather than optional, because a
    background entry missing its verifier hash or its incompatibility metadata
    cannot be checked for whole-composition feasibility, and an unfeasible
    composition entering a bank is the failure section 8.6 rejects proposals to
    avoid.
    """
    constraint_id: str
    stratum: str
    generative_scope: str
    output_schema: str
    verifier_hash: str
    canonical_wording_hash: str
    provenance: str
    parameter_distribution: str = ""
    incompatible_with: tuple[str, ...] = ()
    entails: tuple[str, ...] = ()

    def __post_init__(self):
        if self.stratum not in STRATA:
            raise PoolViolation(
                f"{self.constraint_id}: stratum {self.stratum!r} is not one of "
                f"{STRATA}; the background pool is partitioned into exactly "
                "these three (section 8.2)")
        if self.generative_scope not in GENERATIVE_SCOPES:
            raise PoolViolation(
                f"{self.constraint_id}: generative scope "
                f"{self.generative_scope!r} is not one of {GENERATIVE_SCOPES}")
        for field_name in ("constraint_id", "output_schema", "verifier_hash",
                           "canonical_wording_hash", "provenance"):
            if not getattr(self, field_name):
                raise PoolViolation(
                    f"{self.constraint_id or '<unnamed>'}: {field_name} is "
                    "required by section 8.2; an entry that cannot be hashed or "
                    "traced cannot enter a frozen pool")
        if self.constraint_id in self.incompatible_with:
            raise PoolViolation(
                f"{self.constraint_id} is declared incompatible with itself")


@dataclass(frozen=True)
class Pool:
    """One named body of scientific material belonging to exactly one split."""
    pool_id: str
    pair: str
    kind: str
    split: str
    contents: Slot
    stratum: str = ""
    signed_by: str = ""

    def __post_init__(self):
        if self.kind not in POOL_KINDS:
            raise PoolViolation(f"{self.pool_id}: kind {self.kind!r} is not one "
                                f"of {POOL_KINDS}")
        if self.split not in ALL_SPLITS:
            raise PoolViolation(f"{self.pool_id}: split {self.split!r} is not "
                                f"one of {ALL_SPLITS}")
        if self.pair not in PAIR_IDS and self.pair != "shared":
            raise PoolViolation(
                f"{self.pool_id}: {self.pair!r} is neither a v19 pair "
                f"{PAIR_IDS} nor 'shared'")
        if self.kind == "background" and self.stratum not in STRATA:
            raise PoolViolation(
                f"{self.pool_id}: a background pool must name one of the three "
                f"strata {STRATA}, got {self.stratum!r}")
        if self.kind != "background" and self.stratum:
            raise PoolViolation(
                f"{self.pool_id}: only a background pool has a stratum, but "
                f"kind={self.kind!r} declares {self.stratum!r}")
        if self.signed_by and not self.contents.resolved:
            raise PoolViolation(
                f"{self.pool_id} is signed but has no contents; signing an "
                "empty pool would freeze the absence of material as though it "
                "were material")

    @property
    def populated(self) -> bool:
        return self.contents.resolved

    @property
    def signed(self) -> bool:
        return bool(self.signed_by)

    @property
    def items(self) -> tuple:
        """The pool's contents, or refuse. Never an empty tuple by default."""
        return tuple(self.contents.get())

    @property
    def identity(self) -> list:
        return [self.pool_id, self.pair, self.kind, self.split, self.stratum]

    @property
    def fingerprint(self) -> str:
        """Hash of the pool's identity together with its contents.

        Requires contents: a fingerprint over an unpopulated pool would be a
        stable identifier for nothing, and comparing it later would appear to
        prove the material had not changed.
        """
        item_keys = sorted(_content_key(i) for i in self.items)
        return sha([self.identity, item_keys])

    def sign(self, by: str) -> "Pool":
        """Freeze the pool. One-way: section 11.2 forbids later movement."""
        if not by:
            raise PoolViolation(f"{self.pool_id}: signing requires a signer")
        if self.signed:
            raise PoolViolation(
                f"{self.pool_id} is already signed by {self.signed_by!r}; once "
                "signed and hashed, items cannot move between pools "
                "(section 11.2)")
        if not self.populated:
            raise PoolViolation(
                f"{self.pool_id} has no contents to sign; authoring the material "
                "is a prerequisite, not a consequence, of signing")
        return Pool(pool_id=self.pool_id, pair=self.pair, kind=self.kind,
                    split=self.split, contents=self.contents,
                    stratum=self.stratum, signed_by=by)

    def populate(self, items: Sequence, by: str) -> "Pool":
        """Attach authored content, leaving the pool unsigned."""
        if self.signed:
            raise PoolViolation(
                f"{self.pool_id} is signed; its contents are frozen")
        if not items:
            raise PoolViolation(
                f"{self.pool_id}: an empty pool is a feasibility failure to "
                "report, not content to record (section 11.2)")
        return Pool(pool_id=self.pool_id, pair=self.pair, kind=self.kind,
                    split=self.split, contents=self.contents.freeze(tuple(items), by),
                    stratum=self.stratum, signed_by="")


# ------------------------------------------------------- two kinds of identity
#
# A pool item has two identities and they answer different questions. Collapsing
# them into one - which is what a single _item_key did - breaks whichever question
# it was not designed for.
#
#   CONTENT identity answers "has this material changed?". Section 11.2 says a
#   pool is "signed and hashed", and section 8.2 lists the fields that determine
#   how the material is interpreted: verifier and audit hashes, canonical
#   wording, output schema, parameter distribution, incompatibility and
#   entailment metadata, construction provenance. A signature over the
#   constraint_id alone could not detect any of those changing, so it certified
#   nothing it claimed to.
#
#   OVERLAP identity answers "is this the same scientific item as that one?".
#   Here the id matters: the same constraint appearing in two splits is leakage
#   even if one copy's metadata was edited, and a content-only key would stop
#   detecting that. But content matters too, because a renamed copy of identical
#   material is also leakage. So overlap uses the UNION of both.


def _content_key(item) -> str:
    """Canonical hash of an item's complete content, INCLUDING its declared id.

    Used for signing. The id belongs in the signature because it is how every
    other artifact references the constraint, so renaming an entry does change
    the signed material. Routed through the provenance layer's canonicaliser,
    which refuses values with no reproducible form rather than hashing them by
    identity.
    """
    if isinstance(item, BackgroundEntry):
        return sha(["v19/background-entry", dataclasses.asdict(item)])
    return sha(["v19/pool-item", item])


def _material_key(item) -> str:
    """Canonical hash of the item's content EXCLUDING its declared id.

    Used for overlap. Section 8.2 prohibits "semantic duplicates" as well as
    exact reuse, so a copy of identical material under a new label is still the
    same scientific item and still leakage. Keying overlap on the full content
    hash would miss precisely that, because the rename changes the hash.
    """
    if isinstance(item, BackgroundEntry):
        fields = dataclasses.asdict(item)
        fields.pop("constraint_id")
        return sha(["v19/background-material", fields])
    return sha(["v19/pool-item-material", item])


def _declared_id(item) -> str:
    """The item's declared identifier: a label, not a content address."""
    if isinstance(item, BackgroundEntry):
        return item.constraint_id
    return str(item)


def _overlap_keys(item) -> tuple[str, ...]:
    """Every identity under which this item counts as "the same item".

    The declared id and the id-free material hash, so leakage is caught whether
    the duplicate kept its name and edited its fields, or kept its fields and
    changed its name. Deliberately NOT the signing key, which includes the id.
    """
    return (f"id:{_declared_id(item)}", f"material:{_material_key(item)}")


def declare_pool(pool_id: str, pair: str, kind: str, split: str,
                 rule: str, stratum: str = "", note: str = "") -> Pool:
    """An empty declared pool: structure fixed, contents pending authorship."""
    return Pool(pool_id=pool_id, pair=pair, kind=kind, split=split,
                stratum=stratum,
                contents=pending(f"pool.{pool_id}", "section 11.1 / 8.2",
                                 Resolution.PENDING_CONTENT, rule, note=note))


# ------------------------------------------------------------------ invariants

def assert_splits_disjoint(pools: Sequence[Pool]) -> None:
    """No item may appear in two different splits (section 11.1).

    Only populated pools can be checked, and that is stated rather than hidden:
    a report over unpopulated pools would say "disjoint" about nothing.
    """
    where: dict[str, set[str]] = {}
    for pool in pools:
        if not pool.populated:
            continue
        for item in pool.items:
            for key in _overlap_keys(item):
                where.setdefault(key, set()).add(pool.split)
    shared = {item: sorted(splits) for item, splits in where.items()
              if len(splits) > 1}
    if shared:
        detail = "; ".join(f"{item} in {splits}"
                           for item, splits in sorted(shared.items())[:6])
        raise PoolViolation(
            f"{len(shared)} item(s) appear in more than one material split: "
            f"{detail}. Section 11.1 partitions all material that can affect a "
            "frozen scientific choice, so a shared item breaks the firewall "
            "between pre-freeze decisions and confirmatory content")


def assert_one_stratum_per_constraint(pools: Sequence[Pool]) -> None:
    """A background constraint belongs to exactly one stratum (section 8.2).

    Load-bearing rather than tidy: section 8.3 draws one identity from each
    stratum, so a constraint in two strata could be drawn twice into the same
    superblock and the stated proposal law would stop describing the sampler.
    """
    homes: dict[str, set[str]] = {}
    for pool in pools:
        if pool.kind != "background" or not pool.populated:
            continue
        for item in pool.items:
            homes.setdefault(_declared_id(item), set()).add(pool.stratum)
        for item in pool.items:
            if isinstance(item, BackgroundEntry) and item.stratum != pool.stratum:
                raise PoolViolation(
                    f"{item.constraint_id} is filed in the {pool.stratum!r} pool "
                    f"but declares stratum {item.stratum!r}")
    multiple = {c: sorted(s) for c, s in homes.items() if len(s) > 1}
    if multiple:
        raise PoolViolation(
            f"background constraints in more than one stratum: {multiple}. "
            "Section 8.3 draws one identity from each stratum, so this would "
            "let one constraint enter a superblock twice")


def assert_pool_excludes(pool: Pool, forbidden: Mapping[str, str]) -> None:
    """A pool may not contain the pair's own target, focal, or references.

    Section 8.2: "Neither pool may contain the pair's target, focal constraint,
    admitted references, semantic duplicates, known incompatible rules, or
    content allocated to another scientific split." `forbidden` maps an item
    identity to why it is excluded, so the error says which rule was broken.
    """
    if not pool.populated:
        return
    present = []
    for item in pool.items:
        for key in (_declared_id(item),) + _overlap_keys(item):
            if key in forbidden:
                present.append((_declared_id(item), forbidden[key]))
                break
    if present:
        detail = "; ".join(f"{item} ({why})" for item, why in present[:5])
        raise PoolViolation(
            f"{pool.pool_id} contains {len(present)} excluded item(s): {detail}")


def assert_no_declared_incompatibility(entries: Sequence[BackgroundEntry]) -> None:
    """Declared-incompatible constraints cannot co-occur in one composition.

    A pairwise check only. Section 8.7 is explicit that "individual constraint
    validity and pairwise compatibility are insufficient" and requires
    whole-composition certification, so this rejects the cases it can prove and
    makes no claim about the ones it cannot.
    """
    ids = {e.constraint_id for e in entries}
    for entry in entries:
        clash = sorted(ids & set(entry.incompatible_with))
        if clash:
            raise PoolViolation(
                f"{entry.constraint_id} is declared incompatible with {clash}, "
                "which are present in the same composition. This is a pairwise "
                "check only: section 8.7 still requires whole-composition "
                "certification, which this does not provide")


# ------------------------------------------------------- the declared registry

def _task_pool(pair: str, split: str) -> Pool:
    return declare_pool(
        f"{pair}.tasks.{split}", pair, "task", split,
        rule=f"authored disjoint {split.replace('_', ' ')} task/topic material "
             "under the versioned content procedure (section 11.1)")


def _background_pools(pair: str) -> tuple[Pool, ...]:
    return tuple(
        declare_pool(f"{pair}.backgrounds.{stratum}", pair, "background",
                     "confirmation",
                     rule="scope-compatible background identities with unique "
                          "ids, verifier and wording hashes, parameter "
                          "distributions and incompatibility metadata "
                          "(section 8.2)",
                     stratum=stratum)
        for stratum in STRATA)


def declared_pools() -> tuple[Pool, ...]:
    """Every pool the protocol requires, empty and unsigned.

    Six splits per pair for task material, the three confirmation background
    strata per pair, the per-pair unrelated-target and coupling-probe banks that
    reference construction needs, and the shared adapter/manipulation bank.
    """
    out: list[Pool] = []
    for pair in PAIR_IDS:
        for split in MATERIAL_SPLITS:
            out.append(_task_pool(pair, split))
        out.extend(_background_pools(pair))
        out.append(declare_pool(
            f"{pair}.unrelated_targets", pair, "unrelated_target",
            "reference_construction",
            rule="unrelated targets for outgoing-burden and incoming-"
                 "vulnerability estimation on disjoint material (section 7.3)"))
        out.append(declare_pool(
            f"{pair}.coupling_probes", pair, "coupling_probe",
            "reference_construction",
            rule="2,000 base outputs balanced across the four (Y_A, Y_R) cells, "
                 "with eight frozen truth-preserving nuisance classes "
                 "(section 7.7)",
            note="expansion to the smallest qualifying multiple of 500 requires "
                 "exact epsilon to be frozen first"))
        out.append(declare_pool(
            f"{pair}.wording_calibration", pair, "wording_calibration",
            "reference_construction",
            rule="N_W = 100 independent calibration tasks with G_W = 2 paired "
                 "replicates, common task identities across all 12 wordings "
                 "(section 7.9)"))
        out.append(declare_pool(
            f"{pair}.audit", pair, "audit", "development",
            rule="human-adjudicated examples with both true-pass and true-fail "
                 "support per Tier-1 verifier unit (section 10.4)",
            note="a missing truth class is missing evidence, not zero error: the "
                 "corresponding reliability bound is unavailable"))
    out.append(declare_pool(
        "shared.manipulation_prompts", "shared", "manipulation_prompt",
        ADAPTER_SPLIT,
        rule="adapter/manipulation prompt bank for hard-budget validation, "
             "demonstrably disjoint from every DCI content pool (section 11.1)"))
    return tuple(out)


def declared_slots() -> SlotTable:
    """Every pool's pending contents, for the completion audit."""
    return SlotTable(slots=tuple(p.contents for p in declared_pools()))


def sufficiency_slots() -> SlotTable:
    """Section 11.2's per-pair sufficiency counts, all pending.

    The gate must "establish that every target-focal pair has enough disjoint
    material for all six scientific pools and for every generative scope
    required by that pair". The counts are outputs of authoring the material.
    """
    return SlotTable(slots=tuple(
        pending(f"sufficiency.{pair}.{count}", "section 11.2",
                Resolution.PENDING_CONTENT,
                "the content-sufficiency report, counted separately by pair and "
                "generative scope before expensive calibration begins",
                note="a pair that cannot populate all required pools without "
                     "reuse is a pre-freeze feasibility failure")
        for pair in PAIR_IDS for count in SUFFICIENCY_COUNTS))


def sufficiency_report(pools: Sequence[Pool]) -> dict[str, dict[str, object]]:
    """What each pair's material currently supports, per split.

    Reports rather than asserts: the sufficiency thresholds are themselves
    pre-freeze outputs, so this supplies the counts the gate will judge and does
    not pretend to judge them.
    """
    out: dict[str, dict[str, object]] = {}
    for pair in PAIR_IDS:
        mine = [p for p in pools if p.pair == pair]
        per_split = {
            split: (len(p.items) if p.populated else None)
            for split in MATERIAL_SPLITS
            for p in mine if p.split == split and p.kind == "task"}
        out[pair] = {
            "task_items_by_split": per_split,
            "unpopulated_pools": sorted(p.pool_id for p in mine
                                        if not p.populated),
            "signed_pools": sorted(p.pool_id for p in mine if p.signed),
            "background_strata_populated": sorted(
                p.stratum for p in mine
                if p.kind == "background" and p.populated),
        }
    return out


def forbidden_items(pair_id: str) -> dict[str, str]:
    """Section 8.2's exclusion map for one pair, from the pair registry.

    "Neither pool may contain the pair's target, focal constraint, admitted
    references, semantic duplicates, known incompatible rules, or content
    allocated to another scientific split."

    This assembles the mechanically identifiable part: the pair's own target and
    focal constraint always, and its admitted references once Stage 8 has
    produced them. Semantic duplicates are deliberately absent - section 8.7
    assigns that determination to human review, and inventing an automatic
    equivalence judgement here would claim a certification the protocol does not
    grant. `semantic_duplicate_review` carries that obligation instead.
    """
    from dci.v19.pairs import pair as _pair

    pair = _pair(pair_id)
    out = {f"id:{pair.target.constraint_id}": "the pair's own target constraint",
           f"id:{pair.focal.constraint_id}": "the pair's own focal constraint"}
    for slot in pair.references:
        if slot.admitted:
            out[f"id:{slot.identity.get()}"] = (
                f"an admitted reference of {pair_id} ({slot.arm})")
    return out


def semantic_duplicate_review(pair_id: str) -> Slot:
    """The human-review artifact section 8.2's "semantic duplicates" needs.

    Declared rather than automated. Section 8.7 requires "two independent
    reviews, with a third reviewer adjudicating disagreement" for clauses whose
    semantics deterministic machinery does not exhaustively cover, and semantic
    equivalence between authored constraints is such a clause. Pretending code
    settles it would be a fabricated certification.
    """
    return pending(
        f"review.{pair_id}.semantic_duplicates", "sections 8.2, 8.7",
        Resolution.PENDING_DECISION,
        "two independent human reviews confirming that no pool contains a "
        "semantic duplicate of the pair's target, focal constraint or admitted "
        "references, with a third reviewer adjudicating disagreement",
        depends_on=(f"pool.{pair_id}.candidate_references",),
        note="unresolved disagreement fails certification; deterministic overlap "
             "checks cover exact reuse and renamed identical content, not "
             "semantic equivalence")


def assert_ready_for_confirmation(
        pools: Sequence[Pool],
        exclusions: Optional[Mapping[str, str]] = None) -> None:
    """The one gate before confirmatory drawing. Enforces, not just signatures.

    Signing each pool individually proves nothing about the partition: two
    separately valid signed pools can share an item, and section 11.1's firewall
    is a property of the set. So this invokes every cross-pool invariant rather
    than leaving them as helpers a caller might forget - which is exactly what
    happened, since none of them had a production caller.

    `exclusions` defaults to the union of every declared pair's forbidden map, so
    the common case needs no argument and cannot be silently skipped.
    """
    problems = []
    for pool in pools:
        if not pool.populated:
            problems.append(f"{pool.pool_id} has no authored content")
        elif not pool.signed:
            problems.append(f"{pool.pool_id} is populated but unsigned")
    if problems:
        raise UnresolvedDependency(
            "confirmatory superblock drawing needs every scientific pool signed "
            f"and hashed; {len(problems)} are not ready:\n  "
            + "\n  ".join(problems[:10]))

    # Cross-pool invariants. Each raises PoolViolation, which is fail-closed and
    # distinct from the "not authored yet" condition above.
    assert_splits_disjoint(pools)
    assert_one_stratum_per_constraint(pools)

    if exclusions is None:
        exclusions = {}
        for pair_id in PAIR_IDS:
            exclusions.update(forbidden_items(pair_id))
    for pool in pools:
        assert_pool_excludes(pool, exclusions)

    entries = [item for pool in pools if pool.populated
               for item in pool.items if isinstance(item, BackgroundEntry)]
    if entries:
        assert_no_declared_incompatibility(entries)
