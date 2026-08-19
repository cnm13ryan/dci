"""Frozen v4 seed derivations (§14.2, §17.1, T-14).

Fresh v4 root seeds and fresh domain-separation strings. No ``dci1v3:``
domain and no v3 root is reachable from this module, so no v4 draw can
coincide with a v3 draw. Model generation and the statistical bootstrap use
separate roots and separate domains (§11 of the implementation brief).

Every derivation names its inputs and fails on a missing one; there are no
hidden seed defaults. The generation seed derives from experimental identity
— root, stage label, model identity, prompt hash and draw index — which is
what check C14 measures the realised duplicate rate of.

**There is no primary-draw selector.** v3 derived one draw of sixteen from a
hash; v4 averages all M draws into the cell mean (§8.2), so the construct has
no referent here and no function implements it.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int

# --------------------------------------------------------------- root seeds
#: Drawn fresh for v4 on 19 August 2026. Distinct from every v3 root
#: (202608170-202608175) by construction, and separated further by domain.
GENERATION_ROOT_SEED = 202608190
BOOTSTRAP_ROOT_SEED = 202608191
TOPIC_SPLIT_SEED = 202608192
GATE1_SAMPLE_SEED = 202608193
AUTORATER_SPLIT_SEED = 202608194
ADVERSARIAL_SEED = 202608195

# ----------------------------------------------------- domain separation (v4)
DOMAIN_GENERATION = "dci1v4:gen:v1"
DOMAIN_BOOTSTRAP = "dci1v4:boot:v1"
DOMAIN_TOPIC_SPLIT = "dci1v4:topics:v1"
DOMAIN_GATE1_SAMPLE = "dci1v4:gate1:v1"
DOMAIN_AUTORATER_SPLIT = "dci1v4:autorater-split:v1"
DOMAIN_ANNOTATION_ORDER = "dci1v4:annotation-order:v1"
DOMAIN_ADVERSARIAL = "dci1v4:adversarial:v1"

V4_DOMAINS = (DOMAIN_GENERATION, DOMAIN_BOOTSTRAP, DOMAIN_TOPIC_SPLIT,
              DOMAIN_GATE1_SAMPLE, DOMAIN_AUTORATER_SPLIT,
              DOMAIN_ANNOTATION_ORDER, DOMAIN_ADVERSARIAL)


def _require(**inputs) -> None:
    for name, value in inputs.items():
        if value is None or value == "":
            raise ProtocolError(f"seed derivation missing input {name!r}; "
                                f"hidden seed defaults are prohibited")


def generation_seed(root: int, stage: str, model_id: str, prompt_hash: str,
                    draw_index: int) -> int:
    """§14.2: root seed, stage label, model identity, prompt hash, draw index.

    ``stage`` separates the streams (pilot, ladder screen, solo calibration,
    composed validation, confirmatory, greedy), so the same prompt drawn in
    two stages never reuses a seed.
    """
    _require(root=root, stage=stage, model_id=model_id,
             prompt_hash=prompt_hash, draw_index=draw_index)
    return domain_int(DOMAIN_GENERATION, root, stage, model_id, prompt_hash,
                      draw_index)


def bootstrap_seed(root: int, model_id: str, order: str, family: str) -> int:
    """One bootstrap stream per (model, configuration, multiplicity family).

    Separate root and separate domain from generation: a resample can never
    consume a generation seed (§11 of the brief).
    """
    _require(root=root, model_id=model_id, order=order, family=family)
    return domain_int(DOMAIN_BOOTSTRAP, root, model_id, order, family)


def area_split_seed(root: int, area: str) -> int:
    """Per-stratum shuffle seed for the seeded five-way topic split (§6.2)."""
    _require(root=root, area=area)
    return domain_int(DOMAIN_TOPIC_SPLIT, root, area)


def gate1_sample_seed(root: int, model_id: str, instrument: str,
                      verifier_class: str) -> int:
    """min(150, N_c) per verifier class, per instrument (§10.3)."""
    _require(root=root, model_id=model_id, instrument=instrument,
             verifier_class=verifier_class)
    return domain_int(DOMAIN_GATE1_SAMPLE, root, model_id, instrument,
                      verifier_class)


def autorater_split_seed(root: int, model_id: str, verifier_class: str) -> int:
    """The deterministic class-stratified development/calibration split
    (§10.4)."""
    _require(root=root, model_id=model_id, verifier_class=verifier_class)
    return domain_int(DOMAIN_AUTORATER_SPLIT, root, model_id, verifier_class)


def annotation_order_seed(root: int, annotator_id: str, packet_id: str) -> int:
    """Per-annotator seeded display order, so a class-ordered packet cannot
    leak its own stratification (§10.3)."""
    _require(root=root, annotator_id=annotator_id, packet_id=packet_id)
    return domain_int(DOMAIN_ANNOTATION_ORDER, root, annotator_id, packet_id)
