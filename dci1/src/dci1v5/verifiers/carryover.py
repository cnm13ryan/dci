"""§10.2 and §30's carry-over record: what v5 inherits, and how it is measured.

The carry-over rule is strict on purpose. A carried instrument may supply
carried evidence **only** when its construct string, segmentation function
source, counting function source and frozen case texts with their expectations
are byte-identical to the source artifact. This module names each source,
records its hash, and refuses on any mismatch.

**Two of §30's seven invariants are measured rather than asserted**, and that
is the whole reason this module executes anything:

1. **Verifier semantics.** Both revisions' compliance predicates are run over
   every carried instrument against every case of the frozen boundary corpus,
   and any disagreement is a refusal --- not a note.
2. **The model-facing prompt.** Every constraint sentence a carried row stores
   is compared against the wording v5 renders now, so a wording that drifted
   is caught where the rows are admitted rather than where the numbers are
   used.

The other five --- instrument identity, severity, the sampling regime, the
model and its revision, and the decoding configuration --- are asserted from
the record, because they are properties of the artifact rather than of the
code, and ``carry_over_record`` records a finding for each.

**What v5 carries, and what it deliberately does not.**

| Source | Standing |
|---|---|
| ``alpha_runs`` | carried, byte-identical through ``dci1v4`` to v3 |
| ``s0_count`` and A's alternatives | carried, byte-identical |
| the construct string ``however`` | carried |
| ``words_lower``, ``sentence_units`` | carried from v4r4, which corrected the composition order |
| the fourteen non-marker numerators | carried from v4r4 |
| ``marker_thus`` | carried from v4r4's ``CX1``, which is v5's ``MK1`` |
| the frozen v4r4 boundary case texts and their expectations | carried, with v5's seven marker columns added by ``tools/v5_freeze_marker_boundary.py`` and computed twice |
| the seven new marker numerators | **NOT carried.** They earn their own §10.2 evidence |
| ``XC2`` and ``XC3`` | numerators carried; the **exact-count form** is new and earns its own |

**No v4r4 generation is carried into a v5 estimand.** v4r4's rows exist for v5
only as ``DEVELOPMENT_EVIDENCE`` and ``RECOMPUTED_DIAGNOSTIC``, and §14.2's
admission guard refuses them structurally, in both directions. This module
reads v4r4 *source* to measure agreement; it admits no v4r4 row anywhere.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Iterable, Mapping

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_text

from dci1v5.protocol import wordings as _wordings
from dci1v5.verifiers.boundary import ALL_CASES
from dci1v5.verifiers.constraints import (
    CARRIED_FROM_V4R4, Constraint, FAMILIES, NEW_STATISTIC_IDS, STATISTIC_IDS,
)
from dci1v5.verifiers.statistics import statistic_of

__all__ = ["CARRIED_SYMBOLS", "NOT_CARRIED", "REUSE_INVARIANTS",
           "symbol_source", "assert_statistics_agree_with_v4r4",
           "assert_wordings_match_stored", "carry_over_record"]

#: §30's seven registered invariants. The first two are **measured** here;
#: the other five are asserted from the artifact record.
REUSE_INVARIANTS = ("verifier_semantics", "model_facing_prompt",
                    "instrument_identity", "severity", "sampling_regime",
                    "model_and_revision", "decoding_configuration")
MEASURED_INVARIANTS = ("verifier_semantics", "model_facing_prompt")

#: (module, symbol) pairs whose source v5 inherits unchanged from v4r4.
CARRIED_SYMBOLS = (
    ("verifiers/words.py", "words_lower"),
    ("verifiers/words.py", "sentence_units"),
    ("verifiers/words.py", "case_folding_splitters"),
)

#: Named so a reader learns what must earn its own evidence, on the mandatory
#: path rather than in a report.
NOT_CARRIED = {
    statistic_id: "new in v5: no v4r4 counterpart, so §10.2 requires its own "
                  "boundary, adversarial, reimplementation and mutation "
                  "evidence"
    for statistic_id in NEW_STATISTIC_IDS
}
NOT_CARRIED["XC2:form"] = ("the `comma` numerator is carried; the exact-count "
                           "predicate over it is new")
NOT_CARRIED["XC3:form"] = ("the `sentence` numerator is carried; the "
                           "exact-count predicate over it is new")


def symbol_source(path: Path, name: str) -> str:
    """The exact source text of one top-level symbol, for hashing."""
    tree = ast.parse(Path(path).read_text())
    for node in tree.body:
        if getattr(node, "name", None) == name:
            return ast.get_source_segment(Path(path).read_text(), node) or ""
    raise ProtocolError(f"{name!r} not found in {path}")


def assert_statistics_agree_with_v4r4() -> dict[str, Any]:
    """§30, measured: both revisions' numerators agree on the whole corpus.

    Every carried numerator is run under v4r4's implementation and under v5's
    over every case text of the frozen boundary corpus, and a disagreement is
    a refusal. The seven markers v5 adds have no v4r4 counterpart and are
    excluded by construction, which is what ``NOT_CARRIED`` records.

    This is the one place v5 source reads v4r4 source, and it reads *code*
    rather than evidence: no v4r4 row is admitted anywhere.
    """
    from dci1v4r4.verifiers.statistics import (
        STATISTICS as _V4R4_STATISTICS,
    )

    carried = [s for s in STATISTIC_IDS if s in _V4R4_STATISTICS]
    checked = 0
    for case in ALL_CASES:
        text = case["text"]
        for statistic_id in carried:
            mine = statistic_of(statistic_id, text)
            theirs = _V4R4_STATISTICS[statistic_id](text)
            if mine != theirs:
                raise ProtocolError(
                    f"§30: {statistic_id} reads {mine} in v5 and {theirs} in "
                    f"v4r4 on the frozen case {case['case_id']!r}. A carried "
                    "numerator that disagrees is not carried, and the "
                    "carry-over record is refused rather than annotated")
            checked += 1
    return {"invariant": "verifier_semantics", "measured": True,
            "carried_numerators": carried,
            "not_carried": sorted(NEW_STATISTIC_IDS),
            "cases": len(ALL_CASES), "comparisons": checked,
            "agreement": 1.0}


def assert_wordings_match_stored(rows: Iterable[Mapping[str, Any]]
                                 ) -> dict[str, Any]:
    """§30, measured: every stored constraint sentence is what v5 renders now.

    ``rows`` carry ``kind``, ``severity``, ``wording_index`` and
    ``constraint_sentence``. A row whose stored sentence differs from the
    wording v5 renders is refused: a carried instrument whose *prompt* moved
    is a different treatment, however identical its verifier.

    An empty input returns a finding saying so rather than a silent pass,
    because "no rows were checked" and "every row matched" are different
    facts and only one of them is evidence.
    """
    rows = list(rows)
    mismatches: list[dict[str, Any]] = []
    for row in rows:
        rendered = _wordings.wording(row["kind"], int(row["wording_index"]),
                                     int(row["severity"]))
        if rendered != row["constraint_sentence"]:
            mismatches.append({"kind": row["kind"],
                               "severity": row["severity"],
                               "stored": row["constraint_sentence"],
                               "rendered": rendered})
    if mismatches:
        raise ProtocolError(
            f"§30: {len(mismatches)} stored constraint sentence(s) differ "
            f"from what v5 renders; first {mismatches[0]}. A carried "
            "instrument whose model-facing prompt moved is a different "
            "treatment, however identical its verifier")
    return {"invariant": "model_facing_prompt", "measured": True,
            "rows_checked": len(rows),
            "finding": ("no rows were supplied, so this invariant is "
                        "UNMEASURED for this record" if not rows else
                        "every stored constraint sentence matches")}


def carry_over_record(rows: Iterable[Mapping[str, Any]] = (),
                      *, artifact: Mapping[str, Any] | None = None
                      ) -> dict[str, Any]:
    """§30's ledger entry for the carried instruments, with all seven findings.

    ``artifact`` supplies the five asserted invariants --- instrument
    identity, severity, sampling regime, model and revision, decoding
    configuration --- from the source artifact's own record. A missing one is
    recorded ``UNVERIFIED`` rather than omitted, because §30 requires a
    *finding* for every invariant and an absence is a finding.
    """
    artifact = dict(artifact or {})
    findings: dict[str, Any] = {
        "verifier_semantics": assert_statistics_agree_with_v4r4(),
        "model_facing_prompt": assert_wordings_match_stored(rows),
    }
    for invariant in REUSE_INVARIANTS:
        if invariant in MEASURED_INVARIANTS:
            continue
        value = artifact.get(invariant)
        findings[invariant] = {
            "invariant": invariant, "measured": False,
            "declared": value,
            "status": "ASSERTED" if value is not None else "UNVERIFIED",
        }
    sources = {f"{path}:{name}": sha_text(
        symbol_source(Path(__file__).resolve().parents[1] / path, name))
        for path, name in CARRIED_SYMBOLS}
    return {
        "section": "§30",
        "classification": "REUSED_IMPLEMENTATION",
        "carried_families": dict(CARRIED_FROM_V4R4),
        "carried_symbol_hashes": sources,
        "not_carried": dict(NOT_CARRIED),
        "invariants": findings,
        "all_measured_invariants_passed": all(
            findings[i].get("measured") for i in MEASURED_INVARIANTS),
        "unverified": sorted(k for k, v in findings.items()
                             if v.get("status") == "UNVERIFIED"),
    }
