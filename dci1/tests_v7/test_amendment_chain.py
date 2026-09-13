"""v7 A4: an amendment adopted after rows exist is bindable, once, in order.

v6's lifecycle could replace a registration before any observation and
retire one stage-1 verdict before any row, and nothing else --- so A16 and
A17, adopted with rows on the tree, left every surviving replication unable
to pass ``protocol_hashes_agree``. This is the third path §32 describes:
a signed, append-only chain from the registered document hashes to the
amended ones, read by the pre-freeze audit and bound by the freeze.
"""
from __future__ import annotations

import json
from pathlib import Path

import dci1v7
import pytest
from dci1v4.errors import IntegrityError
from dci1v4.models.registry import MODELS
from dci1v7.engine.context import synthetic_context
from dci1v7.engine.paths import model_tree
from dci1v7.protocol import constants as C
from dci1v7.protocol import manifest
from dci1v7.run import registration_run

COMMIT = "0" * 40
MODEL = MODELS[0].model_key


@pytest.fixture
def study(tmp_path, v7_repo):
    """A registered synthetic study at an isolated repository root."""
    ctx = synthetic_context(tmp_path, repo_root=v7_repo)
    tree = model_tree(ctx, MODEL)
    tree.root.mkdir(parents=True, exist_ok=True)
    registration_run.run_registration(
        tree, producing_commit=COMMIT, adoption={"status": "SYNTHETIC"},
        repo_root=v7_repo, environment_digest="test")
    return ctx, tree, Path(v7_repo)


def _touch_prereg(repo: Path, text: str) -> None:
    path = repo / dci1v7.PREREGISTRATION
    path.write_text(path.read_text() + text)


def _amend(ctx, repo, **overrides):
    kwargs = {"amendment_id": "A-test", "reason": "a test amendment",
              "direction": "neutral", "sections": ["§18"],
              "declaration": "adopted in a test, after nothing",
              "model_keys": [MODEL], "producing_commit": COMMIT,
              "repo_root": repo, "decided_by": "test", "decided_on": "test"}
    kwargs.update(overrides)
    return registration_run.amend_registration(ctx, **kwargs)


def test_an_amendment_binds_the_new_hashes_and_the_chain_head_moves(study):
    ctx, tree, repo = study
    registered = manifest.load_manifest(ctx)
    before = manifest.document_binding(ctx, registered)
    assert before["amendments"] == []
    _touch_prereg(repo, "\n<!-- amendment A-test -->\n")
    record = _amend(ctx, repo)
    assert record["sequence"] == 1
    assert record["before"]["protocol_hash"] == registered["protocol_hash"]
    assert record["after"]["protocol_hash"] != registered["protocol_hash"]
    assert record["replications_at_adoption"][MODEL]["stage_reached"] == \
        C.STAGE_REGISTERED
    head = manifest.document_binding(ctx, registered)
    assert head["protocol_hash"] == record["after"]["protocol_hash"]
    assert [a["amendment_id"] for a in head["amendments"]] == ["A-test"]
    assert head["registered"]["protocol_hash"] == registered["protocol_hash"]
    # signed, mirrored, logged
    path = (Path(ctx.registration_root) / manifest.AMENDMENTS_DIRNAME
            / "001_A-test.json")
    assert path.exists()
    assert "signature" in json.loads(path.read_text())
    rows = [json.loads(line) for line in tree.transition_log.read_text()
            .splitlines() if line.strip()]
    assert rows[-1]["outcome"] == "AMENDED"
    assert rows[-1]["detail"]["amendment_id"] == "A-test"


def test_the_prefreeze_hash_check_reads_the_chain_head(study):
    from dci1v7.run.prefreeze_run import artifact_checks

    ctx, tree, repo = study
    _touch_prereg(repo, "\n<!-- amendment A-test -->\n")
    # Before the amendment is bound, the on-disk document disagrees with the
    # registration and the check fails --- v6's gemma-3n-e2b-it.
    checks = {c["check"]: c for c in artifact_checks(tree, repo_root=repo)}
    assert checks["protocol_hashes_agree"]["verdict"] == "FAIL"
    _amend(ctx, repo)
    checks = {c["check"]: c for c in artifact_checks(tree, repo_root=repo)}
    assert checks["protocol_hashes_agree"]["verdict"] == "PASS"
    detail = checks["protocol_hashes_agree"]["detail"]
    assert [a["amendment_id"] for a in detail["amendments"]] == ["A-test"]
    assert detail["registered"]["protocol_hash"] != detail["in_force"][
        "protocol_hash"]


def test_an_amendment_with_nothing_to_bind_is_refused(study):
    ctx, _tree, repo = study
    with pytest.raises(IntegrityError, match="already bound"):
        _amend(ctx, repo)


def test_section_13_is_refused_once_gate_2_5_exists(study):
    ctx, tree, repo = study
    record = tree.stage_record(C.STAGE_GATE2_5)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("{}")
    _touch_prereg(repo, "\n<!-- amendment touching §13 -->\n")
    with pytest.raises(IntegrityError, match="§32.3"):
        _amend(ctx, repo, sections=["§13.14"])
    # A section outside §13 is bindable at the same point.
    _amend(ctx, repo, sections=["§28"])


def test_the_chain_is_append_only_and_contiguous(study):
    ctx, _tree, repo = study
    _touch_prereg(repo, "\n<!-- one -->\n")
    first = _amend(ctx, repo, amendment_id="A-one")
    _touch_prereg(repo, "\n<!-- two -->\n")
    second = _amend(ctx, repo, amendment_id="A-two")
    assert (first["sequence"], second["sequence"]) == (1, 2)
    assert second["before"] == first["after"]
    head = manifest.document_binding(ctx, manifest.load_manifest(ctx))
    assert [a["sequence"] for a in head["amendments"]] == [1, 2]
    # A link removed from the middle breaks the chain rather than the read.
    (Path(ctx.registration_root) / manifest.AMENDMENTS_DIRNAME
     / "001_A-one.json").unlink()
    with pytest.raises(IntegrityError, match="not contiguous"):
        manifest.document_binding(ctx, manifest.load_manifest(ctx))


def test_every_field_of_the_declaration_is_required(study):
    ctx, _tree, repo = study
    _touch_prereg(repo, "\n<!-- x -->\n")
    with pytest.raises(IntegrityError, match="declares one of"):
        _amend(ctx, repo, direction="sideways")
    with pytest.raises(IntegrityError, match="names the sections"):
        _amend(ctx, repo, sections=["13.14"])
    with pytest.raises(IntegrityError, match="none may be blank"):
        _amend(ctx, repo, declaration="")


def test_the_freeze_binds_the_chain_and_the_manifest_binds_its_start():
    """Shape only: the manifest carries an `amendments` binding at signing
    and the freeze record requires `amendments` and the registered hash."""
    from dci1v7.stages import freeze

    assert "amendments" in manifest.REQUIRED_BINDINGS
    assert "amendments" in freeze.REQUIRED_FIELDS
    assert "registered_protocol_hash" in freeze.REQUIRED_FIELDS
    assert "amendments" in freeze.EMPTIABLE_FIELDS
