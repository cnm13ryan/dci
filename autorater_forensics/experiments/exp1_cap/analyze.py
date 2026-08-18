"""E1 analysis: per-run per-sample records + the pre-registered safe-cap
decision (PREREGISTERED.md E1).

    .venv/bin/python experiments/exp1_cap/analyze.py

Reads every run under logs_exp/exp1/<effort>_<cap>/ plus the original
2048-cap runs in logs/<effort> (the 4096-max-len server baseline),
restricted to the E1 sample IDs. Writes:

    analysis/out/exp1_records.jsonl   one record per (run, sample)
    analysis/out/exp1_report.md       cap-stop counts, label-stability
                                      across caps, safe-cap decision
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[2]
EFFORTS = ("low", "medium", "high")
CAPS = (2048, 4096, 8192, 16384)


def newest(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    if not logs:
        return None
    return read_eval_log(sorted(logs, key=lambda l: l.name)[-1])


def extract(log, effort: int, cap: int, source: str):
    rows = {}
    for s in log.samples:
        m = s.scores["judge_parse"].metadata
        rows[str(s.id)] = {
            "id": str(s.id), "effort": effort, "cap": cap,
            "server": source,
            "reasoning_chars": m.get("reasoning_chars"),
            "final_chars": m.get("final_chars"),
            "completion_tokens": m.get("completion_tokens"),
            "stop_reason": m.get("stop_reason"),
            "cap_stop": m.get("stop_reason") == "max_tokens",
            "final_text": m.get("final_text"),
            "label": m.get("parsed_label"),
            "status": m.get("status"),
        }
    return rows


def main():
    e1_ids = {json.loads(l)["id"] for l in
              (ROOT / "dataset" / "exp1_cap.jsonl").read_text()
              .splitlines()}
    runs = {}   # (effort, cap) -> {id: record}
    for effort in EFFORTS:
        base = newest(ROOT / "logs" / effort)
        if base:
            rows = extract(base, effort, 2048, "maxlen4096")
            runs[(effort, 2048, "maxlen4096")] = {
                k: v for k, v in rows.items() if k in e1_ids}
        for cap in CAPS:
            d = ROOT / "logs_exp" / "exp1" / f"{effort}_{cap}"
            if d.exists():
                log = newest(d)
                if log:
                    runs[(effort, cap, "maxlen12288")] = extract(
                        log, effort, cap, "maxlen12288")

    out = ROOT / "analysis" / "out"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "exp1_records.jsonl").open("w") as fh:
        for key in sorted(runs, key=str):
            for sid in sorted(runs[key]):
                fh.write(json.dumps(runs[key][sid],
                                    ensure_ascii=False) + "\n")

    lines = ["# E1 — output-cap search\n",
             f"E1 samples: {len(e1_ids)}\n",
             "| effort | cap | server | judged | cap-stops | invalid |",
             "|---|---|---|---|---|---|"]
    for key in sorted(runs, key=str):
        effort, cap, server = key
        rows = runs[key].values()
        lines.append(
            f"| {effort} | {cap} | {server} | {len(runs[key])} | "
            f"{sum(r['cap_stop'] for r in rows)} | "
            f"{sum(r['status'] != 'valid' for r in rows)} |")

    # label stability between consecutive caps on the 12288 server
    lines.append("\n## Label changes between consecutive caps "
                 "(12288 server)\n")
    decision = {}
    for effort in EFFORTS:
        caps_here = sorted({c for (e, c, s) in runs
                            if e == effort and s == "maxlen12288"})
        lines.append(f"### {effort}: caps {caps_here}")
        safe = None
        for a, b in zip(caps_here, caps_here[1:]):
            ra = runs[(effort, a, "maxlen12288")]
            rb = runs[(effort, b, "maxlen12288")]
            ids = sorted(set(ra) & set(rb))
            changed = [i for i in ids
                       if (ra[i]["label"], ra[i]["status"])
                       != (rb[i]["label"], rb[i]["status"])]
            stops_a = sum(ra[i]["cap_stop"] for i in ids)
            lines.append(f"- {a} -> {b}: {len(changed)} (label,status) "
                         f"changes; cap-stops at {a}: {stops_a}")
            for i in changed:
                lines.append(
                    f"    - {i}: {a}:{ra[i]['label']}/{ra[i]['status']}"
                    f"{' CAP-STOP' if ra[i]['cap_stop'] else ''}"
                    f" -> {b}:{rb[i]['label']}/{rb[i]['status']}"
                    f"{' CAP-STOP' if rb[i]['cap_stop'] else ''}")
            if safe is None and stops_a == 0 and not changed:
                safe = a
        # a cap qualifies only with zero cap-stops AND unchanged at 2x
        decision[effort] = safe
        lines.append(f"- **pre-registered safe cap C*({effort}) = "
                     f"{safe if safe else 'NOT ESTABLISHED <= 8192'}**")

    # paired server-settings factor (E3.3): high@2048 4096-len vs
    # 12288-len
    key_a = ("high", 2048, "maxlen4096")
    key_b = ("high", 2048, "maxlen12288")
    if key_a in runs and key_b in runs:
        ra, rb = runs[key_a], runs[key_b]
        ids = sorted(set(ra) & set(rb))
        flips = [i for i in ids if ra[i]["label"] != rb[i]["label"]]
        same_text = sum(1 for i in ids
                        if ra[i]["final_text"] == rb[i]["final_text"])
        lines.append("\n## Paired server-settings factor "
                     "(high@2048: max-model-len 4096 vs 12288)\n")
        lines.append(f"- paired samples: {len(ids)}; label flips: "
                     f"{len(flips)}; byte-identical final answers: "
                     f"{same_text}")
        for i in flips:
            lines.append(f"    - {i}: {ra[i]['label']}/"
                         f"{ra[i]['status']} -> {rb[i]['label']}/"
                         f"{rb[i]['status']}")

    (out / "exp1_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(json.dumps({"safe_caps": decision}))


if __name__ == "__main__":
    main()
