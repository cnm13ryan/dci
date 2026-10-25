"""The Batch 1 master instruction library: taxonomy, families, the 51
candidate reference variants, the A and B candidates, and their renderings
in the two wording frames.

**What is prescribed and what is proposed.** The 22 exact-word-count
variants, A's counts {2, 4, 6} and B's limits {8, ..., 13} are the research
design's own grid (``STATUS_PRESCRIBED``). The other 29 variants, their
parameters, the object-type assignments and both wording frames are this
implementation's proposal (``STATUS_PROPOSED``) and are listed as decisions
D01, D02 and D13 in ``config.py``; none is approved until the researcher
records it.

**One library for every model.** The same constraints, parameters and
renderings are used on every model and frame. A constraint never consults a
model, a frame or a B setting; which constraints are usable under a given B
limit is ``compatibility.py``'s business.

**Frames.** ``F0`` is the imperative grammar ("Use ...", "Write ...",
"Do not ..."), ``F1`` the requirement grammar ("Your answer must ...").
A's two strings are v8.1's wording frames 0 and 1 for A
(``dci1v8dev/wording_v8.py``); B's are the historical B wordings 1 and 0
(``dci1v4/protocol/wordings.py``), paired by grammar. v8.1 paired A and B by
index instead, so neither Batch 1 frame is a v8.1 frame (D02).
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping

from dci.batch1 import verifiers as V
from dci.provenance.hashes import sha

__all__ = [
    "OPERATIONS", "OBJECT_TYPES", "FRAMES", "FRAME_GRAMMAR", "Family",
    "FAMILIES", "Constraint", "LibraryError", "A_COUNTS", "B_LIMITS",
    "FOCAL_WORD", "ROLE_A", "ROLE_B", "ROLE_REFERENCE", "STATUS_PRESCRIBED",
    "STATUS_PROPOSED", "a_candidates", "b_candidates", "reference_library",
    "all_constraints", "constraint_by_id", "validate_library",
    "library_manifest", "library_hash", "PLANNED_FAMILY_COUNTS",
    "WORD_COUNT_GRID", "LIBRARY_VERSIONS", "library_version",
    "set_library_version", "using_library_version", "A_COUNTS_V2",
    "V2_WORDS", "V2_COUNTS",
]


class LibraryError(ValueError):
    """A specification that cannot be admitted to the library."""


OPERATIONS = ("exact_count", "required_inclusion", "prohibition",
              "numerical_bound", "uniqueness", "ordering",
              "relational_dependency", "positional")

OBJECT_TYPES = ("word", "punctuation", "sentence", "paragraph", "letter",
                "word_sequence", "sentence_pair", "numeral", "answer_boundary")

#: Library versions (revision 2026-10, R12b). ``v1`` is the library of the
#: pilot of 2026-10-25 (51 references; unquoted target words) and stays the
#: default, so that pilot's data re-derive exactly; ``v2`` is the expanded
#: library of ``docs/batch1/revision/`` (R1) with quoted target words (R2).
#: The active version is process-wide: ``config.config_of`` sets it from the
#: Freeze 1 a run executes, and the CLI from ``--protocol``.
LIBRARY_VERSIONS = ("v1", "v2")
_ACTIVE = ["v1"]


def library_version() -> str:
    return _ACTIVE[0]


def set_library_version(version: str) -> None:
    if version not in LIBRARY_VERSIONS:
        raise ValueError(f"library version {version!r} is not one of "
                         f"{LIBRARY_VERSIONS}")
    _ACTIVE[0] = version


@contextmanager
def using_library_version(version: str) -> Iterator[None]:
    before = library_version()
    set_library_version(version)
    try:
        yield
    finally:
        set_library_version(before)

FRAMES = ("F0", "F1")
FRAME_GRAMMAR = {"F0": "imperative", "F1": "requirement"}

ROLE_A, ROLE_B, ROLE_REFERENCE = "A", "B", "reference"
STATUS_PRESCRIBED = "prescribed_by_design"
STATUS_PROPOSED = "proposed_unapproved"

FOCAL_WORD = "however"
A_COUNTS = (2, 4, 6)
#: v2: A is fixed at 6 (R3); 4 and 5 are screened as diagnostics only.
A_COUNTS_V2 = (4, 5, 6)
#: v2 exact-word-count ladders (R1): connectives of at most 8 letters, so
#: no ladder is incompatible with B 8 or B 10 by proof, at counts 2-6.
V2_WORDS = ("indeed", "instead", "perhaps", "although", "moreover", "thus",
            "hence", "besides", "anyway", "likewise", "overall", "notably",
            "namely")
V2_COUNTS = (2, 3, 4, 5, 6)
B_LIMITS = (8, 9, 10, 11, 12, 13)

#: The design's fixed exact-word-count grid (22 variants).
WORD_COUNT_GRID: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("indeed", (2, 4, 6)), ("instead", (2, 4, 6)), ("perhaps", (2, 4, 6)),
    ("although", (2, 4, 6)), ("moreover", (2, 4, 6)),
    ("therefore", (2, 4, 6)), ("nonetheless", (2, 4)),
    ("consequently", (2, 4)),
)

#: The design's family table: (operation, family label) -> variant count.
PLANNED_FAMILY_COUNTS = {
    ("exact_count", "exact word count"): 22,
    ("exact_count", "exact punctuation, sentence or paragraph count"): 8,
    ("required_inclusion", "include specified words"): 4,
    ("prohibition", "avoid specified words or letters"): 4,
    ("numerical_bound", "words per sentence"): 3,
    ("uniqueness", "avoid repeated words or word sequences"): 3,
    ("ordering", "sentence length or first-word order"): 4,
    ("relational_dependency", "adjacent-sentence boundary relation"): 3,
}


@dataclass(frozen=True)
class Family:
    """One instruction family: a verifier and a rendering grammar."""
    family_id: str
    operation: str
    object_type: str
    design_row: str                  # the PLANNED_FAMILY_COUNTS label
    verifier_id: str
    vacuity: str                     # verifiers.VACUITY_RULES
    templates: Mapping[str, Mapping[str, str]]   # variant form -> frame -> text
    semantic: str                    # the rule, with {placeholders}
    applicability: str

    def __post_init__(self):
        if self.operation not in OPERATIONS:
            raise LibraryError(f"{self.family_id}: operation {self.operation!r}")
        if self.object_type not in OBJECT_TYPES:
            raise LibraryError(f"{self.family_id}: object {self.object_type!r}")
        if self.verifier_id not in V.VERIFIERS:
            raise LibraryError(f"{self.family_id}: no verifier "
                               f"{self.verifier_id!r}")
        if self.vacuity not in V.VACUITY_RULES:
            raise LibraryError(f"{self.family_id}: vacuity {self.vacuity!r}")
        for form, frames in self.templates.items():
            if set(frames) != set(FRAMES):
                raise LibraryError(f"{self.family_id}/{form}: needs exactly "
                                   f"the frames {FRAMES}")

    def state(self) -> dict[str, Any]:
        return {"family_id": self.family_id, "operation": self.operation,
                "object_type": self.object_type, "design_row": self.design_row,
                "verifier_id": self.verifier_id, "vacuity": self.vacuity,
                "templates": {k: dict(v) for k, v in self.templates.items()},
                "semantic": self.semantic,
                "applicability": self.applicability}


def _fam(family_id, operation, object_type, design_row, verifier_id, vacuity,
         templates, semantic, applicability="any natural-language answer"):
    return Family(family_id, operation, object_type, design_row, verifier_id,
                  vacuity, templates, semantic, applicability)


_EW = "exact word count"
_EC = "exact punctuation, sentence or paragraph count"

FAMILIES: dict[str, Family] = {f.family_id: f for f in (
    _fam("exact_word_count", "exact_count", "word", _EW,
         "b1.exact_word_count", "forced_production",
         {"one": {"F0": "Use the word {word} exactly {n} time{s}.",
                  "F1": "Your answer must contain the word {word} exactly "
                        "{n} time{s}."}},
         "the number of words equal to '{word}' (folded) is exactly {n}"),
    _fam("max_word_length", "numerical_bound", "word", "focal B",
         "b1.max_word_length", "min_words",
         {"one": {"F0": "Use only words of {m} letters or fewer.",
                  "F1": "Every word in the answer must have at most {m} "
                        "letters."}},
         "every word has at most {m} letters"),
    _fam("exact_char_count", "exact_count", "punctuation", _EC,
         "b1.exact_char_count", "forced_production",
         {"one": {"F0": "Use exactly {n} {mark}{s}.",
                  "F1": "Your answer must contain exactly {n} {mark}{s}."}},
         "the raw character {char!r} occurs exactly {n} times"),
    _fam("exact_sentence_count", "exact_count", "sentence", _EC,
         "b1.exact_sentence_count", "forced_production",
         {"one": {"F0": "Write exactly {n} sentence{s}.",
                  "F1": "Your answer must contain exactly {n} sentence{s}."}},
         "the answer has exactly {n} sentences"),
    _fam("exact_paragraph_count", "exact_count", "paragraph", _EC,
         "b1.exact_paragraph_count", "forced_production",
         {"one": {"F0": "Write exactly {n} paragraph{s}, separated by blank "
                        "lines.",
                  "F1": "Your answer must contain exactly {n} paragraph{s}, "
                        "separated by blank lines."}},
         "the answer has exactly {n} blank-line-separated paragraphs"),
    _fam("include_words", "required_inclusion", "word",
         "include specified words", "b1.include_words", "forced_production",
         {"one": {"F0": "Use the word {words} at least once.",
                  "F1": "Your answer must contain the word {words} at least "
                        "once."},
          "many": {"F0": "Use each of the words {words} at least once.",
                   "F1": "Your answer must contain each of the words {words} "
                         "at least once."}},
         "every one of {words} occurs at least once as a whole word"),
    _fam("forbid_words", "prohibition", "word",
         "avoid specified words or letters", "b1.forbid_words", "min_words",
         {"one": {"F0": "Do not use the word {words}.",
                  "F1": "Your answer must not contain the word {words}."},
          "many": {"F0": "Do not use any of the words {words}.",
                   "F1": "Your answer must not contain any of the words "
                         "{words}."}},
         "none of {words} occurs as a whole word"),
    _fam("forbid_letter", "prohibition", "letter",
         "avoid specified words or letters", "b1.forbid_letter", "min_words",
         {"one": {"F0": "Do not use the letter {letter}.",
                  "F1": "Your answer must not contain the letter {letter}."}},
         "no word contains the letter '{letter}' in either case"),
    _fam("sentence_word_bound", "numerical_bound", "sentence",
         "words per sentence", "b1.sentence_word_bound", "min_words",
         {"max": {"F0": "Keep every sentence to at most {k} words.",
                  "F1": "Every sentence in your answer must have at most {k} "
                        "words."},
          "min": {"F0": "Make every sentence at least {k} words long.",
                  "F1": "Every sentence in your answer must have at least {k} "
                        "words."}},
         "every sentence has {bound} {k} words"),
    _fam("no_repeated_words", "uniqueness", "word",
         "avoid repeated words or word sequences", "b1.no_repeated_words",
         "min_words",
         {"one": {"F0": "Do not use any word of {min_letters} or more letters "
                        "more than once.",
                  "F1": "No word of {min_letters} or more letters may appear "
                        "more than once in your answer."}},
         "no folded word of at least {min_letters} letters occurs twice"),
    _fam("no_repeated_bigrams", "uniqueness", "word_sequence",
         "avoid repeated words or word sequences", "b1.no_repeated_bigrams",
         "min_words",
         {"one": {"F0": "Do not use any sequence of two consecutive words "
                        "more than once.",
                  "F1": "No sequence of two consecutive words may appear more "
                        "than once in your answer."}},
         "no pair of consecutive folded words (over the whole answer) occurs "
         "twice"),
    _fam("distinct_openers", "uniqueness", "sentence",
         "avoid repeated words or word sequences", "b1.distinct_openers",
         "forced_production",
         {"one": {"F0": "Write at least {min_sentences} sentences and begin "
                        "each one with a different word.",
                  "F1": "Your answer must contain at least {min_sentences} "
                        "sentences, each beginning with a different word."}},
         "at least {min_sentences} sentences, all first words distinct"),
    _fam("length_order", "ordering", "sentence",
         "sentence length or first-word order", "b1.length_order",
         "forced_production",
         {"increasing": {"F0": "Write at least {min_sentences} sentences, each "
                               "containing more words than the one before it.",
                         "F1": "Your answer must contain at least "
                               "{min_sentences} sentences, each with more "
                               "words than the sentence before it."},
          "decreasing": {"F0": "Write at least {min_sentences} sentences, each "
                               "containing fewer words than the one before "
                               "it.",
                         "F1": "Your answer must contain at least "
                               "{min_sentences} sentences, each with fewer "
                               "words than the sentence before it."}},
         "at least {min_sentences} sentences whose word counts are strictly "
         "{direction}"),
    _fam("alphabetical_openers", "ordering", "sentence",
         "sentence length or first-word order", "b1.alphabetical_openers",
         "forced_production",
         {"one": {"F0": "Write at least {min_sentences} sentences and begin "
                        "them with words in strict alphabetical order.",
                  "F1": "Your answer must contain at least {min_sentences} "
                        "sentences whose first words are in strict "
                        "alphabetical order."}},
         "at least {min_sentences} sentences whose folded first words are "
         "strictly increasing in code-point order"),
    _fam("chain_word", "relational_dependency", "sentence_pair",
         "adjacent-sentence boundary relation", "b1.chain_word",
         "forced_production",
         {"one": {"F0": "Write at least {min_sentences} sentences and begin "
                        "each sentence after the first with the last word of "
                        "the sentence before it.",
                  "F1": "Your answer must contain at least {min_sentences} "
                        "sentences, and each sentence after the first must "
                        "begin with the last word of the previous sentence."}},
         "at least {min_sentences} sentences; each later sentence's first "
         "word equals the previous sentence's last word"),
    _fam("chain_letter", "relational_dependency", "sentence_pair",
         "adjacent-sentence boundary relation", "b1.chain_letter",
         "forced_production",
         {"one": {"F0": "Write at least {min_sentences} sentences and begin "
                        "each sentence after the first with the letter that "
                        "ends the sentence before it.",
                  "F1": "Your answer must contain at least {min_sentences} "
                        "sentences, and each sentence after the first must "
                        "begin with the letter that ends the previous "
                        "sentence."}},
         "at least {min_sentences} sentences; each later sentence's first "
         "letter equals the last letter of the previous sentence's last word"),
    _fam("adjacent_shared_word", "relational_dependency", "sentence_pair",
         "adjacent-sentence boundary relation", "b1.adjacent_shared_word",
         "forced_production",
         {"one": {"F0": "Write at least {min_sentences} sentences and make "
                        "each sentence after the first repeat a word of "
                        "{min_letters} or more letters from the sentence "
                        "before it.",
                  "F1": "Your answer must contain at least {min_sentences} "
                        "sentences, and each sentence after the first must "
                        "share a word of {min_letters} or more letters with "
                        "the previous sentence."}},
         "at least {min_sentences} sentences; each adjacent pair shares a "
         "folded word of at least {min_letters} letters"),
    # library v2 only (revision 2026-10)
    _fam("exact_numeral_count", "exact_count", "numeral", _EC,
         "b1.exact_numeral_count", "forced_production",
         {"one": {"F0": "Use exactly {n} number{s} written as digits.",
                  "F1": "Your answer must contain exactly {n} number{s} "
                        "written as digits."}},
         "exactly {n} numbers written as digits occur"),
    _fam("positional_word", "positional", "answer_boundary", "answer position",
         "b1.positional_word", "forced_production",
         {"start": {"F0": "Begin your answer with the word {word}.",
                    "F1": "The first word of your answer must be {word}."},
          "end": {"F0": "End your answer with the word {word}.",
                  "F1": "The last word of your answer must be {word}."}},
         "the answer's {where} word (folded) is '{word}'"),
    _fam("positional_question", "positional", "answer_boundary",
         "answer position", "b1.positional_question", "forced_production",
         {"one": {"F0": "End your answer with a question.",
                  "F1": "Your answer must end with a question."}},
         "the answer ends with a question mark"),
)}

_MARK_NAMES = {",": "comma", ";": "semicolon", ":": "colon",
               "?": "question mark", "!": "exclamation mark",
               "(": "opening parenthesis"}
#: Irregular plurals for ``{mark}{s}``: the field ``s`` is dropped for them.
_MARK_PLURALS = {"(": "opening parentheses"}


def _q(word: str) -> str:
    """A target word as rendered: quoted in library v2 (R2, D02)."""
    return f'"{word}"' if library_version() == "v2" else word


def _join(words: tuple[str, ...], conj: str) -> str:
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} {conj} {words[1]}"
    return ", ".join(words[:-1]) + f" {conj} " + words[-1]


@dataclass(frozen=True)
class Constraint:
    """One constraint instance: A, B, or a candidate reference variant."""
    cid: str
    role: str
    family_id: str
    params: tuple[tuple[str, Any], ...]
    status: str
    provenance: str

    def __post_init__(self):
        if self.family_id not in FAMILIES:
            raise LibraryError(f"{self.cid}: unknown family {self.family_id!r}")
        if self.role not in (ROLE_A, ROLE_B, ROLE_REFERENCE):
            raise LibraryError(f"{self.cid}: role {self.role!r}")
        if self.status not in (STATUS_PRESCRIBED, STATUS_PROPOSED):
            raise LibraryError(f"{self.cid}: status {self.status!r}")
        if not self.provenance:
            raise LibraryError(f"{self.cid}: provenance is required")
        _validate_params(self)

    @property
    def family(self) -> Family:
        return FAMILIES[self.family_id]

    @property
    def operation(self) -> str:
        return self.family.operation

    @property
    def object_type(self) -> str:
        return self.family.object_type

    @property
    def p(self) -> dict[str, Any]:
        return dict(self.params)

    @property
    def form(self) -> str:
        p = self.p
        if self.family_id in ("include_words", "forbid_words"):
            return "one" if len(p["words"]) == 1 else "many"
        if self.family_id == "sentence_word_bound":
            return p["bound"]
        if self.family_id == "length_order":
            return p["direction"]
        if self.family_id == "positional_word":
            return p["where"]
        return "one"

    def _fields(self) -> dict[str, Any]:
        p = self.p
        fields = dict(p)
        if "n" in p:
            fields["s"] = "" if p["n"] == 1 else "s"
        if "char" in p:
            fields["mark"] = _MARK_NAMES[p["char"]]
            if p["char"] in _MARK_PLURALS and p["n"] != 1:
                fields["mark"], fields["s"] = _MARK_PLURALS[p["char"]], ""
        if "word" in p:
            fields["word"] = _q(p["word"])
        if self.family_id == "include_words":
            fields["words"] = _join(tuple(_q(w) for w in p["words"]), "and")
        if self.family_id == "forbid_words":
            fields["words"] = _join(tuple(_q(w) for w in p["words"]), "or")
        if self.family_id == "sentence_word_bound":
            fields["bound"] = "at most" if p["bound"] == "max" else "at least"
        return fields

    def render(self, frame: str) -> str:
        if frame not in FRAMES:
            raise LibraryError(f"{self.cid}: frame {frame!r} is not one of "
                               f"{FRAMES}")
        return self.family.templates[self.form][frame].format(**self._fields())

    def semantic(self) -> str:
        return self.family.semantic.format(**self._fields())

    def required_words(self) -> tuple[str, ...]:
        """Words any satisfying answer must contain (for compatibility)."""
        p = self.p
        if self.family_id == "exact_word_count" and p["n"] >= 1:
            return (p["word"],)
        if self.family_id == "include_words":
            return tuple(p["words"])
        if self.family_id == "positional_word":
            return (p["word"],)
        return ()

    def verifier_params(self) -> dict[str, Any]:
        return self.p

    def spec(self) -> dict[str, Any]:
        fam = self.family
        return {
            "cid": self.cid, "role": self.role, "family_id": self.family_id,
            "operation": fam.operation, "object_type": fam.object_type,
            "design_row": fam.design_row,
            "params": {k: list(v) if isinstance(v, tuple) else v
                       for k, v in self.params},
            "semantic_spec": self.semantic(),
            "wording": {f: self.render(f) for f in FRAMES},
            "verifier_id": fam.verifier_id,
            "verifier_implementation_hash":
                V.verifier_implementation_hash(fam.verifier_id),
            "applicability": fam.applicability,
            "non_vacuity": {
                "rule": fam.vacuity,
                "min_words": (V.NON_VACUITY_MIN_WORDS
                              if fam.vacuity == "min_words" else None),
                "min_sentences": self.p.get("min_sentences"),
            },
            "empty_response": "state EMPTY: scored, never compliant",
            "truncated_response": "state TRUNCATED: scored, never compliant",
            "status": self.status, "provenance": self.provenance,
        }

    @property
    def spec_hash(self) -> str:
        return sha(["batch1/constraint-spec", self.spec()])


_PARAM_SCHEMA: dict[str, dict[str, type]] = {
    "exact_word_count": {"word": str, "n": int},
    "max_word_length": {"m": int},
    "exact_char_count": {"char": str, "n": int},
    "exact_sentence_count": {"n": int},
    "exact_paragraph_count": {"n": int},
    "include_words": {"words": tuple},
    "forbid_words": {"words": tuple},
    "forbid_letter": {"letter": str},
    "sentence_word_bound": {"bound": str, "k": int},
    "no_repeated_words": {"min_letters": int},
    "no_repeated_bigrams": {},
    "distinct_openers": {"min_sentences": int},
    "length_order": {"direction": str, "min_sentences": int},
    "alphabetical_openers": {"min_sentences": int},
    "chain_word": {"min_sentences": int},
    "chain_letter": {"min_sentences": int},
    "adjacent_shared_word": {"min_sentences": int, "min_letters": int},
    "exact_numeral_count": {"n": int},
    "positional_word": {"where": str, "word": str},
    "positional_question": {},
}


def _validate_params(c: Constraint) -> None:
    schema = _PARAM_SCHEMA[c.family_id]
    p = dict(c.params)
    if [k for k, _ in c.params] != sorted(p):
        raise LibraryError(f"{c.cid}: parameters must be sorted by name")
    if set(p) != set(schema):
        raise LibraryError(f"{c.cid}: parameters {sorted(p)} do not match "
                           f"{sorted(schema)}")
    for name, kind in schema.items():
        value = p[name]
        if not isinstance(value, kind) or isinstance(value, bool):
            raise LibraryError(f"{c.cid}: {name}={value!r} is not {kind.__name__}")
        if kind is int and value < 1:
            raise LibraryError(f"{c.cid}: {name}={value} must be positive")
    for name in ("word", "letter"):
        if name in p and not (p[name].isalpha() and p[name] == p[name].lower()):
            raise LibraryError(f"{c.cid}: {name} {p[name]!r} must be a "
                               "lower-case alphabetic string")
    if "letter" in p and len(p["letter"]) != 1:
        raise LibraryError(f"{c.cid}: letter must be one character")
    if "words" in p:
        ws = p["words"]
        if not ws or len(set(ws)) != len(ws) or not all(
                isinstance(w, str) and w.isalpha() and w == w.lower()
                for w in ws):
            raise LibraryError(f"{c.cid}: words {ws!r} must be distinct "
                               "lower-case alphabetic strings")
    if "char" in p and p["char"] not in _MARK_NAMES:
        raise LibraryError(f"{c.cid}: char {p['char']!r} has no name")
    if c.family_id == "sentence_word_bound" and p["bound"] not in ("max", "min"):
        raise LibraryError(f"{c.cid}: bound {p['bound']!r}")
    if c.family_id == "length_order" and p["direction"] not in (
            "increasing", "decreasing"):
        raise LibraryError(f"{c.cid}: direction {p['direction']!r}")
    if c.family_id == "positional_word" and p["where"] not in ("start", "end"):
        raise LibraryError(f"{c.cid}: where {p['where']!r}")
    if "min_sentences" in p and p["min_sentences"] < 2:
        raise LibraryError(f"{c.cid}: an order or relation over fewer than two "
                           "sentences passes vacuously")


def _c(cid, role, family_id, status, provenance, **params) -> Constraint:
    return Constraint(cid, role, family_id, tuple(sorted(params.items())),
                      status, provenance)


_PROV_GRID = ("research design: fixed exact-word-count grid; predicate form "
              "of DCI-1 v8 marker families (dci1v8dev/wording_v8.py)")
_PROV_PROPOSED = ("proposed for Batch 1 pilot review; family distinctions "
                  "inspired by CSE (arXiv 2608.12426) and Harness-IF (arXiv "
                  "2608.11727), whose constraint lists are not in this "
                  "workspace and are not claimed")


def a_candidates() -> tuple[Constraint, ...]:
    if library_version() == "v2":
        return tuple(_c(f"A.however.{n}", ROLE_A, "exact_word_count",
                        STATUS_PRESCRIBED,
                        "research design: focal A; revision 2026-10 (R3): "
                        "fixed at 6, with 4 and 5 screened as diagnostics",
                        word=FOCAL_WORD, n=n) for n in A_COUNTS_V2)
    return tuple(_c(f"A.however.{n}", ROLE_A, "exact_word_count",
                    STATUS_PRESCRIBED, "research design: focal A, N in {2,4,6}",
                    word=FOCAL_WORD, n=n) for n in A_COUNTS)


def b_candidates() -> tuple[Constraint, ...]:
    return tuple(_c(f"B.max{m}", ROLE_B, "max_word_length", STATUS_PRESCRIBED,
                    "research design: focal B, m in {8..13}; historical B "
                    "statistic (dci1v7/verifiers/statistics.py focal_statistic)",
                    m=m) for m in B_LIMITS)


_PROV_V2 = ("revision 2026-10 (R1): library v2 ladder, chosen from where the "
            "v1 families sat in the pilot of 2026-10-25 "
            "(docs/batch1/revision/REVISION_PROPOSAL.md section 2)")


def reference_library() -> tuple[Constraint, ...]:
    v1 = _reference_library_v1()
    if library_version() == "v1":
        return v1
    return v1 + _reference_additions_v2(v1)


def _reference_additions_v2(v1: tuple[Constraint, ...]
                            ) -> tuple[Constraint, ...]:
    """The 110 references library v2 adds to v1 (candidate_library_v2.json)."""
    R, P, V2 = ROLE_REFERENCE, STATUS_PROPOSED, _PROV_V2
    have = {c.cid for c in v1}
    out: list[Constraint] = []

    def add(cid, family, **params):
        if cid not in have:
            out.append(_c(cid, R, family, P, V2, **params))
    for w in V2_WORDS:
        for n in V2_COUNTS:
            add(f"ew.{w}.{n}", "exact_word_count", word=w, n=n)
    for ch, name, ns in ((";", "semicolon", (1, 2, 3, 4)), (":", "colon", (1, 2, 3)),
                         ("?", "question", (1, 2, 3)), ("!", "exclaim", (1, 2, 3)),
                         ("(", "paren", (1, 2, 3))):
        for n in ns:
            add(f"ec.{name}.{n}", "exact_char_count", char=ch, n=n)
    for n in (3, 4, 5, 6, 7, 8, 9):
        add(f"es.{n}", "exact_sentence_count", n=n)
    for n in (2, 3, 4, 5, 6):
        add(f"ep.{n}", "exact_paragraph_count", n=n)
    for n in (1, 2, 3):
        add(f"en.{n}", "exact_numeral_count", n=n)
    for letter in ("q", "x", "j", "k", "v"):
        add(f"pro.letter.{letter}", "forbid_letter", letter=letter)
    for words in (("also",), ("this",)):
        add("pro.word." + "+".join(words), "forbid_words", words=words)
    for words in (("pebble", "velvet"), ("meadow", "candle", "ribbon"),
                  ("walnut", "saddle", "beacon", "canyon"),
                  ("harbor", "marble", "feather", "thimble", "ember")):
        add("inc." + "+".join(words), "include_words", words=words)
    for bound, k in (("max", 6), ("max", 8), ("max", 10), ("min", 12),
                     ("min", 14), ("min", 16)):
        add(f"nb.{bound}{k}", "sentence_word_bound", bound=bound, k=k)
    for ml in (4, 6, 7):
        add(f"unq.word{ml}", "no_repeated_words", min_letters=ml)
    for ms in (4, 5, 6):
        add(f"unq.opener{ms}", "distinct_openers", min_sentences=ms)
    for direction, short, ms in (("increasing", "inc", 3), ("decreasing", "dec", 3)):
        add(f"ord.{short}{ms}", "length_order", direction=direction, min_sentences=ms)
    for ms in (3, 5):
        add(f"ord.alpha{ms}", "alphabetical_openers", min_sentences=ms)
    add("rel.word2", "chain_word", min_sentences=2)
    add("rel.letter2", "chain_letter", min_sentences=2)
    for ml, ms in ((3, 3), (5, 3)):
        add(f"rel.share{ml}", "adjacent_shared_word", min_letters=ml, min_sentences=ms)
    add("rel.share4.s4", "adjacent_shared_word", min_letters=4, min_sentences=4)
    add("pos.start.today", "positional_word", where="start", word="today")
    add("pos.end.onward", "positional_word", where="end", word="onward")
    add("pos.end.question", "positional_question")
    return tuple(out)


def _reference_library_v1() -> tuple[Constraint, ...]:
    R, P = ROLE_REFERENCE, STATUS_PROPOSED
    out = [_c(f"ew.{w}.{n}", R, "exact_word_count", STATUS_PRESCRIBED,
              _PROV_GRID, word=w, n=n)
           for w, counts in WORD_COUNT_GRID for n in counts]
    out += [
        _c("ec.comma.3", R, "exact_char_count", P, _PROV_PROPOSED, char=",", n=3),
        _c("ec.comma.6", R, "exact_char_count", P, _PROV_PROPOSED, char=",", n=6),
        _c("ec.semicolon.1", R, "exact_char_count", P, _PROV_PROPOSED,
           char=";", n=1),
        _c("ec.semicolon.2", R, "exact_char_count", P, _PROV_PROPOSED,
           char=";", n=2),
        _c("es.4", R, "exact_sentence_count", P, _PROV_PROPOSED, n=4),
        _c("es.7", R, "exact_sentence_count", P, _PROV_PROPOSED, n=7),
        _c("ep.2", R, "exact_paragraph_count", P, _PROV_PROPOSED, n=2),
        _c("ep.3", R, "exact_paragraph_count", P, _PROV_PROPOSED, n=3),
        _c("inc.simple", R, "include_words", P, _PROV_PROPOSED,
           words=("simple",)),
        _c("inc.window+garden", R, "include_words", P, _PROV_PROPOSED,
           words=("window", "garden")),
        _c("inc.silver+morning+quiet", R, "include_words", P, _PROV_PROPOSED,
           words=("silver", "morning", "quiet")),
        _c("inc.remarkable", R, "include_words", P, _PROV_PROPOSED,
           words=("remarkable",)),
        _c("pro.word.the", R, "forbid_words", P, _PROV_PROPOSED,
           words=("the",)),
        _c("pro.word.very+really+just", R, "forbid_words", P, _PROV_PROPOSED,
           words=("very", "really", "just")),
        _c("pro.letter.z", R, "forbid_letter", P, _PROV_PROPOSED, letter="z"),
        _c("pro.letter.b", R, "forbid_letter", P, _PROV_PROPOSED, letter="b"),
        _c("nb.max20", R, "sentence_word_bound", P, _PROV_PROPOSED,
           bound="max", k=20),
        _c("nb.max12", R, "sentence_word_bound", P, _PROV_PROPOSED,
           bound="max", k=12),
        _c("nb.min10", R, "sentence_word_bound", P, _PROV_PROPOSED,
           bound="min", k=10),
        _c("unq.word5", R, "no_repeated_words", P, _PROV_PROPOSED,
           min_letters=5),
        _c("unq.bigram", R, "no_repeated_bigrams", P, _PROV_PROPOSED),
        _c("unq.opener3", R, "distinct_openers", P, _PROV_PROPOSED,
           min_sentences=3),
        _c("ord.inc4", R, "length_order", P, _PROV_PROPOSED,
           direction="increasing", min_sentences=4),
        _c("ord.dec4", R, "length_order", P, _PROV_PROPOSED,
           direction="decreasing", min_sentences=4),
        _c("ord.alpha4", R, "alphabetical_openers", P, _PROV_PROPOSED,
           min_sentences=4),
        _c("ord.inc6", R, "length_order", P, _PROV_PROPOSED,
           direction="increasing", min_sentences=6),
        _c("rel.word3", R, "chain_word", P, _PROV_PROPOSED, min_sentences=3),
        _c("rel.letter3", R, "chain_letter", P, _PROV_PROPOSED,
           min_sentences=3),
        _c("rel.share4", R, "adjacent_shared_word", P, _PROV_PROPOSED,
           min_sentences=3, min_letters=4),
    ]
    return tuple(out)


def all_constraints() -> tuple[Constraint, ...]:
    return a_candidates() + b_candidates() + reference_library()


def constraint_by_id() -> dict[str, Constraint]:
    return {c.cid: c for c in all_constraints()}


def validate_library(refs: Iterable[Constraint] | None = None,
                     *, expect_design_counts: bool = True) -> dict[str, Any]:
    """Every structural rule the library must satisfy, or LibraryError."""
    refs = tuple(reference_library() if refs is None else refs)
    ids = [c.cid for c in refs]
    if len(set(ids)) != len(ids):
        raise LibraryError("duplicate variant ids")
    for c in refs:
        if c.role != ROLE_REFERENCE:
            raise LibraryError(f"{c.cid}: not a reference")
        if FOCAL_WORD in c.required_words() or FOCAL_WORD in c.p.get(
                "words", ()) or c.p.get("word") == FOCAL_WORD:
            raise LibraryError(f"{c.cid}: the focal word may not be a "
                               "reference target")
        renderings = [c.render(f) for f in FRAMES]
        if len(set(renderings)) != len(FRAMES):
            raise LibraryError(f"{c.cid}: the frames render identically")
        for f, text in zip(FRAMES, renderings):
            for token in _parameter_tokens(c):
                if token not in text:
                    raise LibraryError(f"{c.cid}/{f}: wording omits parameter "
                                       f"{token!r}: {text!r}")
    rows: dict[tuple[str, str], int] = {}
    for c in refs:
        key = (c.operation, c.family.design_row)
        rows[key] = rows.get(key, 0) + 1
    if library_version() == "v2":
        kept = {c.cid for c in _reference_library_v1()}
        for c in refs:
            for w in c.required_words():
                if len(w) > 8 and c.cid not in kept:
                    raise LibraryError(f"{c.cid}: v2 targets have at most 8 "
                                       f"letters ({w!r})")
        expect_design_counts = False
    if expect_design_counts:
        if rows != PLANNED_FAMILY_COUNTS:
            raise LibraryError(f"family counts {rows} differ from the design "
                               f"{PLANNED_FAMILY_COUNTS}")
        grid = {(c.p["word"], c.p["n"]) for c in refs
                if c.family_id == "exact_word_count"}
        expected = {(w, n) for w, ns in WORD_COUNT_GRID for n in ns}
        if grid != expected:
            raise LibraryError("the exact-word-count grid differs from the "
                               "design")
    operations = sorted({c.operation for c in refs})
    return {"n_variants": len(refs), "operations": operations,
            "n_operations": len(operations),
            "family_rows": {f"{k[0]} / {k[1]}": v for k, v in rows.items()}}


def _parameter_tokens(c: Constraint) -> list[str]:
    p = c.p
    tokens: list[str] = []
    for name in ("word", "letter"):
        if name in p:
            tokens.append(p[name])
    tokens += list(p.get("words", ()))
    for name in ("n", "k", "m", "min_sentences", "min_letters"):
        if name in p:
            tokens.append(str(p[name]))
    if "char" in p:
        tokens.append(_MARK_NAMES[p["char"]] if p.get("n") == 1 or
                      p["char"] not in _MARK_PLURALS else _MARK_PLURALS[p["char"]])
    return tokens


def library_manifest() -> dict[str, Any]:
    """The machine-readable library (without compatibility; see
    ``compatibility.compatibility_matrix``)."""
    used = {c.family_id for c in all_constraints()}
    refs = reference_library()
    return {
        "schema": "dci.batch1/library/" + library_version(),
        "frames": {f: FRAME_GRAMMAR[f] for f in FRAMES},
        "taxonomy": {"operations": [o for o in OPERATIONS
                                    if any(c.operation == o for c in refs)],
                     "object_types": [t for t in OBJECT_TYPES
                                      if any(c.object_type == t for c in refs)]},
        "families": {k: f.state() for k, f in sorted(FAMILIES.items())
                     if k in used},
        "focal_a": [dict(c.spec(), spec_hash=c.spec_hash)
                    for c in a_candidates()],
        "focal_b": [dict(c.spec(), spec_hash=c.spec_hash)
                    for c in b_candidates()],
        "references": [dict(c.spec(), spec_hash=c.spec_hash)
                       for c in reference_library()],
        "verifier_bundle_hash": V.verifier_bundle_hash(),
    }


def library_hash() -> str:
    return sha(["batch1/library", library_manifest()])
