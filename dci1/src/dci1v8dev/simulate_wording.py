"""Wording-level simulation: apparent flatness from wording confusion versus
a genuinely flat ladder, and what the repair recovers.

Each rung's observed compliance is a mixture over the four wording frames
(one per block, as §8.4 assigns them). Under a *bad* frame the model's
behaviour is not the ladder's: with probability ``p_confused`` the marker is
absent from the answer altogether (the pattern the stored rows show for the
frames that do not say "the word": zero-marker shares of 0.46-0.53 on the
Gemma checkpoints, 0.92-1.00 for "though"/"namely"), so exact-count
compliance is deflated at every q and the four-frame average is flattened;
under a robust frame compliance follows the true ladder. Two
cases:

* ``wording_flat``: a genuinely steep ladder whose two bad frames flatten
  the four-frame average --- the repair (drop the bad frames) recovers it;
* ``truly_flat``: all four frames follow a flat ladder --- the repair
  changes nothing.

The audit statistic used to *detect* a bad frame (the gap of a frame's
exact-count compliance to its siblings over the rungs, and its excess
zero-marker share) is the one ``wording.flag_wordings`` applies to the
stored rows; here its false-flag rate on the truly flat ladder and its
detection rate on the confused one are measured.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from dci1v8dev.prescreen.ladder import spearman
from dci1v8dev.wording import flag_wordings

__all__ = ["simulate_wording_case", "simulate_wording_cases"]

STEEP = [0.95, 0.90, 0.84, 0.76, 0.66, 0.54, 0.42, 0.30]
FLAT = [0.66, 0.65, 0.64, 0.64, 0.63, 0.62, 0.62, 0.61]


def _rows(rng: np.random.Generator, truth: Sequence[float], *, bad: Sequence[int],
          p_confused: float, n_topics: int = 48, draws: int = 4,
          kind: str = "MK1") -> list[dict[str, Any]]:
    """The per-(severity, wording) table ``flag_wordings`` reads, drawn from
    the mixture. Bad frames: with probability p_confused the marker is absent
    (statistic 0); otherwise the ladder's own count (exact with probability
    truth[q], else off by one)."""
    table = []
    for i, q in enumerate(range(1, 9)):
        by_w = {}
        for w in range(4):
            n = n_topics * draws
            confused = rng.random(n) < (p_confused if w in bad else 0.0)
            passes = rng.random(n) < truth[i]
            stat = np.where(confused, 0, np.where(passes, q,
                                                  q + rng.choice([-1, 1], n)))
            stat = np.clip(stat, 0, None)
            exact = float(np.mean(stat == q))
            by_w[w] = {"kind": kind, "severity": q, "wording": w, "n": n,
                       "rate": exact, "exact": exact,
                       "zero": float(np.mean(stat == 0)),
                       "under": float(np.mean(stat < q)),
                       "over": float(np.mean(stat > q)),
                       "one_regardless": float(np.mean(stat == 1)),
                       "mean_abs_miss": float(np.mean(np.abs(stat - q)))}
        for w, r in by_w.items():
            others = [by_w[o]["rate"] for o in by_w if o != w]
            r["others_mean_rate"] = sum(others) / 3
            r["gap_to_others"] = r["rate"] - r["others_mean_rate"]
            table.append(r)
    return table


def simulate_wording_case(name: str, truth: Sequence[float], *, bad: Sequence[int],
                          p_confused: float, n_sims: int = 200, seed: int = 5
                          ) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    flagged_bad, flagged_good, rho_all, rho_rep, span_all, span_rep = [], [], [], [], [], []
    for _ in range(n_sims):
        table = _rows(rng, truth, bad=bad, p_confused=p_confused)
        flags = flag_wordings(table)["MK1"]
        fl = {w for w, v in flags.items() if v["flagged"]}
        flagged_bad.append(len(fl & set(bad)) / len(bad) if bad else 0.0)
        flagged_good.append(len(fl - set(bad)) / (4 - len(bad)))
        robust = [w for w in range(4) if w not in fl] or list(range(4))
        by_q_all = {}
        by_q_rep = {}
        for r in table:
            by_q_all.setdefault(r["severity"], []).append(r["rate"])
            if r["wording"] in robust:
                by_q_rep.setdefault(r["severity"], []).append(r["rate"])
        ya = [sum(v) / len(v) for q, v in sorted(by_q_all.items())]
        yr = [sum(v) / len(v) for q, v in sorted(by_q_rep.items())]
        rho_all.append(spearman([float(q) for q in sorted(by_q_all)], ya))
        rho_rep.append(spearman([float(q) for q in sorted(by_q_rep)], yr))
        span_all.append(max(ya) - min(ya))
        span_rep.append(max(yr) - min(yr))
    m = lambda xs: float(np.mean(xs))
    return {"case": name, "truth": list(truth), "bad_frames": list(bad),
            "p_confused": p_confused, "n_sims": n_sims,
            "true_span": max(truth) - min(truth),
            "detection_rate_bad_frames": m(flagged_bad),
            "false_flag_rate_good_frames": m(flagged_good),
            "apparent_span_all_frames": m(span_all),
            "span_after_repair": m(span_rep),
            "rho_all_frames": m(rho_all), "rho_after_repair": m(rho_rep)}


def simulate_wording_cases(*, n_sims: int = 200, seed: int = 5) -> dict[str, Any]:
    return {
        "wording_flat": simulate_wording_case(
            "wording_flat", STEEP, bad=[1, 3], p_confused=0.7, n_sims=n_sims,
            seed=seed),
        "wording_flat_one_frame": simulate_wording_case(
            "wording_flat_one_frame", STEEP, bad=[1], p_confused=0.7,
            n_sims=n_sims, seed=seed + 1),
        "truly_flat": simulate_wording_case(
            "truly_flat", FLAT, bad=[], p_confused=0.0, n_sims=n_sims,
            seed=seed + 2),
        "truly_flat_with_bad_frame": simulate_wording_case(
            "truly_flat_with_bad_frame", FLAT, bad=[1], p_confused=0.7,
            n_sims=n_sims, seed=seed + 3),
    }
