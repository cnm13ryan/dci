"""The extended focal grid, and the proof that it extends rather than changes B.

The registered code refuses an unregistered severity by construction:
``Constraint("B", 11)`` raises and ``focal_wordings(11)`` raises. That refusal
is correct and this screen does not weaken it. Instead the screen carries its
own renderer and its own scorer for m in {11, 12}, and proves they are the
registered ones by two equalities that the test suite enforces:

* ``screen_wordings(m) == focal_wordings(m)`` byte-for-byte for every m in the
  registered FOCAL_GRID, so the extension is the registered template family;
* ``screen_score(m, text)`` agrees with ``score_constraint(Constraint("B", m),
  text)`` on pass, graded and statistic for every m in the registered grid over
  the whole fixture suite, so the extension is the registered rule.

B's *rule* is unchanged: longest alphabetic run at most m letters. Only the
severity range is extended, and only inside this screen.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.wordings import focal_wordings
from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS
from dci1v4.verifiers.constraints import FOCAL_GRID
from dci1v4.verifiers.statistics import focal_statistic
from dci1v4.verifiers.words import alpha_runs, words_lower

#: The registered grid, plus the two screen-only rungs. Nothing registers these.
SCREEN_FOCAL_GRID: tuple[int, ...] = (7, 8, 9, 10, 11, 12)
EXTENSION: tuple[int, ...] = tuple(m for m in SCREEN_FOCAL_GRID
                                   if m not in FOCAL_GRID)
GRID_MAX = max(SCREEN_FOCAL_GRID)

#: The registered §7.1 B templates, verbatim, parameterised on m. Kept here so
#: the extension renders from the same four strings; ``assert_wordings_match``
#: proves the equality on the registered rungs rather than trusting the copy.
_TEMPLATES = (
    "Every word in the answer must have at most {m} letters.",
    "Use only words of {m} letters or fewer.",
    "Do not use any word longer than {m} letters.",
    "No word in your answer may exceed {m} letters.",
)


def screen_wordings(m: int) -> tuple[str, str, str, str]:
    if m not in SCREEN_FOCAL_GRID:
        raise ProtocolError(f"m={m} outside the screen focal grid "
                            f"{SCREEN_FOCAL_GRID}")
    return tuple(t.format(m=m) for t in _TEMPLATES)


def screen_wording(m: int, index: int) -> str:
    return screen_wordings(m)[index % len(_TEMPLATES)]


def screen_score(m: int, text: str, *, truncated: bool) -> dict:
    """B's registered rule at a screen severity; fail-closed like the original."""
    if m not in SCREEN_FOCAL_GRID:
        raise ProtocolError(f"m={m} outside the screen focal grid")
    word_count = len(alpha_runs(text))
    non_vacuous = (word_count > 0 and not truncated
                   and word_count >= NON_VACUITY_MIN_WORDS)
    try:
        statistic = focal_statistic(text)
        passed = statistic <= m
        lowered = words_lower(text)
        graded = (0.0 if not lowered
                  else 1.0 - sum(1 for w in lowered if len(w) > m) / len(lowered))
    except Exception:
        return {"kind": "B", "severity": m, "statistic": None, "passed": False,
                "graded": 0.0, "non_vacuous": False, "vacuous_pass": False,
                "processing_failure": True}
    return {"kind": "B", "severity": m, "statistic": statistic,
            "passed": passed, "graded": graded, "non_vacuous": non_vacuous,
            "vacuous_pass": passed and not non_vacuous,
            "processing_failure": False}


# ------------------------------------------------------------- the equalities
def assert_wordings_match() -> dict:
    """The extension is the registered template family, on every registered m."""
    for m in FOCAL_GRID:
        if screen_wordings(m) != focal_wordings(m):
            raise ProtocolError(
                f"screen B wordings at m={m} differ from the registered ones")
    return {"registered_rungs_checked": list(FOCAL_GRID),
            "extension_rungs": list(EXTENSION),
            "wordings_identical": True,
            "extension_at_m11": list(screen_wordings(11))}


def assert_scoring_matches(texts) -> dict:
    """The extension is the registered rule, on every registered m."""
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import Constraint

    checked = 0
    for m in FOCAL_GRID:
        for text in texts:
            for truncated in (False, True):
                a = score_constraint(Constraint("B", m), text,
                                     truncated=truncated)
                b = screen_score(m, text, truncated=truncated)
                if (a.passed, a.graded, a.statistic, a.non_vacuous) != (
                        b["passed"], b["graded"], b["statistic"],
                        b["non_vacuous"]):
                    raise ProtocolError(
                        f"screen scorer disagrees with the registered "
                        f"verifier at m={m} on {text!r}")
                checked += 1
    return {"verdicts_checked": checked, "agreement": 1.0,
            "registered_rungs": list(FOCAL_GRID)}


def assert_monotone_in_m(texts) -> dict:
    """A looser m never fails a text a tighter m passed."""
    for text in texts:
        seen = [screen_score(m, text, truncated=False)["passed"]
                for m in SCREEN_FOCAL_GRID]
        if any(seen[i] and not seen[i + 1] for i in range(len(seen) - 1)):
            raise ProtocolError(f"B is not monotone in m on {text!r}")
    return {"texts": len(texts), "monotone": True}
