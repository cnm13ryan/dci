#!/usr/bin/env python3
"""Is the planned LOCAL confirmatory allocation precise enough for Δ_R(f)?

For every `LOCAL_SUPPORTED` (model, frame) this projects SE[Δ_R(f)], the
simultaneous 95 % half-width and the ~80 %-power MDE at the **actual**
confirmatory allocation, through the **registered** variance model.

**The estimator is the registered one.** §16.1 lives in
`dci1v4.analysis.variance` and is imported, not restated:

    Var(Delta_R) = ( 2 (1 - rho) sigma2_topic
                     + sigma2_draw (1/M + 1/(3M)) ) / blocks

with `sigma2_topic = phi p(1-p)` and `sigma2_draw = (1 - phi) p(1-p)`. The
design is paired and clustered --- one topic per block, every cell of a block
on the same topic, draws nested inside a cell --- and this form is what
encodes that: `rho` is the within-block correlation between two cells and the
draw term carries `1/M + 1/(3M)`, the 4/3 that averaging three references
against one A leaves behind. No independent-proportions formula appears
anywhere in this file.

**The allocation is read, not assumed.** §8.4 renders a block under one
frame, so one pass over the registered `C.N_BLOCKS` blocks leaves a frame
`N_BLOCKS / N_WORDINGS` of them. `rules.CONFIRMATORY_FRAME_OFFSETS` names the
passes the confirmatory design runs and `rules.CONFIRMATORY_BLOCKS_PER_FRAME`
is what a frame therefore holds; Gate 3's own coverage projection runs on the
same number. Draws are `C.M_DRAWS`. This file states the precision *of the
allocation in force*: run it again after an allocation amendment and every
number moves with it.

**The variance depends on composed-cell compliance, which does not exist
pre-freeze**, so the answer is a range and every scenario says where its
numbers came from:

* `REGISTERED_PLANNING` --- phi 0.27, p(1-p) 0.215, rho 0.5: the constants
  §16.2's table is quoted at and the 384-block allocation was chosen at.
* `REGISTERED_ALTERNATE` --- phi 0.37, the sensitivity value §16.3 carries.
* `WORST_CASE` --- p(1-p) = 0.25 (a composed cell at 0.5, the variance
  maximum), phi at the alternate, rho = 0. Var falls as rho rises, so rho = 0
  is the conservative end; nothing in the design can exceed this row.
* `CALIBRATION_ANCHORED` --- phi and rho estimated from **this frame's own
  solo cells** by the production `realised_decomposition` and
  `realised_correlation` (§23 / check C12), and p(1-p) at B's solo compliance
  at m*(f). Solo cells are not composed cells: this is the nearest pre-freeze
  analogue of the topic/draw split, labelled as one, and it is the only row
  that uses run data.
* `REHEARSAL_ANCHORED` --- the block-bootstrap SE of one companion's D
  measured on the completed v7 development rehearsal at 384 blocks x 8 draws
  (`dci1v8dev.spectrum.precision.MEASURED`, the constant Gate 3's coverage
  projection already runs on), rescaled to the frame's blocks and combined
  under the same registered form. Composed cells of a *v7* rehearsal, already
  a design constant; no v8 composed cell exists or is read.

**Nothing here is a gate.** §17.3 evaluates the precision precondition on the
realised confirmatory interval and `INSUFFICIENT_PRECISION` is its registered,
non-terminal consequence (preregistration v7 §18). This is a projection, and
it is labelled `PROJECTION_NOT_REGISTERED_FOR_INFERENCE` exactly as the probe's
is. It answers a design question --- is the allocation worth running --- and
decides nothing.

    python3 tools/v8_local_precision.py --roots dci1v8-pilot-r8 dci1v8-pilot-r9

Reads `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` only. Writes
`reports/dci1v8dev/local_precision.{md,json}`.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys
from statistics import NormalDist
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.analysis.variance import (realised_correlation,               # noqa: E402
                                      realised_decomposition, variances)
from dci1v7.analysis.bootstrap import sidak_critical                      # noqa: E402
from dci1v7.protocol import constants as C                                # noqa: E402
from dci1v8dev import rules as R                                          # noqa: E402
from dci1v8dev.run import eligibility as EL                               # noqa: E402
from dci1v8dev.run import stages as S                                     # noqa: E402
from dci1v8dev.spectrum.precision import MEASURED                         # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
EVIDENCE = HERE.parent / "evidence"

#: Delta_R's registered precision precondition (§16.2), evaluated on the
#: *simultaneous* half-width --- `claims.Interval.meets_precondition` reads
#: the decision interval, and `analysis_run` builds it from the bootstrap's
#: simultaneous bounds.
PRECONDITION = C.PRECISION_PRECONDITIONS["Delta_R"]
#: Delta_R sits in §15's F1, which has six members, so the simultaneous
#: interval is taken at the six-member critical value. The bootstrap's
#: studentised maximum-modulus value is <= Sidak, so Sidak is the
#: conservative planning constant --- the one §16.2's table is quoted at.
FAMILY = C.PRIMARY_FAMILY
FAMILY_SIZE = len(C.FAMILY_MEMBERS[FAMILY])
POWER = 0.80
ALPHA = 0.05
LABEL = "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"


def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dirs(root: pathlib.Path) -> list[pathlib.Path]:
    base = root / "evidence" / "dci1v8"
    if not base.is_dir():
        base = root / "dci1v8"
    return sorted(d for d in base.iterdir()
                  if d.is_dir() and d.name not in ("keys", "registration"))


# ------------------------------------------------------------------ scenarios

def project(*, blocks: int, m: int, phi: float, rho: float,
            p_one_minus_p: float) -> dict[str, Any]:
    """SE, half-widths and the MDE for Delta_R at one variance setting.

    `variances` is §16.1 verbatim (`dci1v4.analysis.variance`); everything
    below it is the standard reading of that variance.
    """
    var = variances(blocks, m, phi=phi, rho=rho,
                    p_one_minus_p=p_one_minus_p)
    se = math.sqrt(var["Delta_R"])
    critical = sidak_critical(FAMILY_SIZE)
    z_power = NormalDist().inv_cdf(POWER)
    return {
        "phi": phi, "rho": rho, "p_one_minus_p": p_one_minus_p,
        "sigma2_topic": var["sigma2_topic"], "sigma2_draw": var["sigma2_draw"],
        "n_blocks": blocks, "m_draws": m,
        "se_delta_r": se,
        "half_width_95_marginal": NormalDist().inv_cdf(1 - ALPHA / 2) * se,
        "half_width_simultaneous": critical * se,
        "simultaneous_critical_value": critical,
        "family": FAMILY, "family_size": FAMILY_SIZE,
        "mde_80": (critical + z_power) * se,
        "meets_precondition": critical * se <= PRECONDITION,
        "precondition": PRECONDITION,
    }


def _within_cell_variance(vectors: Sequence[Sequence[float]], m: int) -> float:
    """sigma2_draw from per-topic cell means, bias-corrected by M/(M-1).

    For a topic met M times, E[x(1-x)] = pi(1-pi)(M-1)/M, so the correction
    is the one preregistration v7 §18 states for the probe's projection.
    """
    per_cell = [statistics.fmean([x * (1.0 - x) for x in v]) * m / (m - 1)
                for v in vectors if len(v) > 1]
    return statistics.fmean(per_cell) if per_cell else 0.0


def anchored_setting(gate2_frame: Mapping[str, Any],
                     survival: Mapping[str, Any]) -> dict[str, Any] | None:
    """phi and rho from this frame's own **solo** cells; p(1-p) at B's m*(f).

    The cells are A at n*(f) and the frame's three core references at their
    selected severities --- the rungs the LOCAL arm would actually compose.
    Their per-topic vectors are solo, so this estimates the instrument's
    topic/draw split and its within-block correlation, not the composed
    cells' own. Stated as an analogue and labelled as one.
    """
    rows = {f"{r['kind']}:{r['severity']}": r
            for r in gate2_frame["calibration_rows"]["pooled"]}
    wanted = [f"{c['family']}:{c['severity']}" for c in survival["core_references"]]
    vectors: dict[str, list[float]] = {}
    for label in wanted:
        row = rows.get(label)
        if row and row.get("per_topic_solo"):
            vectors[label] = [float(x) for x in row["per_topic_solo"]]
    a_topic = (gate2_frame.get("a_per_topic_by_split") or {}).get("per_topic")
    if isinstance(a_topic, Mapping):
        merged: list[float] = []
        for split in sorted(a_topic):
            merged.extend(float(x) for x in a_topic[split])
        if merged:
            vectors["A"] = merged
    lengths = {len(v) for v in vectors.values()}
    if len(vectors) < 2 or len(lengths) != 1:
        return None
    m_cal = C.M_CAL
    decomposition = realised_decomposition(
        vectors, _within_cell_variance(list(vectors.values()), m_cal), m_cal)
    labels = sorted(vectors)
    pairs = [(vectors[a], vectors[b])
             for i, a in enumerate(labels) for b in labels[i + 1:]]
    correlation = realised_correlation(pairs, decomposition["sigma2_topic"])
    p_b = float(gate2_frame["solo_compliance_b"])
    rho = correlation["rho_clipped"]
    return {
        "phi": decomposition["phi"],
        "rho": max(0.0, rho) if rho is not None else 0.0,
        "p_one_minus_p": p_b * (1.0 - p_b),
        "cells": labels, "n_topics": lengths.pop(),
        "sigma2_topic_solo": decomposition["sigma2_topic"],
        "sigma2_draw_solo": decomposition["sigma2_draw"],
        "rho_raw": rho, "solo_compliance_b": p_b,
        "basis": "solo cells of this frame (A at n*(f) and the three core "
                 "references at their selected severities); p(1-p) at B's "
                 "solo compliance at m*(f). An analogue of the composed "
                 "cells, not a measurement of them.",
    }


def rehearsal_setting(blocks: int, *, se_point: float, block_corr: float
                      ) -> dict[str, Any]:
    """SE[Delta_R] from the measured per-companion SE of D and its measured
    between-companion block correlation.

    Delta_R = D(B<-A) - mean_j D(B<-R_j) has weights (1, -1/3, -1/3, -1/3)
    summing to zero, so under equicorrelation the shared component cancels
    exactly and Var = sigma_D^2 (1 - rho_D) sum w^2 with sum w^2 = 4/3.
    """
    sigma_d = se_point * math.sqrt(C.N_BLOCKS / blocks)
    sum_w2 = 1.0 + 3.0 * (1.0 / 3.0) ** 2
    se = sigma_d * math.sqrt((1.0 - block_corr) * sum_w2)
    critical = sidak_critical(FAMILY_SIZE)
    z_power = NormalDist().inv_cdf(POWER)
    return {"se_point_at_384": se_point, "block_corr": block_corr,
            "se_d_at_n_blocks": sigma_d, "sum_w_squared": sum_w2,
            "n_blocks": blocks, "se_delta_r": se,
            "half_width_95_marginal": NormalDist().inv_cdf(1 - ALPHA / 2) * se,
            "half_width_simultaneous": critical * se,
            "mde_80": (critical + z_power) * se,
            "meets_precondition": critical * se <= PRECONDITION,
            "precondition": PRECONDITION,
            "source": MEASURED["source"]}


def frame_precision(gate2_frame: Mapping[str, Any],
                    survival: Mapping[str, Any]) -> dict[str, Any]:
    blocks = R.CONFIRMATORY_BLOCKS_PER_FRAME
    m = C.M_DRAWS
    out: dict[str, Any] = {
        "n_blocks_per_frame": blocks,
        "n_blocks_registered_total": C.N_BLOCKS,
        "m_draws": m,
        "n_references": C.N_CORE_REFERENCES,
        # One composed cell per (companion, configuration) per block. Delta_R
        # reads four of them --- B+A and B+R_1..3 --- in one configuration.
        "observations_per_cell_per_frame": blocks * m,
        "cells_read_by_delta_r": 1 + C.N_CORE_REFERENCES,
        "observations_entering_delta_r_per_configuration":
            blocks * m * (1 + C.N_CORE_REFERENCES),
        "effective_independent_units": blocks,
        "units_note": "the block (one topic) is the independent unit: the "
                      "bootstrap resamples blocks and carries every cell mean "
                      "of a drawn block, so 8 draws inside a cell reduce the "
                      "draw component and never the topic component",
        "scenarios": {},
        "label": LABEL,
    }
    out["scenarios"]["REGISTERED_PLANNING"] = project(
        blocks=blocks, m=m, phi=C.PHI_PRIMARY, rho=C.RHO,
        p_one_minus_p=C.P_ONE_MINUS_P)
    out["scenarios"]["REGISTERED_ALTERNATE"] = project(
        blocks=blocks, m=m, phi=C.PHI_ALTERNATE, rho=C.RHO,
        p_one_minus_p=C.P_ONE_MINUS_P)
    out["scenarios"]["WORST_CASE"] = project(
        blocks=blocks, m=m, phi=C.PHI_ALTERNATE, rho=0.0, p_one_minus_p=0.25)
    anchored = anchored_setting(gate2_frame, survival)
    if anchored is not None:
        out["scenarios"]["CALIBRATION_ANCHORED"] = {
            **project(blocks=blocks, m=m, phi=anchored["phi"],
                      rho=anchored["rho"],
                      p_one_minus_p=anchored["p_one_minus_p"]),
            "anchor": anchored}
        # The anchored rho is the correlation between two *different
        # constraints'* solo cells, which is not what Var(Delta_R) reads: its
        # four cells all measure **B**, under different companions, on the
        # same topic, and share the topic effect far more. The measured
        # cross-constraint value is a floor, not an estimate, so this row
        # keeps the frame's own phi and p(1-p) and puts §16.1's rho back.
        out["scenarios"]["CALIBRATION_ANCHORED_REGISTERED_RHO"] = {
            **project(blocks=blocks, m=m, phi=anchored["phi"], rho=C.RHO,
                      p_one_minus_p=anchored["p_one_minus_p"]),
            "anchor": {**anchored, "rho": C.RHO,
                       "rho_note": "the frame's own phi and p(1-p) with "
                                   "§16.1's registered rho; the anchored rho "
                                   "measures cross-constraint solo cells and "
                                   "is a floor for the same-outcome composed "
                                   "cells Delta_R actually reads"}}
    out["scenarios"]["REHEARSAL_ANCHORED"] = rehearsal_setting(
        blocks, se_point=MEASURED["se_point"],
        block_corr=MEASURED["block_corr"])
    out["scenarios"]["REHEARSAL_ANCHORED_PESSIMISTIC"] = rehearsal_setting(
        blocks, se_point=MEASURED["se_point_range"][1],
        block_corr=MEASURED["block_corr_range"][0])
    out["scenarios"]["REHEARSAL_ANCHORED_OPTIMISTIC"] = rehearsal_setting(
        blocks, se_point=MEASURED["se_point_range"][0],
        block_corr=MEASURED["block_corr_range"][1])
    ses = [s["se_delta_r"] for s in out["scenarios"].values()]
    hws = [s["half_width_simultaneous"] for s in out["scenarios"].values()]
    out["se_range"] = [min(ses), max(ses)]
    out["half_width_simultaneous_range"] = [min(hws), max(hws)]
    out["mde_range"] = [min(s["mde_80"] for s in out["scenarios"].values()),
                        max(s["mde_80"] for s in out["scenarios"].values())]
    out["meets_precondition_in_every_scenario"] = all(
        s["meets_precondition"] for s in out["scenarios"].values())
    out["meets_precondition_in_any_scenario"] = any(
        s["meets_precondition"] for s in out["scenarios"].values())
    out["required_allocation"] = required_allocation(out["scenarios"], blocks)
    return out


def required_allocation(scenarios: Mapping[str, Mapping[str, Any]],
                        blocks: int) -> dict[str, Any]:
    """What allocation each scenario would need, and whether topics exist.

    A block-bootstrap SE falls as 1/sqrt(blocks), so the blocks needed to
    bring the simultaneous half-width to Delta_R's registered precondition
    scale as (realised / target)^2. Two targets, both registered: §16.2's
    precondition (0.05) and an 80 %-power MDE at §11.9's smallest effect of
    interest (0.10). No invented threshold appears.

    Feasibility is the topic bank: §6.2 holds `N_CONFIRMATORY` = 384
    confirmatory topics and nothing else may be spent (the sequestered set is
    reserved). More blocks per frame than that means **passes** --- rendering
    the confirmatory topics again under a different frame offset, exactly as
    `rules.CALIBRATION_FRAME_OFFSETS` does at Gate 2 --- and `N_WORDINGS`
    passes is the ceiling, at which every frame holds every confirmatory
    topic once and a further pass would repeat a topic inside a frame.
    """
    ceiling_passes = C.N_WORDINGS
    rows = {}
    for name, sc in scenarios.items():
        hw, mde = sc["half_width_simultaneous"], sc["mde_80"]
        need_pre = math.ceil(blocks * (hw / PRECONDITION) ** 2)
        need_sesoi = math.ceil(blocks * (mde / C.SMALLEST_EFFECT_OF_INTEREST) ** 2)
        rows[name] = {
            "blocks_for_precondition": need_pre,
            "blocks_for_sesoi_mde": need_sesoi,
            # one pass gives N_CONFIRMATORY / N_WORDINGS blocks per frame
            "passes_for_precondition": math.ceil(
                need_pre * C.N_WORDINGS / C.N_CONFIRMATORY),
            "passes_for_sesoi_mde": math.ceil(
                need_sesoi * C.N_WORDINGS / C.N_CONFIRMATORY),
            "feasible_within_topic_bank":
                need_pre <= C.N_CONFIRMATORY,
        }
    worst = max(r["passes_for_precondition"] for r in rows.values())
    plausible = max(rows[n]["passes_for_precondition"] for n in rows
                    if n != "WORST_CASE")
    return {
        "by_scenario": rows,
        "blocks_per_frame_now": blocks,
        "confirmatory_topics_available": C.N_CONFIRMATORY,
        "blocks_per_frame_at_one_pass": C.N_CONFIRMATORY // C.N_WORDINGS,
        "max_passes": ceiling_passes,
        "blocks_per_frame_at_ceiling": C.N_CONFIRMATORY,
        "passes_needed_worst_case": worst,
        "passes_needed_excluding_worst_case": plausible,
        "reachable_within_topic_bank": plausible <= ceiling_passes,
        "reachable_worst_case": worst <= ceiling_passes,
        "targets": {"precondition": PRECONDITION,
                    "sesoi": C.SMALLEST_EFFECT_OF_INTEREST},
        "rule": "blocks scale as (realised half-width / target)^2; a pass "
                "renders the confirmatory topics under one frame offset, so "
                f"{C.N_WORDINGS} passes is the ceiling and gives every frame "
                f"all {C.N_CONFIRMATORY} confirmatory topics",
    }


def read_root(root: pathlib.Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for model_dir in _model_dirs(root):
        g3p = model_dir / "GATE_3_REFERENCES" / "gate3_references.json"
        g2p = model_dir / "GATE_2_CALIBRATION" / "gate2_calibration.json"
        if not (g3p.exists() and g2p.exists()):
            continue
        g3, g2 = _payload(g3p), _payload(g2p)
        el = EL.local_eligibility(g3["by_frame"], frames=S.FRAMES)
        frames = {}
        for w in el["local_supported_frames"]:
            frames[str(w)] = {
                "frame": w,
                "n_star": g2["by_frame"][str(w)]["n_star"],
                "m_star": g2["by_frame"][str(w)]["m_star"],
                "iota_a": g2["by_frame"][str(w)]["iota_a"],
                "core_references": g3["by_frame"][str(w)]["survival"]["core_references"],
                **frame_precision(g2["by_frame"][str(w)],
                                  g3["by_frame"][str(w)]["survival"])}
        out[model_dir.name] = {
            "model": model_dir.name, "root": root.name,
            "recorded_at": g3.get("recorded_at"),
            "eligibility": {k: el[k] for k in
                            ("local_supported_frames", "n_local_supported_frames",
                             "local_eligible", "local_eligibility_min_frames")},
            "by_frame": frames}
    return out


def _fmt(x: Any, spec: str = ".4f") -> str:
    return "—" if x is None else format(x, spec)


def render(latest: dict[str, Any]) -> str:
    blocks = R.CONFIRMATORY_BLOCKS_PER_FRAME
    frames = [(model, w, fr) for model, entry in sorted(latest.items())
              for w, fr in sorted(entry["by_frame"].items(),
                                  key=lambda kv: int(kv[0]))]
    # The two rows that are bounds rather than estimates: WORST_CASE fixes
    # p(1-p) at its maximum, and CALIBRATION_ANCHORED's rho is a floor.
    bounds = {"WORST_CASE", "CALIBRATION_ANCHORED"}
    _passes = [(name, r["required_allocation"]["by_scenario"][name]
                ["passes_for_precondition"])
               for _, _, r in frames
               for name in r["required_allocation"]["by_scenario"]]
    passes_plausible = max((v for name, v in _passes if name not in bounds),
                           default=0)
    passes_worst = max((v for _, v in _passes), default=0)
    per_cell = blocks * C.M_DRAWS
    entering = per_cell * (1 + C.N_CORE_REFERENCES)
    lines = [
        "# DCI-1 v8 — LOCAL confirmatory precision for Δ_R(f)",
        "",
        "Produced by `tools/v8_local_precision.py`. **Projection only**, "
        f"labelled `{LABEL}`: §17.3 evaluates the precision precondition on "
        "the realised confirmatory interval and `INSUFFICIENT_PRECISION` is "
        "its registered, non-terminal consequence. Nothing here gates "
        "anything and no composed cell was generated or read.",
        "",
        "## The allocation, read from the design",
        "",
        f"* `C.N_BLOCKS` = {C.N_BLOCKS} registered confirmatory blocks, one "
        f"topic each, wording assigned by frame (§8.4), over "
        f"`rules.CONFIRMATORY_FRAME_PASSES` = {R.CONFIRMATORY_FRAME_PASSES} "
        f"passes at offsets {list(R.CONFIRMATORY_FRAME_OFFSETS)} — so "
        f"**{blocks} blocks per frame** "
        f"(`rules.CONFIRMATORY_BLOCKS_PER_FRAME`), "
        f"{R.CONFIRMATORY_BLOCKS_TOTAL} blocks in all, the same share Gate "
        "3's coverage projection uses. The offsets are distinct modulo "
        f"{C.N_WORDINGS}, so a frame's blocks are {blocks} *distinct* topics "
        "and no topic recurs inside a frame; "
        f"{R.CONFIRMATORY_MAX_PASSES} passes is the ceiling.",
        f"* `C.M_DRAWS` = {C.M_DRAWS} draws per cell.",
        f"* Δ_R(f) reads {1 + C.N_CORE_REFERENCES} composed cells per "
        f"configuration — `pair:B+A` and `pair:B+R_j` for three references — "
        f"so **{per_cell} generations per cell per frame** and "
        f"**{entering} entering the contrast** per configuration.",
        "* The **independent unit is the block**, not the generation: §17.1's "
        "bootstrap resamples blocks with replacement and carries every cell "
        "mean of a drawn block, and cells are never resampled. Eight draws "
        "inside a cell shrink the draw component and leave the topic "
        f"component untouched, so the effective n for Δ_R(f) is **{blocks}**.",
        "",
        "## The estimator",
        "",
        "§16.1 verbatim, imported from `dci1v4.analysis.variance.variances` "
        "— the registered paired/clustered form, not an "
        "independent-proportions formula:",
        "",
        "```",
        "Var(Delta_R) = ( 2 (1 - rho) sigma2_topic",
        "                 + sigma2_draw (1/M + 1/(3M)) ) / blocks",
        "```",
        "",
        "`rho` is the within-block correlation between two cells of the same "
        "block; the draw term's `1/M + 1/(3M)` is the 4/3 that averaging "
        "three references against one A leaves behind. The simultaneous "
        f"half-width is at the {FAMILY} ({FAMILY_SIZE}-member) Šidák constant "
        f"{sidak_critical(FAMILY_SIZE):.4f} — the constant §16.2's table is "
        "quoted at, and an upper bound on the bootstrap's studentised "
        "maximum-modulus value, so it is the conservative end. Δ_R's "
        f"registered precision precondition (§16.2) is **{PRECONDITION}**, "
        "and `claims.Interval.meets_precondition` evaluates it on the "
        "**simultaneous** half-width.",
        "",
        "## A. Per LOCAL-supported (model, frame)",
        "",
        "| model | frame | confirmatory allocation | expected SE | 95 % half-width (simultaneous) | ~80 % MDE |",
        "|---|---|---|---|---|---|",
    ]
    for model, entry in sorted(latest.items()):
        for w, fr in sorted(entry["by_frame"].items(), key=lambda kv: int(kv[0])):
            se_lo, se_hi = fr["se_range"]
            hw_lo, hw_hi = fr["half_width_simultaneous_range"]
            m_lo, m_hi = fr["mde_range"]
            lines.append(
                f"| `{model}` | f{w} | {fr['n_blocks_per_frame']} blocks × "
                f"{fr['m_draws']} draws × {fr['cells_read_by_delta_r']} cells "
                f"= {fr['observations_entering_delta_r_per_configuration']} "
                f"generations | {se_lo:.4f} – {se_hi:.4f} | "
                f"{hw_lo:.4f} – {hw_hi:.4f} | {m_lo:.3f} – {m_hi:.3f} |")
    lines += [
        "",
        "The interval is the span across every scenario in section B, worst "
        "case included. The frames differ only through the "
        "`CALIBRATION_ANCHORED` row — every other scenario is a property of "
        "the allocation, which is the same for all of them.",
        "",
        "## B. Scenarios",
        "",
        "The variance depends on composed-cell compliance, which does not "
        "exist before a freeze. Every row says where its numbers came from.",
        "",
        "| model | frame | scenario | φ | ρ | p(1−p) | SE | simultaneous half-width | ~80 % MDE | ≤ 0.05? |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for model, entry in sorted(latest.items()):
        for w, fr in sorted(entry["by_frame"].items(), key=lambda kv: int(kv[0])):
            for name in sorted(fr["scenarios"]):
                sc = fr["scenarios"][name]
                rho = sc.get("rho", sc.get("block_corr"))
                lines.append(
                    f"| `{model}` | f{w} | {name} | "
                    f"{_fmt(sc.get('phi'), '.3f')} | {_fmt(rho, '.3f')} | "
                    f"{_fmt(sc.get('p_one_minus_p'))} | "
                    f"{sc['se_delta_r']:.4f} | "
                    f"{sc['half_width_simultaneous']:.4f} | "
                    f"{sc['mde_80']:.3f} | "
                    f"{'yes' if sc['meets_precondition'] else '**NO**'} |")
    lines += [
        "",
        "**What each scenario is.**",
        "",
        f"* `REGISTERED_PLANNING` — φ {C.PHI_PRIMARY}, p(1−p) "
        f"{C.P_ONE_MINUS_P}, ρ {C.RHO}: the constants §16.2's table is quoted "
        "at and the 384-block allocation was itself chosen at. This is the "
        "design's own row.",
        f"* `REGISTERED_ALTERNATE` — φ {C.PHI_ALTERNATE}, the sensitivity "
        "value §16.3 carries.",
        "* `WORST_CASE` — p(1−p) = 0.25 (a composed cell at 0.5, the variance "
        "maximum) with ρ = 0. Var falls as ρ rises, so ρ = 0 is the "
        "conservative end; nothing the design can produce exceeds this row.",
        "* `CALIBRATION_ANCHORED` — φ and ρ estimated from **this frame's own "
        "solo cells** (A at n\\*(f) and the three core references at their "
        "selected severities) by the production `realised_decomposition` and "
        "`realised_correlation` (§23 / check C12), with p(1−p) at B's solo "
        "compliance at m\\*(f). Its ρ is the correlation between two "
        "*different constraints'* solo cells; the ρ that governs Δ_R is "
        "between composed cells that all measure **B** under different "
        "companions, which shares far more. This row therefore understates ρ "
        "and its SE is conservative for that reason as well.",
        "* `REHEARSAL_ANCHORED*` — the block-bootstrap SE of one companion's "
        "`D` and the between-companion per-block correlation measured on the "
        "**completed v7 development rehearsal** at 384 blocks × 8 draws "
        "(`dci1v8dev.spectrum.precision.MEASURED`, already the constant Gate "
        "3's coverage projection runs on), rescaled to the frame's blocks. "
        "This is the only row measured on composed cells that actually "
        "measure B under a companion, so it is the most apt — and it is v7 "
        "evidence, a design constant, not a v8 outcome. The pessimistic and "
        "optimistic rows are the ends of `MEASURED`'s own recorded range "
        f"(SE {MEASURED['se_point_range']}, ρ {MEASURED['block_corr_range']}).",
        "",
        "## C. What allocation would meet the registered precondition",
        "",
        "A block-bootstrap SE falls as 1/√blocks, so the blocks needed scale "
        "as (realised ÷ target)². Both targets are registered: §16.2's "
        f"precondition {PRECONDITION}, and an 80 %-power MDE at §11.9's "
        f"smallest effect of interest {C.SMALLEST_EFFECT_OF_INTEREST}. No "
        "threshold is invented here.",
        "",
        "Each row is the **worst LOCAL-supported frame** for that scenario, "
        "so the allocation it names covers every frame.",
        "",
        "| scenario | blocks/frame for the 0.05 precondition | passes | blocks/frame for an MDE of 0.10 | passes | binding frame |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name in sorted(frames[0][2]["required_allocation"]["by_scenario"]):
        rows = [f[2]["required_allocation"]["by_scenario"][name] for f in frames]
        worst = max(frames, key=lambda f: f[2]["required_allocation"]
                    ["by_scenario"][name]["blocks_for_precondition"])
        lines.append(
            f"| {name} | {max(r['blocks_for_precondition'] for r in rows)} | "
            f"{max(r['passes_for_precondition'] for r in rows)} | "
            f"{max(r['blocks_for_sesoi_mde'] for r in rows)} | "
            f"{max(r['passes_for_sesoi_mde'] for r in rows)} | "
            f"`{worst[0]}` f{worst[1]} |")
    lines += [
        "",
        "",
        f"**Feasibility.** §6.2 holds `N_CONFIRMATORY` = {C.N_CONFIRMATORY} "
        "confirmatory topics and the sequestered set is reserved, so one pass "
        f"gives {C.N_CONFIRMATORY // C.N_WORDINGS} blocks per frame and more "
        "blocks per frame means **passes** — rendering the confirmatory "
        "topics again under a different frame offset, exactly as "
        f"`rules.CALIBRATION_FRAME_OFFSETS` does at Gate 2. {C.N_WORDINGS} "
        "passes is the ceiling: every frame then holds every confirmatory "
        "topic once, and a further pass would repeat a topic inside a frame "
        "and count one measurement as two.",
        "",
        f"Across every LOCAL-supported frame, **{passes_plausible} passes** "
        f"({passes_plausible * (C.N_CONFIRMATORY // C.N_WORDINGS)} blocks per "
        "frame) covers every "
        "scenario that is an estimate rather than a bound, and is "
        f"{'inside' if passes_plausible <= C.N_WORDINGS else '**beyond**'} "
        f"the {C.N_WORDINGS}-pass ceiling. The allocation in force is "
        f"**{R.CONFIRMATORY_FRAME_PASSES} passes**, {blocks} blocks per "
        f"frame, so this is "
        f"{'what the design already runs' if R.CONFIRMATORY_FRAME_PASSES >= passes_plausible else '**more than the design runs**'}"
        f". The two bounds need more — "
        f"`WORST_CASE` up to {passes_worst} passes — but `WORST_CASE` fixes "
        "p(1−p) at its maximum 0.25 while every supported frame's own B-solo "
        "compliance at m\\*(f) is 0.75–0.88, i.e. p(1−p) of 0.10–0.19, and "
        "`CALIBRATION_ANCHORED`'s ρ is a cross-constraint floor. Neither is a "
        "scenario the pre-freeze evidence supports; both are stated so the "
        "range is not quietly truncated.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out", default=str(REPORTS / "local_precision"))
    args = ap.parse_args(argv)

    by_root = {}
    for name in args.roots:
        root = pathlib.Path(name)
        if not root.is_absolute() and not root.exists():
            root = EVIDENCE / name
        by_root[root.name] = read_root(root)
    latest: dict[str, Any] = {}
    for entries in by_root.values():
        for model, entry in entries.items():
            current = latest.get(model)
            if current is None or str(entry["recorded_at"]) > str(current["recorded_at"]):
                latest[model] = entry

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(
        {"label": LABEL, "precondition": PRECONDITION,
         "family": FAMILY, "family_size": FAMILY_SIZE,
         "latest_per_model": latest, "by_root": by_root},
        indent=1, sort_keys=True) + "\n")
    out.with_suffix(".md").write_text(render(latest))
    print(f"wrote {out.with_suffix('.md')}")
    for model, entry in sorted(latest.items()):
        for w, fr in sorted(entry["by_frame"].items(), key=lambda kv: int(kv[0])):
            print(f"  {model:<26} f{w}  SE {fr['se_range'][0]:.4f}-{fr['se_range'][1]:.4f}"
                  f"  HW {fr['half_width_simultaneous_range'][0]:.4f}-"
                  f"{fr['half_width_simultaneous_range'][1]:.4f}"
                  f"  MDE {fr['mde_range'][0]:.3f}-{fr['mde_range'][1]:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
