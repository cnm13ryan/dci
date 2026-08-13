"""The structural guard: `LLM(...)` may exist in exactly ONE place.

This repository previously carried eight independent `LLM(...)` constructions —
five under `vllm_backend/`, three under `crossmodel/` — each re-typing dtype,
tensor-parallel size, memory utilisation, eager mode and the seed. They drifted:
`max_model_len` was 8192, 16384, 40960 and `MAX_TOKENS + 2048` depending on
which file you read, and only one of the eight parsed reasoning with the
checkpoint's own delimiters.

Consolidation is not durable unless it is enforced, because the cheapest way to
add a ninth experiment is always to copy the eighth script. This test is what
makes that copy fail in CI instead of in the data.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parents[1]

#: The one module allowed to construct an engine.
CANONICAL = EXPLORATORY / "vllm_backend" / "engine.py"

#: A real construction: `LLM(` not preceded by an identifier character or a dot
#: (so `LLMEngine(`, `self.LLM(` and `MyLLM(` do not count).
CONSTRUCTION = re.compile(r"(?<![A-Za-z0-9_.])LLM\s*\(")

#: Directories that are not source: virtualenvs, run outputs, archived
#: provenance snapshots of code as it was when a run executed.
EXCLUDED_PARTS = {".venv", ".venv-vllm", ".venv-kimi", "runs", ".provenance",
                  "__pycache__", "build", "node_modules"}


def _source_files() -> list[Path]:
    files = []
    for path in EXPLORATORY.rglob("*.py"):
        if EXCLUDED_PARTS & set(path.parts):
            continue
        files.append(path)
    return files


def _strip_noncode(text: str) -> str:
    """Blank out comments and triple-quoted strings.

    Documentation legitimately says `LLM(...)`; only executable code counts.
    """
    text = re.sub(r'"""(?:.|\n)*?"""', '""', text)
    text = re.sub(r"'''(?:.|\n)*?'''", "''", text)
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def test_canonical_module_exists_and_constructs_the_engine() -> None:
    assert CANONICAL.is_file(), f"{CANONICAL} is the canonical engine module"
    code = _strip_noncode(CANONICAL.read_text())
    assert CONSTRUCTION.search(code), (
        "the canonical engine module no longer constructs an LLM; if the "
        "engine moved, move this guard with it")


def test_no_other_module_constructs_an_llm() -> None:
    offenders = []
    for path in _source_files():
        if path == CANONICAL:
            continue
        code = _strip_noncode(path.read_text(errors="replace"))
        for number, line in enumerate(code.splitlines(), start=1):
            if CONSTRUCTION.search(line):
                offenders.append(f"{path.relative_to(EXPLORATORY)}:{number}: {line.strip()}")
    assert not offenders, (
        "vLLM engines must be constructed only through "
        "`vllm_backend.engine.build_engine`, so that dtype, tensor-parallel "
        "size, memory utilisation, eager mode and the seed cannot drift "
        "between call sites. Offending lines:\n  " + "\n  ".join(offenders))


def test_sampling_params_are_built_in_one_place() -> None:
    """`SamplingParams(...)` is the other thing that drifted; same rule."""
    allowed = {CANONICAL}
    pattern = re.compile(r"(?<![A-Za-z0-9_.])SamplingParams\s*\(")
    offenders = []
    for path in _source_files():
        if path in allowed:
            continue
        code = _strip_noncode(path.read_text(errors="replace"))
        for number, line in enumerate(code.splitlines(), start=1):
            if pattern.search(line):
                offenders.append(
                    f"{path.relative_to(EXPLORATORY)}:{number}: {line.strip()}")
    assert not offenders, (
        "decoding parameters must come from `vllm_backend.engine.build_sampling` "
        "so temperature/top_p/top_k cannot differ between experiments. "
        "Offending lines:\n  " + "\n  ".join(offenders))


@pytest.mark.parametrize("module", [
    "contract", "plan", "registry", "records", "resolve", "io", "hardware",
])
def test_pure_modules_import_without_a_gpu_stack(module: str) -> None:
    """The plan builders run in the scientific venv, which has no vLLM.

    If any of these grows a module-level `import vllm` or `import torch`, plan
    building breaks on a machine that cannot hold the vLLM wheel — which is
    every machine in CI and the scientific environment itself.
    """
    import importlib
    import sys

    sys.path.insert(0, str(EXPLORATORY))
    before = set(sys.modules)
    importlib.import_module(f"vllm_backend.{module}")
    pulled = {m.split(".")[0] for m in set(sys.modules) - before}
    assert "vllm" not in pulled, f"vllm_backend.{module} imported vllm at module level"
    assert "torch" not in pulled, f"vllm_backend.{module} imported torch at module level"
