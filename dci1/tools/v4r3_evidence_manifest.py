#!/usr/bin/env python3
"""A committed content manifest of the v4r3 evidence tree.

``dci1/evidence/`` and ``dci1/durable_root/`` are gitignored by this
repository's own design — a run must never dirty the worktree — so a fresh
clone carries none of the generations this study rests on. **This manifest
cannot restore them.** What it does is make loss *detectable*: a clone can
compare what it has against what the study recorded, and a silent truncation or
a partially copied tree stops being invisible.

It lives under ``reports/``, which *is* tracked, so every artifact the reports
cite has a hash in version control even though the artifact does not.

    ./.venv/bin/python tools/v4r3_evidence_manifest.py
    ./.venv/bin/python tools/v4r3_evidence_manifest.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r3 import EVIDENCE_DIRNAME                          # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash            # noqa: E402

EVIDENCE = DCI1 / "evidence" / EVIDENCE_DIRNAME
DURABLE = DCI1 / "durable_root" / EVIDENCE_DIRNAME
MANIFEST = DCI1 / "reports" / "dci1v4r3" / "evidence_manifest.json"

#: Files whose loss would end the study, named so a verify run says which class
#: was lost rather than only how many files.
CRITICAL = ("registration_manifest.json", "regime_record.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = {
                "sha256": sha256(path), "bytes": path.stat().st_size}
    return out


def build() -> dict:
    evidence, durable = inventory(EVIDENCE), inventory(DURABLE)
    rows = sum(1 for p in EVIDENCE.rglob("scored.jsonl")
               for _ in p.open("r", encoding="utf-8"))
    return {
        "study": EVIDENCE_DIRNAME,
        "canonical_verifier_hash": verifier_source_hash(),
        "note": "evidence/ and durable_root/ are gitignored by design; this "
                "manifest makes loss detectable, not recoverable",
        "evidence": {"root": str(EVIDENCE.relative_to(DCI1)),
                     "files": len(evidence),
                     "bytes": sum(f["bytes"] for f in evidence.values()),
                     "scored_rows": rows,
                     "index": evidence},
        "durable_mirror": {"root": str(DURABLE.relative_to(DCI1)),
                           "files": len(durable),
                           "index": durable},
        "critical": {name: sorted(k for k in evidence if k.endswith(name))
                     for name in CRITICAL},
        "reproduce": [
            "./.venv/bin/python tools/run_v4r3.py register",
            "./.venv/bin/python tools/run_v4r3.py regime --model <model> "
            "--device <n>",
            "./.venv/bin/python tools/run_v4r3.py gate1",
            "./.venv/bin/python tools/v4r3_regime_report.py",
            "./.venv/bin/python tools/v4r3_topic_audit.py",
        ],
    }


def verify() -> dict:
    if not MANIFEST.exists():
        return {"status": "NO_MANIFEST"}
    recorded = json.loads(MANIFEST.read_text())
    present = inventory(EVIDENCE)
    expected = recorded["evidence"]["index"]
    missing = sorted(set(expected) - set(present))
    changed = sorted(k for k in set(expected) & set(present)
                     if expected[k]["sha256"] != present[k]["sha256"])
    extra = sorted(set(present) - set(expected))
    return {"status": "OK" if not (missing or changed) else "DIVERGED",
            "missing": missing[:20], "n_missing": len(missing),
            "changed": changed[:20], "n_changed": len(changed),
            "n_added_since": len(extra),
            "critical_missing": sorted(
                m for m in missing if m.endswith(CRITICAL))}


def replicate_all() -> dict:
    """Mirror the whole evidence tree, not only the stage records.

    The mirror held six files -- the regime records -- while fifty-three
    critical artifacts, every raw and scored row among them, existed in one
    copy. A record mirror documents a result; an evidence mirror is the only
    thing that can reproduce one, and `evidence/` is gitignored by design.
    """
    import shutil

    copied = 0
    for source in sorted(EVIDENCE.rglob("*")):
        if not source.is_file():
            continue
        target = DURABLE / source.relative_to(EVIDENCE)
        if target.exists() and sha256(target) == sha256(source):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return {"copied": copied, "durable_files": len(inventory(DURABLE))}


def durability() -> dict:
    """§26's pre-Gate-5 durability gate, with its limitation stated."""
    import subprocess

    from dci1v4r3.stages import durability as D

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(MANIFEST)],
        cwd=DCI1, capture_output=True).returncode == 0
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                            capture_output=True, text=True).stdout.strip()
    return D.report(evidence=EVIDENCE, durable=DURABLE, manifest=MANIFEST,
                    producing_commit=commit, manifest_tracked=tracked)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--replicate", action="store_true",
                        help="mirror the whole evidence tree to durable_root")
    parser.add_argument("--durability", action="store_true",
                        help="the §26 pre-Gate-5 durability gate")
    args = parser.parse_args()
    if args.replicate:
        print(json.dumps(replicate_all(), indent=1))
        return 0
    if args.durability:
        record = durability()
        (DCI1 / "reports" / "dci1v4r3" / "durability.json").write_text(
            json.dumps(record, indent=1, sort_keys=True) + "\n")
        print(json.dumps({k: v for k, v in record.items()
                          if k != "comparison"}, indent=1))
        print(json.dumps(record["comparison"], indent=1))
        return 0 if record["passed"] else 1
    if args.verify:
        print(json.dumps(verify(), indent=1))
        return 0
    manifest = build()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k not in ("evidence", "durable_mirror")}, indent=1))
    print(f"evidence: {manifest['evidence']['files']} files, "
          f"{manifest['evidence']['bytes'] / 1e6:.1f} MB, "
          f"{manifest['evidence']['scored_rows']} scored rows")
    print(f"durable mirror: {manifest['durable_mirror']['files']} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
