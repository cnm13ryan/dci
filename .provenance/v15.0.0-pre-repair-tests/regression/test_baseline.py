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


@pytest.mark.skipif(not FIXTURE.exists(), reason="notebook fixture not present")
def test_dev_fast_pipeline_matches_notebook_fixture(tmp_path):
    code = _run("dev_fast", tmp_path)
    assert code == 0
    runs = sorted((tmp_path / "artifacts").rglob("run-*/gates"))
    assert runs, "no run directory produced"
    problems, compared = compare_runs(FIXTURE, runs[0].parent)
    assert len(compared) >= 30
    assert not problems, "\n".join(problems)


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


def test_gate0_is_110(tmp_path):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(tmp_path / "artifacts")
    loader.activate(cfg)
    assert run_pipeline(until="c222") == 0
    import pandas as pd
    table = pd.read_csv(Path(S.GATE_DIR) / "gate0_selftest.csv")
    assert len(table) == 110 and int(table["passed"].sum()) == 110
