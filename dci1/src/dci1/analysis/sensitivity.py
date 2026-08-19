"""Stochastic-stability sensitivity analysis over pseudo-runs (amendment §2.8).

Robustness and sensitivity only — never a replacement for the preregistered
block-bootstrap intervals, never a way to choose a realised dataset. Reports:

* the distribution of each registered point estimate over stochastic draws;
* the probability the estimated effect changes sign relative to the primary;
* variability of interval-based conclusions (exchangeability, equivalence) on
  the first `pseudo_run_full_analysis_count` pseudo-runs (D05).

No model inference occurs here: this module reads the frozen cache through
the pseudo-run builder only, and the primary lineage is asserted bit-identical
before and after the sweep.
"""
from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

from dci1.analysis.estimators import BlockTable, build_block_table, delta, tau_by_order
from dci1.analysis.tables import score_table
from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST, Block
from dci1.evidence.store import read_jsonl, write_json
from dci1.generation.pools import Cell
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import (
    PSEUDO_RUN_FULL_ANALYSIS_COUNT,
    ProtocolError,
    StudyConfig,
)
from dci1.resampling.pseudo import (
    assert_primary_invariant,
    build_pseudo_run,
    primary_fingerprint,
    pseudo_dir,
)

REGISTERED_POINTS = (f"tau_{TARGET_FIRST}", f"tau_{ADDED_FIRST}",
                     "delta_12", "delta_13", "delta_23")


def point_estimates(scored_rows: list[dict[str, Any]]) -> dict[str, float]:
    table: BlockTable = build_block_table(scored_rows)
    return {
        f"tau_{TARGET_FIRST}": tau_by_order(table, TARGET_FIRST),
        f"tau_{ADDED_FIRST}": tau_by_order(table, ADDED_FIRST),
        "delta_12": delta(table, 1, 2),
        "delta_13": delta(table, 1, 3),
        "delta_23": delta(table, 2, 3),
    }


def run_sensitivity(spec: ModelSpec, cells: list[Cell], blocks: list[Block],
                    *, stage_dir: Path, config: StudyConfig, n: int, m: int,
                    references: tuple[str, str, str],
                    primary_estimates: dict[str, float],
                    bootstrap_seed_value: int,
                    pseudo_runs: int | None = None) -> dict[str, Any]:
    stage_dir = Path(stage_dir)
    runs = config.pseudo_run_count if pseudo_runs is None else pseudo_runs
    if runs > config.pseudo_run_count:
        raise ProtocolError("more pseudo-runs than the frozen count")

    before = primary_fingerprint(stage_dir)
    per_run: list[dict[str, float]] = []
    full_conclusions: list[dict[str, Any]] = []
    for r in range(runs):
        build_pseudo_run(spec, cells, stream="confirmatory",
                         stage_dir=stage_dir, config=config, run_index=r)
        rows = read_jsonl(pseudo_dir(stage_dir, r) / "table.jsonl")
        scored = score_table(rows, blocks, n=n, m=m, references=references)
        per_run.append(point_estimates(scored))
        if r < PSEUDO_RUN_FULL_ANALYSIS_COUNT:
            from dci1.analysis.run import analyze

            result = analyze(rows, blocks, n=n, m=m, references=references,
                             bootstrap_seed_value=bootstrap_seed_value + r,
                             masked=False)
            full_conclusions.append({
                "run": r,
                "exchangeability_holds": result.get("exchangeability_holds"),
                "outcomes": {k: v["outcome"]
                             for k, v in (result.get("outcomes") or
                                          {}).items()},
            })
    after = primary_fingerprint(stage_dir)
    assert_primary_invariant(before, after)

    summary: dict[str, Any] = {"pseudo_runs": runs, "estimates": {}}
    for name in REGISTERED_POINTS:
        values = [run[name] for run in per_run]
        primary = primary_estimates.get(name)
        sign_change = (sum(1 for v in values
                           if primary is not None and v * primary < 0)
                       / len(values)) if values else None
        summary["estimates"][name] = {
            "primary": primary,
            "mean": statistics.fmean(values) if values else None,
            "sd": statistics.stdev(values) if len(values) > 1 else None,
            "q05": _quantile(values, 0.05),
            "q95": _quantile(values, 0.95),
            "sign_change_probability": sign_change,
        }
    if full_conclusions:
        holds = [c["exchangeability_holds"] for c in full_conclusions]
        summary["exchangeability_variability"] = {
            "full_analyses": len(full_conclusions),
            "holds_share": (sum(1 for h in holds if h is True)
                            / len(holds)),
        }
        summary["full_conclusions"] = full_conclusions
    summary["primary_invariant"] = True
    write_json(stage_dir / "pseudo" / "sensitivity_summary.json", summary)
    return summary


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]
