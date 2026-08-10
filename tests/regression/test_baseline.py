"""The required baseline regression (migration spec section 17).

`test_dev_fast_pipeline` runs the full migrated dry run and compares 38
deterministic artifacts against the captured notebook fixture byte-for-byte
(after stripping volatile identity fields). `test_integration_pass_baseline`
reruns the no-bypass self-test and asserts the frozen trace:

    Gate 0 -> PASS, Gate M -> PASS, Gate 1 -> PASS, Gate 2a -> PASS,
    Gate 2 -> NOT_IDENTIFIED_SUPPORT, zero bypasses, exit 10.

That final status is the expected scientific outcome, not a failure of the
port; treating it as success is deliberate and documented.
"""
import os
from pathlib import Path

import pytest

from tests.regression.compare import compare_runs

pytestmark = [pytest.mark.cpu, pytest.mark.slow]
FIXTURE = Path(os.environ.get(
    "DCI_FIXTURE_DIR",
    str(Path(__file__).parent / "fixture_dev_fast")))


def _run(profile: str, tmp_path: Path) -> int:
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    cfg = loader.load_profile(Path("configs/profiles") / f"{profile}.toml")
    cfg.data_root = str(tmp_path / "artifacts")
    loader.activate(cfg)
    return run_pipeline()


# The v15 notebook-fidelity comparison. v15.1 DELIBERATELY diverges from it:
# reference admission gained the kappa audit and the family-level certificate,
# calibration excludes unsatisfiable pairs, the placebo slice became disjoint,
# top_k became explicit, an endpoint was renamed and new artifacts were added.
# Comparing v15.1 output to a v15 fixture must therefore FAIL -- keeping the test
# green would mean the repairs had no effect.
#
# It is retained, xfail, for two reasons: it documents exactly which artifacts the
# repair moved, and it is the mechanism for re-baselining once a v15.1 fixture is
# captured. Two pre-existing failures on darwin/arm64 are also folded in here and
# are NOT caused by the repairs: ~1e-9 float drift (the comparator's docstring
# assumes one container, one numpy build) and a prescreen tie-ordering difference.
V15_1_DIVERGENCES = (
    "kappa eligibility audit now enforced in admit_candidates",
    "reference-error certificate aggregates per family, not per component",
    "unsatisfiable candidate-U pairs excluded from calibration designs",
    "placebo clusters disjoint from confirmatory clusters",
    "top_k explicit -> execution fingerprint changes",
    "strict_or_unscorable renamed to violation_or_unscorable_partial_forgiven",
    "new artifacts: claim_rule inference_status, output_cap_*, "
    "power_planning (12-contrast family), primary_table_support, "
    "instruction_form_balance",
)


@pytest.mark.skipif(not FIXTURE.exists(), reason="notebook fixture not present")
@pytest.mark.xfail(strict=True, reason=(
    "v15.1 intentionally diverges from the frozen v15 fixture: "
    + "; ".join(V15_1_DIVERGENCES)
    + ". Re-baseline against a v15.1 capture rather than making this pass."))
def test_dev_fast_pipeline_matches_notebook_fixture(tmp_path):
    code = _run("dev_fast", tmp_path)
    assert code == 0
    runs = sorted((tmp_path / "artifacts").rglob("run-*/gates"))
    assert runs, "no run directory produced"
    problems, compared = compare_runs(FIXTURE, runs[0].parent)
    assert len(compared) >= 30
    assert not problems, "\n".join(problems)


def test_dev_fast_still_reaches_export_under_v15_1(tmp_path):
    """What the fidelity test used to guarantee, minus byte-equality.

    The dry run must still traverse every stage to export; only the ARTIFACT
    CONTENT is allowed to differ from v15.
    """
    from dci.pipeline import state as S
    assert _run("dev_fast", tmp_path) == 0
    assert S.CFG.protocol_version == "v15.1"
    runs = sorted((tmp_path / "artifacts").rglob("run-*/gates"))
    assert runs, "no run directory produced"
    _, compared = compare_runs(FIXTURE, runs[0].parent)
    assert len(compared) >= 30, (
        f"only {len(compared)} artifacts were produced; the repair must not "
        "reduce the artifact set")


def test_integration_pass_baseline(tmp_path):
    from dci.pipeline import state as S
    from dci.pipeline.runner import EXIT_SCIENTIFIC
    code = _run("integration_pass", tmp_path)
    trace = [(g, o.status, o.dry_run_bypassed) for g, o in S.GATE_STATE.items()]
    assert code == EXIT_SCIENTIFIC
    assert not any(b for *_, b in trace), "a bypass occurred in integration_pass"
    got = [(g, s) for g, s, _ in trace]
    for expected in [("0_implementation", "PASS"), ("M_measurement", "PASS"),
                     ("1_u_bank", "PASS"), ("2a_precision", "PASS"),
                     ("2_feasibility", "NOT_IDENTIFIED_SUPPORT")]:
        assert expected in got, f"missing {expected} in {got}"


# Gate 0's self-test count is a provenance record, not a target. The migration
# froze it at 110. The v15.1 repairs ADD invariants, so the count rises; every
# check must still pass. Growth is expected, shrinkage never is.
GATE0_CHECKS_V15_0 = 110
GATE0_CHECKS_ADDED_V15_1 = {
    "power_planner_covers_the_actual_primary_family",
    "both_orders_is_never_easier_than_one_order",
    "feature_roles_match_the_caliper_machinery",
    "mechanism_and_post_treatment_features_are_never_matched",
}
GATE0_CHECKS_EXPECTED = GATE0_CHECKS_V15_0 + len(GATE0_CHECKS_ADDED_V15_1)


def test_gate0_all_checks_pass(tmp_path):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(tmp_path / "artifacts")
    loader.activate(cfg)
    assert run_pipeline(until="c222") == 0
    import pandas as pd
    table = pd.read_csv(Path(S.GATE_DIR) / "gate0_selftest.csv")
    failed = table.loc[~table["passed"].astype(bool), "check"].tolist()
    assert not failed, f"gate 0 checks failed: {failed}"
    assert len(table) == GATE0_CHECKS_EXPECTED, (
        f"gate 0 has {len(table)} checks, expected {GATE0_CHECKS_EXPECTED} "
        f"({GATE0_CHECKS_V15_0} from v15.0 plus "
        f"{sorted(GATE0_CHECKS_ADDED_V15_1)}). A DROP means an invariant was "
        "removed and must be justified, not re-baselined.")
    assert GATE0_CHECKS_ADDED_V15_1 <= set(table["check"])
