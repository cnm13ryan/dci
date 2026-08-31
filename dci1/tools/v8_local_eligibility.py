#!/usr/bin/env python3
"""Which (model, frame) combinations enter the LOCAL confirmatory design?

Applies the LOCAL inclusion rule (`dci1v8dev.run.eligibility`, researcher
decision of 2026-08-31, `docs/V8_FRAME_CONDITIONING.md` §4d) to stored
pre-freeze records and reports the answer per model.

The rule is not re-implemented here: the tool imports the same
`local_eligibility` the Gate-3 stage calls, so a stored record written before
the rule existed and a record written after it agree by construction. What
the tool adds is that it can read a record whose `local_eligibility` block
predates the rule, which is why it recomputes from `by_frame[f].survival`
rather than reading the block when one is present --- and it says so when the
two disagree.

**Support is the survival requirement, not the frame state.** A frame in
`LOCAL_AND_SPECTRUM` can hold four LOCAL-valid families and one backup, which
is §13.15 unsatisfied and one admissible substitute short. Reading `state`
would count such a frame as supported; the rule does not.

**The latest run per model wins.** A model's records are its most recent
pilot root, because a later root measured the same model at a different
calibration allocation and the earlier one is superseded for this question
(never overwritten, and both are reported).

    python3 tools/v8_local_eligibility.py --roots dci1v8-pilot-r8 dci1v8-pilot-r9

Reads `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` only. Generates nothing,
names no composed quantity, changes no threshold. Writes
`reports/dci1v8dev/local_eligibility.{md,json}`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v8dev import rules as R                                     # noqa: E402
from dci1v8dev.run import eligibility as EL                          # noqa: E402
from dci1v8dev.run import stages as S                                # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
EVIDENCE = HERE.parent / "evidence"


def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dirs(root: pathlib.Path) -> list[pathlib.Path]:
    base = root / "evidence" / "dci1v8"
    if not base.is_dir():
        base = root / "dci1v8"
    return sorted(d for d in base.iterdir()
                  if d.is_dir() and d.name not in ("keys", "registration"))


def read_root(root: pathlib.Path) -> dict[str, dict[str, Any]]:
    """Every model of one pilot root, with its recomputed eligibility."""
    out: dict[str, dict[str, Any]] = {}
    for model_dir in _model_dirs(root):
        g3 = model_dir / "GATE_3_REFERENCES" / "gate3_references.json"
        if not g3.exists():
            continue
        record = _payload(g3)
        computed = EL.local_eligibility(record["by_frame"], frames=S.FRAMES)
        stored = record.get("local_eligibility")
        out[model_dir.name] = {
            "model": model_dir.name,
            "root": root.name,
            "recorded_at": record.get("recorded_at"),
            "producing_commit": record.get("producing_commit"),
            "calibration_allocation": {
                k: record.get("calibration_allocation", {}).get(k)
                for k in ("passes", "frame_offsets", "topics_per_frame",
                          "topics_per_frame_per_split", "at_topic_ceiling")},
            "frame_states": {w: st["state"]
                             for w, st in record["frame_states"].items()},
            "eligibility": computed,
            # A record written before the rule existed carries no block; one
            # written after must agree with the recomputation exactly.
            "stored_block_present": stored is not None,
            "stored_agrees": (None if stored is None else
                              stored["local_supported_frames"]
                              == computed["local_supported_frames"]
                              and stored["local_eligible"]
                              == computed["local_eligible"]),
        }
    return out


def latest_per_model(by_root: dict[str, dict[str, dict[str, Any]]]
                     ) -> dict[str, dict[str, Any]]:
    """The most recent root that measured each model, by recorded_at."""
    best: dict[str, dict[str, Any]] = {}
    for entries in by_root.values():
        for model, entry in entries.items():
            current = best.get(model)
            if current is None or str(entry["recorded_at"]) > str(current["recorded_at"]):
                best[model] = entry
    return dict(sorted(best.items()))


def _frame_line(w: str, e: dict[str, Any], states: dict[str, str]) -> str:
    if e["local_supported"]:
        return (f"f{w} (state {states[w]}, "
                f"{e['n_local_valid_families']} families, "
                f"{e['n_backups']} backups)")
    reasons = ", ".join(e["local_unsupported_reasons"])
    detail = (f"{e['n_local_valid_families']} families, {e['n_backups']} backups"
              if e["n_local_valid_families"] is not None
              else f"Gate 2: {(e['gate2_unsupported_reason'] or {}).get('status')}")
    return f"f{w}: {reasons} ({detail})"


def render(latest: dict[str, dict[str, Any]],
           by_root: dict[str, dict[str, dict[str, Any]]]) -> str:
    lines = [
        "# DCI-1 v8 — LOCAL frame eligibility",
        "",
        "Produced by `tools/v8_local_eligibility.py` from the signed "
        "`GATE_3_REFERENCES` records. Pre-freeze only: no composed cell, no "
        "Δ_R(f), no pooled statistic enters this verdict.",
        "",
        "**Rule.** " + EL.LOCAL_ELIGIBILITY_RULE + ".",
        "",
        "## The verdict, on the latest run of each model",
        "",
        "| model | root | passes | supported frames | unsupported frames + reason | n | eligible? |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for model, entry in latest.items():
        el = entry["eligibility"]
        states = entry["frame_states"]
        sup = "; ".join(_frame_line(str(w), el["by_frame"][str(w)], states)
                        for w in el["local_supported_frames"]) or "—"
        uns = "; ".join(_frame_line(str(w), el["by_frame"][str(w)], states)
                        for w in sorted(el["local_unsupported_frames"],
                                        key=int)) or "—"
        lines.append(
            f"| `{model}` | `{entry['root']}` | "
            f"{entry['calibration_allocation']['passes']} | {sup} | {uns} | "
            f"{el['n_local_supported_frames']} | "
            f"**{'YES' if el['local_eligible'] else 'NO'}** |")
    lines += [
        "",
        f"Minimum for eligibility: {R.LOCAL_ELIGIBILITY_MIN_FRAMES} frames. "
        "Every supported frame of an eligible model enters; the supported "
        "column is the set that would be generated, not a shortlist.",
        "",
        "## Every root, for the record",
        "",
        "| root | model | frame | state | families | backups | core | LOCAL |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for root in sorted(by_root):
        for model, entry in sorted(by_root[root].items()):
            el = entry["eligibility"]
            for w in S.FRAMES:
                e = el["by_frame"][str(w)]
                lines.append(
                    f"| `{root}` | `{model}` | f{w} | "
                    f"{entry['frame_states'][str(w)]} | "
                    f"{e['n_local_valid_families'] if e['n_local_valid_families'] is not None else '—'} | "
                    f"{e['n_backups'] if e['n_backups'] is not None else '—'} | "
                    f"{'yes' if e['core_identified'] else ('—' if e['core_identified'] is None else 'no')} | "
                    f"{e['local_support_state']}"
                    + (f" ({e['local_unsupported_reason']})"
                       if e["local_unsupported_reason"] else "") + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--roots", nargs="+", required=True,
                    help="pilot roots under dci1/evidence/")
    ap.add_argument("--out", default=str(REPORTS / "local_eligibility"))
    args = ap.parse_args(argv)

    by_root = {}
    for name in args.roots:
        root = pathlib.Path(name)
        if not root.is_absolute() and not root.exists():
            root = EVIDENCE / name
        by_root[root.name] = read_root(root)
    latest = latest_per_model(by_root)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rule": EL.LOCAL_ELIGIBILITY_RULE,
               "min_frames": R.LOCAL_ELIGIBILITY_MIN_FRAMES,
               "latest_per_model": latest, "by_root": by_root}
    out.with_suffix(".json").write_text(json.dumps(payload, indent=1,
                                                   sort_keys=True) + "\n")
    out.with_suffix(".md").write_text(render(latest, by_root))
    print(f"wrote {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    for model, entry in latest.items():
        el = entry["eligibility"]
        print(f"  {model:<26} {entry['root']:<18} "
              f"supported={el['local_supported_frames']} "
              f"eligible={el['local_eligible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
