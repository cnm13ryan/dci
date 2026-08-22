"""§14.2's positive admission rule for v5 analysis inputs.

**An analysis input is admissible only when it proves it belongs to the v5
study tree.** The check is positive --- a path must be inside this context's
roots --- rather than a deny list, because a deny list can only refuse what it
was told about, and the artifact that matters most is the one nobody
remembered to name.

Three classes are refused by name as well, so the refusal message says which
corpus was offered: every earlier study revision, every design screen, and the
B+R pilot. **``dci1v4r4`` is the entry that matters**: it holds signed records
through ``UNMASKED_ANALYSIS`` and 24,576 confirmatory rows per survivor, and
none of it may reach a v5 estimator. Its rows are development evidence for
v5's *design* and enter only through ``protocol/reuse_ledger.py``.

The guard runs **in both directions**: ``assert_v5_is_not_foreign_to`` states
the other half, which is that a v5 artifact must not satisfy an earlier
revision's admission rule either. It does not, and the reason is structural:
``dci1v4``'s guard tests ``startswith("dci1-v4")`` and each revision's
``assert_own_study`` tests exact equality, so ``dci1v5`` satisfies none of
them. That is checked here rather than argued.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from dci1v4.errors import ProvenanceGuardError

from dci1v5 import FOREIGN_STUDY_PREFIXES, STUDY_ID
from dci1v5.engine.context import DCI1_ROOT, StudyContext, foreign_roots

__all__ = ["FOREIGN_TREES", "REFUSED_CLASSIFICATIONS", "classify",
           "assert_registered_v5_input", "assert_v5_is_not_foreign_to",
           "assert_no_foreign_manifest"]

#: Trees that are design evidence or history, never analysis input.
FOREIGN_TREES: dict[str, Path] = {
    "v4r4_evidence": DCI1_ROOT / "evidence" / "dci1v4r4",
    "v4r4_durable": DCI1_ROOT / "durable_root" / "dci1v4r4",
    "v4r3_evidence": DCI1_ROOT / "evidence" / "dci1v4r3",
    "v3_evidence": DCI1_ROOT / "evidence" / "dci1-v3",
    "v2_evidence": DCI1_ROOT / "evidence" / "dci1-v2",
    "pilot_cache": DCI1_ROOT / "evidence" / "br-pilot-v4",
    "pilot_reports": DCI1_ROOT / "reports" / "br_pilot_v4",
    "v4r4_reports": DCI1_ROOT / "reports" / "dci1v4r4",
    "legacy_exploratory": DCI1_ROOT.parent / "exploratory",
}

#: Manifest classifications that may never enter registered v5 evidence.
REFUSED_CLASSIFICATIONS = ("DEPRECATED", "FOREIGN", "design_evidence",
                           "non_confirmatory", "historical",
                           "HISTORICAL_OUTCOME", "DEVELOPMENT_EVIDENCE",
                           "RECOMPUTED_DIAGNOSTIC")


def classify(path: Path | str) -> str | None:
    """Which historical tree a path belongs to, or None."""
    resolved = Path(path).resolve()
    for label, root in FOREIGN_TREES.items():
        try:
            if resolved.is_relative_to(root.resolve()):
                return label
        except (OSError, RuntimeError):       # unresolvable path
            continue
    for root in foreign_roots():
        try:
            if resolved.is_relative_to(root.resolve()):
                return root.name
        except (OSError, RuntimeError):
            continue
    return None


def assert_registered_v5_input(context: StudyContext, path: Path | str, *,
                               where: str = "analysis") -> Path:
    """Positive admission: the path must live inside this context's v5 roots."""
    resolved = Path(path).resolve()
    foreign = classify(resolved)
    if foreign is not None:
        raise ProvenanceGuardError(
            f"{where}: {resolved} belongs to {foreign}, which is historical "
            "evidence of another study. §14.2 admits an input only when it "
            "proves it belongs to the v5 study tree, and v4r4 evidence "
            "reaches v5 only through protocol/reuse_ledger.py, as "
            "DEVELOPMENT_EVIDENCE")
    roots = [Path(context.study_root).resolve(),
             (Path(context.durable_root) / "dci1v5").resolve()]
    if not any(resolved.is_relative_to(root) for root in roots):
        raise ProvenanceGuardError(
            f"{where}: {resolved} is outside every registered v5 root "
            f"{[str(r) for r in roots]}. §14.2's guard is a POSITIVE "
            "admission rule: an input must prove it belongs, and failing to "
            "match a deny list is not proof")
    return resolved


def assert_no_foreign_manifest(manifest: dict[str, Any], *,
                               where: str = "analysis") -> None:
    """A manifest declaring another study, or a refused classification."""
    study = manifest.get("study_id")
    if study != STUDY_ID:
        raise ProvenanceGuardError(
            f"{where}: the manifest declares study_id {study!r} and this "
            f"study is {STUDY_ID!r}")
    classification = manifest.get("classification")
    if classification in REFUSED_CLASSIFICATIONS:
        raise ProvenanceGuardError(
            f"{where}: an artifact classified {classification!r} may never "
            "enter registered v5 evidence (§14.2, §30)")


def assert_v5_is_not_foreign_to(prefixes: Iterable[str] = ()) -> dict[str, Any]:
    """The other direction: no earlier revision can adopt a v5 artifact.

    ``dci1v4``'s admission guard tests ``startswith("dci1-v4")`` and each
    revision's ``assert_own_study`` tests exact equality against its own
    identifier, so ``dci1v5`` satisfies none of them. Checked rather than
    argued, because the v4r4 identifier was chosen hyphen-free for exactly
    this reason and a future identifier could lose the property silently.
    """
    checks = {
        "dci1v4_prefix_guard": not STUDY_ID.startswith("dci1-v4"),
        "not_a_prefix_extension": all(
            not STUDY_ID.startswith(p) for p in FOREIGN_STUDY_PREFIXES),
    }
    for prefix in prefixes:
        checks[f"not_{prefix}"] = not STUDY_ID.startswith(prefix)
    failed = sorted(k for k, v in checks.items() if not v)
    if failed:
        raise ProvenanceGuardError(
            f"the v5 study identifier {STUDY_ID!r} would satisfy an earlier "
            f"revision's admission rule: {failed}")
    return {"study_id": STUDY_ID, "checks": checks,
            "foreign_prefixes_refused": list(FOREIGN_STUDY_PREFIXES)}
