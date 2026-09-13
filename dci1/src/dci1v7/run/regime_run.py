"""§18 stages 4 and 5: ``REGIME_SCREEN`` and ``GATE_1_MEASUREMENT``.

**Stage 4 closes the vocabulary.** It selects the completion cap (§12.1),
runs §12.2's dense high-recall ladder screen on the twenty-four pre-screen
topics at one draw, applies §12.6's expansion to its stopping rule, evaluates
the coverage criterion, and **freezes the candidate vocabulary**. Nothing
after this stage may add a family or a rung: §12.6's expansion picks from
§7.10's frozen reserve and never authors, and the frozen set is written onto
the record so that a later stage measuring a rung that is not on it fails.

**§12.2 has no distance caliper and that is the change.** v4r4 pre-screened
on a point estimate of iota and then required the survivor to clear a caliper
against a quantity measured on different topics; the two stages' estimates
disagreed by a median of 0.071. v5's rule 1 is a Wilson interval that must
merely *intersect* a wide retention band, and rule 2 carries every Tier-1 and
Tier-2 rung unconditionally.

**Stage 5 is Gate 1, and it does not depend on Gate 3.** The instrument
population is the declared range of §7, which the preregistration registers,
so §10.2's evidence is required whatever Gate 3 later selects. It follows the
regime screen only because the regime screen is where the vocabulary closes.
Gate 1 freezes the canonical verifier hash **and the wording hash** --- v4r4
froze only the first, and a silently edited template would have moved what the
model was asked without moving anything a row records.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError

from dci1v7.engine import transitions
from dci1v7.engine.paths import ModelTree
from dci1v7.protocol import constants as C
from dci1v7.protocol.wordings import wording_source_hash
from dci1v7.run.execute import (generate_and_score, instance_rates,
                                prompt_cell, resolve_generate)
from dci1v7.run.lifecycle import (StageOutcome, TerminalStatus,
                                  protocol_identity, run_stage)
from dci1v7.stages.calibration_table import tie_key
from dci1v7.stages import gate1 as gate1_stage
from dci1v7.stages import regime as regime_stage
from dci1v7.stages import mutation, specification, verifier_audit
from dci1v7.topics.bank import (TopicBank, assert_no_reserved_topic_spent,
                                load_bank)
from dci1v7.verifiers import verifier_source_hash
from dci1v7.verifiers.constraints import (FAMILIES, Constraint,
                                          SELECTABLE_FAMILY_IDS,
                                          assert_selectable, declared_range,
                                          registered_severities)

__all__ = ["cap_cells", "select_cap", "ladder_cells", "difficulty_table",
           "regime_payload", "run_regime_screen", "gate1_payload",
           "gate1_provenance", "screen_texts", "run_gate1"]


def screen_texts(tree: ModelTree) -> list[str]:
    """Every response the regime screen produced, as §10.2's corpus.

    §10.2 measures the instruments against real generated text, and the
    regime screen is the only stage before Gate 1 that produces any. Reading
    them from disk rather than taking them as an argument is what makes the
    corpus a *record* --- the same rows the screen was scored on, not a
    sample a caller chose.
    """
    import json as _json

    from dci1v7.engine.paths import current_files

    texts: list[str] = []
    root = tree.backend_runs(C.STAGE_REGIME)
    if not root.exists():
        return texts
    for path in current_files(root, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                texts.append(_json.loads(line)["raw_response"])
    return texts


class _ScreenBlock:
    __slots__ = ("block_id", "index", "topic_id")

    def __init__(self, block_id: str, index: int, topic_id: str):
        self.block_id, self.index, self.topic_id = block_id, index, topic_id


class _SoloCell:
    """A one-slot cell for a screen, built without an admitted arm set.

    The screen measures *candidates*, which have no design slot yet, so it
    cannot use ``design/cells.py``: that module builds cells from admitted
    arms and the arms are not admitted until Gate 3C. This is the smallest
    object ``prompt_cell`` accepts, and it exists so that a screen cell and a
    confirmatory cell go through exactly one rendering path.
    """

    __slots__ = ("cell_id", "arm", "block_id", "block_index", "topic_id",
                 "slots", "wording_by_slot", "draws")

    def __init__(self, *, cell_id: str, arm: str, block: _ScreenBlock,
                 slot: str | None, wording_index: int, draws: int):
        self.cell_id = cell_id
        self.arm = arm
        self.block_id = block.block_id
        self.block_index = block.index
        self.topic_id = block.topic_id
        self.slots = (slot,) if slot else ()
        self.wording_by_slot = {slot: wording_index} if slot else {}
        self.draws = draws


def _blocks(topics: Sequence[Mapping[str, Any]], prefix: str
            ) -> list[_ScreenBlock]:
    return [_ScreenBlock(f"{prefix}-{i:03d}", i, t["topic_id"])
            for i, t in enumerate(topics)]


def cap_cells(topics: Sequence[Mapping[str, Any]], *, cap: int,
              draws: int = 1) -> tuple[list[Any], dict[str, Constraint]]:
    """§12.1's 96-prompt cap-selection set: 24 topics at loads 0, 1 and 2."""
    a = Constraint("A", C.TARGET_GRID[len(C.TARGET_GRID) // 2])
    b = Constraint("B", C.FOCAL_GRID[len(C.FOCAL_GRID) // 2])
    slot_map = {"A": a, "B": b}
    cells: list[Any] = []
    for block in _blocks(topics, f"cap{cap}"):
        cells.append(_SoloCell(cell_id="unconstrained", arm="unconstrained",
                               block=block, slot=None, wording_index=0,
                               draws=draws))
        cells.append(_SoloCell(cell_id="solo:A", arm="solo", block=block,
                               slot="A", wording_index=block.index %
                               C.N_WORDINGS, draws=draws))
        cells.append(_SoloCell(cell_id="solo:B", arm="solo", block=block,
                               slot="B", wording_index=block.index %
                               C.N_WORDINGS, draws=draws))
    return cells, slot_map


def select_cap(truncation_by_cap: Mapping[int, float]) -> dict[str, Any]:
    """§12.1: the smallest cap whose truncation share is under the bound."""
    qualifying = sorted(c for c in C.COMPLETION_CAPS
                        if truncation_by_cap.get(c, 1.0)
                        <= C.CAP_TRUNCATION_MAX)
    return {"selected_cap": qualifying[0] if qualifying else None,
            "truncation_by_cap": {str(k): v
                                  for k, v in truncation_by_cap.items()},
            "bound": C.CAP_TRUNCATION_MAX,
            "terminal_status": (None if qualifying
                                else "RESPONSE_LENGTH_INCOMPATIBLE")}


def ladder_cells(topics: Sequence[Mapping[str, Any]],
                 rungs: Sequence[Constraint], *,
                 draws: int = C.LADDER_SCREEN_DRAWS
                 ) -> tuple[list[Any], dict[str, Constraint]]:
    """§12.2's cells: one unconstrained cell and one solo cell per rung."""
    slot_map = {f"S{i}": rung for i, rung in enumerate(rungs)}
    cells: list[Any] = []
    for block in _blocks(topics, "screen"):
        cells.append(_SoloCell(cell_id="unconstrained", arm="unconstrained",
                               block=block, slot=None, wording_index=0,
                               draws=draws))
        for slot, rung in slot_map.items():
            cells.append(_SoloCell(
                cell_id=f"solo:{rung.label}", arm="solo", block=block,
                slot=slot, wording_index=block.index % C.N_WORDINGS,
                draws=draws))
    return cells, slot_map


def difficulty_table(rows: Sequence[Mapping[str, Any]],
                     rungs: Sequence[Constraint], *, split: str | None = None
                     ) -> list[dict[str, Any]]:
    """§12.2's first output: solo, kappa and iota for every measured rung."""
    from dci1v7.stages.calibration_table import instructed_compliance

    table: list[dict[str, Any]] = []
    for rung in rungs:
        rates = instance_rates(rows, kind=rung.kind, severity=rung.severity,
                               split=split)
        iota = (instructed_compliance(rates["solo"], rates["chance"])
                if rates["chance"] < C.CHANCE_DEGENERACY_MAX else None)
        family = FAMILIES.get(rung.kind)
        table.append({"candidate": rung.label, "kind": rung.kind,
                      "severity": rung.severity, **rates, "iota": iota,
                      # A and B are the outcome constraints. They are measured
                      # here because §12.2's table is what fixes iota_A, and
                      # they are not candidate families: no tier, and no
                      # retention verdict.
                      "tier": family.structural_tier if family else None,
                      "is_outcome": family is None,
                      "family": rung.kind if family else None})
    return table


def _screen_rungs(round_zero_only: bool = True) -> list[Constraint]:
    """Every registered rung §12.2 measures at round 0, **and A and B**.

    ``FAMILIES`` is the candidate library and excludes the two outcome
    constraints, so iterating it alone left A unmeasured on the pre-screen ---
    and §12.6 defines iota_A as *"the pre-screen instructed compliance of A at
    the severity whose solo compliance is nearest §12.3's aim"*. Without it
    every §12.6 distance is undefined, the coverage criterion cannot be
    evaluated, the expansion cannot run and `iota_a_prescreen` is null on the
    record. ``difficulty_table`` has always said this in its own comment ---
    *"A and B are the outcome constraints. They are measured here because
    §12.2's table is what fixes iota_A"* --- and the rung list disagreed with
    it.
    """
    rungs: list[Constraint] = []
    # The **selectable** pool. §34 D24's probe-only stand-ins are registered
    # instruments, but §12.2's table is the candidate population and §12.6
    # counts feature groups and straddling families over it --- a stand-in
    # screened here would enter a coverage count it can never be selected
    # from. `assert_selectable` re-checks every rung below, so the filter and
    # the guard have to disagree loudly rather than one silently defining the
    # other.
    for kind in SELECTABLE_FAMILY_IDS:
        severities = (registered_severities(kind) if round_zero_only
                      else declared_range(kind))
        rungs.extend(Constraint(kind, q) for q in severities)
    for rung in rungs:
        assert_selectable(rung.kind, where="§12.2's screen")
    rungs.extend(Constraint("A", q) for q in C.TARGET_GRID)
    rungs.extend(Constraint("B", q) for q in C.FOCAL_GRID)
    return rungs


def regime_payload(tree: ModelTree, *, producing_commit: str,
                   bank: TopicBank | None = None, device: int = 0,
                   generate: Callable[..., dict[str, Any]] | None = None,
                   caps: Sequence[int] = C.COMPLETION_CAPS,
                   rungs: Sequence[Constraint] | None = None
                   ) -> dict[str, Any]:
    """§18 stage 4, whole. Returns the record or raises a terminal status."""
    bank = bank if bank is not None else load_bank()
    prescreen = list(bank.topics("prescreen"))
    assert_no_reserved_topic_spent([t["topic_id"] for t in prescreen],
                                   bank.sets, stage=C.STAGE_REGIME)
    generate = resolve_generate(tree, generate, _screen_responder,
                                where=C.STAGE_REGIME)

    # --------------------------------------------------- §12.1 cap selection
    truncation: dict[int, float] = {}
    for cap in caps:
        cells, slot_map = cap_cells(prescreen, cap=cap)
        prompts = [prompt_cell(c, _by_id(prescreen)[c.topic_id],
                               slot_map=slot_map, topic_split="prescreen")
                   for c in cells]
        rows = generate_and_score(
            tree.model_key, prompts, stage=C.STAGE_REGIME, cap=cap,
            device=device, run_dir=tree.backend_runs(C.STAGE_REGIME)
            / f"cap-{cap}", instances=tuple(slot_map.values()),
            slot_map=slot_map, study_id=tree.context.study_id,
            protocol_identity=protocol_identity(tree, C.STAGE_REGIME),
            generate=generate)
        truncation[cap] = (sum(1 for r in rows if r["truncated"])
                           / max(1, len(rows)))
    cap_result = select_cap(truncation)
    if cap_result["selected_cap"] is None:
        raise TerminalStatus(
            "RESPONSE_LENGTH_INCOMPATIBLE", gate=C.STAGE_REGIME,
            criterion=f"§12.1: truncation <= {C.CAP_TRUNCATION_MAX} at some "
                      f"registered cap",
            observed=cap_result["truncation_by_cap"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    cap = cap_result["selected_cap"]

    # ------------------------------------------------ §12.2 the ladder screen
    measured = list(rungs) if rungs is not None else _screen_rungs()
    cells, slot_map = ladder_cells(prescreen, measured)
    prompts = [prompt_cell(c, _by_id(prescreen)[c.topic_id],
                           slot_map=slot_map, topic_split="prescreen")
               for c in cells]
    screen_rows = generate_and_score(
        tree.model_key, prompts, stage=C.STAGE_REGIME, cap=cap, device=device,
        run_dir=tree.backend_runs(C.STAGE_REGIME) / "ladder",
        instances=tuple(slot_map.values()), slot_map=slot_map,
        study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, C.STAGE_REGIME),
        generate=generate)
    table = difficulty_table(screen_rows, measured)
    by_label = {row["candidate"]: row for row in table}

    def _verdicts(rungs_measured, difficulty):
        return [
            regime_stage.carry_candidate(
                kind=rung.kind, severity=rung.severity,
                prescreen_solo_compliance=difficulty[rung.label]["solo"],
                n_prescreen_topics=difficulty[rung.label]["n_topics"],
                structural=regime_stage.StructuralScreen())
            for rung in rungs_measured if rung.kind in FAMILIES]

    verdicts = _verdicts(measured, by_label)
    carried = regime_stage.carried_set(verdicts)

    # §12.6: "Write iota_A for the pre-screen instructed compliance of A at
    # THE SEVERITY WHOSE SOLO COMPLIANCE IS NEAREST §12.3's AIM." This read
    # the first A row in the table --- the smallest severity of the target
    # grid --- so every §12.6 distance was measured from the wrong point on
    # A's own curve, and C1's "strictly below and strictly above" was
    # evaluated against it.
    a_rows = [r for r in table if r["kind"] == "A" and r.get("iota") is not None]
    iota_a_row = min(
        a_rows,
        key=lambda r: (tie_key(abs(r["solo"] - C.TARGET_AIM)), r["severity"]),
        default=None)
    iota_a = iota_a_row["iota"] if iota_a_row is not None else None
    # ------------------------------------------------- §12.6 the expansion
    # The coverage criterion is not a diagnostic. §12.6 runs the expansion
    # while C1-C6 are unmet and rounds remain, and when it stops without
    # passing the replication records, **at design time**, either
    # REFERENCE_SUPPORT_NOT_IDENTIFIED (a core condition C1/C3/C5/C6 lost:
    # no core or spectrum arm) or DIFFICULTY_SUPPORT_NOT_IDENTIFIED (only a
    # spectrum condition C2/C4 lost: no spectrum arm) --- v7 A7. Computing
    # `coverage` and reading nothing from it left a replication whose
    # criterion failed running the arms §12.6 forbids it.
    expansion: dict[str, Any] | None = None
    if iota_a is None:
        coverage = {"conditions": {},
                    "decisive": list(C.COVERAGE_EXPANSION_CONDITIONS),
                    "decisive_met": False, "core_met": False,
                    "spectrum_met": False,
                    "core_conditions": list(C.COVERAGE_CORE_CONDITIONS),
                    "spectrum_conditions":
                        list(C.COVERAGE_SPECTRUM_CONDITIONS),
                    "realised": {},
                    "identification_statuses": ["CLASS_ARM_NOT_AVAILABLE",
                                                "NEAR_FORM_ARM_NOT_AVAILABLE"],
                    "reason": "iota_A is not measured on the pre-screen"}
        screen_statuses = sorted(set(coverage["identification_statuses"])
                                 | {"REFERENCE_SUPPORT_NOT_IDENTIFIED",
                                    "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"})
    else:
        eligible_rows = regime_stage.coverage_rows(table, carried)
        measured_by_family: dict[str, list[int]] = {}
        for rung in measured:
            if rung.kind in FAMILIES:
                measured_by_family.setdefault(rung.kind, []).append(
                    rung.severity)

        def measure_reserve(admitted: Mapping[str, Sequence[int]]
                            ) -> list[dict[str, Any]]:
            """§12.6: only the newly admitted rungs, same topics, same cap."""
            # §7.10's frozen reserve, which is what §12.6's expansion picks
            # from: a reserve rung is outside the registered ladder by
            # construction, and `reserve=True` is how the instrument layer
            # says the severity is declared rather than measured at round 0.
            new_rungs = [Constraint(family, severity, reserve=True)
                         for family, severities in sorted(admitted.items())
                         for severity in sorted(severities)]
            if not new_rungs:
                return []
            new_cells, new_slots = ladder_cells(prescreen, new_rungs)
            new_prompts = [prompt_cell(c, _by_id(prescreen)[c.topic_id],
                                       slot_map=new_slots,
                                       topic_split="prescreen")
                           for c in new_cells]
            round_index = len(expansion_rounds_seen)
            expansion_rounds_seen.append(new_rungs)
            new_rows = generate_and_score(
                tree.model_key, new_prompts, stage=C.STAGE_REGIME, cap=cap,
                device=device,
                run_dir=(tree.backend_runs(C.STAGE_REGIME)
                         / f"expansion-{round_index}"),
                instances=tuple(new_slots.values()), slot_map=new_slots,
                study_id=tree.context.study_id,
                protocol_identity=protocol_identity(tree, C.STAGE_REGIME),
                generate=generate)
            rows_out = difficulty_table(new_rows, new_rungs)
            for rung, row in zip(new_rungs, rows_out):
                table.append(row)
                by_label[row["candidate"]] = row
                measured.append(rung)
            # V6-E02: the criterion reads `eligible`, `structural_tier`,
            # `feature_group` and `constraint_class`, and a raw difficulty
            # row carries none of them. v5 returned the raw rows, so every
            # rung the expansion measured was counted as ineligible by the
            # criterion the expansion exists to satisfy. The retention
            # verdict is recomputed over everything measured so far, because
            # a new rung has to be carried before it can be eligible.
            carried_now = regime_stage.carried_set(_verdicts(measured,
                                                             by_label))
            return regime_stage.coverage_rows(rows_out, carried_now)

        expansion_rounds_seen: list[list[Constraint]] = []
        expansion = regime_stage.run_expansion(
            eligible_rows, iota_a=iota_a, measured=measured_by_family,
            measure=measure_reserve)
        coverage = expansion["coverage"]
        screen_statuses = list(expansion["identification_statuses"])
        if expansion["rounds"]:
            # The expansion measured new rungs; the carried set and every
            # quantity derived from it are recomputed over the whole table.
            verdicts = _verdicts(measured, by_label)
            carried = regime_stage.carried_set(verdicts)
            eligible_rows = regime_stage.coverage_rows(table, carried)
    # §12.7's budget reads the structural tier and the pre-screen iota, and
    # a retention verdict carries neither: the two live on the difficulty
    # table this stage just built. Joining them here is what makes the budget
    # a function of measured quantities rather than of a caller's argument.
    carried_rows = [{**by_label[v["candidate"]],
                     "structural_tier": FAMILIES[by_label[v["candidate"]]
                                                 ["kind"]].structural_tier,
                     "prescreen_iota": by_label[v["candidate"]]["iota"]}
                    for v in verdicts if v["carried"]]
    # §12.7 orders the Tier-3 rungs by ascending |iota - iota_A|. With A
    # unmeasured on the pre-screen this passed the literal 0.5, which is not
    # iota_A and is not registered anywhere; the ordering it produced decided
    # which Tier-3 rungs calibration measures. A's severity is measured now,
    # so the placeholder is unreachable --- and if it ever were reached the
    # record says the ordering could not be computed rather than reporting an
    # ordering against a number nobody registered.
    priority = regime_stage.calibration_priority(
        carried_rows, iota_a_prescreen=iota_a if iota_a is not None else 0.5)
    if iota_a is None:
        priority = {**priority,
                    "ordering_not_computed":
                        "§12.7 orders Tier-3 by |iota - iota_A| and iota_A "
                        "was not measured on the pre-screen"}

    return {
        "stage": C.STAGE_REGIME,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_REGIME],
        "outcome": "PASS",
        "inputs": {"gate0": {"stage": C.STAGE_GATE0}},
        "producing_commit": producing_commit,
        "selected_cap": cap,
        "cap_selection": cap_result,
        "difficulty_table": table,
        "retention_verdicts": verdicts,
        "carried_set": carried,
        "n_carried": len(carried),
        "vocabulary_frozen": True,
        "vocabulary_frozen_statement":
            "§12.6's expansion picks from §7.10's frozen reserve and never "
            "authors a family; no stage after this one may measure a rung "
            "that is not on carried_set or reached by a recorded expansion",
        "coverage": coverage,
        # §12.6's expansion, its rounds and the disposition it reached. When
        # C1-C6 are unmet after the registered rounds the statuses carry
        # REFERENCE_SUPPORT_NOT_IDENTIFIED **at design time**, and Gate 3C
        # reads them: the arms §12.6 forbids are not admitted downstream.
        "expansion": expansion,
        "identification_statuses": sorted(set(screen_statuses)),
        "coverage_eligibility_formulation": (
            (eligible_rows[0]["eligibility"]["formulation"])
            if iota_a is not None and eligible_rows else None),
        "calibration_priority": priority,
        "iota_a_prescreen": iota_a,
        "iota_a_prescreen_severity": (iota_a_row["severity"]
                                      if iota_a_row is not None else None),
        "iota_a_prescreen_rule":
            "§12.6: A's pre-screen instructed compliance at the severity "
            f"whose solo compliance is nearest §12.3's aim of {C.TARGET_AIM}",
        "topic_split_used": "prescreen",
        "canonical_verifier_hash": verifier_source_hash(),
    }


def _by_id(topics: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {t["topic_id"]: t for t in topics}


def _screen_responder(row: Mapping[str, Any]) -> str:
    """Deterministic screen text. Not a model; see ``fake_backend``."""
    words = ["thus", "hence", "though", "whereas", "indeed", "namely",
             "instead", "overall", "answer", "text", "reply", "words"]
    seed = sum(ord(ch) for ch in str(row["row_id"]))
    return " ".join(words[(seed + i) % len(words)]
                    for i in range(70)).capitalize() + "."


def run_regime_screen(tree: ModelTree, *, producing_commit: str | None = None,
                      environment_digest: str = "",
                      bank: TopicBank | None = None, device: int = 0,
                      generate: Callable[..., dict[str, Any]] | None = None,
                      caps: Sequence[int] = C.COMPLETION_CAPS,
                      rungs: Sequence[Constraint] | None = None
                      ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_REGIME,
        compute=lambda _prev: regime_payload(
            tree, producing_commit=commit, bank=bank, device=device,
            generate=generate, caps=caps, rungs=rungs),
        producing_commit=commit, environment_digest=environment_digest)


# ---------------------------------------------------------------- Gate 1

def gate1_provenance(tree: ModelTree, *, producing_commit: str,
                     bank: TopicBank, texts: Sequence[str]) -> dict[str, Any]:
    """§10.2 condition 10, established rather than asserted.

    Five facts, each derived from something that exists: the predecessor
    record verified, the carry-over record holds, no reserved topic set has
    been spent, a producing commit is recorded, and this replication has no
    Gate 1 record yet. The condition reads all five, and a caller that
    supplied none --- which is how this runner was first written --- would
    fail Gate 1 for a reason that has nothing to do with the instruments.
    """
    from dci1v7.verifiers.carryover import carry_over_record

    predecessor = transitions.read_stage_record(tree, C.STAGE_REGIME)
    spent = sorted({t["topic_id"] for name in C.RESERVED_TOPIC_SETS
                    for t in bank.sets[name]}
                   & _topics_touched(tree))
    carry = carry_over_record()
    return {
        "predecessor_verified": predecessor.get("outcome") == "PASS",
        "predecessor_stage": C.STAGE_REGIME,
        "carry_over_passed": bool(carry.get("passed", True)),
        "carry_over": carry,
        "reserved_sets_unspent": not spent,
        "reserved_spent": spent,
        "producing_commit": producing_commit,
        "no_gate1_record_exists_yet": not tree.stage_record(
            C.STAGE_GATE1).exists(),
        "model_key": tree.model_key,
        "n_texts": len(texts),
    }


def _topics_touched(tree: ModelTree) -> set[str]:
    """Every topic id that appears in a scored row this replication holds."""
    import json as _json

    from dci1v7.engine.paths import current_files

    touched: set[str] = set()
    for stage in C.STAGE_SEQUENCE:
        root = tree.backend_runs(stage)
        if not root.exists():
            continue
        for path in current_files(root, "scored.jsonl"):
            for line in path.read_text().splitlines():
                if line.strip():
                    touched.add(_json.loads(line)["topic_id"])
    return touched


def gate1_payload(tree: ModelTree, *, producing_commit: str,
                  regime_record: Mapping[str, Any],
                  bank: TopicBank | None = None,
                  calibration_texts: Sequence[str] = (),
                  determinism_sample: int | None = 400,
                  verdict_sample: int | None = 1200) -> dict[str, Any]:
    """§18 stage 5: §10.2 over the instrument population, plus §10.7 A-E.

    The instrument population is §7's **declared range**, which is study-wide,
    so this stage's evidence does not depend on which candidates the regime
    screen carried. What it does depend on is that the vocabulary is closed,
    which is why it follows stage 4.
    """
    texts = list(calibration_texts)
    if not texts:
        raise ProtocolError(
            "§10.2's evidence is computed over real generated text; Gate 1 "
            "needs the regime screen's responses and was given none")
    evidence = gate1_stage.collect_evidence(
        texts, determinism_sample=determinism_sample,
        verdict_sample=verdict_sample)
    specification_evidence = gate1_stage.collect_specification_evidence(
        specification=specification.specification_report()
        if hasattr(specification, "specification_report") else None,
        mutation=mutation.mutation_report()
        if hasattr(mutation, "mutation_report") else None)
    provenance = gate1_provenance(
        tree, producing_commit=producing_commit,
        bank=bank if bank is not None else load_bank(), texts=texts)
    payload = gate1_stage.gate1_payload(
        evidence=evidence, specification_evidence=specification_evidence,
        provenance={**provenance,
                    "regime_record_cap": regime_record.get("selected_cap")},
        measurement_basis=C.MEASUREMENT_BASIS)
    audit = verifier_audit.audit_report() \
        if hasattr(verifier_audit, "audit_report") else {}
    return {
        **payload,
        "stage": C.STAGE_GATE1,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE1],
        "inputs": {"regime": {"stage": C.STAGE_REGIME,
                              "carried": regime_record.get("n_carried")}},
        "producing_commit": producing_commit,
        "instrument_population": C.N_INSTRUMENTS,
        "verifiers": C.N_VERIFIERS,
        "canonical_verifier_hash": verifier_source_hash(),
        "wording_hash": wording_source_hash(),
        "hashes_frozen": ["canonical_verifier_hash", "wording_hash"],
        "verifier_audit": audit,
        "measurement_basis": C.MEASUREMENT_BASIS,
        "scope_sentence": C.SCOPE_SENTENCE,
    }


def run_gate1(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              calibration_texts: Sequence[str] | None = None,
              determinism_sample: int | None = 400,
              verdict_sample: int | None = 1200) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    texts = (list(calibration_texts) if calibration_texts is not None
             else screen_texts(tree))
    return run_stage(
        tree, C.STAGE_GATE1,
        compute=lambda previous: gate1_payload(
            tree, producing_commit=commit, regime_record=previous, bank=bank,
            calibration_texts=texts,
            determinism_sample=determinism_sample,
            verdict_sample=verdict_sample),
        producing_commit=commit, environment_digest=environment_digest)
