#!/usr/bin/env python3
"""Extract a golden-master fixture of the legacy (frame-pooled) pre-screen
from one model's signed pilot records, for the characterization tests.

Read-only and zero-generation. Reads the signed ``REGIME_SCREEN``,
``SECOND_PASS_SCREEN``, ``GATE_1_INSTRUMENT``, ``GATE_2_CALIBRATION`` and
``GATE_3_REFERENCES`` records and the screen's scored rows (loads 0 and 1
only; a composed row cannot exist before a freeze and is refused). Writes
one JSON file holding

* the pooled counts the legacy screen consumed (``prescreen_table``) and
  the per-batch counts the legacy second pass consumed (``batch_counts``);
* the same counts **per wording frame**, recomputed from the scored rows
  with the production kernel ``regime.prescreen_counts`` on each frame's
  own blocks --- the evidence a frame-aware policy reads;
* the screen configuration the records used (seed included);
* the outputs the records carry, so a test can pin them: statuses, labels,
  rankings, per-family scores, the second pass's batch history, the
  forwarded set and the retention plan;
* the frame-specific facts a counterfactual needs: Gate 1's per-frame
  screen coordinates, Gate 2's per-frame operating points and ι_A(f), and
  Gate 3's per-frame LOCAL / SPECTRUM verdicts on the forwarded rungs.

    dci1/.venv/bin/python tools/v8_prescreen_fixture.py \
        --root evidence/dci1v8-pilot-r12 --model gemma-3n-e2b-it \
        --out tests_v8dev/fixtures/legacy_prescreen/gemma-3n-e2b-it.r12.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                       # noqa: E402
from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError, ProtocolError            # noqa: E402
from dci1v7.verifiers.constraints import Constraint                # noqa: E402
from dci1v8dev.confirm.pilot_import import open_pilot              # noqa: E402
from dci1v8dev.run import EVIDENCE_DIRNAME                         # noqa: E402
from dci1v8dev.run import eligibility as EL                        # noqa: E402
from dci1v8dev.run import stages as PS                             # noqa: E402
from dci1v8dev.run.execute import frame_of_block                   # noqa: E402
from dci1v8dev.run.regime import prescreen_counts                  # noqa: E402

DCI1 = HERE.parent
FIXTURES = DCI1 / "tests_v8dev" / "fixtures" / "legacy_prescreen"


def second_pass_record(root: pathlib.Path, model_key: str) -> dict[str, Any]:
    base = root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    path = (base / model_key / PS.STAGE_SECOND_PASS / "records"
            / PS.STAGE_RECORD_FILES[PS.STAGE_SECOND_PASS])
    if not path.exists():
        raise IntegrityError(f"{model_key}: no signed SECOND_PASS_SCREEN "
                             f"record at {path}")
    record = fs.read_json(path)
    payload = verify_signed(record, key, where=f"{model_key}:SECOND_PASS_SCREEN")
    return payload, record["record_hash"]


def scored_rows(model_dir: pathlib.Path, stage: str, run: str
                ) -> list[dict[str, Any]]:
    path = model_dir / stage / "backend_runs" / run / "scored.jsonl"
    if not path.exists():
        raise IntegrityError(f"no scored rows at {path}")
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]
    for row in rows:
        if row.get("load", 0) > 1 or len([s for s in row["scores"]
                                          if s.get("present")]) > 1:
            raise ProtocolError(f"{row['row_id']}: a composed row; the "
                                "fixture reads loads 0 and 1 only")
    return rows


COUNT_COLUMNS = ("kind", "severity", "solo_k", "solo_n", "chance_k", "chance_n",
                 "vacuous_k", "n_topics", "draws_per_topic", "reserve")


def columnar(rows: Sequence[Mapping[str, Any]],
             columns: Sequence[str] = COUNT_COLUMNS) -> dict[str, Any]:
    """Rows of equal shape as one column header plus value lists: the same
    information at a quarter of the bytes. ``expand`` inverts it."""
    return {"columns": list(columns),
            "rows": [[row.get(c) for c in columns] for row in rows]}


def expand(table: Mapping[str, Any]) -> list[dict[str, Any]]:
    cols = table["columns"]
    return [dict(zip(cols, row)) for row in table["rows"]]


def rungs_of(counts: Sequence[Mapping[str, Any]]) -> list[Constraint]:
    return [Constraint(r["kind"], int(r["severity"]), reserve=bool(r.get("reserve")))
            for r in counts]


def counts_by_frame(rows: Sequence[Mapping[str, Any]],
                    rungs: Sequence[Constraint]) -> dict[str, list[dict[str, Any]]]:
    """``regime.prescreen_counts`` on each frame's own blocks."""
    out: dict[str, list[dict[str, Any]]] = {}
    for frame in PS.FRAMES:
        frame_rows = [r for r in rows if frame_of_block(r) == frame]
        if not frame_rows:
            continue
        counts = prescreen_counts(frame_rows, rungs)
        for row in counts:
            row["reserve"] = bool(next(c.reserve for c in rungs
                                       if c.kind == row["kind"]
                                       and c.severity == row["severity"]))
        out[str(frame)] = columnar(counts)
    return out


def family_summary(screen: Mapping[str, Any]) -> dict[str, Any]:
    return {k: {"status": v["status"], "labels": list(v["labels"]),
                "p_spectrum": v["p_spectrum"],
                "score_local": v["score_local"],
                "local_rungs": list(v["local_rungs"]),
                "deficiency": v.get("deficiency"),
                "resolved_by": v.get("resolved_by"),
                "rungs": {"columns": ["candidate", "p_admissible", "p_local",
                                      "iota_mean"],
                          "rows": [[r["candidate"], r["p_admissible"],
                                    r["p_local"], r["iota_mean"]]
                                   for r in v["rungs"]]}}
            for k, v in sorted(screen["families"].items())}


def build(root: pathlib.Path, model_key: str) -> dict[str, Any]:
    source = open_pilot(root, model_key)
    second, second_hash = second_pass_record(root, model_key)
    regime, gate1, gate2, gate3 = (source.regime, source.gate1, source.gate2,
                                   source.gate3)
    model_dir = source.model_dir
    ladder = scored_rows(model_dir, PS.STAGE_REGIME, "ladder")
    rungs = rungs_of(regime["prescreen_table"])
    batches: dict[str, Any] = {}
    for b in second["batches"]:
        rows = scored_rows(model_dir, PS.STAGE_SECOND_PASS, b["run"])
        counts = second["batch_counts"][str(b["index"])]
        batches[str(b["index"])] = {
            "index": b["index"], "run": b["run"], "rungs": list(b["rungs"]),
            "families": list(b["families"]), "n_topics": len(b["topic_ids"]),
            "counts": columnar(counts),
            "counts_by_frame": counts_by_frame(rows, rungs_of(counts)),
        }
    forwarded = list(second["forwarded_set"])
    g2_frames = {}
    for w in PS.FRAMES:
        f2 = gate2["by_frame"][str(w)]
        entry: dict[str, Any] = {"status": f2.get("status")}
        if f2.get("status") == PS.FRAME_SUPPORTED:
            entry.update({
                "n_star": f2["n_star"], "m_star": f2["m_star"],
                "iota_a": f2["iota_a"], "kappa_a": f2["kappa_a"],
                "solo_compliance_a": f2["solo_compliance_a"],
                "n_topics_a": f2["n_topics_a"],
                "iota_a_by_split": f2["iota_a_by_split"],
                "a_per_topic_by_split": f2["a_per_topic_by_split"],
                "calibration_iota": {
                    f"{r['kind']}:{r['severity']}": {
                        "solo": r["solo_compliance"],
                        "chance": r["chance_compliance"],
                        "n_topics": r.get("n_topics")}
                    for r in f2["calibration_rows"]["pooled"]},
                "withheld_degenerate": [
                    f"{r['kind']}:{r['severity']}"
                    for r in f2["calibration_rows_withheld"].get("pooled", [])],
            })
        else:
            entry["unsupported_reason"] = f2.get("unsupported_reason")
        g2_frames[str(w)] = entry
    g3_frames = {}
    for w in PS.FRAMES:
        f3 = gate3["by_frame"][str(w)]
        if f3.get("status") != PS.FRAME_SUPPORTED:
            g3_frames[str(w)] = {"status": f3.get("status"),
                                 "state": f3.get("state")}
            continue
        s = f3["survival"]
        g3_frames[str(w)] = {
            "status": f3["status"], "state": f3["state"],
            "local_valid": sorted(k for k, v in f3["local"].items() if v["passed"]),
            "spectrum_valid": sorted(k for k, v in f3["spectrum"].items()
                                     if v["passed"]),
            "local_first_failing": {k: v.get("first_failing_component")
                                    for k, v in sorted(f3["local"].items())},
            "spectrum_side": {k: v.get("side") for k, v in sorted(f3["spectrum"].items())
                              if v["passed"]},
            "local_valid_families": list(s["local_valid_families"]),
            "core_references": [f"{c['family']}:{c['severity']}"
                                for c in s["core_references"]],
            "core_identified": s["core_identified"],
            "coverage_identified": s["coverage_identified"],
            "selected_families": list(s["selected_families"]),
            "selected_points": [p["candidate"] for p in
                                f3["spectrum_selection"].get("points", ())],
            "backups": list(s["backups"]), "n_backups": s["n_backups"],
            "local_supported": s.get("local_supported"),
            "n_local_valid_families": s["n_local_valid_families"],
        }
    eligibility = EL.local_eligibility(gate3["by_frame"], frames=PS.FRAMES)
    fc = gate1.get("frame_comparison_screen") or {}
    gate1_screen = {
        "columns": ["iota", "se_iota", "n_topics", "exact_compliance"],
        "by_label": {label: {f: [v.get("iota"), v.get("se_iota"),
                                 v.get("n_topics"), v.get("exact_compliance")]
                             for f, v in (block.get("frames") or {}).items()}
                     for label, block in sorted(fc.items())}}
    return {
        "model_key": model_key, "root": root.name, "study_id": source.study_id,
        "manifest_hash": source.manifest_hash,
        "record_hashes": {**source.record_hashes,
                          PS.STAGE_SECOND_PASS: second_hash},
        "producing_commit": {"regime": regime.get("producing_commit"),
                             "second_pass": second.get("producing_commit"),
                             "gate2": gate2.get("producing_commit")},
        "reads": "loads 0 and 1 of REGIME_SCREEN and SECOND_PASS_SCREEN rows; "
                 "signed records of REGIME_SCREEN, SECOND_PASS_SCREEN, "
                 "GATE_1_INSTRUMENT, GATE_2_CALIBRATION, GATE_3_REFERENCES",
        "screen_config": regime["screen"]["config"],
        "second_pass_screen_config": second["screen"]["config"],
        "rescreen_config": second["rescreen_config"],
        "retention_config": second["retention"]["config"],
        "selected_cap": regime["selected_cap"],
        "prescreen_table": columnar(regime["prescreen_table"]),
        "prescreen_table_by_frame": counts_by_frame(ladder, rungs),
        "iota_a_prescreen": regime["iota_a_prescreen"],
        "iota_a_prescreen_severity": regime.get("iota_a_prescreen_severity"),
        "screen_rows_by_frame": {
            str(f): {"n_rows": sum(1 for r in ladder if frame_of_block(r) == f),
                     "n_topics": len({r["topic_id"] for r in ladder
                                      if frame_of_block(r) == f})}
            for f in PS.FRAMES},
        "batches": batches,
        "expected": {
            "regime": {
                "statuses": regime["screen"]["statuses"],
                "labels": regime["screen"]["labels"],
                "ranking_spectrum": regime["screen"]["ranking_spectrum"],
                "ranking_local": regime["screen"]["ranking_local"],
                "iota_a": regime["screen"]["iota_a"],
                "iota_a_prescreen_point": regime["screen"]["iota_a_prescreen_point"],
                "summary": regime["screen"]["summary"],
                "families": family_summary(regime["screen"]),
            },
            "second_pass": {
                "batches_used": second["batches_used"],
                "resolved_at_max": second["resolved_at_max"],
                "history": [{"batch": h["batch"], "statuses": h["statuses"],
                             "p_spectrum": {k: round(v, 6) for k, v in
                                            h["p_spectrum"].items()}}
                            for h in second["history"]],
                "cost_generations": second["cost_generations"],
                "statuses": second["screen"]["statuses"],
                "labels": second["screen"]["labels"],
                "iota_a": second["screen"]["iota_a"],
                "families": family_summary(second["screen"]),
                "forwarded_set": forwarded,
                "n_forwarded": second["n_forwarded"],
                "retention": second["retention"],
                "calibration_cost_generations":
                    second["calibration_cost_generations"],
            },
        },
        "gate1_frame_comparison_screen": gate1_screen,
        "gate2_by_frame": g2_frames,
        "gate2_calibration_population": gate2["calibration_population"],
        "gate2_extension_measured": gate2["extension"]["measured"],
        "gate3_by_frame": g3_frames,
        # Computed by the rule from every frame's survival block, never read
        # from a key: a record written before the rule existed (r9) has none.
        "local_eligibility": {
            "supported": eligibility["local_supported_frames"],
            "eligible": eligibility["local_eligible"]},
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root)
    root = (root if root.is_absolute() else DCI1 / root).resolve()
    fixture = build(root, args.model)
    out = (pathlib.Path(args.out) if args.out
           else FIXTURES / f"{args.model}.{root.name.rpartition('-')[2]}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":"))
                   + "\n")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
