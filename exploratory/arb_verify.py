"""Independent recomputation of every headline number, from the scored rows.

Imports nothing from `dci_exploratory.arbprogram` for the recomputation: no
estimand function, no grouping helper, no bootstrap. It reads the JSONL with the
standard library, rebuilds tau, Delta, Gamma, the four arbitration probabilities,
S and Psi from scratch with plain dictionaries, and only then imports the
pipeline to compare. A bug in the analysis module therefore cannot hide inside
its own verification.

It also re-derives the target verdict from the answer text through
`dci.verifiers.rules` directly, so the stored `A_pass` column is checked to still
mean "did this answer contain exactly four sentences" rather than something that
drifted.

Exit code is non-zero if any comparison disagrees.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

TOLERANCE = 1e-9
SOURCE = Path(sys.argv[1])
FOCAL, REFERENCE = "B", "C_L3"
# The background pair may be overridden, because the boundary experiment
# replaces the bracket control with a matched non-boundary MARK and its Delta
# has to be verified by this script too, not by a second one written beside it.
AMPLIFIER = sys.argv[2] if len(sys.argv) > 2 else "X_SEMICOLON_FREE"
CONTROL = sys.argv[3] if len(sys.argv) > 3 else "X_PAREN_FREE"

rows = [json.loads(line) for line in SOURCE.open()]
print(f"independent recomputation of {len(rows)} scored rows from {SOURCE}\n")
# A technical failure carries no verdict and leaves every behavioural estimand,
# including the four state probabilities. The rule is restated here rather than
# imported, like everything else this script recomputes.
technical = sum(1 for row in rows if row.get("generation_state") == "TECHNICAL_FAILURE")
rows = [row for row in rows if row.get("generation_state") != "TECHNICAL_FAILURE"]
print(f"  {technical} technical-failure rows set aside\n")
problems = []


def note(ok: bool, message: str) -> None:
    print(("  ok    " if ok else "  FAIL  ") + message)
    if not ok:
        problems.append(message)


# --- 1. the stored verdicts still mean what they say --------------------------
sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest  # noqa: E402
extensions.register()
STATE = harvest.load()

mismatched_a = mismatched_q = mismatched_c = 0
for row in rows:
    text = row["raw_final_answer"] or ""
    if int(STATE.verify(text, row["measured"]).binary_pass) != int(row["A_pass"]):
        mismatched_a += 1
    if int(STATE.verify(text, row["arm"]).binary_pass) != int(row["Q_pass"]):
        mismatched_q += 1
    if int(STATE.verify(text, row["background"]).binary_pass) != int(row["background_pass"]):
        mismatched_c += 1
note(mismatched_a == 0, f"A_pass re-derived from the answer text: {mismatched_a} mismatches")
note(mismatched_q == 0, f"Q_pass re-derived from the answer text: {mismatched_q} mismatches")
note(mismatched_c == 0, f"background_pass re-derived: {mismatched_c} mismatches")

# --- 2. arbitration state is the stated function of A and Q -------------------
bad_state = 0
for row in rows:
    a, q = int(row["A_pass"]), int(row["Q_pass"])
    expected = ("both" if a and q else "target only" if a else
                "focal only" if q else "neither")
    if expected != row["arbitration_state"]:
        bad_state += 1
note(bad_state == 0, f"arbitration_state is exactly f(A_pass, Q_pass): {bad_state} mismatches")

# --- 3. tau, Delta, Gamma, S and Psi, rebuilt with plain dictionaries ---------
bucket = defaultdict(list)
for row in rows:
    key = (row["order"], row["background"], row["reasoning_budget"], row["arm"],
           row.get("priority", "none"), row["task_id"])
    bucket[key].append(1.0 - int(row["A_pass"]))


def rate(order, background, budget, arm, task, priority="none"):
    values = bucket.get((order, background, budget, arm, priority, task))
    return None if not values else sum(values) / len(values)


def mean(values):
    values = [v for v in values if v is not None]
    return None if not values else sum(values) / len(values)


tasks = sorted({row["task_id"] for row in rows})
orders = sorted({row["order"] for row in rows})
budgets = sorted({row["reasoning_budget"] for row in rows})
backgrounds = sorted({row["background"] for row in rows})
priorities = sorted({row.get("priority", "none") for row in rows})


def my_tau(order, background, budget, priority="none"):
    per_task = []
    for task in tasks:
        focal = rate(order, background, budget, FOCAL, task, priority)
        reference = rate(order, background, budget, REFERENCE, task, priority)
        if focal is not None and reference is not None:
            per_task.append(focal - reference)
    return mean(per_task)


def my_delta(order, budget):
    per_task = []
    for task in tasks:
        pieces = {}
        for background in (AMPLIFIER, CONTROL):
            focal = rate(order, background, budget, FOCAL, task)
            reference = rate(order, background, budget, REFERENCE, task)
            pieces[background] = (None if focal is None or reference is None
                                  else focal - reference)
        if None not in pieces.values():
            per_task.append(pieces[AMPLIFIER] - pieces[CONTROL])
    return mean(per_task)


states = defaultdict(lambda: defaultdict(list))
for row in rows:
    if row["arm"] != FOCAL:
        continue
    key = (row["order"], row["background"], row["reasoning_budget"],
           row.get("priority", "none"), row["task_id"])
    states[key][row["arbitration_state"]].append(1)
    states[key]["__n"].append(1)


def my_state(order, background, budget, state, priority="none"):
    per_task = []
    for task in tasks:
        cell = states.get((order, background, budget, priority, task))
        if cell:
            per_task.append(len(cell.get(state, [])) / len(cell["__n"]))
    return mean(per_task)


# --- 4. compare against the pipeline ------------------------------------------
import pandas as pd  # noqa: E402
from dci_exploratory import arbprogram as A  # noqa: E402

frame = pd.read_json(SOURCE, lines=True)
has_priority = "priority" in frame.columns
checked = 0
for order in orders:
    for budget in budgets:
        for background in backgrounds:
            for priority in (priorities if has_priority else ["none"]):
                where = dict(background=background, order=order,
                             reasoning_budget=budget)
                if has_priority:
                    where["priority"] = priority
                mine = my_tau(order, background, budget, priority)
                if mine is None:
                    continue
                theirs = A.tau(frame, **where)
                if theirs.empty:
                    continue
                checked += 1
                note(abs(mine - theirs.mean()) < TOLERANCE,
                     f"tau {order} {background} b={budget} p={priority}: "
                     f"mine {mine:+.6f} vs pipeline {theirs.mean():+.6f}")
        if not has_priority:
            mine = my_delta(order, budget)
            theirs = A.delta(frame, order=order, reasoning_budget=budget,
                             amplifier=AMPLIFIER, control=CONTROL)
            if mine is not None and not theirs.empty:
                checked += 1
                note(abs(mine - theirs.mean()) < TOLERANCE,
                     f"Delta {order} b={budget}: mine {mine:+.6f} vs "
                     f"pipeline {theirs.mean():+.6f}")

for order in orders:
    for budget in budgets:
        for background in backgrounds:
            for priority in (priorities if has_priority else ["none"]):
                where = dict(background=background, order=order,
                             reasoning_budget=budget)
                if has_priority:
                    where["priority"] = priority
                theirs = A.arbitration(frame, **where)
                for state in A.STATES:
                    mine = my_state(order, background, budget, state, priority)
                    if mine is None or theirs[state].empty:
                        continue
                    checked += 1
                    note(abs(mine - theirs[state].mean()) < TOLERANCE,
                         f"P({state}) {order} {background} b={budget} p={priority}: "
                         f"mine {mine:.6f} vs pipeline {theirs[state].mean():.6f}")

if not has_priority:
    for order in orders:
        mine = my_delta(order, budgets[-1]) - my_delta(order, budgets[0])
        theirs = A.gamma(frame, order=order, low=budgets[0], high=budgets[-1],
                         amplifier=AMPLIFIER, control=CONTROL)
        checked += 1
        note(abs(mine - theirs.mean()) < TOLERANCE,
             f"Gamma {order}: mine {mine:+.6f} vs pipeline {theirs.mean():+.6f}")
else:
    for background in backgrounds:
        for budget in budgets:
            common = dict(background=background, reasoning_budget=budget)
            s = {}
            for priority in ("a_over_b", "b_over_a"):
                target = my_state(orders[0], background, budget, "target only", priority)
                focal = my_state(orders[0], background, budget, "focal only", priority)
                s[priority] = None if target is None else target - focal
            if None in s.values():
                continue
            mine = s["a_over_b"] - s["b_over_a"]
            theirs = (A.survival(frame, priority="a_over_b", **common)
                      - A.survival(frame, priority="b_over_a", **common)).dropna()
            checked += 1
            note(abs(mine - theirs.mean()) < TOLERANCE,
                 f"Psi {background} b={budget}: mine {mine:+.6f} vs "
                 f"pipeline {theirs.mean():+.6f}")

print(f"\n{checked} quantities recomputed independently and compared.")
if problems:
    print(f"{len(problems)} DISAGREEMENTS")
    raise SystemExit(1)
print("no disagreements")
