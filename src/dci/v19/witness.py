"""Deterministic construction of a concrete witness for a whole composition.

Section 8.6 puts the witness above the solver in the evidential hierarchy:

    "The stronger operational evidence is a concrete complete witness x* for the
    actual natural-language composition. Witnesses may be generated automatically.
    The permitted pipeline is: (1) generate a candidate witness by a deterministic
    constructor or a separately seeded pre-confirmatory generator; (2) run the
    complete deterministic verifier conjunction on that same witness; (3) retain
    the witness only if every active deterministically verifiable constraint
    passes."

This module is step (1). It builds the witness from the *clauses*, not from the
solver's model, for a reason worth stating: the model is an assignment to the
abstract projection, and a constructor that read it would inherit the projection's
blind spots. Building from the clauses and then verifying independently is what
makes step (2) an actual cross-check rather than a restatement.

Construction can fail, and failing is a legitimate result. Section 15 of the
directive: certification must fail if witness generation fails. So
`construct_witness` returns a record whose `text` is None with a stated reason,
rather than something approximate.

WHY THE RENDERING IS A BULLET LIST WHEN A LIST CLAUSE IS PRESENT
----------------------------------------------------------------
The inherited segmentation strips list markers and treats each remaining line as a
sentence, so a bullet list of N lines is simultaneously N items and N sentences.
That is the Pair 1 / Pair 3 coupling the audit demonstrated, used here
constructively: one rendering can satisfy a structural item count and a sentence
count at once, but only when the two counts agree. When they disagree no rendering
satisfies both, and the constructor says so instead of guessing.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19.encoding import ClauseKind, Composition
from dci.v19.parsing import OrderingRelation

# A deterministic vocabulary. Every entry is a single ASCII word token under the
# frozen `WORD_PATTERN`, so a filler word never becomes two tokens or none.
VOCABULARY: tuple[str, ...] = (
    "alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliett", "kilo", "lima", "mike", "november", "oscar", "papa",
    "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey",
    "xray", "yankee", "zulu",
)

# The construction procedure's identity. Recorded with every witness so that a
# changed constructor is visible in the artifact rather than only in the diff.
CONSTRUCTOR_ID = "v19:witness-constructor.deterministic-v1"


class WitnessConstructionError(RuntimeError):
    """The constructor cannot build a witness for this composition."""


@dataclass(frozen=True)
class WitnessRecord:
    """One construction attempt, successful or not.

    `text is None` means construction failed; `reason` says why, and certification
    fails closed on it. A record is produced either way so that section 8.5's
    "every proposal, rejection reason, solver record, witness, verifier output, and
    attempt seed is archived" holds for the failures too.
    """
    composition_id: str
    encoding_hash: str
    constructor: str
    seed: int
    text: str | None
    reason: str
    structure: Mapping[str, Any]

    def __post_init__(self):
        if not self.reason:
            raise WitnessConstructionError("a witness record states its reason")
        if self.text is not None and not self.text.strip():
            raise WitnessConstructionError(
                f"{self.composition_id}: an all-whitespace witness is not a "
                "constructed answer; return None with a reason instead")

    @property
    def constructed(self) -> bool:
        return self.text is not None

    @property
    def witness_hash(self) -> str:
        """Hash of the witness bytes, or of its absence."""
        return sha(["v19/witness", self.text if self.text is not None else None])

    def state(self) -> dict[str, Any]:
        return {"composition_id": self.composition_id,
                "encoding_hash": self.encoding_hash,
                "constructor": self.constructor, "seed": self.seed,
                "constructed": self.constructed, "text": self.text,
                "witness_hash": self.witness_hash,
                "structure": dict(self.structure)}

    def describe(self) -> dict[str, Any]:
        return {**self.state(), "reason": self.reason}


def _requirements(composition: Composition) -> dict[str, Any]:
    """What the clauses demand of the rendered text, gathered in one place."""
    wanted: dict[str, Any] = {
        "n_items": None, "n_sentences": None, "relation": None,
        "mandatory_words": (), "all_distinct": False, "increasing": False}
    for clause in composition.clauses:
        if clause.kind is ClauseKind.EXACT_ITEM_COUNT:
            wanted["n_items"] = clause.parameters["n_items"]
        elif clause.kind is ClauseKind.ITEM_PRECEDENCE:
            wanted["relation"] = clause.parameters["relation"]
        elif clause.kind is ClauseKind.EXACT_SENTENCE_COUNT:
            wanted["n_sentences"] = clause.parameters["n_sentences"]
        elif clause.kind is ClauseKind.INCREASING_SENTENCE_LENGTHS:
            wanted["increasing"] = True
        elif clause.kind is ClauseKind.MANDATORY_TOKENS:
            wanted["mandatory_words"] = tuple(clause.parameters["mandatory_words"])
        elif clause.kind is ClauseKind.ALL_TOKENS_DISTINCT:
            wanted["all_distinct"] = True
    return wanted


def _topological_order(relation: OrderingRelation) -> tuple[str, ...]:
    """A valid linear extension, chosen deterministically (lexicographic first).

    The relation is acyclic by construction, so one exists. Picking the
    lexicographically smallest ready item at each step makes the witness
    reproducible from the relation alone.
    """
    remaining = set(relation.items)
    edges = list(relation.edges)
    order: list[str] = []
    while remaining:
        blocked = {after for before, after in edges
                   if before in remaining and after in remaining}
        ready = sorted(remaining - blocked)
        if not ready:                                  # pragma: no cover - acyclic
            raise WitnessConstructionError(
                "no linear extension exists, so the relation was not acyclic")
        order.append(ready[0])
        remaining.discard(ready[0])
    return tuple(order)


class _Words:
    """A deterministic supply of never-repeated word tokens."""

    def __init__(self, seed: int, forbidden: Sequence[str]):
        self.index = seed % len(VOCABULARY)
        self.round = 0
        self.used: set[str] = set()
        self.forbidden = tuple(forbidden)

    def take(self) -> str:
        for _ in range(len(VOCABULARY) * 64):
            base = VOCABULARY[self.index]
            candidate = base if self.round == 0 else f"{base}{self.round}"
            self.index += 1
            if self.index == len(VOCABULARY):
                self.index, self.round = 0, self.round + 1
            if candidate in self.used:
                continue
            # A filler must not contain a declared item label, or the ordering
            # verifier's containment matching would identify it as that item.
            if any(label and label in candidate for label in self.forbidden):
                continue
            self.used.add(candidate)
            return candidate
        raise WitnessConstructionError(          # pragma: no cover - vocabulary
            "the deterministic vocabulary is exhausted for this composition")

    def reserve(self, word: str) -> None:
        self.used.add(word)


def construct_witness(composition: Composition, *, seed: int = 0) -> WitnessRecord:
    """Build a concrete answer intended to satisfy every clause at once.

    Deterministic in `(composition, seed)`. The seed varies the filler vocabulary
    only; it never varies whether a constraint is satisfied, so a failure cannot be
    retried away by reseeding.
    """
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise WitnessConstructionError(f"seed {seed!r} is not a non-negative int")
    wanted = _requirements(composition)
    relation: OrderingRelation | None = wanted["relation"]
    labels = _topological_order(relation) if relation is not None else ()

    def fail(reason: str, **structure: Any) -> WitnessRecord:
        return WitnessRecord(
            composition_id=composition.composition_id,
            encoding_hash=composition.encoding_hash, constructor=CONSTRUCTOR_ID,
            seed=seed, text=None, reason=reason,
            structure={"requested": _describe_requirements(wanted), **structure})

    n_items = wanted["n_items"]
    n_sentences = wanted["n_sentences"]
    as_list = n_items is not None or relation is not None

    if as_list and n_items is None:
        # A precedence clause with no count clause: the declared items are the
        # whole list, which is the smallest rendering consistent with the relation.
        n_items = len(labels)
    if as_list and n_items is not None and n_items < len(labels):
        return fail(
            f"the composition requires exactly {n_items} list item(s) while the "
            f"ordering relation declares {len(labels)}; no arrangement places "
            "more items than exist, so the composition is infeasible rather than "
            "hard to construct (section 8.6)")
    if as_list and n_sentences is not None and n_sentences != n_items:
        return fail(
            f"the composition requires exactly {n_items} list item(s) and exactly "
            f"{n_sentences} sentence(s). Under the frozen segmentation each item "
            "line is also a sentence, so a list rendering gives equal counts and a "
            "prose rendering gives zero items; no single rendering satisfies both")

    n_segments = n_items if as_list else n_sentences
    if n_segments is None:
        # Nothing fixes the structure, so one segment is the minimal rendering that
        # can still carry the lexical clauses.
        n_segments = max(1, len(wanted["mandatory_words"]))
    if wanted["increasing"] and n_segments < 2:
        n_segments = max(n_segments, 2)

    lengths = ([index + 1 for index in range(n_segments)] if wanted["increasing"]
               else [1] * n_segments)
    if as_list:
        # Each item must be able to carry its label as its first word.
        lengths = [max(length, 1) for length in lengths]

    supply = _Words(seed, forbidden=labels)
    for label in labels:
        supply.reserve(label)
    mandatory = list(dict.fromkeys(wanted["mandatory_words"]))
    for word in mandatory:
        supply.reserve(word)

    # Enough room for the labels plus every mandatory word.
    capacity = sum(lengths)
    needed = len(labels) + len(mandatory)
    if capacity < needed:
        if wanted["increasing"] or n_segments != len(lengths):
            return fail(
                f"the rendering has room for {capacity} word(s) but the "
                f"composition requires {needed} distinguished word(s)")
        lengths[-1] += needed - capacity

    segments: list[list[str]] = []
    pending_mandatory = list(mandatory)
    for index, length in enumerate(lengths):
        words: list[str] = []
        if as_list and index < len(labels):
            words.append(labels[index])
        while len(words) < length:
            if pending_mandatory:
                words.append(pending_mandatory.pop(0))
            else:
                words.append(supply.take())
        segments.append(words)
    if pending_mandatory:
        segments[-1].extend(pending_mandatory)
        pending_mandatory = []

    if as_list:
        text = "\n".join("- " + " ".join(words) for words in segments)
    else:
        text = " ".join(" ".join(words).capitalize() + "." for words in segments)

    return WitnessRecord(
        composition_id=composition.composition_id,
        encoding_hash=composition.encoding_hash, constructor=CONSTRUCTOR_ID,
        seed=seed, text=text,
        reason=(f"constructed {len(segments)} "
                f"{'list item' if as_list else 'sentence'}(s) with word counts "
                f"{[len(w) for w in segments]}"),
        structure={"requested": _describe_requirements(wanted),
                   "rendering": "bullet_list" if as_list else "prose",
                   "n_segments": len(segments),
                   "segment_lengths": [len(w) for w in segments],
                   "item_order": list(labels),
                   "mandatory_placed": mandatory})


def _describe_requirements(wanted: Mapping[str, Any]) -> dict[str, Any]:
    relation = wanted["relation"]
    return {"n_items": wanted["n_items"], "n_sentences": wanted["n_sentences"],
            "increasing": wanted["increasing"],
            "all_distinct": wanted["all_distinct"],
            "mandatory_words": list(wanted["mandatory_words"]),
            "relation": relation.state() if relation is not None else None}
