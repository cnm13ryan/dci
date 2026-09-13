"""Every function a v19 verifier executes is in its implementation hash, or is
identity machinery whose output is already hashed elsewhere.

Appendix I wants an invariant hash over "the code that ran". The implementation
tuples in `dci.v19.verifiers.bundle` were written by hand, and review found them
short: the outcome contract every verifier returns through (`_scored`,
`_count_compliance`, `Verifier.invoke`, ...), Pair 1's marker builders and
ordering-relation closure, and two Pair 2 token helpers all executed on every
scored answer while no hash covered their source. A change to any of them would
move a recorded verdict, compliance or generation state with the frozen bundle
identity standing still.

This test replaces trust in the hand-written tuples with a trace. It runs every
verifier over inputs that reach each outcome branch (PASS, FAIL, missing
metadata, empty, unparseable, caller-supplied states) and asserts that each
executed `dci.*` function either lies inside the source of a hashed callable
(nested functions and generator expressions are part of their parent's source)
or is on IDENTITY_ONLY, where each entry says which hash already carries it.
"""
import inspect
import re
import sys

import pytest

from dci.v19 import parsing
from dci.v19 import verifiers as V
from dci.v19.pairs import PAIR_1, PAIR_2, PAIR_3
from dci.v19.verifiers import GenerationState

pytestmark = pytest.mark.cpu

P = V.CANONICAL_LIST_POLICY
RELATION = parsing.OrderingRelation(items=("alpha", "beta", "gamma"),
                                    edges=(("alpha", "beta"), ("beta", "gamma")))

TEXTS = (
    "Intro:\n1. alpha first.\n2. beta second.\n3. gamma third.",
    "- gamma\n- alpha\n- beta",
    "1) alpha\n2) alpha\n3) beta",
    "",
    "   ",
    "One. Two words. Three words here.",
    "Three words here. Two words. One.",
    "the and the and",
    "unique words only here",
    "Mr. Smith went home. He stayed.",
    "no terminator",
    "alpha beta gamma",
)

PARAMETERS = {
    PAIR_1.target.constraint_id: (dict(n_items=3), dict(n_items=2),
                                  dict(n_items=None), dict(n_items="x")),
    PAIR_1.focal.constraint_id: (dict(relation=RELATION), dict(relation=None)),
    PAIR_2.target.constraint_id: (dict(mandatory_words=("the", "and")),
                                  dict(mandatory_words=("zebra",)),
                                  dict(mandatory_words=None)),
    PAIR_2.focal.constraint_id: (dict(),),
    PAIR_3.target.constraint_id: (dict(n_sentences=3), dict(n_sentences=2),
                                  dict(n_sentences=None)),
    PAIR_3.focal.constraint_id: (dict(),),
}

STATES = tuple(GenerationState)

#: Executed, deliberately not in any implementation tuple, and why that is safe.
#: Each pattern is matched against "<module>.<qualname>".
IDENTITY_ONLY = {
    # Hashing itself: the machinery that turns everything below into a digest.
    r"dci\.provenance\.hashes\.(sha|canonicalize)": "the hash function",
    # Specification construction: its output IS the spec hash.
    r"dci\.v19\.verifiers\._p\d_\w+_spec": "builds the spec; hashed as spec_hash",
    r"dci\.v19\.verifiers\.VerifierSpec\.(__post_init__|spec_hash|state)":
        "spec validation and serialisation; hashed as spec_hash",
    r"dci\.v19\.verifiers\.frozen_segmentation": "spec segmentation state",
    r"dci\.v19\.text\.abbreviation_guard_state": "spec segmentation state",
    # Policy and parameter identity: serialised into the spec or outcome hashes.
    r"dci\.v19\.text\.TextPolicy\.(state|policy_hash)": "text policy hash in spec",
    r"dci\.v19\.parsing\.ListPolicy\.(state|policy_hash|marker_patterns)":
        "list policy state and marker patterns are in frozen_segmentation",
    r"dci\.v19\.(text|parsing)\.require_policy": "type check on the policy object",
    r"dci\.v19\.parsing\.OrderingRelation\.(state|relation_hash)":
        "the relation's identity, not its evaluation",
    # Generated and dispatch code with no measurement of its own.
    r"dci\.v19\.\w+\.__create_fn__\.<locals>\.__init__": "dataclass-generated __init__",
    r"dci\.v19\.verifiers\.bundle\.<locals>\.<lambda>":
        "dispatch to the hashed verify_* function with the hashed policy",
}


def _spans(verifier):
    spans = []
    for fn in verifier.implementation:
        lines, start = inspect.getsourcelines(fn)
        spans.append((inspect.getsourcefile(fn), start, start + len(lines) - 1))
    return spans


def _executed(verifier, constraint_id):
    seen = {}

    def profile(frame, event, arg):
        if event == "call":
            module = frame.f_globals.get("__name__", "")
            if module.startswith("dci."):
                code = frame.f_code
                seen[(code.co_filename, code.co_firstlineno)] = (
                    f"{module}.{code.co_qualname}")

    for text in TEXTS:
        for kwargs in PARAMETERS[constraint_id]:
            for state in STATES:
                sys.setprofile(profile)
                try:
                    verifier.invoke(text, delivered_state=state, **kwargs)
                finally:
                    sys.setprofile(None)
    return seen


def _identity_only(name):
    return any(re.fullmatch(pattern, name) for pattern in IDENTITY_ONLY)


@pytest.mark.parametrize("constraint_id", sorted(PARAMETERS))
def test_every_executed_function_is_hashed_or_identity_only(constraint_id):
    verifier = V.bundle(P)[constraint_id]
    spans = _spans(verifier)
    executed = _executed(verifier, constraint_id)
    unhashed = []
    for (filename, line), name in executed.items():
        if any(filename == f and start <= line <= end for f, start, end in spans):
            continue                      # hashed directly, or nested in a hashed function
        if _identity_only(name):
            continue
        # A generator expression or local inside an identity-only function.
        parent = name.split(".<locals>")[0]
        if parent != name and _identity_only(parent):
            continue
        unhashed.append(name)
    assert not unhashed, (
        f"{constraint_id} executes code outside its implementation hash: "
        f"{sorted(set(unhashed))}. Add it to the verifier's implementation tuple, "
        "or to IDENTITY_ONLY with the hash that already carries it.")


def test_the_trace_reaches_every_outcome_branch():
    """The closure check is only as good as its inputs."""
    outcomes = set()
    for constraint_id, verifier in V.bundle(P).items():
        for text in TEXTS:
            for kwargs in PARAMETERS[constraint_id]:
                for state in STATES:
                    outcome = verifier.invoke(text, delivered_state=state, **kwargs)
                    outcomes.add((outcome.scoring, outcome.verdict))
    assert {(V.Scoring.SCORED, V.Verdict.PASS), (V.Scoring.SCORED, V.Verdict.FAIL),
            (V.Scoring.MISSING_METADATA, None)} <= outcomes


def test_the_outcome_contract_is_in_every_verifier_hash():
    contract = set(V._outcome_contract())
    for constraint_id, verifier in V.bundle(P).items():
        assert contract <= set(verifier.implementation), constraint_id
