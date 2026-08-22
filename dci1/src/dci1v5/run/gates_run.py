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

**Gate 4 validates composed headroom. It selects nothing.** There is no
function here that takes a Gate-4 failure and substitutes a frozen backup, and
``assert_no_backup_substitution`` is asserted on this module's own namespace
so that adding one is a test failure rather than a review finding.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError

from dci1v5.design.cells import (design_cells,
                                 normalise_arms, slots_for)
from dci1v5.engine import transitions
from dci1v5.engine.paths import ModelTree
from dci1v5.protocol import constants as C
from dci1v5.run.execute import (fake_backend, generate_and_score,
                                instance_rates, per_topic_compliance,
                                prompt_cell)
from dci1v5.run.lifecycle import StageOutcome, TerminalStatus, run_stage
from dci1v5.stages import audit_prefreeze
from dci1v5.stages import construct_strength, interaction, regime as regime_stage
from dci1v5.stages import qualification_gate, selection, stability, support
from dci1v5.stages.calibration_table import (instructed_compliance,
                                             load_calibration_table)
from dci1v5.topics.bank import (TopicBank, calibration_binding, load_bank)
from dci1v5.verifiers.constraints import FAMILIES, Constraint

__all__ = ["assert_synthetic_only", "slot_map_from_record",
           "gate2_payload", "run_gate2", "gate2_5_payload", "run_gate2_5",
           "gate3a_payload", "run_gate3a", "gate3b_payload", "run_gate3b",
           "gate3c_payload", "run_gate3c", "gate4_payload", "run_gate4",
           "headroom_table_shape", "assert_headroom_table_complete",
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
            "only in the synthetic namespace, whose study id no v5 estimator "
            "or gate accepts")


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
    generate = generate or fake_backend(_responder)
    cap = regime_record["selected_cap"]
    candidates = _constraints_from_labels(regime_record["carried_set"])
    non_outcome = [c for c in candidates if c.kind not in ("A", "B")]

    grids = {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID)}
    curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    chance_curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    grid_rows: list[dict[str, Any]] = []
    for kind, grid in grids.items():
        slot_map = {f"{kind}{q}": Constraint(kind, q) for q in grid}
        cells: list[Any] = []
        for block in _blocks(topics, f"g2{kind}"):
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
            run_dir=tree.backend_runs(C.STAGE_GATE2) / f"grid-{kind}",
            instances=instances, slot_map=slot_map,
            study_id=tree.context.study_id, generate=generate)
        grid_rows.extend(rows)
        for q in grid:
            rates = instance_rates(rows, kind=kind, severity=q)
            curves[kind][q] = rates["solo"]
            chance_curves[kind][q] = rates["chance"]

    target = regime_stage.select_target(curves["A"])
    focal = regime_stage.select_focal(curves["B"])
    for result, status in ((target, "TARGET_RANGE_EXHAUSTED"),
                           (focal, "FOCAL_RANGE_EXHAUSTED")):
        if result.get("selected") is None:
            raise TerminalStatus(
                result.get("terminal_status", status), gate=C.STAGE_GATE2,
                criterion="§12.3: an eligible severity inside the registered "
                          "band",
                observed={"curve": result.get("curve")},
                strongest_permissible_statement=C.TERMINAL_SENTENCE)
    m_star, n_star = focal["selected"], target["selected"]

    strength = construct_strength.assert_construct_floor(
        m_star, chance_compliance_at_m_star=chance_curves["B"][m_star],
        curve=chance_curves["B"], solo_curve=curves["B"], floor=floor)
    if strength.get("selection_refused"):
        raise TerminalStatus(
            strength["status"], gate=C.STAGE_GATE2,
            criterion="§34 D17's registered construct floor",
            observed=strength["reason"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)

    # ------------------------------ pass 2: the candidates' solo compliance
    b_star = Constraint("B", m_star)
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
            study_id=tree.context.study_id, generate=generate)

    b_solo_rows = [r for r in grid_rows
                   if r["cell_id"] == f"solo:{b_star.label}"]
    tables = _calibration_rows(
        tree.model_key, non_outcome, m_star=m_star,
        solo_rows=candidate_rows, chance_rows=grid_rows,
        b_solo_rows=b_solo_rows)

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
        "solo_curves": {k: {str(q): v for q, v in c.items()}
                        for k, c in curves.items()},
        "chance_curves": {k: {str(q): v for q, v in c.items()}
                          for k, c in chance_curves.items()},
        "iota_a": instructed_compliance(curves["A"][n_star],
                                        chance_curves["A"][n_star]),
        "solo_compliance_a": curves["A"][n_star],
        "iota_a_by_split": _iota_a_by_split(grid_rows, n_star),
        "solo_a_by_split": _solo_a_by_split(grid_rows, n_star),
        "construct_strength": strength,
        "calibration_binding": binding,
        "calibration_rows": tables,
        "n_candidates_measured": len(non_outcome),
        "kappa_under_b_source":
            "the B-solo cells at m*, on which every carried candidate was "
            "scored as absent under §9.1; no generation of its own (§13.6)",
        "adequacy": {
            "vacuity_max": C.REGIME_VACUITY_MAX,
            "graded_degeneracy_share_max": C.GRADED_DEGENERACY_SHARE_MAX},
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


def _calibration_rows(model_key: str, candidates: Sequence[Constraint], *,
                      m_star: int, solo_rows: Sequence[Mapping[str, Any]],
                      chance_rows: Sequence[Mapping[str, Any]],
                      b_solo_rows: Sequence[Mapping[str, Any]]
                      ) -> dict[str, list[dict[str, Any]]]:
    """The §13.11 closed-schema table, per split and pooled.

    Built here because this is the stage that generated the rows. A table
    assembled by a caller is a table nobody can trace to a generation, and
    §13.11's whole point is that the selection input is auditable.
    """
    out: dict[str, list[dict[str, Any]]] = {}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled"):
        restrict = None if split == "pooled" else split
        rows: list[dict[str, Any]] = []
        for candidate in candidates:
            try:
                solo = instance_rates(solo_rows, kind=candidate.kind,
                                      severity=candidate.severity,
                                      split=restrict)
            except ProtocolError:
                continue
            try:
                chance = instance_rates(chance_rows, kind=candidate.kind,
                                        severity=candidate.severity,
                                        split=restrict)
                chance_value = chance["chance"]
            except ProtocolError:
                chance_value = 0.0
            kappa_b, n_topics_b, n_draws_b = _kappa_under_b(
                b_solo_rows, candidate, split=restrict)
            entry: dict[str, Any] = {
                "kind": candidate.kind, "severity": candidate.severity,
                "split": split, "model_key": model_key,
                "solo_compliance": solo["solo"],
                "chance_compliance": chance_value,
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
                    solo_rows, kind=candidate.kind,
                    severity=candidate.severity, split=restrict)),
            }
            if kappa_b is not None:
                entry["kappa_under_b"] = kappa_b
                # Written as a mapping, not as the dataclass: the table goes
                # onto a signed JSON record and §13.11 requires the source to
                # travel with the value. `load_calibration_table` rebuilds it
                # and validates it, on a fresh table and a reloaded one alike.
                entry["kappa_under_b_source"] = {
                    "load": 1, "present": [f"B:{m_star}"],
                    "candidate": candidate.label, "model_key": model_key,
                    "m_star": m_star, "split": split,
                    "n_topics": n_topics_b, "n_draws": n_draws_b}
            rows.append(entry)
        out[split] = rows
    return out


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
    raw = list(gate2_record["calibration_rows"][split])
    rows = load_calibration_table(raw, model_key=tree.model_key,
                                  m_star=m_star, split=split)
    qualified = qualification_gate.qualify_candidates(
        rows, model_key=tree.model_key, m_star=m_star,
        producing_commit=producing_commit)
    interaction_rows = [
        {"candidate": r.label, "kappa": r.chance_compliance,
         "iota": instructed_compliance(r.solo_compliance,
                                       r.chance_compliance),
         "kappa_under_b": r.kappa_under_b, "source": r.kappa_under_b_source}
        for r in rows]
    report = interaction.measure_interaction(
        interaction_rows, model_key=tree.model_key, m_star=m_star,
        split=split)
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


# ---------------------------------------------------------------- Gate 3A

def gate3a_payload(tree: ModelTree, *, producing_commit: str,
                   gate2_5_record: Mapping[str, Any],
                   gate2_record: Mapping[str, Any],
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
    m_star = gate2_5_record["m_star"]
    tables = gate2_record["calibration_rows"]
    qualified = list(gate2_5_record["qualified_pool"])
    population = stability.calibration_b_population(
        carried=[r["kind"] + ":" + str(r["severity"])
                 for r in tables[C.CALIBRATION_A]],
        a_survivors=qualified)
    table_a = load_calibration_table(tables[C.CALIBRATION_A],
                                     model_key=tree.model_key,
                                     m_star=m_star, split=C.CALIBRATION_A)
    table_b = load_calibration_table(tables[C.CALIBRATION_B],
                                     model_key=tree.model_key,
                                     m_star=m_star, split=C.CALIBRATION_B)
    table_pooled = load_calibration_table(tables["pooled"],
                                          model_key=tree.model_key,
                                          m_star=m_star, split="pooled")
    stability.assert_not_pooled(table_a, split=C.CALIBRATION_A)
    stability.assert_not_pooled(table_b, split=C.CALIBRATION_B)
    pairs = stability.split_pair(table_a, table_b)
    verdicts = {label: stability.stability_verdict(
        pair, iota_a_by_split=gate2_record["iota_a_by_split"],
        solo_a_by_split=gate2_record["solo_a_by_split"], seed=seed,
        resamples=resamples)
        for label, pair in pairs.items()}
    return {
        "stage": C.STAGE_GATE3A,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE3A],
        "outcome": "PASS",
        "inputs": {"gate2_5": {"stage": C.STAGE_GATE2_5, "m_star": m_star}},
        "producing_commit": producing_commit,
        "m_star": m_star,
        "calibration_b_population": list(population),
        "split_tables": {
            C.CALIBRATION_A: calibration_binding(bank, split=C.CALIBRATION_A,
                                                 draws=C.M_CAL),
            C.CALIBRATION_B: calibration_binding(bank, split=C.CALIBRATION_B,
                                                 draws=C.M_CAL)},
        "n_rows": {C.CALIBRATION_A: len(table_a),
                   C.CALIBRATION_B: len(table_b),
                   "pooled": len(table_pooled)},
        "stability": verdicts,
        "n_stable": sum(1 for v in verdicts.values() if v.get("stable")),
        "equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
        "pooled_table": [dict(r) for r in tables["pooled"]],
        "iota_a": gate2_record["iota_a"],
        "solo_compliance_a": gate2_record["solo_compliance_a"],
    }


def run_gate3a(tree: ModelTree, *, producing_commit: str | None = None,
               environment_digest: str = "", bank: TopicBank | None = None,
               seed: int = 0,
               resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
               ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    return run_stage(
        tree, C.STAGE_GATE3A,
        compute=lambda previous: gate3a_payload(
            tree, producing_commit=commit, gate2_5_record=previous,
            gate2_record=gate2, bank=bank, seed=seed, resamples=resamples),
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
    rows = load_calibration_table(gate3a_record["pooled_table"],
                                  model_key=tree.model_key,
                                  m_star=gate3a_record["m_star"],
                                  split="pooled")
    stability_by_candidate = {
        label: verdict for label, verdict
        in (gate3a_record.get("stability") or {}).items()}
    result = selection.select_all(
        rows, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
        n_topics_a=n_topics_a,
        stability_by_candidate=stability_by_candidate)
    chosen = {"core": result.core, "spectrum": result.spectrum,
              "near_form": result.near_form,
              "broad_class": result.broad_class,
              "slot_map": {k: list(v) for k, v in result.slot_map().items()},
              "identification_statuses": result.identification_statuses}
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
                   regime_record: Mapping[str, Any]) -> dict[str, Any]:
    """§18 stage 10: §13.15's support, the arm set, the derived cell count.

    Every identification status is written **at design time**, onto a signed
    record, before a confirmatory row exists. That is what makes the arm set
    a design fact rather than a post-hoc description of what happened to work.
    """
    qualified_families = list(gate2_5_record["qualified_families"])
    structurally_eligible_tier12_families = sorted({
        label.rpartition(":")[0] for label in regime_record["carried_set"]
        if FAMILIES[label.rpartition(":")[0]].structural_tier in (1, 2)})
    selection_record = gate3b_record["selection"]
    core_block = selection_record.get("core") or {}
    # `evaluate_support` reads `core_references` and `identification_statuses`
    # at the top level of what it is given, and Gate 3B's record nests them
    # under the pool they came from. Flattening here, rather than reshaping
    # the record, keeps Gate 3B's record readable as four pools and gives
    # §13.15 the shape it registers.
    flattened = {
        "core_references": core_block.get("core_references") or [],
        "identification_statuses":
            selection_record.get("identification_statuses") or [],
    }
    # An arm is available when it has a **companion**, not when its selection
    # block exists: `admit_near_form_controls` returns a record whether or not
    # it admitted anything, and reading the record's truthiness admitted an
    # arm with no constituents --- which Gate 4 then could not render. Found
    # by the synthetic lifecycle.
    near_form_available = bool(
        (selection_record.get("near_form") or {}).get("controls"))
    class_available = bool(
        (selection_record.get("broad_class") or {}).get("companion"))
    spectrum_identified = bool(core_block.get("spectrum_identified"))
    report = support.evaluate_support(
        model_key=tree.model_key,
        structurally_eligible_tier12_families=(
            structurally_eligible_tier12_families),
        qualified_families=qualified_families,
        selection=flattened,
        near_form_available=near_form_available,
        class_available=class_available,
        spectrum_identified=spectrum_identified)
    arms = normalise_arms(report["admitted_arms"])
    statuses = sorted(set(report["identification_statuses"]))
    disposition = report["disposition"]
    if not report["support_met"]:
        disposition = support.support_disposition(met=False)
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
    return run_stage(
        tree, C.STAGE_GATE3C,
        compute=lambda previous: gate3c_payload(
            tree, producing_commit=commit, gate3b_record=previous,
            gate2_5_record=gate2_5, regime_record=regime),
        producing_commit=commit, environment_digest=environment_digest)


# ----------------------------------------------------------------- Gate 4

def headroom_table_shape(arms: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """design cell id -> the slots §13.14 evaluates for that cell.

    Derived from the admitted arm set, so the table §13.14 requires is exactly
    the table the design produces. A hard-coded shape is how v4r4's variant
    table drifted from its own cell plan.
    """
    from dci1v5.design.cells import cell_types

    return {t.cell_id: t.slots for t in cell_types(normalise_arms(arms))}


def assert_headroom_table_complete(table: Mapping[str, Mapping[str, float]],
                                   arms: Sequence[str]) -> None:
    """§13.14 evaluates **every** registered cell type, so the table holds
    them all and every slot of each."""
    expected = headroom_table_shape(arms)
    missing_cells = sorted(set(expected) - set(table))
    if missing_cells:
        raise ProtocolError(
            f"§13.14: the composed-headroom table is missing cell type(s) "
            f"{missing_cells}; every registered cell type of the admitted "
            "arms is evaluated")
    for cell_id, slots in expected.items():
        got = set(table[cell_id])
        want = set(slots) if slots else {"unconstrained"}
        if got != want:
            raise ProtocolError(
                f"§13.14: cell {cell_id} should carry {sorted(want)} and "
                f"carries {sorted(got)}")


def slot_map_from_record(record: Mapping[str, Any]) -> dict[str, Constraint]:
    """The slot -> instance binding a gate record wrote, re-typed.

    Read from the record so that Gate 4, the freeze and the confirmatory run
    all bind the same constituents to the same slots without any of them
    choosing. A slot map a caller supplied would be a design nobody signed.
    """
    return {slot: Constraint(value[0], int(value[1]), reserve=True)
            for slot, value in (record.get("slot_map") or {}).items()}


def gate4_payload(tree: ModelTree, *, producing_commit: str,
                  gate3c_record: Mapping[str, Any],
                  slot_map: Mapping[str, Constraint],
                  bank: TopicBank | None = None, cap: int,
                  device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None
                  ) -> dict[str, Any]:
    """§18 stage 11: composed-headroom **validation**, on §6.2's reserved
    composed-validation topics at M_cal.

    This is a validation gate. It measures every registered cell type of the
    admitted arms and asks whether every constraint in every one of them lands
    inside [0.05, 0.95]. It **selects nothing**: there is no path from a
    failure here to a different reference, and ``assert_no_substitution_path``
    is asserted on this module.
    """
    bank = bank if bank is not None else load_bank()
    arms = normalise_arms(gate3c_record["admitted_arms"])
    topics = list(bank.topics("composed"))
    blocks = _blocks(topics, "g4")
    cells = design_cells(blocks, arms, draws=C.M_CAL)
    generate = generate or fake_backend(_responder)
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
        generate=generate)
    if len(rows) != expected_rows:
        raise ProtocolError(
            f"§13.14: {expected_rows} rows expected and {len(rows)} produced")

    shape = headroom_table_shape(arms)
    table: dict[str, dict[str, float]] = {}
    for cell_id, slots in shape.items():
        cell_rows = [r for r in rows if r["cell_id"] == cell_id]
        if not slots:
            table[cell_id] = {"unconstrained": float(len(cell_rows))}
            continue
        entry: dict[str, float] = {}
        for slot in slots:
            constraint = slot_map[slot]
            passes = [float(s["passed"]) for r in cell_rows
                      for s in r["scores"]
                      if s["present"] and s["kind"] == constraint.kind
                      and s["severity"] == constraint.severity]
            entry[slot] = sum(passes) / len(passes) if passes else 0.0
        table[cell_id] = entry
    assert_headroom_table_complete(table, arms)

    low, high = C.COMPOSED_HEADROOM_BAND
    failures = [
        {"cell": cell_id, "slot": slot, "compliance": value}
        for cell_id, entry in table.items() if shape[cell_id]
        for slot, value in entry.items()
        if not (low <= value <= high)]
    payload = {
        "stage": C.STAGE_GATE4,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE4],
        "inputs": {"gate3c": {"stage": C.STAGE_GATE3C,
                              "arms": list(arms)}},
        "producing_commit": producing_commit,
        "admitted_arms": list(arms),
        "cell_types": sorted(shape),
        "n_cell_types": len(shape),
        "expected_rows": expected_rows,
        "rows": len(rows),
        "topics": sorted(t["topic_id"] for t in topics),
        "topic_set": "composed",
        "reserved_topic_use":
            "§6.2's composed-validation set, spent here and nowhere else",
        "headroom_table": table,
        "band": list(C.COMPOSED_HEADROOM_BAND),
        "failures": failures,
        "selects_nothing": True,
        # §33 check 8 scans every other key for a name that would betray an
        # outcome-driven selection, and requires this block. Declarations of
        # absence live here so that the scan does not read the refusal as the
        # thing refused --- and so that omitting the refusal fails the check.
        audit_prefreeze.DECLARED_REFUSALS_KEY: {
            "no_substitution_after_failure":
                "§13.14: a Gate-4 failure is terminal for the replication. No "
                "function takes a failure and substitutes a frozen backup, "
                "and adding one is a test failure",
            "no_selection_here":
                "§13.14: Gate 4 validates composed headroom on the arm set "
                "Gate 3C admitted. It admits nothing, drops nothing and "
                "reorders nothing",
        },
        "draws": C.M_CAL,
    }
    if failures:
        raise TerminalStatus(
            "COMPOSED_HEADROOM_FAILURE", gate=C.STAGE_GATE4,
            criterion=f"§13.14: every registered cell type inside "
                      f"{list(C.COMPOSED_HEADROOM_BAND)} on every constraint",
            observed=failures,
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    return {**payload, "outcome": "PASS"}


def run_gate4(tree: ModelTree, *, cap: int | None = None,
              producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              device: int = 0,
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    gate3b = transitions.read_stage_record(tree, C.STAGE_GATE3B)
    slot_map = slot_map_from_record(gate3b)
    regime = transitions.read_stage_record(tree, C.STAGE_REGIME)
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    slot_map.setdefault("A", Constraint("A", gate2["n_star"]))
    slot_map.setdefault("B", Constraint("B", gate2["m_star"]))
    cap = cap if cap is not None else regime["selected_cap"]
    return run_stage(
        tree, C.STAGE_GATE4,
        compute=lambda previous: gate4_payload(
            tree, producing_commit=commit, gate3c_record=previous,
            slot_map=slot_map, bank=bank, cap=cap, device=device,
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
