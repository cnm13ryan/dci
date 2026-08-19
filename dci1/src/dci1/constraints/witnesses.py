"""Satisfiability and non-entailment witnesses (prereg §3, §5, Gate 2).

For every composition (target A at parameter n plus one added constraint —
the focal B at parameter m, or a pool candidate) three hand-written witnesses
exist:

* ``joint``      — satisfies A and the added constraint together;
* ``a_only``     — satisfies A and fails the added constraint;
* ``added_only`` — satisfies the added constraint and fails A.

``certify_composition`` executes the real verifiers on all three and returns a
machine-readable certificate; any witness failing its expectation raises. The
certificates for every composition to be used are produced before confirmatory
generation and carried in the freeze record (Gate 2).
"""
from __future__ import annotations

from dci1.constraints.definitions import added_verifier
from dci1.protocol.constants import ProtocolError
from dci1.verifiers.target import s0_count

#: One sentence per added constraint, each containing exactly one 'however'
#: and satisfying that constraint. n sentences joined give an A-pass at n.
_JOINT_SENTENCE = {
    "C1": "However, rain falls in many places.",
    "C2": "However, most people enjoy warm weather.",
    "C3": "However, rain falls in many dry places.",
    "C4": "However, rain falls in many dry places.",
    "C5": "However, rain arrives in many dry places.",
    "C6": "However, rain falls in several dry places.",
    "C7": "However, rain falls in many dry regions.",
    "C8": "However, rain falls in many dry places.",
    "C9": "However, rain falls in many dry places.",
    "C10": "However, rain falls in many dry places.",
    "C11": "However, rain falls in many dry places.",
    "C12": "However, rain is rare in the dry desert.",
    "B": "However, dry air can stay clear at night.",
}

#: One word violating each added constraint while leaving A satisfiable.
_VIOLATING_SENTENCE = {
    "C1": "However, a storm may come.",
    "C2": "However, an odd storm may come.",
    "C3": "However, big storms may come.",
    "C4": "However, cold rain may come.",
    "C5": "However, fresh rain may come.",
    "C6": "However, mild rain may come.",
    "C7": "However, polar rain may come.",
    "C8": "However, salty rain may come.",
    "C9": "However, tidal rain may come.",
    "C10": "However, rain may come quickly.",
    "C11": "However, rain keeps coming.",
    "C12": "However, sudden rain may come.",
}

#: A word longer than m for each admissible m, to violate B.
_OVERLONG_WORD = {7: "rainfall", 8: "hurricane", 9: "cloudburst",
                  10: "atmospheric"}

#: Zero-'however' texts satisfying each added constraint (fails A for n >= 1).
_ADDED_ONLY = {
    "C1": "Rain falls in many places.",
    "C2": "Most people enjoy warm weather.",
    "C3": "Rain falls in many dry places.",
    "C4": "Rain falls in many dry places.",
    "C5": "Rain arrives in many dry places.",
    "C6": "Rain falls in several dry places.",
    "C7": "Rain falls in many dry regions.",
    "C8": "Rain falls in many dry places.",
    "C9": "Rain falls in many dry places.",
    "C10": "Rain falls in many dry places.",
    "C11": "Rain falls in many dry places.",
    "C12": "Rain is rare in the dry desert.",
    "B": "Dry air can stay clear at night.",
}


def joint_witness(constraint_id: str, n: int) -> str:
    return " ".join([_JOINT_SENTENCE[constraint_id]] * n)


def a_only_witness(constraint_id: str, n: int, m: int | None = None) -> str:
    if constraint_id == "B":
        if m not in _OVERLONG_WORD:
            raise ProtocolError(f"no overlong word declared for m={m}")
        sentence = f"However, {_OVERLONG_WORD[m]} may come at night."
    else:
        sentence = _VIOLATING_SENTENCE[constraint_id]
    return " ".join([sentence] * n)


def added_only_witness(constraint_id: str) -> str:
    return _ADDED_ONLY[constraint_id]


def certify_composition(constraint_id: str, n: int,
                        m: int | None = None) -> dict:
    """Execute all three witnesses with the real verifiers; fail closed."""
    verify_added = added_verifier(constraint_id,
                                  m if constraint_id == "B" else None)

    joint = joint_witness(constraint_id, n)
    a_only = a_only_witness(constraint_id, n, m)
    added_only = added_only_witness(constraint_id)

    checks = {
        "joint_satisfies_target": s0_count(joint) == n,
        "joint_satisfies_added": verify_added(joint),
        "a_only_satisfies_target": s0_count(a_only) == n,
        "a_only_fails_added": not verify_added(a_only),
        "added_only_satisfies_added": verify_added(added_only),
        "added_only_fails_target": s0_count(added_only) != n,
    }
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise ProtocolError(
            f"witness certification failed for composition A(n={n}) + "
            f"{constraint_id}" + (f"(m={m})" if constraint_id == "B" else "")
            + f": {failed}")
    return {
        "composition": {"target_n": n, "added": constraint_id,
                        "m": m if constraint_id == "B" else None},
        "witnesses": {"joint": joint, "a_only": a_only,
                      "added_only": added_only},
        "checks": checks,
        "jointly_satisfiable": True,
        "non_entailment_bidirectional": True,
    }
