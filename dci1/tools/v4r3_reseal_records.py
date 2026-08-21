"""Re-seal stage records whose content hash was computed over integer keys.

**What went wrong.** `write_stage_record` signed the in-memory payload and
wrote it as JSON. §12.2's regime record carries `completion_cap.table`, a dict
keyed by the integer completion caps 512, 768 and 1024. `canonical_json` sorts
those numerically; a reader loads them back as the strings `"512"`, `"768"`,
`"1024"` and sorts them lexicographically, putting `"1024"` first. The two
orders hash differently, so all four v4r3 regime records failed
`verify_signed` and `assert_transition_legal` refused every transition out of
`REGIME_SCREEN`. Gate 1 could not have written a record even had its
measurement basis been licensed.

**Why this is a re-seal and not an edit.** The proof is exact and it runs
before anything is written: for every record repaired, the stored
`record_hash` must equal `sha_obj` of the payload with its numeric keys read
back as integers --- that is, the stored hash must be reproducibly the hash of
*this* payload under the defective canonicalisation. A payload that had been
altered by so much as one character could not satisfy that. The tool refuses
the whole run if any record fails the proof, and refuses any record whose
payload is already self-consistent.

Only `record_hash` and `signature` change. No payload byte is touched, no
number moves, and the reader copy beside the record is left exactly as it is.

    python3 tools/v4r3_reseal_records.py --check
    python3 tools/v4r3_reseal_records.py --apply
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine.signing import sign_payload, verify_signed
from dci1v4.protocol.hashing import sha_obj
from dci1v4r3 import CLASSIFICATION, EVIDENCE_DIRNAME
from dci1v4r3.engine.paths import is_superseded
from dci1v4r3.engine.transitions import on_the_wire

ROOTS = (DCI1 / "evidence" / EVIDENCE_DIRNAME,
         DCI1 / "durable_root" / EVIDENCE_DIRNAME)
OUT = DCI1 / "reports" / "dci1v4r3" / "record_signature_repair.json"


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                          capture_output=True, text=True,
                          check=False).stdout.strip()


def with_integer_keys(obj: Any) -> Any:
    """The in-memory shape the defective signature was computed over.

    A dict every one of whose keys is a decimal string came from a dict keyed
    by integers; nothing else in a v4r3 payload produces one.
    """
    if isinstance(obj, dict):
        keys = list(obj)
        if keys and all(isinstance(k, str) and k.lstrip("-").isdigit()
                        for k in keys):
            return {int(k): with_integer_keys(v) for k, v in obj.items()}
        return {k: with_integer_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [with_integer_keys(v) for v in obj]
    return obj


def signed_records() -> list[Path]:
    paths: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            if is_superseded(path):
                continue
            try:
                record = json.loads(path.read_text())
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(record, dict) and {"payload", "record_hash",
                                             "signature"} <= set(record):
                paths.append(path)
    return paths


def diagnose() -> dict[str, Any]:
    """Classify every current signed record, before anything is written.

    Every entry carries both hashes, so a report-only run *after* a repair
    reconstructs the whole audit trail from the files themselves: a repaired
    record is one that verifies now and whose integer-key hash --- the hash it
    used to carry --- is a different, and still recomputable, value.
    """
    healthy, repaired, repairable, unexplained = [], [], [], []
    for path in signed_records():
        record = json.loads(path.read_text())
        stored = record["record_hash"]
        payload = record["payload"]
        entry = {"path": str(path.relative_to(DCI1)),
                 "stored_record_hash": stored,
                 "hash_of_payload_as_stored": sha_obj(payload),
                 "hash_of_payload_with_integer_keys":
                     sha_obj(with_integer_keys(payload))}
        if entry["hash_of_payload_as_stored"] != stored:
            (repairable if entry["hash_of_payload_with_integer_keys"] == stored
             else unexplained).append(entry)
        elif entry["hash_of_payload_with_integer_keys"] != stored:
            repaired.append(entry)          # holds integer keys, seals clean
        else:
            healthy.append(entry)
    return {"healthy": healthy, "already_repaired": repaired,
            "repairable": repairable, "unexplained": unexplained}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="re-seal; without it the tool only reports")
    args = parser.parse_args(argv)

    report = diagnose()
    if report["unexplained"]:
        print(json.dumps({"outcome": "REFUSED",
                          "reason": "a record's stored hash is not the hash "
                                    "of its payload under either "
                                    "canonicalisation, so this is not the "
                                    "integer-key defect and must not be "
                                    "re-sealed",
                          "unexplained": report["unexplained"]}, indent=1))
        return 1

    payload = {
        "artifact_type": "v4r3-record-signature-repair",
        "classification": CLASSIFICATION,
        "defect": "canonical_json sorts integer dict keys numerically and "
                  "string dict keys lexicographically; a record signed over "
                  "the in-memory payload and verified over the JSON it was "
                  "written to therefore disagreed whenever the payload held "
                  "an integer-keyed dict. §12.2's completion_cap.table is "
                  "the only such payload in v4r3.",
        "proof": "for every repaired record the stored hash is exactly "
                 "sha_obj of THIS payload with its numeric keys read back as "
                 "integers, which an altered payload could not satisfy",
        "changes": "record_hash and signature only; no payload byte, and no "
                   "reader copy",
        "fixed_in_code": "dci1v4r3.engine.transitions.on_the_wire, which "
                         "signs the wire form so what is hashed is what is "
                         "stored",
        "producing_commit": _commit(),
        "generated_at": _dt.datetime.now(_dt.UTC)
                           .isoformat(timespec="seconds"),
        "healthy": report["healthy"],
        "repaired": (report["repairable"] if args.apply
                     else report["already_repaired"]),
        "repairable_not_applied": [] if args.apply else report["repairable"],
    }

    if args.apply:
        key_path = _key_path()
        for entry in report["repairable"]:
            path = DCI1 / entry["path"]
            record = json.loads(path.read_text())
            resealed = sign_payload(on_the_wire(record["payload"]), key_path)
            verify_signed(resealed, key_path, entry["path"])
            if resealed["record_hash"] != entry["hash_of_payload_as_stored"]:
                raise SystemExit(f"re-seal changed the payload of {path}")
            path.write_text(json.dumps(resealed, indent=1) + "\n")
            entry["new_record_hash"] = resealed["record_hash"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"outcome": "APPLIED" if args.apply else "REPORT_ONLY",
                      "healthy": len(report["healthy"]),
                      "repaired": len(report["repairable"] if args.apply
                                      else report["already_repaired"]),
                      "still_repairable": 0 if args.apply
                                          else len(report["repairable"]),
                      "unexplained": len(report["unexplained"]),
                      "report": str(OUT.relative_to(DCI1))}, indent=1))
    return 0


def _key_path() -> Path:
    sys.path.insert(0, str(DCI1 / "tools"))
    import run_v4r3
    return run_v4r3.registered_context().signing_key_path


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
