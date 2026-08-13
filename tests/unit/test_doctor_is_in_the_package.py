"""`dci doctor` must work from the installed package, not from a repo path.

The command shelled out to scripts/local_doctor.py, which is not part of the
distribution. Any checkout with the package and no repository working tree - a
wheel install, or any snapshot of this stack before the scripts land - printed a
Python file-not-found and returned a nonzero code that looked like an
unsupported environment.
"""
import pytest

from dci import diagnostics

pytestmark = pytest.mark.cpu


def test_the_doctor_is_importable_from_the_package():
    assert callable(diagnostics.run)
    assert callable(diagnostics.main)


def test_the_cpu_tier_reports_supported_here(capsys):
    assert diagnostics.run(gpu=False) == 0
    assert "environment supported" in capsys.readouterr().out


def test_requiring_an_accelerator_that_is_absent_is_unsupported(capsys):
    """30 is the documented exit code for "unsupported for the requested tier"."""
    assert diagnostics.run(gpu=True) == 30
    assert "UNSUPPORTED" in capsys.readouterr().out


# ------------------------------------------- the dependency check itself
#
# The doctor reported a healthy scientific core while `z3-solver` was absent,
# because the list it checked was hand-maintained and had drifted from the
# declaration. Nine v19 tests then failed at collection. These tests pin the
# property that repair depends on: the checked set IS the declared set.

def _declared_in_pyproject():
    import tomllib
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    table = tomllib.loads((root / "pyproject.toml").read_text())
    return table["project"]["dependencies"]


def test_the_checked_set_is_exactly_the_declared_set():
    """Not a subset, not a superset: any drift is the original defect."""
    import re
    declared = {re.split(r"[<>=!~\[ ]", r, maxsplit=1)[0].strip()
                for r in _declared_in_pyproject()}
    checked = {distribution for distribution, _ in
               diagnostics.declared_dependencies()}
    assert checked == declared


def test_the_solver_that_gates_stage_two_is_among_them():
    """Named explicitly, because this is the one that was missing."""
    checked = dict(diagnostics.declared_dependencies())
    assert checked.get("z3-solver") == "z3", (
        "z3-solver must be checked, and under its IMPORT name: "
        "`import z3-solver` is a SyntaxError, so a naive name would report the "
        "dependency missing on an environment that has it")


def test_an_uninstalled_checkout_still_checks_the_full_declaration(monkeypatch):
    """The path that used to fall back to a six-name literal omitting z3."""
    import importlib.metadata as md

    def absent(_name):
        raise md.PackageNotFoundError("dci")

    monkeypatch.setattr(md, "requires", absent)
    checked = dict(diagnostics.declared_dependencies())
    assert checked.get("z3-solver") == "z3"
    assert "numpy" in checked and len(checked) == len(_declared_in_pyproject())


def test_a_checkout_with_no_declaration_at_all_is_unsupported(monkeypatch, capsys):
    """Checking nothing must never read as a healthy environment."""
    monkeypatch.setattr(diagnostics, "declared_dependencies", lambda: [])
    assert diagnostics.run(gpu=False) == 30
    assert "NOT FOUND" in capsys.readouterr().out


def test_a_missing_declared_dependency_is_reported_as_unsupported(monkeypatch,
                                                                 capsys):
    monkeypatch.setattr(diagnostics, "declared_dependencies",
                        lambda: [("no-such-distribution", "no_such_module")])
    assert diagnostics.run(gpu=False) == 30
    out = capsys.readouterr().out
    assert "no-such-distribution" in out and "MISSING" in out


def test_the_doctor_holds_no_hardcoded_dependency_list():
    """Parsed, not grepped: a literal list is how the defect returns."""
    import ast
    from pathlib import Path
    source = Path(diagnostics.__file__).read_text()
    tree = ast.parse(source)
    declaring = {"numpy", "pandas", "scipy", "matplotlib", "tqdm", "psutil",
                 "z3-solver", "z3"}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            continue
        names = {e.value for e in node.elts
                 if isinstance(e, ast.Constant) and isinstance(e.value, str)}
        assert len(names & declaring) < 3, (
            f"a literal dependency list is back in the doctor: {sorted(names)}")


def test_the_cli_does_not_shell_out_to_a_repository_path():
    """Parsed, not grepped: the explanation of the old behaviour is a docstring."""
    import ast
    from pathlib import Path
    tree = ast.parse(Path("src/dci/cli.py").read_text())
    doctor = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "cmd_doctor")
    body = [node for node in doctor.body
            if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
    code = "\n".join(ast.unparse(node) for node in body)
    assert "scripts" not in code
    assert "subprocess" not in code
    assert "diagnostics" in code


def test_the_cli_command_runs_in_process(monkeypatch):
    seen = {}
    monkeypatch.setattr(diagnostics, "run",
                        lambda gpu, expect_devices: seen.update(
                            gpu=gpu, expect_devices=expect_devices) or 0)
    from dci.cli import main
    assert main(["doctor"]) == 0
    assert seen == {"gpu": False, "expect_devices": None}
    assert main(["doctor", "--gpu", "--expect-devices", "2"]) == 0
    assert seen == {"gpu": True, "expect_devices": 2}
