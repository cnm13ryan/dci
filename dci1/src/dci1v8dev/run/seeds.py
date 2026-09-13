"""v8 seed derivations: v7's root seeds under ``dci1v8:*`` domain strings.

The root seeds are the ones drawn fresh for v4r3 on 21 August 2026 and
carried by every revision since; what separates one revision's draws from
another's is the domain string, and every v8 domain names ``dci1v8``. No
``dci1v7:`` domain is reachable from here, so a v8 draw cannot coincide with
a v7 draw even where the prompt text is identical --- which for every
non-marker family at every severity but 1 it is.

Every derivation names its inputs and fails on a missing one; there are no
hidden seed defaults and no primary-draw selector.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int
from dci1v7.protocol import seeds as _v7

GENERATION_ROOT_SEED = _v7.GENERATION_ROOT_SEED
BOOTSTRAP_ROOT_SEED = _v7.BOOTSTRAP_ROOT_SEED
CARRIED_TOPIC_SPLIT_SEED = _v7.CARRIED_TOPIC_SPLIT_SEED

DOMAIN_GENERATION = "dci1v8:gen:v1"
DOMAIN_BOOTSTRAP = "dci1v8:boot:v1"
DOMAIN_SCREEN = "dci1v8:screen:v1"
V8_DOMAINS = (DOMAIN_GENERATION, DOMAIN_BOOTSTRAP, DOMAIN_SCREEN)
assert not set(V8_DOMAINS) & set(_v7.V4R3_DOMAINS)
assert all(d.startswith("dci1v8:") for d in V8_DOMAINS)


def _require(**inputs) -> None:
    for name, value in inputs.items():
        if value is None or value == "":
            raise ProtocolError(f"seed derivation missing input {name!r}; "
                                "hidden seed defaults are prohibited")


def generation_seed(stage: str, model_id: str, prompt_hash: str,
                    draw_index: int) -> int:
    """§14.2's shape: root, stage, model identity, prompt hash, draw."""
    _require(stage=stage, model_id=model_id, prompt_hash=prompt_hash)
    if draw_index is None or draw_index < 0:
        raise ProtocolError("draw index must be a non-negative integer")
    return domain_int(DOMAIN_GENERATION, GENERATION_ROOT_SEED, stage,
                      model_id, prompt_hash, draw_index)


def bootstrap_seed(estimand: str, model_id: str) -> int:
    _require(estimand=estimand, model_id=model_id)
    return domain_int(DOMAIN_BOOTSTRAP, BOOTSTRAP_ROOT_SEED, estimand,
                      model_id)


def screen_seed(model_id: str, stage: str) -> int:
    """The Monte Carlo seed of the uncertainty-aware screen, per model and
    stage, so a replication's posterior draws are its own and reproducible."""
    _require(model_id=model_id, stage=stage)
    return domain_int(DOMAIN_SCREEN, BOOTSTRAP_ROOT_SEED, model_id, stage,
                      bits=31)


__all__ = ["GENERATION_ROOT_SEED", "BOOTSTRAP_ROOT_SEED",
           "CARRIED_TOPIC_SPLIT_SEED", "DOMAIN_GENERATION",
           "DOMAIN_BOOTSTRAP", "DOMAIN_SCREEN", "V8_DOMAINS",
           "generation_seed", "bootstrap_seed", "screen_seed"]
