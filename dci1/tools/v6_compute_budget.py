#!/usr/bin/env python3
"""§34 D1: the generation budget of each registered compute option.

Every number is derived from `dci1v6`'s own constants and the arm-derived cell
set --- not from a spreadsheet and not from a hand estimate. A budget quoted
from a document that has drifted from the code is a budget for a study nobody
is running.

**The order matters and it is the researcher's.** Arms come first, because
they decide which estimands exist; claims second, because they decide which
arms are essential; models third; and the budget is what falls out. This tool
computes the last step only.

The derivation itself lives in ``dci1v6.design.budget``, because the
registration manifest binds the adopted option and a manifest cannot import a
tool. This file is the regenerable report over it.

    python3 tools/v6_compute_budget.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v6.design.budget import (                    # noqa: E402
    all_options, calibration_burden, expansion_burden, library, probe_burden)
from dci1v6.design.cells import n_cells_for           # noqa: E402
from dci1v6.protocol import constants as C            # noqa: E402

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v6" / "development" / "d1_compute_budget.json"


def build() -> dict[str, object]:
    options = all_options()
    marginal = {}
    full = tuple(C.ARMS)
    for arm in C.OPTIONAL_ARMS:
        rest = tuple(a for a in full if a != arm)
        try:
            cells = n_cells_for(rest)
            marginal[arm] = {"cells_without": cells,
                             "cells_saved": n_cells_for(full) - cells}
        except Exception as exc:                     # noqa: BLE001
            marginal[arm] = {"cells_without": None, "refused": str(exc)}
    return {
        "_what": "§34 D1's registered options, costed from the code's own "
                 "constants and the arm-derived cell set",
        "_v6_note": (
            "Confirmatory cost is n_cells x N_BLOCKS x M_DRAWS and nothing "
            "else. The v6 proposal's '~110,000 confirmatory' was v5's "
            "CALIBRATION burden (110,736) quoted in the wrong row; on D1's "
            "registered 56-cell option the confirmatory figure is "
            "56 x 384 x 8 = 172,032 per replication. Every number here is "
            "computed, none is transcribed."),
        "_v6_conditional_terms": {
            "why": "two v6 terms are conditional and are named rather than "
                   "folded into a figure a replication is expected to spend: "
                   "§12.6's expansion stops the moment C1-C6 pass, and the "
                   "Gate-2.75 probe stops the moment m* passes its margin",
            "expansion_ceiling": expansion_burden(),
            "composed_probe": {
                "if_m_star_passes": probe_burden(),
                "worst_case": probe_burden(
                    n_severities=probe_burden()["max_severities"])}},
        "_decision": "§34 D1",
        "_units": "generations = prompt x draw; one generation is one "
                  "model response",
        "library": library(),
        "calibration": calibration_burden(C.N_CELLS_FULL),
        "cells_by_arm": dict(C.N_CELLS_BY_ARM),
        "cells_full": C.N_CELLS_FULL,
        "removing_one_arm": marginal,
        "options": options,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; rerun without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    built = json.loads(text)
    print(f"wrote {OUT}")
    for name, opt in built["options"].items():
        print(f"  {name:24s} {opt['cells_per_block']:3d} cells x "
              f"{opt['models']} models -> {opt['total_generations']:,} "
              f"generations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
