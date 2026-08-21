"""The evidence-durability gate that must pass before Gate 5 (§26).

**Why this is a gate and not a report.** `evidence/` and `durable_root/` are
gitignored by this repository's own design --- a run must never dirty the
worktree --- so the scientific chain of a 411,648-generation study would
otherwise live entirely outside version control, with the manifest that would
detect its loss living outside version control too. v4r2's design screens
already had that weakness; repeating it for a confirmatory run would mean the
sole authoritative evidence is an undocumented ephemeral cache.

**What this module can and cannot promise.** It verifies that two filesystem
roots hold byte-identical copies of every critical artifact, that the tracked
manifest agrees with both, and that a restore actually works when rehearsed.
It does **not** promise off-machine durability, and `report()` says so
explicitly rather than letting "durable mirror" imply something it is not. If
both roots sit on one device, that is recorded as a stated limitation, because
the honest statement is more useful than the comfortable one.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from dci1v4.errors import IntegrityError

__all__ = ["CRITICAL_SUFFIXES", "file_index", "compare_roots",
           "restore_rehearsal", "report", "assert_durable_before_freeze"]

#: Artifacts whose loss would make a result unauditable.
CRITICAL_SUFFIXES = (
    "registration_manifest.json", "regime_record.json",
    "gate0_apparatus.json", "gate1_measurement.json", "gate2_regime.json",
    "gate3_references.json", "gate4_composed.json", "gate5_freeze.json",
    "confirmatory_manifest.json", "masked_result.json", "unmask_record.json",
    "unmasked_result.json", "scored.jsonl", "rows.jsonl",
    # A replication that fails a registered gate produces exactly one signed
    # artifact saying so, and that is a result. Two of v4r4's four stopped at
    # §13.10, so this is not hypothetical.
    "terminal_report.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_index(root: Path) -> dict[str, str]:
    """Relative path -> sha256, for every file under ``root``."""
    root = Path(root)
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): _sha256(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def _critical(paths: Iterable[str]) -> list[str]:
    return sorted(p for p in paths if p.endswith(CRITICAL_SUFFIXES))


def compare_roots(evidence: Path, durable: Path) -> dict[str, Any]:
    """Every critical artifact present in both roots, byte for byte."""
    left, right = file_index(evidence), file_index(durable)
    critical = _critical(left)
    missing = [p for p in critical if p not in right]
    diverged = [p for p in critical if p in right and left[p] != right[p]]
    return {
        "evidence_files": len(left), "durable_files": len(right),
        "critical_files": len(critical),
        "critical_missing_from_mirror": missing[:20],
        "n_critical_missing": len(missing),
        "critical_diverged": diverged[:20], "n_critical_diverged": len(diverged),
        "matched": not missing and not diverged,
    }


def restore_rehearsal(durable: Path, sample: int = 8) -> dict[str, Any]:
    """Read a sample of the mirror back and re-hash it.

    A mirror that cannot be read is not a mirror. This is cheap and it is the
    difference between "the files are listed" and "the files are there".
    """
    index = file_index(durable)
    chosen = _critical(index)[:sample] or sorted(index)[:sample]
    failures = []
    for relative in chosen:
        path = Path(durable) / relative
        try:
            if _sha256(path) != index[relative]:
                failures.append(relative)
        except OSError as exc:                       # pragma: no cover
            failures.append(f"{relative}: {exc}")
    return {"rehearsed": len(chosen), "failures": failures,
            "passed": not failures and bool(chosen)}


def _same_device(a: Path, b: Path) -> bool | None:
    try:
        return os.stat(a).st_dev == os.stat(b).st_dev
    except OSError:                                  # pragma: no cover
        return None


def report(*, evidence: Path, durable: Path, manifest: Path,
           producing_commit: str, manifest_tracked: bool) -> dict[str, Any]:
    """The durability record, with its limitation stated rather than implied."""
    comparison = compare_roots(evidence, durable)
    rehearsal = restore_rehearsal(durable)
    same_device = _same_device(evidence, durable)
    return {
        "artifact_type": "durability_report",
        "producing_commit": producing_commit,
        "evidence_root": str(evidence), "durable_root": str(durable),
        "manifest": str(manifest), "manifest_tracked_in_git": manifest_tracked,
        "comparison": comparison, "restore_rehearsal": rehearsal,
        "roots_on_one_device": same_device,
        "off_machine_copy": False,
        "stated_limitation": (
            "Both roots are local. This establishes that two filesystem "
            "copies agree and that a restore works when rehearsed; it does "
            "NOT establish off-machine durability, and no off-machine copy "
            "exists. Loss of this machine loses the raw evidence. What "
            "survives in version control is the manifest, the hashes, the "
            "producing commit and the reproduction commands, which make loss "
            "detectable and the run repeatable — not recoverable."
            + ("" if same_device is not True else
               " Both roots are on ONE device, so device failure loses both "
               "copies at once.")),
        "passed": comparison["matched"] and rehearsal["passed"]
        and manifest_tracked,
    }


def assert_durable_before_freeze(record: Mapping[str, Any]) -> None:
    """§26: refuse Gate 5 when the evidence chain is not verifiably duplicated.

    Fails closed. A confirmatory run is the most expensive thing this study
    does, and starting one whose evidence has a single unverified copy is how
    a study loses its own result.
    """
    if record.get("passed"):
        return
    reasons = []
    comparison = record.get("comparison", {})
    if not comparison.get("matched"):
        reasons.append(
            f"{comparison.get('n_critical_missing', '?')} critical artifact(s) "
            f"missing from the mirror and "
            f"{comparison.get('n_critical_diverged', '?')} diverged")
    if not record.get("restore_rehearsal", {}).get("passed"):
        reasons.append("the restore rehearsal did not pass")
    if not record.get("manifest_tracked_in_git"):
        reasons.append(
            "the evidence manifest is not tracked in git, so the artifact "
            "that would make loss detectable is itself only in the cache")
    raise IntegrityError(
        "the evidence chain is not verifiably duplicated, so Gate 5 may not "
        "pass: " + "; ".join(reasons))
