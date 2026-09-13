"""The complete v8 wording instrument (prospective; nothing stored was generated under it).

Two changes against the v7 instrument, both to text the model is shown:

1. **A and MK1–MK8: the four exact-count frames all name "the word X"**
   (``wording_v8.V8_FRAMES``). The diagnosed mechanism and the audit are in
   ``wording_v8`` and ``reports/dci1v8dev/prescreen/wording_audit.md``: the two
   v7 frames that do not say "the word" are read with the marker modifying
   the instruction (46–53 % marker-absent answers on Gemma, 92–100 % for
   *though* / *namely*). A and the eight marker families differ only in the
   marker, as §7.8 requires; "time"/"times" follows q.
2. **Grammatical number in every other template** (ported from the
   maintenance branch ``maint/v7-docs-marker-unification``, 2026-08-29,
   where it was written against ``dci1v7`` in place; here it is applied to
   the v7 templates at import time and ``dci1v7`` is untouched). Every
   template renders through ``{q}`` and the two number placeholders ``{s}``
   (plural *s* on the noun the numeral governs) and ``{v}`` (singular *s* on
   the verb that noun is the subject of): *1 word contains*, *2 words
   contain*, *0 words*, *1 semicolon*. Until 2026-08-29 every non-marker
   template hard-coded the plural, so q = 1 rendered *exactly 1 semicolons*
   and *at most 1 words*. The rendering is byte-identical to v7's at every
   severity but 1, and ``_number_aware`` refuses a template it cannot make so.

``assert_v8_instrument`` runs every structural guarantee; ``diff_from_v7``
lists every (kind, q, index) whose text differs from v7's and why;
``v8_wording_source_hash`` binds the bytes that decide what a model is asked
(this module, ``wording_v8``, and the v7/v4 template modules by path), the
way v7's ``wording_source_hash`` does for v7.
"""
from __future__ import annotations

import pathlib
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol import wordings as _v4_wordings_module
from dci1v4.protocol.hashing import sha_file, sha_obj
from dci1v7.protocol import wordings as _v7_wordings_module
from dci1v7.protocol.wordings import (
    N_WORDINGS,
    WORDING_LENGTH_TOLERANCE,
    _TEMPLATES as _V7_TEMPLATES,
    focal_wordings,
    wording_word_count,
)
from dci1v7.protocol.wordings import wordings as v7_wordings
from dci1v7.verifiers.constraints import (
    FAMILIES,
    TARGET_GRID,
    TIER1_FAMILY_IDS,
    declared_range,
    focal_severities,
)
from dci1v8dev import wording_v8 as _frames
from dci1v8dev.wording_v8 import V8_FRAMES, assert_v8_wordings

__all__ = [
    "N_WORDINGS",
    "NUMBER_PLACEHOLDERS",
    "V8_FRAMES",
    "V8_TEMPLATES",
    "assert_grammatical_number",
    "assert_v8_instrument",
    "diff_from_v7",
    "grammatical_number_defects",
    "number_fields",
    "v8_wording",
    "v8_wording_source_hash",
    "v8_wordings",
]

#: The two grammatical-number placeholders every template may carry, and the
#: one rule that fills them. ``s`` is a noun's plural ending, ``v`` a verb's
#: singular ending; one is empty exactly when the other is not.
NUMBER_PLACEHOLDERS = ("s", "v")


def number_fields(q: int) -> dict[str, str]:
    """``{s}`` and ``{v}`` for severity ``q``: singular at 1, plural otherwise
    (0 takes the plural in English: *0 words*)."""
    return {"s": "" if q == 1 else "s", "v": "s" if q == 1 else ""}


#: The plural phrases a numeral governs in the v7 templates, mapped to their
#: placeholder forms. Ordered: a longer phrase before the phrase it contains.
_NUMBER_REWRITES: tuple[tuple[str, str], ...] = (
    ("{q} words contain ", "{q} word{s} contain{v} "),
    ("{q} words", "{q} word{s}"),
    ("{q} comma characters", "{q} comma character{s}"),
    ("{q} commas", "{q} comma{s}"),
    ("{q} semicolon characters", "{q} semicolon character{s}"),
    ("{q} semicolons", "{q} semicolon{s}"),
    ("{q} sentences", "{q} sentence{s}"),
    ("{q} capitalised words", "{q} capitalised word{s}"),
    ("{q} upper-case English letters", "{q} upper-case English letter{s}"),
)


def _number_aware(templates: tuple[str, ...]) -> tuple[str, ...]:
    """The checked rewrite: apply the phrase map, then refuse any template
    that does not render v7's text byte-for-byte at every severity but 1."""
    out = []
    for template in templates:
        aware = template
        for plural, placeholder in _NUMBER_REWRITES:
            aware = aware.replace(plural, placeholder)
        for q in (0, 2, 3, 12):
            v7 = template.format(q=q, s="s")
            if aware.format(q=q, **number_fields(q)) != v7:
                raise ProtocolError(
                    f"the number-aware form of {template!r} does not render "
                    f"v7's text at q={q}; the carry-over is refused")
        out.append(aware)
    return tuple(out)


def _marker_templates(kind: str) -> tuple[str, str, str, str]:
    x = _frames._marker(kind)
    return tuple(f.replace("{X}", x) for f in V8_FRAMES)


#: Every registered family's four v8 templates: A and the markers from the
#: v8 frames, every other family from v7's templates made number-aware.
V8_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "A": _marker_templates("A"),
    **{kind: _marker_templates(kind) for kind in TIER1_FAMILY_IDS},
    **{kind: _number_aware(tuple(templates))
       for kind, templates in _V7_TEMPLATES.items()
       if kind in FAMILIES and kind not in TIER1_FAMILY_IDS},
}


def v8_wordings(kind: str, q: int) -> tuple[str, str, str, str]:
    """The four v8 wordings of ``kind`` at severity ``q`` (B: v7's, unchanged)."""
    if kind == "B":
        return focal_wordings(q)
    if kind == "A":
        if q not in TARGET_GRID and q not in range(1, 13):
            raise ProtocolError(f"A: severity {q} outside the grid")
    elif kind not in FAMILIES:
        raise ProtocolError(f"{kind!r} is not a registered family")
    elif q not in declared_range(kind):
        raise ProtocolError(f"severity q={q} outside the declared range of {kind}")
    return tuple(t.format(q=q, **number_fields(q)) for t in V8_TEMPLATES[kind])


def v8_wording(kind: str, index: int, q: int) -> str:
    if not 0 <= index < N_WORDINGS:
        raise ProtocolError(f"wording index {index} outside 0..{N_WORDINGS - 1}")
    return v8_wordings(kind, q)[index]


# ---------------------------------------------------------------- number check

_NUMBER_PHRASE_STOPS = frozenset((
    "may", "must", "will", "can", "of", "per", "percent", "or", "and", "in",
    "to", "with", "at", "is", "are", "containing", "beginning", "ending",
))
_NUMBER_BARE_VERBS = frozenset((
    "contain", "have", "begin", "end", "start", "appear", "use",
))
_NUMBER_SINGULAR_VERBS = frozenset((
    "contains", "has", "begins", "ends", "starts", "appears", "uses",
))


def _number_phrase(tokens: list[str], start: int) -> tuple[list[str], str]:
    phrase: list[str] = []
    for token in tokens[start:]:
        if token in _NUMBER_PHRASE_STOPS or token in _NUMBER_BARE_VERBS \
                or token in _NUMBER_SINGULAR_VERBS:
            return phrase, token
        phrase.append(token)
    return phrase, ""


def grammatical_number_defects(text: str, q: int) -> list[str]:
    """Every place a rendered wording pairs a numeral with the wrong number.

    Mechanical rather than linguistic: after the numeral ``q`` the noun phrase
    up to the next modal, preposition or bare verb must end in ``s`` exactly
    when ``q != 1`` (*1 word*, *0 words*, *2 words*; *percent* is invariant),
    and a bare verb that follows it must carry ``s`` exactly when ``q == 1``
    (*1 word contains*, *2 words contain*). *1 or more words* stops at *or*
    and is plural, as it should be.
    """
    defects: list[str] = []
    tokens = [t.strip(".,:;") for t in text.lower().split()]
    for index, token in enumerate(tokens):
        if token != str(q):
            continue
        phrase, following = _number_phrase(tokens, index + 1)
        if not phrase:
            continue
        head = phrase[-1]
        if head in ("percent",):
            continue
        if q == 1 and head.endswith("s"):
            defects.append(f"'1 {' '.join(phrase)}': plural noun after 1")
        if q != 1 and not head.endswith("s"):
            defects.append(f"'{q} {' '.join(phrase)}': singular noun after {q}")
        if following in _NUMBER_BARE_VERBS and q == 1:
            defects.append(f"'1 {' '.join(phrase)} {following}': bare verb "
                           "after a singular noun")
        if following in _NUMBER_SINGULAR_VERBS and q != 1:
            defects.append(f"'{q} {' '.join(phrase)} {following}': singular "
                           "verb after a plural noun")
    return defects


def _kinds_and_severities() -> list[tuple[str, tuple[int, ...]]]:
    return ([("A", TARGET_GRID), ("B", focal_severities(extended=True))]
            + [(family, declared_range(family)) for family in FAMILIES])


def assert_grammatical_number() -> dict[str, int]:
    """Every v8 wording of every registered constraint, at every severity of
    its declared range, pairs its numeral with the right grammatical number."""
    checked: dict[str, int] = {}
    for kind, severities in _kinds_and_severities():
        for q in severities:
            for index, text in enumerate(v8_wordings(kind, q)):
                defects = grammatical_number_defects(text, q)
                if defects:
                    raise ProtocolError(
                        f"{kind} wording {index} at q={q} renders {text!r}: {defects}")
                checked[kind] = checked.get(kind, 0) + 1
    return checked


def _differs_only_in_number(old: str, new: str) -> bool:
    a = [t.strip(".,:;") for t in old.split()]
    b = [t.strip(".,:;") for t in new.split()]
    if len(a) != len(b):
        return False
    return all(x == y or x == y + "s" or y == x + "s" for x, y in zip(a, b))


def diff_from_v7() -> list[dict[str, Any]]:
    """Every (kind, q, index) whose v8 text differs from v7's, classified:
    ``the_word`` (a marker frame gained the two tokens) or ``number``
    (grammatical number at q = 1). Anything else is refused."""
    out = []
    for kind, severities in _kinds_and_severities():
        for q in severities:
            if kind == "A" and q not in TARGET_GRID:
                continue
            old = v7_wordings(kind, q)
            new = v8_wordings(kind, q)
            for index, (o, n) in enumerate(zip(old, new)):
                if o == n:
                    continue
                if kind == "A" or kind in TIER1_FAMILY_IDS:
                    inserted = [t for t in n.split() if t not in o.split()]
                    if inserted != ["the", "word"]:
                        raise ProtocolError(f"{kind} w{index} q={q}: {o!r} -> {n!r} is not "
                                            "the 'the word' insertion")
                    why = "the_word"
                elif q == 1 and _differs_only_in_number(o, n):
                    why = "number"
                else:
                    raise ProtocolError(f"{kind} w{index} q={q}: {o!r} -> {n!r} differs "
                                        "in more than grammatical number")
                out.append({"kind": kind, "severity": q, "index": index,
                            "v7": o, "v8": n, "why": why})
    return out


def assert_v8_instrument() -> dict[str, Any]:
    """Every structural guarantee of the v8 instrument, executable:
    the frame test (``wording_v8.assert_v8_wordings``), grammatical number
    everywhere, A/MK identity up to the marker, byte-identity with v7 at
    every severity but 1 for every non-marker family, and the §7.7 length
    caliper of every family against A at its own severity."""
    frames = assert_v8_wordings()
    checked = assert_grammatical_number()
    diffs = diff_from_v7()
    for kind in FAMILIES:
        if kind in TIER1_FAMILY_IDS:
            continue
        for q in declared_range(kind):
            if q != 1 and v8_wordings(kind, q) != v7_wordings(kind, q):
                raise ProtocolError(f"{kind} at q={q}: not v7's text")
    for kind in TIER1_FAMILY_IDS:
        for q in declared_range(kind):
            a = v8_wordings("A", min(q, 8))
            for i, f in enumerate(v8_wordings(kind, q)):
                if f.replace(_frames._marker(kind), _frames.TARGET) != \
                        a[i].replace(str(min(q, 8)), str(q)) and q <= 8:
                    raise ProtocolError(f"{kind} w{i} q={q} differs from A beyond the marker")
    caliper = {}
    for kind in FAMILIES:
        worst = 0.0
        for q in declared_range(kind):
            for f, a in zip(v8_wordings(kind, q), v8_wordings("A", min(max(q, 1), 8))):
                n_f, n_a = wording_word_count(f), wording_word_count(a)
                worst = max(worst, abs(n_f - n_a) / max(n_a, 1))
        caliper[kind] = worst
    return {"frames": frames, "renderings_checked": checked,
            "n_differences_from_v7": len(diffs),
            "differences_by_reason": {w: sum(1 for d in diffs if d["why"] == w)
                                      for w in ("the_word", "number")},
            "worst_relative_length_vs_A": caliper,
            "length_tolerance": WORDING_LENGTH_TOLERANCE}


def v8_wording_source_hash() -> str:
    """The v8 wording hash: this module, the frames, and the v7/v4 template
    modules by path (a drift underneath the import is a v8 hash change)."""
    here = pathlib.Path(__file__).resolve()
    files = {
        "dci1v8dev/wordings.py": here,
        "dci1v8dev/wording_v8.py": here.parent / "wording_v8.py",
        "dci1v7/protocol/wordings.py": pathlib.Path(_v7_wordings_module.__file__).resolve(),
        "dci1v4/protocol/wordings.py": pathlib.Path(_v4_wordings_module.__file__).resolve(),
    }
    return sha_obj({k: sha_file(p) for k, p in files.items()})
