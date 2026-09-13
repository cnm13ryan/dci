"""Read the matrix screen cache and report every §11 quantity it identifies.

The registered thresholds are applied for *reading*, never for claiming: §17.3
sets precision preconditions this screen cannot meet, so every verdict field
below is a description of where the interval sits, and `claim_licensed` is
False everywhere by construction.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.protocol import constants as C
from dci1v4.topics.split import split_topics

from matrix_screen_v4 import estimators as est

DCI1 = Path(__file__).resolve().parent.parent.parent
EVIDENCE = DCI1 / "evidence" / "matrix-screen-v4"

#: §15-style multiplicity families, in this screen's own vocabulary.
FAMILIES: dict[str, tuple[str, ...]] = {
    "primary": ("D_B_from_A", "D_A_from_B", "Lambda", "Delta_R"),
    "per_reference_swap": ("Delta_R1", "Delta_R2", "Delta_R3"),
    # The focal loss against each reference separately. Delta_j is the swap
    # D(B<-A) - D(B<-R_j); these are the D(B<-R_j) levels the swap is built
    # from, which the swap alone does not expose.
    "focal_losses": ("D_B_from_R1", "D_B_from_R2", "D_B_from_R3"),
    "reciprocal": ("D_Rbar_from_A", "D_Rbar_from_B",
                   "D_Rbar_from_Rbar_prime", "Xi"),
    "reference_losses": ("D_R1_from_A", "D_R2_from_A", "D_R3_from_A",
                         "D_R1_from_B", "D_R2_from_B", "D_R3_from_B"),
    "outcome_side": ("D_A_from_R1", "D_A_from_R2", "D_A_from_R3",
                     "Delta_A_side"),
}


def load_rows(model: str) -> list[dict[str, Any]]:
    hits = sorted(EVIDENCE.glob(f"{model}/screen-cap*/cache.jsonl"))
    if not hits:
        raise FileNotFoundError(f"no matrix-screen cache for {model}")
    return [json.loads(line) for line in hits[-1].open()]


#: The arms a fitted line may be built from. A is excluded wherever a line is
#: used to predict A, and so is the production-class companion.
FITTABLE_ARMS: tuple[str, ...] = ("matched", "spanning")


def fit_points(points: Sequence[Mapping[str, Any]]
               ) -> list[Mapping[str, Any]]:
    """The companions a line may be fitted on before it is used to predict A.

    Two exclusions, two reasons. **A is excluded** because fitting a line
    through the point it is then used to predict is circular, and the bias is
    not small when that point carries leverage -- A had most of the leverage on
    the length line, where it is the only companion that lengthens responses.
    **The production-class companion is excluded** because letting the line
    absorb the class effect would hide the very thing the class arm exists to
    expose.

    Both fits call this, so the invariant lives on the execution path rather
    than in two inline comprehensions that can drift apart.
    """
    return [p for p in points
            if p["arm"] in FITTABLE_ARMS and p["companion"] != "A"]


def _within_support(x: float, xs: Sequence[float]) -> dict[str, Any]:
    """Is A's predictor value inside the range the line was fitted over?

    A line fitted on companions whose x all sit on one side of A's x does not
    predict A -- it extrapolates to A. When that is true the residual is not
    identified from these points, however tight it looks, and saying so is the
    only honest reading.
    """
    lo, hi = min(xs), max(xs)
    inside = lo <= x <= hi
    return {"A_x": x, "fitted_x_range": [lo, hi], "inside": inside,
            "reading": ("A's residual is identified from these points"
                        if inside else
                        "A's x lies OUTSIDE the fitted range: the line "
                        "extrapolates to A and the residual is NOT identified "
                        "from this companion set")}


def read_delta_r(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Where the interval sits relative to the two registered thresholds.

    §11.6: Delta_R below 0.10 supports generic load; above 0.25 supports
    pair-specific. The reading is about the interval, not the point.
    """
    lo, hi = entry["ci95_percentile"]
    generic = C.DELTA_R_GENERIC_THRESHOLD
    pair = C.DELTA_R_PAIR_SPECIFIC_THRESHOLD
    if hi < generic:
        where = "entirely below the generic-load threshold"
    elif lo > pair:
        where = "entirely above the pair-specific threshold"
    elif lo > generic and hi < pair:
        where = "entirely between the two thresholds"
    else:
        where = "spans at least one threshold"
    return {"interval": [lo, hi], "generic_load_threshold": generic,
            "pair_specific_threshold": pair, "where_the_interval_sits": where,
            "claim_licensed": False,
            "why_not": ("§17.3 precision preconditions require a half-width of "
                        "0.05 for Delta_R on 384 blocks; this is a screen")}


def analyse(model: str, *, resamples: int = 10000, seed: int = 202608230
            ) -> dict[str, Any]:
    rows = load_rows(model)
    matrix_rows = [r for r in rows if r["arm"] in ("solo", "composed")]
    unconstrained = [r for r in rows if r["arm"] == "unconstrained"]
    blocks = sorted({r["topic_id"] for r in rows})
    roles = {r["role"] for row in rows for r in row["scores"]}
    spanning_roles = sorted(r for r in roles if r.startswith("S"))

    out: dict[str, Any] = {
        "model": model, "rows": len(rows), "blocks": len(blocks),
        "screen_protocol_hash": rows[0]["screen_protocol_hash"],
        "constraint_set": {r["role"]: [r["kind"], r["severity"]]
                           for row in rows for r in row["scores"]},
    }

    for scale in ("compliance", "vacuity_forced"):
        table = est.cell_table(matrix_rows, scale=scale)
        scale_out: dict[str, Any] = {}
        for order in (None,) + est.CONFIGURATIONS:
            label = order or "pooled_over_orders"
            try:
                contributions = est.per_block_contributions(
                    table, blocks, order=order)
            except KeyError as missing:
                scale_out[label] = {"unavailable": str(missing)}
                continue
            reduced = "_reduced_design" in contributions
            contributions.pop("_reduced_design", None)
            family_out: dict[str, Any] = {}
            for name, members in FAMILIES.items():
                present = [m for m in members if m in contributions]
                if not present:
                    continue
                family_out[name] = est.bootstrap(
                    {k: contributions[k] for k in present},
                    resamples=resamples, seed=seed, family=present)
            levels = {k: {"estimate": sum(v) / len(v)}
                      for k, v in contributions.items() if k.startswith("p_")}
            scale_out[label] = {"families": family_out, "levels": levels,
                                "design": ("§8.6 reduced" if reduced
                                           else "§8.1 full matrix")}
            if "primary" in family_out and "Delta_R" in family_out["primary"]:
                scale_out[label]["Delta_R_reading"] = read_delta_r(
                    family_out["primary"]["Delta_R"])
        out[scale] = scale_out

    # ---- the selection-clean subgroup
    #
    # The reference severities were selected on the 96 solo-calibration topics,
    # so a quantity estimated on those same topics carries the winner's curse of
    # that selection. The 24 pre-screen blocks are disjoint from the selection
    # sample. Every primary quantity is therefore reported on them alone as well
    # as on all blocks, which answers the objection with a number instead of an
    # argument -- and makes the pre-screen half of this screen self-sufficient.
    split = split_topics()
    prescreen_blocks = sorted({t["topic_id"] for t in split["prescreen"]}
                              & set(blocks))
    out["selection_clean_subgroup"] = {
        "blocks": len(prescreen_blocks),
        "why": ("the 24 pre-screen topics are disjoint from the 96 topics the "
                "calibration screen selected the reference severities on"),
    }
    if len(prescreen_blocks) >= 8:
        try:
            sub = est.per_block_contributions(table, prescreen_blocks,
                                              order=None)
            sub.pop("_reduced_design", None)
            wanted = [k for k in ("D_B_from_A", "D_A_from_B", "Lambda",
                                  "Delta_R", "Xi") if k in sub]
            out["selection_clean_subgroup"]["estimates"] = est.bootstrap(
                {k: sub[k] for k in wanted}, resamples=resamples, seed=seed + 5)
        except KeyError as missing:
            out["selection_clean_subgroup"]["unavailable"] = str(missing)

    # ---- order contrast, paired within block (§8.4 makes order within-block)
    table = est.cell_table(matrix_rows, scale="compliance")
    try:
        first = est.per_block_contributions(table, blocks,
                                            order="registered_first")
        second = est.per_block_contributions(table, blocks,
                                             order="registered_second")
        contrast = {k: [a - b for a, b in zip(first[k], second[k])]
                    for k in ("D_B_from_A", "D_A_from_B", "Delta_R", "Xi")
                    if k in first and k in second}
        out["order_contrast_registered_first_minus_second"] = est.bootstrap(
            contrast, resamples=resamples, seed=seed + 1)
    except KeyError as missing:
        out["order_contrast_registered_first_minus_second"] = {"unavailable": str(missing)}

    # ---- rho: the §16.1 correlation check C12 records as BLOCKED
    try:
        pooled = est.per_block_contributions(table, blocks, order=None)
        rho: dict[str, Any] = {}
        for j in est.REFERENCE_ROLES:
            x, y = pooled["p_B_with_A"], pooled[f"p_B_with_{j}"]
            rho[f"corr(p_B|A+B, p_B|B+{j})"] = est.bootstrap_statistic(
                lambda idx, x=x, y=y: est.correlation([x[i] for i in idx],
                                                      [y[i] for i in idx]),
                len(blocks), resamples=resamples, seed=seed + 2)
        values = [v["estimate"] for v in rho.values()
                  if not math.isnan(v["estimate"])]
        rho["mean"] = sum(values) / len(values) if values else float("nan")
        rho["what_it_settles"] = (
            "check C12's a_versus_reference_correlation, recorded BLOCKED: two "
            "composed cells with the same outcome constraint on the same "
            "blocks. Screen scale, screen topics, provisional reference set; "
            "Gate 4 supplies the registered value on the composed-validation "
            "topics before the freeze needs it.")
        out["rho_a_versus_reference"] = rho
    except KeyError as missing:
        out["rho_a_versus_reference"] = {"unavailable": str(missing)}

    # ---- V5: the companion-difficulty relationship
    # The V5 table needs the matched companions from the §8.1 matrix as well as
    # the spanning arm, so it reads every row rather than the spanning arm alone.
    span_table = est.cell_table(rows, scale="compliance")
    points: list[dict[str, Any]] = []
    try:
        for role in ("A",) + est.REFERENCE_ROLES:
            solo = span_table[(role, "solo", role)]
            comp = span_table[(est.pair_key("B", role), "B_first", "B")]
            b_solo = span_table[("B", "solo", "B")]
            points.append({
                "companion": role,
                "companion_solo_compliance": sum(solo.values()) / len(solo),
                "D_B_from_companion": sum(b_solo[b] - comp[b] for b in blocks)
                                      / len(blocks),
                "arm": "matched"})
        for role in sorted(r for r in roles if r.startswith("C")):
            solo = span_table[(role, "solo", role)]
            comp = span_table[(est.pair_key("B", role), "B_first", "B")]
            b_solo = span_table[("B", "solo", "B")]
            points.append({
                "companion": role,
                "companion_solo_compliance": sum(solo.values()) / len(solo),
                "D_B_from_companion": sum(b_solo[b] - comp[b] for b in blocks)
                                      / len(blocks),
                "arm": "class_matched_production"})
        span = est.spanning_contributions(span_table, blocks, spanning_roles)
        for role in spanning_roles:
            points.append({
                "companion": role,
                "companion_solo_compliance":
                    sum(span[f"p_{role}_solo"]) / len(blocks),
                "D_B_from_companion":
                    sum(span[f"D_B_from_{role}"]) / len(blocks),
                "arm": "spanning"})
        # Fitted on budget companions only, with A excluded: see fit_points.
        reference_points = fit_points(points)
        line = est.weighted_least_squares(
            [p["companion_solo_compliance"] for p in reference_points],
            [p["D_B_from_companion"] for p in reference_points])
        a_point = next(p for p in points if p["companion"] == "A")
        predicted = (line["intercept"]
                     + line["slope"] * a_point["companion_solo_compliance"])
        class_points = [p for p in points
                        if p["arm"] == "class_matched_production"]
        out["companion_difficulty_v5"] = {
            "points": points,
            "line_fitted_on_budget_companions_excluding_A": line,
            "A_within_support_of_fit": _within_support(
                a_point["companion_solo_compliance"],
                [p["companion_solo_compliance"] for p in reference_points]),
            "class_matched_residuals": [
                {"companion": p["companion"],
                 "observed": p["D_B_from_companion"],
                 "predicted_by_difficulty_alone":
                     line["intercept"]
                     + line["slope"] * p["companion_solo_compliance"],
                 "residual": p["D_B_from_companion"]
                             - (line["intercept"] + line["slope"]
                                * p["companion_solo_compliance"])}
                for p in class_points],
            "A_observed": a_point["D_B_from_companion"],
            "A_predicted_by_difficulty_alone": predicted,
            "A_residual": a_point["D_B_from_companion"] - predicted,
            "reading": (
                "the residual is what a difficulty account does not explain. "
                "It is a point estimate on a line through a handful of "
                "companions at screen scale, and it is decision V5's evidence, "
                "not its answer."),
        }
    except KeyError as missing:
        out["companion_difficulty_v5"] = {"unavailable": str(missing)}

    # ---- §25 accidental compliance
    if unconstrained:
        by_role: dict[str, list[float]] = defaultdict(list)
        for row in unconstrained:
            for score in row["scores"]:
                by_role[score["role"]].append(1.0 if score["passed"] else 0.0)
        out["accidental_compliance"] = {
            "rows": len(unconstrained),
            "by_constraint": {role: sum(v) / len(v)
                              for role, v in sorted(by_role.items())},
            "reading": ("the rate at which an answer to the same question, "
                        "carrying no constraint at all, satisfies each "
                        "constraint by chance. A compliance figure cannot be "
                        "read as delivery without it."),
        }
    else:
        out["accidental_compliance"] = {"unavailable": "no unconstrained cell"}

    # ---- the class-matched companion (production vs budget)
    class_roles = sorted(r for r in roles if r.startswith("C"))
    if class_roles:
        role = class_roles[0]
        try:
            contributions = est.class_control_contributions(
                est.cell_table(rows, scale="compliance"), blocks, role)
            out["class_control"] = {
                "companion_role": role,
                "companion": out["constraint_set"].get(role),
                "estimates": est.bootstrap(contributions, resamples=resamples,
                                           seed=seed + 4),
                "reading": (
                    "Delta_class holds the companion's structural class fixed "
                    "and swaps only its identity. A large Delta_R with a small "
                    "Delta_class says the excess belongs to the class -- a "
                    "production companion damaging a budget outcome -- and not "
                    "to A."),
            }
        except KeyError as missing:
            out["class_control"] = {"unavailable": str(missing)}
    else:
        # A lower-bound family may have been taken as a REFERENCE rather than
        # reserved for the class arm, which happens when reserving it would
        # cost the model its third reference. Where that is so, the class
        # contrast is still available -- it is that reference's own Delta_j,
        # which is D(B<-A) - D(B<-CL) by definition.
        constraints = out.get("constraint_set", {})
        lower = [role for role, spec in constraints.items()
                 if role in est.REFERENCE_ROLES
                 and str(spec[0]).startswith("CL")]
        if lower:
            role = lower[0]
            fam = out["compliance"]["pooled_over_orders"]["families"]
            entry = fam.get("per_reference_swap", {}).get(f"Delta_{role}")
            out["class_control"] = {
                "companion_role": role,
                "companion": constraints.get(role),
                "delta_class_is_delta_j": entry,
                "reading": (
                    f"the lower-bound family sits in the {role} slot rather "
                    f"than in a dedicated class arm, because reserving it "
                    f"would have cost this model its third reference. "
                    f"Delta_{role} = D(B<-A) - D(B<-{role}) IS the class "
                    f"contrast; what is lost is D(A<-CL) and the two "
                    f"reciprocal directions the dedicated arm would add, and "
                    f"Delta_R for this model averages over one production and "
                    f"two budget companions rather than three budgets."),
            }
        else:
            out["class_control"] = {
                "unavailable": ("no lower-bound family cleared §13.2 for this "
                                "model, so the production-versus-budget "
                                "contrast is not estimable here")}

    # ---- the length channel, as an ACROSS-COMPANION description
    #
    # §22 forbids conditioning the primary estimand on response length, and
    # §13.3 gives the reason: composition shortens answers and shorter answers
    # satisfy length-style constraints more readily, so length is on the causal
    # path from companion to outcome. Conditioning within response would be a
    # collider. Regressing D(B<-g) on how much g shortens the answer, ACROSS
    # companions, conditions on nothing: it asks whether A's delivery loss is
    # what its length effect alone would predict, in the same shape as the V5
    # difficulty question. It is descriptive and it is not a mediation estimate.
    try:
        b_solo_words = [row["word_count"] for row in rows
                        if row["cell_key"] == "B" and row["arm"] == "solo"]
        median_b_solo = sorted(b_solo_words)[len(b_solo_words) // 2]
        length_points = []
        for point in out.get("companion_difficulty_v5", {}).get("points", []):
            role = point["companion"]
            cell = est.pair_key("B", role)
            companion_words = [row["word_count"] for row in rows
                               if row["cell_key"] == cell
                               and row["order_label"] == "B_first"]
            if not companion_words:
                continue
            median = sorted(companion_words)[len(companion_words) // 2]
            length_points.append({
                "companion": role, "arm": point["arm"],
                "median_words_B_solo": median_b_solo,
                "median_words_B_with_companion": median,
                "length_shift": median - median_b_solo,
                "D_B_from_companion": point["D_B_from_companion"]})
        others = fit_points(length_points)
        line = est.weighted_least_squares(
            [p["length_shift"] for p in others],
            [p["D_B_from_companion"] for p in others])
        a_point = next(p for p in length_points if p["companion"] == "A")
        predicted = line["intercept"] + line["slope"] * a_point["length_shift"]
        out["length_channel"] = {
            "points": length_points,
            "line_fitted_on_budget_companions_excluding_A": line,
            "A_within_support_of_fit": _within_support(
                a_point["length_shift"],
                [p["length_shift"] for p in others]),
            "A_observed": a_point["D_B_from_companion"],
            "A_predicted_by_length_shift_alone": predicted,
            "A_residual": a_point["D_B_from_companion"] - predicted,
            "reading": ("what A's delivery loss would be if only its effect on "
                        "response length mattered, and how far the observed "
                        "loss sits from that. Across companions, not within "
                        "response: nothing is conditioned on and §22 is not "
                        "violated. Descriptive, at screen scale, on a handful "
                        "of companions."),
        }
    except (KeyError, StopIteration, IndexError, ZeroDivisionError) as error:
        out["length_channel"] = {"unavailable": repr(error)}

    # ---- length and vacuity, reported never conditioned on (§13.3, §22)
    vacuity = est.cell_table(rows, scale="vacuity")
    # Word count is a property of the response, not of a constraint, so it is
    # collapsed to one entry per (cell, order) rather than one per scored role.
    words_by_cell: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        words_by_cell[f"{row['cell_key']}|{row['order_label']}"].append(
            float(row["word_count"]))
    out["mediators"] = {
        "median_words_by_cell": {
            key: sorted(v)[len(v) // 2] for key, v in sorted(words_by_cell.items())},
        "mean_words_by_cell": {
            key: sum(v) / len(v) for key, v in sorted(words_by_cell.items())},
        "vacuity_rate_by_cell_and_outcome": {
            f"{key}|{order}|{role}": sum(v.values()) / len(v)
            for (key, order, role), v in sorted(vacuity.items())},
        "note": ("§13.3 registers composed response length as a mediator and "
                 "§22 forbids conditioning the primary estimand on it. The "
                 "vacuity-forced scale above is the registered §17.4 "
                 "recomputation, which is a bound and not a length control."),
    }
    return out


__all__ = ["FAMILIES", "load_rows", "analyse", "read_delta_r"]
