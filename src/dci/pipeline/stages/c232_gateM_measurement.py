"""Stage 232 — migrated from notebook cell 232.py (gateM_measurement).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/232.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.measurement.audit_sizing import error_ceiling_sample_size, wilson_interval  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

S.require_gate("0_implementation")

with S.phase("gateM_measurement"):
    _reviewer, _key, _strata_plan = S.build_measurement_cases()
    _template_state = S.write_template_if_absent(S.VERIFIER_TEMPLATE_PATH, _reviewer)
    _key_state = S.write_template_if_absent(S.VERIFIER_KEY_PATH, _key)
    _plan_state = S.write_template_if_absent(S.VERIFIER_STRATA_PATH, _strata_plan)
    print(f"verifier audit template {_template_state}: {S.VERIFIER_TEMPLATE_PATH}")
    print(f"verifier audit key      {_key_state}: {S.VERIFIER_KEY_PATH}")
    print(f"verifier audit strata   {_plan_state}: {S.VERIFIER_STRATA_PATH}")
    print(f"pilot outputs in the audit sample: {S.PILOT_AUDIT_SOURCE}")

    if S.CFG.integration_autosign_audits and not S.VERIFIER_SIGNED_PATH.exists():
        # integration_pass only. The oracle's ground truth IS the verifier's
        # verdict by construction in this profile, so adjudicating from it makes
        # the verifier perfect by fiat. That is exactly what the self-test needs:
        # it isolates the pipeline from measurement error so that any gate that
        # fails downstream fails for a structural reason. Stamped synthetic.
        _key_disk = pd.read_csv(S.VERIFIER_KEY_PATH)
        pd.DataFrame({
            "case_id": _key_disk["case_id"],
            "manual_verdict": np.where(_key_disk["auto_binary_pass"] == 1, "pass", "fail"),
            "reviewer_note": "SYNTHETIC_INTEGRATION_SELF_TEST; not evidence",
        }).to_csv(S.VERIFIER_SIGNED_PATH, index=False)
        print("integration_pass: verifier audit auto-adjudicated (SYNTHETIC).")

    if S.VERIFIER_SIGNED_PATH.exists() and S.VERIFIER_AUDIT_SIGNED_INPUT is None:
        S.VERIFIER_AUDIT_SIGNED_INPUT = str(S.VERIFIER_SIGNED_PATH)

    # Always evaluate against the key that pairs with the template on disk, so a
    # rerun with a different random draw cannot invalidate completed labels.
    _key_on_disk = pd.read_csv(S.VERIFIER_KEY_PATH)
    VERIFIER_RELIABILITY = S.evaluate_verifier_reliability(
        S.VERIFIER_AUDIT_SIGNED_INPUT, _key_on_disk)

RELIABILITY_TABLE = VERIFIER_RELIABILITY.get("table", pd.DataFrame())
if len(RELIABILITY_TABLE):
    display(RELIABILITY_TABLE.round(4))
    RELIABILITY_TABLE.to_csv(S.AUDIT_DIR / "verifier_reliability.csv", index=False)
    if VERIFIER_RELIABILITY.get("pooled"):
        display(pd.Series(VERIFIER_RELIABILITY["pooled"]).to_frame("pooled_tier2"))

S.VERIFIER_AUDIT_SHA256 = VERIFIER_RELIABILITY.get("sha256")
S.VERIFIER_GATE_PASSED = bool(VERIFIER_RELIABILITY.get("passed", False))
VERIFIER_AUDIT_STATUS = VERIFIER_RELIABILITY.get("status", GateStatus.AUDIT_MISSING)

MEASUREMENT_VALIDITY = {
    "paraphrase_audit_signed": bool(S.PARAPHRASE_AUDIT["present"]),
    "paraphrase_audit_approved": S.PARAPHRASE_AUDIT_PASSED,
    "paraphrase_audit_sha256": S.PARAPHRASE_AUDIT_SHA256,
    "verifier_audit_signed": bool(VERIFIER_RELIABILITY.get("present", False)),
    "verifier_audit_passed": S.VERIFIER_GATE_PASSED,
    "verifier_audit_status": VERIFIER_AUDIT_STATUS,
    "verifier_audit_sha256": S.VERIFIER_AUDIT_SHA256,
    "cases_per_truth_class_tier1": S.CASES_PER_TRUTH_CLASS,
    "cases_per_truth_class_tier2": S.STRATUM_CASES_PER_TRUTH_CLASS,
    "error_ceiling": S.CFG.verifier_error_ceiling,
    "stratum_error_ceiling": S.CFG.stratum_error_ceiling,
    "tier1_units": list(S.TIER1_IDS),
    "tier2_strata": len(S.TIER2_STRATA),
    "human_labels_required": S.AUDIT_LABEL_BUDGET["total_labels"],
    "constraints_covered": len(S.SELECTABLE_IDS),
}
display(pd.Series({k: str(v) for k, v in MEASUREMENT_VALIDITY.items()}).to_frame("value"))

# Only constraints whose audit unit actually passed may go on to shape the
# reference architecture. A tier-2 stratum that passes certifies every
# constraint that runs that implementation. In a dry run nothing is adjudicated,
# so the whole set is admitted under the recorded bypass and none of it is
# evidence.
if S.VERIFIER_GATE_PASSED and len(RELIABILITY_TABLE):
    _passing_units = set(RELIABILITY_TABLE.query("passes")["audit_unit"])
    S.VALID_VERIFIERS = {
        cid for cid in S.SELECTABLE_IDS
        if cid in _passing_units or S.VERIFIER_IMPLEMENTATION[cid] in _passing_units}
else:
    S.VALID_VERIFIERS = set(S.CONSTRAINTS)

# The four measurement problems have four different remedies, so they are four
# different statuses. v14 returned MEASUREMENT_VALIDITY_FAILED for all of them.
if S.PARAPHRASE_AUDIT_PASSED and S.VERIFIER_GATE_PASSED:
    S.record_gate(GateOutcome(
        gate="M_measurement", status=GateStatus.PASS,
        reason="paraphrase semantics and verifier reliability are both established",
        quantities=MEASUREMENT_VALIDITY,
        thresholds={"kappa_floor": S.CFG.verifier_kappa_floor,
                    "error_ceiling": S.CFG.verifier_error_ceiling,
                    "stratum_error_ceiling": S.CFG.stratum_error_ceiling,
                    "cases_per_truth_class": S.CASES_PER_TRUTH_CLASS}))
else:
    if not S.PARAPHRASE_AUDIT["present"]:
        _status = GateStatus.AUDIT_MISSING
        _reason = "the paraphrase semantic audit has not been signed"
        _more_data, _new_version = True, False
    elif not S.PARAPHRASE_AUDIT_PASSED:
        # An adjudicated semantic non-equivalence is a fact about the wordings.
        _status = GateStatus.PARAPHRASE_SEMANTICS_FAILED
        _reason = "adjudicated wordings are not semantically equivalent"
        _more_data, _new_version = False, True
    else:
        _status = VERIFIER_AUDIT_STATUS
        _reason = VERIFIER_RELIABILITY.get("reason", "verifier reliability not established")
        _more_data = _status in (GateStatus.AUDIT_MISSING,
                                 GateStatus.AUDIT_UNDERPOWERED,
                                 GateStatus.AUDIT_CLASS_SUPPORT_INSUFFICIENT)
        _new_version = _status == GateStatus.VERIFIER_RELIABILITY_FAILED
    assert not (_more_data and _status in GateStatus.NEVER_RESOLVED_BY_MORE_DATA), (
        f"{_status} can never be resolved by collecting more data")
    S.stop("M_measurement", _status, _reason,
         quantities={**MEASUREMENT_VALIDITY,
                     "missing_units": VERIFIER_RELIABILITY.get("missing_units", []),
                     "class_short_units": VERIFIER_RELIABILITY.get("class_short_units", []),
                     "reliability_failed_units":
                         VERIFIER_RELIABILITY.get("reliability_failed_units", [])},
         thresholds={"kappa_floor": S.CFG.verifier_kappa_floor,
                     "error_ceiling": S.CFG.verifier_error_ceiling,
                     "stratum_error_ceiling": S.CFG.stratum_error_ceiling,
                     "cases_per_truth_class_tier1": S.CASES_PER_TRUTH_CLASS,
                     "cases_per_truth_class_tier2": S.STRATUM_CASES_PER_TRUTH_CLASS},
         more_data_could_resolve=_more_data,
         new_protocol_version_required=_new_version,
         message=f"""
{_status}: {_reason}

No empirical generation is permitted until both audits are complete, because a
verifier or a wording that has not been validated would otherwise determine the
reference architecture and every number that follows.

  1. Complete {S.PARAPHRASE_TEMPLATE_PATH.name}
     without looking at model performance, save as
     {S.PARAPHRASE_SIGNED_PATH.name}, and set PARAPHRASE_AUDIT_SIGNED_INPUT.
  2. Complete {S.VERIFIER_TEMPLATE_PATH.name}
     ({S.AUDIT_LABEL_BUDGET['total_labels']} labels: {len(S.TIER1_IDS)} tier-1 units at {S.CASES_PER_TRUTH_CLASS} per truth class,
     {len(S.TIER2_STRATA)} tier-2 strata at {S.STRATUM_CASES_PER_TRUTH_CLASS} per truth class), save as
     {S.VERIFIER_SIGNED_PATH.name}, and set VERIFIER_AUDIT_SIGNED_INPUT.

The binding sample size is PER HUMAN-GROUND-TRUTH CLASS, because the gate
bounds P(auto pass | human fail) and P(auto fail | human pass) separately. An
audit of any size that contains three human failures cannot certify a false-pass
ceiling. v14 sized this audit at {error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)} cases from a formula its own gate did not
use, and the Wilson upper bound with zero errors in {error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)} is {wilson_interval(0, error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence), S.CFG.verifier_audit_confidence)[1]:.3f}: its Gate M
could not be passed by any verifier, however perfect.
""")

S.checkpoint("gateM", MEASUREMENT_VALIDITY)
