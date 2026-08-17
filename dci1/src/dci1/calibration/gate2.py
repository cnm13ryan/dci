"""Gate 2 — regime calibration (prereg §18), per model, behavioural.

All quantities are measured on the 96 calibration topics, one response per
constraint per topic, each constraint presented alone (stream "calibration",
single generation per prompt, decision D09). The calibration run produces solo
failure rates only: no composed condition, no focal-to-reference contrast, and
no estimate of any §14 family quantity.

Selection rules, verbatim from §18:
* n ∈ {1,2,3} with solo failure rate closest to 0.30; gate band [0.15, 0.50];
* m ∈ {7,8,9,10} with solo failure rate closest to 0.30; band [0.15, 0.55];
* a candidate is admitted when its solo failure rate is within 0.10 of the
  focal constraint's, its instruction text is within 20% of the focal
  constraint's length in words (D20: wording 0, whitespace tokens), and it
  applies to the whole answer; admitted candidates are ranked by absolute
  rate difference and the three closest taken (ties by candidate order, D20);
* every composition to be used is certified jointly satisfiable and free of
  entailment in both directions (witness certificates).
"""
from __future__ import annotations

from typing import Any

from dci1.constraints.definitions import CANDIDATE_IDS, added_verifier
from dci1.constraints.witnesses import certify_composition
from dci1.constraints.wordings import wording
from dci1.protocol.constants import (
    ADMISSION_LENGTH_TOLERANCE,
    ADMISSION_RATE_WINDOW,
    FOCAL_SOLO_BAND,
    M_GRID,
    N_GRID,
    N_REFERENCES,
    SOLO_RATE_TARGET,
    TARGET_SOLO_BAND,
    ProtocolError,
)
from dci1.verifiers.target import s0_count


def solo_failure(response: str, constraint_id: str, *, n: int | None = None,
                 m: int | None = None) -> int:
    """F = 1 unless the solo constraint's verifier passes."""
    if constraint_id == "A":
        return 0 if s0_count(response) == n else 1
    verifier = added_verifier(constraint_id, m if constraint_id == "B" else None)
    return 0 if verifier(response) else 1


def parse_solo_arm(arm: str) -> dict[str, Any]:
    if not arm.startswith("solo:"):
        raise ProtocolError(f"not a calibration arm: {arm!r}")
    solo_id = arm[len("solo:"):]
    if solo_id.startswith("A:n="):
        return {"constraint_id": "A", "n": int(solo_id[4:]), "m": None}
    if solo_id.startswith("B:m="):
        return {"constraint_id": "B", "n": None, "m": int(solo_id[4:])}
    return {"constraint_id": solo_id, "n": None, "m": None}


def solo_rates(calibration_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-condition solo failure rates over the 96 calibration topics,
    plus the per-topic target-verdict tabulation for Gate 1 item behaviour."""
    per_condition: dict[str, list[int]] = {}
    per_topic_target: dict[str, dict[int, int]] = {}
    for row in calibration_rows:
        condition = parse_solo_arm(row["arm"])
        f = solo_failure(row["raw_response"], condition["constraint_id"],
                        n=condition["n"], m=condition["m"])
        per_condition.setdefault(row["arm"], []).append(f)
        if condition["constraint_id"] == "A":
            per_topic_target.setdefault(row["block_id"], {})[
                condition["n"]] = f
    rates = {arm: sum(v) / len(v) for arm, v in per_condition.items()}
    counts = {arm: len(v) for arm, v in per_condition.items()}
    return {"rates": rates, "counts": counts,
            "per_topic_target": per_topic_target}


def _closest(grid, rates_by_value):
    return min(grid, key=lambda v: (abs(rates_by_value[v] - SOLO_RATE_TARGET),
                                    v))


def _length_tokens(text: str) -> int:
    return len(text.split())


def evaluate_gate2(rates: dict[str, float]) -> dict[str, Any]:
    """The §18 Gate 2 decision from solo failure rates. Pure and testable."""
    n_rates = {n: rates[f"solo:A:n={n}"] for n in N_GRID}
    m_rates = {m: rates[f"solo:B:m={m}"] for m in M_GRID}
    n_star = _closest(N_GRID, n_rates)
    m_star = _closest(M_GRID, m_rates)
    n_ok = TARGET_SOLO_BAND[0] <= n_rates[n_star] <= TARGET_SOLO_BAND[1]
    m_ok = FOCAL_SOLO_BAND[0] <= m_rates[m_star] <= FOCAL_SOLO_BAND[1]

    focal_rate = m_rates[m_star]
    focal_length = _length_tokens(wording("B", 0, m=m_star))
    admission = []
    for cid in CANDIDATE_IDS:
        rate = rates[f"solo:{cid}"]
        length = _length_tokens(wording(cid, 0))
        rate_ok = abs(rate - focal_rate) <= ADMISSION_RATE_WINDOW
        length_ok = (abs(length - focal_length) / focal_length
                     <= ADMISSION_LENGTH_TOLERANCE)
        admission.append({
            "candidate": cid, "solo_rate": rate,
            "rate_distance": abs(rate - focal_rate),
            "length_tokens": length,
            "admitted": bool(rate_ok and length_ok),
            "rate_ok": rate_ok, "length_ok": length_ok,
            "whole_answer_scope": True,
        })
    admitted = [a for a in admission if a["admitted"]]
    admitted.sort(key=lambda a: (a["rate_distance"],
                                 CANDIDATE_IDS.index(a["candidate"])))
    references = tuple(a["candidate"] for a in admitted[:N_REFERENCES])

    passed = bool(n_ok and m_ok and len(admitted) >= N_REFERENCES)
    reasons = []
    if not n_ok:
        reasons.append(f"target solo rate {n_rates[n_star]:.3f} at n={n_star} "
                       f"outside {TARGET_SOLO_BAND}")
    if not m_ok:
        reasons.append(f"focal solo rate {m_rates[m_star]:.3f} at m={m_star} "
                       f"outside {FOCAL_SOLO_BAND}")
    if len(admitted) < N_REFERENCES:
        reasons.append(f"only {len(admitted)} admitted candidates; "
                       f"{N_REFERENCES} required — a scientific result, "
                       f"reported as such")
    record: dict[str, Any] = {
        "n_rates": {str(k): v for k, v in n_rates.items()},
        "m_rates": {str(k): v for k, v in m_rates.items()},
        "selected_n": n_star, "selected_m": m_star,
        "target_headroom_rate": n_rates[n_star],
        "focal_solo_rate": focal_rate,
        "n_in_band": n_ok, "m_in_band": m_ok,
        "admission": admission,
        "admitted_count": len(admitted),
        "references": list(references),
        "passed": passed,
        "failure_reasons": reasons,
    }
    if passed:
        certificates = [certify_composition("B", n_star, m_star)]
        certificates += [certify_composition(cid, n_star)
                         for cid in references]
        record["certificates"] = certificates
    return record
