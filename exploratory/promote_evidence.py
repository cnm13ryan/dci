#!/usr/bin/env python3
"""Copy the evidence behind a durable claim out of `runs/` and into the repository.

THE PROBLEM THIS SOLVES
-----------------------
`runs/` is gitignored, which is right: most runs are scratch, and raw generations
are large. But the run manifests in this directory hash files under `runs/` that
no longer exist in a fresh checkout, and a sha256 of an unrecoverable file proves
nothing anyone can check. `verify_independently.py` takes a run directory and so
cannot be executed either. The result is that the headline numbers are, in a
clean clone, unverifiable in principle.

The distinction that fixes it is not "keep everything" but:

  ephemeral   a run under `runs/`. Overwritable, gitignored, expected to vanish.
  promoted    a run that a durable claim rests on. Its identity, its resolved
              configuration and its scored rows live under `evidence/`, in git.

Promotion is deliberate and per claim, not automatic. If nothing cites a run, it
stays ephemeral.

WHAT A PROMOTED BUNDLE HOLDS
----------------------------
`evidence/<slug>/`
    evidence.json    identity, configuration, code, model, seed regime, the file
                     table with sizes and hashes, and the claim it supports
    <copied files>   the run records naming the evidence: by default the design,
                     the resolved config, the environment record and the scored
                     rows. Raw generations are copied when they fit the budget
                     and are otherwise recorded by hash with their location.

Nothing here is recomputed or reformatted: the files are copied byte for byte, so
the hashes in `evidence.json` are hashes of what the run actually produced.

USE
    python promote_evidence.py runs/stageS18_... --slug natural-reasoning-headline \\
        --claim "tau at the natural reasoning endpoint" --execute
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

#: Run records copied by default. Everything a reader needs to know WHAT was run
#: and to recompute the numbers, without the raw generations.
DEFAULT_RECORDS = (
    "config.json", "selection_audit.json", "design.jsonl", "environment.json",
    "run_summary.json", "technical_failures.jsonl",
    # The raw artifact. `verify_independently.py` needs exactly this file plus
    # `config.json`, and both are promoted under their original names, so
    # independent recomputation runs against a bundle directory unchanged:
    #     python verify_independently.py evidence/<slug>
    # Without it a bundle records what was run and leaves the numbers uncheckable.
    "generations.jsonl",
)

#: The one record a bundle may not be written without. See the refusal in
#: `build` for why it is required rather than merely default.
REQUIRED_RECORD = "generations.jsonl"


class MissingRawGenerations(FileNotFoundError):
    """A run that cannot be promoted, because its numbers would be uncheckable."""

#: Files above this size are recorded by hash and location rather than copied, so
#: promoting a claim never silently commits hundreds of megabytes.
DEFAULT_MAX_MIB = 40.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), cwd=HERE, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                   # noqa: BLE001
        return ""


def code_identity() -> dict[str, Any]:
    """What was running. `dirty` matters: a promoted claim built from an
    uncommitted tree cannot be reconstructed from the commit alone."""
    return {"commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain"))}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:                                   # noqa: BLE001
        return {}


def build(run_dir: Path, slug: str, claim: str, extra: tuple[str, ...],
          max_mib: float) -> tuple[dict[str, Any], list[Path]]:
    config = _read_json(run_dir / "config.json")
    environment = _read_json(run_dir / "environment.json")

    wanted = list(DEFAULT_RECORDS) + list(extra)
    files, to_copy = [], []
    for name in wanted:
        path = run_dir / name
        if not path.exists():
            # `generations.jsonl` is not optional. A bundle without it records
            # what was run and leaves the numbers uncheckable, which is the exact
            # failure promotion exists to prevent: `verify_independently.py`
            # reads it unconditionally, so an ABSENT entry produces an artifact
            # that presents as durable evidence and crashes when anyone tries to
            # verify it.
            if name == REQUIRED_RECORD:
                raise MissingRawGenerations(
                    f"{path} does not exist. A promoted bundle must carry the raw "
                    "generations, because they are what makes its numbers "
                    "recomputable from a clone. Promote a run that completed, or "
                    "keep this one ephemeral.")
            files.append({"file": name, "status": "ABSENT",
                          "note": "not produced by this run"})
            continue
        size_mib = path.stat().st_size / 2 ** 20
        record = {"file": name, "bytes": path.stat().st_size,
                  "sha256": sha256(path)}
        if size_mib <= max_mib:
            record["status"] = "COPIED"
            to_copy.append(path)
        else:
            record["status"] = "BY_HASH"
            record["note"] = (f"{size_mib:.0f} MiB exceeds the {max_mib:.0f} MiB "
                              f"copy budget; retained at {run_dir / name}")
        files.append(record)

    evidence = {
        "slug": slug,
        "claim": claim,
        "promoted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_run": str(run_dir),
        "code": code_identity(),
        # Straight from the run's own resolved config: the design identity, the
        # model identity and the seed regime are recorded once, by the runner,
        # and copied here rather than re-derived.
        "design": {key: config.get(key) for key in
                   ("stage", "tasks", "replicates", "load", "orders", "permute",
                    "paraphrase_id", "n_rows", "reasoning_budgets",
                    "answer_token_budget", "selection")},
        "model": config.get("model"),
        "seed_regime": {key: config.get(key) for key in
                        ("base_seed", "master_seed", "seed_scheme")},
        "definitions": config.get("harvest_provenance"),
        "environment": {key: environment.get(key) for key in
                        ("gpu", "rocm", "torch", "transformers", "python",
                         "git_commit", "git_branch")},
        "files": files,
    }
    return evidence, to_copy


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--slug", required=True,
                        help="directory name under evidence/, one per claim")
    parser.add_argument("--claim", required=True,
                        help="the durable claim this evidence supports")
    parser.add_argument("--also", default="",
                        help="comma-separated extra run files to promote "
                             "(e.g. the scored rows)")
    parser.add_argument("--max-mib", type=float, default=DEFAULT_MAX_MIB)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    if not args.run_dir.is_dir():
        print(f"{args.run_dir} is not a run directory", file=sys.stderr)
        return 2

    extra = tuple(n.strip() for n in args.also.split(",") if n.strip())
    try:
        evidence, to_copy = build(args.run_dir, args.slug, args.claim, extra,
                                  args.max_mib)
    except MissingRawGenerations as error:
        print(f"refusing to promote: {error}", file=sys.stderr)
        return 2

    print(f"evidence/{args.slug}  <- {args.run_dir}")
    for record in evidence["files"]:
        print(f"  {record['status']:<8} {record['file']}")
    if evidence["code"]["dirty"]:
        print("\n  WARNING: the working tree is dirty, so this bundle cannot be "
              "reconstructed from its commit alone")

    if not args.execute:
        print("\ndry run; pass --execute to write")
        return 0

    target = EVIDENCE / args.slug
    target.mkdir(parents=True, exist_ok=True)
    for path in to_copy:
        shutil.copy2(path, target / path.name)
    (target / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
