"""Balanced, randomly sampled forensic packet for human reading.

Strata are declared in advance and sampled uniformly WITHIN stratum, so the
packet cannot become a tour of the most dramatic examples. Classification of
what the model is doing differently is done by a person reading these, not by a
model judging them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from dci_exploratory.forensics import classify_failure, structural_features


def build(run_dir: Path, seed: int = 7, per_stratum: int = 5) -> dict[str, Any]:
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    n_target = int(config["harvest_provenance"]["exact_sentence_count"])
    focal = config["selection"]["focal"]
    ordinary = [r for r in config["selection"]["references"] if r != "S_SEMICOLON"]

    feats = structural_features(frame)
    feats["mode"] = feats.apply(
        lambda r: classify_failure(r, n_target) if r["scorable"] else "unscorable",
        axis=1)
    contrast = feats[feats["condition"].isin(["focal", "reference"])]
    rng = np.random.default_rng(seed)

    # Units whose verdict FLIPS when only the instruction order is reversed.
    wide = contrast[contrast["scorable"]].pivot_table(
        index=["arm", "task_id", "replicate"], columns="order",
        values="a_failure", aggfunc="first").dropna()
    flipped = wide[wide["o_A"] != wide["o_Q"]].reset_index()
    flip_keys = set(zip(flipped["arm"], flipped["task_id"], flipped["replicate"]))

    # Tasks that fail repeatedly in the focal arm.
    focal_rows = contrast[(contrast["arm"] == focal) & contrast["scorable"]]
    per_task = focal_rows.groupby("task_id")["a_failure"].mean()
    vulnerable = set(per_task[per_task >= 0.5].index)

    strata = {
        "focal_oQ_failure": contrast[(contrast["arm"] == focal)
                                     & (contrast["order"] == "o_Q")
                                     & (contrast["a_failure"] == 1)],
        "focal_oQ_success": contrast[(contrast["arm"] == focal)
                                     & (contrast["order"] == "o_Q")
                                     & (contrast["a_failure"] == 0)],
        "focal_oA_any": contrast[(contrast["arm"] == focal)
                                 & (contrast["order"] == "o_A")],
        "semicolon_reference_failure": contrast[(contrast["arm"] == "S_SEMICOLON")
                                                & (contrast["a_failure"] == 1)],
        "semicolon_reference_success": contrast[(contrast["arm"] == "S_SEMICOLON")
                                                & (contrast["a_failure"] == 0)],
        "ordinary_reference_failure": contrast[contrast["arm"].isin(ordinary)
                                               & (contrast["a_failure"] == 1)],
        "order_flip": contrast[contrast.apply(
            lambda r: (r["arm"], r["task_id"], r["replicate"]) in flip_keys, axis=1)],
        "repeatedly_vulnerable_task": contrast[contrast["task_id"].isin(vulnerable)
                                               & (contrast["arm"] == focal)],
    }

    picked: dict[str, list[str]] = {}
    for name, pool in strata.items():
        ids = sorted(pool["row_id"].tolist())
        k = min(per_stratum, len(ids))
        picked[name] = sorted(rng.choice(ids, size=k, replace=False).tolist()) if k else []

    strata_of: dict[str, list[str]] = {}
    for name, ids in picked.items():
        for row_id in ids:
            strata_of.setdefault(row_id, []).append(name)

    indexed = feats.set_index("row_id")
    cases = []
    for row_id, names in sorted(strata_of.items()):
        row = indexed.loc[row_id]
        cases.append({
            "row_id": row_id, "strata": names,
            "task_id": row["task_id"], "topic": row["topic"],
            "arm": row["arm"], "condition": row["condition"], "order": row["order"],
            "replicate": int(row["replicate"]), "pair_key": row["pair_key"],
            "user_prompt": row["user_prompt"],
            "response": row["response"],
            "observed_sentences": (None if pd.isna(row["observed_sentences"])
                                   else int(row["observed_sentences"])),
            "mode": row["mode"],
            "a_failure": None if pd.isna(row["a_failure"]) else int(row["a_failure"]),
            "n_semicolons": int(row["n_semicolons"]),
            "n_periods": int(row["n_periods"]),
            "n_commas": int(row["n_commas"]),
            "n_newlines": int(row["n_newlines"]),
            "generated_token_count": (None if pd.isna(row["generated_token_count"])
                                      else int(row["generated_token_count"])),
            "stop_reason": row["stop_reason"],
            "human_classification": "",
        })

    out = run_dir / "forensics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "packet.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases),
        encoding="utf-8")
    (out / "packet_sample.json").write_text(json.dumps({
        "seed": seed, "per_stratum": per_stratum,
        "counts": {k: len(v) for k, v in picked.items()},
        "pool_sizes": {k: int(len(v)) for k, v in strata.items()},
        "n_unique_cases": len(cases),
    }, indent=2), encoding="utf-8")
    (out / "packet.md").write_text(_markdown(cases, config), encoding="utf-8")
    return {"n_cases": len(cases), "dir": str(out),
            "counts": {k: len(v) for k, v in picked.items()},
            "pool_sizes": {k: int(len(v)) for k, v in strata.items()}}


def _markdown(cases: list[dict[str, Any]], config: dict[str, Any]) -> str:
    lines = ["# Forensic packet — raw prompts and responses", "",
             f"model `{config['model']['model_id']}` @ `{config['model']['revision']}`",
             "", "Sampled uniformly within each declared stratum. "
             "`human_classification` is filled in by a reader.", ""]
    for case in cases:
        lines += [
            "---", "",
            f"## `{case['row_id']}` — arm `{case['arm']}`, order `{case['order']}`",
            "",
            f"- strata: {', '.join(case['strata'])}",
            f"- task `{case['task_id']}` rep {case['replicate']}: {case['topic']}",
            f"- observed sentences: **{case['observed_sentences']}** "
            f"→ mode `{case['mode']}` → a_failure={case['a_failure']}",
            f"- semicolons {case['n_semicolons']}, periods {case['n_periods']}, "
            f"commas {case['n_commas']}, newlines {case['n_newlines']}",
            f"- tokens {case['generated_token_count']}, stop `{case['stop_reason']}`",
            "", "### Prompt", "", "```", case["user_prompt"] or "", "```",
            "", "### Response", "", "```", case["response"] or "<none>", "```",
            "", f"- human_classification: {case['human_classification'] or '_(to fill)_'}", "",
        ]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Build the forensic packet.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--per-stratum", type=int, default=5)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.run_dir, args.seed, args.per_stratum), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
