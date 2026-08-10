"""The completeness ledger must range over the planned generation manifest.

Appendix I requires exactly one terminal state per *planned* generation ID. The
reviewed implementation iterated the ledger's own keys, so a generation that was
deleted outright - including the case of an entirely empty ledger - passed
vacuously. That is precisely the failure mode section 12.10 forbids: a
permanently missing generation must be *represented* by a terminal missing state
and interval completion, never removed from the scientific population.
"""
import pytest

from dci.v19 import identity
from dci.v19.identity import (LedgerViolation, TERMINAL_MISSING,
                              TERMINAL_OBSERVED, assert_one_terminal_state)

pytestmark = pytest.mark.cpu

PLANNED = ("g1", "g2", "g3")


def observed(attempt=1):
    return {"attempt": attempt, "terminal": True, "state": TERMINAL_OBSERVED,
            "output_hash": "sha256:" + "a" * 64, "output_path": "raw/g.json"}


def missing(attempt=3):
    return {"attempt": attempt, "terminal": True, "state": TERMINAL_MISSING,
            "retries_exhausted": True}


def failed(attempt):
    return {"attempt": attempt, "terminal": False, "failure": "worker_death"}


def healthy():
    return {"g1": [observed()],
            "g2": [failed(1), failed(2), missing(3)],
            "g3": [failed(1), observed(2)]}


def test_a_complete_ledger_passes():
    report = assert_one_terminal_state(healthy(), PLANNED)
    assert report.n_planned == 3
    assert report.n_observed == 2
    assert report.n_permanently_missing == 1
    assert report.missingness_rate == pytest.approx(1 / 3)


def test_an_empty_ledger_is_a_failure_not_a_vacuous_pass():
    """The exact defect: {} used to satisfy the gate."""
    with pytest.raises(LedgerViolation, match="3 planned generations are absent"):
        assert_one_terminal_state({}, PLANNED)


def test_a_deleted_generation_is_refused():
    ledger = healthy()
    del ledger["g2"]
    with pytest.raises(LedgerViolation, match="absent"):
        assert_one_terminal_state(ledger, PLANNED)


def test_a_deleted_permanently_missing_generation_is_refused():
    """Dropping the interval-completed row is the tempting shortcut."""
    ledger = {"g1": [observed()], "g3": [observed()]}
    with pytest.raises(LedgerViolation) as caught:
        assert_one_terminal_state(ledger, PLANNED)
    assert "g2" in str(caught.value)


def test_an_unexpected_generation_is_refused():
    ledger = healthy()
    ledger["g_rogue"] = [observed()]
    with pytest.raises(LedgerViolation, match="not in the planned manifest"):
        assert_one_terminal_state(ledger, PLANNED)


def test_an_empty_planned_manifest_is_refused():
    with pytest.raises(LedgerViolation, match="planned manifest is empty"):
        assert_one_terminal_state({}, [])


def test_a_duplicated_planned_id_is_refused():
    with pytest.raises(LedgerViolation, match="duplicate"):
        assert_one_terminal_state({"g1": [observed()]}, ["g1", "g1"])


def test_no_terminal_state_is_refused():
    ledger = healthy()
    ledger["g1"] = [failed(1), failed(2)]
    with pytest.raises(LedgerViolation, match="0 terminal states"):
        assert_one_terminal_state(ledger, PLANNED)


def test_two_terminal_states_are_refused():
    ledger = healthy()
    ledger["g1"] = [observed(1), observed(2)]
    with pytest.raises(LedgerViolation, match="2 terminal states"):
        assert_one_terminal_state(ledger, PLANNED)


def test_no_attempt_lineage_is_refused():
    ledger = healthy()
    ledger["g1"] = []
    with pytest.raises(LedgerViolation, match="no attempt lineage"):
        assert_one_terminal_state(ledger, PLANNED)


def test_non_monotonic_attempts_are_refused():
    ledger = healthy()
    ledger["g1"] = [failed(1), observed(3)]
    with pytest.raises(LedgerViolation, match="non-monotonic"):
        assert_one_terminal_state(ledger, PLANNED)


def test_the_terminal_attempt_must_be_the_last_one():
    ledger = healthy()
    ledger["g1"] = [observed(1), failed(2)]
    with pytest.raises(LedgerViolation, match="terminal state at attempt 1"):
        assert_one_terminal_state(ledger, PLANNED)


def test_an_unknown_terminal_state_is_refused():
    ledger = healthy()
    ledger["g1"] = [{"attempt": 1, "terminal": True, "state": "PROBABLY_FINE"}]
    with pytest.raises(LedgerViolation, match="not a terminal scientific state"):
        assert_one_terminal_state(ledger, PLANNED)


def test_a_terminal_record_without_a_state_is_refused():
    """A missing state is missing evidence, not a default success."""
    ledger = healthy()
    ledger["g1"] = [{"attempt": 1, "terminal": True}]
    with pytest.raises(LedgerViolation, match="terminal scientific state"):
        assert_one_terminal_state(ledger, PLANNED)


@pytest.mark.parametrize("drop", ["output_hash", "output_path"])
def test_a_success_without_durable_output_linkage_is_refused(drop):
    ledger = healthy()
    record = observed()
    del record[drop]
    ledger["g1"] = [record]
    with pytest.raises(LedgerViolation, match="durable"):
        assert_one_terminal_state(ledger, PLANNED)


def test_a_success_with_an_empty_output_hash_is_refused():
    ledger = healthy()
    ledger["g1"] = [{**observed(), "output_hash": ""}]
    with pytest.raises(LedgerViolation, match="durable"):
        assert_one_terminal_state(ledger, PLANNED)


def test_permanent_missingness_requires_exhausted_retries():
    ledger = healthy()
    ledger["g2"] = [failed(1), {"attempt": 2, "terminal": True,
                                "state": TERMINAL_MISSING}]
    with pytest.raises(LedgerViolation, match="exhausted retry lineage"):
        assert_one_terminal_state(ledger, PLANNED)


def test_permanent_missingness_cannot_claim_a_durable_output():
    ledger = healthy()
    ledger["g2"] = [failed(1), {**missing(2), "output_hash": "sha256:x"}]
    with pytest.raises(LedgerViolation, match="durable output"):
        assert_one_terminal_state(ledger, PLANNED)


def test_the_gate_is_wired_to_a_real_expanded_manifest():
    """Not an isolated helper: the planned set comes from expand_superblock."""
    planned = identity.expand_superblock(
        "p1", 1, identity.context_fingerprint({"task": "T1"}),
        ["b_lo", "b_mid", "b_hi"], 2, "sha256:model")
    ids = [row.generation for row in planned]
    ledger = {gen: [observed()] for gen in ids}
    report = assert_one_terminal_state(ledger, ids)
    assert report.n_planned == len(ids) == identity.generations_per_superblock(3, 2)
    assert report.n_observed == len(ids)

    ledger.pop(ids[7])
    with pytest.raises(LedgerViolation, match="absent"):
        assert_one_terminal_state(ledger, ids)


def test_the_manifest_helper_derives_the_planned_set_and_root_hash():
    planned = identity.expand_superblock("p1", 1, "fp", ["b"], 1, "sha256:m")
    manifest = identity.GenerationManifest.from_planned(planned)
    assert manifest.generation_ids == tuple(p.generation for p in planned)
    assert len(manifest.root_hash) == 64
    # Same rows, same hash; one row removed, different hash.
    assert manifest.root_hash == identity.GenerationManifest.from_planned(
        planned).root_hash
    assert manifest.root_hash != identity.GenerationManifest.from_planned(
        planned[:-1]).root_hash
    manifest.assert_complete({gen: [observed()] for gen in manifest.generation_ids})
