"""DCI-1 v4 revision 4: the hybrid difficulty-spectrum study, with a
deterministic-measurement Gate 1.

A prospectively isolated sibling of ``dci1v4r3``, which is closed. It imports
``dci1v4``'s protocol-neutral machinery -- hashing, seeds, prompt rendering
primitives, word segmentation, the exact-count rule, the count statistics --
and carries its own protocol: its own constants, grids, ladders, cell plan,
selection rules, estimators and gate payloads.

**Why this revision exists.** v4r3 terminated at Gate 1. Its registered
measurement criterion (§18 stage 4: §10.2 plus §10.3 or §10.4) asked whether
external reviewers reproduce the verifier's verdicts, and neither pathway
established that basis: §10.3 had no independent annotator available, and
§10.4/§10.4-R/§10.4-R2 failed their own registered criteria. The development
evidence behind those failures is specific and it is recorded: reviewers --
human and LLM alike -- introduced counting, arithmetic, segmentation,
threshold and convention errors of exactly the kind a deterministic verifier
exists to avoid. For a study whose constraints are *mechanically decidable*,
reviewer agreement measures reviewer performance, not instrument validity.

v4r4 therefore replaces that criterion, prospectively and before Gate 2, with a
deterministic-measurement architecture (§10.7): specification validity,
implementation validity, independent reimplementation, adversarial/boundary/
**mutation** validation, and provenance binding. Reviewer evidence survives as
a diagnostic and can move no gate in either direction.

**What v4r4 does not claim.** The measurement basis it can write is
``deterministic_measurement_validated``. That is not ``human_validated``, so
``SCOPE_SENTENCE`` attaches to every analysis record under it, permanently:
the outcomes remain verifier-defined. v4r4 buys the study its execution, not a
stronger claim. §10.5's second question -- would an independent human reproduce
these verdicts? -- is as unanswered in v4r4 as it was in v4r3, and the
revision says so rather than letting the change of criterion imply otherwise.

**Isolation, in three directions.** ``dci1v4``'s admission guard tests a study
identifier prefix (``str(study).startswith("dci1-v4")``), so an identifier
carrying a hyphen would satisfy it and a v4r4 artifact could reach a v4r2
estimator. ``STUDY_ID`` is therefore ``dci1v4r4`` with no hyphen. This
package's own admission rule rejects every v4r2 **and every v4r3** identifier:
v4r3's records are historical evidence of a study that stopped, and none of
them satisfies a v4r4 predecessor check. ``tests_v4r4/test_isolation.py``
asserts every direction.

**Status.** Registered under a signed manifest, **not frozen**; no
confirmatory data exist. No registered v4r2 or v4r3 constant, verifier, grid,
ladder, wording, threshold or evidence record is changed by this package's
existence.
"""
from __future__ import annotations

#: The study identity written into every v4r4 manifest and stage record.
#: Deliberately hyphen-free: see the isolation note above.
STUDY_ID = "dci1v4r4"

#: What this package's artifacts are, for any reader that meets one.
CLASSIFICATION = "DCI-1 PROTOCOL v4 REVISION 4 (ADOPTED, NOT FROZEN)"
SUPERSEDED_CLASSIFICATIONS: tuple[str, ...] = ()

#: The revision this one supersedes, and the stage it reached. Recorded here
#: so that a reader who meets only this module learns that v4r3 exists, that
#: it stopped, and where.
SUPERSEDES = "dci1v4r3"
SUPERSEDES_TERMINAL_STAGE = "GATE_1_MEASUREMENT"
SUPERSEDES_TERMINAL_STATUS = "MEASUREMENT_EVIDENCE_INSUFFICIENT"

#: The evidence tree, a sibling of every other study's and of every screen's.
EVIDENCE_DIRNAME = "dci1v4r4"

#: The preregistration this package implements, by repository path.
PREREGISTRATION = "user-notes/DCI1_preregistration_v4r4.md"

#: Study identifier prefixes whose artifacts this package refuses as input
#: (§14.2). ``dci1v4r3`` is the entry that matters most: v4r3 produced signed
#: qualification, apparatus and regime records, and a v4r4 stage must never
#: accept one as its predecessor. Its *rows* may be reused, but only through
#: the explicit ledger of ``stages/reuse.py``, never by a path that mistakes
#: them for v4r4's own.
FOREIGN_STUDY_PREFIXES = ("dci1-v2", "dci1-v3", "dci1-v4", "dci1v4r3",
                          "br-pilot", "fs-screen", "bgrid-screen",
                          "matrix-screen", "dci1-cal-screen")

__all__ = ["STUDY_ID", "CLASSIFICATION", "SUPERSEDED_CLASSIFICATIONS",
           "EVIDENCE_DIRNAME", "PREREGISTRATION", "FOREIGN_STUDY_PREFIXES",
           "SUPERSEDES", "SUPERSEDES_TERMINAL_STAGE",
           "SUPERSEDES_TERMINAL_STATUS"]
