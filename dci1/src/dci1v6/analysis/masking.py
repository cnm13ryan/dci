"""Companion-label masking and one-way unmasking (§20).

**What is masked.** After confirmatory generation and before any analysis, the
companion label is permuted within each ``(outcome constraint, configuration,
block)`` group of composed observations, using a seed from the system random
source. Solo and unconstrained cells carry no companion and are not permuted.
The primary contrasts are companion swaps, so the companion label is the
dimension that has to be hidden.

**What v4r3 adds to v4r2's §20, declared rather than discovered.** Permuting
companion labels within an outcome-and-configuration group permutes which
``D(B <- .)`` belongs to which companion, so the masked-phase fit of §11.7 is a
fit of the same nine losses against a *permuted* assignment of difficulties.
That is the intended protection: decisions about the fit --- its diagnostics,
its degenerate-replicate handling, its support reporting --- are made without
knowing which point is which.

The companion **difficulties** are not permuted. They come from solo and
unconstrained cells, they are pre-treatment quantities fixed at Gate 3, and
nothing about them can be tuned, so the difficulty coordinate is visible in the
masked phase deliberately.

``A``'s point sits inside the permuted group, so **delta_difficulty is not
computable in the masked phase** and is computed after unmasking under the
fully registered plan, labelled as such. `assert_delta_difficulty_not_masked`
puts that on the execution path instead of in a comment.
"""
from __future__ import annotations

import datetime as _dt
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import sha_obj, sha_text

from dci1v6.analysis.observations import Observation
from dci1v6.protocol import constants as C

__all__ = ["MASKED_VIEW_EXCLUDED_FIELDS", "DECLARED_LIMITATION",
           "MASKED_PHASE_DECLARATIONS", "MaskedObservation", "MaskKey",
           "build_mask", "apply_mask", "assert_mask_effective",
           "assert_masked_view_clean",
           "assert_delta_difficulty_not_masked", "masked_cell_id",
           "permutation_groups", "unmoved_companions",
           "masked_phase_order_contrasts", "unmask", "analysis_code_hash"]

#: §20: fields a masked view must not carry, because they identify the true
#: companion.
#: §20: fields a masked view must not carry, because they identify the true
#: companion. ``cell_id`` names the constituents, ``prompt_hash`` is invertible
#: by rendering candidates, and ``raw_response`` states the constraints in
#: words.
#:
#: ``arm`` was listed here and is **not** one of them. It takes three
#: design-level values --- ``unconstrained``, ``solo``, ``composed`` --- and
#: the permutation moves labels *within* an (outcome, configuration, block)
#: group, every composed member of which carries the same value. So ``arm`` is
#: constant across everything the mask could have swapped and narrows the true
#: companion not at all; the integration test asserts that property over the
#: written artifact rather than leaving the argument in prose.
#:
#: It was removed because the masked analysis cannot build an observation
#: table without separating §25's load-0 cell from a solo cell, so excluding
#: it bought no protection and made the masked stage unrunnable.
MASKED_VIEW_EXCLUDED_FIELDS = (
    "companion_slot_true", "companion_slot", "cell_id", "prompt_hash",
    "constituents", "companion_kind", "companion_severity",
    "companion_wording_index", "raw_response", "response_content_hash",
)

DECLARED_LIMITATION = (
    "a composed generation contributes two observations whose companion "
    "labels are permuted independently, so joint-state and joint-success "
    "quantities cannot be computed in the masked phase; they are computed "
    "after unmasking under the registered plan of §11.5, are labelled as "
    "computed post-unmasking, and support no L1, L2 or L3 claim")

MASKED_PHASE_DECLARATIONS = {
    "difficulty_relation": (
        "the masked-phase fit is a fit of the same losses against a permuted "
        "assignment of difficulties; that is the intended protection"),
    "difficulty_coordinate": (
        "companion difficulties come from solo and unconstrained cells and "
        "are NOT permuted: they are pre-treatment quantities fixed at Gate 3 "
        "and nothing about them can be tuned"),
    "delta_difficulty": (
        "A's point is inside the permuted group, so delta_difficulty is not "
        "computable in the masked phase and is computed after unmasking "
        "under the fully registered plan, labelled as such"),
    "joint_quantities": DECLARED_LIMITATION,
}

#: Members that may not appear in a masked-phase result (§20).
#: §20 names these as **not computable in the masked phase**: A's point is
#: inside the permuted group, so both the residual and the excess are contrasts
#: of A against a set A may have been permuted into. ``Delta_R`` was missing
#: here while §20's text named it, so the masked record carried an estimate of
#: the study's primary quantity computed against a permuted assignment of
#: companions --- the one number the mask exists to withhold.
#: ``gamma_tier`` is the fifth coefficient of the same §11.8 fit as ``beta``
#: and the three intercepts, and §20 names *"the fit's coefficients"*. It was
#: missing here for the same reason ``Delta_R`` once was --- and it could not
#: be noticed, because F8 had no producer on any path until A4.
MASKED_PHASE_FORBIDDEN_MEMBERS = ("delta_difficulty", "Delta_R", "beta",
                                  "alpha_1", "alpha_2", "alpha_3",
                                  "gamma_tier")

#: The companions of each outcome that share a permutation group. §20's rule
#: for masked-phase computability is that a member is computable when every
#: companion it reads is **alone** in its (outcome, configuration) group ---
#: a permutation of one element is the identity, so that label did not move.
#: §20 states the consequence for the reduced arm set as an example: Ord_A
#: differences the two A+B cells, and in the reduced set B is A's only
#: companion, so it is computable there; Ord_Rbar averages over permuted
#: labels and is not.


def permutation_groups(mask: Mapping[str, Any]
                       ) -> dict[tuple[str, str], set[str]]:
    """The companion labels sharing each (outcome, configuration) group."""
    groups: dict[tuple[str, str], set[str]] = {}
    for key in mask["mapping"]:
        outcome, configuration, _block, companion = key.split("|")
        groups.setdefault((outcome, configuration), set()).add(companion)
    return groups


def unmoved_companions(mask: Mapping[str, Any]) -> set[tuple[str, str]]:
    """The (outcome, companion) pairs no permutation could have moved."""
    out: set[tuple[str, str]] = set()
    for (outcome, _configuration), companions in \
            permutation_groups(mask).items():
        if len(companions) == 1:
            out.add((outcome, next(iter(companions))))
    return out


def masked_phase_order_contrasts(mask: Mapping[str, Any]
                                 ) -> dict[str, Any]:
    """§20's **one named function**: which order contrasts are computable now.

    §20 requires this to be *derived* from the realised design and *recorded
    on the masked record* rather than assumed, because the answer depends on
    the admitted arm set: under §8.6's reduced set B is A's only companion and
    ``Ord_A`` is computable; under the full set it is not.

    A contrast is computable when every (outcome, companion) pair it reads is
    unmoved --- alone in its permutation group, where a permutation is the
    identity.
    """
    reads = {
        "Ord_A": (("A", "B"),),
        "Ord_B": (("B", "A"),),
        "Ord_Lambda": (("A", "B"), ("B", "A")),
        # The reference mean averages over every core companion of B, so it
        # reads whatever the permutation moved.
        "Ord_Rbar": tuple(("B", slot) for slot in C.CORE_SLOTS),
        "Ord_CL": (("B", C.CLASS_SLOT),),
    }
    unmoved = unmoved_companions(mask)
    computable = {name: all(pair in unmoved for pair in pairs)
                  for name, pairs in reads.items()}
    return {
        "computable": sorted(k for k, v in computable.items() if v),
        "not_computable": sorted(k for k, v in computable.items() if not v),
        "reads": {k: [list(p) for p in v] for k, v in reads.items()},
        "unmoved_companions": sorted(f"{o}<-{g}" for o, g in unmoved),
        "rule": "§20: a contrast is masked-phase computable when every "
                "(outcome, companion) pair it reads is alone in its "
                "permutation group, because a permutation of one element is "
                "the identity",
    }


@dataclass(frozen=True)
class MaskedObservation:
    """One observation with its companion label permuted.

    **Structure is not identity.** The masked analysis has to be able to tell
    a solo cell from an unconstrained one from a composed one, and a stated
    verdict from a §9.1 absent verdict, or it cannot build an observation
    table at all --- and none of those facts says *which* companion a cell
    carried. So ``arm``, ``present``, ``draws`` and ``processing_failures``
    travel, while ``cell_id`` and the true ``companion_slot`` do not; the
    cell's identity is replaced by ``masked_cell_id``, which is derived from
    the **permuted** label and therefore groups the same observations together
    without saying what they are.

    An earlier revision omitted all five. The masked view was then unusable as
    an analysis input --- a solo cell and an unconstrained cell were
    indistinguishable, and rebuilding an ``Observation`` from it raised on the
    missing arguments --- which is why the masked stage had never run.
    """

    block_id: str
    outcome_slot: str
    companion_label: str | None
    configuration: str | None
    position: int
    compliance: float
    graded: float
    vacuity: float
    truncation: float
    non_vacuous_compliance: float
    graded_threshold: float
    response_words: float
    masked_id: str
    #: `unconstrained` | `solo` | `composed`. The design's arm names carry no
    #: companion identity: `composed` does not say composed with what.
    arm: str = "composed"
    #: §9.1. False is a verdict on a constraint the prompt did not state.
    present: bool = True
    draws: int = 0
    processing_failures: int = 0
    #: The cell's identity under the permutation, so absent verdicts stay
    #: indexable without the true constituents appearing anywhere.
    masked_cell_id: str = ""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _non_identity_permutation(labels: Sequence[str],
                              rng: random.Random) -> list[str]:
    """A uniform permutation of ``labels`` that fixes none of them.

    Rejection sampling, which is exact and terminates quickly: the share of
    permutations of k elements with no fixed point is at least 1/3 for every
    k >= 2, so the expected number of draws is under three.
    """
    ordered = list(labels)
    if len(ordered) < 2:
        return ordered
    while True:
        candidate = list(ordered)
        rng.shuffle(candidate)
        if all(a != b for a, b in zip(ordered, candidate)):
            return candidate


def build_mask(observations: Sequence[Observation], *, namespace: str,
               entropy: int | None = None) -> dict[str, Any]:
    """Permute the companion label within each (outcome, configuration, block).

    The seed comes from the system random source, as §20 requires, so no
    analysis path can reconstruct the permutation from registered values.
    ``entropy`` exists for the §19 pilot and for tests, and a registered
    confirmatory mask never supplies it.

    **Stratified, not independent, and the reason is arithmetic** (§20-R4). An
    independent uniform permutation per block moves a given label with
    probability ``1 - 1/k`` for a group of ``k`` companions. §8.6's reduced
    design gives ``B`` exactly two companions, ``A`` and the class companion,
    so ``1 - 1/k`` is **0.5** --- which is `MASK_MIN_DIFFERING_FRACTION`
    exactly. The mask's own effectiveness check then fails about half the time
    by chance, on a design that is otherwise perfectly maskable, and halts the
    replication for a coin flip.

    So the number of blocks that receive a non-identity permutation is fixed
    at ``ceil(N * target)`` rather than left to the binomial, and *which*
    blocks they are is drawn uniformly without replacement. Nothing about any
    one block becomes predictable: an analyst learns how many blocks moved,
    which is a registered constant, and not which. The criterion is unchanged
    and is now met by construction instead of in expectation.
    """
    if namespace not in C.MASK_NAMESPACES:
        raise ProtocolError(f"{namespace!r} is not a registered mask "
                            f"namespace {C.MASK_NAMESPACES}")
    seed = (entropy if entropy is not None
            else random.SystemRandom().getrandbits(128))
    rng = random.Random(seed)
    groups: dict[tuple[str, str, str], list[str]] = {}
    for obs in observations:
        if obs.companion_slot is None:
            continue
        key = (obs.outcome_slot, obs.configuration, obs.block_id)
        entry = groups.setdefault(key, [])
        if obs.companion_slot not in entry:
            entry.append(obs.companion_slot)

    # Blocks that share an (outcome, configuration) are one stratum: that is
    # the unit `assert_mask_effective` measures over.
    strata: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for key in sorted(groups):
        strata.setdefault((key[0], key[1]), []).append(key)

    mapping: dict[str, str] = {}
    plan: dict[str, dict[str, Any]] = {}
    for stratum, keys in sorted(strata.items()):
        sizes = {len(groups[k]) for k in keys}
        k = min(sizes)
        target = (0.0 if k < 2
                  else max(C.MASK_MIN_DIFFERING_FRACTION, 1.0 - 1.0 / k))
        wanted = math.ceil(len(keys) * target)
        moved = set(rng.sample(range(len(keys)), wanted)) if wanted else set()
        plan["|".join(stratum)] = {"blocks": len(keys), "companions": k,
                                   "target": target, "non_identity": wanted}
        for index, key in enumerate(keys):
            labels = sorted(groups[key])
            permuted = (_non_identity_permutation(labels, rng)
                        if index in moved else list(labels))
            for true_label, masked_label in zip(labels, permuted):
                mapping[f"{key[0]}|{key[1]}|{key[2]}|{true_label}"] = \
                    masked_label
    return {"namespace": namespace, "seed": seed, "mapping": mapping,
            "groups": len(groups), "created": _now(),
            "stratification": plan,
            "declarations": dict(MASKED_PHASE_DECLARATIONS),
            "mask_key_hash": sha_obj({"seed": seed, "mapping": mapping})}


class MaskKey:
    """The mask key file, opened exactly once in a full run (§20)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._opened = 0

    def write(self, mask: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fs.write_json_once(self.path, mask)

    def open_once(self) -> dict[str, Any]:
        if self._opened:
            raise IntegrityError(
                f"the mask key at {self.path} was already opened in this run; "
                f"§20 permits exactly one open")
        self._opened += 1
        return fs.read_json(self.path)

    @property
    def opens(self) -> int:
        return self._opened


def apply_mask(observations: Sequence[Observation], mask: dict[str, Any]
               ) -> list[MaskedObservation]:
    """The masked view. Solo observations pass through unpermuted."""
    mapping = mask["mapping"]
    out: list[MaskedObservation] = []
    for index, obs in enumerate(observations):
        if obs.companion_slot is None:
            label = None
        else:
            key = (f"{obs.outcome_slot}|{obs.configuration}|{obs.block_id}|"
                   f"{obs.companion_slot}")
            if key not in mapping:
                raise IntegrityError(f"no mask entry for {key}")
            label = mapping[key]
        out.append(MaskedObservation(
            block_id=obs.block_id, outcome_slot=obs.outcome_slot,
            companion_label=label, configuration=obs.configuration,
            position=obs.position, compliance=obs.compliance,
            graded=obs.graded, vacuity=obs.vacuity,
            truncation=obs.truncation,
            non_vacuous_compliance=obs.non_vacuous_compliance,
            graded_threshold=obs.graded_threshold,
            response_words=obs.response_words,
            masked_id=sha_text(f"{mask['mask_key_hash']}|{index}")[:16],
            arm=obs.arm, present=obs.present, draws=obs.draws,
            processing_failures=obs.processing_failures,
            masked_cell_id=masked_cell_id(obs, mask["mask_key_hash"])))
    return out


def masked_cell_id(obs: Observation, mask_key_hash: str) -> str:
    """A stable pseudonym for the cell an observation came from.

    ``ObservationTable`` indexes §9.1 absent verdicts by the cell they were
    read from, so the masked table needs a per-cell key --- and the true
    ``cell_id`` names the cell's constituents, which is the one thing the mask
    exists to hide. The pseudonym is a hash under the sealed mask key, exactly
    as ``masked_id`` is: observations of one cell keep the same key, so the
    table's duplicate check still works, and the key says nothing about which
    constraints the cell stated.

    Solo and unconstrained cells need no pseudonym. Neither has a companion,
    and their own key already names only the outcome slot.
    """
    if obs.arm == "unconstrained":
        return f"unconstrained|{obs.block_id}"
    if obs.companion_slot is None and obs.present:
        return f"solo|{obs.block_id}|{obs.outcome_slot}"
    return "cell|" + sha_text(
        f"{mask_key_hash}|{obs.block_id}|{obs.cell_id}")[:16]


def assert_mask_effective(observations: Sequence[Observation],
                          mask: dict[str, Any]) -> dict[str, Any]:
    """§20: permuted labels differ from true labels in at least half the
    blocks of every group."""
    mapping = mask["mapping"]
    groups: dict[tuple[str, str], list[bool]] = {}
    companions: dict[tuple[str, str], set[str]] = {}
    for obs in observations:
        if obs.companion_slot is None:
            continue
        key = (f"{obs.outcome_slot}|{obs.configuration}|{obs.block_id}|"
               f"{obs.companion_slot}")
        index = (obs.outcome_slot, obs.configuration)
        groups.setdefault(index, []).append(
            mapping[key] != obs.companion_slot)
        companions.setdefault(index, set()).add(obs.companion_slot)

    # A group with one companion cannot be permuted: a permutation of one
    # element is the identity. In v4r3 this is a property of the DESIGN, not a
    # defect in the mask. The spectrum rungs and the class companion pair with
    # B alone (§8.1), so with one of them as the OUTCOME the only companion is
    # B, and "the companion was B" is not information because it could not
    # have been anything else. v4r2's block was a full matrix and had no such
    # group, which is why §20 did not have to say this.
    singleton = sorted(k for k, v in companions.items() if len(v) < 2)
    maskable = {k: v for k, v in groups.items() if k not in singleton}
    failures = [(k, sum(f) / len(f)) for k, f in sorted(maskable.items())
                if sum(f) / len(f) < C.MASK_MIN_DIFFERING_FRACTION]
    if failures:
        raise IntegrityError(
            f"the mask is ineffective for {len(failures)} group(s); permuted "
            f"labels must differ from true labels in at least half the "
            f"blocks: first {failures[0]}")
    return {
        "groups": len(groups), "maskable_groups": len(maskable),
        "min_differing_share": min((sum(f) / len(f)
                                    for f in maskable.values()), default=None),
        "structurally_unmaskable": [list(k) for k in singleton],
        "structurally_unmaskable_outcomes": sorted({k[0] for k in singleton}),
        "structurally_unmaskable_note": (
            "these (outcome, configuration) groups carry exactly one "
            "companion, because §8.1's spectrum and class arms pair with B "
            "alone, so their companion label is not hidden and could not be. "
            "Under the full and no-spectrum designs that costs nothing: the "
            "singleton outcomes are the spectrum rungs and the class "
            "companion, and no registered estimand reads them as an OUTCOME "
            "-- F8 reads D(B <- R_j+-) and F9 reads D(B <- CL), both with B "
            "as the outcome and masked among its many companions. Under "
            "§8.6's REDUCED design it costs something and the cost is stated "
            "rather than implied: B has exactly two companions (A and the "
            "class companion) and is masked among them, while A and CL each "
            "have only B, so D(A <- B) -- a registered reduced-design "
            "estimand -- and any CL-as-outcome quantity are analysed with "
            "their companion identity visible. The masked phase protects "
            "D(B <- A), D(B <- CL) and Lambda on that design, and does not "
            "protect the reciprocal direction. This sentence used to assert "
            "the full-design case unconditionally, which is false for a "
            "reduced replication"),
    }


def assert_masked_view_clean(records: Iterable[dict[str, Any]]) -> None:
    """No masked-phase record may carry a companion-identifying field."""
    for record in records:
        present = [f for f in MASKED_VIEW_EXCLUDED_FIELDS if f in record]
        if present:
            raise IntegrityError(
                f"the masked view carries companion-identifying field(s) "
                f"{present}")


def assert_delta_difficulty_not_masked(result: dict[str, Any]) -> None:
    """§20: delta_difficulty and the fit's coefficients are post-unmasking.

    A's point is inside the permuted group, so a masked-phase value for any of
    them would be a value computed against a permuted assignment of
    difficulties and would mean nothing. This is on the execution path so that
    the declaration cannot drift from what the pipeline does.
    """
    found: list[str] = []
    # The result's own shape: one bucket per configuration plus the
    # cross-configuration bucket, each mapping member -> entry. This used to
    # read ``result["families"]``, a key no estimate record has ever carried,
    # so the guard ran on an empty dict and could not fail --- a check on the
    # execution path that was not checking anything.
    buckets = list((result.get("configurations") or {}).values())
    buckets.append(result.get("cross_configuration") or {})
    for bucket in buckets:
        for member, entry in bucket.items():
            if member.split("|")[0] not in MASKED_PHASE_FORBIDDEN_MEMBERS:
                continue
            if isinstance(entry, Mapping) and entry.get("point") is not None:
                found.append(member)
    for key in (result.get("intervals") or {}):
        for member in (result["intervals"][key] or {}):
            if member.split("|")[0] in MASKED_PHASE_FORBIDDEN_MEMBERS:
                found.append(f"{key}:{member}")
    if found:
        raise IntegrityError(
            f"a masked-phase result carries {sorted(set(found))}, which §20 "
            f"computes only after unmasking: A's point is inside the permuted "
            f"group, so a masked value for it is a value against a permuted "
            f"assignment of difficulties")


def unmask(key: MaskKey, *, analysis_code_hash: str,
           masked_outputs_hash: str) -> dict[str, Any]:
    """The single named unmasking function, invoked once (§20)."""
    mask = key.open_once()
    return {"unmasked_at": _now(), "mask_namespace": mask["namespace"],
            "mask_key_hash": mask["mask_key_hash"],
            "analysis_code_hash": analysis_code_hash,
            "masked_outputs_hash": masked_outputs_hash,
            "declared_limitation": DECLARED_LIMITATION,
            "declarations": dict(MASKED_PHASE_DECLARATIONS),
            "post_unmasking_note": ("any analysis-code change after this "
                                    "record is labelled post-unmasking, is "
                                    "exploratory, and supports no registered "
                                    "claim")}


def analysis_code_hash(paths: Sequence[Path]) -> str:
    """The content hash of the analysis code, recorded at unmasking."""
    from dci1v4.protocol.hashing import sha_file

    return sha_obj({str(p): sha_file(p) for p in sorted(paths)})
