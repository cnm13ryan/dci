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
