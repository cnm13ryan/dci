"""The v8 **pilot** execution layer: stages, CLI, manifest, seeds, roots.

**Status (2026-08-30).** Development candidate, prospective, unregistered.
This package runs the v8 candidate's pre-composition chain on a real model
under the v8 wording instrument, in an evidence root of its own, so that the
four questions the candidate leaves open can be measured before anything is
frozen (``dci1/docs/V8_PILOT.md``):

1. the repaired frames' reliability (marker-absent share per frame);
2. ladder difficulty coverage after the uncertainty-aware screen, the
   second pass and the spaced retention;
3. the chance column measured on §13.2's unconstrained cell, in both tables;
4. LOCAL / SPECTRUM reference survival at calibration precision.

It generates **no composed cell**: no B+R, no R+B, no confirmatory row. The
spectrum arm's cells are a post-freeze experiment and this layer has no
stage that could render one (``stages.STAGE_SEQUENCE`` ends at the report).

**What it reuses and what it owns.** The generative seam
(``dci1v4.generation.backend``), the row-statistics kernels
(``dci1v7.run.execute.cell_rates`` and friends), §13.11's producer on the
corrected chance basis (``dci1v7.run.gates_run._calibration_rows``, the
7f89dae fix), the §12.3 operating-point rules, §13.7's stability verdict and
§13.8's core-selection kernel are imported from v7 unchanged --- they are
pure functions of rows and tables and carry no v7 identity. Everything that
carries an identity is this package's own: the study id ``dci1v8``, the
classification stamped on every row, the evidence layout under a root no v7
reader accepts, the seed domain ``dci1v8:*``, the prompt rendered from
``dci1v8dev.wordings`` (the v8 instrument), the rows scored by
``dci1v8dev.verifiers`` (the v8 hash), and the record schemas of nine stages.

**Isolation.** A v8 root must lie outside every other study's evidence and
durable tree (``context.assert_isolated_root``); a v8 record carries
``study_id: dci1v8`` (or ``dci1v8-synthetic``) which no ``dci1v7``
``read_stage_record`` accepts, and the v8 signing key is its own. Nothing here
reads a v7 evidence tree, and nothing here can write into one.

**Namespaces.** ``pilot`` --- the pinned backend, the real model, every rule;
``synthetic`` --- a stand-in generator and scale knobs, for the lifecycle test
and the audits. There is no registered namespace: v8 is not registered, and a
root is always named on the command line.
"""
from __future__ import annotations

#: The study identity on every v8 pilot manifest, record and row. Hyphen-free,
#: a prefix-extension of no earlier id, and a prefix of none of v7's
#: (``dci1v7`` refuses anything but exact equality anyway).
STUDY_ID = "dci1v8"
#: Stamped on every generated row by ``run/execute``.
CLASSIFICATION = "DCI-1 PROTOCOL v8 PILOT (development candidate; not registered)"
#: The evidence tree under a root: ``<root>/evidence/dci1v8/<model>/...``.
EVIDENCE_DIRNAME = "dci1v8"
#: The design of record this layer executes, and the pilot's own note.
DESIGN_DOCUMENT = "dci1/docs/V8_CANDIDATE.md"
PILOT_DOCUMENT = "dci1/docs/V8_PILOT.md"
#: The frame-conditioning design note (Approach A, researcher decision of
#: 2026-08-30): the wording frame is part of the experimental condition.
FRAME_DOCUMENT = "dci1/docs/V8_FRAME_CONDITIONING.md"
#: The frame-aware pre-screen (successor design, 2026-09-03): the screen,
#: the second pass and the forwarding are per frame.
PRESCREEN_DOCUMENT = "dci1/docs/V8_FRAME_AWARE_PRESCREEN.md"
#: The v7 preregistration the candidate amends; bound by hash as the base.
BASE_PREREGISTRATION = "user-notes/DCI1_preregistration_v7.md"
#: What this layer supersedes as the live line, and how that line ended.
SUPERSEDES = "dci1v7"
SUPERSEDES_TERMINAL_STATUS = "CLOSED: 0/4 survivors (C4 lost at Gate 3C; " \
                             "PREFREEZE_AUDIT_FAILURE)"

__all__ = ["STUDY_ID", "CLASSIFICATION", "EVIDENCE_DIRNAME",
           "DESIGN_DOCUMENT", "PILOT_DOCUMENT", "FRAME_DOCUMENT",
           "PRESCREEN_DOCUMENT", "BASE_PREREGISTRATION",
           "SUPERSEDES", "SUPERSEDES_TERMINAL_STATUS"]
