"""§13.6's interaction rule: kappa(R|B), displacement, projection.

**The problem it names.** A control can be validly matched on every solo
quantity and still be worthless, because the outcome constraint changes the
response distribution its verifier integrates over. v4r4's `gemma-3n-e2b-it`
terminated because `RF11` --- *at most q words may begin with a vowel* --- was
composed with B: B shortens words and shortens answers, the vowel-initial
count fell from about 24 to about 17, and a budget of 26 became trivially
satisfiable, taking `RF11:26` from 0.635 solo to 0.969 composed. Pairing the
same rung with other references barely moved it. **The ceiling was produced by
B specifically** --- the outcome constraint of the whole study.

**The quantity that sees it before composing.** Under §9.1 every generation is
scored on every registered instance, so R's verifier is already run on
responses written under B **alone**::

    kappa(R|B) = P(X_R = 1 | B alone at m*, R absent)

R is never stated in those prompts. This is a chance verdict under a different
load-one treatment. It reads no composed cell, no contrast between composed
cells, and B's compliance in no cell, and it costs **zero extra generations**.

**Why this is not outcome-based selection.** Delta_R reads X_B in the B+R_j
cells; the B-solo baseline cancels. kappa(R|B) reads X_R in the B-solo cell.
Different verdict, different rows, and kappa(R|B) observes B's compliance
nowhere. The residual-bias direction is checkable and is *conservative*: a
reference B makes trivial would show a **small** D(B <- R_j), which would make
the reference mean small and Delta_R **large**, so excluding such references
is conservative with respect to H_pair and not favourable to it.

**What the development evidence showed, and what it does not establish.** On
`gemma-3n-e2b-it` --- the only v4r4 replication that ever composed a reference
with B --- the projection was computed for 20 composed rate checks from
pre-composition quantities alone: median absolute error 0.067, and at a
ceiling of 0.90 it caught 4 of 4 composed-headroom failures with 0 false
alarms among 16 passing checks. **Twenty rate checks on one model is design
fitting.** The 0.90 ceiling is derived from §13.14's band and a 0.05 error
allowance, and the fact that it happens to sit inside the observed gap
between the highest passing projection (0.8836) and the lowest failing one
(0.9388) is recorded rather than used as evidence.

**Generality.** The rule names a property of the pair (statistic, focal
constraint) and measures it. It excludes no family by name. It is not
*"exclude RF11"*; it is *"exclude a candidate whose verifier statistic the
focal constraint's own response-distribution shift moves into a degenerate
region"*, and RF11 is excluded on a model where that is measured to happen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C

__all__ = ["KappaUnderBSource", "kappa_under_b", "displacement",
           "projected_compliance", "interaction_verdict",
           "assert_kappa_under_b_source", "InteractionMeasurement",
           "measure_interaction", "realised_drift"]


@dataclass(frozen=True)
class KappaUnderBSource:
    """Where a kappa(R|B) value came from, in enough detail to refuse it.

    §13.11 puts ``kappa_under_b`` on the permitted list **by name** and then
    requires the loader to assert that the rows supplying it are load-one
    cells whose single present constraint is B. This structure is what that
    assertion reads: without it the field is a number with a good name.
    """

    load: int
    #: The constraint labels the prompt stated, e.g. ``("B:9",)``.
    present: tuple[str, ...]
    #: The candidate's own label, which must be **absent** from the prompt.
    candidate: str
    model_key: str
    m_star: int
    split: str
    n_topics: int
    n_draws: int


def assert_kappa_under_b_source(source: KappaUnderBSource, *,
                                model_key: str, m_star: int,
                                split: str, candidate: str,
                                n_topics: int | None = None,
                                where: str = "kappa_under_b") -> None:
    """§13.6 and §13.11: seven hard conditions, each refused by name.

    Every one of them is a way a composed row, or a row from the wrong
    treatment, could reach a quantity that decides admission. They are checked
    together because any one of them alone leaves a route open.
    """
    if source.load != 1:
        raise ProtocolError(
            f"{where}: kappa(R|B) is measured on a cell of load one and this "
            f"row carries load {source.load}. A composed row may never enter "
            "this quantity (§13.6, §13.11)")
    expected_present = (f"B:{m_star}",)
    if tuple(source.present) != expected_present:
        raise ProtocolError(
            f"{where}: kappa(R|B) reads the B-solo cell at m* and this row "
            f"states {list(source.present)}, not {list(expected_present)}")
    if source.candidate != candidate:
        raise ProtocolError(
            f"{where}: this source describes {source.candidate!r} and the "
            f"row is {candidate!r}")
    if source.candidate in source.present:
        raise ProtocolError(
            f"{where}: R must be ABSENT in the cell kappa(R|B) is read from; "
            f"{source.candidate!r} is stated in it")
    if source.model_key != model_key:
        raise ProtocolError(
            f"{where}: kappa(R|B) is a property of the pair (R, B at m*) on "
            f"ONE model; this source is {source.model_key!r} and the "
            f"replication is {model_key!r}. §29 registers that no cross-model "
            "transfer of an interaction verdict is licensed")
    if source.m_star != m_star:
        raise ProtocolError(
            f"{where}: measured at m={source.m_star} and the replication's "
            f"operating point is m*={m_star}")
    if source.split != split:
        raise ProtocolError(
            f"{where}: measured on split {source.split!r} and this table is "
            f"{split!r}; §13.7 evaluates each split on that split alone")
    if n_topics is not None and source.n_topics != n_topics:
        raise ProtocolError(
            f"{where}: measured over {source.n_topics} topics and the split "
            f"carries {n_topics}")
    if source.n_draws <= 0:
        raise ProtocolError(f"{where}: no draws recorded")


def kappa_under_b(verdicts: Iterable[bool]) -> float:
    """P(X_R = 1 | B alone at m*, R absent), from stored chance verdicts.

    The caller supplies the verdicts; this function does the arithmetic and
    nothing else, so there is no path here that could reach a composed row.
    """
    values = [1.0 if v else 0.0 for v in verdicts]
    if not values:
        raise ProtocolError(
            "§13.6: kappa(R|B) has no verdicts. A candidate for which it is "
            "missing is NOT admitted; absence is never read as a pass")
    return sum(values) / len(values)


def displacement(kappa: float, kappa_b: float) -> float:
    """Sigma_R = kappa(R|B) - kappa(R): how far stating B moves the regime.

    Signed and two-sided. It catches the **floor** direction, which the
    projection does not: on `qwen3-4b`, `CL7:30` moved from kappa 0.849 to
    kappa(R|B) 0.122, so its measured difficulty described a response
    distribution B destroys.
    """
    return kappa_b - kappa


def projected_compliance(kappa_b: float, iota: float) -> float:
    """p_hat(R) = kappa(R|B) + iota_R * (1 - kappa(R|B)).

    iota_R evaluated at the counterfactual baseline B induces rather than at
    the unconstrained baseline: the definition of instructed compliance
    re-evaluated in the regime the reference will actually be used in.

    One property makes the gate robust where it binds: as kappa(R|B) -> 1 the
    projection -> 1 whatever iota_R is, so it is least sensitive to the
    transfer assumption exactly where it decides.
    """
    if not 0.0 <= kappa_b <= 1.0:
        raise ProtocolError(f"kappa(R|B) out of range: {kappa_b}")
    return kappa_b + iota * (1.0 - kappa_b)


@dataclass(frozen=True)
class InteractionMeasurement:
    """Everything §13.6 computes for one candidate on one split."""

    candidate: str
    kappa: float
    kappa_under_b: float
    iota: float
    displacement: float
    projected_compliance: float
    passed: bool
    reason: str | None


def interaction_verdict(*, kappa: float, kappa_b: float, iota: float,
                        candidate: str = "R") -> InteractionMeasurement:
    """§13.6's rule: the projection inside its band and |Sigma| inside its bound.

    Both conditions, and the reason names whichever failed first in the order
    the preregistration states them.
    """
    sigma = displacement(kappa, kappa_b)
    p_hat = projected_compliance(kappa_b, iota)
    lo, hi = C.PROJECTED_COMPLIANCE_BAND
    reason = None
    if not lo <= p_hat <= hi:
        reason = (f"projected composed compliance {p_hat:.4f} outside the "
                  f"registered band [{lo}, {hi}]: stating B alone already "
                  f"satisfies this candidate on {kappa_b:.4f} of responses")
    elif abs(sigma) > C.DISPLACEMENT_MAX:
        reason = (f"displacement {sigma:+.4f} beyond +/-{C.DISPLACEMENT_MAX}: "
                  f"stating B moves the regime this candidate's difficulty "
                  f"was measured in (kappa {kappa:.4f} -> {kappa_b:.4f})")
    return InteractionMeasurement(
        candidate=candidate, kappa=kappa, kappa_under_b=kappa_b, iota=iota,
        displacement=sigma, projected_compliance=p_hat,
        passed=reason is None, reason=reason)


def measure_interaction(rows: Sequence[Mapping[str, Any]], *, model_key: str,
                        m_star: int, split: str) -> dict[str, Any]:
    """§18 stage 7: every carried candidate's interaction verdict.

    ``rows`` carry ``candidate``, ``kappa``, ``iota``, ``kappa_under_b`` and a
    ``source`` that ``assert_kappa_under_b_source`` validates. A candidate
    whose kappa(R|B) is missing is **not admitted**: §13.6 says absence is
    never read as a pass, and this returns it as a failure with that reason
    rather than skipping it.
    """
    out: list[dict[str, Any]] = []
    for row in rows:
        candidate = row["candidate"]
        source = row.get("source")
        if row.get("kappa_under_b") is None or source is None:
            out.append({"candidate": candidate, "passed": False,
                        "reason": "kappa(R|B) not measured; §13.6 does not "
                                  "admit a candidate whose interaction "
                                  "quantity is missing, and absence is never "
                                  "read as a pass"})
            continue
        assert_kappa_under_b_source(source, model_key=model_key,
                                    m_star=m_star, split=split,
                                    candidate=candidate,
                                    where=f"§13.6:{candidate}")
        verdict = interaction_verdict(kappa=row["kappa"],
                                      kappa_b=row["kappa_under_b"],
                                      iota=row["iota"], candidate=candidate)
        out.append({"candidate": candidate, "passed": verdict.passed,
                    "reason": verdict.reason, "kappa": verdict.kappa,
                    "kappa_under_b": verdict.kappa_under_b,
                    "displacement": verdict.displacement,
                    "projected_compliance": verdict.projected_compliance})
    return {"model_key": model_key, "m_star": m_star, "split": split,
            "band": list(C.PROJECTED_COMPLIANCE_BAND),
            "displacement_max": C.DISPLACEMENT_MAX,
            "verdicts": out,
            "n_passed": sum(1 for v in out if v["passed"]),
            "n_failed": sum(1 for v in out if not v["passed"])}


def realised_drift(*, calibration_kappa_b: float, confirmatory_kappa_b: float,
                   iota: float, reference: str) -> dict[str, Any]:
    """§13.8's realised check on §13.6's own input, on the confirmatory data.

    kappa(R|B) is estimated on the calibration splits and used to admit a
    reference that is then composed on the confirmatory blocks, where it is
    measured again on the B-solo cell of all 384 blocks. When the two differ
    by more than the registered amount, or the realised projection falls
    outside §13.6's band, every L3 statement carries
    ``INTERACTION_ESTIMATE_DRIFTED``.

    It is an identification status and **not** a terminal one: the reference
    was admitted under the registered rule on the registered data, and a
    drift discovered afterwards is a finding about the rule --- which §26 says
    is what v5 exists to produce.
    """
    drift = confirmatory_kappa_b - calibration_kappa_b
    realised = projected_compliance(confirmatory_kappa_b, iota)
    lo, hi = C.PROJECTED_COMPLIANCE_BAND
    drifted = (abs(drift) > C.INTERACTION_DRIFT_MAX
               or not lo <= realised <= hi)
    return {"reference": reference,
            "calibration_kappa_under_b": calibration_kappa_b,
            "confirmatory_kappa_under_b": confirmatory_kappa_b,
            "drift": drift, "threshold": C.INTERACTION_DRIFT_MAX,
            "realised_projected_compliance": realised,
            "identification_statuses":
                ["INTERACTION_ESTIMATE_DRIFTED"] if drifted else [],
            "terminal": False}
