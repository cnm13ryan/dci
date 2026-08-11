"""What Pair 1's `ordering_depth` is, and the generator that makes it mean that.

Section 6.1 names ordering depth among the family-specific parameter quantities and
never defines it. The Stage 2 amendment A4 defines it:

    ordering_depth(R) = the LONGEST-CHAIN CARDINALITY of the required precedence
    relation R - the number of items in the longest chain of R.

WHY A STATISTIC ALONE IS NOT ENOUGH
-----------------------------------
A statistic on a relation does not fix what the parameter manipulates. Two relations
can share a longest-chain cardinality and differ completely in how constrained they
are: a single chain over d items, and that same chain plus every other item wedged
into unrelated precedences, both have depth d while presenting a reader with very
different problems. If the constraint generator were free to produce either, then
"depth" would be confounded with total constrainedness and a dose-response over depth
would not be a dose-response over anything nameable.

So A4 freezes the generator alongside the statistic:

    for N items at depth d, expose exactly ONE chain of d items and leave the
    remaining N - d items explicitly unconstrained.

Under that generator the statistic uniquely determines the manipulation. Edge count is
then d - 1, constrained-item count is d, and free-item count is N - d, all functions
of d; nothing else about the relation varies with it. `assert_canonical_form` is what
holds the generator to it, and `encode_clause` and the focal verifier both accept any
relation, so the canonical form is a property of what the protocol GENERATES rather
than a hidden assumption inside a measurement rule.

COVER RELATIONS, NOT THE CLOSURE
--------------------------------
The chain is exposed as its d - 1 cover edges. Presenting the transitive closure
instead would present d(d-1)/2 precedences for the same partial order, so the number
of stated requirements would grow quadratically in d while the order itself did not -
again confounding depth with prompt length. The verifier still evaluates the closure;
`OrderingRelation.closure` computes it internally, which is where that belongs.

WHAT IS NOT DECIDED HERE
------------------------
Which depths are retained. Section 6.2's ordered grid of at most five admissible
settings is a Stage 5 calibration output (`parameters.p1.admissible_set`, register
item D6), reached by the prescribed boundary procedure over observed pass rates. A4
fixes the construct, its admissible range and the nominal harder direction; it does
not anticipate the grid, and `DECISION` carries no grid for that reason.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import PROTOCOL_VERSION
from dci.v19.parsing import ListPolicy, OrderingRelation, RelationError, require_policy

# The statistic and the generator are separately identified, because a later
# amendment could keep one and replace the other and the artifact trail has to be
# able to say which.
STATISTIC_ID = "v19:ordering-depth.longest-chain-cardinality"
GENERATOR_ID = "v19:ordering-depth.single-chain-v1"

# "require 2 <= d <= N". Depth 1 is the empty relation: every item unconstrained, so
# no arrangement can be wrong and the focal constraint is vacuous. Depth N is the
# total order.
MIN_DEPTH = 2

# Larger d is NOMINALLY harder: it states more required precedences over more items,
# so more arrangements are wrong. Nominal because whether it is empirically harder is
# exactly what Stage 5's calibration measures, and section 6.2 forbids anticipating it.
HARDER_DIRECTION = "increasing"

# How the chain is presented. See the module docstring.
EXPOSES = "cover_relations"


class OrderingDepthError(ValueError):
    """A depth, or a relation, that the frozen definition does not admit."""


def ordering_depth(relation: OrderingRelation) -> int:
    """The number of items in the longest chain of required precedences.

    Counted in ITEMS, not edges: a chain of three items is depth 3. The distinction
    matters because `OrderingRelation.chain_depth` counts edges and predates this
    definition; `depth == chain_depth + 1` whenever there is at least one item, and
    `test_v19_ordering_depth` asserts that rather than leaving it to be assumed.
    """
    if not isinstance(relation, OrderingRelation):
        raise OrderingDepthError(
            f"ordering depth is defined on an OrderingRelation, got "
            f"{type(relation).__name__}")
    longest = {item: 1 for item in relation.items}
    # The relation is acyclic by construction, so |items| relaxation rounds suffice.
    for _ in relation.items:
        for before, after in relation.edges:
            longest[after] = max(longest[after], longest[before] + 1)
    return max(longest.values(), default=0)


def constrained_items(relation: OrderingRelation) -> tuple[str, ...]:
    """The items that appear in at least one precedence, in declaration order."""
    named = {label for edge in relation.edges for label in edge}
    return tuple(item for item in relation.items if item in named)


def free_items(relation: OrderingRelation) -> tuple[str, ...]:
    """The items A4 leaves explicitly unconstrained, in declaration order."""
    named = {label for edge in relation.edges for label in edge}
    return tuple(item for item in relation.items if item not in named)


def chain_of(relation: OrderingRelation) -> tuple[str, ...]:
    """The single chain, in required order, or () if the relation is not one chain.

    Returns the chain rather than a boolean so `assert_canonical_form` can say what
    it found. A relation is a single chain over its constrained items when every
    such item has at most one predecessor and at most one successor and the edges
    connect all of them - which is exactly a simple path, and a simple path's edges
    are exactly its cover relations.
    """
    constrained = constrained_items(relation)
    if len(constrained) < 2 or len(relation.edges) != len(constrained) - 1:
        return ()
    successor: dict[str, str] = {}
    predecessor: dict[str, str] = {}
    for before, after in relation.edges:
        if before in successor or after in predecessor:
            return ()                      # a branch or a merge, so not a chain
        successor[before] = after
        predecessor[after] = before
    heads = [item for item in constrained if item not in predecessor]
    if len(heads) != 1:
        return ()
    walk = [heads[0]]
    while walk[-1] in successor:
        walk.append(successor[walk[-1]])
    if len(walk) != len(constrained):
        return ()                          # disconnected, so more than one chain
    return tuple(walk)


def assert_canonical_form(relation: OrderingRelation) -> tuple[str, ...]:
    """Hold a relation to A4's generator form, and return its chain.

    Not applied by the verifier or the encoder: both accept any partial order, and
    they must, because a relation the protocol did not generate is a failing input
    rather than an impossible one. This is applied where relations are CONSTRUCTED,
    so the canonical form is a checked property of the construction path.
    """
    chain = chain_of(relation)
    if not chain:
        raise OrderingDepthError(
            f"the relation over {list(relation.items)} with edges "
            f"{[list(e) for e in relation.edges]} is not one chain plus free items. "
            "A4 exposes exactly one chain of d items and leaves the remaining N - d "
            "explicitly unconstrained, so that ordering depth is not confounded with "
            "how constrained the rest of the relation is")
    depth = ordering_depth(relation)
    if depth != len(chain):
        raise OrderingDepthError(                      # pragma: no cover - guarded
            f"the chain has {len(chain)} items but the longest chain has {depth}")
    return chain


# ------------------------------------------------------------------ the generator

def _shuffled(values: Sequence[str], stream: str, seed: int) -> tuple[str, ...]:
    """A Fisher-Yates shuffle driven by a domain-separated digest.

    Hash-derived rather than `random.Random`, for the reason `dci.v19.identity`
    gives: a counter-based derivation is reproducible from the recorded seed alone,
    independent of any library's generator state or version.
    """
    out = list(values)
    for index in range(len(out) - 1, 0, -1):
        digest = sha(["v19/ordering-depth/shuffle",
                      [PROTOCOL_VERSION, stream, seed, index]])
        swap = int(digest[:16], 16) % (index + 1)
        out[index], out[swap] = out[swap], out[index]
    return tuple(out)


def generate(labels: Sequence[str], depth: int, policy: ListPolicy, *,
             seed: int = 0) -> OrderingRelation:
    """The A4 relation over `labels` at `depth`, deterministic in (labels, depth, seed).

    Randomises which items form the chain, the chain's internal order, and the
    presentation order of all N items, each from its own domain-separated stream, so
    that depth is not delivered together with a positional cue: if the chain were
    always the first d labels in their declared order, an answer could satisfy the
    relation by copying the prompt's order without representing the order at all.
    """
    policy = require_policy(policy)
    items = tuple(labels)
    if len(set(items)) != len(items):
        raise OrderingDepthError(f"duplicate item labels in {list(items)}")
    n_items = len(items)
    if isinstance(depth, bool) or not isinstance(depth, int):
        raise OrderingDepthError(f"depth {depth!r} is not an integer")
    if not MIN_DEPTH <= depth <= n_items:
        raise OrderingDepthError(
            f"ordering depth {depth} is outside {MIN_DEPTH}..{n_items} for "
            f"{n_items} item(s). Depth {MIN_DEPTH - 1} would state no precedence at "
            "all, so no arrangement could be wrong and the focal constraint would be "
            "vacuous; depth above N would need items that do not exist")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise OrderingDepthError(f"seed {seed!r} is not a non-negative integer")

    chosen = _shuffled(items, "membership", seed)[:depth]
    chain = _shuffled(chosen, "chain-order", seed)
    presentation = _shuffled(items, "presentation", seed)
    edges = tuple((chain[i], chain[i + 1]) for i in range(depth - 1))
    try:
        relation = OrderingRelation(items=presentation, edges=edges)
    except RelationError as error:                     # pragma: no cover - guarded
        raise OrderingDepthError(f"the generated relation is invalid: {error}") from error
    relation.assert_labels_are_tokens(policy)
    assert_canonical_form(relation)
    return relation


def realisation(labels: Sequence[str], depth: int, policy: ListPolicy, *,
                seed: int = 0) -> dict[str, Any]:
    """The generated relation with the record that makes it auditable."""
    relation = generate(labels, depth, policy, seed=seed)
    chain = chain_of(relation)
    return {"relation": relation, "ordering_depth": depth,
            "statistic": STATISTIC_ID, "generator": GENERATOR_ID,
            "seed": seed, "n_items": len(relation.items),
            "chain": list(chain), "free_items": list(free_items(relation)),
            "n_cover_edges": len(relation.edges),
            "relation_hash": relation.relation_hash}


# ---------------------------------------------------------------- the decision value

DEFINITION = ("ordering_depth(R) is the longest-chain cardinality of the required "
              "precedence relation R: the number of items in the longest chain of R, "
              "counted in items rather than edges")

DECISION: dict[str, Any] = {
    "definition": DEFINITION,
    "statistic": STATISTIC_ID,
    "generator": GENERATOR_ID,
    "min_depth": MIN_DEPTH,
    "max_depth_rule": "n_items",
    "harder_direction": HARDER_DIRECTION,
    "exposes": EXPOSES,
    "generator_form": (
        "for N items at depth d, expose exactly one chain containing d items as its "
        "d - 1 cover relations, and leave the remaining N - d items explicitly "
        "unconstrained; randomise chain membership, chain order and presentation "
        "order from separate domain-separated streams of the recorded seed"),
    "grid": None,
    "grid_rule": (
        "not decided at Stage 2. Section 6.2's ordered grid of at most five "
        "admissible settings is the Stage 5 boundary-calibration output recorded in "
        "parameters.p1.admissible_set (register item D6); anticipating it here would "
        "pre-empt the calibration that selects it"),
    "rejected_alternatives": {
        "n_items": ("item count is not a property of the ordering relation at all, "
                    "so it would make the focal parameter a second copy of the "
                    "target parameter n_items and confound the two constraints the "
                    "pair is designed to separate"),
        "edge_count": ("counts stated requirements rather than the depth of the "
                       "order; under the canonical generator it is d - 1 and so "
                       "carries the same information, but off it a wide shallow "
                       "relation and a deep narrow one can share an edge count"),
        "linear_extension_count": ("measures constrainedness, which is a defensible "
                                   "different construct; it is not a depth, is "
                                   "#P-hard in general, and is not monotone in any "
                                   "quantity the prompt states"),
    },
    "citation": "sections 4.1, 6.1, 6.2, 14.5 + Stage 2 amendment A4",
}
