"""§7.5's joint-satisfiability and non-entailment witnesses.

Two obligations, both discharged by machine-verified construction rather than
by argument:

* **joint satisfiability** — for every realisable pair of registered
  constraint instances of distinct kinds, one response satisfies both;
* **non-entailment** — for the same pairs, one response satisfies the first and
  fails the second, and one does the reverse.

**Which pairs are realisable, and why the question has an answer.** §8.1's
composed cells put two constituents together, and only these combinations
occur: $A$ with anything, $B$ with anything, one core reference with another,
and the class companion with $A$ or $B$. Two core references co-occur, so the
obligation covers reference-with-reference; but §13.4 requires the three core
references to come from three different **counted statistics**, so two
instances of the same numerator never co-occur and the obligation does not
cover them.

That scoping is not a convenience. A count budget at $q = 0$ **entails** the
rate budget of the same numerator at every $q$: $S \\le 0$ forces the rate to
zero, so no response satisfies the count and fails the rate, and the
non-entailment obligation would be unsatisfiable rather than merely unmet.
§13.4's numerator-diversity rule is what makes the pair unrealisable, and this
module refuses such a pair rather than constructing a witness for it, so the
two rules are checked against each other rather than assumed compatible.

**The constructor envelope.** Every constructor asserts the form it was
written for and refuses outside it. This is registered because a v4r2-era
constructor used outside its envelope was found to report a construction
failure as an entailment claim -- the worst possible failure for this check,
because it turns a bug into a scientific finding.
"""
from __future__ import annotations

from typing import Any, Iterable

from dci1v4.errors import InstrumentError
from dci1v7.verifiers.statistics import s0_count

from dci1v7.verifiers.compliance import passes
from dci1v7.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_RATE, LOWER_BOUND_FORMS,
    Constraint, TARGET_GRID, declared_range, focal_severities,
)
from dci1v7.verifiers.words import SENTENCE_TERMINATORS
from dci1v7.verifiers.statistics import STATISTICS, focal_statistic

__all__ = ["FILLER", "TARGET", "LONG_WORD", "FEATURE_WORD", "feature_free",
           "sentences_text",
           "realisable_pairs", "assert_pair_realisable", "joint_witness",
           "separating_witnesses", "run_witness_suite",
           "assert_filler_is_feature_free",
           "assert_feature_words_are_specific"]

#: Words carrying **none** of the registered features: they do not begin with
#: b, t or a vowel, do not end in ing, y or s, have more than one letter,
#: contain no doubled letter, no comma, no semicolon, no sentence terminator,
#: no upper-case character, no letter a, and none of them is the marker word.
#: Every budget family reads zero on a text made of these, so a filler text is
#: the universal witness for the reference pool.
#:
#: Three of the round-0 fillers had to go when §7.0-R3 added its numerators:
#: `topic` begins with t, `unit` begins with a vowel, and `result` would have
#: been fine but is replaced alongside them so the eight stay a set a reader
#: can check in one pass. `assert_filler_is_feature_free` checks the property
#: rather than trusting this comment, over every registered numerator, so a
#: future numerator cannot silently invalidate the witness corpus.
FILLER = ("point", "clue", "form", "step", "field", "cloud", "north", "guide")

#: The target word is itself feature-free, which is why $A$ composes with every
#: budget family without a construction: seven letters, no a, no doubling, no
#: b at the front, no ing or y at the end, no capital.
TARGET = "however"

#: Longer than the loosest admissible m (12) and still feature-free, so it can
#: break $B$ without moving any family statistic.
LONG_WORD = "counterproductive"

#: One word per numerator that carries that feature and, where possible, no
#: other. Used to push a statistic above a budget or up to a lower bound.
#:
#: §7.0-R3 forced two of them to move. `o` was the one-letter word and `area`
#: was the letter-a word, and both begin with a vowel --- so breaking either
#: family raised the new `vowel_initial` count and broke the *other*
#: constraint of the pair, which the suite correctly reported as an
#: entailment failure. `assert_feature_words_are_specific` now checks the
#: property over every numerator instead of leaving it to inspection.
FEATURE_WORD = {
    "b_initial": "bold",          # b-initial; contains no a, no doubling
    "ing_final": "helping",       # ing-final
    "one_letter": "n",            # one letter; not a vowel, not t, not s
    "doubled_letter": "cell",     # doubled l
    "comma": ",",                 # a raw comma character
    "capital_char": "Point",      # one upper-case character
    "capital_word": "Point",      # a word containing an upper-case character
    "letter_a": "car",            # contains a; not vowel-initial
    "y_final": "duty",            # y-final
    "t_initial": "top",           # t-initial; no a, no doubling, not s-final
    "s_final": "clues",           # s-final; not b/t/vowel-initial, no a
    "vowel_initial": "under",     # vowel-initial; ends r, no a, no doubling
    "sentence": ".",              # a raw sentence terminator
    "semicolon": ";",             # a raw semicolon character
    # v5's eight markers. Each is its own feature word, verbatim: a witness
    # for "use `hence` exactly q times" is q copies of `hence`, which is the
    # only construction that cannot accidentally satisfy another marker's
    # family --- no registered marker is a substring-word of another.
    "marker_thus": "thus",
    "marker_hence": "hence",
    "marker_though": "though",
    "marker_whereas": "whereas",
    "marker_indeed": "indeed",
    "marker_namely": "namely",
    "marker_instead": "instead",
    "marker_overall": "overall",
}

#: Numerators whose feature is a **character** rather than a word. A text made
#: only of these has no words at all, so its rate is undefined and a rate
#: constraint over it fails for the wrong reason; the breaking constructor
#: attaches them to filler words instead.
_CHARACTER_NUMERATORS = ("comma", "sentence", "semicolon")


def assert_filler_is_feature_free() -> dict[str, int]:
    """Every registered numerator reads zero on a filler text --- except the
    sentence count, which reads one.

    The exception is registered rather than patched around: §7.3-R3 counts an
    unterminated final sentence, so no non-blank text has zero sentences and
    RF12's own reserve therefore starts at one. A filler text is still the
    universal witness for RF12, because one is at most every severity RF12 can
    take.
    """
    text = feature_free(40)
    readings = {}
    for statistic_id, fn in STATISTICS.items():
        value = fn(text)
        expected = 1 if statistic_id == "sentence" else 0
        if value != expected:
            raise InstrumentError(
                f"the filler corpus reads {statistic_id} = {value}, not "
                f"{expected}; it is no longer feature-free and every witness "
                "built from it is void")
        readings[statistic_id] = value
    return readings


def feature_free(n_words: int) -> str:
    """A response of ``n_words`` filler words and nothing else."""
    if n_words <= 0:
        return ""
    return " ".join(FILLER[i % len(FILLER)] for i in range(n_words))


def _statistic(kind: str, text: str) -> int:
    if kind == "A":
        return s0_count(text)
    if kind == "B":
        return focal_statistic(text)
    return STATISTICS[FAMILIES[kind].statistic_id](text)


def _group(kind: str) -> str | None:
    return None if kind in ("A", "B") else FAMILIES[kind].feature_group


def assert_pair_realisable(first: Constraint, second: Constraint) -> None:
    """§8.1 plus §13.4: refuse a pair no cell of this design can contain."""
    kinds = {first.kind, second.kind}
    if first.kind == second.kind:
        raise InstrumentError("a cell never states one constraint twice")
    # v5 states realisability on the **structural tier** rather than on a
    # declared role. §7.4 admits Tier 1 and Tier 2 to the core reference slot
    # and Tier 3 to the broad-class slot alone, so "core-eligible" is
    # tier in (1, 2) and "broad-class only" is tier 3. §7.7's rule: A with
    # anything, B with anything, one core reference with another OF A
    # DIFFERENT FEATURE GROUP, and a near-form or broad-class companion with
    # B.
    roles = {k: ("outcome" if k in ("A", "B")
                 else "core_eligible" if FAMILIES[k].structural_tier in (1, 2)
                 else "broad_class")
             for k in kinds}
    values = sorted(roles.values())
    if values == ["broad_class", "broad_class"]:
        raise InstrumentError(
            "§13.10 admits exactly one broad-class companion, so two Tier-3 "
            "families never co-occur")
    if "broad_class" in values and "core_eligible" in values:
        raise InstrumentError(
            "§13.10 places the broad-class companion beside B alone; it never "
            "shares a cell with a core reference")
    if values == ["core_eligible", "core_eligible"]:
        if _group(first.kind) == _group(second.kind):
            raise InstrumentError(
                f"{first.kind} and {second.kind} measure the same feature "
                f"({_group(first.kind)}), and §13.8 admits three core "
                "references from three different feature groups, so they "
                "never co-occur. The obligation is not merely unmet for this "
                "pair -- it is unsatisfiable: a count budget at q=0 forces "
                "its rate sibling's rate to zero, and zero upper-case "
                "characters forces zero words carrying one")


def realisable_pairs() -> list[tuple[Constraint, Constraint]]:
    """Every pair §7.5 must discharge, in a fixed order."""
    outcomes = ([Constraint("A", n) for n in TARGET_GRID]
                + [Constraint("B", m, extended=True)
                   for m in focal_severities(extended=True)])
    references = [Constraint(k, q, reserve=True) for k in FAMILIES
                  if FAMILIES[k].structural_tier in (1, 2)
                  for q in declared_range(k)]
    classes = [Constraint(k, q, reserve=True) for k in FAMILIES
               if FAMILIES[k].structural_tier == 3
               for q in declared_range(k)]
    pairs: list[tuple[Constraint, Constraint]] = []
    for i, a in enumerate(outcomes):
        for b in outcomes[i + 1:]:
            if a.kind != b.kind:
                pairs.append((a, b))
    for outcome in outcomes:
        for other in references + classes:
            pairs.append((outcome, other))
    for i, a in enumerate(references):
        for b in references[i + 1:]:
            if a.kind != b.kind and _group(a.kind) != _group(b.kind):
                pairs.append((a, b))
    return pairs


# ------------------------------------------------------------ constructors
def _satisfy_one(constraint: Constraint, *, base_words: int = 40) -> str:
    """A text satisfying ``constraint`` alone, by its declared form."""
    kind, q = constraint.kind, constraint.severity
    if kind == "A":
        return " ".join([TARGET] * q + [feature_free(base_words)])
    if kind == "B":
        return feature_free(base_words)          # every filler is <= 6 letters
    family = FAMILIES[kind]
    if family.form is FORM_EXACT:
        if family.statistic_id == "sentence":
            # An exact SENTENCE count is not q copies of a terminator: the
            # registered rule counts maximal terminator runs plus an
            # unterminated tail, so q copies of "." followed by filler is
            # q + 1 sentences. The witness is q terminated sentences and no
            # tail, which is what the rule counts as exactly q.
            per = max(3, base_words // max(q, 1))
            return " ".join(f"{feature_free(per)}." for _ in range(q))
        word = FEATURE_WORD[family.statistic_id]
        return " ".join([word] * q + [feature_free(base_words)])
    if family.form in (FORM_COUNT, FORM_RATE):
        return feature_free(max(base_words, _words_needed(constraint)))
    if family.form not in LOWER_BOUND_FORMS:     # pragma: no cover
        raise InstrumentError(f"{kind}: unknown form {family.form!r}")
    word = FEATURE_WORD[family.statistic_id]
    if family.form == "count_lower_bound":
        return " ".join([word] * (q + 2))
    # A rate lower bound is scale-free: an all-feature text reads 100 percent.
    return " ".join([word] * max(q, 8))


def _words_needed(constraint: Constraint) -> int:
    """How long a filler text must be for ``constraint`` to hold on it.

    Only the sentence rate needs one. A filler text is one unterminated
    sentence, so its sentence rate is 100/W, and CR12 at q = 1 wants that at
    most one --- which a forty-word witness does not deliver. Every other
    budget numerator reads zero on filler and holds at any length.
    """
    if constraint.kind in ("A", "B"):
        return 0
    family = FAMILIES[constraint.kind]
    if family.form is FORM_RATE and family.statistic_id == "sentence":
        return -(-100 // constraint.severity) + 5
    return 0


def joint_witness(first: Constraint, second: Constraint) -> str:
    """One response satisfying both constraints of a realisable pair."""
    assert_pair_realisable(first, second)
    lower = [c for c in (first, second)
             if c.kind not in ("A", "B")
             and FAMILIES[c.kind].form in LOWER_BOUND_FORMS]
    target = next((c for c in (first, second) if c.kind == "A"), None)
    if lower:
        constraint = lower[0]
        family = FAMILIES[constraint.kind]
        word = FEATURE_WORD[family.statistic_id]
        n = target.severity if target else 0
        if family.form == "count_lower_bound":
            count = constraint.severity + 2
        else:
            # rate >= q with n target words present: k / (k + n) >= q/100.
            count = max(constraint.severity, 8)
            if n:
                count = max(count, int(4 * n) + count)
        words = [word] * count + [TARGET] * n
        return " ".join(words)
    exact = [c for c in (first, second)
             if c.kind not in ("A", "B")
             and FAMILIES[c.kind].form is FORM_EXACT]
    n = target.severity if target else 0
    base = feature_free(max(40, _words_needed(first), _words_needed(second)))
    if exact:
        # **Every** exact constraint of the pair, not only the first. v5's
        # core pool is exact counts, so a realisable pair can carry two of
        # them --- one marker family and one near-form family, from different
        # feature groups --- and satisfying only the first would report a
        # construction defect as a non-entailment finding.
        sentence_exact = [c for c in exact
                          if FAMILIES[c.kind].statistic_id == "sentence"]
        others = [c for c in exact
                  if FAMILIES[c.kind].statistic_id != "sentence"]
        tokens: list[str] = []
        for constraint in others:
            word = FEATURE_WORD[FAMILIES[constraint.kind].statistic_id]
            tokens += [word] * constraint.severity
        tokens += [TARGET] * n
        if sentence_exact:
            # An exact SENTENCE count is q terminated sentences and no tail:
            # §9.2 counts maximal terminator runs plus an unterminated tail,
            # so q copies of "." followed by filler is q + 1 sentences.
            q = sentence_exact[0].severity
            per = max(3, 40 // max(q, 1))
            chunks = []
            for index in range(q):
                chunk = feature_free(per)
                if index == 0 and tokens:
                    chunk = " ".join(tokens + [chunk])
                chunks.append(chunk + ".")
            return " ".join(chunks)
        return " ".join(tokens + [base])
    return " ".join([TARGET] * n + [base])


def sentences_text(q: int, *, inner: str = "", per: int = 8) -> str:
    """Exactly ``q`` sentences of filler, with ``inner`` inside the first.

    §9.2 counts maximal runs of ``.``, ``!`` and ``?`` plus an unterminated
    tail, so a sentence count is **not compositional under concatenation**:
    appending filler to a terminated text adds a sentence, and prefixing a
    terminated text with more sentences adds those too. Every construction
    that has to hit an exact sentence count therefore goes through here, and
    ``inner`` has its terminators stripped so that whatever it carries cannot
    move the count it is being embedded in.
    """
    body = "".join(ch for ch in inner if ch not in SENTENCE_TERMINATORS)
    chunks = []
    for index in range(max(q, 0)):
        chunk = feature_free(per)
        if index == 0 and body.strip():
            chunk = f"{body.strip()} {chunk}"
        chunks.append(chunk + ".")
    return " ".join(chunks)


def _break(constraint: Constraint, *, alongside: Constraint,
           min_words: int = 0) -> str:
    """A text that FAILS ``constraint`` while leaving ``alongside`` free.

    ``alongside`` is passed so the constructor can pick a breaking word that
    does not move the other constraint's statistic; where no such word exists
    the pair is not realisable and ``assert_pair_realisable`` has already said
    so.

    ``min_words`` is how long the text has to be for ``alongside`` to hold on
    it, and it exists for one family. Every violation here is built to survive
    the length: a count is not diluted by adding filler, and a rate is broken
    by an all-feature text whose rate is a hundred at any length. Padding a
    rate violation with filler instead would dilute it back under its own
    threshold, which is the failure this parameter replaced.
    """
    kind, q = constraint.kind, constraint.severity
    if kind == "A":
        return feature_free(max(40, min_words))  # zero occurrences, and n >= 1
    if kind == "B":
        return " ".join([LONG_WORD, feature_free(max(30, min_words))])
    family = FAMILIES[kind]
    word = FEATURE_WORD[family.statistic_id]
    if family.form is FORM_EXACT:
        if family.statistic_id == "sentence":
            # One more sentence than the target, built as sentences rather
            # than as q + 1 loose terminators followed by a tail.
            return sentences_text(q + 1)
        # One more than the target: never equal to q, for every registered q.
        return " ".join([word] * (q + 1) + [feature_free(max(30, min_words))])
    if family.form == FORM_COUNT:
        return " ".join([word] * (q + 1) + [feature_free(max(30, min_words))])
    if family.form == FORM_RATE:
        # rate > q needs the feature share above q percent. For a word-shaped
        # numerator an all-feature text reads 100 and every registered q is
        # below it. The comma numerator is NOT word-shaped -- its feature is a
        # character, and a text of bare commas has no words at all, so its
        # rate is undefined and the constraint fails for the wrong reason.
        # Commas are therefore attached to filler words, which raises commas
        # per hundred words far above every registered q while leaving the
        # text a text.
        if family.statistic_id in _CHARACTER_NUMERATORS:
            n = max(4, min_words)
            return " ".join(f"{FILLER[i % len(FILLER)]}{word * 5}"
                            for i in range(n))
        return " ".join([word] * max(12, min_words))
    # A lower bound is broken by producing none of the feature at all.
    return feature_free(max(40, min_words))


def separating_witnesses(first: Constraint, second: Constraint
                         ) -> tuple[str, str]:
    """(satisfies first and fails second, satisfies second and fails first)."""
    assert_pair_realisable(first, second)

    def _one(keep: Constraint, drop: Constraint) -> str:
        base = _break(drop, alongside=keep, min_words=_words_needed(keep))
        if keep.kind == "A":
            return " ".join([TARGET] * keep.severity + [base])
        family = FAMILIES.get(keep.kind)
        if family is not None and family.form is FORM_EXACT:
            if family.statistic_id == "sentence":
                # Exactly q sentences, with the breaking material embedded in
                # the first so it cannot add one.
                return sentences_text(keep.severity, inner=base)
            word = FEATURE_WORD[family.statistic_id]
            return " ".join([word] * keep.severity + [base])
        if family is not None and family.form in LOWER_BOUND_FORMS:
            word = FEATURE_WORD[family.statistic_id]
            count = (keep.severity + 2 if family.form == "count_lower_bound"
                     else max(keep.severity, 8) * 4)
            return " ".join([word] * count + [base])
        return base

    return _one(first, second), _one(second, first)


def run_witness_suite(pairs: Iterable[tuple[Constraint, Constraint]] | None
                      = None) -> dict[str, Any]:
    """Discharge §7.5 over every realisable pair, and report the failures."""
    pairs = list(pairs) if pairs is not None else realisable_pairs()
    joint_failures: list[str] = []
    entail_failures: list[str] = []
    for first, second in pairs:
        label = f"{first.label}+{second.label}"
        text = joint_witness(first, second)
        if not (passes(first, _statistic(first.kind, text), text)
                and passes(second, _statistic(second.kind, text), text)):
            joint_failures.append(label)
        one, two = separating_witnesses(first, second)
        ok_one = (passes(first, _statistic(first.kind, one), one)
                  and not passes(second, _statistic(second.kind, one), one))
        ok_two = (passes(second, _statistic(second.kind, two), two)
                  and not passes(first, _statistic(first.kind, two), two))
        if not (ok_one and ok_two):
            entail_failures.append(label)
    return {"pairs": len(pairs),
            "joint_satisfiability_failures": joint_failures,
            "non_entailment_failures": entail_failures,
            "passed": not (joint_failures or entail_failures)}


def _families_of(statistic_id: str) -> tuple[str, ...]:
    return tuple(k for k, f in FAMILIES.items()
                 if f.statistic_id == statistic_id)


def _can_share_a_cell(statistic_a: str, statistic_b: str) -> bool:
    """Could a registered cell ever state a family of each?

    ``assert_pair_realisable`` is the rule; this asks it over the families
    each numerator belongs to. It is the scope of the specificity check
    below.
    """
    for kind_a in _families_of(statistic_a):
        for kind_b in _families_of(statistic_b):
            try:
                assert_pair_realisable(Constraint(kind_a,
                                                  declared_range(kind_a)[0],
                                                  reserve=True),
                                       Constraint(kind_b,
                                                  declared_range(kind_b)[0],
                                                  reserve=True))
            except InstrumentError:
                continue
            return True
    return False


def assert_feature_words_are_specific() -> dict[str, list[str]]:
    """Each breaking word carries as few features as it can **that matter**.

    A breaking word carrying a second feature does not merely make an
    inelegant witness: it silently violates the *other* constraint of the pair
    and the suite reports a non-entailment failure --- a construction defect
    dressed as a scientific finding, which §7.7 names as the worst outcome
    this module can produce.

    **v5 narrows the check to collisions that can actually happen, and the
    narrowing is a finding rather than a convenience.** v4r4's feature words
    were all *chosen*, so orthogonality was achievable and the check was
    unconditional. v5's eight marker words are **registered by §7.6** and
    their letters are what English makes them: `whereas` contains an `a` and
    ends in `s`, `indeed` has a doubled letter and is vowel-initial, `overall`
    has both, `though` is t-initial, `namely` contains an `a` and ends in `y`.
    None of that is a design defect and none of it can be designed away
    without changing the marker vocabulary.

    What matters is whether a collision can ever occur **in a cell**. §7.4
    admits Tier 1 and Tier 2 to the core reference slot and Tier 3 to the
    broad-class slot alone, and §13.10 places a broad-class companion beside B
    only --- so a marker family never shares a cell with a family over
    `letter_a`, `s_final`, `doubled_letter`, `vowel_initial`, `t_initial` or
    `y_final`, all of which are Tier 3. The check therefore asks
    ``assert_pair_realisable`` rather than assuming, and every collateral
    feature it tolerates is recorded with the reason it cannot bite.
    """
    collateral: dict[str, list[str]] = {}
    tolerated: dict[str, list[str]] = {}
    for statistic_id, word in FEATURE_WORD.items():
        text = " ".join([word] * 3)
        others = [other for other, fn in STATISTICS.items()
                  if other != statistic_id
                  and fn(text) > (1 if other == "sentence" else 0)]
        # capital_char and capital_word share one word by construction.
        allowed = {"capital_char": {"capital_word"},
                   "capital_word": {"capital_char"},
                   "sentence": set(), "semicolon": set(), "comma": set()}
        unexpected = []
        for other in sorted(set(others) - allowed.get(statistic_id, set())):
            if _can_share_a_cell(statistic_id, other):
                unexpected.append(other)
            else:
                tolerated.setdefault(statistic_id, []).append(other)
        if unexpected:
            collateral[statistic_id] = unexpected
    if collateral:
        raise InstrumentError(
            "these breaking words carry a feature they were not chosen for "
            "AND their families can share a cell, so a witness built from "
            f"them breaks the wrong constraint: {collateral}")
    return {k: sorted(tolerated.get(k, [])) for k in FEATURE_WORD}
