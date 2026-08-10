"""The run's shared state: the explicit successor of the notebook kernel namespace.

Every name the notebook cells shared through their single global namespace is
an attribute of this module, written and read as `S.NAME` by the stage modules
in `pipeline/stages/`. Making the namespace a real module keeps notebook
semantics exactly (late binding, in-place mutation, rebinding visible to every
stage and to functions defined in earlier stages) while making every shared
name greppable and auditable: `grep -rn "S\\.NAME" src/dci` lists every reader
and writer.

This is operational state (class C of the configuration taxonomy). Nothing here
may redefine the experiment: the scientific protocol lives in the frozen CFG
object and its hash, and the migration ledger records that state routing was a
mechanical transformation with no behavioral intent.
"""
from __future__ import annotations


def reset() -> None:
    """Drop every run attribute so a fresh pipeline run starts clean."""
    for k in list(globals()):
        if not k.startswith("__") and k not in ("reset",):
            del globals()[k]
