"""Stage sequencing and the software/science failure split.

Importing a stage module runs it, exactly as executing the notebook cell did.
The runner owns: fresh state per run, stage order, exit-code taxonomy, and the
machine-readable stop record. The taxonomy exists so a cloud orchestrator can
tell `the process failed` from `the study stopped correctly at a gate`:

  EXIT_OK            0   pipeline completed to export
  EXIT_SCIENTIFIC   10   StudyStop: a gate returned a non-PASS status. This is
                         a meaningful experimental outcome; artifacts stand.
  EXIT_INVARIANT    20   an implementation invariant failed (Gate 0 assertion,
                         lineage violation, frozen-plan mismatch, task bank)
  EXIT_ENVIRONMENT  30   missing GPU stack, hardware-class refusal at startup,
                         storage unavailable
  EXIT_CRASH         1   anything unexpected
"""
from __future__ import annotations

import importlib
import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Optional

EXIT_OK, EXIT_CRASH = 0, 1
EXIT_SCIENTIFIC, EXIT_INVARIANT, EXIT_ENVIRONMENT = 10, 20, 30

STAGE_PACKAGE = "dci.pipeline.stages"


def stage_order() -> list[str]:
    mod = importlib.import_module(STAGE_PACKAGE)
    return list(mod.ORDER)


def _purge() -> None:
    """Fresh run state and fresh stage modules, like restarting the kernel."""
    from dci.pipeline import state
    state.reset()
    for name in list(sys.modules):
        if name.startswith(STAGE_PACKAGE + "."):
            del sys.modules[name]


def run_pipeline(until: Optional[str] = None) -> int:
    import matplotlib
    matplotlib.use("Agg")
    from dci.exceptions import (CacheIntegrityError, FrozenPlanMismatch,
                                LineageViolation, StudyStop,
                                TaskBankInsufficient)
    from dci.pipeline import state as S

    _purge()
    order = stage_order()
    ran: list[str] = []
    try:
        for name in order:
            print(f"\n{'=' * 72}\n[stage {name}]\n{'=' * 72}", flush=True)
            importlib.import_module(f"{STAGE_PACKAGE}.{name}")
            ran.append(name)
            if until and name.startswith(until):
                print(f"\n[runner] stopped after {name} as requested (--until).")
                return EXIT_OK
            if getattr(S, "GENERATION_FOLLOWER_DONE", False):
                print("\n[runner] shard follower finished its generation work.")
                return EXIT_OK
        print("\nALL STAGES EXECUTED")
        return EXIT_OK
    except StudyStop as stop:
        outcome = stop.outcome
        print(f"\nSTUDY STOPPED at a scientific gate: {outcome.gate} -> "
              f"{outcome.status}\n{outcome.reason}")
        _write_stop(S, {"kind": "scientific_stop", "stage": _next(ran, order),
                        "outcome": asdict(outcome)})
        return EXIT_SCIENTIFIC
    except (AssertionError, LineageViolation, FrozenPlanMismatch,
            TaskBankInsufficient, CacheIntegrityError) as exc:
        traceback.print_exc()
        _write_stop(S, {"kind": "invariant_failure", "stage": _next(ran, order),
                        "error": f"{type(exc).__name__}: {exc}"})
        return EXIT_INVARIANT
    except EnvironmentError as exc:
        traceback.print_exc()
        _write_stop(S, {"kind": "environment_failure",
                        "stage": _next(ran, order), "error": str(exc)})
        return EXIT_ENVIRONMENT
    except Exception:
        traceback.print_exc()
        _write_stop(S, {"kind": "crash", "stage": _next(ran, order),
                        "error": traceback.format_exc(limit=3)})
        return EXIT_CRASH


def _next(ran: list[str], order: list[str]) -> str:
    return order[len(ran)] if len(ran) < len(order) else "complete"


def _write_stop(S, payload: dict) -> None:
    root = getattr(S, "RUN_ROOT", None)
    if root is None:
        return
    try:
        Path(root, "stop.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass
