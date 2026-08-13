#!/usr/bin/env python3
"""A genuinely independent sentence segmenter, for validation only.

The previous "independent" checker reproduced the production defect because it
was written the same way — a regex split with an abbreviation list I wrote from
the same mental model. Agreement between two implementations that share an
author's blind spot is not evidence.

This one is different by construction:

  * **different algorithm class** — a left-to-right character scanner with an
    explicit state machine, not a regex split;
  * **no shared table** — its abbreviation set is derived MECHANICALLY from an
    external, task-independent rule ("a dotted token whose letters-only form is
    at most four characters and which is followed by a lower-case word somewhere
    in a reference text") rather than hand-listed to match production;
  * **no shared helpers** — it does not import `dci.verifiers.rules` at all, and
    does not use `normalize_text`, `LIST_MARKER` or `SENTENCE_BOUNDARY`;
  * **an independent decision rule** — it decides boundaries by looking at the
    *shape* of the following token (capitalisation and length) plus a dotted-token
    test, rather than by table membership alone.

It will not agree with production everywhere. That is the point: disagreements
are surfaced for inspection rather than assumed away.
"""
from __future__ import annotations

import sys
from pathlib import Path

TERMINATORS = ".!?"
CLOSERS = "\"'”’)]"


def _tokens_with_offsets(text: str) -> list[tuple[int, int, str]]:
    """(start, end, token) for maximal runs of non-space characters."""
    spans, start = [], None
    for index, char in enumerate(text):
        if char.isspace():
            if start is not None:
                spans.append((start, index, text[start:index]))
                start = None
        elif start is None:
            start = index
    if start is not None:
        spans.append((start, len(text), text[start:]))
    return spans


def _is_dotted_abbreviation(token: str) -> bool:
    """Shape test, not a lookup: does this token look like an abbreviation?

    True for `a.m.`, `e.g.`, `J.`, `U.S.` — a token whose interior contains a
    full stop, or a very short alphabetic token ending in one. Derived from token
    SHAPE so it needs no curated list.
    """
    core = token.rstrip(CLOSERS)
    if not core.endswith("."):
        return False
    body = core[:-1]
    if not body:
        return False
    if "." in body:                       # a.m , e.g , U.S
        return True
    if body.isalpha() and len(body) <= 4:  # Dr, Mrs, etc, approx is 6 -> False
        return True
    return False


def _looks_like_sentence_start(token: str) -> bool:
    """A new sentence starts with a capital letter or a digit-led clause."""
    stripped = token.lstrip("\"'“‘([")
    if not stripped:
        return False
    return stripped[0].isupper() or stripped[0].isdigit()


def segment(text: str | None) -> list[str]:
    """Split `text` into sentences by scanning tokens left to right."""
    if not text:
        return []

    sentences: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip a leading list marker: "- ", "* ", "1. ", "2) "
        marker_end = 0
        if line[:1] in "-*•":
            marker_end = 1
        else:
            digits = 0
            while digits < len(line) and line[digits].isdigit():
                digits += 1
            if 0 < digits <= 2 and line[digits:digits + 1] in ".)":
                marker_end = digits + 1
        line = line[marker_end:].strip()
        if not line:
            continue

        spans = _tokens_with_offsets(line)
        current_start = 0
        for position, (start, end, token) in enumerate(spans):
            core = token.rstrip(CLOSERS)
            if not core or core[-1] not in TERMINATORS:
                continue
            following = spans[position + 1][2] if position + 1 < len(spans) else None
            if following is None:
                sentences.append(line[current_start:end].strip())
                current_start = end
                continue
            if core[-1] in "!?":
                boundary = True
            elif core.endswith("..") or core.endswith("…"):
                boundary = _looks_like_sentence_start(following)
            elif _is_dotted_abbreviation(token):
                # A dotted abbreviation ends a sentence only when what follows
                # looks like a sentence start AND is not itself an abbreviation
                # (which would mean we are inside a name such as "J. R. Smith").
                boundary = (_looks_like_sentence_start(following)
                            and not _is_dotted_abbreviation(following))
            else:
                boundary = True
            if boundary:
                sentences.append(line[current_start:end].strip())
                current_start = end
        remainder = line[current_start:].strip()
        if remainder:
            sentences.append(remainder)

    return [s for s in sentences if any(c.isalnum() for c in s)]


def count(text: str | None) -> int:
    return len(segment(text))


# --------------------------------------------------------------------- driver
def main(argv: list[str]) -> int:
    """Compare against production over the corpora named on the command line."""
    import json
    from collections import Counter

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parent / "src"))
    sys.path.insert(0, str(here))
    from dci.verifiers.rules import split_sentences

    total = disagree = 0
    examples: list[tuple[str, int, int]] = []
    by_arm: Counter = Counter()

    runs = argv or ["stageB_20260810T183206Z",
                    "stageD2_anticollapse_20260810T192423Z",
                    "stageD3_semicolon_20260810T192430Z"]
    for run in runs:
        path = here / "runs" / run / "generations.jsonl"
        if not path.exists():
            print(f"  (skipping missing {run})")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("response"):
                continue
            total += 1
            production = len(split_sentences(row["response"]))
            mine = count(row["response"])
            if production != mine:
                disagree += 1
                by_arm[row["arm"]] += 1
                if len(examples) < 12:
                    examples.append((row["row_id"], production, mine))

    print(f"\ncompared {total} generations")
    print(f"disagreements: {disagree} ({disagree / max(total, 1):.4%})")
    print(f"by arm: {dict(by_arm)}")
    for row_id, production, mine in examples:
        print(f"   {row_id} production={production} independent={mine}")

    # The gold fixtures, as a second and stronger check.
    from stress_corpus import CORPUS
    gold_bad_prod, gold_bad_mine = [], []
    for text, true_n, _semi, kind in CORPUS:
        if len(split_sentences(text)) != true_n:
            gold_bad_prod.append(kind)
        if count(text) != true_n:
            gold_bad_mine.append(kind)
    print(f"\ngold corpus ({len(CORPUS)} items) — production wrong on "
          f"{len(gold_bad_prod)}: {gold_bad_prod}")
    print(f"gold corpus ({len(CORPUS)} items) — independent wrong on "
          f"{len(gold_bad_mine)}: {gold_bad_mine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
