"""The Pair 1 structured list parser, separated from both scientific verdicts.

Section 4.2 states Pair 1's principal measurement risk in one sentence: "both the
count and ordering verifiers may parse the same list representation. A malformed
list could therefore change both verdicts through shared parsing rather than
through genuine interference." The architectural answer is to make the shared step
a first-class object rather than a private detail of two functions:

    raw final-answer segment
              |
              v
      parse_list(text, policy)  ->  ParsedList
              |
      +-------+--------+
      |                |
      v                v
  exact count      ordering
      |                |
      v                v
  target verdict   focal verdict

Because `ParsedList` is inspectable, a later coupling audit can ask whether two
verdicts moved together because the *parse* changed or because the *behaviour*
did. That question is unanswerable if the parse exists only inside the verifiers.

WHAT THE PREREGISTRATION FIXES, AND WHAT IT DOES NOT
----------------------------------------------------
It fixes the statements ("Produce exactly N bullet-list items"; "Place the items
in the correct transitive order"), the family labels, the coupling risk, and that
the verifiers must be built (sections 4.1, 4.2, 10.9, 14.2). It fixes no parsing
semantics at all: not the markers, not whether numbered lists count, not nesting,
not continuation lines, not empty items, not Unicode normalisation, and not how an
item is matched to a declared entity.

So there is no frozen v19 list policy to implement, and inventing one silently
would put an unreviewed measurement decision under the primary outcome of a third
of the design. Instead:

  * `ListPolicy` makes every one of those decisions an explicit, hashed field;
  * there is NO default policy parameter anywhere in this module, so no call site
    can drift onto an implied answer;
  * `INHERITED_MARKER_POLICY` reproduces the one recoverable candidate in the
    repository - `dci.verifiers.rules.LIST_MARKER`, already load-bearing because
    `split_sentences` strips it - and is labelled a candidate, not the frozen rule;
  * `UNDETERMINED_BY_PREREGISTRATION` names each field the protocol does not fix,
    with the question that has to be answered, and Stage 2 certification fails
    closed until `verifiers.p1.list_policy` is frozen by a signed decision.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from dci.provenance.hashes import sha

NORMALISATIONS = ("none", "NFC", "NFD", "NFKC", "NFKD")

# How an observed item is matched to one of the relation's declared entity labels.
#   normalised_containment: the label occurs in the item text after normalisation.
#   leading_label:          the item text begins with the label.
LABEL_MATCH_MODES = ("normalised_containment", "leading_label")

MARKER_KINDS = ("bullet", "numbered")

# Why a marker line did not become a counted item.
EXCLUSION_REASONS = ("numbered_not_counted", "nested_not_counted", "empty_item")


@dataclass(frozen=True)
class ListPolicy:
    """Every list-parsing decision Pair 1 needs, as one hashable object.

    Field order is part of the hash only through the field *names*: `state()`
    sorts, so reordering the declaration does not move the hash while changing any
    answer does.
    """
    policy_id: str
    provenance: str
    bullet_markers: tuple[str, ...]
    numbered_forms: tuple[str, ...]
    numbered_max_digits: int
    require_space_after_marker: bool
    numbered_items_count: bool
    nested_items_count: bool
    continuation_joins_previous: bool
    empty_items_count: bool
    unicode_normalisation: str
    label_match: str
    label_case_sensitive: bool
    extra_items_permitted: bool

    def __post_init__(self):
        if not self.policy_id or not self.provenance:
            raise ValueError("a list policy needs an id and a provenance note; an "
                             "anonymous parsing rule cannot be audited")
        if not self.bullet_markers and not (self.numbered_forms
                                            and self.numbered_items_count):
            raise ValueError(
                f"{self.policy_id}: no marker can open an item, so every answer "
                "parses to zero items and the target verdict is constant")
        for marker in self.bullet_markers:
            if len(marker) != 1:
                raise ValueError(f"{self.policy_id}: bullet marker {marker!r} is "
                                 "not a single character")
        for form in self.numbered_forms:
            if form.count("N") != 1:
                raise ValueError(
                    f"{self.policy_id}: numbered form {form!r} must contain "
                    "exactly one 'N' standing for the digits")
        if not 1 <= self.numbered_max_digits <= 9:
            raise ValueError(f"{self.policy_id}: numbered_max_digits "
                             f"{self.numbered_max_digits} is outside 1..9")
        if self.unicode_normalisation not in NORMALISATIONS:
            raise ValueError(
                f"{self.policy_id}: {self.unicode_normalisation!r} is not one of "
                f"{NORMALISATIONS}")
        if self.label_match not in LABEL_MATCH_MODES:
            raise ValueError(f"{self.policy_id}: {self.label_match!r} is not one "
                             f"of {LABEL_MATCH_MODES}")

    def state(self) -> dict[str, Any]:
        """The canonical serialisation that enters every hash."""
        return {"policy_id": self.policy_id,
                "bullet_markers": list(self.bullet_markers),
                "numbered_forms": list(self.numbered_forms),
                "numbered_max_digits": self.numbered_max_digits,
                "require_space_after_marker": self.require_space_after_marker,
                "numbered_items_count": self.numbered_items_count,
                "nested_items_count": self.nested_items_count,
                "continuation_joins_previous": self.continuation_joins_previous,
                "empty_items_count": self.empty_items_count,
                "unicode_normalisation": self.unicode_normalisation,
                "label_match": self.label_match,
                "label_case_sensitive": self.label_case_sensitive,
                "extra_items_permitted": self.extra_items_permitted}

    @property
    def policy_hash(self) -> str:
        """Identity of the parsing semantics.

        Excludes `provenance`, which is the prose explaining where the policy came
        from. Including it would make rewording a citation look like a change of
        measurement.
        """
        return sha(["v19/list-policy", self.state()])


# --------------------------------------------------------------- the candidate
#
# `dci.verifiers.rules.LIST_MARKER` is `^\s*(?:[-*•‣▪]|\(?\d{1,2}[.)])\s+`. Read
# field by field:
#
#   bullet_markers              the five characters in the class
#   numbered_forms              `\(?\d{1,2}[.)]` admits "1." "1)" and "(1)"
#   numbered_max_digits         `{1,2}`, so "100." is NOT a marker
#   require_space_after_marker  the trailing `\s+`
#   nested_items_count          leading `\s*` accepts any indent and the regex
#                               records none, so indented items are ordinary items
#
# The regex says nothing about the remaining five fields. They are filled with the
# reading that keeps this policy closest to the inherited behaviour and are listed
# in UNDETERMINED_BY_PREREGISTRATION below.

INHERITED_MARKER_POLICY = ListPolicy(
    policy_id="v19:list-policy.inherited-marker",
    provenance=(
        "reproduces dci.verifiers.rules.LIST_MARKER, the only list-segmentation "
        "rule in the repository and already load-bearing because split_sentences "
        "strips it; reuse keeps Pair 1 and Pair 3 on one frozen segmentation "
        "rather than two (sections 4.2, 4.4, 14.2)"),
    bullet_markers=("-", "*", "•", "‣", "▪"),
    numbered_forms=("N.", "N)", "(N)"),
    numbered_max_digits=2,
    require_space_after_marker=True,
    numbered_items_count=True,
    nested_items_count=True,
    continuation_joins_previous=True,
    empty_items_count=False,
    unicode_normalisation="none",
    label_match="normalised_containment",
    label_case_sensitive=False,
    # Nothing is recoverable here: the inherited module has no ordering verifier at
    # all. False is the strict reading, under which every list item must be one of
    # the declared items. See UNDETERMINED_BY_PREREGISTRATION.
    extra_items_permitted=False)


# Each entry: field -> the question the preregistration leaves open. The keys are
# asserted against `ListPolicy`'s own fields, so a field added later without an
# entry here is caught rather than assumed settled.
UNDETERMINED_BY_PREREGISTRATION: Mapping[str, str] = {
    "bullet_markers":
        "which characters open a bullet-list item; the inherited regex admits "
        "five and excludes '+', which several models emit",
    "numbered_forms":
        "which enumerated forms exist at all",
    "numbered_max_digits":
        "the inherited regex caps enumerated items at two digits, so '100.' is "
        "not a marker; material if a calibrated n_items can exceed 99",
    "require_space_after_marker":
        "whether '-item' with no space is an item",
    "numbered_items_count":
        "whether an enumerated list is a BULLET list for the purposes of "
        "'produce exactly N bullet-list items'",
    "nested_items_count":
        "whether an indented sub-item is counted individually, folded into its "
        "parent, or excluded",
    "continuation_joins_previous":
        "whether a non-marker line after an item continues that item or is prose",
    "empty_items_count":
        "whether a marker with no content is an item",
    "unicode_normalisation":
        "whether the segment is normalised before parsing, which decides whether "
        "combining marks and compatibility variants of the markers are markers",
    "label_match":
        "how an observed item is matched to a declared entity in the ordering "
        "relation; the protocol names no matching rule",
    "label_case_sensitive":
        "whether entity matching is case sensitive",
    "extra_items_permitted":
        "whether \"place the items in the correct transitive order\" quantifies "
        "over the declared items only, permitting a longer list that also contains "
        "undeclared items, or over the list's items, so that an undeclared item is "
        "a structural failure. It decides whether a composition requiring more "
        "items than the relation declares is feasible at all, and the encoding and "
        "the verifier disagree until it is answered",
}


def assert_policy_fields_are_accounted_for() -> None:
    """Every parsing decision is either fixed by v19 or listed as open.

    `policy_id` and `provenance` are identity and prose, not decisions. Every
    other field must appear in `UNDETERMINED_BY_PREREGISTRATION` for as long as
    the protocol fixes none of them, so adding a field without stating whether
    v19 settles it fails here instead of acquiring a silent default.
    """
    import dataclasses
    decisions = {f.name for f in dataclasses.fields(ListPolicy)} - {
        "policy_id", "provenance"}
    unlisted = sorted(decisions - set(UNDETERMINED_BY_PREREGISTRATION))
    if unlisted:
        raise ValueError(
            f"list-policy field(s) {unlisted} are neither fixed by the "
            "preregistration nor listed as open decisions; a parsing decision "
            "with no stated status is a hidden default")
    unknown = sorted(set(UNDETERMINED_BY_PREREGISTRATION) - decisions)
    if unknown:
        raise ValueError(f"UNDETERMINED_BY_PREREGISTRATION names {unknown}, "
                         "which are not ListPolicy fields")


# ------------------------------------------------------------------ the parse

@dataclass(frozen=True)
class ListItem:
    """One marker line, whether or not it ends up counted.

    `span` indexes the NORMALISED text, which is what `ParsedList.text` holds, so
    a diagnostic span can always be sliced back out and shown to a human.
    """
    ordinal: int
    marker: str
    marker_kind: str
    indent: int
    content: str
    span: tuple[int, int]
    continuation_lines: int = 0
    excluded_because: str = ""

    @property
    def counted(self) -> bool:
        return not self.excluded_because

    def describe(self) -> dict[str, Any]:
        return {"ordinal": self.ordinal, "marker": self.marker,
                "marker_kind": self.marker_kind, "indent": self.indent,
                "content": self.content, "span": list(self.span),
                "continuation_lines": self.continuation_lines,
                "excluded_because": self.excluded_because}


@dataclass(frozen=True)
class ParsedList:
    """The shared structural interpretation both Pair 1 verifiers read.

    Everything here is diagnostic evidence in the sense of section 11.8: it
    records how the answer was read, not what the answer was about. The field-role
    registry classifies verifier evidence as `diagnostic`, so none of it may enter
    a primary formula. `assert_evidence_is_diagnostic` in `dci.v19.verifiers`
    enforces that on the way out.
    """
    text: str
    policy_hash: str
    normalisation: str
    items: tuple[ListItem, ...]
    excluded: tuple[ListItem, ...]
    prose_spans: tuple[tuple[int, int], ...]
    trailing_prose: bool
    leading_prose: bool

    @property
    def count(self) -> int:
        """The observed number of bullet-list items under the policy."""
        return len(self.items)

    @property
    def contents(self) -> tuple[str, ...]:
        return tuple(item.content for item in self.items)

    @property
    def max_indent_depth(self) -> int:
        return max((item.indent for item in self.items), default=0)

    def describe(self) -> dict[str, Any]:
        """Serialisable diagnostic evidence: spans, exclusions, normalisation."""
        return {"policy_hash": self.policy_hash,
                "normalisation": self.normalisation,
                "observed_count": self.count,
                "items": [i.describe() for i in self.items],
                "excluded": [i.describe() for i in self.excluded],
                "prose_spans": [list(s) for s in self.prose_spans],
                "leading_prose": self.leading_prose,
                "trailing_prose": self.trailing_prose}


def _numbered_pattern(policy: ListPolicy) -> re.Pattern[str] | None:
    if not policy.numbered_forms:
        return None
    digits = rf"\d{{1,{policy.numbered_max_digits}}}"
    alternatives = "|".join(
        re.escape(form).replace("N", digits) for form in policy.numbered_forms)
    return re.compile(f"(?:{alternatives})")


def _bullet_pattern(policy: ListPolicy) -> re.Pattern[str] | None:
    if not policy.bullet_markers:
        return None
    return re.compile("[" + re.escape("".join(policy.bullet_markers)) + "]")


def require_policy(policy: Any) -> ListPolicy:
    """Refuse anything but an explicit policy.

    Separated out so the check survives type narrowing: the whole point is to
    catch a caller who passes `None`, a dict, or the wrong object entirely.
    """
    if not isinstance(policy, ListPolicy):
        raise TypeError(
            f"an explicit ListPolicy is required, got {type(policy).__name__}. "
            "The preregistration fixes no list-parsing semantics, so there is no "
            "default to fall back on (see UNDETERMINED_BY_PREREGISTRATION)")
    return policy


def normalise(text: Any, policy: ListPolicy) -> str:
    """Apply the policy's Unicode normalisation. `None` is the empty segment."""
    raw = "" if text is None else str(text)
    if policy.unicode_normalisation == "none":
        return raw
    return unicodedata.normalize(
        cast(Any, policy.unicode_normalisation), raw)


def parse_list(text: Any, policy: ListPolicy) -> ParsedList:
    """Segment a final-answer segment into list items under an explicit policy.

    There is deliberately no default policy: section 14.2 requires the Pair 1
    semantics to be built, the preregistration fixes none of them, and a default
    would let a call site inherit an unreviewed measurement decision.
    """
    policy = require_policy(policy)
    body = normalise(text, policy)
    bullets, numbers = _bullet_pattern(policy), _numbered_pattern(policy)
    space = r"\s+" if policy.require_space_after_marker else r"\s*"

    found: list[dict[str, Any]] = []
    prose: list[tuple[int, int]] = []
    offset = 0
    for line in body.split("\n"):
        start, end = offset, offset + len(line)
        offset = end + 1                      # the newline we split on
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        kind = marker = ""
        rest = ""
        if bullets is not None and (m := bullets.match(stripped)):
            tail = re.match(space, stripped[m.end():])
            if tail is not None and (tail.end() > 0
                                     or not policy.require_space_after_marker):
                kind, marker = "bullet", m.group(0)
                rest = stripped[m.end() + tail.end():]
        if not kind and numbers is not None and (m := numbers.match(stripped)):
            tail = re.match(space, stripped[m.end():])
            if tail is not None and (tail.end() > 0
                                     or not policy.require_space_after_marker):
                kind, marker = "numbered", m.group(0)
                rest = stripped[m.end() + tail.end():]
        if kind:
            found.append({"marker": marker, "kind": kind, "indent": indent,
                          "content": rest.strip(), "start": start, "end": end,
                          "continuations": 0})
        elif found and policy.continuation_joins_previous and stripped:
            last = found[-1]
            last["content"] = (last["content"] + " " + stripped).strip()
            last["end"] = end
            last["continuations"] += 1
        elif stripped:
            prose.append((start, end))

    base_indent = min((f["indent"] for f in found), default=0)
    items: list[ListItem] = []
    excluded: list[ListItem] = []
    for ordinal, raw in enumerate(found, start=1):
        reason = ""
        if raw["kind"] == "numbered" and not policy.numbered_items_count:
            reason = "numbered_not_counted"
        elif raw["indent"] > base_indent and not policy.nested_items_count:
            reason = "nested_not_counted"
        elif not raw["content"] and not policy.empty_items_count:
            reason = "empty_item"
        item = ListItem(ordinal=ordinal, marker=raw["marker"],
                        marker_kind=raw["kind"], indent=raw["indent"],
                        content=raw["content"],
                        span=(raw["start"], raw["end"]),
                        continuation_lines=raw["continuations"],
                        excluded_because=reason)
        (excluded if reason else items).append(item)

    first_item_start = min((f["start"] for f in found), default=None)
    last_item_end = max((f["end"] for f in found), default=None)
    return ParsedList(
        text=body, policy_hash=policy.policy_hash,
        normalisation=policy.unicode_normalisation,
        items=tuple(items), excluded=tuple(excluded), prose_spans=tuple(prose),
        leading_prose=any(s < first_item_start for s, _ in prose)
        if first_item_start is not None else bool(prose),
        trailing_prose=any(e > last_item_end for _, e in prose)
        if last_item_end is not None else False)


# ----------------------------------------------------- the ordering relation

class RelationError(ValueError):
    """A relation specification that cannot be satisfied by any arrangement."""


@dataclass(frozen=True)
class OrderingRelation:
    """The instantiated Pair 1 focal relation: declared items and precedences.

    A *partial* order is permitted and matters: if the specification constrains
    only x2 before x4 and x4 before x1, then any arrangement respecting those is
    correct, and there may be several. A verifier that compared against one
    canonical string would fail valid answers, which is why this is a relation
    over labels rather than an expected sequence.
    """
    items: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self):
        if len(self.items) < 2:
            raise RelationError(
                f"an ordering relation needs at least two items, got "
                f"{list(self.items)}; a single item cannot be misordered")
        if any(not label or label != label.strip() for label in self.items):
            raise RelationError(f"item labels must be non-empty and unpadded: "
                                f"{list(self.items)}")
        if len(set(self.items)) != len(self.items):
            raise RelationError(f"duplicate item labels in {list(self.items)}; a "
                                "label must identify one item")
        known = set(self.items)
        for before, after in self.edges:
            if before not in known or after not in known:
                raise RelationError(
                    f"edge {before!r} -> {after!r} names an item outside the "
                    f"declared set {sorted(known)}")
            if before == after:
                raise RelationError(f"{before!r} cannot precede itself")
        if len(set(self.edges)) != len(self.edges):
            raise RelationError(f"duplicate edges in {list(self.edges)}")
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        outgoing: dict[str, list[str]] = {i: [] for i in self.items}
        indegree = {i: 0 for i in self.items}
        for before, after in self.edges:
            outgoing[before].append(after)
            indegree[after] += 1
        queue = [i for i in self.items if indegree[i] == 0]
        seen = 0
        while queue:
            node = queue.pop()
            seen += 1
            for nxt in outgoing[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if seen != len(self.items):
            cyclic = sorted(i for i in self.items if indegree[i] > 0)
            raise RelationError(
                f"the precedence edges contain a cycle involving {cyclic}. No "
                "arrangement satisfies it, so the composition is impossible and "
                "outside the estimand (section 8.6) rather than a failing answer")

    def closure(self) -> tuple[tuple[str, str], ...]:
        """The transitive closure, in sorted order for a stable hash.

        On a fully ordered observation the closure adds no *check* - positions in
        a list are a total order, so transitivity holds automatically. It is
        computed anyway because it is what makes a violation reportable ("x2 must
        precede x1, via x4") and because building it is what proves the
        specification is acyclic.
        """
        reach: dict[str, set[str]] = {i: set() for i in self.items}
        for before, after in self.edges:
            reach[before].add(after)
        changed = True
        while changed:
            changed = False
            for node in self.items:
                new = {far for near in reach[node] for far in reach[near]}
                new -= reach[node] | {node}
                if new:
                    reach[node] |= new
                    changed = True
        return tuple(sorted((a, b) for a in self.items for b in reach[a]))

    @property
    def chain_depth(self) -> int:
        """The longest chain of required precedences, counted in edges.

        Reported as a diagnostic. The Pair 1 focal rule declares a parameter named
        `ordering_depth` (see `pairs.PAIR_1`), but the preregistration never says
        what it ranges over, so this is NOT that parameter and must not be used as
        if the Stage 5 calibration had happened.

        The relation is acyclic - `__post_init__` established that - so relaxing
        once per item is enough to reach the longest path.
        """
        longest = {i: 0 for i in self.items}
        for _ in self.items:
            for before, after in self.edges:
                longest[after] = max(longest[after], longest[before] + 1)
        return max(longest.values(), default=0)

    def state(self) -> dict[str, Any]:
        return {"items": list(self.items),
                "edges": [list(e) for e in self.edges],
                "closure": [list(e) for e in self.closure()]}

    @property
    def relation_hash(self) -> str:
        return sha(["v19/ordering-relation", self.state()])


def match_items_to_labels(parsed: ParsedList, relation: OrderingRelation,
                          policy: ListPolicy) -> dict[str, Any]:
    """Which declared entity each observed item is, under the policy's rule.

    Returns the observed label sequence plus every way the identification can be
    unclear, each kept separate: an item matching no label, an item matching more
    than one, a label claimed by more than one item, and labels never seen. Those
    are different structural facts and collapsing them into one boolean is what
    makes a coupling audit impossible afterwards.
    """
    def prepare(value: str) -> str:
        return value if policy.label_case_sensitive else value.casefold()

    labels = {label: prepare(label) for label in relation.items}
    sequence: list[str | None] = []
    unmatched: list[int] = []
    ambiguous: list[dict[str, Any]] = []
    for item in parsed.items:
        body = prepare(item.content)
        if policy.label_match == "leading_label":
            hits = [label for label, needle in labels.items()
                    if body.startswith(needle)]
        else:
            hits = [label for label, needle in labels.items() if needle in body]
        if len(hits) == 1:
            sequence.append(hits[0])
        elif not hits:
            sequence.append(None)
            unmatched.append(item.ordinal)
        else:
            sequence.append(None)
            ambiguous.append({"ordinal": item.ordinal,
                              "candidates": sorted(hits)})
    seen = [label for label in sequence if label is not None]
    duplicated = sorted({label for label in seen if seen.count(label) > 1})
    missing = sorted(set(relation.items) - set(seen))
    return {"sequence": sequence, "unmatched_ordinals": unmatched,
            "ambiguous": ambiguous, "duplicated_labels": duplicated,
            "missing_labels": missing,
            "label_match": policy.label_match,
            "label_case_sensitive": policy.label_case_sensitive}
