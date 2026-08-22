"""§30's v4r4 -> v5 reuse ledger, as executable state.

Every artifact entering v5 from an earlier revision carries **exactly one**
classification, together with its source path, its source hash, the reason
reuse is scientifically valid, and the v5 criterion it satisfies.

| Class | Meaning |
|---|---|
| ``HISTORICAL_OUTCOME`` | a v4r4 scientific result. Preserved, cited for provenance, **never** presented as a v5 observation and never re-analysed |
| ``DEVELOPMENT_EVIDENCE`` | a v4r4 measurement used to choose a v5 rule |
| ``REUSED_IMPLEMENTATION`` | source carried byte-identically, with a carry-over record |
| ``RECOMPUTED_DIAGNOSTIC`` | a quantity computed for v5's design from v4r4 raw rows with a registered v4r4 verifier |
| ``NEW_V5_EVIDENCE`` | produced under this protocol |

**Two rules this module enforces rather than states.**

1. **No v4r4 generation is carried into a v5 estimand.** ``assert_not_estimand_input``
   refuses any classification other than ``NEW_V5_EVIDENCE`` on the path where
   an analysis input is admitted, so a development table cannot reach an
   estimator by being handed to the wrong function.
2. **Retrospective performance is never called validation.** §30 and §33 check
   15 say the word must not be applied to any retrospective analysis, and
   ``assert_no_validation_language`` is the text check the pre-freeze audit
   runs. It is here rather than in the audit because the sentence it refuses
   is a sentence *about this ledger*.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_file

from dci1v5.protocol import constants as C

__all__ = ["CLASSIFICATIONS", "LedgerEntry", "REGISTERED_ENTRIES",
           "build_ledger", "assert_not_estimand_input",
           "assert_no_validation_language", "FORBIDDEN_PHRASES",
           "ESTIMAND_ADMISSIBLE"]

CLASSIFICATIONS = C.REUSE_CLASSIFICATIONS
#: The one classification an analysis input may carry.
ESTIMAND_ADMISSIBLE = ("NEW_V5_EVIDENCE",)

#: §33 check 15 and §30. A retrospective analysis is **design fitting**;
#: calling it validation is the specific overclaim v5 exists to avoid making.
FORBIDDEN_PHRASES = (
    "retrospective validation", "validated on v4r4", "validates the rule",
    "prospective support from v4r4", "v4r4 validates", "replicated on v4r4",
    "validation on the predecessor", "validated retrospectively",
)


@dataclass(frozen=True)
class LedgerEntry:
    """One reused artifact, with everything §30 requires of it."""

    source: str
    classification: str
    why_valid: str
    v5_criterion: str
    source_hash: str | None = None
    measured_invariants: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self):
        if self.classification not in CLASSIFICATIONS:
            raise ProtocolError(
                f"{self.source}: {self.classification!r} is not a registered "
                f"§30 classification; registered: {CLASSIFICATIONS}")
        if not self.why_valid or not self.v5_criterion:
            raise ProtocolError(
                f"{self.source}: §30 requires the reason reuse is "
                "scientifically valid and the v5 criterion it satisfies; an "
                "entry without both is a citation, not a ledger entry")
        if self.classification == "REUSED_IMPLEMENTATION" and \
                not self.measured_invariants:
            raise ProtocolError(
                f"{self.source}: a REUSED_IMPLEMENTATION entry records a "
                "finding for all seven registered invariants and **measures** "
                "two of them (§30); this entry measures none")

    def as_dict(self) -> dict[str, Any]:
        return {"source": self.source, "classification": self.classification,
                "why_valid": self.why_valid, "v5_criterion": self.v5_criterion,
                "source_hash": self.source_hash,
                "measured_invariants": list(self.measured_invariants),
                "notes": self.notes}


#: The entries v5 registers before any run. Paths are repository-relative and
#: are hashed by ``build_ledger`` where they exist.
REGISTERED_ENTRIES: tuple[LedgerEntry, ...] = (
    LedgerEntry(
        "dci1/evidence/dci1v4r4/*/UNMASKED_ANALYSIS",
        "HISTORICAL_OUTCOME",
        "v4r4's D, Lambda and Delta_class are that study's results under that "
        "study's registered rules; v5 neither re-analyses nor re-labels them",
        "§30.2: never presented as a v5 observation",
        notes="both terminal reports are historical outcomes too, and "
              "COMPOSED_HEADROOM_FAILURE remains their outcome under v4r4's "
              "rules"),
    LedgerEntry(
        "dci1/evidence/dci1v4r4/*/GATE_2_REGIME",
        "DEVELOPMENT_EVIDENCE",
        "the Gate-2 calibration tables were used to choose §13.4's chance "
        "ceiling, §13.7's equivalence bound and §13.8's caliper justification",
        "§12.5: development data for the design of the preregistration, a "
        "permission that expires at adoption"),
    LedgerEntry(
        "dci1/evidence/dci1v4r4/gemma-3n-e2b-it/GATE_4_COMPOSED_HEADROOM",
        "DEVELOPMENT_EVIDENCE",
        "the only v4r4 replication that ever composed a reference with B; its "
        "twenty composed rate checks are what §13.6's projection was fitted "
        "to, on ONE model, which §30.1 declares as design fitting",
        "§30.1: the overfitting declaration, attached permanently"),
    LedgerEntry(
        "dci1/reports/dci1v5/development/d2_kappa_under_b.json",
        "RECOMPUTED_DIAGNOSTIC",
        "kappa(R|B) did not exist in v4r4's records because its calibration "
        "scored load-one rows on the present instance only; it was recomputed "
        "from stored raw responses with the registered v4r4 verifiers",
        "§9.1: the presence rule v5 makes mandatory at every generative stage"),
    LedgerEntry(
        "dci1/reports/dci1v5/development/d3_split_half_stability.json",
        "RECOMPUTED_DIAGNOSTIC",
        "the split-half figures were computed for v5's design from v4r4 rows",
        "§13.7: the equivalence bound's derivation"),
    LedgerEntry(
        "dci1/src/dci1v4r4/verifiers/statistics.py",
        "REUSED_IMPLEMENTATION",
        "fourteen non-marker numerators and marker_thus are carried; "
        "verifiers/carryover.py runs both revisions' predicates over the "
        "whole frozen corpus and refuses on any disagreement",
        "§10.2's carry-over condition",
        measured_invariants=("verifier_semantics", "model_facing_prompt")),
    LedgerEntry(
        "dci1/src/dci1v4r4/verifiers/words.py",
        "REUSED_IMPLEMENTATION",
        "the segmentation rule and its U+0130 correction are carried "
        "unchanged; v5 reopens nothing about how a word is found",
        "§9.2's lexical rule",
        measured_invariants=("verifier_semantics",)),
)


def build_ledger(repo_root: Path | str = ".",
                 extra: Iterable[LedgerEntry] = ()) -> dict[str, Any]:
    """The §30 ledger, with a hash for every source that exists on disk.

    A registered source that is absent is recorded ``missing`` rather than
    dropped: §30 requires an entry per reused artifact, and an artifact the
    tree no longer holds is a finding about the tree.
    """
    root = Path(repo_root)
    entries = list(REGISTERED_ENTRIES) + list(extra)
    out: list[dict[str, Any]] = []
    for entry in entries:
        record = entry.as_dict()
        path = root / entry.source
        if "*" not in entry.source and path.is_file():
            record["source_hash"] = sha_file(path)
            record["present"] = True
        else:
            record["present"] = path.exists() if "*" not in entry.source \
                else None
        out.append(record)
    by_class: dict[str, int] = {}
    for record in out:
        by_class[record["classification"]] = \
            by_class.get(record["classification"], 0) + 1
    return {
        "section": "§30",
        "classifications": list(CLASSIFICATIONS),
        "entries": out,
        "counts": by_class,
        "declaration": (
            "v5 was designed AFTER observing the completed v4r4 study in "
            "full, including its Gate-4 tables, its confirmatory estimates, "
            "its two terminations and its L4 defect. Its matching rule was "
            "chosen because it separates v4r4's known failures from v4r4's "
            "known passes. That is design fitting. Retrospective performance "
            "on v4r4 is NOT prospective validation, and v5 is the "
            "prospective test."),
        "no_v4r4_generation_in_a_v5_estimand": True,
    }


def assert_not_estimand_input(classification: str, *, where: str) -> None:
    """§30 and §14.2: only ``NEW_V5_EVIDENCE`` may reach an estimator."""
    if classification not in CLASSIFICATIONS:
        raise ProtocolError(
            f"{where}: {classification!r} is not a registered §30 "
            f"classification")
    if classification not in ESTIMAND_ADMISSIBLE:
        raise ProtocolError(
            f"{where}: an input classified {classification} may never enter a "
            "v5 estimand. v4r4's rows exist for v5 only as "
            "DEVELOPMENT_EVIDENCE and RECOMPUTED_DIAGNOSTIC, and §14.2's "
            "admission guard is a positive rule: an input must prove it "
            "belongs to the v5 study tree")


def assert_no_validation_language(texts: Mapping[str, str] | Sequence[tuple],
                                  *, where: str = "§33 check 15"
                                  ) -> dict[str, Any]:
    """§33 check 15: the word "validation" is not applied retrospectively.

    ``texts`` maps a label (a path, usually) to the text to scan. The check is
    on **phrases**, not on the bare word: v5's artifacts must be able to say
    "deterministic_measurement_validated", which is a registered measurement
    basis, and "the reimplementation validated the segmenter", which is a
    Gate-1 fact. What they must not say is that v4r4 validated v5's rule.
    """
    items = (texts.items() if isinstance(texts, Mapping) else list(texts))
    offences: list[dict[str, str]] = []
    for label, text in items:
        lowered = str(text).lower()
        for phrase in FORBIDDEN_PHRASES:
            index = lowered.find(phrase)
            if index >= 0:
                offences.append({
                    "where": str(label), "phrase": phrase,
                    "context": str(text)[max(0, index - 60):index + 90]})
    if offences:
        raise ProtocolError(
            f"{where}: retrospective performance on v4r4 is design fitting "
            f"and no v5 artifact may describe it as validation; found "
            f"{offences[:3]}")
    return {"check": where, "scanned": len(items),
            "phrases": list(FORBIDDEN_PHRASES), "offences": 0}
