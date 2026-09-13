"""The targeted second pass: deterministic, bounded, and only where it pays.

Not every family goes from the cheapest screen straight into calibration.
Families whose spectrum verdict the first pass could not settle
(``SCREEN_RESAMPLE``: P(spectrum event) strictly between the reject and
accept thresholds) receive a fixed batch of further observations; the screen
is re-run on the pooled counts; and the loop repeats until the family leaves
the middle band or the registered maximum number of batches is spent.

**What a batch is.** For every family in the middle band: every rung the
family has measured so far, plus at most ``reserve_picks_per_batch`` reserve
severities from §7.10's frozen reserve in the direction the family's
deficiency requires (via v7's own ``expansion_plan_for_family``, so the
direction rule is the registered one: harder when the family lacks a rung
below A, easier when it lacks one above, outward from both extremes when the
span is short). And A's grid, once per batch, because iota_A's own
uncertainty is shared by every family and is the cheapest thing to buy down.

**Layout.** ``layout="topics"`` measures the batch on ``batch_topics`` fresh
topics at ``batch_draws`` draws each; ``layout="draws"`` adds ``batch_draws``
draws on the same pre-screen topics. On the measured topic ICC (~0.40) a
fresh topic is worth about 2.5 repeated draws, which is why ``topics`` is the
default; the effective sample size in ``statistics`` accounts for either.

**Stopping.** Deterministic: a family stops when its status is not
``SCREEN_RESAMPLE`` or when it has consumed ``max_batches``. A family still
in the middle band at the maximum is resolved by the **posterior majority**
--- accept iff P >= 0.5 --- and recorded ``AMBIGUOUS_AT_MAX`` so the record
says the evidence did not settle it. No observed value is read by a person.

**Maximum cost** is a function of the configuration alone
(``max_cost_generations``), so a v8 registration can state it in advance.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages import regime
from dci1v7.verifiers.constraints import LADDERS, RESERVES, SELECTABLE_FAMILY_IDS
from dci1v8dev import rules as R
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import (
    SCREEN_ACCEPT,
    SCREEN_REJECT,
    SCREEN_RESAMPLE,
    ScreenConfig,
    screen_families,
)

__all__ = [
    "AMBIGUOUS_AT_MAX",
    "RescreenBatch",
    "RescreenConfig",
    "apply_batch",
    "max_cost_generations",
    "plan_batch",
    "run_rescreen",
    "run_rescreen_by_frame",
    "resolve_at_max",
    "union_batch",
]

AMBIGUOUS_AT_MAX = "AMBIGUOUS_AT_MAX"


@dataclass(frozen=True)
class RescreenConfig:
    max_batches: int = R.RESCREEN_MAX_BATCHES
    layout: str = "topics"           # "topics" | "draws"
    batch_topics: int = R.RESCREEN_BATCH_TOPICS
    batch_draws: int = 1
    reserve_picks_per_batch: int = R.RESCREEN_RESERVE_PICKS_PER_BATCH
    include_a_grid: bool = True
    #: After ``max_batches`` a family still in the middle band is accepted
    #: iff P(spectrum event) >= this. 0.5 is the posterior majority.
    final_accept_at: float = R.RESCREEN_FINAL_ACCEPT_AT
    #: The frame-aware second pass lays each batch out one pass per frame
    #: offset (``rules.SCREEN_FRAME_OFFSETS``), so a batch generates
    #: ``frame_passes`` rows per (topic, cell) and every frame holds every
    #: batch topic. 1 is the legacy layout (one block per topic).
    frame_passes: int = 1

    def __post_init__(self):
        if self.layout not in ("topics", "draws"):
            raise ProtocolError("layout must be 'topics' or 'draws'")
        if self.max_batches < 0 or self.batch_topics <= 0 \
                or self.batch_draws <= 0:
            raise ProtocolError("batch configuration must be positive")
        if not 1 <= self.frame_passes <= C.N_WORDINGS:
            raise ProtocolError("frame_passes must be between 1 and N_WORDINGS")


DEFAULT_RESCREEN_CONFIG = RescreenConfig()


@dataclass(frozen=True)
class RescreenBatch:
    """What one batch measures. Everything here is decided by rule."""

    index: int
    families: dict[str, dict[str, Any]]      # kind -> {severities, reserve_picks, deficiency}
    a_grid: bool
    layout: str
    n_topics: int
    draws_per_topic: int
    #: Frame-aware second pass only: per frame, the families that frame's
    #: own screen left undecided (its plan), so the batch's ``families`` ---
    #: the union over frames --- keeps the provenance of who asked.
    by_frame: dict[str, dict[str, Any]] | None = None
    #: Passes over the batch topics (one per frame offset); 1 is legacy.
    frame_passes: int = 1

    @property
    def n_rungs(self) -> int:
        return sum(len(f["severities"]) + len(f["reserve_picks"])
                   for f in self.families.values())

    @property
    def cost_generations(self) -> int:
        per = self.n_topics * self.draws_per_topic * self.frame_passes
        rungs = self.n_rungs + (len(C.TARGET_GRID) if self.a_grid else 0)
        # one unconstrained cell per topic per draw, scored for every rung
        return per * (rungs + 1)


def _entries_for_plan(verdict: Mapping[str, Any], *, threshold: float = 0.5
                      ) -> list[dict[str, Any]]:
    return [{"severity": r["severity"], "iota": r["iota_mean"],
             "eligible": r["p_admissible"] >= threshold}
            for r in verdict["rungs"] if r["iota_mean"] is not None]


def plan_batch(screen: Mapping[str, Any], *, batches_used: Mapping[str, int],
               config: RescreenConfig, table: Sequence[PrescreenRung],
               n_batches: int = 0) -> RescreenBatch | None:
    """The next batch, or None when no family is still undecided or the
    budget is spent.

    ``n_batches`` is how many batches the loop has measured so far; the
    returned batch's ``index`` is that position, so every batch in one run
    carries a distinct index and the topic cut keyed on it stays disjoint.
    The cap ``config.max_batches`` bounds this sequence (three batches at
    most: 72 of the 96 Calibration-A topics), not each family's own count.
    Before 2026-08-30 the index was ``max(batches_used.values())`` and the
    cap was per family: a family whose status returned to RESAMPLE after
    ι_A moved (the A-grid is re-measured every batch) re-entered with the
    same index twice --- pilot r2 generated a fourth batch and then refused
    a fifth on the isolation rule. A family still undecided when the
    sequence is spent is resolved by the at-max rule in ``run_rescreen``.
    """
    if n_batches >= config.max_batches:
        return None
    verdicts = screen["families"]
    iota_a = screen["iota_a"]["iota_a_mean"]
    measured: dict[str, list[int]] = {}
    for r in table:
        measured.setdefault(r.kind, []).append(r.severity)
    families: dict[str, dict[str, Any]] = {}
    for kind in sorted(verdicts):
        v = verdicts[kind]
        if v["status"] != SCREEN_RESAMPLE:
            continue
        if batches_used.get(kind, 0) >= config.max_batches:
            continue
        have = sorted(measured.get(kind, ()))
        plan = regime.expansion_plan_for_family(
            kind, entries=_entries_for_plan(v), measured=have, iota_a=iota_a)
        picks = list(plan["picks"])[:config.reserve_picks_per_batch]
        unexplored = v.get("unexplored_reserve")
        if not picks and unexplored:
            from dci1v8dev.prescreen.extension import reach_picks
            picks = reach_picks(kind, measured=have, sides=[unexplored["side"]],
                                n=config.reserve_picks_per_batch)
        families[kind] = {"severities": have, "reserve_picks": picks,
                          "deficiency": v["deficiency"],
                          "v7_plan_direction": plan["direction"],
                          "p_spectrum": v["p_spectrum"]}
    if not families:
        return None
    return RescreenBatch(
        index=n_batches, families=families, a_grid=config.include_a_grid,
        layout=config.layout,
        n_topics=config.batch_topics if config.layout == "topics"
        else C.N_PRESCREEN,
        draws_per_topic=config.batch_draws, frame_passes=config.frame_passes)


def apply_batch(table: Sequence[PrescreenRung], a_grid: Sequence[ARung],
                new_rungs: Sequence[PrescreenRung],
                new_a: Sequence[ARung] = (), *,
                layout: str | None = None) -> tuple[list[PrescreenRung],
                                                     list[ARung]]:
    """Pool a batch's counts into the table (merge) or add a reserve rung.

    ``layout`` declares the batch's layout (``schema.PrescreenRung.merged``);
    unset, the legacy inference from the counts applies, A's grid included.
    """
    by_label = {r.label: r for r in table}
    for n in new_rungs:
        if n.label in by_label:
            by_label[n.label] = by_label[n.label].merged(n, layout=layout)
        else:
            if n.severity in LADDERS[n.kind] and not n.reserve:
                raise ProtocolError(f"{n.label}: a round-0 rung that the "
                                    "table does not carry cannot appear "
                                    "for the first time in a batch")
            by_label[n.label] = n
    a_by = {a.severity: a for a in a_grid}
    for n in new_a:
        old = a_by.get(n.severity)
        if old is None:
            raise ProtocolError(f"A:{n.severity} was not on the pre-screen")
        as_draws = (layout == "draws" if layout is not None
                    else n.n_topics == old.n_topics)
        if as_draws:
            a_by[n.severity] = ARung(
                severity=n.severity, solo_k=old.solo_k + n.solo_k,
                solo_n=old.solo_n + n.solo_n,
                chance_k=old.chance_k + n.chance_k,
                chance_n=old.chance_n + n.chance_n, n_topics=old.n_topics,
                draws_per_topic=old.draws_per_topic + n.draws_per_topic)
        else:
            a_by[n.severity] = ARung(
                severity=n.severity, solo_k=old.solo_k + n.solo_k,
                solo_n=old.solo_n + n.solo_n,
                chance_k=old.chance_k + n.chance_k,
                chance_n=old.chance_n + n.chance_n,
                n_topics=old.n_topics + n.n_topics,
                draws_per_topic=old.draws_per_topic)
    return ([by_label[k] for k in sorted(by_label)],
            [a_by[k] for k in sorted(a_by)])


def run_rescreen(table: Sequence[PrescreenRung], a_grid: Sequence[ARung], *,
                 screen_config: ScreenConfig, config: RescreenConfig,
                 measure: Callable[[RescreenBatch], tuple[Sequence[PrescreenRung],
                                                          Sequence[ARung]]]
                 ) -> dict[str, Any]:
    """The staged loop, to its registered stopping rule.

    ``measure(batch)`` returns the batch's counts as ``PrescreenRung`` (one
    per measured rung, with the batch's own layout) and ``ARung`` entries. In
    production it generates; in the simulation it draws from the truth; in
    the backtest it carves rows from a held-out split.
    """
    table = list(table)
    a_grid = list(a_grid)
    batches_used: dict[str, int] = {}
    history: list[dict[str, Any]] = []
    screen = screen_families(table, a_grid, config=screen_config)
    history.append({"batch": None,
                    "statuses": dict(screen["statuses"]),
                    "p_spectrum": {k: v["p_spectrum"]
                                   for k, v in screen["families"].items()}})
    total_cost = 0
    n_batches = 0
    while True:
        batch = plan_batch(screen, batches_used=batches_used, config=config,
                           table=table, n_batches=n_batches)
        if batch is None:
            break
        assert batch.index == n_batches
        n_batches += 1
        new_rungs, new_a = measure(batch)
        table, a_grid = apply_batch(table, a_grid, new_rungs, new_a)
        for kind in batch.families:
            batches_used[kind] = batches_used.get(kind, 0) + 1
        total_cost += batch.cost_generations
        screen = screen_families(table, a_grid, config=screen_config)
        history.append({
            "batch": {"index": batch.index,
                      "families": sorted(batch.families),
                      "n_rungs": batch.n_rungs,
                      "reserve_picks": {k: f["reserve_picks"]
                                        for k, f in batch.families.items()
                                        if f["reserve_picks"]},
                      "a_grid": batch.a_grid,
                      "cost_generations": batch.cost_generations},
            "statuses": dict(screen["statuses"]),
            "p_spectrum": {k: v["p_spectrum"]
                           for k, v in screen["families"].items()}})
    # Resolve what the maximum left undecided, by rule.
    resolved: dict[str, str] = {}
    for kind, v in screen["families"].items():
        if v["status"] == SCREEN_RESAMPLE:
            final = (SCREEN_ACCEPT if v["p_spectrum"] >= config.final_accept_at
                     else SCREEN_REJECT)
            v["status"] = final
            v["resolved_by"] = AMBIGUOUS_AT_MAX
            resolved[kind] = final
            if final == SCREEN_ACCEPT and "SPECTRUM_REFERENCE_CANDIDATE" \
                    not in v["labels"]:
                v["labels"].append("SPECTRUM_REFERENCE_CANDIDATE")
    screen["statuses"] = {
        s: sorted(k for k, v in screen["families"].items() if v["status"] == s)
        for s in (SCREEN_ACCEPT, SCREEN_REJECT, SCREEN_RESAMPLE)}
    screen["labels"]["SPECTRUM_REFERENCE_CANDIDATE"] = sorted(
        k for k, v in screen["families"].items()
        if "SPECTRUM_REFERENCE_CANDIDATE" in v["labels"])
    screen["summary"].update({
        "n_accept": len(screen["statuses"][SCREEN_ACCEPT]),
        "n_reject": len(screen["statuses"][SCREEN_REJECT]),
        "n_resample": 0})
    return {"screen": screen, "table": table, "a_grid": a_grid,
            "batches_used": dict(sorted(batches_used.items())),
            "resolved_at_max": resolved, "history": history,
            "cost_generations": total_cost,
            "config": {"max_batches": config.max_batches,
                       "layout": config.layout,
                       "batch_topics": config.batch_topics,
                       "batch_draws": config.batch_draws,
                       "reserve_picks_per_batch":
                           config.reserve_picks_per_batch,
                       "include_a_grid": config.include_a_grid,
                       "final_accept_at": config.final_accept_at}}


def max_cost_generations(config: RescreenConfig, *,
                         n_families: int = len(SELECTABLE_FAMILY_IDS)
                         ) -> dict[str, Any]:
    """The ceiling: every family undecided for every batch, every reserve
    pick taken, A's grid every batch. A statement about the configuration."""
    per_rung = (config.batch_topics if config.layout == "topics"
                else C.N_PRESCREEN) * config.batch_draws * config.frame_passes
    max_rungs_per_family = max(len(LADDERS[k]) + min(
        config.reserve_picks_per_batch * config.max_batches,
        len([q for q in RESERVES[k] if q not in LADDERS[k]]))
        for k in SELECTABLE_FAMILY_IDS)
    per_batch = per_rung * (n_families * max_rungs_per_family
                            + (len(C.TARGET_GRID) if config.include_a_grid
                               else 0) + 1)
    return {"per_rung_per_batch": per_rung,
            "max_rungs_per_family": max_rungs_per_family,
            "max_per_batch": per_batch,
            "max_total": per_batch * config.max_batches,
            "against_screen": C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS
            * (326 + len(C.TARGET_GRID) + len(C.FOCAL_GRID) + 1),
            "against_one_calibrated_rung":
                R.CALIBRATION_GENERATIONS_PER_RUNG}


# ------------------------------------------------------- the frame-aware loop
def union_batch(plans: Mapping[int, "RescreenBatch | None"], *, index: int,
                config: RescreenConfig) -> "RescreenBatch | None":
    """One batch for every frame: the union over the frames' own plans.

    A batch measures every rung on every block, and with the screen laid
    out one pass per frame every block-frame sees the batch's topics, so
    the union costs nothing over the largest frame's plan and every frame
    absorbs the batch as data. Which families are *in* the union is decided
    per frame by that frame's screen; ``by_frame`` records each frame's own
    plan (families, reserve picks, deficiency) so the provenance of the
    union is on the record.
    """
    live = {f: b for f, b in plans.items() if b is not None}
    if not live:
        return None
    families: dict[str, dict[str, Any]] = {}
    for f in sorted(live):
        for kind, fam in live[f].families.items():
            entry = families.setdefault(kind, {
                "severities": sorted(fam["severities"]), "reserve_picks": [],
                "requested_by_frames": []})
            entry["severities"] = sorted(set(entry["severities"])
                                         | set(fam["severities"]))
            entry["reserve_picks"] = sorted(set(entry["reserve_picks"])
                                            | set(fam["reserve_picks"]))
            entry["requested_by_frames"].append(int(f))
    by_frame = {str(f): {"families": {k: {"severities": v["severities"],
                                          "reserve_picks": v["reserve_picks"],
                                          "deficiency": v["deficiency"],
                                          "p_spectrum": v["p_spectrum"]}
                                      for k, v in sorted(b.families.items())}}
                for f, b in sorted(live.items())}
    any_batch = next(iter(live.values()))
    return RescreenBatch(
        index=index, families=families,
        a_grid=any(b.a_grid for b in live.values()),
        layout=any_batch.layout, n_topics=any_batch.n_topics,
        draws_per_topic=any_batch.draws_per_topic, by_frame=by_frame,
        frame_passes=config.frame_passes)


def resolve_at_max(screen: dict[str, Any], *, config: RescreenConfig
                   ) -> dict[str, str]:
    """The registered at-max rule applied to one screen in place: a family
    still in the middle band is accepted iff P >= ``final_accept_at`` and
    recorded ``AMBIGUOUS_AT_MAX``; statuses, labels and summary refreshed."""
    resolved: dict[str, str] = {}
    for kind, v in screen["families"].items():
        if v["status"] == SCREEN_RESAMPLE:
            final = (SCREEN_ACCEPT if v["p_spectrum"] >= config.final_accept_at
                     else SCREEN_REJECT)
            v["status"] = final
            v["resolved_by"] = AMBIGUOUS_AT_MAX
            resolved[kind] = final
            if final == SCREEN_ACCEPT and "SPECTRUM_REFERENCE_CANDIDATE" \
                    not in v["labels"]:
                v["labels"].append("SPECTRUM_REFERENCE_CANDIDATE")
    screen["statuses"] = {
        s: sorted(k for k, v in screen["families"].items() if v["status"] == s)
        for s in (SCREEN_ACCEPT, SCREEN_REJECT, SCREEN_RESAMPLE)}
    screen["labels"]["SPECTRUM_REFERENCE_CANDIDATE"] = sorted(
        k for k, v in screen["families"].items()
        if "SPECTRUM_REFERENCE_CANDIDATE" in v["labels"])
    screen["summary"].update({
        "n_accept": len(screen["statuses"][SCREEN_ACCEPT]),
        "n_reject": len(screen["statuses"][SCREEN_REJECT]),
        "n_resample": 0})
    return resolved


def run_rescreen_by_frame(tables: Mapping[int, tuple[Sequence[PrescreenRung],
                                                       Sequence[ARung]]], *,
                          screen_config: ScreenConfig, config: RescreenConfig,
                          measure: Callable[[RescreenBatch],
                                            Mapping[int, tuple[Sequence[PrescreenRung],
                                                               Sequence[ARung]]]]
                          ) -> dict[str, Any]:
    """The staged loop with one screen per frame and one shared batch.

    ``tables[f]`` is frame f's round-0 table and A-grid; ``measure(batch)``
    returns the batch's counts **per frame** (``{f: (rungs, a_grid)}``),
    each frame's from its own blocks. Every frame is screened on its own
    evidence, plans its own next batch by ``plan_batch`` (the legacy planner,
    unchanged), the frames' plans are unioned into one batch, and every
    frame absorbs the batch's counts on its own blocks. Stopping is the
    registered rule per frame; the sequence cap ``max_batches`` is global.
    A frame still undecided at the maximum is resolved by the posterior
    majority, per frame, and recorded ``AMBIGUOUS_AT_MAX`` per frame.
    """
    frames = sorted(tables)
    table: dict[int, list[PrescreenRung]] = {f: list(tables[f][0]) for f in frames}
    a_grid: dict[int, list[ARung]] = {f: list(tables[f][1]) for f in frames}
    batches_used: dict[int, dict[str, int]] = {f: {} for f in frames}
    screens = {f: screen_families(table[f], a_grid[f], config=screen_config)
               for f in frames}
    history: list[dict[str, Any]] = [{
        "batch": None,
        "statuses": {str(f): dict(screens[f]["statuses"]) for f in frames},
        "p_spectrum": {str(f): {k: v["p_spectrum"]
                                for k, v in screens[f]["families"].items()}
                       for f in frames}}]
    total_cost = 0
    n_batches = 0
    while True:
        plans = {f: plan_batch(screens[f], batches_used=batches_used[f],
                               config=config, table=table[f],
                               n_batches=n_batches) for f in frames}
        batch = union_batch(plans, index=n_batches, config=config)
        if batch is None:
            break
        assert batch.index == n_batches
        n_batches += 1
        counts = measure(batch)
        for f in frames:
            new_rungs, new_a = counts[f]
            table[f], a_grid[f] = apply_batch(table[f], a_grid[f], new_rungs,
                                              new_a, layout=config.layout)
            if plans[f] is not None:
                for kind in plans[f].families:
                    batches_used[f][kind] = batches_used[f].get(kind, 0) + 1
            screens[f] = screen_families(table[f], a_grid[f],
                                         config=screen_config)
        total_cost += batch.cost_generations
        history.append({
            "batch": {"index": batch.index,
                      "families": sorted(batch.families),
                      "n_rungs": batch.n_rungs,
                      "reserve_picks": {k: v["reserve_picks"]
                                        for k, v in batch.families.items()
                                        if v["reserve_picks"]},
                      "requested_by_frames": {
                          k: v["requested_by_frames"]
                          for k, v in batch.families.items()},
                      "a_grid": batch.a_grid,
                      "cost_generations": batch.cost_generations},
            "statuses": {str(f): dict(screens[f]["statuses"]) for f in frames},
            "p_spectrum": {str(f): {k: v["p_spectrum"]
                                    for k, v in screens[f]["families"].items()}
                           for f in frames}})
    resolved = {str(f): resolve_at_max(screens[f], config=config) for f in frames}
    return {"screens": screens,
            "tables": {f: (table[f], a_grid[f]) for f in frames},
            "batches_used": {str(f): dict(sorted(batches_used[f].items()))
                             for f in frames},
            "resolved_at_max": resolved, "history": history,
            "cost_generations": total_cost, "n_batches": n_batches,
            "config": {"max_batches": config.max_batches,
                       "layout": config.layout,
                       "batch_topics": config.batch_topics,
                       "batch_draws": config.batch_draws,
                       "reserve_picks_per_batch":
                           config.reserve_picks_per_batch,
                       "include_a_grid": config.include_a_grid,
                       "final_accept_at": config.final_accept_at,
                       "frame_passes": config.frame_passes,
                       "frame_aware": True}}
