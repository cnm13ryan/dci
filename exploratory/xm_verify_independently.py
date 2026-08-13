"""Independent recomputation of every cross-model headline number.

This script deliberately shares NO estimation code with `xm_analysis.py`. It
re-reads the raw generation rows, re-derives the failure indicator from the
final answers, and recomputes tau, the semicolon contrast and the four-state
distribution with plain arithmetic — no pandas groupby chains reused, no
`plotstyle.summarise`, its own bootstrap.

If the two disagree, the disagreement blocks interpretation. A number that only
one implementation can produce is not yet a result.

    uv run python xm_verify_independently.py runs/XM_DIR/generations.jsonl [...]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from dci_exploratory import extensions, harvest

extensions.register()
STATE = harvest.load()

TARGET = "A"
FOCAL = "B"
REFERENCE = "C_L3"
SEMICOLON = "X_SEMICOLON_FREE"
CONTROL = "X_PAREN_FREE"
#: Matches `dci_exploratory.plotstyle.BOOTSTRAP_DRAWS`, stated independently.
DRAWS = 4000

_PROBLEMS: list[str] = []


def note(ok: bool, message: str) -> None:
    print(f"  [{'ok  ' if ok else 'FAIL'}] {message}")
    if not ok:
        _PROBLEMS.append(message)


def read(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with Path(path).open() as handle:
            rows.extend(json.loads(line) for line in handle)
    return rows


def a_failed(row: dict) -> float:
    """1.0 when the target instruction failed, from the FINAL ANSWER only."""
    text = row.get("final_answer")
    if not isinstance(text, str) or not text.strip():
        return float("nan")
    return 0.0 if STATE.verify(text, TARGET).binary_pass else 1.0


def passes(row: dict, constraint: str) -> float:
    text = row.get("final_answer")
    if not isinstance(text, str) or not text.strip():
        return float("nan")
    return 1.0 if STATE.verify(text, constraint).binary_pass else 0.0


def mean(values: list[float]) -> float:
    clean = [v for v in values if v == v]
    return sum(clean) / len(clean) if clean else float("nan")


def bootstrap(values: list[float], key: str) -> tuple[float, float]:
    """Resample TASK clusters, not generations. Deterministic per key."""
    import hashlib

    if not values:
        return float("nan"), float("nan")
    digest = hashlib.sha256(key.encode()).digest()[:8]
    rng = np.random.default_rng(int.from_bytes(digest, "big") ^ 20260811)
    array = np.asarray(values, dtype=float)
    index = rng.integers(0, array.size, size=(DRAWS, array.size))
    means = array[index].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print(__doc__)
        return 2
    rows = read(paths)
    print(f"\nread {len(rows)} raw rows from {len(paths)} file(s)")

    # ------------------------------------------------------------ integrity
    print("\nstructure")
    by_run: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_run[(row["model_id"], row["reasoning_mode"])].append(row)

    seen_ids = defaultdict(set)
    for key, group in by_run.items():
        for row in group:
            seen_ids[key].add(row["row_id"])
        note(len(seen_ids[key]) == len(group),
             f"{key[0]} / {key[1]}: {len(group)} rows, "
             f"{len(seen_ids[key])} unique row ids")
        note(len(group) == 160, f"{key[0]} / {key[1]}: expected 160 rows")
        note({r["order"] for r in group} == {"QAC"},
             f"{key[0]} / {key[1]}: order is QAC")
        note({r["arm"] for r in group} == {FOCAL, REFERENCE},
             f"{key[0]} / {key[1]}: arms are B and C_L3")
        note({r["background"] for r in group} == {SEMICOLON, CONTROL},
             f"{key[0]} / {key[1]}: both backgrounds present")
        note(len({r["task_id"] for r in group}) == 20,
             f"{key[0]} / {key[1]}: 20 tasks")
        revisions = {r["model_revision"] for r in group}
        note(len(revisions) == 1 and len(next(iter(revisions))) == 40,
             f"{key[0]} / {key[1]}: one 40-char revision {sorted(revisions)}")
        cells = defaultdict(int)
        for row in group:
            cells[(row["task_id"], row["arm"], row["background"])] += 1
        note(set(cells.values()) == {2},
             f"{key[0]} / {key[1]}: every cell has 2 replicates")

    # ------------------------------------------------------------ estimates
    print("\n\nrecomputed estimates (independent of xm_analysis.py)\n")
    header = (f"{'model':28s} {'reasoning':18s} {'background':12s} "
              f"{'focal_F':>8s} {'ref_F':>8s} {'tau':>8s} "
              f"{'lo':>8s} {'hi':>8s}")
    print(header)
    print("-" * len(header))

    results = {}
    for (model, mode), group in sorted(by_run.items()):
        for background, label in ((CONTROL, "control"),
                                  (SEMICOLON, "semicolon")):
            cell = [r for r in group if r["background"] == background]
            focal = [r for r in cell if r["arm"] == FOCAL]
            reference = [r for r in cell if r["arm"] == REFERENCE]

            per_task = []
            tasks = sorted({r["task_id"] for r in cell})
            for task in tasks:
                f = mean([a_failed(r) for r in focal if r["task_id"] == task])
                r_ = mean([a_failed(r) for r in reference
                           if r["task_id"] == task])
                if f == f and r_ == r_:
                    per_task.append(f - r_)
            tau = mean(per_task)
            lo, hi = bootstrap(per_task, f"{model}|{mode}|{background}")
            results[(model, mode, background)] = per_task
            print(f"{model.split('/')[-1]:28s} {mode:18s} {label:12s} "
                  f"{mean([a_failed(r) for r in focal]):+8.3f} "
                  f"{mean([a_failed(r) for r in reference]):+8.3f} "
                  f"{tau:+8.3f} {lo:+8.3f} {hi:+8.3f}")

    print("\n\nsemicolon minus control\n")
    print(f"{'model':28s} {'reasoning':18s} {'delta':>8s} {'lo':>8s} {'hi':>8s}")
    print("-" * 74)
    for (model, mode) in sorted(by_run):
        semi = results.get((model, mode, SEMICOLON))
        ctrl = results.get((model, mode, CONTROL))
        if not semi or not ctrl or len(semi) != len(ctrl):
            continue
        delta = [s - c for s, c in zip(semi, ctrl)]
        lo, hi = bootstrap(delta, f"{model}|{mode}|delta")
        print(f"{model.split('/')[-1]:28s} {mode:18s} "
              f"{mean(delta):+8.3f} {lo:+8.3f} {hi:+8.3f}")

    print("\n\nfour-state outcomes, focal arm only\n")
    print(f"{'model':26s} {'reasoning':18s} {'background':11s} "
          f"{'both':>7s} {'target':>7s} {'focal':>7s} {'neither':>7s}")
    print("-" * 92)
    for (model, mode), group in sorted(by_run.items()):
        for background, label in ((CONTROL, "control"),
                                  (SEMICOLON, "semicolon")):
            focal = [r for r in group
                     if r["arm"] == FOCAL and r["background"] == background]
            counts = {"both": 0, "target": 0, "focal": 0, "neither": 0}
            for row in focal:
                a = passes(row, TARGET)
                b = passes(row, FOCAL)
                if a != a or b != b:
                    continue
                counts["both" if (a and b) else
                       "target" if (a and not b) else
                       "focal" if (b and not a) else "neither"] += 1
            total = max(sum(counts.values()), 1)
            print(f"{model.split('/')[-1]:26s} {mode:18s} {label:11s} "
                  + " ".join(f"{counts[k] / total:7.3f}"
                             for k in ("both", "target", "focal", "neither")))

    print(f"\n{'NO DISCREPANCIES' if not _PROBLEMS else f'{len(_PROBLEMS)} PROBLEM(S): {_PROBLEMS}'}")
    return 1 if _PROBLEMS else 0


if __name__ == "__main__":
    raise SystemExit(main())
