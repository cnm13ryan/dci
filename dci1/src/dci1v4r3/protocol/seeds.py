"""Frozen v4r3 seed derivations (§14.2, §17.1, §26).

Fresh roots and fresh domain-separation strings. No ``dci1v3:``, ``dci1v4:``
or screen domain is reachable from this module, so no v4r3 draw can coincide
with a draw of any earlier study or screen even where the prompt text is
identical -- which it sometimes is, because v4r3 carries v4r2's topic split
and several of its wordings unchanged.

Every derivation names its inputs and fails on a missing one; there are no
hidden seed defaults, and there is no primary-draw selector, because §8.2
averages all M draws into the cell mean.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int

# --------------------------------------------------------------- root seeds
#: Drawn fresh for v4r3 on 21 August 2026. Distinct from every v3 root
#: (202608170-175), every v4r2 root (202608190-195) and every screen root
#: (202608200, 202608210, 202608220, 202608230) by construction.
GENERATION_ROOT_SEED = 202608240
BOOTSTRAP_ROOT_SEED = 202608241
GATE1_SAMPLE_SEED = 202608242
AUTORATER_SPLIT_SEED = 202608243
ADVERSARIAL_SEED = 202608244
MASK_ROOT_SEED = 202608245

# --------------------------------------------------- domain separation (v4r3)
DOMAIN_GENERATION = "dci1v4r3:gen:v1"
DOMAIN_BOOTSTRAP = "dci1v4r3:boot:v1"
DOMAIN_GATE1_SAMPLE = "dci1v4r3:gate1:v1"
DOMAIN_AUTORATER_SPLIT = "dci1v4r3:autorater-split:v1"
DOMAIN_ANNOTATION_ORDER = "dci1v4r3:annotation-order:v1"
DOMAIN_ADVERSARIAL = "dci1v4r3:adversarial:v1"
DOMAIN_MASK = "dci1v4r3:mask:v1"

V4R3_DOMAINS = (DOMAIN_GENERATION, DOMAIN_BOOTSTRAP, DOMAIN_GATE1_SAMPLE,
                DOMAIN_AUTORATER_SPLIT, DOMAIN_ANNOTATION_ORDER,
                DOMAIN_ADVERSARIAL, DOMAIN_MASK)

#: §6.2 carries v4r2's topic split unchanged, so the split seed is v4r2's and
#: is deliberately NOT re-drawn: a fresh seed would cut the bank differently
#: and make the two studies' development sets non-comparable for no gain.
CARRIED_TOPIC_SPLIT_SEED = 202608192


def _require(**inputs) -> None:
    for name, value in inputs.items():
        if value is None or value == "":
            raise ProtocolError(f"seed derivation missing input {name!r}; "
                                f"hidden seed defaults are prohibited")


def generation_seed(stage: str, model_id: str, prompt_hash: str,
                    draw_index: int) -> int:
    """§14.2: root, stage label, model identity, prompt hash, draw index."""
    _require(stage=stage, model_id=model_id, prompt_hash=prompt_hash)
    if draw_index is None or draw_index < 0:
        raise ProtocolError("draw index must be a non-negative integer")
    return domain_int(DOMAIN_GENERATION, GENERATION_ROOT_SEED, stage,
                      model_id, prompt_hash, draw_index)


def bootstrap_seed(estimand: str, model_id: str) -> int:
    _require(estimand=estimand, model_id=model_id)
    return domain_int(DOMAIN_BOOTSTRAP, BOOTSTRAP_ROOT_SEED, estimand,
                      model_id)


def gate1_sample_seed(instrument: str, stratum: str) -> int:
    _require(instrument=instrument, stratum=stratum)
    return domain_int(DOMAIN_GATE1_SAMPLE, GATE1_SAMPLE_SEED, instrument,
                      stratum)


def adversarial_seed(instrument: str) -> int:
    _require(instrument=instrument)
    return domain_int(DOMAIN_ADVERSARIAL, ADVERSARIAL_SEED, instrument)


__all__ = ["GENERATION_ROOT_SEED", "BOOTSTRAP_ROOT_SEED", "GATE1_SAMPLE_SEED",
           "AUTORATER_SPLIT_SEED", "ADVERSARIAL_SEED", "MASK_ROOT_SEED",
           "V4R3_DOMAINS", "CARRIED_TOPIC_SPLIT_SEED", "generation_seed",
           "bootstrap_seed", "gate1_sample_seed", "adversarial_seed",
           "DOMAIN_GENERATION", "DOMAIN_BOOTSTRAP", "DOMAIN_GATE1_SAMPLE",
           "DOMAIN_AUTORATER_SPLIT", "DOMAIN_ANNOTATION_ORDER",
           "DOMAIN_ADVERSARIAL", "DOMAIN_MASK"]
