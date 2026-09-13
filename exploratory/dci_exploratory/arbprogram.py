"""Scoring and estimation for the arbitration programme.

Two questions separate the explanations this programme is built to distinguish:

  joint improvement   more reasoning raises P(both) -- the model gets better at
                      the whole task;
  arbitration change  more reasoning moves probability between "target only" and
                      "focal only" -- the model does not get better, it changes
                      which instruction it sacrifices.

Both are measured from the SAME scored rows, so a result can never be joint
improvement in one table and arbitration in another.

Everything is estimated with one cluster bootstrap over `task_id`. When a task is
resampled, every condition and every decoder replicate belonging to it is carried
along, so tau, Delta, Gamma and the four arbitration probabilities in a single
draw all describe the same resampled set of tasks. Individual generations are
never resampled on their own: replicates of one task are not independent.
"""
from __future__ import annotations

import hashlib
import re
import warnings
from typing import Callable, Sequence

import numpy as np
import pandas as pd

#: A final answer is supposed to be an ANSWER. These markers are how continued
#: scratch work announces itself when a thinking phase is cut off mid-thought.
SCRATCH = re.compile(
    r"\b(?:wait|let me (?:check|count|think|see)|i need to|hmm|actually,? (?:no|wait)|"
    r"let'?s count|recount|that'?s wrong)\b", re.IGNORECASE)

AMPLIFIER = "X_SEMICOLON_FREE"
CONTROL = "X_PAREN_FREE"
#: Every background this line of experiments has used. A missing entry makes
#: `background_name` NaN, which silently drops the whole condition out of every
#: groupby, so new backgrounds are registered here rather than discovered later.
BACKGROUND_LABEL = {AMPLIFIER: "semicolon", CONTROL: "parentheses",
                    "X_DEGREE_FREE": "degree", "X_ASTERISK_FREE": "asterisk"}
FOCAL_ARM = "B"
REFERENCE_ARM = "C_L3"
DRAWS = 10_000

#: The four mutually exclusive outcomes of the focal arm.
STATES = ("both", "target only", "focal only", "neither")

# ---------------------------------------------------------- generation states
# The provenance of a missing or invalid final answer decides whether it is
# evidence about the model or evidence about the apparatus, and the two must
# never be pooled. The state is assigned BEFORE any verifier runs, from the
# harness's own record, so it cannot depend on what a verifier returned.
#
#: A final answer exists. The verifiers decide the behavioural outcome.
VALID_ANSWER = "VALID_ANSWER"
#: The run was valid but the model produced no acceptable final answer under the
#: declared condition. This is MODEL behaviour, so it is scored rather than
#: dropped -- an empty answer does not satisfy "exactly four sentences", and
#: excluding it would condition on a treatment-affected outcome. It carries its
#: own label so the sensitivity is computable and any future decision to exclude
#: it is a visible change of estimand rather than a silent one.
NO_FINAL_ANSWER = "NO_FINAL_ANSWER"
#: Verified external apparatus failure: empty generation, decoding failure,
#: backend exception. Never a behavioural outcome. Every pass column is NaN, so
#: the row leaves each estimand through the existing nanmean and dropna paths.
TECHNICAL_FAILURE = "TECHNICAL_FAILURE"

GENERATION_STATES = (VALID_ANSWER, NO_FINAL_ANSWER, TECHNICAL_FAILURE)


def generation_state(answer: object, technical_failure: object) -> str:
    """Classify one row's answer channel before it reaches a verifier."""
    if bool(technical_failure):
        return TECHNICAL_FAILURE
    if not isinstance(answer, str) or not answer.strip():
        return NO_FINAL_ANSWER
    return VALID_ANSWER


# ----------------------------------------------------------------- scoring
def score(rows: Sequence[dict]) -> pd.DataFrame:
    """Score the ANSWER channel against the registry. The reasoning is never read.

    `A_pass` is the target (exactly four sentences). `Q_pass` is whichever
    instruction occupies the focal slot in this row -- `B` in the focal arm,
    `C_L3` in the reference arm -- so a single column carries the arm's own
    constraint and the two arms stay structurally identical.
    """
    from dci_exploratory import extensions, harvest, mechanism
    extensions.register()
    state = harvest.load()

    frame = pd.DataFrame(list(rows))
    target_id = frame["measured"].iloc[0]

    # The state is decided from the harness record, never from `fillna("")`.
    # Substituting the empty string made every verifier return binary_pass=0, so
    # a backend exception arrived in the estimands indistinguishable from a
    # model that wrote a non-compliant answer.
    technical = (frame["technical_failure"] if "technical_failure" in frame
                 else pd.Series(False, index=frame.index))
    frame["generation_state"] = [generation_state(a, t) for a, t
                                 in zip(frame["raw_final_answer"], technical)]
    scorable = frame["generation_state"] != TECHNICAL_FAILURE
    # Apparatus failures are never shown to a verifier at all.
    answers = frame["raw_final_answer"].where(scorable).fillna("")

    def verify(constraints, attribute="binary_pass"):
        """Verify only the rows the apparatus actually produced."""
        out = []
        for ok, text, constraint in zip(scorable, answers, constraints):
            if not ok:
                out.append(np.nan)
                continue
            result = state.verify(text, constraint)
            value = getattr(result, attribute)
            out.append(value if attribute != "binary_pass" else float(value))
        return out

    frame["A_pass"] = verify([target_id] * len(frame))
    frame["Q_pass"] = verify(frame["arm"])
    frame["background_pass"] = verify(frame["background"])
    frame["A_status"] = verify([target_id] * len(frame), attribute="status")

    features = pd.DataFrame([mechanism.row_features(t) if ok else {}
                             for ok, t in zip(scorable, answers)],
                            index=frame.index)
    frame["sentence_count"] = features.get("n_sentences", np.nan)
    frame["word_count"] = features.get("n_words", np.nan)
    frame["scratchpad_leakage"] = answers.where(scorable).str.contains(
        SCRATCH, na=False)

    frame["arbitration_state"] = np.select(
        [~scorable,
         (frame["A_pass"] == 1) & (frame["Q_pass"] == 1),
         (frame["A_pass"] == 1) & (frame["Q_pass"] == 0),
         (frame["A_pass"] == 0) & (frame["Q_pass"] == 1)],
        [TECHNICAL_FAILURE, *STATES[:3]], default=STATES[3])
    frame["A_failure"] = 1.0 - frame["A_pass"]
    frame["background_name"] = frame["background"].map(BACKGROUND_LABEL)
    return frame


# ------------------------------------------------------------- bootstrap
class Clusters:
    """One resampling of the 20 tasks, reused by every estimand in a report.

    A per-task series is turned into an estimate by averaging it; the bootstrap
    replaces that average with the average over a resampled task list. Because
    the same index matrix is applied to every series, a draw that happens to
    exclude a task excludes it from tau, from Delta and from the arbitration
    table at once.
    """

    def __init__(self, tasks: Sequence[str], key: str, draws: int = DRAWS):
        self.tasks = list(tasks)
        digest = hashlib.blake2b(key.encode(), digest_size=8).digest()
        rng = np.random.default_rng(int.from_bytes(digest, "big"))
        self.index = rng.integers(0, len(self.tasks), size=(draws, len(self.tasks)))

    def interval(self, series: pd.Series) -> tuple[float, float, float]:
        """Point estimate and a 95% percentile interval, or NaN if empty.

        A task with no estimate (every row of it a technical failure, say) is
        NaN after the reindex, and a draw that resampled only such tasks has no
        mean. The percentiles are taken over the draws that do. Before, one empty
        draw made both bounds NaN, so a run with failures concentrated in many
        tasks printed unusable intervals beside valid point estimates. Where no
        draw is empty, the draws and percentiles are exactly what they were.
        """
        values = series.reindex(self.tasks).to_numpy(float)
        if np.all(np.isnan(values)):
            return (np.nan, np.nan, np.nan)
        drawn = values[self.index]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # empty draws
            means = np.nanmean(drawn, axis=1)
        means = means[~np.isnan(means)]
        return (float(np.nanmean(values)),
                float(np.percentile(means, 2.5)),
                float(np.percentile(means, 97.5)))


# -------------------------------------------------------------- estimands
def per_task_rate(frame: pd.DataFrame, column: str, **where) -> pd.Series:
    """Mean of `column` over the replicates of each task, in one cell."""
    subset = frame
    for name, value in where.items():
        subset = subset[subset[name] == value]
    if subset.empty:
        return pd.Series(dtype=float)
    return subset.groupby("task_id")[column].mean()


def tau(frame: pd.DataFrame, *, background: str, order: str,
        reasoning_budget: int, **where) -> pd.Series:
    """P(A fails | B) - P(A fails | R), paired within task.

    Positive means the focal instruction damages the target more than the matched
    reference does -- interference attributable to B rather than to carrying a
    third instruction at all.

    `**where` adds further equality selectors on any column, so a design that
    holds the background fixed and varies something else -- the route-closing
    instruction, say -- gets the same estimator rather than a second one written
    beside it.
    """
    common = dict(background=background, order=order,
                  reasoning_budget=reasoning_budget, **where)
    focal = per_task_rate(frame, "A_failure", arm=FOCAL_ARM, **common)
    reference = per_task_rate(frame, "A_failure", arm=REFERENCE_ARM, **common)
    return (focal - reference).dropna()


def omega(frame: pd.DataFrame, *, order: str, reasoning_budget: int,
          background: str = AMPLIFIER, column: str = "route",
          closed: str = "anti_splice", control: str = "off_route") -> pd.Series:
    """The route-closing contrast: tau with the route closed minus tau without.

    Negative means closing the route REDUCED the interference, which is what the
    splice mechanism predicts. The background is held fixed in both arms, and the
    control arm carries a matched off-route instruction, so the contrast is not
    confounded with the added instruction load.
    """
    common = dict(background=background, order=order,
                  reasoning_budget=reasoning_budget)
    return (tau(frame, **common, **{column: closed})
            - tau(frame, **common, **{column: control})).dropna()


def delta(frame: pd.DataFrame, *, order: str, reasoning_budget: int,
          amplifier: str = AMPLIFIER, control: str = CONTROL) -> pd.Series:
    """tau under one background minus tau under its matched control, per task.

    Defaults to the semicolon-versus-brackets contrast every earlier round used.
    `control` is a parameter because the boundary experiment replaces the bracket
    control with a matched non-boundary MARK, and that contrast has to be the
    same estimator rather than a second one written beside it.
    """
    amp = tau(frame, background=amplifier, order=order,
              reasoning_budget=reasoning_budget)
    ctl = tau(frame, background=control, order=order,
              reasoning_budget=reasoning_budget)
    return (amp - ctl).dropna()


def gamma(frame: pd.DataFrame, *, order: str, low: int, high: int,
          amplifier: str = AMPLIFIER, control: str = CONTROL) -> pd.Series:
    """How much reasoning changes the background contrast, within an order."""
    common = dict(order=order, amplifier=amplifier, control=control)
    return (delta(frame, reasoning_budget=high, **common)
            - delta(frame, reasoning_budget=low, **common)).dropna()


def behavioural(frame: pd.DataFrame) -> pd.DataFrame:
    """The rows the four arbitration states partition: all but technical failures.

    Every view of the arbitration states reads its rows from here, the bootstrap
    table and the printed crosstabs alike, so the two cannot disagree about the
    denominator for the same run.
    """
    if "generation_state" not in frame:
        return frame
    return frame[frame["generation_state"] != TECHNICAL_FAILURE]


def arbitration(frame: pd.DataFrame, **where) -> dict[str, pd.Series]:
    """Per-task probability of each of the four focal-arm outcomes.

    The four states partition the behavioural rows only. A technical failure has
    `arbitration_state == TECHNICAL_FAILURE`, so leaving it in the denominator
    would count it as a miss for all four states and deflate every probability.
    """
    subset = behavioural(frame)
    subset = subset[subset["arm"] == FOCAL_ARM]
    for name, value in where.items():
        subset = subset[subset[name] == value]
    return {state: subset.assign(hit=(subset["arbitration_state"] == state)
                                 .astype(float)).groupby("task_id")["hit"].mean()
            for state in STATES}


def survival(frame: pd.DataFrame, **where) -> pd.Series:
    """S = P(target only) - P(focal only): which instruction survives a failure."""
    states = arbitration(frame, **where)
    return (states["target only"] - states["focal only"]).dropna()


# ---------------------------------------------------------------- display
def table(clusters: Clusters, rows: Sequence[tuple[str, pd.Series]]) -> pd.DataFrame:
    """Point estimate and interval for each named per-task series."""
    out = []
    for name, series in rows:
        estimate, lo, hi = clusters.interval(series)
        out.append({"estimand": name, "estimate": estimate, "lo": lo, "hi": hi,
                    "n_tasks": int(series.notna().sum())})
    return pd.DataFrame(out)


def show(frame: pd.DataFrame, float_format: Callable[[float], str] | None = None
         ) -> str:
    return frame.to_string(index=False, float_format=float_format
                           or (lambda v: f"{v:+.3f}"))
