"""DCI-1 v4 revision 3: the hybrid difficulty-spectrum study.

A prospectively isolated sibling of ``dci1v4``. It imports that package's
protocol-neutral machinery — hashing, seeds, prompt rendering primitives,
word segmentation, the exact-count rule, the count statistics — and defines
its own protocol: its own constants, grids, ladders, cell plan, selection
rules, estimators and gate payloads.

**Isolation, in both directions.** ``dci1v4``'s admission guard tests a study
identifier prefix (``str(study).startswith("dci1-v4")``), so a v4r3 identifier
carrying a hyphen would satisfy it and a v4r3 artifact could reach a v4r2
estimator. ``STUDY_ID`` is therefore ``dci1v4r3`` with no hyphen, which that
prefix test rejects; and this package's own admission rule rejects every
v4r2 identifier. ``tests_v4r3/test_isolation.py`` asserts both directions,
and asserts that nothing in ``dci1v4`` imports this package.

**Adoption.** ``user-notes/DCI1_preregistration_v4r3.md`` was adopted by the
researcher on 2026-08-21 (``dci1/DECISIONS_V4R3.md`` A0) and this package is
its executable form. The study is registered under a signed manifest and is
**not frozen**; no confirmatory data exist. No registered v4r2 constant,
verifier, grid, ladder, wording, threshold or evidence record is changed by
its existence.

``CLASSIFICATION`` moved at adoption, so rows generated before it carry the
earlier label. That is a provenance fact and not a defect: a row says which
label was current when it was produced, and the registration record dates the
change. The scientific identity of a row is its ``study_id``, its verifier
hash and its manifest hash, none of which moved.
"""
from __future__ import annotations

#: The study identity written into every v4r3 manifest and stage record.
#: Deliberately hyphen-free: see the isolation note above.
STUDY_ID = "dci1v4r3"

#: What this package's artifacts are, for any reader that meets one.
#: Superseded label, retained so a row carrying it can be placed:
SUPERSEDED_CLASSIFICATIONS = (
    "DCI-1 PROTOCOL v4 REVISION 3 (PROPOSED, NOT ADOPTED)",
)
CLASSIFICATION = "DCI-1 PROTOCOL v4 REVISION 3 (ADOPTED, NOT FROZEN)"

#: The evidence tree, a sibling of every other study's and of every screen's.
EVIDENCE_DIRNAME = "dci1v4r3"

#: The preregistration this package implements, by repository path.
PREREGISTRATION = "user-notes/DCI1_preregistration_v4r3.md"

#: Study identifier prefixes whose artifacts this package refuses as input
#: (§14.2). The v4r2 entry is the one that matters: v4r2 produced no
#: confirmatory data, but it produced signed gate records, and a v4r3
#: analysis must never read one.
FOREIGN_STUDY_PREFIXES = ("dci1-v2", "dci1-v3", "dci1-v4", "br-pilot",
                          "fs-screen", "bgrid-screen", "matrix-screen",
                          "dci1-cal-screen")

__all__ = ["STUDY_ID", "CLASSIFICATION", "SUPERSEDED_CLASSIFICATIONS",
           "EVIDENCE_DIRNAME", "PREREGISTRATION", "FOREIGN_STUDY_PREFIXES"]
