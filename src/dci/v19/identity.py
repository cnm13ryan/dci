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


# ------------------------------------------------- the completeness ledger
#
# Appendix I: "one terminal state per planned generation ID". The planned set is
# the authority, not the ledger's own keys. Iterating the ledger cannot detect a
# generation that was deleted outright, and deletion is exactly the shortcut
# section 12.10 forbids: a permanently missing generation stays in the scientific
# population as a terminal missing state feeding interval completion.

TERMINAL_OBSERVED = "OBSERVED"
TERMINAL_MISSING = "PERMANENTLY_MISSING"
TERMINAL_STATES = (TERMINAL_OBSERVED, TERMINAL_MISSING)


class LedgerViolation(ValueError):
    """A completeness or lineage invariant failed. Fail closed, never repair."""


@dataclass(frozen=True)
class LedgerReport:
    """What the completeness gate established, for the run's provenance record."""
    n_planned: int
    n_observed: int
    n_permanently_missing: int
    n_attempts: int

    @property
    def missingness_rate(self) -> float:
        return self.n_permanently_missing / self.n_planned if self.n_planned else 0.0


def _assert_lineage(gen: str, attempts: Sequence[Mapping[str, Any]]) -> str:
    """Validate one generation's attempt lineage; return its terminal state."""
    if not attempts:
        raise LedgerViolation(f"generation {gen} has no attempt lineage")
    try:
        indices = [int(a["attempt"]) for a in attempts]
    except (KeyError, TypeError, ValueError) as exc:
        raise LedgerViolation(
            f"generation {gen} has an attempt record without a usable attempt "
            f"index: {exc}") from exc
    if indices != list(range(1, len(indices) + 1)):
        raise LedgerViolation(
            f"generation {gen} has non-monotonic attempt indices {indices}; "
            "attempts are lineage and must be densely ordered from 1")

    terminal = [(i, a) for i, a in zip(indices, attempts) if a.get("terminal")]
    if len(terminal) != 1:
        raise LedgerViolation(
            f"generation {gen} has {len(terminal)} terminal states; exactly one "
            "is required, because a second one is a second observation")
    position, record = terminal[0]
    if position != indices[-1]:
        raise LedgerViolation(
            f"generation {gen} records a terminal state at attempt {position} "
            f"but continues to attempt {indices[-1]}; work after a terminal "
            "state means the observation was reopened")

    state = record.get("state")
    if state not in TERMINAL_STATES:
        raise LedgerViolation(
            f"generation {gen} terminal attempt {position} carries state "
            f"{state!r}, which is not a terminal scientific state; one of "
            f"{TERMINAL_STATES} is required, and an absent state is missing "
            "evidence rather than a default success")

    if state == TERMINAL_OBSERVED:
        # Appendix I: every successful generation is linked to durably stored
        # output bytes. A success with no linkage cannot be verified or replayed.
        if not (record.get("output_hash") and record.get("output_path")):
            raise LedgerViolation(
                f"generation {gen} is terminal {TERMINAL_OBSERVED} but has no "
                "durable output linkage; both output_hash and output_path are "
                "required, since a success that cannot be located is not one")
    else:
        if not record.get("retries_exhausted"):
            raise LedgerViolation(
                f"generation {gen} is terminal {TERMINAL_MISSING} without an "
                "exhausted retry lineage; permanent technical missingness is "
                "assigned only after the frozen retry policy is spent")
        if record.get("output_hash") or record.get("output_path"):
            raise LedgerViolation(
                f"generation {gen} is terminal {TERMINAL_MISSING} yet claims a "
                "durable output; if bytes were persisted the generation is "
                "behaviourally observed, however malformed the answer")
    return state


def assert_one_terminal_state(
        ledger: Mapping[str, Sequence[Mapping[str, Any]]],
        planned_generation_ids: Sequence[str]) -> LedgerReport:
    """Appendix I invariants, checked against the PLANNED generation manifest.

    `planned_generation_ids` is the frozen expected scientific population, so a
    generation missing from the ledger is a failure rather than a silence. Each
    record carries `attempt`, `terminal`, `state`, and either durable-output
    linkage or an exhausted-retry marker.
    """
    planned = list(planned_generation_ids)
    if not planned:
        raise LedgerViolation(
            "the planned manifest is empty; completeness cannot be established "
            "against an unknown expected population")
    unique = set(planned)
    if len(unique) != len(planned):
        duplicated = sorted({g for g in planned if planned.count(g) > 1})
        raise LedgerViolation(
            f"the planned manifest contains duplicate generation ids "
            f"{duplicated[:5]}; scientific identities are unique by construction")

    absent = [g for g in planned if g not in ledger]
    if absent:
        raise LedgerViolation(
            f"{len(absent)} planned generations are absent from the ledger, "
            f"beginning with {absent[:5]}; a permanently missing generation is "
            "represented by a terminal missing state and interval completion, "
            "never by deletion")
    unexpected = sorted(set(ledger) - unique)
    if unexpected:
        raise LedgerViolation(
            f"{len(unexpected)} ledger entries are not in the planned manifest, "
            f"beginning with {unexpected[:5]}; an unplanned generation cannot "
            "enter confirmatory analysis")

    observed = missing = attempts = 0
    for gen in planned:
        records = ledger[gen]
        attempts += len(records)
        if _assert_lineage(gen, records) == TERMINAL_OBSERVED:
            observed += 1
        else:
            missing += 1
    return LedgerReport(n_planned=len(planned), n_observed=observed,
                        n_permanently_missing=missing, n_attempts=attempts)


@dataclass(frozen=True)
class GenerationManifest:
    """The frozen scientific-draw manifest and its root hash (Stage 12, D42).

    Holds the planned rows in frozen order, exposes the expected generation-ID
    population the completeness gate needs, and computes the root manifest hash
    over the immutable identity fields only - so a change to any planned identity
    or seed changes the root hash, while incidental reordering cannot.
    """
    rows: tuple[PlannedGeneration, ...]
    protocol: str = PROTOCOL_VERSION

    @classmethod
    def from_planned(cls, rows: Sequence[PlannedGeneration],
                     protocol: str = PROTOCOL_VERSION) -> "GenerationManifest":
        return cls(rows=tuple(rows), protocol=protocol)

    @property
    def generation_ids(self) -> tuple[str, ...]:
        return tuple(row.generation for row in self.rows)

    @property
    def root_hash(self) -> str:
        """SHA-256 over the sorted immutable identity of every planned row."""
        material = sorted(
            [row.pair, row.draw_index, row.superblock, row.cell, row.generation,
             row.budget, row.load, row.order, row.arm, row.replicate, row.seed]
            for row in self.rows)
        return _digest("v19/manifest", [self.protocol, material])

    def assert_complete(self, ledger: Mapping[str, Sequence[Mapping[str, Any]]]
                        ) -> LedgerReport:
        return assert_one_terminal_state(ledger, self.generation_ids)
