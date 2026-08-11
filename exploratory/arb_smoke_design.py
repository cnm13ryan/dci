"""Build the cross-model smoke design: seven prompt types, singly and in triples.

The singleton prompts (A alone, B alone, R alone) are what decide requirement 7 —
whether the model performs the task above unusable floor levels — because a model
that cannot write four sentences when that is the only instruction has nothing to
interfere with, and a cross-model comparison of interference would be measuring
its inability instead.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest

TYPES = [
    ("A_alone", ["A"]),
    ("B_alone", ["B"]),
    ("R_alone", ["C_L3"]),
    ("A_B_semicolon", ["B", "A", "X_SEMICOLON_FREE"]),
    ("A_R_semicolon", ["C_L3", "A", "X_SEMICOLON_FREE"]),
    ("A_B_parentheses", ["B", "A", "X_PAREN_FREE"]),
    ("A_R_parentheses", ["C_L3", "A", "X_PAREN_FREE"]),
]
#: The measured constraint of each type: the target when present, else the lone
#: instruction, so a singleton row is scored against the thing it asked for.
MEASURED = {"A_alone": "A", "B_alone": "B", "R_alone": "C_L3"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--tasks", type=int, default=3)
    parser.add_argument("--replicates", type=int, default=1)
    args = parser.parse_args()

    extensions.register()
    state = harvest.load()
    tasks = [t for t in state.TASKS.to_dict("records")
             if t["split"] == "pilot"][:args.tasks]

    rows = []
    for task in tasks:
        for name, ids in TYPES:
            for replicate in range(args.replicates):
                arm = ("B" if "B" in ids and name != "R_alone"
                       else "C_L3" if "C_L3" in ids else "A")
                background = next((i for i in ids if i.startswith("X_")), "none")
                rows.append({
                    "row_id": hashlib.blake2b(
                        f"smoke|{task['task_id']}|{name}|{replicate}".encode(),
                        digest_size=10).hexdigest(),
                    "stage": "AP_crossmodel_smoke", "task_id": task["task_id"],
                    "topic": task["topic"], "prompt_type": name,
                    "condition": "focal" if arm == "B" else "reference",
                    "arm": arm, "measured": MEASURED.get(name, "A"),
                    "order": "QAC" if len(ids) == 3 else "single",
                    "load": len(ids), "replicate": replicate,
                    "ordered_ids": ids, "paraphrase_id": 0,
                    "user_prompt": harvest.compose_prompt(task["topic"], ids, 0),
                    "pair_key": f"{task['task_id']}|{name}|r{replicate}",
                    "variant": background})

    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"[design] {len(rows)} rows | {len(tasks)} tasks | "
          f"{len(TYPES)} prompt types | {args.replicates} replicates")
    print(f"[out] {args.out}")
    for name, _ in TYPES:
        example = next(r for r in rows if r["prompt_type"] == name)
        print(f"\n### {name}  (measured: {example['measured']})\n"
              f"{example['user_prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
