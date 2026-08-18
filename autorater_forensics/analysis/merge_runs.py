"""Merge the three matched Inspect runs by sample ID and derive the
cross-reasoning comparison tables.

    .venv/bin/python analysis/merge_runs.py [logs_root] [out_dir]

Reads the newest .eval log in logs/{low,medium,high}, aligns samples by
stable ID, and writes:

    analysis/out/merged.jsonl   full per-sample rows (incl. reasoning)
    analysis/out/merged.csv     tabular view without long texts
    analysis/out/report.md      transition tables + pattern listings

The full transition structure across low/medium/high is retained;
nothing is reduced to a single agreement percentage. All judgments are
diagnostic observables of a proxy instrument — never human validation,
ground truth, or semantic correctness.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[1]
EFFORTS = ("low", "medium", "high")

WORDS = {"zero": 0, "one": 1, "once": 1, "two": 2, "twice": 2,
         "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def newest_log(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    if not logs:
        raise SystemExit(f"no eval logs in {log_dir}")
    return read_eval_log(sorted(logs, key=lambda l: l.name)[-1])


def claimed_count(reasoning: str) -> int | None:
    """Last count the reasoning claims (deterministic heuristic)."""
    text = (reasoning or "").lower()
    claims = []
    for pat in (r"count(?:ed)?(?: is|:| =)? ?(\d+)",
                r"appears (?:only |exactly )?(\w+) times?",
                r"that'?s (\d+)\b", r"total(?: is|:| =)? ?(\d+)"):
        for m in re.finditer(pat, text):
            t = m.group(1)
            v = int(t) if t.isdigit() else WORDS.get(t)
            if v is not None:
                claims.append(v)
    return claims[-1] if claims else None


def implied_reasoning_label(reasoning: str) -> str | None:
    """The verdict the reasoning itself decides on: the LAST uppercase
    quoted label token. (A lowercase-phrase heuristic was tried first
    and systematically misread gpt-oss's format meta-commentary — e.g.
    'The first line must be exactly one word: VIOLATES … That
    satisfies.' — as a SATISFIES verdict; refined after manual
    inspection of flagged samples.)"""
    # Quoted alternatives in format reminders ('"SATISFIES" or
    # "VIOLATES"') are not decisions; strip them first (second
    # refinement from manual inspection).
    cleaned = re.sub(r"(?:\"|')?SATISFIES(?:\"|')?\s+or\s+(?:\"|')?VIOLATES(?:\"|')?", " ",
                     reasoning or "")
    hits = re.findall(r"\b(SATISFIES|VIOLATES)\b", cleaned)
    if not hits:
        return None
    return "pass" if hits[-1] == "SATISFIES" else "fail"


def merge(logs_root: Path, out_dir: Path) -> None:
    runs = {}
    for effort in EFFORTS:
        log = newest_log(logs_root / effort)
        cfg = log.plan.config
        run = {}
        for sample in log.samples:
            score = sample.scores["judge_parse"]
            meta = score.metadata
            run[str(sample.id)] = {
                "label": meta.get("parsed_label"),
                "status": meta.get("status"),
                "truncated": meta.get("truncated"),
                "stop_reason": meta.get("stop_reason"),
                "reasoning_chars": meta.get("reasoning_chars"),
                "final_chars": meta.get("final_chars"),
                "completion_tokens": meta.get("completion_tokens"),
                "reasoning_text": meta.get("reasoning_text"),
                "final_text": meta.get("final_text"),
                "sample_metadata": sample.metadata,
                "error": str(sample.error) if sample.error else None,
            }
        runs[effort] = {"samples": run,
                        "config": {
                            "temperature": cfg.temperature,
                            "top_p": cfg.top_p,
                            "max_tokens": cfg.max_tokens,
                            "seed": cfg.seed,
                            "extra_body": cfg.extra_body},
                        "model": str(log.eval.model),
                        "log_file": log.location}
    ids = sorted(set.intersection(*(set(runs[e]["samples"])
                                    for e in EFFORTS)))
    all_ids = set.union(*(set(runs[e]["samples"]) for e in EFFORTS))
    if set(ids) != all_ids:
        print(f"WARNING: {len(all_ids) - len(ids)} samples not present "
              f"in all three runs")

    rows = []
    for sid in ids:
        meta = runs["high"]["samples"][sid]["sample_metadata"]
        row = {
            "id": sid,
            "deterministic_verifier_label":
                meta["deterministic_verifier_label"],
            "source_model": meta["source_model"],
            "source_pool": meta["source_pool"],
            "target_n": meta["target_n"],
            "s0_count": meta["s0_count"],
            "response_length": meta["response_chars"],
            "contested": meta["contested"],
            "contested_reasons": meta["contested_reasons"],
        }
        for effort in EFFORTS:
            s = runs[effort]["samples"][sid]
            row[f"{effort}_label"] = s["label"]
            row[f"{effort}_status"] = s["status"]
            row[f"{effort}_truncated"] = s["truncated"]
            row[f"{effort}_reasoning_tokens_est"] = (
                None if not s["completion_tokens"] else round(
                    s["completion_tokens"] * s["reasoning_chars"]
                    / max(1, s["reasoning_chars"] + s["final_chars"])))
            row[f"{effort}_reasoning_chars"] = s["reasoning_chars"]
            row[f"{effort}_completion_tokens"] = s["completion_tokens"]
            row[f"{effort}_reasoning_text"] = s["reasoning_text"]
            row[f"{effort}_final_text"] = s["final_text"]
        v = row["deterministic_verifier_label"]

        def eq(a, b):
            return a is not None and a == b
        low, med, high = (row["low_label"], row["medium_label"],
                          row["high_label"])
        rc_high = claimed_count(row["high_reasoning_text"])
        implied = implied_reasoning_label(row["high_reasoning_text"])
        row["patterns"] = sorted(p for p, hit in {
            "low_ne_medium": low != med,
            "medium_ne_high": med != high,
            "low_eq_verifier_high_ne": eq(low, v) and high is not None
                and high != v,
            "high_eq_verifier_low_ne": eq(high, v) and low is not None
                and low != v,
            "reasoning_grows_label_constant":
                eq(low, high) and row["low_reasoning_chars"] > 0
                and row["high_reasoning_chars"]
                >= 3 * row["low_reasoning_chars"],
            "truncation_at_higher_effort":
                row["high_truncated"] and not row["low_truncated"],
            "reasoning_correct_count_wrong_label":
                rc_high is not None and rc_high == row["s0_count"]
                and high is not None and high != v,
            "reasoning_final_contradiction":
                implied is not None and high is not None
                and implied != high,
        }.items() if hit)
        rows.append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "merged.jsonl").write_text("".join(
        json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    slim_keys = [k for k in rows[0]
                 if not k.endswith(("_reasoning_text", "_final_text"))]
    import csv
    with (out_dir / "merged.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=slim_keys,
                                extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (json.dumps(r[k])
                                 if isinstance(r[k], (list, dict))
                                 else r[k]) for k in slim_keys})

    # ------------------------------------------------------ report.md
    lines = ["# Cross-reasoning comparison (low / medium / high)\n"]
    for effort in EFFORTS:
        cfg = runs[effort]["config"]
        lines.append(f"- {effort}: model={runs[effort]['model']} "
                     f"config={cfg} log={runs[effort]['log_file']}")
    lines.append(f"\nSamples aligned across all three runs: {len(rows)} "
                 f"(contested {sum(1 for r in rows if r['contested'])}, "
                 f"control "
                 f"{sum(1 for r in rows if not r['contested'])})\n")

    def key3(row, field):
        return tuple((row[f"{e}_{field}"] or "-") for e in EFFORTS)
    for field in ("label", "status"):
        lines.append(f"\n## Full (low, medium, high) {field} "
                     f"transition structure\n")
        lines.append("| low | medium | high | contested | control |")
        lines.append("|---|---|---|---|---|")
        table = Counter((key3(r, field), r["contested"]) for r in rows)
        triples = sorted({k for k, _ in table})
        for t in triples:
            lines.append(f"| {t[0]} | {t[1]} | {t[2]} | "
                         f"{table[(t, True)]} | {table[(t, False)]} |")
    lines.append("\n## Pattern incidence\n")
    pat_counts = Counter(p for r in rows for p in r["patterns"])
    for pat, count in pat_counts.most_common():
        lines.append(f"- **{pat}**: {count}")
        ids_list = [r["id"] for r in rows if pat in r["patterns"]]
        lines.append(f"  - {', '.join(ids_list[:12])}"
                     + (" …" if len(ids_list) > 12 else ""))
    lines.append("\nPer-sample pattern flags and full reasoning traces: "
                 "`merged.jsonl`; open individual samples in Inspect "
                 "View. Reasoning traces are diagnostic observables, "
                 "not guaranteed faithful explanations.\n")
    (out_dir / "report.md").write_text("\n".join(lines))
    print(f"merged {len(rows)} samples -> {out_dir}")
    print("\n".join(lines[lines.index('\n## Pattern incidence\n'):]
                    [:24]))


if __name__ == "__main__":
    logs_root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "logs"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 \
        else ROOT / "analysis" / "out"
    merge(logs_root, out_dir)
