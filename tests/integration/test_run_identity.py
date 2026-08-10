"""An explicit --run-id must not let two execution identities share a directory.

The automatic resume rule only ever selects a run directory whose recorded
execution fingerprint matches the current one, so it was safe. An explicit
--run-id skipped the check completely and returned the directory unread. Batches
generated under one execution condition then landed beside batches generated
under another, inside a directory whose run_meta.json claims a single identity -
and every frozen-manifest guard downstream reasons per batch, not per directory,
so nothing could separate them afterwards.

The refusal surfaces as a scientific stop (exit 10) carrying
RUN_INTEGRITY_FAILURE, because it is a protocol-level refusal rather than a
crash. No stop record is written for it: the refusal happens before a run root
has been chosen, and the one directory that exists is precisely the one that
must not be written to.
"""
import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]

RUN_ID = "fixed-run-id"


def _run(tmp_path: Path, run_id: str | None, seed: int | None = None,
         until: str = "c122"):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(tmp_path / "artifacts")
    cfg.use_google_drive = False
    cfg.run_id = run_id
    if seed is not None:
        cfg.protocol_overrides = {"base_seed": seed}
    loader.activate(cfg)
    code = run_pipeline(until=until)
    return code, getattr(S, "RUN_ROOT", None)


def _meta(root: Path) -> dict:
    return json.loads((root / "run_meta.json").read_text())


def test_reusing_a_run_id_under_the_same_fingerprint_resumes(tmp_path):
    code, root = _run(tmp_path, RUN_ID)
    assert code == 0 and root is not None
    first = _meta(root)

    code, again = _run(tmp_path, RUN_ID)
    assert code == 0
    assert again == root
    # Same identity, same directory, and the manifest was not rewritten.
    assert _meta(root)["execution_sha256"] == first["execution_sha256"]
    assert _meta(root)["created_utc"] == first["created_utc"]


def test_reusing_a_run_id_under_a_different_fingerprint_is_refused(tmp_path,
                                                                  capsys):
    from dci.pipeline.runner import EXIT_SCIENTIFIC
    code, root = _run(tmp_path, RUN_ID)
    assert code == 0
    frozen = _meta(root)["execution_sha256"]
    before = sorted(p.name for p in root.iterdir())
    capsys.readouterr()

    code, _ = _run(tmp_path, RUN_ID, seed=999_777)

    assert code == EXIT_SCIENTIFIC
    printed = capsys.readouterr().out
    assert "RUN_INTEGRITY_FAILURE" in printed
    assert "base_seed" in printed
    assert frozen[:12] in printed
    # Refused BEFORE writing: the directory is untouched.
    assert sorted(p.name for p in root.iterdir()) == before
    assert _meta(root)["execution_sha256"] == frozen


def test_a_directory_with_artifacts_and_no_manifest_is_refused(tmp_path, capsys):
    from dci.pipeline.runner import EXIT_SCIENTIFIC
    code, root = _run(tmp_path, RUN_ID)
    assert code == 0
    (root / "run_meta.json").unlink()
    (root / "responses").mkdir(exist_ok=True)
    (root / "responses" / "batch_0.jsonl").write_text('{"row_id": "r"}\n')
    capsys.readouterr()

    assert _run(tmp_path, RUN_ID)[0] == EXIT_SCIENTIFIC
    printed = capsys.readouterr().out
    assert "RUN_INTEGRITY_FAILURE" in printed
    assert "no run_meta.json" in printed


def test_an_unreadable_manifest_is_refused_rather_than_ignored(tmp_path, capsys):
    from dci.pipeline.runner import EXIT_SCIENTIFIC
    code, root = _run(tmp_path, RUN_ID)
    assert code == 0
    (root / "run_meta.json").write_text("{not json")
    capsys.readouterr()

    assert _run(tmp_path, RUN_ID)[0] == EXIT_SCIENTIFIC
    assert "cannot be read" in capsys.readouterr().out


def test_an_empty_leftover_directory_is_usable(tmp_path):
    """A bare directory is not evidence of a conflicting identity."""
    code, root = _run(tmp_path, RUN_ID)
    assert code == 0
    for child in sorted(root.rglob("*"), reverse=True):
        child.rmdir() if child.is_dir() else child.unlink()
    assert _run(tmp_path, RUN_ID, seed=424_242)[0] == 0


def test_a_fresh_run_id_is_unaffected(tmp_path):
    assert _run(tmp_path, RUN_ID)[0] == 0
    code, root = _run(tmp_path, "another-id", seed=999_777)
    assert code == 0
    assert root.name == "another-id"


def test_the_automatic_resume_rule_still_matches_on_fingerprint(tmp_path):
    """No --run-id: a matching run is reused, a different one is not."""
    code, first = _run(tmp_path, None)
    assert code == 0
    code, same = _run(tmp_path, None)
    assert code == 0 and same == first
    code, other = _run(tmp_path, None, seed=31_337)
    assert code == 0 and other != first
