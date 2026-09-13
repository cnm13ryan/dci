#!/usr/bin/env python3
"""§34 D4: the registered Tier-1 marker vocabulary, audited item by item.

Emits `reports/dci1v5/development/d4_marker_audit.json` --- the measured and
structural facts about each of §7.10's eight markers, against the researcher's
eight approval criteria. The **verdicts** live in `d4_marker_audit.md`; this
file carries only what a machine can recompute, so a reader can check the
audit's arithmetic without taking its judgement on trust.

Two things it computes rather than repeats:

* the ratio of each marker's natural rate to **A's own rate on the same
  model**. §7.6's registered ceiling is absolute (0.15, benchmarked against A's
  maximum across models); per-model it is not, and a marker that is rarer than
  A on three models and six times commoner on the fourth is a fact the
  absolute rule cannot show.
* the tokenisation probes. Criterion 2 is "deterministic verifier", and the
  way an exact-count marker verifier goes wrong is substring leakage --- an
  `although` counted as a `though`, an `overalls` as an `overall`.

    python3 tools/v5_marker_audit.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v5.verifiers.constraints import (            # noqa: E402
    MARKER_MAX_LETTERS, MARKER_NATURAL_FREQUENCY_MAX,
    REJECTED_MARKERS, RESERVE_MARKER_WORDS, TARGET_WORD, TIER1_FAMILY_IDS,
    FAMILIES, focal_severities,
)
from dci1v5.verifiers.statistics import marker_count  # noqa: E402

DCI1 = Path(__file__).resolve().parents[1]
FREQ = DCI1 / "reports" / "dci1v5" / "development" / "d6_marker_frequency.json"
OUT = DCI1 / "reports" / "dci1v5" / "development" / "d4_marker_audit.json"


#: Probes that must count 1 --- the marker really is there.
MUST_COUNT = ("sentence_initial_with_comma", "quoted", "upper_case")
#: Probes that must count 0 --- the marker is not there and a substring is.
MUST_NOT_COUNT = ("as_a_prefixed_substring", "as_a_suffixed_substring",
                  "inside_an_unrelated_word")


def probes(word: str) -> dict[str, int]:
    """The ways an exact-count marker verifier is usually wrong.

    ``hyphenated_compound`` and ``hyphenated_spelling`` are neither: they are
    §9.2's segmentation convention showing itself. A hyphen splits a word, so
    a compound ending in the marker counts and a hyphenated spelling of the
    marker does not. Reported rather than judged --- A's own ``however``
    counter behaves identically, which is what makes v5's same-form claim an
    identity of implementation.
    """
    return {
        "sentence_initial_with_comma": marker_count(
            f"{word.capitalize()}, it holds.", word),
        "quoted": marker_count(f"He said '{word}' once.", word),
        "upper_case": marker_count(f"{word.upper()} IT HOLDS", word),
        "as_a_prefixed_substring": marker_count(f"al{word} it holds", word),
        "as_a_suffixed_substring": marker_count(f"{word}s here", word),
        "inside_an_unrelated_word": marker_count("enthusiasm overalls", word),
        "hyphenated_compound": marker_count(f"semi-{word} case", word),
        "hyphenated_spelling": marker_count(
            f"{word[:len(word)//2]}-{word[len(word)//2:]} case", word),
    }


def build() -> dict[str, object]:
    freq = json.loads(FREQ.read_text())
    per_model = freq["per_model"]
    benchmark = freq["a_marker_benchmark"]
    grid = focal_severities(extended=True)
    markers = []
    for kind in TIER1_FAMILY_IDS:
        family = FAMILIES[kind]
        word = family.marker
        natural = {m: per_model[m].get(word, {}).get(
            "p_at_least_one_unconstrained") for m in per_model}
        under_b = {m: per_model[m].get(word, {}).get(
            "p_at_least_one_b_solo") for m in per_model}
        markers.append({
            "family": kind,
            "statistic_id": family.statistic_id,
            "marker": word,
            "letters": len(word),
            "discourse_role": family.metadata["discourse_role"],
            "form": family.form,
            "registered_max_natural_rate": family.development_frequency_max,
            "natural_rate_by_model": natural,
            "rate_under_b_by_model": under_b,
            "ratio_to_a_by_model": {
                m: (round(natural[m] / benchmark[m], 3)
                    if natural[m] is not None and benchmark[m] else None)
                for m in per_model},
            "violates_b_at": [m for m in grid if len(word) > m],
            "at_the_b_boundary_at": [m for m in grid if len(word) == m],
            "verifier_probes": probes(word),
            "carried_from_v4r4": family.statistic_source == "CX1",
        })
    return {
        "_what": "the measured and structural facts behind §34 D4's audit; "
                 "the verdicts are in d4_marker_audit.md",
        "_classification": "DEVELOPMENT_EVIDENCE (§30)",
        "_frequency_source": "development/d6_marker_frequency.json, four "
                             "v4r4 replications, unconstrained and B-solo "
                             "cells",
        "a_marker": TARGET_WORD,
        "a_natural_rate_by_model": benchmark,
        "registered_rules": {
            "max_letters": MARKER_MAX_LETTERS,
            "max_natural_rate": MARKER_NATURAL_FREQUENCY_MAX,
            "excluded": TARGET_WORD,
        },
        "focal_grid": list(grid),
        "markers": markers,
        "reserve": {w: dict(v) for w, v in RESERVE_MARKER_WORDS.items()},
        "rejected": dict(REJECTED_MARKERS),
        "summary": {
            "n_markers": len(markers),
            "n_discourse_roles": len({m["discourse_role"] for m in markers}),
            "any_marker_violates_b_on_the_grid": any(
                m["violates_b_at"] for m in markers),
            "every_marker_counts_where_it_appears": all(
                m["verifier_probes"][k] == 1
                for m in markers for k in MUST_COUNT),
            "no_substring_leaks": all(
                m["verifier_probes"][k] == 0
                for m in markers for k in MUST_NOT_COUNT),
            "hyphen_splits_a_word": "a compound ending in the marker counts "
                                    "and a hyphenated spelling of the marker "
                                    "does not; §9.2's convention, and A's own "
                                    "counter behaves the same way",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; rerun without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
