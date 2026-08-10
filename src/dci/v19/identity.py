"""Scientific identity and domain-separated seed derivation.

Preregistration sections 8.7, 11.3 and 11.7. The identity hierarchy exists to
keep three different things apart that a single "row id" would conflate:

    context_fingerprint   the pretreatment CONTENT of a draw
    superblock_id         the statistical UNIT: hash(protocol, pair, i, context)
    cell_id               hash(superblock_id, budget, load, order, arm)
    generation_id         hash(cell_id, replicate)
    attempt_id            hash(generation_id, retry index)

Including the accepted draw index `i` in superblock_id is mandatory, not
cosmetic. Sampling is WITH REPLACEMENT, so two accepted indices may legitimately
draw identical task, background and parameter content; keying the unit on content
alone would silently merge two independent draws into one, understating H and
overstating precision. Conversely, attempts never create observations: a retry
reuses the identical generation_id and the identical seed, so a failure cannot
become a fresh draw.

Seeds are derived by domain-separated counter-based SHA-256 over the canonical
serialisation of (protocol, model, pair, superblock, cell condition, budget,
load, order, arm, replicate), reduced modulo 2^63 - 1. Domain separation is what
makes retrying or parallelising one superblock unable to consume draws assigned
to another: there is no shared stream to advance.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from dci.provenance.hashes import canonicalize
from dci.v19 import PROTOCOL_VERSION

# 2^63 - 1, per section 11.6: interpret the first 64 bits as unsigned, reduce.
SEED_MODULUS = (1 << 63) - 1

ARMS = ("B", "R1", "R2", "R3", "R4")      # focal plus exactly four references
LOADS = (2, 5)
ORDERS = ("o_A", "o_Q")


def _digest(domain: str, payload: Any) -> str:
    """SHA-256 over a domain tag and the canonical serialisation of `payload`.

    The domain tag is inside the hashed bytes, so two different kinds of object
    can never collide even when their payloads coincide. canonicalize() is reused
    from the provenance layer because it refuses values with no reproducible
    form - a seed that depends on a memory address is not a seed.
    """
    import json
    material = json.dumps({"domain": domain, "payload": canonicalize(payload)},
                          sort_keys=True).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def context_fingerprint(context: Mapping[str, Any]) -> str:
    """Hash of the pretreatment CONTENT of a proposal.

    Deliberately excludes the draw index: two draws with the same content have
    the same fingerprint, and that is the fact the diagnostics report.
    """
    return _digest("v19/context", dict(context))


def superblock_id(pair: str, draw_index: int, fingerprint: str,
                  protocol: str = PROTOCOL_VERSION) -> str:
    """hash(protocol, pair, i, context_fingerprint) - the statistical unit."""
    if draw_index < 1:
        raise ValueError("accepted draw indices start at 1 and are never reused")
    return _digest("v19/superblock", [protocol, pair, draw_index, fingerprint])


def cell_id(superblock: str, budget: str, load: int, order: str,
            arm: str) -> str:
    """hash(superblock_id, b, k, o, q) - one causal condition."""
    if load not in LOADS:
        raise ValueError(f"load {load} is not one of the paired loads {LOADS}")
    if order not in ORDERS:
        raise ValueError(f"order {order!r} is not one of {ORDERS}")
    if arm not in ARMS:
        raise ValueError(f"arm {arm!r} is not one of {ARMS}")
    return _digest("v19/cell", [superblock, budget, load, order, arm])


def generation_id(cell: str, replicate: int) -> str:
    """hash(cell_id, g) - one planned stochastic replicate."""
    if replicate < 1:
        raise ValueError("replicate indices start at 1")
    return _digest("v19/generation", [cell, replicate])


def attempt_id(generation: str, attempt: int) -> str:
    """hash(generation_id, a) - one execution attempt, never an observation."""
    if attempt < 1:
        raise ValueError("attempt indices start at 1")
    return _digest("v19/attempt", [generation, attempt])


def scientific_seed(generation: str, model_hash: str,
                    protocol: str = PROTOCOL_VERSION) -> int:
    """The frozen seed for one logical generation (section 11.6).

    A function of the PLANNED identity only. It does not take an attempt index:
    a retry is the same scientific observation and must reuse the same seed, and
    passing the attempt in here is exactly how a replacement draw gets created
    by accident.
    """
    digest = _digest("v19/seed", [protocol, model_hash, generation])
    return int(digest[:16], 16) % SEED_MODULUS


def proposal_seed(pair: str, draw_index: int, attempt: int, field: str,
                  root_seed: int, protocol: str = PROTOCOL_VERSION) -> int:
    """A construction-time seed for one (pair, index, proposal attempt, field).

    Counter-based and domain separated, so rejecting a proposal or building two
    superblocks in parallel cannot consume randomness assigned to another index.
    Proposal attempts DO index here: a rejected proposal must be followed by a
    fresh independent draw, which is the opposite requirement from a retry.
    """
    if draw_index < 1 or attempt < 1:
        raise ValueError("proposal indices and attempts start at 1")
    digest = _digest("v19/proposal",
                     [protocol, root_seed, pair, draw_index, attempt, field])
    return int(digest[:16], 16) % SEED_MODULUS


@dataclass(frozen=True)
class PlannedGeneration:
    """One immutable row of the scientific-draw manifest."""
    pair: str
    draw_index: int
    superblock: str
    cell: str
    generation: str
    budget: str
    load: int
    order: str
    arm: str
    replicate: int
    seed: int


def expand_superblock(pair: str, draw_index: int, fingerprint: str,
                      budgets: Sequence[str], replicates: int,
                      model_hash: str,
                      protocol: str = PROTOCOL_VERSION
                      ) -> list[PlannedGeneration]:
    """Every planned generation for one accepted superblock.

    Crossed over both loads, every retained budget, both presentation orders,
    the focal arm and all four references, and G replicates: the 20|B_ret|G
    logical generations per superblock of Appendix F.
    """
    if replicates < 1:
        raise ValueError("G is a positive integer")
    unit = superblock_id(pair, draw_index, fingerprint, protocol)
    out: list[PlannedGeneration] = []
    for budget in budgets:
        for load in LOADS:
            for order in ORDERS:
                for arm in ARMS:
                    cell = cell_id(unit, budget, load, order, arm)
                    for replicate in range(1, replicates + 1):
                        gen = generation_id(cell, replicate)
                        out.append(PlannedGeneration(
                            pair=pair, draw_index=draw_index, superblock=unit,
                            cell=cell, generation=gen, budget=budget, load=load,
                            order=order, arm=arm, replicate=replicate,
                            seed=scientific_seed(gen, model_hash, protocol)))
    return out


def generations_per_superblock(n_budgets: int, replicates: int) -> int:
    """20 |B_ret| G (Appendix F): 2 loads x 2 orders x 5 arms."""
    return len(LOADS) * len(ORDERS) * len(ARMS) * n_budgets * replicates


def assert_one_terminal_state(ledger: Mapping[str, Sequence[Mapping[str, Any]]]
                              ) -> None:
    """Appendix I: one terminal state per planned generation, attempts indexed.

    `ledger` maps generation_id to its attempt records, each carrying `attempt`
    and `terminal` keys. The invariants are mechanical, so they are checked
    mechanically rather than trusted.
    """
    for gen, attempts in ledger.items():
        if not attempts:
            raise ValueError(f"generation {gen} has no attempt lineage")
        indices = [int(a["attempt"]) for a in attempts]
        if indices != list(range(1, len(indices) + 1)):
            raise ValueError(
                f"generation {gen} has non-monotonic attempt indices {indices}; "
                "attempts are lineage and must be densely ordered")
        terminal = [a for a in attempts if a.get("terminal")]
        if len(terminal) != 1:
            raise ValueError(
                f"generation {gen} has {len(terminal)} terminal states; exactly "
                "one is required, because a second one is a second observation")
