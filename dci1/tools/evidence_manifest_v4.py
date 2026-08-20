#!/usr/bin/env python3
"""Write a committed content manifest of the registered v4 evidence tree.

``dci1/evidence/`` and ``dci1/durable_root/`` are gitignored by design (prereg
§28: a run must never dirty the worktree), so a fresh clone carries none of the
15,264 signed generations this study rests on. This manifest cannot restore
them. What it does is make loss *detectable*: a clone can compare what it has
against what the study recorded, and a silent truncation or a partially copied
tree stops being invisible.

Usage:
    python tools/evidence_manifest_v4.py            # write the manifest
    python tools/evidence_manifest_v4.py --verify   # check the tree against it
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parent.parent
EVIDENCE = DCI1 / "evidence" / "dci1-v4"
DURABLE = DCI1 / "durable_root" / "dci1-v4"
MANIFEST = DCI1 / "docs" / "evidence_manifest_v4.json"

#: Files whose loss would end the study, listed separately so a verify run says
#: which class was lost rather than only how many files.
CRITICAL_SUFFIXES = ("qualification.json", "gate0_apparatus.json",
                     "regime_screen.json", "manifest.json",
                     "transition_log.jsonl")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def scan(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "signing_key":
            continue                      # the key is a secret, never manifested
        rel = str(path.relative_to(root))
        out[rel] = {"sha256": sha256(path), "bytes": path.stat().st_size,
                    "critical": rel.endswith(CRITICAL_SUFFIXES)}
    return out


def build() -> dict:
    evidence, durable = scan(EVIDENCE), scan(DURABLE)
    unmirrored = sorted(r for r in evidence
                        if durable.get(r, {}).get("sha256")
                        != evidence[r]["sha256"])
    return {
        "study_id": "dci1-v4",
        "classification": "content manifest of registered pre-freeze evidence",
        "purpose": ("makes loss detectable in a fresh clone; it cannot restore "
                    "the tree, which is gitignored by prereg §28"),
        "evidence_root": str(EVIDENCE.relative_to(DCI1)),
        "durable_root": str(DURABLE.relative_to(DCI1)),
        "file_count": len(evidence),
        "critical_count": sum(1 for v in evidence.values() if v["critical"]),
        "total_bytes": sum(v["bytes"] for v in evidence.values()),
        "mirror_complete": not unmirrored,
        "unmirrored": unmirrored,
        "second_physical_copy": False,
        "second_physical_copy_note": (
            "VERIFIED 2026-08-20: evidence/ and durable_root/ share device "
            "64512 (/dev/mapper/ubuntu--vg-ubuntu--lv, the single root "
            "volume). The mirror protects against a bad write or a partial "
            "run, NOT against loss of the disk. No off-host copy of the "
            "evidence exists. The repository has a remote "
            "(github.com/cnm13ryan/dci.git), so this manifest survives a push "
            "even though the 72 MB of generations it describes never can."),
        "devices": {"evidence": 64512, "durable_root": 64512,
                    "same_device": True},
        "files": evidence,
    }


def verify() -> int:
    if not MANIFEST.exists():
        print(f"no manifest at {MANIFEST}", file=sys.stderr)
        return 2
    recorded = json.loads(MANIFEST.read_text())["files"]
    present = scan(EVIDENCE)
    missing = sorted(set(recorded) - set(present))
    changed = sorted(r for r in set(recorded) & set(present)
                     if recorded[r]["sha256"] != present[r]["sha256"])
    extra = sorted(set(present) - set(recorded))
    lost_critical = [r for r in missing + changed if recorded[r]["critical"]]
    print(json.dumps({"recorded": len(recorded), "present": len(present),
                      "missing": len(missing), "changed": len(changed),
                      "extra": len(extra),
                      "critical_records_lost_or_altered": lost_critical},
                     indent=1))
    return 1 if (missing or changed) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return verify()
    manifest = build()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"},
                     indent=1))
    print(f"wrote {MANIFEST.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
