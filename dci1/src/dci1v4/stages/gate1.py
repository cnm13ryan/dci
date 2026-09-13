"""Gate 1, GATE_1_MEASUREMENT (§10.2-§10.6, checks C1-C5).

**Five primary instruments, not one.** Under v4 the exact-count rule, the
word-length rule and each admitted family verifier are all primary, so every
line of §10.2 evidence is required for each of them: three-process determinism
at exactly 1.000, a frozen boundary suite of at least forty cases covering the
§24 enumeration, an independent reimplementation written from the registered
prose alone at exactly 1.000, a targeted adversarial corpus with realised
per-cell-type incidence, and either human agreement or the autorater pathway.

The measurement basis is a three-value machine field and is kept distinct from
the identification status: ``HUMAN_VALIDATION_UNAVAILABLE`` says no independent
annotator existed, while ``measurement_basis`` says how the instruments were
validated instead. While the basis is not ``human_validated`` every analysis
record carries the §10.5 scope sentence verbatim.

The canonical verifier hash is frozen here and re-verified at every §10.6 entry
point afterwards. It is never silently updated.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.analysis.intervals import wilson_upper_bound
from dci1v4.engine import fs
from dci1v4.engine.artifacts import claim_one_shot, one_shot_claimed
from dci1v4.engine.binding import verifier_provenance
from dci1v4.engine.paths import ModelTree
from dci1v4.errors import IntegrityError, ProtocolError, TerminalStatus
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import sha_obj
from dci1v4.verifiers import boundary, independent, verifier_source_hash
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import Constraint

#: The five instrument classes Gate 1 validates. Families beyond the three
#: admitted references are not instruments for this replication.
def instruments(slot_map: Mapping[str, tuple[str, int]]) -> list[tuple[str, int]]:
    return [slot_map[slot] for slot in sorted(slot_map)]


# ------------------------------------------------------- three-process
_DETERMINISM_SNIPPET = """
import json, sys
sys.path.insert(0, {src!r})
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import Constraint
payload = json.loads(sys.stdin.read())
out = []
for kind, severity, text in payload:
    s = score_constraint(Constraint(kind, severity), text, truncated=False)
    out.append([s.passed, s.graded, s.statistic, s.non_vacuous])
print(json.dumps(out))
"""


def three_process_determinism(instrument_list: Sequence[tuple[str, int]],
                              responses: Sequence[str], *,
                              src_root: Path | None = None) -> dict[str, Any]:
    """§10.2: three executions on three separate processes, agreement 1.000."""
    src = str(src_root or Path(__file__).resolve().parents[2])
    payload = json.dumps([[kind, severity, text]
                          for kind, severity in instrument_list
                          for text in responses])
    outputs: list[str] = []
    for _ in range(C.DETERMINISM_PROCESSES):
        completed = subprocess.run(
            [sys.executable, "-c", _DETERMINISM_SNIPPET.format(src=src)],
            input=payload, capture_output=True, text=True)
        if completed.returncode != 0:
            raise IntegrityError(f"determinism subprocess failed: "
                                 f"{completed.stderr.strip()[:400]}")
        outputs.append(completed.stdout.strip())
    agreement = 1.0 if len(set(outputs)) == 1 else 0.0
    return {"processes": C.DETERMINISM_PROCESSES,
            "responses": len(responses),
            "instruments": len(instrument_list), "agreement": agreement}


# ------------------------------------------- independent reimplementation
def independent_agreement(instrument_list: Sequence[tuple[str, int]],
                          responses: Sequence[str]) -> dict[str, Any]:
    """§10.2 / C1: agreement between the primary and the prose-only
    reimplementation, over every calibration response and the whole boundary
    suite. Required to be exactly 1.000."""
    texts = list(responses) + [c["text"] for c in boundary.TARGET_CASES]
    texts += [c["text"] for c in boundary.FOCAL_CASES]
    per_instrument: dict[str, float] = {}
    disagreements: list[dict[str, Any]] = []
    for kind, severity in instrument_list:
        agree = 0
        for text in texts:
            primary = score_constraint(Constraint(kind, severity), text,
                                       truncated=False)
            same = (primary.passed == independent.passes(kind, severity, text)
                    and abs(primary.graded
                            - independent.graded(kind, severity, text)) < 1e-12)
            if same:
                agree += 1
            else:
                disagreements.append({"kind": kind, "severity": severity,
                                      "text": text[:80]})
        per_instrument[f"{kind}@{severity}"] = agree / len(texts)
    return {"responses": len(texts), "agreement": per_instrument,
            "disagreements": disagreements[:10],
            "source_material": ("the registered prose of v4r2 §7.1, §7.2, "
                                "§7.4, §9.2 and §9.3 only; the "
                                "reimplementation imports nothing from "
                                "dci1v4.verifiers")}


# ------------------------------------------------------- human agreement
def human_agreement(labels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """§10.3: the one-sided 95% Wilson upper bound on human-to-verifier
    disagreement, per verifier class, with the fail class split by whether the
    realised margin is exactly one.

    Each label carries ``verifier_class`` ("pass" or "fail"), ``margin_one``
    (bool, meaningful in the fail class) and ``agrees`` (bool).
    """
    strata: dict[str, list[bool]] = {}
    for label in labels:
        verifier_class = label["verifier_class"]
        if verifier_class not in C.VERIFIER_CLASSES:
            raise ProtocolError(f"unknown verifier class {verifier_class!r}")
        if verifier_class == "fail":
            key = ("fail:margin_one" if label.get("margin_one")
                   else "fail:margin_larger")
        else:
            key = "pass"
        strata.setdefault(key, []).append(not label["agrees"])
    out: dict[str, Any] = {}
    for key, disagreements in sorted(strata.items()):
        total = len(disagreements)
        count = sum(disagreements)
        bound = wilson_upper_bound(count, total)
        out[key] = {"n": total, "disagreements": count,
                    "wilson_upper_bound": bound,
                    "meets_criterion": bound <= C.HUMAN_DISAGREEMENT_MAX}
    return {"strata": out, "criterion": C.HUMAN_DISAGREEMENT_MAX,
            "all_met": bool(out) and all(v["meets_criterion"]
                                         for v in out.values())}


# ---------------------------------------------------- sealed final-check set
def seal_final_check_set(tree: ModelTree, items: Sequence[Mapping[str, Any]],
                         *, producing_commit: str) -> dict[str, Any]:
    """§10.4: a **v4** reserved final-check set, sealed at Gate 1.

    Check C4 asks whether the v3 sealed set may serve. It may not: v4's
    instrument population is five instruments rather than one, so a set
    composed for the exact-count rule cannot exercise the word-length or family
    verifiers. A new v4 set is sealed here and the v3 set stays sealed either
    way — nothing in this package can open it.
    """
    path = tree.root / "gate1" / "sealed_final_check.json"
    digest = sha_obj(list(items))
    fs.write_json_once(path, {"sealed": True, "items": len(items),
                              "content_hash": digest,
                              "producing_commit": producing_commit,
                              "note": ("opened at most once, after every "
                                       "autorater choice is frozen; never "
                                       "used for tuning and never rerun to "
                                       "obtain a better result (§10.4)")})
    return {"path": str(path), "content_hash": digest, "items": len(items)}


def open_final_check_set(tree: ModelTree, *, autorater_frozen: bool,
                         producing_commit: str,
                         purpose: str = "final_check") -> dict[str, Any]:
    """Open the sealed set at most once, and never for tuning."""
    if purpose != "final_check":
        raise ProtocolError(
            f"the sealed set is never used for {purpose!r}; it is opened once "
            f"for the final check and never for tuning (§10.4)")
    if not autorater_frozen:
        raise ProtocolError(
            "the sealed final-check set may not be opened before every "
            "autorater choice is frozen (§10.4)")
    if one_shot_claimed(tree, "open_sealed_final_check"):
        raise IntegrityError(
            "the sealed final-check set has already been opened; §10.4 "
            "permits at most one open and it is never rerun to obtain a "
            "better result")
    claim_one_shot(tree, operation="open_sealed_final_check",
                   detail={"purpose": purpose},
                   producing_commit=producing_commit)
    path = tree.root / "gate1" / "sealed_final_check.json"
    return fs.read_json(path)


# --------------------------------------------------------------- the gate
def gate1_payload(*, instrument_list: Sequence[tuple[str, int]],
                  determinism: Mapping[str, Any],
                  suites: Mapping[str, Any],
                  reimplementation: Mapping[str, Any],
                  adversarial: Mapping[str, Any],
                  measurement_basis: str,
                  human: Mapping[str, Any] | None = None,
                  autorater: Mapping[str, Any] | None = None,
                  sealed_set: Mapping[str, Any] | None = None,
                  identification_statuses: Sequence[str] = ()
                  ) -> dict[str, Any]:
    """Gate 1 for every registered outcome verifier."""
    if measurement_basis not in C.MEASUREMENT_BASES:
        raise ProtocolError(f"measurement basis {measurement_basis!r} is not "
                            f"one of {C.MEASUREMENT_BASES}")

    # §10.3 distinguishes the two terminal statuses by *why* the evidence
    # fails: a measured excess is MEASUREMENT_NOT_ESTABLISHED, an exhausted
    # natural class — too few natural items to reach the criterion at all — is
    # MEASUREMENT_EVIDENCE_INSUFFICIENT. Failures are tagged, not pattern
    # matched, so the two can never be confused.
    failures: list[dict[str, str]] = []

    def _fail(kind: str, detail: str) -> None:
        failures.append({"kind": kind, "detail": detail})

    if determinism["agreement"] != 1.0:
        _fail("measured_excess",
              "three-process determinism is not exactly 1.000")
    for name, value in sorted(suites["agreement"].items()):
        if value != 1.0:
            _fail("measured_excess",
                  f"the boundary suite of {name} agrees at {value}")
    if suites["cases"]["A"] < C.BOUNDARY_SUITE_MIN_CASES:
        _fail("evidence_insufficient",
              "the A-side boundary suite holds fewer than forty cases")
    for name, value in sorted(reimplementation["agreement"].items()):
        if value != 1.0:
            _fail("measured_excess",
                  f"the independent reimplementation of {name} agrees at "
                  f"{value}")
    if measurement_basis == "human_validated":
        if human is None:
            _fail("evidence_insufficient",
                  "the basis is human_validated and no human labels exist")
        else:
            for stratum, entry in sorted(human["strata"].items()):
                if entry["n"] == 0:
                    _fail("evidence_insufficient",
                          f"the {stratum} class is exhausted: no natural item")
                elif not entry["meets_criterion"]:
                    # An exhausted class is one that could not meet the
                    # criterion even with zero disagreements: the natural
                    # population is too small, which is evidence insufficiency
                    # rather than a measured excess (§10.3).
                    best = wilson_upper_bound(0, entry["n"])
                    kind = ("evidence_insufficient"
                            if best > C.HUMAN_DISAGREEMENT_MAX
                            else "measured_excess")
                    _fail(kind,
                          f"the {stratum} Wilson upper bound "
                          f"{entry['wilson_upper_bound']:.4f} exceeds "
                          f"{C.HUMAN_DISAGREEMENT_MAX}; the best achievable "
                          f"bound at n={entry['n']} is {best:.4f}")
    elif measurement_basis == "autorater_calibration_approved":
        if not (autorater and autorater.get("approved")):
            _fail("measured_excess", "the autorater pathway is not approved")
    else:
        # §18 stage 4: Gate 1 passes on §10.2 **plus §10.3 or §10.4**.
        # ``human_validation_unavailable`` is the state in which neither
        # pathway has completed. §10.3 routes it to §10.4 "without waiving the
        # criterion", so it is not itself a basis Gate 1 can pass on: the
        # autorater pathway has to finish and the researcher has to approve it
        # explicitly. v3's Gate 1 recorded basis
        # ``autorater_calibration_approved`` with HUMAN_VALIDATION_UNAVAILABLE
        # as the identification status, which is the same distinction.
        _fail("evidence_insufficient",
              "the measurement basis is human_validation_unavailable: no "
              "independent annotator completed §10.3 and the §10.4 autorater "
              "pathway has not been approved, so neither pathway Gate 1 "
              "requires has completed")

    if failures:
        status = ("MEASUREMENT_NOT_ESTABLISHED"
                  if any(f["kind"] == "measured_excess" for f in failures)
                  else "MEASUREMENT_EVIDENCE_INSUFFICIENT")
        raise TerminalStatus(status, {
            "status": status, "gate": C.STAGE_GATE1,
            "criterion": "§10.2 for every registered outcome verifier, plus "
                         "§10.3 or §10.4",
            "threshold": {"determinism": 1.0, "boundary_agreement": 1.0,
                          "reimplementation_agreement": 1.0,
                          "human_disagreement_max":
                              C.HUMAN_DISAGREEMENT_MAX},
            "observed": failures, "artifact_hashes": {},
            "measurement_basis": measurement_basis,
            "strongest_permissible_statement":
                "measurement is not established for at least one registered "
                "primary instrument",
            "estimands_unanswerable": "all"})

    return {
        "outcome": "PASS",
        "instruments": [f"{k}@{s}" for k, s in instrument_list],
        **verifier_provenance(),
        "boundary_suites": dict(suites),
        "determinism": dict(determinism),
        "independent_reimplementation": dict(reimplementation),
        "adversarial_corpus": dict(adversarial),
        "human_agreement": dict(human) if human else None,
        "autorater": dict(autorater) if autorater else None,
        "sealed_final_check_set": dict(sealed_set) if sealed_set else None,
        "measurement_basis": measurement_basis,
        "scope_sentence": (None if measurement_basis == "human_validated"
                           else C.SCOPE_SENTENCE),
        "frozen_verifier_hash": verifier_source_hash(),
        "identification_statuses": list(identification_statuses),
    }
