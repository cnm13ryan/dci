"""The v8 exact-count wording set (development candidate, prospective).

**What the v7 evidence showed (diagnostically, `tools/v8_wording_audit.py`).**
A and the eight marker families share four frames. Two of them never name
the target as a *word*:

    w1  Your answer must contain X exactly q times.
    w2  Include X exactly q times in your answer.

and on the stored Gate-2 rows those two frames are read unreliably: pooled
over MK families the marker is absent from the answer in 46-53% of
responses on both Gemma checkpoints (14-23% under w0/w3), and for markers
that can be parsed as discourse connectives ("though", "namely") it is
absent in 92-100% of them. The frames that do name the target as a word ---
w0 "Use the word X exactly q times." and w3 "The word X must appear exactly
q times." --- are the reliable ones on every model, w3 the most reliable on
all four. One further ambiguity survives w0: "Use the word namely exactly 3
times" can be parsed with *namely* as an appositive ("use the word, namely,
...") and on Gemma the marker is then absent in 50-98% of answers, while w3
("The word namely must appear ...") is followed.

**The mechanism, therefore the rule.** A frame is interpreted reliably when
(a) the target is introduced as ``the word X`` and (b) ``X`` sits in a
position where it cannot be read as a connective of the instruction itself
--- immediately after "the word" and immediately before a verb or the
count. The v8 set applies (a) to every frame and (b) by keeping the target
inside the noun phrase ``the word X`` with the count following it directly.

**The v8 frames.** Minimal edits of the four registered frames: w0 and w3
are unchanged; w1 and w2 gain the two words "the word":

    v8-w0  Use the word X exactly q times.                  (= w0)
    v8-w1  Your answer must contain the word X exactly q times.
    v8-w2  Include the word X exactly q times in your answer.
    v8-w3  The word X must appear exactly q times.          (= w3)

A and MK1-MK8 use the same four frames with the marker substituted, as
§7.8 requires; "time"/"times" follows q. **This is a prospective design
from the diagnosed mechanism, not a post-hoc selection of the best old
frame**: the four-frame diversity is kept, the two repaired frames are
new strings that no stored row was scored under, and their reliability
is a v8 Gate-1 / regime-screen question. ``assert_v8_wordings`` is the
structural test: every frame names the target as "the word X" exactly
once, A and MK frames are identical up to the marker, each frame is a
minimal edit of its v7 counterpart, and the §7.7 length caliper against A
holds by construction.
"""
from __future__ import annotations

from dci1v7.protocol.wordings import (
    WORDING_LENGTH_TOLERANCE,
    target_wordings,
    wording_word_count,
)
from dci1v7.protocol.wordings import wordings as v7_wordings
from dci1v7.verifiers.constraints import FAMILIES, MARKER_WORDS, TIER1_FAMILY_IDS

__all__ = [
    "V8_FRAMES",
    "assert_v8_wordings",
    "diff_from_v7",
    "v8_wording",
    "v8_wordings",
]

TARGET = "however"

V8_FRAMES: tuple[str, str, str, str] = (
    "Use the word {X} exactly {q} time{s}.",
    "Your answer must contain the word {X} exactly {q} time{s}.",
    "Include the word {X} exactly {q} time{s} in your answer.",
    "The word {X} must appear exactly {q} time{s}.",
)


def _marker(kind: str) -> str:
    if kind == "A":
        return TARGET
    if kind not in TIER1_FAMILY_IDS:
        raise ValueError(f"{kind} is not A or a Tier-1 marker family")
    return MARKER_WORDS[FAMILIES[kind].statistic_id]


def v8_wordings(kind: str, q: int) -> tuple[str, str, str, str]:
    x = _marker(kind)
    return tuple(f.format(X=x, q=q, s="" if q == 1 else "s") for f in V8_FRAMES)


def v8_wording(kind: str, index: int, q: int) -> str:
    return v8_wordings(kind, q)[index]


def diff_from_v7(kind: str, q: int) -> list[dict[str, object]]:
    """Per frame: the v7 string, the v8 string, and the inserted tokens.
    A's registered grid stops at 8; the comparison is made where v7 renders."""
    out = []
    q_v7 = min(q, 8) if kind == "A" else q
    for i, (old, new) in enumerate(zip(v7_wordings(kind, q_v7),
                                       v8_wordings(kind, q_v7))):
        old_t, new_t = old.split(), new.split()
        inserted = [t for t in new_t if t not in old_t] if old != new else []
        out.append({"index": i, "v7": old, "v8": new, "changed": old != new,
                    "inserted": inserted})
    return out


def assert_v8_wordings() -> dict[str, object]:
    """The structural guarantees, executable."""
    kinds = ("A",) + tuple(TIER1_FAMILY_IDS)
    for q in (1, 2, 3, 8, 12):
        a_frames = v8_wordings("A", q)
        for kind in kinds:
            x = _marker(kind)
            frames = v8_wordings(kind, q)
            for i, f in enumerate(frames):
                phrase = f"the word {x}"
                if f.lower().count(phrase) != 1:
                    raise AssertionError(f"{kind} v8-w{i} at q={q} does not name "
                                         f"'the word {x}' exactly once: {f!r}")
                after = f.lower().split(phrase, 1)[1].split()[0]
                if after not in ("exactly", "must"):
                    raise AssertionError(f"{kind} v8-w{i}: the marker is not "
                                         f"followed by the count or the verb: {f!r}")
                # identical structure to A's frame, up to the marker
                if f.replace(x, TARGET) != a_frames[i]:
                    raise AssertionError(f"{kind} v8-w{i} differs from A's frame "
                                         "beyond the marker")
                # grammatical number
                expect = "time." if q == 1 else "times."
                if not f.endswith((expect, expect[:-1] + " in your answer.")):
                    raise AssertionError(f"{kind} v8-w{i}: singular/plural: {f!r}")
            # minimal difference from v7: at most the two tokens 'the word'
            for d in diff_from_v7(kind, q):
                if d["changed"] and d["inserted"] != ["the", "word"]:
                    raise AssertionError(f"{kind} v8-w{d['index']}: not a minimal "
                                         f"edit of v7: inserted {d['inserted']}")
            # §7.7 length caliper against A's registered wordings
            for f, a in zip(frames, target_wordings(min(q, 8))):
                n_f, n_a = wording_word_count(f), wording_word_count(a)
                if abs(n_f - n_a) > WORDING_LENGTH_TOLERANCE * max(n_a, 1) + 2:
                    raise AssertionError(f"{kind}: length caliper vs A: {f!r} "
                                         f"({n_f}) against {a!r} ({n_a})")
    return {"frames": list(V8_FRAMES), "families": list(kinds),
            "unchanged_frames": [0, 3], "repaired_frames": [1, 2],
            "inserted_phrase": "the word"}
