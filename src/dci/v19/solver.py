"""The Z3 conjunction, and the three results section 8.6 insists on separating.

    "Z3 distinguishes `sat`, `unsat`, and `unknown`; only `sat` may support
    progression, while `unsat`, `unknown`, timeout, or missing required solver
    output fails closed."

Four distinct ways not to progress, and the interesting one is the fourth. If z3
is not installed the honest result is "missing required solver output", not "skip
the solver step" - so `SolverUnavailable` is raised and the certification records
a non-progressable outcome. A satisfiability layer that silently degrades to no
solver at all is worse than one that is absent, because the artifact still says
certified.

WHAT THE SOLVER IS ASKED
------------------------
Only statements about `encoding.ABSTRACT_FEATURES`. The bounds that make the
projection finite - how many sentences and items may be modelled - are part of the
question, so they are hashed into the record alongside the encoding. A `sat` found
under a 12-sentence bound is evidence about compositions of at most 12 sentences
and the record says so.

The consistency axioms below are also part of the abstraction and are deliberately
WEAK where the direction matters. Sentence lengths are constrained to sum to at
most the token count rather than exactly, because an over-strong axiom produces
spurious `unsat`, and `unsat` rejects a proposal outright (section 8.5) whereas a
spurious `sat` is caught downstream by the concrete all-verifier witness. The
evidential hierarchy of section 8.6 puts the witness above the solver, so the
solver is allowed to be the looser of the two.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19.encoding import ClauseKind, Composition
from dci.v19.parsing import OrderingRelation

SOLVER_STATUSES = ("sat", "unsat", "unknown")

# Section 8.6: "only sat may support progression".
PROGRESSABLE_STATUSES = ("sat",)

# The finite bounds that make the abstract projection decidable. Part of the
# question asked, therefore part of the record's hash.
DEFAULT_BOUNDS: Mapping[str, int] = {
    "max_items": 32,
    "max_sentences": 32,
    "max_tokens": 4096,
    "timeout_ms": 10_000,
}


class SolverUnavailable(RuntimeError):
    """No frozen solver is installed, so required solver output is missing."""


class SolverError(RuntimeError):
    """The conjunction could not be built for this composition."""


@dataclass(frozen=True)
class SolverRecord:
    """One solver invocation, archived as section 8.6 requires.

    "Archive the exact composition, structured encoding, solver input/output,
    candidate/winning witness, verifier results, semantic reviews where
    applicable, hashes, and construction commit." `smt2` is the exact input.
    """
    solver: str
    version: str
    status: str
    reason: str
    bounds: Mapping[str, int]
    encoding_hash: str
    smt2: str
    model: Mapping[str, int]

    def __post_init__(self):
        if self.status not in SOLVER_STATUSES:
            raise SolverError(
                f"{self.status!r} is not one of {SOLVER_STATUSES}; section 8.6 "
                "requires the three to stay distinct")
        if self.status != "sat" and self.model:
            raise SolverError(
                f"status is {self.status} yet a model is recorded; only sat has one")
        if not self.reason:
            raise SolverError("a solver record states why it reached its status")

    @property
    def progressable(self) -> bool:
        return self.status in PROGRESSABLE_STATUSES

    def state(self) -> dict[str, Any]:
        return {"solver": self.solver, "version": self.version,
                "status": self.status, "bounds": dict(self.bounds),
                "encoding_hash": self.encoding_hash,
                "smt2": self.smt2, "model": dict(self.model)}

    @property
    def record_hash(self) -> str:
        return sha(["v19/solver-record", self.state()])

    def describe(self) -> dict[str, Any]:
        return {**self.state(), "reason": self.reason,
                "progressable": self.progressable,
                "record_hash": self.record_hash}


def solver_identity() -> tuple[str, str]:
    """The frozen solver's name and version, or refuse.

    Section 8.6 permits "Z3 or an equivalently frozen solver"; the identity is
    recorded because a solver whose version is unknown is not frozen.
    """
    try:
        import z3
    except ImportError as error:                      # pragma: no cover - env
        raise SolverUnavailable(
            "no Z3 installation is importable, so the required solver output for "
            "the abstract conjunction is missing. Section 8.6 fails closed on "
            "missing solver output; it does not permit skipping the solver step"
        ) from error
    return "z3", z3.get_version_string()


def _conjunction(composition: Composition, bounds: Mapping[str, int]):
    """Build the Z3 assertions for one composition, plus the feature variables."""
    import z3

    max_items = bounds["max_items"]
    max_sentences = bounds["max_sentences"]
    max_tokens = bounds["max_tokens"]

    n_items = z3.Int("n_items")
    n_sentences = z3.Int("n_sentences")
    n_tokens = z3.Int("n_tokens")
    n_distinct = z3.Int("n_distinct_tokens")
    lengths = [z3.Int(f"sentence_length_{i}") for i in range(max_sentences)]
    variables: dict[str, Any] = {
        "n_items": n_items, "n_sentences": n_sentences, "n_tokens": n_tokens,
        "n_distinct_tokens": n_distinct}
    for index, length in enumerate(lengths):
        variables[f"sentence_length_{index}"] = length

    # Consistency axioms for the abstraction itself.
    assertions = [
        n_items >= 0, n_items <= max_items,
        n_sentences >= 0, n_sentences <= max_sentences,
        n_tokens >= 0, n_tokens <= max_tokens,
        n_distinct >= 0, n_distinct <= n_tokens,
    ]
    for index, length in enumerate(lengths):
        # A modelled sentence carries at least one word; an unmodelled slot is 0.
        assertions.append(z3.If(index < n_sentences, length >= 1, length == 0))
    # Weak on purpose: see the module docstring.
    assertions.append(z3.Sum(lengths) <= n_tokens)

    multiplicities: dict[str, Any] = {}
    positions: dict[str, Any] = {}

    for clause in composition.clauses:
        if clause.kind is ClauseKind.EXACT_ITEM_COUNT:
            assertions.append(n_items == clause.parameters["n_items"])
        elif clause.kind is ClauseKind.ITEM_PRECEDENCE:
            relation = clause.parameters["relation"]
            if not isinstance(relation, OrderingRelation):
                raise SolverError(
                    f"{clause.constraint_id}: the precedence clause lost its "
                    "OrderingRelation, so its closure cannot be asserted")
            for label in relation.items:
                variable = z3.Int(f"item_position_{label}")
                positions[label] = variable
                variables[f"item_position_{label}"] = variable
                assertions += [variable >= 0, variable < n_items]
            assertions.append(z3.Distinct(*positions.values()))
            if clause.parameters.get("extra_items_permitted"):
                assertions.append(n_items >= len(relation.items))
            else:
                # The frozen policy makes an undeclared list item a structural
                # failure, so the list is exactly the declared items. Asserting
                # only `>=` here would make the solver report sat for a
                # composition whose witness every verifier rejects, which is the
                # encoding/verifier disagreement section 14 exists to prevent.
                assertions.append(n_items == len(relation.items))
            for before, after in relation.closure():
                assertions.append(positions[before] < positions[after])
        elif clause.kind is ClauseKind.EXACT_SENTENCE_COUNT:
            assertions.append(n_sentences == clause.parameters["n_sentences"])
        elif clause.kind is ClauseKind.INCREASING_SENTENCE_LENGTHS:
            for index in range(max_sentences - 1):
                assertions.append(z3.Implies(index + 1 < n_sentences,
                                             lengths[index] < lengths[index + 1]))
        elif clause.kind is ClauseKind.MANDATORY_TOKENS:
            # Set semantics, matching the deterministic verifier exactly: the
            # inherited `v_require_word_set` records presence, not multiplicity, so
            # asserting a count here would encode a stricter rule than the one
            # measured and could produce an unsat the verifier would never see.
            for token in sorted(set(clause.parameters["folded"])):
                variable = z3.Int(f"token_multiplicity_{token}")
                multiplicities[token] = variable
                variables[f"token_multiplicity_{token}"] = variable
                assertions += [variable >= 1, variable <= n_tokens]
            distinct_required = clause.parameters["distinct_required"]
            assertions.append(n_distinct >= distinct_required)
            assertions.append(n_tokens >= distinct_required)
        elif clause.kind is ClauseKind.ALL_TOKENS_DISTINCT:
            assertions.append(n_distinct == n_tokens)
        else:                                          # pragma: no cover - guarded
            raise SolverError(f"{clause.kind!r} has no Z3 encoding")

    # Derived from the frozen segmentation rather than assumed: markers are
    # stripped and each remaining line becomes a sentence, so every list item line
    # is at least one sentence. Sound in the direction that matters -- it removes
    # only genuinely infeasible models -- and asserted only when both feature
    # families are actually constrained, so it cannot narrow an unrelated question.
    kinds = {c.kind for c in composition.clauses}
    if kinds & {ClauseKind.EXACT_ITEM_COUNT, ClauseKind.ITEM_PRECEDENCE} and \
            kinds & {ClauseKind.EXACT_SENTENCE_COUNT,
                     ClauseKind.INCREASING_SENTENCE_LENGTHS}:
        assertions.append(n_sentences >= n_items)

    # A distinctness clause may be asserted before the mandatory-token clause that
    # introduces the multiplicity variables, so tie them together once at the end
    # rather than depending on clause order.
    if any(c.kind is ClauseKind.ALL_TOKENS_DISTINCT for c in composition.clauses):
        for variable in multiplicities.values():
            assertions.append(variable <= 1)
    if multiplicities:
        assertions.append(z3.Sum(list(multiplicities.values())) <= n_tokens)
        assertions.append(n_distinct >= len(multiplicities))

    return assertions, variables


def solve(composition: Composition, *,
          bounds: Mapping[str, int] | None = None) -> SolverRecord:
    """Ask the frozen solver whether the whole conjunction is satisfiable.

    Returns a record for every outcome including `unsat` and `unknown`, because
    section 8.5 requires "every proposal, rejection reason, solver record, witness,
    verifier output, and attempt seed" to be archived - the rejections especially.
    """
    import z3

    name, version = solver_identity()
    limits = {**DEFAULT_BOUNDS, **(dict(bounds) if bounds else {})}
    assertions, variables = _conjunction(composition, limits)

    solver = z3.Solver()
    solver.set("timeout", limits["timeout_ms"])
    solver.add(*assertions)
    smt2 = solver.to_smt2()
    outcome = solver.check()

    if outcome == z3.sat:
        model = solver.model()
        assignment = {}
        for label, variable in variables.items():
            value = model.eval(variable, model_completion=True)
            assignment[label] = value.as_long()
        return SolverRecord(
            solver=name, version=version, status="sat",
            reason=(f"the conjunction of {len(composition.clauses)} clause(s) is "
                    "satisfiable over the abstract feature projection"),
            bounds=limits, encoding_hash=composition.encoding_hash, smt2=smt2,
            model=assignment)
    if outcome == z3.unsat:
        return SolverRecord(
            solver=name, version=version, status="unsat",
            reason=(f"the conjunction of {len(composition.clauses)} clause(s) is "
                    "unsatisfiable, so no response satisfies the composition even "
                    "in the abstraction; the proposal is rejected (section 8.5)"),
            bounds=limits, encoding_hash=composition.encoding_hash, smt2=smt2,
            model={})
    return SolverRecord(
        solver=name, version=version, status="unknown",
        reason=(f"the solver returned unknown ({solver.reason_unknown()}); section "
                "8.6 fails closed on unknown exactly as on unsat, because an "
                "undecided conjunction is not evidence of feasibility"),
        bounds=limits, encoding_hash=composition.encoding_hash, smt2=smt2,
        model={})


def assert_progressable(record: SolverRecord) -> SolverRecord:
    """Fail closed unless the solver said `sat`."""
    if record.progressable:
        return record
    raise SolverError(
        f"solver status {record.status!r} does not support progression: "
        f"{record.reason}")
