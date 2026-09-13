"""The B-grid screen: does an honest focal severity exist on all four models?

NON-CONFIRMATORY DESIGN SCREEN. Same standing as the FORM x STEM screen. Not a
registered v4 stage, no Gate 1 dependency, nothing here may enter a v4
estimator, and ``evidence/bgrid-screen-v4`` sits outside the v4 namespace so the
positive-admission guard refuses it.

**The question.** Under the current prompt stem, honest B-solo compliance is
0.000 on qwen3-4b and 0.042 on qwen3-4b-instruct-2507: their apparent ~0.75 is
carried entirely by sub-twenty-word answers. The floored stem removes that
escape and, on the registered focal grid m in {7, 8, 9, 10}, drives both Qwens
to FOCAL_RANGE_EXHAUSTED. An extended focal grid is the only known route to an
honest B on all four models. This screen measures whether one exists at
m <= 12.

m = 11 and m = 12 are screen-only extensions. They are not registered, and
nothing in this package registers them.
"""
from __future__ import annotations

STUDY_ID = "bgrid-screen-v4"
CLASSIFICATION = "design evidence; non-confirmatory"
