"""Separate local-reference and spectrum-reference validity (v8 candidate).

The v5-v7 rule set carries one stability verdict per candidate, computed in
the core-reference slot with §13.8's proximity caliper folded into §13.7's
per-split admissibility, and the spectrum selection reuses that verdict. The
consequence is that a spectrum rung --- which exists to sit away from A ---
must sit inside +/-0.10 of A on both splits to be "stable". This package
states the two validities separately, replaces C4 with a criterion on the
**selected** coverage, counts only fully admissible references as backups,
and gives the spectrum a deterministic selection rule and its own design.
"""
from __future__ import annotations
