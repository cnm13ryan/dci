#!/usr/bin/env python3
"""Extract the committed evidence subset that lets CI run two stored-evidence
checks a fresh clone would otherwise skip.

Read-only and zero-generation. ``dci1/evidence`` is gitignored, so every test
that reads it skips in CI and in a fresh clone. Two of those tests guard
results the study relies on and need only a few signed records, so exactly
those records are committed under ``tests_v8dev/fixtures/evidence_subset``:

* **the six v7 ``qwen3-4b`` stage records that
  ``dci1v8dev.backtest.load_replication`` opens** (``backtest.STAGE_FILES``),
  byte-identical and gzip-compressed. ``test_simulation_and_evidence`` replays
  them on the recorded and on the corrected chance basis. Those two tests
  raised ``ProtocolError`` from 7196123 until PR #39, unseen, because they
  skipped everywhere the tree was absent;
* **the three fields per frame the LOCAL eligibility rule reads** from five
  signed pilot ``GATE_3_REFERENCES`` records --- ``by_frame[f]``'s
  ``survival``, ``status`` and ``unsupported_reason``, the whole input of
  ``eligibility.local_eligibility`` --- for ``test_local_eligibility``'s
  verdicts on the pre-freeze pilots behind the v8.1 decision.

Every source record is verified before a byte is taken: its signature, with
its own tree's key, and the reader copy the loaders open against the signed
payload's ``record_hash``. ``MANIFEST.json`` records each source's path under
its evidence root, its SHA-256 and its ``record_hash``; the tests check the
committed bytes against it in CI, and against the tree where one is on disk.
The keys stay out of Git: nothing committed here can sign or verify a record.

The v7 records and the pilot roots live in different trees on the author's
machine, so ``--evidence`` may be given more than once; each source is read
from the first root that holds it.

    dci1/.venv/bin/python tools/v8_ci_evidence_fixture.py \\
        --evidence evidence --evidence <root holding the dci1v8-pilot-* trees>
    dci1/.venv/bin/python tools/v8_ci_evidence_fixture.py --check --evidence ...
"""
from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                       # noqa: E402
from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError                           # noqa: E402
from dci1v4.protocol.hashing import sha_bytes, sha_obj             # noqa: E402
from dci1v8dev import backtest as B                                # noqa: E402
from dci1v8dev.run import stages as PS                             # noqa: E402

DCI1 = HERE.parent
OUT = DCI1 / "tests_v8dev" / "fixtures" / "evidence_subset"
MANIFEST = "MANIFEST.json"
ELIGIBILITY_FILE = "pilot_local_eligibility.json"

#: The replication both backtests replay: (tree label, model, path under root).
BACKTEST = ("v7", "qwen3-4b", "dci1v7/qwen3-4b")
#: The pilot lanes whose recorded LOCAL verdict ``test_local_eligibility`` pins.
PILOT_LANES = (
    ("dci1v8-pilot-r9", "qwen3-4b"),
    ("dci1v8-pilot-r8", "gemma-3n-e2b-it"),
    ("dci1v8-pilot-r8", "qwen3-4b-instruct-2507"),
    ("dci1v8-pilot-r10", "qwen3-4b-instruct-2507"),
    ("dci1v8-pilot-r11", "gemma-3n-e4b-it"),
)
#: Everything ``eligibility.local_eligibility`` reads from one frame's entry.
ELIGIBILITY_FIELDS = ("survival", "status", "unsupported_reason")


def locate(roots: list[pathlib.Path], rel: str) -> pathlib.Path:
    for root in roots:
        if (root / rel).exists():
            return root / rel
    raise IntegrityError(f"{rel} is under none of {[str(r) for r in roots]}")


def verified_reader_copy(model_dir: pathlib.Path, stage: str, name: str
                         ) -> tuple[bytes, str]:
    """The bytes a loader opens, proven to be the signed payload."""
    key = model_dir.parent / "keys" / "signing.key"
    signed = fs.read_json(model_dir / stage / "records" / name)
    verify_signed(signed, key, where=f"{model_dir.name}:{stage}")
    data = (model_dir / stage / name).read_bytes()
    if sha_obj(json.loads(data)) != signed["record_hash"]:
        raise IntegrityError(f"{model_dir}/{stage}/{name}: the reader copy is "
                             "not the signed payload")
    return data, signed["record_hash"]


def dumps(obj: Any) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
            + "\n").encode()


def build(roots: list[pathlib.Path]) -> dict[str, bytes]:
    """Every file of the fixture directory, by path relative to it."""
    out: dict[str, bytes] = {}
    tree, model, rel = BACKTEST
    model_dir = locate(roots, rel)
    files: dict[str, Any] = {}
    for key, (stage, name) in B.STAGE_FILES.items():
        data, record_hash = verified_reader_copy(model_dir, stage, name)
        source = f"{rel}/{stage}/{name}"
        out[f"{source}.gz"] = gzip.compress(data, compresslevel=9, mtime=0)
        files[source] = {"fixture": f"{source}.gz", "stage_key": key,
                         "bytes": len(data), "sha256": sha_bytes(data),
                         "record_hash": record_hash}

    extract: dict[str, Any] = {}
    lanes: dict[str, Any] = {}
    stage, name = PS.STAGE_GATE3, PS.STAGE_RECORD_FILES[PS.STAGE_GATE3]
    for root_name, model_key in PILOT_LANES:
        lane = f"{root_name}/{model_key}"
        lane_dir = locate(roots, f"{root_name}/evidence/dci1v8/{model_key}")
        data, record_hash = verified_reader_copy(lane_dir, stage, name)
        by_frame = json.loads(data)["by_frame"]
        extract[lane] = {"by_frame": {
            str(w): {f: by_frame[str(w)].get(f) for f in ELIGIBILITY_FIELDS}
            for w in PS.FRAMES}}
        lanes[lane] = {
            "source": f"{root_name}/evidence/dci1v8/{model_key}/{stage}/{name}",
            "bytes": len(data), "sha256": sha_bytes(data),
            "record_hash": record_hash, "extract_sha": sha_obj(extract[lane])}
    out[ELIGIBILITY_FILE] = dumps(extract)

    out[MANIFEST] = dumps({
        "generated_by": "tools/v8_ci_evidence_fixture.py",
        "read_only": True,
        "note": "Source paths are relative to a DCI-1 evidence root, which is "
                "gitignored. Each source was signature-verified with its own "
                "tree's key at extraction; no key is committed.",
        "backtest": {
            "tree": tree, "model": model, "rel": rel,
            "read_by": "tests_v8dev/test_simulation_and_evidence.py",
            "chance_cache": f"reports/dci1v8dev/chance_basis/{tree}__{model}.json",
            "files": files},
        "local_eligibility": {
            "fixture": ELIGIBILITY_FILE, "fields": list(ELIGIBILITY_FIELDS),
            "frames": list(PS.FRAMES),
            "read_by": "tests_v8dev/test_local_eligibility.py",
            "lanes": lanes},
    })
    return out


def compare(built: dict[str, bytes], out_dir: pathlib.Path) -> list[str]:
    """What differs between a fresh extraction and the committed directory.
    Compressed files are compared decompressed, so another zlib is not a
    difference."""
    problems = []
    on_disk = {str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()}
    for rel in sorted(on_disk - set(built)):
        problems.append(f"unexpected file {rel}")
    for rel, data in sorted(built.items()):
        path = out_dir / rel
        if not path.exists():
            problems.append(f"missing {rel}")
            continue
        committed = path.read_bytes()
        if rel.endswith(".gz"):
            same = gzip.decompress(committed) == gzip.decompress(data)
        else:
            same = json.loads(committed) == json.loads(data)
        if not same:
            problems.append(f"differs from the evidence: {rel}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidence", action="append", type=pathlib.Path,
                    help="an evidence root; repeatable (default: dci1/evidence)")
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="compare with the committed subset; write nothing")
    args = ap.parse_args(argv)
    roots = [r.resolve() for r in (args.evidence or [DCI1 / "evidence"])]
    built = build(roots)
    if args.check:
        problems = compare(built, args.out)
        for p in problems:
            print(p)
        print("evidence subset: " + ("MATCHES the evidence" if not problems
                                     else f"{len(problems)} difference(s)"))
        return 1 if problems else 0
    for rel, data in built.items():
        path = args.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"wrote {len(built)} files under {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
