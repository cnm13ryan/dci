"""Evidence verification command and the readiness report (items 7, 65).

``verify-evidence`` is the public face of the one canonical verification
routine. ``readiness_report`` assembles the item-65 implementation report
from durable state; it is read-only.
"""
from __future__ import annotations

from typing import Any

from dci1v3.engine import transitions
from dci1v3.engine.context import StudyContext
from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.paths import model_tree
from dci1v3.engine.verify import NAMED_CHECKS, verify_evidence
from dci1v3.errors import V3Error
from dci1v3.models.registry import MODEL_KEYS, registration_models
from dci1v3.protocol import constants as C


@operation("verify-evidence", stage=None, mutating=False)
def run_verify(job: Job) -> dict[str, Any]:
    report = verify_evidence(job.tree,
                             expected_stage=job.options.get("expected"))
    return {"status": "VERIFIED", "checks": sorted(NAMED_CHECKS),
            "report": report}


def model_states(context: StudyContext) -> dict[str, Any]:
    states: dict[str, Any] = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        try:
            state = transitions.current_state(tree)
            terminal = transitions.terminal_status(tree)
        except V3Error as error:
            state, terminal = f"VERIFICATION_ERROR: {error}", None
        states[model_key] = {"state": state, "terminal": terminal}
    return states


def readiness_report(context: StudyContext, *,
                     synthetic_trace: dict[str, Any] | None = None,
                     test_results: dict[str, Any] | None = None
                     ) -> dict[str, Any]:
    """The item-65 readiness report over current durable state."""
    return {
        "implementation_root": "dci1/src/dci1v3",
        "protocol": C.PROTOCOL, "protocol_version": C.PROTOCOL_VERSION,
        "study_id": context.study_id,
        "models": registration_models(),
        "scientific_dependency_isolation":
            "dci1v3 imports no earlier DCI implementation; verified by "
            "tests_v3/test_transcription.py::test_no_v2_imports",
        "shared_generic_infrastructure": [
            "exploratory/vllm_backend (subprocess seam)",
            "dci1/environments/backend (pinned vLLM interpreter)"],
        "canonical_interface": "dci1v3.cli via dci1v3.engine.dispatch",
        "state_machine": "dci1v3/engine/transitions.py",
        "evidence_verification": "dci1v3/engine/verify.py "
                                 f"({len(NAMED_CHECKS)} named checks)",
        "writer_locking": "dci1v3/engine/locks.py (cross-process flock)",
        "git_cleanliness": "dci1v3/engine/gitinfo.py (no bypass)",
        "uv_provenance": "dci1v3/engine/environment.py "
                         "(uv.lock + frozen export, fail-closed)",
        "gate1": "dci1v3/stages/gate1.py (reservoir, seeded sample, "
                 "one-sided Wilson bound; carry-over in carry_over)",
        "sequestered_access_control": "dci1v3/topics/sequestered.py "
                                      "(opaque manifest, fail-closed)",
        "cache_and_selection": "dci1v3/generation/cache.py + "
                               "dci1v3/stages/select.py (response-blind "
                               "hash rule)",
        "pseudo_run_isolation": "dci1v3/stages/sensitivity.py "
                                "(separate domain and derived path)",
        "masking": "dci1v3/stages/masking.py (persistent single-shot mask "
                   "and unmask; pilot/confirmatory namespaces disjoint)",
        "predecessor_verification": "hash AND signature on every stage "
                                    "record (engine/transitions.py)",
        "durable_restoration": "dci1v3/engine/store.py "
                               "(replicate/assert_replicated/restore)",
        "artifact_states": "dci1v3/engine/artifacts.py (monotonic ledger)",
        "model_states": model_states(context),
        "synthetic_lifecycle": synthetic_trace,
        "test_results": test_results,
        "not_executed": [
            "registered confirmatory generation (prohibited at readiness)",
            "real-model qualification through Gate 2B (GPU-dependent)",
            "independent human validation (unavailable — amendment A2: "
            "Gate 1 runs the autorater-assisted verifier workflow; the "
            "annotation packet and reviewer GUI are preserved for a "
            "future `human-audit`)",
        ],
    }
