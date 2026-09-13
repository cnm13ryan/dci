"""§30's v5 -> v6 reuse ledger, as executable state.

Every artifact entering v6 from an earlier revision carries **exactly one**
classification, together with its source path, its source hash, the reason
reuse is scientifically valid, and the v6 criterion it satisfies.

**v5 closed without confirmatory data, and that changes what may be reused.**
v5 generated 459,312 live rows and reached ``CONFIRMATORY_GENERATION`` on no
replication; three replications are irreversibly D6
``REFERENCE_SUPPORT_NOT_IDENTIFIED`` and one terminated
``COMPOSED_HEADROOM_FAILURE``. There is no ``Delta_R``, ``Delta_j`` or ``Xi``
estimate to carry, and ``NOT_IDENTIFIED`` is never read as a null result. What
v5 supplies v6 is **development evidence about mechanisms** --- survival,
identification, headroom, and two defects in §12.6's expansion --- and nothing
else.

| Class | Meaning |
|---|---|
| ``HISTORICAL_OUTCOME`` | a v4r4 scientific result. Preserved, cited for provenance, **never** presented as a v5 observation and never re-analysed |
| ``DEVELOPMENT_EVIDENCE`` | a v4r4 measurement used to choose a v5 rule |
| ``REUSED_IMPLEMENTATION`` | source carried byte-identically, with a carry-over record |
| ``RECOMPUTED_DIAGNOSTIC`` | a quantity computed for v5's design from v4r4 raw rows with a registered v4r4 verifier |
| ``NEW_V6_EVIDENCE`` | produced under this protocol |

**Two rules this module enforces rather than states.**

1. **No v5 generation is carried into a v6 estimand.** ``assert_not_estimand_input``
   refuses any classification other than ``NEW_V6_EVIDENCE`` on the path where
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

from dci1v6.protocol import constants as C

__all__ = ["CLASSIFICATIONS", "LedgerEntry", "REGISTERED_ENTRIES",
           "build_ledger", "assert_not_estimand_input",
           "assert_no_validation_language", "FORBIDDEN_PHRASES",
           "ARTIFACT_TEXT_GLOBS", "collect_artifact_texts",
           "ESTIMAND_ADMISSIBLE"]

CLASSIFICATIONS = C.REUSE_CLASSIFICATIONS
#: The one classification an analysis input may carry.
ESTIMAND_ADMISSIBLE = ("NEW_V6_EVIDENCE",)

#: §33 check 15 and §30. A retrospective analysis is **design fitting**;
#: calling it validation is the specific overclaim v5 exists to avoid making.
FORBIDDEN_PHRASES = (
    "retrospective validation", "validated on v4r4", "validates the rule",
    "prospective support from v4r4", "v4r4 validates", "replicated on v4r4",
    "validation on the predecessor", "validated retrospectively",
    "validated on v5", "prospective support from v5", "v5 validates",
    "replicated on v5",
)


@dataclass(frozen=True)
class LedgerEntry:
    """One reused artifact, with everything §30 requires of it."""

    source: str
    classification: str
    why_valid: str
    v6_criterion: str
    source_hash: str | None = None
    measured_invariants: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self):
        if self.classification not in CLASSIFICATIONS:
            raise ProtocolError(
                f"{self.source}: {self.classification!r} is not a registered "
                f"§30 classification; registered: {CLASSIFICATIONS}")
        if not self.why_valid or not self.v6_criterion:
            raise ProtocolError(
                f"{self.source}: §30 requires the reason reuse is "
                "scientifically valid and the v6 criterion it satisfies; an "
                "entry without both is a citation, not a ledger entry")
        if self.classification == "REUSED_IMPLEMENTATION" and \
                not self.measured_invariants:
            raise ProtocolError(
                f"{self.source}: a REUSED_IMPLEMENTATION entry records a "
                "finding for all seven registered invariants and **measures** "
                "two of them (§30); this entry measures none")

    def as_dict(self) -> dict[str, Any]:
        return {"source": self.source, "classification": self.classification,
                "why_valid": self.why_valid, "v6_criterion": self.v6_criterion,
                "source_hash": self.source_hash,
                "measured_invariants": list(self.measured_invariants),
                "notes": self.notes}


#: The entries v6 registers before any run. Paths are repository-relative and
#: are hashed by ``build_ledger`` where they exist.
#:
#: **v5's own reuse of v4r4 is not repeated here.** v6 supersedes v5 and v5
#: supersedes v4r4; what v6 carries from v4r4 it carries *through* v5's
#: implementation, and v5's ledger records that chain. What is registered
#: below is what enters v6 directly.
REGISTERED_ENTRIES: tuple[LedgerEntry, ...] = (
    LedgerEntry(
        "dci1/evidence/dci1v5/*/terminal_report.json",
        "HISTORICAL_OUTCOME",
        "v5's four terminal statuses are that study's results under that "
        "study's registered rules. Three are irreversibly D6 "
        "REFERENCE_SUPPORT_NOT_IDENTIFIED and one is "
        "COMPOSED_HEADROOM_FAILURE; v6 neither re-analyses, re-labels nor "
        "re-verdicts them, and NOT_IDENTIFIED is never read as a null result",
        "§30.2: never presented as a v6 observation",
        notes="v5 reached CONFIRMATORY_GENERATION on no replication, so "
              "there is no Delta_R, Delta_j or Xi estimate to carry at all"),
    LedgerEntry(
        "dci1/evidence/dci1v5/*/REGIME_SCREEN",
        "DEVELOPMENT_EVIDENCE",
        "the four signed pre-screen tables are what V6-E01 and V6-E02 were "
        "found on, and what `tools/v6_expansion_dryrun.py` replays both "
        "expansion rules over. They measure the MECHANISM --- which rungs a "
        "rule can reach and which rows a criterion sees --- and no effect "
        "quantity is estimated from them",
        "§12.5: development data for the design of the preregistration, a "
        "permission that expires at adoption"),
    LedgerEntry(
        "dci1/evidence/dci1v5/*/GATE_2_FOCAL_CALIBRATION",
        "DEVELOPMENT_EVIDENCE",
        "the solo curves at m* are what the composed-headroom decomposition "
        "in `reports/dci1v6/readiness_evidence.json` is taken from: "
        "calibration solo, split transfer, composition term. They are why a "
        "Gate-2.75 probe is proposed at all",
        "§12.5, and §30.1's declaration that anything fitted to them is "
        "prospectively tested by v6 and not established by it"),
    LedgerEntry(
        "dci1/evidence/dci1v5/*/GATE_4_COMPOSED_HEADROOM",
        "DEVELOPMENT_EVIDENCE",
        "the realised §13.14 tables are what the delta sensitivity in "
        "READINESS §4.b is computed on. Two replications raised before "
        "writing a record and their tables are recomputed from retained "
        "scored rows by the runner's own rule, validated against the two "
        "signed records and the two signed terminal reports",
        "§30.1: the design-fitting declaration, attached permanently"),
    LedgerEntry(
        "dci1/reports/dci1v6/readiness_evidence.json",
        "RECOMPUTED_DIAGNOSTIC",
        "every non-constant number in READINESS.md, computed from signed v5 "
        "records whose hash and signature are verified on read; the tool "
        "aborts unless its recomputations reproduce every signed value",
        "§30: a quantity computed for v6's design from v5 raw rows with the "
        "registered v5 verifiers"),
    LedgerEntry(
        "dci1/reports/dci1v6/expansion_dryrun.json",
        "RECOMPUTED_DIAGNOSTIC",
        "V6-E01 and V6-E02, replayed on the four signed pre-screen tables. "
        "The `qwen3-4b` row --- decisive_met True over the full measured "
        "table where the signed record says False --- is evidence about the "
        "v5 IMPLEMENTATION and is not a re-verdict; D6 is irreversible and "
        "v5's outcome stands",
        "§30: a diagnostic recomputed for v6's design, never a v5 result"),
    LedgerEntry(
        "dci1/src/dci1v5",
        "REUSED_IMPLEMENTATION",
        "v6's package is v5's implementation carried into its own namespace "
        "with the changes `protocol/revision.py` enumerates and checks. "
        "Everything not listed there is carried unchanged, including every "
        "verifier predicate, every threshold and the whole claim ladder",
        "§10.2's carry-over condition, and §30's requirement that a carried "
        "implementation records a finding for every registered invariant",
        measured_invariants=("verifier_semantics", "model_facing_prompt")),
    LedgerEntry(
        "dci1/src/dci1v4r4/verifiers/words.py",
        "REUSED_IMPLEMENTATION",
        "the segmentation rule and its U+0130 correction are carried "
        "unchanged through v5; v6 reopens nothing about how a word is found",
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
            "v6 was designed AFTER observing the closed v5 study in full, "
            "including its four terminal statuses, its coverage tables, its "
            "Gate-4 headroom and two defects in its own expansion rule. Its "
            "expansion repair, its probe and its margin are all chosen "
            "against what v5 measured. That is design fitting. Retrospective "
            "performance on v5 is NOT prospective validation, and v6 is the "
            "prospective test. v5 reached CONFIRMATORY_GENERATION on no "
            "replication, so no effect estimate is carried and no "
            "NOT_IDENTIFIED verdict is read as a null result."),
        "no_v5_generation_in_a_v6_estimand": True,
    }


def assert_not_estimand_input(classification: str, *, where: str) -> None:
    """§30 and §14.2: only ``NEW_V6_EVIDENCE`` may reach an estimator."""
    if classification not in CLASSIFICATIONS:
        raise ProtocolError(
            f"{where}: {classification!r} is not a registered §30 "
            f"classification")
    if classification not in ESTIMAND_ADMISSIBLE:
        raise ProtocolError(
            f"{where}: an input classified {classification} may never enter a "
            "v6 estimand. v5's 459,312 rows exist for v6 only as "
            "DEVELOPMENT_EVIDENCE and RECOMPUTED_DIAGNOSTIC, and §14.2's "
            "admission guard is a positive rule: an input must prove it "
            "belongs to the v6 study tree")


#: The v5 artifacts §33 check 15 scans. Naming them here gives the check a
#: **producer**: an earlier revision left ``artifact_texts`` at ``None`` and
#: the check reported UNRESOLVED at every stage that ran it, which is a check
#: that never actually ran. These exist from stage 1 onward, so check 15 is
#: discharged at ``PREFREEZE_AUDIT`` as §33 states, and re-run at
#: ``FINAL_REPORT`` over the report text that did not exist before.
#: v5 listed a separate ``DCI1_v4r4_to_v5_changelog.md`` here. v6 does not
#: have one and does not need one: its changes are enumerated in
#: ``protocol/revision.py``, where the code can check that each was actually
#: made, and in the repository's ``CHANGES_SCIENTIFIC.md``. A second prose
#: list would be a third place to drift from.
ARTIFACT_TEXT_GLOBS: tuple[str, ...] = (
    "user-notes/DCI1_preregistration_v6.md",
    "dci1/reports/dci1v6/*.md",
)


def collect_artifact_texts(repo_root: Path | str = ".",
                           extra: Mapping[str, str] | None = None
                           ) -> dict[str, str]:
    """Every v5 artifact text on disk, by repository-relative path.

    A glob that matches nothing contributes nothing; a *named* file that is
    absent is not silently skipped, because §33 check 15 scanning zero texts
    and passing is exactly the failure mode this replaces.
    """
    root = Path(repo_root)
    out: dict[str, str] = {}
    for pattern in ARTIFACT_TEXT_GLOBS:
        if "*" in pattern:
            for path in sorted(root.glob(pattern)):
                out[str(path.relative_to(root))] = path.read_text()
            continue
        path = root / pattern
        if not path.is_file():
            raise ProtocolError(
                f"§33 check 15 scans {pattern} and it is not at {path}; a "
                "text check that silently scans nothing is not a check")
        out[pattern] = path.read_text()
    out.update(extra or {})
    return out


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
