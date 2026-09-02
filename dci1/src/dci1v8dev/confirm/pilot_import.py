"""Reading a model's pilot evidence, by verified signature, read-only.

The confirmatory layer never re-runs a pilot stage. It reads the pilot
root's signed ``GATE_2_CALIBRATION`` and ``GATE_3_REFERENCES`` records (and
the pilot manifest) under the pilot root's own key, records every hash it
read, and extracts the per-frame design inputs: the operating points, the
core references, the frozen backups' rungs and the selected spectrum
points. The grid rows are read for the stability bootstrap
(``confirm.stability``) and, for a top-up, the calibration tables.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs
from dci1v4.engine.signing import verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import sha_obj

from dci1v8dev.run import EVIDENCE_DIRNAME, STUDY_ID
from dci1v8dev.run import eligibility as EL
from dci1v8dev.run import stages as PS
from dci1v8dev.run.context import SYNTHETIC_STUDY_ID

__all__ = ["PilotSource", "open_pilot", "frame_inputs", "spectrum_points"]


@dataclass(frozen=True)
class PilotSource:
    root: Path
    model_key: str
    study_id: str
    manifest_hash: str
    gate2: dict[str, Any]
    gate3: dict[str, Any]
    record_hashes: dict[str, str]
    regime: dict[str, Any]
    gate1: dict[str, Any]

    @property
    def selected_cap(self) -> int:
        return int(self.regime["selected_cap"])

    @property
    def model_dir(self) -> Path:
        return self.root / "evidence" / EVIDENCE_DIRNAME / self.model_key

    def scored_rows(self, stage: str, run: str) -> list[dict[str, Any]]:
        path = self.model_dir / stage / "backend_runs" / run / "scored.jsonl"
        if not path.exists():
            raise IntegrityError(f"no scored rows at {path}")
        return [json.loads(line) for line in path.read_text().splitlines()
                if line.strip()]

    def as_record(self) -> dict[str, Any]:
        return {"root": str(self.root), "model_key": self.model_key,
                "study_id": self.study_id, "manifest_hash": self.manifest_hash,
                "record_hashes": dict(self.record_hashes),
                "gate2_recorded_at": self.gate2.get("recorded_at"),
                "gate3_recorded_at": self.gate3.get("recorded_at"),
                "gate3_producing_commit": self.gate3.get("producing_commit")}


def open_pilot(root: Path, model_key: str, *, synthetic: bool = False
               ) -> PilotSource:
    root = Path(root).resolve()
    base = root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    manifest_path = base / "registration" / "pilot_manifest.json"
    if not manifest_path.exists():
        raise IntegrityError(f"no pilot manifest under {root}")
    manifest = fs.read_json(manifest_path)
    verify_signed(manifest, key, where="pilot manifest")
    expected = SYNTHETIC_STUDY_ID if synthetic else STUDY_ID
    if manifest["payload"].get("study_id") != expected:
        raise IntegrityError(
            f"the pilot root {root} carries study_id "
            f"{manifest['payload'].get('study_id')!r}; expected {expected!r}")
    hashes = {"pilot_manifest": manifest["record_hash"]}
    payloads: dict[str, dict[str, Any]] = {}
    for stage in (PS.STAGE_REGIME, PS.STAGE_GATE1, PS.STAGE_GATE2,
                  PS.STAGE_GATE3):
        path = (base / model_key / stage / "records"
                / PS.STAGE_RECORD_FILES[stage])
        if not path.exists():
            raise IntegrityError(f"{model_key}: no signed {stage} record at "
                                 f"{path}")
        record = fs.read_json(path)
        payload = verify_signed(record, key, where=f"{model_key}:{stage}")
        if payload.get("study_id") != expected:
            raise IntegrityError(f"{stage} record of another study")
        if payload.get("outcome") != "PASS":
            raise ProtocolError(f"{model_key}: {stage} is "
                                f"{payload.get('outcome')!r}, not PASS")
        payloads[stage] = payload
        hashes[stage] = record["record_hash"]
    return PilotSource(root=root, model_key=model_key, study_id=expected,
                       manifest_hash=manifest["record_hash"],
                       gate2=payloads[PS.STAGE_GATE2],
                       gate3=payloads[PS.STAGE_GATE3], record_hashes=hashes,
                       regime=payloads[PS.STAGE_REGIME],
                       gate1=payloads[PS.STAGE_GATE1])


def spectrum_points(g3_frame: Mapping[str, Any]) -> list[dict[str, Any]]:
    sel = g3_frame.get("spectrum_selection") or {}
    return [dict(p) for p in sel.get("points", ())]


def frame_inputs(source: PilotSource, frame: int,
                 gate3_override: Mapping[str, Any] | None = None
                 ) -> dict[str, Any]:
    """The per-frame design inputs, from the signed records alone."""
    g2 = source.gate2["by_frame"][str(frame)]
    gate3 = gate3_override if gate3_override is not None else source.gate3
    g3 = gate3["by_frame"][str(frame)]
    if g2.get("status") != PS.FRAME_SUPPORTED:
        return {"frame": frame, "supported": False,
                "gate2_status": g2.get("status"),
                "unsupported_reason": g2.get("unsupported_reason"),
                "state": g3.get("state", "UNSUPPORTED")}
    survival = g3["survival"]
    core = [{"slot": f"R{i + 1}", "family": c["family"],
             "severity": int(c["severity"]), "iota": c["iota"],
             "label": f"{c['family']}:{c['severity']}"}
            for i, c in enumerate(survival["core_references"])]
    backups = [{"slot": f"R{4 + i}", "family": e["family"],
                "candidate": e["candidate"],
                "severity": int(e["candidate"].rsplit(":", 1)[1]),
                "iota": e["iota"], "label": e["candidate"]}
               for i, e in enumerate((g3.get("backups") or {})
                                     .get("backup_entries", ())[:2])]
    return {
        "frame": frame, "supported": True, "state": g3["state"],
        "n_star": int(g2["n_star"]), "m_star": int(g2["m_star"]),
        "iota_a": float(g2["iota_a"]),
        "solo_compliance_a": float(g2["solo_compliance_a"]),
        "solo_compliance_b": float(g2["solo_compliance_b"]),
        "n_topics_a": int(g2["n_topics_a"]),
        "core_identified": bool(survival["core_identified"]),
        "coverage_identified": bool(survival["coverage_identified"]),
        # Computed from the survival fields by the rule itself, never read
        # from a key: a record written before the rule existed carries none.
        "local_supported": bool(EL.local_support(
            survival, frame=frame)["local_supported"]),
        "n_local_valid_families": survival["n_local_valid_families"],
        "local_valid_families": list(survival["local_valid_families"]),
        "n_backups": survival["n_backups"],
        "core": core, "backups": backups,
        "spectrum": spectrum_points(g3),
        "identification_statuses": list(g3.get("identification_statuses", ())),
        "record_hash_gate3": sha_obj(gate3) if gate3_override is not None
        else source.record_hashes[PS.STAGE_GATE3],
    }
