"""Constraints authored HERE, for the Round 4 generalization experiments.

Everything in this module is new scientific content, which is exactly what the
rest of this package refuses to invent. That refusal is right for the primary
contrast — re-typing a registry wording would silently create a different
experiment — and it is impossible for the questions Round 4 asks, because the
registry contains no per-sentence colon rule, no exact-paragraph-count target and
no N = 3/5/6 sentence targets to harvest.

So these are declared separately, registered onto the harvested state at run
time, and stamped. Three consequences follow and are enforced below:

  * **Production is untouched.** Nothing here writes to `src/dci`. The v19
    registry, its wordings, its verifiers and its hashes are exactly what they
    were. `harvest.provenance()` still describes the harvested definitions; the
    run config additionally records everything this module added.
  * **Nothing here is admitted evidence.** Every id carries the `X_` prefix and
    every spec's origin is `"exploratory"`, which is not one of the roles the
    registry's own screens accept.
  * **Wordings are matched, not merely authored.** The per-sentence mark family
    exists so that "semicolon", "colon", "dash" and "comma" differ in the MARK
    and in nothing else. If each mark had been given its own hand-written
    sentence, the factorial would confound the mark with its phrasing.

The N-variant targets are the one exception that needs no authoring: the
registry's own `exact_sentence_count` family renders them from its certified
templates with a different `n`, so those wordings are the protocol's.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Optional

from dci_exploratory import harvest

STAMP = "EXPLORATORY_AUTHORED_HERE"

# --------------------------------------------------------------- verifiers
# Each reuses the PRODUCTION segmenter, so a per-sentence exploratory rule and
# the target it is meant to interfere with agree about what a sentence is. A
# private segmenter here would make every cross-arm comparison a comparison of
# two segmenters as well as of two instructions.

#: Characters accepted for each named mark. The dash entry is a set because a
#: model that is asked for "a dash" may reasonably produce an em dash, an en
#: dash or a double hyphen, and scoring only U+2014 would measure typography.
MARK_CHARS: dict[str, tuple[str, ...]] = {
    "semicolon": (";",),
    "colon": (":",),
    "dash": ("—", "–", "--"),
    "comma": (",",),
}

#: Whether the mark can stand, in ordinary written English, exactly where a
#: sentence boundary would stand. This is the PREDICTOR the mechanism account
#: proposes, declared before the run rather than read off the results.
MARK_IS_BOUNDARY_CAPABLE: dict[str, bool] = {
    "semicolon": True,     # joins two independent clauses; the canonical case
    "colon": True,         # joins clauses, though it also has a listing use
    "dash": True,          # joins clauses in informal register
    "comma": False,        # joining two independent clauses with one is an error
}


def _marks_in(text: str, mark: str) -> int:
    return sum(text.count(ch) for ch in MARK_CHARS[mark])


def v_mark_per_sentence(text: str, mark: str):
    """At least one of the named mark in every sentence."""
    from dci.verifiers.rules import _per_sentence
    chars = MARK_CHARS[mark]
    return _per_sentence(text, lambda s: any(c in s for c in chars),
                         f"{mark}_ok")


def v_mark_total_min(text: str, mark: str, n: int):
    """At least `n` of the named mark ANYWHERE in the answer.

    Deliberately the same quantity demanded by the per-sentence rule at the
    target sentence count, with the per-sentence scoping removed. It is the
    control that separates "the answer must contain this many marks" from "each
    sentence must contain one".
    """
    from dci.verifiers.rules import VerificationResult, normalize_text
    observed = _marks_in(normalize_text(text), mark)
    binary = int(observed >= n)
    score = min(observed / n, 1.0) if n else 1.0
    status = "full" if binary else ("partial" if observed else "violation")
    return VerificationResult(status, binary, score,
                              {"observed": observed, "target_min": n, "mark": mark})


#: A paragraph break, as the instruction describes it: a line that is blank.
_PARAGRAPH_BREAK = re.compile(r"\n[^\S\n]*\n")


def split_paragraphs(text: Any) -> list[str]:
    """Blocks separated by a BLANK line, with empty blocks dropped.

    Written to mirror `split_sentences`'s contract — normalise, split on the
    declared delimiter, drop anything with no alphanumeric content — so the
    paragraph target is the sentence target's structural twin and a difference
    between them is a difference in the unit, not in the counting convention.
    """
    if text is None:
        return []
    blocks = _PARAGRAPH_BREAK.split(str(text).strip())
    return [b.strip() for b in blocks if any(c.isalnum() for c in b)]


def v_exact_paragraph_count(text: str, n: int):
    from dci.verifiers.rules import VerificationResult, count_status
    observed = len(split_paragraphs(text))
    if observed == 0:
        return VerificationResult("unscorable", 0, 0.0,
                                  {"observed": 0, "target": n})
    status, binary, score = count_status(observed, n)
    return VerificationResult(status, binary, score, {"observed": observed, "target": n})


def v_linebreak_per_paragraph(text: str):
    """Every paragraph carries at least one line break inside it.

    The paragraph-level analogue of the per-sentence mark rules: a single newline
    is a delimiter that can stand where the target's delimiter — a blank line —
    would stand, without being one.
    """
    from dci.verifiers.rules import VerificationResult, fraction_status
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return VerificationResult("unscorable", 0, 0.0, {"n_paragraphs": 0})
    ok = [("\n" in p) for p in paragraphs]
    score = sum(ok) / len(ok)
    return VerificationResult(fraction_status(score), int(all(ok)), score,
                              {"n_paragraphs": len(paragraphs),
                               "linebreak_ok": ok})


# Clause-initial words, as a CLOSED list. Used only to measure whether a
# prohibition was obeyed; never to score an experimental outcome. A mark followed
# by one of these is being used where a sentence boundary could stand, which is
# the structural fact the substitution account is about — the grammatical
# question of whether both sides are independent clauses is not decidable here
# and is not claimed to be.
# Pronouns and connectives only. Determiners were in the first version and had
# to come out: `The parts are a lever; a spring; a base.` is a list, not a clause
# join, and `; a` cannot tell the two apart. With determiners removed the proxy
# can only UNDER-count — `The lever moves; the spring returns.` is a real join it
# will miss — which is the safe direction for a measure whose job is to check
# that a prohibition was obeyed.
CLAUSE_INITIAL = frozenset({
    "this", "these", "those", "it", "they", "he", "she", "we", "you",
    "there", "then", "thus", "therefore", "however", "otherwise", "meanwhile",
    "instead", "consequently", "nevertheless", "afterwards", "subsequently",
})
#: Every mark that could occupy a clause boundary, in one alternation. The first
#: version listed only `[;,]`, which made `splice_count(text, "colon")` and
#: `splice_count(text, "dash")` return 0 for every input — silently, because the
#: character test downstream could then never match. Any conclusion drawn from a
#: colon or dash splice count before this was fixed would have been an artefact
#: of the regex rather than a fact about the text.
_AFTER_MARK = re.compile(r"(--|[;,:—–])\s*([A-Za-z']+)")


def splice_count(text: str, mark: str) -> int:
    """Occurrences of `mark` immediately followed by a clause-initial word.

    A PROXY, and labelled one everywhere it is reported. It is exact about what
    it counts and silent about grammar.
    """
    chars = set(MARK_CHARS[mark])
    return sum(1 for m in _AFTER_MARK.finditer(str(text or ""))
               if m.group(1) in chars and m.group(2).lower() in CLAUSE_INITIAL)


def v_no_splice(text: str, mark: str):
    """No occurrence of `mark` standing where a sentence boundary could stand."""
    from dci.verifiers.rules import VerificationResult, normalize_text
    body = normalize_text(text)
    if not body:
        return VerificationResult("unscorable", 0, 0.0, {"splices": 0})
    splices = splice_count(body, mark)
    binary = int(splices == 0)
    return VerificationResult("full" if binary else "violation", binary,
                              float(binary), {"splices": splices, "mark": mark,
                                              "measure": "closed-list proxy"})


def v_no_exclamation(text: str):
    from dci.verifiers.rules import VerificationResult, normalize_text
    body = normalize_text(text)
    if not body:
        return VerificationResult("unscorable", 0, 0.0, {"exclamations": 0})
    count = body.count("!")
    binary = int(count == 0)
    return VerificationResult("full" if binary else "violation", binary,
                              float(binary), {"exclamations": count})


_NUMERAL = re.compile(r"\d")


def v_numbers_as_words(text: str):
    """No digit characters at all — the 'spell the number out' route.

    Deliberately identical in effect to the registry's own `no_digits`, and
    given a different id and wording because the point of the arm is the
    INSTRUCTION ("write numbers as words"), which names a substitute surface
    form, rather than the prohibition ("use no digits"), which does not.
    """
    from dci.verifiers.rules import VerificationResult, normalize_text
    body = normalize_text(text)
    if not body:
        return VerificationResult("unscorable", 0, 0.0, {"digits": 0})
    digits = len(_NUMERAL.findall(body))
    binary = int(digits == 0)
    return VerificationResult("full" if binary else "violation", binary,
                              float(binary), {"digits": digits})


# ---------------------------------------------------------------- wordings
# Six wordings per family, in the same slots and the same order as the
# registry's, so a paraphrase index means the same escalation step here as
# there. Slots 6 and 7 repeat slots 0 and 1: this study never reaches them, and
# leaving them short would make `S.INSTRUCTIONS[cid][p]` an index error for a
# wording the registry can supply.
_MARK_TEMPLATES = (
    "Use at least one {mark} in every sentence.",
    "Each sentence must contain {article} {mark}.",
    "Every sentence must include at least one {mark}.",
    "No sentence may be written without {article} {mark}.",
    "Place {article} {mark} in each sentence.",
    "Each sentence must carry one or more {mark_plural}.",
)

_MARK_TOTAL_TEMPLATES = (
    "Use at least {n} {mark_plural} in the whole answer.",
    "The answer must contain at least {n} {mark_plural} in total.",
    "Across the entire answer, there must be {n} or more {mark_plural}.",
    "Include no fewer than {n} {mark_plural} overall.",
    "The total count of {mark_plural} in the answer must be at least {n}.",
    "At least {n} {mark_plural} must appear somewhere in the answer.",
)

_PARAGRAPH_TEMPLATES = (
    "Write exactly {n} paragraphs, separated by a blank line.",
    "Your entire answer must consist of exactly {n} paragraphs, separated by "
    "blank lines, no more and no fewer.",
    "Use precisely {n} paragraphs, with a blank line between them.",
    "The answer must contain {n} paragraphs exactly, each separated from the "
    "next by a blank line.",
    "Produce a response of exactly {n} paragraphs, divided by blank lines.",
    "Let the total number of blank-line-separated paragraphs be exactly {n}.",
)

_LINEBREAK_TEMPLATES = (
    "Include at least one line break inside every paragraph.",
    "Each paragraph must contain a line break within it.",
    "Every paragraph must include at least one internal line break.",
    "No paragraph may be written without a line break inside it.",
    "Place a line break within each paragraph.",
    "Each paragraph must carry one or more internal line breaks.",
)

_NO_SPLICE_TEMPLATES = (
    "Do not use a {mark} to join two complete sentences.",
    "A {mark} must never stand between two clauses that could each be a sentence.",
    "Never place a {mark} where a full stop could go.",
    "No {mark} may join one complete statement to another.",
    "Avoid using a {mark} to link two independent clauses.",
    "A {mark} must not take the place of a sentence break.",
)

_NO_EXCLAM_TEMPLATES = (
    "Do not use any exclamation marks.",
    "The answer must contain no exclamation marks at all.",
    "Never place an exclamation mark anywhere in the answer.",
    "No exclamation mark may appear in the response.",
    "Avoid exclamation marks entirely.",
    "The count of exclamation marks must be zero.",
)

_WORDNUM_TEMPLATES = (
    "Write out every number as a word rather than as a numeral.",
    "Any number in the answer must be spelled out in letters, not written in digits.",
    "Express all numbers in words instead of figures.",
    "No number may appear as a numeral; write each one as a word.",
    "Spell every number out rather than using digits.",
    "Each number must be given in word form, never in numeral form.",
)

_ARTICLE = {"semicolon": "a", "colon": "a", "dash": "a", "comma": "a"}
_PLURAL = {"semicolon": "semicolons", "colon": "colons", "dash": "dashes",
           "comma": "commas"}


def _render(templates: tuple[str, ...], **view: Any) -> tuple[str, ...]:
    rendered = tuple(t.format(**view) for t in templates)
    return rendered + rendered[:2]          # pad to the registry's eight slots


# ------------------------------------------------------------- registration
def _mark_spec(constraint_id: str, mark: str, spec, P):
    return spec(constraint_id, "exploratory", f"A {mark} in every sentence",
                "format", "local_check", "sentence",
                "sentence_segmentation+punctuation", "candidate",
                f"x_{mark}_per_sentence", P(mark=mark), "exploratory",
                "authored for the Round 4 mark factorial")


#: id -> (spec factory, verifier factory, wordings). Declared as data so the
#: registration loop below cannot register a verifier for one id and a wording
#: for another.
def _catalogue(spec, P) -> dict[str, tuple[Any, Callable[[str], Any], tuple[str, ...]]]:
    out: dict[str, tuple[Any, Callable[[str], Any], tuple[str, ...]]] = {}

    # --- the per-sentence mark family: mark varies, wording does not ---------
    for mark in MARK_CHARS:
        cid = f"X_{mark.upper()}_EACH"
        out[cid] = (
            _mark_spec(cid, mark, spec, P),
            (lambda m: (lambda t: v_mark_per_sentence(t, m)))(mark),
            _render(_MARK_TEMPLATES, mark=mark, article=_ARTICLE[mark],
                    mark_plural=_PLURAL[mark]),
        )

    # --- whole-answer mark floors: quantity crossed with mark ----------------
    # `X_SEMI_TOTAL4` began as the SCOPING control: four is the target sentence
    # count, so at one mark per sentence it demands the same number of semicolons
    # as the per-sentence rule, with the per-sentence framing removed.
    #
    # E4 then found it collapses HARDER than the per-sentence rule (1.000 against
    # 0.68-0.75), which rules scoping out as the operative variable and makes
    # quantity the candidate. The rest of this family exists to cross the two
    # things that could then be doing the work — how many marks are demanded, and
    # which mark — at one scope and under one wording.
    for mark, n in (("semicolon", 1), ("semicolon", 2), ("semicolon", 3),
                    ("semicolon", 4), ("semicolon", 5), ("semicolon", 6),
                    ("colon", 4), ("dash", 4), ("comma", 4)):
        cid = f"X_{mark.upper()}_TOTAL{n}"
        out[cid] = (
            spec(cid, "exploratory", f"At least {n} {_PLURAL[mark]} in the answer",
                 "format", "global_count", "whole_text", "character_stream",
                 "candidate", f"x_{mark}_total{n}", P(mark=mark, n=n), "exploratory",
                 "authored for the whole-answer quantity-by-mark crossing"),
            (lambda m, k: (lambda t: v_mark_total_min(t, m, k)))(mark, n),
            _render(_MARK_TOTAL_TEMPLATES, n=n, mark_plural=_PLURAL[mark]),
        )

    # The id E4 was run under, before the family was widened. Kept, with
    # identical content, so that run's command still reproduces exactly.
    out["X_SEMI_TOTAL4"] = out["X_SEMICOLON_TOTAL4"]

    # --- N-variant targets: the registry's own family and templates ----------
    for n in (2, 3, 5, 6):
        cid = f"X_A{n}"
        out[cid] = (
            spec(cid, "exploratory", f"Exact sentence count ({n})", "structural",
                 "global_count", "sentence", "sentence_segmentation", "target",
                 "exact_sentence_count", P(n=n), "exploratory",
                 "the registry's own family and certified templates at a different n"),
            (lambda k: (lambda t: _exact_sentence_count(t, k)))(n),
            None,                                  # rendered from the registry
        )

    # --- the structural twin: paragraphs instead of sentences ----------------
    out["X_PARA4"] = (
        spec("X_PARA4", "exploratory", "Exact paragraph count (4)", "structural",
             "global_count", "whole_text", "paragraph_segmentation", "target",
             "x_exact_paragraph_count", P(n=4), "exploratory",
             "authored as the structural twin of the sentence-count target"),
        lambda t: v_exact_paragraph_count(t, 4),
        _render(_PARAGRAPH_TEMPLATES, n=4),
    )
    out["X_LINEBREAK_EACH"] = (
        spec("X_LINEBREAK_EACH", "exploratory", "A line break inside every paragraph",
             "format", "local_check", "whole_text", "paragraph_segmentation",
             "candidate", "x_linebreak_per_paragraph", (), "exploratory",
             "authored as the paragraph-level substitutable delimiter"),
        lambda t: v_linebreak_per_paragraph(t),
        _render(_LINEBREAK_TEMPLATES),
    )

    # --- route-closing prohibitions, for the double-dissociation intervention -
    # Three prohibitions of the same grammatical form and comparable length, one
    # on each suspected route and one on neither. Each is the others' control, so
    # the design needs no clause to be inert — which E1 showed cannot be
    # arranged for a system-message scaffold.
    for cid, mark, phrase in (("X_NO_SEMI_SPLICE", "semicolon", "semicolon"),
                              ("X_NO_COMMA_SPLICE", "comma", "comma")):
        out[cid] = (
            spec(cid, "exploratory", f"No {phrase} where a sentence could end",
                 "format", "local_check", "whole_text", "character_stream",
                 "unrelated", f"x_no_{mark}_splice", P(mark=mark), "exploratory",
                 "authored as a route-closing prohibition",
                 u_family="format",
                 pathway_audit="Prohibits one punctuation USAGE. Does not read "
                               "the sentence count and never compares one "
                               "sentence with another."),
            (lambda m: (lambda t: v_no_splice(t, m)))(mark),
            _render(_NO_SPLICE_TEMPLATES, mark=phrase),
        )
    out["X_NO_EXCLAM"] = (
        spec("X_NO_EXCLAM", "exploratory", "No exclamation marks", "format",
             "local_check", "whole_text", "character_stream", "unrelated",
             "x_no_exclamation", (), "exploratory",
             "authored as the off-route prohibition", u_family="format",
             pathway_audit="Character absence over the whole answer."),
        lambda t: v_no_exclamation(t),
        _render(_NO_EXCLAM_TEMPLATES),
    )

    # --- a different constraint family altogether ----------------------------
    out["X_WORDNUM"] = (
        spec("X_WORDNUM", "exploratory", "Numbers written as words", "numerical",
             "local_check", "whole_text", "token_stream", "candidate",
             "x_numbers_as_words", (), "exploratory",
             "authored as the numerical-family substitutable surface form"),
        lambda t: v_numbers_as_words(t),
        _render(_WORDNUM_TEMPLATES),
    )
    return out


def _exact_sentence_count(text: str, n: int):
    from dci.verifiers.rules import v_exact_sentence_count
    return v_exact_sentence_count(text, n)


_REGISTERED: Optional[dict[str, Any]] = None


def register() -> dict[str, Any]:
    """Add the exploratory constraints to the harvested state. Idempotent.

    Returns the manifest that every run config records, so a run directory says
    on its face which non-registry definitions were in scope when it was made.
    """
    global _REGISTERED
    if _REGISTERED is not None:
        return _REGISTERED

    S = harvest.load()
    from dci.constraints.spec import P, spec
    from dci.provenance.hashes import sha

    catalogue = _catalogue(spec, P)
    collisions = sorted(set(catalogue) & set(S.CONSTRAINTS))
    if collisions:
        raise ValueError(
            f"exploratory ids collide with registry ids: {collisions}. An "
            "exploratory constraint must never shadow a registry one, because "
            "every downstream table would then silently describe the wrong rule.")

    # `S.verify` closes over the dispatch table that lives on the STAGE module,
    # not on shared state, so an entry added to a copy would never be reached.
    from dci.pipeline.stages import c152_verifiers

    manifest: dict[str, Any] = {"stamp": STAMP, "constraints": {}}
    for cid, (constraint, verifier, wordings) in catalogue.items():
        S.CONSTRAINTS[cid] = constraint
        c152_verifiers.VERIFIERS[cid] = verifier
        if wordings is None:
            # A registry family: render its certified templates at these params.
            from dci.pipeline.stages.c172_paraphrases_and_audit import render_instruction
            wordings = tuple(render_instruction(cid, p) for p in range(8))
        S.INSTRUCTIONS[cid] = wordings
        manifest["constraints"][cid] = {
            "name": constraint.name,
            "rule_family": constraint.rule_family,
            "params": dict(constraint.params),
            "generative_scope": constraint.generative_scope,
            "wordings": list(wordings),
            "wording_origin": ("registry template (certified)"
                               if constraint.rule_family == "exact_sentence_count"
                               else "authored in exploratory/extensions.py"),
        }
    manifest["manifest_sha256"] = sha(manifest["constraints"])

    # Round 4's own smoke test, run at registration rather than in a test file
    # that a run could skip: every new verifier must return a verdict on a
    # trivially conforming and a trivially violating text.
    _self_check(S, catalogue)

    _REGISTERED = manifest
    return manifest


_SELF_CHECK: dict[str, tuple[str, str]] = {
    # id: (a text that must PASS, a text that must FAIL)
    "X_SEMICOLON_EACH": ("Rain falls; rivers rise. Wind blows; leaves turn.",
                         "Rain falls. Rivers rise."),
    "X_COLON_EACH": ("One fact: rain falls. Another: rivers rise.",
                     "Rain falls. Rivers rise."),
    "X_DASH_EACH": ("Rain falls — rivers rise. Wind blows — leaves turn.",
                    "Rain falls. Rivers rise."),
    "X_COMMA_EACH": ("Rain falls, and rivers rise. Wind blows, and leaves turn.",
                     "Rain falls. Rivers rise."),
    "X_SEMI_TOTAL4": ("a; b; c; d; e.", "a; b."),
    "X_SEMICOLON_TOTAL1": ("a; b.", "a b."),
    "X_SEMICOLON_TOTAL2": ("a; b; c.", "a b."),
    "X_SEMICOLON_TOTAL3": ("a; b; c; d.", "a; b."),
    "X_SEMICOLON_TOTAL5": ("a; b; c; d; e; f.", "a; b."),
    "X_SEMICOLON_TOTAL4": ("a; b; c; d; e.", "a; b."),
    "X_SEMICOLON_TOTAL6": ("a; b; c; d; e; f; g.", "a; b."),
    "X_COLON_TOTAL4": ("a: b: c: d: e.", "a: b."),
    "X_DASH_TOTAL4": ("a — b — c — d — e.", "a — b."),
    "X_COMMA_TOTAL4": ("a, b, c, d, e.", "a, b."),
    "X_A3": ("One. Two. Three.", "One. Two."),
    "X_A5": ("One. Two. Three. Four. Five.", "One. Two."),
    "X_A6": ("One. Two. Three. Four. Five. Six.", "One. Two."),
    "X_A2": ("One. Two.", "One. Two. Three."),
    "X_PARA4": ("one\n\ntwo\n\nthree\n\nfour", "one\n\ntwo"),
    "X_LINEBREAK_EACH": ("one\nline\n\ntwo\nlines", "one\n\ntwo"),
    "X_WORDNUM": ("Three rivers rise.", "3 rivers rise."),
    "X_NO_SEMI_SPLICE": ("The parts are a lever; a spring; a base.",
                         "Rain falls; it soaks the ground."),
    "X_NO_COMMA_SPLICE": ("Rain falls on the roof and soaks the ground.",
                          "Rain falls, it soaks the ground."),
    "X_NO_EXCLAM": ("Rain falls.", "Rain falls!"),
}


def _self_check(S, catalogue) -> None:
    missing = sorted(set(catalogue) - set(_SELF_CHECK))
    if missing:
        raise AssertionError(
            f"exploratory constraints with no self-check: {missing}. A verifier "
            "that has never been shown to separate a passing from a failing text "
            "cannot be allowed to decide an outcome.")
    for cid, (good, bad) in _SELF_CHECK.items():
        if cid not in catalogue:
            continue
        passing = S.verify(good, cid)
        failing = S.verify(bad, cid)
        if passing.binary_pass != 1:
            raise AssertionError(
                f"{cid}: the declared conforming text does not pass "
                f"({passing.status}, {passing.detail})")
        if failing.binary_pass != 0:
            raise AssertionError(
                f"{cid}: the declared violating text does not fail "
                f"({failing.status}, {failing.detail})")


# ------------------------------------------------ a screen the registry lacks
# `dci.constraints.satisfiability` declares the semicolon case by hand:
# `_exact_char_total_vs_per_sentence` fires only when the whole-answer rule's
# `char` parameter is exactly `";"`, and `_no_char_vs_per_sentence` only when it
# is exactly `","`. Both were written for the two registry pairs that motivated
# them, and neither generalises.
#
# Verified against the shipped screen on 2026-08-11: it returns "ok" for
# `U_FMT_COLON1` x `X_COLON_EACH` (one colon in the answer against a colon in
# every sentence — impossible above one sentence), for `U_FMT_NOCOMMA` x
# `X_COMMA_EACH` (no commas against a comma in every sentence — impossible), and
# for `U_FMT_SEMI2` x `X_SEMICOLON_EACH`, which is the very relation it was
# written to catch, merely under a rule-family name it does not recognise.
#
# So the exploratory designs do not rely on it. This function states the
# arithmetic in the general form: whatever the mark, a whole-answer budget of `b`
# occurrences cannot coexist with a per-sentence demand of one occurrence when
# the target fixes more than `b` sentences.
_MARK_BUDGETS: dict[str, tuple[str, Optional[int]]] = {
    # constraint id -> (mark, whole-answer upper bound; None means "at least")
    "U_FMT_SEMI2": ("semicolon", 2),
    "U_FMT_COLON1": ("colon", 1),
    "U_FMT_NOCOMMA": ("comma", 0),
    **{f"X_{m.upper()}_TOTAL{k}": (m, None)
       for m in ("semicolon", "colon", "dash", "comma")
       for k in (1, 2, 3, 4, 5, 6)},
}
_PER_SENTENCE_MARKS: dict[str, tuple[str, int]] = {
    # constraint id -> (mark, occurrences demanded in EVERY sentence)
    "S_SEMICOLON": ("semicolon", 1),
    "S_COMMA": ("comma", 1),
    "S_TWOCOMMA": ("comma", 2),
    **{f"X_{m.upper()}_EACH": (m, 1) for m in MARK_CHARS},
}


def punctuation_conflicts(constraint_ids: list[str],
                          n_sentences: Optional[int]) -> list[dict[str, Any]]:
    """Whole-answer punctuation budgets against per-sentence punctuation demands.

    `n_sentences` is the count the target fixes, or None when the target does not
    fix one — in which case the only detectable conflict is a flat prohibition.
    """
    found: list[dict[str, Any]] = []
    for budget_id, (mark, bound) in _MARK_BUDGETS.items():
        if budget_id not in constraint_ids or bound is None:
            continue
        for demand_id, (demand_mark, per) in _PER_SENTENCE_MARKS.items():
            if demand_id not in constraint_ids or demand_mark != mark:
                continue
            if bound == 0:
                found.append({"a": budget_id, "b": demand_id, "kind": "hard",
                              "why": f"{budget_id} forbids the {mark} entirely "
                                     f"while {demand_id} requires {per} in every "
                                     "sentence"})
            elif n_sentences is not None and bound < per * n_sentences:
                found.append({"a": budget_id, "b": demand_id, "kind": "hard",
                              "why": f"{budget_id} allows {bound} {mark}(s) in the "
                                     f"whole answer while {demand_id} requires "
                                     f"{per} in each of {n_sentences} sentences, "
                                     f"i.e. {per * n_sentences}"})
    return found


def mark_of(constraint_id: str) -> Optional[str]:
    """The punctuation mark an arm demands, or None if it demands none."""
    S = harvest.load()
    spec = S.CONSTRAINTS.get(constraint_id)
    if spec is None:
        return None
    params = dict(spec.params)
    if "mark" in params:
        return str(params["mark"])
    return {"S_SEMICOLON": "semicolon", "S_COMMA": "comma",
            "S_TWOCOMMA": "comma", "U_FMT_SEMI2": "semicolon",
            "U_FMT_COLON1": "colon"}.get(constraint_id)
