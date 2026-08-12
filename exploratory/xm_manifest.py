"""Tracked provenance for every cross-model raw generation file.

`exploratory/runs/` is gitignored, so the raw artefacts are not in version
control. A future reader must still be able to identify the exact file a number
came from without trusting a filename convention, which is what this manifest is
for: content hash, row count, and the execution condition read out of the rows
themselves rather than out of the directory name.

    uv run python xm_manifest.py runs/xm_main_* --out CROSS_MODEL_RUN_MANIFEST.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, seeds


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def one(values: Counter, field: str):
    """The single value of a field, or a record of the disagreement."""
    if len(values) == 1:
        return next(iter(values))
    return {"DISAGREEMENT": dict(values), "field": field}


def describe(path: Path) -> dict:
    rows = [json.loads(line) for line in path.open()]
    if not rows:
        return {"file": path.name, "rows": 0, "error": "empty file"}

    def field(name: str):
        return one(Counter(str(r.get(name)) for r in rows), name)

    audit = seeds.replicate_duplication(rows)
    ceiling = rows[0].get("engineering_ceiling")
    return {
        "relative_path": str(path.parent),
        "file_name": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": len(rows),

        "model_id": field("model_id"),
        "model_revision": field("model_revision"),
        "model_family": field("model_family"),
        "backend": field("backend"),
        "backend_version": field("backend_version"),
        "dtype": field("dtype"),
        "quantization": field("quantization"),
        "device_configuration": field("device_configuration"),
        "chat_template_sha256": field("chat_template_sha256"),

        "reasoning_mode": field("reasoning_mode"),
        "reasoning_control": field("reasoning_control"),
        "assigned_reasoning_budget": field("assigned_reasoning_budget"),
        "engineering_ceiling": ceiling,

        "decoding": {"temperature": rows[0].get("temperature"),
                     "top_p": rows[0].get("top_p"),
                     "top_k": rows[0].get("top_k"),
                     "max_final_answer_tokens":
                         rows[0].get("max_final_answer_tokens")},

        "task_count": len({r["task_id"] for r in rows}),
        "replicate_count": len({r["replicate_id"] for r in rows}),
        "arms": sorted({r["arm"] for r in rows}),
        "backgrounds": sorted({r["background"] for r in rows}),
        "orders": sorted({r["order"] for r in rows}),
        "unique_row_ids": len({r["row_id"] for r in rows}),
        "seed_scheme": ("sha256(MASTER_SEED, task_id, replicate, arm, "
                        "background, order, paraphrase, phase); "
                        f"MASTER_SEED={contract.MASTER_SEED}"),

        "replicate_duplication": audit,
        "technical_failures": sum(1 for r in rows if r.get("technical_failure")),
        "empty_answers": sum(1 for r in rows if r.get("answer_empty")),
        "truncated_answers": sum(1 for r in rows if r.get("answer_truncated")),
        "ceiling_hits": sum(1 for r in rows if r.get("reasoning_cap_hit")),
        "forced_close_artefacts": sum(
            1 for r in rows if r.get("forced_close_artefact")),
        "traces_opened": sum(1 for r in rows if r.get("reasoning_emitted")),

        "canonical_status": (
            "CANONICAL"
            if (len(rows) == contract.EXPECTED_ROWS
                and not audit["implausible"]
                and not any(r.get("technical_failure") for r in rows)
                and not any(r.get("answer_empty") for r in rows)
                and not any(r.get("reasoning_cap_hit") for r in rows))
            else "NOT CANONICAL — see the counters above"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dirs", nargs="+")
    parser.add_argument("--out", default="CROSS_MODEL_RUN_MANIFEST.json")
    args = parser.parse_args()

    def git(*command: str) -> str:
        try:
            return subprocess.run(["git", *command], capture_output=True,
                                  text=True, timeout=30).stdout.strip()
        except Exception:                               # noqa: BLE001
            return ""

    entries = []
    for directory in args.dirs:
        base = Path(directory)
        patterns = ("**/generations*.jsonl", "**/raw_generations*.jsonl")
        seen = set()
        for pattern in patterns:
          for path in sorted(base.glob(pattern)):
            if path in seen or path.name.endswith("_engine.json"):
                continue
            seen.add(path)
            print(f"hashing {path} ...", flush=True)
            try:
                entries.append(describe(path))
            except Exception as error:  # noqa: BLE001
                entries.append({"relative_path": str(path.parent),
                                "file_name": path.name,
                                "sha256": sha256(path),
                                "rows": sum(1 for _ in path.open()),
                                "canonical_status": "QUALIFICATION ARTEFACT — "
                                                    "not a scientific slice",
                                "note": f"{type(error).__name__}: {error}"[:200]})

    manifest = {
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "contract": contract.as_dict(),
        "note": ("runs/ is gitignored. These hashes and row counts are how a "
                 "raw artefact is identified; filenames are not evidence."),
        "files": entries,
    }
    Path(args.out).write_text(json.dumps(manifest, indent=1))
    print(f"\nwrote {args.out} — {len(entries)} file(s)")
    for entry in entries:
        print(f"  {entry['file_name']:34s} {entry.get('model_id','?'):40s} "
              f"{entry.get('reasoning_mode','?'):18s} rows={entry['rows']:4d} "
              f"{entry.get('canonical_status','')[:20]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
