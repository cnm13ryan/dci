"""The verifier-coupling ELIGIBILITY AUDIT declared by `primary_total`.

WHAT kappa IS
-------------
Verifier coupling kappa(X, A) is the measured tendency for a small
boundary-level edit -- removing a sentence break, swapping it for a newline or a
semicolon, turning a full stop into an exclamation mark, appending a clause -- to
flip A's verdict and X's verdict TOGETHER. High coupling means the two verifiers
lean on the same textual structure, so one textual accident breaks both
measurements at once.

WHY IT IS AUDITED AND NOT MATCHED
---------------------------------
`primary_total` deliberately does NOT match on kappa. The supplied methodology
lists coupling both as a verifier artefact to exclude and as a potential
moderator, which would place it on the causal pathway -- and matching on a
pathway variable removes part of the effect under study. So primary_total keeps
coupling INSIDE tau and merely refuses references whose coupling with A is
grossly unlike B's. `kappa_matched` is the separate, narrower estimand that does
match on it.

THE DEFECT THIS FIXES
---------------------
`coupling_audit_max` (0.20) was declared in ProtocolConfig, printed in a message
that told the reader coupling had become "a hard measurement-coupling audit at
|kappa_C - kappa_B| <= 0.20", and consumed by NOTHING. The whole codebase
referenced it exactly once, inside that f-string. Meanwhile `admit_candidates`
iterates `calipers.index`, which omits kappa entirely when the role is `audit`.
The declared reference definition and the executed one therefore differed.

Support is required of CANDIDATES on the same terms as the focal constraint. A
candidate whose kappa rests on too few informative probes, or is too imprecise,
has not passed the audit -- it has failed to take it, which is not the same as
passing and must not be treated as such.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from typing import Iterable, Optional


def coupling_support(kappa: float, se: float, n_informative: int,
                     min_probes: int, max_se: float) -> tuple[bool, str]:
    """Is this kappa estimate usable at all? Same rule as the focal estimate."""
    if not np.isfinite(kappa):
        return False, "kappa is undefined"
    if n_informative < min_probes:
        return False, (f"only {n_informative} informative probes "
                       f"(minimum {min_probes})")
    if not np.isfinite(se):
        return False, "kappa standard error is undefined"
    if se > max_se:
        return False, f"kappa SE {se:.4f} exceeds the ceiling {max_se:.2f}"
    return True, ""


def coupling_audit(coupling: pd.Series, coupling_se: pd.Series,
                   n_informative: pd.Series, focal: str,
                   candidate_ids: Iterable[str], max_gap: float,
                   min_probes: int, max_se: float,
                   uncertainty_q: float = 1.0,
                   indexed_frame: Optional[callable] = None) -> pd.DataFrame:
    """|kappa_C - kappa_B| + q*SE <= max_gap, with support required of both.

    The uncertainty term points the same way as everywhere else in the protocol:
    imprecision makes admission HARDER, never easier. A candidate cannot pass by
    being unmeasurable.
    """
    focal_kappa = float(coupling.get(focal, np.nan))
    focal_se = float(coupling_se.get(focal, np.nan))
    focal_n = int(n_informative.get(focal, 0) or 0)
    focal_ok, focal_reason = coupling_support(
        focal_kappa, focal_se, focal_n, min_probes, max_se)

    rows = []
    for cid in candidate_ids:
        if cid == focal:
            continue
        kappa = float(coupling.get(cid, np.nan))
        se = float(coupling_se.get(cid, np.nan))
        n = int(n_informative.get(cid, 0) or 0)
        ok, reason = coupling_support(kappa, se, n, min_probes, max_se)

        gap = abs(focal_kappa - kappa) if np.isfinite(kappa) and focal_ok else np.nan
        combined_se = math.sqrt(np.nansum([focal_se ** 2, se ** 2])) \
            if (np.isfinite(focal_se) or np.isfinite(se)) else np.nan
        adjusted = (gap + uncertainty_q * combined_se
                    if np.isfinite(gap) and np.isfinite(combined_se) else np.nan)

        if not focal_ok:
            audit_ok, why = False, f"focal coupling unusable: {focal_reason}"
        elif not ok:
            audit_ok, why = False, f"candidate coupling unusable: {reason}"
        elif not np.isfinite(adjusted):
            audit_ok, why = False, "coupling gap is undefined"
        elif adjusted > max_gap:
            audit_ok, why = False, (
                f"coupling audit |kappa_C - kappa_B| + q*SE = {adjusted:.3f} "
                f"> {max_gap:.2f}")
        else:
            audit_ok, why = True, ""

        rows.append({"constraint_id": cid, "kappa": kappa, "kappa_se": se,
                     "n_informative": n, "focal_kappa": focal_kappa,
                     "focal_kappa_se": focal_se, "focal_n_informative": focal_n,
                     "support_ok": bool(ok), "coupling_gap": gap,
                     "combined_se": combined_se, "adjusted_gap": adjusted,
                     "audit_max": max_gap, "coupling_audit_ok": bool(audit_ok),
                     "coupling_audit_reason": why})

    columns = ["constraint_id", "kappa", "kappa_se", "n_informative",
               "focal_kappa", "focal_kappa_se", "focal_n_informative",
               "support_ok", "coupling_gap", "combined_se", "adjusted_gap",
               "audit_max", "coupling_audit_ok", "coupling_audit_reason"]
    if indexed_frame is not None:
        return indexed_frame(rows, "constraint_id", columns)
    frame = pd.DataFrame(rows, columns=columns)
    return frame.set_index("constraint_id") if len(frame) else frame


def passthrough_audit(candidate_ids: Iterable[str]) -> pd.DataFrame:
    """An all-pass audit frame, for FIXTURES ONLY.

    Gate 0 exercises the caliper and certificate logic on synthetic candidate ids
    that were never probed for coupling, so a strict audit would reject them for
    absence of data and the fixture would test the wrong thing. Real admission
    never uses this: absent coupling data must fail there, which is the point of
    requiring candidate-level support. The kappa audit itself is covered by
    tests/unit/test_coupling_audit.py.
    """
    ids = [str(c) for c in candidate_ids]
    out = pd.DataFrame(
        {"kappa": [np.nan] * len(ids), "adjusted_gap": [0.0] * len(ids),
         "coupling_audit_ok": [True] * len(ids),
         "coupling_audit_reason": [""] * len(ids)},
        index=pd.Index(ids, name="constraint_id"))
    # Marks the frame as a fixture, so admission fills UNLISTED candidates with
    # `True` instead of the strict `False`. Only a passthrough frame gets that
    # treatment; the real audit still fails an unmeasured candidate.
    out.attrs["passthrough_fixture"] = True
    return out


def audit_summary(audit: pd.DataFrame) -> dict:
    """Counts for the gate record."""
    if not len(audit):
        return {"n_candidates": 0, "n_passed": 0, "n_no_support": 0,
                "n_over_tolerance": 0}
    return {
        "n_candidates": int(len(audit)),
        "n_passed": int(audit["coupling_audit_ok"].sum()),
        "n_no_support": int((~audit["support_ok"].astype(bool)).sum()),
        "n_over_tolerance": int((audit["support_ok"].astype(bool)
                                 & ~audit["coupling_audit_ok"].astype(bool)).sum()),
        "worst_adjusted_gap": float(pd.to_numeric(
            audit["adjusted_gap"], errors="coerce").max()),
    }


def kappa_is_degenerate(coupling: pd.Series, coupling_se: pd.Series,
                        min_distinct: int = 3) -> dict:
    """Is the kappa statistic discriminating at all?

    If every constraint's kappa collapses onto one or two values, an audit on it
    is vacuous -- it would pass everything or nothing for reasons unrelated to
    measurement coupling. That is a measurement-design problem to be fixed in the
    coupling probe, NOT a reason to widen or drop the tolerance.
    """
    values = pd.to_numeric(coupling, errors="coerce").dropna()
    ses = pd.to_numeric(coupling_se, errors="coerce").dropna()
    distinct = int(values.round(6).nunique())
    return {
        "n_estimates": int(len(values)),
        "n_distinct": distinct,
        "degenerate": bool(len(values) and distinct < min_distinct),
        "spread": float(values.max() - values.min()) if len(values) else float("nan"),
        "median_se": float(ses.median()) if len(ses) else float("nan"),
        "all_zero": bool(len(values) and bool((values == 0).all())),
    }
