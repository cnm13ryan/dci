"""Build the focal-ladder calibration design.

Every rung sits in the same prompt slot, under the same order, with the same
background and the same target, so the only thing that varies across candidates
is how many increases the focal instruction demands.

Only the focal arm is generated. The four-state decomposition — both / target
only / focal only / neither — is defined on the focal arm alone, and the
construction gates are all statements about it, so a reference arm would add
generations without adding evidence about whether a rung is usable.

The calibration tasks are a block of the `calibration` split disjoint from the
20 evaluation tasks, and disjoint again from the block used for the
boundary-control preflight, so no single set of topics is doing double duty.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest

#: Hardest first. The selection rule takes the FIRST rung that passes, so this
#: order is the rule and must not be permuted after seeing results.
LADDER = ("B", "X_B_INC2", "X_B_INC1")
TARGET = "A"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--tasks", type=int, default=20)
    parser.add_argument("--offset", type=int, default=12,
                        help="skip the block used by the boundary preflight")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--backgrounds", default="X_PAREN_FREE,X_SEMICOLON_FREE")
    parser.add_argument("--order", default="QAC")
    args = parser.parse_args()

    extensions.register()
    state = harvest.load()
    records = state.TASKS.to_dict("records")
    pool = [t for t in records if t["split"] == "calibration"]
    tasks = pool[args.offset:args.offset + args.tasks]
    if len(tasks) != args.tasks:
        raise SystemExit(f"calibration split cannot supply {args.tasks} tasks "
                         f"from offset {args.offset}")

    evaluation = {t["task_id"] for t in records if t["split"] == "pilot"}
    clash = {t["task_id"] for t in tasks} & evaluation
    if clash:
        raise SystemExit(f"calibration would reuse evaluation tasks: {clash}")

    backgrounds = args.backgrounds.split(",")
    rows = []
    for task in tasks:
        for focal in LADDER:
            for background in backgrounds:
                for replicate in range(args.replicates):
                    roles = {"A": TARGET, "Q": focal, "C": background}
                    ordered = [roles[r] for r in args.order]
                    rows.append({
                        "row_id": hashlib.blake2b(
                            f"focalcal|{task['task_id']}|{focal}|{background}"
                            f"|{replicate}".encode(), digest_size=10).hexdigest(),
                        "stage": "MFR_focal_calibration",
                        "task_id": task["task_id"], "topic": task["topic"],
                        "condition": "focal", "arm": focal, "measured": TARGET,
                        "focal_rung": focal,
                        "order": args.order, "load": len(ordered),
                        "replicate": replicate, "ordered_ids": ordered,
                        "paraphrase_id": 0,
                        "user_prompt": harvest.compose_prompt(
                            task["topic"], ordered, 0),
                        "pair_key": (f"{task['task_id']}|{background}"
                                     f"|r{replicate}"),
                        "variant": background})

    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("calibration rows are not uniquely identified")

    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"[design] {len(rows)} rows | {len(tasks)} calibration tasks "
          f"({tasks[0]['task_id']}..{tasks[-1]['task_id']}) | "
          f"{len(LADDER)} rungs | {len(backgrounds)} backgrounds | "
          f"{args.replicates} replicates")
    print(f"[out] {args.out}")
    print(f"[disjoint] 0 of the 20 evaluation tasks appear here")
    for focal in LADDER:
        example = next(r for r in rows if r["arm"] == focal
                       and r["variant"] == backgrounds[0])
        print(f"\n### {focal}\n{example['user_prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
