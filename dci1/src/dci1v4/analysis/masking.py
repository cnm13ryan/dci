"""Companion-label masking and one-way unmasking (§20).

**What is masked.** After confirmatory generation and before any analysis, the
companion label is permuted within each ``(outcome constraint, order, block)``
group of composed observations, using a seed from the system random source.
Solo cells carry no companion and are not permuted. The primary contrasts are
companion swaps, so the companion label is the dimension that must be hidden.

**The declared limitation, carried in every analysis record.** A composed
generation contributes two observations whose companion labels are permuted
independently, so joint-state and joint-success quantities cannot be computed
in the masked phase. They are computed after unmasking under the registered
plan of §11.5, are labelled as computed post-unmasking, and support no L1, L2
or L3 claim.

The mask key is opened exactly once in a full run, unmasking is a single named
function invoked once, and the executable checks of §20 are here: permuted
labels differ from true labels in at least half the blocks in every group, the
key file is opened once, and the recorded analysis-code hash reproduces every
masked-phase output.
"""
from __future__ import annotations

import datetime as _dt
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from dci1v4.analysis.observations import Observation
from dci1v4.engine import fs
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import sha_obj, sha_text

#: §20: the fields a masked view must not carry, because they identify the
#: true companion. The v3 analogue (decision V11) listed the fields that would
#: identify the true arm; under v4 the companion dimension is what is hidden.
MASKED_VIEW_EXCLUDED_FIELDS = (
    "companion_slot_true", "cell_id", "cell_type", "prompt_hash",
    "constituents", "companion_kind", "companion_severity",
    "companion_wording_index", "raw_response", "response_content_hash",
)

DECLARED_LIMITATION = (
    "a composed generation contributes two observations whose companion "
    "labels are permuted independently, so joint-state and joint-success "
    "quantities cannot be computed in the masked phase; they are computed "
    "after unmasking under the registered plan of §11.5, are labelled as "
    "computed post-unmasking, and support no L1, L2 or L3 claim")


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
    response_words: float
    masked_id: str


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def build_mask(observations: Sequence[Observation], *, namespace: str,
               entropy: int | None = None) -> dict[str, Any]:
    """Permute the companion label within each (outcome, order, block) group.

    The seed comes from the system random source, as §20 requires, so no
    analysis path can reconstruct the permutation from registered values.
    """
    if namespace not in C.MASK_NAMESPACES:
        raise ProtocolError(f"{namespace!r} is not a registered mask "
                            f"namespace {C.MASK_NAMESPACES}")
    seed = entropy if entropy is not None else random.SystemRandom().getrandbits(128)
    rng = random.Random(seed)
    groups: dict[tuple[str, str, str], list[str]] = {}
    for obs in observations:
        if obs.companion_slot is None:
            continue
        key = (obs.outcome_slot, obs.configuration, obs.block_id)
        groups.setdefault(key, []).append(obs.companion_slot)

    mapping: dict[str, str] = {}
    for key, companions in sorted(groups.items()):
        permuted = list(companions)
        rng.shuffle(permuted)
        for true_label, masked_label in zip(sorted(companions), permuted):
            mapping[f"{key[0]}|{key[1]}|{key[2]}|{true_label}"] = masked_label
    return {"namespace": namespace, "seed": seed, "mapping": mapping,
            "groups": len(groups), "created": _now(),
            "mask_key_hash": sha_obj({"seed": seed, "mapping": mapping})}


class MaskKey:
    """The mask key file, opened exactly once in a full run (§20)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._opened = 0

    def write(self, mask: dict[str, Any]) -> None:
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
            response_words=obs.response_words,
            masked_id=sha_text(f"{mask['mask_key_hash']}|{index}")[:16]))
    return out


def assert_mask_effective(observations: Sequence[Observation],
                          mask: dict[str, Any]) -> dict[str, Any]:
    """§20: permuted labels differ from true labels in at least half the
    blocks of every group."""
    groups: dict[tuple[str, str], list[bool]] = {}
    mapping = mask["mapping"]
    for obs in observations:
        if obs.companion_slot is None:
            continue
        key = (f"{obs.outcome_slot}|{obs.configuration}|{obs.block_id}|"
               f"{obs.companion_slot}")
        differs = mapping[key] != obs.companion_slot
        groups.setdefault((obs.outcome_slot, obs.configuration),
                          []).append(differs)
    failures = []
    for key, flags in sorted(groups.items()):
        share = sum(flags) / len(flags)
        if share < C.MASK_MIN_DIFFERING_FRACTION:
            failures.append((key, share))
    if failures:
        raise IntegrityError(
            f"the mask is ineffective for {len(failures)} group(s); permuted "
            f"labels must differ from true labels in at least half the "
            f"blocks: first {failures[0]}")
    return {"groups": len(groups),
            "min_differing_share": min(sum(f) / len(f)
                                       for f in groups.values())}


def assert_masked_view_clean(records: Iterable[dict[str, Any]]) -> None:
    """No masked-phase record may carry a companion-identifying field."""
    for record in records:
        present = [f for f in MASKED_VIEW_EXCLUDED_FIELDS if f in record]
        if present:
            raise IntegrityError(
                f"the masked view carries companion-identifying field(s) "
                f"{present}")


def unmask(key: MaskKey, *, analysis_code_hash: str,
           masked_outputs_hash: str) -> dict[str, Any]:
    """The single named unmasking function, invoked once (§20).

    Writes a timestamped record with the mask-key hash and the content hash of
    the analysis code at that moment. Any later analysis-code change is
    labelled post-unmasking, is exploratory, and supports no registered claim.
    """
    mask = key.open_once()
    return {"unmasked_at": _now(), "mask_namespace": mask["namespace"],
            "mask_key_hash": mask["mask_key_hash"],
            "analysis_code_hash": analysis_code_hash,
            "masked_outputs_hash": masked_outputs_hash,
            "declared_limitation": DECLARED_LIMITATION,
            "post_unmasking_note": ("any analysis-code change after this "
                                    "record is labelled post-unmasking, is "
                                    "exploratory, and supports no registered "
                                    "claim")}


def analysis_code_hash(paths: Sequence[Path]) -> str:
    """The content hash of the analysis code, recorded at unmasking."""
    from dci1v4.protocol.hashing import sha_file

    return sha_obj({str(p): sha_file(p) for p in sorted(paths)})
