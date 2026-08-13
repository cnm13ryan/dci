"""Seed validation: are replicate seeds distinct, and how often do outputs repeat?

The requirement is on the SEEDS, not on the text. Two distinct seeds may still
produce the same string -- with four sentences of constrained prose that is a
real possibility -- so the assertion here is that no two replicates of one task
share a request seed, and the duplicate-output rate is reported beside it as a
diagnostic rather than as a pass criterion.

The failure this guards against is the original defect: a single seed shared by a
whole batch, which made nominal replicates byte-identical and turned N draws into
one draw counted N times.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PATH = Path(sys.argv[1])
rows = [json.loads(line) for line in PATH.open()]
print(f"{len(rows)} generations from {PATH}\n")

# --- 1. seeds are distinct across replicates within a task -------------------
# They are deliberately EQUAL across arm, background, order and budget: that is
# the common-random-number pairing tau relies on.
failures = []
by_unit = defaultdict(set)
for row in rows:
    by_unit[(row["task_id"], row["replicate_id"], row["reasoning_budget"])].add(
        row["actual_request_seed"])
for unit, seeds in sorted(by_unit.items()):
    if len(seeds) != 1:
        failures.append(f"unit {unit} carries {len(seeds)} answer seeds")

per_task = defaultdict(dict)
for (task, replicate, budget), seeds in by_unit.items():
    per_task[(task, budget)][replicate] = next(iter(seeds))
for (task, budget), seeds in sorted(per_task.items()):
    if len(set(seeds.values())) != len(seeds):
        failures.append(f"task {task} b={budget} repeats a seed across replicates: {seeds}")

print("### answer-phase seeds, by task and replicate (b = max budget)\n")
top = max(r["reasoning_budget"] for r in rows)
for (task, budget), seeds in sorted(per_task.items()):
    if budget == top:
        print(f"  {task}  " + "  ".join(f"r{r}={s}" for r, s in sorted(seeds.items())))

think = {(r["task_id"], r["replicate_id"]): r["reasoning_request_seed"]
         for r in rows if r["reasoning_request_seed"] is not None}
answer = {(r["task_id"], r["replicate_id"]): r["actual_request_seed"] for r in rows}
overlap = {k for k in think if think[k] == answer[k]}
if overlap:
    failures.append(f"{len(overlap)} units reuse the thinking seed for the answer")

# --- 2. duplicate-output frequency -------------------------------------------
print("\n### duplicate outputs within a cell (same task, arm, background, order, budget)\n")
cells = defaultdict(list)
for row in rows:
    cells[(row["task_id"], row["arm"], row["background"], row["order"],
           row["reasoning_budget"])].append(row["raw_final_answer"])
dup_pairs = total_pairs = 0
for texts in cells.values():
    digests = [hashlib.blake2b(t.encode(), digest_size=8).hexdigest() for t in texts]
    counts = Counter(digests)
    n = len(digests)
    total_pairs += n * (n - 1) // 2
    dup_pairs += sum(c * (c - 1) // 2 for c in counts.values())
print(f"  identical replicate pairs: {dup_pairs}/{total_pairs} "
      f"= {dup_pairs / total_pairs:.3f}")

by_budget = defaultdict(lambda: [0, 0])
for (task, arm, bg, order, budget), texts in cells.items():
    digests = [hashlib.blake2b(t.encode(), digest_size=8).hexdigest() for t in texts]
    counts = Counter(digests)
    n = len(digests)
    by_budget[budget][1] += n * (n - 1) // 2
    by_budget[budget][0] += sum(c * (c - 1) // 2 for c in counts.values())
for budget, (dup, tot) in sorted(by_budget.items()):
    print(f"  b={budget:>5}  {dup}/{tot} = {dup / tot:.3f}")

print("\n### distinct answers per cell\n")
sizes = Counter(len({hashlib.blake2b(t.encode(), digest_size=8).hexdigest()
                     for t in texts}) for texts in cells.values())
for k in sorted(sizes):
    print(f"  {k} distinct of 4 replicates: {sizes[k]} cells")

# --- 3. verdict ---------------------------------------------------------------
print()
if failures:
    print("SEED VALIDATION FAILED")
    for line in failures:
        print("  -", line)
    raise SystemExit(1)
print("SEED VALIDATION PASSED: every replicate of every task carries its own "
      "request seed, and the thinking and answer phases are seeded apart.")
