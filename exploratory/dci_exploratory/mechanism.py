"""Round 5 analysis: one module that works for ANY target, arm set and scaffold.

The Round 1–4 analysis modules hard-wire the pair-3 slice — `focal_id="B"`,
`control="C_L3"`, `n_target=4`. That was right while there was one experiment.
Round 5 varies the target (N = 3, 5, 6; paragraphs), the arms (four marks, a
whole-answer control, a numerical family) and the model, so a module that reads
those three things out of the run's own config is the only way the same numbers
mean the same thing across experiments.

Three commitments, enforced here rather than remembered:

1. **The corrected segmenter is primary.** The pre-repair segmenter is
   reimplemented below, frozen, and reported only in a column named
   `*_legacy`. It is never the headline and never enters a contrast.
2. **Collapse is measured on the response, not inferred from the verdict.**
   `severe_collapse` counts sentences; it does not ask whether the row failed.
   Round 2 withdrew a correlation that was partly definitional, and the way to
   not repeat that is for the mechanism variables to be computable on a row
   whose target verdict is unknown.
3. **Pairing is on `pair_key`.** Never on position, never on row order.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd

EXPLORATORY_NOTE = ("EXPLORATORY — descriptive only. Intervals are paired "
                    "cluster bootstrap percentiles over tasks, with no "
                    "multiplicity control and no inferential guarantee.")

# --------------------------------------------------------- the frozen defect
# The pre-repair boundary rule, copied here so the sensitivity column can be
# computed for runs generated AFTER the repair, where storage holds only the
# corrected count. It is deliberately a verbatim reconstruction of the defect —
# one full stop before whitespace, one optional closing quote — and must never
# be improved.
_LEGACY_BOUNDARY = re.compile(r'(?<=[.!?])["”’]?\s+')


def legacy_split_sentences(text: Any) -> list[str]:
    """The Pair-3 segmenter as it stood before the Round 4 repair."""
    from dci.verifiers.rules import LIST_MARKER, normalize_text
    clean = normalize_text(text)
    if not clean:
        return []
    parts: list[str] = []
    for line in clean.split("\n"):
        line = LIST_MARKER.sub("", line).strip()
        if not line:
            continue
        parts.extend(part.strip() for part in _LEGACY_BOUNDARY.split(line)
                     if re.search(r"[A-Za-z0-9]", part))
    if parts:
        return parts
    return [clean] if re.search(r"[A-Za-z0-9]", clean) else []


# ------------------------------------------------------------- row features
_TERMINAL = re.compile(r"[.!?]")
_DASHES = ("—", "–", "--")


def _blank_line_blocks(text: str) -> int:
    from dci_exploratory.extensions import split_paragraphs
    return len(split_paragraphs(text))


def row_features(text: Optional[str]) -> dict[str, Any]:
    """Everything the mechanism account talks about, measured on the text alone.

    Nothing here consults a verdict, a target or an arm, so these columns are
    usable as independent variables without the circularity Round 2 found.
    """
    from dci.verifiers.rules import normalize_text, split_sentences, word_tokens
    if not text or not text.strip():
        return {}
    body = str(text)
    clean = normalize_text(body)
    sentences = split_sentences(body)
    return {
        "n_sentences": len(sentences),
        "n_sentences_legacy": len(legacy_split_sentences(body)),
        "n_periods": clean.count("."),
        "n_terminals": len(_TERMINAL.findall(clean)),
        "n_semicolons": clean.count(";"),
        "n_colons": clean.count(":"),
        "n_dashes": sum(clean.count(d) for d in _DASHES),
        "n_commas": clean.count(","),
        "n_newlines": body.count("\n"),
        "n_paragraphs": _blank_line_blocks(body),
        "n_words": len(word_tokens(body)),
        "ends_every_sentence_with_terminal": bool(sentences) and all(
            s.rstrip('"\'”’)]').endswith((".", "!", "?")) for s in sentences),
    }


def _target_n(config: dict[str, Any]) -> Optional[int]:
    """The count the measured constraint demands, read from the run's own config.

    Returns None for a target that is not a count, in which case the
    count-shaped columns are simply absent rather than silently wrong.
    """
    manifest = (config.get("extensions_manifest") or {}).get("constraints", {})
    target = config["selection"]["target"]
    if target in manifest:
        params = manifest[target].get("params") or {}
        return int(params["n"]) if "n" in params else None
    return int(config["harvest_provenance"]["exact_sentence_count"]) if target == "A" \
        else None


def _unit_column(config: dict[str, Any]) -> str:
    """Sentences or paragraphs — whichever unit this run's target counts."""
    manifest = (config.get("extensions_manifest") or {}).get("constraints", {})
    target = config["selection"]["target"]
    family = manifest.get(target, {}).get("rule_family", "exact_sentence_count")
    return "n_paragraphs" if family == "x_exact_paragraph_count" else "n_sentences"


# ------------------------------------------------------------------- loading
def load(run_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The run's generations with mechanism features and derived outcomes."""
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))

    features = pd.DataFrame([row_features(t) for t in frame["response"]],
                            index=frame.index)
    frame = pd.concat([frame, features], axis=1)
    if "scaffold" not in frame:
        frame["scaffold"] = ""
    frame["scaffold"] = frame["scaffold"].fillna("")

    n_target = _target_n(config)
    unit = _unit_column(config)
    frame.attrs["n_target"] = n_target
    frame.attrs["unit"] = unit
    frame.attrs["config"] = config

    if n_target is not None:
        observed = frame[unit]
        frame["undershoot"] = (observed < n_target).where(observed.notna())
        frame["overshoot"] = (observed > n_target).where(observed.notna())
        # SEVERE collapse is one unit — the substitution endpoint, where every
        # boundary has been replaced. A threshold of "at most two" was used in
        # earlier rounds at N = 4; it does not transfer to N = 3 or N = 6, and a
        # threshold that moves with the target would not be one variable.
        frame["severe_collapse"] = (observed == 1).where(observed.notna())
        # Failure that is NOT the collapse route, so the two can be compared
        # without one containing the other by construction.
        frame["noncollapse_failure"] = (
            (frame["a_failure"] == 1) & (observed > 1)).where(frame["a_failure"].notna())
        legacy = frame["n_sentences_legacy"]
        frame["a_failure_legacy"] = (legacy != n_target).where(
            legacy.notna() & frame["scorable"]).astype("float")
    return frame, config


# --------------------------------------------------------------- cell tables
_MEANS = ("n_sentences", "n_sentences_legacy", "n_paragraphs", "n_periods",
          "n_terminals", "n_semicolons", "n_colons", "n_dashes", "n_commas",
          "n_newlines", "n_words")


def cell_table(frame: pd.DataFrame, by: Iterable[str] = ("scaffold", "order", "arm")
               ) -> pd.DataFrame:
    """One row per experimental cell, contrast rows only."""
    by = list(by)
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    unit = frame.attrs.get("unit", "n_sentences")
    rows = []
    for key, group in contrast.groupby(by, dropna=False):
        scorable = group[group["scorable"]]
        arm_scorable = group[group.get("arm_scorable", pd.Series(False, group.index))]
        record = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        record.update({
            "n": len(group),
            "n_scorable": len(scorable),
            "n_technical": int(group["technical_failure"].sum()),
            "a_failure": _rate(scorable["a_failure"]),
            "a_failure_legacy": _rate(group.get("a_failure_legacy")),
            "severe_collapse": _rate(group.get("severe_collapse")),
            "undershoot": _rate(group.get("undershoot")),
            "overshoot": _rate(group.get("overshoot")),
            "noncollapse_failure": _rate(group.get("noncollapse_failure")),
            # Does the model KEEP the added instruction while dropping the
            # target? That is what "traded A away" means, and without it a row
            # that failed both is indistinguishable from a substitution.
            "arm_compliance": _rate(arm_scorable.get("arm_binary_pass")),
            "truncated": _rate(group["output_truncated"]),
        })
        record.update({f"mean_{c}": float(group[c].mean())
                       for c in _MEANS if c in group})
        record[f"mean_units"] = float(group[unit].mean()) if unit in group else np.nan
        rows.append(record)
    return pd.DataFrame(rows).sort_values(by).reset_index(drop=True)


def _rate(series) -> float:
    if series is None or len(series) == 0:
        return float("nan")
    values = pd.Series(series).dropna()
    return float(values.astype(float).mean()) if len(values) else float("nan")


def unit_distribution(frame: pd.DataFrame,
                      by: Iterable[str] = ("scaffold", "order", "arm")) -> pd.DataFrame:
    """The full count distribution per cell — the shape a mean would hide."""
    by = list(by)
    unit = frame.attrs.get("unit", "n_sentences")
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    table = (contrast.groupby(by + [unit]).size().rename("n").reset_index()
             .pivot_table(index=by, columns=unit, values="n", fill_value=0))
    return table.div(table.sum(axis=1), axis=0)


# -------------------------------------------------------------- contrasts
def _cluster_boot(values: np.ndarray, clusters: np.ndarray, n_boot: int = 10000,
                  alpha: float = 0.05, seed: int = 20260811) -> tuple[float, float]:
    """Percentile CI resampling whole TASKS, which are the independent unit."""
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    unique = np.unique(clusters)
    if len(unique) < 2:
        return float("nan"), float("nan")
    by_cluster = {c: values[clusters == c] for c in unique}
    draws = np.empty(n_boot)
    for i in range(n_boot):
        picked = rng.choice(unique, size=len(unique), replace=True)
        draws[i] = np.concatenate([by_cluster[c] for c in picked]).mean()
    return float(np.percentile(draws, 100 * alpha / 2)), \
        float(np.percentile(draws, 100 * (1 - alpha / 2)))


def paired_excess(frame: pd.DataFrame, control: str,
                  outcome: str = "a_failure",
                  by: Iterable[str] = ("scaffold", "order"),
                  n_boot: int = 10000) -> pd.DataFrame:
    """Each arm minus the control, paired on `pair_key`, within each cell.

    The control absorbs whatever the cell does to every arm — a scaffold that
    helps compliance in general, a task set that is unusually easy — so the
    residual is what is specific to the arm. Rows are dropped in pairs when
    either side is unscorable, and the drop is counted rather than hidden.
    """
    by = list(by)
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    out = []
    for key, group in contrast.groupby(by, dropna=False):
        cell = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        ctrl = group[group["arm"] == control].set_index("pair_key")
        if ctrl.empty:
            continue
        for arm, arm_rows in group.groupby("arm"):
            if arm == control:
                continue
            merged = arm_rows.set_index("pair_key").join(
                ctrl[[outcome, "task_id"]], rsuffix="_control", how="inner")
            usable = merged[merged[outcome].notna()
                            & merged[f"{outcome}_control"].notna()]
            diff = (usable[outcome].astype(float)
                    - usable[f"{outcome}_control"].astype(float)).to_numpy()
            low, high = _cluster_boot(diff, usable["task_id"].to_numpy(), n_boot)
            out.append({**cell, "arm": arm, "control": control, "outcome": outcome,
                        "n_pairs": len(usable), "n_dropped": len(merged) - len(usable),
                        "excess": float(diff.mean()) if len(diff) else float("nan"),
                        "ci_low": low, "ci_high": high})
    return pd.DataFrame(out)


def paired_delta(frame: pd.DataFrame, factor: str, baseline: Any,
                 outcome: str = "a_failure",
                 by: Iterable[str] = ("order", "arm"),
                 n_boot: int = 10000) -> pd.DataFrame:
    """Change in an outcome when `factor` moves off `baseline`, paired per unit.

    The pairing key drops `factor` from `pair_key`, so a scaffolded row is
    compared with the *same task, order and replicate* run without the scaffold
    rather than with the cell average.
    """
    by = list(by)
    contrast = frame[frame["condition"].isin(["focal", "reference"])].copy()
    contrast["_key"] = (contrast["task_id"] + "|" + contrast["order"] + "|r"
                        + contrast["replicate"].astype(str) + "|" + contrast["arm"])
    out = []
    base = contrast[contrast[factor] == baseline].set_index("_key")
    for key, group in contrast[contrast[factor] != baseline].groupby(by + [factor],
                                                                    dropna=False):
        cell = dict(zip(by + [factor], key if isinstance(key, tuple) else (key,)))
        merged = group.set_index("_key").join(
            base[[outcome, "task_id"]], rsuffix="_base", how="inner")
        usable = merged[merged[outcome].notna() & merged[f"{outcome}_base"].notna()]
        diff = (usable[outcome].astype(float)
                - usable[f"{outcome}_base"].astype(float)).to_numpy()
        low, high = _cluster_boot(diff, usable["task_id"].to_numpy(), n_boot)
        out.append({**cell, "baseline": baseline, "outcome": outcome,
                    "n_pairs": len(usable),
                    "delta": float(diff.mean()) if len(diff) else float("nan"),
                    "ci_low": low, "ci_high": high})
    return pd.DataFrame(out)


# -------------------------------------------------------- scaffold compliance
def scaffold_compliance(frame: pd.DataFrame) -> pd.DataFrame:
    """Was the scaffold literally obeyed, where obedience is checkable?

    The sham's row is deliberately blank: it asks for something no rule can
    score, which is what makes it a sham. Inventing a proxy for it would turn a
    control into a measurement.
    """
    from dci_exploratory.runner import SCAFFOLD_COMPLIANCE
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    rows = []
    for (scaffold, arm), group in contrast.groupby(["scaffold", "arm"], dropna=False):
        text = group["response"].fillna("")
        if scaffold == "one_sentence_per_line":
            obeyed = (group["n_newlines"] + 1 >= group["n_sentences"]).mean()
        elif scaffold == "weak_reminder":
            obeyed = group["ends_every_sentence_with_terminal"].mean()
        else:
            obeyed = float("nan")
        rows.append({"scaffold": scaffold, "arm": arm,
                     "definition": SCAFFOLD_COMPLIANCE.get(scaffold, "unknown"),
                     "literal_compliance": float(obeyed),
                     "mean_newlines": float(group["n_newlines"].mean()),
                     "mean_words": float(group["n_words"].mean())})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- report
def _fmt(frame: pd.DataFrame, floats: int = 3) -> str:
    return frame.to_string(index=False, float_format=lambda v: f"{v:.{floats}f}")


def report(run_dir: Path, control: str, n_boot: int = 10000,
           by: Iterable[str] = ("scaffold", "order", "arm")) -> str:
    frame, config = load(run_dir)
    unit = frame.attrs["unit"]
    lines = [f"# {Path(run_dir).name}", "", EXPLORATORY_NOTE, "",
             f"target={config['selection']['target']} "
             f"focal={config['selection']['focal']} "
             f"references={config['selection']['references']} "
             f"n_target={frame.attrs['n_target']} unit={unit}",
             f"design_path={config.get('design_path')} "
             f"split={config.get('task_split')}+{config.get('task_offset', 0)} "
             f"wording={config.get('paraphrase_id')}",
             f"rows={len(frame)} technical_failures={int(frame['technical_failure'].sum())}",
             "", "## cells", _fmt(cell_table(frame, by)),
             "", f"## {unit} distribution", _fmt(unit_distribution(frame, by)),
             "", f"## paired excess over {control} (A-failure)",
             _fmt(paired_excess(frame, control, "a_failure",
                                by=[b for b in by if b != "arm"], n_boot=n_boot)),
             "", f"## paired excess over {control} (severe collapse)",
             _fmt(paired_excess(frame, control, "severe_collapse",
                                by=[b for b in by if b != "arm"], n_boot=n_boot))]
    lines += ["", "## collapse signature (severely collapsed rows only)",
              _fmt(collapse_signature(frame, [b for b in by if b != "scaffold"]
                                      if frame["scaffold"].nunique() == 1 else list(by)))]
    if frame["scaffold"].nunique() > 1:
        lines += ["", "## scaffold delta vs no scaffold (A-failure)",
                  _fmt(paired_delta(frame, "scaffold", "", "a_failure", n_boot=n_boot)),
                  "", "## scaffold delta vs no scaffold (severe collapse)",
                  _fmt(paired_delta(frame, "scaffold", "", "severe_collapse",
                                    n_boot=n_boot)),
                  "", "## scaffold literal compliance",
                  _fmt(scaffold_compliance(frame))]
    primitives = frame[frame["condition"] == "primitive"]
    if len(primitives):
        table = (primitives.groupby(["scaffold", "arm"])
                 .agg(n=("row_id", "size"),
                      failure=("a_failure", "mean"),
                      units=(unit, "mean")).reset_index())
        lines += ["", "## primitives (isolated, one instruction)", _fmt(table)]
    return "\n".join(lines)


def collapse_signature(frame: pd.DataFrame,
                       by: Iterable[str] = ("order", "arm")) -> pd.DataFrame:
    """What a collapsed answer LOOKS like, per arm — not merely that it collapsed.

    Two arms can both end at one sentence by different routes, and the
    replication criterion is about the route, not the count. The columns that
    separate them:

      `arm_compliance_when_collapsed` — did the model *satisfy the instruction it
          was given* while losing the target? That is what "traded the target
          away" means. An arm that collapses while also failing its own rule is
          not substituting; it is failing at both.
      `marks_per_lost_boundary` — boundary-capable marks (`;` `:` `—`) divided by
          the boundaries that went missing. Substitution predicts ≈1; a run-on
          predicts ≈0.
      `commas_per_lost_boundary` — the same for a mark that CANNOT stand at a
          boundary. A comma-chained run-on shows up here and nowhere else.
    """
    by = list(by)
    n_target = frame.attrs.get("n_target")
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    collapsed = contrast[contrast["severe_collapse"] == True]        # noqa: E712
    rows = []
    for key, group in collapsed.groupby(by, dropna=False):
        lost = max((n_target or 1) - 1, 1)
        boundary_marks = (group["n_semicolons"] + group["n_colons"]
                          + group["n_dashes"])
        scorable = group[group.get("arm_scorable", pd.Series(False, group.index))]
        rows.append({
            **dict(zip(by, key if isinstance(key, tuple) else (key,))),
            "n_collapsed": len(group),
            "arm_compliance_when_collapsed": _rate(scorable.get("arm_binary_pass")),
            "n_arm_unscorable": len(group) - len(scorable),
            "mean_boundary_marks": float(boundary_marks.mean()),
            "marks_per_lost_boundary": float(boundary_marks.mean() / lost),
            "commas_per_lost_boundary": float(group["n_commas"].mean() / lost),
            "mean_words": float(group["n_words"].mean()),
            "mean_periods": float(group["n_periods"].mean()),
        })
    return pd.DataFrame(rows)


def compare(runs: dict[str, Path], control: str, outcomes: Iterable[str] =
            ("a_failure", "severe_collapse"), n_boot: int = 10000) -> pd.DataFrame:
    """The same quantities across several runs, stacked for direct reading.

    A replication is a claim about two numbers being the same, and the way to
    make that claim checkable is to put them on one line rather than in two
    reports a reader has to hold in their head.
    """
    out = []
    for label, run_dir in runs.items():
        frame, config = load(run_dir)
        for outcome in outcomes:
            if outcome not in frame:
                continue
            table = paired_excess(frame, control, outcome, by=["order"], n_boot=n_boot)
            table.insert(0, "run", label)
            table["n_target"] = frame.attrs["n_target"]
            table["wording"] = config.get("paraphrase_id")
            table["split"] = config.get("task_split")
            out.append(table)
    return (pd.concat(out, ignore_index=True) if out else pd.DataFrame())


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--control", default="C_L3")
    parser.add_argument("--boot", type=int, default=10000)
    parser.add_argument("--by", default="scaffold,order,arm")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    text = report(args.run_dir, args.control, args.boot,
                  by=tuple(b for b in args.by.split(",") if b))
    print(text)
    out = args.out or (args.run_dir / "mechanism_report.md")
    out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
