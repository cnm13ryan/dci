"""Figure 1 candidates, designed for a reader who knows nothing about this project.

Three prototypes, then the selected headline figure and its supporting
distribution plot. Every value is recomputed from the stored generations by the
same pipeline the technical figures use — the presentation is selective, the
analysis is not.

No project vocabulary appears on any of these figures: no DCI, no tau, no QAC,
no A/B/R/C, no internal constraint IDs. The two conditions are named by what was
actually changed in the prompt ("+ one bracket pair" / "+ one semicolon"),
because naming them "control" and "amplifier" would put our conclusion on the
axis that is supposed to show it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import plotdata, plotstyle

OUT = Path("figures/reasoning_compute")
DATA = OUT / "data"
plotstyle.use_style()

# ---------------------------------------------------------------- vocabulary
# Reader-facing names. The left column never appears on a figure.
BRACKET, SEMICOLON = "X_PAREN_FREE", "X_SEMICOLON_FREE"
LABEL = {BRACKET: "+ one bracket pair", SEMICOLON: "+ one semicolon"}
COLOR = {BRACKET: "#2a78d6", SEMICOLON: "#eb6834"}
STYLE = {BRACKET: "-", SEMICOLON: "--"}          # so the two survive greyscale
MARKER = {BRACKET: "o", SEMICOLON: "s"}

#: The experimental sequence, in the order it is read, with the labels a new
#: reader can act on. "Natural" is set apart because it answers a different
#: question from the capped settings.
SETTINGS = [(0, "No\nthinking"), (256, "256"), (512, "512"),
            (1024, "1,024"), (4096, "4,096"), ("natural", "Natural\nreasoning")]


def load() -> tuple[pd.DataFrame, dict]:
    run = plotdata.latest("runs/stageS18_reasoning_design_*/")
    frame = plotdata.load_all_reasoning(run)
    return frame, {"run": run}


def tau_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Extra main-instruction failures caused by the competing instruction."""
    records = []
    for setting, _ in SETTINGS:
        for variant in (BRACKET, SEMICOLON):
            cell = frame[(frame["setting"] == setting) & (frame["variant"] == variant)]
            if cell.empty:
                continue
            series = plotstyle.per_task_tau(cell)
            stats = plotstyle.summarise(series, f"headline|{setting}|{variant}")
            records.append({"setting": setting, "variant": variant,
                            "label": LABEL[variant], **stats,
                            "cap_hit": cell["reasoning_cap_hit"].mean(),
                            "realised_median": cell["reasoning_tokens"].median()})
    return pd.DataFrame(records)


def positions() -> tuple[list[float], list[str]]:
    """Ordered categorical positions, with a visible gap before Natural."""
    x = [0, 1, 2, 3, 4, 5.55]
    return x, [label for _, label in SETTINGS]


def draw_lines(ax, table, x, linewidth=2.4, markersize=8, label_fontsize=11):
    for variant in (BRACKET, SEMICOLON):
        sub = table[table["variant"] == variant]
        order = {s: i for i, (s, _) in enumerate(SETTINGS)}
        sub = sub.assign(pos=[x[order[s]] for s in sub["setting"]]).sort_values("pos")
        ax.errorbar(sub["pos"], sub["estimate"],
                    yerr=[sub["estimate"] - sub["lo"], sub["hi"] - sub["estimate"]],
                    color=COLOR[variant], ls=STYLE[variant], marker=MARKER[variant],
                    lw=linewidth, markersize=markersize, capsize=3, elinewidth=1.2,
                    markeredgecolor="white", markeredgewidth=0.9, zorder=3)
        last = sub.iloc[-1]
        # A series that ends ON the zero line would have the zero line struck
        # through its own label, so that label steps up out of the way.
        dy = 13 if abs(last["estimate"]) < 0.05 else 0
        ax.annotate(LABEL[variant], (last["pos"], last["estimate"]),
                    xytext=(12, dy), textcoords="offset points", va="center",
                    fontsize=label_fontsize, fontweight="bold", color=COLOR[variant])
    return ax


def frame_axes(ax, x, labels, ylabel=True, tick_fontsize=10):
    ax.axhline(0, color="#1a1a19", lw=1.0, zorder=1)
    ax.axvline((x[4] + x[5]) / 2, color="#c8c8c2", lw=1.0, ls=":", zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=tick_fontsize)
    ax.set_xlim(-0.45, x[-1] + 2.55)
    ax.set_ylim(-0.14, 0.82)
    ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_yticklabels(["0", "0.2", "0.4", "0.6"], fontsize=tick_fontsize)
    if ylabel:
        ax.set_ylabel("Increase in failure rate\non the main instruction",
                      fontsize=11.5)
    ax.set_xlabel("How much thinking the model was allowed\n"
                  "(numbers are the maximum reasoning tokens it could use)",
                  fontsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", alpha=.45)
    ax.grid(axis="x", visible=False)


# =============================================================== prototype A
def prototype_a(table, natural, name="prototype_A_full_progression", final=False):
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    x, labels = positions()
    draw_lines(ax, table, x)
    frame_axes(ax, x, labels)

    bracket_last = table[(table["variant"] == BRACKET)
                         & (table["setting"] == "natural")]["estimate"].iloc[0]
    semi_last = table[(table["variant"] == SEMICOLON)
                      & (table["setting"] == "natural")]["estimate"].iloc[0]
    ax.annotate("More thinking\nfixes this one", (x[3], -0.005),
                xytext=(2.45, 0.20), fontsize=11, color=COLOR[BRACKET],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[BRACKET], lw=1.6))
    ax.annotate("This one stays broken", (x[4], semi_last + 0.03),
                xytext=(1.95, 0.74), fontsize=11, color=COLOR[SEMICOLON],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[SEMICOLON], lw=1.6))
    # The right-hand gap between the two lines is the only clear space; the
    # endpoint note goes there rather than under the axis, where it collided
    # with the blue line's own label.
    ax.annotate("model finished thinking on its own\n"
                f"{natural['cap_reached']}/{natural['n']} hit the safety limit\n"
                f"median {natural['median']:,.0f} reasoning tokens",
                (x[5] + 0.55, 0.175), ha="center", va="center", fontsize=8.5,
                color="#6f6f6a", linespacing=1.5)
    ax.set_title("Does letting the model think for longer remove the conflict\n"
                 "between its instructions?", fontsize=13.5, fontweight="bold",
                 loc="left", pad=14)
    fig.tight_layout()
    plotstyle.save(fig, OUT, name)
    plt.close(fig)


# =============================================================== prototype B
def prototype_b(table, natural, name="prototype_B_endpoints"):
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    ends = [(0, "No thinking"), ("natural", "Natural reasoning")]
    x = [0, 1]
    for variant in (BRACKET, SEMICOLON):
        values = [table[(table["variant"] == variant)
                        & (table["setting"] == s)]["estimate"].iloc[0]
                  for s, _ in ends]
        lows = [table[(table["variant"] == variant)
                      & (table["setting"] == s)]["lo"].iloc[0] for s, _ in ends]
        highs = [table[(table["variant"] == variant)
                       & (table["setting"] == s)]["hi"].iloc[0] for s, _ in ends]
        ax.errorbar(x, values, yerr=[np.array(values) - lows, np.array(highs) - values],
                    color=COLOR[variant], ls=STYLE[variant], marker=MARKER[variant],
                    lw=3.0, markersize=11, capsize=4, elinewidth=1.3,
                    markeredgecolor="white", markeredgewidth=1.0, zorder=3)
        ax.annotate(f"{LABEL[variant]}\n{values[1]:.2f}", (1, values[1]),
                    xytext=(14, 0), textcoords="offset points", va="center",
                    fontsize=11.5, fontweight="bold", color=COLOR[variant])
        ax.annotate(f"{values[0]:.2f}", (0, values[0]), xytext=(-12, 0),
                    textcoords="offset points", va="center", ha="right",
                    fontsize=11, color=COLOR[variant])
    ax.axhline(0, color="#1a1a19", lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(["No thinking", "Natural reasoning\n(finished on its own)"],
                       fontsize=11)
    ax.set_xlim(-0.55, 2.15)
    ax.set_ylim(-0.14, 0.82)
    ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_ylabel("Increase in failure rate\non the main instruction", fontsize=11.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", alpha=.45)
    ax.grid(axis="x", visible=False)
    ax.set_title("Letting the model finish thinking removes one conflict,\n"
                 "and leaves the other where it was", fontsize=13,
                 fontweight="bold", loc="left", pad=14)
    fig.tight_layout()
    plotstyle.save(fig, OUT, name)
    plt.close(fig)


# =============================================================== prototype C
def prototype_c(table, natural, name="prototype_C_with_schematic"):
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.0),
                             gridspec_kw={"width_ratios": [1.85, 1]})
    ax = axes[0]
    x, labels = positions()
    draw_lines(ax, table, x, label_fontsize=10)
    frame_axes(ax, x, labels)
    ax.annotate("More thinking\nfixes this one", (x[3], 0.02),
                xytext=(x[2] - 0.35, 0.30), fontsize=10, color=COLOR[BRACKET],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[BRACKET], lw=1.5))
    ax.annotate("This one stays broken", (x[4], 0.50),
                xytext=(x[2] + 0.15, 0.70), fontsize=10, color=COLOR[SEMICOLON],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[SEMICOLON], lw=1.5))

    ax = axes[1]
    ax.axis("off")
    ax.set_title("What the vertical axis measures", fontsize=12, fontweight="bold",
                 loc="left")
    blocks = [
        (0.86, "Prompt A", "#f0f0ea",
         'Write exactly 4 sentences.\nBegin every sentence with a\nword starting with S.'),
        (0.46, "Prompt B", "#f0f0ea",
         'Write exactly 4 sentences.\nMake each sentence longer\nthan the one before.'),
    ]
    for y, title, shade, body in blocks:
        ax.add_patch(plt.Rectangle((0.02, y - 0.20), 0.96, 0.24, transform=ax.transAxes,
                                   facecolor=shade, edgecolor="#c8c8c2", lw=0.8))
        ax.text(0.06, y - 0.005, title, transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="top")
        ax.text(0.06, y - 0.055, body, transform=ax.transAxes, fontsize=9,
                va="top", linespacing=1.35)
    ax.annotate("", xy=(0.5, 0.50), xytext=(0.5, 0.62), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#1a1a19", lw=1.4))
    ax.text(0.5, 0.20, "How much more often does the model\n"
                       "get \"exactly 4 sentences\" wrong\n"
                       "in Prompt B than in Prompt A?",
            transform=ax.transAxes, fontsize=10.5, ha="center", va="top",
            linespacing=1.5)
    ax.text(0.5, 0.02, "Both prompts also carry the same third instruction —\n"
                       "either \"one bracket pair\" or \"one semicolon\".",
            transform=ax.transAxes, fontsize=9, ha="center", va="bottom",
            color="#6f6f6a", linespacing=1.4)
    fig.suptitle("Does letting the model think for longer remove the conflict "
                 "between its instructions?", fontsize=13.5, fontweight="bold",
                 x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    plotstyle.save(fig, OUT, name)
    plt.close(fig)


# ================================================= supporting: how long it thought
def natural_distribution(frame, name="fig15_natural_reasoning_length"):
    natural = frame[frame["setting"] == "natural"]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.3))
    ax = axes[0]
    for variant in (BRACKET, SEMICOLON):
        values = natural[natural["variant"] == variant]["reasoning_tokens"]
        ax.hist(values, bins=np.linspace(0, natural["reasoning_tokens"].max(), 36),
                alpha=.55, color=COLOR[variant], label=LABEL[variant])
    ax.set_xlabel("Reasoning tokens the model used before answering", fontsize=10.5)
    ax.set_ylabel("Number of responses", fontsize=10.5)
    ax.legend(fontsize=10)
    ax.set_title("How long the model thought when nothing stopped it", fontsize=11.5)

    ax = axes[1]
    for variant in (BRACKET, SEMICOLON):
        values = np.sort(natural[natural["variant"] == variant]["reasoning_tokens"])
        ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post",
                color=COLOR[variant], ls=STYLE[variant], lw=2.2, label=LABEL[variant])
    ceiling = int(natural["engineering_ceiling"].iloc[0])
    ax.axhline(1.0, color="#c8c8c2", lw=0.8)
    ax.set_xlabel("Reasoning tokens", fontsize=10.5)
    ax.set_ylabel("Share of responses finished\nby this reasoning length", fontsize=10.5)
    ax.set_ylim(0, 1.04)
    ax.legend(fontsize=10, loc="lower right")
    ax.set_title(f"Every response finished far below the safety limit "
                 f"of {ceiling:,}", fontsize=11.5)
    fig.suptitle("When we stopped limiting its reasoning, how long did the model "
                 "actually think?", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    plotstyle.save(fig, OUT, name)
    plt.close(fig)


# ============================================== the selected headline figure
def figure1(table, natural, meta, name="figure1_headline", figsize=(8.2, 5.6)):
    """Prototype A, with every gap the cold-reader test exposed closed.

    The test found the shape read in 10-15 seconds but left the reader unable to
    say what the two lines WERE, what the units were, what the error bars meant,
    or how many items were behind each point. Each of those is now stated on the
    figure in plain words rather than deferred to a caption, because the brief
    requires the figure to stand alone.

    The "stays broken" callout no longer points from 512 down to 4,096: the cold
    reader correctly objected that an arrow along that path implies a decline the
    error bars do not support.
    """
    fig, ax = plt.subplots(figsize=figsize)
    x, labels = positions()
    draw_lines(ax, table, x)
    frame_axes(ax, x, labels)

    ax.set_ylabel("Increase in failure rate on the main instruction\n"
                  "(\u201cwrite exactly 4 sentences\u201d)", fontsize=11.5)
    ax.annotate("More thinking\nfixes this one", (x[3], -0.005),
                xytext=(2.45, 0.20), fontsize=11, color=COLOR[BRACKET],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[BRACKET], lw=1.6))
    ax.annotate("This one stays broken", (x[5] - 0.35, 0.44),
                xytext=(2.1, 0.76), fontsize=11, color=COLOR[SEMICOLON],
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=COLOR[SEMICOLON], lw=1.6,
                                connectionstyle="arc3,rad=-0.12"))
    ax.annotate("0 = the extra instruction\ncost the model nothing",
                (x[5] + 0.62, -0.062), fontsize=8.5, color="#6f6f6a",
                ha="center", va="center", linespacing=1.4)
    ax.annotate("model finished thinking on its own\n"
                f"{natural['cap_reached']}/{natural['n']} hit the safety limit\n"
                f"median {natural['median']:,.0f} reasoning tokens",
                (x[5] + 0.62, 0.185), ha="center", va="center", fontsize=8.5,
                color="#6f6f6a", linespacing=1.5)

    ax.set_title("Does letting the model think for longer remove the conflict\n"
                 "between its instructions?", fontsize=14, fontweight="bold",
                 loc="left", pad=54)
    # The single thing the cold reader could not recover from the plot: what the
    # two lines actually are. It is one sentence, so it goes on the figure.
    ax.text(0, 1.035,
            "Every prompt asks for exactly 4 sentences, plus a competing "
            "instruction, plus one formatting instruction.\n"
            "The two lines differ only in that formatting instruction \u2014 and "
            "in nothing else.",
            transform=ax.transAxes, fontsize=9.5, va="bottom", color="#3a3a36",
            linespacing=1.5)
    fig.text(0.5, -0.055,
             f"Qwen3-4B  \u00b7  {meta['n_tasks']} tasks \u00d7 "
             f"{meta['replicates']} replicates behind every point  \u00b7  "
             "error bars are 95% intervals from resampling the tasks",
             ha="center", fontsize=8.5, color="#6f6f6a")
    fig.tight_layout()
    plotstyle.save(fig, OUT, name)
    plt.close(fig)


def main() -> int:
    frame, meta = load()
    table = tau_table(frame)
    DATA.mkdir(parents=True, exist_ok=True)
    table.to_csv(DATA / "headline_extra_failures.csv", index=False)

    natural_rows = frame[frame["setting"] == "natural"]
    natural = {"n": len(natural_rows),
               "cap_reached": int(natural_rows["reasoning_cap_hit"].sum()),
               "median": float(natural_rows["reasoning_tokens"].median()),
               "max": int(natural_rows["reasoning_tokens"].max()),
               "ceiling": int(natural_rows["engineering_ceiling"].iloc[0])}
    print("natural reasoning:", natural)

    prototype_a(table, natural)
    figure1(table, natural, {'n_tasks': 20, 'replicates': 2})
    # Deployment-size test: the width a two-column paper actually gives it.
    figure1(table, natural, {'n_tasks': 20, 'replicates': 2},
            name='figure1_headline_deployment_7in', figsize=(7.0, 4.9))
    prototype_b(table, natural)
    prototype_c(table, natural)
    natural_distribution(frame)
    print(table.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
