"""Spot checks on the extracted verifier rules: identical verdicts to the
notebook's unit expectations (the full 96-assertion battery still runs inside
the pipeline as part of Gate 0)."""
import pytest

from dci.verifiers import rules as R

pytestmark = pytest.mark.cpu


def test_exact_sentence_count():
    four = ("One begins here. Two continues clearly. "
            "Three adds useful context. Four concludes the response.")
    assert R.v_exact_sentence_count(four, 4).status == "full"
    assert R.v_exact_sentence_count("One. Two.", 4).status == "violation"
    assert R.v_exact_sentence_count("", 4).status == "unscorable"


def test_increasing_lengths():
    assert R.v_increasing_lengths(
        "Birds fly. Small birds fly swiftly. "
        "Many small birds fly swiftly above fields.").status == "full"
    assert R.v_increasing_lengths(
        "Birds fly now. Fish swim fast. Clouds move away.").status == "violation"


def test_count_status_zero_of_n_is_violation():
    status, binary, _ = R.count_status(0, 1)
    assert status == "violation" and binary == 0


def test_paren_pairs_balance():
    assert R.v_paren_pairs("The tide (twice daily) shapes the shore.", 1).status == "full"
    assert R.v_paren_pairs("The tide (twice daily) shapes (the shore.", 1).binary_pass == 0
