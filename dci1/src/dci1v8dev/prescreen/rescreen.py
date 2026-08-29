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
]

AMBIGUOUS_AT_MAX = "AMBIGUOUS_AT_MAX"


@dataclass(frozen=True)
class RescreenConfig:
    max_batches: int = 3
    layout: str = "topics"           # "topics" | "draws"
    batch_topics: int = 24
    batch_draws: int = 1
    reserve_picks_per_batch: int = 2
    include_a_grid: bool = True
    #: After ``max_batches`` a family still in the middle band is accepted
    #: iff P(spectrum event) >= this. 0.5 is the posterior majority.
    final_accept_at: float = 0.5

    def __post_init__(self):
        if self.layout not in ("topics", "draws"):
            raise ProtocolError("layout must be 'topics' or 'draws'")
        if self.max_batches < 0 or self.batch_topics <= 0 \
                or self.batch_draws <= 0:
            raise ProtocolError("batch configuration must be positive")


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

    @property
    def n_rungs(self) -> int:
        return sum(len(f["severities"]) + len(f["reserve_picks"])
                   for f in self.families.values())

    @property
    def cost_generations(self) -> int:
        per = self.n_topics * self.draws_per_topic
        rungs = self.n_rungs + (len(C.TARGET_GRID) if self.a_grid else 0)
        # one unconstrained cell per topic per draw, scored for every rung
        return per * (rungs + 1)


def _entries_for_plan(verdict: Mapping[str, Any], *, threshold: float = 0.5
                      ) -> list[dict[str, Any]]:
    return [{"severity": r["severity"], "iota": r["iota_mean"],
             "eligible": r["p_admissible"] >= threshold}
            for r in verdict["rungs"] if r["iota_mean"] is not None]


def plan_batch(screen: Mapping[str, Any], *, batches_used: Mapping[str, int],
               config: RescreenConfig, table: Sequence[PrescreenRung]
               ) -> RescreenBatch | None:
    """The next batch, or None when no family is still undecided."""
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
    index = max(batches_used.values(), default=0)
    return RescreenBatch(
        index=index, families=families, a_grid=config.include_a_grid,
        layout=config.layout,
        n_topics=config.batch_topics if config.layout == "topics"
        else C.N_PRESCREEN,
        draws_per_topic=config.batch_draws)


def apply_batch(table: Sequence[PrescreenRung], a_grid: Sequence[ARung],
                new_rungs: Sequence[PrescreenRung],
                new_a: Sequence[ARung] = ()) -> tuple[list[PrescreenRung],
                                                       list[ARung]]:
    """Pool a batch's counts into the table (merge) or add a reserve rung."""
    by_label = {r.label: r for r in table}
    for n in new_rungs:
        if n.label in by_label:
            by_label[n.label] = by_label[n.label].merged(n)
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
        if n.n_topics == old.n_topics:
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
    while True:
        batch = plan_batch(screen, batches_used=batches_used, config=config,
                           table=table)
        if batch is None:
            break
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
                else C.N_PRESCREEN) * config.batch_draws
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
                2 * C.N_CALIBRATION_A * C.M_CAL}
