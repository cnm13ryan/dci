"""Shared palette, typography and interval estimators for the figure set.

The palette is the validated categorical theme, used in fixed slot order and
never cycled. It was checked with the reference validator over ALL pairs on the
light surface (`#fcfcfb`): the two-, three- and four-series subsets used here
pass the lightness band, chroma floor, CVD separation and normal-vision floor.
Aqua sits below 3:1 against the surface, which obliges visible labels — every
series that uses it carries a legend entry and a direct label.

Every interval in the figure set comes from one place: a percentile bootstrap
over the 20 TASK clusters, 4000 draws, 2.5/97.5 percentiles. Task is the cluster
unit because replicates of the same task are not independent, and because every
τ in this study is a within-task paired difference. These are exploratory
intervals: no multiplicity correction is applied and none is claimed.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

# --------------------------------------------------------------- palette
#: Fixed categorical slots. An entity keeps its colour in every figure; a figure
#: that shows fewer series does not repaint the survivors.
SLOT = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a", 4: "#4a3aa7"}
INK = "#1a1a19"
MUTED = "#6f6f6a"
#: Reserved for conditions whose own manipulation check failed. Deliberately not
#: a categorical slot, so a failed manipulation can never read as "series 5".
INVALID = "#a9a9a4"
SURFACE = "#fcfcfb"

#: Structural class, which is the thing the amplifier figures actually contrast.
CLASS_COLOR = {"unattached mark": SLOT[2], "enclosing pair": SLOT[1],
               "manipulation failed": INVALID}

#: The two conditions of the reasoning experiment.
AMP, CTRL = "X_SEMICOLON_FREE", "X_PAREN_FREE"
COND_COLOR = {AMP: SLOT[2], CTRL: SLOT[1]}
COND_LABEL = {AMP: "amplifying background\n(exactly 1 semicolon)",
              CTRL: "matched control background\n(exactly 1 bracket pair)"}
COND_SHORT = {AMP: "amplifier", CTRL: "control"}

#: Variant colours for the amplifier-property figures, in fixed slot order.
VARIANT_COLOR = {"X_SEMICOLON_FREE": SLOT[2], "X_PAREN_FREE": SLOT[1],
                 "X_ELLIPSIS_FREE": SLOT[3], "X_COLON_FREE": SLOT[4]}

ARBITRATION_ORDER = ("both", "target only", "focal only", "neither")
ARBITRATION_COLOR = dict(zip(ARBITRATION_ORDER,
                             (SLOT[1], SLOT[2], SLOT[3], SLOT[4])))
ARBITRATION_MARKER = dict(zip(ARBITRATION_ORDER, ("o", "s", "^", "D")))

BOOTSTRAP_DRAWS = 4000
BOOTSTRAP_UNIT = "task_id"
BOOTSTRAP_INTERVAL = "percentile 2.5 / 97.5"


def use_style() -> None:
    """Recessive grid, thin marks, one consistent typography."""
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.edgecolor": "#c8c8c2", "axes.linewidth": 0.8,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "grid.color": "#e4e4de", "grid.linewidth": 0.7,
        "axes.grid": True, "axes.axisbelow": True,
        "lines.linewidth": 1.6, "lines.markersize": 5,
        "legend.frameon": False, "figure.dpi": 140,
    })


# ----------------------------------------------------------- estimators
def rng() -> np.random.Generator:
    return np.random.default_rng(20260811)


def generator_for(key: str) -> np.random.Generator:
    """A generator determined by WHAT is being estimated, not by call order.

    A single shared stream makes an interval depend on how many estimates were
    drawn before it, so re-ordering the figures silently moves the error bars by
    a few hundredths. Seeding from the estimand's own name makes every interval
    reproducible on its own terms.
    """
    import hashlib
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
    return np.random.default_rng(int.from_bytes(digest, "big") ^ 20260811)


def boot_ci(values: np.ndarray, generator: np.random.Generator,
            draws: int = BOOTSTRAP_DRAWS) -> tuple[float, float]:
    """Percentile interval for the mean, resampling the CLUSTERS themselves."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    index = generator.integers(0, values.size, size=(draws, values.size))
    resampled = values[index].mean(axis=1)
    return float(np.percentile(resampled, 2.5)), float(np.percentile(resampled, 97.5))


def cluster_rate(frame: pd.DataFrame, column: str, key: str) -> dict[str, Any]:
    """Task-clustered mean of a 0/1 column, with its bootstrap interval."""
    per_task = frame.groupby(BOOTSTRAP_UNIT)[column].mean().to_numpy(float)
    low, high = boot_ci(per_task, generator_for(key))
    return {"estimate": float(per_task.mean()) if per_task.size else float("nan"),
            "lo": low, "hi": high, "n_rows": int(len(frame)),
            "n_tasks": int(per_task.size)}


def per_task_tau(frame: pd.DataFrame, focal: str = "B", reference: str = "C_L3",
                 column: str = "a_failure") -> pd.Series:
    """Within-task paired excess failure, focal minus reference.

    Returned per task rather than averaged, so a downstream Δ can subtract two
    τ series task by task and keep the pairing that makes the interval valid.
    """
    cells = frame.groupby(["arm", BOOTSTRAP_UNIT])[column].mean()
    if focal not in cells.index.get_level_values("arm"):
        return pd.Series(dtype=float)
    return (cells.loc[focal] - cells.loc[reference]).dropna()


def summarise(series: pd.Series, key: str) -> dict[str, Any]:
    values = series.to_numpy(float)
    low, high = boot_ci(values, generator_for(key))
    return {"estimate": float(values.mean()) if values.size else float("nan"),
            "lo": low, "hi": high, "n_tasks": int(values.size)}


#: Appended to every budget axis. `b = 0` is a different KIND of condition — the
#: model's own non-thinking mode, not a trace truncated to zero — and the axis
#: says so without a three-line tick label that collides with its neighbours at
#: the crowded low end of a linear scale.
BUDGET_AXIS_LABEL = ("assigned reasoning budget b  (the treatment)\n"
                     "* b = 0 is the model's native non-thinking mode, "
                     "not a zero-length truncation")


def budget_label(budget: int) -> str:
    return "0*" if budget == 0 else str(budget)


def save(fig, directory, name: str) -> None:
    """Every figure ships PNG, PDF and SVG under one stem."""
    from pathlib import Path
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(directory / f"{name}.{suffix}", bbox_inches="tight")
    print(f"  wrote {name}.{{png,pdf,svg}}")
