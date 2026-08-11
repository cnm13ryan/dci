"""Build the priority-intervention designs (Experiment 3).

Two prompt styles are built from the SAME wording strings, pulled out of the
protocol's own `compose_prompt` rather than retyped:

  historical  the numbered list every earlier round used;
  labelled    the same instructions, in the same order, each tagged with the
              semantic label the priority rule will refer to.

The label is semantic and fixed -- A is always the target, B always the focal
instruction, C always the background -- while its position follows the
experimental order. That is the whole point: a priority rule that named a
position would be a different manipulation.

The bridge design carries no priority rule. It exists to find out whether the
labels alone move behaviour, so that anything the priority conditions do can be
attributed to the priority relationship rather than to the relabelling.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest

ROLE_IDS = {"A": "A", "B": "B"}
PREAMBLE = "Satisfy every constraint below simultaneously:"

PRIORITY = {
    "equal": ("Priority rule: Satisfy Instructions A and B if possible. If a "
              "trade-off is unavoidable, do not prefer either instruction over "
              "the other."),
    "a_over_b": ("Priority rule: Satisfy Instructions A and B if possible. If a "
                 "trade-off is unavoidable, prioritize Instruction A over "
                 "Instruction B."),
    "b_over_a": ("Priority rule: Satisfy Instructions A and B if possible. If a "
                 "trade-off is unavoidable, prioritize Instruction B over "
                 "Instruction A."),
}


def wording(constraint_id: str) -> str:
    """The protocol's own paraphrase-0 string for one constraint."""
    rendered = harvest.compose_prompt("", [constraint_id], 0)
    return rendered.rsplit("\n1. ", 1)[1]


def render(topic: str, ordered: list[tuple[str, str]], style: str,
           priority: str | None) -> str:
    """`ordered` is [(label, constraint_id), ...] already in prompt order."""
    if style == "historical":
        body = "\n".join(f"{i}. {wording(cid)}"
                         for i, (_, cid) in enumerate(ordered, 1))
    else:
        body = "\n".join(f"Instruction {label}: {wording(cid)}"
                         for label, cid in ordered)
    prompt = f"{topic}\n\n{PREAMBLE}\n{body}"
    if priority:
        prompt += f"\n\n{PRIORITY[priority]}"
    return prompt


def row_id(*parts) -> str:
    return hashlib.blake2b("|".join(map(str, parts)).encode(),
                           digest_size=10).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--mode", choices=("bridge", "main"), required=True)
    parser.add_argument("--order", default="QAC")
    parser.add_argument("--tasks", type=int, default=20)
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--backgrounds", default="X_SEMICOLON_FREE,X_PAREN_FREE")
    parser.add_argument("--focal", default="B")
    args = parser.parse_args()

    extensions.register()
    state = harvest.load()
    tasks = [t for t in state.TASKS.to_dict("records")
             if t["split"] == "pilot"][:args.tasks]
    if len(tasks) != args.tasks:
        raise SystemExit(f"pilot split holds {len(tasks)} tasks, need {args.tasks}")
    backgrounds = args.backgrounds.split(",")

    if args.mode == "bridge":
        conditions = [(style, None) for style in ("historical", "labelled")]
    else:
        conditions = [("labelled", p) for p in PRIORITY]

    rows = []
    for task in tasks:
        for background in backgrounds:
            for style, priority in conditions:
                for replicate in range(args.replicates):
                    roles = {"A": "A", "Q": args.focal, "C": background}
                    labels = {"A": "A", "Q": "B", "C": "C"}
                    ordered = [(labels[r], roles[r]) for r in args.order]
                    rows.append({
                        "row_id": row_id(args.mode, task["task_id"], args.order,
                                         background, style, priority, replicate),
                        "stage": f"AP_priority_{args.mode}",
                        "task_id": task["task_id"], "topic": task["topic"],
                        "condition": "focal", "arm": args.focal, "measured": "A",
                        "order": args.order, "load": len(ordered),
                        "replicate": replicate,
                        "ordered_ids": [cid for _, cid in ordered],
                        "paraphrase_id": 0,
                        "prompt_style": style,
                        "priority": priority or "none",
                        "user_prompt": render(task["topic"], ordered, style,
                                              priority),
                        "pair_key": (f"{task['task_id']}|{args.order}|"
                                     f"{background}|r{replicate}"),
                        "variant": background})

    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("priority design rows are not uniquely identified")

    # Only the priority relationship may differ between the three conditions.
    if args.mode == "main":
        stripped = {}
        for row in rows:
            body = row["user_prompt"].rsplit("\n\nPriority rule:", 1)[0]
            stripped.setdefault((row["task_id"], row["variant"]), set()).add(body)
        offenders = {k: v for k, v in stripped.items() if len(v) != 1}
        if offenders:
            raise SystemExit(f"instruction body differs across priority "
                             f"conditions for {list(offenders)[:2]}")
        print(f"[check] instruction body identical across the three priority "
              f"conditions in all {len(stripped)} task x background groups")

    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"[design] {len(rows)} rows | {len(tasks)} tasks | mode {args.mode} | "
          f"order {args.order} | backgrounds {backgrounds}")
    print(f"[out] {args.out}")
    print("\n--- one prompt per condition ---")
    seen = set()
    for row in rows:
        key = (row["prompt_style"], row["priority"], row["variant"])
        if key in seen or row["variant"] != backgrounds[0]:
            continue
        seen.add(key)
        print(f"\n### style={key[0]} priority={key[1]}\n{row['user_prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
