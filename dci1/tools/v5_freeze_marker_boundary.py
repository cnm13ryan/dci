#!/usr/bin/env python3
"""Freeze §10.2's boundary expectations for v5's seven new marker numerators.

**Every number this writes is computed twice** --- once with the primary
verifiers of ``dci1v5.verifiers.statistics`` and once with the prose-only
reimplementation of ``dci1v5.verifiers.independent``, which was written from
the registered rule statements by a process that does not read the primary
source --- and the tool **refuses to write anything** if the two disagree on
any case. A frozen number that both implementations produce is evidence about
the rule; a frozen number that only one produces is a transcription of that
one, and the suite would then be measuring itself. This is v4r4's own
``tools/v4r3_freeze_r3_boundary.py`` pattern, applied to what v5 adds.

Two things are written:

* ``V5_MARKER_STATS`` --- the seven added numerators for every case text v5
  carries from v4r4, whose fifteen existing expectations stay where they are
  and are untouched;
* ``V5_MARKER_CASES`` --- the cases v5 **authors**, for the phenomena §10.2
  requires of every Tier-1 marker verifier: the marker embedded in a longer
  word, adjacent to punctuation, capitalised at a sentence start, and
  hyphenated. Those four are the ways an exact count of a word can be got
  wrong, and none of them is exercised by a suite written for budgets over
  letter properties.

Usage::

    python3 tools/v5_freeze_marker_boundary.py [--check]

``--check`` recomputes and compares against the committed file without
writing, which is what a test calls.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r4.verifiers import boundary as _v4r4_boundary   # noqa: E402
from dci1v5.verifiers import independent as _independent    # noqa: E402
from dci1v5.verifiers import statistics as _primary         # noqa: E402
from dci1v5.verifiers.constraints import (                  # noqa: E402
    MARKER_WORDS, NEW_STATISTIC_IDS, STATISTIC_IDS,
)

OUTPUT = DCI1 / "src" / "dci1v5" / "verifiers" / "boundary_v5.py"

#: §10.2's four marker-specific phenomena, authored for v5. Each text is
#: chosen so that a defective counter --- one matching substrings, or folding
#: before segmenting, or splitting on a hyphen --- returns a *different*
#: number from the registered rule, which is what makes the case discriminate
#: rather than merely pass.
AUTHORED: tuple[tuple[str, str, str], ...] = (
    ("mk01", "Thus the tide fell and thus the wind rose.",
     "marker-capitalised-at-sentence-start;repeated"),
    ("mk02", "Nevertheless the thusly odd result held.",
     "marker-embedded-in-longer-word"),
    ("mk03", "The result, though, held; though rain fell.",
     "marker-adjacent-to-punctuation;repeated"),
    ("mk04", "A though-provoking though hyphenated case.",
     "marker-hyphenated"),
    ("mk05", "THOUGH though Though tHoUgH.",
     "marker-case-variants"),
    ("mk06", "Whereas whereas whereas.", "marker-repeated-three"),
    ("mk07", "hence hence, hence; hence.", "marker-with-mixed-punctuation"),
    ("mk08", "indeed­indeed indeed", "marker-soft-hyphen"),
    ("mk09", "namely​namely namely", "marker-zero-width"),
    ("mk10", "instead instead instead instead instead instead instead "
             "instead", "marker-eight-occurrences"),
    ("mk11", "Overall, overall matters overall.", "marker-three-with-comma"),
    ("mk12", "", "empty-answer"),
    ("mk13", "Thusly hencewise thoughtful whereabouts indeedy namelycheck "
             "insteadly overalls.", "every-marker-embedded-only"),
)


def _both(statistic_id: str, text: str) -> int:
    """One number, computed twice. Refuses on any disagreement."""
    mine = _primary.statistic_of(statistic_id, text)
    theirs = _independent.statistic(statistic_id, text)
    if mine != theirs:
        raise SystemExit(
            f"§10.2: the primary verifier reads {mine} and the independent "
            f"reimplementation reads {theirs} for {statistic_id!r} on "
            f"{text[:60]!r}. Nothing is frozen: a disagreement is adjudicated "
            "against the registered prose of §7.6 and §9.2, never by writing "
            "one of the two numbers down.")
    return mine


def build() -> str:
    carried_ids = []
    stats: dict[str, tuple[int, ...]] = {}
    for case in _v4r4_boundary.ALL_CASES:
        case_id = case["case_id"]
        carried_ids.append(case_id)
        stats[case_id] = tuple(_both(s, case["text"])
                               for s in NEW_STATISTIC_IDS)
    authored = []
    for case_id, text, covers in AUTHORED:
        vector = {s: _both(s, text) for s in STATISTIC_IDS}
        authored.append({
            "case_id": case_id, "text": text, "covers": covers,
            "origin": "authored_v5", "word_count": _both("one_letter", text)
            if False else len(_primary.alpha_runs(text)),
            "focal": _primary.focal_statistic(text), "stats": vector})

    lines = ['"""Frozen v5 boundary expectations for the marker numerators.',
             "",
             "Generated by ``tools/v5_freeze_marker_boundary.py``, which "
             "computes every",
             "number twice --- once with the primary verifiers and once with "
             "the prose-only",
             "reimplementation of ``verifiers.independent`` --- and refuses "
             "to write anything",
             "if the two disagree on any case. **Do not edit by hand**: "
             "re-run the tool,",
             "which will either reproduce this file exactly or refuse.",
             "",
             "``V5_MARKER_STATS`` carries the seven numerators v5 adds, for "
             "every case text",
             "carried from v4r4; their fifteen existing expectations stay "
             "where they were and",
             "are untouched. ``V5_MARKER_CASES`` are the cases v5 authors "
             "for §10.2's four",
             "marker-specific phenomena: the marker embedded in a longer "
             "word, adjacent to",
             "punctuation, capitalised at a sentence start, and hyphenated.",
             '"""',
             "from __future__ import annotations",
             "",
             "from typing import Any",
             "",
             '__all__ = ["V5_MARKER_STATS", "V5_MARKER_CASES", '
             '"NEW_STATISTIC_ORDER"]',
             "",
             "#: The order the tuples of ``V5_MARKER_STATS`` are written in.",
             f"NEW_STATISTIC_ORDER = {NEW_STATISTIC_IDS!r}",
             "",
             "#: case id -> " + ", ".join(NEW_STATISTIC_IDS),
             "V5_MARKER_STATS: dict[str, tuple[int, ...]] = {"]
    for case_id in carried_ids:
        lines.append(f"    {case_id!r}: {stats[case_id]!r},")
    lines += ["}", "", "V5_MARKER_CASES: tuple[dict[str, Any], ...] = ("]
    for case in authored:
        lines.append(f"    {case!r},")
    lines += [")", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = build()
    if args.check:
        if not OUTPUT.exists():
            print(f"missing {OUTPUT}")
            return 1
        if OUTPUT.read_text() != text:
            print(f"{OUTPUT} does not reproduce; re-run without --check")
            return 1
        print(f"OK: {OUTPUT} reproduces exactly")
        return 0
    OUTPUT.write_text(text)
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
