"""The documented migrator command must leave the authoritative package alone.

`python tools/migrate_v15.py` wrote its reconstruction straight into
src/dci/pipeline/stages/, src/dci/pipeline/_prelude.py and the extracted library
modules. Its source is the ARCHIVED v15 notebook, so running the documented
command replaced repaired code with pre-repair code: measured here, 13 of 34
reconstructed stage files differ from the live package. The result still imports
and still passes a syntax check, which is precisely why it is dangerous - a
mixed v15/current tree with no marker saying so.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]

MIGRATOR = Path("tools/migrate_v15.py")
AUTHORITATIVE = Path("src/dci")


def _tree_hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def _run(*args, expect_ok=True):
    done = subprocess.run([sys.executable, str(MIGRATOR), *args],
                          capture_output=True, text=True, timeout=600)
    if expect_ok:
        assert done.returncode == 0, done.stdout + done.stderr
    return done


def test_the_documented_command_leaves_src_byte_identical(tmp_path):
    before = _tree_hashes(AUTHORITATIVE)
    assert before, "the authoritative package must exist for this test to mean anything"
    _run("--out", str(tmp_path / "reconstruction"))
    assert _tree_hashes(AUTHORITATIVE) == before


def test_the_bare_documented_command_also_leaves_src_alone():
    """No arguments at all: exactly what the README tells a reader to run."""
    before = _tree_hashes(AUTHORITATIVE)
    _run()
    assert _tree_hashes(AUTHORITATIVE) == before


def test_the_reconstruction_is_actually_produced(tmp_path):
    out = tmp_path / "reconstruction"
    _run("--out", str(out))
    stages = out / "src" / "dci" / "pipeline" / "stages"
    assert len(list(stages.glob("c*.py"))) == 33
    assert (stages / "__init__.py").read_text().startswith('"""Generated stage')
    assert (out / "docs" / "migration_map.csv").exists()
    assert (out / "docs" / "migration_ledger_patches.csv").exists()
    assert (out / "src" / "dci" / "pipeline" / "_prelude.py").exists()


def test_the_reconstruction_really_would_have_overwritten_repaired_code(tmp_path):
    """The defect's severity: the two trees are not the same code."""
    out = tmp_path / "reconstruction"
    _run("--out", str(out))
    reconstructed = out / "src" / "dci" / "pipeline" / "stages"
    live = AUTHORITATIVE / "pipeline" / "stages"
    differing = [p.name for p in sorted(reconstructed.glob("c*.py"))
                 if (live / p.name).read_bytes() != p.read_bytes()]
    assert differing, ("if these matched, the migrator would be harmless and "
                       "this whole guard would be unnecessary")


def test_an_out_path_inside_the_package_is_refused(tmp_path):
    done = _run("--out", "src/dci/pipeline", expect_ok=False)
    assert done.returncode != 0
    assert "points inside the authoritative package" in done.stdout + done.stderr


def test_the_destructive_target_needs_exact_consent():
    done = _run("--overwrite-authoritative", "yes", expect_ok=False)
    assert done.returncode != 0
    assert "requires the exact consent value" in done.stdout + done.stderr


def test_the_destructive_target_is_not_the_default():
    text = MIGRATOR.read_text()
    assert "DEFAULT_OUT" in text
    assert "build" in text
    # The consent string must be spelled out, not inferable from a bare flag.
    assert "yes-overwrite-the-repaired-package" in text
