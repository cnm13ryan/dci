"""Frozen seed derivations (§4, item 39/40/42).

Three separated randomness levels: generation seeds, pseudo-run selection,
and bootstrap resampling each use a distinct domain and a distinct registered
root seed, so no seed can be reused across levels. Every derivation fails on
a missing input; there are no hidden seed defaults.
"""
from __future__ import annotations

from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import domain_digest, domain_int


def _require(**inputs) -> None:
    for name, value in inputs.items():
        if value is None or value == "":
            raise ProtocolError(f"seed derivation missing input {name!r}; "
                                f"hidden seed defaults are prohibited")


def generation_seed(root: int, stage: str, model_id: str, prompt_hash: str,
                    draw_index: int) -> int:
    """Item 39: fixed root seed, model identifier, exact prompt hash, and
    cached-draw index. ``stage`` separates streams (pilot, prescreen, solo,
    composed, confirmatory, greedy, validation)."""
    _require(root=root, stage=stage, model_id=model_id,
             prompt_hash=prompt_hash, draw_index=draw_index)
    return domain_int(C.DOMAIN_GENERATION, root, stage, model_id,
                      prompt_hash, draw_index)


def primary_draw_index(model_id: str, prompt_hash: str) -> int:
    """Item 40, verbatim: j_c = H("primary-root", model-id, prompt-hash) mod 16.

    H is SHA-256 over the 0x1f-joined inputs. Response content and verifier
    outcomes are not inputs and cannot affect the choice.
    """
    _require(model_id=model_id, prompt_hash=prompt_hash)
    digest = domain_digest(C.PRIMARY_SELECTION_DOMAIN, model_id, prompt_hash)
    return int.from_bytes(digest, "big") % C.M_DRAWS


def pseudo_run_index(root: int, run_index: int, model_id: str,
                     prompt_hash: str) -> int:
    """Item 42: frozen pseudo-run seed scheme, separate from generation and
    bootstrap domains. Selects one cached draw per prompt cell."""
    _require(root=root, run_index=run_index, model_id=model_id,
             prompt_hash=prompt_hash)
    digest = domain_digest(C.DOMAIN_PSEUDO, root, run_index, model_id,
                           prompt_hash)
    return int.from_bytes(digest, "big") % C.M_DRAWS


def bootstrap_seed(root: int, model_id: str, family: str) -> int:
    """One bootstrap stream per (model, multiplicity family)."""
    _require(root=root, model_id=model_id, family=family)
    return domain_int(C.DOMAIN_BOOTSTRAP, root, model_id, family)


def area_split_seed(root: int, area: str) -> int:
    """Per-stratum shuffle seed for the topic split (§6)."""
    _require(root=root, area=area)
    return domain_int(C.DOMAIN_TOPIC_SPLIT, root, area)


def gate1_sample_seed(root: int, model_id: str, verifier_class: str) -> int:
    """Fixed seeded sample of min(150, N_c) per verifier class (§10)."""
    _require(root=root, model_id=model_id, verifier_class=verifier_class)
    return domain_int(C.DOMAIN_GATE1_SAMPLE, root, model_id, verifier_class)
