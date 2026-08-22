"""§3.2 L4 is gated per named member; `emit_l4` compares level *sets*.

This is a **characterization test of a post-freeze defect**, not a
specification. It pins what the sealed emitter does, because the emitter may
not move: `run_unmasked_analysis` refuses an unmasked analysis under code
that differs from the masked seal, and §20 forbids regenerating a mask after
semantic identities are known. Correcting `emit_l4` would therefore either
strand both v4r4 replications (their unmasked analyses could never be
recomputed) or require a mask regenerated after unmasking, which the
protocol forbids outright. The correction belongs to the next revision.

Until then this test fails loudly if someone edits `emit_l4`, which is the
point: the edit is the thing that breaks the study, not the defect.

The defect is recorded in `CHANGES_SCIENTIFIC.md` and its consequence ---
`gemma-3n-e4b-it`'s emitted L4 is invalidated --- is stated in the execution
report and recomputed in `tools/v4r4_final_report.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v4r4.analysis import claims as CL          # noqa: E402
from dci1v4r4.protocol import constants as C        # noqa: E402

BASIS = "deterministic_measurement_validated"


def _l4(per_configuration):
    return CL.emit_l4(per_configuration=per_configuration,
                      measurement_basis=BASIS)


def test_the_registered_configurations_are_the_two_outcome_positions():
    assert set(C.CONFIGURATIONS) == {"outcome_first", "outcome_second"}


def test_l4_emits_when_the_same_member_reaches_the_same_level():
    # The `qwen3-4b` shape: D(A<-B) reaches L1 in both configurations.
    out = _l4({"outcome_first": ["L1"], "outcome_second": ["L1"]})
    assert out["emitted"] is True


def test_l4_withholds_when_the_level_sets_differ():
    out = _l4({"outcome_first": ["L1", "L2"], "outcome_second": ["L1"]})
    assert out["emitted"] is False
    assert "did not reach the same" in out["reason"]


def test_l4_withholds_when_no_configuration_reached_a_level():
    out = _l4({"outcome_first": [], "outcome_second": []})
    assert out["emitted"] is False


def test_l4_withholds_when_a_configuration_is_missing():
    out = _l4({"outcome_first": ["L1"]})
    assert out["emitted"] is False


def test_the_defect_emits_l4_when_the_members_swap_across_configurations():
    """The `gemma-3n-e4b-it` shape, and why its emitted L4 is invalidated.

    Both configurations reach L1, so the level sets match and `emit_l4`
    emits. But in `outcome_first` the member reaching L1 is D(A<-B) and in
    `outcome_second` it is D(B<-A) --- each named member's classification
    *flips*. §3.2 licenses L1 on "the named D(c <- g)" and §28.1's
    *Configuration dependence* row says "**the quantity** is configuration-
    dependent", so the registered gate is per member and does not hold here.

    `emit_l4` cannot see the difference: its input is a list of level names
    with the member identity already discarded by `run/analysis_run.py`.
    """
    swapped = _l4({"outcome_first": ["L1"], "outcome_second": ["L1"]})
    assert swapped["emitted"] is True, (
        "characterizing the defect: identical level sets emit L4 even when "
        "the members that reached L1 swapped places")
    # The input the emitter is handed carries no member identity at all,
    # which is what makes the defect unreachable from inside the emitter.
    assert "member" not in swapped
    assert swapped["levels_by_configuration"] == {
        "outcome_first": ["L1"], "outcome_second": ["L1"]}


def test_the_emitter_input_discards_member_identity():
    """The producing expression in `run/analysis_run.py`, pinned by shape."""
    src = (Path(__file__).resolve().parents[1] / "src" / "dci1v4r4" / "run"
           / "analysis_run.py").read_text()
    assert '[s["claim_level"] for s in v["statements"]' in src, (
        "if this expression changed, `emit_l4`'s input changed, and the "
        "characterization above no longer describes the sealed analysis")
