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
from typing import Any, Iterable, Sequence

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import sha_obj, sha_text

from dci1v4r4.analysis.observations import Observation
from dci1v4r4.protocol import constants as C

__all__ = ["MASKED_VIEW_EXCLUDED_FIELDS", "DECLARED_LIMITATION",
           "MASKED_PHASE_DECLARATIONS", "MaskedObservation", "MaskKey",
           "build_mask", "apply_mask", "assert_mask_effective",
           "assert_masked_view_clean",
           "assert_delta_difficulty_not_masked", "unmask",
           "analysis_code_hash"]

#: §20: fields a masked view must not carry, because they identify the true
#: companion.
MASKED_VIEW_EXCLUDED_FIELDS = (
    "companion_slot_true", "companion_slot", "cell_id", "arm", "prompt_hash",
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
MASKED_PHASE_FORBIDDEN_MEMBERS = ("delta_difficulty", "beta", "alpha_1",
                                  "alpha_2", "alpha_3")


@dataclass(frozen=True)
class MaskedObservation:
    """One observation with its companion label permuted."""

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
            masked_id=sha_text(f"{mask['mask_key_hash']}|{index}")[:16]))
    return out


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
        "structurally_unmaskable_note": (
            "these (outcome, configuration) groups carry exactly one "
            "companion because the spectrum and class arms pair with B alone, "
            "so their companion label is not hidden and could not be. No "
            "registered estimand reads them as an OUTCOME: F8 reads "
            "D(B <- R_j+-) and F9 reads D(B <- CL), both of which have B as "
            "the outcome and are masked among ten companions"),
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
    for family in (result.get("families") or {}).values():
        for member in (family.get("members") or {}):
            if member.split("|")[0] in MASKED_PHASE_FORBIDDEN_MEMBERS:
                found.append(member)
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
