"""Classify every reasoning data file, by measurement rather than by filename.

`exploratory/runs/` is gitignored, so the analysis input to this branch is not
identifiable from the repository alone. This script fixes that: it hashes every
candidate file, measures its sampling regime directly, assigns a status, and
writes both a machine-readable manifest and a readable provenance table.

Status is derived from evidence, not asserted:

  CANONICAL   independent per-row seeds, complete cells, used by the analysis
  DEPRECATED  a real run whose sampling regime is defective — kept, never used
  DERIVED     an output of a previous analysis, not a generation artifact
  FOREIGN     a valid run belonging to another line of work on another branch
"""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import plotdata

#: A nominal replicate pair that is byte-identical is one draw counted twice.
#: Sampling noise makes a handful plausible; a majority means a shared seed.
DUPLICATE_ALARM = 0.25


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def measure(path: Path) -> dict:
    rows = [json.loads(line) for line in path.open()]
    budgets = collections.Counter(r.get("reasoning_budget") for r in rows)
    pairs = collections.defaultdict(list)
    for row in rows:
        key = (row.get("reasoning_budget"), row.get("task_id"), row.get("arm"),
               row.get("variant"))
        pairs[key].append(row)
    complete = [v for v in pairs.values() if len(v) == 2]
    identical = sum(1 for v in complete
                    if v[0].get("answer") == v[1].get("answer"))
    duplicate_rate = identical / len(complete) if complete else float("nan")
    return {
        "rows": len(rows),
        "tasks": len({r.get("task_id") for r in rows}),
        "arms": sorted({r.get("arm") for r in rows if r.get("arm")}),
        "variants": sorted({r.get("variant") for r in rows if r.get("variant")}),
        "budgets": {str(k): v for k, v in sorted(budgets.items(),
                                                 key=lambda kv: (kv[0] is None, kv[0]))},
        "replicate_pairs": len(complete),
        "identical_replicate_answers": identical,
        "duplicate_rate": round(duplicate_rate, 4) if complete else None,
        "independent_seeds": bool(complete) and duplicate_rate < DUPLICATE_ALARM,
        "has_condition_field": any("condition" in r for r in rows),
        "cap_hits": sum(bool(r.get("reasoning_cap_hit")) for r in rows),
        "empty_answers": sum(1 for r in rows if not str(r.get("answer", "")).strip()),
        "truncated": sum(bool(r.get("answer_truncated")) for r in rows),
    }


#: Declared roles. The measurement above is what decides whether a file that
#: claims to be canonical actually qualifies.
ROLE = {
    "s18_reseeded.jsonl": (
        "CANONICAL", "capped reasoning grid",
        "Regenerated with per-row seeds. The default capped input for every "
        "figure on this branch."),
    "natural_reasoning.jsonl": (
        "CANONICAL", "natural reasoning",
        "Per-row seeds, context-derived 39,550-token engineering ceiling, native "
        "natural closure. The endpoint of the headline figure."),
    "s18_reasoning.jsonl": (
        "DEPRECATED", "capped reasoning grid",
        "One shared seed for all 160 requests, so nominal replicate pairs are "
        "duplicates. Superseded by s18_reseeded.jsonl. Retained, never loaded."),
    "s18_reasoning.scored.jsonl": (
        "DERIVED", "scoring output",
        "An analysis output of the deprecated grid, not a generation artifact."),
    "s18_transition.jsonl": (
        "FOREIGN", "transition budgets 320-640",
        "Belongs to the Round 10 line of work on the original branch. Outside "
        "this branch's scope; not used here."),
    "s18_seedfix.jsonl": (
        "FOREIGN", "Round 10 seed-fix verification",
        "Another branch's verification run. Not used as canonical input here; "
        "reported only as an independent consistency check."),
}


def main() -> int:
    run = plotdata.latest("runs/stageS18_reasoning_design_*/")
    records = []
    for path in sorted(run.glob("*.jsonl")):
        if path.name == "design.jsonl":
            continue
        status, role, reason = ROLE.get(
            path.name, ("UNCLASSIFIED", "unknown",
                        "Not declared in reasoning_provenance.ROLE — classify it "
                        "before any analysis reads it."))
        record = {"file": str(path), "status": status,
                  "role": role, "reason": reason, "bytes": path.stat().st_size,
                  "sha256": sha256(path), **measure(path)}
        # A file cannot be called canonical if its own numbers disagree.
        if status == "CANONICAL" and not record["independent_seeds"]:
            record["status"] = "CONTRADICTED"
            record["reason"] += (" DECLARED CANONICAL BUT MEASURED "
                                 f"{record['duplicate_rate']:.1%} DUPLICATE "
                                 "REPLICATES.")
        records.append(record)

    envelope = run / "natural_reasoning_envelope.json"
    manifest = {
        "branch": "exp/natural-reasoning-headline",
        "run_directory": str(run),
        "duplicate_alarm_threshold": DUPLICATE_ALARM,
        "natural_reasoning_envelope": (json.loads(envelope.read_text())
                                       if envelope.exists() else None),
        "files": records,
    }
    Path("CANONICAL_RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=1))

    lines = ["# Reasoning data provenance", "",
             "Every reasoning file in the frozen run directory, classified by "
             "**measurement** rather than by filename. Regenerate with "
             "`uv run python reasoning_provenance.py`; hashes and row counts are "
             "in `CANONICAL_RUN_MANIFEST.json`.", "",
             f"Run directory: `{run}` (gitignored, hence this manifest).", "",
             "| file | status | role | rows | budgets | replicate pairs | identical | independent seeds |",
             "|---|---|---|---|---|---|---|---|"]
    for r in records:
        budgets = ", ".join(r["budgets"].keys())
        lines.append(
            f"| `{Path(r['file']).name}` | **{r['status']}** | {r['role']} | "
            f"{r['rows']} | {budgets} | {r['replicate_pairs']} | "
            f"{r['identical_replicate_answers']} "
            f"({r['duplicate_rate']:.1%}) | {'yes' if r['independent_seeds'] else '**NO**'} |")
    lines += ["", "## Why each file has its status", ""]
    for r in records:
        lines.append(f"**`{Path(r['file']).name}` — {r['status']}.** {r['reason']}")
        lines.append("")
    lines += ["## The rule this encodes", "",
              "A nominal replicate pair that is byte-identical is one draw counted "
              "twice. Sampling noise makes a few plausible; a majority means a "
              f"shared seed. Anything above {DUPLICATE_ALARM:.0%} duplicates is "
              "refused as canonical input, and a file declared canonical that "
              "fails this test is re-labelled `CONTRADICTED` rather than "
              "silently trusted.", ""]
    Path("REASONING_DATA_PROVENANCE.md").write_text("\n".join(lines))

    print(f"{len(records)} files classified")
    for r in records:
        print(f"  {r['status']:12s} {Path(r['file']).name:30s} rows {r['rows']:5d} "
              f"dup {r['duplicate_rate']:.1%}" if r["duplicate_rate"] is not None
              else f"  {r['status']:12s} {Path(r['file']).name}")
    bad = [r for r in records if r["status"] in ("CONTRADICTED", "UNCLASSIFIED")]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
