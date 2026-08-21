"""Freeze the R3 boundary expectations, from two implementations that agree.

§10.2 requires a frozen number to be evidence about the *rule* rather than a
transcription of one implementation. So every number this writes is computed
by the primary verifier and by the prose-only reimplementation of
``verifiers.independent``, and the tool refuses to write anything if the two
disagree anywhere. Run it again after any change to either and it will either
reproduce the file byte for byte or refuse.

    python3 tools/v4r3_freeze_r3_boundary.py           # check only
    python3 tools/v4r3_freeze_r3_boundary.py --write
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r3.verifiers import independent as I                   # noqa: E402
from dci1v4r3.verifiers.constraints import R3_STATISTIC_IDS       # noqa: E402
from dci1v4r3.verifiers.statistics import (                       # noqa: E402
    STATISTICS, focal_statistic, word_count,
)

OUT = DCI1 / "src" / "dci1v4r3" / "verifiers" / "boundary_r3.py"
SOURCE = DCI1 / "src" / "dci1v4r3" / "verifiers" / "boundary.py"

#: Cases authored for the R3 amendment: the phenomena its six numerators and
#: its one new predicate form introduce and the round-0 corpus does not reach.
#: Text and coverage labels are authored; every number below is derived.
AUTHORED: tuple[tuple[str, str], ...] = (
    ("r301", "Rain falls"),
    ("r302", "Rain falls."),
    ("r303", "Rain falls..."),
    ("r304", "Rain falls?!"),
    ("r305", "Rain falls.   "),
    ("r306", "Dr. Smith spoke"),
    ("r307", "It cost 3.14 euros"),
    ("r308", "One. Two. Three."),
    ("r309", "thus"),
    ("r310", "thus thus"),
    ("r311", "thus thus thus"),
    ("r312", "thusly thus"),
    ("r313", "Thus THUS thus"),
    ("r314", "a; b;; c"),
    ("r315", ";"),
    ("r316", "Apple orange Igloo under Egg"),
    ("r317", "yellow year yes"),
    ("r318", "İstanbul under"),
    ("r319", "cats' toys are"),
    ("r320", "s"),
    ("r321", "The tall trees to town"),
    ("r322", "sit sat set sun"),
    ("r323", "tap tap tap tap tap tap tap tap"),
    ("r324", "as at ax an am"),
    ("r325", "one two three four five six seven eight nine ten "
             "one two three four five six seven eight nine"),
    ("r326", "one two three four five six seven eight nine ten "
             "one two three four five six seven eight nine ten"),
    ("r327", ""),
    ("r328", "   \n  "),
)

COVERS = {
    "r301": "sentence-boundary;unterminated-tail",
    "r302": "sentence-boundary;single-terminator",
    "r303": "sentence-boundary;terminator-run",
    "r304": "sentence-boundary;terminator-run;mixed-terminators",
    "r305": "sentence-boundary;trailing-whitespace",
    "r306": "sentence-boundary;abbreviation-overcount",
    "r307": "sentence-boundary;non-decimal-numeric;decimal-overcount",
    "r308": "sentence-boundary;rate-straddle",
    "r309": "exact-count;single-word-answer",
    "r310": "exact-count;threshold-minus-one",
    "r311": "exact-count;threshold-plus-one",
    "r312": "exact-count;substring-not-word;concatenated-copies",
    "r313": "exact-count;capitalisation",
    "r314": "adjacent-punctuation;semicolon-run",
    "r315": "single-token-output;semicolon-run",
    "r316": "vowel-initial;capitalisation",
    "r317": "vowel-initial;y-is-not-a-vowel",
    "r318": "vowel-initial;case-folding-split;combining-mark",
    "r319": "s-final;adjacent-punctuation",
    "r320": "s-final;single-word-answer;one-letter",
    "r321": "t-initial;capitalisation",
    "r322": "s-final;rate-straddle",
    "r323": "t-initial;rate-straddle;repeated",
    "r324": "vowel-initial;rate-straddle",
    "r325": "non-vacuity-boundary;nineteen-words",
    "r326": "non-vacuity-boundary;twenty-words",
    "r327": "empty-output",
    "r328": "empty-output;trailing-whitespace",
}


def derive(text: str) -> tuple[int, int, tuple[int, ...], tuple[int, ...]]:
    """Both implementations, or a refusal."""
    primary = {k: fn(text) for k, fn in STATISTICS.items()}
    independent = {k: I.statistic(k, text) for k in STATISTICS}
    if primary != independent:
        raise SystemExit(f"the two implementations disagree on {text!r}: "
                         f"{ {k: (primary[k], independent[k]) for k in primary if primary[k] != independent[k]} }")
    if word_count(text) != I.word_count(text):
        raise SystemExit(f"word count disagrees on {text!r}")
    if focal_statistic(text) != I.focal_statistic(text):
        raise SystemExit(f"focal statistic disagrees on {text!r}")
    round0 = tuple(v for k, v in primary.items() if k not in R3_STATISTIC_IDS)
    r3 = tuple(primary[k] for k in R3_STATISTIC_IDS)
    return word_count(text), focal_statistic(text), round0, r3


def existing_case_texts() -> list[tuple[str, str]]:
    """The v4r3 case ids and texts, read out of the source as literals.

    Parsed rather than imported, because ``boundary`` imports this module's
    output and a cycle would make the freeze depend on the frozen file.
    """
    tree = ast.parse(SOURCE.read_text())
    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_case":
            case_id = ast.literal_eval(node.args[0])
            text = ast.literal_eval(node.args[1])
            out.append((case_id, text))
    return out


def render() -> str:
    lines = ['"""Frozen R3 boundary expectations (§10.2, §7.0-R3).',
             "",
             "Generated by ``tools/v4r3_freeze_r3_boundary.py``, which computes every",
             "number twice --- once with the primary verifiers and once with the",
             "prose-only reimplementation of ``verifiers.independent`` --- and refuses",
             "to write anything if the two disagree on any case. Do not edit by hand:",
             "re-run the tool, which will either reproduce this file exactly or refuse.",
             "",
             "``R3_STATS`` carries the six added numerators for the forty cases authored",
             "before the amendment; their nine round-0 expectations stay where they were",
             "and are untouched. ``R3_CASES`` are the cases the amendment adds, for the",
             "phenomena its numerators and its exact-count form introduce.",
             '"""',
             "from __future__ import annotations",
             "",
             "from typing import Any",
             "",
             '__all__ = ["R3_STATS", "R3_CASES"]',
             "",
             "#: case id -> (t_initial, s_final, vowel_initial, sentence,",
             "#:             marker_thus, semicolon)",
             "R3_STATS: dict[str, tuple[int, ...]] = {"]
    for case_id, text in existing_case_texts():
        _, _, _, r3 = derive(text)
        lines.append(f"    {case_id!r}: {r3!r},")
    lines.append("}")
    lines.append("")
    lines.append("R3_CASES: tuple[dict[str, Any], ...] = (")
    for case_id, text in AUTHORED:
        w, b, round0, r3 = derive(text)
        covers = COVERS[case_id]
        lines.append(f"    {{'case_id': {case_id!r}, 'text': {text!r},")
        lines.append(f"     'covers': {covers!r}, 'origin': 'authored_r3',")
        lines.append(f"     'word_count': {w}, 'focal': {b},")
        lines.append(f"     'round0': {round0!r},")
        lines.append(f"     'r3': {r3!r}}},")
    lines.append(")")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rendered = render()
    if args.write:
        OUT.write_text(rendered)
        print(f"wrote {OUT.relative_to(DCI1)}")
        return 0
    current = OUT.read_text() if OUT.exists() else ""
    if current != rendered:
        print("the frozen file does not match what the two implementations "
              "now produce; re-run with --write only if the change is intended")
        return 1
    print("frozen R3 boundary expectations reproduce exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
