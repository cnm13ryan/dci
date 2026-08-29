"""The staged procedure, end to end, with the legacy path beside it.

    broad cheap search -> uncertainty-aware ranking -> targeted re-screen
                       -> spaced rung retention -> (full calibration)

``run_pipeline`` takes the pre-screen table (round-0 counts) and A's grid,
runs stage 1, runs stage 2 through ``measure`` when one is supplied (the
simulation and the backtest supply one; production would generate), retains
by role, and reports the legacy certificate and retention on the same input
so the two can be compared on every replication.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from dci1v7.protocol import constants as C
from dci1v8dev.prescreen import legacy
from dci1v8dev.prescreen.rescreen import (
    DEFAULT_RESCREEN_CONFIG,
    RescreenConfig,
    max_cost_generations,
    run_rescreen,
)
from dci1v8dev.prescreen.retention import (
    DEFAULT_RETENTION_CONFIG,
    RetentionConfig,
    retain,
)
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import (
    DEFAULT_SCREEN_CONFIG,
    ScreenConfig,
    screen_families,
)

__all__ = ["run_pipeline"]


def run_pipeline(table: Sequence[PrescreenRung], a_grid: Sequence[ARung], *,
                 screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                 rescreen_config: RescreenConfig = DEFAULT_RESCREEN_CONFIG,
                 retention_config: RetentionConfig = DEFAULT_RETENTION_CONFIG,
                 measure: Callable | None = None) -> dict[str, Any]:
    stage1 = screen_families(table, a_grid, config=screen_config)
    if measure is not None:
        stage2 = run_rescreen(table, a_grid, screen_config=screen_config,
                              config=rescreen_config, measure=measure)
        final_screen = stage2["screen"]
        final_table = stage2["table"]
    else:
        stage2 = None
        final_screen = stage1
        final_table = list(table)
    retention = retain(final_screen, config=retention_config)
    certificate = legacy.legacy_certificate(table, a_grid)
    legacy_kept = legacy.legacy_retention(
        table, iota_a=certificate["iota_a_prescreen"])
    screen_cost = C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS * (
        len(table) + len(a_grid) + 1)
    per_rung = 2 * C.N_CALIBRATION_A * C.M_CAL
    return {
        "stage1": stage1,
        "stage2": stage2,
        "final_screen": final_screen,
        "final_table_size": len(final_table),
        "retention": retention,
        "legacy": {"certificate": {k: v for k, v in certificate.items()
                                   if k != "rows"},
                   "retention": legacy_kept},
        "cost": {
            "screen_generations": screen_cost,
            "rescreen_generations": (stage2["cost_generations"]
                                     if stage2 else 0),
            "rescreen_max_generations":
                max_cost_generations(rescreen_config)["max_total"],
            "calibration_generations_new":
                retention["calibration_cost_generations"],
            "calibration_generations_legacy":
                legacy_kept["n_measured"] * per_rung,
            "forwarded_new": retention["n_forwarded"],
            "forwarded_legacy": legacy_kept["n_measured"],
        },
    }
