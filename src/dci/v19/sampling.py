"""The confirmatory superblock proposal law: independent, with replacement.

Preregistration section 8.3 and Appendix C. v19 replaces v15's deterministic
without-replacement background cycles because both claim-bearing candidates need
an explicitly stated probability model, and a round-robin cycle is not one.

For each pair and each intended index i, a fresh proposal is drawn independently:
a task with replacement from the frozen task population; exactly one background
identity with replacement from each of the three frozen strata; every active
constraint's parameter from its own frozen distribution; and the position
permutation. The COMPLETE proposal is then evaluated in the focal arm and all
four reference arms, and if any required composition fails the acceptance
conjunction the ENTIRE proposal is rejected and a fresh one drawn. No individual
background identity is ever swapped in isolation - that would be a different,
unstated law, and the accepted draws would no longer be identically distributed.

Because this is ordinary rejection sampling from a fixed proposal law, accepted
superblocks are i.i.d. draws from the proposal distribution conditioned on the
frozen acceptance event. Two properties are load-bearing and enforced here:

  * per-index proposal streams are independent, derived by domain-separated
    counter-based hashing of (pair, index, attempt, field). Rejecting a proposal
    or building two indices in parallel therefore cannot consume randomness
    assigned to another index.
  * reproducibility of the realised stream is an implementation property, NOT
    the argument for independence. The argument is the stated design law; the
    seed just lets someone re-derive the same realisation.

Every proposal, accepted or rejected, is archived with its rejection reason.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

from dci.v19.identity import context_fingerprint, proposal_seed, superblock_id

STRATA = ("lexical_content", "structural_format", "relational_order")
BACKGROUNDS_AT_MAX_LOAD = 3          # one per stratum, k = 5


@dataclass(frozen=True)
class Proposal:
    pair: str
    draw_index: int
    attempt: int
    task: str
    backgrounds: tuple[str, ...]
    parameters: Mapping[str, Any]
    permutation: tuple[int, ...]

    @property
    def context(self) -> dict[str, Any]:
        """The pretreatment content, which is what the fingerprint hashes."""
        return {"pair": self.pair, "task": self.task,
                "backgrounds": list(self.backgrounds),
                "parameters": dict(self.parameters),
                "permutation": list(self.permutation)}

    @property
    def fingerprint(self) -> str:
        return context_fingerprint(self.context)


@dataclass(frozen=True)
class Accepted:
    proposal: Proposal
    superblock: str
    attempts: int                    # proposals drawn, including the accepted one


@dataclass
class ProposalLedger:
    """Every proposal and why it was rejected (section 8.3)."""
    accepted: list[Accepted] = field(default_factory=list)
    rejected: list[tuple[Proposal, str]] = field(default_factory=list)

    def rejection_reasons(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for _, reason in self.rejected:
            out[reason] = out.get(reason, 0) + 1
        return out

    def acceptance_rate(self) -> float:
        total = len(self.accepted) + len(self.rejected)
        return len(self.accepted) / total if total else 0.0

    def duplicate_context_rate(self) -> float:
        """Legal under with-replacement sampling; reported, never deduplicated."""
        if not self.accepted:
            return 0.0
        prints = [a.proposal.fingerprint for a in self.accepted]
        return 1.0 - len(set(prints)) / len(prints)


def _index(seed: int, size: int) -> int:
    if size < 1:
        raise ValueError("cannot draw from an empty population")
    return seed % size


def draw_proposal(pair: str, draw_index: int, attempt: int, root_seed: int,
                  tasks: Sequence[str],
                  strata: Mapping[str, Sequence[str]],
                  parameter_supports: Mapping[str, Sequence[Any]],
                  ) -> Proposal:
    """One independent proposal. With replacement, from a frozen law.

    Each field gets its own domain-separated seed, so adding a field later
    cannot shift the draws of the existing ones.
    """
    missing = [s for s in STRATA if s not in strata]
    if missing:
        raise ValueError(f"the background pool must be partitioned into exactly "
                         f"{STRATA}; missing {missing}")

    def seed_for(name: str) -> int:
        return proposal_seed(pair, draw_index, attempt, name, root_seed)

    task = tasks[_index(seed_for("task"), len(tasks))]
    backgrounds = tuple(
        strata[stratum][_index(seed_for(f"background/{stratum}"),
                               len(strata[stratum]))]
        for stratum in STRATA)
    parameters = {
        name: support[_index(seed_for(f"parameter/{name}"), len(support))]
        for name, support in sorted(parameter_supports.items())}
    # A permutation of the three background positions, drawn from its own stream.
    order_seed = seed_for("permutation")
    positions = list(range(BACKGROUNDS_AT_MAX_LOAD))
    permutation: list[int] = []
    for step in range(BACKGROUNDS_AT_MAX_LOAD):
        pick = (order_seed >> (8 * step)) % len(positions)
        permutation.append(positions.pop(pick))
    return Proposal(pair=pair, draw_index=draw_index, attempt=attempt, task=task,
                    backgrounds=backgrounds, parameters=parameters,
                    permutation=tuple(permutation))


def accept_superblock(pair: str, draw_index: int, root_seed: int,
                      tasks: Sequence[str],
                      strata: Mapping[str, Sequence[str]],
                      parameter_supports: Mapping[str, Sequence[Any]],
                      acceptable: Callable[[Proposal], Optional[str]],
                      ledger: ProposalLedger,
                      max_attempts: int = 10_000) -> Optional[Accepted]:
    """Draw until a WHOLE proposal passes, archiving every rejection.

    `acceptable` returns None to accept, or a rejection reason. It is handed the
    complete proposal because acceptance is a property of the complete
    composition in the focal arm and all four reference arms - pairwise
    compatibility is not sufficient (section 8.7).
    """
    for attempt in range(1, max_attempts + 1):
        proposal = draw_proposal(pair, draw_index, attempt, root_seed, tasks,
                                 strata, parameter_supports)
        reason = acceptable(proposal)
        if reason is None:
            got = Accepted(proposal=proposal,
                           superblock=superblock_id(pair, draw_index,
                                                    proposal.fingerprint),
                           attempts=attempt)
            ledger.accepted.append(got)
            return got
        ledger.rejected.append((proposal, reason))
    return None                     # construction fails before confirmation


def build_bank(pair: str, target: int, root_seed: int,
               tasks: Sequence[str],
               strata: Mapping[str, Sequence[str]],
               parameter_supports: Mapping[str, Sequence[Any]],
               acceptable: Callable[[Proposal], Optional[str]],
               ledger: Optional[ProposalLedger] = None
               ) -> tuple[list[Accepted], ProposalLedger]:
    """Accepted superblocks 1..target for one pair, in frozen bank order."""
    ledger = ledger or ProposalLedger()
    bank: list[Accepted] = []
    for draw_index in range(1, target + 1):
        got = accept_superblock(pair, draw_index, root_seed, tasks, strata,
                                parameter_supports, acceptable, ledger)
        if got is None:
            break               # attainable count is what it is; never relaxed
        bank.append(got)
    return bank, ledger
