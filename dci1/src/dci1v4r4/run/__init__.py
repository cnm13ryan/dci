"""Execution layer for v4r3: plan, generate, score, record.

Nothing scientific is decided here. The design comes from ``design`` and
``stages``, the instruments from ``verifiers``, the seeds from
``protocol.seeds``; this package turns those into backend plans, runs them
through the carried ``dci1v4.generation`` seam, scores the rows with the v4r3
compliance primitive and writes append-only evidence under
``evidence/dci1v4r4/``.
"""
