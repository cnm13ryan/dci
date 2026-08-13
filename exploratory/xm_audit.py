"""Manual audit: stratified sampling for inspection, and leakage triage.

Two jobs, both of which exist because verifier aggregates are not evidence about
what a model actually did.

**Stratified sample.** Five rows per (background x arm) cell per model, plus —
for the focal arm — a sample from each four-state outcome that exists, so the
inspection covers "A pass / B pass", "A pass / B fail", "A fail / B pass" and
"A fail / B fail" rather than whatever the top of the file happens to hold.

**Leakage triage.** The repository's own detector over-flags ordinary prose: the
canonical run's two hits were both benign uses of the word *wait*. So detector
hits are written out as a QUEUE with their context, and the report separates
`detector_hits` from `confirmed_leakage`. A hit is not a finding until a human
has classified it, and this script never fills that column in.

    uv run python xm_audit.py runs/xm_main_*/generations.jsonl --out audit/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract

#: The repository's detector, verbatim from `reasoning_score.py`.
LEAK = re.compile(
    r"\b(wait|let me (check|count|think|see)|i need to|hmm|actually,? (no|wait)|"
    r"let'?s count|recount|that'?s wrong)\b", re.IGNORECASE)

PER_CELL = 5


def score_states(rows: list[dict], state) -> None:
    """Attach A/arm compliance so the sample can be stratified by outcome."""
    for row in rows:
        text = row.get("final_answer") or ""
        if not text.strip():
            row["_a"], row["_arm"], row["_state"] = None, None, "empty"
            continue
        row["_a"] = bool(state.verify(text, contract.TARGET).binary_pass)
        row["_arm"] = bool(state.verify(text, row["arm"]).binary_pass)
        row["_state"] = ("both" if row["_a"] and row["_arm"] else
                         "target only" if row["_a"] else
                         "focal only" if row["_arm"] else "neither")


def stratified(rows: list[dict]) -> list[dict]:
    chosen: list[dict] = []
    seen: set[str] = set()

    def take(pool: list[dict], n: int) -> None:
        for row in sorted(pool, key=lambda r: r["row_id"])[:n]:
            if row["row_id"] not in seen:
                seen.add(row["row_id"])
                chosen.append(row)

    for background in contract.BACKGROUNDS:
        for arm in contract.ARMS:
            take([r for r in rows if r["background"] == background
                  and r["arm"] == arm], PER_CELL)

    # Every four-state outcome that exists, in the focal arm.
    for outcome in ("both", "target only", "focal only", "neither", "empty"):
        take([r for r in rows if r["arm"] == contract.FOCAL
              and r.get("_state") == outcome], 3)

    # Everything that is technically anomalous, in full.
    for row in rows:
        if (row.get("technical_failure") or row.get("answer_empty")
                or row.get("answer_truncated") or row.get("reasoning_cap_hit")
                or row.get("forced_close_artefact")):
            if row["row_id"] not in seen:
                seen.add(row["row_id"])
                chosen.append(row)
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--out", default="audit")
    args = parser.parse_args()

    from dci_exploratory import extensions, harvest

    extensions.register()
    state = harvest.load()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for path in args.files:
        rows = [json.loads(line) for line in Path(path).open()]
        if not rows:
            continue
        model = rows[0]["model_id"]
        mode = rows[0]["reasoning_mode"]
        tag = f"{model.split('/')[-1]}_{mode}"
        score_states(rows, state)

        sample = stratified(rows)
        sample_path = out_dir / f"sample_{tag}.jsonl"
        with sample_path.open("w") as handle:
            for row in sample:
                handle.write(json.dumps({
                    "row_id": row["row_id"], "task_id": row["task_id"],
                    "arm": row["arm"], "background": row["background"],
                    "outcome": row.get("_state"),
                    "a_pass": row.get("_a"), "arm_pass": row.get("_arm"),
                    "reasoning_tokens": row["reasoning_tokens"],
                    "final_answer_tokens": row["final_answer_tokens"],
                    "reasoning_emitted": row.get("reasoning_emitted"),
                    "natural_reasoning_closed": row["natural_reasoning_closed"],
                    "reasoning_cap_hit": row["reasoning_cap_hit"],
                    "forced_close_artefact": row.get("forced_close_artefact"),
                    "answer_truncated": row["answer_truncated"],
                    "final_answer": row["final_answer"],
                    "reasoning_text": row["reasoning_text"][:1500]}) + "\n")

        hits = [r for r in rows if LEAK.search(r.get("final_answer") or "")]
        queue_path = out_dir / f"leakage_queue_{tag}.jsonl"
        with queue_path.open("w") as handle:
            for row in hits:
                triggers = sorted({m.group(0).lower()
                                   for m in LEAK.finditer(row["final_answer"])})
                for trigger in triggers:
                    index = row["final_answer"].lower().find(trigger)
                    context = row["final_answer"][max(0, index - 90):
                                                  index + 90]
                    handle.write(json.dumps({
                        "model_id": model, "reasoning_mode": mode,
                        "task_id": row["task_id"], "arm": row["arm"],
                        "background": row["background"],
                        "row_id": row["row_id"],
                        "trigger": trigger, "context": context,
                        "automated_flag": "DETECTOR_HIT",
                        # Deliberately left blank. A detector hit is not
                        # leakage until a human says it is.
                        "manual_classification": ""}) + "\n")

        summary.append({
            "model_id": model, "reasoning_mode": mode, "rows": len(rows),
            "sample_size": len(sample), "sample_file": str(sample_path),
            "detector_hits": len(hits),
            "confirmed_leakage": None,
            "leakage_queue": str(queue_path),
            "outcomes_present": sorted({r.get("_state") for r in rows
                                        if r["arm"] == contract.FOCAL}),
            "technical_anomalies": sum(
                1 for r in rows if r.get("technical_failure")
                or r.get("answer_empty") or r.get("answer_truncated")
                or r.get("reasoning_cap_hit")
                or r.get("forced_close_artefact")),
        })
        print(f"{tag:44s} sample {len(sample):3d}  detector hits "
              f"{len(hits):3d}  anomalies {summary[-1]['technical_anomalies']}")

    (out_dir / "audit_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"\nwrote {out_dir}/ — 'confirmed_leakage' is null until the queue "
          "has been read by hand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
