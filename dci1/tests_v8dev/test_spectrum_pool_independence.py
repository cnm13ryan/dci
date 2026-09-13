"""Finding 3 of the 2026-09-02 audit, the pool-composition half: v8's
spectrum selection draws from every SPECTRUM-valid rung of the frame and is
never restricted to LOCAL-valid (V_diff-passing) families, which is how v7's
spectrum inherited the LOCAL caliper. Structural, on the mandatory path."""
from __future__ import annotations

import ast
import inspect

from dci1v8dev.spectrum import selection, validity


def _names(module) -> set[str]:
    tree = ast.parse(inspect.getsource(module))
    out = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    out |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    out |= {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)}
    return out


def test_spectrum_selection_reads_no_local_verdict():
    names = _names(selection)
    forbidden = {"V_diff", "local_valid", "local_validity", "n_local_valid",
                 "local_valid_families", "REFERENCE_CALIPER",
                 "admit_core_references", "LOCAL_COMPONENTS"}
    assert not (names & forbidden), names & forbidden


def test_spectrum_rule_has_no_v_diff_and_local_rule_keeps_it():
    assert "V_diff" not in validity.SPECTRUM_COMPONENTS
    assert "V_diff" in validity.LOCAL_COMPONENTS
    assert "V_diff" not in validity.UNFOLDED_SPLIT_COMPONENTS
