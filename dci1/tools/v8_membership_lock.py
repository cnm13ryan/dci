#!/usr/bin/env python3
"""Lock the confirmatory model x frame membership before any composed row.

Reads every model's signed MEMBERSHIP record under one confirm root,
applies the study-level allocation rule at the largest LOCAL frame count
(`confirm.precision.allocation_record`), and writes
`reports/dci1v8dev/confirmatory_membership.{json,md}` --- the document
every model's FROZEN record binds by hash and checks its own entry against.

    python3 tools/v8_membership_lock.py --root <confirm root> [--synthetic]
        [--out <path without suffix>]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                          # noqa: E402
from dci1v4.models.registry import MODELS                             # noqa: E402
from dci1v8dev.confirm import MEMBERSHIP_DOCUMENT                     # noqa: E402
from dci1v8dev.confirm import lifecycle as L                          # noqa: E402
from dci1v8dev.confirm import precision as P                          # noqa: E402


def collect(root: pathlib.Path, *, synthetic: bool) -> dict[str, Any]:
    ctx = L.confirm_context(root, synthetic=synthetic)
    models: dict[str, Any] = {}
    for spec in MODELS:
        tree = L.confirm_tree(ctx, spec.model_key)
        path = tree.stage_record(L.STAGE_MEMBERSHIP)
        if not path.exists():
            continue
        payload = L.read_stage_record(tree, L.STAGE_MEMBERSHIP)
        models[spec.model_key] = {
            "membership_record_hash": fs.read_json(path)["record_hash"],
            "frames_entering_local": payload["frames_entering_local"],
            "frames_entering_spectrum": payload["frames_entering_spectrum"],
            "local_eligible": payload["local_eligibility"]["eligible"],
            "local_supported_frames": payload["local_eligibility"]["supported_frames"],
            "topped_up": payload["local_eligibility"]["after_topup"],
            "by_frame": {w: {k: e.get(k) for k in
                             ("state", "enters_local", "enters_spectrum",
                              "n_star", "m_star", "iota_a", "cells_per_block",
                              "local_valid_families")}
                         for w, e in payload["by_frame"].items()},
            "stability": {w: (e.get("stability") or {}).get("n_star", {})
                          .get("p_selected_reproduced")
                          for w, e in payload["by_frame"].items()},
        }
    n_local = {m: len(e["frames_entering_local"]) for m, e in models.items()}
    return {"document": MEMBERSHIP_DOCUMENT, "root": str(root),
            "models": models,
            "allocation": P.allocation_record(n_local),
            "rule": {"local": "LOCAL_SUPPORTED frames of a LOCAL_ELIGIBLE "
                              "model (>= 2 supported frames); all of them",
                     "spectrum": "coverage_identified frames of any model"},
            "no_composed_cells": True}


def render(lock: dict[str, Any]) -> str:
    lines = ["# DCI-1 v8 — confirmatory membership (locked before any composed row)",
             "", f"Produced by `tools/v8_membership_lock.py` from the signed "
             f"`MEMBERSHIP` records under `{lock['root']}`.", "",
             "| model | LOCAL eligible | LOCAL frames | SPECTRUM frames | topped up | P(n* reproduced) by frame |",
             "|---|---|---|---|---|---|"]
    for m, e in sorted(lock["models"].items()):
        st = ", ".join(f"f{w}: {v:.2f}" if v is not None else f"f{w}: —"
                       for w, v in sorted(e["stability"].items()))
        lines.append(f"| `{m}` | {'yes' if e['local_eligible'] else 'no'} | "
                     f"{e['frames_entering_local']} | {e['frames_entering_spectrum']} | "
                     f"{'yes' if e['topped_up'] else 'no'} | {st} |")
    a = lock["allocation"]
    lines += ["", f"**Allocation:** {a['chosen_blocks_per_frame']} blocks per frame "
              f"(decided at {a['decided_at_n_frames']} LOCAL frames, joint family size "
              f"{a['joint_family_size']}; rule met: {a['rule_met_at_chosen']}).",
              "", f"**Precision rule.** {a['precision_rule']}", "",
              f"**Multiplicity rule.** {a['multiplicity_rule']}", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    lock = collect(pathlib.Path(args.root).resolve(), synthetic=args.synthetic)
    out = pathlib.Path(args.out) if args.out else \
        HERE.parent.parent / MEMBERSHIP_DOCUMENT
    out = out.with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n")
    out.with_suffix(".md").write_text(render(lock))
    print(f"wrote {out.with_suffix('.json')}")
    for m, e in sorted(lock["models"].items()):
        print(f"  {m:26s} LOCAL={e['frames_entering_local']} "
              f"SPECTRUM={e['frames_entering_spectrum']}")
    print(f"  allocation: {lock['allocation']['chosen_blocks_per_frame']} blocks/frame")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
