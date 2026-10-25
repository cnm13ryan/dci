"""B-specific logical compatibility, with jointly satisfying witnesses.

For a constraint X and a limit m the status is decided in this order:

1. **INCOMPATIBLE**, by proof: X forces the answer to contain a word longer
   than m letters (an exact count of at least one, or a required word), and
   B_m forbids every such word. The proof names the word.
2. **COMPATIBLE**, by witness: a constructed, non-vacuous text that passes
   X's verifier and B_m's verifier and is compliant under both
   (``verifiers.score_constraint``). The witness is stored.
3. **UNRESOLVED** otherwise --- no proof and no witness. Never read as
   compatible; ``assert_resolved`` refuses it for a B setting that enters the
   confirmatory freeze.

Compatibility is never inferred from whether a model managed to satisfy both.

**Task-level compatibility** (``task_level``) asks more of every COMPATIBLE
cell: a witness that also meets the prompt's response-length contract
("Answer in 60 to 120 words", counted with the library's own word rule) and
is non-vacuous. These are built from a second pool, ``LONG_POOL``, by a
deterministic construction per family, and checked with the same verifiers.
A cell with no such witness is ``TASK_UNRESOLVED`` --- a claim for review,
never a proof of incompatibility. Three facts are kept apart: logical
compatibility of X and B, compatibility with the full response contract,
and empirical followability, which no witness says anything about.

Witnesses are built from ``SENTENCE_POOL``: plain sentences whose words all
have at most seven letters (``however`` has seven, the smallest m is eight),
and which avoid every word and letter a library constraint forbids or
requires. The pool's properties are asserted by ``assert_pool`` so a careless
edit fails loudly. A witness is a logical certificate, not an example of
good writing.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from dci.batch1 import text as T
from dci.batch1 import verifiers as V
from dci.batch1.library import (
    B_LIMITS, Constraint, a_candidates, b_candidates, reference_library,
)
from dci.provenance.hashes import sha

__all__ = ["COMPATIBLE", "INCOMPATIBLE", "UNRESOLVED", "SENTENCE_POOL",
           "LONG_POOL", "TASK_COMPATIBLE", "TASK_UNRESOLVED", "TASK_MIN_WORDS",
           "TASK_MAX_WORDS", "assert_pool", "build_witness", "check",
           "compatibility_matrix", "compatible_ids", "assert_resolved",
           "violation_text", "matrix_hash", "task_witness", "task_level"]

COMPATIBLE, INCOMPATIBLE, UNRESOLVED = "COMPATIBLE", "INCOMPATIBLE", "UNRESOLVED"
POOL_MAX_LETTERS = 7

SENTENCE_POOL: tuple[str, ...] = (
    "Calm rivers carry cold water past old mills.",
    "Many people walk to work each day.",
    "Small shops open early near a stone square.",
    "Fresh fruit sells fast in summer.",
    "Our town has four old towers.",
    "Kids play games after school ends.",
    "Rain falls often in spring.",
    "Farmers grow corn on low hills.",
    "Every street has a name and a story.",
    "Local cooks make soup with onions.",
    "Travel guides point out hidden paths.",
    "Night markets glow with warm lights.",
    "Wise elders share tales at dusk.",
    "Young poets read aloud in cafes.",
    "Ferry trips cross a narrow strait.",
    "Gulls circle over fishing ships.",
    "Artists sketch cliffs at sunset.",
    "Doctors visit homes on Fridays.",
    "Quick trains link distant cities.",
    "Thick walls hold daytime heat.",
    "Choirs sing loud songs on feast days.",
    "Lamps shine softly in tall halls.",
    "Guests leave notes in a long ledger.",
    "Dogs nap in sunny yards.",
)

#: Words and letters the pool must never contain, gathered from the library
#: so that a new forbidding or requiring constraint extends the check.
def _pool_exclusions() -> tuple[set[str], set[str]]:
    """Read from A and the v1 references. Library v2's additions (R1) forbid
    or require words and letters (q, x, j, k, v, velvet, ...) that the pools
    use; the pools stay as they are, so v1's witnesses and matrix hash are
    unchanged. A v2 addition is served by the verifier-filtered witnesses
    (``_greedy``, ``_fill``), and ``check`` verifies every witness anyway."""
    from dci.batch1.library import _reference_library_v1
    words: set[str] = {"however", "the"}
    letters: set[str] = set()
    for c in a_candidates() + _reference_library_v1():
        p = c.p
        words |= set(c.required_words())
        words |= set(p.get("words", ()))
        if "letter" in p:
            letters.add(p["letter"])
    return words, letters


def assert_pool() -> dict[str, Any]:
    words, letters = _pool_exclusions()
    seen_openers = set()
    for s in SENTENCE_POOL:
        ws = T.folded_words(s)
        if T.sentences(s) != [s]:
            raise AssertionError(f"pool sentence is not one sentence: {s!r}")
        if max(len(w) for w in ws) > POOL_MAX_LETTERS:
            raise AssertionError(f"pool word over {POOL_MAX_LETTERS} letters: {s!r}")
        if set(ws) & words:
            raise AssertionError(f"pool uses a library word: {s!r}")
        if any(ch in w for w in ws for ch in letters):
            raise AssertionError(f"pool uses a forbidden letter: {s!r}")
        if "," in s or ";" in s:
            raise AssertionError(f"pool sentence carries punctuation: {s!r}")
        opener = ws[0]
        if opener in seen_openers:
            raise AssertionError(f"pool opener repeated: {opener!r}")
        seen_openers.add(opener)
    return {"sentences": len(SENTENCE_POOL),
            "max_letters": max(T.max_word_letters(s) for s in SENTENCE_POOL)}


#: Plain sentences for the full-length witnesses. Every word has at most
#: seven letters; no b, z, comma, semicolon or library word; every opener,
#: every word of five or more letters and every adjacent word pair occurs
#: once in the whole pool (``assert_long_pool``), so the uniqueness rules
#: survive any selection.
LONG_POOL: tuple[str, ...] = (
    "Farmers plant early crops on warm slopes.",
    "Local cooks simmer soup with onions and leeks.",
    "Night markets glow with paper lights.",
    "Young poets read aloud in crowded cafes.",
    "Ferry trips cross a narrow strait at dawn.",
    "Gulls circle over fishing ships.",
    "Artists sketch cliffs at sunset.",
    "Doctors visit homes on Fridays.",
    "Quick trains link distant cities.",
    "Thick walls hold daytime heat.",
    "Choirs sing loud songs on feast days.",
    "Lamps shine softly in tall halls.",
    "Guests leave notes in long ledgers.",
    "Elders share old tales at dusk.",
    "Kids play games after school ends.",
    "Rain falls often in spring.",
    "Many people walk to work each day.",
    "Our town has four stone towers.",
    "Fresh fruit sells fast in summer.",
    "Hikers walk steep trails in pairs.",
    "Weavers spin wool into soft yarn.",
    "Clocks tick loudly in empty rooms.",
    "Tailors mix red and gold silk.",
    "Pupils queue for tickets at noon.",
    "Horses rest calmly near ponds.",
    "Jesters amuse crowds at fairs.",
    "Uncles tell jokes over dinners.",
    "Ink dries slowly on damp pages.",
    "Velvet drapes frame old stages.",
    "Ice melts quickly on hot roofs.",
    "Wise owls hunt mice in dark fields.",
    "Potters shape wet clay on a wheel.",
)
TASK_MIN_WORDS, TASK_MAX_WORDS = 60, 120
TASK_COMPATIBLE, TASK_UNRESOLVED = "TASK_COMPATIBLE", "TASK_UNRESOLVED"
_TASK_TARGET = 64


def assert_long_pool() -> dict[str, Any]:
    words, letters = _pool_exclusions()
    openers, long_words, pairs = set(), set(), set()
    for s in LONG_POOL:
        ws = T.folded_words(s)
        if T.sentences(s) != [s] or "," in s or ";" in s:
            raise AssertionError(f"long pool: not one plain sentence: {s!r}")
        if max(len(w) for w in ws) > POOL_MAX_LETTERS or set(ws) & words or \
                any(ch in w for w in ws for ch in letters | {"b", "z"}):
            raise AssertionError(f"long pool: forbidden word or letter: {s!r}")
        for item, seen in ((ws[0], openers),):
            if item in seen:
                raise AssertionError(f"long pool: opener repeated: {s!r}")
            seen.add(item)
        for w in ws:
            if len(w) >= 5:
                if w in long_words:
                    raise AssertionError(f"long pool: {w!r} repeated")
                long_words.add(w)
        for pair in zip(ws, ws[1:]):
            if pair in pairs:
                raise AssertionError(f"long pool: pair {pair} repeated")
            pairs.add(pair)
    return {"sentences": len(LONG_POOL),
            "words": sum(T.word_count(s) for s in LONG_POOL)}


def _lower_first(s: str) -> str:
    return s[0].lower() + s[1:]


def _strip_stop(s: str) -> str:
    return s[:-1] if s.endswith(".") else s


def _pool(i: int) -> str:
    return SENTENCE_POOL[i % len(SENTENCE_POOL)]


def _base(n: int = 4) -> list[str]:
    return [_pool(i) for i in range(n)]


#: Natural carriers for required words; anything else is mentioned.
_CARRIERS = {
    "simple": "The plan was simple.",
    "window": "A window faced east.",
    "garden": "A garden grew there.",
    "silver": "A silver spoon lay there.",
    "morning": "Rain fell all morning.",
    "quiet": "The room was quiet.",
    "remarkable": "The view was remarkable.",
}


def _carrier(word: str, i: int) -> str:
    rest = _lower_first(_pool(i + 4))
    if word == "although":
        return f"Although it was late, {rest}"
    return f"{word.capitalize()}, {rest}"


def _greedy(keep: Callable[[str], bool], *, min_words: int = 24,
            max_sentences: int = 24) -> str:
    chosen: list[str] = []
    for s in SENTENCE_POOL:
        if keep(" ".join(chosen + [s])):
            chosen.append(s)
        if T.word_count(" ".join(chosen)) >= min_words or \
                len(chosen) >= max_sentences:
            break
    return " ".join(chosen)


def _joined(i: int, j: int, sep: str = " and ") -> str:
    return _strip_stop(_pool(i)) + sep + _lower_first(_pool(j))


#: Library v2's marks (R1), one per sentence: the mark ends or joins it.
_MARKED = (":", "?", "!", "(")


def _marked(char: str, pool: Callable[[int], str], i: int) -> str:
    a, b = _strip_stop(pool(2 * i)), _lower_first(pool(2 * i + 1))
    if char == ":":
        return f"{a}: {b}"
    if char == "(":
        return f"{a} (and {_strip_stop(b)})."
    return f"{a}{char}"


def _numbered(pool: Callable[[int], str], i: int) -> str:
    return f"{_strip_stop(pool(i))} {i + 2} times."


def _padding(parts: list[str], pool: Callable[[int], str], *,
             start: int = 20, min_words: int = 24) -> list[str]:
    """Plain pool sentences after ``parts`` until the text keeps B
    non-vacuous."""
    out: list[str] = []
    i = start
    while T.word_count(" ".join(parts + out)) < min_words:
        out.append(pool(i))
        i += 1
    return out


def _lengthened(target: int) -> str:
    """A sentence of exactly ``target`` words from pool material."""
    words: list[str] = []
    i = 0
    while len(words) < target:
        words += T.words(_pool(i))
        i += 1
    words = words[:target]
    return " ".join([words[0].capitalize()] + [w.lower() for w in words[1:]]) + "."


def build_witness(c: Constraint) -> str | None:
    """A non-vacuous text meant to satisfy ``c``; ``check`` verifies it."""
    p, fam = c.p, c.family_id
    if fam == "exact_word_count":
        return " ".join(_base(3) + [_carrier(p["word"], i) for i in range(p["n"])])
    if fam == "max_word_length":
        return " ".join(_base(4))
    if fam == "exact_char_count" and p["char"] in _MARKED:
        marked = [_marked(p["char"], _pool, i) for i in range(p["n"])]
        return " ".join(marked + _padding(marked, _pool))
    if fam == "exact_char_count":
        sep = ", and " if p["char"] == "," else "; "
        # One mark per joined pair; two plain sentences keep B non-vacuous.
        joined = [_joined(2 * i, 2 * i + 1, sep) for i in range(p["n"])]
        return " ".join(joined + [_pool(20), _pool(21)])
    if fam == "exact_numeral_count":
        counted = [_numbered(_pool, i) for i in range(p["n"])]
        return " ".join(counted + _padding(counted, _pool))
    if fam == "positional_word" and p["where"] == "start":
        first = [f"{p['word'].capitalize()} {_lower_first(_pool(0))}"]
        return " ".join(first + _padding(first, _pool, start=1))
    if fam == "positional_word":
        return " ".join(_padding([], _pool) + [f"We move {p['word']}."])
    if fam == "positional_question":
        return " ".join(_padding([], _pool) + ["Who knows why?"])
    if fam == "exact_sentence_count":
        return " ".join(_pool(i) for i in range(p["n"]))
    if fam == "exact_paragraph_count":
        return "\n\n".join(" ".join(_pool(2 * i + k) for k in range(2))
                           for i in range(p["n"]))
    if fam == "include_words":
        carriers = [_CARRIERS.get(w, f"We say {w} here.") for w in p["words"]]
        return " ".join(_base(3) + carriers)
    if fam in ("forbid_words", "forbid_letter", "no_repeated_words",
               "no_repeated_bigrams"):
        return _greedy(lambda t: V.VERIFIERS[c.family.verifier_id](
            t, **p).passed)
    if fam == "sentence_word_bound":
        if p["bound"] == "max":
            return _greedy(lambda t: V.VERIFIERS[c.family.verifier_id](
                t, **p).passed)
        return " ".join(_lengthened(max(p["k"], 12) + i) for i in range(3))
    if fam == "distinct_openers":
        return " ".join(_base(max(p["min_sentences"], 4)))
    if fam == "length_order":
        k = p["min_sentences"]
        # Shortest first sentence that keeps B non-vacuous (4 for k >= 4).
        first = max(4, -(-(V.NON_VACUITY_MIN_WORDS - k * (k - 1) // 2) // k))
        lengths = [first + i for i in range(k)]
        if p["direction"] == "decreasing":
            lengths.reverse()
        return " ".join(_lengthened(n) for n in lengths)
    if fam == "alphabetical_openers":
        ordered = sorted(SENTENCE_POOL, key=lambda s: T.first_word(s))
        return " ".join(ordered[:max(p["min_sentences"], 4)])
    if fam == "chain_word":
        chain = ["Rivers carry cold water to the mill.",
                 "Mill wheels turn all day long.",
                 "Long days end in calm evenings.",
                 "Evenings bring rest to every town."]
        return " ".join(chain[:max(p["min_sentences"], 4)])
    if fam == "chain_letter":
        chain = ["Calm rivers carry cold water past old mills.",
                 "Small shops open early near a stone square.",
                 "Every street has a name and a story.",
                 "Young poets read aloud in cafes."]
        return " ".join(chain[:max(p["min_sentences"], 4)])
    if fam == "adjacent_shared_word":
        chain = ["Rivers carry cold water past old mills.",
                 "That water turns the mill wheels all day.",
                 "Each day the wheels grind fresh grain.",
                 "Fresh grain then goes to local cooks."]
        return " ".join(chain[:max(p["min_sentences"], 4)])
    return None


# ----------------------------------------------- full-length witnesses (§11)

def _lp(i: int) -> str:
    return LONG_POOL[i % len(LONG_POOL)]


def _lp_join(i: int, j: int, sep: str = " and ") -> str:
    return _strip_stop(_lp(i)) + sep + _lower_first(_lp(j))


def _wc(parts: list[str], sep: str = " ") -> int:
    return T.word_count(sep.join(parts))


def _fill(parts: list[str], keep: Callable[[str], bool], *, start: int = 0,
          target: int = _TASK_TARGET) -> str:
    """Add long-pool sentences (in order, from ``start``) while ``keep`` holds,
    until the text reaches ``target`` words."""
    out = list(parts)
    for k in range(len(LONG_POOL)):
        if _wc(out) >= target:
            break
        candidate = _lp(start + k)
        if candidate in out:
            continue
        if keep(" ".join(out + [candidate])):
            out.append(candidate)
    return " ".join(out)


def _stream(n: int, offset: int = 0) -> list[str]:
    words: list[str] = []
    i = offset
    while len(words) < n:
        words += [w.lower() for w in T.words(_lp(i))]
        i += 1
    return words[:n]


def _sentence(words: list[str]) -> str:
    return " ".join([words[0].capitalize()] + words[1:]) + "."


def task_witness(c: Constraint) -> str | None:
    """A 60-120 word, non-vacuous text meant to satisfy ``c`` (and every B
    limit ``c`` is logically compatible with); ``task_level`` verifies it."""
    p, fam = c.p, c.family_id
    vid = c.family.verifier_id
    keep = lambda t: V.VERIFIERS[vid](t, **p).passed   # noqa: E731
    if fam == "exact_word_count":
        carriers = [(f"Although it was late, {_lower_first(_lp(i))}"
                     if p["word"] == "although" else
                     f"{p['word'].capitalize()}, {_lower_first(_lp(i))}")
                    for i in range(p["n"])]
        return _fill(carriers, keep, start=p["n"])
    if fam == "exact_char_count" and p["char"] in _MARKED:
        marked = [_marked(p["char"], _lp, i) for i in range(p["n"])]
        return _fill(marked, keep, start=2 * p["n"])
    if fam == "exact_char_count":
        sep = ", and " if p["char"] == "," else "; "
        joined = [_lp_join(2 * i, 2 * i + 1, sep) for i in range(p["n"])]
        return _fill(joined, keep, start=2 * p["n"])
    if fam == "exact_numeral_count":
        return _fill([_numbered(_lp, i) for i in range(p["n"])], keep,
                     start=p["n"])
    if fam == "positional_word" and p["where"] == "start":
        return _fill([f"{p['word'].capitalize()} {_lower_first(_lp(0))}"],
                     keep, start=1)
    if fam == "positional_word":
        return _fill([], lambda t: True, target=_TASK_TARGET - 3) + \
            f" We move {p['word']}."
    if fam == "positional_question":
        return _fill([], lambda t: True, target=_TASK_TARGET - 3) + \
            " Who knows why?"
    if fam == "exact_sentence_count":
        n, per = p["n"], 1
        while n * per * 6 < _TASK_TARGET:
            per += 1
        out = []
        for i in range(n):
            body = [_strip_stop(_lp(i * per + k)) for k in range(per)]
            out.append(" and ".join([body[0]] + [_lower_first(b)
                                                  for b in body[1:]]) + ".")
        return " ".join(out)
    if fam == "exact_paragraph_count":
        n = p["n"]
        per = -(-_TASK_TARGET // (6 * n))
        return "\n\n".join(" ".join(_lp(i * per + k) for k in range(per))
                           for i in range(n))
    if fam == "include_words":
        carriers = [_CARRIERS.get(w, f"We say {w} here.") for w in p["words"]]
        return _fill(carriers, keep)
    if fam in ("forbid_words", "forbid_letter", "no_repeated_words",
               "no_repeated_bigrams"):
        return _fill([], keep)
    if fam == "distinct_openers":
        # Every long-pool opener is distinct; a prefix of the pool keeps it so.
        return _fill([], lambda t: True)
    if fam == "sentence_word_bound":
        if p["bound"] == "max":
            return _fill([], keep)
        out, i = [], 0
        while _wc(out) < _TASK_TARGET:
            # Pairs (v1); longer runs where a pair is shorter than k (v2).
            parts = [_strip_stop(_lp(i)), _lower_first(_lp(i + 1))]
            i += 2
            while T.word_count(" and ".join(parts)) < p["k"]:
                parts = [parts[0]] + [_strip_stop(x) for x in parts[1:]] + \
                    [_lower_first(_lp(i))]
                i += 1
            out.append(" and ".join(parts))
        return " ".join(out)
    if fam == "length_order":
        k = p["min_sentences"]
        step = 2
        first = max(4, -(-(_TASK_TARGET - step * k * (k - 1) // 2) // k))
        lengths = [first + step * i for i in range(k)]
        if p["direction"] == "decreasing":
            lengths.reverse()
        words, out = _stream(sum(lengths)), []
        for n in lengths:
            out.append(_sentence(words[:n]))
            words = words[n:]
        return " ".join(out)
    if fam == "alphabetical_openers":
        ordered = sorted(LONG_POOL, key=T.first_word)
        out = []
        for sentence in ordered:
            if _wc(out) >= _TASK_TARGET:
                break
            out.append(sentence)
        return " ".join(out)
    if fam in ("chain_word", "chain_letter", "adjacent_shared_word"):
        links = ["rivers", "stones", "lights", "towers", "roads", "lamps",
                 "tales", "songs"]
        k = 6
        middle = _stream(9 * k, offset=3)
        out = []
        for i in range(k):
            body = middle[9 * i: 9 * i + 9]
            if fam == "chain_word":
                words = [links[i]] + body + [links[i + 1]]
            elif fam == "chain_letter":
                words = ["stern"] + body + ["towns"]     # s ... s, then s
            else:
                words = body[:4] + [links[i]] + body[4:] + [links[i + 1]]
            out.append(_sentence(words))
        return " ".join(out)
    return None


def task_level(constraints: tuple[Constraint, ...],
               cells: Mapping[str, Mapping[str, Mapping[str, Any]]]
               ) -> dict[str, Any]:
    """Every logically COMPATIBLE cell, checked against the full contract."""
    assert_long_pool()
    by_id = {c.cid: c for c in constraints}
    out: dict[str, dict[str, Any]] = {}
    unresolved: list[list[Any]] = []
    for cid, row in cells.items():
        c = by_id[cid]
        witness = task_witness(c)
        for m, cell in row.items():
            if cell["status"] != COMPATIBLE:
                continue
            b = next(x for x in b_candidates() if x.p["m"] == int(m))
            words = T.word_count(witness) if witness else 0
            ok = (witness is not None
                  and TASK_MIN_WORDS <= words <= TASK_MAX_WORDS
                  and _compliant(c, witness).compliant
                  and _compliant(b, witness).compliant)
            out.setdefault(cid, {})[m] = {
                "status": TASK_COMPATIBLE if ok else TASK_UNRESOLVED,
                "words": words,
                "witness_hash": sha(["task-witness", witness]) if witness
                else None}
            if not ok:
                unresolved.append([cid, int(m)])
    witnesses = {cid: task_witness(by_id[cid]) for cid in out}
    counts = {s: sum(1 for row in out.values() for cell in row.values()
                     if cell["status"] == s)
              for s in (TASK_COMPATIBLE, TASK_UNRESOLVED)}
    return {"contract": f"{TASK_MIN_WORDS}-{TASK_MAX_WORDS} words "
                        "(library word rule), non-vacuous, X and B compliant",
            "cells": out, "witnesses": witnesses, "counts": counts,
            "unresolved": unresolved}


def _compliant(c: Constraint, text: str) -> V.ConstraintScore:
    return V.score_constraint(c.cid, c.family.verifier_id, c.verifier_params(),
                              c.family.vacuity, text, present=True)


def check(c: Constraint, m: int) -> dict[str, Any]:
    """The status of ``c`` jointly with B_m, with its evidence."""
    b = next(x for x in b_candidates() if x.p["m"] == m) if m in B_LIMITS \
        else Constraint(f"B.max{m}", "B", "max_word_length", (("m", m),),
                        "proposed_unapproved", "ad hoc limit")
    long_words = [w for w in c.required_words() if len(w) > m]
    if long_words:
        return {"cid": c.cid, "m": m, "status": INCOMPATIBLE,
                "reason": (f"every answer satisfying {c.cid} contains "
                           f"{long_words[0]!r} ({len(long_words[0])} letters), "
                           f"which B{m} forbids"),
                "witness": None}
    witness = build_witness(c)
    if witness is None:
        return {"cid": c.cid, "m": m, "status": UNRESOLVED,
                "reason": "no incompatibility proof and no witness builder",
                "witness": None}
    sx, sb = _compliant(c, witness), _compliant(b, witness)
    if sx.compliant and sb.compliant:
        return {"cid": c.cid, "m": m, "status": COMPATIBLE,
                "reason": "constructed witness is compliant with both",
                "witness": witness, "witness_hash": sha(["witness", witness])}
    return {"cid": c.cid, "m": m, "status": UNRESOLVED,
            "reason": (f"witness failed: {c.cid} {sx.verdict}/nv={sx.non_vacuous}"
                       f", B{m} {sb.verdict}/nv={sb.non_vacuous}"),
            "witness": witness}


def compatibility_matrix(constraints: tuple[Constraint, ...] | None = None,
                         limits: tuple[int, ...] = B_LIMITS) -> dict[str, Any]:
    assert_pool()
    constraints = (a_candidates() + reference_library()
                   if constraints is None else constraints)
    cells = {c.cid: {str(m): check(c, m) for m in limits} for c in constraints}
    counts = {s: sum(1 for row in cells.values() for cell in row.values()
                     if cell["status"] == s)
              for s in (COMPATIBLE, INCOMPATIBLE, UNRESOLVED)}
    per_limit = {str(m): sorted(cid for cid, row in cells.items()
                                if row[str(m)]["status"] == COMPATIBLE)
                 for m in limits}
    return {"schema": "dci.batch1/compatibility/v2",
            "limits": list(limits), "cells": cells, "counts": counts,
            "compatible_by_limit": per_limit,
            "task_level": task_level(constraints, cells)}


def compatible_ids(matrix: dict[str, Any], m: int) -> set[str]:
    return set(matrix["compatible_by_limit"][str(m)])


def assert_resolved(matrix: dict[str, Any], limits: tuple[int, ...]) -> None:
    open_cells = [(cid, m) for cid, row in matrix["cells"].items()
                  for m in limits if row[str(m)]["status"] == UNRESOLVED]
    if open_cells:
        raise ValueError(f"unresolved compatibility must be resolved or "
                         f"excluded before the freeze: {open_cells}")


def matrix_hash(matrix: dict[str, Any]) -> str:
    return sha(["batch1/compatibility", matrix])


# ------------------------------------------------- violations (synthetic use)

_VIOLATION_CANDIDATES: tuple[str, ...] = (
    " ".join(SENTENCE_POOL[:4]),
    " ".join(SENTENCE_POOL[:4]) + " The very end is just near, really.",
    " ".join(SENTENCE_POOL[:4]) + " Zebras bring internationalisation.",
    " ".join(SENTENCE_POOL[:4]) + " Calm days pass. Rivers carry rivers.",
    " ".join(SENTENCE_POOL[:3]) + " " + " ".join(
        T.words(" ".join(SENTENCE_POOL[3:7]))).capitalize() + ".",
)


#: Library v2's letter bans (q, x, j) need a text that uses them. Kept apart
#: so that v1's synthetic task-only texts stay as they were.
_VIOLATION_CANDIDATES_V2: tuple[str, ...] = (
    " ".join(SENTENCE_POOL[:4]) + " Six jolly quick foxes vex a judge."
    " This is also so. Gardens and gardens.",
)


def violation_text(c: Constraint) -> str:
    """A non-empty text that ``c``'s verifier FAILS (for synthetic data)."""
    for candidate in _VIOLATION_CANDIDATES + _VIOLATION_CANDIDATES_V2:
        if not V.VERIFIERS[c.family.verifier_id](candidate, **c.p).passed:
            return candidate
    raise AssertionError(f"no violation text fails {c.cid}")
