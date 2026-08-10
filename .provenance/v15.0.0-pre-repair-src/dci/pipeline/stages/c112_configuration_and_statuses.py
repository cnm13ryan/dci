"""Stage 112 — migrated from notebook cell 112.py (configuration_and_statuses).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/112.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.measurement.audit_sizing import error_ceiling_sample_size, required_cases_for_ceiling, wilson_interval  # noqa: F401
from dci.config.loader import ACTIVE


import gc
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
from dci.compat import torch
from dci.reporting.display import display
from scipy import stats
from tqdm.auto import tqdm
from dci.compat import AutoModelForCausalLM, AutoTokenizer, set_seed

# =====================================================================
# EXECUTION SWITCHES. Shipped so that a first run cannot spend compute.
# =====================================================================
MODEL_PROFILE: Literal["dev_fast", "integration_pass", "pilot", "study"] = ACTIVE.model_profile
RUN_MODE: Literal["smoke", "full"] = ACTIVE.run_mode
DRY_RUN_MODE = ACTIVE.dry_run_mode
USE_GOOGLE_DRIVE = ACTIVE.use_google_drive

# Resume target. None starts a new run directory, or resumes the most recent
# one whose execution fingerprint matches. Set explicitly to resume a named run.
S.RUN_ID: Optional[str] = ACTIVE.run_id

# Every revision below was verified against the Hugging Face model API. A
# scientific run may never use "main": it is mutable, so two runs under it are
# not the same experiment.
MODEL_PROFILES: dict[str, dict[str, Any]] = {
    "dev_fast": {
        "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "role": "development",
        "produces_evidence": False,
        "stamp": "DEVELOPMENT_ONLY",
        "purpose": ("engineering smoke tests, Drive persistence, batching, "
                    "tokenizer and chat-template checks, scoring and verifier "
                    "plumbing, interruption and resume testing"),
    },
    # A synthetic profile, not a model. It exists so that ONE coherent
    # execution can traverse every gate to a PASS with no bypass anywhere, which
    # no fixture-by-fixture unit test can demonstrate. It loads no weights and
    # its outputs carry a permanent SYNTHETIC_NO_EVIDENCE stamp.
    "integration_pass": {
        "model_id": "synthetic://integration_pass",
        "revision": "0" * 40,
        "role": "integration_self_test",
        "produces_evidence": False,
        "stamp": "SYNTHETIC_NO_EVIDENCE",
        "purpose": ("one complete no-bypass traversal of Gate 0, Gate M, "
                    "Gate 1, Gate 2, Gate 3, Gate 3b, freeze, confirmation, "
                    "Gate 4 and export, on a corpus constructed so that every "
                    "gate's passing branch is reachable"),
    },
    "pilot": {
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "role": "pilot",
        "produces_evidence": False,
        "stamp": "PILOT_MODEL_SPECIFIC",
        "purpose": ("empirical feasibility, U dynamic-range stress testing, "
                    "gate runtime measurement, early detection of output "
                    "pathologies, rough reference-support diagnostics"),
    },
    "study": {
        "model_id": "Qwen/Qwen2.5-3B-Instruct",
        "revision": "aa8e72537993ba99e69dfaafa59ed015b17504d1",
        "role": "study",
        "produces_evidence": True,
        "stamp": "SCIENTIFIC",
        "purpose": "the target scientific model",
    },
}

assert MODEL_PROFILE in MODEL_PROFILES, f"unknown profile {MODEL_PROFILE!r}"
assert RUN_MODE in ("smoke", "full"), f"unknown RUN_MODE {RUN_MODE!r}"
for _name, _p in MODEL_PROFILES.items():
    if _p["model_id"].startswith("synthetic://"):
        assert not _p["produces_evidence"], "a synthetic profile cannot produce evidence"
        continue
    assert _p["revision"] != "main" and len(_p["revision"]) == 40, (
        f"profile {_name} must pin an immutable 40-character revision, not "
        f"{_p['revision']!r}. A mutable revision is not a reproducible study.")

S.PROFILE = MODEL_PROFILES[MODEL_PROFILE]
DEVELOPMENT_ONLY = MODEL_PROFILE == "dev_fast"
SYNTHETIC_PROFILE = S.PROFILE["model_id"].startswith("synthetic://")
INTEGRATION_SELF_TEST = MODEL_PROFILE == "integration_pass"
if INTEGRATION_SELF_TEST:
    # The integration self-test is a self-test, not a dry run: no gate may be
    # bypassed inside it, and it must never be mistaken for a scientific run.
    DRY_RUN_MODE = True
S.PILOT_MODEL_SPECIFIC = MODEL_PROFILE == "pilot"
PRODUCES_EVIDENCE = bool(S.PROFILE["produces_evidence"]) and not DRY_RUN_MODE


# =====================================================================
# Machine-readable outcome statuses. Scientifically different failures
# must never share one exception: their remedies are different.
# =====================================================================


@dataclass
class ProtocolConfig:
    run_mode: Literal["smoke", "full"]
    dry_run: bool
    model_profile: str

    model_id: str = ""
    model_revision: str = ""

    base_seed: int = 20260901

    # --- execution identity -------------------------------------------------
    engine: str = "hf_transformers"
    attn_implementation: str = "sdpa"
    inference_dtype: str = "float16"
    require_exact_dtype: bool = True
    single_gpu_index: int = ACTIVE.device_index if ACTIVE.device_index is not None else 0
    adaptive_batching: Literal["off", "exploratory"] = "off"

    # --- durability ---------------------------------------------------------
    use_google_drive: bool = True
    allow_local_fallback: bool = True
    mirror_committed_batches: bool = True
    verify_drive_mirror: bool = True
    sample_telemetry: bool = True
    telemetry_interval_s: float = 5.0
    require_fresh_generation: bool = False

    target_id: str = "A"
    focal_id: str = "B"

    # --- estimand -----------------------------------------------------------
    orders: tuple[str, ...] = ("target_first", "added_first")
    reference_count: int = 6
    max_single_weight: float = 0.30
    j_eff_floor: float = 4.0
    # Penalty on individual donor distance in the synthetic fit, so aggregate
    # balance cannot be bought with individually distant donors.
    synthetic_distance_penalty: float = 1.0

    # --- unrelated-target architecture -------------------------------------
    # 'bridge' is sentence-scoped and reserved for validation and test, never
    # for building features: it exists to test transport to A's own scope.
    u_families: tuple[str, ...] = ("lexical", "format", "numerical", "bridge")
    u_build_families: tuple[str, ...] = ("lexical", "format", "numerical")
    u_min_eligible_per_family: int = 3
    u_screen_isolated_low: float = 0.20
    u_screen_isolated_high: float = 0.80
    u_screen_composed_low: float = 0.10
    u_screen_composed_high: float = 0.90
    u_screen_partner_id: str = "N_NEUTRAL"
    # A candidate whose interval straddles a band edge is not classified.
    u_screen_confidence: float = 0.90

    # --- calipers -----------------------------------------------------------
    sesoi_risk_difference: float = 0.10
    caliper_slope_q: float = 1.0
    caliper_uncertainty_q: float = 1.0
    caliper_precision_fraction: float = 0.50
    caliper_slope_floor: float = 0.40
    caliper_absolute_ceiling: float = 0.25
    mahalanobis_ridge: float = 0.10
    # Precision must protect the candidates that could plausibly enter the
    # panel. A contender is within this multiple of every caliper.
    contender_buffer_multiple: float = 1.50
    # Family slopes are taken as the largest credible upper sensitivity across
    # rotations and orders unless heterogeneity is demonstrably small.
    slope_pooling_max_relative_spread: float = 0.50
    # --- sensitivity estimation quality (v15) -------------------------------
    # A slope read from a rank-deficient or ill-conditioned design is not a
    # measurement. These are prospective minimum requirements, not diagnostics.
    min_constraints_for_sensitivity: int = 5
    min_constraints_for_jackknife: int = 5
    max_condition_number: float = 1.0e6
    # Used only when neither the bootstrap nor the jackknife yields a slope
    # standard error. Larger than any slope SE this design has produced, so it
    # can only narrow a caliper. Never a substitute for a real estimate.
    slope_se_conservative_fallback: float = 1.00

    # --- joint reference-error certificate (v15) ----------------------------
    # Componentwise calipers bound each coordinate separately. They do not bound
    # the accumulated mismatch: with 17 components each at SESOI/s_r, the
    # first-order predicted burden difference could reach 17 x SESOI. The
    # certificate below bounds the sum.
    #
    #   B_C = sum_r s_r^U * (|z_B,r - z_C,r| + q * SE_r)   <=   epsilon_ref
    #
    # s_r^U is the same conservative upper sensitivity that sets the caliper, so
    # B_C is a first-order upper bound on the predicted difference in outgoing
    # burden between B and C on a generic target, under the linear sensitivity
    # model and ignoring sign cancellation between components.
    #
    # epsilon_ref = 0.05 against a 0.10 SESOI. The source methodology states
    # exactly this number, but for a DIFFERENT quantity: the pseudo-focal
    # held-out prediction error, "reserve half of it as the maximum tolerable
    # reference-model discrepancy". Reusing the same half-SESOI reservation for
    # the joint bias certificate is a v15 decision, not an inherited one, and
    # the additivity of component sensitivities is an assumption rather than a
    # measured fact. Both are recorded in v15_open_questions.md.
    enforce_reference_budget: bool = True
    epsilon_ref: float = 0.05
    reference_budget_aggregation: Literal["sum", "rss"] = "sum"

    # --- wording ------------------------------------------------------------
    # Frozen for the workshop protocol at 4 -> 6. The source discusses
    # 4->6->8->10 but its own revision retracts the fixed count in favour of a
    # sequential precision rule, and only six construction wordings are audited
    # here. Unresolved wording precision after six is PRECISION_INSUFFICIENT; it
    # is never resolved by consuming the held-out set.
    paraphrase_schedule: tuple[int, ...] = (4, 6)
    paraphrase_holdout: tuple[int, ...] = (6, 7)
    # Held-out comparability may exceed the caliper by at most this multiple.
    wording_val_caliper_multiple: float = 1.50
    wording_val_confidence: float = 0.95

    # --- pseudo-focal validation -------------------------------------------
    min_pseudo_focal: int = 3
    ref_val_mae_max: float = 0.05
    ref_val_q90_max: float = 0.10
    ref_val_random_ratio_max: float = 0.80
    ref_val_random_draws: int = 400
    ref_val_loo_max: float = 0.05
    # No individually admitted reference may show a held-out discrepancy above
    # this, simultaneously across U_val and order. Averaging cannot rescue it.
    ref_val_individual_max: float = 0.10
    ref_val_panel_max: float = 0.05
    ref_val_confidence: float = 0.95

    # --- final falsification ------------------------------------------------
    falsification_individual_max: float = 0.10
    falsification_panel_max: float = 0.05
    falsification_confidence: float = 0.95

    # --- measurement validity ----------------------------------------------
    # The audit size is DERIVED from the ceiling, not asserted. 12 cases cannot
    # establish a 5% error rate; the notebook computes what can.
    verifier_error_ceiling: float = 0.05
    verifier_audit_confidence: float = 0.95
    min_cases_per_verifier: int = 12
    review_boundary_share: float = 0.50
    verifier_kappa_floor: float = 0.80
    paraphrase_audit_required: bool = True
    # v15. Gate M decides on a two-sided Wilson upper bound computed within each
    # human-ground-truth class, so the binding sample size is the number of
    # adjudicated cases IN THAT CLASS, not the audit total. The required counts
    # are obtained by inverting the same bound function the gate uses.
    audit_size_rule: Literal["wilson_two_sided", "zero_error_one_sided"] = "wilson_two_sided"
    min_truth_class_cases: int = 5
    audit_class_balance: float = 0.50
    # Auditing all 45 constraints independently costs 45 x n labels for no
    # additional identification: most share a verifier implementation. v15
    # audits implementation-by-parameter strata and requires every constraint
    # that can be selected to be covered by an audited stratum. A and B are
    # always audited in their own right.
    audit_by_implementation_stratum: bool = True
    always_audited_ids: tuple[str, ...] = ("A", "B")
    # Two-level reliability claim, and the levels are NOT the same claim.
    #
    #   tier 1  A and B individually, at verifier_error_ceiling. These carry the
    #           primary outcome and define the focal contrast.
    #   tier 2  every other verifier IMPLEMENTATION as its own stratum, at the
    #           coarser stratum_error_ceiling, PLUS a pooled certificate across
    #           all strata at verifier_error_ceiling.
    #
    # The pooled claim is a real claim about the measurement system. The
    # per-stratum claim is weaker and is reported as weaker: a single stratum
    # certifies only that its error rate is below stratum_error_ceiling. The
    # alternative -- certifying every implementation individually at 5% -- is
    # implemented and costed in the compute budget; it was not adopted because
    # it needs 4,526 adjudicated labels, not because 5% is inconvenient.
    stratum_error_ceiling: float = 0.20
    require_pooled_system_ceiling: bool = True
    # The truth class is unknown until adjudication, so the sample is drawn
    # against the automatic verdict and over-drawn by this margin. Without it a
    # reasonable disagreement rate leaves a class denominator short and the gate
    # returns AUDIT_CLASS_SUPPORT_INSUFFICIENT for an avoidable reason.
    audit_overdraw_margin: float = 0.20
    review_malformed_share: float = 0.20

    # --- design sizes -------------------------------------------------------
    smoke_screening_tasks: int = 8
    full_screening_tasks: int = 8
    smoke_prescreen_tasks: int = 6
    full_prescreen_tasks: int = 6
    smoke_calibration_tasks: int = 12
    full_calibration_tasks: int = 16
    smoke_confirmatory_tasks: int = 6
    full_confirmatory_tasks: int = 48
    smoke_placebo_tasks: int = 3
    full_placebo_tasks: int = 12
    smoke_wording_tasks: int = 4
    full_wording_tasks: int = 8

    smoke_calibration_seeds: tuple[int, ...] = (11, 29)
    full_calibration_seeds: tuple[int, ...] = (11, 29)
    smoke_confirmatory_seeds: tuple[int, ...] = (11,)
    full_confirmatory_seeds: tuple[int, ...] = (11,)
    screening_seeds: tuple[int, ...] = (11, 29)
    wording_seeds: tuple[int, ...] = (11,)
    prescreen_paraphrase: int = 0
    prescreen_difficulty_margin: float = 0.35

    # --- constraint parameters ---------------------------------------------
    # Dry-run fixture only: the fewest corpus members that must both satisfy
    # and violate each declared constraint before the oracle is usable.
    oracle_min_corpus_support: int = 5
    oracle_u_target_latent: Optional[float] = None
    # How far a planted twin sits from the focal constraint on the latent
    # difficulty scale. Fixture only.
    oracle_twin_jitter: float = 0.02
    # Named so that a reader can see exactly what the fixture plants. Under the
    # oracle these candidates are given the focal constraint's latent difficulty,
    # which is what makes the "references exist" branch of Gates 3, 3b and 4
    # reachable at all in a dry run. Read only by _latent_difficulty, which is
    # itself read only by the synthetic oracle: when dry_run is False the model
    # generates every response and this tuple has no effect whatsoever.
    oracle_planted_twins: tuple[str, ...] = (
        "C_W3", "S_COMMA", "S_ENDLONG", "S_MINWORDS12", "S_MINWORDS15",
        "S_TWOLONG", "S_SEMICOLON")

    exact_sentence_count: int = 4
    minimum_sentence_words: int = 8
    long_word_letters: int = 7
    shadow_min_words_a: int = 12
    shadow_min_words_b: int = 15
    shadow_min_words_c: int = 20
    shadow_min_words_d: int = 25
    shadow_min_words_e: int = 30
    shadow_long_word_count: int = 2
    shadow_long_word_count_high: int = 3
    band_low: int = 15
    band_high: int = 25
    two_commas: int = 2
    comma_min_words: int = 12

    u_forbidden_words: tuple[str, ...] = ("very", "important", "process")
    u_required_words: tuple[str, ...] = ("evidence", "threshold", "gradual")
    u_alliteration_letter: str = "p"
    u_alliteration_count: int = 4
    u_semicolon_total: int = 2
    u_colon_total: int = 1
    u_quote_pairs: int = 1
    u_integer_count_small: int = 2
    u_integer_count_large: int = 4
    u_integer_sum_target: int = 100
    u_integer_sum_count: int = 3
    u_percent_count: int = 1
    u_integer_min: int = 2
    u_integer_max: int = 2
    u_neutral_word: str = "overall"
    # bridge family parameters
    u_bridge_initial_letter: str = "t"
    u_bridge_vowel_min: int = 3
    u_bridge_caps_sentences: int = 1

    # --- coupling probe -----------------------------------------------------
    # "matched": kappa is a quantitative component of the signature with its own
    # caliper and its own uncertainty. "audit": kappa cannot be given a
    # defensible uncertainty model on the available probe bank, so it is
    # demoted to an explicit hard measurement-coupling audit. Demotion is a
    # declared protocol choice recorded in the hash, never a silent drop.
    # v15. The source methodology treats kappa predominantly as verifier /
    # measurement coupling to be controlled -- it is a hard rejection rule in
    # the protocol ("shares A's verifier target") -- but it also appears once in
    # the variable taxonomy among the principal potential MODERATORS, which
    # would put it on the causal pathway. That ambiguity is not resolvable from
    # the supplied documents, so v15 does not resolve it by choosing: it
    # declares two nested estimands with different reference definitions and
    # different interpretations, and never calls them estimates of the same
    # parameter. See v15_open_questions.md.
    #
    #   primary_total    kappa is AUDITED, not matched. tau_{j,o} is the total
    #                    pair-specific contrast, including any part of the
    #                    effect that runs through A-Q structural coupling.
    #   kappa_matched    kappa is a matched signature component. The contrast
    #                    answers the narrower question of what remains after
    #                    coupling is held fixed, and is secondary.
    primary_estimand: Literal["primary_total", "kappa_matched"] = "primary_total"
    report_kappa_matched_secondary: bool = True
    coupling_role: Literal["matched", "audit"] = "audit"
    coupling_audit_max: float = 0.20
    min_informative_coupling_probes: int = 20
    max_coupling_se: float = 0.15

    # --- duplication / entailment ------------------------------------------
    duplicate_agreement_threshold: float = 0.98

    scope_restricted_pool: bool = True
    mediator_features: tuple[str, ...] = ("response_words",)

    # --- inference ----------------------------------------------------------
    alpha: float = 0.05
    power: float = 0.80
    confidence_level: float = 0.95
    target_ci_halfwidth: float = 0.075
    bootstrap_reps_smoke: int = 400
    bootstrap_reps_full: int = 4000
    power_sim_reps: int = 4000
    run_placebo: bool = True

    # --- decoding -----------------------------------------------------------
    max_input_tokens: int = 1024
    max_new_tokens: int = 180
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True
    initial_batch_size: int = 4

    # --- benchmark ----------------------------------------------------------
    benchmark_prompts: int = 24
    benchmark_seconds_per_generation_default: float = 2.0

    # --- dry-run only -------------------------------------------------------
    dry_run_bypass_gates: bool = True
    # integration_pass only: adjudicate the blinded audits from the oracle's own
    # ground truth so Gate M can be REACHED without a human, while every other
    # gate still has to pass on its own terms. Permanently stamped synthetic.
    integration_autosign_audits: bool = False

    # --- v15 execution integrity -------------------------------------------
    # No scientific prompt may be generated after its input was truncated.
    forbid_input_truncation: bool = True
    input_token_headroom: int = 0
    # Above this share of truncated outputs in any reported cell, the declared
    # output cap is plausibly dominating measured compliance and the run stops.
    output_truncation_warn_share: float = 0.05
    output_truncation_stop_share: float = 0.20
    # Strict hardware consistency. A future protocol may define validated
    # equivalence classes; v15 has none and refuses to guess.
    enforce_hardware_class: bool = True
    hardware_equivalence_classes: tuple[str, ...] = ()

    # --- v15 U split --------------------------------------------------------
    # The source locks 3/3/3. v15 uses 3/4/4: the fourth member of validation
    # and of test is a bridge target, which is sentence-scoped and therefore
    # inadmissible to build. The build set is unchanged at the locked size.
    u_split_architecture: str = "3/4/4 (3 build, 3+1 bridge val, 3+1 bridge test)"
    # Only targets whose dynamic range is RESOLVED may enter an evidential
    # split. Indeterminate targets wait in the pending-precision reserve.
    evidential_splits_require_resolved_eligibility: bool = True

    # --- v15 confirmatory sizing -------------------------------------------
    # Option A of the two the specification offers: a fixed, frozen,
    # conservative cluster count evaluated against a variance grid. N is NOT
    # chosen from pilot variance in v15. The source permits a pilot-informed N
    # from non-focal quantities, and forbids it from A+B or A+C outcomes; the
    # adaptive path is deferred rather than half-implemented.
    confirmatory_n_rule: Literal["fixed", "pilot_informed"] = "fixed"

    # --- v15 cross-model transport (optional, separable) --------------------
    enable_transport_module: bool = False
    transport_models: tuple[str, ...] = ("llama_3_2_3b", "phi_4_mini")
    transport_caliper_multiple: float = 1.00

    drive_root: str = "/content/drive/MyDrive/directional_interference"
    local_root: str = "/content/directional_interference_local"
    protocol_version: str = "v15"

    def _pick(self, smoke: Any, full: Any) -> Any:
        return smoke if self.run_mode == "smoke" else full

    @property
    def screening_tasks(self) -> int:
        return self._pick(self.smoke_screening_tasks, self.full_screening_tasks)

    @property
    def prescreen_tasks(self) -> int:
        return self._pick(self.smoke_prescreen_tasks, self.full_prescreen_tasks)

    @property
    def calibration_tasks(self) -> int:
        return self._pick(self.smoke_calibration_tasks, self.full_calibration_tasks)

    @property
    def confirmatory_tasks(self) -> int:
        return self._pick(self.smoke_confirmatory_tasks, self.full_confirmatory_tasks)

    @property
    def placebo_tasks(self) -> int:
        return self._pick(self.smoke_placebo_tasks, self.full_placebo_tasks)

    @property
    def wording_tasks(self) -> int:
        return self._pick(self.smoke_wording_tasks, self.full_wording_tasks)

    @property
    def calibration_seeds(self) -> tuple[int, ...]:
        return self._pick(self.smoke_calibration_seeds, self.full_calibration_seeds)

    @property
    def confirmatory_seeds(self) -> tuple[int, ...]:
        return self._pick(self.smoke_confirmatory_seeds, self.full_confirmatory_seeds)

    @property
    def bootstrap_reps(self) -> int:
        return self._pick(self.bootstrap_reps_smoke, self.bootstrap_reps_full)

    @property
    def u_per_split(self) -> int:
        return len(self.u_build_families)


_INTEGRATION_OVERRIDES: dict[str, Any] = {
    # No bypass anywhere. A gate that fails in this profile fails the self-test.
    "dry_run_bypass_gates": False,
    # The audits are adjudicated from the oracle's own ground truth, so the
    # measurement gate can be reached honestly rather than waived.
    "integration_autosign_audits": True,
    # Enough clusters for the precision rules to be satisfiable.
    # The whole authored bank for every stage that binds a precision rule.
    # These are capacities, not wishes: _take() raises rather than returning a
    # short allocation, so an over-ambitious integration size fails loudly.
    "smoke_screening_tasks": 24,
    "smoke_prescreen_tasks": 6,
    "smoke_calibration_tasks": 64,
    "smoke_wording_tasks": 8,
    "smoke_confirmatory_tasks": 24,
    "smoke_placebo_tasks": 8,
    "bootstrap_reps_smoke": 300,
    # The self-test needs references that genuinely exist, so the oracle plants
    # them. Every gate still has to find and validate them on its own.
    "u_screen_confidence": 0.90,
    # Place the synthetic U targets in the MIDDLE of the declared dynamic-range
    # band rather than near its lower edge, so the screen can resolve them at
    # the cluster count the bank supports. This moves the fixture, not the band:
    # u_screen_isolated_low/high are unchanged, and a target that could not
    # register burden would still be rejected.
    "oracle_u_target_latent": 0.889,
    # Twins tight enough that a six-reference panel genuinely exists. Every
    # gate still has to FIND them: nothing is admitted by declaration.
    "oracle_twin_jitter": 0.002,
    "oracle_planted_twins": ("C_W3", "S_COMMA", "S_ENDLONG", "S_MINWORDS12",
                             "S_MINWORDS15", "S_TWOLONG", "S_SEMICOLON",
                             "S_TWOCOMMA", "S_MINWORDS20", "C_L3"),
} if INTEGRATION_SELF_TEST else {}

S.CFG = ProtocolConfig(run_mode=RUN_MODE, dry_run=DRY_RUN_MODE,
                     model_profile=MODEL_PROFILE,
                     model_id=S.PROFILE["model_id"],
                     model_revision=S.PROFILE["revision"],
                     use_google_drive=USE_GOOGLE_DRIVE,
                     **{**_INTEGRATION_OVERRIDES,
                        **ACTIVE.storage_overrides(),
                        **ACTIVE.protocol_overrides})

assert list(S.CFG.paraphrase_schedule) == sorted(set(S.CFG.paraphrase_schedule))
assert all(isinstance(p, int) and p >= 0 for p in S.CFG.paraphrase_holdout)
assert set(S.CFG.u_build_families) <= set(S.CFG.u_families)
assert "bridge" not in S.CFG.u_build_families, (
    "the bridge family is sentence-scoped and shares A's segmentation span. It "
    "is admissible for validation and test, where it probes transport, and "
    "never for building the features that define comparability.")


# =====================================================================
# The two nested estimands. They answer different questions and are never
# reported as estimates of the same parameter.
# =====================================================================








# The binding denominators are PER HUMAN-GROUND-TRUTH CLASS, because Gate M
# bounds P(auto pass | human fail) and P(auto fail | human pass) separately.
# An audit of N cases that happens to contain 3 human failures cannot certify a
# false-pass ceiling however large N is.
S.CASES_PER_TRUTH_CLASS = required_cases_for_ceiling(
    S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)
S.STRATUM_CASES_PER_TRUTH_CLASS = required_cases_for_ceiling(
    S.CFG.stratum_error_ceiling, S.CFG.verifier_audit_confidence)
S.VERIFIER_AUDIT_SIZE = max(S.CFG.min_cases_per_verifier, 2 * S.CASES_PER_TRUTH_CLASS)
STRATUM_AUDIT_SIZE = max(S.CFG.min_cases_per_verifier, 2 * S.STRATUM_CASES_PER_TRUTH_CLASS)

display(pd.Series(asdict(S.CFG), name="value").to_frame())
print(f"""
profile        : {MODEL_PROFILE}  ({S.PROFILE['model_id']} @ {S.PROFILE['revision'][:12]}...)
role           : {S.PROFILE['role']}   stamp: {S.PROFILE['stamp']}
produces evidence: {S.PROFILE['produces_evidence']}
RUN_MODE       : {RUN_MODE}     DRY_RUN_MODE: {DRY_RUN_MODE}
Drive          : {USE_GOOGLE_DRIVE}

Verifier audit size, derived by inverting the bound Gate M actually applies
  claimed error ceiling       : {S.CFG.verifier_error_ceiling:.2f} at {S.CFG.verifier_audit_confidence:.0%} two-sided Wilson
  cases per TRUTH CLASS       : {S.CASES_PER_TRUTH_CLASS}   (human-fail and human-pass separately)
  tier-1 audit size (A, B)    : {S.VERIFIER_AUDIT_SIZE} each
  per-stratum ceiling         : {S.CFG.stratum_error_ceiling:.2f}  ->  {S.STRATUM_CASES_PER_TRUTH_CLASS} cases per truth class
  tier-2 audit size / stratum : {STRATUM_AUDIT_SIZE}

  v14 sized this audit at {error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)} cases from a one-sided zero-error
  formula, then decided on a two-sided Wilson bound. Those are different
  functions: the Wilson upper bound with zero errors in {error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)} cases is
  {wilson_interval(0, error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence), S.CFG.verifier_audit_confidence)[1]:.3f}, which does not establish {S.CFG.verifier_error_ceiling:.0%}. v14's Gate M was therefore
  impossible to pass at its own declared size. v15 inverts the same function it
  applies, and it does so within each human-ground-truth class.
""")
if S.CFG.dry_run:
    print("DRY RUN. No model is loaded and no output is evidence.")
if not S.PROFILE["produces_evidence"]:
    print(f"{S.PROFILE['stamp']}. Outputs from this profile can never authorize a "
          "scientific freeze, and no behavioural result transfers to another "
          "profile.")
