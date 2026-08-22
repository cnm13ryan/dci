"""DCI-1 protocol v5: the rebuilt reference-construction procedure.

**Status: DRAFT. Not adopted, not registered, not frozen.** No v5 stage
record exists, no v5 topic has been authored, no v5 instrument has been
measured, and no v5 generation exists. ``protocol/decisions.py`` carries the
nineteen registered open decisions of preregistration §34; every one of them
is ``UNRESOLVED`` and any stage that depends on one refuses to execute. A
reader who meets only this module should take from it that the machinery
below is implemented and that the science it implements has not been closed.

**Why there is a v5.** v4r4 completed: two of four replications reached
``UNMASKED_ANALYSIS`` on the reduced design and two terminated at Gate 4 with
``COMPOSED_HEADROOM_FAILURE``. Every companion-specific estimand --- Delta_R,
Delta_j, delta_difficulty, Xi --- was ``NOT_IDENTIFIED`` study-wide, because
the reference-construction procedure delivered no usable counterfactual on any
surviving replication. v4r4 was frozen and produced confirmatory data, so
under v4r3 §31 a scientific change creates a new protocol version.

**What this package implements that v4r4 did not.** A structural taxonomy with
three tiers and thirteen declared metadata fields; a candidate library whose
core reference pool is *same-form with A* --- exact counts of a short marker
word --- reversing v4r4's class rule; an eight-component reference-validity
conjunction evaluated lexicographically, with instructed compliance evaluated
**last**; a pre-composition interaction gate reading kappa(R|B); a two-split
calibration with an equivalence-based stability rule; an arm-derived cell plan;
direct cross-configuration order estimands; and a per-named-member L4.

**Isolation, in every direction.** ``STUDY_ID`` is ``dci1v5``. It satisfies no
earlier revision's admission prefix: ``dci1v4``'s guard tests
``startswith("dci1-v4")`` and v4r3's and v4r4's ``assert_own_study`` test exact
equality against their own identifiers, so a v5 record can never satisfy an
earlier stage's predecessor check. In the other direction this package's
``FOREIGN_STUDY_PREFIXES`` names every earlier study and screen, **including
``dci1v4r4``**, whose evidence is historical and enters v5 only as
``DEVELOPMENT_EVIDENCE`` or ``RECOMPUTED_DIAGNOSTIC`` through
``protocol/reuse_ledger.py``. ``tests_v5/test_isolation.py`` asserts both
directions.

**What v5 does not claim.** The measurement basis its Gate 1 can write is
``deterministic_measurement_validated``, exactly as v4r4's was. That is not
``human_validated``, so ``SCOPE_SENTENCE`` attaches to every analysis record
under it, permanently.
"""
from __future__ import annotations

#: The study identity written into every v5 manifest and stage record.
#: Deliberately hyphen-free and deliberately not a prefix-extension of any
#: earlier identifier: see the isolation note above.
STUDY_ID = "dci1v5"

#: What this package's artifacts are, for any reader that meets one. The
#: word DRAFT is load-bearing: nothing here may be described as registered
#: until §34's decisions are closed and the manifest is signed.
CLASSIFICATION = "DCI-1 PROTOCOL v5 (DRAFTED, NOT ADOPTED, NOT FROZEN)"
SUPERSEDED_CLASSIFICATIONS: tuple[str, ...] = ()

#: The revision this one follows, and how it ended. v4r4 did **not**
#: terminate: it completed, and that is why v5 is a new version rather than a
#: continuation.
SUPERSEDES = "dci1v4r4"
SUPERSEDES_TERMINAL_STAGE = "UNMASKED_ANALYSIS"
SUPERSEDES_TERMINAL_STATUS = "COMPLETED"

#: The evidence tree, a sibling of every other study's and of every screen's.
EVIDENCE_DIRNAME = "dci1v5"

#: The preregistration this package implements, by repository path.
PREREGISTRATION = "user-notes/DCI1_preregistration_v5.md"

#: The machine-readable statement of §13's rule. §13.1: where it and the
#: preregistration disagree, the preregistration governs and the file is
#: repaired.
REFERENCE_DESIGN_SPEC = "dci1/reports/dci1v5/reference_design_spec.json"

#: Study identifier prefixes whose artifacts this package refuses as input
#: (§14.2). ``dci1v4r4`` is the entry that matters: v4r4 produced signed
#: records through ``UNMASKED_ANALYSIS`` and confirmatory rows, and none of
#: them may satisfy a v5 stage or reach a v5 estimator. Its rows are
#: development evidence and reach v5 only through ``protocol/reuse_ledger.py``.
FOREIGN_STUDY_PREFIXES = ("dci1-v2", "dci1-v3", "dci1-v4", "dci1v4r3",
                          "dci1v4r4", "br-pilot", "fs-screen", "bgrid-screen",
                          "matrix-screen", "dci1-cal-screen")

__all__ = ["STUDY_ID", "CLASSIFICATION", "SUPERSEDED_CLASSIFICATIONS",
           "EVIDENCE_DIRNAME", "PREREGISTRATION", "REFERENCE_DESIGN_SPEC",
           "FOREIGN_STUDY_PREFIXES", "SUPERSEDES", "SUPERSEDES_TERMINAL_STAGE",
           "SUPERSEDES_TERMINAL_STATUS"]
