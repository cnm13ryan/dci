"""Shared helpers for the Batch 1 suite. Everything here is CPU-only."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def historical_source(relative: str) -> str:
    path = REPO / relative
    if not path.exists():
        pytest.skip(f"{relative} is not in this checkout")
    return path.read_text()


def function_source(module_text: str, name: str) -> str:
    tree = ast.parse(module_text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(module_text, node)
    raise AssertionError(f"{name} not found")


def string_constants(module_text: str, names: tuple[str, ...]) -> dict[str, str]:
    """Evaluate top-level string assignments (concatenations of literals and
    earlier names) without importing the module."""
    tree = ast.parse(module_text)
    env: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name):
            try:
                value = eval(compile(ast.Expression(node.value), "<ast>", "eval"),
                             {"__builtins__": {}}, dict(env))
            except Exception:
                continue
            if isinstance(value, str):
                env[node.targets[0].id] = value
    return {n: env[n] for n in names}


@pytest.fixture(autouse=True)
def library_version():
    """The library version is process-wide (``library.set_library_version``);
    every test starts on v1 unless its module overrides this fixture."""
    from dci.batch1 import library as L
    L.set_library_version("v1")
    yield "v1"
    L.set_library_version("v1")
