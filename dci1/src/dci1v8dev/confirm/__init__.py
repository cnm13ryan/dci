"""The v8 **confirmatory** layer: freeze, protected generation, analysis.

**Status (2026-09-02).** The pilot layer (``dci1v8dev.run``) ends at
``PILOT_REPORT`` and can render no composed cell; this package is the
continuation that can, and it can do so only after a signed freeze. It has
its own seven-stage lifecycle in its own roots (``dci1v8-confirm-*``), and
it reads each model's pilot evidence --- the signed Gate-2 and Gate-3
records and their rows --- by verified signature and recorded hash, never
by re-running a pilot stage.

Stages, in order:

1. ``CONFIRM_REGISTERED``   the confirmatory manifest, signed once per root
2. ``LOCAL_TOPUP``          the frame-aware rung top-up (a stated rule; may
                            generate nothing), and the augmented Gate-3
3. ``MEMBERSHIP``           n*(f)/m*(f) stability, LOCAL/SPECTRUM membership,
                            the slot maps, the reference-sensitivity plan
4. ``FROZEN``               the signed design: everything the analysis reads
5. ``CONFIRMATORY_GENERATION``  the protected composed cells
6. ``CONFIRMATORY_ANALYSIS``    per-frame estimates, bootstrap, claims
7. ``FINAL_REPORT``

**The development / protected boundary.** Every stage up to and including
``FROZEN`` reads solo, chance and counterfactual-chance rows only (the
pilot's §13.11 schema is closed and this layer adds no field to it). A
composed cell exists only under ``CONFIRMATORY_GENERATION``, whose runner
verifies the signed freeze before rendering one, and nothing after the
freeze can move a threshold, an operating point, a reference or a frame:
``FROZEN`` is write-once and the analysis asserts its own inputs against
the freeze hash.

**What is v7's and what is new.** The estimators (``dci1v7.analysis``:
``estimators``, ``bootstrap``, ``spectrum``, ``boundary``, ``claims``), the
block bootstrap, the studentised maximum-modulus intervals, the boundary
allowance and the Delta_R readings are the registered v7 code, imported
and called **per frame**. New: the frame-preserving design (every slot of
a block is rendered under the block's frame), the joint cross-frame family
(topic-level resampling, one draw shared by every frame's members), the
pre-registered reference-sensitivity contrast over the admissible triples
of {R1..R5}, and the prospective allocation/multiplicity rule
(``confirm.precision``).
"""
from __future__ import annotations

from dci1v8dev.run import STUDY_ID, EVIDENCE_DIRNAME  # noqa: F401

#: Stamped on every confirmatory row. Distinct from the pilot's so a
#: composed row can never be mistaken for a pilot row, and vice versa.
CLASSIFICATION = ("DCI-1 PROTOCOL v8 CONFIRMATORY (frozen design; "
                  "protected composed outcome)")
#: The design note of record for this layer.
CONFIRM_DOCUMENT = "dci1/docs/V8_CONFIRMATORY.md"
#: The standalone v8 preregistration: the document every freeze binds and
#: the readiness audit requires to be final (``Status: FROZEN-READY``).
PREREGISTRATION_DOCUMENT = "dci1/docs/DCI1_preregistration_v8.md"
#: The study-level membership lock, written before any composed row exists
#: and bound by hash into every model's freeze.
MEMBERSHIP_DOCUMENT = "dci1/reports/dci1v8dev/confirmatory_membership.json"
PROTOCOL_VERSION = "8.0-confirmatory"

__all__ = ["STUDY_ID", "EVIDENCE_DIRNAME", "CLASSIFICATION",
           "CONFIRM_DOCUMENT", "MEMBERSHIP_DOCUMENT", "PROTOCOL_VERSION"]
