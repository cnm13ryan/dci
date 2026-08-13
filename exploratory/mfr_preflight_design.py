"""Build the boundary-control preflight design.

Two things about this design are deliberate and load-bearing.

**It never contains the focal instruction.** Every combined row uses `C_L3` in
the focal slot, so no row of this design can yield a focal-versus-reference
contrast. The control is therefore selected on compliance and rendering alone,
and it is not merely a promise not to look at τ — τ is not computable from these
generations.

**It never touches the 20 evaluation tasks.** It draws from the `calibration`
split, which no run in this repository has used and whose topics do not overlap
the pilot set.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest

#: The semicolon is measured alongside the candidates, not assumed: the choosing
#: rule asks which candidate's compliance is CLOSEST to it, which needs its value
#: on the same material.
MARKS = ("X_SEMICOLON_FREE", "X_DEGREE_FREE", "X_ASTERISK_FREE")
REFERENCE = "C_L3"
TARGET = "A"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--tasks", type=int, default=12)
    parser.add_argument("--replicates", type=int, default=2)
    parser.add_argument("--split", default="calibration")
    args = parser.parse_args()

    extensions.register()
    state = harvest.load()
    tasks = [t for t in state.TASKS.to_dict("records")
             if t["split"] == args.split][:args.tasks]
    if len(tasks) != args.tasks:
        raise SystemExit(f"{args.split} split holds {len(tasks)} tasks")

    main_tasks = {t["task_id"] for t in state.TASKS.to_dict("records")
                  if t["split"] == "pilot"}
    overlap = {t["task_id"] for t in tasks} & main_tasks
    if overlap:
        raise SystemExit(f"preflight would reuse main evaluation tasks: {overlap}")

    rows = []
    for task in tasks:
        for mark in MARKS:
            # "isolated" is the mark alone; "combined" is QAC with the REFERENCE
            # in the focal slot, which is the main design's reference arm exactly.
            for kind, ids in (("isolated", [mark]),
                              ("combined", [REFERENCE, TARGET, mark])):
                for replicate in range(args.replicates):
                    rows.append({
                        "row_id": hashlib.blake2b(
                            f"preflight|{task['task_id']}|{mark}|{kind}|{replicate}"
                            .encode(), digest_size=10).hexdigest(),
                        "stage": "MFR_boundary_preflight",
                        "task_id": task["task_id"], "topic": task["topic"],
                        "prompt_kind": kind, "condition": "reference",
                        "arm": REFERENCE if kind == "combined" else mark,
                        "measured": TARGET if kind == "combined" else mark,
                        "order": "QAC" if kind == "combined" else "single",
                        "load": len(ids), "replicate": replicate,
                        "ordered_ids": ids, "paraphrase_id": 0,
                        "user_prompt": harvest.compose_prompt(task["topic"], ids, 0),
                        "pair_key": f"{task['task_id']}|{kind}|r{replicate}",
                        "variant": mark})

    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("preflight rows are not uniquely identified")

    # The three marks must differ only in the mark name, in both prompt kinds.
    for kind in ("isolated", "combined"):
        for task in tasks:
            texts = {r["variant"]: r["user_prompt"] for r in rows
                     if r["task_id"] == task["task_id"] and r["prompt_kind"] == kind}
            base = texts["X_SEMICOLON_FREE"]
            for cid, name in (("X_DEGREE_FREE", "degree symbol (°)"),
                              ("X_ASTERISK_FREE", "asterisk (*)")):
                if texts[cid] != base.replace("semicolon", name):
                    raise SystemExit(f"{cid} differs from the semicolon prompt by "
                                     f"more than the mark name ({kind})")
    print(f"[check] all three marks render identically apart from the mark name, "
          f"in both prompt kinds, on all {len(tasks)} tasks")

    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"[design] {len(rows)} rows | {len(tasks)} {args.split} tasks | "
          f"{len(MARKS)} marks | 2 prompt kinds | {args.replicates} replicates")
    print(f"[out] {args.out}")
    print(f"[disjoint] 0 of the 20 evaluation tasks appear here")
    for kind in ("isolated", "combined"):
        example = next(r for r in rows if r["prompt_kind"] == kind
                       and r["variant"] == "X_DEGREE_FREE")
        print(f"\n### {kind}\n{example['user_prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
