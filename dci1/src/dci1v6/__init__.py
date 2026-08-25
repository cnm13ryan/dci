"""DCI-1 protocol v6: the reference-supply and composed-headroom revision.

**Status: DRAFTED, NOT ADOPTED, NOT REGISTERED, NOT FROZEN.** No manifest
exists, no stage has run, and no behavioural row has been or may be generated
against this package. ``protocol/decisions.py`` carries the open decisions of
the v6 draft --- every one ``UNRESOLVED`` --- and
``engine/transitions.assert_transition_legal`` refuses a stage whose decisions
are open, so the lifecycle is closed at stage 1 by construction. Two further
refusals are deliberate and are **not** defects to be routed around: the v6
preregistration document named below does not exist, and neither does the v6
reference-design spec, so ``protocol/manifest.document_hashes`` raises
``Blocker``. A registration that cannot name its own protocol text binds
nothing.

**Why there is a v6.** v5 closed on 2026-08-24 having generated 459,312 live
rows and reached ``CONFIRMATORY_GENERATION`` on **no** replication. Three
replications were irreversibly D6 ``REFERENCE_SUPPORT_NOT_IDENTIFIED``;
``qwen3-4b-instruct-2507`` retained identification and terminated
``COMPOSED_HEADROOM_FAILURE``. No ``Delta_R``, ``Delta_j`` or ``Xi`` estimate
exists. ``NOT_IDENTIFIED`` is not a null result and v6 never reads it as one.

**What this package changes, and nothing else.** The scientific question, the
estimands, every threshold, the claim ladder with L5 permanently withheld, the
multiplicity families F1-F11, interaction-blind reference selection, the
prohibition on a B+R composed outcome entering selection, irreversible D6, the
prospective freeze and one-shot masking, and §31's no-repair rule are carried
from v5 **unchanged**. ``protocol/revision.py`` enumerates the differences and
checks each one against the code. In summary they are:

* **V6-E01's repair.** §12.6's expansion could not reach the Tier-1 reserve
  §7.10 widened for C4's within-family span --- on all four v5 replications,
  in both rounds, it admitted zero reserve rungs. ``stages/regime`` now
  evaluates C4's three conditions per family and extends **outward from both
  extremes** when the deficiency is a short span, which is the only direction
  that can raise a span at all. C4 itself is unchanged.
* **``GATE_2_75_COMPOSED_PROBE``.** A nineteenth stage between Gate 2.5 and
  Gate 3A, measuring composed compliance headroom at m* against
  ``probe_only`` structural stand-ins on the calibration split, before any
  reference exists. It may re-select m* exactly once, by a rule fixed before
  data, or terminate ``COMPOSED_HEADROOM_UNREACHABLE``.
* **The audits that would otherwise not see the new stage** --- §33 check 8's
  name scan, the generating-stage set, the producer/consumer contract and the
  execution-path audit.

**Isolation, in every direction.** ``STUDY_ID`` is ``dci1v6``. It satisfies no
earlier revision's admission prefix, and ``FOREIGN_STUDY_PREFIXES`` names
every earlier study and screen **including ``dci1v5``**, whose evidence is
closed and enters v6 only as ``DEVELOPMENT_EVIDENCE`` or
``RECOMPUTED_DIAGNOSTIC`` through ``protocol/reuse_ledger.py``. No v5 row may
enter a v6 estimand. ``tests_v6/test_isolation.py`` asserts both directions.

**What v6 does not claim.** The measurement basis its Gate 1 can write is
``deterministic_measurement_validated``, exactly as v5's was. That is not
``human_validated``, so ``SCOPE_SENTENCE`` attaches to every analysis record
under it, permanently.
"""
from __future__ import annotations

#: The study identity written into every v6 manifest and stage record.
#: Deliberately hyphen-free and deliberately not a prefix-extension of any
#: earlier identifier: see the isolation note above.
STUDY_ID = "dci1v6"

#: What this package's artifacts are, for any reader that meets one. It moves
#: only when the researcher adopts and registers v6, and the word that is
#: load-bearing today is NOT REGISTERED.
CLASSIFICATION = "DCI-1 PROTOCOL v6 (DRAFTED, NOT ADOPTED, NOT REGISTERED)"
SUPERSEDED_CLASSIFICATIONS: tuple[str, ...] = ()

#: The revision this one follows, and how it ended. v5 **closed**: it ran to
#: its registered terminal outcomes on all four replications and produced no
#: confirmatory evidence, which is why v6 is a new prospective version and not
#: a continuation. Per-replication terminal statuses live in
#: ``dci1/reports/dci1v5/closure.json`` and are read only as development
#: evidence.
SUPERSEDES = "dci1v5"
SUPERSEDES_TERMINAL_STAGE = "GATE_4_COMPOSED_HEADROOM"
SUPERSEDES_TERMINAL_STATUS = "CLOSED_WITHOUT_CONFIRMATORY_GENERATION"

#: The evidence tree, a sibling of every other study's and of every screen's.
EVIDENCE_DIRNAME = "dci1v6"

#: The preregistration this package implements, by repository path.
#: **It does not exist yet**, and ``protocol/manifest.document_hashes``
#: refuses to build a manifest until it does. That refusal is blocker 3 of
#: ``dci1/reports/dci1v6/READINESS.md`` and is not waivable.
PREREGISTRATION = "user-notes/DCI1_preregistration_v6.md"

#: The machine-readable statement of §13's rule, also not yet written. Where
#: it and the preregistration disagree, the preregistration governs.
REFERENCE_DESIGN_SPEC = "dci1/reports/dci1v6/reference_design_spec.json"

#: Study identifier prefixes whose artifacts this package refuses as input
#: (§14.2). ``dci1v5`` is the entry that matters: v5 produced 459,312 signed
#: rows and four terminal reports, and none of them may satisfy a v6 stage or
#: reach a v6 estimator. They are development evidence and reach v6 only
#: through ``protocol/reuse_ledger.py``.
FOREIGN_STUDY_PREFIXES = ("dci1-v2", "dci1-v3", "dci1-v4", "dci1v4r3",
                          "dci1v4r4", "dci1v5", "br-pilot", "fs-screen",
                          "bgrid-screen", "matrix-screen", "dci1-cal-screen")

__all__ = ["STUDY_ID", "CLASSIFICATION", "SUPERSEDED_CLASSIFICATIONS",
           "EVIDENCE_DIRNAME", "PREREGISTRATION", "REFERENCE_DESIGN_SPEC",
           "FOREIGN_STUDY_PREFIXES", "SUPERSEDES", "SUPERSEDES_TERMINAL_STAGE",
           "SUPERSEDES_TERMINAL_STATUS"]
