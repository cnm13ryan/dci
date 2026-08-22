"""§18 stages 15-18: masked analysis, the one-shot unmask, the unmasked
analysis, and the final report.

The path is one line and every arrow is a signed record:

    confirmatory rows -> observation table -> mask -> masked analysis ->
    sealed masked artifact -> one-shot unmask -> registered final analysis ->
    final report.

**The mask is a commitment device (§20).** The masked analysis runs the whole
registered pipeline on a *permuted* view, seals its result and its analysis
code hash, and only then is the key readable. What that buys is that the
analysis code cannot be adjusted after seeing which companion is which --- and
what it costs is that a defect found after the seal cannot be repaired, which
is exactly what happened to v4r4's L4 emitter. That is why §19's pilot runs the
claim-ladder tests *before* qualification.

**Unmask exactly once.** ``analysis/masking.unmask`` binds the event to the
sealed masked artifact's hash and to the analysis code hash, and the
``UNMASKING`` stage record is write-once like every other. A second unmask is
refused by ``assert_transition_legal``: the record already exists, and a
repair is a new protocol revision, not a rewritten record. There is no
"supersede this unmask" path here; §28's supersession machinery is explicit,
historical and separate.

**A quantity is computed only when its identification status licenses it.**
Otherwise the entry is ``NOT_IDENTIFIED`` with the status that explains it ---
never zero, never a bare NaN, never an omission, and never a substitute
estimand that happened to be computable. ``NOT_IDENTIFIED`` and "we measured
it and it was small" are different results and the record distinguishes them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import sha_obj

from dci1v5.analysis import claims, estimators, masking, spectrum
from dci1v5.analysis.bootstrap import bootstrap_family
from dci1v5.analysis.observations import ObservationTable, build_observations
from dci1v5.engine import transitions
from dci1v5.engine.paths import ModelTree
from dci1v5.protocol import constants as C
from dci1v5.protocol import identification, seeds
from dci1v5.run.confirmatory_run import collect_rows
from dci1v5.run import final_report_checks
from dci1v5.run.freeze_run import load_freeze
from dci1v5.run.lifecycle import StageOutcome, run_stage
from dci1v5.stages import final_report as final_report_stage
from dci1v5.stages import support as support_stage

__all__ = ["ANALYSIS_MODULES", "NOT_IDENTIFIED", "analysis_code_hash",
           "observation_table", "estimate_all", "masked_payload",
           "run_masked_analysis", "unmask_payload", "run_unmasking",
           "unmasked_payload", "run_unmasked_analysis", "final_report_payload",
           "run_final_report"]

NOT_IDENTIFIED = "NOT_IDENTIFIED"

#: The modules whose bytes decide what the analysis computes. Hashed before
#: the mask is sealed and re-verified before the unmask, so an analysis that
#: moved between the two is refused rather than reported.
ANALYSIS_MODULES = ("analysis/observations.py", "analysis/estimators.py",
                    "analysis/spectrum.py", "analysis/bootstrap.py",
                    "analysis/intervals.py", "analysis/claims.py",
                    "analysis/masking.py", "run/analysis_run.py")


def analysis_code_hash() -> str:
    here = Path(__file__).resolve().parents[1]
    return masking.analysis_code_hash([here / name
                                       for name in ANALYSIS_MODULES])


def observation_table(rows: Sequence[Mapping[str, Any]], *, m_draws: int
                      ) -> ObservationTable:
    return ObservationTable(build_observations(list(rows), m_draws=m_draws))


def _licensed(statuses: Sequence[str]) -> dict[str, str | None]:
    """Which estimand each identification status blocks.

    Every entry carries the status that blocked it, so a reader of the record
    can see *why* a quantity was not computed and adding a status without
    deciding what it blocks stays a visible omission.

    **``REFERENCE_SUPPORT_NOT_IDENTIFIED`` blocks the whole reference-dependent
    set**, derived by ``protocol/identification.py``'s one rule rather than
    listed here. An earlier revision named five members; the other forty-three
    were attempted, returned no vector because the design supplies no cell for
    them, and were recorded as ``not_computable`` --- which reads as a design
    that was never asked rather than as §34 D6's irreversible verdict. The
    difference matters because the freeze binds the D6 set and the final
    report is checked against it.
    """
    blocked: dict[str, str] = {}
    statuses = set(statuses)
    if "REFERENCE_SUPPORT_NOT_IDENTIFIED" in statuses or \
            "EXCESS_NOT_IDENTIFIED" in statuses:
        for member in identification.AFFECTED_ESTIMANDS:
            blocked[member] = "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    if "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in statuses:
        blocked["delta_difficulty"] = "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    if "NEAR_FORM_ARM_NOT_AVAILABLE" in statuses:
        blocked["Delta_near"] = "NEAR_FORM_ARM_NOT_AVAILABLE"
    if "CLASS_ARM_NOT_AVAILABLE" in statuses:
        blocked["Delta_broad"] = "CLASS_ARM_NOT_AVAILABLE"
    if "DIFFICULTY_COORDINATE_DEGENERATE" in statuses:
        blocked["delta_difficulty"] = "DIFFICULTY_COORDINATE_DEGENERATE"
    return blocked


def _vector(fn: Callable[..., Any], *args: Any, **kwargs: Any
            ) -> list[float] | None:
    """Compute a per-block vector, or None when the design does not supply it.

    A missing cell is an ``IntegrityError`` from the observation table --- the
    analysis fails closed on a missing cell (§21) --- and that is a different
    fact from an unidentified estimand. It is returned as ``None`` and the
    caller records which of the two it was.
    """
    try:
        return list(fn(*args, **kwargs))
    except Exception:
        return None


def spectrum_inputs(table: ObservationTable,
                    slot_families: Mapping[str, str]
                    ) -> dict[str, spectrum.SpectrumInput]:
    """§11.7's nine points per configuration, from the table and the freeze.

    ``slot_families`` is the freeze's slot map reduced to slot -> family, for
    the core and spectrum slots only: §11.7 fits three families of three
    severities, A is excluded because the relation is what predicts A, and the
    near-form and broad-class slots are not on the ladder.

    Returns one input per configuration, because ``delta_difficulty`` is a
    per-configuration member of F1 exactly as ``Delta_R`` is.
    """
    family_of = {slot: family for slot, family in slot_families.items()
                 if slot in set(C.CORE_SLOTS) | set(C.SPECTRUM_SLOTS)}
    out: dict[str, spectrum.SpectrumInput] = {}
    for configuration in C.CONFIGURATIONS:
        slots = [s for s in family_of if table.has_composed(
            "B", s, configuration)]
        if len(slots) != len(family_of) or not table.has_composed(
                "B", "A", configuration):
            continue
        b_with = {s: estimators.composed_vector(table, "B", s, configuration)
                  for s in slots}
        b_with["A"] = estimators.composed_vector(table, "B", "A",
                                                 configuration)
        out[configuration] = spectrum.SpectrumInput(
            blocks=tuple(table.blocks),
            family_of={s: family_of[s] for s in slots},
            b_solo=estimators.solo_vector(table, "B"),
            b_with=b_with,
            companion_solo={s: estimators.solo_vector(table, s)
                            for s in slots},
            companion_chance={s: estimators.chance_vector(table, s)
                              for s in slots},
            a_solo=estimators.solo_vector(table, "A"),
            a_chance=estimators.chance_vector(table, "A"))
    return out


def estimate_all(table: ObservationTable, *, statuses: Sequence[str],
                 arms: Sequence[str], seed: int,
                 resamples: int = C.BOOTSTRAP_RESAMPLES,
                 slot_families: Mapping[str, str] | None = None
                 ) -> dict[str, Any]:
    """Every registered quantity, or ``NOT_IDENTIFIED`` with its reason.

    The five order contrasts of F11 are computed **across** configurations,
    which is why F11 is declared as the one cross-configuration family: an
    order contrast has no value inside a single configuration and v4r4 had no
    registered direct contrast at all.

    ``slot_families`` supplies §11.7's family grouping and is passed **only
    after unmasking**. A's point sits inside the permuted group, so
    ``delta_difficulty`` and the fit's coefficients have no masked-phase value
    (§20); without it the member is recorded ``NOT_IDENTIFIED`` with that
    reason, which is a different fact from an unidentified design and is
    written as such.
    """
    blocked = _licensed(statuses)
    post_unmask = bool(slot_families)
    spectrum_by_configuration = (spectrum_inputs(table, slot_families)
                                 if post_unmask else {})
    # §20 names the members that have no masked-phase value: A's point is
    # inside the permuted group, so a contrast of A against the reference set
    # is a contrast against a set A may have been permuted into. They are
    # withheld here rather than computed and discarded downstream --- a number
    # that exists is a number a masked-phase decision can see.
    withheld = () if post_unmask else masking.MASKED_PHASE_FORBIDDEN_MEMBERS
    out: dict[str, Any] = {"configurations": {}, "cross_configuration": {},
                           "blocked": blocked,
                           "spectrum_phase": ("post_unmask" if post_unmask
                                              else "masked"),
                           "masked_phase_members_withheld": list(withheld),
                           "not_identified": [], "not_computable": []}

    def record(bucket: dict[str, Any], member: str,
               vector: list[float] | None) -> None:
        if member in withheld:
            bucket[member] = {
                "status": NOT_IDENTIFIED, "reason": "MASKED_PHASE",
                "detail": masking.MASKED_PHASE_DECLARATIONS.get(
                    member, "§20: not computable before the unmask")}
            out["not_computable"].append(member)
            return
        if member in blocked:
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": blocked[member]}
            out["not_identified"].append(member)
            return
        if vector is None:
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": "the admitted design supplies no "
                                        "cell for this contrast"}
            out["not_computable"].append(member)
            return
        bucket[member] = {"status": "IDENTIFIED", "n_blocks": len(vector),
                          "point": sum(vector) / len(vector)}
        bucket[member]["_vector"] = vector

    for configuration in C.CONFIGURATIONS:
        bucket: dict[str, Any] = {}
        record(bucket, "D(B<-A)",
               _vector(estimators.delivery_loss, table, "B", "A",
                       configuration=configuration))
        record(bucket, "D(A<-B)",
               _vector(estimators.delivery_loss, table, "A", "B",
                       configuration=configuration))
        record(bucket, "Lambda",
               _vector(estimators.asymmetry, table, configuration))
        record(bucket, "Delta_R",
               _vector(estimators.delta_r, table, configuration))
        # §11.7 and §17.2: a replicate refits the relation, so the member is
        # a *function* of the replicate's index vector, not a per-block
        # vector. ``bootstrap_family`` takes both kinds and gives them one
        # index draw, which is what keeps F1's simultaneous interval coherent
        # --- and an earlier revision computed this member nowhere at all, so
        # F1's critical value was taken over five members instead of six.
        _record_delta_difficulty(bucket, out, spectrum_by_configuration,
                                 configuration, blocked)
        record(bucket, "Xi", _vector(estimators.xi, table, configuration))
        for index, slot in enumerate(C.CORE_SLOTS, start=1):
            record(bucket, f"Delta_{index}",
                   _vector(estimators.delta_j, table, slot, configuration))
        record(bucket, "Delta_near",
               _vector(estimators.delta_near, table, configuration))
        record(bucket, "Delta_broad",
               _vector(estimators.delta_broad, table, configuration))
        record(bucket, "Delta^A",
               _vector(estimators.delta_a, table, configuration))
        record(bucket, "D(Rbar<-A)",
               _vector(estimators.d_rbar_from, table, "A", configuration))
        record(bucket, "D(Rbar<-B)",
               _vector(estimators.d_rbar_from, table, "B", configuration))
        record(bucket, "D(Rbar<-Rbar')",
               _vector(estimators.d_rbar_rbar, table, configuration))
        out["configurations"][configuration] = bucket

    cross = out["cross_configuration"]
    for member in C.FAMILY_MEMBERS["F11"]:
        record(cross, member,
               _vector(estimators.order_contrast, table, member))

    out["intervals"] = _intervals(out, seed=seed, resamples=resamples,
                                  n_blocks=len(table.blocks))
    return out


def _record_delta_difficulty(bucket: dict[str, Any], out: dict[str, Any],
                             inputs: Mapping[str, Any], configuration: str,
                             blocked: Mapping[str, str]) -> None:
    """§11.7's residual, or the reason there is no value for it.

    Three different absences, written as three different reasons: the design
    did not identify the spectrum; this is the masked phase and A's point is
    inside the permuted group; or the fit is degenerate on the observed
    sample. None of them is zero and none of them is an omission.
    """
    member = "delta_difficulty"
    if member in blocked:
        bucket[member] = {"status": NOT_IDENTIFIED, "reason": blocked[member]}
        out["not_identified"].append(member)
        return
    data = inputs.get(configuration)
    if data is None:
        bucket[member] = {
            "status": NOT_IDENTIFIED,
            "reason": "MASKED_PHASE" if not inputs else
                      "the admitted design supplies no spectrum ladder for "
                      "this configuration",
            "detail": "§20: A's point is inside the permuted group, so the "
                      "residual has no masked-phase value" if not inputs
                      else None}
        out["not_computable"].append(member)
        return
    point = spectrum.estimate(data)
    if point["degenerate"]:
        bucket[member] = {"status": NOT_IDENTIFIED,
                          "reason": "DIFFICULTY_COORDINATE_DEGENERATE",
                          "detail": point.get("reason")}
        out["not_identified"].append(member)
        return
    bucket[member] = {
        "status": "IDENTIFIED", "n_blocks": len(data.blocks),
        "point": float(point["delta_difficulty"]),
        "slope": float(point["slope"]),
        "predicted_at_A": float(point["predicted_at_A"]),
        "support": point["support"],
        "refit_per_replicate": True,
        # The callable form §17.2 requires: every replicate resamples blocks,
        # recomputes the difficulties, refits the non-A relation, predicts at
        # A and recomputes the residual.
        "_vector": lambda picks, _d=data: float(
            spectrum.estimate(_d, list(picks))["delta_difficulty"]),
    }


def _intervals(estimates: Mapping[str, Any], *, seed: int, resamples: int,
               n_blocks: int) -> dict[str, Any]:
    """Simultaneous intervals per §15 family, one index draw per replicate."""
    out: dict[str, Any] = {}
    if n_blocks < 2:
        return {"skipped": "the block bootstrap needs at least two blocks"}
    for family, members in C.FAMILY_MEMBERS.items():
        source = (estimates["cross_configuration"]
                  if family in C.CROSS_CONFIGURATION_FAMILIES else None)
        configurations = ([None] if source is not None
                          else list(C.CONFIGURATIONS))
        for configuration in configurations:
            bucket = (source if source is not None
                      else estimates["configurations"][configuration])
            usable = {m: bucket[m]["_vector"] for m in members
                      if m in bucket and "_vector" in bucket[m]}
            if not usable:
                continue
            result = bootstrap_family(usable, seed=seed,
                                      configuration=configuration or "cross",
                                      family=family, n_blocks=n_blocks,
                                      resamples=resamples)
            key = f"{family}:{configuration or 'cross'}"
            out[key] = {
                name: {"estimate": member.estimate,
                       "lower": member.simultaneous_lower,
                       "upper": member.simultaneous_upper,
                       "half_width": member.half_width,
                       # §31's table needs the standard error and the
                       # marginal bounds beside the simultaneous ones, and
                       # §17.1 reports the marginal interval alongside. They
                       # were computed and then dropped here, so the final
                       # report had no producer for four of its own fields.
                       "standard_error": member.standard_error,
                       "marginal_lower": member.marginal_lower,
                       "marginal_upper": member.marginal_upper,
                       "refit_per_replicate": member.refit_per_replicate,
                       "degenerate": member.degenerate}
                for name, member in result.members.items()}
    return out


def _strip_vectors(estimates: Mapping[str, Any]) -> dict[str, Any]:
    """The record form: per-block vectors are working state, not evidence."""
    def clean(bucket: Mapping[str, Any]) -> dict[str, Any]:
        return {k: {kk: vv for kk, vv in v.items() if kk != "_vector"}
                for k, v in bucket.items()}
    return {
        "configurations": {k: clean(v)
                           for k, v in estimates["configurations"].items()},
        "cross_configuration": clean(estimates["cross_configuration"]),
        "blocked": estimates["blocked"],
        "spectrum_phase": estimates["spectrum_phase"],
        "masked_phase_members_withheld":
            list(estimates.get("masked_phase_members_withheld", ())),
        "not_identified": sorted(set(estimates["not_identified"])),
        "not_computable": sorted(set(estimates["not_computable"])),
        "intervals": estimates.get("intervals", {}),
    }


# ------------------------------------------------------------ stage 15

def masked_payload(tree: ModelTree, *, producing_commit: str,
                   entropy: int | None = None) -> dict[str, Any]:
    freeze_record = load_freeze(tree)
    freeze = freeze_record["freeze"]
    confirmatory = transitions.read_stage_record(tree, C.STAGE_CONFIRMATORY)
    rows = collect_rows(tree)
    if not rows:
        raise ProtocolError(
            "§20: the masked analysis has no confirmatory rows to mask")
    observations = build_observations(rows, m_draws=freeze["m_draws"])
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=entropy)
    effectiveness = masking.assert_mask_effective(observations, mask)
    masked_view = masking.apply_mask(observations, mask)

    mask_dir = tree.mask_dir("confirmatory_mask")
    mask_dir.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(tree.mask_key_path("confirmatory_mask"), mask)
    records = [dict(vars(o)) for o in masked_view]
    # §20's cleanliness rule, on the path that writes the artifact. It existed
    # and nothing called it, so the one guarantee about what the masked view
    # may contain was never checked against what was written.
    masking.assert_masked_view_clean(records)
    tree.masked_view("confirmatory_mask").write_text(
        "".join(json.dumps(r, sort_keys=True, default=str) + "\n"
                for r in records))

    table = ObservationTable([_as_observation(o) for o in masked_view])
    statuses = list(freeze_record["identification_statuses"])
    estimates = estimate_all(table, statuses=statuses,
                             arms=freeze["admitted_arms"],
                             seed=seeds.bootstrap_seed(
                                 "masked", tree.model_key),
                             resamples=C.BOOTSTRAP_RESAMPLES)
    result = _strip_vectors(estimates)
    masking.assert_delta_difficulty_not_masked(result)
    payload = {
        "stage": C.STAGE_MASKED_ANALYSIS,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_MASKED_ANALYSIS],
        "outcome": "PASS",
        "inputs": {"confirmatory": {"stage": C.STAGE_CONFIRMATORY,
                                    "n_rows": confirmatory["n_rows"]},
                   "freeze": {"stage": C.STAGE_GATE5,
                              "freeze_hash": freeze_record["freeze_hash"]}},
        "producing_commit": producing_commit,
        "mask_namespace": "confirmatory_mask",
        "mask_effectiveness": effectiveness,
        # §20 requires which order contrasts are masked-phase computable to be
        # derived by one named function and recorded here rather than assumed.
        "masked_phase_order_contrasts":
            masking.masked_phase_order_contrasts(mask),
        "masked_result": result,
        "analysis_code_hash": analysis_code_hash(),
        "n_observations": len(observations),
        "sealed": True,
        "seal_statement":
            "§20: the masked result and the analysis code hash are sealed "
            "here; the key is readable only through the UNMASKING stage, and "
            "a defect found after this point cannot be repaired --- which is "
            "why §19's pilot runs the claim-ladder tests before qualification",
    }
    payload["masked_result_hash"] = sha_obj(result)
    return payload


def _as_observation(masked: Any) -> Any:
    """A masked observation, re-typed for the observation table.

    The two names that differ are the two the mask acts on: the companion is
    the **permuted** label and the cell is its pseudonym. Everything else is
    the observation's own value. Copying only the fields whose names happened
    to match left ``cell_id``, ``arm``, ``companion_slot``, ``draws`` and
    ``processing_failures`` unset and raised on construction, which is why
    the masked stage had never run.
    """
    from dci1v5.analysis.observations import Observation

    return Observation(
        block_id=masked.block_id, cell_id=masked.masked_cell_id,
        arm=masked.arm, outcome_slot=masked.outcome_slot,
        companion_slot=masked.companion_label, position=masked.position,
        configuration=masked.configuration, draws=masked.draws,
        compliance=masked.compliance, graded=masked.graded,
        vacuity=masked.vacuity, truncation=masked.truncation,
        non_vacuous_compliance=masked.non_vacuous_compliance,
        graded_threshold=masked.graded_threshold,
        response_words=masked.response_words,
        processing_failures=masked.processing_failures,
        present=masked.present)


def run_masked_analysis(tree: ModelTree, *, producing_commit: str | None = None,
                        environment_digest: str = "",
                        entropy: int | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_MASKED_ANALYSIS,
        compute=lambda _prev: masked_payload(tree, producing_commit=commit,
                                             entropy=entropy),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 16

def unmask_payload(tree: ModelTree, *, producing_commit: str
                   ) -> dict[str, Any]:
    """§20's irreversible unmask, bound to the sealed masked artifact.

    The stage record is write-once, so a second unmask is refused by the
    stage machine rather than by a flag this function keeps. There is no
    supersession path here on purpose: re-unmasking after seeing a result is
    the failure §20 exists to prevent, and making it require an explicit,
    historical, separately-recorded supersession is the point.
    """
    masked = transitions.read_stage_record(tree, C.STAGE_MASKED_ANALYSIS)
    current = analysis_code_hash()
    if current != masked["analysis_code_hash"]:
        raise ProtocolError(
            "§20: the analysis code moved between the seal and the unmask. "
            f"Sealed {masked['analysis_code_hash']}, now {current}. An "
            "unmasked analysis under a moved analysis hash is refused")
    key = masking.MaskKey(tree.mask_key_path("confirmatory_mask"))
    event = masking.unmask(key, analysis_code_hash=current,
                           masked_outputs_hash=masked["masked_result_hash"])
    return {
        "stage": C.STAGE_UNMASKING,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKING],
        "outcome": "PASS",
        "inputs": {"masked": {"stage": C.STAGE_MASKED_ANALYSIS,
                              "masked_result_hash":
                                  masked["masked_result_hash"]}},
        "producing_commit": producing_commit,
        "unmasked": True,
        "mask_key_hash": sha_obj(fs.read_json(
            tree.mask_key_path("confirmatory_mask"))),
        "unmask_event": event,
        "analysis_code_hash": current,
        "once_only":
            "the stage record is write-once; a second unmask is refused by "
            "assert_transition_legal and a repair is a new protocol "
            "revision, not a rewritten record",
    }


def run_unmasking(tree: ModelTree, *, producing_commit: str | None = None,
                  environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_UNMASKING,
        compute=lambda _prev: unmask_payload(tree, producing_commit=commit),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 17

def unmasked_payload(tree: ModelTree, *, producing_commit: str
                     ) -> dict[str, Any]:
    freeze_record = load_freeze(tree)
    freeze = freeze_record["freeze"]
    unmask_record = transitions.read_stage_record(tree, C.STAGE_UNMASKING)
    if not unmask_record.get("unmasked"):
        raise ProtocolError("§20: the mask has not been lifted")
    rows = collect_rows(tree)
    table = observation_table(rows, m_draws=freeze["m_draws"])
    statuses = list(freeze_record["identification_statuses"])
    # §20: the fit's coefficients and delta_difficulty are post-unmasking, so
    # this is the one call that gets §11.7's family grouping.
    slot_families = {slot: (value[0] if isinstance(value, (list, tuple))
                            else value["kind"])
                     for slot, value in (freeze_record.get("slot_map")
                                         or {}).items()}
    estimates = estimate_all(
        table, statuses=statuses, arms=freeze["admitted_arms"],
        seed=seeds.bootstrap_seed("unmasked", tree.model_key),
        resamples=C.BOOTSTRAP_RESAMPLES, slot_families=slot_families)
    result = _strip_vectors(estimates)
    statements = _statements(result, statuses=statuses,
                             measurement_basis=freeze["measurement_basis"],
                             near_form_available="NEAR_FORM_ARM_NOT_AVAILABLE"
                             not in statuses)
    success = support_stage.methodological_success(
        freeze["support_realised"], gate4_passed=True)
    # §34 D6: the last place an estimate could appear for a member Gate 3C
    # marked NOT_IDENTIFIED. `_licensed` already blocks them, so this asserts
    # the outcome of that rather than repeating it --- which is the point: a
    # future estimator added beside `estimate_all` is checked too.
    identification.assert_not_rehabilitated(
        {"estimands": result}, gate3c=freeze_record.get("non_identification"),
        where="§34 D6: UNMASKED_ANALYSIS")
    return {
        "stage": C.STAGE_UNMASKED_ANALYSIS,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKED_ANALYSIS],
        "outcome": "PASS",
        "inputs": {"unmasking": {"stage": C.STAGE_UNMASKING},
                   "freeze": {"stage": C.STAGE_GATE5,
                              "freeze_hash": freeze_record["freeze_hash"]}},
        "producing_commit": producing_commit,
        "estimands": result,
        "statements": statements,
        "identification_statuses": statuses,
        "success_criterion": success,
        "measurement_basis": freeze["measurement_basis"],
        "scope_sentence": C.SCOPE_SENTENCE,
        "analysis_code_hash": analysis_code_hash(),
        "projection_audit": [],
        "spectrum_families": slot_families,
        "not_identified_is_not_zero":
            "a quantity the design does not identify is recorded "
            f"{NOT_IDENTIFIED} with the status that explains it, never as "
            "zero, a bare NaN, an omission or a substitute estimand",
    }


def _statements(result: Mapping[str, Any], *, statuses: Sequence[str],
                measurement_basis: str, near_form_available: bool
                ) -> list[dict[str, Any]]:
    """§17.5's guarded emitters, applied per configuration.

    An estimand the design did not identify never reaches an emitter: the
    emitter is guarded, but a guard that is only ever reached with a real
    interval is a guard that has never been tested, and the record says which
    members were withheld rather than leaving the reader to notice.
    """
    out: list[dict[str, Any]] = []
    for configuration, bucket in result["configurations"].items():
        entry = bucket.get("D(B<-A)")
        intervals = result.get("intervals", {}).get(f"F1:{configuration}", {})
        if not entry or entry.get("status") != "IDENTIFIED":
            continue
        interval = intervals.get("D(B<-A)")
        if interval is None:
            continue
        position = 1 if configuration == C.OUTCOME_FIRST else 2
        out.append(claims.emit_l1(
            configuration=configuration, cell="pair:A+B",
            outcome_position=position, measurement_basis=measurement_basis,
            member="D(B<-A)",
            interval=claims.Interval("D(B<-A)", interval["estimate"],
                                     interval["lower"], interval["upper"]),
            solo_headroom=True))
    return out


def run_unmasked_analysis(tree: ModelTree,
                          *, producing_commit: str | None = None,
                          environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_UNMASKED_ANALYSIS,
        compute=lambda _prev: unmasked_payload(tree, producing_commit=commit),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 18

def final_report_payload(tree: ModelTree, *, producing_commit: str,
                         repo_root: Path | str | None = None
                         ) -> dict[str, Any]:
    """§31's machine-readable table, from signed records only.

    Then stage 18's own checks (``run/final_report_checks.py``): the §33 items
    the pre-freeze audit deferred, plus every traceability claim that only
    becomes checkable once the table exists. A mandatory failure records
    ``outcome`` ``FAIL`` --- ``FINAL_REPORT`` has no successor to refuse, so
    the failure has to be on the record itself.
    """
    freeze_record = load_freeze(tree)
    analysis = transitions.read_stage_record(tree, C.STAGE_UNMASKED_ANALYSIS)
    hashes = {stage: sha_obj(transitions.read_stage_record(tree, stage))
              for stage in C.STAGE_SEQUENCE
              if tree.stage_record(stage).exists()}
    rows = _report_rows(tree, analysis, freeze_record,
                        hashes[C.STAGE_UNMASKED_ANALYSIS])
    report = final_report_stage.build_final_report(
        model_key=tree.model_key, rows=rows,
        statements=analysis["statements"],
        success_criterion=analysis["success_criterion"],
        identification_statuses=analysis["identification_statuses"],
        admitted_arms=freeze_record["admitted_arms"],
        projection_audit=analysis.get("projection_audit", ()),
        stage_record_hashes=hashes)
    root = repo_root if repo_root is not None else tree.context.repo_root
    checks = final_report_checks.final_report_checks(tree, report,
                                                     repo_root=root)
    failed = [c for c in checks if c["mandatory"] and c["verdict"] != "PASS"]
    return {
        **report,
        "stage": C.STAGE_FINAL_REPORT,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_FINAL_REPORT],
        "outcome": "PASS" if not failed else "FAIL",
        "failure_status": None if not failed
        else final_report_checks.FINAL_REPORT_FAILURE,
        "inputs": {"unmasked": {"stage": C.STAGE_UNMASKED_ANALYSIS},
                   "freeze": {"stage": C.STAGE_GATE5}},
        "producing_commit": producing_commit,
        "final_report_checks": checks,
        "n_final_report_checks": len(checks),
        "n_final_report_passed": sum(1 for c in checks
                                     if c["verdict"] == "PASS"),
        "blocked": [c["check"] for c in failed],
        "traceability":
            "every number traces to a v5 stage record and its hash; no v4r4 "
            "outcome is presented as a v5 observation (§30)",
    }


def _report_rows(tree: ModelTree, analysis: Mapping[str, Any],
                 freeze_record: Mapping[str, Any],
                 analysis_hash: str) -> list[dict[str, Any]]:
    """§31's table: one row per (member, configuration), withheld ones too.

    Every one of ``final_report.ROW_FIELDS`` is filled from a signed record.
    An earlier revision emitted six of the twenty-one and the stage refused
    the table, which is the check working: §31 lists what the released table
    carries and a row that omits its standard error, its bounds or its
    provenance is not that table.
    """
    freeze = freeze_record["freeze"]
    confirmatory = transitions.read_stage_record(tree, C.STAGE_CONFIRMATORY)
    rows: list[dict[str, Any]] = []
    statuses = ";".join(analysis["identification_statuses"]) or "none"
    family_of = {member: family
                 for family, members in C.FAMILY_MEMBERS.items()
                 for member in members}
    estimands = analysis["estimands"]
    intervals = estimands.get("intervals") or {}

    # ------------------------------------------------- the row-wide context
    coordinate = {
        "primary": freeze["difficulty_coordinate_definition"],
        "iota_a": freeze.get("iota_a"),
        "solo_compliance_a": freeze.get("solo_compliance_a"),
        "m_star": freeze["m_star"], "n_star": freeze["n_star"]}
    tiers = sorted({int(e["structural_tier"])
                    for e in (freeze.get("core_references") or ())
                    if e.get("structural_tier") is not None})
    # §16.1's decomposition as the freeze bound it. phi splits a cell's
    # variance into a topic and a draw part, and the draw part needs
    # draw-level data that §14.1 keeps out of the analysis on purpose --- so
    # the realised decomposition is the freeze's, with its source named, and
    # the realised *dispersion* is the bootstrap standard error on each row.
    variance = dict(freeze["variance_reestimate"])
    counts = {"blocks": confirmatory["blocks"],
              "cells_per_block": confirmatory["cells_per_block"],
              "draws_per_cell": confirmatory["draws"],
              "rows": confirmatory["n_rows"]}

    def row(member: str, configuration: str, claim_level: str,
            entry: Mapping[str, Any], family: str) -> dict[str, Any]:
        key = f"{family}:{configuration}"
        interval = (intervals.get(key) or {}).get(member) or {}
        half_width = interval.get("half_width")
        precondition = C.PRECISION_PRECONDITIONS.get(
            claims.precondition_key(member))
        return {
            "member": member, "configuration": configuration,
            "cell": "pair:A+B", "claim_level": claim_level,
            "family": family,
            "identification_status": (entry.get("reason")
                                      if entry["status"] == NOT_IDENTIFIED
                                      else statuses),
            "status": entry["status"],
            "measurement_basis": freeze["measurement_basis"],
            "difficulty_coordinate": coordinate,
            "structural_tier_of_reference_pool": tiers,
            "point": entry.get("point"),
            "estimate": interval.get("estimate", entry.get("point")),
            "standard_error": interval.get("standard_error"),
            "marginal_lower": interval.get("marginal_lower"),
            "marginal_upper": interval.get("marginal_upper"),
            "simultaneous_lower": interval.get("lower"),
            "simultaneous_upper": interval.get("upper"),
            "realised_half_width": half_width,
            "variance_decomposition": variance,
            # §16.3 reads the realised simultaneous half-width as the
            # magnitude the design resolves --- a half-width of 0.0452
            # resolves an order contrast above about 0.045 --- so the
            # achieved detectable effect *is* that half-width, and the
            # derivation travels with it rather than being asserted.
            "achieved_detectable_effect": {
                "value": half_width,
                "derivation": "§16.3: the realised simultaneous half-width "
                              "is the magnitude at which the interval "
                              "excludes zero",
                "precondition": precondition,
                "met": (None if half_width is None or precondition is None
                        else half_width <= precondition)},
            "cell_counts": counts,
            "source_stage": C.STAGE_UNMASKED_ANALYSIS,
            "stage_record": C.STAGE_UNMASKED_ANALYSIS,
            "stage_record_hash": analysis_hash,
            "freeze_hash": freeze_record["freeze_hash"]}

    for configuration, bucket in estimands["configurations"].items():
        for member, entry in sorted(bucket.items()):
            rows.append(row(member, configuration, "L1", entry,
                            family_of.get(member, "unassigned")))
    for member, entry in sorted(estimands["cross_configuration"].items()):
        rows.append(row(member, "cross", "L4b", entry,
                        family_of.get(member, "F11")))
    return rows


def run_final_report(tree: ModelTree, *, producing_commit: str | None = None,
                     environment_digest: str = "",
                     repo_root: Path | str | None = None) -> StageOutcome:
    """Stage 18. A mandatory check failing raises, **after** the record.

    Every other stage's failure is enforced by its successor refusing to run.
    Stage 18 has no successor, so the record is written first --- it is the
    evidence of what failed and it must survive --- and the failure is then
    raised so no caller mistakes a failed report for a finished study.
    """
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    outcome = run_stage(
        tree, C.STAGE_FINAL_REPORT,
        compute=lambda _prev: final_report_payload(
            tree, producing_commit=commit, repo_root=repo_root),
        producing_commit=commit, environment_digest=environment_digest)
    if outcome.payload.get("outcome") != "PASS":
        raise IntegrityError(
            f"{tree.model_key}: {C.STAGE_FINAL_REPORT} recorded "
            f"{outcome.payload['outcome']!r}; the mandatory checks "
            f"{outcome.payload['blocked']} did not pass and the report does "
            "not establish its own traceability")
    return outcome
