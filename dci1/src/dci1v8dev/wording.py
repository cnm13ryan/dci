"""The wording instrument: is the exact-count ladder measuring difficulty or
wording confusion? Read-only reconstruction from stored scored rows.

A and every Tier-1 marker family share four templates (§7.8: MK wordings are
A's with the marker substituted), so wording index ``w`` names the same
sentence frame across the nine families:

    w0  Use the word X exactly q times.
    w1  Your answer must contain X exactly q times.
    w2  Include X exactly q times in your answer.
    w3  The word X must appear exactly q times.

Every scored row records ``wording_indices`` and, for the stated constraint,
the verifier's counted ``statistic`` (the number of occurrences), so for each
(tree, model, family, severity, wording) this module accumulates: rows,
exact-count passes, the histogram of the statistic, the zero-marker share,
under/overshoot shares, the mean absolute miss, and per-topic pass means.
From those, per wording it reports the compliance gap to the other three
wordings at the same rung, and per family the ladder reconstructed on a
chosen wording subset (monotonicity, span, location relative to iota_A).

Streaming: the Gate-2 candidate files are 2-3.5 GB each; only the solo cells
of A and the marker families are read, and only the present score is parsed.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dci1v7.protocol.wordings import wordings
from dci1v7.verifiers.constraints import TIER1_FAMILY_IDS
from dci1v8dev.prescreen.ladder import spearman

__all__ = [
    "WORDING_FRAMES",
    "flag_wordings",
    "ladders_under",
    "misinterpretation_patterns",
    "scan_rows",
    "wording_table",
]

WORDING_FRAMES = tuple(w.replace("however", "X") for w in wordings("A", 2))

_CELL = re.compile(r'"cell_id": "solo:((?:MK\d|A):\d+)"')
_WORDING = re.compile(r'"wording_indices": \[(\d+)\]')
_TOPIC = re.compile(r'"topic_id": "([^"]+)"')
_SPLIT = re.compile(r'"topic_split": "([^"]+)"')
_PRESENT = re.compile(r'\{[^{}]*"present": true[^{}]*\}')
_WORDS = re.compile(r'"word_count": (\d+)')


def scan_rows(paths: Sequence[Path]) -> dict[str, Any]:
    """Accumulate per (family, severity, wording) from scored.jsonl files."""
    acc: dict[tuple[str, int, int], dict[str, Any]] = {}
    for path in paths:
        with open(path) as f:
            for line in f:
                m = _CELL.search(line)
                if m is None:
                    continue
                kind, sev = m.group(1).split(":")
                sev = int(sev)
                w = int(_WORDING.search(line).group(1))
                pm = _PRESENT.search(line)
                if pm is None:
                    continue
                score = json.loads(pm.group(0))
                if score["kind"] != kind or int(score["severity"]) != sev:
                    continue
                topic = _TOPIC.search(line).group(1)
                key = (kind, sev, w)
                a = acc.setdefault(key, {"n": 0, "passed": 0, "hist": {},
                                         "per_topic": defaultdict(list),
                                         "vacuous": 0, "words": 0})
                stat = score.get("statistic")
                stat = -1 if stat is None else int(stat)
                a["n"] += 1
                a["passed"] += int(bool(score["passed"]))
                a["vacuous"] += int(bool(score.get("vacuous_pass")))
                a["hist"][stat] = a["hist"].get(stat, 0) + 1
                a["per_topic"][topic].append(int(bool(score["passed"])))
                wm = _WORDS.search(line)
                a["words"] += int(wm.group(1)) if wm else 0
    out = {}
    for (kind, sev, w), a in acc.items():
        per_topic = {t: sum(v) / len(v) for t, v in a["per_topic"].items()}
        out[f"{kind}:{sev}:{w}"] = {
            "kind": kind, "severity": sev, "wording": w, "n": a["n"],
            "passed": a["passed"], "rate": a["passed"] / a["n"],
            "vacuous_rate": a["vacuous"] / a["n"],
            "histogram": {str(k): v for k, v in sorted(a["hist"].items())},
            "mean_words": a["words"] / a["n"],
            "per_topic": per_topic}
    return out


def _stats(entry: Mapping[str, Any]) -> dict[str, float]:
    q, n = entry["severity"], entry["n"]
    hist = {int(k): v for k, v in entry["histogram"].items()}
    zero = hist.get(0, 0) / n
    under = sum(v for k, v in hist.items() if 0 <= k < q) / n
    over = sum(v for k, v in hist.items() if k > q) / n
    exact = hist.get(q, 0) / n
    one = hist.get(1, 0) / n
    miss = sum(abs(k - q) * v for k, v in hist.items() if k >= 0) / n
    mean_stat = sum(k * v for k, v in hist.items() if k >= 0) / n
    return {"exact": exact, "zero": zero, "under": under, "over": over,
            "one_regardless": one, "mean_abs_miss": miss,
            "mean_statistic": mean_stat}


def wording_table(scan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Per (family, severity, wording): the rates, and the gap to the other
    three wordings at the same rung."""
    rows = []
    by_rung: dict[tuple[str, int], dict[int, Mapping[str, Any]]] = defaultdict(dict)
    for e in scan.values():
        by_rung[(e["kind"], e["severity"])][e["wording"]] = e
    for (kind, sev), ws in sorted(by_rung.items()):
        for w, e in sorted(ws.items()):
            others = [ws[o]["rate"] for o in ws if o != w]
            st = _stats(e)
            rows.append({"kind": kind, "severity": sev, "wording": w,
                         "frame": WORDING_FRAMES[w], "n": e["n"],
                         "rate": e["rate"], **st,
                         "others_mean_rate": (sum(others) / len(others)
                                              if others else None),
                         "gap_to_others": (e["rate"] - sum(others) / len(others)
                                           if others else None),
                         "mean_words": e["mean_words"]})
    return rows


def flag_wordings(table: Sequence[Mapping[str, Any]], *, min_rungs: int = 4,
                  gap: float = 0.10, zero_excess: float = 0.10
                  ) -> dict[str, Any]:
    """Per family, which wordings are unreliable relative to their siblings.

    A wording is flagged for a family when, over at least ``min_rungs``
    severities, its exact-count compliance sits at least ``gap`` below the
    mean of the other three on average, or its zero-marker share exceeds the
    others' by ``zero_excess``. Both are relative criteria: a rung that is
    hard for every wording is not a wording problem.
    """
    by_fw: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for r in table:
        by_fw[(r["kind"], r["wording"])].append(r)
    by_rung: dict[tuple[str, int], dict[int, Mapping[str, Any]]] = defaultdict(dict)
    for r in table:
        by_rung[(r["kind"], r["severity"])][r["wording"]] = r
    out: dict[str, Any] = {}
    for (kind, w), rs in sorted(by_fw.items()):
        gaps = [r["gap_to_others"] for r in rs if r["gap_to_others"] is not None]
        zero_ex = []
        for r in rs:
            sibs = [by_rung[(kind, r["severity"])][o]["zero"]
                    for o in by_rung[(kind, r["severity"])] if o != w]
            if sibs:
                zero_ex.append(r["zero"] - sum(sibs) / len(sibs))
        mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
        mean_zero_ex = sum(zero_ex) / len(zero_ex) if zero_ex else 0.0
        flagged = (len(gaps) >= min_rungs
                   and (mean_gap <= -gap or mean_zero_ex >= zero_excess))
        out.setdefault(kind, {})[w] = {
            "frame": WORDING_FRAMES[w], "n_rungs": len(gaps),
            "mean_gap_to_others": mean_gap,
            "mean_zero_excess": mean_zero_ex,
            "rungs_below_others_by_gap": sum(1 for g in gaps if g <= -gap),
            "flagged": flagged}
    return out


def ladders_under(scan: Mapping[str, Any], *, wordings_used: Sequence[int],
                  iota_a: float | None, chance: float = 0.0
                  ) -> dict[str, Any]:
    """Per family: the ladder (rate per severity) pooled over the chosen
    wordings, its monotonicity, span and location relative to iota_A.
    Marker families are chance-free (kappa 0.000-0.005 on every stored
    table), so iota = rate at ``chance = 0``."""
    used = set(wordings_used)
    by_family: dict[str, dict[int, list[Mapping[str, Any]]]] = defaultdict(
        lambda: defaultdict(list))
    for e in scan.values():
        if e["wording"] in used:
            by_family[e["kind"]][e["severity"]].append(e)
    out = {}
    for kind, sevs in sorted(by_family.items()):
        ladder = {}
        for sev, es in sorted(sevs.items()):
            n = sum(e["n"] for e in es)
            p = sum(e["passed"] for e in es) / n
            ladder[sev] = {"rate": p, "iota": (p - chance) / (1 - chance),
                           "n": n, "zero": sum(_stats(e)["zero"] * e["n"]
                                               for e in es) / n,
                           "over": sum(_stats(e)["over"] * e["n"]
                                       for e in es) / n}
        xs = sorted(ladder)
        ys = [ladder[q]["iota"] for q in xs]
        rho = spearman([float(q) for q in xs], ys)      # q up = harder
        eligible = [q for q in xs if 0.10 <= ladder[q]["rate"] <= 0.90]
        span = (max(ys) - min(ys)) if len(ys) >= 2 else 0.0
        el = [ladder[q]["iota"] for q in eligible]
        out[kind] = {
            "ladder": {str(q): v for q, v in ladder.items()},
            "rho_severity_iota": rho,
            "span_all": span,
            "span_eligible": (max(el) - min(el)) if len(el) >= 2 else 0.0,
            "n_eligible": len(eligible),
            "min_iota": min(ys) if ys else None,
            "max_iota": max(ys) if ys else None,
            "reaches_below": (None if iota_a is None
                              else min(ys) <= iota_a - 0.15),
            "reaches_above": (None if iota_a is None
                              else max(ys) >= iota_a + 0.10),
            "straddles": (None if iota_a is None
                          else min(ys) < iota_a < max(ys)),
            "n_over_0_90": sum(1 for q in xs if ladder[q]["rate"] > 0.90),
            "classification": _classify(rho, span, ys, iota_a),
        }
    return out


def _classify(rho, span, ys, iota_a) -> str:
    if len(ys) < 3:
        return "TOO_FEW_RUNGS"
    if span < 0.15:
        return "FLAT"
    if rho is None or rho > -0.5:
        return "NON_MONOTONIC"
    if iota_a is not None and max(ys) < iota_a:
        return "MONOTONE_ALL_BELOW_A"
    if iota_a is not None and min(ys) > iota_a - 0.15:
        return "MONOTONE_TOO_EASY"
    return "MONOTONE_USABLE"


def misinterpretation_patterns(table: Sequence[Mapping[str, Any]]
                               ) -> dict[str, Any]:
    """Coarse patterns per wording, pooled over MK families and severities:
    the marker never appears; the marker appears exactly once whatever q;
    systematic overshoot; systematic undershoot."""
    by_w: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for r in table:
        if r["kind"] in TIER1_FAMILY_IDS:
            by_w[r["wording"]].append(r)
    out = {}
    for w, rs in sorted(by_w.items()):
        n = sum(r["n"] for r in rs)

        def pooled(key, rs=rs, n=n):
            return sum(r[key] * r["n"] for r in rs) / n

        out[w] = {"frame": WORDING_FRAMES[w], "n_rows": n,
                  "exact": pooled("exact"), "zero": pooled("zero"),
                  "under": pooled("under"), "over": pooled("over"),
                  "one_regardless_of_q": sum(
                      r["one_regardless"] * r["n"] for r in rs
                      if r["severity"] > 1) / max(1, sum(
                          r["n"] for r in rs if r["severity"] > 1)),
                  "mean_abs_miss": pooled("mean_abs_miss")}
    return out
