"""Build the QACD designs for the semicolon-splice intervention.

The semicolon requirement is held FIXED in every cell. What varies is a fourth
instruction appended in one fixed slot:

    Q   the focal instruction B, or its matched reference C_L3
    A   the exact-four-sentence target
    C   X_SEMICOLON_FREE, in every cell
    D   X_NO_SEMI_SPLICE  (closes the suspected route)
        X_NO_EXCLAM       (matched off-route control, same added load)

The off-route arm exists because adding an instruction is itself a manipulation.
Comparing "semicolon alone" with "semicolon + anti-splice" would confound closing
the route with carrying a fourth constraint, so that comparison is never built.

`D` never moves slot. The builder asserts that two matched prompts differ in
exactly one line — the D line — before anything is generated.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest

TARGET = "A"
BACKGROUND = "X_SEMICOLON_FREE"
ANTI_SPLICE = "X_NO_SEMI_SPLICE"
OFF_ROUTE = "X_NO_EXCLAM"
ROUTES = {"off_route": OFF_ROUTE, "anti_splice": ANTI_SPLICE}
#: The preflight carries the REFERENCE arm only, so no focal-versus-reference
#: contrast is computable from it and the manipulation gate cannot be influenced
#: by the outcome the main experiment measures.
PREFLIGHT_ARMS = ("C_L3",)
MAIN_ARMS = ("B", "C_L3")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--mode", choices=("preflight", "main"), required=True)
    parser.add_argument("--tasks", type=int, default=20)
    parser.add_argument("--offset", type=int, default=32,
                        help="calibration offset; CAL01-12 and CAL13-32 are used")
    parser.add_argument("--replicates", type=int, default=2)
    args = parser.parse_args()

    extensions.register()
    state = harvest.load()
    records = state.TASKS.to_dict("records")
    evaluation = [t for t in records if t["split"] == "pilot"][:20]

    if args.mode == "preflight":
        pool = [t for t in records if t["split"] == "calibration"]
        tasks = pool[args.offset:args.offset + args.tasks]
        arms = PREFLIGHT_ARMS
    else:
        tasks = evaluation
        arms = MAIN_ARMS
    if len(tasks) != args.tasks:
        raise SystemExit(f"cannot supply {args.tasks} tasks in mode {args.mode}")

    evaluation_ids = {t["task_id"] for t in evaluation}
    if args.mode == "preflight":
        clash = {t["task_id"] for t in tasks} & evaluation_ids
        if clash:
            raise SystemExit(f"preflight would reuse evaluation tasks: {clash}")

    rows = []
    for task in tasks:
        for route, route_id in ROUTES.items():
            for arm in arms:
                for replicate in range(args.replicates):
                    ordered = [arm, TARGET, BACKGROUND, route_id]
                    rows.append({
                        "row_id": hashlib.blake2b(
                            f"ssi|{args.mode}|{task['task_id']}|{route}|{arm}"
                            f"|{replicate}".encode(), digest_size=10).hexdigest(),
                        "stage": f"SSI_{args.mode}",
                        "task_id": task["task_id"], "topic": task["topic"],
                        "condition": "focal" if arm == "B" else "reference",
                        "arm": arm, "measured": TARGET,
                        "route": route, "route_id": route_id,
                        "order": "QACD", "load": len(ordered),
                        "replicate": replicate, "ordered_ids": ordered,
                        "paraphrase_id": 0,
                        "user_prompt": harvest.compose_prompt(
                            task["topic"], ordered, 0),
                        "pair_key": f"{task['task_id']}|{route}|r{replicate}",
                        "variant": BACKGROUND})

    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("design rows are not uniquely identified")

    # The two route conditions must differ in exactly one line, and it must be
    # the D line. Anything else means the intervention is confounded.
    groups = {}
    for row in rows:
        groups.setdefault((row["task_id"], row["arm"], row["replicate"]), {})[
            row["route"]] = row["user_prompt"]
    for key, texts in groups.items():
        left = texts["off_route"].split("\n")
        right = texts["anti_splice"].split("\n")
        if len(left) != len(right):
            raise SystemExit(f"prompts differ in line count for {key}")
        differing = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
        if differing != [len(left) - 1]:
            raise SystemExit(f"prompts differ on lines {differing}, not only the "
                             f"last (D) line, for {key}")
    print(f"[check] the two route conditions differ in exactly one line — the "
          f"final D line — in all {len(groups)} matched groups")

    expected = len(tasks) * len(ROUTES) * len(arms) * args.replicates
    if len(rows) != expected:
        raise SystemExit(f"expected {expected} design rows, built {len(rows)}")
    print(f"[assert] {len(rows)} design rows = {len(tasks)} tasks x "
          f"{len(ROUTES)} routes x {len(arms)} arms x {args.replicates} "
          f"replicates; x 2 reasoning states = {2 * len(rows)} generations")

    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"[design] mode {args.mode} | tasks {tasks[0]['task_id']}.."
          f"{tasks[-1]['task_id']} | arms {arms}")
    print(f"[out] {args.out}")
    for route in ROUTES:
        example = next(r for r in rows if r["route"] == route
                       and r["arm"] == arms[0])
        print(f"\n### route = {route}\n{example['user_prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
