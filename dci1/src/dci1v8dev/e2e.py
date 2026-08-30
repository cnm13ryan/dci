"""The v8 candidate pipeline end to end, on one supplied world.

    clean wording -> broad discovery -> uncertainty-aware pre-screen
    -> adaptive severity expansion -> LOCAL/SPECTRUM-specific rung retention
    -> full calibration (+ one bounded extension round)
    -> separate LOCAL / SPECTRUM validity -> deterministic spectrum selection
    -> coverage + projected-precision gate (+ admissible backups)

``run_candidate`` takes a ``World`` --- the synthetic truth: every family's
true solo rate over its declared range, its chance rate on the
unconstrained cell, its vacuity, κ(R|B), and A's true curve --- and drives
the whole chain with seeded draws at the registered sample sizes
(24 × 1 pre-screen, 24 × 1 per second-pass batch, 96 × 4 per calibration
split). Every stage's output is the record the stage would write, so the
tests can assert determinism, order invariance, leakage refusal and the
behaviour of each rule on a case that exercises it. ``truth_of`` evaluates
the same rules on the true parameters, which is what the pipeline's verdict
is compared with.

Nothing here reads evidence; nothing here is registered.
"""
from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dci1v7.protocol import constants as C
from dci1v7.stages import stability as stability_stage
from dci1v7.stages.calibration_table import CalibrationRow, tie_key
from dci1v7.stages.interaction import KappaUnderBSource
from dci1v7.stages.selection import _group_order, restrictiveness_key
from dci1v7.verifiers.constraints import FAMILIES, LADDERS, RESERVES
from dci1v8dev import rules as R
from dci1v8dev.prescreen import legacy
from dci1v8dev.prescreen.extension import ExtensionRule, calibration_extension_plan
from dci1v8dev.prescreen.geometry import select_iota_a
from dci1v8dev.prescreen.rescreen import (
    DEFAULT_RESCREEN_CONFIG,
    RescreenBatch,
    RescreenConfig,
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
    SCREEN_ACCEPT,
    SPECTRUM_LABEL,
    ScreenConfig,
    screen_families,
)
from dci1v8dev.simulate import _draw_counts, _topic_rates
from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.coverage import CoverageRule, selected_coverage
from dci1v8dev.spectrum.selection import (
    DEFAULT_SELECTION_RULE,
    SelectionRule,
    select_spectrum,
)
from dci1v8dev.spectrum.validity import (
    DEFAULT_SPECTRUM_RULE,
    SpectrumRule,
    classify_pool,
)

__all__ = ["FamilyTruth", "World", "run_candidate", "truth_of",
           "world_from_archetypes"]

MODEL_KEY = "synthetic-model"
M_STAR = 9


@dataclass(frozen=True)
class FamilyTruth:
    kind: str
    #: true solo compliance by severity over the declared range
    true_p: dict[int, float]
    #: chance compliance on the unconstrained cell (one value or per severity)
    kappa: float | dict[int, float] = 0.0
    vacuity: float = 0.0
    #: κ(R|B): the family's compliance on the B-solo cell (§13.6)
    kappa_under_b: float | dict[int, float] | None = None
    #: v7-instrument reading defect: this many of the four frames are read
    #: with the marker absent (the wording-confusion case); the v8 frames
    #: read all four.
    misread_frames: int = 0
    #: A composed outcome the world knows and the pipeline must never read
    #: (the leakage check runs two worlds that differ only here).
    interference: float | dict[int, float] = 0.0

    def p(self, q: int, *, instrument: str) -> float:
        base = self.true_p[q]
        if instrument == "v7" and self.misread_frames:
            return base * (4 - self.misread_frames) / 4.0
        return base

    def k(self, q: int) -> float:
        return self.kappa[q] if isinstance(self.kappa, dict) else self.kappa

    def kb(self, q: int) -> float:
        if self.kappa_under_b is None:
            return self.k(q)
        return (self.kappa_under_b[q] if isinstance(self.kappa_under_b, dict)
                else self.kappa_under_b)


@dataclass(frozen=True)
class World:
    families: dict[str, FamilyTruth]
    a_curve: dict[int, float]
    icc: float = 0.40
    a_kappa: float = 0.0
    instrument: str = "v8"
    seed: int = 20260829
    name: str = "world"
    config: dict[str, Any] = field(default_factory=dict)


def world_from_archetypes(assignments: Mapping[str, str], *, a_curve: dict[int, float],
                          name: str, seed: int = 20260829, **kw) -> World:
    """Families from ``simulate.ARCHETYPES``: kind -> archetype name."""
    from dci1v8dev.simulate import ARCHETYPES
    fams = {}
    for kind, arch_name in assignments.items():
        arch = ARCHETYPES[arch_name]
        sev = list(LADDERS[kind]) + [q for q in RESERVES[kind] if q not in LADDERS[kind]]
        vals = [arch.true_p[q] for q in sorted(arch.true_p)]
        if len(vals) < len(sev):
            vals += [vals[-1]] * (len(sev) - len(vals))
        fams[kind] = FamilyTruth(kind=kind, true_p={q: v for q, v in zip(sev, vals)},
                                 kappa=arch.kappa, vacuity=arch.vacuity)
    return World(families=fams, a_curve=dict(a_curve), name=name, seed=seed, **kw)


# ----------------------------------------------------------------- sampling

def _rng(world: World, *parts: Any) -> np.random.Generator:
    key = "|".join(str(p) for p in parts)
    # a stable digest, not the builtin hash: the builtin is salted per
    # process (PYTHONHASHSEED), which made the synthetic worlds differ
    # between runs and tests_v8dev/test_e2e.py flaky (2026-08-30)
    digest = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return np.random.default_rng([world.seed, digest % (2 ** 31)])


def _prescreen_table(world: World) -> tuple[list[PrescreenRung], list[ARung]]:
    table = []
    for kind in sorted(world.families):
        fam = world.families[kind]
        rng = _rng(world, "prescreen", kind)
        for q in LADDERS[kind]:
            k, n = _draw_counts(rng, fam.p(q, instrument=world.instrument),
                                C.N_PRESCREEN, 1, world.icc)
            ck, cn = _draw_counts(rng, fam.k(q), C.N_PRESCREEN, 1, world.icc)
            vk, _ = _draw_counts(rng, fam.vacuity, C.N_PRESCREEN, 1, world.icc)
            table.append(PrescreenRung(kind=kind, severity=q, solo_k=k, solo_n=n,
                                       chance_k=float(ck), chance_n=float(cn),
                                       vacuous_k=min(vk, k), n_topics=C.N_PRESCREEN,
                                       draws_per_topic=1))
    rng = _rng(world, "prescreen", "A")
    a_grid = []
    for q, p in sorted(world.a_curve.items()):
        k, n = _draw_counts(rng, p, C.N_PRESCREEN, 1, world.icc)
        ck, cn = _draw_counts(rng, world.a_kappa, C.N_PRESCREEN, 1, world.icc)
        a_grid.append(ARung(severity=q, solo_k=k, solo_n=n, chance_k=float(ck),
                            chance_n=float(cn), n_topics=C.N_PRESCREEN,
                            draws_per_topic=1))
    return table, a_grid


def _measure_factory(world: World):
    counter = {"batches": 0}

    def measure(batch: RescreenBatch):
        counter["batches"] += 1
        new = []
        for kind, fam_batch in sorted(batch.families.items()):
            fam = world.families[kind]
            rng = _rng(world, "rescreen", kind, counter["batches"])
            for q in list(fam_batch["severities"]) + list(fam_batch["reserve_picks"]):
                k, n = _draw_counts(rng, fam.p(q, instrument=world.instrument),
                                    batch.n_topics, batch.draws_per_topic, world.icc)
                ck, cn = _draw_counts(rng, fam.k(q), batch.n_topics,
                                      batch.draws_per_topic, world.icc)
                vk, _ = _draw_counts(rng, fam.vacuity, batch.n_topics,
                                     batch.draws_per_topic, world.icc)
                new.append(PrescreenRung(kind=kind, severity=q, solo_k=k, solo_n=n,
                                         chance_k=float(ck), chance_n=float(cn),
                                         vacuous_k=min(vk, k), n_topics=batch.n_topics,
                                         draws_per_topic=batch.draws_per_topic,
                                         reserve=q not in LADDERS[kind]))
        new_a = []
        if batch.a_grid:
            rng = _rng(world, "rescreen", "A", counter["batches"])
            for q, p in sorted(world.a_curve.items()):
                k, n = _draw_counts(rng, p, batch.n_topics, batch.draws_per_topic, world.icc)
                ck, cn = _draw_counts(rng, world.a_kappa, batch.n_topics,
                                      batch.draws_per_topic, world.icc)
                new_a.append(ARung(severity=q, solo_k=k, solo_n=n, chance_k=float(ck),
                                   chance_n=float(cn), n_topics=batch.n_topics,
                                   draws_per_topic=batch.draws_per_topic))
        return new, new_a
    return measure


def _split_measurement(rng: np.random.Generator, p: float, kappa: float, *,
                       n_topics: int, draws: int, icc: float) -> dict[str, Any]:
    rates = _topic_rates(rng, p, n_topics, icc)
    per_topic = rng.binomial(draws, rates) / draws
    chance = float(np.mean(rng.binomial(draws, np.full(n_topics, kappa)) / draws))
    return {"per_topic": tuple(float(v) for v in per_topic),
            "solo": float(np.mean(per_topic)), "chance": chance}


def _calibrate(world: World, labels: Sequence[str], *, round_label: str
               ) -> dict[str, list[CalibrationRow]]:
    """Two disjoint 96-topic splits at M_cal draws for every label, and the
    pooled 192-topic row; chance from the unconstrained cell of each split."""
    rows: dict[str, list[CalibrationRow]] = {C.CALIBRATION_A: [], C.CALIBRATION_B: [],
                                             "pooled": []}
    for label in sorted(labels, key=lambda s: (s.split(":")[0], int(s.split(":")[1]))):
        kind, q = label.split(":")
        q = int(q)
        fam = world.families[kind]
        rng = _rng(world, "calibration", round_label, label)
        parts = {}
        for split in (C.CALIBRATION_A, C.CALIBRATION_B):
            parts[split] = _split_measurement(
                rng, fam.p(q, instrument=world.instrument), fam.k(q),
                n_topics=C.N_CALIBRATION_A, draws=C.M_CAL, icc=world.icc)
        pooled_pt = parts[C.CALIBRATION_A]["per_topic"] + parts[C.CALIBRATION_B]["per_topic"]
        pooled = {"per_topic": pooled_pt, "solo": float(np.mean(pooled_pt)),
                  "chance": float(np.mean([parts[s]["chance"]
                                           for s in (C.CALIBRATION_A, C.CALIBRATION_B)]))}
        for split, m in ((C.CALIBRATION_A, parts[C.CALIBRATION_A]),
                         (C.CALIBRATION_B, parts[C.CALIBRATION_B]), ("pooled", pooled)):
            n_topics = len(m["per_topic"])
            rows[split].append(CalibrationRow(
                kind=kind, severity=q, split=split, model_key=MODEL_KEY,
                solo_compliance=m["solo"], chance_compliance=m["chance"],
                solo_vacuity=fam.vacuity, kappa_under_b=fam.kb(q),
                kappa_under_b_source=KappaUnderBSource(
                    load=1, present=(f"B:{M_STAR}",), candidate=label,
                    model_key=MODEL_KEY, m_star=M_STAR, split=split,
                    n_topics=n_topics, n_draws=C.M_CAL),
                n_topics=n_topics, n_draws=C.M_CAL, per_topic_solo=m["per_topic"]))
    return rows


def _calibrate_a(world: World) -> dict[str, Any]:
    """A's grid at calibration precision; §12.3's selection on the calibrated
    curve gives ι_A on the pooled table and per split."""
    out = {}
    curves = {C.CALIBRATION_A: {}, C.CALIBRATION_B: {}, "pooled": {}}
    for q, p in sorted(world.a_curve.items()):
        rng = _rng(world, "calibration", "A", q)
        parts = {s: _split_measurement(rng, p, world.a_kappa, n_topics=C.N_CALIBRATION_A,
                                       draws=C.M_CAL, icc=world.icc)
                 for s in (C.CALIBRATION_A, C.CALIBRATION_B)}
        for s in (C.CALIBRATION_A, C.CALIBRATION_B):
            curves[s][q] = (parts[s]["solo"], parts[s]["chance"])
        curves["pooled"][q] = (
            float(np.mean([parts[s]["solo"] for s in parts])),
            float(np.mean([parts[s]["chance"] for s in parts])))
    sev = sorted(world.a_curve)
    p = np.array([[curves["pooled"][q][0] for q in sev]])
    k = np.array([[curves["pooled"][q][1] for q in sev]])
    iota_a, n_star = select_iota_a(p, k, sev)
    n_star = int(n_star[0])
    out["n_star"] = n_star
    out["iota_a"] = float(iota_a[0])
    out["solo_compliance_a"] = curves["pooled"][n_star][0]
    out["iota_a_by_split"] = {}
    out["solo_a_by_split"] = {}
    for s in (C.CALIBRATION_A, C.CALIBRATION_B):
        solo, kappa = curves[s][n_star]
        out["solo_a_by_split"][s] = solo
        out["iota_a_by_split"][s] = (solo - kappa) / (1 - kappa)
    out["curves"] = {s: {str(q): v for q, v in c.items()} for s, c in curves.items()}
    return out


# ----------------------------------------------------------------- the chain

def _core_references(local: Mapping[str, Mapping[str, Any]],
                     pooled: Sequence[CalibrationRow]) -> dict[str, int]:
    """Development stand-in for §13.8's core selection: the LOCAL-valid rung
    nearest ι_A per family, three families by distance then the registered
    tie-breaks. Not the registered kernel; labelled as such in the record."""
    by_label = {r.label: r for r in pooled}
    best: dict[str, tuple] = {}
    for label, v in local.items():
        if not v.get("passed"):
            continue
        row = by_label[label]
        key = (tie_key(v["distance"]), row.structural_tier, _group_order(row.kind),
               restrictiveness_key(row.kind, row.severity), row.kind)
        if row.kind not in best or key < best[row.kind][0]:
            best[row.kind] = (key, row.severity)
    ranked = sorted(best.items(), key=lambda kv: kv[1][0])
    return {kind: sev for kind, (_, sev) in ranked[:C.N_CORE_REFERENCES]}


def run_candidate(world: World, *,
                  screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                  rescreen_config: RescreenConfig = DEFAULT_RESCREEN_CONFIG,
                  retention_config: RetentionConfig = DEFAULT_RETENTION_CONFIG,
                  extension_rule: ExtensionRule = ExtensionRule(),
                  spectrum_rule: SpectrumRule = DEFAULT_SPECTRUM_RULE,
                  selection_rule: SelectionRule = DEFAULT_SELECTION_RULE,
                  stability_resamples: int = 400,
                  family_order: Sequence[str] | None = None) -> dict[str, Any]:
    """The whole chain on ``world``. ``family_order`` only permutes the input
    table (an order-invariance check); every stage sorts by family id."""
    table, a_grid = _prescreen_table(world)
    if family_order is not None:
        order = {k: i for i, k in enumerate(family_order)}
        table = sorted(table, key=lambda r: (order.get(r.kind, 99), -r.severity))
    # 1. stage 1 + 2
    stage1 = screen_families(table, a_grid, config=screen_config)
    stage2 = run_rescreen(table, a_grid, screen_config=screen_config,
                          config=rescreen_config, measure=_measure_factory(world))
    final_screen = stage2["screen"]
    # 2. retention
    retention = retain(final_screen, config=retention_config)
    forwarded = [e["candidate"] for e in retention["forwarded"]]
    # 3. calibration
    tables = _calibrate(world, forwarded, round_label="round-0")
    a_cal = _calibrate_a(world)
    iota_a = a_cal["iota_a"]
    # 4. one bounded extension round for spectrum candidates not reaching a side
    spectrum_families = [k for k, v in final_screen["families"].items()
                         if SPECTRUM_LABEL in v["labels"] and v["status"] == SCREEN_ACCEPT]
    reach_input = {}
    for kind in spectrum_families:
        rows = [r for r in tables["pooled"] if r.kind == kind
                and r.chance_compliance < C.CHANCE_DEGENERACY_MAX]
        adm = [r for r in rows if R.SPECTRUM_GUARD_BAND[0] <= r.solo_compliance
               <= R.SPECTRUM_GUARD_BAND[1] and r.chance_compliance <= C.CHANCE_MAX
               and r.solo_compliance - r.chance_compliance >= C.INSTRUCTION_LIFT_MIN]
        reach_input[kind] = {
            "measured": sorted({r.severity for r in rows}),
            "reaches_below": any(r.iota <= iota_a - extension_rule.d_below for r in adm),
            "reaches_above": any(r.iota >= iota_a + extension_rule.d_above for r in adm),
            "spectrum_candidate": True}
    ext_plan = calibration_extension_plan(reach_input, rule=extension_rule)
    ext_labels = [f"{k}:{q}" for k, qs in ext_plan["picks"].items() for q in qs]
    if ext_labels:
        ext_tables = _calibrate(world, ext_labels, round_label="extension-1")
        for s in tables:
            tables[s].extend(ext_tables[s])
    # 5. validity (folded = v7's own §13.7 on the same rows; unfolded = v8's)
    pairs = stability_stage.split_pair(tables[C.CALIBRATION_A], tables[C.CALIBRATION_B])
    folded = {lab: stability_stage.stability_verdict(
        pair, iota_a_by_split=a_cal["iota_a_by_split"],
        solo_a_by_split=a_cal["solo_a_by_split"], seed=world.seed,
        resamples=stability_resamples) for lab, pair in sorted(pairs.items())}
    pool = classify_pool(tables["pooled"], tables[C.CALIBRATION_A], tables[C.CALIBRATION_B],
                         iota_a=iota_a, solo_compliance_a=a_cal["solo_compliance_a"],
                         n_topics_a=C.N_CALIBRATION, folded_stability=folded,
                         seed=world.seed, resamples=stability_resamples, rule=spectrum_rule)
    # 6. core (development stand-in), spectrum selection, coverage, backups
    core = _core_references(pool["local"], tables["pooled"])
    by_label = {r.label: r for r in tables["pooled"]}
    valid_rows = [r for r in tables["pooled"] if pool["spectrum"][r.label]["passed"]]
    core_rows = [by_label[f"{f}:{q}"] for f, q in core.items() if f"{f}:{q}" in by_label]
    selection = select_spectrum(valid_rows + [r for r in core_rows if r not in valid_rows],
                                iota_a=iota_a, core_references=core, rule=selection_rule)
    backups = admissible_backups(pool["local"], tables["pooled"], iota_a=iota_a,
                                 used_families=list(core))
    # 7. costs
    per_rung = 2 * C.N_CALIBRATION_A * C.M_CAL
    screen_gens = C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS * (len(table) + len(a_grid) + 1)
    spectrum_refs = selection["n_spectrum_references"]
    costs = {"screen": screen_gens,
             "rescreen": stage2["cost_generations"],
             "calibration_rungs": len(forwarded), "calibration": len(forwarded) * per_rung,
             "extension_rungs": len(ext_labels), "extension": len(ext_labels) * per_rung,
             "a_grid_calibration": len(a_grid) * per_rung,
             "spectrum_confirmatory": spectrum_refs * 3 * C.N_BLOCKS * 8,
             "total_to_freeze": screen_gens + stage2["cost_generations"]
             + (len(forwarded) + len(ext_labels) + len(a_grid)) * per_rung}
    return {
        "world": world.name, "instrument": world.instrument, "seed": world.seed,
        "stage1": {"statuses": stage1["statuses"],
                   "p_spectrum": {k: v["p_spectrum"] for k, v in stage1["families"].items()}},
        "final_screen": {"statuses": final_screen["statuses"],
                         "labels": final_screen["labels"],
                         "p_spectrum": {k: v["p_spectrum"]
                                        for k, v in final_screen["families"].items()},
                         "resolved_at_max": stage2["resolved_at_max"],
                         "batches_used": stage2["batches_used"],
                         "reserve_picks": {h["batch"]["index"]: h["batch"]["reserve_picks"]
                                           for h in stage2["history"] if h["batch"]}},
        "retention": {"forwarded": forwarded,
                      "roles": {e["candidate"]: e["roles"] for e in retention["forwarded"]},
                      "spectrum_families": retention["spectrum_families"],
                      "local_families": retention["local_families"],
                      "spectrum_geometry": retention["spectrum_geometry"]},
        "calibration": {"iota_a": iota_a, "n_star": a_cal["n_star"],
                        "iota_a_by_split": a_cal["iota_a_by_split"],
                        "rows": {r.label: {"iota": r.iota if r.chance_compliance
                                           < C.CHANCE_DEGENERACY_MAX else None,
                                           "solo": r.solo_compliance,
                                           "chance": r.chance_compliance}
                                 for r in tables["pooled"]}},
        "extension": ext_plan,
        "validity": {"local_valid": sorted(k for k, v in pool["local"].items() if v["passed"]),
                     "spectrum_valid": sorted(k for k, v in pool["spectrum"].items()
                                              if v["passed"]),
                     "first_failing_spectrum": {k: v["first_failing_component"]
                                                for k, v in pool["spectrum"].items()
                                                if not v["passed"]},
                     "n_folded_stable": pool["n_folded_stable"],
                     "n_unfolded_stable": pool["n_unfolded_stable"]},
        "core_references": core,
        "core_selection_note": "development stand-in for §13.8 (nearest LOCAL-valid "
                               "rung per family, three by distance); not the kernel",
        "selection": {k: v for k, v in selection.items() if k != "trace"},
        "selection_trace": selection["trace"],
        "backups": backups,
        "identified": selection["identified"], "status": selection["status"],
        "costs": costs,
    }


def truth_of(world: World, *, spectrum_rule: SpectrumRule = DEFAULT_SPECTRUM_RULE,
             selection_rule: SelectionRule = DEFAULT_SELECTION_RULE,
             coverage_rule: CoverageRule | None = None) -> dict[str, Any]:
    """The same rules on the true parameters over each family's whole
    declared range (what a perfectly informed pipeline would find)."""
    sev_a = sorted(world.a_curve)
    p = np.array([[world.a_curve[q] for q in sev_a]])
    k = np.array([[world.a_kappa for _ in sev_a]])
    iota_a, n_star = select_iota_a(p, k, sev_a)
    iota_a = float(iota_a[0])
    rows: list[CalibrationRow] = []
    for kind in sorted(world.families):
        fam = world.families[kind]
        for q in sorted(fam.true_p):
            rows.append(CalibrationRow(
                kind=kind, severity=q, split="pooled", model_key=MODEL_KEY,
                solo_compliance=fam.p(q, instrument=world.instrument),
                chance_compliance=fam.k(q), solo_vacuity=fam.vacuity,
                kappa_under_b=fam.kb(q),
                kappa_under_b_source=KappaUnderBSource(
                    load=1, present=(f"B:{M_STAR}",), candidate=f"{kind}:{q}",
                    model_key=MODEL_KEY, m_star=M_STAR, split="pooled",
                    n_topics=C.N_CALIBRATION, n_draws=C.M_CAL),
                n_topics=C.N_CALIBRATION, n_draws=C.M_CAL,
                per_topic_solo=(fam.p(q, instrument=world.instrument),) * C.N_CALIBRATION))
    from dci1v8dev.spectrum.validity import local_validity, spectrum_validity
    local = {r.label: local_validity(r, iota_a=iota_a, solo_compliance_a=world.a_curve[int(n_star[0])],
                                     n_topics_a=C.N_CALIBRATION,
                                     folded_stability={"passed": True})
             for r in rows if r.chance_compliance < C.CHANCE_DEGENERACY_MAX}
    spectrum = {r.label: spectrum_validity(r, iota_a=iota_a, unfolded={"passed": True},
                                           rule=spectrum_rule)
                for r in rows}
    valid = [r for r in rows if spectrum[r.label]["passed"]]
    sel = select_spectrum(valid, iota_a=iota_a, rule=selection_rule)
    cov = coverage_rule or selection_rule.coverage
    family_support = {}
    for kind in sorted(world.families):
        fam_valid = [r for r in valid if r.kind == kind]
        family_support[kind] = bool(
            any(r.iota <= iota_a - cov.d_below for r in fam_valid)
            and any(r.iota >= iota_a + cov.d_above for r in fam_valid))
    return {"iota_a": iota_a, "n_star": int(n_star[0]),
            "family_support": family_support,
            "iota": {r.label: (r.iota if r.chance_compliance < C.CHANCE_DEGENERACY_MAX
                               else None) for r in rows},
            "local_families": sorted({lab.split(":")[0] for lab, v in local.items()
                                      if v["passed"]}),
            "spectrum_valid": sorted(lab for lab, v in spectrum.items() if v["passed"]),
            "spectrum_valid_families": sorted({lab.split(":")[0] for lab, v in spectrum.items()
                                               if v["passed"]}),
            "identified": sel["identified"], "status": sel["status"],
            "selection": {k: v for k, v in sel.items() if k != "trace"}}
