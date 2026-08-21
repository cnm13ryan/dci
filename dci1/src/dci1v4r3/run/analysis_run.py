"""The three analysis stages: masked, unmasking, unmasked (§15, §17, §20).

The order is the whole point and it is enforced by the stage machine, not by
this module's good behaviour. What this module adds is the seal: the masked
artifact is hashed before the unmask key is opened, and the unmask record
carries that hash and the hash of the analysis code that produced it. An
analysis rewritten after the identities were revealed therefore shows up as a
code hash the sealed artifact does not name.

**What the mask does and does not hide.** §20 permutes the *companion
identities* within the maskable groups. It does not and cannot hide
`delta_difficulty`, whose whole construction is a fit over the companions'
difficulties --- `assert_delta_difficulty_not_masked` says so on the path. Nor
can it hide the spectrum rungs or the class companion, which pair with `B`
alone: with one of them as outcome the single companion is `B`, and a
permutation of one element is the identity. Those groups are reported as
`structurally_unmaskable` rather than quietly counted as masked.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r3.analysis import claims as CL
from dci1v4r3.analysis import run as A
from dci1v4r3.analysis import spectrum as S
from dci1v4r3.analysis.masking import (
    MaskKey, analysis_code_hash, apply_mask, assert_delta_difficulty_not_masked,
    assert_mask_effective, assert_masked_view_clean, build_mask, unmask,
)
from dci1v4r3.analysis.observations import ObservationTable, build_observations
from dci1v4r3.engine.paths import ModelTree
from dci1v4r3.protocol import constants as C

SRC = Path(__file__).resolve().parents[1]

#: §17.1's bootstrap root. Registered in `protocol.seeds`, read here rather
#: than restated, so a seed cannot be one number in the plan and another in the
#: run.
from dci1v4r3.protocol.seeds import BOOTSTRAP_ROOT_SEED as _SEED  # noqa: E402

__all__ = ["ANALYSIS_MODULES", "observation_table", "family_of_slots",
           "run_masked_analysis", "run_unmasking", "run_unmasked_analysis"]

#: Everything whose edit would change a number. Hashed into both the masked
#: seal and the unmask record.
ANALYSIS_MODULES = ("analysis/observations.py", "analysis/estimators.py",
                    "analysis/bootstrap.py", "analysis/spectrum.py",
                    "analysis/run.py", "analysis/claims.py",
                    "analysis/masking.py")


def _code_hash() -> str:
    return analysis_code_hash([SRC / name for name in ANALYSIS_MODULES])


def observation_table(rows: Sequence[Mapping[str, Any]], *, m_draws: int,
                      variant: str) -> ObservationTable:
    """The §11.1 table, checked against the cells **this variant** requires.

    The variant has to travel. §14.1's within-block check builds its expected
    set from `cell_types`, and telling it only whether the design is reduced
    left it demanding the six spectrum rungs of a replication that dropped
    them --- 11,520 cells the frozen design does not contain, on the variant
    §12.6's coverage failure produces.
    """
    from dci1v4r3.stages.confirmatory import DESIGN_VARIANTS

    reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
    table = ObservationTable(build_observations(rows, m_draws=m_draws))
    table.assert_within_block(reduced=reduced, class_arm=class_arm,
                              spectrum=spectrum,
                              expected_blocks=C.N_BLOCKS)
    return table


def family_of_slots(freeze_record: Mapping[str, Any]) -> dict[str, str]:
    """§11.7's `family_of`: each fit slot to its registered constraint family.

    Read from the frozen slot map, so the fit cannot be told a slot belongs to
    a family the freeze did not bind it to.
    """
    out: dict[str, str] = {}
    for slot, entry in dict(freeze_record["slot_map"]).items():
        if slot in ("A", "B", C.CLASS_SLOT):
            continue
        kind = entry["family"] if isinstance(entry, Mapping) else entry[0]
        out[slot] = kind
    return out


def _analyse(table: ObservationTable, freeze_record: Mapping[str, Any],
             *, resamples: int, spectrum: bool = True) -> dict[str, Any]:
    variant = freeze_record["design_variant"]
    out: dict[str, Any] = {}
    for configuration in C.CONFIGURATIONS:
        spectrum_input = None
        if variant == "full" and spectrum:
            spectrum_input = A.build_spectrum_input(
                table, configuration, family_of=family_of_slots(freeze_record))
        families = A.analyse_configuration(
            table, configuration, spectrum_input=spectrum_input,
            design=variant, seed=_SEED, resamples=resamples)
        entry: dict[str, Any] = {
            "families": families,
            "precision": A.precision_report(families),
            "f6_gate": A.f6_gate(families)}
        if spectrum_input is not None:
            entry["spectrum"] = S.estimate(spectrum_input)
        out[configuration] = entry
    return out


def _masked_observations(observations, masked):
    """Rebuild §11.1 observations from the masked view.

    The masked view is what the analysis runs on: the companion label is the
    *permuted* one, so every per-companion contrast in the masked phase is a
    contrast against a companion the analyst cannot name. The cell identity,
    the prompt hash and the true slot do not travel --- `MaskedObservation`
    has no field for them, which is why the reconstruction goes through it
    rather than through the original observation with a label swapped.
    """
    from dci1v4r3.analysis.observations import Observation

    out = []
    for original, view in zip(observations, masked):
        out.append(Observation(
            block_id=view.block_id,
            cell_id=f"masked:{view.masked_id}",
            arm=original.arm,
            outcome_slot=view.outcome_slot,
            companion_slot=view.companion_label,
            position=view.position, configuration=view.configuration,
            draws=original.draws, compliance=view.compliance,
            graded=view.graded, vacuity=view.vacuity,
            truncation=view.truncation,
            non_vacuous_compliance=view.non_vacuous_compliance,
            graded_threshold=view.graded_threshold,
            response_words=view.response_words,
            processing_failures=original.processing_failures))
    return out



# ------------------------------------------------------------- the ladder

def _interval(entry: Mapping[str, Any], family: str, member: str
              ) -> CL.Interval | None:
    """One simultaneous interval, or None when the design does not identify it.

    None and not a zero: `delta_r_reading` compares an interval against two
    registered thresholds, and a fabricated zero interval would read as `L3c`
    --- a claim that the excess is below the generic threshold --- on a design
    that never estimated the excess at all.
    """
    members = ((entry.get("families") or {}).get(family) or {}).get("members")
    if not members or member not in members:
        return None
    found = members[member]
    lower, upper = found["simultaneous"]
    return CL.Interval(member=member, estimate=found["estimate"],
                       lower=lower, upper=upper)


def _heterogeneity_disagrees(entry: Mapping[str, Any]) -> bool:
    """§17: do the three per-reference excesses agree on one side?"""
    threshold = C.DELTA_R_GENERIC_THRESHOLD
    intervals = [_interval(entry, C.PRIMARY_FAMILY, f"Delta_{j}")
                 for j in (1, 2, 3)]
    present = [i for i in intervals if i is not None]
    if len(present) < 3:
        return False
    above = all(i.lower > threshold for i in present)
    below = all(i.upper < threshold for i in present)
    return not (above or below)


def _vacuity_forced_agrees(entry: Mapping[str, Any]) -> bool:
    """§17.4: the primary and the vacuity-forced recomputation license the
    same claim, or no claim is licensed."""
    primary = _interval(entry, C.PRIMARY_FAMILY, "Delta_R")
    forced = _interval(entry, C.PRIMARY_FAMILY, "Delta_R|vacuity_forced")
    if primary is None or forced is None:
        return True
    forced = CL.Interval("Delta_R", forced.estimate, forced.lower,
                         forced.upper)
    return (CL.delta_r_reading(primary)["levels"]
            == CL.delta_r_reading(forced)["levels"])


def _claims(entry: Mapping[str, Any], *, configuration: str,
            measurement_basis: str) -> dict[str, Any]:
    """§17.5's guarded emitter, applied to one configuration's intervals.

    Nothing here chooses a reading. `analysis.claims` holds the lookup, it was
    fixed before any number existed, and this function's whole job is to hand
    it the intervals the registered analysis produced and to say plainly when
    the design did not produce one.
    """
    position = 1 if configuration == C.OUTCOME_FIRST else 2
    support = (entry.get("spectrum") or {}).get("support") or {"holds": False}
    delta_r = _interval(entry, C.PRIMARY_FAMILY, "Delta_R")
    xi = _interval(entry, C.PRIMARY_FAMILY, "Xi")
    delta_difficulty = _interval(entry, C.PRIMARY_FAMILY, "delta_difficulty")

    base = {"configuration": configuration, "outcome_position": position,
            "position_status": CL.position_status(position),
            "measurement_basis": measurement_basis,
            "identified": {"Delta_R": delta_r is not None,
                           "Xi": xi is not None,
                           "delta_difficulty": delta_difficulty is not None},
            "support": support}
    if delta_r is None or xi is None:
        return {**base, "statements": [{
            "claim_level": "L3", "configuration": configuration,
            "family": C.PRIMARY_FAMILY, "interval_type": "simultaneous",
            "identification_status": ["COMPANION_CLASS_NOT_MATCHED",
                                      "EXCESS_NOT_IDENTIFIED"],
            "measurement_basis": measurement_basis,
            "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
            "outcome_position": position, "emitted": False,
            "reason": ("§8.6's design in force does not estimate "
                       + ("Delta_R" if delta_r is None else "Xi")
                       + ", so no L3 sub-level about the excess is "
                         "reachable")}]}
    if delta_difficulty is None:
        # §13.8's support gate short-circuits before the interval is read, so
        # the placeholder's numbers are never compared against anything; the
        # `identified` flag above is what a reader is meant to see.
        delta_difficulty = CL.Interval("delta_difficulty", 0.0, 0.0, 0.0)
        support = {"holds": False, "reason":
                   "the design in force carries no spectrum arm"}
    return {**base, "statements": CL.emit_l3(
        configuration=configuration, outcome_position=position,
        measurement_basis=measurement_basis, delta_r=delta_r,
        delta_difficulty=delta_difficulty, xi=xi, support=support,
        references_identified=True,
        heterogeneity_disagrees=_heterogeneity_disagrees(entry),
        vacuity_forced_agrees=_vacuity_forced_agrees(entry))}


def run_masked_analysis(model_key: str, tree: ModelTree, *,
                        freeze_record: Mapping[str, Any],
                        rows: Sequence[Mapping[str, Any]],
                        resamples: int = C.BOOTSTRAP_RESAMPLES
                        ) -> dict[str, Any]:
    """§20: mask, verify the mask, analyse the *masked view*, seal it.

    The spectrum fit does not run here and cannot: `A`'s point is inside the
    permuted group, so a masked-phase `delta_difficulty` would be a residual
    against a permuted assignment of difficulties and would mean nothing.
    `assert_delta_difficulty_not_masked` checks each configuration's result
    for it rather than trusting that the fit was skipped.
    """
    variant = freeze_record["design_variant"]
    table = observation_table(rows, m_draws=int(freeze_record["m_draws"]),
                              variant=variant)
    mask = build_mask(table.observations, namespace="confirmatory_mask")
    effectiveness = assert_mask_effective(table.observations, mask)
    masked = apply_mask(table.observations, mask)
    assert_masked_view_clean([m.__dict__ for m in masked])

    MaskKey(tree.mask_key_path("confirmatory_mask")).write(mask)
    view = tree.masked_view("confirmatory_mask")
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text("".join(canonical_json(m.__dict__) + "\n" for m in masked))

    masked_table = ObservationTable(
        _masked_observations(table.observations, masked))
    result = _analyse(masked_table, freeze_record, resamples=resamples,
                      spectrum=False)
    for configuration, entry in result.items():
        assert_delta_difficulty_not_masked(entry)

    payload = {
        "outcome": "PASS", "stage": C.STAGE_MASKED_ANALYSIS,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_MASKED_ANALYSIS],
        "model_key": model_key, "design_variant": variant,
        "blocks": len(table.blocks), "resamples": resamples,
        "mask_effectiveness": effectiveness,
        "mask_key_hash": mask["mask_key_hash"],
        "masked_view_rows": len(masked),
        "analysis_code_hash": _code_hash(),
        "spectrum_fit_ran": False,
        "result": result,
    }
    payload["masked_artifact_hash"] = sha_text(canonical_json(
        {k: v for k, v in payload.items() if k != "masked_artifact_hash"}))
    return payload


def run_unmasking(model_key: str, tree: ModelTree, *,
                  masked_record: Mapping[str, Any]) -> dict[str, Any]:
    """§20's irreversible unmask, bound to the sealed masked artifact."""
    key_path = tree.mask_key_path("confirmatory_mask")
    if not key_path.exists():
        raise IntegrityError(
            f"{model_key}: no confirmatory mask key at {key_path}; there is "
            "nothing to unmask and no masked analysis to bind to")
    key = MaskKey(key_path)
    record = unmask(key, analysis_code_hash=masked_record["analysis_code_hash"],
                    masked_outputs_hash=masked_record["masked_artifact_hash"])
    return {"outcome": "PASS", "stage": C.STAGE_UNMASKING,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKING],
            "model_key": model_key, **record}


def run_unmasked_analysis(model_key: str, tree: ModelTree, *,
                          freeze_record: Mapping[str, Any],
                          rows: Sequence[Mapping[str, Any]],
                          masked_record: Mapping[str, Any],
                          resamples: int = C.BOOTSTRAP_RESAMPLES
                          ) -> dict[str, Any]:
    """§15 and §17: the fixed analysis, then the frozen claim ladder.

    The claim ladder is applied by `analysis.claims`, whose lookup was fixed
    before any number existed. Nothing here chooses a reading.
    """
    variant = freeze_record["design_variant"]
    table = observation_table(rows, m_draws=int(freeze_record["m_draws"]),
                              variant=variant)
    result = _analyse(table, freeze_record, resamples=resamples)
    if _code_hash() != masked_record["analysis_code_hash"]:
        raise IntegrityError(
            "the analysis code has changed since the masked artifact was "
            "sealed; an unmasked analysis under different code is not the "
            "analysis the mask protected")
    basis = str(freeze_record.get("gate1_measurement_basis", "UNKNOWN"))
    ladder = {configuration: _claims(entry, configuration=configuration,
                                     measurement_basis=basis)
              for configuration, entry in result.items()}
    CL.assert_no_l5_emitter(vars(CL))
    return {"outcome": "PASS", "stage": C.STAGE_UNMASKED_ANALYSIS,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKED_ANALYSIS],
            "model_key": model_key, "design_variant": variant,
            "blocks": len(table.blocks), "resamples": resamples,
            "analysis_code_hash": _code_hash(),
            "masked_artifact_hash": masked_record["masked_artifact_hash"],
            "measurement_basis": basis,
            "result": result, "claims": ladder,
            "identical_computation_as_masked": True}
