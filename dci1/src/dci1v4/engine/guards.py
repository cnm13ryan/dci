"""The deprecated-and-foreign input guard (§14.2, §26, check C15, trap T-13).

The construct memo §B.0 records a committed analysis table built entirely from
files the project itself marks DEPRECATED and FOREIGN, with roughly 98%
byte-identical replicate pairs. v4r2 answers that with an executable guard, and
this is it: **an analysis input is admissible only when it is a registered v4
artifact**, and the check is positive — a path must prove it belongs to the v4
namespace, rather than merely failing to match a deny list.

Three classes are refused by name as well, so the refusal message says which
corpus was offered: the legacy exploratory corpus, the v3 trees, and the B+R
pilot cache. The pilot is design evidence for §16 variance information and for
checks C12, C13 and C16 — reading it *for those checks* is required, and those
readers go through ``design_evidence_read`` which records the read and marks
the result non-confirmatory (check C20). Nothing that passes through here can
reach an estimator.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from dci1v4.engine.context import DCI1_ROOT, StudyContext
from dci1v4.errors import ProvenanceGuardError

#: Trees that are design evidence or history, never analysis input.
FOREIGN_TREES = {
    "v3_evidence": DCI1_ROOT / "evidence" / "dci1-v3",
    "v3_durable": DCI1_ROOT / "durable_root" / "dci1-v3",
    "v2_evidence": DCI1_ROOT / "evidence" / "dci1-v2",
    "v2_durable": DCI1_ROOT / "durable_root" / "dci1-v2",
    "pilot_cache": DCI1_ROOT / "evidence" / "br-pilot-v4",
    "pilot_reports": DCI1_ROOT / "reports" / "br_pilot_v4",
    "legacy_exploratory": DCI1_ROOT.parent / "exploratory",
    "v3_reports": DCI1_ROOT / "reports",
}

#: Manifest classifications that may never enter registered v4 evidence.
REFUSED_CLASSIFICATIONS = ("DEPRECATED", "FOREIGN", "design_evidence",
                           "non_confirmatory", "historical")


def classify(path: Path) -> str | None:
    """Which historical tree a path belongs to, or None."""
    resolved = Path(path).resolve()
    for label, root in FOREIGN_TREES.items():
        try:
            if resolved.is_relative_to(root.resolve()):
                return label
        except (OSError, RuntimeError):       # unresolvable path
            continue
    return None


def assert_registered_v4_input(context: StudyContext, path: Path, *,
                               where: str = "analysis") -> Path:
    """Positive admission: the path must live inside this context's v4 roots."""
    resolved = Path(path).resolve()
    foreign = classify(resolved)
    if foreign is not None:
        raise ProvenanceGuardError(
            f"{where} refuses {resolved}: it belongs to {foreign}, which is "
            f"design evidence or history and is structurally excluded from "
            f"every v4 analysis input (§14.2)")
    for root in (context.study_root, context.durable_study_root):
        try:
            if resolved.is_relative_to(Path(root).resolve()):
                return resolved
        except (OSError, RuntimeError):
            continue
    raise ProvenanceGuardError(
        f"{where} refuses {resolved}: it is not a registered v4 artifact of "
        f"study {context.study_id!r}. Analysis reads only accepted v4 "
        f"evidence (§26)")


def assert_admissible_manifest(manifest: dict[str, Any], *,
                               where: str = "analysis") -> None:
    """Refuse an input whose own manifest declares it deprecated or foreign."""
    classification = str(manifest.get("classification", "")).strip()
    if classification.upper() in {c.upper() for c in REFUSED_CLASSIFICATIONS}:
        raise ProvenanceGuardError(
            f"{where} refuses an input classified {classification!r}")
    study = manifest.get("study_id")
    if study is not None and not str(study).startswith("dci1-v4"):
        raise ProvenanceGuardError(
            f"{where} refuses an input from study {study!r}; only dci1-v4 "
            f"artifacts are registered v4 analysis inputs")


def assert_rows_admissible(context: StudyContext, rows: Iterable[dict],
                           *, where: str = "analysis") -> int:
    """Every row must declare the v4 study and a v4 stage."""
    count = 0
    for row in rows:
        study = row.get("study_id")
        if study != context.study_id:
            raise ProvenanceGuardError(
                f"{where} refuses a row from study {study!r}; expected "
                f"{context.study_id!r}")
        count += 1
    return count


def design_evidence_read(path: Path, *, check: str, purpose: str) -> dict:
    """Record a deliberate read of design evidence for a pre-freeze check.

    §14.2 permits reading the pilot and the v3 cache for checks C6, C12, C13,
    C14 and C18 and prohibits feeding either into an estimator. This function
    is the only sanctioned door: it returns a provenance stamp that carries the
    non-confirmatory label check C20 requires every citing artifact to repeat.
    """
    resolved = Path(path).resolve()
    tree = classify(resolved)
    if tree is None:
        raise ProvenanceGuardError(
            f"{path} is not design evidence; a registered v4 artifact is read "
            f"through the normal path, not through the design-evidence door")
    if not resolved.exists():
        raise ProvenanceGuardError(f"design evidence missing at {resolved}")
    return {"path": str(resolved), "tree": tree, "check": check,
            "purpose": purpose, "classification": "design_evidence",
            "status": "non-confirmatory",
            "note": ("this source licenses no scientific claim; its rows may "
                     "never enter a v4 estimator and its point estimates are "
                     "never the effect the confirmatory design expects")}
