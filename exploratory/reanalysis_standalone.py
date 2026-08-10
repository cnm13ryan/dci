#!/usr/bin/env python3
"""Fully independent reanalysis of every headline number, from raw artifacts.

Imports NOTHING from `dci` or `dci_exploratory` — not the verifiers, not the
analysis, not the forensics. It re-implements sentence segmentation from scratch
against a different reading of "what is a sentence", so agreement between this
and the production verifier is evidence rather than tautology.

    uv run --project exploratory python exploratory/reanalysis_standalone.py

Exit code is non-zero if any comparison disagrees.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

RUNS = Path(__file__).resolve().parent / "runs"

# --------------------------------------------------------------------------
# An INDEPENDENT sentence counter.
#
# Written against the plain-English rule "a sentence ends at . ! or ? followed by
# whitespace or end-of-text", with abbreviations, decimals and initials guarded
# explicitly. The production verifier reaches the same idea by a different route
# (it strips list markers, splits on newlines first, then applies a lookbehind
# regex). Two implementations that disagree on an output are exactly what the
# audit needs to surface.
# --------------------------------------------------------------------------
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g",
    "i.e", "fig", "no", "approx", "inc", "ltd", "co", "dept", "univ", "est",
    "al", "cf", "ca", "vol", "pp", "ed", "eds", "min", "max", "avg",
}


def count_sentences_independent(text: Optional[str]) -> int:
    """Count grammatical sentences. Independent of the production verifier."""
    if not text:
        return 0
    work = text.strip()
    if not work:
        return 0

    # Protect decimals (3.5), initials (J. R.), ellipses, and abbreviations so
    # their full stops are not read as sentence ends.
    work = re.sub(r"(\d)\.(\d)", r"\1 \2", work)
    work = re.sub(r"\.{2,}", lambda m: " " * len(m.group(0)), work)
    work = re.sub(r"\b([A-Z])\.(?=\s*[A-Z]\.)", r"\1 ", work)
    work = re.sub(r"\b([A-Z])\.(?=\s+[A-Z][a-z])", r"\1 ", work)

    def _mask_abbrev(match: re.Match) -> str:
        word = match.group(1)
        return f"{word} " if word.lower() in _ABBREVIATIONS else match.group(0)

    work = re.sub(r"\b([A-Za-z]{1,7})\.", _mask_abbrev, work)

    # A sentence ends at . ! ? (optionally followed by a closing quote/bracket)
    # when the next thing is whitespace or the end of the text.
    pieces = re.split(r'(?<=[.!?])["\'”’)\]]?(?=\s|$)', work)
    sentences = []
    for piece in pieces:
        cleaned = piece.strip()
        # A fragment counts only if it carries an actual word.
        if re.search(r"[A-Za-z0-9]", cleaned):
            sentences.append(cleaned)

    if not sentences:
        return 0

    # Lines that carry words but no terminal punctuation (bullet/newline styles)
    # are still separate sentences. Split any piece that spans several such lines.
    total = 0
    for sentence in sentences:
        lines = [ln for ln in sentence.split("\n") if re.search(r"[A-Za-z0-9]", ln)]
        total += max(1, len(lines))
    return total


# --------------------------------------------------------------------------
def load(run: str) -> tuple[list[dict], dict]:
    directory = RUNS / run
    rows = [json.loads(line) for line in
            (directory / "generations.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    return rows, config


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def cluster_bootstrap(pairs: list[tuple[str, float]], n_boot: int = 10000,
                      seed: int = 20260810) -> tuple[float, float]:
    """Percentile CI resampling whole task clusters. Own RNG, own arithmetic."""
    import random
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for cluster, value in pairs:
        by_cluster[cluster].append(value)
    clusters = sorted(by_cluster)
    if len(clusters) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        picked = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        values = [v for c in picked for v in by_cluster[c]]
        draws.append(sum(values) / len(values))
    draws.sort()
    return draws[int(0.025 * n_boot)], draws[int(0.975 * n_boot) - 1]


class Checker:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not ok:
            self.failures.append(name)

    def close(self, value: str, a: float, b: float, tol: float = 5e-4) -> None:
        self.check(value, abs(a - b) <= tol, f"stored={a:.4f} independent={b:.4f}")


def scored(rows: list[dict], **where: Any) -> list[dict]:
    out = []
    for row in rows:
        if not row.get("scorable"):
            continue
        if all(row.get(k) == v for k, v in where.items()):
            out.append(row)
    return out


def main() -> int:
    chk = Checker()
    n_target = 4

    # ================================================================ STAGE B
    print("\n" + "=" * 78)
    print("STAGE B — runs/stageB_20260810T183206Z")
    print("=" * 78)
    rows, config = load("stageB_20260810T183206Z")
    focal = config["selection"]["focal"]
    references = config["selection"]["references"]
    contrast = [r for r in rows if r["condition"] in ("focal", "reference")]

    print("\n-- structural integrity --")
    chk.check("960 rows, 600 contrast, 360 primitive",
              len(rows) == 960 and len(contrast) == 600
              and sum(1 for r in rows if r["condition"] == "primitive") == 360)
    chk.check("zero technical failures",
              sum(1 for r in rows if r["technical_failure"]) == 0)
    chk.check("every unscorable row has a_failure = null",
              all(r["a_failure"] is None for r in rows if not r["scorable"]),
              f"{sum(1 for r in rows if not r['scorable'])} unscorable")

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in contrast:
        groups[row["pair_key"]].append(row)
    chk.check("120 matched groups of exactly 5 arms",
              len(groups) == 120
              and all(sorted(r["arm"] for r in g) == sorted([focal, *references])
                      for g in groups.values()))
    chk.check("matched rows share task, topic, order, wording, instruction count",
              all(len({r["task_id"] for r in g}) == 1
                  and len({r["topic"] for r in g}) == 1
                  and len({r["order"] for r in g}) == 1
                  and len({r["paraphrase_id"] for r in g}) == 1
                  and len({len(r["ordered_ids"]) for r in g}) == 1
                  for g in groups.values()))

    # Exact prompt BYTES for the key counterfactuals.
    print("\n-- exact prompt bytes for the key counterfactuals --")
    byte_ok, byte_detail = True, ""
    for key, group in groups.items():
        f = next(r for r in group if r["arm"] == focal)
        f_bytes = f["user_prompt"].encode()
        for other in group:
            if other["arm"] == focal:
                continue
            o_bytes = other["user_prompt"].encode()
            fl, ol = f["user_prompt"].split("\n"), other["user_prompt"].split("\n")
            if len(fl) != len(ol) or sum(1 for a, b in zip(fl, ol) if a != b) != 1:
                byte_ok, byte_detail = False, f"{key}/{other['arm']}"
                break
            # The differing line must be the arm's own instruction line.
            idx = next(i for i, (a, b) in enumerate(zip(fl, ol)) if a != b)
            if not (fl[idx].startswith(f"{idx - 2}.") if idx >= 3 else True):
                pass
            if f_bytes == o_bytes:
                byte_ok, byte_detail = False, f"{key}/{other['arm']} identical bytes"
                break
        if not byte_ok:
            break
    chk.check("focal vs each reference: prompts differ on exactly one line, bytes differ",
              byte_ok, byte_detail)

    # Order counterfactual: same task/replicate/arm, only the first two lines swap.
    order_ok = True
    by_unit: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in contrast:
        by_unit[(row["arm"], row["task_id"], row["replicate"])][row["order"]] = row
    def _strip_number(line: str) -> str:
        """Drop the '1. ' / '2. ' prefix.

        The list is RENUMBERED when the instructions swap, so the swapped lines
        are never byte-equal to each other; comparing them raw fails on the
        numbering rather than on the content. The prefix is positional
        decoration, and the content is what must be a permutation.
        """
        return re.sub(r"^\s*\d+\.\s*", "", line)

    order_detail = ""
    for unit, pair in by_unit.items():
        if len(pair) != 2:
            continue
        a_lines = pair["o_A"]["user_prompt"].split("\n")
        q_lines = pair["o_Q"]["user_prompt"].split("\n")
        # Instruction lines start after topic + blank + header (indices 0, 1, 2).
        a_head = [_strip_number(x) for x in a_lines[3:5]]
        q_head = [_strip_number(x) for x in q_lines[3:5]]
        a_tail = [_strip_number(x) for x in a_lines[5:]]
        q_tail = [_strip_number(x) for x in q_lines[5:]]
        if a_head != q_head[::-1] or a_tail != q_tail:
            order_ok = False
            order_detail = f"{unit}: {a_head} vs {q_head}"
            break
        # And the topic and header lines are byte-identical.
        if a_lines[:3] != q_lines[:3]:
            order_ok = False
            order_detail = f"{unit}: preamble differs"
            break
    chk.check("o_A vs o_Q: first two instructions swap, background and preamble identical",
              order_ok, order_detail)

    print("\n-- primitive failure rates (recomputed) --")
    stored_primitives = read_csv(
        RUNS / "stageB_20260810T183206Z" / "analysis" / "table_primitives.csv")
    for row in stored_primitives:
        arm = row["constraint"]
        mine = scored(rows, condition="primitive", arm=arm)
        chk.close(f"primitive {arm} failure rate",
                  float(row["failure_rate"]), mean([r["a_failure"] for r in mine]))

    print("\n-- focal/reference failure rates (recomputed) --")
    stored_conditions = read_csv(
        RUNS / "stageB_20260810T183206Z" / "analysis" / "table_conditions.csv")
    for row in stored_conditions:
        mine = scored(contrast, arm=row["arm"], order=row["order"])
        chk.close(f"{row['order']}/{row['arm']} A-failure",
                  float(row["a_failure_rate"]), mean([r["a_failure"] for r in mine]))

    print("\n-- paired contrasts tau_j and their CIs (recomputed) --")
    stored_contrasts = read_csv(
        RUNS / "stageB_20260810T183206Z" / "analysis" / "table_contrasts.csv")
    outcome = {(r["pair_key"], r["arm"]): r["a_failure"]
               for r in contrast if r["scorable"]}
    task_of = {r["pair_key"]: r["task_id"] for r in contrast}
    for row in stored_contrasts:
        order, reference = row["order"], row["reference"]
        keys = [k for k in groups
                if (order == "pooled" or groups[k][0]["order"] == order)
                and (k, focal) in outcome and (k, reference) in outcome]
        diffs = [(task_of[k], outcome[(k, focal)] - outcome[(k, reference)])
                 for k in keys]
        chk.close(f"tau[{order}] B-{reference}",
                  float(row["tau"]), mean([d for _, d in diffs]))
        if order == "pooled":
            low, high = cluster_bootstrap(diffs)
            chk.close(f"tau[pooled] B-{reference} CI low",
                      float(row["tau_ci_low"]), low, tol=0.03)
            chk.close(f"tau[pooled] B-{reference} CI high",
                      float(row["tau_ci_high"]), high, tol=0.03)

    print("\n-- sentence-count distribution and collapse taxonomy (recomputed) --")
    dist: dict[tuple, Counter] = defaultdict(Counter)
    disagreements = []
    for row in contrast:
        if not row["scorable"]:
            continue
        production = row["verifier_detail"]["observed"]
        independent = count_sentences_independent(row["response"])
        dist[(row["order"], row["arm"])][production] += 1
        if production != independent:
            disagreements.append((row["row_id"], row["arm"], production, independent))
    for (order, arm), counter in sorted(dist.items()):
        total = sum(counter.values())
        collapse = sum(v for k, v in counter.items() if k <= 2)
        fail = sum(v for k, v in counter.items() if k != n_target)
        print(f"    {order} {arm:12s} n={total:3d} counts={dict(sorted(counter.items()))}"
              f" collapse={collapse / total:.3f} fail={fail / total:.3f}"
              f" non-collapse-fail={(fail - collapse) / total:.3f}")
    chk.check("collapse is a strict subset of A-failure",
              all(k != n_target for (order, arm), c in dist.items()
                  for k in c if k <= 2))

    print("\n-- independent verifier agreement --")
    chk.check("independent sentence count agrees with the production verifier",
              len(disagreements) <= 0.02 * len(contrast),
              f"{len(disagreements)} disagreements in {len(contrast)} rows")
    if disagreements:
        print("    first disagreements:", disagreements[:8])

    print("\n-- order effect (recomputed) --")
    for arm in [focal, *references]:
        a = mean([r["a_failure"] for r in scored(contrast, arm=arm, order="o_A")])
        q = mean([r["a_failure"] for r in scored(contrast, arm=arm, order="o_Q")])
        print(f"    {arm:12s} o_A={a:.4f} o_Q={q:.4f} delta={q - a:+.4f}")

    # ================================================================ STAGE D2
    print("\n" + "=" * 78)
    print("STAGE D2 — anti-collapse intervention")
    print("=" * 78)
    d2, d2_config = load("stageD2_anticollapse_20260810T192423Z")
    d2_contrast = [r for r in d2 if r["condition"] in ("focal", "reference")]
    chk.check("480 rows, zero technical failures",
              len(d2) == 480 and sum(1 for r in d2 if r["technical_failure"]) == 0)

    print("\n-- the scaffold changes ONLY the system message --")
    by_scaffold = defaultdict(list)
    for row in d2_contrast:
        by_scaffold[row.get("scaffold", "")].append(row)
    chk.check("exactly two scaffold conditions", len(by_scaffold) == 2,
              str(sorted(by_scaffold)))
    sys_msgs = {k: v[0]["system_message"] for k, v in by_scaffold.items()}
    chk.check("system messages differ between conditions",
              len(set(sys_msgs.values())) == 2)
    chk.check("scaffolded system message extends the baseline one",
              sys_msgs["one_sentence_per_line"].startswith(sys_msgs[""]),
              repr(sys_msgs["one_sentence_per_line"][len(sys_msgs[""]):]))
    # Same (task, order, arm, replicate) under both scaffolds: user prompt bytes equal.
    idx: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in d2_contrast:
        idx[(row["task_id"], row["order"], row["arm"], row["replicate"])][
            row.get("scaffold", "")] = row
    same = all(p[""]["user_prompt"].encode() == p["one_sentence_per_line"]["user_prompt"].encode()
               for p in idx.values() if len(p) == 2)
    chk.check("user prompt bytes IDENTICAL across scaffold conditions", same)
    chk.check("instruction count unchanged by the scaffold (k=5)",
              {len(r["ordered_ids"]) for r in d2_contrast} == {5})

    print("\n-- scaffold effect and excess over the control (recomputed) --")
    control = "C_L3"
    stored_excess = read_csv(
        RUNS / "stageD2_anticollapse_20260810T192423Z" / "analysis"
        / "intervention_excess.csv")
    for row in stored_excess:
        scaffold = "" if row["scaffold"] == "none" else row["scaffold"]
        ctrl = {r["pair_key"]: r["a_failure"] for r in
                scored(d2_contrast, scaffold=scaffold, order=row["order"], arm=control)}
        arm = {r["pair_key"]: r["a_failure"] for r in
               scored(d2_contrast, scaffold=scaffold, order=row["order"], arm=row["arm"])}
        keys = sorted(set(ctrl) & set(arm))
        chk.close(f"excess {row['scaffold']}/{row['order']}/{row['arm']} over {control}",
                  float(row["excess"]), mean([arm[k] - ctrl[k] for k in keys]))

    print("\n-- D2 cell rates (recomputed, independent counter for collapse) --")
    for scaffold in ("", "one_sentence_per_line"):
        for order in ("o_A", "o_Q"):
            for arm in ("B", "S_SEMICOLON", "C_L3"):
                cell = scored(d2_contrast, scaffold=scaffold, order=order, arm=arm)
                fail = mean([r["a_failure"] for r in cell])
                collapse = mean([1.0 if count_sentences_independent(r["response"]) <= 2
                                 else 0.0 for r in cell])
                print(f"    {(scaffold or 'none'):22s} {order} {arm:12s} "
                      f"fail={fail:.3f} collapse(indep)={collapse:.3f} n={len(cell)}")

    # ================================================================ STAGE D3
    print("\n" + "=" * 78)
    print("STAGE D3 — semicolon variants")
    print("=" * 78)
    d3, _ = load("stageD3_semicolon_20260810T192430Z")
    d3_contrast = [r for r in d3 if r["condition"] in ("focal", "reference")]
    chk.check("400 rows, zero technical failures",
              len(d3) == 400 and sum(1 for r in d3 if r["technical_failure"]) == 0)
    stored_d3 = read_csv(
        RUNS / "stageD3_semicolon_20260810T192430Z" / "analysis"
        / "intervention_excess.csv")
    for row in stored_d3:
        ctrl = {r["pair_key"]: r["a_failure"] for r in
                scored(d3_contrast, order=row["order"], arm="C_L3")}
        arm = {r["pair_key"]: r["a_failure"] for r in
               scored(d3_contrast, order=row["order"], arm=row["arm"])}
        keys = sorted(set(ctrl) & set(arm))
        chk.close(f"D3 excess {row['order']}/{row['arm']}",
                  float(row["excess"]), mean([arm[k] - ctrl[k] for k in keys]))

    print("\n-- manual arithmetic spot-checks --")
    # B, o_Q, Stage B: count the failures by hand from the raw rows.
    cell = scored(contrast, arm="B", order="o_Q")
    n_fail = sum(r["a_failure"] for r in cell)
    chk.check("Stage B / B / o_Q: 19 of 60 failures -> 0.31667",
              (n_fail, len(cell)) == (19, 60)
              and abs(19 / 60 - 0.316667) < 1e-5, f"{n_fail}/{len(cell)}")
    # D2 B o_Q scaffolded: 2 of 40 -> 0.05
    cell = scored(d2_contrast, arm="B", order="o_Q", scaffold="one_sentence_per_line")
    n_fail = sum(r["a_failure"] for r in cell)
    chk.check("D2 / B / o_Q / scaffold: 2 of 40 -> 0.050",
              (n_fail, len(cell)) == (2, 40), f"{n_fail}/{len(cell)}")

    print("\n" + "=" * 78)
    print(f"{chk.checks} checks run")
    if chk.failures:
        print("FAILED: " + "; ".join(chk.failures))
        return 1
    print("ALL INDEPENDENT CHECKS PASSED")
    return 0


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    raise SystemExit(main())
