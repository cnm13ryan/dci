"""§12.1's restricted view of the cap-selection probe.

**The hazard.** §12.1 selects the completion cap from the truncation rate over
the one- and two-constraint prompts, so the probe *must* generate composed
`A + B` prompts --- "the one- and two-constraint prompts use the most
restrictive registered severity of each grid, because a cap has to be adequate
where the answer is hardest to write". Twenty-four topics x three caps x one
draw = 72 composed generations per replication, at `A:8 + B:7`.

Those generations go through the same scorer as every other row, so the stored
`scored.jsonl` carries a `scores` list with `passed` for **both** constituents.
Nothing in the registered procedure reads it, and no record contains it --- but
`D(B <- A)` at those severities is *derivable* from stored evidence by anyone
who aggregates the field. §12.5 and §13.9 forbid a composed outcome from
reaching candidate construction or reference selection, and an unread field is
a weaker guarantee than an unreachable one.

**The seal.** `restrict` projects the probe down to the three fields §12.1
actually registers --- cell id, load, truncated --- and drops everything else
including `scores`. `select_cap` and every later stage consume the restricted
artifact. `assert_restricted` refuses a mapping that still carries an outcome
field, so a future caller cannot re-widen the view by accident, and
`assert_no_probe_outcome_reachable` checks the reverse direction: that the
selection modules do not import the raw row reader at all.

The raw rows stay exactly where they are. Provenance requires them; §12.1's
answer does not.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C

__all__ = ["REGISTERED_CAP_FIELDS", "FORBIDDEN_CAP_FIELDS", "restrict",
           "truncation_by_load", "assert_restricted", "cap_probe_artifact"]

#: The only fields §12.1 registers as inputs to the cap decision.
REGISTERED_CAP_FIELDS = ("cell_id", "load", "truncated")

#: Fields that carry, or can reconstruct, a composed compliance outcome.
FORBIDDEN_CAP_FIELDS = ("scores", "passed", "graded", "non_vacuous",
                        "vacuous_pass", "outcome", "compliance",
                        "raw_response", "final_answer", "raw_generation")


def restrict(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Project cap-probe rows onto §12.1's registered fields, dropping the rest.

    This is the only supported way for a cap row to leave the probe.
    """
    out: list[dict[str, Any]] = []
    for row in rows:
        missing = [f for f in REGISTERED_CAP_FIELDS if f not in row]
        if missing:
            raise ProtocolError(
                f"a cap-probe row is missing {missing}; §12.1 cannot decide "
                f"the cap from it")
        out.append({"cell_id": row["cell_id"], "load": int(row["load"]),
                    "truncated": bool(row["truncated"])})
    return out


def assert_restricted(rows: Sequence[Mapping[str, Any]]) -> None:
    """Refuse a cap view that still carries an outcome-bearing field."""
    leaked = sorted({f for row in rows for f in FORBIDDEN_CAP_FIELDS
                     if f in row})
    if leaked:
        raise ProtocolError(
            f"the §12.1 cap view carries {leaked}, from which a composed "
            f"compliance outcome is derivable. §12.5 and §13.9 forbid a "
            f"composed outcome reaching cap selection, candidate "
            f"construction or reference selection; use "
            f"`cap_probe.restrict` and pass the restricted rows")


def truncation_by_load(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """§12.1's two rates: load 0, and loads 1 and 2 together."""
    assert_restricted(rows)
    loads: dict[int, list[float]] = {0: [], 1: [], 2: []}
    for row in rows:
        load = int(row["load"])
        if load not in loads:
            raise ProtocolError(
                f"§12.1's probe has loads 0, 1 and 2; got {load}")
        loads[load].append(float(row["truncated"]))
    constrained = loads[1] + loads[2]
    return {
        "unconstrained": sum(loads[0]) / max(len(loads[0]), 1),
        "constrained": sum(constrained) / max(len(constrained), 1),
        "n": len(rows),
        "n_by_load": {str(k): len(v) for k, v in loads.items()},
    }


def cap_probe_artifact(truncation_by_cap: Mapping[int, Mapping[str, Any]], *,
                       model_key: str, selected_cap: int | None
                       ) -> dict[str, Any]:
    """The durable restricted artifact later stages read instead of raw rows."""
    return {
        "artifact_type": "cap_probe_truncation",
        "stage": C.STAGE_REGIME,
        "section": "12.1",
        "model_key": model_key,
        "selected_cap": selected_cap,
        "criterion": ("truncation over load 1 and 2 prompts "
                      f"<= {C.CAP_TRUNCATION_MAX}"),
        "table": {str(cap): dict(entry)
                  for cap, entry in sorted(truncation_by_cap.items())},
        "registered_fields": list(REGISTERED_CAP_FIELDS),
        "withheld": (
            "The probe's composed A+B generations are scored by the same "
            "verifier as every other row and their per-constituent verdicts "
            "remain in the raw evidence for provenance. They are NOT "
            "aggregated here and no registered stage reads them: §12.5 and "
            "§13.9 forbid a composed outcome reaching candidate construction "
            "or reference selection, and D(B<-A) at A:8+B:7 would be exactly "
            "that."),
    }
