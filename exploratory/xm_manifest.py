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


def identity_audit(rows: list[dict]) -> dict:
    """Whether the file holds EXACTLY the design it claims to hold.

    A line count cannot establish this. A 160-line file with one design row
    missing and some other row duplicated in its place has the right length, the
    right task count and the right arm set, and is not the experiment: one cell
    contributes two draws and another contributes none. Row identity is what
    separates those cases, and `unique_row_ids` was computed and then never
    consulted.

    Identity is checked on the design COORDINATE rather than on `row_id`, which
    is a content hash: the coordinate is what the design enumerates, so a
    missing cell and a duplicated cell surface here as concrete lists rather
    than as a count that happens to reconcile.
    """
    coordinates = Counter(
        (r.get("task_id"), r.get("arm"), r.get("background"),
         r.get("order"), r.get("replicate_id"))
        for r in rows)
    tasks = sorted({r.get("task_id") for r in rows})
    orders = sorted({r.get("order") for r in rows})

    expected = {
        (task, arm, background, order, replicate)
        for task in tasks
        for arm in contract.ARMS
        for background in contract.BACKGROUNDS
        for order in orders
        for replicate in range(contract.REPLICATES)}

    observed = set(coordinates)
    show = lambda key: "|".join(str(part) for part in key)
    duplicated = {show(key): n for key, n in coordinates.items() if n > 1}
    row_ids = Counter(r.get("row_id") for r in rows)

    return {
        "expected_cells": len(expected),
        "observed_cells": len(observed),
        "missing_cells": sorted(show(key) for key in expected - observed),
        "unexpected_cells": sorted(show(key) for key in observed - expected),
        "duplicated_cells": duplicated,
        "duplicate_row_ids": {rid: n for rid, n in row_ids.items() if n > 1},
        "unique_row_ids": len(row_ids),
        "task_count_matches_contract": len(tasks) == contract.N_TASKS,
        "complete": bool(
            not (expected - observed) and not (observed - expected)
            and not duplicated and len(row_ids) == len(rows)
            and len(tasks) == contract.N_TASKS),
    }


def describe(path: Path) -> dict:
    rows = [json.loads(line) for line in path.open()]
    if not rows:
        return {"file": path.name, "rows": 0, "error": "empty file"}

    def field(name: str):
        return one(Counter(str(r.get(name)) for r in rows), name)

    audit = seeds.replicate_duplication(rows)
    identity = identity_audit(rows)
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

        "row_identity": identity,
        "contract_identity": {
            "expected_rows": contract.EXPECTED_ROWS,
            "n_tasks": contract.N_TASKS,
            "replicates": contract.REPLICATES,
            "arms": list(contract.ARMS),
            "backgrounds": list(contract.BACKGROUNDS),
            "master_seed": contract.MASTER_SEED,
        },

        # Canonical status is a statement about IDENTITY, not about length.
        # Requiring only `len(rows) == EXPECTED_ROWS` accepted a file with one
        # design cell missing and another duplicated in its place: right length,
        # right task count, wrong experiment. `identity["complete"]` requires the
        # exact expected set of design coordinates, each exactly once, with
        # unique row ids and the contract's task count — so a substitution
        # cannot reconcile itself by arithmetic.
        #
        # `replicate_multiplicity_ok` is separate from the duplication alarm: the
        # alarm looks at whether two replicates produced identical text, and it
        # silently skipped groups whose size was not 2, which is exactly the
        # malformed case.
        "canonical_status": (
            "CANONICAL"
            if (len(rows) == contract.EXPECTED_ROWS
                and identity["complete"]
                and audit["malformed_groups"] == 0
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
