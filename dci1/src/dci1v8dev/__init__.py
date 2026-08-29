"""DCI-1 **v8 development candidate**: the uncertainty-aware reference pre-screen.

This package is *not* a registered protocol. It is exploratory, development-only
code (see `CLAUDE.md`, "Two areas, different expectations") that proposes how a
v8 preregistration could replace §12.2's carry-everything retention and
§12.6's raw max-min coverage certificate with a staged, uncertainty-aware
screen:

    broad cheap search  ->  uncertainty-aware ranking  ->  targeted re-screen
                        ->  deliberately spaced rung retention  ->  calibration

It **imports** the registered v7 kernels it needs (family metadata, ladders,
reserves, the registered thresholds, the production coverage criterion for the
comparison baseline) and **changes none of them**. Nothing here is on any v7
execution path, no v7 record is read for writing, and no v7 constant moves.

Layout:

* ``prescreen.schema``     the closed pre-screen input schema (the §13.11-style
                           leakage guard: no composed field can enter)
* ``prescreen.statistics`` Beta posteriors, topic-clustered effective sample
                           sizes, seeded posterior draws, conservative spans,
                           shrinkage
* ``prescreen.geometry``   per-draw evaluation of the calibration-basis
                           geometry (eligibility, straddle, span, support
                           below/above A, local match)
* ``prescreen.ladder``     monotonicity and ladder-quality diagnostics
* ``prescreen.screen``     the family screen: probabilities, statuses, labels,
                           ranking
* ``prescreen.rescreen``   the deterministic targeted second pass
* ``prescreen.retention``  deliberately spaced rung retention, per arm
* ``prescreen.pipeline``   the staged procedure end to end
* ``prescreen.legacy``     the current (v5-v7) certificate, for comparison
* ``simulate``             synthetic families and operating characteristics
* ``backtest``             read-only replay over stored evidence

Every quantity a rule here reads is a **solo, unconstrained-chance or vacuity
measurement on the pre-screen (or re-screen) topics**, family structure, and
severity. No composed outcome exists in the input schema; ``tests_v8dev``
asserts that executably.
"""
from __future__ import annotations

__all__ = ["VERSION_NOTE"]

VERSION_NOTE = ("dci1v8dev: development candidate for a v8 reference "
                "pre-screen; not registered; not on any v7 path")
