"""Artifact collection may authorise termination only after verifying something.

Three defects, exercised against the real export layout that c402 writes -
RUN_ROOT/exports/<label>/sha256_manifest.json with entries relative to RUN_ROOT:

  1. entries were resolved against the manifest's own directory, two levels too
     deep, so every entry read as MISSING;
  2. zero manifests or zero entries produced exit 0 and the message that
     termination was safe;
  3. the remote data root defaulted to ~/dci/artifacts while the runbook uses a
     persistent filesystem root, so the documented commands collected the wrong
     tree and verified nothing.

The verifier is embedded in a bash heredoc, so these tests extract and run that
exact Python rather than a paraphrase of it.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

SCRIPT = Path("scripts/lambda_collect.sh")


@pytest.fixture(scope="module")
def verifier(tmp_path_factory):
    """The exact heredoc body the shipped script runs."""
    text = SCRIPT.read_text()
    body = re.search(r"python3 - \"\$DEST/artifacts\" <<'PY'\n(.*?)\nPY\n",
                     text, re.S)
    assert body, "the verifier heredoc moved; this test must follow it"
    path = tmp_path_factory.mktemp("verifier") / "verify.py"
    path.write_text(body.group(1))
    return path


def _run(verifier: Path, root: Path):
    return subprocess.run([sys.executable, str(verifier), str(root)],
                          capture_output=True, text=True, timeout=120)


def _export_tree(root: Path, label: str = "confirmatory",
                 files=(("gates/gate_0_implementation.json", '{"status": "PASS"}'),
                        ("config/config.json", '{"protocol_version": "v15.1"}'),
                        ("scores/tau.csv", "a,b\n1,2\n"))):
    """RUN_ROOT/... exactly as c402_export writes it."""
    run_root = root / "artifacts" / "v15.1" / "study" / "run-20260810T000000Z-ab"
    manifest = {}
    for rel, text in files:
        target = run_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        manifest[rel] = hashlib.sha256(text.encode()).hexdigest()
    export_dir = run_root / "exports" / label
    export_dir.mkdir(parents=True, exist_ok=True)
    (export_dir / "sha256_manifest.json").write_text(json.dumps(manifest, indent=2))
    return run_root, export_dir / "sha256_manifest.json"


# ------------------------------------------------------- anchoring the entries
def test_the_real_export_tree_verifies(verifier, tmp_path):
    run_root, _ = _export_tree(tmp_path)
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 0, done.stdout
    assert "entries verified: 3" in done.stdout
    assert str(run_root) in done.stdout          # anchored at RUN_ROOT
    assert "OK:" in done.stdout


def test_entries_are_not_resolved_against_the_manifest_directory(verifier,
                                                                tmp_path):
    """The old base was exports/<label>/, where none of the entries live."""
    _export_tree(tmp_path)
    done = _run(verifier, tmp_path / "artifacts")
    assert "MISSING" not in done.stdout, done.stdout


def test_a_zip_extracted_layout_also_anchors(verifier, tmp_path):
    """In the archive the manifest sits beside its entries; both must work."""
    flat = tmp_path / "artifacts" / "unzipped"
    flat.mkdir(parents=True)
    payload = "a,b\n1,2\n"
    (flat / "scores").mkdir()
    (flat / "scores" / "tau.csv").write_text(payload)
    (flat / "sha256_manifest.json").write_text(json.dumps(
        {"scores/tau.csv": hashlib.sha256(payload.encode()).hexdigest()}))
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 0, done.stdout
    assert "entries verified: 1" in done.stdout


# ------------------------------------------------------------- failing closed
def test_no_manifest_anywhere_fails(verifier, tmp_path):
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "stray.txt").write_text("nothing verifiable")
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1
    assert "no sha256_manifest.json" in done.stdout
    assert "OK:" not in done.stdout


def test_an_empty_collection_fails(verifier, tmp_path):
    (tmp_path / "artifacts").mkdir()
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1


def test_an_empty_manifest_fails(verifier, tmp_path):
    export = tmp_path / "artifacts" / "run" / "exports" / "confirmatory"
    export.mkdir(parents=True)
    (export / "sha256_manifest.json").write_text("{}")
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1
    assert "EMPTY MANIFEST" in done.stdout


def test_an_unreadable_manifest_fails(verifier, tmp_path):
    export = tmp_path / "artifacts" / "run" / "exports" / "confirmatory"
    export.mkdir(parents=True)
    (export / "sha256_manifest.json").write_text("{not json")
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1
    assert "UNREADABLE MANIFEST" in done.stdout


def test_a_manifest_whose_entries_are_all_absent_fails(verifier, tmp_path):
    """The case that used to verify zero files and exit 0."""
    export = tmp_path / "artifacts" / "run" / "exports" / "confirmatory"
    export.mkdir(parents=True)
    (export / "sha256_manifest.json").write_text(json.dumps({"gates/x.json": "0" * 64}))
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1
    assert "UNANCHORED MANIFEST" in done.stdout


def test_a_missing_declared_file_fails(verifier, tmp_path):
    run_root, _ = _export_tree(tmp_path)
    (run_root / "scores" / "tau.csv").unlink()
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1


def test_a_wrong_hash_fails(verifier, tmp_path):
    run_root, _ = _export_tree(tmp_path)
    (run_root / "config" / "config.json").write_text('{"protocol_version": "v19"}')
    done = _run(verifier, tmp_path / "artifacts")
    assert done.returncode == 1
    assert "HASH MISMATCH" in done.stdout


# ----------------------------------------------------------- the remote root
def test_the_script_requires_an_explicit_remote_root():
    """Executable lines only: the comments explain the old default on purpose."""
    text = SCRIPT.read_text()
    code = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("#"))
    assert 'REMOTE=""' in code, "there must be no plausible-but-wrong default"
    assert "~/dci/artifacts" not in code
    assert "--remote is required" in text


def test_running_without_remote_exits_two():
    done = subprocess.run(["bash", str(SCRIPT), "--host", "h", "--key", "k"],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 2
    assert "--remote is required" in done.stdout


def test_the_bootstrap_persists_provenance_outside_the_root_disk():
    text = Path("scripts/lambda_bootstrap.sh").read_text()
    assert "--data-root" in text
    assert "$DATA_ROOT/provenance" in text
    assert 'open("environment_identity.json", "w")' not in text
