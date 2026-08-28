"""§30's v6 -> v7 reuse ledger, as executable state.

Every artifact entering v7 from an earlier revision carries **exactly one**
classification, together with its source path, its source hash, the reason
reuse is scientifically valid, and the v7 criterion it satisfies.

**v6 closed without confirmatory data, and that changes what may be reused.**
v6 registered on 2026-08-26 and every replication reached a §28 terminal
status by 2026-08-27: two ``COMPOSED_HEADROOM_UNREACHABLE`` at Gate 2.75,
one ``COMPOSED_HEADROOM_FAILURE`` at Gate 4, one ``PREFREEZE_AUDIT_FAILURE``
after the preregistration was amended under it. There is no ``Delta_R``,
``Delta_j`` or ``Xi`` estimate to carry. What v6 supplies v7 is **historical
outcomes** --- the four terminations, read as what they are under v6's rule
--- and **development evidence about the mechanism** that produced two of
them: the composed compliance of B under A on two replications, which is the
measurement v7's design responds to.

| Class | Meaning |
|---|---|
| ``HISTORICAL_OUTCOME`` | a v6 or earlier scientific result. Preserved, cited for provenance, **never** presented as a v7 observation and never re-analysed |
| ``DEVELOPMENT_EVIDENCE`` | a v6 measurement used to choose a v7 rule |
| ``REUSED_IMPLEMENTATION`` | source carried byte-identically, with a carry-over record |
| ``RECOMPUTED_DIAGNOSTIC`` | a quantity computed for v7's design from v6 raw rows with a registered v6 verifier |
| ``NEW_V7_EVIDENCE`` | produced under this protocol |

**Two rules this module enforces rather than states.**

1. **No v6 generation is carried into a v7 estimand.** ``assert_not_estimand_input``
   refuses any classification other than ``NEW_V7_EVIDENCE`` on the path where
   an analysis input is admitted, so a development table cannot reach an
   estimator by being handed to the wrong function. v7 re-runs its
   pre-composed stages under its own seeds rather than carrying v6's records.
2. **Retrospective performance is never called validation.** §30 and §33 check
   15 say the word must not be applied to any retrospective analysis, and
   ``assert_no_validation_language`` is the text check the pre-freeze audit
   runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_file

from dci1v7.protocol import constants as C

__all__ = ["CLASSIFICATIONS", "LedgerEntry", "REGISTERED_ENTRIES",
           "build_ledger", "assert_not_estimand_input",
           "assert_no_validation_language", "FORBIDDEN_PHRASES",
           "ARTIFACT_TEXT_GLOBS", "collect_artifact_texts",
           "ESTIMAND_ADMISSIBLE"]

CLASSIFICATIONS = C.REUSE_CLASSIFICATIONS
#: The one classification an analysis input may carry.
ESTIMAND_ADMISSIBLE = ("NEW_V7_EVIDENCE",)

#: §33 check 15 and §30. A retrospective analysis is **design fitting**;
#: calling it validation is the specific overclaim v5 exists to avoid making.
FORBIDDEN_PHRASES = (
    "retrospective validation", "validated on v4r4", "validates the rule",
    "prospective support from v4r4", "v4r4 validates", "replicated on v4r4",
    "validation on the predecessor", "validated retrospectively",
    "validated on v5", "prospective support from v5", "v5 validates",
    "replicated on v5",
    "validated on v6", "prospective support from v6", "v6 validates",
    "replicated on v6",
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
        "dci1/evidence/dci1v6/*/terminal_report.json",
        "HISTORICAL_OUTCOME",
        "v6's four terminal statuses are that study's results under that "
        "study's registered rules: COMPOSED_HEADROOM_UNREACHABLE on both "
        "Qwen replications, COMPOSED_HEADROOM_FAILURE on gemma-3n-e4b-it, "
        "PREFREEZE_AUDIT_FAILURE on gemma-3n-e2b-it. v7 neither re-analyses, "
        "re-labels nor re-verdicts them; withdrawing the criterion "
        "prospectively does not lift a verdict reached under it",
        "§30.2: never presented as a v7 observation",
        notes="v6 reached CONFIRMATORY_GENERATION on no replication, so "
              "there is no Delta_R, Delta_j or Xi estimate to carry at all"),
    LedgerEntry(
        "dci1/reports/dci1v6/closure.json",
        "HISTORICAL_OUTCOME",
        "the v6 study-level closure record: survivor count zero and the "
        "four terminal statuses, read from signed records",
        "§30.2"),
    LedgerEntry(
        "dci1/evidence/dci1v6/*/GATE_2_75_COMPOSED_PROBE",
        "DEVELOPMENT_EVIDENCE",
        "the four signed probe records are the measurement v7 responds to: "
        "B's compliance under A rose from its solo value toward the ceiling "
        "on both Qwen replications (0.747 -> 0.891, 0.779 -> 0.924) and the "
        "projected-interval verdict ended them. They measure what a "
        "boundary DOES to the arm the estimand differences, and no effect "
        "quantity is estimated from them",
        "§12.5 and §30.1: development data for the design of the "
        "preregistration, a permission that expires at adoption"),
    LedgerEntry(
        "dci1/evidence/dci1v6/*/GATE_4_COMPOSED_CONTRAST",
        "DEVELOPMENT_EVIDENCE",
        "gemma-3n-e2b-it's Gate-4 table (8 cell types, base and class arms) "
        "and gemma-3n-e4b-it's retained rows, on which the v5/v6 criterion "
        "fired on solo:CL = 0.958 --- a companion's own solo compliance, a "
        "quantity that enters no primary estimand",
        "§30.1: the design-fitting declaration, attached permanently",
        notes="the v6 stage directory is GATE_4_COMPOSED_HEADROOM; the glob "
              "names the v7 stage id for the ledger's own consistency check "
              "and resolves nothing on disk"),
    LedgerEntry(
        "dci1/evidence/dci1v6/*/GATE_3C_IDENTIFICATION",
        "DEVELOPMENT_EVIDENCE",
        "both Gemma replications recorded REFERENCE_SUPPORT_NOT_IDENTIFIED "
        "at Gate 3C under the calibrated coverage re-read, so no v6 "
        "replication reached Gate 4 with a core arm. Withdrawing the "
        "headroom criterion opens nothing for them; it is why v7's "
        "changelog says so",
        "§30.1"),
    LedgerEntry(
        "dci1/src/dci1v6",
        "REUSED_IMPLEMENTATION",
        "v7's package is v6's implementation carried into its own namespace "
        "with the changes `protocol/revision.py` enumerates and checks. "
        "Everything not listed there is carried unchanged, including every "
        "verifier predicate, every admission threshold and the whole claim "
        "ladder; the estimand layer is compared byte for byte",
        "§10.2's carry-over condition, and §30's requirement that a carried "
        "implementation records a finding for every registered invariant",
        measured_invariants=("verifier_semantics", "model_facing_prompt")),
    LedgerEntry(
        "dci1/src/dci1v4r4/verifiers/words.py",
        "REUSED_IMPLEMENTATION",
        "the segmentation rule and its U+0130 correction are carried "
        "unchanged through v5 and v6; v7 reopens nothing about how a word "
        "is found",
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
            "v7 was designed AFTER observing the closed v6 study in full, "
            "including its four terminal statuses and the probe and Gate-4 "
            "tables that produced three of them. That is design fitting, "
            "of the rule rather than of any number. The withdrawal of the "
            "composed-headroom criterion is a response to those outcomes and "
            "is declared as one under §32.2; it is a loosening relative to "
            "v6 with respect to what ends a replication, and the reason it "
            "is adoptable is that it withdraws a criterion on a marginal "
            "rate in favour of readings of the contrast the study estimates "
            "--- it does not move any threshold. Retrospective performance "
            "on v6 is NOT prospective validation, and v7 is the prospective "
            "test. v6 reached CONFIRMATORY_GENERATION on no replication, so "
            "no effect estimate is carried and no terminal status is read as "
            "a null result."),
        "no_v6_generation_in_a_v7_estimand": True,
    }


def assert_not_estimand_input(classification: str, *, where: str) -> None:
    """§30 and §14.2: only ``NEW_V7_EVIDENCE`` may reach an estimator."""
    if classification not in CLASSIFICATIONS:
        raise ProtocolError(
            f"{where}: {classification!r} is not a registered §30 "
            f"classification")
    if classification not in ESTIMAND_ADMISSIBLE:
        raise ProtocolError(
            f"{where}: an input classified {classification} may never enter a "
            "v7 estimand. v6's rows exist for v7 only as HISTORICAL_OUTCOME "
            "and DEVELOPMENT_EVIDENCE, and §14.2's admission guard is a "
            "positive rule: an input must prove it belongs to the v7 study "
            "tree")


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
    "user-notes/DCI1_preregistration_v7.md",
    "dci1/reports/dci1v7/*.md",
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
