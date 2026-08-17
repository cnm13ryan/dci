"""Programmatic report generation from analysis.parquet (Addendum A §5, R51).

Every number comes from the analysis table; nothing is transcribed by hand.
The emitted report carries the analysis-table hash and the study-manifest
hash, and regeneration from sealed evidence is byte-identical (tested)."""
from __future__ import annotations

from typing import Any

from dci1.evidence.layout import StudyTree
from dci1.evidence.store import write_json
from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_text
from dci1.tables.build import read_table


def build_report(tree: StudyTree) -> dict[str, Any]:
    analysis_path = tree.derived_primary / "analysis.parquet"
    if not analysis_path.exists():
        raise ProtocolError(f"no analysis table at {analysis_path}")
    table = read_table(analysis_path, "analysis")
    rows = table.to_pylist()
    families: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda r: (r["family_id"], r["estimand_id"])):
        families.setdefault(row["family_id"], []).append({
            "estimand_id": row["estimand_id"],
            "point_estimate": row["point_estimate"],
            "ci_lower": row["ci_lower"], "ci_upper": row["ci_upper"],
            "claim_outcome": row["claim_outcome"],
            "n_blocks": row["n_blocks"],
            "n_observations": row["n_observations"],
        })
    manifest_hash = (sha_text(tree.study_manifest.read_text())
                     if tree.study_manifest.exists() else "")
    report = {
        "study_id": tree.study_id,
        "model_slug": tree.model_slug,
        "freeze_id": tree.freeze_id,
        "analysis_table_hash": sha_text(analysis_path.read_bytes().hex()),
        "study_manifest_hash": manifest_hash,
        "analysis_stage": rows[0]["analysis_stage"] if rows else None,
        "families": families,
    }
    write_json(tree.root / "report.json", report)
    return report
