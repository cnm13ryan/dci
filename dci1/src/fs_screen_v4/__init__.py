"""FORM x STEM screen — a NON-CONFIRMATORY design screen for DCI-1 v4.

Same standing as the B+R pilot: this is design evidence. It is not a registered
v4 stage, it has no Gate 1 dependency, and nothing it produces may enter a v4
estimator. Its evidence root (``evidence/fs-screen-v4``) is outside the v4
namespace, so ``dci1v4.engine.guards.assert_registered_v4_input`` refuses it by
construction — the admission rule is positive and this tree cannot prove v4
membership.

It changes no registered constant, verifier, threshold, grid, ladder, wording or
protocol text. It reads the registered verifier statistics and the registered
wording discipline; it defines its own candidate constraints beside them.

What it tests, from the read-only diagnostic of 2026-08-20:

* **FORM** — every registered reference family is an ``S <= q`` monotone count
  budget whose pass set is downward-closed under prefix. The empty string scores
  94/94 on the pool, 4/4 on B and 0/8 on A. Candidate forms (rate, lower-bound)
  break that closure.
* **STEM** — a uniform answer-length instruction removes the shortening escape
  for B and for every reference at once, leaving the gradient alone.

Neither has ever been observed under its own instruction.
"""
STUDY_ID = "fs-screen-v4"
CLASSIFICATION = "design evidence; non-confirmatory"
