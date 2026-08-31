"""The declared z3 dependency and the frozen solver identity cannot drift apart.

`stage2_frozen.json` records the solver that produced the Stage-2 evidence,
and `dci.v19.solver.solver_identity` re-reads the installed build at import,
so a checkout whose solver differs fails closed -- correctly, because §8.6
needs "the solver that produced the evidence, not a remembered one".

That guard worked. What did not was the dependency declaration: `pyproject.toml`
asked for `z3-solver>=4.13` with no upper bound, so a resolver was free to
install a newer z3 than the record names, and CI was consequently red on every
branch *and on `main`* for a reason no PR introduced. The two facts live in
different files, so this test is what keeps them one fact.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _frozen_solver() -> dict:
    data = json.loads((REPO / "src" / "dci" / "v19" / "stage2_frozen.json").read_text())
    for entry in data["records"]:
        if entry.get("slot") == "satisfiability.solver_identity":
            return entry["value"]
    raise AssertionError("no satisfiability.solver_identity in stage2_frozen.json")


def _declared_pin() -> str:
    text = (REPO / "pyproject.toml").read_text()
    match = re.search(r'"z3-solver([^"]*)"', text)
    assert match, "pyproject.toml no longer declares z3-solver"
    return match.group(1).strip()


def test_the_declared_pin_names_the_frozen_solver_version():
    frozen = _frozen_solver()
    assert frozen["name"] == "z3", frozen
    pin = _declared_pin()
    assert pin.startswith("=="), (
        f"z3-solver is declared {pin!r}: an open bound lets a resolver install "
        "a solver the frozen record does not name, which fails closed at import "
        "and turns every check run red for an environment reason")
    # the dist version is the solver version plus a packaging component
    assert pin[2:].startswith(frozen["version"] + "."), (
        f"declared z3-solver{pin} does not match the frozen "
        f"solver_identity {frozen['version']!r}")


def test_the_installed_solver_is_the_frozen_one():
    """The check the domain already performs, stated where a reader looks."""
    from dci.v19.solver import solver_identity

    name, version = solver_identity()
    frozen = _frozen_solver()
    assert (name, version) == (frozen["name"], frozen["version"]), (
        f"installed {name} {version} is not the frozen {frozen['name']} "
        f"{frozen['version']}; §8.6 needs the solver that produced the evidence")
