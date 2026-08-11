"""The canonical Pair 1 list grammar, and the parser both its verifiers read.

Section 4.2 states Pair 1's principal measurement risk in one sentence: "both the
count and ordering verifiers may parse the same list representation. A malformed
list could therefore change both verdicts through shared parsing rather than through
genuine interference." The architectural answer is to make the shared step a
first-class, inspectable object:

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

WHERE THE SEMANTICS COME FROM
-----------------------------
The preregistration fixes the two statements, the family labels, the coupling risk,
and that the support must be built (sections 4.1, 4.2, 10.9, 14.2). It fixes no
parsing rule at all. Every field of `ListPolicy` was therefore an open question, and
`RESOLVED_BY_AMENDMENT` records the answer the prospective Stage 2 amendment gives
and why - see docs/v19_stage2_specification_amendments.md. `CANONICAL_LIST_POLICY`
is that grammar. There is still no default policy parameter anywhere, so a call site
cannot drift onto an implied answer; the amendment is what makes one policy the
frozen one, and the registry is where it is frozen.

Two decisions in that amendment are worth reading in the source rather than the
document.

`extra_items_permitted = False`. An item matching no declared entity is a structural
failure. The alternative - order the declared items and ignore the rest - would
leave the focal rule silent about part of the list the target counts, and section
4.2's coupling analysis presumes the two rules read the same list.

`label_match = "token_membership"`. An item is identified with a declared entity
when that entity appears as one of the item's word tokens. The earlier reading was
substring containment, which the audit broke twice: "item1" was found inside
"item10", and a mandatory word "alfaX" was found to contain the label "alfa". Token
equality removes both, and it removes them at the level of the frozen text policy
rather than by special-casing either.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import text as textlib
from dci.v19.text import CANONICAL_TEXT_POLICY, TextPolicy

# How an observed item is matched to one of the relation's declared entity labels.
#   token_membership: the label is one of the item's word tokens.
#   leading_token:    the label is the item's FIRST word token.
LABEL_MATCH_MODES = ("token_membership", "leading_token")

MARKER_KINDS = ("bullet", "numbered")

# Why a marker line did not become a counted item.
EXCLUSION_REASONS = ("numbered_not_counted", "nested_not_counted", "empty_item")


class ListPolicyError(ValueError):
    """A list grammar that cannot be applied as declared."""


@dataclass(frozen=True)
class ListPolicy:
    """The frozen list grammar: one object, every decision, one hash.

    `text` is the shared text policy rather than a private copy of it, so the list
    span and the sentence span cannot disagree about normalisation, tokenisation or
    case.
    """
    policy_id: str
    provenance: str
    text: TextPolicy
    bullet_markers: tuple[str, ...]
    numbered_forms: tuple[str, ...]
    numbered_max_digits: int
    require_space_after_marker: bool
    numbered_items_count: bool
    nested_items_count: bool
    continuation_joins_previous: bool
    empty_items_count: bool
    label_match: str
    extra_items_permitted: bool

    def __post_init__(self):
        if not self.policy_id or not self.provenance:
            raise ListPolicyError(
                "a list policy needs an id and a provenance note; an anonymous "
                "parsing rule cannot be audited")
        textlib.require_policy(self.text)
        if not self.bullet_markers and not (self.numbered_forms
                                            and self.numbered_items_count):
            raise ListPolicyError(
                f"{self.policy_id}: no marker can open an item, so every answer "
                "parses to zero items and the target verdict is constant")
        for marker in self.bullet_markers:
            if len(marker) != 1:
                raise ListPolicyError(f"{self.policy_id}: bullet marker {marker!r} "
                                      "is not a single character")
        for form in self.numbered_forms:
            if form.count("N") != 1:
                raise ListPolicyError(
                    f"{self.policy_id}: numbered form {form!r} must contain exactly "
                    "one 'N' standing for the digits")
        if not 1 <= self.numbered_max_digits <= 9:
            raise ListPolicyError(f"{self.policy_id}: numbered_max_digits "
                                  f"{self.numbered_max_digits} is outside 1..9")
        if self.label_match not in LABEL_MATCH_MODES:
            raise ListPolicyError(f"{self.policy_id}: {self.label_match!r} is not "
                                  f"one of {LABEL_MATCH_MODES}")

    def marker_patterns(self) -> tuple[str, ...]:
        """The marker regexes, handed to the sentence segmenter.

        Section 4.4's shared-segmentation risk becomes attributable only if both
        spans agree about what a marker is, so the grammar supplies them rather
        than the segmenter hard-coding its own.
        """
        space = r"\s+" if self.require_space_after_marker else r"\s*"
        patterns = []
        if self.bullet_markers:
            patterns.append("^\\s*[" + re.escape("".join(self.bullet_markers))
                            + "]" + space)
        if self.numbered_forms:
            digits = rf"\d{{1,{self.numbered_max_digits}}}"
            alternatives = "|".join(
                re.escape(form).replace("N", digits) for form in self.numbered_forms)
            patterns.append(f"^\\s*(?:{alternatives}){space}")
        return tuple(patterns)

    def state(self) -> dict[str, Any]:
        return {"policy_id": self.policy_id,
                "text_policy": self.text.state(),
                "bullet_markers": list(self.bullet_markers),
                "numbered_forms": list(self.numbered_forms),
                "numbered_max_digits": self.numbered_max_digits,
                "require_space_after_marker": self.require_space_after_marker,
                "numbered_items_count": self.numbered_items_count,
                "nested_items_count": self.nested_items_count,
                "continuation_joins_previous": self.continuation_joins_previous,
                "empty_items_count": self.empty_items_count,
                "label_match": self.label_match,
                "extra_items_permitted": self.extra_items_permitted}

    @property
    def policy_hash(self) -> str:
        """Identity of the grammar, including the text policy it rests on.

        Excludes `provenance`, which explains where the grammar came from; rewording
        a citation is not a change of measurement.
        """
        return sha(["v19/list-policy", self.state()])


CANONICAL_LIST_POLICY = ListPolicy(
    policy_id="v19:list-policy.canonical",
    provenance=(
        "the prospective Stage 2 amendment (docs/v19_stage2_specification_"
        "amendments.md). The marker set descends from the inherited "
        "dci.verifiers.rules.LIST_MARKER, which is the only list segmentation in "
        "the repository and is already load-bearing because the inherited "
        "split_sentences strips it; every other field is a decision the "
        "preregistration does not make, recorded in RESOLVED_BY_AMENDMENT"),
    text=CANONICAL_TEXT_POLICY,
    bullet_markers=("-", "*", "•", "‣", "▪"),
    numbered_forms=("N.", "N)", "(N)"),
    numbered_max_digits=3,
    require_space_after_marker=True,
    numbered_items_count=True,
    nested_items_count=True,
    continuation_joins_previous=True,
    empty_items_count=False,
    label_match="token_membership",
    extra_items_permitted=False)


# Every grammar decision, the answer the amendment gives, and why. Each key is a
# `ListPolicy` field; `assert_policy_fields_are_accounted_for` requires the table to
# stay exhaustive, so a field added later cannot acquire a silent default.
RESOLVED_BY_AMENDMENT: Mapping[str, str] = {
    "bullet_markers":
        "the five characters of the inherited LIST_MARKER. '+' is excluded because "
        "including it would change the inherited sentence segmentation Pair 3 "
        "already depends on",
    "numbered_forms":
        "'N.', 'N)' and '(N)', the three the inherited regex admits",
    "numbered_max_digits":
        "raised from the inherited 2 to 3, so a calibrated n_items between 100 and "
        "999 cannot silently exceed the parser; the inherited cap was an artefact "
        "of the regex, not a decision",
    "require_space_after_marker":
        "required, as inherited: '-word' is a hyphenated word far more often than "
        "it is a list item",
    "numbered_items_count":
        "an enumerated item IS a bullet-list item. The target counts list items, "
        "and refusing enumerated lists would score a correctly structured answer as "
        "zero items",
    "nested_items_count":
        "a nested item is counted individually, as the inherited regex does, "
        "because it is a list item by the same rule as its parent",
    "continuation_joins_previous":
        "a non-marker line after an item continues that item, so a wrapped item is "
        "one item",
    "empty_items_count":
        "a marker with no content is not an item: there is nothing for the ordering "
        "rule to identify",
    "label_match":
        "token membership, not substring containment. Containment made 'item1' a "
        "match inside 'item10' and made a mandatory word 'alfaX' match the label "
        "'alfa'; both are removed by comparing whole word tokens under the frozen "
        "text policy",
    "extra_items_permitted":
        "not permitted: an item matching no declared entity is a structural "
        "failure. Permitting it would leave the focal rule silent about part of the "
        "list the target counts, and section 4.2's coupling analysis presumes both "
        "rules read the same list",
}


# ------------------------------------------------- predeclared equivalent surfaces
#
# Amendment A1 requires the grammar to be "semantically faithful to the prompt": two
# answers that a reader would call the same list must be read as the same list. The
# forms below are the ones the canonical grammar declares equivalent, and
# `test_v19_list_parsing` runs the metamorphic property over all of them - every form
# must yield the same counted item contents in the same order.
#
# The set is exhaustive over the grammar's own admitted surfaces by construction:
# `assert_surface_forms_cover_the_grammar` requires every bullet marker and every
# numbered form to appear in it, so a marker added to the policy without a
# corresponding metamorphic form is a failure rather than an untested surface.
#
# Each renderer takes the item contents and returns a final-answer segment. Contents
# are assumed to contain a space, which `wrapped_items` needs to wrap one.

def _bullet(marker: str):
    def render(contents: Sequence[str]) -> str:
        return "\n".join(f"{marker} {content}" for content in contents)
    return render


def _numbered(form: str, start: int = 1):
    def render(contents: Sequence[str]) -> str:
        return "\n".join(f"{form.replace('N', str(start + i))} {content}"
                         for i, content in enumerate(contents))
    return render


def _wrapped(contents: Sequence[str]) -> str:
    lines = []
    for content in contents:
        head, _, tail = content.partition(" ")
        lines.append(f"- {head}")
        if tail:
            lines.append(f"  {tail}")
    return "\n".join(lines)


def _blank_separated(contents: Sequence[str]) -> str:
    return "\n\n".join(f"- {content}" for content in contents)


def _trailing_space(contents: Sequence[str]) -> str:
    return "\n".join(f"- {content}   \t" for content in contents)


def _crlf(contents: Sequence[str]) -> str:
    return "\r\n".join(f"- {content}" for content in contents) + "\r"


def _uniformly_indented(contents: Sequence[str]) -> str:
    return "\n".join(f"    - {content}" for content in contents)


def _mixed_bullets(contents: Sequence[str]) -> str:
    cycle = ("-", "*", "•", "‣", "▪")
    return "\n".join(f"{cycle[i % len(cycle)]} {content}"
                     for i, content in enumerate(contents))


def _fullwidth_numbered(contents: Sequence[str]) -> str:
    """NFKC folds fullwidth digits and the fullwidth full stop onto 'N.'."""
    wide = {str(d): chr(ord("０") + d) for d in range(10)}
    return "\n".join(
        "".join(wide[c] for c in str(i)) + "．" + f" {content}"
        for i, content in enumerate(contents, start=1))


EQUIVALENT_SURFACE_FORMS: Mapping[str, Any] = {
    "hyphen_bullet": _bullet("-"),
    "asterisk_bullet": _bullet("*"),
    "bullet_u2022": _bullet("•"),
    "bullet_u2023": _bullet("‣"),
    "bullet_u25aa": _bullet("▪"),
    "mixed_bullet_markers": _mixed_bullets,
    "numbered_dot": _numbered("N."),
    "numbered_paren": _numbered("N)"),
    "numbered_bracketed": _numbered("(N)"),
    "numbered_from_seven": _numbered("N.", start=7),
    "numbered_fullwidth_nfkc": _fullwidth_numbered,
    "wrapped_items": _wrapped,
    "blank_lines_between": _blank_separated,
    "trailing_whitespace": _trailing_space,
    "crlf_line_endings": _crlf,
    "uniform_indentation": _uniformly_indented,
}

# Why each form is declared equivalent, so the table can be audited rather than read
# as a list of test fixtures.
SURFACE_FORM_RATIONALE: Mapping[str, str] = {
    "hyphen_bullet": "the reference surface; the inherited marker",
    "asterisk_bullet": "an admitted bullet marker",
    "bullet_u2022": "an admitted bullet marker",
    "bullet_u2023": "an admitted bullet marker",
    "bullet_u25aa": "an admitted bullet marker",
    "mixed_bullet_markers": (
        "marker consistency is not a requirement the prompt states, so an answer "
        "that varies its marker is still the same list"),
    "numbered_dot": "an admitted numbered form; numbered_items_count is true",
    "numbered_paren": "an admitted numbered form",
    "numbered_bracketed": "an admitted numbered form",
    "numbered_from_seven": (
        "the count does not depend on the digits, so an answer that numbers from "
        "anything is the same list"),
    "numbered_fullwidth_nfkc": (
        "NFKC is part of the frozen text policy, so fullwidth digits and a "
        "fullwidth full stop are the same marker as their ASCII forms"),
    "wrapped_items": (
        "continuation_joins_previous is true, so a wrapped item is one item"),
    "blank_lines_between": "a blank line carries no word token and opens no item",
    "trailing_whitespace": "the text policy rstrips each line",
    "crlf_line_endings": (
        "carriage return is a format control character the text policy removes, so "
        "line endings are not a measurement decision"),
    "uniform_indentation": (
        "nesting is relative to the shallowest marker line, so a uniformly indented "
        "list has no nested item"),
}


def assert_surface_forms_cover_the_grammar(
        policy: ListPolicy = CANONICAL_LIST_POLICY) -> None:
    """Every admitted marker must appear in the metamorphic set, with a reason."""
    policy = require_policy(policy)
    undocumented = sorted(set(EQUIVALENT_SURFACE_FORMS) - set(SURFACE_FORM_RATIONALE))
    if undocumented:
        raise ListPolicyError(
            f"surface form(s) {undocumented} have no recorded rationale")
    stray = sorted(set(SURFACE_FORM_RATIONALE) - set(EQUIVALENT_SURFACE_FORMS))
    if stray:
        raise ListPolicyError(f"SURFACE_FORM_RATIONALE names {stray}, which are not "
                              "declared surface forms")
    rendered = {name: render(("alfa one", "bravo two"))
                for name, render in EQUIVALENT_SURFACE_FORMS.items()}
    for marker in policy.bullet_markers:
        if not any(marker in text for text in rendered.values()):
            raise ListPolicyError(
                f"bullet marker {marker!r} is admitted by {policy.policy_id} but no "
                "declared surface form exercises it, so the metamorphic property "
                "would not cover it")
    for form in policy.numbered_forms:
        pattern = re.compile(re.escape(form).replace("N", r"\d+"))
        if not any(pattern.search(text) for text in rendered.values()):
            raise ListPolicyError(
                f"numbered form {form!r} is admitted by {policy.policy_id} but no "
                "declared surface form exercises it")


def assert_policy_fields_are_accounted_for() -> None:
    """Every grammar decision has a recorded answer and a reason.

    `policy_id`, `provenance` and `text` are identity, prose and a delegated
    policy. Every other field must appear in `RESOLVED_BY_AMENDMENT`.
    """
    import dataclasses
    decisions = {f.name for f in dataclasses.fields(ListPolicy)} - {
        "policy_id", "provenance", "text"}
    unlisted = sorted(decisions - set(RESOLVED_BY_AMENDMENT))
    if unlisted:
        raise ListPolicyError(
            f"list-grammar field(s) {unlisted} have no recorded decision; a parsing "
            "decision with no stated answer is a hidden default")
    unknown = sorted(set(RESOLVED_BY_AMENDMENT) - decisions)
    if unknown:
        raise ListPolicyError(f"RESOLVED_BY_AMENDMENT names {unknown}, which are "
                              "not ListPolicy fields")


# ------------------------------------------------------------------ the parse

@dataclass(frozen=True)
class ListItem:
    """One marker line, whether or not it ends up counted."""
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

    Everything here is diagnostic evidence in the sense of section 11.8: it records
    how the answer was read, not what it was about. `assert_evidence_is_diagnostic`
    in `dci.v19.verifiers` enforces that on the way out.
    """
    text: str
    policy_hash: str
    text_policy_hash: str
    items: tuple[ListItem, ...]
    excluded: tuple[ListItem, ...]
    prose_spans: tuple[tuple[int, int], ...]
    trailing_prose: bool
    leading_prose: bool

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def contents(self) -> tuple[str, ...]:
        return tuple(item.content for item in self.items)

    @property
    def max_indent_depth(self) -> int:
        return max((item.indent for item in self.items), default=0)

    def describe(self) -> dict[str, Any]:
        return {"policy_hash": self.policy_hash,
                "text_policy_hash": self.text_policy_hash,
                "observed_count": self.count,
                "items": [i.describe() for i in self.items],
                "excluded": [i.describe() for i in self.excluded],
                "prose_spans": [list(s) for s in self.prose_spans],
                "leading_prose": self.leading_prose,
                "trailing_prose": self.trailing_prose}


def require_policy(policy: Any) -> ListPolicy:
    """Refuse anything but an explicit grammar."""
    if not isinstance(policy, ListPolicy):
        raise TypeError(
            f"an explicit ListPolicy is required, got {type(policy).__name__}. The "
            "grammar is a frozen scientific commitment; there is no default")
    return policy


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


def parse_list(text: Any, policy: ListPolicy) -> ParsedList:
    """Segment a final-answer segment into list items under the frozen grammar."""
    policy = require_policy(policy)
    body = textlib.normalise(text, policy.text)
    bullets, numbers = _bullet_pattern(policy), _numbered_pattern(policy)
    space = r"\s+" if policy.require_space_after_marker else r"\s*"
    word = re.compile(policy.text.word_pattern)

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
        for pattern, label in ((bullets, "bullet"), (numbers, "numbered")):
            if kind or pattern is None:
                continue
            match = pattern.match(stripped)
            if match is None:
                continue
            remainder = stripped[match.end():]
            if not remainder:
                # A marker alone on its line. It IS a marker line carrying no
                # content, and calling it prose would let it join the previous item
                # as a continuation - turning "- a\n- \n- b" into two items, the
                # first of which reads "a -". Whether an empty item counts is then
                # decided by `empty_items_count`, which is where that decision lives.
                kind, marker, rest = label, match.group(0), ""
                continue
            tail = re.match(space, remainder)
            if tail is None:
                continue
            if policy.require_space_after_marker and tail.end() == 0:
                continue
            kind, marker = label, match.group(0)
            rest = remainder[tail.end():]
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
        elif not word.search(raw["content"]) and not policy.empty_items_count:
            # "Empty" means carrying no word token under the frozen text policy, so
            # an item of punctuation alone is empty for the same reason it is not a
            # sentence. The two spans agree because they consult the same pattern.
            reason = "empty_item"
        item = ListItem(ordinal=ordinal, marker=raw["marker"],
                        marker_kind=raw["kind"], indent=raw["indent"],
                        content=raw["content"], span=(raw["start"], raw["end"]),
                        continuation_lines=raw["continuations"],
                        excluded_because=reason)
        (excluded if reason else items).append(item)

    first_item_start = min((f["start"] for f in found), default=None)
    last_item_end = max((f["end"] for f in found), default=None)
    return ParsedList(
        text=body, policy_hash=policy.policy_hash,
        text_policy_hash=policy.text.policy_hash,
        items=tuple(items), excluded=tuple(excluded), prose_spans=tuple(prose),
        leading_prose=any(s < first_item_start for s, _ in prose)
        if first_item_start is not None else bool(prose),
        trailing_prose=any(e > last_item_end for _, e in prose)
        if last_item_end is not None else False)


def sentences(text: Any, policy: ListPolicy) -> list[str]:
    """Sentence segments under the SAME marker definition the list span uses."""
    policy = require_policy(policy)
    return textlib.split_sentences(text, policy.text, policy.marker_patterns())


def sentence_lengths(text: Any, policy: ListPolicy) -> list[int]:
    """The frozen length unit, over the same segmentation."""
    policy = require_policy(policy)
    return textlib.sentence_lengths(text, policy.text, policy.marker_patterns())


# ----------------------------------------------------- the ordering relation

class RelationError(ValueError):
    """A relation specification that cannot be satisfied by any arrangement."""


@dataclass(frozen=True)
class OrderingRelation:
    """The instantiated Pair 1 focal relation: declared items and precedences.

    A *partial* order is permitted and matters: if the specification constrains only
    x2 before x4 and x4 before x1, any arrangement respecting those is correct and
    there may be several. A verifier comparing against one canonical string would
    fail valid answers, which is why this is a relation over labels rather than an
    expected sequence.
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
        for edge in self.edges:
            if len(edge) != 2:
                raise RelationError(f"{edge!r} is not a precedence pair")
            before, after = edge
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

    def assert_labels_are_tokens(self, policy: ListPolicy) -> None:
        """Every label must be exactly one word token under the frozen text policy.

        Token membership cannot identify a label the tokeniser would split, and a
        multi-token label would be silently unfindable rather than reported. Refusing
        it here makes a mis-specified relation a construction error.
        """
        policy = require_policy(policy)
        bad = {}
        for label in self.items:
            tokens = textlib.word_tokens(label, policy.text)
            if tokens != [label] and [textlib.fold(t, policy.text) for t in tokens] \
                    != [textlib.fold(label, policy.text)]:
                bad[label] = tokens
        if bad:
            raise RelationError(
                f"item label(s) are not single word tokens under "
                f"{policy.text.policy_id}: {bad}. Token-membership matching cannot "
                "identify a label the tokeniser splits")
        folded = [textlib.fold(label, policy.text) for label in self.items]
        if len(set(folded)) != len(folded):
            raise RelationError(
                f"item labels collide once folded under {policy.text.policy_id}: "
                f"{sorted(folded)}. Two labels that compare equal cannot identify "
                "two items")

    def closure(self) -> tuple[tuple[str, str], ...]:
        """The transitive closure, sorted for a stable hash."""
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

        A diagnostic. The Pair 1 focal rule declares a parameter named
        `ordering_depth` (see `pairs.PAIR_1`) which the preregistration never
        defines, so this is NOT that parameter and must not stand in for it.
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
    """Which declared entity each observed item is, by word-token equality.

    Returns the observed label sequence plus every way the identification can be
    unclear, each kept separate: an item matching no label, an item matching more
    than one, a label claimed by more than one item, and labels never seen. Those are
    different structural facts, and collapsing them into one boolean is what makes a
    coupling audit impossible afterwards.
    """
    policy = require_policy(policy)
    relation.assert_labels_are_tokens(policy)
    by_folded = {textlib.fold(label, policy.text): label
                 for label in relation.items}

    sequence: list[str | None] = []
    unmatched: list[int] = []
    ambiguous: list[dict[str, Any]] = []
    for item in parsed.items:
        tokens = textlib.folded_tokens(item.content, policy.text)
        if policy.label_match == "leading_token":
            hits = [by_folded[tokens[0]]] if tokens and tokens[0] in by_folded else []
        else:
            hits = sorted({by_folded[t] for t in tokens if t in by_folded})
        if len(hits) == 1:
            sequence.append(hits[0])
        elif not hits:
            sequence.append(None)
            unmatched.append(item.ordinal)
        else:
            sequence.append(None)
            ambiguous.append({"ordinal": item.ordinal, "candidates": sorted(hits)})
    seen = [label for label in sequence if label is not None]
    duplicated = sorted({label for label in seen if seen.count(label) > 1})
    missing = sorted(set(relation.items) - set(seen))
    return {"sequence": sequence, "unmatched_ordinals": unmatched,
            "ambiguous": ambiguous, "duplicated_labels": duplicated,
            "missing_labels": missing, "label_match": policy.label_match,
            "text_policy": policy.text.policy_id}
