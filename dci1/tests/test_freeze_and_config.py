"""§8.6 frozen configuration and freeze-record behaviour."""
import pytest

pytestmark = pytest.mark.cpu

from dci1.protocol.constants import (
    RESAMPLING_FIELDS,
    ProtocolError,
    StudyConfig,
    study_config,
)


def test_registered_config_carries_every_field():
    config = study_config()
    payload = config.to_dict()
    for field in RESAMPLING_FIELDS:
        assert field in payload and payload[field] is not None
    assert payload["generation_pool_size"] == 16
    assert payload["primary_selection_rule"] == "primary_pool_index=0"
    assert payload["pseudo_run_count"] == 1000


@pytest.mark.parametrize("missing", list(RESAMPLING_FIELDS))
def test_missing_design_defining_field_raises(missing):
    payload = study_config().to_dict()
    del payload[missing]
    with pytest.raises(ProtocolError, match="§2.10|resampling fields"):
        StudyConfig.from_dict(payload)


def test_config_is_immutable():
    config = study_config()
    with pytest.raises(Exception):
        config.generation_pool_size = 32       # frozen dataclass


def _minimal_freeze_inputs():
    from helpers import SPEC

    gate2 = {
        "passed": True, "selected_n": 2, "selected_m": 8,
        "references": ["C1", "C3", "C10"], "certificates": [],
        "admission": [], "n_rates": {}, "m_rates": {},
    }
    gate0 = {"passed": True}
    gate1 = {"status": "PENDING_HUMAN", "passed": False}
    qualification = {"verdict": "QUALIFIED"}
    split_ids = {"calibration": ["a"], "confirmatory": ["b"],
                 "sequestered": ["c"]}
    return SPEC, gate0, gate1, gate2, qualification, split_ids


def test_freeze_record_completeness_and_immutability(tmp_path, monkeypatch):
    from dci1.freeze import record as freeze_module

    spec, gate0, gate1, gate2, qualification, split_ids = \
        _minimal_freeze_inputs()
    monkeypatch.setattr(freeze_module, "environment_record",
                        lambda: {"environment_digest": "x", "gcn_archs": []})
    record = freeze_module.build_freeze_record(
        spec, config=study_config(), gate0=gate0, gate1=gate1, gate2=gate2,
        qualification=qualification, topic_split_ids=split_ids,
        block_plan_hash="h" * 64,
        environment={"environment_digest": "x", "gcn_archs": []})
    for field in RESAMPLING_FIELDS:
        assert field in record["resampling"]
    path = freeze_module.write_freeze(tmp_path, record)
    assert path.exists()
    # rebuilding identically is fine
    freeze_module.write_freeze(tmp_path, record)
    # any changed frozen field is refused
    mutated = dict(record)
    mutated["resampling"] = dict(record["resampling"],
                                 generation_pool_size=32)
    with pytest.raises(ProtocolError, match="immutable"):
        freeze_module.write_freeze(tmp_path, mutated)


def test_incomplete_freeze_record_fails_closed():
    from dci1.freeze.record import validate_freeze

    with pytest.raises(ProtocolError, match="incomplete"):
        validate_freeze({"protocol": {}})


def test_mismatched_config_refused(tmp_path, monkeypatch):
    from helpers import SPEC

    from dci1.freeze import record as freeze_module

    spec, gate0, gate1, gate2, qualification, split_ids = \
        _minimal_freeze_inputs()
    record = freeze_module.build_freeze_record(
        spec, config=study_config(), gate0=gate0, gate1=gate1, gate2=gate2,
        qualification=qualification, topic_split_ids=split_ids,
        block_plan_hash="h" * 64,
        environment={"environment_digest": "x", "gcn_archs": []})
    changed = StudyConfig.from_dict(
        dict(study_config().to_dict(), generation_pool_size=8))
    with pytest.raises(ProtocolError, match="immutable after freeze"):
        freeze_module.assert_freeze_matches(record, SPEC, changed)
    from dci1.models.adapters import get_model

    with pytest.raises(ProtocolError):
        freeze_module.assert_freeze_matches(record, get_model("qwen3-4b"),
                                            study_config())


def test_gate2_failure_is_terminal_for_freeze():
    from helpers import SPEC

    from dci1.freeze.record import build_freeze_record

    with pytest.raises(ProtocolError, match="Gate 2"):
        build_freeze_record(
            SPEC, config=study_config(), gate0={"passed": True},
            gate1={"status": "PENDING_HUMAN"},
            gate2={"passed": False}, qualification={},
            topic_split_ids={}, block_plan_hash="h")


def test_per_model_records_are_independent(monkeypatch):
    """No field of one model's record is inherited from another's: two specs
    with different calibrated inputs produce records differing exactly there."""

    from dci1.freeze import record as freeze_module

    spec, gate0, gate1, gate2, qualification, split_ids = \
        _minimal_freeze_inputs()
    environment = {"environment_digest": "x", "gcn_archs": []}
    a = freeze_module.build_freeze_record(
        spec, config=study_config(), gate0=gate0, gate1=gate1, gate2=gate2,
        qualification=qualification, topic_split_ids=split_ids,
        block_plan_hash="h" * 64, environment=environment)
    gate2_b = dict(gate2, selected_n=3, selected_m=9,
                   references=["C4", "C5", "C10"])
    b = freeze_module.build_freeze_record(
        spec, config=study_config(), gate0=gate0, gate1=gate1,
        gate2=gate2_b, qualification=qualification,
        topic_split_ids=split_ids, block_plan_hash="h" * 64,
        environment=environment)
    assert a["constraints"]["n"] == 2 and b["constraints"]["n"] == 3
    assert a["constraints"]["references"] != b["constraints"]["references"]
    assert a["freeze_hash"] != b["freeze_hash"]
