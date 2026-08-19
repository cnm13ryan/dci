"""T11. Masking.

Companion-label permutation within (outcome, order, block); solo cells
unpermuted; separate pilot and confirmatory namespaces; single unmask; mask-key
access restriction; exact masked-phase rerun from the recorded analysis-code
hash; the declared inability to compute joint states while masked.
"""
from __future__ import annotations

import pytest

from dci1v4.analysis import masking
from dci1v4.analysis.observations import Observation
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C

SLOTS = ("A", "B", "R1", "R2", "R3")


def _observations(blocks=16):
    out = []
    for index in range(blocks):
        block = f"b{index:03d}"
        for slot in SLOTS:
            out.append(Observation(
                block_id=block, cell_id=f"{block}:solo:{slot}",
                cell_type=f"solo:{slot}", outcome_slot=slot,
                companion_slot=None, position=1, configuration=None, draws=4,
                compliance=0.8, graded=0.8, vacuity=0.0, truncation=0.0,
                non_vacuous_compliance=0.8, response_words=60.0,
                processing_failures=0))
        for outcome in SLOTS:
            for companion in SLOTS:
                if outcome == companion:
                    continue
                for position in (1, 2):
                    configuration = ("outcome_first" if position == 1
                                     else "outcome_second")
                    out.append(Observation(
                        block_id=block,
                        cell_id=f"{block}:{outcome}+{companion}:{position}",
                        cell_type=f"pair:{outcome}+{companion}",
                        outcome_slot=outcome, companion_slot=companion,
                        position=position, configuration=configuration,
                        draws=4, compliance=0.6, graded=0.6, vacuity=0.0,
                        truncation=0.0, non_vacuous_compliance=0.6,
                        response_words=55.0, processing_failures=0))
    return out


def test_the_permutation_is_within_outcome_order_and_block():
    observations = _observations()
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=12345)
    masked = masking.apply_mask(observations, mask)
    by_group: dict[tuple, list] = {}
    for original, permuted in zip(observations, masked):
        if original.companion_slot is None:
            continue
        key = (original.outcome_slot, original.configuration,
               original.block_id)
        by_group.setdefault(key, []).append(permuted.companion_label)
    for key, labels in by_group.items():
        # The permutation is a bijection of the companions present in the
        # group: the multiset is preserved and only the assignment moves.
        assert sorted(labels) == sorted(s for s in SLOTS if s != key[0])


def test_solo_cells_are_not_permuted():
    observations = _observations()
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=1)
    masked = masking.apply_mask(observations, mask)
    for original, permuted in zip(observations, masked):
        if original.companion_slot is None:
            assert permuted.companion_label is None


def test_the_mask_must_differ_from_the_truth_in_at_least_half_the_blocks():
    observations = _observations(blocks=32)
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=7)
    report = masking.assert_mask_effective(observations, mask)
    assert report["min_differing_share"] >= C.MASK_MIN_DIFFERING_FRACTION

    identity = {key: key.split("|")[-1] for key in mask["mapping"]}
    with pytest.raises(IntegrityError, match="ineffective"):
        masking.assert_mask_effective(observations,
                                      {**mask, "mapping": identity})


def test_the_two_mask_namespaces_are_separate():
    assert C.MASK_NAMESPACES == ("pilot_mask", "confirmatory_mask")
    observations = _observations(blocks=4)
    pilot = masking.build_mask(observations, namespace="pilot_mask",
                               entropy=1)
    confirmatory = masking.build_mask(observations,
                                      namespace="confirmatory_mask",
                                      entropy=1)
    assert pilot["namespace"] != confirmatory["namespace"]
    with pytest.raises(ProtocolError):
        masking.build_mask(observations, namespace="other", entropy=1)


def test_the_mask_key_is_opened_exactly_once(tmp_path):
    observations = _observations(blocks=4)
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=3)
    key = masking.MaskKey(tmp_path / "mask_key.json")
    key.write(mask)
    assert key.opens == 0
    assert key.open_once()["mask_key_hash"] == mask["mask_key_hash"]
    assert key.opens == 1
    with pytest.raises(IntegrityError, match="exactly one open"):
        key.open_once()


def test_the_mask_key_is_write_once(tmp_path):
    observations = _observations(blocks=2)
    mask = masking.build_mask(observations, namespace="pilot_mask", entropy=1)
    key = masking.MaskKey(tmp_path / "mask_key.json")
    key.write(mask)
    with pytest.raises(IntegrityError, match="write-once"):
        key.write(mask)


def test_unmasking_records_the_analysis_code_hash_and_the_limitation(tmp_path):
    observations = _observations(blocks=2)
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=5)
    key = masking.MaskKey(tmp_path / "mask_key.json")
    key.write(mask)
    record = masking.unmask(key, analysis_code_hash="abc",
                            masked_outputs_hash="def")
    assert record["analysis_code_hash"] == "abc"
    assert record["mask_key_hash"] == mask["mask_key_hash"]
    assert record["declared_limitation"] == masking.DECLARED_LIMITATION
    assert "post-unmasking" in record["post_unmasking_note"]
    assert "unmasked_at" in record


def test_the_masked_view_carries_no_companion_identifying_field():
    observations = _observations(blocks=2)
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=2)
    masked = masking.apply_mask(observations, mask)
    records = [vars(m) for m in masked]
    masking.assert_masked_view_clean(records)
    with pytest.raises(IntegrityError, match="companion-identifying"):
        masking.assert_masked_view_clean([{"cell_id": "leak"}])


def test_joint_states_are_computed_post_unmasking_and_support_no_claim():
    from dci1v4.analysis.diagnostics import joint_states

    rows = [{"load": 2, "cell_type": "pair:A+B:c1_first",
             "scores": [{"position": 1, "passed": True},
                        {"position": 2, "passed": False}]},
            {"load": 2, "cell_type": "pair:A+B:c1_first",
             "scores": [{"position": 1, "passed": True},
                        {"position": 2, "passed": True}]}]
    report = joint_states(rows)
    assert report["computed"] == "post-unmasking"
    assert "L1, L2 and L3 never read these" in report["supports_claims"]
    vector = report["cells"]["pair:A+B:c1_first"]["vector"]
    assert vector["P(1,1)"] == 0.5 and vector["P(1,0)"] == 0.5
    assert "permuted independently" in masking.DECLARED_LIMITATION


def test_the_analysis_code_hash_reproduces_from_the_recorded_files(tmp_path):
    first = tmp_path / "a.py"
    second = tmp_path / "b.py"
    first.write_text("x = 1\n")
    second.write_text("y = 2\n")
    digest = masking.analysis_code_hash([first, second])
    assert masking.analysis_code_hash([second, first]) == digest
    first.write_text("x = 2\n")
    assert masking.analysis_code_hash([first, second]) != digest
