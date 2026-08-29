"""§18 stages 6-11: Gate 2, Gate 2.5, Gate 3A/3B/3C and Gate 4.

v4r4 had one Gate 3 doing four things at once --- measuring, qualifying,
selecting and deciding what was identified --- and when it failed there was
no record of which of the four had failed. v5 splits them into four stages
with four records, and this module is the four runners plus the two gates
around them.

**The order is the point.** Calibration comes before qualification comes
before selection comes before identification; each reads only its
predecessor's signed record; and none of them ever reads a composed outcome.
§13.11's schema does that structurally: ``load_calibration_table`` refuses a
table that merely *carries* a composed column, before a value is read.

**kappa(R|B) costs no generation.** Gate 2 produces B-solo rows at m*; every
carried candidate is scored on them as an absent instance under §9.1; and
that is §13.6's entire input. Gate 2.5 therefore appears in ``STAGE_SEQUENCE``
and **not** in ``GENERATION_STAGES``, which is the executable form of the
claim.

**Gate 4 records the composed contrast. It selects nothing and terminates
nothing (v7).** There is no function here that takes a Gate-4 reading and
substitutes a frozen backup, and ``assert_no_substitution_path`` is asserted
on this module's own namespace so that adding one is a test failure rather
than a review finding.
"""
from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError

from dci1v7.design.cells import (design_cells,
                                 normalise_arms, slots_for)
from dci1v7.engine import transitions
from dci1v7.engine import parallel
from dci1v7.engine.paths import ModelTree
from dci1v7.analysis.observations import ObservationTable, build_observations
from dci1v7.protocol import constants as C
from dci1v7.protocol import seeds
from dci1v7.run.execute import (cell_rates, generate_and_score,
                                instance_rates, per_topic_compliance,
                                prompt_cell, resolve_generate)
from dci1v7.run.lifecycle import (StageOutcome, TerminalStatus,
                                  protocol_identity, run_stage)
from dci1v7.stages import audit_prefreeze, composed_contrast, composed_probe
from dci1v7.stages import construct_strength, feasibility, interaction
from dci1v7.stages import qualification_gate, regime as regime_stage
from dci1v7.stages.feasibility import (calibration_rows_at,
                                       qualification_at)
from dci1v7.stages.calibration_table import (instructed_compliance,
                                             load_calibration_table)
from dci1v7.topics.bank import (TopicBank, calibration_binding, load_bank)
from dci1v7.verifiers.constraints import (Constraint, assert_selectable,
                                          registered_severities)

__all__ = ["assert_synthetic_only", "assert_calibration_population",
           "focal_constraint",
           "slot_map_from_record",
           "gate2_payload", "run_gate2", "gate2_5_payload", "run_gate2_5",
           "probe_topics", "effective_m_star", "assert_probe_m_star_agrees",
           "gate2_75_payload",
           "run_gate2_75",
           "gate3a_payload", "run_gate3a", "gate3b_payload", "run_gate3b",
           "gate3c_payload", "run_gate3c", "gate4_payload", "run_gate4",
           "composed_table_shape", "assert_composed_table_complete",
           "assert_no_substitution_path"]


class _Block:
    __slots__ = ("block_id", "index", "topic_id")

    def __init__(self, block_id: str, index: int, topic_id: str):
        self.block_id, self.index, self.topic_id = block_id, index, topic_id


class _Cell:
    """A cell over explicit slots, for stages that precede arm admission."""

    __slots__ = ("cell_id", "arm", "block_id", "block_index", "topic_id",
                 "slots", "wording_by_slot", "draws")

    def __init__(self, *, cell_id: str, arm: str, block: _Block,
                 slots: tuple[str, ...], draws: int):
        self.cell_id = cell_id
        self.arm = arm
        self.block_id = block.block_id
        self.block_index = block.index
        self.topic_id = block.topic_id
        self.slots = slots
        if len(slots) == 2:
            first = block.index % C.N_WORDINGS
            second = ((block.index + block.index // C.N_WORDINGS)
                      % C.N_WORDINGS)
            self.wording_by_slot = dict(zip(slots, (first, second)))
        elif slots:
            self.wording_by_slot = {slots[0]: block.index % C.N_WORDINGS}
        else:
            self.wording_by_slot = {}
        self.draws = draws


def _blocks(topics: Sequence[Mapping[str, Any]], prefix: str) -> list[_Block]:
    return [_Block(f"{prefix}-{i:03d}", i, t["topic_id"])
            for i, t in enumerate(topics)]


def _by_id(topics: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {t["topic_id"]: t for t in topics}


def _responder(row: Mapping[str, Any]) -> str:
    words = ["thus", "hence", "though", "whereas", "indeed", "namely",
             "instead", "overall", "reply", "text", "short", "words"]
    seed = sum(ord(ch) for ch in str(row["row_id"]))
    return " ".join(words[(seed + i) % len(words)]
                    for i in range(70)).capitalize() + "."


# ------------------------------------------------------------------ Gate 2

def focal_constraint(m_star: int) -> Constraint:
    """B at m*, whether m* is on the registered grid or §7.2's extension.

    ``Constraint`` refuses an extension severity unless the caller sets
    ``extended``, and §12.3 is the only rule that may. Every reconstruction of
    B from a recorded m* goes through here so that a replication that
    escalated is not refused by its own instrument layer three stages later.
    """
    return Constraint("B", m_star,
                      extended=m_star in C.FOCAL_EXTENSION)


def assert_synthetic_only(tree: ModelTree, name: str, value: Any) -> None:
    """A scale parameter may be passed only in the synthetic namespace.

    Batching and sub-sampling knobs are how an integration harness runs in
    seconds instead of hours. They are also how a registered run silently
    measures a subset of the design it claims. The guard is positive: the
    parameter is admitted only where the study id says the results can never
    be evidence.
    """
    if tree.context.namespace != "synthetic":
        raise ProtocolError(
            f"{name}={value!r} was passed in the {tree.context.namespace!r} "
            "namespace. It reduces the measured design and is admissible "
            "only in the synthetic namespace, whose study id no v6 estimator "
            "or gate accepts")


def assert_calibration_population(priority: Mapping[str, Any],
                                  measured: Sequence[Constraint]) -> None:
    """§12.7: calibration measures the capped population and nothing else.

    Asserted on the mandatory path rather than trusted, because the defect it
    exists for was invisible: the wrong population is not malformed, it is
    merely *larger*, every row in it verifies, and the stage passes. What
    changes is which candidates reach §13.7, Gate 2.5 and reference
    selection.
    """
    expected = len(priority["tier12"]) + len(priority["tier3_measured"])
    if expected != len(measured):
        raise ProtocolError(
            f"§12.7: calibration must measure {expected} rungs "
            f"({len(priority['tier12'])} Tier-1/2 + "
            f"{len(priority['tier3_measured'])} Tier-3 under the cap of "
            f"{priority['tier3_cap']}), not {len(measured)}. "
            f"{len(priority['tier3_dropped_for_budget'])} Tier-3 rungs are "
            "dropped for budget and may not be measured, qualified or "
            "selected")
    if priority["tier3_cap"] < len(priority["tier3_measured"]):
        raise ProtocolError(
            f"§12.7: {len(priority['tier3_measured'])} Tier-3 rungs exceed "
            f"the registered cap of {priority['tier3_cap']}")


def _constraints_from_labels(labels: Sequence[str]) -> list[Constraint]:
    """``"MK1:3"`` -> ``Constraint("MK1", 3)``, from the frozen carried set."""
    out: list[Constraint] = []
    for label in labels:
        kind, _, severity = label.rpartition(":")
        out.append(Constraint(kind, int(severity), reserve=True))
    return out


def gate2_payload(tree: ModelTree, *, producing_commit: str,
                  regime_record: Mapping[str, Any],
                  bank: TopicBank | None = None, device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None,
                  floor: construct_strength.FloorSpec | None = None,
                  topic_limit: int | None = None) -> dict[str, Any]:
    """§18 stage 6: n* and m* on the pooled calibration --- and the candidate
    calibration table every later gate reads.

    Selection is on **raw solo compliance** over the pooled calibration
    topics, which is Calibration-A and Calibration-B together. With
    Calibration-B unauthored the pooled set does not exist, and
    ``calibration_binding`` refuses rather than quietly selecting on half of
    it: an operating point chosen on 96 topics and then compared across two
    96-topic splits would make §13.7's stability rule read its own input.

    **This stage measures the candidates, because the stage after it may
    not.** §18 makes Gate 2.5 a non-generating stage --- that is the whole
    point of §9.1's presence rule and of §13.6 being free --- so every
    quantity Gate 2.5 evaluates has to exist by the end of this one. Two
    passes do it:

    1. the two outcome grids and the unconstrained cell, which fix n* and m*
       and supply every candidate's chance compliance;
    2. one solo cell per carried candidate on the same pooled topics, with B
       at the now-known m* also present as an **absent** instance, which
       supplies each candidate's solo compliance.

    Every carried candidate is scored as absent on the B-solo cells at m*,
    and that --- not a third pass --- is where kappa(R|B) comes from.
    """
    bank = bank if bank is not None else load_bank()
    binding = calibration_binding(bank, split="pooled", draws=C.M_CAL)
    topics = list(bank.topics(C.CALIBRATION_A)) + \
        list(bank.topics(C.CALIBRATION_B))
    if topic_limit is not None:
        # A harness parameter and nothing else. §12.3 selects on the whole
        # pooled calibration, so a registered run that measured a subset
        # would be a different experiment under the same name --- refused
        # here rather than trusted to be passed only by a test.
        assert_synthetic_only(tree, "topic_limit", topic_limit)
        per_split = max(1, topic_limit // 2)
        topics = (list(bank.topics(C.CALIBRATION_A))[:per_split]
                  + list(bank.topics(C.CALIBRATION_B))[:per_split])
    generate = resolve_generate(tree, generate, _responder,
                                where=C.STAGE_GATE2)
    cap = regime_record["selected_cap"]
    # §12.7's calibration population, NOT the screen's carried set. §12.2 is
    # high-recall by construction and carries every structurally admissible
    # rung; §12.7 then says what calibration measures: "all 88 Tier-1 and
    # Tier-2 rungs, which §12.2 rule 2 carries unconditionally, plus at most
    # 24 Tier-3 rungs, ordered by ascending pre-screen |iota - iota_A| when
    # more than 24 are carried". `regime.calibration_priority` computes that
    # and the regime runner records it; this read used `carried_set` instead,
    # so calibration measured all 326 carried rungs and the 214 Tier-3 rungs
    # §12.7 drops for budget reached §13.7's table --- and from there Gate 2.5
    # and reference selection. That is the reference pool, not a cost.
    priority = regime_record["calibration_priority"]
    measured = list(priority["tier12"]) + list(priority["tier3_measured"])
    candidates = _constraints_from_labels(measured)
    non_outcome = [c for c in candidates if c.kind not in ("A", "B")]
    assert_calibration_population(priority, non_outcome)

    grids = {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID)}
    curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    chance_curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    # §34 D17's floor reads kappa_B on the **load-zero** cells only. The
    # registered `chance` rate above averages every row where the severity was
    # absent, which in this grid includes the B-solo cells at the other seven
    # severities --- answers written under a stated length budget, which
    # satisfy a looser budget far more often than an unconstrained answer
    # does. Both are computed and both are recorded; the floor takes the one
    # its threshold was derived from.
    load_zero_curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    n_load_zero: dict[str, int] = {}
    grid_rows: list[dict[str, Any]] = []

    def measure_grid(kind: str, grid: Sequence[int], run_name: str
                     ) -> list[dict[str, Any]]:
        """One severity grid, with its unconstrained cell, on the pooled
        calibration topics. Called again for §7.2's extension when §12.3
        escalates, which is why it is a function and not the loop body."""
        # §7.2's extension {15, 16} is outside B's registered grid by
        # construction, and `Constraint.__post_init__` refuses it unless the
        # caller says so --- *"only this flag does, and only §12.3 sets it"*.
        # A3 gave §12.3's escalation a caller and the branch itself then
        # refused the moment a replication needed it: the synthetic
        # lifecycle's focal curve always found a rung inside the registered
        # grid, so the restored escalation had never once executed.
        extended = any(q in C.FOCAL_EXTENSION for q in grid)
        slot_map = {f"{kind}{q}": Constraint(kind, q, extended=extended)
                    for q in grid}
        cells: list[Any] = []
        for block in _blocks(topics, f"g2{run_name}"):
            cells.append(_Cell(cell_id="unconstrained", arm="unconstrained",
                               block=block, slots=(), draws=C.M_CAL))
            for slot in slot_map:
                cells.append(_Cell(cell_id=f"solo:{slot_map[slot].label}",
                                   arm="solo", block=block, slots=(slot,),
                                   draws=C.M_CAL))
        prompts = [prompt_cell(c, _by_id(topics)[c.topic_id],
                               slot_map=slot_map,
                               topic_split=_split_of(bank, c.topic_id))
                   for c in cells]
        instances = tuple(slot_map.values()) + tuple(
            c for c in non_outcome if c.kind != kind)
        rows = generate_and_score(
            tree.model_key, prompts, stage=C.STAGE_GATE2, cap=cap,
            device=device,
            run_dir=tree.backend_runs(C.STAGE_GATE2) / run_name,
            instances=instances, slot_map=slot_map,
            study_id=tree.context.study_id,
            protocol_identity=protocol_identity(tree, C.STAGE_GATE2),
            generate=generate)
        grid_rows.extend(rows)
        for q in grid:
            rates = instance_rates(rows, kind=kind, severity=q,
                                   unconstrained_arm="unconstrained")
            curves[kind][q] = rates["solo"]
            chance_curves[kind][q] = rates["chance"]
            load_zero_curves[kind][q] = rates["chance_unconstrained"]
            n_load_zero[kind] = rates["n_topics_unconstrained"]
        return rows

    for kind, grid in grids.items():
        measure_grid(kind, grid, f"grid-{kind}")

    target = regime_stage.select_target(curves["A"])
    focal = regime_stage.select_focal(curves["B"])
    # §7.2 / §12.3's escalation, which had no caller. `select_focal` measures
    # the registered grid first and asks for {15, 16} only when it finds no
    # eligible severity there, or when the selection sits at the grid top and
    # the bracketing rule therefore cannot be met. It signals that by
    # returning `extension_required` with `selected` None --- and this runner
    # read only `selected`, so it raised FOCAL_RANGE_EXHAUSTED instead of
    # escalating. A replication that §12.3 says should extend its grid was
    # recorded terminal, which is a false scientific outcome, and it made the
    # focal extension R14 objected to --- and D17's floor was designed
    # around --- unreachable in the registered lifecycle.
    extension_measured = False
    if focal.get("extension_required"):
        measure_grid("B", list(C.FOCAL_EXTENSION), "grid-B-extension")
        extension_measured = True
        focal = regime_stage.select_focal(
            {q: curves["B"][q] for q in C.FOCAL_GRID},
            {q: curves["B"][q] for q in C.FOCAL_EXTENSION})
    # §12.3 registers THREE diagnoses for a selection that finds nothing and
    # they are different facts. GRID_RESOLUTION_INSUFFICIENT --- the curve
    # passes through the band between two adjacent registered severities
    # without either landing in it --- takes precedence, because it is a
    # statement about the registered ladder rather than about the model. It
    # had no production caller at all.
    resolution = {
        "A": regime_stage.grid_resolution(curves["A"], band=C.TARGET_BAND,
                                          grid=C.TARGET_GRID),
        "B": regime_stage.grid_resolution(
            curves["B"], band=C.FOCAL_BAND,
            grid=(list(C.FOCAL_GRID) + list(C.FOCAL_EXTENSION)
                  if extension_measured else list(C.FOCAL_GRID))),
    }
    for kind, result, status in (("A", target, "TARGET_RANGE_EXHAUSTED"),
                                 ("B", focal, "FOCAL_RANGE_EXHAUSTED")):
        if result.get("selected") is not None:
            continue
        if resolution[kind]["insufficient"]:
            raise TerminalStatus(
                "GRID_RESOLUTION_INSUFFICIENT", gate=C.STAGE_GATE2,
                criterion="§12.3: two adjacent registered severities lie on "
                          "opposite sides of a whole band, so the grid "
                          "resolves nothing inside it",
                observed={"constraint": kind, "curve": result.get("curve"),
                          "straddling_pairs":
                              resolution[kind]["straddling_pairs"]},
                strongest_permissible_statement=C.TERMINAL_SENTENCE)
        raise TerminalStatus(
            result.get("terminal_status", status), gate=C.STAGE_GATE2,
            criterion="§12.3: an eligible severity inside the registered "
                      "band",
            observed={"curve": result.get("curve")},
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    m_star, n_star = focal["selected"], target["selected"]

    # ------------------------------------------------- §12.4 regime adequacy
    # "A replication proceeds only when..." --- three conditions, on the
    # pooled calibration, at the selected severities. The record carried the
    # two thresholds under the name `adequacy` and evaluated neither
    # condition, so REGIME_NOT_FOUND had no production caller and a
    # replication whose B was degenerate or vacuous proceeded to selection.
    a_rates = instance_rates(grid_rows, kind="A", severity=n_star)
    b_rates = instance_rates(grid_rows, kind="B", severity=m_star)
    adequacy = regime_stage.regime_adequacy(
        solo_a=a_rates["solo"], solo_b=b_rates["solo"],
        vacuity_b=b_rates["vacuity"],
        graded_shares={
            "A": {"graded_share_above": a_rates["graded_share_above"],
                  "graded_share_below": a_rates["graded_share_below"]},
            "B": {"graded_share_above": b_rates["graded_share_above"],
                  "graded_share_below": b_rates["graded_share_below"]}})
    if not adequacy["adequate"]:
        raise TerminalStatus(
            "REGIME_NOT_FOUND", gate=C.STAGE_GATE2,
            criterion="§12.4: the three regime-adequacy conditions on the "
                      "pooled calibration topics",
            observed=adequacy["failures"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)

    # The topic is the independent unit kappa_B was estimated over --- §13.7's
    # topics, never the four draws within one --- and it is what the Wilson
    # interval beside the verdict is computed from. The floor still refuses on
    # the point.
    strength = construct_strength.assert_construct_floor(
        m_star, chance_compliance_at_m_star=load_zero_curves["B"][m_star],
        curve=load_zero_curves["B"], solo_curve=curves["B"],
        n_topics=n_load_zero["B"], floor=floor)
    if strength.get("selection_refused"):
        raise TerminalStatus(
            strength["status"], gate=C.STAGE_GATE2,
            criterion="§34 D17's registered construct floor",
            observed=strength["reason"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)

    # ---------------- §12.4 and §34 D17 across the eligible severities
    # §12.3's eligible set is a band test on the solo curve and nothing more.
    # §12.4 and §34 D17 are evaluated at m* alone and terminate the
    # replication when either fails, so every *other* eligible severity is one
    # no admissibility rule has been applied to. Applying both here, to every
    # eligible severity, from curves already measured, costs no generation and
    # gives the record a prospective statement of which severities would have
    # been admissible at all. m* is in the set by construction: the two checks
    # above terminated the replication if it were not, and P3.1 asserts the
    # probed m* is in it.
    #
    # kappa(R|B) is then built for each of them off the B-solo cells pass 1
    # already scored every candidate as absent on. It costs no generation, and
    # computing it here --- before Gate 2.5 qualifies anything and before the
    # probe observes a single composed cell --- is what keeps the qualified
    # pool independent of a composed outcome (§30).
    eligible = sorted({int(q) for q in (focal.get("eligible") or ())}
                      | {int(m_star)})
    admissibility = _focal_admissibility(
        eligible, a_rates=a_rates, grid_rows=grid_rows,
        load_zero_curve=load_zero_curves["B"], solo_curve=curves["B"],
        n_topics=n_load_zero["B"], floor=floor)
    admissible = sorted(int(q) for q, v in admissibility.items()
                        if v["admissible"])
    if m_star not in admissible:                          # pragma: no cover
        raise ProtocolError(
            f"§12.4/§34 D17: m*={m_star} passed both rules above and the "
            "per-severity evaluation disagrees; the two must be the same rule")
    kappa_by_severity = _kappa_columns(
        grid_rows, non_outcome, severities=admissible,
        model_key=tree.model_key)
    # The order in which Gate 2.75 may try operating points, frozen here ---
    # before the probe generates a row --- so that trying more than one is a
    # registered procedure and not a search over what looked promising.
    search_order = feasibility.operating_point_order(
        m_star=m_star, admissible=admissible, curve=curves["B"])

    # ------------------------------ pass 2: the candidates' solo compliance
    # m* can come from §7.2's extension, which is outside the registered
    # grid: every later reconstruction of B has to say so or the instrument
    # layer refuses it. A replication that escalated could not have built its
    # own candidate pass, let alone its slot map.
    b_star = focal_constraint(m_star)
    candidate_rows: list[dict[str, Any]] = []
    if non_outcome:
        slot_map = {f"S{i}": c for i, c in enumerate(non_outcome)}
        cells = []
        for block in _blocks(topics, "g2cand"):
            for slot, rung in slot_map.items():
                cells.append(_Cell(cell_id=f"solo:{rung.label}", arm="solo",
                                   block=block, slots=(slot,),
                                   draws=C.M_CAL))
        prompts = [prompt_cell(c, _by_id(topics)[c.topic_id],
                               slot_map=slot_map,
                               topic_split=_split_of(bank, c.topic_id))
                   for c in cells]
        candidate_rows = generate_and_score(
            tree.model_key, prompts, stage=C.STAGE_GATE2, cap=cap,
            device=device,
            run_dir=tree.backend_runs(C.STAGE_GATE2) / "candidates",
            instances=tuple(non_outcome) + (b_star,), slot_map=slot_map,
            study_id=tree.context.study_id,
            protocol_identity=protocol_identity(tree, C.STAGE_GATE2),
            generate=generate)

    b_solo_rows = [r for r in grid_rows
                   if r["cell_id"] == f"solo:{b_star.label}"]
    # §12.2 measured every one of these candidates too. Joining the two
    # measurements of one instrument is free and had never been done.
    prescreen_by_candidate = {
        row["candidate"]: row
        for row in (regime_record.get("difficulty_table") or ())
        if not row.get("is_outcome")}
    tables = _calibration_rows(
        tree.model_key, non_outcome, m_star=m_star,
        solo_rows=candidate_rows, chance_rows=grid_rows,
        b_solo_rows=b_solo_rows,
        kappa_column=kappa_by_severity[str(m_star)],
        prescreen=prescreen_by_candidate)

    statuses = sorted(set(target.get("identification_statuses", [])
                          + focal.get("identification_statuses", [])
                          + strength.get("statuses", [])))
    return {
        "stage": C.STAGE_GATE2,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2],
        "outcome": "PASS",
        "inputs": {"regime": {"stage": C.STAGE_REGIME,
                              "carried": regime_record.get("n_carried")}},
        "producing_commit": producing_commit,
        "n_star": n_star, "m_star": m_star,
        "target_selection": target, "focal_selection": focal,
        # The severities Gate 2.75 may move B to: eligible under §12.3 **and**
        # adequate under §12.4 **and** past §34 D17's floor, each evaluated at
        # that severity rather than at m*. The kappa(R|B) column for each is
        # recorded with it, so the pool at every candidate operating point is
        # signed before the probe observes one composed cell (§30).
        "focal_admissible": admissible,
        "focal_admissibility": admissibility,
        "kappa_under_b_by_severity": kappa_by_severity,
        # Frozen before Gate 2.75 observes one composed cell.
        "operating_point_search_order": search_order,
        "operating_point_search_rule":
            "§12.3's own preference on Gate 2's measured solo B curve --- "
            "ascending |solo - FOCAL_AIM|, ties to the smaller severity --- "
            "over `focal_admissible`, with m* first. It is the registered "
            "focal rule and not a second rule, and it is fixed before any "
            "composed outcome exists",
        # §7.2: whether {15, 16} were measured on this replication. §12.3
        # measures them only on escalation, so this is model-adaptive and
        # §6.1 lists it as such.
        "focal_extension_measured": extension_measured,
        "focal_grid_measured": (list(C.FOCAL_GRID) + list(C.FOCAL_EXTENSION)
                                if extension_measured
                                else list(C.FOCAL_GRID)),
        # §12.7's calibration population, and what it excluded.
        "calibration_population": {
            "tier12": len(priority["tier12"]),
            "tier3_measured": len(priority["tier3_measured"]),
            "tier3_cap": priority["tier3_cap"],
            "tier3_dropped_for_budget":
                list(priority["tier3_dropped_for_budget"]),
            "n_measured": len(non_outcome),
            "carried_by_the_screen": len(regime_record["carried_set"]),
            "rule": "§12.7: every Tier-1/2 rung plus at most 24 Tier-3, "
                    "ordered by ascending pre-screen |iota - iota_A|; the "
                    "screen's carried set is high-recall and larger"},
        "solo_curves": {k: {str(q): v for q, v in c.items()}
                        for k, c in curves.items()},
        "chance_curves": {k: {str(q): v for q, v in c.items()}
                          for k, c in chance_curves.items()},
        # The load-zero curve, recorded separately and named, so a reader can
        # see which denominator §34 D17's floor was applied to.
        "load_zero_chance_curves": {k: {str(q): v for q, v in c.items()}
                                    for k, c in load_zero_curves.items()},
        "n_topics_load_zero": dict(n_load_zero),
        "iota_a": instructed_compliance(curves["A"][n_star],
                                        chance_curves["A"][n_star]),
        "solo_compliance_a": curves["A"][n_star],
        # §3.2's L1 identification gate is "the outcome constraint has solo
        # headroom", and `emit_l1` takes it as a parameter. The analysis
        # passed the constant True, so the gate was asserted rather than
        # measured; B's realised solo compliance at m* is the quantity it is
        # a statement about, and nothing carried it past this record.
        "solo_compliance_b": curves["B"][m_star],
        "iota_a_by_split": _iota_a_by_split(grid_rows, n_star),
        "solo_a_by_split": _solo_a_by_split(grid_rows, n_star),
        # The between-topic variance of A at n* and of B at every measured
        # severity. Gate 2.75 projects a cell to §13.14's sample size and
        # needs it; recording it here is why that stage can read `solo:A` and
        # `solo:B` instead of drawing them again.
        "solo_topic_moments": {
            "A": _solo_topic_moments(grid_rows, kind="A",
                                     severities=(n_star,)),
            "B": _solo_topic_moments(grid_rows, kind="B",
                                     severities=tuple(curves["B"]))},
        # v7: the per-topic solo vectors themselves, keyed by topic id, for
        # A at n* and B at every measured severity. Gate 2.75 forms the
        # paired contrasts D(B<-A) and D(A<-B) inside the topic and needs
        # the vector, not the moments.
        "solo_topic_values": {
            "A": _solo_topic_values(grid_rows, kind="A",
                                    severities=(n_star,)),
            "B": _solo_topic_values(grid_rows, kind="B",
                                    severities=tuple(curves["B"]))},
        "a_per_topic_by_split": _a_per_topic_by_split(grid_rows, n_star),
        "construct_strength": strength,
        "calibration_binding": binding,
        # The topics this stage actually measured, as distinct from the
        # split's full membership. A later stage may reuse a Gate-2 cell only
        # when its own topic set is this one, and that is checked against
        # this field rather than against the bank.
        "calibration_topic_ids": sorted(t["topic_id"] for t in topics),
        "calibration_rows": tables,
        # Two recorded diagnostics, both free and both read by nothing.
        "kappa_b_under_candidate": _kappa_b_under_candidate(
            candidate_rows, m_star=m_star, model_key=tree.model_key),
        "prescreen_to_calibration": _prescreen_to_calibration(
            tables["pooled"]),
        "n_candidates_measured": len(non_outcome),
        "kappa_under_b_source":
            "the B-solo cells at m*, on which every carried candidate was "
            "scored as absent under §9.1; no generation of its own (§13.6)",
        "adequacy": adequacy,
        "grid_resolution": resolution,
        "identification_statuses": statuses,
        "selected_on": C.SECONDARY_DIFFICULTY_COORDINATE,
    }


def _kappa_under_b(b_solo_rows: Sequence[Mapping[str, Any]],
                   candidate: Constraint, *, split: str | None) -> tuple:
    """kappa(R|B) and the per-topic count, from B-solo rows where R is absent."""
    per_topic: dict[str, list[float]] = {}
    for row in b_solo_rows:
        if split is not None and row.get("topic_split") != split:
            continue
        for score in row["scores"]:
            if (score["kind"] == candidate.kind
                    and score["severity"] == candidate.severity
                    and not score["present"]):
                per_topic.setdefault(row["topic_id"], []).append(
                    float(score["passed"]))
    if not per_topic:
        return None, 0, 0
    topics = sorted(per_topic)
    value = sum(sum(v) / len(v) for v in
                (per_topic[t] for t in topics)) / len(topics)
    draws = max(len(per_topic[t]) for t in topics)
    return value, len(topics), draws


#: §13.2 / §25: the cell kappa_c is measured in.
UNCONSTRAINED_ARM = "unconstrained"


def _reduced(row: Mapping[str, Any], *, label: str, present: bool
             ) -> dict[str, Any] | None:
    """The row as `cell_rates`, `per_topic_compliance` and `_kappa_under_b`
    read it, keeping only the verdicts of one instance in one presence.

    Those readers touch `topic_split`, `arm`, `topic_id`, `word_count`,
    `truncated` and, of `scores`, the entries whose label and presence
    match; a row reduced to exactly that is the same row to them, in the
    same order, and it is small enough to send to a worker by pickle. None
    when the row carries no such verdict, which the readers would have
    skipped.
    """
    scores = [s for s in row["scores"]
              if f"{s['kind']}:{s['severity']}" == label
              and bool(s["present"]) == present]
    if not scores:
        return None
    return {"topic_split": row.get("topic_split"), "arm": row.get("arm"),
            "topic_id": row["topic_id"], "word_count": row["word_count"],
            "truncated": row["truncated"],
            "scores": [{"kind": s["kind"], "severity": s["severity"],
                        "present": s["present"], "passed": s["passed"],
                        "vacuous_pass": s["vacuous_pass"],
                        "graded": s["graded"]} for s in scores]}


def _n_in_split(rows: Sequence[Mapping[str, Any]], split: str | None) -> int:
    return len(rows) if split is None else sum(
        1 for r in rows if r.get("topic_split") == split)


def _calibration_entry(task: Mapping[str, Any]) -> dict[str, Any] | None:
    """One §13.11 row: a candidate on a split. The serial loop body.

    A pure function of its task. Returns None where the serial loop
    `continue`d: a candidate the split holds no solo row for, or ---
    preserving the reference implementation's rule exactly --- one that
    every solo row of the split states, so that `instance_rates`'s absent
    scan found nothing.
    """
    split, candidate = task["split"], task["candidate"]
    restrict = None if split == "pooled" else split
    if task["n_present"] == 0 or task["n_present"] == task["n_solo"]:
        return None
    try:
        solo = cell_rates(task["present_rows"], kind=candidate.kind,
                          severity=candidate.severity, present=True,
                          split=restrict)
    except ProtocolError:                                # pragma: no cover
        return None
    # §13.2: kappa_c "measured in the unconstrained cell of the same topic
    # set at the same M under the same prompt". Every candidate is scored as
    # an absent instance on every unconstrained cell of the grid runs, so
    # the quantity exists on the rows; a split with no such cell is a
    # broken run and refuses rather than recording a chance nobody measured.
    try:
        chance = cell_rates(task["unconstrained_rows"], kind=candidate.kind,
                            severity=candidate.severity, present=False,
                            split=restrict, arm=UNCONSTRAINED_ARM)
    except ProtocolError as absent:
        raise ProtocolError(
            f"§13.2: kappa_c for {candidate.label} on the {split} split has "
            "no unconstrained cell to be measured in; the calibration table "
            "records no chance it did not measure") from absent
    screened = task["screened"] or {}
    # ``precomputed`` is ``_kappa_columns``' entry for this m*: the same
    # quantity from one pass over the rows instead of one pass per
    # candidate. The per-candidate form stays as the reference
    # implementation and a unit test asserts the two agree exactly.
    precomputed = task["precomputed"]
    if precomputed is not None:
        kappa_b = precomputed["kappa_under_b"]
        source = precomputed["kappa_under_b_source"]
        n_topics_b, n_draws_b = source["n_topics"], source["n_draws"]
    elif task["kappa_column_given"]:
        kappa_b, n_topics_b, n_draws_b = None, 0, 0
    else:
        kappa_b, n_topics_b, n_draws_b = _kappa_under_b(
            task["b_solo_rows"], candidate, split=restrict)
    entry: dict[str, Any] = {
        "kind": candidate.kind, "severity": candidate.severity,
        "split": split, "model_key": task["model_key"],
        "solo_compliance": solo["compliance"],
        "chance_compliance": chance["compliance"],
        "solo_vacuity": solo["vacuity"],
        "n_topics": solo["n_topics"], "n_draws": C.M_CAL,
        "median_words": solo["median_words"],
        "graded_mean": solo["graded_mean"],
        # §13.7 resamples topics, so the vector travels with the
        # mean. A row with an empty vector makes the equivalence test
        # report that it could not be run, and an untested
        # equivalence is not a satisfied one --- which is how this
        # missing producer surfaced.
        "per_topic_solo": list(per_topic_compliance(
            task["present_rows"], kind=candidate.kind,
            severity=candidate.severity, split=restrict)),
    }
    if screened.get("solo") is not None:
        entry["prescreen_solo_compliance"] = screened["solo"]
    if screened.get("chance") is not None:
        entry["prescreen_chance_compliance"] = screened["chance"]
    if kappa_b is not None:
        entry["kappa_under_b"] = kappa_b
        # Written as a mapping, not as the dataclass: the table goes
        # onto a signed JSON record and §13.11 requires the source to
        # travel with the value. `load_calibration_table` rebuilds it
        # and validates it, on a fresh table and a reloaded one alike.
        entry["kappa_under_b_source"] = {
            "load": 1, "present": [f"B:{task['m_star']}"],
            "candidate": candidate.label, "model_key": task["model_key"],
            "m_star": task["m_star"], "split": split,
            "n_topics": n_topics_b, "n_draws": n_draws_b}
    return entry


def _calibration_rows(model_key: str, candidates: Sequence[Constraint], *,
                      m_star: int, solo_rows: Sequence[Mapping[str, Any]],
                      chance_rows: Sequence[Mapping[str, Any]],
                      b_solo_rows: Sequence[Mapping[str, Any]],
                      kappa_column: Mapping[str, Any] | None = None,
                      prescreen: Mapping[str, Mapping[str, Any]] | None = None
                      ) -> dict[str, list[dict[str, Any]]]:
    """The §13.11 closed-schema table, per split and pooled.

    Built here because this is the stage that generated the rows. A table
    assembled by a caller is a table nobody can trace to a generation, and
    §13.11's whole point is that the selection input is auditable.

    ``prescreen`` joins §12.2's measurement of **the same instrument**.
    ``CalibrationRow`` has carried ``prescreen_solo_compliance`` and
    ``prescreen_chance_compliance`` since v5 and nothing ever filled them, so
    the two measurements of one candidate --- 24 topics at one draw, and 192
    at four --- have never been joined on any replication. They are the paired
    form of the basis change §12.6 is certified on and reference selection
    works on, and joining them costs nothing: both were measured.

    **No admission rule reads a pre-screen quantity.** §12.7's Tier-3
    *ordering* does, and that is all; v4r4's pre-screen distance caliper is
    deleted. Filling the columns therefore changes no verdict, which is why it
    can be done without amending §13.

    **2026-08-29, two changes.** (1) ``chance_compliance`` is §13.2's
    kappa_c, measured on the grid runs' unconstrained cells, where every
    candidate is scored as an absent instance. Until this date it was
    obtained through ``instance_rates(chance_rows, ...)``, whose *solo* scan
    runs first and finds no row in which a non-outcome candidate is stated,
    so the call raised and the column was written as ``0.0`` for every
    candidate of every replication of v5, v6 and v7: iota(R) equalled raw
    solo compliance, §13.4's chance ceiling never fired, and §13.6's
    displacement was measured against zero. (2) The table is built one
    (split, candidate) unit at a time in a process pool, each unit given
    the rows that carry its candidate's verdicts, reduced to those verdicts
    (`_reduced`) --- the same rows in the same order to every reader, so
    every other column is the byte the serial scan produced
    (``tests_v7/test_parallel.py``, and checked on the 2026-08-28
    rehearsal's 86,016 stored rows against the previous implementation).
    """
    splits = (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")
    unconstrained = [r for r in chance_rows
                     if r.get("arm") == UNCONSTRAINED_ARM]
    n_solo = {s: _n_in_split(solo_rows, None if s == "pooled" else s)
              for s in splits}
    # One pass per candidate over each row set, in the parent: the rows
    # that state the candidate, the unconstrained rows where it is absent,
    # and --- for the per-candidate kappa(R|B) fallback --- the B-solo rows
    # where it is absent.
    tasks: list[dict[str, Any]] = []
    for split in splits:
        restrict = None if split == "pooled" else split
        for candidate in candidates:
            label = candidate.label
            present_rows = [r for r in (
                _reduced(row, label=label, present=True) for row in solo_rows)
                if r is not None]
            precomputed = (None if kappa_column is None
                           else (kappa_column.get(split) or {}).get(label))
            tasks.append({
                "split": split, "candidate": candidate,
                "n_present": _n_in_split(present_rows, restrict),
                "n_solo": n_solo[split],
                "present_rows": present_rows,
                "unconstrained_rows": [r for r in (
                    _reduced(row, label=label, present=False)
                    for row in unconstrained) if r is not None],
                "b_solo_rows": ([] if kappa_column is not None else [
                    r for r in (_reduced(row, label=label, present=False)
                                for row in b_solo_rows) if r is not None]),
                "precomputed": precomputed,
                "kappa_column_given": kappa_column is not None,
                "screened": (prescreen or {}).get(label) or {},
                "m_star": m_star, "model_key": model_key})
    entries = parallel.pool_map(_calibration_entry, tasks)
    out: dict[str, list[dict[str, Any]]] = {s: [] for s in splits}
    for task, entry in zip(tasks, entries):
        if entry is not None:
            out[task["split"]].append(entry)
    return out


def _prescreen_to_calibration(rows: Sequence[Mapping[str, Any]]
                              ) -> dict[str, Any]:
    """How far §12.2's measurement of an instrument moved by §12.3's.

    **Paired by instrument.** Both numbers describe the same candidate on the
    same model; what differs is 24 topics at one draw against 192 at four.
    That is the basis §12.6 is certified on against the basis reference
    selection works on, and until these columns were joined no replication
    could report it for a single candidate, let alone summarise it.

    Reported and read by nothing. The point is that a reader --- and the next
    protocol version --- can see whether the screen's coordinate predicts the
    one the study matches on, instead of assuming it.
    """
    moved: list[dict[str, Any]] = []
    for row in rows:
        pre_solo = row.get("prescreen_solo_compliance")
        pre_chance = row.get("prescreen_chance_compliance")
        if pre_solo is None or pre_chance is None:
            continue
        if (pre_chance >= C.CHANCE_DEGENERACY_MAX
                or row["chance_compliance"] >= C.CHANCE_DEGENERACY_MAX):
            continue
        moved.append({
            "candidate": f"{row['kind']}:{row['severity']}",
            "d_solo": row["solo_compliance"] - pre_solo,
            "d_iota": (instructed_compliance(row["solo_compliance"],
                                             row["chance_compliance"])
                       - instructed_compliance(pre_solo, pre_chance))})
    def _summary(key: str) -> dict[str, Any]:
        values = [abs(e[key]) for e in moved]
        signed = [e[key] for e in moved]
        return {"n": len(values),
                "mean_abs": (sum(values) / len(values)) if values else None,
                "max_abs": max(values) if values else None,
                "min_signed": min(signed) if signed else None,
                "max_signed": max(signed) if signed else None}
    return {
        "paired_by": "the same candidate on the same model, measured by "
                     "§12.2 on 24 pre-screen topics at one draw and by §12.3 "
                     "on 192 calibration topics at four",
        "costs_no_generation": True,
        "read_by": [],
        "n_paired": len(moved),
        "solo": _summary("d_solo"), "iota": _summary("d_iota"),
        "per_candidate": moved,
    }


def _kappa_b_under_candidate(candidate_rows: Sequence[Mapping[str, Any]],
                             *, m_star: int, model_key: str
                             ) -> dict[str, Any]:
    """B's compliance at m* while **R** is the instructed constraint.

    Pass 2 already scores ``B:m*`` as an *absent* instance on every
    candidate-solo cell --- ``instances=tuple(non_outcome) + (b_star,)`` --- so
    this is arithmetic over rows that exist, on the same 192 topics and the
    same four draws as everything else in §13.11's table. It is the load-1
    mirror of §13.6's kappa(R|B), per candidate.

    **It is a recorded diagnostic and it is deliberately kept off the
    calibration table.** §13.11's schema is closed and a new column would be
    refused there; that refusal is the point. No admission rule, no caliper
    and no selection reads this, and putting it on the Gate-2 record rather
    than in the selection input is what keeps that true by construction.
    """
    per_candidate: dict[str, dict[str, list[float]]] = {}
    for row in candidate_rows:
        cell = row.get("cell_id", "")
        if not cell.startswith("solo:"):
            continue
        label = cell.partition(":")[2]
        for score in row["scores"]:
            if (score["kind"] == "B" and score["severity"] == m_star
                    and not score["present"]):
                per_candidate.setdefault(label, {}).setdefault(
                    row["topic_id"], []).append(float(score["passed"]))
    out: dict[str, Any] = {}
    for label, per_topic in sorted(per_candidate.items()):
        topics = sorted(per_topic)
        out[label] = {
            "kappa_b_under_candidate": sum(
                sum(per_topic[t]) / len(per_topic[t])
                for t in topics) / len(topics),
            "n_topics": len(topics),
            "n_draws": max(len(per_topic[t]) for t in topics)}
    return {
        "m_star": m_star, "model_key": model_key, "by_candidate": out,
        "quantity": "B at m* scored as an ABSENT instance on each "
                    "candidate's own solo cell (§9.1's presence rule)",
        "costs_no_generation": True,
        "read_by": [],
        "not_on_the_calibration_table":
            "§13.11's schema is closed and would refuse this column. It is a "
            "diagnostic; no admission rule, caliper or selection reads it",
    }


def _kappa_columns(grid_rows: Sequence[Mapping[str, Any]],
                   candidates: Sequence[Constraint], *,
                   severities: Sequence[int], model_key: str
                   ) -> dict[str, dict[str, dict[str, Any]]]:
    """kappa(R|B) at every admissible operating point.

    §13.6 reads the interaction quantity off the **B-solo cell at the
    operating point**. Gate 2 already scores every carried candidate as an
    *absent* instance on every B-solo cell of the focal grid, so the column at
    another admissible severity is arithmetic over rows that already exist and
    costs no generation at all.

    The study runs at the frozen m* and reads that column. The others are
    computed because they are free and because they let §13.6's quantity at m*
    be read against its neighbours; and computing every one of them **here**,
    before Gate 2.5 qualifies and before any composed cell exists, is what
    keeps §30 intact: no qualified pool anywhere on the record can have been
    shaped by a composed outcome.
    """
    wanted = {(c.kind, c.severity): c.label for c in candidates}
    splits = (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for severity in severities:
        cell_id = f"solo:{focal_constraint(severity).label}"
        # One pass over the B-solo rows, bucketing by (split, candidate,
        # topic). `_kappa_under_b` rescans every row for every candidate,
        # which is the same arithmetic and quadratic in the pool; at six
        # admissible severities and three splits that is the difference
        # between seconds and minutes. The two agree exactly and a test
        # asserts it against the m* column `_calibration_rows` builds.
        acc: dict[tuple[str, str], dict[str, list[float]]] = {}
        for row in grid_rows:
            if row["cell_id"] != cell_id:
                continue
            row_split = row.get("topic_split")
            for score in row["scores"]:
                if score["present"]:
                    continue
                label = wanted.get((score["kind"], score["severity"]))
                if label is None:
                    continue
                passed = float(score["passed"])
                for split in dict.fromkeys(("pooled", row_split)):
                    if split not in splits:
                        continue
                    acc.setdefault((split, label), {}).setdefault(
                        row["topic_id"], []).append(passed)
        per_split: dict[str, dict[str, Any]] = {s: {} for s in splits}
        for (split, label), per_topic in acc.items():
            topics = sorted(per_topic)
            value = sum(sum(per_topic[t]) / len(per_topic[t])
                        for t in topics) / len(topics)
            per_split[split][label] = {
                "kappa_under_b": value,
                "kappa_under_b_source": {
                    "load": 1, "present": [f"B:{severity}"],
                    "candidate": label, "model_key": model_key,
                    "m_star": severity, "split": split,
                    "n_topics": len(topics),
                    "n_draws": max(len(per_topic[t]) for t in topics)}}
        out[str(severity)] = per_split
    return out


def _focal_admissibility(severities: Sequence[int], *,
                         a_rates: Mapping[str, Any],
                         grid_rows: Sequence[Mapping[str, Any]],
                         load_zero_curve: Mapping[int, float],
                         solo_curve: Mapping[int, float], n_topics: int,
                         floor: construct_strength.FloorSpec | None
                         ) -> dict[str, Any]:
    """§12.4 and §34 D17, at every eligible severity.

    Gate 2 evaluates both **at m\\***, and terminates the replication when
    either fails. An *eligible* severity is only one whose solo compliance sat
    inside §12.3's band: it has been through neither §12.4's regime adequacy
    nor D17's construct floor, so `eligible` on its own overstates what Gate 2
    established.

    Nothing here relaxes a rule and nothing here selects. m* is §12.3's choice,
    it is frozen at this stage, and it still terminates the replication when
    it fails either rule. This records which of the *other* eligible
    severities would also have satisfied §12.4 and D17 --- read by P3.1 as the
    set the probed m* must belong to, and by Gate 2.5 as the set it qualifies
    over. It generates nothing and reads only curves Gate 2 has already
    measured.
    """
    verdicts: dict[str, Any] = {}
    for severity in severities:
        rates = instance_rates(grid_rows, kind="B", severity=severity)
        adequacy = regime_stage.regime_adequacy(
            solo_a=a_rates["solo"], solo_b=rates["solo"],
            vacuity_b=rates["vacuity"],
            graded_shares={
                "A": {"graded_share_above": a_rates["graded_share_above"],
                      "graded_share_below": a_rates["graded_share_below"]},
                "B": {"graded_share_above": rates["graded_share_above"],
                      "graded_share_below": rates["graded_share_below"]}})
        strength = construct_strength.assert_construct_floor(
            severity, chance_compliance_at_m_star=load_zero_curve[severity],
            curve=load_zero_curve, solo_curve=solo_curve,
            n_topics=n_topics, floor=floor)
        refused = bool(strength.get("selection_refused"))
        verdicts[str(severity)] = {
            "severity": severity,
            "adequate": bool(adequacy["adequate"]),
            "adequacy_failures": list(adequacy.get("failures") or ()),
            "construct_floor_refused": refused,
            "construct_strength": strength,
            "admissible": bool(adequacy["adequate"]) and not refused,
        }
    return verdicts


# `calibration_rows_at` and `qualification_at` live in
# `stages/feasibility.py`, with the criterion they feed. They are imported
# above because this module reads them; they are deliberately NOT re-exported
# from here, so that a caller wanting a record reader takes it from the seam
# that owns it rather than from whichever runner happened to import it first.


def _iota_a_by_split(rows: Sequence[Mapping[str, Any]], n_star: int
                     ) -> dict[str, float]:
    out: dict[str, float] = {}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        try:
            rates = instance_rates(rows, kind="A", severity=n_star,
                                   split=split)
        except ProtocolError:
            continue
        out[split] = instructed_compliance(rates["solo"], rates["chance"])
    return out



def _solo_topic_moments(rows: Sequence[Mapping[str, Any]], *, kind: str,
                        severities: Sequence[int]) -> dict[str, Any]:
    """Per severity: the solo compliance, and the variance **between topics**.

    The mean was already recorded; the variance was not, and it is the
    quantity ``GATE_2_75_COMPOSED_PROBE`` needs to project a cell forward to
    §13.14's sample size. Recording it here rather than re-measuring it there
    is what lets the probe read ``solo:A`` and ``solo:B`` off this record
    instead of drawing a second sample of two numbers the design is already
    fixed on --- and the per-split breakdown is the same paired contrast §34
    D20's measured-transfer branch reads, because Calibration-A comes from
    §6.2's seeded cut and §34 D3's Calibration-B is newly authored.

    The topic is the sampling unit: draws inside a topic are correlated, so
    the variance of a topic's own draw-mean is what a resample of topics
    moves, and dividing raw draw variance by the row count would understate
    it. ``per_topic_compliance`` already returns exactly that vector.
    """
    out: dict[str, Any] = {}
    for severity in sorted({int(q) for q in severities}):
        vector = per_topic_compliance(rows, kind=kind, severity=severity)
        if not vector:
            continue
        entry: dict[str, Any] = {
            "compliance": sum(vector) / len(vector),
            "s2_topic": (statistics.variance(vector) if len(vector) > 1
                         else 0.0),
            "n_topics": len(vector)}
        by_split: dict[str, Any] = {}
        for split in (C.CALIBRATION_A, C.CALIBRATION_B):
            half = per_topic_compliance(rows, kind=kind, severity=severity,
                                        split=split)
            if half:
                by_split[split] = {"compliance": sum(half) / len(half),
                                   "n_topics": len(half)}
        entry["by_split"] = by_split
        if len(by_split) == 2:
            # At the entry level, not inside `by_split`, because that is where
            # `_entry_moments` puts it and `_measured_split_transfer` reads a
            # table built from both. Two shapes for one quantity would make
            # the reused Gate-2 cells silently absent from §34 D20's record.
            entry["a_minus_b"] = (by_split[C.CALIBRATION_A]["compliance"]
                                  - by_split[C.CALIBRATION_B]["compliance"])
        out[str(severity)] = entry
    return out


def _solo_topic_values(rows: Sequence[Mapping[str, Any]], *, kind: str,
                       severities: Sequence[int]) -> dict[str, dict[str, float]]:
    """Per severity: topic id -> that topic's own draw-mean solo compliance.

    The vector ``_solo_topic_moments`` summarises, keyed so a later stage can
    pair it with a composed cell measured on the same topics (v7).
    """
    out: dict[str, dict[str, float]] = {}
    for severity in sorted({int(q) for q in severities}):
        per_topic: dict[str, list[float]] = {}
        label = f"{kind}:{severity}"
        for row in rows:
            for score in row["scores"]:
                if (f"{score['kind']}:{score['severity']}" == label
                        and bool(score["present"])):
                    per_topic.setdefault(row["topic_id"], []).append(
                        float(score["passed"]))
        if per_topic:
            out[str(severity)] = {t: sum(v) / len(v)
                                  for t, v in sorted(per_topic.items())}
    return out


def _solo_a_by_split(rows: Sequence[Mapping[str, Any]], n_star: int
                     ) -> dict[str, float]:
    out: dict[str, float] = {}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        try:
            out[split] = instance_rates(rows, kind="A", severity=n_star,
                                        split=split)["solo"]
        except ProtocolError:
            continue
    return out


def _a_per_topic_by_split(rows: Sequence[Mapping[str, Any]], n_star: int
                          ) -> dict[str, Any]:
    """A's own per-topic solo vector and chance rate on each split.

    §13.7 subjects iota_A to the same equivalence rule as every candidate,
    and ``stability.assert_iota_a_stable`` implements it. It resamples
    topics, so it needs A's per-topic vector --- which no record carried, so
    the one rule that pins the reference point every §13.8 distance is
    measured from could not run.
    """
    out: dict[str, Any] = {"per_topic": {}, "chance": {}}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        try:
            rates = instance_rates(rows, kind="A", severity=n_star,
                                   split=split)
        except ProtocolError:
            continue
        out["per_topic"][split] = list(per_topic_compliance(
            rows, kind="A", severity=n_star, split=split))
        out["chance"][split] = rates["chance"]
    return out


def _split_of(bank: TopicBank, topic_id: str) -> str:
    for name in C.TOPIC_SETS:
        if any(t["topic_id"] == topic_id for t in bank.sets[name]):
            return name
    raise ProtocolError(f"{topic_id!r} is in no registered set")


def run_gate2(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              device: int = 0,
              generate: Callable[..., dict[str, Any]] | None = None,
              floor: construct_strength.FloorSpec | None = None,
              topic_limit: int | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    # Gate 2's predecessor is Gate 1; the cap and the carried set are on the
    # REGIME record, two stages back. A runner that read `previous` for them
    # would read Gate 1's payload and find neither --- which is precisely the
    # reader-with-no-producer defect run/contracts.py exists to catch, and
    # which it caught here.
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    return run_stage(
        tree, C.STAGE_GATE2,
        compute=lambda _previous: gate2_payload(
            tree, producing_commit=commit, regime_record=regime, bank=bank,
            device=device, generate=generate, floor=floor,
            topic_limit=topic_limit),
        producing_commit=commit, environment_digest=environment_digest)


# ---------------------------------------------------------------- Gate 2.5

def gate2_5_payload(tree: ModelTree, *, producing_commit: str,
                    gate2_record: Mapping[str, Any],
                    split: str = "pooled") -> dict[str, Any]:
    """§18 stage 7: kappa(R|B) at m*, then §13.1's first six components.

    The input is **Gate 2's own record**, not a table a caller assembled: the
    rows are loaded through ``load_calibration_table``, which refuses a
    composed field before reading a value and validates every kappa(R|B)
    against the source that produced it.

    **This stage generates nothing** and it is deliberately absent from
    ``GENERATION_STAGES``: kappa(R|B) is a verdict for an absent candidate on
    the B-solo rows Gate 2 already produced.
    """
    m_star = gate2_record["m_star"]
    # §13.6's quantity is a property of the pair (R, B at the operating
    # point). This stage generates nothing, so qualifying at **every**
    # admissible severity costs arithmetic and no rows, and every pool on the
    # record is fixed before the probe observes anything (§30). The study runs
    # at the frozen m*; the rest of the column is a signed prospective record
    # and no selection rule reads it.
    admissible = sorted({int(q) for q in
                         (gate2_record.get("focal_admissible") or ())}
                        | {int(m_star)})
    by_severity: dict[str, Any] = {}
    for severity in admissible:
        raw_q = calibration_rows_at(gate2_record, m_star=severity, split=split)
        rows_q = load_calibration_table(raw_q, model_key=tree.model_key,
                                        m_star=severity, split=split)
        qualified_q = qualification_gate.qualify_candidates(
            rows_q, model_key=tree.model_key, m_star=severity,
            producing_commit=producing_commit)
        interaction_rows_q = [
            {"candidate": r.label, "kappa": r.chance_compliance,
             "iota": instructed_compliance(r.solo_compliance,
                                           r.chance_compliance),
             "kappa_under_b": r.kappa_under_b,
             "source": r.kappa_under_b_source}
            for r in rows_q]
        by_severity[str(severity)] = {
            "m_star": severity,
            "qualification": qualified_q,
            "qualified_pool": qualified_q["qualified_pool"],
            "qualified_families": qualified_q["qualified_families"],
            "n_qualified": qualified_q["n_qualified"],
            "earliest_failing_components": {
                v["candidate"]: v["first_failing_component"]
                for v in qualified_q["verdicts"]},
            "interaction": interaction.measure_interaction(
                interaction_rows_q, model_key=tree.model_key,
                m_star=severity, split=split),
        }
    at_m_star = by_severity[str(m_star)]
    qualified = at_m_star["qualification"]
    report = at_m_star["interaction"]
    # §12.3's recorded order, restricted to the severities that can meet
    # §13.15's five-family minimum. Doing it **here** is what keeps the probe
    # blind to the pool: the probe reads a severity, never a family name, and
    # every quantity behind the restriction was signed before it ran.
    #
    # A necessary condition, exactly evaluated, and already computed --- Gate
    # 2.5 runs the full V(R) at every admissible severity because it generates
    # nothing. Re-deriving it per candidate would re-bootstrap §13.7 over
    # identical per-topic vectors with identical seeds.
    frozen = gate2_record.get("operating_point_search_order")
    if not frozen:
        raise ProtocolError(
            "§12.3: Gate 2 recorded no `operating_point_search_order`, so "
            "there is no recorded preference for this stage to restrict. "
            "Constructing one here would build after Gate 2.5's own "
            "measurements what §12.3 is required to have written before them")
    search_order = [int(q) for q in frozen]
    op_support = feasibility.qualified_family_support(
        {"qualification_by_severity": by_severity}, severities=search_order)
    order, order_reason = feasibility.restricted_operating_point_order(
        search_order, op_support, m_star=m_star)
    return {
        "stage": C.STAGE_GATE2_5,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2_5],
        "outcome": "PASS",
        "inputs": {"gate2": {"stage": C.STAGE_GATE2, "m_star": m_star}},
        "producing_commit": producing_commit,
        "m_star": m_star,
        # The whole block, and then the three things later stages actually
        # read, at the top level under the names the stage module uses. A
        # nested `qualified_pool["qualified"]` was read by three later
        # runners and written by none --- found by the synthetic lifecycle.
        "qualification": qualified,
        "qualified_pool": qualified["qualified_pool"],
        "qualified_families": qualified["qualified_families"],
        "n_qualified": qualified["n_qualified"],
        # The same three at every admissible severity, recorded. The study
        # runs at Gate 2's frozen m* and the top-level fields carry it; the
        # per-severity column is a signed prospective statement of where a
        # reference set could have existed and is read by no selection rule.
        "qualification_by_severity": by_severity,
        "qualified_at_severities": admissible,
        # §12.3's preference over the admissible severities, narrowed to
        # where §13.15 can be met. Severities only; no family name crosses
        # this boundary. Gate 2.75 reads the head, to check that this stage
        # and Gate 2 agree about the frozen m*, and nothing reads the tail.
        "operating_point_order": order,
        "operating_point_order_reason": order_reason,
        "operating_point_support": op_support,
        "operating_point_order_generates_nothing": True,
        "earliest_failing_components": {
            v["candidate"]: v["first_failing_component"]
            for v in qualified["verdicts"]},
        "interaction": report,
        "generates_rows": False,
        "generation_free_statement":
            "kappa(R|B) is a verdict for an absent candidate on the B-solo "
            "rows Gate 2 already produced; §9.1's presence rule is what makes "
            "it free and §13.6 registers its only use",
        "components": list(qualification_gate.QUALIFICATION_COMPONENTS),
    }


def run_gate2_5(tree: ModelTree, *, producing_commit: str | None = None,
                environment_digest: str = "",
                split: str = "pooled") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_GATE2_5,
        compute=lambda previous: gate2_5_payload(
            tree, producing_commit=commit, gate2_record=previous,
            split=split),
        producing_commit=commit, environment_digest=environment_digest)


# --------------------------------------------------------------- Gate 2.75

def probe_topics(bank: TopicBank, split: str) -> tuple[list[Any], str]:
    """The topic set §34 D20's closure names, and the label rows carry.

    ``calibration_pooled`` and ``calibration_both_subsplits`` read §6.2's 192
    calibration topics --- Calibration-A and Calibration-B together, the same
    pooled set Gate 2 selects m* over, so the probe costs no reserved topics
    and is measured where m* was chosen. ``composed`` reads the reserved
    composed set, which §6.2 spends once; taking it here is what couples
    §34 D20 to D21.

    The label rows carry is the registered split name, never "calibration":
    ``pooled`` is what §13.7 calls the union and what ``calibration_binding``
    already stamps.
    """
    if split == "composed":
        return list(bank.topics("composed")), "composed"
    topics = (list(bank.topics(C.CALIBRATION_A))
              + list(bank.topics(C.CALIBRATION_B)))
    return topics, "pooled"


def effective_m_star(tree: ModelTree) -> int:
    """The operating point every stage after Gate 2.75 uses.

    **It is Gate 2's, and this checks that Gate 2.75 left it alone.** §12.3
    selects m* from B's solo curve at ``GATE_2_FOCAL_CALIBRATION`` and the
    selection is frozen there; Gate 2.75 measures the composed contrast at that
    severity and either passes or terminates the replication. So the
    authoritative value is Gate 2's, and the probe record is read only to
    refuse a disagreement --- the consuming half of the invariant whose
    producing half is ``composed_probe.assert_m_star_unmoved``.

    Both records are required rather than defaulted: a missing probe record
    at a stage that runs after it is a lifecycle fault, and falling back to
    Gate 2 alone would make the check vacuous exactly when it matters.
    """
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    probe = transitions.read_stage_record(tree, C.STAGE_GATE2_75)
    return assert_probe_m_star_agrees(probe, gate2_m_star=int(gate2["m_star"]))


def assert_probe_m_star_agrees(probe_record: Mapping[str, Any], *,
                               gate2_m_star: int) -> int:
    """The consuming half of the frozen-m\\* invariant.

    Separated from ``effective_m_star`` so that it can be driven directly ---
    a guard whose only caller reads two real records is a guard no scenario
    can exercise against a record that actually disagrees.
    """
    if int(probe_record["m_star"]) != int(gate2_m_star):
        raise ProtocolError(
            f"{C.STAGE_GATE2} froze m* = {gate2_m_star} and the "
            f"{C.STAGE_GATE2_75} record says {probe_record['m_star']}. m* is "
            "selected once, by §12.3's focal rule on the solo B curve, and "
            "no later stage may move it; a probe record that disagrees is a "
            "defect and this refuses rather than following it")
    return int(gate2_m_star)


def _entry_moments(rows: Sequence[Mapping[str, Any]], *, cell_id: str,
                   constraint: Constraint) -> dict[str, Any]:
    """One cell x slot entry: its compliance, its between-topic variance, and
    its value on each calibration sub-split.

    The **topic** is the sampling unit --- draws inside one topic are
    correlated --- so the variance recorded is the variance of a topic's own
    draw-mean, which is what a resample of topics moves.

    The per-sub-split values are §34 D20's measured transfer. They are not a
    diagnostic: Calibration-A comes from §6.2's seeded per-area cut and is
    exchangeable with the composed set §13.14 audits on, while §34 D3's
    Calibration-B is newly authored and is not, so their difference is the
    only part of the calibration-to-composed movement that is **not**
    sampling. Recording it per entry is what makes the residual allowance
    checkable at the moment it is applied instead of assumed from a table.
    """
    per_topic: dict[str, list[float]] = {}
    per_split: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        if row["cell_id"] != cell_id:
            continue
        for score in row["scores"]:
            if (score["present"] and score["kind"] == constraint.kind
                    and score["severity"] == constraint.severity):
                per_topic.setdefault(row["topic_id"], []).append(
                    float(score["passed"]))
                split = row.get("topic_split") or "unlabelled"
                (per_split.setdefault(split, {})
                 .setdefault(row["topic_id"], []).append(
                     float(score["passed"])))
    values = [sum(v) / len(v) for v in per_topic.values()]
    if not values:
        raise ProtocolError(
            f"{cell_id}: no scored observation of {constraint.label} was "
            "produced, so this entry has no measurement and cannot be "
            "judged. A zero would be indistinguishable from a real floor")
    subsplits = {name: {"compliance": sum(sum(v) / len(v) for v in per.values())
                                     / len(per),
                        "n_topics": len(per)}
                 for name, per in sorted(per_split.items()) if per}
    entry = {"compliance": sum(values) / len(values),
             "s2_topic": statistics.variance(values) if len(values) > 1
                         else 0.0,
             "n_topics": len(values),
             # The per-topic vector itself, keyed by topic id, so a paired
             # contrast can be formed inside the topic (v7).
             "per_topic": {t: sum(v) / len(v)
                           for t, v in sorted(per_topic.items())},
             "by_split": subsplits}
    a, b = C.CALIBRATION_A, C.CALIBRATION_B
    if a in subsplits and b in subsplits:
        entry["a_minus_b"] = (subsplits[a]["compliance"]
                              - subsplits[b]["compliance"])
    return entry


def _standin_ladders(tree: ModelTree, kinds: Sequence[str], *, bank: TopicBank,
                     cap: int, device: int, generate: Callable[..., Any],
                     topics: Sequence[Any]) -> dict[str, dict[int, float]]:
    """Each stand-in's solo curve, on §12.5's pre-screen topics at one draw.

    The cheap instrument, deliberately: this curve decides only **which
    severity** a stand-in is probed at, and every quantity a verdict reads is
    measured on the probe split at ``M_CAL``. §12.2 chooses B's grid the same
    way and for the same reason.

    A stand-in is never carried, so it is not in the regime screen's table and
    §12.6's coverage conditions never see it. Measuring it here keeps it out
    of every population a registered rule counts.
    """
    cells: list[_Cell] = []
    instances: list[Constraint] = []
    for kind in kinds:
        for q in registered_severities(kind):
            rung = Constraint(kind, q)
            instances.append(rung)
            for block in _blocks(topics, f"g275-ladder-{kind}"):
                cells.append(_Cell(cell_id=f"solo:{rung.label}", arm="solo",
                                   block=block, slots=(rung.label,),
                                   draws=C.LADDER_SCREEN_DRAWS))
    slot_map = {c.label: c for c in instances}
    prompts = [prompt_cell(cell, _by_id(topics)[cell.topic_id],
                           slot_map=slot_map, topic_split="prescreen")
               for cell in cells]
    rows = generate_and_score(
        tree.model_key, prompts, stage=C.STAGE_GATE2_75, cap=cap,
        device=device, run_dir=tree.backend_runs(C.STAGE_GATE2_75) / "ladder",
        instances=tuple(instances), slot_map=slot_map,
        study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, C.STAGE_GATE2_75),
        generate=generate)
    curves: dict[str, dict[int, float]] = {}
    for rung in instances:
        passes = [float(s["passed"]) for r in rows
                  if r["cell_id"] == f"solo:{rung.label}"
                  for s in r["scores"]
                  if s["present"] and s["kind"] == rung.kind
                  and s["severity"] == rung.severity]
        if passes:
            curves.setdefault(rung.kind, {})[rung.severity] = (
                sum(passes) / len(passes))
    return curves



def _measured_split_transfer(probed: Mapping[int, Mapping[str, Mapping[str, Any]]]
                             ) -> dict[str, Any]:
    """§34 D20's measured transfer, per entry and in summary.

    §6.2 cuts Calibration-A, the composed set and the confirmatory set from
    one seeded per-area shuffle, so those are exchangeable and the difference
    between them is sampling. §34 D3's Calibration-B is newly authored and is
    not part of that cut, and it supplies half the topics a pooled probe
    measures on --- so a pooled estimate of a confirmatory-set value carries
    **half** of whatever instrument-specific offset the authored half
    introduces. This block is that quantity measured on **this**
    replication, beside the contrasts it qualifies.

    It **gates nothing** and, in v7, parameterises nothing: the projected
    interval it once fed a residual term to no longer exists. It is recorded
    so a reader of a probe contrast can see how far the two halves it pools
    disagree.
    """
    rows: list[dict[str, Any]] = []
    for severity, table in sorted(probed.items()):
        for cell_id, entry in sorted(table.items()):
            if cell_id == "unconstrained":
                continue
            for slot, measurement in sorted(entry.items()):
                if "a_minus_b" not in measurement:
                    continue
                halves = measurement["by_split"]
                rows.append({
                    "severity": severity, "cell": cell_id, "slot": slot,
                    "compliance": measurement["compliance"],
                    "calibration_a": halves[C.CALIBRATION_A]["compliance"],
                    "calibration_b": halves[C.CALIBRATION_B]["compliance"],
                    "a_minus_b": measurement["a_minus_b"],
                    "carried_by_the_pooled_estimate":
                        measurement["a_minus_b"] / 2.0})
    carried = [abs(r["carried_by_the_pooled_estimate"]) for r in rows]
    summary: dict[str, Any] = {
        "n_entries": len(rows),
        "read_by": [],
        "gates_nothing": True,
        "parameterises_nothing": True,
        "why_it_gates_nothing":
            "a rule that re-tuned anything from the transfer it was "
            "measuring would fit a design constant to the replication it is "
            "about to judge; and v7 has no projected-interval verdict for a "
            "residual term to enter",
        "entries": rows,
    }
    if rows:
        signed = [r["carried_by_the_pooled_estimate"] for r in rows]
        summary.update({
            "mean_absolute_carried_offset": sum(carried) / len(carried),
            "max_absolute_carried_offset": max(carried),
            "mean_carried_offset": sum(signed) / len(signed),
            "sd_of_the_carried_offset":
                statistics.stdev(signed) if len(signed) > 1
                else 0.0})
    return summary


def gate2_75_payload(tree: ModelTree, *, producing_commit: str,
                     gate2_5_record: Mapping[str, Any],
                     bank: TopicBank | None = None, cap: int,
                     device: int = 0,
                     standins: Sequence[Constraint] | None = None,
                     block_limit: int | None = None,
                     resamples: int = C.BOOTSTRAP_RESAMPLES,
                     generate: Callable[..., dict[str, Any]] | None = None
                     ) -> dict[str, Any]:
    """§18 stage 8: the composed contrast at m*, **before** any reference
    exists, recorded (v7).

    Reads Gate 2 for the frozen m*, for n*, iota_A, the admissible severity
    set m* has to belong to, and the per-topic solo vectors the paired
    contrasts need. Reads the Gate 2.5 record for its outcome and for the
    head of ``operating_point_order`` --- **one severity, checked against
    Gate 2's m***. The probe still must not know which candidates qualified,
    and it does not: the family names stay on Gate 2.5's record and no name
    crosses this boundary.

    **It measures one operating point and records what it finds.** m* is
    §12.3's choice and it is frozen at Gate 2; this stage has one outcome,
    PASS. There is no severity loop, no admissible-severity search, no
    branch that writes an m* different from the one it read, and no
    terminal status (v7 A1).

    Every probed cell is A, B or a ``probe_only`` stand-in. No reference
    exists at this point in the sequence and ``assert_probe_reads_no_reference``
    is asserted on the stage module, so the two guarantees are independent.
    """
    if gate2_5_record.get("outcome") != "PASS":
        raise ProtocolError(
            f"{C.STAGE_GATE2_75} runs after a passing Gate 2.5 and the "
            f"record says {gate2_5_record.get('outcome')!r}")
    composed_probe.assert_probe_reads_no_reference()
    bank = bank if bank is not None else load_bank()
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    m_star = int(gate2["m_star"])
    n_star = int(gate2["n_star"])
    iota_a = float(gate2["iota_a"])
    focal = gate2["focal_selection"]
    eligible = [int(q) for q in (focal.get("eligible") or ())]

    split = composed_probe.probe_split()          # §34 D20, refuses while open
    topics, topic_label = probe_topics(bank, split)
    generate = resolve_generate(tree, generate, _responder,
                                where=C.STAGE_GATE2_75)
    if block_limit is not None:
        # The same seam `confirmatory_run.licensed_design` uses, and admitted
        # on the same terms: a probe measured on a subset is a different
        # measurement under the same name, so it is refused anywhere the
        # study id says a row could be evidence.
        assert_synthetic_only(tree, "block_limit", block_limit)
        topics = topics[:block_limit]

    ladders: dict[str, Any] = {}
    operating: dict[str, Any] = {}
    if standins is None:
        kinds = composed_probe.standins()         # §34 D24, refuses while open
        ladder_topics = list(bank.topics("prescreen"))
        if block_limit is not None:
            ladder_topics = ladder_topics[:block_limit]
        ladders = _standin_ladders(
            tree, kinds, bank=bank, cap=cap, device=device, generate=generate,
            topics=ladder_topics)
        operating = composed_probe.standin_operating_points(
            ladders, iota_a=iota_a)
        # A17. An unplaceable stand-in keeps its slot --- the cell ids stay
        # comparable across replications --- and is given its ladder's best
        # severity purely so the slot has an instrument to name. Nothing is
        # generated for it.
        standin_rungs = tuple(
            Constraint(kind, int(operating[kind]["severity"]
                                 if operating[kind].get("placed")
                                 else operating[kind]["best_severity"]))
            for kind in kinds)
    else:
        assert_synthetic_only(tree, "standins",
                              [c.label for c in standins])
        standin_rungs = tuple(standins)
    for rung in standin_rungs:
        if rung.kind not in composed_probe.PROBE_ONLY_KINDS():
            raise ProtocolError(
                f"{rung.label} is not a registered probe-only stand-in. Every "
                "probed companion must be one, or a probed cell could be a "
                "B+R cell by instrument identity")
    slots = composed_probe.probe_slots(len(standin_rungs))
    slot_map: dict[str, Constraint] = dict(zip(slots, standin_rungs))
    coverage = composed_probe.assert_probe_covers_gate4_classes(slots)
    unplaceable_kinds = composed_probe.unplaceable_standins(operating)
    unplaceable_slots = [slot for slot, rung in slot_map.items()
                         if rung.kind in unplaceable_kinds]

    # A13: **m\* and nothing else.** Gate 2.5's `operating_point_order` is
    # read for its head --- where Gate 2 and Gate 2.5 record their agreement
    # about the operating point --- and for nothing else.
    admissible = [int(q) for q in (gate2.get("focal_admissible") or ())]
    frozen = gate2_5_record.get("operating_point_order")
    if not frozen:
        raise ProtocolError(
            "P3.1: Gate 2.5 recorded no `operating_point_order`. Its head is "
            "where Gate 2.5 records which operating point it qualified at, "
            "and a record without one cannot be checked against Gate 2's m*")
    if int(frozen[0]) != m_star:
        raise ProtocolError(
            f"P3.1: Gate 2.5's order starts at {frozen[0]} and Gate 2 froze "
            f"m* = {m_star}. The two gates disagree about the operating "
            "point; repaired silently, that would measure the composed "
            "contrast at a severity §12.3 did not select")
    order = [m_star]
    composed_probe.assert_probe_severities_are_admissible(order, gate2)

    shape = composed_probe.probe_cell_types(slots)
    # The unconstrained cell and the two determinate solo cells are
    # quantities Gate 2 measured, per topic. When this stage runs on the same
    # topics at the same draws they are the *same case*, so it reads them
    # rather than drawing a second sample --- which also makes every paired
    # contrast a difference from the number the design was fixed on.
    shared = composed_probe.shared_cell_verdict(
        gate2_topic_ids=gate2.get("calibration_topic_ids") or (),
        probe_topic_ids=[t["topic_id"] for t in topics],
        gate2_draws=C.M_CAL, probe_draws=C.M_CAL)
    moments = gate2.get("solo_topic_moments") or {}
    values = gate2.get("solo_topic_values") or {}
    if shared["shared"] and not (moments.get("A") and moments.get("B")
                                 and values.get("A") and values.get("B")):
        raise ProtocolError(
            "the Gate-2 record carries no `solo_topic_moments` or no "
            "`solo_topic_values`, so `solo:A` and `solo:B` could be reused "
            "as means but not as the per-topic vectors a paired contrast "
            "needs. Reusing half a measurement is refused")
    reused = (set(composed_probe.SHARED_WITH_GATE2)
              if shared["shared"] else set())
    unmeasured = composed_probe.unmeasured_probe_cells(shape,
                                                       unplaceable_slots)
    generated_shape = [entry for entry in shape
                       if entry[0] not in reused and entry[0] not in unmeasured]
    probed: dict[int, dict[str, dict[str, Any]]] = {}
    n_rows = 0
    for severity in order:
        b_rung = focal_constraint(severity)
        bound = {**slot_map, "B": b_rung, "A": Constraint("A", n_star)}
        cells = [_Cell(cell_id=cell_id, arm=arm, block=block, slots=cell_slots,
                       draws=C.M_CAL)
                 for block in _blocks(topics, f"g275-m{severity}")
                 for cell_id, arm, cell_slots in generated_shape]
        prompts = [prompt_cell(cell, _by_id(topics)[cell.topic_id],
                               slot_map=bound, topic_split=topic_label)
                   for cell in cells]
        rows = generate_and_score(
            tree.model_key, prompts, stage=C.STAGE_GATE2_75, cap=cap,
            device=device,
            run_dir=(tree.backend_runs(C.STAGE_GATE2_75) / f"m{severity}"),
            instances=tuple(dict.fromkeys(bound.values())), slot_map=bound,
            study_id=tree.context.study_id,
            protocol_identity=protocol_identity(tree, C.STAGE_GATE2_75),
            generate=generate)
        n_rows += len(rows)
        table: dict[str, dict[str, Any]] = {}
        if shared["shared"]:
            # Read, not re-measured, with the per-topic vector alongside.
            table["unconstrained"] = {"unconstrained": {
                "compliance": float(len(topics)), "s2_topic": 0.0,
                "n_topics": len(topics)}}
            table["solo:A"] = {"A": {**moments["A"][str(n_star)],
                                     "per_topic": dict(
                                         values["A"][str(n_star)])}}
            table["solo:B"] = {"B": {**moments["B"][str(severity)],
                                     "per_topic": dict(
                                         values["B"][str(severity)])}}
        for cell_id, _arm, cell_slots in generated_shape:
            if not cell_slots:
                table[cell_id] = {"unconstrained": {
                    "compliance": float(sum(1 for r in rows
                                            if r["cell_id"] == cell_id)),
                    "s2_topic": 0.0, "n_topics": len(topics)}}
                continue
            table[cell_id] = {
                slot: _entry_moments(rows, cell_id=cell_id,
                                     constraint=bound[slot])
                for slot in cell_slots}
        probed[severity] = table

    disposition = composed_probe.probe_disposition(
        m_star=m_star, probed=probed,
        seed=seeds.bootstrap_seed("gate2_75", tree.model_key),
        resamples=resamples)
    composed_probe.assert_m_star_unmoved(disposition, gate2_m_star=m_star)
    record = disposition["verdict"]
    return {
        "stage": C.STAGE_GATE2_75,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2_75],
        "producing_commit": producing_commit,
        "inputs": {
            "gate2": {"stage": C.STAGE_GATE2, "m_star": m_star,
                      "n_star": n_star, "iota_a": iota_a,
                      "eligible": sorted(eligible),
                      "admissible": sorted(admissible),
                      "read": ["m_star", "n_star", "iota_a",
                               "focal_selection.eligible",
                               "focal_admissible",
                               "solo_topic_moments", "solo_topic_values"]},
            "gate2_5": {"stage": C.STAGE_GATE2_5,
                        "read": ["outcome", "operating_point_order"],
                        "outcome": gate2_5_record["outcome"],
                        "operating_point_order_head": int(frozen[0]),
                        "why": "the probe must not know which candidates "
                               "qualified. It reads the stage's outcome and "
                               "one severity, which it checks against Gate "
                               "2's frozen m*; no family name crosses this "
                               "boundary"}},
        "m_star_in": m_star,
        "m_star": disposition["m_star_out"],
        "m_star_is_frozen_at": C.STAGE_GATE2,
        "m_star_is_unchanged": disposition["m_star_out"] == m_star,
        # Kept, always false, and checked by `assert_m_star_unmoved`. §33's
        # name scan requires this record to state whether m* moved.
        "reselected": disposition["reselected"],
        "disposition": disposition,
        # The v7 record proper: every contrast, its boundary readings and its
        # projected precision. Read by no rule.
        "composed_contrast": record,
        "contrast_statuses": record["contrast_statuses"],
        "topic_split": topic_label,
        "topics": sorted(t["topic_id"] for t in topics),
        "draws": C.M_CAL,
        "rows": n_rows,
        "resamples": resamples,
        "probe_slots": list(slots),
        "standins": [c.label for c in standin_rungs],
        "standin_operating_points": operating,
        "standin_ladders": {k: {str(q): v for q, v in sorted(c.items())}
                            for k, c in sorted(ladders.items())},
        "standin_placement_rule":
            "§13.8 matches a reference's iota(R) to iota_A, so a stand-in is "
            "placed at the severity of its own solo ladder nearest Gate 2's "
            "iota_A inside §13.4's band. iota_A does not depend on m*, so "
            "the companion a probed cell carries is fixed by a quantity the "
            "operating point cannot move",
        "probe_cell_types": [cell_id for cell_id, _a, _s in shape],
        "probe_cell_types_generated": [cell_id for cell_id, _a, _s
                                       in generated_shape],
        "standin_placement": {
            kind: {"status": entry.get("status"),
                   "placed": bool(entry.get("placed")),
                   "severity": entry.get("severity"),
                   "reason": entry.get("reason"),
                   "best_severity": entry.get("best_severity"),
                   "best_compliance": entry.get("best_compliance"),
                   "curve": entry.get("curve")}
            for kind, entry in sorted(operating.items())},
        "unplaceable_standins": list(unplaceable_kinds),
        "unplaceable_standin_slots": sorted(unplaceable_slots),
        "n_unplaceable_standins": len(unplaceable_kinds),
        "cells_not_measured": unmeasured,
        "n_cells_not_measured": len(unmeasured),
        "cells_not_measured_gate_nothing":
            "every cell here is stand-in-dependent by construction and "
            "nothing on this record gates anything; an unplaceable stand-in "
            "costs diagnostic breadth (A17)",
        "gate4_class_coverage": coverage,
        "shared_with_gate2": shared,
        "rows_not_drawn": {
            "cells_read_from_gate2": len(shape) - len(generated_shape),
            "rows_read_from_gate2": (len(shape) - len(generated_shape))
                                    * len(topics) * C.M_CAL * len(probed),
            "severities_not_probed": sorted(set(admissible) - {m_star}),
            "why_they_were_not_probed":
                "m* is frozen at GATE_2_FOCAL_CALIBRATION and this stage "
                "cannot move it, so no severity but m* is measurable here",
            "severities_probed": sorted(probed),
            "rows_the_operating_point_costs":
                len(generated_shape) * len(topics) * C.M_CAL},
        # §34 D20's measured transfer: the realised Calibration-A vs
        # Calibration-B movement of every probed entry. Read by nothing.
        "measured_split_transfer": _measured_split_transfer(probed),
        "proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
        "proximity_band_is_descriptive": True,
        "n_composed_audited_at": C.N_COMPOSED,
        "selects_nothing": True,
        "selects_nothing_is":
            "this stage chooses no severity, no candidate, no pool and no "
            "reference, and terminates nothing. It measures the composed "
            "contrast at the operating point §12.3 already chose and "
            "records it",
        "admissible_severities": sorted(admissible),
        "scope_limits": list(composed_probe.PROBE_SCOPE_LIMITS),
        audit_prefreeze.DECLARED_REFUSALS_KEY:
            dict(composed_probe.PROBE_DECLARED_REFUSALS),
        "outcome": composed_probe.PROBE_OUTCOME,
    }


def run_gate2_75(tree: ModelTree, *, cap: int | None = None,
                 producing_commit: str | None = None,
                 environment_digest: str = "", bank: TopicBank | None = None,
                 device: int = 0,
                 standins: Sequence[Constraint] | None = None,
                 block_limit: int | None = None,
                 resamples: int = C.BOOTSTRAP_RESAMPLES,
                 generate: Callable[..., dict[str, Any]] | None = None
                 ) -> StageOutcome:
    """The stage entry point. Takes ``device``, so ``cli.generating_stages``
    picks it up from the signature rather than from a hand-kept list."""
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    cap = cap if cap is not None else regime["selected_cap"]
    return run_stage(
        tree, C.STAGE_GATE2_75,
        compute=lambda previous: gate2_75_payload(
            tree, producing_commit=commit, gate2_5_record=previous,
            bank=bank, cap=cap, device=device, standins=standins,
            block_limit=block_limit, resamples=resamples, generate=generate),
        producing_commit=commit, environment_digest=environment_digest)


# ---------------------------------------------------------------- Gate 3A

def gate3a_payload(tree: ModelTree, *, producing_commit: str,
                   probe_record: Mapping[str, Any],
                   gate2_5_record: Mapping[str, Any],
                   gate2_record: Mapping[str, Any],
                   regime_record: Mapping[str, Any],
                   bank: TopicBank | None = None, seed: int = 0,
                   resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
                   ) -> dict[str, Any]:
    """§18 stage 8: every §13.7 quantity on A, on B and on the pooled set.

    Three tables, three hashes, one stability verdict per candidate. §13.7's
    two estimates are independent only if their rows are, so the two split
    tables are loaded separately and ``assert_not_pooled`` refuses a table
    that carries the other split's rows.
    """
    bank = bank if bank is not None else load_bank()
    # Gate 2.75 is Gate 3A's registered predecessor and it cannot have moved
    # m*: §12.3 froze it at Gate 2 and the probe passes at it or terminates.
    # `effective_m_star` is the checked accessor; here the probe record is
    # already in hand, so the same equality is asserted against Gate 2's.
    m_star = int(probe_record["m_star"])
    if m_star != int(gate2_record["m_star"]):
        raise ProtocolError(
            f"{C.STAGE_GATE2_75} records m* = {m_star} and {C.STAGE_GATE2} "
            f"froze {gate2_record['m_star']}. m* is selected once and no "
            "later stage may move it")
    # §13.7's whole computation is `feasibility.calibration_at`, which is the
    # same function the operating-point search and the development pilot run.
    # It generates nothing: every quantity in it was measured at Gate 2 and
    # Gate 2.5, which is what lets a search evaluate it at a candidate
    # operating point before a composed row exists.
    calibration = feasibility.calibration_at(
        model_key=tree.model_key, gate2_record=gate2_record,
        gate2_5_record=gate2_5_record, m_star=m_star, seed=seed,
        resamples=resamples)
    # §12.6, re-read where reference selection actually works. This **gates**:
    # `support_at` takes its failures as design-time failures, under §34 D6's
    # existing disposition and with no new status and no drift threshold.
    # v7 A7: the core conditions' failures and the spectrum conditions'
    # failures are two lists, and Gate 3C reads each into the arm it gates.
    coverage = feasibility.coverage_at_calibrated_iota_a(
        gate2_record=gate2_record, regime_record=regime_record)
    return {
        "stage": C.STAGE_GATE3A,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE3A],
        "outcome": "PASS",
        # §12.6 on the calibration basis at the measured iota_A. Gate 3C
        # reads `failures` and `spectrum_failures` from it; nothing else may.
        "coverage_at_calibrated_iota_a": coverage,
        "calibrated_coverage_failures": list(coverage["failures"]),
        "calibrated_spectrum_failures": list(coverage["spectrum_failures"]),
        "inputs": {"gate2_5": {"stage": C.STAGE_GATE2_5},
                   "gate2_75": {"stage": C.STAGE_GATE2_75,
                                "m_star": m_star,
                                "reselected": probe_record["reselected"]}},
        "producing_commit": producing_commit,
        "m_star": m_star,
        "calibration_b_population": list(
            calibration["calibration_b_population"]),
        "split_tables": {
            C.CALIBRATION_A: calibration_binding(bank, split=C.CALIBRATION_A,
                                                 draws=C.M_CAL),
            C.CALIBRATION_B: calibration_binding(bank, split=C.CALIBRATION_B,
                                                 draws=C.M_CAL)},
        "n_rows": dict(calibration["n_rows"]),
        "stability": calibration["stability"],
        "iota_a_stability": calibration["iota_a_stability"],
        "n_stable": calibration["n_stable"],
        "equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
        "pooled_table": [dict(r) for r in calibration["pooled_table"]],
        # The pool this stage actually used, named with the severity it was
        # qualified at, so a reader never has to infer which entry of the
        # by-severity column the replication ran on.
        "qualified_pool": list(calibration["qualified_pool"]),
        "qualified_families": list(calibration["qualified_families"]),
        "n_qualified": calibration["n_qualified"],
        "qualified_at_m_star": m_star,
        "iota_a": calibration["iota_a"],
        "solo_compliance_a": calibration["solo_compliance_a"],
    }


def run_gate3a(tree: ModelTree, *, producing_commit: str | None = None,
               environment_digest: str = "", bank: TopicBank | None = None,
               seed: int = 0,
               resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
               ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    gate2_5 = transitions.read_stage_record(tree, C.STAGE_GATE2_5)
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    return run_stage(
        tree, C.STAGE_GATE3A,
        # `previous` is the GATE_2_75 record: inserting a stage moved Gate
        # 3A's predecessor, and a payload that kept calling it `gate2_5`
        # would have read the probe's fields under Gate 2.5's name.
        compute=lambda previous: gate3a_payload(
            tree, producing_commit=commit, probe_record=previous,
            gate2_5_record=gate2_5, gate2_record=gate2,
            regime_record=regime, bank=bank, seed=seed,
            resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)


# ---------------------------------------------------------------- Gate 3B

def gate3b_payload(tree: ModelTree, *, producing_commit: str,
                   gate3a_record: Mapping[str, Any],
                   n_topics_a: int | None = None) -> dict[str, Any]:
    """§18 stage 9: §13.8, §13.9, §13.10 and §13.12 on the qualified pool.

    Both coordinates A is matched on come from Gate 3A's record, which got
    them from Gate 2's. A selection run against an iota_A the caller supplied
    would be a selection against a number with no producer.
    """
    iota_a = gate3a_record["iota_a"]
    solo_compliance_a = gate3a_record["solo_compliance_a"]
    # §13.8 to §13.12 are `feasibility.selection_at`, the same function the
    # operating-point search runs at a candidate m*. Gate 3A's record carries
    # exactly the block that kernel takes, so the search and the registered
    # stage cannot diverge in what "the selected references" means.
    chosen = feasibility.selection_at(
        {"pooled_table": gate3a_record["pooled_table"],
         "m_star": gate3a_record["m_star"], "iota_a": iota_a,
         "solo_compliance_a": solo_compliance_a,
         "stability": gate3a_record.get("stability") or {}},
        model_key=tree.model_key, n_topics_a=n_topics_a)
    return {
        "stage": C.STAGE_GATE3B,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE3B],
        "outcome": "PASS",
        "inputs": {"gate3a": {"stage": C.STAGE_GATE3A,
                              "m_star": gate3a_record["m_star"]}},
        "producing_commit": producing_commit,
        "m_star": gate3a_record["m_star"],
        "iota_a": iota_a, "solo_compliance_a": solo_compliance_a,
        "selection": chosen,
        "slot_map": chosen["slot_map"],
        "identification_statuses": chosen["identification_statuses"],
        "backups_may_substitute_after_gate_4":
            C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4,
        "no_substitution_statement":
            "§13.14: a frozen backup is never substituted into an admitted "
            "slot after Gate 4. The guarantee is that no substitution "
            "function exists; assert_no_substitution_path checks this "
            "module's namespace",
    }


def run_gate3b(tree: ModelTree, *, n_topics_a: int | None = None,
               producing_commit: str | None = None,
               environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_GATE3B,
        compute=lambda previous: gate3b_payload(
            tree, producing_commit=commit, gate3a_record=previous,
            n_topics_a=n_topics_a),
        producing_commit=commit, environment_digest=environment_digest)


# ---------------------------------------------------------------- Gate 3C

def gate3c_payload(tree: ModelTree, *, producing_commit: str,
                   gate3b_record: Mapping[str, Any],
                   gate2_5_record: Mapping[str, Any],
                   gate3a_record: Mapping[str, Any],
                   regime_record: Mapping[str, Any]) -> dict[str, Any]:
    """§18 stage 10: §13.15's support, the arm set, the derived cell count.

    Every identification status is written **at design time**, onto a signed
    record, before a confirmatory row exists. That is what makes the arm set
    a design fact rather than a post-hoc description of what happened to work.
    """
    # §13.15 is `feasibility.support_at`, the same kernel the search and the
    # development pilot run. The calibrated re-reading of §12.6 enters it as a
    # design-time failure --- the same route the screen-time failure takes,
    # under the same §34 D6 disposition, with no second status.
    calibration = {"qualified_families": list(qualification_at(
        gate2_5_record, m_star=int(gate3b_record["m_star"]))
        ["qualified_families"])}
    supported = feasibility.support_at(
        gate3b_record["selection"], model_key=tree.model_key,
        calibration=calibration, regime_record=regime_record,
        extra_design_time_failures=list(
            gate3a_record.get("calibrated_coverage_failures") or ()),
        extra_spectrum_failures=list(
            gate3a_record.get("calibrated_spectrum_failures") or ()))
    report = supported["report"]
    screen_statuses = set(supported["screen_statuses"])
    design_time_failures = list(supported["design_time_failures"])
    arms = normalise_arms(supported["arms"])
    # §8.1 / v7 A8: the base arm is unconditional, so a replication that
    # reaches this stage always retains D(B<-A), D(A<-B), Lambda and the A/B
    # order contrasts whatever else it loses.
    if C.ARM_BASE not in arms:
        raise ProtocolError("§8.1: the base arm is always admitted")
    statuses = list(supported["identification_statuses"])
    disposition = report["disposition"]
    if not report["support_met"]:
        if disposition == "REFERENCE_SUPPORT_NOT_IDENTIFIED_TERMINAL":
            raise TerminalStatus(
                "REFERENCE_SUPPORT_NOT_IDENTIFIED", gate=C.STAGE_GATE3C,
                criterion="§13.15's support requirements, with §34 D6 closed "
                          "at 'terminal'",
                observed=report["failures"],
                strongest_permissible_statement=C.TERMINAL_SENTENCE)
    assert_arms_are_bound(arms, gate3b_record, gate2_5_record)
    return {
        "stage": C.STAGE_GATE3C,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE3C],
        "outcome": "PASS",
        "inputs": {"gate3b": {"stage": C.STAGE_GATE3B,
                              "m_star": gate3b_record["m_star"]}},
        "producing_commit": producing_commit,
        "m_star": gate3b_record["m_star"],
        "support": report,
        "support_disposition": disposition,
        # §12.6's screen-time verdict, named on this record so a reader can
        # tell a design-time non-identification from a calibration-time one.
        "regime_screen_statuses": sorted(screen_statuses),
        "design_time_failures": list(design_time_failures),
        # v7 A7: the spectrum arm's own design-time failures, if any.
        "spectrum_failures": list(supported["spectrum_failures"]),
        "spectrum_met": bool(report["spectrum_met"]),
        # §34 D6, closed at `identification_status`. Present and null when
        # §13.15 was met: a reader of the record can tell "the support held"
        # from "this record predates the decision", and every later stage
        # reads the same key.
        "non_identification": report["non_identification"],
        "not_identified_members": list(report["not_identified_members"]),
        "admitted_arms": list(arms),
        "derived_cell_count": report["derived_cell_count"],
        "slots": list(slots_for(arms)),
        "identification_statuses": statuses,
        "written_at_design_time": True,
    }


def assert_arms_are_bound(arms: Sequence[str], gate3b_record: Mapping[str, Any],
                          gate2_5_record: Mapping[str, Any]) -> None:
    """Every slot the admitted arms need has a bound constituent.

    The invariant that keeps §13.15's arm admission and §13.8-§13.10's
    selection from disagreeing. An arm admitted with no companion produces a
    cell plan Gate 4 cannot render, and the failure surfaces two stages later
    as a missing slot rather than here as an unmet requirement.
    """
    bound = set(gate3b_record.get("slot_map") or {}) | {"A", "B"}
    needed = set(slots_for(normalise_arms(arms)))
    missing = sorted(needed - bound)
    if missing:
        raise ProtocolError(
            f"§13.15: the admitted arm set {list(arms)} needs slot(s) "
            f"{missing} and Gate 3B bound none of them. An arm is admitted "
            "when it has a companion, not when its selection block exists")


def run_gate3c(tree: ModelTree, *, producing_commit: str | None = None,
               environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    gate2_5 = transitions.read_stage_record(tree, C.STAGE_GATE2_5)
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    gate3a = transitions.read_stage_record(tree, C.STAGE_GATE3A)
    return run_stage(
        tree, C.STAGE_GATE3C,
        compute=lambda previous: gate3c_payload(
            tree, producing_commit=commit, gate3b_record=previous,
            gate2_5_record=gate2_5, gate3a_record=gate3a,
            regime_record=regime),
        producing_commit=commit, environment_digest=environment_digest)


# ----------------------------------------------------------------- Gate 4

def composed_table_shape(arms: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """design cell id -> the slots Gate 4 records for that cell.

    Derived from the admitted arm set, so the table the stage records is
    exactly the table the design produces. A hard-coded shape is how v4r4's
    variant table drifted from its own cell plan.
    """
    from dci1v7.design.cells import cell_types

    return {t.cell_id: t.slots for t in cell_types(normalise_arms(arms))}


def assert_composed_table_complete(table: Mapping[str, Mapping[str, float]],
                                   arms: Sequence[str]) -> None:
    """Gate 4 measures **every** registered cell type, so the table holds
    them all and every slot of each. Apparatus completeness, not a verdict:
    a missing cell is a run that did not produce its rows."""
    expected = composed_table_shape(arms)
    missing_cells = sorted(set(expected) - set(table))
    if missing_cells:
        raise ProtocolError(
            f"Gate 4: the composed table is missing cell type(s) "
            f"{missing_cells}; every registered cell type of the admitted "
            "arms is measured")
    for cell_id, slots in expected.items():
        got = set(table[cell_id])
        want = set(slots) if slots else {"unconstrained"}
        if got != want:
            raise ProtocolError(
                f"Gate 4: cell {cell_id} should carry {sorted(want)} and "
                f"carries {sorted(got)}")


def slot_map_from_record(record: Mapping[str, Any]) -> dict[str, Constraint]:
    """The slot -> instance binding a gate record wrote, re-typed.

    Read from the record so that Gate 4, the freeze and the confirmatory run
    all bind the same constituents to the same slots without any of them
    choosing. A slot map a caller supplied would be a design nobody signed.
    """
    slot_map: dict[str, Constraint] = {}
    for slot, value in (record.get("slot_map") or {}).items():
        kind = value[0]
        # §34 D24: a probe-only stand-in may not be bound to any slot.
        assert_selectable(kind, where="§13.11 slot_map_from_record")
        slot_map[slot] = (focal_constraint(int(value[1])) if kind == "B"
                          else Constraint(kind, int(value[1]), reserve=True))
    return slot_map


def _split_transfer(table: Mapping[str, Mapping[str, float]], *,
                    slot_map: Mapping[str, Constraint],
                    calibration_rows: Sequence[Mapping[str, Any]]
                    ) -> dict[str, Any]:
    """Each bound instrument's own solo compliance, here against at Gate 2.

    **Paired by instrument.** §13.4 admits a companion on 192 calibration
    topics at M_cal draws; this stage measures it again on 24 reserved
    composed topics at M_cal draws. One of v5's two terminations and v6's
    Gemma termination were companion slots in a *solo* cell, which is this
    movement and not a composition effect at all --- and under v7 it is
    recorded and terminates nothing.
    """
    by_label = {f"{r['kind']}:{r['severity']}": r for r in calibration_rows}
    moved: list[dict[str, Any]] = []
    for slot, constraint in sorted(slot_map.items()):
        entry = (table.get(f"solo:{slot}") or {}).get(slot)
        calibrated = (by_label.get(constraint.label) or {}).get(
            "solo_compliance")
        if entry is None or calibrated is None:
            continue
        moved.append({"slot": slot, "instrument": constraint.label,
                      "calibration_solo": calibrated,
                      "composed_topic_solo": entry,
                      "movement": entry - calibrated})
    values = [abs(e["movement"]) for e in moved]
    return {
        "paired_by": "the same instrument on the same model, measured by "
                     "§13.4 on the calibration topics and by Gate 4 on "
                     "§6.2's 24 reserved composed topics",
        "gates_nothing": True, "costs_no_generation": True,
        "n_paired": len(moved),
        "mean_abs": (sum(values) / len(values)) if values else None,
        "max_abs": max(values) if values else None,
        "per_instrument": moved,
    }


def gate4_payload(tree: ModelTree, *, producing_commit: str,
                  gate3c_record: Mapping[str, Any],
                  slot_map: Mapping[str, Constraint],
                  calibration_rows: Sequence[Mapping[str, Any]] = (),
                  bank: TopicBank | None = None, cap: int,
                  device: int = 0,
                  resamples: int = C.BOOTSTRAP_RESAMPLES,
                  generate: Callable[..., dict[str, Any]] | None = None
                  ) -> dict[str, Any]:
    """§18 stage 11 (v7): the composed contrast, projected on §6.2's reserved
    composed-validation topics at M_cal, and recorded.

    It measures every registered cell type of the admitted arms, forms every
    registered contrast inside each topic by the confirmatory estimators,
    reads each through the v7 §13.14 boundary rule, and records the result.
    It **selects nothing** and **terminates nothing**: there is no path from
    anything here to a different reference, and ``assert_no_substitution_path``
    is asserted on this module. The only refusals are apparatus: a row count
    that is not the plan's, or a table missing a registered cell.
    """
    bank = bank if bank is not None else load_bank()
    arms = normalise_arms(gate3c_record["admitted_arms"])
    topics = list(bank.topics("composed"))
    blocks = _blocks(topics, "g4")
    cells = design_cells(blocks, arms, draws=C.M_CAL)
    generate = resolve_generate(tree, generate, _responder,
                                where=C.STAGE_GATE4)
    prompts = [prompt_cell(cell, _by_id(topics)[cell.topic_id],
                           slot_map=slot_map, topic_split="composed")
               for cell in cells]
    expected_rows = len(prompts) * C.M_CAL
    instances = tuple(dict.fromkeys(slot_map.values()))
    rows = generate_and_score(
        tree.model_key, prompts, stage=C.STAGE_GATE4, cap=cap, device=device,
        run_dir=tree.backend_runs(C.STAGE_GATE4) / "composed",
        instances=instances, slot_map=slot_map,
        study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, C.STAGE_GATE4),
        generate=generate)
    if len(rows) != expected_rows:
        raise ProtocolError(
            f"Gate 4: {expected_rows} rows expected and {len(rows)} produced")

    shape = composed_table_shape(arms)
    table = composed_contrast.composed_table(rows, shape, slot_map)
    assert_composed_table_complete(table, arms)
    proximity = composed_contrast.cell_proximity(table, shape)
    # The rows as the confirmatory analysis will read rows: one cell mean per
    # (cell, constituent) per topic-block, and the registered contrasts
    # formed inside each block by the registered estimators.
    observations = ObservationTable(build_observations(rows,
                                                       m_draws=C.M_CAL))
    projected = composed_contrast.projection(
        observations, arms=arms,
        seed=seeds.bootstrap_seed("gate4", tree.model_key),
        resamples=resamples)
    payload = {
        "stage": C.STAGE_GATE4,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE4],
        "inputs": {"gate3c": {"stage": C.STAGE_GATE3C,
                              "arms": list(arms)}},
        "producing_commit": producing_commit,
        "admitted_arms": list(arms),
        "m_star": slot_map["B"].severity,
        "slot_map": {slot: [c.kind, c.severity]
                     for slot, c in sorted(slot_map.items())},
        "cell_types": sorted(shape),
        "n_cell_types": len(shape),
        "expected_rows": expected_rows,
        "rows": len(rows),
        "topics": sorted(t["topic_id"] for t in topics),
        "topic_set": "composed",
        "reserved_topic_use":
            "§6.2's composed-validation set, spent here and nowhere else",
        # v5's per-cell table, kept as a descriptive record.
        "composed_table": table,
        "cell_proximity": proximity,
        "cells_near_a_boundary": [p for p in proximity if p["near_boundary"]],
        "proximity_band": list(C.COMPOSED_PROXIMITY_BAND),
        "proximity_band_is_descriptive": True,
        # v7's record proper.
        "composed_contrast": projected,
        "contrast_statuses": projected["statuses"],
        "any_structural_zero": projected["any_structural_zero"],
        "resamples": resamples,
        "split_transfer": _split_transfer(
            table, slot_map=slot_map, calibration_rows=calibration_rows),
        "selects_nothing": True,
        "terminates_nothing": True,
        audit_prefreeze.DECLARED_REFUSALS_KEY: {
            "no_substitution_after_a_reading":
                "no function takes a Gate-4 reading and substitutes a frozen "
                "backup, and adding one is a test failure "
                "(assert_no_substitution_path)",
            "no_selection_here":
                "Gate 4 records the composed contrast on the arm set Gate 3C "
                "admitted. It admits nothing, drops nothing and reorders "
                "nothing",
            "no_composed_rate_terminates_a_replication":
                "v7 §13.14: the (0.05, 0.95) band is descriptive; the v5/v6 "
                "composed-headroom terminal status is withdrawn and has no "
                "raise path in this package",
        },
        "draws": C.M_CAL,
        "outcome": composed_contrast.GATE4_OUTCOME,
    }
    return payload


def run_gate4(tree: ModelTree, *, cap: int | None = None,
              producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              device: int = 0,
              resamples: int = C.BOOTSTRAP_RESAMPLES,
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    gate3b = transitions.read_stage_record(tree, C.STAGE_GATE3B)
    slot_map = slot_map_from_record(gate3b)
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    slot_map.setdefault("A", Constraint("A", gate2["n_star"]))
    # Gate 4 composes B at the operating point the study runs. That is Gate
    # 2's frozen m*, and `effective_m_star` refuses a probe record that
    # disagrees with it rather than following either.
    slot_map.setdefault("B", focal_constraint(effective_m_star(tree)))
    cap = cap if cap is not None else regime["selected_cap"]
    return run_stage(
        tree, C.STAGE_GATE4,
        compute=lambda previous: gate4_payload(
            tree, producing_commit=commit, gate3c_record=previous,
            slot_map=slot_map,
            calibration_rows=gate2["calibration_rows"]["pooled"],
            bank=bank, cap=cap, device=device, resamples=resamples,
            generate=generate),
        producing_commit=commit, environment_digest=environment_digest)


def assert_no_substitution_path(namespace: Mapping[str, Any] | None = None
                                ) -> dict[str, Any]:
    """§13.14, §33 check 2: no Gate-4 failure -> substitute -> rerun exists.

    Static and by name. A function whose name suggests substitution, retry or
    a second Gate-4 pass is refused here rather than found in review, and the
    check runs over **this** module because this is where such a function
    would naturally be written.
    """
    namespace = namespace if namespace is not None else globals()
    forbidden = ("substitute", "swap_reference", "replace_reference",
                 "retry_gate4", "rerun_gate4", "promote_backup",
                 "fallback_reference")
    found = sorted(name for name in namespace
                   if any(token in name.lower() for token in forbidden)
                   and not name.startswith("assert_no"))
    if found:
        raise ProtocolError(
            f"§13.14: {found} would be a post-outcome substitution path. A "
            "frozen backup is never substituted into an admitted slot after "
            "Gate 4, and the guarantee is that no such function exists")
    return {"checked": len(namespace), "forbidden_tokens": list(forbidden),
            "found": []}
