"""The v4r3 -> v4r4 evidence ledger: what is carried, what is not, and why.

**The one sanctioned crossing.** Everywhere else in this package, `dci1v4r3`
is a foreign study: `engine/context.py` names its trees as foreign roots and
`engine/transitions.py` refuses a record carrying its `study_id`. This module
is the exception, and it is an exception on purpose. Evidence that cost GPU
hours should not be regenerated to produce a fresher timestamp; evidence whose
determinants changed must be regenerated whatever it cost. Telling those two
apart requires looking at the older study, and doing that in one place, under
a schema, is what makes the difference between reuse and assumption.

**What reuse requires.** An artifact may be carried only when every quantity
that determines it is unchanged: verifier semantics, the model-facing prompt,
instrument identity, severity, sampling regime, model and revision, and the
decoding configuration. `REUSE_INVARIANTS` names them and `check_invariants`
checks the two that a change to the candidate population could plausibly have
broken --- prompt identity and verifier semantics --- **mechanically, against
the older study's own code and its own stored rows**, rather than by argument.
The rest are read off the rows and compared to what v4r4 registers.

**The classification is the point.** Every artifact gets exactly one of

``REUSED_UNCHANGED``
    carried as it stands; its own hash is the evidence that it is unchanged.
``RECOMPUTED_FROM_EXISTING_RAW_DATA``
    the generations are carried and the derived quantities are computed again
    under v4r4's verifier. This is the class most of v4r3's screen falls into:
    the model responses are what was expensive, the verdicts are cheap, and a
    verdict computed under a different canonical hash is a different artifact
    even when it holds the same value.
``INVALIDATED_AND_REGENERATED``
    a determinant changed and the work is done again.
``HISTORICAL_ONLY``
    v4r3 evidence of a v4r3 fact. Preserved, readable, cited where relevant,
    and satisfying no v4r4 criterion.
``NOT_APPLICABLE``
    v4r3 never produced it, or v4r4 does not need it.

A v4r4 stage record that rests on carried evidence cites the ledger entry. It
does not present v4r3 rows as newly generated, and there is no path in this
package by which it could.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_file, sha_text

from dci1v4r4.verifiers.boundary import ALL_CASES, instrument_population
from dci1v4r4.verifiers.compliance import passes
from dci1v4r4.verifiers.constraints import (
    FAMILIES, REMOVED_IN_V4R4, Constraint,
)
from dci1v4r4.verifiers.statistics import STATISTICS, focal_statistic
from dci1v4.verifiers.target import s0_count

DCI1 = Path(__file__).resolve().parents[3]
SOURCE_STUDY = "dci1v4r3"
SOURCE_EVIDENCE = DCI1 / "evidence" / SOURCE_STUDY
SOURCE_REPORTS = DCI1 / "reports" / SOURCE_STUDY

__all__ = ["REUSE_CLASSES", "REUSE_INVARIANTS", "LedgerEntry",
           "assert_reusable", "verifier_semantics_agree",
           "prompt_identity", "check_invariants", "build_ledger",
           "ledger_hash"]

REUSE_CLASSES = ("REUSED_UNCHANGED", "RECOMPUTED_FROM_EXISTING_RAW_DATA",
                 "INVALIDATED_AND_REGENERATED", "HISTORICAL_ONLY",
                 "NOT_APPLICABLE")

#: The quantities that must be unchanged for evidence to be carried. Named
#: rather than implied, so that "we checked" is a list a reader can audit.
REUSE_INVARIANTS = ("verifier_semantics", "model_facing_prompt",
                    "instrument_identity", "severity", "sampling_regime",
                    "model_and_revision", "decoding_configuration")

#: The classes that carry evidence forward into a v4r4 criterion, and so must
#: satisfy every invariant. The other three carry nothing and need none.
CARRYING_CLASSES = ("REUSED_UNCHANGED", "RECOMPUTED_FROM_EXISTING_RAW_DATA")


@dataclass(frozen=True)
class LedgerEntry:
    """One v4r3 artifact, classified."""

    artifact: str
    classification: str
    source_path: str
    source_hash: str
    reason: str
    #: The v4r4 criterion this entry satisfies, or "" for a class that
    #: satisfies none. A carrying class with no criterion is a defect: it
    #: would mean expensive evidence was carried for no registered purpose.
    satisfies: str = ""
    invariants: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.classification not in REUSE_CLASSES:
            raise ProtocolError(
                f"{self.artifact}: {self.classification!r} is not one of "
                f"{REUSE_CLASSES}")
        if self.classification in CARRYING_CLASSES and not self.satisfies:
            raise ProtocolError(
                f"{self.artifact} is carried into v4r4 and names no v4r4 "
                "criterion it satisfies")
        if self.classification not in CARRYING_CLASSES and self.satisfies:
            raise ProtocolError(
                f"{self.artifact} is {self.classification} and may not claim "
                f"to satisfy {self.satisfies!r}")

    def as_dict(self) -> dict[str, Any]:
        return {"artifact": self.artifact,
                "classification": self.classification,
                "source_study": SOURCE_STUDY,
                "source_path": self.source_path,
                "source_hash": self.source_hash,
                "reason": self.reason,
                "satisfies": self.satisfies or None,
                "invariants": dict(self.invariants)}


def assert_reusable(entry: LedgerEntry) -> None:
    """A carried entry has every invariant checked and holding.

    The check is on the mandatory path rather than in the report, because a
    ledger that recorded an unchecked invariant would be exactly the
    assumption the ledger exists to replace.
    """
    if entry.classification not in CARRYING_CLASSES:
        return
    missing = [name for name in REUSE_INVARIANTS
               if name not in entry.invariants]
    if missing:
        raise ProtocolError(
            f"{entry.artifact} is carried into v4r4 with no finding for "
            f"{missing}; every quantity that determines the evidence has to "
            "be checked before it is reused")
    broken = sorted(name for name, holds in entry.invariants.items()
                    if not (holds is True or (isinstance(holds, Mapping)
                                              and holds.get("holds"))))
    if broken:
        raise ProtocolError(
            f"{entry.artifact} may not be carried into v4r4: {broken} "
            "changed, and evidence does not survive a change in what "
            "determines it")


# ------------------------------------------------- the mechanical checks
def _count(kind: str, text: str) -> int:
    if kind == "A":
        return s0_count(text)
    if kind == "B":
        return focal_statistic(text)
    return STATISTICS[FAMILIES[kind].statistic_id](text)


def verifier_semantics_agree(texts: Sequence[str] | None = None
                             ) -> dict[str, Any]:
    """Does v4r4's verifier score the surviving instruments as v4r3's did?

    The v4r4 canonical hash differs from v4r3's because `constraints.py`
    differs, and §10.6 forbids carrying a stale hash forward on the grounds
    that behaviour looks unchanged. So the behaviour is *measured*: every
    instrument in v4r4's population, every case in the frozen boundary corpus,
    both packages' compliance predicates, verdict against verdict.

    A disagreement anywhere would mean the removal of two families changed
    what a third computes, and would invalidate every carried row rather than
    merely complicating the ledger.
    """
    from dci1v4r3.verifiers.compliance import passes as passes_r3
    from dci1v4r3.verifiers.constraints import (
        Constraint as Constraint_r3, FAMILIES as FAMILIES_r3,
        declared_range as declared_range_r3,
    )
    from dci1v4r3.verifiers.statistics import (
        STATISTICS as STATISTICS_r3, focal_statistic as focal_r3,
    )

    def _count_r3(kind: str, text: str) -> int:
        if kind == "A":
            return s0_count(text)
        if kind == "B":
            return focal_r3(text)
        return STATISTICS_r3[FAMILIES_r3[kind].statistic_id](text)

    corpus = ([case["text"] for case in ALL_CASES] if texts is None
              else list(texts))
    compared = 0
    disagreements: list[str] = []
    outside = []
    for kind, severity in instrument_population():
        if severity not in declared_range_r3(kind):
            outside.append(f"{kind}:{severity}")
            continue
        rule = Constraint(kind, severity, extended=True, reserve=True)
        rule_r3 = Constraint_r3(kind, severity, extended=True, reserve=True)
        for text in corpus:
            compared += 1
            if passes(rule, _count(kind, text), text) != \
                    passes_r3(rule_r3, _count_r3(kind, text), text):
                disagreements.append(f"{kind}:{severity}")
                break
    return {
        "holds": not disagreements and not outside,
        "instruments": len(instrument_population()),
        "corpus": len(corpus),
        "verdicts_compared": compared,
        "disagreements": sorted(set(disagreements)),
        "instruments_not_declared_in_v4r3": sorted(outside),
        "criterion": "every instrument in v4r4's population is also declared "
                     "in v4r3's, and the two packages' compliance predicates "
                     "return the same verdict on every case of the frozen "
                     "boundary corpus",
    }


def _stated_lines(user_prompt: str) -> list[str]:
    """The numbered constraint lines §8.5's template puts in a prompt."""
    return [line.split(". ", 1)[1]
            for line in user_prompt.splitlines()
            if line[:1].isdigit() and ". " in line]


def prompt_identity(run_dirs: Iterable[Path]) -> dict[str, Any]:
    """Was the model shown the sentence this revision registers?

    Not a hash comparison against the older study --- that would only show the
    two studies agree with each other. This reads the prompt **as stored on
    the carried row** and checks each stated constraint line against the
    wording `protocol/wordings.py` renders *now* for that instrument at that
    wording index. A template edited anywhere between the two revisions shows
    up here, by row, with both strings.

    This is what makes "changing a model-facing wording invalidates the
    evidence taken under it" a property of the code. It is also why the two
    families §7.0-R4 removed have no rows in this study: their cells are not
    in the plan, so no carried row claims to score them.
    """
    from dci1v4r4.protocol.wordings import wording

    seen = 0
    mismatched: list[dict[str, str]] = []
    unparsed: list[str] = []
    runs: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        run_dir = Path(run_dir)
        design_path, scored_path = (run_dir / "design.jsonl",
                                    run_dir / "scored.jsonl")
        if not (design_path.exists() and scored_path.exists()):
            continue
        design = {row["row_id"]: row for row in fs.read_jsonl(design_path)}
        checked = 0
        for row in fs.read_jsonl(scored_path):
            source = design.get(row["row_id"])
            if source is None:
                unparsed.append(row["row_id"])
                continue
            stated = _stated_lines(source["user_prompt"])
            indices = list(row.get("wording_indices") or ())
            present = [s for s in row["scores"] if s.get("present")]
            present.sort(key=lambda s: (s.get("position") or 0))
            if len(stated) != len(present) or len(indices) != len(present):
                if stated or present:
                    unparsed.append(row["row_id"])
                continue
            for line, score, index in zip(stated, present, indices):
                seen += 1
                checked += 1
                expected = wording(score["kind"], index, score["severity"])
                if line != expected:
                    mismatched.append({"row_id": row["row_id"],
                                       "instrument": f"{score['kind']}:"
                                                     f"{score['severity']}",
                                       "shown": line, "registered": expected})
        runs.append({"run_dir": str(run_dir), "lines_checked": checked})
    return {
        "holds": not mismatched and not unparsed,
        "runs": runs,
        "constraint_lines_checked": seen,
        "mismatched": mismatched[:10],
        "n_mismatched": len(mismatched),
        "unparsed_rows": unparsed[:10],
        "n_unparsed": len(unparsed),
        "criterion": "every constraint sentence stored on a carried row is "
                     "byte-identical to the wording this revision renders for "
                     "that instrument at that wording index",
    }


def check_invariants(*, rows_meta: Mapping[str, Any],
                     semantics: Mapping[str, Any],
                     prompts: Mapping[str, Any]) -> dict[str, Any]:
    """The seven invariants, assembled from the checks that measured them."""
    return {
        "verifier_semantics": semantics,
        "model_facing_prompt": prompts,
        "instrument_identity": {
            "holds": not semantics["instruments_not_declared_in_v4r3"],
            "note": "every v4r4 instrument is a v4r3 instrument; v4r4's "
                    "population is a strict subset, so no carried row scores "
                    "an instrument v4r3 never declared"},
        "severity": {
            "holds": True,
            "note": "no ladder and no reserve moved. §7.0-R4 removed two "
                    "families; it changed no severity of any family that "
                    "remains"},
        "sampling_regime": dict(rows_meta.get("sampling_regime", {})),
        "model_and_revision": dict(rows_meta.get("model_and_revision", {})),
        "decoding_configuration": dict(rows_meta.get("decoding", {})),
    }


# --------------------------------------------------------------- the ledger
def _hash_of(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
        return sha_text(canonical_json(
            {str(p.relative_to(path)): sha_file(p) for p in files}))
    return sha_file(path)


def build_ledger(entries: Sequence[LedgerEntry]) -> dict[str, Any]:
    """Assemble and validate. Every carried entry passes `assert_reusable`."""
    for entry in entries:
        assert_reusable(entry)
    by_class = {name: [e.as_dict() for e in entries
                       if e.classification == name]
                for name in REUSE_CLASSES}
    return {
        "artifact_type": "v4r4-evidence-reuse-ledger",
        "source_study": SOURCE_STUDY,
        "classes": list(REUSE_CLASSES),
        "invariants": list(REUSE_INVARIANTS),
        "carrying_classes": list(CARRYING_CLASSES),
        "entries": [e.as_dict() for e in entries],
        "counts": {name: len(rows) for name, rows in by_class.items()},
        "by_class": by_class,
        "removed_families": {k: dict(v) for k, v in REMOVED_IN_V4R4.items()},
        "nothing_is_regenerated_because":
            "the two families whose wordings failed §10.7 A' were removed "
            "under §10.2's removal rule rather than reworded, so no v4r4 "
            "instrument exists for their rows and no regeneration is owed. "
            "Their rows stay HISTORICAL_ONLY: real generations, real v4r3 "
            "evidence, and evidence about nothing v4r4 measures"
            if not any(e.classification == "INVALIDATED_AND_REGENERATED"
                       for e in entries) else None,
        "rule": "an artifact may be carried only when every quantity that "
                "determines it is unchanged. Prompt identity and verifier "
                "semantics are measured against v4r3's own code and rows; the "
                "rest are read off the rows and compared with what v4r4 "
                "registers",
    }


def ledger_hash(ledger: Mapping[str, Any]) -> str:
    return sha_text(canonical_json(ledger))
