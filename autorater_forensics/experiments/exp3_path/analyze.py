"""E3 analysis: paired execution-path comparisons on the 61 controls,
one factor at a time (PREREGISTERED.md E3).

    .venv/bin/python experiments/exp3_path/analyze.py

Pairs (each table lists exactly which samples changed):
  T1 registered offline round vs original API run   (baseline, per effort)
  T2 API conc=1 vs API conc=4                       (batching in API path)
  T3 API conc=1 vs registered offline               (API minus batching)
  T4 offline chunk32 on 61 items vs registered      (batch COMPOSITION,
     round (chunk32 over ~246/model)                 same engine)
  T5 offline chunk1 vs offline chunk32              (chunk size, same engine)
  T6 offline chunk1 vs API conc=1                   (engine vs server,
                                                     both single-stream)
Plus final-answer byte-identity rates for every pair where raw final
text exists on both sides.
"""
from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[2]
_FINAL = "<|channel|>final<|message|>"
_STOPS = ("<|return|>", "<|end|>", "<|call|>")


def harmony_final(raw: str | None) -> str | None:
    if not raw or _FINAL not in raw:
        return None
    text = raw.rsplit(_FINAL, 1)[1]
    for stop in _STOPS:
        text = text.split(stop, 1)[0]
    return text.strip()


def api_run(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    if not logs:
        return None
    log = read_eval_log(sorted(logs, key=lambda l: l.name)[-1])
    out = {}
    for s in log.samples:
        m = s.scores["judge_parse"].metadata
        out[str(s.id)] = {"label": m.get("parsed_label"),
                          "status": m.get("status"),
                          "final": (m.get("final_text") or "").strip()}
    return out


def offline_run(name: str):
    p = (ROOT / "experiments" / "scratch" / "exp3" / name
         / "judgments.jsonl")
    if not p.exists():
        return None
    out = {}
    for j in map(json.loads, p.read_text().splitlines()):
        out[j["sample_id"]] = {
            "label": j["label"], "status": j["status"],
            "final": harmony_final(j.get("raw_generation")) or ""}
    return out


def pair(lines, title, a, b, name_a, name_b):
    if a is None or b is None:
        lines.append(f"\n## {title}\n\n- SKIPPED (missing run)")
        return None
    ids = sorted(set(a) & set(b))
    flips = [i for i in ids if a[i]["label"] != b[i]["label"]
             or a[i]["status"] != b[i]["status"]]
    both_final = [i for i in ids if a[i]["final"] and b[i]["final"]]
    same_text = [i for i in both_final
                 if a[i]["final"] == b[i]["final"]]
    lines.append(f"\n## {title}\n")
    lines.append(f"- paired: {len(ids)}; (label,status) changes: "
                 f"{len(flips)}; byte-identical final answers: "
                 f"{len(same_text)}/{len(both_final)}")
    for i in flips:
        lines.append(f"    - {i}: {name_a}={a[i]['label']}/"
                     f"{a[i]['status']} vs {name_b}={b[i]['label']}/"
                     f"{b[i]['status']}"
                     + ("  [final text identical -> parser-side]"
                        if i in same_text else
                        "  [final text differs -> generation-side]"))
    return {"paired": len(ids), "flips": len(flips),
            "text_identical": len(same_text),
            "text_compared": len(both_final)}


def main():
    ds = [json.loads(l) for l in
          (ROOT / "dataset" / "diagnostic.jsonl").read_text()
          .splitlines()]
    controls = {r["id"]: r for r in ds if not r["contested"]}
    registered = {e: {i: {"label": r[f"prior_{e}_label"],
                          "status": r[f"prior_{e}_status"],
                          "final": ""}
                      for i, r in controls.items()}
                  for e in ("low", "medium", "high")}
    lines = ["# E3 — execution-path divergence, paired factor tests",
             f"\nControls: {len(controls)}. Registered labels come from "
             "the three registered development rounds (offline seam, "
             "full-round batch composition, chunk 32)."]

    # prompt-identity (E3.2) summary if present
    pid = ROOT / "analysis" / "out" / "exp3_prompt_identity.json"
    if pid.exists():
        s = json.loads(pid.read_text())["summary"]
        lines.append(f"\n## T0 (E3.2) prompt rendering\n\n- offline "
                     f"apply_chat_template vs server /tokenize: "
                     f"{s['mismatches']}/{s['comparisons']} token-ID "
                     f"mismatches over {s['controls']} controls x 3 "
                     f"efforts -> "
                     + ("templating EXCLUDED as a cause"
                        if s["mismatches"] == 0 else "DIVERGENT"))

    summary = {}
    for e in ("low", "high"):
        base = api_run(ROOT / "logs" / e)
        base = ({i: v for i, v in base.items() if i in controls}
                if base else None)
        c1 = api_run(ROOT / "logs_exp" / "exp3" / f"{e}_conc1")
        c4 = api_run(ROOT / "logs_exp" / "exp3" / f"{e}_conc4")
        summary[f"T1_{e}"] = pair(
            lines, f"T1 {e}: registered offline round vs original API "
            f"run (cap 2048)", registered[e], base, "registered", "api")
        summary[f"T2_{e}"] = pair(
            lines, f"T2 {e}: API conc=1 vs API conc=4 (same server, "
            "cap 2048)", c1, c4, "conc1", "conc4")
        summary[f"T3_{e}"] = pair(
            lines, f"T3 {e}: API conc=1 vs registered offline round",
            c1, registered[e], "conc1", "registered")
    off32 = offline_run("offline_high_chunk32_cap2048")
    off1 = offline_run("offline_high_chunk1_cap2048")
    c1h = api_run(ROOT / "logs_exp" / "exp3" / "high_conc1")
    summary["T4"] = pair(
        lines, "T4 high: offline chunk32 on 61 items vs registered "
        "round (same engine, different batch composition)",
        off32, registered["high"], "chunk32/61items", "registered")
    summary["T5"] = pair(
        lines, "T5 high: offline chunk1 vs offline chunk32 (same "
        "engine, chunk size only)", off1, off32, "chunk1", "chunk32")
    summary["T6"] = pair(
        lines, "T6 high: offline chunk1 vs API conc=1 (engine vs "
        "server, both single-stream)", off1, c1h, "offline", "api")

    out = ROOT / "analysis" / "out" / "exp3_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\n" + json.dumps(summary))


if __name__ == "__main__":
    main()
