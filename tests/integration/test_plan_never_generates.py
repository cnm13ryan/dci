"""`dci plan` must be incapable of real generation, not merely arranged to stop.

Before the repair, `plan` ran the pipeline to c242. Two stages inside that range
generate: Gate 0 runs a micro-generation self-test (c222) and the throughput
benchmark generates a whole benchmark design (c242). Under a profile with
dry_run_mode=false those calls reach the real engine, so a command documented as
"no generation" loaded a checkpoint and spent inference budget - and wrote model
output into a run directory.

The proof here is direct: the real backend class is replaced with one that
explodes if it is constructed at all. If the seam ever selects it, the test
fails.
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]

# dry_run_mode=false is the whole point: with it, the seam would hand out the
# REAL engine, so the exploding stub below proves planning never asks for one.
# dev_fast sizes keep the traversal quick, and the pilot/study banks cannot
# reach c216 in this repository anyway - their content-sufficiency gate stops
# earlier, which is a separate pre-freeze gap.
PROFILE = """
model_profile = "dev_fast"
run_mode = "smoke"
dry_run_mode = false
use_google_drive = false
"""

EVIDENCE_PROFILE = """
model_profile = "pilot"
run_mode = "smoke"
dry_run_mode = false
use_google_drive = false
"""


@pytest.fixture
def evidence_capable_profile(tmp_path):
    """Non-dry-run and evidence-capable, at smoke sizes so the test is quick."""
    path = tmp_path / "pilot_real.toml"
    path.write_text(PROFILE)
    return path


@pytest.fixture
def forbid_real_generation(monkeypatch):
    """Make any real-engine construction or oracle generation a hard failure."""
    calls = []

    class _Exploding:
        def __init__(self, *a, **k):
            calls.append("hf_transformers")
            raise AssertionError(
                "the real inference engine was constructed during `dci plan`")

    import dci.inference.hf_transformers as hf
    import dci.inference.oracle as oracle
    monkeypatch.setattr(hf, "HFTransformersBackend", _Exploding)

    real_generate = oracle.OracleBackend.generate

    def _watched(self, rows, seed):
        calls.append("oracle")
        return real_generate(self, rows, seed)

    monkeypatch.setattr(oracle.OracleBackend, "generate", _watched)
    return calls


def _plan(profile: Path, tmp_path: Path) -> int:
    from dci.cli import main
    return main(["plan", "--profile", str(profile),
                 "--data-root", str(tmp_path / "artifacts")])


def test_plan_on_a_non_dry_run_profile_generates_nothing(
        evidence_capable_profile, forbid_real_generation, tmp_path):
    code = _plan(evidence_capable_profile, tmp_path)
    assert code == 0, "planning must complete, not crash"
    assert forbid_real_generation == [], (
        f"planning reached a generation path: {forbid_real_generation}")


def test_the_backend_bound_during_planning_refuses_to_generate(
        evidence_capable_profile, forbid_real_generation, tmp_path):
    _plan(evidence_capable_profile, tmp_path)
    from dci.pipeline import state as S
    from dci.inference.planning import PlanningModeViolation
    assert S.BACKEND.name == "planning_no_generation"
    with pytest.raises(PlanningModeViolation):
        S.BACKEND.generate([{"row_id": "r"}], 7)


def test_planning_stops_before_the_first_generating_stage(
        evidence_capable_profile, forbid_real_generation, tmp_path):
    """c222 (Gate 0 micro-generation) and c242 (benchmark) must not be reached."""
    import sys
    _plan(evidence_capable_profile, tmp_path)
    reached = {name.rsplit(".", 1)[-1] for name in sys.modules
               if name.startswith("dci.pipeline.stages.c")}
    assert any(n.startswith("c216") for n in reached), reached
    assert not any(n.startswith(("c222", "c232", "c242")) for n in reached), reached


def test_planning_writes_no_response_artifacts(
        evidence_capable_profile, forbid_real_generation, tmp_path):
    _plan(evidence_capable_profile, tmp_path)
    responses = list((tmp_path / "artifacts").rglob("responses/*"))
    assert responses == [], responses


def test_qualify_is_the_command_that_may_generate(tmp_path):
    """The evidence guard applies to qualify, so it refuses without --execute."""
    from dci.cli import main
    path = tmp_path / "pilot.toml"
    path.write_text(EVIDENCE_PROFILE)
    with pytest.raises(SystemExit) as exit_info:
        main(["qualify", "--profile", str(path),
              "--data-root", str(tmp_path / "artifacts")])
    assert exit_info.value.code == 2


def test_the_stages_plan_used_to_traverse_do_generate():
    """Host-independent proof of the defect the boundary change fixes.

    The end-to-end reproduction needs CUDA: on a CPU-only host a non-dry-run
    profile stops at the accelerator guard in c122 before reaching Gate 0. What
    is verifiable anywhere is the condition that made the old boundary unsafe -
    stages inside the old plan range (c216 < stage <= c242) call the generation
    entry point, and with dry_run_mode=false that entry point is the real engine.
    """
    from pathlib import Path
    from dci.cli import PLAN_LAST_STAGE, QUALIFY_LAST_STAGE
    from dci.pipeline.stages import ORDER

    stages = Path("src/dci/pipeline/stages")
    names = [n for n in ORDER
             if PLAN_LAST_STAGE < n[:4] <= QUALIFY_LAST_STAGE]
    # `S.run_generation_stage(` is the CALL; c192 defines the function and is
    # matched by a looser search without invoking anything at import.
    generating = [n for n in names
                  if "S.run_generation_stage(" in (stages / f"{n}.py").read_text()]
    assert generating, names
    assert any(n.startswith("c222") for n in generating), generating
    assert any(n.startswith("c242") for n in generating), generating

    # And nothing in the new plan range does.
    planned = [n for n in ORDER if n[:4] <= PLAN_LAST_STAGE]
    leaks = [n for n in planned
             if "S.run_generation_stage(" in (stages / f"{n}.py").read_text()]
    assert leaks == [], leaks
